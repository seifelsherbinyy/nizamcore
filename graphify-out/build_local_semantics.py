import json
import re
from pathlib import Path


ROOT = Path("D:/NIZAM").resolve()
OUT = ROOT / "graphify-out"

AREA_NAMES = {
    "(root)": "NIZAM Core Foundation",
    "NIZAM__system": "NIZAM System and Governance",
    "TAFRIGH__brain_dumper": "TAFRIGH Capture and Brain Dump",
    "SHURA__brainstormer": "SHURA Consultation and Brainstorming",
    "NAQD__brain_griller": "NAQD Critique and Reconciliation",
    "SUKOON__recovery_first": "SUKOON Recovery and Capacity",
    "MAKHZAN__archive": "MAKHZAN Immutable Archive",
    "HAJR__quarantine": "HAJR Quarantine",
    "TARIQ__long_horizon_strategy": "TARIQ Long-Horizon Strategy",
    "MUNAWARA__tactical_strategy": "MUNAWARA Tactical Execution",
    "MAL__financial_engine": "MAL Financial Engine",
    "BADAN__body_health_system": "BADAN Body and Health Signals",
    "AHEL__family_network": "AHEL Family Network",
    "INTAJ__output_engine": "INTAJ Output Engine",
    "YAWMIYAT__journaling": "YAWMIYAT Journaling",
    "QARAR__decisions": "QARAR Decisions",
    "HIKMAH__learnings": "HIKMAH Learning and Synthesis",
    "NUR__obsidian_vault": "NUR Obsidian Knowledge Vault",
    "JADWAL__notion_dashboards": "JADWAL Dashboards",
    "HIFZ__github_version_control": "HIFZ Version Control and Mirroring",
    "BASIRA__future_visualization": "BASIRA Visualization and Knowledge Graphs",
    "MARSAD__flight_radar": "MARSAD Flight Intelligence",
    "docs": "Architecture and Operations Documentation",
    "scripts": "Local Operations and Migration Scripts",
    "tools": "Startup and Verification Tools",
    "Research_docs": "Research Corpus",
    "install-audit": "Installation and Deployment Audit",
    ".github": "GitHub Automation",
}

MODULE_TOKENS = {
    key.split("__", 1)[0]: value
    for key, value in AREA_NAMES.items()
    if "__" in key
}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "root"


def rel_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def file_id(relative: str) -> str:
    return "file_" + slug(relative)


def area_id(area: str) -> str:
    return "area_" + slug(area)


def add_node(nodes: dict, node: dict) -> None:
    nodes.setdefault(node["id"], node)


def edge(source: str, target: str, relation: str, source_file: str, score=1.0):
    return {
        "source": source,
        "target": target,
        "relation": relation,
        "confidence": "EXTRACTED" if score == 1.0 else "INFERRED",
        "confidence_score": score,
        "source_file": source_file,
        "source_location": None,
        "weight": score,
    }


def title_for(path: Path, text: str) -> str:
    if path.suffix.lower() in {".md", ".txt"}:
        match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
        if match:
            return match.group(1).strip()
    return path.name


def resolve_reference(source: Path, raw: str, known: set[str], by_name: dict) -> str | None:
    clean = raw.split("#", 1)[0].split("?", 1)[0].strip().strip("`'\"")
    clean = clean.replace("\x00", "")
    if not clean or re.match(r"^[a-z]+://", clean, re.I):
        return None
    clean = clean.replace("\\", "/")
    candidates = [(source.parent / clean).resolve(), (ROOT / clean).resolve()]
    for candidate in candidates:
        try:
            relative = rel_path(candidate)
        except ValueError:
            continue
        if relative in known:
            return relative
    base = Path(clean).name.lower()
    matches = by_name.get(base, [])
    return matches[0] if len(matches) == 1 else None


def main() -> None:
    detection = json.loads((OUT / ".graphify_detect.json").read_text(encoding="utf-8"))
    ast = json.loads((OUT / ".graphify_ast.json").read_text(encoding="utf-8"))
    paths = []
    for group in detection["files"].values():
        paths.extend(Path(value) for value in group)

    relative_paths = [rel_path(path) for path in paths]
    known = set(relative_paths)
    allowed_commands = {
        Path(relative).stem
        for relative in relative_paths
        if relative.startswith("NIZAM__system/skills/") and relative.endswith(".md")
    }
    by_name: dict[str, list[str]] = {}
    for relative in relative_paths:
        by_name.setdefault(Path(relative).name.lower(), []).append(relative)
        by_name.setdefault(Path(relative).stem.lower(), []).append(relative)

    nodes: dict[str, dict] = {}
    edges = []
    project = "project_nizam"
    add_node(nodes, {
        "id": project,
        "label": "NIZAM Personal Operating System",
        "file_type": "concept",
        "source_file": "NIZAM_TEMPLE.json",
        "source_location": None,
        "rationale": "Recovery-first, local-first personal operating system.",
    })

    for area, label in AREA_NAMES.items():
        aid = area_id(area)
        add_node(nodes, {
            "id": aid,
            "label": label,
            "file_type": "concept",
            "source_file": None,
            "source_location": None,
        })
        edges.append(edge(project, aid, "has_area", "NIZAM_MASTER_REGISTER.json"))

    for path, relative in zip(paths, relative_paths):
        area = relative.split("/", 1)[0] if "/" in relative else "(root)"
        fid = file_id(relative)
        category = (
            "document"
            if path.suffix.lower() in {".md", ".txt"}
            else "image"
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}
            else "code"
        )
        if category == "image":
            text = ""
        else:
            try:
                text = path.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                text = ""
        add_node(nodes, {
            "id": fid,
            "label": title_for(path, text),
            "file_type": category,
            "source_file": relative,
            "source_location": "L1" if text else None,
        })
        edges.append(edge(area_id(area), fid, "contains_file", relative))

        if category == "document":
            for match in re.finditer(r"(?m)^(#{2,3})\s+(.+?)\s*$", text):
                heading = re.sub(r"[`*_]", "", match.group(2)).strip()
                hid = fid + "_section_" + slug(heading)[:80]
                add_node(nodes, {
                    "id": hid,
                    "label": heading,
                    "file_type": "concept",
                    "source_file": relative,
                    "source_location": f"L{text[:match.start()].count(chr(10)) + 1}",
                })
                edges.append(edge(fid, hid, "contains_section", relative))

        references = []
        references += re.findall(r"\[[^\]]*\]\(([^)]+)\)", text)
        references += re.findall(r"\[\[([^\]|#]+)", text)
        references += re.findall(
            r"(?<![\w.-])([A-Za-z0-9_. -]+(?:/|\\\\)[A-Za-z0-9_./\\\\ -]+\.(?:md|json|jsonl|py|ps1|yaml|yml|txt))",
            text,
        )
        for raw in references:
            target = resolve_reference(path, raw, known, by_name)
            if target and target in known and target != relative:
                edges.append(edge(fid, file_id(target), "references_file", relative))

        commands = set(re.findall(r"(?<![\w/:])/([a-z][a-z0-9-]{2,})", text))
        for command in sorted(commands & allowed_commands):
            sid = "skill_" + slug(command)
            add_node(nodes, {
                "id": sid,
                "label": f"/{command}",
                "file_type": "concept",
                "source_file": relative,
                "source_location": None,
            })
            edges.append(edge(fid, sid, "references_skill", relative))

        upper = text.upper()
        for token, label in MODULE_TOKENS.items():
            if re.search(rf"\b{re.escape(token)}\b", upper):
                target_area = next(
                    (key for key in AREA_NAMES if key.startswith(token + "__")),
                    None,
                )
                if target_area and area_id(target_area) != area_id(area):
                    edges.append(
                        edge(fid, area_id(target_area), "references_module", relative, 0.85)
                    )

    ast_nodes = {node["id"]: node for node in ast["nodes"]}
    for node in ast_nodes.values():
        source = node.get("source_file")
        if source in known:
            edges.append(edge(file_id(source), node["id"], "contains_symbol", source))

    merged_nodes = list(ast_nodes.values())
    for node_id, node in nodes.items():
        if node_id not in ast_nodes:
            merged_nodes.append(node)

    all_ids = {node["id"] for node in merged_nodes}
    for item in ast["edges"]:
        for endpoint in ("source", "target"):
            node_id = item[endpoint]
            if node_id not in all_ids:
                merged_nodes.append({
                    "id": node_id,
                    "label": node_id,
                    "file_type": "concept",
                    "source_file": item.get("source_file"),
                    "source_location": item.get("source_location"),
                })
                all_ids.add(node_id)

    combined = {
        "nodes": merged_nodes,
        "edges": ast["edges"] + edges,
        "hyperedges": [],
        "input_tokens": 0,
        "output_tokens": 0,
    }
    (OUT / ".graphify_extract.json").write_text(
        json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Combined: {len(merged_nodes)} nodes, {len(combined['edges'])} edges")


if __name__ == "__main__":
    main()
