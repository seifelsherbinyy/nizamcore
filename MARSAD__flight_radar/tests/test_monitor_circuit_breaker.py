"""
Regression test for the MONITOR rate-limit circuit breaker.

Context: the daily MARSAD Daily Monitor GitHub Action hung for its full
30-minute timeout every day from 2026-05-21 onward because a sustained SerpApi
429 (quota exhaustion) was retried with full backoff for every single
route-carrier-cabin series, with no way to bail out early. run_monitor() now
aborts after MONITOR_RATE_LIMIT_ABORT_THRESHOLD consecutive rate-limited
series instead of grinding through the rest of the matrix.

EXECUTED_IN_SESSION: runs with pytest.
"""

from __future__ import annotations

from unittest import mock

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
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


def _seed_series(n: int) -> None:
    """Seed n distinct route-carrier-cabin series with one baseline observation each."""
    from radar.schema_store import append_observation

    for i in range(n):
        append_observation(
            origin="CAI",
            destination=f"D{i:02d}",
            carrier="MS",
            cabin="BUSINESS",
            price_usd=2000.0 + i,
            outbound_date="2027-04-01",
            return_date="2027-04-10",
            outbound_duration_hours=12.0,
            return_duration_hours=12.0,
            outbound_stops=0,
            return_stops=0,
            outbound_routing="CAI-D",
            return_routing="D-CAI",
            source="serpapi",
            observation_type="baseline",
        )


def test_monitor_aborts_after_consecutive_rate_limited_series(tmp_store, monkeypatch):
    """Sustained rate-limiting should abort early, not grind through every series."""
    monkeypatch.setattr("radar.stages.monitor.MONITOR_RATE_LIMIT_ABORT_THRESHOLD", 3)
    _seed_series(10)

    with mock.patch(
        "radar.stages.monitor.fetch_best_price",
        return_value=(None, ["SERPAPI_RATE_LIMITED: max retries exceeded (429)"], True),
    ) as mocked_fetch:
        from radar.stages.monitor import run_monitor

        stats = run_monitor()

    assert stats["aborted_reason"] == "source_rate_limited"
    # Stopped after hitting the threshold — did not call fetch for all 10 series.
    assert mocked_fetch.call_count == 3
    assert stats["routes_checked"] == 3
    assert stats["routes_unchecked_after_abort"] == 7


def test_monitor_does_not_abort_on_ordinary_no_data(tmp_store, monkeypatch):
    """Legitimate 'no data' (not rate-limited) responses must not trip the breaker."""
    monkeypatch.setattr("radar.stages.monitor.MONITOR_RATE_LIMIT_ABORT_THRESHOLD", 3)
    _seed_series(5)

    with mock.patch(
        "radar.stages.monitor.fetch_best_price",
        return_value=(None, ["no matching itineraries"], False),
    ) as mocked_fetch:
        from radar.stages.monitor import run_monitor

        stats = run_monitor()

    assert stats["aborted_reason"] is None
    assert mocked_fetch.call_count == 5
    assert stats["routes_checked"] == 5
    assert stats["routes_no_data"] == 5
