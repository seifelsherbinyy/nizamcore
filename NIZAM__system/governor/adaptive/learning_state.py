"""learning_state.py — knowledge promotion state machine with counterevidence.

Owning contract: NIZAM-CONTRACT-03 knowledge_state_machine v1.0.0
Also serves:     NIZAM-CONTRACT-05 learning_promotion
Satisfies:       C03-T01, C03-T02, C03-T05, C05-T02, C05-T03, L01, L02, L03, L04
Phase:           R1_FIXTURES

DOCTRINE:
  * Three similar observations may create a HYPOTHESIS, never a FACT (C03-T01).
  * A hypothesis with only supporting evidence cannot be promoted; a
    counterevidence search is mandatory (C03-T02).
  * Daily runs never promote durable learning. Only the weekly HIKMAH review
    may (Contract 05 learning_promotion.daily.may_promote_durable_learning=false).
  * "No hypothesis may be labeled causal without an approved evidentiary method."
  * A superseded learning is preserved, never deleted (C03-T05).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

CONFIDENCE_PROMOTION_THRESHOLD = 0.70
MIN_OBSERVATIONS_FOR_REPEATED_SIGNAL = 2
MIN_SUPPORT_FOR_LEARNING_CANDIDATE = 3


class Stage(str, Enum):
    OBSERVATION = "observation"
    REPEATED_SIGNAL = "repeated_signal"
    HYPOTHESIS = "hypothesis"
    TESTED_HYPOTHESIS = "tested_hypothesis"
    LEARNING_CANDIDATE = "learning_candidate"
    PROMOTED_LEARNING = "promoted_learning"
    SUPERSEDED_LEARNING = "superseded_learning"


_ORDER = (
    Stage.OBSERVATION, Stage.REPEATED_SIGNAL, Stage.HYPOTHESIS,
    Stage.TESTED_HYPOTHESIS, Stage.LEARNING_CANDIDATE, Stage.PROMOTED_LEARNING,
)


class CausalStatus(str, Enum):
    DESCRIPTIVE = "descriptive"
    CORRELATIONAL_CANDIDATE = "correlational_candidate"
    TESTED_ASSOCIATION = "tested_association"
    CAUSAL_UNPROVEN = "causal_unproven"


class Cadence(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"      # HIKMAH
    MONTHLY = "monthly"


class PromotionBlocked(Exception):
    """Raised when a promotion precondition is not met."""


@dataclass(frozen=True)
class Belief:
    """One row of the hypothesis ledger (Contract 03 hypothesis_ledger)."""

    hypothesis_id: str
    claim: str
    domains: tuple[str, ...]
    stage: Stage = Stage.OBSERVATION
    evidence_for: tuple[str, ...] = ()
    evidence_against: tuple[str, ...] = ()
    counterevidence_searched: bool = False
    observation_window: str | None = None
    distinct_observation_days: int = 0
    confidence: float = 0.0
    causal_status: CausalStatus = CausalStatus.DESCRIPTIVE
    interventions: tuple[str, ...] = ()
    outcomes_observed: tuple[str, ...] = ()
    authority_conflict: bool = False
    reversibility_note: str | None = None
    evidence_trace: tuple[str, ...] = ()
    superseded_by: str | None = None
    last_reviewed_at: str | None = None

    def __post_init__(self) -> None:
        if not (0.0 <= float(self.confidence) <= 1.0):
            raise ValueError("confidence must be within 0.0..1.0")
        if self.causal_status is CausalStatus.CAUSAL_UNPROVEN and \
                self.stage in (Stage.OBSERVATION, Stage.REPEATED_SIGNAL):
            raise PromotionBlocked(
                "a bare observation may not carry a causal label"
            )


def _next_stage(stage: Stage) -> Stage:
    idx = _ORDER.index(stage)
    if idx + 1 >= len(_ORDER):
        raise PromotionBlocked(f"{stage.value} has no further promotion stage")
    return _ORDER[idx + 1]


def blockers(b: Belief, cadence: Cadence) -> tuple[str, ...]:
    """Every reason the belief may NOT advance one stage right now."""
    out: list[str] = []
    if b.stage is Stage.SUPERSEDED_LEARNING:
        return ("a superseded learning is terminal and is never re-promoted",)
    try:
        target = _next_stage(b.stage)
    except PromotionBlocked as exc:
        return (str(exc),)

    if target is Stage.REPEATED_SIGNAL:
        if len(b.evidence_for) < MIN_OBSERVATIONS_FOR_REPEATED_SIGNAL:
            out.append(
                f"needs >= {MIN_OBSERVATIONS_FOR_REPEATED_SIGNAL} supporting "
                f"observations, has {len(b.evidence_for)}")
        if b.distinct_observation_days < MIN_OBSERVATIONS_FOR_REPEATED_SIGNAL:
            out.append("needs temporal separation across distinct days")

    elif target is Stage.HYPOTHESIS:
        if not b.claim.strip():
            out.append("needs an explicit claim")
        if not b.evidence_for:
            out.append("needs evidence_for")
        if not b.counterevidence_searched:
            out.append("counterevidence search is mandatory before a hypothesis")
        if b.confidence <= 0.0:
            out.append("needs a stated confidence")

    elif target is Stage.TESTED_HYPOTHESIS:
        if not b.interventions:
            out.append("needs at least one intervention or natural test")
        if not b.outcomes_observed:
            out.append("needs an observed outcome")

    elif target is Stage.LEARNING_CANDIDATE:
        if len(b.evidence_for) < MIN_SUPPORT_FOR_LEARNING_CANDIDATE:
            out.append(
                f"needs repeated support (>= {MIN_SUPPORT_FOR_LEARNING_CANDIDATE})")
        if not b.counterevidence_searched:
            out.append("counterexamples must have been recorded")
        if b.authority_conflict:
            out.append("an authority conflict is unresolved")

    elif target is Stage.PROMOTED_LEARNING:
        if cadence is not Cadence.WEEKLY:
            out.append(
                "durable learning may only be promoted by the weekly HIKMAH "
                "review; a daily run may not promote")
        if not b.evidence_trace:
            out.append("needs an evidence trace")
        if b.confidence < CONFIDENCE_PROMOTION_THRESHOLD:
            out.append(
                f"confidence {b.confidence:.2f} is below the promotion threshold "
                f"{CONFIDENCE_PROMOTION_THRESHOLD:.2f}")
        if not b.reversibility_note:
            out.append("needs a reversibility note")
        if b.authority_conflict:
            out.append("an authority conflict is unresolved")
        if not b.counterevidence_searched:
            out.append("counterevidence review is mandatory before promotion")
    return tuple(out)


def can_promote(b: Belief, cadence: Cadence) -> bool:
    return not blockers(b, cadence)


def promote(b: Belief, cadence: Cadence) -> Belief:
    """Advance exactly one stage, or refuse with every reason."""
    reasons = blockers(b, cadence)
    if reasons:
        raise PromotionBlocked(
            f"cannot promote {b.hypothesis_id} from {b.stage.value}: "
            + "; ".join(reasons))
    return replace(b, stage=_next_stage(b.stage))


def add_counterevidence(b: Belief, note: str, confidence_penalty: float = 0.2) -> Belief:
    """Contradicting evidence lowers confidence; it never silently vanishes.

    L03 / C05-T02: repeated contradiction drives confidence down rather than
    being discarded to protect a belief.
    """
    new_conf = max(0.0, round(float(b.confidence) - float(confidence_penalty), 4))
    return replace(
        b,
        evidence_against=b.evidence_against + (note,),
        confidence=new_conf,
        counterevidence_searched=True,
    )


def supersede(old: Belief, new_id: str) -> Belief:
    """Retire a promoted learning while preserving it (C03-T05).

    The old row is marked SUPERSEDED_LEARNING and keeps all of its evidence; it
    is never deleted or rewritten.
    """
    if old.stage is not Stage.PROMOTED_LEARNING:
        raise PromotionBlocked(
            "only a promoted learning is superseded; earlier stages are "
            "downgraded by counterevidence instead")
    return replace(old, stage=Stage.SUPERSEDED_LEARNING, superseded_by=new_id)


def label_causal(b: Belief, approved_method: str | None) -> Belief:
    """A causal label requires an approved evidentiary method, else refuse."""
    if not approved_method:
        raise PromotionBlocked(
            "no hypothesis may be labeled causal without an approved "
            "evidentiary method (Contract 03 hypothesis_ledger.rule)")
    return replace(b, causal_status=CausalStatus.CAUSAL_UNPROVEN,
                   evidence_trace=b.evidence_trace + (f"method:{approved_method}",))
