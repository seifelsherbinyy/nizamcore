"""kill_switch.py — NIZAM_KILL_ALL panic stop, with a file-based hard path.

Every writer (ledger_writer, sync_arbiter, telegram-egress, drive-mirror)
MUST call `assert_alive()` before performing its operation.

Two independent signals, OR'd together (either one being "killed" wins):

  1. The env var NIZAM_KILL_ALL=1 — cheap, but lives in
     ~/.hermes/profiles/<profile>/.env, which the running Hermes agent's own
     tool calls can edit. Good for a deliberate, code-driven halt; NOT
     resistant to the same agent un-setting it later.

  2. KILL_SWITCH_FILE (default /etc/nizam/HALT) — its mere *existence*
     means killed, regardless of content. This path lives outside every
     Hermes-profile-writable directory, so an ordinary Hermes turn editing
     its own .env cannot clear it. Removing it requires a deliberate,
     separately-privileged action (root/sudo), which is a materially
     higher bar than a stray .env edit, though NOT a boundary against a
     fully compromised or deliberately malicious host-native session that
     chooses to invoke sudo itself — nothing local can be, once the running
     agent has passwordless sudo on this host. The kill authority that
     survives THAT case is external to this VPS entirely: revoking the
     Slack bot token or OpenRouter key at the provider, or powering off
     the VPS from the hosting console. This file is a tripwire against
     accidents and confused turns, not a defense against a hostile root.

Pure stdlib.
"""
from __future__ import annotations

import os
from pathlib import Path

KILL_SWITCH_FILE = Path(os.environ.get("NIZAM_KILL_SWITCH_FILE", "/etc/nizam/HALT"))


class KillSwitchActive(RuntimeError):
    pass


def _env_killed() -> bool:
    return os.environ.get("NIZAM_KILL_ALL", "") == "1"


def _file_killed(path: Path = KILL_SWITCH_FILE) -> bool:
    try:
        return path.exists()
    except OSError:
        # A path that can't even be stat'd (e.g. a permissions problem on
        # /etc/nizam itself) is treated as an ambiguous state -> fail safe.
        return True


def is_alive(kill_switch_file: Path = KILL_SWITCH_FILE) -> bool:
    return not (_env_killed() or _file_killed(kill_switch_file))


def assert_alive(component: str = "unknown", kill_switch_file: Path = KILL_SWITCH_FILE) -> None:
    if not is_alive(kill_switch_file):
        reason = []
        if _env_killed():
            reason.append("NIZAM_KILL_ALL=1")
        if _file_killed(kill_switch_file):
            reason.append(f"{kill_switch_file} exists")
        raise KillSwitchActive(
            f"Kill switch active ({', '.join(reason)}); {component} refuses to run. "
            f"Unset NIZAM_KILL_ALL and/or remove {kill_switch_file} to resume."
        )


def status(kill_switch_file: Path = KILL_SWITCH_FILE) -> dict:
    return {
        "kill_switch_env": "NIZAM_KILL_ALL",
        "kill_switch_env_value": os.environ.get("NIZAM_KILL_ALL", ""),
        "kill_switch_file": str(kill_switch_file),
        "kill_switch_file_present": _file_killed(kill_switch_file),
        "alive": is_alive(kill_switch_file),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(status(), indent=2))
