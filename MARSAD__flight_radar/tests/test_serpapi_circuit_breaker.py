"""
Tests for the SerpApi source's process-wide rate-limit circuit breaker.

Context: SerpApiSource() is re-instantiated per (route, carrier, cabin) combo,
so per-instance counters never accumulate. When the account's monthly quota
is exhausted every request 429s forever, and without a breaker the daily
monitor loop burns its full retry budget on every single combo until the CI
job timeout kills it (observed: 51 consecutive days of workflow runs
cancelled at the 30-minute job timeout with zero data collected).

EXECUTED_IN_SESSION: all tests in this file run with pytest + unittest.mock.
"""

from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture(autouse=True)
def _reset_breaker():
    """Circuit breaker state is module-level — reset it before and after each test."""
    from radar.sources import serpapi_source as mod
    mod.reset_circuit_breaker()
    yield
    mod.reset_circuit_breaker()


def _mock_429_response():
    resp = MagicMock()
    resp.status_code = 429
    return resp


class TestCircuitBreaker:
    def test_trips_after_threshold_consecutive_429s(self):
        from radar.sources import serpapi_source as mod

        with patch.object(mod, "SERPAPI_KEY", "fake-key"), \
             patch("time.sleep", return_value=None), \
             patch("requests.get", return_value=_mock_429_response()) as mock_get:

            src = mod.SerpApiSource()
            window_start = date.today() + timedelta(days=200)
            window_end = window_start + timedelta(days=14)

            assert not mod.is_quota_likely_exhausted()

            # First combo: every sub-fetch 429s — this alone should trip the
            # breaker (>= _QUOTA_EXHAUSTED_TRIP_THRESHOLD exhausted sub-fetches).
            result = src.search(
                origin="CAI", destination="JFK", cabin="BUSINESS",
                window_start=window_start, window_end=window_end,
            )

            assert mod.is_quota_likely_exhausted()
            assert result.offers == []
            assert result.rate_limited is True
            calls_made_before_trip = mock_get.call_count
            assert calls_made_before_trip > 0

            # A subsequent combo must short-circuit — no new HTTP calls at all.
            result2 = src.search(
                origin="CAI", destination="LAX", cabin="BUSINESS",
                window_start=window_start, window_end=window_end,
            )
            assert result2.offers == []
            assert result2.rate_limited is True
            assert mock_get.call_count == calls_made_before_trip, (
                "breaker should prevent any further HTTP requests once tripped"
            )

    def test_resets_on_success(self):
        from radar.sources import serpapi_source as mod

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"best_flights": [], "other_flights": []}
        ok_resp.raise_for_status.return_value = None

        with patch.object(mod, "SERPAPI_KEY", "fake-key"), \
             patch("time.sleep", return_value=None), \
             patch("requests.get", return_value=ok_resp):

            src = mod.SerpApiSource()
            window_start = date.today() + timedelta(days=200)
            window_end = window_start + timedelta(days=14)

            src.search(
                origin="CAI", destination="JFK", cabin="BUSINESS",
                window_start=window_start, window_end=window_end,
            )

            assert not mod.is_quota_likely_exhausted()
            assert mod._consecutive_exhausted_combos == 0
