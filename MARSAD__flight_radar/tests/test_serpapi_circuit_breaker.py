"""
Regression test for the SerpApi quota circuit breaker.

Incident (2026-07-08): every scheduled MONITOR run since 2026-05-19 hit 429 on
every request and ground through the full 30-minute CI timeout retrying combos
that could never succeed. This test verifies the circuit breaker trips after
repeated full-retry exhaustions and stops making network calls for the rest
of the run.
"""
from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

_MARSAD = Path(__file__).resolve().parents[1]
if str(_MARSAD) not in sys.path:
    sys.path.insert(0, str(_MARSAD))

from radar.sources.serpapi_source import SerpApiSource  # noqa: E402


class _Resp429:
    status_code = 429
    content = b""


class SerpApiCircuitBreakerTest(unittest.TestCase):
    def setUp(self) -> None:
        SerpApiSource.reset_circuit_breaker()
        # window_start sits 5 days inside the ~305-day booking horizon, which
        # collapses _sample_dates() to exactly one probe date; window_end is
        # 20 days out so both the 9-night and 14-night options are in range.
        # Net effect: each search() call makes exactly two _fetch_one attempts
        # — deterministic call counts for this test.
        self.window_start = date.today() + timedelta(days=300)
        self.window_end = self.window_start + timedelta(days=20)

    def tearDown(self) -> None:
        SerpApiSource.reset_circuit_breaker()

    @patch("radar.sources.base.time.sleep", return_value=None)
    @patch("radar.sources.serpapi_source.requests.get", return_value=_Resp429())
    @patch("radar.sources.serpapi_source.SERPAPI_KEY", "fake-key")
    def test_breaker_trips_after_threshold_and_skips_network_calls(
        self, mock_get, mock_sleep
    ) -> None:
        # First combo: nights=9 and nights=14 each exhaust all 4 attempts against
        # a 429 — two full exhaustions, meeting _QUOTA_EXHAUSTION_THRESHOLD (2).
        src = SerpApiSource()
        src.search(
            origin="CAI", destination="JFK", cabin="BUSINESS",
            window_start=self.window_start, window_end=self.window_end,
        )
        self.assertTrue(SerpApiSource._quota_exhausted)
        calls_after_first_combo = mock_get.call_count
        self.assertEqual(calls_after_first_combo, 8)  # 2 sub-calls x 4 attempts

        # Second combo (fresh instance, as fetcher._build_source() creates per
        # route-carrier-cabin combo): breaker is already tripped — must return
        # immediately with zero new network calls.
        src2 = SerpApiSource()
        result = src2.search(
            origin="CAI", destination="LAX", cabin="BUSINESS",
            window_start=self.window_start, window_end=self.window_end,
        )
        self.assertEqual(mock_get.call_count, calls_after_first_combo)
        self.assertEqual(result.offers, [])
        self.assertTrue(any("quota exhausted" in e.lower() for e in result.errors))

    @patch("radar.sources.base.time.sleep", return_value=None)
    @patch("radar.sources.serpapi_source.SERPAPI_KEY", "fake-key")
    def test_successful_call_resets_the_breaker(self, mock_sleep) -> None:
        ok_payload = {"best_flights": [], "other_flights": []}

        class _Resp200:
            status_code = 200
            content = b"{}"

            def raise_for_status(self):
                return None

            def json(self):
                return ok_payload

        with patch(
            "radar.sources.serpapi_source.requests.get", return_value=_Resp200()
        ):
            src = SerpApiSource()
            src.search(
                origin="CAI", destination="JFK", cabin="BUSINESS",
                window_start=self.window_start, window_end=self.window_end,
            )

        self.assertFalse(SerpApiSource._quota_exhausted)
        self.assertEqual(SerpApiSource._consecutive_quota_exhaustions, 0)


if __name__ == "__main__":
    unittest.main()
