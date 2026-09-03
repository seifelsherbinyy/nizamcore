"""test_evidence.py — evidence labelling and no-imputation acceptance tests.

Owning contract: NIZAM-CONTRACT-01 T04/T08 v1.0.0
Covers:          C01-T04, E01, E02, F01, C03-T04
Phase:           R1_FIXTURES
"""
import pytest

from adaptive.evidence import (
    Evidence, EvidenceError, Label, assumption, authority_rank, fact,
    inference, missing, promote_to_fact, resolve_conflict,
)


def test_C01_T04_absent_metric_stays_missing_with_no_imputation():
    ev = missing("whoop.hrv", "provider returned no record")
    assert ev.label is Label.MISSING
    assert ev.value is None
    assert ev.is_known is False


def test_E01_assigning_a_value_to_missing_is_refused():
    with pytest.raises(EvidenceError, match="imputation"):
        Evidence(Label.MISSING, 0, "whoop.hrv", "deterministic_engine_output")


def test_model_inference_may_never_be_a_fact():
    with pytest.raises(EvidenceError, match="may not originate a FACT"):
        Evidence(Label.FACT, 42, "llm.recall", "model_inference")


def test_silent_promotion_to_fact_is_refused():
    guess = inference(1234, "llm.recall")
    with pytest.raises(EvidenceError, match="cannot promote to FACT"):
        promote_to_fact(guess, "llm.recall", "model_inference")


def test_promotion_to_fact_on_deterministic_authority_is_allowed():
    guess = inference(1234, "llm.recall")
    promoted = promote_to_fact(guess, "mal.engine.balance",
                              "deterministic_engine_output")
    assert promoted.label is Label.FACT
    assert promoted.authority == "deterministic_engine_output"


def test_missing_cannot_be_promoted_because_there_is_nothing_to_promote():
    with pytest.raises(EvidenceError, match="MISSING cannot be promoted"):
        promote_to_fact(missing("x"), "engine", "deterministic_engine_output")


def test_E02_conflict_preserves_both_sides():
    journal = inference("felt rested", "yawmiyat.2026-09-03")
    biometric = fact(31, "whoop.recovery")
    conflict = resolve_conflict(journal, biometric, "recovery")
    # Neither side is discarded or merged.
    assert conflict.left is journal
    assert conflict.right is biometric
    assert conflict.winner is biometric


def test_F01_and_C03_T04_engine_beats_model_recollection():
    """An LLM-remembered balance loses to the deterministic engine."""
    recalled = inference(50_000, "llm.recall")
    engine = fact(42_500, "mal.engine", "deterministic_engine_output")
    conflict = resolve_conflict(recalled, engine, "balance")
    assert conflict.winner is engine
    assert conflict.winner.value == 42_500


def test_authority_rank_orders_engine_above_model():
    assert authority_rank("deterministic_engine_output") < authority_rank(
        "model_inference")


def test_unknown_authority_ranks_lowest():
    assert authority_rank("something_invented") >= authority_rank("model_inference")


def test_evidence_requires_a_source_pointer():
    with pytest.raises(EvidenceError, match="source"):
        Evidence(Label.INFERENCE, 1, "", "model_inference")


def test_assumption_is_distinguishable_from_inference():
    assert assumption(1, "s").label is not inference(1, "s").label
