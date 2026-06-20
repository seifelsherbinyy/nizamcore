#!/usr/bin/env python3
"""Run production completion verification gate and write go-live receipt."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PY = sys.executable


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_cmd(label: str, cmd: list[str]) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=str(REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "label": label,
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-1000:],
    }


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    steps: list[dict] = []

    steps.append(
        run_cmd(
            "verify_nizamcore",
            ["powershell", "-NoProfile", "-File", str(REPO / "scripts" / "verify-nizamcore.ps1")],
        )
    )
    steps.append(run_cmd("production_status", [PY, str(REPO / "tools" / "nizam_production_status.py")]))
    steps.append(run_cmd("audit_vps_wiring", [PY, str(REPO / "tools" / "audit_vps_wiring.py")]))
    steps.append(run_cmd("stress_test", [PY, str(REPO / "tools" / "stress_test_production.py")]))
    steps.append(
        run_cmd(
            "persona_matrix_telegram",
            [PY, str(REPO / "tools" / "persona_blurb_matrix.py"), "--telegram-from-report"],
        )
    )

    production = load_json(REPO / "install-audit" / "production-status.json")
    audit = load_json(REPO / "install-audit" / "vps-wiring-audit.json")

    audit_checks = audit.get("checks") or {}
    oauth_live = bool(audit_checks.get("oauth_live"))
    oauth_write_smoke = bool(audit_checks.get("oauth_write_smoke"))
    production_ready = bool(production.get("production_ready"))
    gateway_running = bool(audit_checks.get("hermes_gateway"))
    wiring_pass = bool(audit.get("wiring_pass"))
    all_steps_pass = all(step["passed"] for step in steps)

    receipt = {
        "generated_at": utc_now(),
        "steps": steps,
        "production_status": {
            "production_ready": production_ready,
            "oauth": production.get("live", {}).get("oauth"),
        },
        "vps_wiring": {
            "wiring_pass": wiring_pass,
            "oauth_live": oauth_live,
            "oauth_write_smoke": oauth_write_smoke,
            "gateway_running": gateway_running,
            "failures": audit.get("failures", []),
        },
        "completion_ready": all_steps_pass
        and production_ready
        and oauth_live
        and oauth_write_smoke
        and wiring_pass,
    }

    out = REPO / "install-audit" / "go-live-completion.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["completion_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
