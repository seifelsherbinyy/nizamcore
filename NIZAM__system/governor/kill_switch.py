"""kill_switch.py — NIZAM_KILL_ALL=1 panic stop.

Every writer (ledger_writer, sync_arbiter, telegram-egress, drive-mirror)
MUST call `assert_alive()` before performing its operation. The check is
cheap (env var lookup).

Pure stdlib.
"""
from __future__ import annotations

import os


class KillSwitchActive(RuntimeError):
    pass


def is_alive() -> bool:
    return os.environ.get("NIZAM_KILL_ALL", "") != "1"


def assert_alive(component: str = "unknown") -> None:
    if not is_alive():
        raise KillSwitchActive(
            f"NIZAM_KILL_ALL=1 is set; {component} refuses to run. "
            f"Set NIZAM_KILL_ALL=0 (or unset) to resume."
        )


def status() -> dict:
    return {
        "kill_switch_env": "NIZAM_KILL_ALL",
        "kill_switch_value": os.environ.get("NIZAM_KILL_ALL", ""),
        "alive": is_alive(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(status(), indent=2))
