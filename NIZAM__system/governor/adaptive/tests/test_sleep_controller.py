"""test_sleep_controller.py — sleep trajectory controller acceptance tests.

Owning contract: directive nizam.cross_domain_adaptive_intelligence sleep_control
Covers:          SL01 SL02 SL03 SL04 SL05 SL06 SL07
Phase:           R1_FIXTURES
"""
import pytest

from adaptive.sleep_controller import (
    DEFAULT_SHIFT_MINUTES, MAX_NORMAL_SHIFT_MINUTES, SleepControllerError,
    SleepDecision, SleepInput, SleepState, is_adhered, step,
)

TARGET_0130 = 90     # 01:30 as minutes-from-midnight
ONSET_0300 = 180     # 03:00


def test_SL01_adhered_advances_by_no_more_than_ten_minutes_by_default():
    d = step(SleepInput(current_target_min=TARGET_0130,
                        observed_onset_min=ONSET_0300, adhered=True))
    assert d.state is SleepState.ADVANCE
    assert d.shift_minutes == -DEFAULT_SHIFT_MINUTES
    assert abs(d.shift_minutes) <= DEFAULT_SHIFT_MINUTES
    assert d.next_target_min == TARGET_0130 - DEFAULT_SHIFT_MINUTES


def test_SL02_repeated_strong_adherence_unlocks_the_fifteen_minute_maximum():
    d = step(SleepInput(current_target_min=TARGET_0130, adhered=True,
                        consecutive_strong_adherence_days=4))
    assert d.state is SleepState.ADVANCE
    assert d.shift_minutes == -MAX_NORMAL_SHIFT_MINUTES


def test_SL02_max_step_is_never_exceeded_even_on_a_long_streak():
    d = step(SleepInput(current_target_min=TARGET_0130, adhered=True,
                        consecutive_strong_adherence_days=99))
    assert abs(d.shift_minutes) <= MAX_NORMAL_SHIFT_MINUTES


def test_SL03_missed_target_holds_and_does_not_advance():
    d = step(SleepInput(current_target_min=TARGET_0130, adhered=False))
    assert d.state is SleepState.HOLD
    assert d.shift_minutes == 0
    assert d.next_target_min == TARGET_0130


def test_SL04_material_recovery_regression_triggers_recover():
    d = step(SleepInput(current_target_min=TARGET_0130, adhered=True,
                        recovery_delta_points=-15))
    assert d.state is SleepState.RECOVER
    assert d.shift_minutes == 0


def test_SL04_material_sleep_shortfall_triggers_recover():
    d = step(SleepInput(current_target_min=TARGET_0130, adhered=True,
                        sleep_duration_min=300, sleep_need_min=460))
    assert d.state is SleepState.RECOVER


def test_SL05_travel_or_regime_change_recalibrates():
    d = step(SleepInput(current_target_min=TARGET_0130, adhered=True,
                        travel_or_regime_change=True))
    assert d.state is SleepState.RECALIBRATE
    assert d.needs_recompute is True
    assert d.shift_minutes == 0


def test_SL05_recalibrate_outranks_advance_and_recover():
    d = step(SleepInput(current_target_min=TARGET_0130, adhered=True,
                        recovery_delta_points=-40, travel_or_regime_change=True))
    assert d.state is SleepState.RECALIBRATE


def test_SL06_reaching_the_sustainable_target_maintains_it():
    d = step(SleepInput(current_target_min=TARGET_0130,
                        sustainable_target_min=TARGET_0130, adhered=True))
    assert d.state is SleepState.TARGET_REACHED
    assert d.shift_minutes == 0


def test_SL07_barriers_are_associations_never_causal_facts():
    d = step(SleepInput(current_target_min=TARGET_0130, adhered=True,
                        barriers=("late_gaming", "late_caffeine")))
    assert len(d.barrier_associations) == 2
    for assoc in d.barrier_associations:
        assert assoc.causal_status == "correlational_candidate"


def test_unknown_adherence_holds_rather_than_guessing():
    d = step(SleepInput(current_target_min=TARGET_0130))
    assert d.state is SleepState.HOLD
    assert any("unknown" in r for r in d.reasons)


def test_is_adhered_returns_none_when_nothing_was_observed():
    assert is_adhered(None, TARGET_0130) is None


def test_is_adhered_uses_the_tolerance_window():
    assert is_adhered(TARGET_0130 + 20, TARGET_0130) is True
    assert is_adhered(TARGET_0130 + 90, TARGET_0130) is False


# ── the controller's central invariant, asserted directly ────────────────────

def test_a_step_larger_than_the_maximum_cannot_be_constructed():
    """SleepDecision refuses to exist with an out-of-bound shift."""
    with pytest.raises(SleepControllerError, match="exceeds maximum normal"):
        SleepDecision(state=SleepState.ADVANCE, next_target_min=70,
                      shift_minutes=-20, needs_recompute=False,
                      barrier_associations=())


def test_a_non_advancing_state_may_not_move_the_target():
    with pytest.raises(SleepControllerError, match="must not move the target"):
        SleepDecision(state=SleepState.HOLD, next_target_min=80,
                      shift_minutes=-10, needs_recompute=False,
                      barrier_associations=())


def test_advance_must_move_the_target_earlier():
    with pytest.raises(SleepControllerError, match="must move the target earlier"):
        SleepDecision(state=SleepState.ADVANCE, next_target_min=100,
                      shift_minutes=10, needs_recompute=False,
                      barrier_associations=())
