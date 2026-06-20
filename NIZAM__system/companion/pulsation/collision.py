"""Loop collision resolution — Loop A wins within 20 minutes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

COLLISION_WINDOW = timedelta(minutes=20)
DEFER_B = timedelta(minutes=25)


def resolve_collision(
    *,
    loop_a_due: bool,
    loop_b_due: bool,
    last_loop_a_at: datetime | None,
    last_loop_b_at: datetime | None,
    now: datetime,
) -> tuple[Literal["a", "b", "none"], str | None]:
    """Return which loop may send and optional defer reason for B."""
    if not loop_a_due and not loop_b_due:
        return "none", None

    if loop_a_due and not loop_b_due:
        return "a", None

    if loop_b_due and not loop_a_due:
        return "b", None

    # Both due — check proximity of scheduled slots
    if last_loop_a_at and abs(now - last_loop_a_at) <= COLLISION_WINDOW:
        return "a", "loop_b_deferred_loop_a_priority"
    if last_loop_b_at and abs(now - last_loop_b_at) <= COLLISION_WINDOW:
        return "a", "loop_b_deferred_loop_a_priority"

    # Both due at same tick — A always wins
    return "a", "loop_b_deferred_loop_a_priority"


def defer_loop_b_until(now: datetime) -> str:
    return (now + DEFER_B).strftime("%Y-%m-%dT%H:%M:%SZ")
