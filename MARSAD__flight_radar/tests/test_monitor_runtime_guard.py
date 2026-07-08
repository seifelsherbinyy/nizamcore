"""
Regression test for the MONITOR stage wall-clock safety net.

Incident (2026-07-08): MONITOR had no time budget at all — a rate-limited
source made it grind through every combination until GitHub Actions hard-
cancelled the job at the 30-minute CI timeout, skipping the final commit
step entirely. This test verifies run_monitor() stops itself early and
reports which combinations were left for the next scheduled run.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_MARSAD = Path(__file__).resolve().parents[1]
if str(_MARSAD) not in sys.path:
    sys.path.insert(0, str(_MARSAD))

from radar.stages import monitor as monitor_mod  # noqa: E402


class MonitorRuntimeGuardTest(unittest.TestCase):
    def test_stops_early_once_max_runtime_exceeded(self) -> None:
        all_keys = [
            {"origin": "CAI", "destination": d, "carrier": "MS", "cabin": "BUSINESS", "observation_count": 1}
            for d in ["JFK", "LAX", "ORD", "ATL"]
        ]

        # Simulate the clock advancing past MONITOR_MAX_RUNTIME_SEC right after
        # the first combo is checked, so every combo after it must be skipped.
        fake_clock = iter([0.0, 0.0, 9999.0, 9999.0, 9999.0, 9999.0, 9999.0])

        with patch.object(monitor_mod, "backup_store", return_value=None), \
             patch.object(monitor_mod, "get_all_series_keys", return_value=all_keys), \
             patch.object(monitor_mod, "fetch_best_price", return_value=(None, [])), \
             patch.object(monitor_mod, "MONITOR_MAX_RUNTIME_SEC", 1.0), \
             patch("radar.stages.monitor.time.monotonic", side_effect=lambda: next(fake_clock, 9999.0)):
            stats = monitor_mod.run_monitor()

        self.assertTrue(stats["stopped_early"])
        self.assertLess(stats["routes_checked"], len(all_keys))


if __name__ == "__main__":
    unittest.main()
