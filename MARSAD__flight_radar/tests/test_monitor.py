"""
Tests for STAGE 2 — MONITOR.

EXECUTED_IN_SESSION: All tests in this file run with pytest.

Regression coverage for the 2026-05-21 production incident: run_monitor()
iterated one source fetch per CARRIER series instead of per (route, cabin)
group, multiplying SerpApi calls 2-3x and exceeding the 30-minute CI job
timeout every day for 41 consecutive days. These tests pin the fix:
fetch once per (route, cabin) group, and cap groups processed per run to a
session budget so a run can never grow unbounded with the store.
"""

from datetime import date
from unittest import mock

import pytest

from radar.sources.base import FlightOffer


def _offer(destination, carrier, cabin, price):
    return FlightOffer(
        origin="CAI",
        destination=destination,
        cabin=cabin,
        carrier=carrier,
        outbound_date=date(2027, 4, 1),
        return_date=date(2027, 4, 12),
        outbound_duration_hours=14.0,
        return_duration_hours=14.0,
        outbound_stops=1,
        return_stops=1,
        outbound_routing="CAI-X-" + destination,
        return_routing=destination + "-X-CAI",
        price_usd=price,
        source="serpapi",
    )


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


def _seed(carrier, cabin="BUSINESS", destination="JFK", price=3000.0):
    from radar.schema_store import append_observation
    append_observation(
        origin="CAI", destination=destination, carrier=carrier, cabin=cabin,
        price_usd=price,
        outbound_date="2027-04-01", return_date="2027-04-12",
        outbound_duration_hours=14.0, return_duration_hours=14.0,
        outbound_stops=1, return_stops=1,
        outbound_routing="CAI-X-" + destination, return_routing=destination + "-X-CAI",
        source="serpapi", observation_type="baseline",
    )


class TestGroupedFetch:
    def test_one_fetch_serves_all_carriers_sharing_route_and_cabin(self, tmp_store):
        """Three carrier series on the same route+cabin must cost ONE source fetch."""
        from radar.stages.monitor import run_monitor

        _seed("EK", destination="JFK")
        _seed("QR", destination="JFK")
        _seed("MS", destination="JFK")

        with mock.patch(
            "radar.stages.monitor.fetch_qualifying_offers",
            return_value=([
                _offer("JFK", "EK", "BUSINESS", 2900.0),
                _offer("JFK", "QR", "BUSINESS", 3100.0),
                _offer("JFK", "MS", "BUSINESS", 2800.0),
            ], []),
        ) as mocked_fetch:
            stats = run_monitor()

        assert mocked_fetch.call_count == 1
        assert stats["groups_checked"] == 1
        assert stats["routes_checked"] == 3
        assert stats["observations_written"] == 3

    def test_separate_routes_cost_separate_fetches(self, tmp_store):
        from radar.stages.monitor import run_monitor

        _seed("EK", destination="JFK")
        _seed("EK", destination="LAX")

        with mock.patch(
            "radar.stages.monitor.fetch_qualifying_offers",
            return_value=([], []),
        ) as mocked_fetch:
            run_monitor()

        assert mocked_fetch.call_count == 2

    def test_carrier_missing_from_results_is_no_data_not_error(self, tmp_store):
        from radar.stages.monitor import run_monitor

        _seed("EK", destination="JFK")
        _seed("QR", destination="JFK")

        with mock.patch(
            "radar.stages.monitor.fetch_qualifying_offers",
            return_value=([_offer("JFK", "EK", "BUSINESS", 2900.0)], []),
        ):
            stats = run_monitor()

        assert stats["routes_checked"] == 2
        assert stats["routes_no_data"] == 1
        assert stats["observations_written"] == 1


class TestSessionBudget:
    def test_groups_beyond_budget_are_deferred_not_dropped(self, tmp_store, monkeypatch):
        """
        With MAX_REQUESTS_PER_SESSION small enough to cover only one group,
        the rest must be reported as skipped — never silently lost.
        """
        from radar.stages import monitor as monitor_mod

        monkeypatch.setattr(monitor_mod, "MAX_REQUESTS_PER_SESSION", 6)  # = 1 group budget

        _seed("EK", destination="JFK")
        _seed("EK", destination="LAX")
        _seed("EK", destination="ORD")

        with mock.patch(
            "radar.stages.monitor.fetch_qualifying_offers",
            return_value=([], []),
        ) as mocked_fetch:
            stats = monitor_mod.run_monitor()

        assert mocked_fetch.call_count == 1
        assert stats["groups_checked"] == 1
        assert stats["groups_skipped_session_budget"] == 2

    def test_stalest_series_checked_first(self, tmp_store, monkeypatch):
        """When the budget can't cover every group, the least-recently-observed
        group must be picked, so coverage rotates instead of starving the same
        series every day."""
        from radar.schema_store import append_observation
        from radar.stages import monitor as monitor_mod

        monkeypatch.setattr(monitor_mod, "MAX_REQUESTS_PER_SESSION", 6)  # = 1 group budget

        _seed("EK", destination="JFK")  # observed first -> stalest after LAX is re-touched
        _seed("EK", destination="LAX")

        # Touch LAX again so JFK is now the stalest series.
        append_observation(
            origin="CAI", destination="LAX", carrier="EK", cabin="BUSINESS",
            price_usd=2950.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.0, return_duration_hours=14.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-X-LAX", return_routing="LAX-X-CAI",
            source="serpapi", observation_type="daily",
        )

        seen_destinations = []

        def _fake_fetch(origin, destination, cabin, window_start, window_end):
            seen_destinations.append(destination)
            return [], []

        with mock.patch("radar.stages.monitor.fetch_qualifying_offers", side_effect=_fake_fetch):
            monitor_mod.run_monitor()

        assert seen_destinations == ["JFK"]
