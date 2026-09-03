"""test_sukoon_gate.py — SUKOON capacity gate acceptance tests.

Owning contract: NIZAM-CONTRACT-01 T01_RECOVERY_AWARE_EXECUTION v1.0.0
Covers:          S01 S02 S03 S04 S05, C01-T01 C01-T02 C01-T03,
                 C04-T02 C04-T03, E03 (stale recovery),
                 CEILING (objective recovery never elevates capacity)
Phase:           R1_FIXTURES

TAUTOLOGY POLICY
    This file must never derive an expectation from the module under test.
    Thresholds, mode names and stage names are restated here as LITERALS
    transcribed from the contract text, so that renaming or retuning a
    production constant breaks these tests instead of silently moving them.
    Importing BOUNDED_RECOVERY_THRESHOLD to test its own boundary -- which an
    earlier revision of this file did -- is not a gate.
"""
import pytest

from adaptive.evidence import Label
from adaptive.sukoon_gate import (
    Capacity, Freshness, Mode, SukoonInput, evaluate,
)

# ── Literals transcribed from Contract 01 T01_RECOVERY_AWARE_EXECUTION ────────
# rules:
#   - "SUKOON green permits full cognitive actions."
#   - "SUKOON yellow permits SHURA, NAQD, QARAR, planning, and bounded
#      optimization."
#   - "Objective recovery >= 40 percent permits cognitive actions unless a hard
#      safety state exists."
# Note there is NO rule granting full mode on a recovery percentage.
CONTRACT_BOUNDED_RECOVERY_PERCENT = 40
CONTRACT_BELOW_BOUNDED_PERCENT = 39

# Mode identifiers, as literal wire values.
MODE_FULL = "full"
MODE_BOUNDED = "bounded"
MODE_RECOVERY = "recovery"
MODE_CRISIS = "crisis_override"

# Stage identifiers, as literal wire values (Contract 04 daily_dag vocabulary).
SHURA = "SHURA"
NAQD = "NAQD"
QARAR = "QARAR"
PLANNING = "planning"
OPTIMIZATION = "optimization"
CALENDAR_OPTIMIZATION = "calendar_optimization"
BOUNDED_BUILD = "bounded_build_actions"
CAPTURE = "capture"
ESSENTIAL_MAINTENANCE = "essential_maintenance"
RECOVERY_PLANNING = "recovery_planning"
DATA_REFRESH = "data_refresh"
CONTINUITY = "continuity"

ALL_STAGES = (
    SHURA, NAQD, QARAR, PLANNING, OPTIMIZATION, CALENDAR_OPTIMIZATION,
    BOUNDED_BUILD, CAPTURE, ESSENTIAL_MAINTENANCE, RECOVERY_PLANNING,
    DATA_REFRESH, CONTINUITY,
)

# The four stages RED-with-recovery may add on top of the recovery-mode set.
RED_BOUNDED_COGNITIVE = (SHURA, NAQD, QARAR, PLANNING)
# Throughput stages RED must never unlock, however good the recovery number.
RED_FORBIDDEN_THROUGHPUT = (OPTIMIZATION, CALENDAR_OPTIMIZATION, BOUNDED_BUILD)

EVERY_FRESHNESS = (
    Freshness.FRESH, Freshness.OBSERVED, Freshness.STALE,
    Freshness.UNKNOWN, Freshness.MISSING,
)


def _inp(cap, rec=None, fresh=Freshness.FRESH, crisis=False):
    return SukoonInput(capacity_state=cap, objective_recovery_percent=rec,
                       recovery_freshness=fresh, crisis_or_safety_signal=crisis)


# ── Vocabulary pinning: catch a renamed constant ─────────────────────────────

def test_mode_wire_values_match_the_contract_vocabulary():
    assert Mode.FULL.value == MODE_FULL
    assert Mode.BOUNDED.value == MODE_BOUNDED
    assert Mode.RECOVERY.value == MODE_RECOVERY
    assert Mode.CRISIS_OVERRIDE.value == MODE_CRISIS
    assert {m.value for m in Mode} == {
        MODE_FULL, MODE_BOUNDED, MODE_RECOVERY, MODE_CRISIS}


def test_full_mode_stage_set_is_exactly_the_twelve_known_stages():
    """A new stage must be classified deliberately, not inherited silently."""
    d = evaluate(_inp(Capacity.GREEN))
    assert d.allowed_stages == frozenset(ALL_STAGES)
    assert len(d.allowed_stages) == 12


# ── playbook test_matrix.sukoon ──────────────────────────────────────────────

def test_S01_green_recovery_70_allows_full_reasoning():
    d = evaluate(_inp(Capacity.GREEN, 70))
    assert d.mode is Mode.FULL
    assert d.allows(SHURA) and d.allows(NAQD) and d.allows(QARAR)
    assert d.max_primary_targets == 3


def test_S02_yellow_recovery_45_allows_bounded_chain():
    d = evaluate(_inp(Capacity.YELLOW, 45))
    assert d.mode is Mode.BOUNDED
    assert d.allows(SHURA) and d.allows(NAQD) and d.allows(QARAR)
    assert d.max_primary_targets < 3


def test_S03_red_recovery_55_no_crisis_runs_bounded_but_conservative():
    d = evaluate(_inp(Capacity.RED, 55))
    assert d.mode is Mode.BOUNDED
    assert d.allows(NAQD)
    assert d.conservative_workload is True


def test_S04_red_recovery_31_is_recovery_mode_and_blocks_naqd():
    d = evaluate(_inp(Capacity.RED, 31))
    assert d.mode is Mode.RECOVERY
    assert d.blocks(NAQD)
    assert d.blocks(SHURA)
    assert d.max_primary_targets == 0


def test_S05_crisis_overrides_even_high_recovery():
    d = evaluate(_inp(Capacity.GREEN, 80, crisis=True))
    assert d.mode is Mode.CRISIS_OVERRIDE
    assert d.blocks(NAQD) and d.blocks(SHURA) and d.blocks(QARAR)
    assert any("hard override" in r for r in d.reasons)


# ── Contract 01 acceptance_tests ─────────────────────────────────────────────

def test_C01_T01_yellow_recovery_35_allows_bounded_naqd_and_shura():
    """Given SUKOON=yellow and recovery=35: NAQD and SHURA allowed but bounded."""
    d = evaluate(_inp(Capacity.YELLOW, 35))
    assert d.mode is Mode.BOUNDED
    assert d.allows(NAQD) and d.allows(SHURA)
    assert d.max_primary_targets < 3


def test_C01_T02_red_recovery_39_blocks_heavy_planning_and_naqd():
    """Given SUKOON=red and recovery=39: heavy planning and NAQD blocked."""
    d = evaluate(_inp(Capacity.RED, CONTRACT_BELOW_BOUNDED_PERCENT))
    assert d.mode is Mode.RECOVERY
    # The contract names exactly two things: heavy planning, and NAQD. Assert
    # both by name. OPTIMIZATION is additionally checked because a throughput
    # stage leaking into recovery mode would be a worse failure than either.
    assert d.blocks(PLANNING), "contract names heavy planning explicitly"
    assert d.blocks(NAQD)
    assert d.blocks(OPTIMIZATION)


def test_C01_T01_rule4_red_below_40_restricts_to_the_named_recovery_set():
    """Rule 4: red AND recovery < 40 restricts execution to recovery, capture,
    essential maintenance, and low-pressure review -- nothing cognitive."""
    d = evaluate(_inp(Capacity.RED, CONTRACT_BELOW_BOUNDED_PERCENT))
    assert d.mode is Mode.RECOVERY
    assert d.allows(CAPTURE) and d.allows(ESSENTIAL_MAINTENANCE)
    assert d.allows(RECOVERY_PLANNING) and d.allows(CONTINUITY)
    for stage in (SHURA, NAQD, QARAR, PLANNING, OPTIMIZATION,
                  CALENDAR_OPTIMIZATION, BOUNDED_BUILD):
        assert d.blocks(stage), f"recovery mode must block {stage}"


def test_C01_T03_red_recovery_55_allows_cognitive_with_explicit_evidence():
    d = evaluate(_inp(Capacity.RED, 55))
    assert d.mode is Mode.BOUNDED
    assert d.recovery_evidence.label is Label.FACT
    assert d.recovery_evidence.value == 55
    assert any("55" in r for r in d.reasons)


def test_boundary_exactly_40_is_bounded_not_recovery():
    """40 is the literal contract boundary, not whatever the module now says."""
    d = evaluate(_inp(Capacity.RED, CONTRACT_BOUNDED_RECOVERY_PERCENT))
    assert d.mode is Mode.BOUNDED


def test_boundary_39_is_recovery():
    d = evaluate(_inp(Capacity.RED, CONTRACT_BELOW_BOUNDED_PERCENT))
    assert d.mode is Mode.RECOVERY


def test_C04_T03_recovery_42_red_no_safety_block_runs_cognitive_stages():
    d = evaluate(_inp(Capacity.RED, 42))
    assert d.mode is Mode.BOUNDED
    assert d.allows(SHURA) and d.allows(QARAR)


# ── CEILING: objective recovery must never elevate capacity ──────────────────
# Owner ruling 2026-09-03: "RED must NEVER become FULL merely because recovery
# >= 67." Contract 01 T01 grants full mode only to a green capacity state.

@pytest.mark.parametrize("percent", [67, 68, 75, 90, 99, 100])
@pytest.mark.parametrize("fresh", [Freshness.FRESH, Freshness.OBSERVED])
def test_red_never_reaches_full_however_high_and_fresh_the_recovery(percent, fresh):
    d = evaluate(_inp(Capacity.RED, percent, fresh=fresh))
    assert d.mode is not Mode.FULL, (
        f"red capacity with recovery {percent}% ({fresh.value}) reached FULL; "
        "the self-reported capacity state must be a ceiling"
    )
    assert d.mode is Mode.BOUNDED
    assert d.conservative_workload is True


@pytest.mark.parametrize("percent", [67, 80, 100])
@pytest.mark.parametrize("fresh", [Freshness.FRESH, Freshness.OBSERVED])
def test_yellow_never_reaches_full_however_high_the_recovery(percent, fresh):
    d = evaluate(_inp(Capacity.YELLOW, percent, fresh=fresh))
    assert d.mode is not Mode.FULL
    assert d.mode is Mode.BOUNDED


@pytest.mark.parametrize("percent", list(range(0, 101, 5)))
@pytest.mark.parametrize("fresh", EVERY_FRESHNESS)
def test_full_mode_is_unreachable_without_green_capacity(percent, fresh):
    """Exhaustive sweep: no (recovery, freshness) pair unlocks FULL off green."""
    for cap in (Capacity.RED, Capacity.YELLOW):
        d = evaluate(_inp(cap, percent, fresh=fresh))
        assert d.mode is not Mode.FULL, (
            f"{cap.value} + recovery {percent}% ({fresh.value}) reached FULL"
        )


def test_green_is_the_only_capacity_that_yields_full():
    yields_full = {
        cap.value for cap in Capacity
        if evaluate(_inp(cap, 100, fresh=Freshness.FRESH)).mode is Mode.FULL
    }
    assert yields_full == {"green"}


def test_red_bounded_grants_cognitive_stages_but_no_throughput_stages():
    """Contract 01 T01 rule 3 permits *cognitive* actions, not workload growth."""
    d = evaluate(_inp(Capacity.RED, 90))
    assert d.mode is Mode.BOUNDED
    for stage in RED_BOUNDED_COGNITIVE:
        assert d.allows(stage), f"red+recovery should permit cognitive {stage}"
    for stage in RED_FORBIDDEN_THROUGHPUT:
        assert d.blocks(stage), f"red+recovery must not unlock throughput {stage}"


def test_red_bounded_set_is_strictly_smaller_than_yellow_bounded_set():
    red = evaluate(_inp(Capacity.RED, 90)).allowed_stages
    yellow = evaluate(_inp(Capacity.YELLOW, 90)).allowed_stages
    assert red < yellow, "red must be strictly more restricted than yellow"


def test_crisis_outranks_every_recovery_score_for_every_capacity():
    """Crisis/immediate safety always wins, per the owner ruling."""
    for cap in Capacity:
        for percent in (0, 40, 67, 100):
            d = evaluate(_inp(cap, percent, crisis=True))
            assert d.mode is Mode.CRISIS_OVERRIDE
            assert d.max_primary_targets == 0
            assert d.conservative_workload is True
            assert d.blocks(SHURA) and d.blocks(NAQD) and d.blocks(QARAR)
            assert d.allows(CAPTURE) and d.allows(CONTINUITY)


def test_no_full_recovery_threshold_constant_is_reintroduced():
    """A 67-style elevation constant must not come back into the module."""
    import adaptive.sukoon_gate as gate
    assert not hasattr(gate, "FULL_RECOVERY_THRESHOLD"), (
        "FULL_RECOVERY_THRESHOLD reintroduces the RED-to-FULL elevation defect"
    )


# ── E03: stale recovery must not be treated as current truth ─────────────────

@pytest.mark.parametrize("stale", [Freshness.STALE, Freshness.UNKNOWN,
                                   Freshness.MISSING])
def test_E03_stale_recovery_cannot_elevate_capacity(stale):
    d = evaluate(_inp(Capacity.RED, 90, fresh=stale))
    assert d.mode is Mode.RECOVERY, "stale recovery must not unlock any mode"
    assert any("not usable as current truth" in r for r in d.reasons)


def test_absent_recovery_is_missing_not_zero():
    d = evaluate(_inp(Capacity.RED, None, fresh=Freshness.MISSING))
    assert d.recovery_evidence.label is Label.MISSING
    assert d.recovery_evidence.value is None
    assert d.mode is Mode.RECOVERY


def test_recovery_percent_out_of_range_is_refused():
    with pytest.raises(ValueError):
        SukoonInput(capacity_state=Capacity.GREEN, objective_recovery_percent=140)
