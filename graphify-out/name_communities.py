import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
from graphify.analyze import suggest_questions
from graphify.report import generate


OUT = Path("graphify-out")

PREFIX_NAMES = [
    ("NIZAM__system/schemas/", "NIZAM Data Schemas"),
    ("NIZAM__system/governor/", "NIZAM Governor and Safety"),
    ("NIZAM__system/relay/", "Telegram Relay and Routing"),
    ("NIZAM__system/config/", "Persona and Intent Router"),
    ("NIZAM__system/policies/", "Privacy and Sync Policies"),
    ("NIZAM__system/skills/", "Encoded Skill Procedures"),
    ("NIZAM__system/workflows/", "Scenario Workflows"),
    ("NIZAM__system/protocols/", "Operating Protocols"),
    ("NIZAM__system/runtime/", "Hermes Runtime Plans"),
    ("NIZAM__system/docs/", "System Architecture Doctrine"),
    ("NIZAM__system/templates/", "Artifact Templates"),
    ("NIZAM__system/personas/", "Agent Personas"),
    ("NIZAM__system/ledgers/", "Continuity Ledgers"),
    ("MARSAD__flight_radar/", "MARSAD Flight Intelligence"),
    ("MAL__financial_engine/", "MAL Financial Engine"),
    ("BADAN__body_health_system/", "BADAN Health Signals"),
    ("AHEL__family_network/", "AHEL Family Network"),
    ("TARIQ__long_horizon_strategy/", "TARIQ Long-Horizon Strategy"),
    ("MUNAWARA__tactical_strategy/", "MUNAWARA Tactical Execution"),
    ("TAFRIGH__brain_dumper/", "TAFRIGH Capture"),
    ("SHURA__brainstormer/", "SHURA Consultation"),
    ("NAQD__brain_griller/", "NAQD Critique"),
    ("SUKOON__recovery_first/", "SUKOON Recovery"),
    ("HIFZ__github_version_control/", "HIFZ Version Control"),
    ("BASIRA__future_visualization/", "BASIRA Knowledge Graphs"),
    ("MAKHZAN__archive/", "MAKHZAN Archive"),
    ("docs/architecture/", "Deployment Architecture"),
    ("scripts/", "Local Operations Scripts"),
    ("tools/", "Startup and Verification"),
    ("install-audit/", "Installation Audit"),
    ("Research_docs/", "Research Corpus"),
]

STOP = {
    "file", "area", "project", "properties", "property", "schema", "type",
    "items", "required", "description", "format", "enum", "default", "title",
    "additionalproperties", "ref", "definitions", "root", "main", "init",
    "test", "tests", "community", "json", "python", "markdown",
}


def clean_label(label: str) -> str:
    label = re.sub(r"\(\)$", "", label)
    label = re.sub(r"\.(py|json|md|txt|yaml|yml|ps1)$", "", label, flags=re.I)
    label = re.sub(r"[_-]+", " ", label)
    label = re.sub(r"\s+", " ", label).strip()
    return label


def base_name(files: list[str]) -> str:
    counts = Counter()
    for source in files:
        for prefix, name in PREFIX_NAMES:
            if source.startswith(prefix):
                counts[name] += 1
                break
        else:
            counts["NIZAM Core Foundation"] += 1
    return counts.most_common(1)[0][0] if counts else "External Dependencies"


def focus_name(node_ids: list[str], node_map: dict, degree: Counter) -> str:
    candidates = []
    for node_id in node_ids:
        node = node_map.get(node_id, {})
        label = clean_label(str(node.get("label", node_id)))
        if node_id.startswith(("area_", "file_", "project_")):
            continue
        if node.get("file_type") == "concept" and not node_id.startswith("skill_"):
            continue
        words = [word.lower() for word in re.findall(r"[A-Za-z0-9]+", label)]
        meaningful = [word for word in words if word not in STOP and len(word) > 2]
        if not meaningful:
            continue
        score = degree[node_id] * 10 + min(len(meaningful), 5)
        candidates.append((score, label))
    if not candidates:
        for node_id in node_ids:
            label = clean_label(str(node_map.get(node_id, {}).get("label", node_id)))
            if label:
                return label[:48]
        return "Supporting Components"
    return max(candidates)[1][:48]


def main() -> None:
    extraction = json.loads((OUT / ".graphify_extract.json").read_text(encoding="utf-8"))
    detection = json.loads((OUT / ".graphify_detect.json").read_text(encoding="utf-8"))
    analysis = json.loads((OUT / ".graphify_analysis.json").read_text(encoding="utf-8"))
    graph_json = json.loads((OUT / "graph.json").read_text(encoding="utf-8"))
    node_map = {node["id"]: node for node in graph_json["nodes"]}
    degree = Counter()
    for link in graph_json["links"]:
        degree[link["source"]] += 1
        degree[link["target"]] += 1

    labels = {}
    used = defaultdict(int)
    for key, node_ids in analysis["communities"].items():
        files = [
            str(node_map.get(node_id, {}).get("source_file") or "")
            for node_id in node_ids
            if node_map.get(node_id, {}).get("source_file")
        ]
        base = base_name(files)
        focus = focus_name(node_ids, node_map, degree)
        name = base if focus.lower() in base.lower() else f"{base}: {focus}"
        name = name[:72].rstrip(": ")
        used[name] += 1
        if used[name] > 1:
            name = f"{name} {used[name]}"
        labels[int(key)] = name

    graph = nx.node_link_graph(graph_json, edges="links")
    communities = {int(key): value for key, value in analysis["communities"].items()}
    cohesion = {int(key): value for key, value in analysis["cohesion"].items()}
    questions = suggest_questions(graph, communities, labels)
    (OUT / ".graphify_labels.json").write_text(
        json.dumps({str(key): value for key, value in labels.items()}, indent=2),
        encoding="utf-8",
    )
    report = generate(
        graph,
        communities,
        cohesion,
        labels,
        analysis["gods"],
        analysis["surprises"],
        detection,
        {"input": 0, "output": 0},
        ".",
        suggested_questions=questions,
    )
    (OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    analysis["questions"] = questions
    (OUT / ".graphify_analysis.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Named {len(labels)} communities")
    for key in sorted(labels)[:15]:
        print(f"{key}: {labels[key]}")


if __name__ == "__main__":
    main()
