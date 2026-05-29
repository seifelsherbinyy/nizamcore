"""sukoon_gate.py — SUKOON pre-gate (B4.4).

Reads `SUKOON__recovery_first/overload_flags.jsonl` for any flag in the
last 24 hours. If present, the gate returns a downshift recommendation
that the coordinator uses to switch NAQD/Hazim into supportive_reflection
mode and to suppress aggressive routing (e.g. /naqd-grill).

Pure stdlib.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OVERLOAD_FILE = REPO / "SUKOON__recovery_first" / "overload_flags.jsonl"
WINDOW_HOURS = 24


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def recent_flags(window_hours: int = WINDOW_HOURS) -> list[dict]:
    if not OVERLOAD_FILE.exists():
        return []
    cutoff = _now() - _dt.timedelta(hours=window_hours)
    flags: list[dict] = []
    with OVERLOAD_FILE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_raw = row.get("ts") or row.get("timestamp")
            if not ts_raw:
                continue
            try:
                ts = _dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts >= cutoff:
                flags.append(row)
    return flags


def pre_gate(input_text: str) -> dict:
    """Return SUKOON pre-gate decision for an inbound message.

    Output schema:
        {
          "downshift": bool,
          "mode": "normal" | "supportive_reflection" | "crisis_protocol",
          "reasons": [str, ...],
          "recent_flag_count": int
        }
    """
    low = input_text.lower()
    if any(k in low for k in ("panic", "can't breathe", "overload red",
                              "crisis", "emergency")):
        return {
            "downshift": True,
            "mode": "crisis_protocol",
            "reasons": ["crisis_keyword_detected"],
            "recent_flag_count": 0,
        }
    flags = recent_flags()
    if flags:
        return {
            "downshift": True,
            "mode": "supportive_reflection",
            "reasons": [f"overload_flag_in_last_{WINDOW_HOURS}h"],
            "recent_flag_count": len(flags),
        }
    return {
        "downshift": False,
        "mode": "normal",
        "reasons": [],
        "recent_flag_count": 0,
    }
