"""test_sleep_context.py — sleep feasibility acceptance tests.

Owning contract: directive nizam.cross_domain_adaptive_intelligence sleep_control
Covers:          SL03, SL06, SL08 (feasibility), SL09 (no catch-up jump),
                 E03 (missing data stays missing)
Phase:           R1_FIXTURES

TAUTOLOGY POLICY
    Expected minute values are computed by hand in the test and written as
    literals with the clock time in a comment. Nothing is imported from the
    module under test to build an expectation.
"""
import pytest

from adaptive.sleep_context import (
    Feasibility, Obligations, assess, constrained_step, span_minutes,
)
from adaptive.sleep_controller import SleepInput, SleepState

# Clock literals, minutes from midnight.
T_22_00 = 1320
T_23_00 = 1380
T_00_30 = 30
T_01_30 = 90
T_03_45 = 225
T_05_00 = 300
T_07_45 = 465
T_09_00 = 540

NEED_8H = 480
LATENCY_15 = 15


def _work_day(**kw):
    base = dict(earliest_obligation_min=T_09_00, commute_minutes=45,
                preparation_minutes=30, sleep_need_min=NEED_8H,
                sleep_latency_min=LATENCY_15)
    base.update(kw)
    return Obligations(**base)


# ── wrap-around arithmetic ───────────────────────────────────────────────────

def test_span_wraps_midnight_and_is_never_negative():
    assert span_minutes(T_23_00, T_07_45) == 525   # 23:00 -> 07:45 is 8h45
    assert span_minutes(T_01_30, T_07_45) == 375   # 01:30 -> 07:45 is 6h15
    assert span_minutes(T_09_00, T_09_00) == 0
    for start in range(0, 1440, 97):
        for end in range(0, 1440, 89):
            assert 0 <= span_minutes(start, end) < 1440


def test_required_wake_subtracts_commute_and_preparation():
    ob = _work_day()
    assert ob.required_wake_min() == T_07_45     # 09:00 - 45 - 30 = 07:45


def test_latest_feasible_bedtime_walks_back_need_and_latency():
    ob = _work_day()
    # 07:45 - 8h - 15m = 23:30
    assert ob.latest_feasible_bedtime_min() == 1410


# ── FEASIBLE ─────────────────────────────────────────────────────────────────

def test_bedtime_23_00_meets_an_eight_hour_need_before_a_09_00_obligation():
    r = assess(T_23_00, _work_day())
    assert r.status is Feasibility.FEASIBLE
    assert r.deficit_minutes == 0
    assert r.required_wake_min == T_07_45
    assert r.is_actionable is True


def test_feasible_never_reports_a_negative_deficit():
    r = assess(T_22_00, _work_day())
    assert r.status is Feasibility.FEASIBLE
    assert r.deficit_minutes == 0, "surplus must clamp to 0, not go negative"


# ── BEDTIME_TOO_LATE ─────────────────────────────────────────────────────────

def test_bedtime_01_30_is_two_hours_short_and_names_the_bedtime():
    # 01:30 -> 07:45 is 375 min; minus 15 latency = 360; need 480; short 120.
    r = assess(T_01_30, _work_day())
    assert r.status is Feasibility.BEDTIME_TOO_LATE
    assert r.deficit_minutes == 120
    assert any("too late" in x for x in r.reasons)


def test_deficit_is_exact_not_rounded():
    r = assess(T_00_30, _work_day())
    # 00:30 -> 07:45 is 435; minus 15 = 420; need 480; short 60.
    assert r.deficit_minutes == 60


# ── OBLIGATION_INFEASIBLE ────────────────────────────────────────────────────

def test_an_05_00_obligation_blames_the_obligation_not_the_bedtime():
    ob = _work_day(earliest_obligation_min=T_05_00,
                   earliest_tolerable_bedtime_min=T_22_00)
    # wake 03:45; 22:00 -> 03:45 is 345; minus 15 = 330; need 480; short 150.
    r = assess(T_23_00, ob)
    assert r.status is Feasibility.OBLIGATION_INFEASIBLE
    assert r.required_wake_min == T_03_45
    assert any("binding constraint" in x for x in r.reasons)


def test_without_a_tolerable_floor_a_shortfall_is_attributed_to_the_bedtime():
    """No floor supplied means we cannot prove the obligation is at fault."""
    ob = _work_day(earliest_obligation_min=T_05_00)
    r = assess(T_23_00, ob)
    assert r.status is Feasibility.BEDTIME_TOO_LATE


# ── E03: missing data stays missing ──────────────────────────────────────────

@pytest.mark.parametrize("field", [
    "earliest_obligation_min", "commute_minutes", "preparation_minutes",
    "sleep_need_min", "sleep_latency_min",
])
def test_any_missing_input_yields_insufficient_data_and_names_it(field):
    r = assess(T_23_00, _work_day(**{field: None}))
    assert r.status is Feasibility.INSUFFICIENT_DATA
    assert field in r.missing_inputs
    assert r.deficit_minutes is None, "must not guess a deficit"
    assert r.is_actionable is False


def test_zero_is_not_treated_as_missing():
    """A genuine zero commute is data, not absence."""
    r = assess(T_23_00, _work_day(commute_minutes=0, preparation_minutes=0))
    assert r.status is not Feasibility.INSUFFICIENT_DATA
    assert r.required_wake_min == T_09_00


def test_latency_default_is_opt_in_only():
    ob = _work_day(sleep_latency_min=None)
    assert assess(T_23_00, ob).status is Feasibility.INSUFFICIENT_DATA
    opted = assess(T_23_00, ob, allow_default_latency=True)
    assert opted.status is Feasibility.FEASIBLE


def test_latency_accessor_itself_withholds_the_default_unless_opted_in():
    """Guards the accessor directly. assess() has its own missing-input check,
    so testing only through assess() leaves this path unprotected."""
    ob = _work_day(sleep_latency_min=None)
    assert ob.latency() is None, "unmeasured latency must not be imputed"
    assert ob.latency(allow_default=True) == 15
    measured = _work_day(sleep_latency_min=25)
    assert measured.latency() == 25
    assert measured.latency(allow_default=True) == 25, "measured wins over default"


def test_latest_feasible_bedtime_is_none_without_latency_unless_opted_in():
    ob = _work_day(sleep_latency_min=None)
    assert ob.latest_feasible_bedtime_min() is None
    # 07:45 - 8h - 15m = 23:30
    assert ob.latest_feasible_bedtime_min(allow_default_latency=True) == 1410


@pytest.mark.parametrize("missing_field", [
    "earliest_obligation_min", "commute_minutes", "preparation_minutes",
    "sleep_need_min",
])
def test_latest_feasible_bedtime_is_none_when_any_component_is_missing(
        missing_field):
    ob = _work_day(**{missing_field: None})
    assert ob.latest_feasible_bedtime_min() is None
    assert ob.required_wake_min() is None or missing_field == "sleep_need_min"


def test_out_of_range_inputs_are_refused():
    with pytest.raises(ValueError):
        Obligations(earliest_obligation_min=1440)
    with pytest.raises(ValueError):
        Obligations(commute_minutes=-1)
    with pytest.raises(ValueError):
        assess(1440, _work_day())


# ── SL09: a deficit must never buy a bigger step ─────────────────────────────

def _adhered(target, streak=0):
    return SleepInput(current_target_min=target, observed_onset_min=target,
                      adhered=True, consecutive_strong_adherence_days=streak)


@pytest.mark.parametrize("obligation,expected_status", [
    (T_09_00, Feasibility.FEASIBLE),
    (T_05_00, Feasibility.BEDTIME_TOO_LATE),
])
def test_constrained_step_never_exceeds_the_maximum_normal_shift(
        obligation, expected_status):
    cd = constrained_step(_adhered(T_01_30),
                          _work_day(earliest_obligation_min=obligation))
    assert abs(cd.shift_minutes) <= 15


def test_a_large_deficit_still_only_moves_the_default_ten_minutes():
    ob = _work_day(earliest_obligation_min=T_05_00)
    cd = constrained_step(_adhered(T_01_30), ob)
    assert cd.feasibility.deficit_minutes is not None
    assert cd.feasibility.deficit_minutes >= 120, "set up a large deficit"
    assert cd.state is SleepState.ADVANCE
    assert cd.shift_minutes == -10, "a deficit must not become a catch-up jump"


def test_a_streak_earns_fifteen_but_a_deficit_adds_nothing_further():
    ob = _work_day(earliest_obligation_min=T_05_00)
    cd = constrained_step(_adhered(T_01_30, streak=3), ob)
    assert cd.shift_minutes == -15
    assert abs(cd.shift_minutes) <= 15


def test_missed_target_holds_even_when_a_deficit_exists():
    """A deficit must not override the HOLD rule."""
    inp = SleepInput(current_target_min=T_01_30, observed_onset_min=T_01_30 + 90,
                     adhered=False)
    cd = constrained_step(inp, _work_day(earliest_obligation_min=T_05_00))
    assert cd.state is SleepState.HOLD
    assert cd.shift_minutes == 0
    assert cd.feasibility.status is Feasibility.BEDTIME_TOO_LATE


def test_feasibility_is_attached_without_altering_the_controller_decision():
    from adaptive.sleep_controller import step
    inp = _adhered(T_01_30)
    bare = step(inp)
    cd = constrained_step(inp, _work_day())
    assert cd.decision == bare, "feasibility must not change the decision"
