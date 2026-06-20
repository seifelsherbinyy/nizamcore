"""Pulsation loop cadence and waking-hours gate."""
from __future__ import annotations

import json
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ..contracts import ContextRefresh, PulsationMessage, utc_now
from .collision import defer_loop_b_until, resolve_collision
from .context_refresh import refresh_context
from .himayah_egress import apply_egress, should_suppress_crisis, tiny_mode_for_capacity
from .message_builder import build_companion_checkin, build_islamic_reminder_placeholder
from .state import load_state, save_state

REPO = Path(__file__).resolve().parents[3]
ISLAMIC_CONFIG = REPO / "NIZAM__system" / "companion" / "islamic_reminder_config.json"

TIMEZONE = "Africa/Cairo"
WAKE_START = time(7, 0)
WAKE_END = time(22, 30)
LOOP_A_INTERVAL = timedelta(hours=3)
LOOP_B_INTERVAL = timedelta(hours=2)


def _load_islamic_enabled() -> bool:
    if not ISLAMIC_CONFIG.exists():
        return False
    try:
        payload = json.loads(ISLAMIC_CONFIG.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return bool(payload.get("enabled", False))


def in_waking_hours(now: datetime, *, timezone: str = TIMEZONE) -> bool:
    local = now.astimezone(ZoneInfo(timezone))
    current = local.time()
    return WAKE_START <= current < WAKE_END


def _parse_state_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def loop_due(
    last_at: str | None,
    interval: timedelta,
    *,
    now: datetime,
) -> bool:
    previous = _parse_state_ts(last_at)
    if previous is None:
        return True
    return now - previous >= interval


def evaluate_loops(
    *,
    now: datetime | None = None,
    loop: str | None = None,
    dry_run: bool = False,
) -> dict[str, object]:
    current = now or datetime.now(timezone.utc)
    state = load_state()

    if not in_waking_hours(current):
        return {
            "ok": True,
            "skipped": True,
            "reason": "outside_waking_hours",
            "loop_sent": None,
        }

    loop_a_due = loop_due(state.get("last_loop_a_at"), LOOP_A_INTERVAL, now=current)
    loop_b_due = loop_due(state.get("last_loop_b_at"), LOOP_B_INTERVAL, now=current)

    if loop == "a":
        loop_a_due = True
        loop_b_due = False
    elif loop == "b":
        loop_a_due = False
        loop_b_due = True
    else:
        deferred_until = _parse_state_ts(state.get("loop_b_deferred_until"))
        if deferred_until and current < deferred_until:
            loop_b_due = False

    winner, defer_reason = resolve_collision(
        loop_a_due=loop_a_due,
        loop_b_due=loop_b_due,
        last_loop_a_at=_parse_state_ts(state.get("last_loop_a_at")),
        last_loop_b_at=_parse_state_ts(state.get("last_loop_b_at")),
        now=current,
    )

    if winner == "none":
        return {
            "ok": True,
            "skipped": True,
            "reason": "not_due",
            "loop_sent": None,
        }

    refresh = refresh_context(now=current)

    if should_suppress_crisis(refresh):
        return {
            "ok": True,
            "skipped": True,
            "reason": "crisis_suppress",
            "loop_sent": None,
            "context_refresh": refresh.to_dict(),
        }

    tiny = tiny_mode_for_capacity(refresh)

    if winner == "a":
        message = build_companion_checkin(refresh, tiny_mode=tiny)
        loop_sent = "a"
    else:
        if not _load_islamic_enabled():
            return {
                "ok": True,
                "skipped": True,
                "reason": "islamic_reminder_disabled",
                "loop_sent": None,
                "context_refresh": refresh.to_dict(),
            }
        message = build_islamic_reminder_placeholder(refresh)
        loop_sent = "b"

    safe_message, egress = apply_egress(message)

    stamp = utc_now()
    if not dry_run:
        if loop_sent == "a":
            state["last_loop_a_at"] = stamp
            if defer_reason:
                state["loop_b_deferred_until"] = defer_loop_b_until(current)
        else:
            state["last_loop_b_at"] = stamp
        save_state(state)

    return {
        "ok": True,
        "skipped": False,
        "loop_sent": loop_sent,
        "defer_reason": defer_reason,
        "message": safe_message,
        "egress": egress,
        "tiny_mode": tiny,
        "context_refresh": refresh.to_dict(),
    }


def build_message_for_loop(
    loop: str,
    *,
    now: datetime | None = None,
) -> tuple[PulsationMessage | None, ContextRefresh, str | None]:
    """Build a message without updating state (for dry-run/tests)."""
    current = now or datetime.now(timezone.utc)
    if not in_waking_hours(current):
        refresh = refresh_context(now=current)
        return None, refresh, "outside_waking_hours"

    refresh = refresh_context(now=current)
    if should_suppress_crisis(refresh):
        return None, refresh, "crisis_suppress"

    tiny = tiny_mode_for_capacity(refresh)
    if loop == "a":
        message = build_companion_checkin(refresh, tiny_mode=tiny)
    elif loop == "b":
        if not _load_islamic_enabled():
            return None, refresh, "islamic_reminder_disabled"
        message = build_islamic_reminder_placeholder(refresh)
    else:
        return None, refresh, "invalid_loop"

    safe, _egress = apply_egress(message)
    return safe, refresh, None
