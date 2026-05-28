"""
Tests for STAGE 2 — MONITOR: Daily Delta.

EXECUTED_IN_SESSION: All tests run with pytest.
Uses mocked fetcher to avoid real API calls.
"""

from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import MagicMock, patch


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect schema_store paths to a temp directory."""
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


def _make_offer(price: float = 3000.0) -> "FlightOffer":
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
        price_usd=price,
        source="serpapi",
    )


class TestMonitorSkipsEmptyStore:
    def test_no_series_returns_skipped(self, tmp_store):
        from radar.stages.monitor import run_monitor
        result = run_monitor()
        assert result.get("skipped") == "no_series_in_store"


class TestMonitorDetectsDelta:
    def test_price_drop_recorded_in_delta(self, tmp_store):
        """After a baseline observation, a lower daily price must yield negative delta."""
        from radar.schema_store import append_observation, get_series
        from radar.stages.monitor import run_monitor

        # Seed a baseline observation
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )

        # Mock the fetcher to return a lower price
        lower_offer = _make_offer(2700.0)
        with patch("radar.stages.monitor.fetch_best_price", return_value=(lower_offer, [])):
            result = run_monitor()

        assert result["observations_written"] == 1
        assert result["routes_with_price_change"] == 1
        assert result["largest_drop_usd"] == pytest.approx(300.0)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        last = series[-1]
        assert last["price_usd"] == 2700.0
        assert last["delta_from_previous_usd"] == pytest.approx(-300.0)
        assert last["delta_pct"] == pytest.approx(-10.0)

    def test_stable_price_no_change_recorded(self, tmp_store):
        """Same price day-over-day: routes_with_price_change must be 0."""
        from radar.schema_store import append_observation
        from radar.stages.monitor import run_monitor

        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )

        same_offer = _make_offer(3000.0)
        with patch("radar.stages.monitor.fetch_best_price", return_value=(same_offer, [])):
            result = run_monitor()

        assert result["routes_with_price_change"] == 0
        assert result["observations_written"] == 1

    def test_no_data_returned_increments_no_data_counter(self, tmp_store):
        from radar.schema_store import append_observation
        from radar.stages.monitor import run_monitor

        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )

        with patch("radar.stages.monitor.fetch_best_price", return_value=(None, ["fetch error"])):
            result = run_monitor()

        assert result["routes_no_data"] == 1
        assert result["observations_written"] == 0

    def test_backup_created_before_monitoring(self, tmp_store):
        """Monitor must create a backup before writing new observations."""
        from radar.schema_store import append_observation
        from radar.stages.monitor import run_monitor

        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )

        backups_dir = tmp_store / "backups"
        assert not backups_dir.exists() or len(list(backups_dir.glob("*.json"))) == 0

        offer = _make_offer(2900.0)
        with patch("radar.stages.monitor.fetch_best_price", return_value=(offer, [])):
            run_monitor()

        assert backups_dir.exists()
        backup_files = list(backups_dir.glob("*.json"))
        assert len(backup_files) == 1


class TestMonitorPastWindow:
    def test_skips_monitoring_after_window_end(self, tmp_store, monkeypatch):
        """Monitor must return skipped status if today is past WINDOW_END."""
        monkeypatch.setattr("radar.stages.monitor.WINDOW_END", "2020-01-01")
        from radar.stages.monitor import run_monitor
        result = run_monitor()
        assert result.get("skipped") == "travel_window_ended"
