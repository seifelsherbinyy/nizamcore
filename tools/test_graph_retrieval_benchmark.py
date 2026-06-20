from __future__ import annotations

from tools.graph_retrieval_benchmark import evaluate, rank_sources


def test_generic_schema_nodes_are_downweighted() -> None:
    graph = {
        "nodes": [
            {
                "label": "type enum properties required schema",
                "source_file": "schemas/generic.json",
            },
            {
                "label": "HIMAYAH privacy egress firewall",
                "source_file": "governor/classifier.py",
            },
        ]
    }
    ranked = rank_sources(
        graph,
        "How does HIMAYAH privacy egress work?",
        aliases={"himayah": ["privacy", "egress", "firewall"]},
        generic_terms={"type", "enum", "properties", "required", "schema"},
    )
    assert ranked[0]["source_file"] == "governor/classifier.py"


def test_evaluation_calculates_hit_rate_and_mrr() -> None:
    graph = {
        "nodes": [
            {"label": "canonical path", "source_file": "AGENTS.md"},
            {"label": "relay coordinator stub", "source_file": "relay/coordinator.py"},
        ]
    }
    benchmark = {
        "top_k": 5,
        "minimum_mrr": 0.6,
        "aliases": {},
        "generic_terms": [],
        "benchmarks": [
            {
                "id": "path",
                "question": "canonical path",
                "expected_sources": ["AGENTS.md"],
            },
            {
                "id": "relay",
                "question": "relay stub",
                "expected_sources": ["relay/coordinator.py"],
            },
        ],
    }
    result = evaluate(graph, benchmark)
    assert result["hit_rate"] == 1.0
    assert result["mrr"] == 1.0
    assert result["passed"] is True
