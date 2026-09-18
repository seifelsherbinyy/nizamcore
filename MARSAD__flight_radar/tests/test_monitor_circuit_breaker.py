"""
Tests for the MONITOR-stage circuit breaker (Stage 2).

Root cause this guards against: a persistently rate-limited source (quota
exhausted or invalid key) returns HTTP 429 on every single call. Without a
breaker, run_monitor() retries every series in the store the same way,
burning ~30s of backoff per series and guaranteeing the daily CI job times
out silently (30 min) without writing anything or reaching ALERT/FORECAST.

EXECUTED_IN_SESSION: All tests in this file run with pytest.
"""

from unittest import mock

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    monkeypatch.setattr("radar.config.DATA_DIR", data_dir)
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr("radar.config.BACKUPS_DIR", data_dir / "backups")

    import radar.schema_store as ss
    monkeypatch.setattr(ss, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(ss, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(ss, "BACKUPS_DIR", data_dir / "backups")

    return data_dir


def _seed_series(n: int):
    """Fake get_all_series_keys() output — n distinct route/carrier/cabin combos."""
    return [
        {
            "origin": "CAI",
            "destination": f"DEST{i}",
            "carrier": "MS",
            "cabin": "BUSINESS",
            "observation_count": 1,
        }
        for i in range(n)
    ]


class TestCircuitBreaker:
    def test_aborts_after_threshold_consecutive_rate_limits(self, tmp_store):
        """10 series all rate-limited must abort well before checking all 10."""
        from radar.stages import monitor as monitor_mod

        with mock.patch.object(monitor_mod, "get_all_series_keys", return_value=_seed_series(10)), \
             mock.patch.object(monitor_mod, "backup_store", return_value=None), \
             mock.patch.object(monitor_mod, "fetch_best_price", return_value=(None, ["429"], True)):
            stats = monitor_mod.run_monitor()

        assert stats["aborted_reason"] is not None
        # Must stop at the breaker threshold (3), not grind through all 10.
        assert stats["routes_checked"] == 3

    def test_does_not_abort_on_transient_single_rate_limit(self, tmp_store):
        """A single rate-limited combo amid otherwise-fine ones must not abort the run."""
        from radar.stages import monitor as monitor_mod

        call_results = iter([
            (None, ["429"], True),
            (None, [], False),
            (None, [], False),
        ])

        with mock.patch.object(monitor_mod, "get_all_series_keys", return_value=_seed_series(3)), \
             mock.patch.object(monitor_mod, "backup_store", return_value=None), \
             mock.patch.object(monitor_mod, "fetch_best_price", side_effect=lambda **kw: next(call_results)):
            stats = monitor_mod.run_monitor()

        assert stats["aborted_reason"] is None
        assert stats["routes_checked"] == 3

    def test_no_rate_limiting_runs_to_completion(self, tmp_store):
        from radar.stages import monitor as monitor_mod

        with mock.patch.object(monitor_mod, "get_all_series_keys", return_value=_seed_series(5)), \
             mock.patch.object(monitor_mod, "backup_store", return_value=None), \
             mock.patch.object(monitor_mod, "fetch_best_price", return_value=(None, [], False)):
            stats = monitor_mod.run_monitor()

        assert stats["aborted_reason"] is None
        assert stats["routes_checked"] == 5
        assert stats["routes_no_data"] == 5


class TestMainExitCode:
    def test_cmd_monitor_returns_nonzero_when_aborted(self):
        from radar import main as main_mod

        with mock.patch(
            "radar.stages.monitor.run_monitor",
            return_value={"stage": "MONITOR", "aborted_reason": "persistent_rate_limit"},
        ):
            assert main_mod.cmd_monitor(argparse_namespace()) == 1

    def test_cmd_monitor_returns_zero_on_clean_run(self):
        from radar import main as main_mod

        with mock.patch(
            "radar.stages.monitor.run_monitor",
            return_value={"stage": "MONITOR", "aborted_reason": None},
        ):
            assert main_mod.cmd_monitor(argparse_namespace()) == 0


def argparse_namespace():
    import argparse
    return argparse.Namespace()
