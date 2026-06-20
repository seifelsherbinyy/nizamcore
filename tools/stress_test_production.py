#!/usr/bin/env python3
"""Stress-test NIZAM production capabilities locally and on VPS."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.companion.contracts import ProactiveCandidate  # noqa: E402
from NIZAM__system.companion import badan_import, scheduler  # noqa: E402
from NIZAM__system.connectors import google_oauth  # noqa: E402
from NIZAM__system.relay import env_loader, poller, telemetry  # noqa: E402
from NIZAM__system.relay.persona_runtime import PersonaRuntime, PersonaRuntimeRequest  # noqa: E402
from NIZAM__system.relay.providers import build_provider  # noqa: E402
from tools.nizam_production_status import build_report, telegram_get_me, vps_status  # noqa: E402

VPS = "nizam@31.97.154.5"
REMOTE_ROOT = "/home/nizam/nizamcore"
REMOTE_PY = "/home/nizam/.hermes/hermes-agent/venv/bin/python"


def run_ssh(script: str) -> dict:
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", VPS, script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
    }


def test_local_model() -> dict:
    env_loader.load_all(activate=True)
    provider = build_provider()
    if provider is None:
        return {"ok": False, "reason": "no_provider"}
    try:
        result = PersonaRuntime(provider).run(
            PersonaRuntimeRequest(
                target="Amin",
                input_text="Stress test ping.",
                trace_id="stress-model",
                timeout_seconds=25.0,
            )
        )
        return {"ok": result.status == "ok", **result.to_dict()}
    except (urllib.error.URLError, RuntimeError, TimeoutError) as exc:
        return {"ok": False, "error": type(exc).__name__}


def test_local_oauth() -> dict:
    env_loader.load_all(activate=True)
    if not google_oauth.credentials_available():
        return {"ok": False, "reason": "files_missing"}
    probe = google_oauth.probe_live()
    return {"ok": bool(probe.get("ok")), **probe}


def test_local_telegram_send() -> dict:
    env_loader.load_all(activate=True)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return {"ok": False, "reason": "token_missing"}
    try:
        me = telegram_get_me(token)
        if not me.get("ok"):
            return {"ok": False, "reason": "getMe_failed"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": str(exc)}
    candidate = ProactiveCandidate(
        persona="Amin",
        trigger="stress_test",
        relevance_score=0.99,
        source_refs=("system:stress-test",),
        expires_at="2099-01-01T00:00:00Z",
        message="NIZAM stress test: Telegram send path OK.",
    )
    send = scheduler.send_proactive(candidate)
    return {"ok": bool(send.get("ok")), **send}


def test_local_poll_conflict() -> dict:
    env_loader.load_all(activate=True)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return {"ok": False, "reason": "token_missing", "skipped": True}
    try:
        poller.poll_once(token, 1, send=False)
        return {"ok": True, "mode": "local_poll_available"}
    except poller.GatewayPollingConflict:
        vps = vps_status()
        gateway = "gateway=running" in vps.get("details", [])
        return {
            "ok": gateway,
            "mode": "hermes_gateway_owns_polling",
            "vps_gateway": gateway,
        }


def test_local_import() -> dict:
    fixture = REPO / "NIZAM__system" / "companion" / "tests" / "fixtures" / "whoop-sample.csv"
    if not fixture.exists():
        return {"ok": False, "reason": "fixture_missing"}
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        whoop = badan_import.persist_whoop_export(fixture, badan_dir=Path(tmp) / "badan")
        journal = badan_import.persist_journal_entry(
            title="Stress import",
            body="stress test",
            session_date="2026-06-13",
            journal_dir=Path(tmp) / "journal",
        )
    return {
        "ok": whoop.get("observation_count", 0) > 0 and bool(journal.get("path")),
        "whoop": whoop,
        "journal": journal,
    }


def test_vps_bundle() -> dict:
    script = (
        f"cd {REMOTE_ROOT} && PYTHONPATH={REMOTE_ROOT} {REMOTE_PY} tools/nizam_production_status.py 2>&1 | "
        f"{REMOTE_PY} -c \"import sys,json; d=json.load(sys.stdin); "
        f"print(json.dumps({{'production_ready': d.get('production_ready'), 'live': d.get('live')}}))\""
    )
    status = run_ssh(script)
    pulse = run_ssh(
        f"set -a && source ~/.hermes/.env && set +a && "
        f"{REMOTE_PY} ~/.hermes/scripts/nizam-scheduled-pulse.py | head -3"
    )
    cron = run_ssh("crontab -l 2>/dev/null | grep run_pulsation_loops.py || true")
    pulsation_dry = run_ssh(
        f"cd {REMOTE_ROOT} && PYTHONPATH={REMOTE_ROOT} {REMOTE_PY} "
        f"tools/run_pulsation_loops.py --dry-run --at 2026-06-15T09:00:00+00:00 --loop a 2>&1 | tail -3"
    )
    scheduler_run = run_ssh(
        f"cd {REMOTE_ROOT} && PYTHONPATH={REMOTE_ROOT} {REMOTE_PY} "
        f"tools/run_pulsation_loops.py --dry-run --at 2026-06-15T09:00:00+00:00 --loop a 2>&1 | tail -3"
    )
    return {
        "production_status": status,
        "pulse_script": {"ok": pulse["ok"] and bool(pulse["stdout"]), "lines": len(pulse["stdout"].splitlines())},
        "pulsation_crontab": {"ok": "run_pulsation_loops" in cron["stdout"], "stdout": cron["stdout"]},
        "pulsation_dry_run": pulsation_dry,
        "hourly_scheduler": scheduler_run,
    }


def build_stress_report() -> dict:
    env_loader.load_all(activate=True)
    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tests": {
            "production_status": build_report(),
            "model": test_local_model(),
            "oauth": test_local_oauth(),
            "telemetry": telemetry.export_remote(),
            "telegram_send": test_local_telegram_send(),
            "telegram_poll": test_local_poll_conflict(),
            "personal_import": test_local_import(),
            "vps": test_vps_bundle(),
        },
    }
    critical = {
        "model": report["tests"]["model"]["ok"],
        "oauth": report["tests"]["oauth"]["ok"],
        "telegram_send": report["tests"]["telegram_send"]["ok"],
        "telegram_poll": report["tests"]["telegram_poll"]["ok"],
        "personal_import": report["tests"]["personal_import"]["ok"],
        "local_production": report["tests"]["production_status"]["production_ready"],
        "vps_pulse": report["tests"]["vps"]["pulse_script"]["ok"],
        "vps_cron": report["tests"]["vps"]["pulsation_crontab"]["ok"],
    }
    try:
        vps_live = json.loads(report["tests"]["vps"]["production_status"]["stdout"])
        critical["vps_production"] = bool(vps_live.get("production_ready"))
    except (json.JSONDecodeError, KeyError, TypeError):
        critical["vps_production"] = False
    report["stress_pass"] = all(critical.values())
    report["failures"] = [name for name, ok in critical.items() if not ok]
    return report


def main() -> int:
    report = build_stress_report()
    out = REPO / "install-audit" / "stress-test-report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {
        "stress_pass": report["stress_pass"],
        "failures": report["failures"],
        "live": report["tests"]["production_status"]["live"],
    }
    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {out}", file=sys.stderr)
    return 0 if report["stress_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
