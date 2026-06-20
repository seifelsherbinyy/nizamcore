#!/usr/bin/env python3
"""Deploy latest NIZAM staging tree to Hostinger VPS for Hermes operation.

Recommended deploy with progress logging (PowerShell):

    $env:PYTHONUNBUFFERED='1'
    D:\\NIZAM\\.venv\\Scripts\\python.exe D:\\NIZAM\\tools\\deploy_nizam_vps.py 2>&1 |
      Tee-Object D:\\NIZAM\\install-audit\\vps-deploy-last.log

Verify-only (no tarball upload):

    D:\\NIZAM\\.venv\\Scripts\\python.exe D:\\NIZAM\\tools\\deploy_nizam_vps.py --verify-only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VPS = "nizam@31.97.154.5"
REMOTE_ROOT = "/home/nizam/nizamcore"
REMOTE_HERMES = "/home/nizam/.hermes"
HERMES_VENV = f"{REMOTE_HERMES}/hermes-agent/venv"
REMOTE_PY = f"{HERMES_VENV}/bin/python"

SYNC_TOP_LEVEL = (
    "NIZAM__system",
    "tools",
    "scripts",
    "requirements.txt",
    "HIFZ__github_version_control/requirements-governor.txt",
    "CRITICAL_FACTS.md",
    "NIZAM_TEMPLE.json",
    "AGENTS.md",
)

SYNC_OPTIONAL = ("SOUL.md", "user.md")

EXCLUDE_DIR_NAMES = {
    ".venv",
    ".git",
    "__pycache__",
    "graphify-out",
    "install-audit",
    "hermes-venv",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
}

EXCLUDE_FILE_NAMES = {
    ".env",
    "oauth-token.json",
    "oauth-client.json",
    "NIZAM-secrets.json",
    "nizam-prod-oauthclient.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(stage: str, detail: str = "") -> None:
    msg = f"[deploy] {stage}"
    if detail:
        msg = f"{msg}: {detail}"
    print(msg, flush=True)


def run(
    cmd: list[str],
    *,
    check: bool = True,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[str | bytes]:
    return subprocess.run(
        cmd,
        input=input_bytes,
        capture_output=True,
        check=check,
        text=input_bytes is None,
        encoding=None if input_bytes is not None else "utf-8",
        errors="replace",
    )


def should_skip(path: Path) -> bool:
    rel = path.relative_to(REPO)
    for part in rel.parts:
        if part in EXCLUDE_DIR_NAMES:
            return True
    if path.name in EXCLUDE_FILE_NAMES:
        return True
    if path.suffix in {".pyc", ".pyo"}:
        return True
    return False


def build_archive() -> Path:
    log("build_archive", "start")
    tmp = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
    tmp.close()
    archive = Path(tmp.name)
    with tarfile.open(archive, "w:gz") as tar:
        for rel in SYNC_TOP_LEVEL:
            src = REPO / rel
            if not src.exists():
                continue
            if src.is_file():
                tar.add(src, arcname=rel)
                continue
            for path in src.rglob("*"):
                if path.is_dir():
                    continue
                if should_skip(path):
                    continue
                tar.add(path, arcname=str(path.relative_to(REPO)).replace("\\", "/"))
        for rel in SYNC_OPTIONAL:
            src = REPO / rel
            if src.exists() and src.is_file():
                tar.add(src, arcname=rel)
    log("build_archive", f"done size={archive.stat().st_size}")
    return archive


def upload_and_extract(archive: Path) -> None:
    remote_tar = "/tmp/nizam-deploy.tgz"
    log("scp", remote_tar)
    run(["scp", str(archive), f"{VPS}:{remote_tar}"])
    log("extract", REMOTE_ROOT)
    run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            f"mkdir -p {REMOTE_ROOT} && "
            f"tar -xzf {remote_tar} -C {REMOTE_ROOT} && "
            f"rm -f {remote_tar}",
        ]
    )


def remote_post_install() -> str:
    log("post_install", "start")
    script = f"""
set -e
mkdir -p {REMOTE_ROOT}/NIZAM__system/connectors {REMOTE_ROOT}/NIZAM__system/relay/.state {REMOTE_HERMES}/connectors {REMOTE_HERMES}/scripts
ln -sf {REMOTE_HERMES}/connectors/oauth-client.json {REMOTE_ROOT}/NIZAM__system/connectors/oauth-client.json
ln -sf {REMOTE_HERMES}/connectors/oauth-token.json {REMOTE_ROOT}/NIZAM__system/connectors/oauth-token.json
if [ ! -x {REMOTE_PY} ]; then echo 'hermes venv missing' >&2; exit 1; fi
{REMOTE_PY} -m pip install -q --upgrade pip
{REMOTE_PY} -m pip install -q python-dotenv google-api-python-client google-auth-oauthlib google-auth-httplib2
grep -q '^GOOGLE_OAUTH_CLIENT_SECRETS=' {REMOTE_HERMES}/.env 2>/dev/null || echo 'GOOGLE_OAUTH_CLIENT_SECRETS={REMOTE_HERMES}/connectors/oauth-client.json' >> {REMOTE_HERMES}/.env
grep -q '^GOOGLE_OAUTH_TOKEN=' {REMOTE_HERMES}/.env 2>/dev/null || echo 'GOOGLE_OAUTH_TOKEN={REMOTE_HERMES}/connectors/oauth-token.json' >> {REMOTE_HERMES}/.env
grep -q '^NIZAM_TIMEZONE=' {REMOTE_HERMES}/.env 2>/dev/null || echo 'NIZAM_TIMEZONE=Africa/Cairo' >> {REMOTE_HERMES}/.env
grep -q '^NIZAM_KHALDUN_OUTBOUND_APPROVED=' {REMOTE_HERMES}/.env 2>/dev/null || echo 'NIZAM_KHALDUN_OUTBOUND_APPROVED=1' >> {REMOTE_HERMES}/.env
{REMOTE_PY} - <<'PY'
import os
from pathlib import Path
from dotenv import dotenv_values
hermes = Path("{REMOTE_HERMES}/.env")
relay = Path("{REMOTE_ROOT}/NIZAM__system/relay/.env")
vals = dotenv_values(hermes)
lines = [
    "RELAY_MODE=live",
    "NIZAM_REAL_PERSONA_RUNTIME=1",
    "NIZAM_LIVE_MODEL_APPROVED=1",
    "NIZAM_LIVE_CONNECTORS_APPROVED=1",
    "NIZAM_DEPLOYMENT_APPROVED=1",
    "NIZAM_REMOTE_TELEMETRY_APPROVED=1",
    "NIZAM_KHALDUN_OUTBOUND_APPROVED=1",
]
mapping = {{
    "TELEGRAM_BOT_TOKEN": "TELEGRAM_BOT_TOKEN",
    "NIZAM_TELEGRAM_ALLOWED_IDS": "TELEGRAM_ALLOWED_USERS",
    "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
    "GOOGLE_OAUTH_CLIENT_SECRETS": "GOOGLE_OAUTH_CLIENT_SECRETS",
    "GOOGLE_OAUTH_TOKEN": "GOOGLE_OAUTH_TOKEN",
    "TELEGRAM_HOME_CHANNEL": "TELEGRAM_HOME_CHANNEL",
    "NIZAM_KHALDUN_OUTBOUND_APPROVED": "NIZAM_KHALDUN_OUTBOUND_APPROVED",
}}
for local, remote in mapping.items():
    value = vals.get(remote) or vals.get(local) or ""
    if value:
        lines.append(f"{{local}}={{value}}")
relay.parent.mkdir(parents=True, exist_ok=True)
relay.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
relay.chmod(0o600)
PY
test -f {REMOTE_ROOT}/SOUL.md && cp {REMOTE_ROOT}/SOUL.md {REMOTE_HERMES}/SOUL.md || true
test -f {REMOTE_ROOT}/user.md && cp {REMOTE_ROOT}/user.md {REMOTE_HERMES}/user.md || true
( (crontab -l 2>/dev/null || true) | grep -v 'run_proactive_scheduler.py' | grep -v 'run_pulsation_loops.py'; echo '*/15 * * * * cd {REMOTE_ROOT} && PYTHONPATH={REMOTE_ROOT} {REMOTE_PY} tools/run_pulsation_loops.py >> {REMOTE_HERMES}/nizam-scheduler.log 2>&1') | crontab -
echo OK
"""
    proc = run(["ssh", "-o", "BatchMode=yes", VPS, script], check=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "post_install failed").strip())
    log("post_install", "done")
    return (proc.stdout or "").strip()


def deploy_hermes_plugin() -> None:
    log("hermes_plugin", "start")
    plugin = REPO / "NIZAM__system" / "hermes-plugins" / "nizam-governor"
    run(["ssh", "-o", "BatchMode=yes", VPS, f"rm -rf {REMOTE_HERMES}/plugins/nizam-governor"])
    run(["scp", "-r", str(plugin), f"{VPS}:{REMOTE_HERMES}/plugins/nizam-governor"])
    config = REPO / "NIZAM__system" / "hermes-config" / "config.vps-snapshot.yaml"
    if config.exists():
        run(["scp", str(config), f"{VPS}:{REMOTE_HERMES}/config.nizam-staging.yaml"])
    pulse = REPO / "NIZAM__system" / "hermes-config" / "scripts" / "nizam-scheduled-pulse.py"
    if pulse.exists():
        run(["scp", str(pulse), f"{VPS}:{REMOTE_HERMES}/scripts/nizam-scheduled-pulse.py"])
        run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                VPS,
                f"chmod +x {REMOTE_HERMES}/scripts/nizam-scheduled-pulse.py",
            ]
        )
    log("hermes_plugin", "done")


def ensure_pulsation_crontab() -> None:
    log("pulsation_crontab", "start")
    line = (
        f"*/15 * * * * cd {REMOTE_ROOT} && PYTHONPATH={REMOTE_ROOT} "
        f"{REMOTE_PY} tools/run_pulsation_loops.py >> {REMOTE_HERMES}/nizam-scheduler.log 2>&1"
    )
    run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            f"( (crontab -l 2>/dev/null || true) | grep -v 'run_proactive_scheduler.py' | "
            f"grep -v 'run_pulsation_loops.py'; echo '{line}') | crontab -",
        ]
    )
    log("pulsation_crontab", "done")


def sync_oauth() -> None:
    log("sync_oauth", "start")
    client = REPO / "NIZAM__system" / "connectors" / "oauth-client.json"
    token = REPO / "NIZAM__system" / "connectors" / "oauth-token.json"
    run(["ssh", "-o", "BatchMode=yes", VPS, f"mkdir -p {REMOTE_HERMES}/connectors"])
    if client.exists():
        run(["scp", str(client), f"{VPS}:{REMOTE_HERMES}/connectors/oauth-client.json"])
    if token.exists():
        run(["scp", str(token), f"{VPS}:{REMOTE_HERMES}/connectors/oauth-token.json"])
    log("sync_oauth", "done")


def restart_gateway() -> str:
    log("restart_gateway", "start")
    proc = run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            "pgrep -f 'hermes_cli.main gateway' >/dev/null && "
            "kill $(pgrep -f 'hermes_cli.main gateway') || true; "
            "sleep 2; "
            "cd ~/.hermes/hermes-agent && "
            "nohup ./venv/bin/python -m hermes_cli.main gateway run --replace "
            ">/tmp/hermes-gateway.log 2>&1 & "
            "sleep 2; "
            "pgrep -af 'hermes_cli.main gateway' | head -1",
        ],
        check=False,
    )
    log("restart_gateway", "done")
    return (proc.stdout or proc.stderr or "").strip()


def verify_remote() -> dict:
    log("verify_remote", "start")
    proc = run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            f"test -d {REMOTE_ROOT}/NIZAM__system/companion && echo companion=ok || echo companion=missing; "
            f"test -d {REMOTE_ROOT}/NIZAM__system/relay && echo relay=ok || echo relay=missing; "
            f"test -f {REMOTE_HERMES}/plugins/nizam-governor/__init__.py && echo governor=ok || echo governor=missing; "
            f"pgrep -f 'hermes_cli.main gateway' >/dev/null && echo gateway=running || echo gateway=stopped; "
            f"grep -q '^NIZAM_KHALDUN_OUTBOUND_APPROVED=1' {REMOTE_HERMES}/.env 2>/dev/null && echo khaldun_outbound=approved || echo khaldun_outbound=missing; "
            f"cd {REMOTE_HERMES}/hermes-agent && ./venv/bin/python -m hermes_cli.main cron status 2>/dev/null | tail -3",
        ],
        check=False,
    )
    lines = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    log("verify_remote", f"lines={len(lines)}")
    return {"lines": lines, "raw": proc.stdout or ""}


def verify_only() -> dict:
    verify = verify_remote()
    gateway_proc = run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            "pgrep -af 'hermes_cli.main gateway' | head -1",
        ],
        check=False,
    )
    receipt = {
        "mode": "verify_only",
        "checked_at": utc_now(),
        "gateway": (gateway_proc.stdout or gateway_proc.stderr or "").strip(),
        "verify": verify,
    }
    out = REPO / "install-audit" / "vps-deploy-receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def deploy() -> dict:
    log("deploy", "start")
    archive = build_archive()
    try:
        upload_and_extract(archive)
    finally:
        archive.unlink(missing_ok=True)
    sync_oauth()
    post = remote_post_install()
    deploy_hermes_plugin()
    gateway = restart_gateway()
    log("scheduled_setup", "start")
    setup = run(
        [sys.executable, str(REPO / "tools" / "setup_hermes_scheduled_telegram.py"), "--remove"],
        check=False,
    )
    log("scheduled_setup", f"exit={setup.returncode} (remove Hermes pulses)")
    ensure_pulsation_crontab()
    crontab_proc = run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            "crontab -l 2>/dev/null | grep run_pulsation_loops.py || true",
        ],
        check=False,
    )
    if "run_pulsation_loops.py" not in (crontab_proc.stdout or ""):
        raise RuntimeError("pulsation crontab missing after ensure_pulsation_crontab")
    log("pulsation_crontab", "verified")
    oauth_probe = run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            VPS,
            f"cd {REMOTE_ROOT} && PYTHONPATH={REMOTE_ROOT} {REMOTE_PY} -c "
            f"\"from NIZAM__system.relay import env_loader; from NIZAM__system.connectors import google_oauth; "
            f"env_loader.load_all(activate=True); import json; print(json.dumps(google_oauth.probe_live()))\"",
        ],
        check=False,
    )
    verify = verify_remote()
    receipt = {
        "deployed_at": utc_now(),
        "remote_root": REMOTE_ROOT,
        "remote_hermes": REMOTE_HERMES,
        "post_install": post,
        "gateway": gateway,
        "scheduled_setup_exit": setup.returncode,
        "oauth_probe_stdout": (oauth_probe.stdout or oauth_probe.stderr or "").strip(),
        "verify": verify,
        "local_head": run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], check=False).stdout.strip(),
        "local_branch": run(["git", "-C", str(REPO), "branch", "--show-current"], check=False).stdout.strip(),
    }
    out = REPO / "install-audit" / "vps-deploy-receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    log("deploy", "complete")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy NIZAM to Hostinger VPS")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Skip tarball upload; run verify_remote and gateway check only",
    )
    args = parser.parse_args()
    receipt = verify_only() if args.verify_only else deploy()
    print(json.dumps(receipt, indent=2))
    ok = "companion=ok" in receipt["verify"]["lines"] and "gateway=running" in receipt["verify"]["lines"]
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
