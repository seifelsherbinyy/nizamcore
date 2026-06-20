#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.connectors.health import probe_all  # noqa: E402
from NIZAM__system.companion.knowledge_eval import evaluate as evaluate_companion_knowledge  # noqa: E402
from NIZAM__system.companion.reminders import validate_sourced_reminder  # noqa: E402
from tools.graph_retrieval_benchmark import evaluate, load_benchmark  # noqa: E402


def build_report(graph_path: Path | None = None) -> dict:
    connector_report = probe_all(environ={})
    graph_path = graph_path or REPO / "graphify-out" / "graph.json"
    graph_result = None
    if graph_path.exists():
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        graph_result = evaluate(graph, load_benchmark())
    companion_result = evaluate_companion_knowledge()
    reminder_ok, _ = validate_sourced_reminder(
        "Remember Q2:286 about patience.",
        ("quran-2-286",),
    )
    mode_bundle = REPO / "NIZAM__system" / "modes" / "khaldun_islamic_cosmic_wisdom"
    khaldun_ok = (mode_bundle / "mode_charter.md").exists() and (
        mode_bundle / "khaldun_test_cases.json"
    ).exists()

    local_gates = {
        "canonical_path": (
            (REPO / "NIZAMCORE_PATH.txt").read_text(encoding="utf-8").strip()
            == str(REPO)
        ),
        "dependency_lock": all(
            (REPO / name).exists()
            for name in ("requirements.txt", "requirements-dev.txt")
        ),
        "connectors_contract": all(
            item["state"] == "disabled" for item in connector_report["connectors"]
        ),
        "graph_relevance": bool(graph_result and graph_result["passed"]),
        "companion_knowledge": companion_result["passed"],
        "islamic_reminders": reminder_ok,
        "khaldun_wisdom_mode": khaldun_ok,
    }
    gates = {
        **local_gates,
        "live_model_approved": os.environ.get("NIZAM_LIVE_MODEL_APPROVED") == "1",
        "live_connectors_approved": (
            os.environ.get("NIZAM_LIVE_CONNECTORS_APPROVED") == "1"
        ),
        "deployment_approved": os.environ.get("NIZAM_DEPLOYMENT_APPROVED") == "1",
        "remote_telemetry_approved": (
            os.environ.get("NIZAM_REMOTE_TELEMETRY_APPROVED") == "1"
        ),
    }
    activation_gates = (
        "live_model_approved",
        "live_connectors_approved",
        "deployment_approved",
        "remote_telemetry_approved",
    )
    blockers = [name for name in activation_gates if not gates[name]]
    local_blockers = [name for name, ok in local_gates.items() if not ok]
    return {
        "decision": "GO" if not blockers and all(gates.values()) else "NO_GO",
        "local_decision": "GO" if not local_blockers else "NO_GO",
        "mode": "local_evidence_only",
        "thresholds": {
            "p95_latency_seconds": 15,
            "maximum_error_rate": 0.02,
            "privacy_incidents": 0,
        },
        "local_gates": local_gates,
        "local_blockers": local_blockers,
        "gates": gates,
        "blockers": blockers,
        "connector_summary": connector_report,
        "graph_summary": graph_result,
        "companion_summary": companion_result,
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, indent=2))
    return 0 if report["decision"] == "GO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
