"""pulsation-state.json persistence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_STATE = (
    Path(__file__).resolve().parents[2] / "relay" / ".state" / "pulsation-state.json"
)


def load_state(path: Path = DEFAULT_STATE) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict[str, Any], path: Path = DEFAULT_STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
