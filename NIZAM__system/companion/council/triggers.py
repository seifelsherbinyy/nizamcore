from __future__ import annotations

from typing import Any

from ..contracts import ContextRefresh, PulsationMessage

FULL_COUNCIL_TRIGGERS = frozenset(
    {
        "strategic_motion",
        "operator_request",
        "weekly_synthesis",
        "conflict_flag",
        "crisis",
        "value_conflict",
        "body_red_flag",
        "council_motion",
    }
)

ROUTINE_PULSE_KINDS = frozenset(
    {
        "companion_checkin",
        "islamic_reminder",
        "routine_pulse",
        "heartbeat",
        "status_ping",
    }
)


def _refresh_flags(refresh: ContextRefresh) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    sukoon = refresh.sukoon_capacity
    if sukoon == "red":
        flags["crisis"] = True
        flags["body_red_flag"] = True
    elif sukoon == "yellow":
        flags["conflict_flag"] = True
    if "open_loops" in refresh.sources_found:
        count = refresh.source_snapshots.get("open_loops", {}).get("open_loop_count", 0)
        if count and int(count) >= 3:
            flags["conflict_flag"] = True
    return flags


def should_convene_council(
    refresh: ContextRefresh,
    *,
    pulse_kind: str | None = None,
    council_required: bool = False,
    operator_requested: bool = False,
    message: PulsationMessage | None = None,
) -> bool:
    """Return True when a full council deliberation should run."""
    if operator_requested:
        return True
    if council_required:
        return True
    if message is not None and message.council_required:
        return True
    if message is not None and message.council_motion_candidate:
        return True

    kind = pulse_kind or (message.message_type if message else None)
    if kind in ROUTINE_PULSE_KINDS:
        return False

    flags = _refresh_flags(refresh)
    if flags.get("crisis") and kind != "companion_checkin":
        return True
    if flags.get("body_red_flag") and kind not in ROUTINE_PULSE_KINDS:
        return True
    if flags.get("conflict_flag") and kind in FULL_COUNCIL_TRIGGERS:
        return True
    if kind in FULL_COUNCIL_TRIGGERS:
        return True
    return False


def council_scope(refresh: ContextRefresh) -> str:
    if refresh.sukoon_capacity == "red":
        return "governance"
    if "whoop_badan" in refresh.sources_found or "pulse_entries" in refresh.sources_found:
        return "body"
    if "yawmiyat_journal" in refresh.sources_found or "witness_reflection" in refresh.sources_found:
        return "journal_meta"
    if "active_decisions" in refresh.sources_found:
        return "strategic"
    return "tactical"


def trigger_reason(
    refresh: ContextRefresh,
    *,
    pulse_kind: str | None = None,
    operator_requested: bool = False,
    message: PulsationMessage | None = None,
) -> str:
    if operator_requested:
        return "operator_request"
    kind = pulse_kind or (message.message_type if message else None)
    if kind in ROUTINE_PULSE_KINDS:
        return "routine_pulse_skipped"
    if message is not None and message.council_motion_candidate:
        return "council_motion"
    for flag, reason in (
        ("crisis", "crisis"),
        ("conflict_flag", "conflict_flag"),
        ("body_red_flag", "body_red_flag"),
    ):
        if _refresh_flags(refresh).get(flag):
            return reason
    return kind or "unspecified"


def minimal_pulse_note(
    refresh: ContextRefresh,
    *,
    pulse_kind: str | None = None,
    message: PulsationMessage | None = None,
) -> dict[str, Any]:
    """Lightweight record for routine pulses that skip full council."""
    kind = pulse_kind or (message.message_type if message else "routine_pulse")
    return {
        "pulse_kind": kind,
        "refreshed_at": refresh.refreshed_at,
        "council": "skipped",
        "reason": trigger_reason(refresh, pulse_kind=kind, message=message),
        "sources_found": list(refresh.sources_found),
        "confidence": refresh.confidence,
    }
