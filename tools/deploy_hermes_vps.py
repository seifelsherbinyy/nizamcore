#!/usr/bin/env python3
"""Deploy NIZAM Hermes governor plugin and config snapshot to VPS."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VPS = "nizam@31.97.154.5"
REMOTE_HERMES = "/home/nizam/.hermes"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def deploy() -> int:
    plugin = REPO / "NIZAM__system" / "hermes-plugins" / "nizam-governor"
    config = REPO / "NIZAM__system" / "hermes-config" / "config.vps-snapshot.yaml"
    if not plugin.exists():
        print("governor plugin missing", file=sys.stderr)
        return 2
    run(
        [
            "scp",
            "-r",
            str(plugin),
            f"{VPS}:{REMOTE_HERMES}/plugins/nizam-governor",
        ]
    )
    if config.exists():
        run(["scp", str(config), f"{VPS}:{REMOTE_HERMES}/config.nizam-staging.yaml"])
    run(
        [
            "ssh",
            VPS,
            "pgrep -f 'hermes_cli.main gateway' >/dev/null && "
            "kill $(pgrep -f 'hermes_cli.main gateway') || true; "
            "sleep 2; "
            "cd ~/.hermes/hermes-agent && "
            "nohup ./venv/bin/python -m hermes_cli.main gateway run --replace "
            ">/tmp/hermes-gateway.log 2>&1 &",
        ]
    )
    print("deploy complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(deploy())
