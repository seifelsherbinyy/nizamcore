#!/usr/bin/env python3
"""
test_schedule_gate.py — Proves the 11:00 Africa/Cairo schedule is DST-correct.

Owning contract: NIZAM-HEALTH-INTELLIGENCE v0.2.0
Phase: cloud-first reconciliation

This host's cron has no CRON_TZ support, so daily-ingest.sh fires at BOTH 08:00
and 09:00 UTC and gates on the real Cairo hour. The property that makes that
correct is proven here for every day of several years, including the DST
transition days, rather than asserted in a comment.

Pure: tz database only, no network, no DB, no clock read.
"""
import datetime as dt
import os
import re
import sys

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    pytest.skip("zoneinfo unavailable", allow_module_level=True)

CAIRO = ZoneInfo("Africa/Cairo")
UTC = dt.timezone.utc
TARGET_HOUR = 11
CRON_UTC_SLOTS = (8, 9)

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPT = os.path.join(os.path.dirname(_HERE), "scripts", "daily-ingest.sh")


def cairo_hour(day: dt.date, utc_hour: int) -> int:
    return (dt.datetime(day.year, day.month, day.day, utc_hour, 0, tzinfo=UTC)
            .astimezone(CAIRO).hour)


def days(year: int):
    d = dt.date(year, 1, 1)
    while d.year == year:
        yield d
        d += dt.timedelta(days=1)


@pytest.mark.parametrize("year", [2026, 2027, 2028])
def test_exactly_one_slot_hits_1100_cairo_every_day(year):
    """The whole point: one fire per day, never zero, never two."""
    bad = []
    for day in days(year):
        hits = [h for h in CRON_UTC_SLOTS if cairo_hour(day, h) == TARGET_HOUR]
        if len(hits) != 1:
            bad.append((day.isoformat(), hits))
    assert bad == [], f"days without exactly one 11:00 Cairo slot: {bad[:10]}"


def test_summer_uses_the_0800_slot():
    day = dt.date(2026, 9, 1)
    assert cairo_hour(day, 8) == 11
    assert cairo_hour(day, 9) == 12


def test_winter_uses_the_0900_slot():
    day = dt.date(2026, 12, 15)
    assert cairo_hour(day, 8) == 10
    assert cairo_hour(day, 9) == 11


@pytest.mark.parametrize("year", [2026, 2027, 2028])
def test_dst_transition_days_are_covered(year):
    """Find the actual transition days from the tz database and check them."""
    transitions = []
    prev = None
    for day in days(year):
        off = dt.datetime(day.year, day.month, day.day, 12, 0,
                          tzinfo=UTC).astimezone(CAIRO).utcoffset()
        if prev is not None and off != prev:
            transitions.append(day)
        prev = off
    assert transitions, f"no Cairo DST transition found in {year}"
    for day in transitions:
        for probe in (day - dt.timedelta(days=1), day, day + dt.timedelta(days=1)):
            hits = [h for h in CRON_UTC_SLOTS if cairo_hour(probe, h) == TARGET_HOUR]
            assert len(hits) == 1, f"{probe} has hits={hits}"


def test_a_single_fixed_utc_slot_would_be_wrong():
    """Justifies the two-slot design instead of one hard-coded UTC hour."""
    for h in range(24):
        summer = cairo_hour(dt.date(2026, 9, 1), h) == TARGET_HOUR
        winter = cairo_hour(dt.date(2026, 12, 15), h) == TARGET_HOUR
        assert not (summer and winter), (
            f"{h:02d}:00 UTC would work year-round, so the two-slot gate is unnecessary")


def test_previous_schedule_was_not_1100_cairo():
    """The schedule this replaced fired at 10:00 UTC, which is 13:00 Cairo in summer."""
    assert cairo_hour(dt.date(2026, 9, 1), 10) == 13


# ── The shipped script must actually implement what is proven above ─────────
@pytest.mark.skipif(not os.path.exists(_SCRIPT), reason="daily-ingest.sh not deployed here")
def test_script_targets_hour_11():
    src = open(_SCRIPT, encoding="utf-8").read()
    assert re.search(r"^CAIRO_TARGET_HOUR=11\s*$", src, re.M)


@pytest.mark.skipif(not os.path.exists(_SCRIPT), reason="daily-ingest.sh not deployed here")
def test_script_reads_the_real_cairo_hour():
    src = open(_SCRIPT, encoding="utf-8").read()
    assert "TZ=Africa/Cairo date +%H" in src
    assert "timedelta(hours=3)" not in src, "no hard-coded Cairo offset allowed"


@pytest.mark.skipif(not os.path.exists(_SCRIPT), reason="daily-ingest.sh not deployed here")
def test_script_takes_a_single_run_lock():
    src = open(_SCRIPT, encoding="utf-8").read()
    assert "flock -n 9" in src


def _active_lines(path: str):
    """Executable lines only. Comments explain the old bug and must not trip a check."""
    out = []
    for raw in open(path, encoding="utf-8").read().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


@pytest.mark.skipif(not os.path.exists(_SCRIPT), reason="daily-ingest.sh not deployed here")
def test_script_does_not_abort_the_chain_on_one_failure():
    """The stall that hid the Drive gap for 2.5 months must not be reintroduced."""
    active = _active_lines(_SCRIPT)
    for line in active:
        assert not re.match(r"^set\s+-\S*e", line), (
            f"errexit is active on: {line!r} — one failed step would skip the rest")
    assert any(re.match(r"^set\s+-uo\s+pipefail$", l) for l in active)


@pytest.mark.skipif(not os.path.exists(_SCRIPT), reason="daily-ingest.sh not deployed here")
def test_every_step_records_its_own_status():
    """Isolation is only real if each step has its own failure branch."""
    src = open(_SCRIPT, encoding="utf-8").read()
    assert src.count("note_fail") >= 6, "expected one note_fail per step plus the helper"
    assert "FAILED_STEPS" in src


@pytest.mark.skipif(not os.path.exists(_SCRIPT), reason="daily-ingest.sh not deployed here")
def test_script_never_writes_calendar():
    src = open(_SCRIPT, encoding="utf-8").read()
    assert "human approval required" in src
    for forbidden in ("events insert", "events().insert", "calendar_write",
                      "nizam_gcal.py create", "nizam_gcal.py insert"):
        assert forbidden not in src, f"calendar write path present: {forbidden}"
