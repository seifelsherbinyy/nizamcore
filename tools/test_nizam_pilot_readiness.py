from __future__ import annotations

from tools.nizam_pilot_readiness import build_report


def test_local_readiness_remains_no_go_without_approvals(monkeypatch) -> None:
    for name in (
        "NIZAM_LIVE_MODEL_APPROVED",
        "NIZAM_LIVE_CONNECTORS_APPROVED",
        "NIZAM_DEPLOYMENT_APPROVED",
        "NIZAM_REMOTE_TELEMETRY_APPROVED",
    ):
        monkeypatch.delenv(name, raising=False)
    report = build_report()
    assert report["local_decision"] == "GO"
    assert report["decision"] == "NO_GO"
    assert set(report["blockers"]) == {
        "live_model_approved",
        "live_connectors_approved",
        "deployment_approved",
        "remote_telemetry_approved",
    }
