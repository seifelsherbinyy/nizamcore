"""sleep_context.py — deterministic sleep feasibility from real obligations.

Owning contract: directive nizam.cross_domain_adaptive_intelligence sleep_control
Also serves:     NIZAM-CONTRACT-03 daily_feature_vector.physiology;
                 NIZAM-CONTRACT-04 stage calendar_optimization (read-only input)
Satisfies:       SL03 (responsibilities), SL06 (barriers as associations),
                 SL08 (feasibility), SL09 (no catch-up jump)
Phase:           R1_FIXTURES

WHY THIS EXISTS
    sleep_controller.step() decides whether to move the bedtime target. It does
    not know when the owner must be awake, so it cannot tell the difference
    between "the bedtime is wrong" and "the wake obligation is the real
    constraint". This module supplies that missing half, deterministically.

DOCTRINE
  * All times are minutes-from-midnight in [0, 1440). 01:30 == 90, 23:00 == 1380.
    Windows wrap midnight, so every span is computed modulo one day.
  * Nothing is imputed. Any missing input yields INSUFFICIENT_DATA, never a
    guessed default and never a zero (Contract 01 T04, playbook E03).
  * A sleep deficit is a finding, never a licence to jump the target. The
    maximum normal daily shift still binds; catch-up steps are a defect.
  * Barriers stay correlational candidates. This module never asserts a cause.
  * No monetary value is read, derived or emitted here.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .sleep_controller import (
    MAX_NORMAL_SHIFT_MINUTES,
    SleepDecision,
    SleepInput,
    SleepState,
    step,
)

MINUTES_PER_DAY = 1440
# Falling asleep is not instantaneous. Used only when measured latency is absent
# AND the caller explicitly opts into the documented fallback.
DOCUMENTED_DEFAULT_LATENCY_MINUTES = 15


class Feasibility(str, Enum):
    FEASIBLE = "feasible"
    # The bedtime target cannot deliver sleep need before the wake obligation.
    BEDTIME_TOO_LATE = "bedtime_too_late"
    # Even the earliest tolerable bedtime cannot; the obligation is the problem.
    OBLIGATION_INFEASIBLE = "obligation_infeasible"
    INSUFFICIENT_DATA = "insufficient_data"


def _wrap(minutes: int) -> int:
    return int(minutes) % MINUTES_PER_DAY


def span_minutes(start_min: int, end_min: int) -> int:
    """Forward span from start to end, wrapping midnight. Never negative."""
    return _wrap(int(end_min) - int(start_min))


@dataclass(frozen=True)
class Obligations:
    """Tomorrow's hard constraints. Every field may be unknown (None)."""

    earliest_obligation_min: int | None = None
    commute_minutes: int | None = None
    preparation_minutes: int | None = None
    sleep_need_min: int | None = None
    sleep_latency_min: int | None = None
    # Earliest bedtime the owner will actually accept; guards against the
    # controller marching the target into an absurdly early hour.
    earliest_tolerable_bedtime_min: int | None = None

    def __post_init__(self) -> None:
        for name in ("earliest_obligation_min", "earliest_tolerable_bedtime_min"):
            v = getattr(self, name)
            if v is not None and not (0 <= int(v) < MINUTES_PER_DAY):
                raise ValueError(f"{name} must be in [0,1440) or None")
        for name in ("commute_minutes", "preparation_minutes",
                     "sleep_need_min", "sleep_latency_min"):
            v = getattr(self, name)
            if v is not None and int(v) < 0:
                raise ValueError(f"{name} must be >= 0 or None")

    def required_wake_min(self) -> int | None:
        """Wake time implied by the obligation, commute and preparation."""
        if self.earliest_obligation_min is None:
            return None
        if self.commute_minutes is None or self.preparation_minutes is None:
            return None
        return _wrap(int(self.earliest_obligation_min)
                     - int(self.commute_minutes)
                     - int(self.preparation_minutes))

    def latency(self, *, allow_default: bool = False) -> int | None:
        if self.sleep_latency_min is not None:
            return int(self.sleep_latency_min)
        return DOCUMENTED_DEFAULT_LATENCY_MINUTES if allow_default else None

    def latest_feasible_bedtime_min(self, *, allow_default_latency: bool = False
                                    ) -> int | None:
        """Latest bedtime that still satisfies sleep need before wake."""
        wake = self.required_wake_min()
        lat = self.latency(allow_default=allow_default_latency)
        if wake is None or self.sleep_need_min is None or lat is None:
            return None
        return _wrap(wake - int(self.sleep_need_min) - lat)


@dataclass(frozen=True)
class FeasibilityReport:
    status: Feasibility
    required_wake_min: int | None
    latest_feasible_bedtime_min: int | None
    # Minutes of sleep need the current target cannot deliver. Positive = short.
    deficit_minutes: int | None
    missing_inputs: tuple[str, ...]
    reasons: tuple[str, ...]

    @property
    def is_actionable(self) -> bool:
        return self.status is not Feasibility.INSUFFICIENT_DATA


def assess(target_bedtime_min: int, ob: Obligations, *,
           allow_default_latency: bool = False) -> FeasibilityReport:
    """Deterministically judge whether a bedtime target can meet sleep need."""
    if not (0 <= int(target_bedtime_min) < MINUTES_PER_DAY):
        raise ValueError("target_bedtime_min must be in [0,1440)")

    missing: list[str] = []
    if ob.earliest_obligation_min is None:
        missing.append("earliest_obligation_min")
    if ob.commute_minutes is None:
        missing.append("commute_minutes")
    if ob.preparation_minutes is None:
        missing.append("preparation_minutes")
    if ob.sleep_need_min is None:
        missing.append("sleep_need_min")
    if ob.sleep_latency_min is None and not allow_default_latency:
        missing.append("sleep_latency_min")

    wake = ob.required_wake_min()
    latest = ob.latest_feasible_bedtime_min(
        allow_default_latency=allow_default_latency)

    if missing or wake is None or latest is None:
        return FeasibilityReport(
            status=Feasibility.INSUFFICIENT_DATA,
            required_wake_min=wake,
            latest_feasible_bedtime_min=latest,
            deficit_minutes=None,
            missing_inputs=tuple(missing),
            reasons=(
                "insufficient data to judge feasibility; missing "
                + ", ".join(missing) if missing else
                "insufficient data to judge feasibility",
            ),
        )

    lat = ob.latency(allow_default=allow_default_latency)
    assert lat is not None  # guarded above
    opportunity = span_minutes(target_bedtime_min, wake) - lat
    deficit = int(ob.sleep_need_min) - opportunity  # type: ignore[arg-type]
    reasons: list[str] = [
        f"wake {wake} implied by obligation {ob.earliest_obligation_min} "
        f"minus commute {ob.commute_minutes} minus prep {ob.preparation_minutes}",
        f"sleep opportunity {opportunity} min after {lat} min latency "
        f"versus need {ob.sleep_need_min} min",
    ]

    if deficit <= 0:
        return FeasibilityReport(
            status=Feasibility.FEASIBLE,
            required_wake_min=wake,
            latest_feasible_bedtime_min=latest,
            deficit_minutes=0,
            missing_inputs=(),
            reasons=tuple(reasons + ["target meets sleep need"]),
        )

    # Short. Decide whether the bedtime or the obligation is the real constraint.
    tolerable = ob.earliest_tolerable_bedtime_min
    if tolerable is not None:
        best_opportunity = span_minutes(tolerable, wake) - lat
        if int(ob.sleep_need_min) - best_opportunity > 0:  # type: ignore[arg-type]
            reasons.append(
                f"even the earliest tolerable bedtime {tolerable} leaves "
                f"{int(ob.sleep_need_min) - best_opportunity} min short; the "
                "wake obligation is the binding constraint, not the bedtime"
            )
            return FeasibilityReport(
                status=Feasibility.OBLIGATION_INFEASIBLE,
                required_wake_min=wake,
                latest_feasible_bedtime_min=latest,
                deficit_minutes=deficit,
                missing_inputs=(),
                reasons=tuple(reasons),
            )

    reasons.append(
        f"bedtime is {deficit} min too late for sleep need; latest feasible "
        f"bedtime is {latest}"
    )
    return FeasibilityReport(
        status=Feasibility.BEDTIME_TOO_LATE,
        required_wake_min=wake,
        latest_feasible_bedtime_min=latest,
        deficit_minutes=deficit,
        missing_inputs=(),
        reasons=tuple(reasons),
    )


@dataclass(frozen=True)
class ConstrainedDecision:
    decision: SleepDecision
    feasibility: FeasibilityReport

    @property
    def state(self) -> SleepState:
        return self.decision.state

    @property
    def shift_minutes(self) -> int:
        return self.decision.shift_minutes


def constrained_step(inp: SleepInput, ob: Obligations, *,
                     allow_default_latency: bool = False) -> ConstrainedDecision:
    """Run the controller, then attach feasibility. Never enlarges a step.

    A deficit, however large, must not produce a catch-up jump: the returned
    decision is exactly what sleep_controller.step() emitted, so the maximum
    normal daily shift keeps binding. Feasibility is reported alongside, as
    evidence for the brief, not as a licence to move faster.
    """
    decision = step(inp)
    report = assess(_wrap(inp.current_target_min), ob,
                    allow_default_latency=allow_default_latency)
    if abs(decision.shift_minutes) > MAX_NORMAL_SHIFT_MINUTES:
        raise AssertionError(
            "controller emitted a step beyond the maximum normal daily shift"
        )
    return ConstrainedDecision(decision=decision, feasibility=report)
