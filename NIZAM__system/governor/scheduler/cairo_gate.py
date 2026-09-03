# Contract: NIZAM-DAILY-ORCHESTRATION-04 | Phase: R2_SCHEDULER
"""Cairo-instant gate for a UTC-only cron daemon.

Owning contract: NIZAM Contract 04, schedule.timezone / preflight_requirement
Phase: R2_SCHEDULER

WHY THIS EXISTS
This host's cron has no CRON_TZ support and the system zone is UTC, so a single
fixed UTC slot cannot hold a fixed Cairo time across DST:

    EEST (+3, summer)   12:00 Cairo == 09:00 UTC
    EET  (+2, winter)   12:00 Cairo == 10:00 UTC

The proven house pattern is to fire at BOTH candidate UTC slots and let the job
gate on the real Cairo clock via the tz database, so exactly one slot per day
passes in either regime with no dated offset table to maintain. This module is
that gate, extracted as a pure function so the claim "exactly one slot passes"
is proven by test rather than asserted in a comment.

The Hermes cron store is NOT the timing authority. Its schedules carry a null
timezone and its stored next-run instants are UTC, so a fixed Cairo hour written
as a Hermes cron expression would drift by an hour at every DST transition.
OS cron plus this gate is the sole timing authority.

No clock is read here. `now_utc` is always supplied by the caller.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from enum import Enum
from zoneinfo import ZoneInfo

CAIRO = ZoneInfo("Africa/Cairo")
UTC = _dt.timezone.utc

#: Egypt's observed offsets. Used only to derive the candidate UTC fire slots;
#: the gate itself never assumes an offset, it asks the tz database.
_CANDIDATE_OFFSET_HOURS = (2, 3)

#: A slot is accepted when the real Cairo minute is within this many minutes of
#: the target. It MUST stay below 60 or both candidate slots would pass.
DEFAULT_TOLERANCE_MINUTES = 5
MAX_TOLERANCE_MINUTES = 59

MINUTES_PER_DAY = 1440


class Verdict(str, Enum):
    RUN = "run"
    SKIP_WRONG_CAIRO_TIME = "skip_wrong_cairo_time"
    SKIP_NOT_TZ_AWARE = "skip_not_tz_aware"


@dataclass(frozen=True)
class SlotDecision:
    """Why this invocation runs or stands down. Never a bare boolean."""

    verdict: Verdict
    cairo_local: str | None
    utc_instant: str | None
    target: str
    delta_minutes: int | None
    reason: str
    #: The Cairo calendar date of this instant, or None when no offset was
    #: supplied. This is the run-identity key: the governor must execute once
    #: per Cairo day, and because two UTC slots are registered the caller must
    #: NOT key that guard on the UTC date. See `dst_hazards`.
    cairo_date: str | None = None

    @property
    def should_run(self) -> bool:
        return self.verdict is Verdict.RUN


class HazardKind(str, Enum):
    """A Cairo wall-clock target the dual-slot pattern cannot serve exactly once."""

    NO_FIRE = "no_fire_cairo_wall_time_does_not_exist"
    DOUBLE_FIRE = "double_fire_cairo_wall_time_occurs_twice"


@dataclass(frozen=True)
class DstHazard:
    """One Cairo date on which a target fires other than exactly once."""

    cairo_date: str
    kind: HazardKind
    fire_count: int
    detail: str


def _as_utc(now: _dt.datetime) -> _dt.datetime | None:
    """Return `now` in UTC, or None when it carries no offset.

    A naive instant is refused rather than assumed to be UTC. Guessing an
    offset is exactly the class of imputation the constitution forbids.
    """
    if now.tzinfo is None or now.tzinfo.utcoffset(now) is None:
        return None
    return now.astimezone(UTC)


def _signed_minute_delta(actual: int, target: int) -> int:
    """Minutes from target to actual on a 24h circle, in (-720, 720]."""
    d = (actual - target) % MINUTES_PER_DAY
    if d > MINUTES_PER_DAY // 2:
        d -= MINUTES_PER_DAY
    return d


def candidate_utc_slots(
    target_hour: int, target_minute: int = 0
) -> tuple[tuple[int, int], ...]:
    """The UTC (hour, minute) slots that OS cron must fire for a Cairo target.

    One slot per observed Egyptian offset, ordered earliest-offset-first and
    de-duplicated. Both are always registered; the gate discards the wrong one.
    """
    _validate_target(target_hour, target_minute)
    slots: list[tuple[int, int]] = []
    for off in _CANDIDATE_OFFSET_HOURS:
        total = (target_hour * 60 + target_minute - off * 60) % MINUTES_PER_DAY
        slot = (total // 60, total % 60)
        if slot not in slots:
            slots.append(slot)
    return tuple(sorted(slots))


def cron_expressions(target_hour: int, target_minute: int = 0) -> str:
    """A single crontab time spec covering every candidate slot.

    Only collapsible into one expression when the candidate slots share a
    minute, which they always do because Egypt's offsets differ by whole hours.
    """
    slots = candidate_utc_slots(target_hour, target_minute)
    minutes = {m for _h, m in slots}
    if len(minutes) != 1:
        raise ValueError(
            "candidate slots do not share a minute; write one entry per slot"
        )
    hours = ",".join(str(h) for h, _m in slots)
    return f"{slots[0][1]} {hours} * * *"


def _validate_target(target_hour: int, target_minute: int) -> None:
    if not 0 <= target_hour <= 23:
        raise ValueError(f"target_hour out of range: {target_hour}")
    if not 0 <= target_minute <= 59:
        raise ValueError(f"target_minute out of range: {target_minute}")


def decide(
    now_utc: _dt.datetime,
    target_hour: int,
    target_minute: int = 0,
    tolerance_minutes: int = DEFAULT_TOLERANCE_MINUTES,
) -> SlotDecision:
    """Should this invocation run, judged against the real Cairo clock."""
    _validate_target(target_hour, target_minute)
    if not 0 <= tolerance_minutes <= MAX_TOLERANCE_MINUTES:
        raise ValueError(
            "tolerance must be 0..59; 60 or more would pass both candidate "
            f"slots, got {tolerance_minutes}"
        )
    target = f"{target_hour:02d}:{target_minute:02d} Africa/Cairo"

    utc = _as_utc(now_utc)
    if utc is None:
        return SlotDecision(
            verdict=Verdict.SKIP_NOT_TZ_AWARE,
            cairo_local=None,
            utc_instant=None,
            target=target,
            delta_minutes=None,
            reason="instant carries no offset; an offset is never assumed",
            cairo_date=None,
        )

    local = utc.astimezone(CAIRO)
    delta = _signed_minute_delta(
        local.hour * 60 + local.minute, target_hour * 60 + target_minute
    )
    cairo_local = local.strftime("%Y-%m-%dT%H:%M:%S%z")
    cairo_date = local.strftime("%Y-%m-%d")
    utc_instant = utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    if abs(delta) <= tolerance_minutes:
        return SlotDecision(
            verdict=Verdict.RUN,
            cairo_local=cairo_local,
            utc_instant=utc_instant,
            target=target,
            delta_minutes=delta,
            reason=f"Cairo clock is within {tolerance_minutes} min of target",
            cairo_date=cairo_date,
        )
    return SlotDecision(
        verdict=Verdict.SKIP_WRONG_CAIRO_TIME,
        cairo_local=cairo_local,
        utc_instant=utc_instant,
        target=target,
        delta_minutes=delta,
        reason=(
            f"Cairo clock is {delta:+d} min from target, outside "
            f"{tolerance_minutes} min"
        ),
        cairo_date=cairo_date,
    )


#: Days of UTC padding around the judged window. A Cairo date is only judged
#: once every UTC slot that could land on it has been enumerated.
_HAZARD_PAD_DAYS = 10


def dst_hazards(
    target_hour: int,
    target_minute: int = 0,
    *,
    first_year: int,
    last_year: int,
    tolerance_minutes: int = DEFAULT_TOLERANCE_MINUTES,
) -> tuple[DstHazard, ...]:
    """Cairo dates on which this target does NOT fire exactly once.

    The dual-slot pattern guarantees one firing per Cairo day for almost every
    target, but not all of them, and the exceptions are real rather than
    theoretical:

      * A target inside the hour Egypt skips forward does not exist as a wall
        time on that date, so it cannot fire at all (NO_FIRE).
      * A target near the hour Egypt repeats can be matched by both candidate
        slots on the same Cairo date (DOUBLE_FIRE).

    This is a pure enumeration over the tz database; no clock is read. Callers
    schedule a target only after this returns empty for the horizon they care
    about, so the property is checked rather than assumed. A DOUBLE_FIRE is
    additionally contained at runtime by keying the run-once guard on
    `SlotDecision.cairo_date`; NO_FIRE cannot be contained and must be
    designed out by choosing a different target.
    """
    _validate_target(target_hour, target_minute)
    if first_year > last_year:
        raise ValueError(f"empty year range: {first_year}..{last_year}")

    slots = candidate_utc_slots(target_hour, target_minute)
    fires: dict[str, int] = {}

    cursor = _dt.date(first_year, 1, 1) - _dt.timedelta(days=_HAZARD_PAD_DAYS)
    stop = _dt.date(last_year, 12, 31) + _dt.timedelta(days=_HAZARD_PAD_DAYS)
    while cursor <= stop:
        for slot_hour, slot_minute in slots:
            instant = _dt.datetime(
                cursor.year, cursor.month, cursor.day, slot_hour, slot_minute,
                tzinfo=UTC,
            )
            decision = decide(
                instant, target_hour, target_minute, tolerance_minutes
            )
            if decision.should_run:
                assert decision.cairo_date is not None
                fires[decision.cairo_date] = fires.get(decision.cairo_date, 0) + 1
        cursor += _dt.timedelta(days=1)

    hazards: list[DstHazard] = []
    judged = _dt.date(first_year, 1, 1)
    last = _dt.date(last_year, 12, 31)
    while judged <= last:
        key = judged.isoformat()
        count = fires.get(key, 0)
        if count != 1:
            kind = HazardKind.NO_FIRE if count == 0 else HazardKind.DOUBLE_FIRE
            hazards.append(
                DstHazard(
                    cairo_date=key,
                    kind=kind,
                    fire_count=count,
                    detail=(
                        f"{target_hour:02d}:{target_minute:02d} Africa/Cairo "
                        f"fired {count} time(s) on {key} from UTC slots {slots}"
                    ),
                )
            )
        judged += _dt.timedelta(days=1)
    return tuple(hazards)
