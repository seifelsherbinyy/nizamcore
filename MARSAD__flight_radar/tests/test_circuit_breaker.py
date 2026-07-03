"""
Tests for the SerpApi circuit breaker (sustained-429 detection).

EXECUTED_IN_SESSION: All tests in this file run with pytest.

Context: the daily monitor cron (06:00 UTC, 30-minute job timeout) was found
grinding through the full 2s/4s/8s/16s backoff cycle for every single
route-carrier-cabin combination when SerpApi returns 429 on every request
(exhausted quota or invalid key) — reliably burning the entire job timeout
without writing a single observation, and showing up as a silent "cancelled"
run rather than a clear failure. These tests verify the fix: after
_CIRCUIT_BREAKER_THRESHOLD consecutive fully-exhausted fetches, the source
raises SourceExhausted instead of continuing to grind, and a single
successful fetch resets the counter.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _reset_circuit_breaker():
    from radar.sources.serpapi_source import SerpApiSource
    SerpApiSource._consecutive_exhausted = 0
    yield
    SerpApiSource._consecutive_exhausted = 0


def _rate_limited_response():
    resp = MagicMock()
    resp.status_code = 429
    return resp


def _ok_response():
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"best_flights": [], "other_flights": []}
    resp.raise_for_status.return_value = None
    return resp


class TestCircuitBreaker:
    def test_trips_after_threshold_consecutive_exhausted_fetches(self):
        from radar.sources.base import SourceExhausted
        from radar.sources.serpapi_source import SerpApiSource, _CIRCUIT_BREAKER_THRESHOLD

        src = SerpApiSource()

        with patch("radar.sources.serpapi_source.SERPAPI_KEY", "test-key"), \
             patch("radar.sources.serpapi_source.requests.get", return_value=_rate_limited_response()), \
             patch("radar.sources.base.time.sleep"):

            # Every fetch is fully rate-limited — should not raise before the threshold
            for _ in range(_CIRCUIT_BREAKER_THRESHOLD - 1):
                offers, errors = src._fetch_one(
                    origin="CAI", destination="JFK",
                    dep_date=date(2027, 3, 15), ret_date=date(2027, 3, 24),
                    travel_class=3, cabin="BUSINESS",
                )
                assert offers == []
                assert errors

            # The Nth consecutive exhausted fetch trips the breaker
            with pytest.raises(SourceExhausted):
                src._fetch_one(
                    origin="CAI", destination="JFK",
                    dep_date=date(2027, 3, 15), ret_date=date(2027, 3, 24),
                    travel_class=3, cabin="BUSINESS",
                )

    def test_successful_fetch_resets_counter(self):
        from radar.sources.base import SourceExhausted
        from radar.sources.serpapi_source import SerpApiSource, _CIRCUIT_BREAKER_THRESHOLD

        src = SerpApiSource()

        with patch("radar.sources.serpapi_source.SERPAPI_KEY", "test-key"), \
             patch("radar.sources.base.time.sleep"):

            # Fail once (below threshold)
            with patch("radar.sources.serpapi_source.requests.get", return_value=_rate_limited_response()):
                src._fetch_one(
                    origin="CAI", destination="JFK",
                    dep_date=date(2027, 3, 15), ret_date=date(2027, 3, 24),
                    travel_class=3, cabin="BUSINESS",
                )
            assert SerpApiSource._consecutive_exhausted == 1

            # A clean success resets the streak
            with patch("radar.sources.serpapi_source.requests.get", return_value=_ok_response()):
                offers, errors = src._fetch_one(
                    origin="CAI", destination="JFK",
                    dep_date=date(2027, 3, 15), ret_date=date(2027, 3, 24),
                    travel_class=3, cabin="BUSINESS",
                )
            assert errors == []
            assert SerpApiSource._consecutive_exhausted == 0

            # Now it takes a full new streak of THRESHOLD to trip again
            with patch("radar.sources.serpapi_source.requests.get", return_value=_rate_limited_response()):
                for _ in range(_CIRCUIT_BREAKER_THRESHOLD - 1):
                    src._fetch_one(
                        origin="CAI", destination="JFK",
                        dep_date=date(2027, 3, 15), ret_date=date(2027, 3, 24),
                        travel_class=3, cabin="BUSINESS",
                    )
                with pytest.raises(SourceExhausted):
                    src._fetch_one(
                        origin="CAI", destination="JFK",
                        dep_date=date(2027, 3, 15), ret_date=date(2027, 3, 24),
                        travel_class=3, cabin="BUSINESS",
                    )


class TestMonitorStageStopsEarlyOnCircuitBreaker:
    def test_run_monitor_records_circuit_breaker_and_stops(self):
        from radar.sources.base import SourceExhausted

        keys = [
            {"origin": "CAI", "destination": "JFK", "carrier": "MS", "cabin": "BUSINESS"},
            {"origin": "CAI", "destination": "LAX", "carrier": "MS", "cabin": "BUSINESS"},
        ]

        with patch("radar.stages.monitor.get_all_series_keys", return_value=keys), \
             patch("radar.stages.monitor.backup_store", return_value=None), \
             patch("radar.stages.monitor.fetch_best_price", side_effect=SourceExhausted("quota exhausted")):
            from radar.stages.monitor import run_monitor
            stats = run_monitor()

        assert stats["circuit_breaker_tripped"] == "quota exhausted"
        assert stats["routes_checked"] == 0  # broke out before incrementing
