"""
Tests for STAGE 1 — DISCOVER: Baseline Collection.

EXECUTED_IN_SESSION: All tests run with pytest.
Uses mocked fetcher to avoid real API calls.
"""

from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import patch


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


def _make_offer(dest: str = "JFK", cabin: str = "BUSINESS", price: float = 3000.0):
    from radar.sources.base import FlightOffer
    return FlightOffer(
        origin="CAI",
        destination=dest,
        cabin=cabin,
        carrier="EK",
        outbound_date=date(2027, 4, 1),
        return_date=date(2027, 4, 12),
        outbound_duration_hours=14.5,
        return_duration_hours=15.0,
        outbound_stops=1,
        return_stops=1,
        outbound_routing=f"CAI-DXB-{dest}",
        return_routing=f"{dest}-DXB-CAI",
        price_usd=price,
        source="serpapi",
    )


class TestDiscoverDryRun:
    def test_dry_run_returns_pending_count(self, tmp_store):
        from radar.stages.discover import run_discover
        result = run_discover(dry_run=True)
        assert result["dry_run"] is True
        assert result["pending"] == 24  # 12 destinations × 2 cabins
        assert result["total_combinations"] == 24


class TestDiscoverBaselineCollection:
    def test_writes_baseline_observation(self, tmp_store):
        from radar.stages.discover import run_discover
        from radar.schema_store import get_series

        offer = _make_offer("JFK", "BUSINESS", 3000.0)
        # fetch_all_combinations returns list of (combo, best_offer, errors)
        mock_results = [
            ({"origin": "CAI", "destination": "JFK", "cabin": "BUSINESS"}, offer, []),
        ]
        with patch("radar.stages.discover.fetch_all_combinations", return_value=mock_results):
            result = run_discover()

        assert result["observations_written"] >= 1
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "baseline"
        assert series[0]["price_usd"] == 3000.0

    def test_no_data_increments_no_data_counter(self, tmp_store):
        from radar.stages.discover import run_discover

        mock_results = [
            ({"origin": "CAI", "destination": "JFK", "cabin": "BUSINESS"}, None, ["no data"]),
        ]
        with patch("radar.stages.discover.fetch_all_combinations", return_value=mock_results):
            result = run_discover()

        assert result["combinations_no_data"] == 1
        assert result["observations_written"] == 0

    def test_baseline_complete_true_when_all_covered(self, tmp_store):
        """baseline_complete flag must be True once all 24 combos have an observation."""
        from radar.stages.discover import run_discover

        # Return one offer per combination
        from radar.constraints import generate_search_combinations
        combos = generate_search_combinations()

        mock_results = []
        for combo in combos:
            offer = _make_offer(combo["destination"], combo["cabin"], 2000.0)
            mock_results.append((combo, offer, []))

        with patch("radar.stages.discover.fetch_all_combinations", return_value=mock_results):
            result = run_discover()

        assert result["baseline_complete"] is True
        assert result["observations_written"] == 24

    def test_skips_already_covered_combinations(self, tmp_store):
        """Combinations already in the store must be skipped — not re-fetched."""
        from radar.schema_store import append_observation
        from radar.stages.discover import run_discover

        # Pre-seed one combination
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )

        # The discover run should see 23 pending (1 already covered)
        result = run_discover(dry_run=True)
        assert result["pending"] == 23

    def test_premium_economy_unavailable_flagged(self, tmp_store):
        """When no Premium Economy offer is returned, the carrier must be flagged."""
        from radar.stages.discover import run_discover
        from radar.schema_store import load_store

        mock_results = [
            ({"origin": "CAI", "destination": "JFK", "cabin": "PREMIUM_ECONOMY"}, None, []),
        ]
        with patch("radar.stages.discover.fetch_all_combinations", return_value=mock_results):
            run_discover()

        store = load_store()
        unavailable = store["metadata"].get("carriers_premium_economy_unavailable", [])
        assert len(unavailable) >= 1
