#!/usr/bin/env python3
"""Build a lightweight companion module graph for wiring reviews (graphify fallback)."""
from __future__ import annotations

import ast
import json
from pathlib import Path

COMPANION = Path(__file__).resolve().parents[1] / "NIZAM__system" / "companion"
OUT = COMPANION / "graphify-out"
OUT.mkdir(parents=True, exist_ok=True)


def _module_id(path: Path) -> str:
    rel = path.relative_to(COMPANION).with_suffix("")
    return str(rel).replace("\\", "/")


def _scan() -> tuple[list[dict], list[dict]]:
    nodes: list[dict] = []
    edges: list[dict] = []
    seen: set[str] = set()

    for py in sorted(COMPANION.rglob("*.py")):
        if "graphify-out" in py.parts or py.name == "__init__.py":
            continue
        mid = _module_id(py)
        if mid not in seen:
            seen.add(mid)
            nodes.append({"id": mid, "label": mid, "type": "module"})
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("NIZAM__system.companion"):
                        target = alias.name.split(".", 2)[-1]
                        edges.append(
                            {"source": mid, "target": target, "type": "import"}
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith(
                    ("NIZAM__system.companion", ".")
                ):
                    mod = node.module.replace("NIZAM__system.companion.", "")
                    if mod.startswith("."):
                        continue
                    edges.append({"source": mid, "target": mod, "type": "import_from"})

    return nodes, edges


def main() -> int:
    nodes, edges = _scan()
    graph = {"nodes": nodes, "edges": edges, "generator": "companion_graph_baseline"}
    (OUT / "graph.json").write_text(
        json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    report = [
        "# Companion Graph Baseline",
        "",
        f"Modules: {len(nodes)}",
        f"Edges: {len(edges)}",
        "",
        "## Modules",
        "",
    ]
    for n in nodes:
        report.append(f"- {n['id']}")
    (OUT / "GRAPH_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"nodes": len(nodes), "edges": len(edges), "out": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
