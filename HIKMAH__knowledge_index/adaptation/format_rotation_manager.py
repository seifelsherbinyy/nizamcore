"""FormatRotationManager — state machine for message format rotation.

Manages per-persona format rotation with:
- Deterministic FORMATS cycle: standard → short → emoji → direct_question → story
- No-consecutive-repeat guard (previous_format check)
- 1-rotation-per-week guard (last_rotation_at check)
- ADAPTATION_LEDGER.jsonl audit logging (written BEFORE state update)
- Disk-persisted state via ADAPTATION_STATE.jsonl
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .adaptation_logger import AdaptationLogger
from .adaptation_state import FORMATS, AdaptationState, load_state, save_state

logger = logging.getLogger(__name__)

# Rotation rate limit: minimum days between rotations for the same persona.
_MIN_ROTATION_DAYS = 7


class FormatRotationManager:
    """State machine for per-persona format rotation.

    Parameters
    ----------
    state_path : Path
        Path to ADAPTATION_STATE.jsonl — persists current/previous format.
    ledger_path : Path
        Path to ADAPTATION_LEDGER.jsonl — receives audit log entries.
    """

    def __init__(self, state_path: Path, ledger_path: Path) -> None:
        self.state_path = state_path
        self.ledger_path = ledger_path
        self._logger = AdaptationLogger(ledger_path)

    # ---- public API ---------------------------------------------------------

    def get_current_format(self, persona: str) -> str:
        """Return the current active format for the persona.

        Returns "standard" for personas with no rotation history.

        Parameters
        ----------
        persona : str
            Persona identifier.

        Returns
        -------
        str
            Current format name (one of FORMATS).
        """
        state = load_state(persona, self.state_path)
        return state.current_format

    def rotate_format(
        self,
        persona: str,
        reason: str,
        response_rate: float,
        numerator: int,
        denominator: int,
    ) -> str:
        """Advance the format cycle for the persona and log the rotation event.

        Guards:
        1. Weekly rate-limit: if last_rotation_at is within 7 days, returns
           current format unchanged (no rotation, no log entry).
        2. No-consecutive-repeat: if next format == previous_format, skip
           one additional step forward.

        The ADAPTATION_LEDGER entry is written BEFORE state is updated.

        Parameters
        ----------
        persona : str
            Persona identifier.
        reason : str
            Trigger label for the audit log (e.g. "engagement_threshold_breach").
        response_rate : float
            Rate value to store in the audit log.
        numerator : int
            Responses count for the audit log.
        denominator : int
            Deliveries count for the audit log.

        Returns
        -------
        str
            The new (or current if rate-limited) format name.
        """
        state = load_state(persona, self.state_path)

        # ---- 1. Weekly rate-limit guard -------------------------------------
        if self._is_rate_limited(state):
            logger.info(
                "Skipping format rotation for %s — last rotation within %d days "
                "(last_rotation_at=%s)",
                persona,
                _MIN_ROTATION_DAYS,
                state.last_rotation_at,
            )
            return state.current_format

        # ---- 2. Advance format index ----------------------------------------
        try:
            current_idx = FORMATS.index(state.current_format)
        except ValueError:
            current_idx = 0

        next_idx = (current_idx + 1) % len(FORMATS)
        next_format = FORMATS[next_idx]

        # ---- 3. No-consecutive-repeat guard ---------------------------------
        if next_format == state.previous_format:
            next_idx = (next_idx + 1) % len(FORMATS)
            next_format = FORMATS[next_idx]

        # ---- 4. Log to ledger BEFORE updating state -------------------------
        adaptation_id = self._logger.log_rotation(
            persona=persona,
            old_format=state.current_format,
            new_format=next_format,
            response_rate=response_rate,
            numerator=numerator,
            denominator=denominator,
            reason=reason,
        )

        # ---- 5. Update and persist state ------------------------------------
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        new_state = AdaptationState(
            persona=persona,
            current_format=next_format,
            previous_format=state.current_format,
            rotation_index=next_idx,
            last_rotation_at=now_str,
            adaptation_id=adaptation_id,
        )
        save_state(new_state, self.state_path)

        return next_format

    # ---- private helpers ----------------------------------------------------

    def _is_rate_limited(self, state: AdaptationState) -> bool:
        """Return True if the persona has rotated within the last 7 days."""
        if state.last_rotation_at is None:
            return False
        try:
            last = datetime.fromisoformat(state.last_rotation_at.replace("Z", "+00:00"))
            elapsed = datetime.now(timezone.utc) - last
            return elapsed < timedelta(days=_MIN_ROTATION_DAYS)
        except (ValueError, TypeError):
            return False
