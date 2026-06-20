#!/usr/bin/env python3
"""Install Hermes cron jobs on VPS for scheduled Telegram delivery."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VPS = "nizam@31.97.154.5"
REMOTE_HERMES = "/home/nizam/.hermes"
SCRIPT = REPO / "NIZAM__system" / "hermes-config" / "scripts" / "nizam-scheduled-pulse.py"
OAUTH_CLIENT = REPO / "NIZAM__system" / "connectors" / "oauth-client.json"
OAUTH_TOKEN = REPO / "NIZAM__system" / "connectors" / "oauth-token.json"


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )


def ensure_script() -> None:
    run(["ssh", "-o", "BatchMode=yes", VPS, f"mkdir -p {REMOTE_HERMES}/scripts"])
    run(["scp", str(SCRIPT), f"{VPS}:{REMOTE_HERMES}/scripts/nizam-scheduled-pulse.py"])
    run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            f"chmod +x {REMOTE_HERMES}/scripts/nizam-scheduled-pulse.py",
        ]
    )


def sync_oauth_to_vps() -> None:
    remote_conn = f"{REMOTE_HERMES}/connectors"
    run(["ssh", "-o", "BatchMode=yes", VPS, f"mkdir -p {remote_conn}"])
    if OAUTH_CLIENT.exists():
        run(["scp", str(OAUTH_CLIENT), f"{VPS}:{remote_conn}/oauth-client.json"])
    if OAUTH_TOKEN.exists():
        run(["scp", str(OAUTH_TOKEN), f"{VPS}:{remote_conn}/oauth-token.json"])
    append = (
        f"grep -q '^GOOGLE_OAUTH_CLIENT_SECRETS=' {REMOTE_HERMES}/.env 2>/dev/null || "
        f"echo 'GOOGLE_OAUTH_CLIENT_SECRETS={remote_conn}/oauth-client.json' >> {REMOTE_HERMES}/.env; "
        f"grep -q '^GOOGLE_OAUTH_TOKEN=' {REMOTE_HERMES}/.env 2>/dev/null || "
        f"echo 'GOOGLE_OAUTH_TOKEN={remote_conn}/oauth-token.json' >> {REMOTE_HERMES}/.env; "
        f"grep -q '^NIZAM_TIMEZONE=' {REMOTE_HERMES}/.env 2>/dev/null || "
        f"echo 'NIZAM_TIMEZONE=Africa/Cairo' >> {REMOTE_HERMES}/.env"
    )
    run(["ssh", "-o", "BatchMode=yes", VPS, append])


def job_exists(name: str) -> bool:
    proc = run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            f"cd {REMOTE_HERMES}/hermes-agent && "
            "./venv/bin/python -m hermes_cli.main cron list",
        ]
    )
    return name in (proc.stdout or "")


def create_jobs() -> list[str]:
    hermes = f"cd {REMOTE_HERMES}/hermes-agent && ./venv/bin/python -m hermes_cli.main"
    created: list[str] = []
    jobs = [
        (
            "nizam-morning-pulse",
            f'{hermes} cron create --name nizam-morning-pulse --deliver telegram '
            f'--script nizam-scheduled-pulse.py --no-agent '
            f'"0 9 * * *"',
        ),
        (
            "nizam-afternoon-pulse",
            f'{hermes} cron create --name nizam-afternoon-pulse --deliver telegram '
            f'--script nizam-scheduled-pulse.py --no-agent '
            f'"0 15 * * *"',
        ),
        (
            "nizam-evening-pulse",
            f'{hermes} cron create --name nizam-evening-pulse --deliver telegram '
            f'--script nizam-scheduled-pulse.py --no-agent '
            f'"0 21 * * *"',
        ),
    ]
    for name, cmd in jobs:
        if job_exists(name):
            created.append(f"{name}:exists")
            continue
        proc = run(["ssh", "-o", "BatchMode=yes", VPS, cmd], check=False)
        if proc.returncode == 0:
            created.append(f"{name}:created")
        else:
            created.append(f"{name}:failed:{(proc.stderr or proc.stdout)[:120]}")
    return created


def trigger_job(name: str) -> str:
    proc = run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            f"python3 -c \"import json; "
            f"d=json.load(open('{REMOTE_HERMES}/cron/jobs.json')); "
            f"jobs=d if isinstance(d,list) else d.get('jobs',[]); "
            f"print(next((j.get('id','') for j in jobs if j.get('name')=='{name}'), ''))\"",
        ],
        check=False,
    )
    job_id = (proc.stdout or "").strip()
    if not job_id:
        return f"{name}:no_id"
    run_proc = run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            f"cd {REMOTE_HERMES}/hermes-agent && "
            f"./venv/bin/python -m hermes_cli.main cron run {job_id}",
        ],
        check=False,
    )
    if run_proc.returncode == 0:
        return f"{name}:triggered:{job_id}"
    return f"{name}:trigger_failed:{(run_proc.stderr or run_proc.stdout)[:120]}"


def remove_jobs() -> list[str]:
    hermes = f"cd {REMOTE_HERMES}/hermes-agent && ./venv/bin/python -m hermes_cli.main"
    results: list[str] = []
    for name in ("nizam-morning-pulse", "nizam-afternoon-pulse", "nizam-evening-pulse"):
        proc = run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                VPS,
                f"python3 -c \"import json; "
                f"d=json.load(open('{REMOTE_HERMES}/cron/jobs.json')); "
                f"jobs=d if isinstance(d,list) else d.get('jobs',[]); "
                f"print(next((j.get('id','') for j in jobs if j.get('name')=='{name}'), ''))\"",
            ],
            check=False,
        )
        job_id = (proc.stdout or "").strip()
        if not job_id:
            results.append(f"{name}:missing")
            continue
        delete = run(
            ["ssh", "-o", "BatchMode=yes", VPS, f"{hermes} cron delete {job_id}"],
            check=False,
        )
        if delete.returncode == 0:
            results.append(f"{name}:removed:{job_id}")
        else:
            results.append(
                f"{name}:failed:{(delete.stderr or delete.stdout)[:120]}"
            )
    return results


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Install or remove Hermes scheduled Telegram pulse jobs"
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove nizam-morning/afternoon/evening-pulse Hermes cron jobs",
    )
    args = parser.parse_args()

    if args.remove:
        results = remove_jobs()
        print("removed:", results)
        return 0

    ensure_script()
    sync_oauth_to_vps()
    results = create_jobs()
    trigger = trigger_job("nizam-morning-pulse")
    print("jobs:", results)
    print("trigger:", trigger)
    list_proc = run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            f"cd {REMOTE_HERMES}/hermes-agent && ./venv/bin/python -m hermes_cli.main cron list",
        ]
    )
    status_proc = run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            f"cd {REMOTE_HERMES}/hermes-agent && ./venv/bin/python -m hermes_cli.main cron status",
        ]
    )
    out = REPO / "install-audit" / "hermes-schedule-status.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f"jobs: {results}\ntrigger: {trigger}\n\n{list_proc.stdout}\n{status_proc.stdout}",
        encoding="utf-8",
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
