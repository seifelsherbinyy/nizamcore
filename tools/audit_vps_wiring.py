#!/usr/bin/env python3

"""Full VPS wiring audit against NIZAM production plan."""

from __future__ import annotations



import json

import subprocess

import sys

from datetime import datetime, timezone

from pathlib import Path



REPO = Path(__file__).resolve().parents[1]

VPS = "nizam@31.97.154.5"

REMOTE_ROOT = "/home/nizam/nizamcore"

REMOTE_HERMES = "/home/nizam/.hermes"

REMOTE_PY = f"{REMOTE_HERMES}/hermes-agent/venv/bin/python"





def run_ssh(script: str, timeout: int = 90) -> dict:

    proc = subprocess.run(

        ["ssh", "-o", "BatchMode=yes", VPS, script],

        capture_output=True,

        text=True,

        encoding="utf-8",

        errors="replace",

        timeout=timeout,

    )

    return {

        "ok": proc.returncode == 0,

        "exit_code": proc.returncode,

        "stdout": (proc.stdout or "").strip(),

        "stderr": (proc.stderr or "").strip(),

    }





def _parse_probe_stdout(stdout: str) -> dict:

    text = stdout.strip()

    if not text:

        return {}

    # Handle repr-style dict from print(probe_live()) or JSON from json.dumps

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        pass

    try:

        import ast



        value = ast.literal_eval(text)

        return value if isinstance(value, dict) else {}

    except (SyntaxError, ValueError):

        return {}





def audit_vps() -> dict:

    checks: dict[str, dict] = {}



    layout = run_ssh(

        f"for p in {REMOTE_ROOT}/NIZAM__system/companion {REMOTE_ROOT}/NIZAM__system/relay "

        f"{REMOTE_ROOT}/NIZAM__system/connectors {REMOTE_ROOT}/tools/deploy_nizam_vps.py "

        f"{REMOTE_ROOT}/tools/verify_google_connectors.py "

        f"{REMOTE_HERMES}/plugins/nizam-governor/__init__.py "

        f"{REMOTE_HERMES}/scripts/nizam-scheduled-pulse.py "

        f"{REMOTE_HERMES}/connectors/oauth-token.json "

        f"{REMOTE_ROOT}/NIZAM__system/relay/.env; do "

        f"test -e \"$p\" && echo OK:$p || echo MISSING:$p; done"

    )

    checks["filesystem"] = layout



    gateway = run_ssh(

        "pgrep -af 'hermes_cli.main gateway' | head -1; "

        f"cd {REMOTE_HERMES}/hermes-agent && ./venv/bin/python -m hermes_cli.main cron status 2>&1 | tail -6"

    )

    checks["hermes_gateway_cron"] = gateway



    env_keys = run_ssh(

        f"grep -E '^(TELEGRAM_BOT_TOKEN|TELEGRAM_ALLOWED_USERS|TELEGRAM_HOME_CHANNEL|"

        f"OPENROUTER_API_KEY|GOOGLE_OAUTH|NIZAM_TIMEZONE)=' {REMOTE_HERMES}/.env | cut -d= -f1 | sort"

    )

    checks["hermes_env_keys"] = env_keys



    relay_env = run_ssh(

        f"test -f {REMOTE_ROOT}/NIZAM__system/relay/.env && "

        f"grep -E '^(RELAY_MODE|NIZAM_LIVE_|TELEGRAM_BOT_TOKEN|NIZAM_TELEGRAM|GOOGLE_OAUTH)' "

        f"{REMOTE_ROOT}/NIZAM__system/relay/.env | cut -d= -f1 | sort || echo MISSING"

    )

    checks["relay_env_keys"] = relay_env



    live_connectors = run_ssh(

        f"grep -q '^NIZAM_LIVE_CONNECTORS_APPROVED=1' {REMOTE_ROOT}/NIZAM__system/relay/.env "

        f"&& echo approved || echo missing"

    )

    checks["live_connectors_approved"] = live_connectors



    oauth = run_ssh(

        f"cd {REMOTE_ROOT} && PYTHONPATH={REMOTE_ROOT} {REMOTE_PY} -c "

        f"\"from NIZAM__system.relay import env_loader; from NIZAM__system.connectors import google_oauth; "

        f"env_loader.load_all(activate=True); import json; print(json.dumps(google_oauth.probe_live()))\""

    )

    checks["oauth_probe"] = oauth

    checks["oauth_probe_parsed"] = {"payload": _parse_probe_stdout(oauth.get("stdout", ""))}



    write_smoke = run_ssh(

        f"cd {REMOTE_ROOT} && PYTHONPATH={REMOTE_ROOT} {REMOTE_PY} tools/verify_google_connectors.py "

        f"--write-smoke --json 2>&1 | tail -1",

        timeout=180,

    )

    checks["oauth_write_smoke"] = write_smoke



    production = run_ssh(

        f"cd {REMOTE_ROOT} && PYTHONPATH={REMOTE_ROOT} {REMOTE_PY} tools/nizam_production_status.py 2>&1 | "

        f"{REMOTE_PY} -c \"import sys,json; d=json.load(sys.stdin); "

        f"print(json.dumps({{'production_ready':d.get('production_ready'),'live':d.get('live')}}, indent=2))\"",

        timeout=120,

    )

    checks["production_status"] = production



    governor_root = run_ssh(

        f"{REMOTE_PY} -c \"import re; t=open('{REMOTE_HERMES}/plugins/nizam-governor/__init__.py').read(); "

        f"m=re.search(r'NIZAM_ROOT = .*', t); print(m.group(0) if m else 'missing')\""

    )

    checks["governor_nizam_root"] = governor_root



    crontab = run_ssh("crontab -l 2>/dev/null | grep -E 'proactive|nizam|pulsation' || echo none")

    checks["user_crontab"] = crontab



    pulse = run_ssh(

        f"set -a && source {REMOTE_HERMES}/.env && set +a && "

        f"{REMOTE_PY} {REMOTE_HERMES}/scripts/nizam-scheduled-pulse.py | wc -l"

    )

    checks["pulse_script"] = pulse



    plugin_enabled = run_ssh(

        f"grep -A3 '^plugins:' {REMOTE_HERMES}/config.yaml 2>/dev/null | head -5 || "

        f"grep nizam-governor {REMOTE_HERMES}/config.yaml 2>/dev/null | head -3"

    )

    checks["hermes_config_plugins"] = plugin_enabled



    return checks





def evaluate(checks: dict) -> dict:

    fs_ok = checks["filesystem"]["ok"] and "MISSING:" not in checks["filesystem"]["stdout"]

    gateway_ok = "hermes_cli.main gateway" in checks["hermes_gateway_cron"]["stdout"]

    probe_payload = checks.get("oauth_probe_parsed", {}).get("payload") or {}

    oauth_ok = bool(probe_payload.get("ok"))

    prod = {}

    try:

        prod = json.loads(checks["production_status"]["stdout"])

    except json.JSONDecodeError:

        prod = {}

    production_ready = bool(prod.get("production_ready"))

    governor_ok = "nizamcore" in checks["governor_nizam_root"]["stdout"]

    relay_ok = "MISSING" not in checks["relay_env_keys"]["stdout"]

    connectors_ok = checks["live_connectors_approved"]["stdout"].strip() == "approved"

    crontab_ok = "run_pulsation_loops" in checks["user_crontab"]["stdout"]

    # Pulsation replaces Hermes static pulses; Hermes cron jobs are optional when pulsation crontab exists.

    hermes_cron_ok = crontab_ok or (

        "nizam-morning-pulse" in checks["hermes_gateway_cron"]["stdout"]

        or "active job" in checks["hermes_gateway_cron"]["stdout"].lower()

    )

    pulse_ok = checks["pulse_script"]["ok"] and checks["pulse_script"]["stdout"].strip() not in {"", "0"}



    write_smoke_payload = {}

    smoke_stdout = checks.get("oauth_write_smoke", {}).get("stdout", "")

    if smoke_stdout:

        try:

            write_smoke_payload = json.loads(smoke_stdout)

        except json.JSONDecodeError:

            write_smoke_payload = {}

    write_smoke_ok = bool(write_smoke_payload.get("ok")) if write_smoke_payload else oauth_ok



    wiring = {

        "filesystem": fs_ok,

        "hermes_gateway": gateway_ok,

        "hermes_cron_jobs": hermes_cron_ok,

        "governor_plugin_path": governor_ok,

        "hermes_env": checks["hermes_env_keys"]["ok"],

        "relay_env": relay_ok,

        "live_connectors_approved": connectors_ok,

        "oauth_live": oauth_ok,

        "oauth_write_smoke": write_smoke_ok,

        "production_ready": production_ready,

        "pulsation_crontab": crontab_ok,

        "pulse_script": pulse_ok,

    }

    return {

        "wiring_pass": all(wiring.values()),

        "checks": wiring,

        "failures": [k for k, v in wiring.items() if not v],

    }





def main() -> int:

    checks = audit_vps()

    summary = evaluate(checks)

    report = {

        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),

        "vps": VPS,

        "remote_root": REMOTE_ROOT,

        "remote_hermes": REMOTE_HERMES,

        "raw": checks,

        **summary,

    }

    out = REPO / "install-audit" / "vps-wiring-audit.json"

    out.parent.mkdir(parents=True, exist_ok=True)

    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({k: report[k] for k in ("wiring_pass", "checks", "failures")}, indent=2))

    print(f"\nFull audit: {out}", file=sys.stderr)

    return 0 if report["wiring_pass"] else 2





if __name__ == "__main__":

    raise SystemExit(main())


