"""test_sukoon_gate.py — SUKOON capacity gate acceptance tests.

Owning contract: NIZAM-CONTRACT-01 T01_RECOVERY_AWARE_EXECUTION v1.0.0
Covers:          S01 S02 S03 S04 S05, C01-T01 C01-T02 C01-T03,
                 C04-T02 C04-T03, E03 (stale recovery)
Phase:           R1_FIXTURES
"""
import pytest

from adaptive.evidence import Label
from adaptive.sukoon_gate import (
    BOUNDED_RECOVERY_THRESHOLD, Capacity, Freshness, Mode, STAGE_NAQD,
    STAGE_OPTIMIZATION, STAGE_QARAR, STAGE_SHURA, SukoonInput, evaluate,
)


def _inp(cap, rec=None, fresh=Freshness.FRESH, crisis=False):
    return SukoonInput(capacity_state=cap, objective_recovery_percent=rec,
                       recovery_freshness=fresh, crisis_or_safety_signal=crisis)


# ── playbook test_matrix.sukoon ──────────────────────────────────────────────

def test_S01_green_recovery_70_allows_full_reasoning():
    d = evaluate(_inp(Capacity.GREEN, 70))
    assert d.mode is Mode.FULL
    assert d.allows(STAGE_SHURA) and d.allows(STAGE_NAQD) and d.allows(STAGE_QARAR)
    assert d.max_primary_targets == 3


def test_S02_yellow_recovery_45_allows_bounded_chain():
    d = evaluate(_inp(Capacity.YELLOW, 45))
    assert d.mode is Mode.BOUNDED
    assert d.allows(STAGE_SHURA) and d.allows(STAGE_NAQD) and d.allows(STAGE_QARAR)
    # Bounded means fewer targets than full, per directive bounded_mode constraints.
    assert d.max_primary_targets < 3


def test_S03_red_recovery_55_no_crisis_runs_bounded_but_conservative():
    d = evaluate(_inp(Capacity.RED, 55))
    assert d.mode is Mode.BOUNDED
    assert d.allows(STAGE_NAQD)
    # "workload expansion remains conservative"
    assert d.conservative_workload is True


def test_S04_red_recovery_31_is_recovery_mode_and_blocks_naqd():
    d = evaluate(_inp(Capacity.RED, 31))
    assert d.mode is Mode.RECOVERY
    assert d.blocks(STAGE_NAQD)
    assert d.blocks(STAGE_SHURA)
    assert d.max_primary_targets == 0


def test_S05_crisis_overrides_even_high_recovery():
    d = evaluate(_inp(Capacity.GREEN, 80, crisis=True))
    assert d.mode is Mode.CRISIS_OVERRIDE
    assert d.blocks(STAGE_NAQD) and d.blocks(STAGE_SHURA) and d.blocks(STAGE_QARAR)
    assert any("hard override" in r for r in d.reasons)


# ── Contract 01 acceptance_tests ─────────────────────────────────────────────

def test_C01_T01_yellow_recovery_35_allows_bounded_naqd_and_shura():
    """Given SUKOON=yellow and recovery=35: NAQD and SHURA allowed but bounded."""
    d = evaluate(_inp(Capacity.YELLOW, 35))
    assert d.mode is Mode.BOUNDED
    assert d.allows(STAGE_NAQD) and d.allows(STAGE_SHURA)
    assert d.max_primary_targets < 3


def test_C01_T02_red_recovery_39_blocks_heavy_planning_and_naqd():
    """Given SUKOON=red and recovery=39: heavy planning and NAQD blocked."""
    d = evaluate(_inp(Capacity.RED, 39))
    assert d.mode is Mode.RECOVERY
    assert d.blocks(STAGE_NAQD)
    assert d.blocks(STAGE_OPTIMIZATION)


def test_C01_T03_red_recovery_55_allows_cognitive_with_explicit_evidence():
    """Cognitive actions allowed, and the recovery evidence is explicit."""
    d = evaluate(_inp(Capacity.RED, 55))
    assert d.mode is Mode.BOUNDED
    assert d.recovery_evidence.label is Label.FACT
    assert d.recovery_evidence.value == 55
    assert any("55" in r for r in d.reasons)


def test_boundary_exactly_40_is_bounded_not_recovery():
    d = evaluate(_inp(Capacity.RED, BOUNDED_RECOVERY_THRESHOLD))
    assert d.mode is Mode.BOUNDED


def test_boundary_39_is_recovery():
    assert evaluate(_inp(Capacity.RED, 39)).mode is Mode.RECOVERY


def test_C04_T03_recovery_42_red_no_safety_block_runs_cognitive_stages():
    d = evaluate(_inp(Capacity.RED, 42))
    assert d.mode is Mode.BOUNDED
    assert d.allows(STAGE_SHURA) and d.allows(STAGE_QARAR)


# ── E03: stale recovery must not be treated as current truth ─────────────────

@pytest.mark.parametrize("stale", [Freshness.STALE, Freshness.UNKNOWN,
                                   Freshness.MISSING])
def test_E03_stale_recovery_cannot_elevate_capacity(stale):
    d = evaluate(_inp(Capacity.RED, 90, fresh=stale))
    assert d.mode is Mode.RECOVERY, "stale recovery must not unlock full mode"
    assert any("not usable as current truth" in r for r in d.reasons)


def test_absent_recovery_is_missing_not_zero():
    d = evaluate(_inp(Capacity.RED, None, fresh=Freshness.MISSING))
    assert d.recovery_evidence.label is Label.MISSING
    assert d.recovery_evidence.value is None
    assert d.mode is Mode.RECOVERY


def test_recovery_percent_out_of_range_is_refused():
    with pytest.raises(ValueError):
        SukoonInput(capacity_state=Capacity.GREEN, objective_recovery_percent=140)
