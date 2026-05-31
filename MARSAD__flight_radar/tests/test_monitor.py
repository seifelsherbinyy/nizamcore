"""
Tests for the MONITOR stage (Stage 2).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses mocks to avoid any real API calls — tests delta logic and store integration only.
"""

from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import MagicMock, patch


@pytest.fixture()
def tmp_store_with_series(tmp_path, monkeypatch):
    """
    Redirect schema_store to a temp directory and pre-seed it with one series
    (CAI-JFK / EK / BUSINESS) having a single baseline observation at $3000.
    """
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

    from radar.schema_store import append_observation
    append_observation(
        origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
        price_usd=3000.0,
        outbound_date="2027-04-01", return_date="2027-04-12",
        outbound_duration_hours=14.5, return_duration_hours=15.0,
        outbound_stops=1, return_stops=1,
        outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
        source="serpapi", observation_type="baseline",
    )
    return data_dir


def _make_offer(price_usd: float):
    """Build a minimal FlightOffer mock with the given price."""
    from radar.sources.base import FlightOffer
    return FlightOffer(
        origin="CAI",
        destination="JFK",
        cabin="BUSINESS",
        carrier="EK",
        outbound_date=date(2027, 4, 1),
        return_date=date(2027, 4, 12),
        outbound_duration_hours=14.5,
        return_duration_hours=15.0,
        outbound_stops=1,
        return_stops=1,
        outbound_routing="CAI-DXB-JFK",
        return_routing="JFK-DXB-CAI",
        price_usd=price_usd,
        source="serpapi",
    )


class TestMonitorNominal:
    def test_monitor_appends_daily_observation(self, tmp_store_with_series):
        """A successful fetch should append a 'daily' observation."""
        with patch("radar.stages.monitor.fetch_best_price") as mock_fetch:
            mock_fetch.return_value = (_make_offer(2900.0), [])

            from radar.stages.monitor import run_monitor
            stats = run_monitor()

        assert stats["observations_written"] == 1
        assert stats["routes_checked"] == 1

        from radar.schema_store import get_series
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        assert series[-1]["observation_type"] == "daily"
        assert series[-1]["price_usd"] == 2900.0

    def test_monitor_delta_calculated_correctly(self, tmp_store_with_series):
        """Delta from baseline ($3000) to new price ($2700) must be -300 and -10%."""
        with patch("radar.stages.monitor.fetch_best_price") as mock_fetch:
            mock_fetch.return_value = (_make_offer(2700.0), [])

            from radar.stages.monitor import run_monitor
            run_monitor()

        from radar.schema_store import get_series
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        last = series[-1]
        assert last["delta_from_previous_usd"] == -300.0
        assert last["delta_pct"] == -10.0

    def test_monitor_tracks_largest_drop(self, tmp_store_with_series):
        """stats['largest_drop_usd'] must reflect the biggest single-day price fall."""
        with patch("radar.stages.monitor.fetch_best_price") as mock_fetch:
            mock_fetch.return_value = (_make_offer(2400.0), [])  # $600 drop from $3000

            from radar.stages.monitor import run_monitor
            stats = run_monitor()

        assert stats["largest_drop_usd"] == 600.0
        assert stats["largest_drop_series"] == "CAI-JFK/EK/BUSINESS"

    def test_monitor_price_increase_not_flagged_as_drop(self, tmp_store_with_series):
        """A price increase must NOT update largest_drop_usd."""
        with patch("radar.stages.monitor.fetch_best_price") as mock_fetch:
            mock_fetch.return_value = (_make_offer(3500.0), [])  # $500 increase

            from radar.stages.monitor import run_monitor
            stats = run_monitor()

        assert stats["largest_drop_usd"] == 0.0
        assert stats["routes_with_price_change"] == 1


class TestMonitorNoData:
    def test_monitor_no_offer_increments_routes_no_data(self, tmp_store_with_series):
        """When source returns None, routes_no_data must increment and no observation written."""
        with patch("radar.stages.monitor.fetch_best_price") as mock_fetch:
            mock_fetch.return_value = (None, ["source timeout"])

            from radar.stages.monitor import run_monitor
            stats = run_monitor()

        assert stats["routes_no_data"] == 1
        assert stats["observations_written"] == 0

        from radar.schema_store import get_series
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1  # still just the baseline — nothing new written


class TestMonitorEmptyStore:
    def test_monitor_warns_on_empty_store(self, tmp_path, monkeypatch):
        """Monitor must return a skipped status when no series exist yet."""
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

        from radar.stages.monitor import run_monitor
        stats = run_monitor()

        assert stats.get("skipped") == "no_series_in_store"


class TestMonitorFetchErrors:
    def test_fetch_errors_collected_in_stats(self, tmp_store_with_series):
        """Error strings returned by the source must appear in stats['fetch_errors']."""
        with patch("radar.stages.monitor.fetch_best_price") as mock_fetch:
            mock_fetch.return_value = (None, ["429 rate limited", "timeout"])

            from radar.stages.monitor import run_monitor
            stats = run_monitor()

        assert "429 rate limited" in stats["fetch_errors"]
        assert "timeout" in stats["fetch_errors"]
