"""test_calendar_idempotency.py — calendar idempotency and human-only guards.

Owning contract: NIZAM-CONTRACT-04 calendar_policy.safeguards v1.0.0
Covers:          C04-T04, playbook C01 C04 C05
Phase:           R1_FIXTURES
"""
import pytest

from adaptive.calendar_idempotency import (
    CalendarIdempotencyError, Decision, EventIntent, HUMAN_ONLY_FIELDS,
    HumanOnlyFieldError, assert_no_human_only_fields, resolve,
)


# ---------------------------------------------------------------------------
# Independent restatement of NIZAM-CONTRACT-04 calendar_policy.safeguards
# human-only truth fields. Not derived from the module under test, for the
# same reason as test_provenance.py: parametrising over HUMAN_ONLY_FIELDS
# means removing a field from that frozenset also removes it from the test,
# so an agent could silently win the right to write a human-only field.
# ---------------------------------------------------------------------------
CONTRACT_04_HUMAN_ONLY = (
    "calendar_approved",
    "approved_by_human",
    "human_confirmed",
    "operator_confirmed_externalize",
)


def test_human_only_field_set_matches_contract_04_exactly():
    """Shrinking HUMAN_ONLY_FIELDS must fail here, not pass silently."""
    assert set(HUMAN_ONLY_FIELDS) == set(CONTRACT_04_HUMAN_ONLY)
    assert len(HUMAN_ONLY_FIELDS) == len(CONTRACT_04_HUMAN_ONLY) == 4


def _intent(**over):
    base = dict(run_date="2026-09-03", purpose="focus_block",
                window_start="2026-09-03T09:00:00+03:00",
                window_end="2026-09-03T10:30:00+03:00", title="Deep work")
    base.update(over)
    return EventIntent(**base)


def test_idempotency_key_is_deterministic_across_calls():
    assert _intent().idempotency_key() == _intent().idempotency_key()


def test_distinct_windows_produce_distinct_keys():
    a = _intent().idempotency_key()
    b = _intent(window_start="2026-09-03T11:00:00+03:00").idempotency_key()
    assert a != b


def test_distinct_purposes_produce_distinct_keys():
    assert _intent(purpose="recovery_block").idempotency_key() != \
        _intent(purpose="focus_block").idempotency_key()


def test_C01_first_run_creates():
    assert resolve(_intent(), {}).decision is Decision.CREATE


def test_C01_C04_retry_of_the_same_run_does_not_duplicate():
    """C04-T04: a calendar event generated twice is not created twice."""
    intent = _intent()
    key = intent.idempotency_key()
    r = resolve(intent, {key: ["event-1"]})
    assert r.decision is Decision.SKIP_ALREADY_PRESENT
    assert r.matched_event_ids == ("event-1",)


def test_multiple_matching_keys_fail_closed():
    intent = _intent()
    key = intent.idempotency_key()
    r = resolve(intent, {key: ["event-1", "event-2"]})
    assert r.decision is Decision.FAIL_CLOSED_AMBIGUOUS
    assert any("fail closed" in x for x in r.reasons)


def test_absent_key_is_not_treated_as_free_time():
    """Absence of calendar data never becomes evidence of availability."""
    r = resolve(_intent(), {})
    assert r.decision is Decision.CREATE
    assert any("no event carries this idempotency key" in x for x in r.reasons)
    assert not any("free" in x.lower() for x in r.reasons)


@pytest.mark.parametrize("field_name", CONTRACT_04_HUMAN_ONLY)
def test_C04_agent_may_never_set_a_human_only_truth_field(field_name):
    with pytest.raises(HumanOnlyFieldError):
        assert_no_human_only_fields({"title": "x", field_name: True})


def test_ordinary_payload_passes_the_human_only_guard():
    assert_no_human_only_fields({"title": "x", "start": "y", "end": "z"})


def test_malformed_run_date_is_refused():
    with pytest.raises(CalendarIdempotencyError, match="run_date"):
        _intent(run_date="03-09-2026")


def test_empty_required_field_is_refused():
    with pytest.raises(CalendarIdempotencyError, match="title"):
        _intent(title="   ")
