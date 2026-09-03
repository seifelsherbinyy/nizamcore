"""test_learning_state.py — learning promotion and counterevidence tests.

Owning contract: NIZAM-CONTRACT-03 knowledge_state_machine v1.0.0
Also serves:     NIZAM-CONTRACT-05 learning_promotion
Covers:          C03-T01, C03-T02, C03-T05, C05-T02, C05-T03, L01 L02 L03 L04
Phase:           R1_FIXTURES
"""
import pytest

from adaptive.learning_state import (
    CONFIDENCE_PROMOTION_THRESHOLD, Belief, Cadence, CausalStatus,
    PromotionBlocked, Stage, add_counterevidence, blockers, can_promote,
    label_causal, promote, supersede,
)


def _observation(**over):
    base = dict(hypothesis_id="h1", claim="late gaming precedes later sleep",
                domains=("health_fitness",))
    base.update(over)
    return Belief(**base)


def _candidate(**over):
    base = dict(hypothesis_id="h1", claim="c", domains=("health_fitness",),
                stage=Stage.LEARNING_CANDIDATE,
                evidence_for=("o1", "o2", "o3"), counterevidence_searched=True,
                confidence=0.85, evidence_trace=("run-1", "run-2"),
                reversibility_note="revert the earlier bedtime target")
    base.update(over)
    return Belief(**base)


# ── L01 / C03-T01: observations are not learnings or facts ───────────────────

def test_L01_a_single_observation_is_not_a_promoted_learning():
    b = _observation(evidence_for=("one intervention worked",))
    assert b.stage is Stage.OBSERVATION
    assert not can_promote(b, Cadence.WEEKLY)


def test_C03_T01_three_observations_may_reach_hypothesis_never_fact():
    b = _observation(evidence_for=("o1", "o2", "o3"),
                     distinct_observation_days=3)
    signal = promote(b, Cadence.DAILY)
    assert signal.stage is Stage.REPEATED_SIGNAL
    # A hypothesis still needs a counterevidence search first.
    assert not can_promote(signal, Cadence.DAILY)
    ready = add_counterevidence(signal, "counterexample on 2026-08-30",
                                confidence_penalty=0.0)
    ready = Belief(**{**ready.__dict__, "confidence": 0.5})
    hypothesis = promote(ready, Cadence.DAILY)
    assert hypothesis.stage is Stage.HYPOTHESIS
    # There is no path to a FACT in this state machine at all.
    assert not hasattr(Stage, "FACT")


def test_repeated_signal_requires_temporal_separation():
    b = _observation(evidence_for=("o1", "o2"), distinct_observation_days=1)
    assert any("temporal separation" in r for r in blockers(b, Cadence.DAILY))


# ── C03-T02 / L02: counterevidence is mandatory ──────────────────────────────

def test_C03_T02_hypothesis_with_only_supporting_evidence_cannot_promote():
    b = _observation(stage=Stage.REPEATED_SIGNAL, evidence_for=("o1", "o2"),
                     confidence=0.9, counterevidence_searched=False)
    reasons = blockers(b, Cadence.DAILY)
    assert any("counterevidence search is mandatory" in r for r in reasons)


def test_L02_counterevidence_is_recorded_alongside_support():
    b = _observation(stage=Stage.HYPOTHESIS, evidence_for=("o1", "o2"),
                     confidence=0.8, counterevidence_searched=True)
    updated = add_counterevidence(b, "2026-08-29 slept early after gaming")
    assert updated.evidence_for == ("o1", "o2")
    assert updated.evidence_against == ("2026-08-29 slept early after gaming",)


def test_promotion_to_learning_requires_counterevidence_review():
    b = _candidate(counterevidence_searched=False)
    assert any("counterevidence" in r for r in blockers(b, Cadence.WEEKLY))


# ── L03 / C05-T02: contradiction lowers confidence ───────────────────────────

def test_L03_contradicting_evidence_lowers_confidence():
    b = _observation(stage=Stage.HYPOTHESIS, confidence=0.8,
                     counterevidence_searched=True, evidence_for=("o1",))
    assert add_counterevidence(b, "contra").confidence == pytest.approx(0.6)


def test_C05_T02_repeated_contradiction_drives_confidence_to_the_floor():
    b = _observation(stage=Stage.HYPOTHESIS, confidence=0.5,
                     counterevidence_searched=True, evidence_for=("o1",))
    for i in range(3):
        b = add_counterevidence(b, f"contra-{i}")
    assert b.confidence == 0.0
    assert len(b.evidence_against) == 3


def test_confidence_below_threshold_blocks_promotion():
    b = _candidate(confidence=CONFIDENCE_PROMOTION_THRESHOLD - 0.01)
    assert any("below the promotion threshold" in r
               for r in blockers(b, Cadence.WEEKLY))


# ── Contract 05: only the weekly HIKMAH review promotes durable learning ─────

def test_a_daily_run_may_not_promote_durable_learning():
    with pytest.raises(PromotionBlocked, match="weekly HIKMAH"):
        promote(_candidate(), Cadence.DAILY)


def test_the_weekly_review_may_promote_durable_learning():
    assert promote(_candidate(), Cadence.WEEKLY).stage is Stage.PROMOTED_LEARNING


def test_a_monthly_cadence_does_not_substitute_for_the_weekly_review():
    with pytest.raises(PromotionBlocked, match="weekly HIKMAH"):
        promote(_candidate(), Cadence.MONTHLY)


def test_promotion_requires_a_reversibility_note():
    assert any("reversibility" in r
               for r in blockers(_candidate(reversibility_note=None),
                                 Cadence.WEEKLY))


def test_promotion_requires_an_evidence_trace():
    assert any("evidence trace" in r
               for r in blockers(_candidate(evidence_trace=()), Cadence.WEEKLY))


def test_an_unresolved_authority_conflict_blocks_promotion():
    assert any("authority conflict" in r
               for r in blockers(_candidate(authority_conflict=True),
                                 Cadence.WEEKLY))


# ── C03-T05 / L04: supersession preserves history ────────────────────────────

def test_C03_T05_superseding_a_learning_preserves_it():
    promoted = promote(_candidate(), Cadence.WEEKLY)
    old = supersede(promoted, "h2")
    assert old.stage is Stage.SUPERSEDED_LEARNING
    assert old.superseded_by == "h2"
    # Nothing was deleted.
    assert old.evidence_for == promoted.evidence_for
    assert old.evidence_trace == promoted.evidence_trace


def test_a_superseded_learning_is_terminal():
    promoted = promote(_candidate(), Cadence.WEEKLY)
    old = supersede(promoted, "h2")
    assert any("terminal" in r for r in blockers(old, Cadence.WEEKLY))


def test_only_a_promoted_learning_may_be_superseded():
    with pytest.raises(PromotionBlocked, match="only a promoted learning"):
        supersede(_candidate(), "h2")


# ── causal labelling discipline ──────────────────────────────────────────────

def test_a_causal_label_without_an_approved_method_is_refused():
    b = _observation(stage=Stage.HYPOTHESIS, confidence=0.5)
    with pytest.raises(PromotionBlocked, match="approved"):
        label_causal(b, None)


def test_a_causal_label_with_an_approved_method_is_recorded_as_unproven():
    b = _observation(stage=Stage.HYPOTHESIS, confidence=0.5)
    out = label_causal(b, "within-subject alternating exposure")
    assert out.causal_status is CausalStatus.CAUSAL_UNPROVEN
    assert any("method:" in t for t in out.evidence_trace)


def test_a_bare_observation_may_not_carry_a_causal_label():
    with pytest.raises(PromotionBlocked, match="bare observation"):
        Belief(hypothesis_id="h", claim="c", domains=("d",),
               stage=Stage.OBSERVATION,
               causal_status=CausalStatus.CAUSAL_UNPROVEN)


def test_confidence_outside_zero_to_one_is_refused():
    with pytest.raises(ValueError, match="confidence"):
        Belief(hypothesis_id="h", claim="c", domains=("d",), confidence=1.5)


def test_promotion_beyond_promoted_learning_is_refused():
    promoted = promote(_candidate(), Cadence.WEEKLY)
    assert any("no further promotion stage" in r
               for r in blockers(promoted, Cadence.WEEKLY))
