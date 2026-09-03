# Contract: NIZAM-DAILY-ORCHESTRATION-04 | Phase: R2_SCHEDULER
"""Acceptance tests for the Cairo-instant cron gate.

Owning contract: NIZAM Contract 04, schedule.timezone / preflight_requirement
Phase:           R2_SCHEDULER

Every expected value in this file is TRANSCRIBED from governing text, never
imported from the module under test. Importing a constant to test the boundary
it defines proves only that the module agrees with itself.

Transcribed authority
---------------------
Contract 04 `schedule`:
    timezone          Africa/Cairo
    primary_run       12:00   (exact_after_scheduler_preflight)
    reconciliation_run 13:00  (retry_or_reconcile_only)
Owner refresh cadence, 2026-09-03:
    10:00 Cairo  heavier Drive / index / cache refresh
    11:40 Cairo  volatile WHOOP, Calendar, location, weather, news, economic
Egypt's civil time (tz database, cross-checked by weekday in the tests below):
    EET  UTC+2 in winter,  EEST UTC+3 in summer
    forward transition on the last FRIDAY of April
    back    transition on the last THURSDAY of October
"""
import datetime as dt
import inspect
import pathlib

import pytest

from scheduler import cairo_gate
from scheduler.cairo_gate import (
    CAIRO,
    UTC,
    DstHazard,
    HazardKind,
    SlotDecision,
    Verdict,
    candidate_utc_slots,
    cron_expressions,
    decide,
    dst_hazards,
)

UTC_PLUS_2 = 2
UTC_PLUS_3 = 3

# (target_hour, target_minute, expected crontab spec, expected UTC slots)
PRODUCTION_TARGETS = [
    (10, 0, "0 7,8 * * *", ((7, 0), (8, 0))),
    (11, 40, "40 8,9 * * *", ((8, 40), (9, 40))),
    (12, 0, "0 9,10 * * *", ((9, 0), (10, 0))),
    (13, 0, "0 10,11 * * *", ((10, 0), (11, 0))),
]

SWEEP_FIRST_YEAR = 2026
SWEEP_LAST_YEAR = 2030


# --------------------------------------------------------------------------
# 1. The crontab specs the deployment will actually install
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "hour,minute,expected_spec,expected_slots", PRODUCTION_TARGETS
)
def test_R2_T01_production_targets_render_the_transcribed_crontab_spec(
    hour, minute, expected_spec, expected_slots
):
    """Hand-computed from the offsets, so a wrong offset table cannot hide."""
    assert candidate_utc_slots(hour, minute) == expected_slots
    assert cron_expressions(hour, minute) == expected_spec


def test_R2_T02_candidate_slots_are_exactly_one_hour_apart_and_share_a_minute():
    """Egypt's two offsets differ by a whole hour, which is why one crontab
    line can carry both slots. If that ever stopped being true the collapsed
    expression would be silently wrong."""
    for hour in range(24):
        for minute in (0, 40):
            slots = candidate_utc_slots(hour, minute)
            assert len(slots) == 2, (hour, minute, slots)
            assert {m for _h, m in slots} == {minute}
            gap = (slots[1][0] - slots[0][0]) % 24
            assert gap in (1, 23), (hour, minute, slots)


def test_R2_T03_slot_derivation_matches_hand_arithmetic_for_both_offsets():
    """12:00 Cairo is 09:00 UTC at +3 and 10:00 UTC at +2. Transcribed, not
    derived from the module's own offset tuple."""
    assert (12 - UTC_PLUS_3) % 24 == 9
    assert (12 - UTC_PLUS_2) % 24 == 10
    assert candidate_utc_slots(12, 0) == ((9, 0), (10, 0))


# --------------------------------------------------------------------------
# 2. The load-bearing property, proven by independent sweep
# --------------------------------------------------------------------------

def _independent_once_per_cairo_day_sweep(hour, minute, first_year, last_year):
    """Re-derive the invariant with `decide` alone, not via `dst_hazards`.

    Enumerates every firing OS cron would produce over a padded UTC range and
    buckets the accepted ones by Cairo calendar date. Returns {cairo_date: n}
    restricted to fully covered interior dates.
    """
    slots = candidate_utc_slots(hour, minute)
    fires = {}
    pad = dt.timedelta(days=10)
    cursor = dt.date(first_year, 1, 1) - pad
    stop = dt.date(last_year, 12, 31) + pad
    while cursor <= stop:
        for slot_hour, slot_minute in slots:
            instant = dt.datetime(
                cursor.year, cursor.month, cursor.day,
                slot_hour, slot_minute, tzinfo=UTC,
            )
            if decide(instant, hour, minute).should_run:
                key = instant.astimezone(CAIRO).date().isoformat()
                fires[key] = fires.get(key, 0) + 1
        cursor += dt.timedelta(days=1)
    judged = {}
    day = dt.date(first_year, 1, 1)
    last = dt.date(last_year, 12, 31)
    while day <= last:
        key = day.isoformat()
        judged[key] = fires.get(key, 0)
        day += dt.timedelta(days=1)
    return judged


@pytest.mark.parametrize(
    "hour,minute", [(h, m) for h, m, _s, _c in PRODUCTION_TARGETS]
)
def test_R2_T04_every_production_target_fires_exactly_once_per_cairo_day(
    hour, minute
):
    """The whole reason the dual-slot pattern is admissible.

    Five years including four DST transitions. A regression here means the
    governor either skipped a day or ran twice, and both are contract
    violations: Contract 04 forbids a duplicated daily plan.
    """
    judged = _independent_once_per_cairo_day_sweep(
        hour, minute, SWEEP_FIRST_YEAR, SWEEP_LAST_YEAR
    )
    assert judged, "sweep produced no judged days"
    offenders = {d: n for d, n in judged.items() if n != 1}
    assert offenders == {}, (
        f"{hour:02d}:{minute:02d} Cairo did not fire exactly once on: "
        f"{sorted(offenders.items())[:8]}"
    )


@pytest.mark.parametrize(
    "hour,minute", [(h, m) for h, m, _s, _c in PRODUCTION_TARGETS]
)
def test_R2_T05_hazard_analyser_agrees_with_the_independent_sweep(hour, minute):
    """`dst_hazards` is the deployment-time preflight. It must report clean for
    exactly the targets the independent sweep finds clean, or the preflight is
    decorative."""
    assert dst_hazards(
        hour, minute,
        first_year=SWEEP_FIRST_YEAR, last_year=SWEEP_LAST_YEAR,
    ) == ()


# --------------------------------------------------------------------------
# 3. Non-vacuity: the analyser must FIND the real hazards
# --------------------------------------------------------------------------

def test_R2_T06_midnight_cairo_cannot_fire_on_the_spring_forward_date():
    """Egypt jumps 00:00 -> 01:00, so 00:00 does not exist that day.

    A target that cannot fire is unfixable at runtime and must be designed
    out. Proving the analyser detects it is what makes T05's empty result
    meaningful rather than a function that always returns ().
    """
    hazards = dst_hazards(0, 0, first_year=2026, last_year=2027)
    assert [h.cairo_date for h in hazards] == ["2026-04-24", "2027-04-30"]
    for hazard in hazards:
        assert hazard.kind is HazardKind.NO_FIRE
        assert hazard.fire_count == 0
        # Egypt's published rule is the last FRIDAY of April. weekday()==4.
        assert dt.date.fromisoformat(hazard.cairo_date).weekday() == 4
        assert dt.date.fromisoformat(hazard.cairo_date).month == 4


def test_R2_T07_late_evening_cairo_double_fires_on_the_fall_back_date():
    """Egypt repeats an hour, so both candidate slots can land on the same
    Cairo date. Runtime containment is the Cairo-date run-once guard."""
    hazards = dst_hazards(23, 0, first_year=2026, last_year=2027)
    assert [h.cairo_date for h in hazards] == ["2026-10-29", "2027-10-28"]
    for hazard in hazards:
        assert hazard.kind is HazardKind.DOUBLE_FIRE
        assert hazard.fire_count == 2
        # Egypt's published rule is the last THURSDAY of October. weekday()==3.
        assert dt.date.fromisoformat(hazard.cairo_date).weekday() == 3
        assert dt.date.fromisoformat(hazard.cairo_date).month == 10


def test_R2_T08_hazard_records_name_the_target_and_the_slots():
    """A hazard has to be actionable by a human reading a preflight log."""
    hazard = dst_hazards(0, 0, first_year=2026, last_year=2026)[0]
    assert isinstance(hazard, DstHazard)
    assert "00:00 Africa/Cairo" in hazard.detail
    assert "(21, 0)" in hazard.detail and "(22, 0)" in hazard.detail


def test_R2_T09_hazard_analyser_rejects_an_empty_year_range():
    with pytest.raises(ValueError, match="empty year range"):
        dst_hazards(12, 0, first_year=2027, last_year=2026)


# --------------------------------------------------------------------------
# 4. Run identity: the Cairo date, never the UTC date
# --------------------------------------------------------------------------

def test_R2_T10_cairo_date_is_the_cairo_day_not_the_utc_day():
    """22:00 UTC on 15 July is already 16 July in Cairo. Keying a run-once
    guard on the UTC date would let a dual-slot target run twice."""
    instant = dt.datetime(2026, 7, 15, 22, 0, tzinfo=UTC)
    decision = decide(instant, 1, 0)
    assert decision.should_run
    assert decision.utc_instant == "2026-07-15T22:00:00Z"
    assert decision.cairo_date == "2026-07-16"
    assert decision.cairo_local.startswith("2026-07-16T01:00:00")


def test_R2_T11_a_naive_instant_is_refused_and_never_assumed_to_be_utc():
    decision = decide(dt.datetime(2026, 9, 3, 9, 0), 12, 0)
    assert decision.verdict is Verdict.SKIP_NOT_TZ_AWARE
    assert decision.should_run is False
    assert decision.cairo_local is None
    assert decision.utc_instant is None
    assert decision.cairo_date is None
    assert decision.delta_minutes is None
    assert "never assumed" in decision.reason


def test_R2_T12_a_non_utc_offset_is_accepted_and_converted():
    """The gate must not require its caller to have already normalised to UTC;
    it must require only that an offset is present."""
    eest = dt.timezone(dt.timedelta(hours=3))
    decision = decide(dt.datetime(2026, 7, 15, 12, 0, tzinfo=eest), 12, 0)
    assert decision.should_run
    assert decision.utc_instant == "2026-07-15T09:00:00Z"
    assert decision.cairo_date == "2026-07-15"


# --------------------------------------------------------------------------
# 5. Regime behaviour in both halves of the year
# --------------------------------------------------------------------------

def test_R2_T13_summer_noon_passes_at_0900_utc_and_stands_down_at_1000():
    """15 July is EEST (+3): 12:00 Cairo == 09:00 UTC."""
    assert decide(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0).should_run
    late = decide(dt.datetime(2026, 7, 15, 10, 0, tzinfo=UTC), 12, 0)
    assert late.verdict is Verdict.SKIP_WRONG_CAIRO_TIME
    assert late.delta_minutes == 60


def test_R2_T14_winter_noon_passes_at_1000_utc_and_stands_down_at_0900():
    """15 January is EET (+2): 12:00 Cairo == 10:00 UTC."""
    assert decide(dt.datetime(2026, 1, 15, 10, 0, tzinfo=UTC), 12, 0).should_run
    early = decide(dt.datetime(2026, 1, 15, 9, 0, tzinfo=UTC), 12, 0)
    assert early.verdict is Verdict.SKIP_WRONG_CAIRO_TIME
    assert early.delta_minutes == -60


def test_R2_T15_the_1140_volatile_slot_holds_in_both_regimes():
    """A non-zero target minute must not be rounded away."""
    assert decide(dt.datetime(2026, 7, 15, 8, 40, tzinfo=UTC), 11, 40).should_run
    assert decide(dt.datetime(2026, 1, 15, 9, 40, tzinfo=UTC), 11, 40).should_run
    off_by_ten = decide(dt.datetime(2026, 7, 15, 8, 50, tzinfo=UTC), 11, 40)
    assert off_by_ten.verdict is Verdict.SKIP_WRONG_CAIRO_TIME
    assert off_by_ten.delta_minutes == 10


# --------------------------------------------------------------------------
# 6. Tolerance is bounded so it can never admit both slots
# --------------------------------------------------------------------------

def test_R2_T16_a_tolerance_of_60_or_more_is_refused():
    """At 60 minutes both candidate slots would pass and the governor would
    run twice a day, every day. The bound is the whole safety argument."""
    with pytest.raises(ValueError, match="pass both candidate"):
        decide(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0,
               tolerance_minutes=60)
    with pytest.raises(ValueError):
        decide(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0,
               tolerance_minutes=-1)


def test_R2_T17_the_widest_legal_tolerance_still_admits_only_one_slot():
    """59 is the documented maximum. Proven, not asserted in a comment."""
    passing = [
        slot for slot in candidate_utc_slots(12, 0)
        if decide(
            dt.datetime(2026, 7, 15, slot[0], slot[1], tzinfo=UTC),
            12, 0, tolerance_minutes=59,
        ).should_run
    ]
    assert passing == [(9, 0)]


def test_R2_T18_a_zero_tolerance_demands_the_exact_minute():
    exact = decide(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, 0,
                   tolerance_minutes=0)
    assert exact.should_run
    drifted = decide(dt.datetime(2026, 7, 15, 9, 1, tzinfo=UTC), 12, 0,
                     tolerance_minutes=0)
    assert drifted.verdict is Verdict.SKIP_WRONG_CAIRO_TIME
    assert drifted.delta_minutes == 1


def test_R2_T19_the_default_tolerance_is_below_the_one_hour_separation():
    assert 0 < cairo_gate.DEFAULT_TOLERANCE_MINUTES < 60
    assert cairo_gate.MAX_TOLERANCE_MINUTES == 59


# --------------------------------------------------------------------------
# 7. Midnight-wrapping delta and input validation
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "actual,target,expected",
    [
        (0, 0, 0),
        (1439, 0, -1),      # 23:59 is one minute BEFORE midnight, not 1439 after
        (1, 1439, 2),       # 00:01 is two minutes AFTER 23:59
        (5, 0, 5),
        (720, 0, 720),
        (721, 0, -719),
    ],
)
def test_R2_T20_minute_delta_wraps_across_midnight_by_the_short_arc(
    actual, target, expected
):
    assert cairo_gate._signed_minute_delta(actual, target) == expected


def test_R2_T21_a_target_near_midnight_is_measured_by_the_short_arc():
    """Real consequence of T20: 00:02 Cairo against a 00:00 target is +2, not
    a 1438-minute miss."""
    decision = decide(dt.datetime(2026, 7, 14, 21, 2, tzinfo=UTC), 0, 0)
    assert decision.cairo_local.startswith("2026-07-15T00:02:00")
    assert decision.delta_minutes == 2
    assert decision.should_run


@pytest.mark.parametrize("hour", [-1, 24, 99])
def test_R2_T22_an_out_of_range_target_hour_is_refused(hour):
    with pytest.raises(ValueError, match="target_hour out of range"):
        decide(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), hour, 0)
    with pytest.raises(ValueError, match="target_hour out of range"):
        candidate_utc_slots(hour, 0)


@pytest.mark.parametrize("minute", [-1, 60, 100])
def test_R2_T23_an_out_of_range_target_minute_is_refused(minute):
    with pytest.raises(ValueError, match="target_minute out of range"):
        decide(dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC), 12, minute)


# --------------------------------------------------------------------------
# 8. Purity: the gate reads no clock and mutates nothing
# --------------------------------------------------------------------------

def test_R2_T24_the_module_reads_no_clock():
    """A gate that could read the clock itself would be untestable at the
    exact instants that matter, and the caller could not replay a decision."""
    source = pathlib.Path(inspect.getsourcefile(cairo_gate)).read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "datetime.now", "datetime.utcnow", ".now(", ".utcnow(",
        "date.today", "time.time", "time.localtime",
    ):
        assert forbidden not in source, f"clock read found: {forbidden}"


def test_R2_T25_decide_is_deterministic_and_its_result_is_frozen():
    instant = dt.datetime(2026, 7, 15, 9, 0, tzinfo=UTC)
    first = decide(instant, 12, 0)
    second = decide(instant, 12, 0)
    assert first == second
    assert isinstance(first, SlotDecision)
    with pytest.raises(Exception):
        first.verdict = Verdict.SKIP_WRONG_CAIRO_TIME  # type: ignore[misc]


def test_R2_T26_should_run_is_true_for_exactly_one_verdict():
    truthy = [
        verdict for verdict in Verdict
        if SlotDecision(
            verdict=verdict, cairo_local=None, utc_instant=None,
            target="x", delta_minutes=None, reason="x", cairo_date=None,
        ).should_run
    ]
    assert truthy == [Verdict.RUN]


def test_R2_T27_the_gate_names_the_contract_and_phase_in_its_header():
    """Repository rule: every file under source control declares its owning
    contract and phase in the first 20 lines."""
    lines = pathlib.Path(inspect.getsourcefile(cairo_gate)).read_text(
        encoding="utf-8"
    ).splitlines()[:20]
    head = "\n".join(lines)
    assert "NIZAM-DAILY-ORCHESTRATION-04" in head
    assert "R2_SCHEDULER" in head
    assert "Africa/Cairo" in head or "Cairo" in head


def test_R2_T28_the_timezone_is_the_contract_timezone():
    """Contract 04 schedule.timezone is Africa/Cairo, transcribed."""
    assert str(CAIRO) == "Africa/Cairo"
