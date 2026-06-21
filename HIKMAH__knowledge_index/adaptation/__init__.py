"""Adaptation package — format rotation based on response rate signals.

Public API
----------
WeeklyResponseRateCalculator : Computes 7-day response rate from delivery ledger.
FormatRotationManager        : State machine — rotates format when rate < threshold.
AdaptationLogger             : Append-only JSONL writer for rotation audit events.
AdaptationState              : Dataclass holding per-persona format state.
load_state                   : Reads most recent AdaptationState from JSONL.
save_state                   : Appends AdaptationState to JSONL (never overwrites).
FORMATS                      : Immutable format rotation cycle list.
"""

from .adaptation_logger import AdaptationLogger
from .adaptation_state import FORMATS, AdaptationState, load_state, save_state
from .format_rotation_manager import FormatRotationManager
from .response_rate_calculator import WeeklyResponseRateCalculator

__all__ = [
    "WeeklyResponseRateCalculator",
    "FormatRotationManager",
    "AdaptationLogger",
    "AdaptationState",
    "load_state",
    "save_state",
    "FORMATS",
]
