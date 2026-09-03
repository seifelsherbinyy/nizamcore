"""sukoon_gate.py — deterministic capacity gate (recovery before pressure).

Owning contract: NIZAM-CONTRACT-01 T01_RECOVERY_AWARE_EXECUTION v1.0.0
Also serves:     NIZAM-CONTRACT-04 stage C_SUKOON; directive
                 nizam.cross_domain_adaptive_intelligence sukoon_policy
Satisfies:       C01-T01, C01-T02, C01-T03, C04-T02, C04-T03,
                 S01, S02, S03, S04, S05
Phase:           R1_FIXTURES

DOCTRINE:
  * A crisis / immediate-safety signal overrides EVERY recovery percentage and
    blocks ordinary automation (Contract 01 T01, playbook S05).
  * Objective recovery may only elevate capacity when it is FRESH. Stale or
    unknown recovery is not current truth (playbook E03).
  * A low recovery state is never evidence of laziness or moral failure; this
    module emits capacity, never judgement (Contract 01 T01 forbidden).
  * Nothing here is imputed. Absent recovery is MISSING, not zero.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .evidence import Evidence, Label, missing, fact

# Thresholds are contract constants, not tunables.
FULL_RECOVERY_THRESHOLD = 67   # directive sukoon_policy.full_mode
BOUNDED_RECOVERY_THRESHOLD = 40  # Contract 01 T01 + directive bounded_mode


class Mode(str, Enum):
    FULL = "full"
    BOUNDED = "bounded"
    RECOVERY = "recovery"
    CRISIS_OVERRIDE = "crisis_override"


class Capacity(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class Freshness(str, Enum):
    FRESH = "fresh"
    OBSERVED = "observed"
    STALE = "stale"
    UNKNOWN = "unknown"
    MISSING = "missing"


# Stage vocabulary shared with Contract 04 daily_dag.
STAGE_SHURA = "SHURA"
STAGE_NAQD = "NAQD"
STAGE_QARAR = "QARAR"
STAGE_PLANNING = "planning"
STAGE_OPTIMIZATION = "optimization"
STAGE_CALENDAR_OPTIMIZATION = "calendar_optimization"
STAGE_BOUNDED_BUILD = "bounded_build_actions"
STAGE_CAPTURE = "capture"
STAGE_ESSENTIAL_MAINTENANCE = "essential_maintenance"
STAGE_RECOVERY_PLANNING = "recovery_planning"
STAGE_DATA_REFRESH = "data_refresh"
STAGE_CONTINUITY = "continuity"

_FULL_STAGES = frozenset(
    {STAGE_SHURA, STAGE_NAQD, STAGE_QARAR, STAGE_PLANNING, STAGE_OPTIMIZATION,
     STAGE_CALENDAR_OPTIMIZATION, STAGE_BOUNDED_BUILD, STAGE_CAPTURE,
     STAGE_ESSENTIAL_MAINTENANCE, STAGE_RECOVERY_PLANNING, STAGE_DATA_REFRESH,
     STAGE_CONTINUITY}
)
_BOUNDED_STAGES = frozenset(
    {STAGE_SHURA, STAGE_NAQD, STAGE_QARAR, STAGE_PLANNING,
     STAGE_CALENDAR_OPTIMIZATION, STAGE_BOUNDED_BUILD, STAGE_CAPTURE,
     STAGE_ESSENTIAL_MAINTENANCE, STAGE_RECOVERY_PLANNING, STAGE_DATA_REFRESH,
     STAGE_CONTINUITY}
)
_RECOVERY_STAGES = frozenset(
    {STAGE_CAPTURE, STAGE_ESSENTIAL_MAINTENANCE, STAGE_RECOVERY_PLANNING,
     STAGE_DATA_REFRESH, STAGE_CONTINUITY}
)
# A crisis stops ordinary automation. Capture and continuity remain, because
# losing the record would itself be harm (Contract 01 T03, T07).
_CRISIS_STAGES = frozenset({STAGE_CAPTURE, STAGE_CONTINUITY})

# Contract 04 H_SHURA caps primary targets at 3; bounded mode reduces the count
# (directive bounded_mode.constraints "Reduce number of recommendations").
MAX_TARGETS = {
    Mode.FULL: 3,
    Mode.BOUNDED: 2,
    Mode.RECOVERY: 0,
    Mode.CRISIS_OVERRIDE: 0,
}


@dataclass(frozen=True)
class SukoonInput:
    capacity_state: Capacity
    objective_recovery_percent: int | None = None
    recovery_freshness: Freshness = Freshness.MISSING
    crisis_or_safety_signal: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.capacity_state, Capacity):
            raise ValueError("capacity_state must be a Capacity")
        r = self.objective_recovery_percent
        if r is not None and not (0 <= int(r) <= 100):
            raise ValueError("objective_recovery_percent must be 0..100 or None")


@dataclass(frozen=True)
class SukoonDecision:
    mode: Mode
    allowed_stages: frozenset[str]
    blocked_stages: frozenset[str]
    max_primary_targets: int
    conservative_workload: bool
    recovery_evidence: Evidence
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def allows(self, stage: str) -> bool:
        return stage in self.allowed_stages

    def blocks(self, stage: str) -> bool:
        return stage not in self.allowed_stages


def _usable_recovery(inp: SukoonInput) -> tuple[int | None, Evidence, str]:
    """Return (usable_percent_or_None, evidence, reason).

    Recovery may only elevate capacity when FRESH or OBSERVED. Stale/unknown/
    missing recovery is recorded but never used to unlock a higher mode.
    """
    r = inp.objective_recovery_percent
    if r is None:
        return None, missing("whoop.recovery", "no recovery record available"), \
            "objective recovery MISSING; cannot elevate capacity"
    ev = fact(int(r), "whoop.recovery", "deterministic_engine_output")
    if inp.recovery_freshness in (Freshness.FRESH, Freshness.OBSERVED):
        return int(r), ev, f"objective recovery {int(r)}% is {inp.recovery_freshness.value}"
    return None, ev, (
        f"objective recovery {int(r)}% is {inp.recovery_freshness.value}; "
        "not usable as current truth"
    )


def evaluate(inp: SukoonInput) -> SukoonDecision:
    """Deterministically resolve capacity into an allowed-stage set.

    Precedence, strictly in this order:
      1. crisis / immediate-safety signal  -> CRISIS_OVERRIDE (hard stop)
      2. green            OR fresh recovery >= 67 -> FULL
      3. yellow          OR fresh recovery >= 40 -> BOUNDED
      4. otherwise (red and recovery <40/unusable) -> RECOVERY
    """
    usable, rec_ev, rec_reason = _usable_recovery(inp)
    reasons: list[str] = [rec_reason]

    # 1. Hard override. Recovery percentage is irrelevant here by contract.
    if inp.crisis_or_safety_signal:
        reasons.append(
            "crisis/immediate-safety signal present: hard override, ordinary "
            "automation stops regardless of recovery percentage"
        )
        return SukoonDecision(
            mode=Mode.CRISIS_OVERRIDE,
            allowed_stages=_CRISIS_STAGES,
            blocked_stages=_FULL_STAGES - _CRISIS_STAGES,
            max_primary_targets=MAX_TARGETS[Mode.CRISIS_OVERRIDE],
            conservative_workload=True,
            recovery_evidence=rec_ev,
            reasons=tuple(reasons),
        )

    # A red capacity state always keeps workload expansion conservative, even
    # when an objective recovery figure unlocks a higher cognitive mode
    # (playbook S03).
    conservative = inp.capacity_state is Capacity.RED

    # 2. FULL
    if inp.capacity_state is Capacity.GREEN or (
        usable is not None and usable >= FULL_RECOVERY_THRESHOLD
    ):
        reasons.append(
            "full mode: capacity green"
            if inp.capacity_state is Capacity.GREEN
            else f"full mode: objective recovery {usable}% >= {FULL_RECOVERY_THRESHOLD}"
        )
        return SukoonDecision(
            mode=Mode.FULL,
            allowed_stages=_FULL_STAGES,
            blocked_stages=frozenset(),
            max_primary_targets=MAX_TARGETS[Mode.FULL],
            conservative_workload=conservative,
            recovery_evidence=rec_ev,
            reasons=tuple(reasons),
        )

    # 3. BOUNDED
    if inp.capacity_state is Capacity.YELLOW or (
        usable is not None and usable >= BOUNDED_RECOVERY_THRESHOLD
    ):
        reasons.append(
            "bounded mode: capacity yellow"
            if inp.capacity_state is Capacity.YELLOW
            else f"bounded mode: objective recovery {usable}% >= "
                 f"{BOUNDED_RECOVERY_THRESHOLD} with no hard safety block"
        )
        return SukoonDecision(
            mode=Mode.BOUNDED,
            allowed_stages=_BOUNDED_STAGES,
            blocked_stages=_FULL_STAGES - _BOUNDED_STAGES,
            max_primary_targets=MAX_TARGETS[Mode.BOUNDED],
            conservative_workload=conservative,
            recovery_evidence=rec_ev,
            reasons=tuple(reasons),
        )

    # 4. RECOVERY
    reasons.append(
        "recovery mode: capacity red and objective recovery is below "
        f"{BOUNDED_RECOVERY_THRESHOLD} or unusable"
    )
    return SukoonDecision(
        mode=Mode.RECOVERY,
        allowed_stages=_RECOVERY_STAGES,
        blocked_stages=_FULL_STAGES - _RECOVERY_STAGES,
        max_primary_targets=MAX_TARGETS[Mode.RECOVERY],
        conservative_workload=True,
        recovery_evidence=rec_ev,
        reasons=tuple(reasons),
    )
