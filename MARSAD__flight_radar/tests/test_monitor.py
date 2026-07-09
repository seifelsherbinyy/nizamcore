"""
Tests for MONITOR (Stage 2) — round-robin batching, lean re-check, circuit breaker.

EXECUTED_IN_SESSION: All tests in this file run with pytest.

Context: the daily MONITOR GitHub Action was silently failing on every run for
weeks because it resampled DISCOVER's full date/night matrix (up to 6 SerpApi
calls per series) for every known series with no cap, exhausting the SerpApi
free-tier quota and then burning the job's timeout retrying 429s. These tests
cover the fix: a lean single-call re-check of the known itinerary, a
round-robin batch cap (MONITOR_KEYS_PER_RUN), and a circuit breaker that
aborts early on repeated no-data results instead of retrying every series.
"""

from datetime import date
from unittest.mock import patch

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect all schema_store paths to a temporary directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    alerts_dir = tmp_path / "alerts"
    alerts_dir.mkdir()

    monkeypatch.setattr("radar.config.DATA_DIR", data_dir)
    monkeypatch.setattr("radar.config.ALERTS_DIR", alerts_dir)
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr("radar.config.BACKUPS_DIR", data_dir / "backups")

    import radar.schema_store as ss
    monkeypatch.setattr(ss, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(ss, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(ss, "BACKUPS_DIR", data_dir / "backups")

    return data_dir


def _seed_series(count: int):
    """Seed `count` distinct route-carrier-cabin series with one baseline observation each."""
    from radar.schema_store import append_observation

    destinations = ["JFK", "LAX", "ORD", "ATL", "MIA", "SFO", "IAD", "BOS", "EWR", "DFW", "SEA", "LAS"]
    for i in range(count):
        append_observation(
            origin="CAI", destination=destinations[i % len(destinations)],
            carrier="MS" if i < len(destinations) else "LH",
            cabin="BUSINESS" if i % 2 == 0 else "PREMIUM_ECONOMY",
            price_usd=3000.0 + i,
            outbound_date="2027-04-01", return_date="2027-04-10",
            outbound_duration_hours=14.0, return_duration_hours=14.0,
            outbound_stops=0, return_stops=0,
            outbound_routing="CAI-JFK", return_routing="JFK-CAI",
            source="serpapi", observation_type="baseline",
        )


class TestSelectBatch:
    def test_batch_capped_at_size(self):
        from radar.stages.monitor import _select_batch
        keys = list(range(24))
        batch, _ = _select_batch(keys, cursor=0, batch_size=8)
        assert len(batch) == 8
        assert batch == keys[0:8]

    def test_batch_wraps_around(self):
        from radar.stages.monitor import _select_batch
        keys = list(range(10))
        batch, next_cursor = _select_batch(keys, cursor=7, batch_size=5)
        assert batch == [7, 8, 9, 0, 1]
        assert next_cursor == 2

    def test_full_rotation_covers_every_key_without_repeats_first(self):
        from radar.stages.monitor import _select_batch
        keys = list(range(24))
        cursor = 0
        seen = []
        for _ in range(3):
            batch, cursor = _select_batch(keys, cursor, 8)
            seen.extend(batch)
        assert seen == keys  # 3 batches of 8 cover all 24 exactly once

    def test_batch_size_larger_than_keys_returns_all(self):
        from radar.stages.monitor import _select_batch
        keys = [1, 2, 3]
        batch, next_cursor = _select_batch(keys, cursor=0, batch_size=8)
        assert batch == [1, 2, 3]
        assert next_cursor == 0

    def test_empty_keys(self):
        from radar.stages.monitor import _select_batch
        batch, next_cursor = _select_batch([], cursor=5, batch_size=8)
        assert batch == []
        assert next_cursor == 0


class TestMonitorCursorPersistence:
    def test_cursor_defaults_to_zero(self, tmp_store):
        from radar.schema_store import get_monitor_cursor
        assert get_monitor_cursor() == 0

    def test_cursor_round_trips(self, tmp_store):
        from radar.schema_store import get_monitor_cursor, set_monitor_cursor
        set_monitor_cursor(5)
        assert get_monitor_cursor() == 5


class TestRunMonitorBatching:
    def test_only_checks_monitor_keys_per_run(self, tmp_store, monkeypatch):
        """With 24 known series and MONITOR_KEYS_PER_RUN=8, only 8 get fetched."""
        _seed_series(24)
        monkeypatch.setattr("radar.stages.monitor.MONITOR_KEYS_PER_RUN", 8)
        monkeypatch.setattr("radar.stages.monitor.MONITOR_CONSECUTIVE_FAILURE_LIMIT", 999)

        calls = []

        def fake_fetch(*, origin, destination, cabin, carrier, outbound_date, return_date):
            calls.append((origin, destination, carrier, cabin))
            from radar.sources.base import FlightOffer
            return FlightOffer(
                origin=origin, destination=destination, cabin=cabin, carrier=carrier,
                outbound_date=outbound_date, return_date=return_date,
                outbound_duration_hours=14.0, return_duration_hours=14.0,
                outbound_stops=0, return_stops=0,
                outbound_routing=f"{origin}-{destination}", return_routing=f"{destination}-{origin}",
                price_usd=2500.0, source="serpapi",
            ), []

        with patch("radar.stages.monitor.fetch_price_for_known_itinerary", side_effect=fake_fetch):
            from radar.stages.monitor import run_monitor
            stats = run_monitor()

        assert len(calls) == 8
        assert stats["batch_size"] == 8
        assert stats["total_series"] == 24
        assert stats["routes_checked"] == 8

    def test_lean_recheck_uses_prior_observed_dates(self, tmp_store, monkeypatch):
        """MONITOR must re-query the exact previously-observed date pair, not resample."""
        _seed_series(1)
        monkeypatch.setattr("radar.stages.monitor.MONITOR_KEYS_PER_RUN", 8)

        received = {}

        def fake_fetch(*, origin, destination, cabin, carrier, outbound_date, return_date):
            received["outbound_date"] = outbound_date
            received["return_date"] = return_date
            from radar.sources.base import FlightOffer
            return FlightOffer(
                origin=origin, destination=destination, cabin=cabin, carrier=carrier,
                outbound_date=outbound_date, return_date=return_date,
                outbound_duration_hours=14.0, return_duration_hours=14.0,
                outbound_stops=0, return_stops=0,
                outbound_routing="CAI-JFK", return_routing="JFK-CAI",
                price_usd=2500.0, source="serpapi",
            ), []

        with patch("radar.stages.monitor.fetch_price_for_known_itinerary", side_effect=fake_fetch):
            from radar.stages.monitor import run_monitor
            run_monitor()

        assert received["outbound_date"] == date(2027, 4, 1)
        assert received["return_date"] == date(2027, 4, 10)

    def test_cursor_advances_across_runs(self, tmp_store, monkeypatch):
        _seed_series(24)
        monkeypatch.setattr("radar.stages.monitor.MONITOR_KEYS_PER_RUN", 8)

        def fake_fetch(**kwargs):
            return None, ["no offer for test"]

        from radar.schema_store import get_monitor_cursor
        with patch("radar.stages.monitor.fetch_price_for_known_itinerary", side_effect=fake_fetch):
            from radar.stages.monitor import run_monitor
            monkeypatch.setattr("radar.stages.monitor.MONITOR_CONSECUTIVE_FAILURE_LIMIT", 999)
            run_monitor()
        assert get_monitor_cursor() == 8


class TestCircuitBreaker:
    def test_aborts_after_consecutive_failures(self, tmp_store, monkeypatch):
        _seed_series(24)
        monkeypatch.setattr("radar.stages.monitor.MONITOR_KEYS_PER_RUN", 8)
        monkeypatch.setattr("radar.stages.monitor.MONITOR_CONSECUTIVE_FAILURE_LIMIT", 3)

        def always_fails(**kwargs):
            return None, ["SerpApi max retries exceeded"]

        with patch("radar.stages.monitor.fetch_price_for_known_itinerary", side_effect=always_fails):
            from radar.stages.monitor import run_monitor
            stats = run_monitor()

        assert stats["aborted_early"] is True
        assert stats["routes_checked"] == 3  # stopped after 3 consecutive failures
        assert stats["routes_no_data"] == 3

    def test_does_not_abort_when_failures_not_consecutive(self, tmp_store, monkeypatch):
        _seed_series(8)
        monkeypatch.setattr("radar.stages.monitor.MONITOR_KEYS_PER_RUN", 8)
        monkeypatch.setattr("radar.stages.monitor.MONITOR_CONSECUTIVE_FAILURE_LIMIT", 3)

        call_count = {"n": 0}

        def alternating(*, origin, destination, cabin, carrier, outbound_date, return_date):
            call_count["n"] += 1
            if call_count["n"] % 2 == 0:
                return None, ["no data"]
            from radar.sources.base import FlightOffer
            return FlightOffer(
                origin=origin, destination=destination, cabin=cabin, carrier=carrier,
                outbound_date=outbound_date, return_date=return_date,
                outbound_duration_hours=14.0, return_duration_hours=14.0,
                outbound_stops=0, return_stops=0,
                outbound_routing="CAI-X", return_routing="X-CAI",
                price_usd=2500.0, source="serpapi",
            ), []

        with patch("radar.stages.monitor.fetch_price_for_known_itinerary", side_effect=alternating):
            from radar.stages.monitor import run_monitor
            stats = run_monitor()

        assert stats["aborted_early"] is False
        assert stats["routes_checked"] == 8


class TestRunMonitorEdgeCases:
    def test_no_series_in_store_returns_skipped(self, tmp_store):
        from radar.stages.monitor import run_monitor
        stats = run_monitor()
        assert stats.get("skipped") == "no_series_in_store"

    def test_series_with_no_prior_observation_is_skipped_not_fetched(self, tmp_store, monkeypatch):
        """A series with an empty observation_series (shouldn't normally happen) must not
        trigger a fetch — there's no known date pair to re-check."""
        from radar.schema_store import load_store, _safe_write, _ensure_series
        store = load_store()
        _ensure_series(store, "CAI", "JFK", "MS", "BUSINESS")
        _safe_write(store)

        called = {"n": 0}

        def fake_fetch(**kwargs):
            called["n"] += 1
            return None, []

        with patch("radar.stages.monitor.fetch_price_for_known_itinerary", side_effect=fake_fetch):
            from radar.stages.monitor import run_monitor
            stats = run_monitor()

        assert called["n"] == 0
        assert stats["routes_no_data"] == 1
