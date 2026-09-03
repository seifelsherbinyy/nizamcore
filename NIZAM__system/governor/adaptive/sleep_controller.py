"""sleep_controller.py — deterministic sleep-trajectory controller.

Owning contract: directive nizam.cross_domain_adaptive_intelligence sleep_control
Also serves:     NIZAM-CONTRACT-03 daily_feature_vector.physiology
Satisfies:       SL01, SL02, SL03, SL04, SL05, SL06, SL07
Phase:           R1_FIXTURES

DOCTRINE (sleep_control):
  * Optimise timing and adherence, NOT an arbitrarily early bedtime.
  * default_daily_shift_minutes = 10; maximum_normal_daily_shift_minutes = 15.
    A step larger than the maximum is a defect, never a "catch-up".
  * A missed or harmful target produces HOLD/RECOVER, never forced progression.
  * Barrier features are stored as candidate ASSOCIATIONS. Never causal facts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

DEFAULT_SHIFT_MINUTES = 10
MAX_NORMAL_SHIFT_MINUTES = 15
# Repeated strong adherence is what unlocks the larger-than-default step.
STRONG_ADHERENCE_DAYS_FOR_MAX_STEP = 3
# Adherence tolerance: within this many minutes of target counts as adhered.
ADHERENCE_TOLERANCE_MINUTES = 30
# "Materially worsens" thresholds (recovery points, sleep minutes).
MATERIAL_RECOVERY_DROP_POINTS = 10
MATERIAL_SLEEP_SHORTFALL_MINUTES = 60
# Distance from the sustainable target that still counts as reached.
TARGET_REACHED_TOLERANCE_MINUTES = 10


class SleepState(str, Enum):
    ADVANCE = "ADVANCE"
    HOLD = "HOLD"
    RECOVER = "RECOVER"
    RECALIBRATE = "RECALIBRATE"
    TARGET_REACHED = "TARGET_REACHED"


class SleepControllerError(Exception):
    """Raised when a controller invariant would be violated."""


def is_adhered(observed_onset_min: int | None, target_min: int,
               tolerance: int = ADHERENCE_TOLERANCE_MINUTES) -> bool | None:
    """None when unknown — never guessed (Contract 01 T04)."""
    if observed_onset_min is None:
        return None
    return abs(int(observed_onset_min) - int(target_min)) <= tolerance


@dataclass(frozen=True)
class SleepInput:
    """All times are minutes-from-midnight (01:30 == 90)."""

    current_target_min: int
    sustainable_target_min: int | None = None
    observed_onset_min: int | None = None
    adhered: bool | None = None
    consecutive_strong_adherence_days: int = 0
    sleep_duration_min: int | None = None
    sleep_need_min: int | None = None
    recovery_delta_points: int | None = None
    travel_or_regime_change: bool = False
    barriers: tuple[str, ...] = ()

    def resolved_adherence(self) -> bool | None:
        if self.adhered is not None:
            return self.adhered
        return is_adhered(self.observed_onset_min, self.current_target_min)


@dataclass(frozen=True)
class BarrierAssociation:
    """A candidate association. causal_status is fixed by contract."""

    barrier: str
    causal_status: str = "correlational_candidate"


@dataclass(frozen=True)
class SleepDecision:
    state: SleepState
    next_target_min: int
    shift_minutes: int
    needs_recompute: bool
    barrier_associations: tuple[BarrierAssociation, ...]
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # The controller's central safety invariant, enforced on every output.
        if abs(self.shift_minutes) > MAX_NORMAL_SHIFT_MINUTES:
            raise SleepControllerError(
                f"shift {self.shift_minutes} exceeds maximum normal daily shift "
                f"{MAX_NORMAL_SHIFT_MINUTES} minutes (sleep_control invariant)"
            )
        if self.state is not SleepState.ADVANCE and self.shift_minutes != 0:
            raise SleepControllerError(
                f"state {self.state.value} must not move the target; "
                f"got shift {self.shift_minutes}"
            )
        if self.state is SleepState.ADVANCE and self.shift_minutes >= 0:
            raise SleepControllerError(
                "ADVANCE must move the target earlier (negative shift); "
                f"got {self.shift_minutes}"
            )


def _material_regression(inp: SleepInput) -> str | None:
    """Did sleep duration or next-day recovery materially worsen?"""
    if inp.recovery_delta_points is not None and \
            int(inp.recovery_delta_points) <= -MATERIAL_RECOVERY_DROP_POINTS:
        return (f"recovery dropped {abs(int(inp.recovery_delta_points))} points "
                f"(>= {MATERIAL_RECOVERY_DROP_POINTS})")
    if inp.sleep_duration_min is not None and inp.sleep_need_min is not None:
        shortfall = int(inp.sleep_need_min) - int(inp.sleep_duration_min)
        if shortfall >= MATERIAL_SLEEP_SHORTFALL_MINUTES:
            return (f"sleep {shortfall} min short of need "
                    f"(>= {MATERIAL_SLEEP_SHORTFALL_MINUTES})")
    return None


def _allowed_step(inp: SleepInput) -> int:
    """Default 10; the 15-minute step requires a repeated strong-adherence run."""
    if inp.consecutive_strong_adherence_days >= STRONG_ADHERENCE_DAYS_FOR_MAX_STEP:
        return MAX_NORMAL_SHIFT_MINUTES
    return DEFAULT_SHIFT_MINUTES


def _build(inp: SleepInput, state: SleepState, shift: int, reasons: list[str],
           needs_recompute: bool = False) -> SleepDecision:
    if abs(shift) > MAX_NORMAL_SHIFT_MINUTES:
        raise SleepControllerError(
            f"refusing to emit a {shift}-minute step; maximum normal daily shift "
            f"is {MAX_NORMAL_SHIFT_MINUTES} minutes"
        )
    return SleepDecision(
        state=state,
        next_target_min=int(inp.current_target_min) + shift,
        shift_minutes=shift,
        needs_recompute=needs_recompute,
        barrier_associations=tuple(BarrierAssociation(b) for b in inp.barriers),
        reasons=tuple(reasons),
    )


def step(inp: SleepInput) -> SleepDecision:
    """Resolve one day's sleep-target decision.

    Precedence, strictly in this order:
      1. travel / schedule-regime change      -> RECALIBRATE (no phase advance)
      2. material sleep or recovery regression -> RECOVER    (protect opportunity)
      3. sustainable target already reached    -> TARGET_REACHED
      4. previous target missed or unknown     -> HOLD
      5. previous target adhered               -> ADVANCE (10, or 15 on a streak)
    """
    adherence = inp.resolved_adherence()

    if inp.travel_or_regime_change:
        return _build(inp, SleepState.RECALIBRATE, 0,
                      ["travel or schedule-regime change: recompute the target "
                       "trajectory from responsibilities and observed behaviour; "
                       "no phase advance today"],
                      needs_recompute=True)

    regression = _material_regression(inp)
    if regression is not None:
        return _build(inp, SleepState.RECOVER, 0,
                      [f"material regression: {regression}; protect sleep "
                       "opportunity and do not continue the phase advance"])

    if inp.sustainable_target_min is not None and \
            abs(int(inp.current_target_min) - int(inp.sustainable_target_min)) \
            <= TARGET_REACHED_TOLERANCE_MINUTES and adherence is True:
        return _build(inp, SleepState.TARGET_REACHED, 0,
                      ["sustainable target window reached with acceptable "
                       "adherence and no recovery regression: maintain and monitor"])

    if adherence is not True:
        why = ("previous target missed" if adherence is False
               else "adherence unknown; nothing observed to justify an advance")
        return _build(inp, SleepState.HOLD, 0,
                      [f"{why}: keep the target unchanged and inspect the barrier"])

    stepsize = _allowed_step(inp)
    note = (f"repeated strong adherence ({inp.consecutive_strong_adherence_days} "
            f"days): advance by the maximum normal {stepsize} minutes"
            if stepsize == MAX_NORMAL_SHIFT_MINUTES
            else f"target adhered: advance by the default {stepsize} minutes")
    return _build(inp, SleepState.ADVANCE, -stepsize, [note])
