"""AdaptationState dataclass and file I/O for format adaptation persistence.

This module provides the core state structure for tracking which message format
each persona is currently using, along with JSONL append-only persistence.

File format: ADAPTATION_STATE.jsonl — one JSON object per line.
On load, the last entry matching the persona wins (append-only, latest wins).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Immutable format rotation cycle — order must never change.
FORMATS = ["standard", "short", "emoji", "direct_question", "story"]


@dataclass
class AdaptationState:
    """State for a single persona's format adaptation.

    Fields
    ------
    persona : str
        Persona identifier (e.g. "AMMAR", "HIKMAH").
    current_format : str
        The active message format. Defaults to "standard".
    previous_format : Optional[str]
        The format used before the last rotation. None if never rotated.
    rotation_index : int
        Index into FORMATS of the current format. Defaults to 0 (standard).
    last_rotation_at : Optional[str]
        ISO 8601 UTC timestamp of the last rotation. None if never rotated.
    adaptation_id : Optional[str]
        ID of the last rotation event. None if never rotated.
    """

    persona: str
    current_format: str = "standard"
    previous_format: Optional[str] = None
    rotation_index: int = 0
    last_rotation_at: Optional[str] = None
    adaptation_id: Optional[str] = None


def to_dict(state: AdaptationState) -> dict:
    """Serialize AdaptationState to a plain dict with UTC timestamp.

    Parameters
    ----------
    state : AdaptationState
        The state to serialize.

    Returns
    -------
    dict
        JSON-serializable dict including a "ts" field (ISO 8601 UTC).
    """
    return {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "persona": state.persona,
        "current_format": state.current_format,
        "previous_format": state.previous_format,
        "rotation_index": state.rotation_index,
        "last_rotation_at": state.last_rotation_at,
        "adaptation_id": state.adaptation_id,
    }


def save_state(state: AdaptationState, state_path: Path) -> None:
    """Append AdaptationState as a JSONL line to state_path.

    Creates the file (and any parent directories) if it does not exist.
    Never overwrites existing data — pure append.

    Parameters
    ----------
    state : AdaptationState
        The state to persist.
    state_path : Path
        Path to the ADAPTATION_STATE.jsonl file.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    entry = to_dict(state)
    with state_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def load_state(persona: str, state_path: Path) -> AdaptationState:
    """Load the most recent AdaptationState for a persona from state_path.

    Reads the JSONL file line by line. The last entry whose "persona" field
    matches is returned. If the file does not exist or no matching entry is
    found, returns an AdaptationState with default values.

    Parameters
    ----------
    persona : str
        Persona identifier to look up.
    state_path : Path
        Path to the ADAPTATION_STATE.jsonl file.

    Returns
    -------
    AdaptationState
        The most recent state for the persona, or defaults.
    """
    if not state_path.exists():
        return AdaptationState(persona=persona)

    last_match: Optional[dict] = None
    with state_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("persona") == persona:
                last_match = entry

    if last_match is None:
        return AdaptationState(persona=persona)

    return AdaptationState(
        persona=last_match["persona"],
        current_format=last_match.get("current_format", "standard"),
        previous_format=last_match.get("previous_format"),
        rotation_index=last_match.get("rotation_index", 0),
        last_rotation_at=last_match.get("last_rotation_at"),
        adaptation_id=last_match.get("adaptation_id"),
    )
