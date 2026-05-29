"""dedup.py — Telegram update_id dedup table (B4.3).

Idempotent storage of seen update_ids. On crash, the relay resumes from
the highest known update_id; replays from Telegram do not double-fire any
downstream action.

State file: `NIZAM__system/relay/.state/update_ids.json` (gitignored).
Bounded ring: keep last N=8192 update_ids to bound memory.

Pure stdlib.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

STATE_DIR = Path(__file__).resolve().parent / ".state"
STATE_FILE = STATE_DIR / "update_ids.json"
MAX_ENTRIES = 8192


def _load() -> dict:
    if not STATE_FILE.exists():
        return {"seen": [], "max_seen": -1}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"seen": [], "max_seen": -1}


def _save(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        os.replace(tmp, STATE_FILE)
    except OSError:
        # Fallback for FS where replace can fail
        tmp.rename(STATE_FILE)


def already_seen(update_id: int) -> bool:
    state = _load()
    return update_id in state["seen"]


def record(update_id: int) -> bool:
    """Returns True if this update_id is new; False if duplicate."""
    state = _load()
    if update_id in state["seen"]:
        return False
    state["seen"].append(update_id)
    if update_id > state.get("max_seen", -1):
        state["max_seen"] = update_id
    if len(state["seen"]) > MAX_ENTRIES:
        state["seen"] = state["seen"][-MAX_ENTRIES:]
    _save(state)
    return True


def max_seen() -> int:
    return int(_load().get("max_seen", -1))


def reset() -> None:
    if STATE_FILE.exists():
        STATE_FILE.unlink()
