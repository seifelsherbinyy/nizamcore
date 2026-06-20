#!/usr/bin/env python3
"""Sync production env vars from the live VPS into local relay .env (gitignored)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RELAY_ENV = REPO / "NIZAM__system" / "relay" / ".env"
VPS = "nizam@31.97.154.5"
REMOTE_ENV = "~/.hermes/.env"

LOCAL_MAP = {
    "TELEGRAM_BOT_TOKEN": "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_ALLOWED_USERS": "NIZAM_TELEGRAM_ALLOWED_IDS",
    "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY": "OPENAI_API_KEY",
}


def _remote_env() -> dict[str, str]:
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", VPS, f"cat {REMOTE_ENV}"],
        capture_output=True,
        text=True,
        check=True,
    )
    values: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def sync() -> Path:
    remote = _remote_env()
    lines = [
        "# Synced from VPS ~/.hermes/.env — do not commit",
        "RELAY_MODE=live",
        "NIZAM_REAL_PERSONA_RUNTIME=1",
        "NIZAM_LIVE_MODEL_APPROVED=1",
        "NIZAM_LIVE_CONNECTORS_APPROVED=1",
        "NIZAM_DEPLOYMENT_APPROVED=1",
        "NIZAM_REMOTE_TELEMETRY_APPROVED=1",
        "",
    ]
    for remote_key, local_key in LOCAL_MAP.items():
        value = remote.get(remote_key, "")
        if value:
            lines.append(f"{local_key}={value}")
    RELAY_ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return RELAY_ENV


def main() -> int:
    try:
        path = sync()
    except subprocess.CalledProcessError as exc:
        print(f"sync failed: {exc.stderr or exc.stdout}", file=sys.stderr)
        return 2
    print(f"synced production env to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
