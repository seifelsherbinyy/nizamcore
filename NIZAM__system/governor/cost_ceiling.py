"""cost_ceiling.py — $50 soft / $300 hard / NIZAM_KILL_ALL panic stop.

Reads + writes `NIZAM__system/ledgers/.cost-month.json` (gitignored). Every
LLM provider call MUST register its projected cost via `accumulate(usd)`
BEFORE making the call; `check_or_block()` is then evaluated.

Behavior:
- spend < soft       : permit; emit info
- soft <= spend < hard: permit; emit WARN to EVENT_LEDGER
- spend >= hard      : raise CostCeilingExceeded; recommend NIZAM_KILL_ALL=1

Pure stdlib. No egress.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path
from typing import Any

_DEFAULT_REPO = Path(__file__).resolve().parents[2]
_STATE_FILE = (
    _DEFAULT_REPO / "NIZAM__system" / "ledgers" / ".cost-month.json"
)
SOFT_USD = 50.0
HARD_USD = 300.0


class CostCeilingExceeded(RuntimeError):
    pass


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _current_month() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m")


def _load_state(path: Path = _STATE_FILE) -> dict[str, Any]:
    if not path.exists():
        return {"month": _current_month(), "spend_usd": 0.0, "calls": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("month") != _current_month():
        # Auto-roll month
        return {"month": _current_month(), "spend_usd": 0.0, "calls": []}
    return data


def _save_state(state: dict, path: Path = _STATE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def accumulate(
    usd: float, *, provider: str, model: str, agent: str,
    state_path: Path = _STATE_FILE,
) -> float:
    """Record `usd` against this month's budget. Returns new total."""
    if usd < 0:
        raise ValueError("cost cannot be negative")
    state = _load_state(state_path)
    state["spend_usd"] = round(float(state["spend_usd"]) + float(usd), 4)
    state["calls"].append({
        "ts": _now(),
        "provider": provider,
        "model": model,
        "agent": agent,
        "usd": round(float(usd), 4),
    })
    _save_state(state, state_path)
    return state["spend_usd"]


def check_or_block(state_path: Path = _STATE_FILE) -> dict[str, Any]:
    """Inspect current spend. Raises if hard ceiling crossed."""
    state = _load_state(state_path)
    spend = float(state["spend_usd"])
    status = "ok"
    if spend >= HARD_USD:
        status = "blocked"
        raise CostCeilingExceeded(
            f"hard ceiling ${HARD_USD} reached "
            f"(spend=${spend:.2f}); set NIZAM_KILL_ALL=1 to halt all writers."
        )
    if spend >= SOFT_USD:
        status = "warn"
    return {"month": state["month"], "spend_usd": spend, "status": status,
            "soft_usd": SOFT_USD, "hard_usd": HARD_USD}


def report(state_path: Path = _STATE_FILE) -> dict[str, Any]:
    """Daily /cost report — caller may format for Telegram."""
    state = _load_state(state_path)
    by_provider: dict[str, float] = {}
    by_agent: dict[str, float] = {}
    for c in state["calls"]:
        by_provider[c["provider"]] = by_provider.get(c["provider"], 0.0) + c["usd"]
        by_agent[c["agent"]] = by_agent.get(c["agent"], 0.0) + c["usd"]
    return {
        "month": state["month"],
        "spend_usd": round(state["spend_usd"], 4),
        "soft_usd": SOFT_USD,
        "hard_usd": HARD_USD,
        "by_provider": by_provider,
        "by_agent": by_agent,
        "call_count": len(state["calls"]),
    }


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "report":
        print(json.dumps(report(), indent=2))
    elif cmd == "check":
        try:
            print(json.dumps(check_or_block(), indent=2))
        except CostCeilingExceeded as exc:
            print(f"BLOCKED: {exc}")
            sys.exit(2)
