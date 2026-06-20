#!/usr/bin/env python3
"""Production capability status report for NIZAM."""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.companion import badan_import, scheduler  # noqa: E402
from NIZAM__system.companion.contracts import ProactiveCandidate  # noqa: E402
from NIZAM__system.connectors import google_oauth  # noqa: E402
from NIZAM__system.relay import env_loader, poller, telemetry  # noqa: E402
from NIZAM__system.relay.persona_runtime import PersonaRuntime, PersonaRuntimeRequest  # noqa: E402
from NIZAM__system.relay.providers import build_provider  # noqa: E402


VPS = "nizam@31.97.154.5"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def telegram_get_me(token: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/getMe"
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def vps_status() -> dict:
    on_vps = Path("/home/nizam/nizamcore").exists() and Path("/home/nizam/.hermes").exists()
    if on_vps:
        gateway = subprocess.run(
            ["pgrep", "-f", "hermes_cli.main gateway"],
            capture_output=True,
            text=True,
        ).returncode == 0
        env_ok = Path("/home/nizam/.hermes/.env").exists()
        lines = [
            "gateway=running" if gateway else "gateway=stopped",
            "env=ok" if env_ok else "env=missing",
        ]
        return {"ok": gateway and env_ok, "details": lines, "mode": "local"}
    probe = (
        "pgrep -f 'hermes_cli.main gateway' >/dev/null && echo gateway=running || echo gateway=stopped; "
        "test -f ~/.hermes/.env && echo env=ok || echo env=missing"
    )
    try:
        proc = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", VPS, probe],
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        )
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return {"ok": True, "details": lines, "mode": "remote_ssh"}
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc), "mode": "remote_ssh"}


def build_report() -> dict:
    env_loader.load_all(activate=True)
    report: dict = {"generated_at": utc_now(), "capabilities": {}}

    provider = build_provider()
    model_status = {"configured": provider is not None, "provider": getattr(provider, "name", None)}
    if provider is not None:
        try:
            result = PersonaRuntime(provider).run(
                PersonaRuntimeRequest(
                    target="Amin",
                    input_text="Production model smoke test.",
                    trace_id="production-status",
                    timeout_seconds=20.0,
                )
            )
            model_status.update(result.to_dict())
        except (urllib.error.URLError, RuntimeError, TimeoutError) as exc:
            model_status["error"] = type(exc).__name__
    report["capabilities"]["production_model"] = model_status

    oauth_status = {
        "files_present": google_oauth.credentials_available(),
        "write_scopes_ok": google_oauth.scopes_sufficient_for_write(),
        "live_probe": google_oauth.probe_live(),
    }
    report["capabilities"]["oauth_connectors"] = oauth_status

    report["capabilities"]["hostinger_deployment"] = vps_status()

    telemetry_result = telemetry.export_remote()
    report["capabilities"]["remote_telemetry"] = telemetry_result

    candidate = ProactiveCandidate(
        persona="Amin",
        trigger="production_status_check",
        relevance_score=0.95,
        source_refs=("calendar:event:status",),
        expires_at="2099-01-01T00:00:00Z",
        message="NIZAM proactive scheduler smoke test.",
    )
    proactive_eval = scheduler.run_hourly_evaluation(
        [candidate],
        dry_run=True,
        now=datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc),
    )
    token = env_loader.configured("TELEGRAM_BOT_TOKEN")
    if token:
        import os

        try:
            me = telegram_get_me(os.environ["TELEGRAM_BOT_TOKEN"])
            proactive_eval["telegram_get_me"] = bool(me.get("ok"))
        except urllib.error.URLError:
            proactive_eval["telegram_get_me"] = False
    else:
        proactive_eval["telegram_get_me"] = False
    report["capabilities"]["scheduled_telegram"] = proactive_eval

    fixture = REPO / "NIZAM__system" / "companion" / "tests" / "fixtures" / "whoop-sample.csv"
    if not fixture.exists():
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text(
            "date,recovery score,hrv,strain\n2026-06-10,72,48,10.2\n",
            encoding="utf-8",
        )
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        badan_dir = Path(tmp) / "badan"
        personal = badan_import.persist_whoop_export(fixture, badan_dir=badan_dir)
        personal["journal"] = badan_import.persist_journal_entry(
            title="Production import smoke",
            body="Imported during production status check.",
            session_date="2026-06-13",
            journal_dir=Path(tmp) / "journal",
        )
    report["capabilities"]["personal_data_import"] = personal

    telegram_ok = False
    if env_loader.configured("TELEGRAM_BOT_TOKEN"):
        import os

        try:
            me = telegram_get_me(os.environ["TELEGRAM_BOT_TOKEN"])
            telegram_ok = bool(me.get("ok"))
        except urllib.error.URLError:
            telegram_ok = False
    report["live"] = {
        "telegram": telegram_ok,
        "model": model_status.get("status") == "ok",
        "vps_gateway": "gateway=running" in report["capabilities"]["hostinger_deployment"].get("details", []),
        "telemetry": telemetry_result.get("ok", False),
        "oauth": oauth_status["live_probe"].get("ok", False),
    }
    report["production_ready"] = all(
        [
            report["live"]["telegram"],
            report["live"]["model"],
            report["live"]["vps_gateway"],
            report["live"]["telemetry"],
            report["live"]["oauth"],
        ]
    )
    return report


def main() -> int:
    report = build_report()
    out = REPO / "install-audit" / "production-status.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["production_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
