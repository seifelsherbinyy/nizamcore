"""
Tests for the append-only schema store.

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses a temporary directory to avoid touching the real data store.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect all schema_store paths to a temporary directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    alerts_dir = tmp_path / "alerts"
    alerts_dir.mkdir()

    monkeypatch.setattr("radar.config.DATA_DIR", data_dir)
    monkeypatch.setattr("radar.config.ALERTS_DIR", alerts_dir)
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr("radar.config.BACKUPS_DIR", data_dir / "backups")

    # Also patch the module-level imports in schema_store
    import radar.schema_store as ss
    monkeypatch.setattr(ss, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(ss, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(ss, "BACKUPS_DIR", data_dir / "backups")
    # Note: schema_store does not import ALERTS_DIR — alerts are written by alert.py

    return data_dir


class TestStoreInit:
    def test_creates_empty_store_if_none_exists(self, tmp_store):
        from radar.schema_store import load_store
        store = load_store()
        assert "schema_version" in store
        assert "routes" in store
        assert store["routes"] == {}
        assert (tmp_store / "flight_prices.json").exists()

    def test_store_has_correct_schema_version(self, tmp_store):
        from radar.schema_store import load_store
        store = load_store()
        assert store["schema_version"] == "1.0"

    def test_metadata_contains_expected_fields(self, tmp_store):
        from radar.schema_store import load_store
        store = load_store()
        meta = store["metadata"]
        assert meta["origin"] == "CAI"
        assert "JFK" in meta["destinations"]
        assert "BUSINESS" in meta["cabins"]


class TestAppendObservation:
    def test_first_observation_has_null_delta(self, tmp_store):
        from radar.schema_store import append_observation, get_series
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="amadeus", observation_type="baseline",
        )
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["delta_from_previous_usd"] is None
        assert series[0]["delta_pct"] is None

    def test_second_observation_calculates_delta(self, tmp_store):
        from radar.schema_store import append_observation, get_series
        kwargs = dict(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="amadeus",
        )
        append_observation(price_usd=3000.0, **kwargs)
        append_observation(price_usd=2700.0, **kwargs)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        last = series[-1]
        assert last["delta_from_previous_usd"] == -300.0
        assert last["delta_pct"] == -10.0

    def test_append_never_overwrites_history(self, tmp_store):
        """INVARIANT: historical observations must never be modified."""
        from radar.schema_store import append_observation, get_series
        kwargs = dict(
            origin="CAI", destination="LAX", carrier="QR", cabin="PREMIUM_ECONOMY",
            outbound_date="2027-05-01", return_date="2027-05-12",
            outbound_duration_hours=18.5, return_duration_hours=19.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DOH-LAX", return_routing="LAX-DOH-CAI",
            source="amadeus",
        )
        append_observation(price_usd=2000.0, **kwargs)
        first_id = get_series("CAI", "LAX", "QR", "PREMIUM_ECONOMY")[0]["observation_id"]

        append_observation(price_usd=1800.0, **kwargs)
        append_observation(price_usd=1900.0, **kwargs)

        series = get_series("CAI", "LAX", "QR", "PREMIUM_ECONOMY")
        assert len(series) == 3
        # First observation must be unchanged
        assert series[0]["observation_id"] == first_id
        assert series[0]["price_usd"] == 2000.0

    def test_multiple_carriers_independent_series(self, tmp_store):
        """Different carriers on the same route maintain separate series."""
        from radar.schema_store import append_observation, get_series
        base_kwargs = dict(
            origin="CAI", destination="JFK", cabin="BUSINESS",
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.0, return_duration_hours=14.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-X-JFK", return_routing="JFK-X-CAI",
            source="amadeus",
        )
        append_observation(carrier="EK", price_usd=3000.0, **base_kwargs)
        append_observation(carrier="QR", price_usd=3200.0, **base_kwargs)

        ek_series = get_series("CAI", "JFK", "EK", "BUSINESS")
        qr_series = get_series("CAI", "JFK", "QR", "BUSINESS")
        assert len(ek_series) == 1
        assert len(qr_series) == 1
        assert ek_series[0]["price_usd"] == 3000.0
        assert qr_series[0]["price_usd"] == 3200.0


class TestAtomicWrite:
    def test_no_tmp_file_after_successful_write(self, tmp_store):
        from radar.schema_store import append_observation
        import radar.schema_store as ss

        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="amadeus",
        )
        assert not ss.FLIGHT_PRICES_TMP.exists(), ".tmp file must be cleaned up after successful write"

    def test_store_is_valid_json_after_write(self, tmp_store):
        import radar.schema_store as ss
        from radar.schema_store import append_observation

        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="amadeus",
        )
        content = ss.FLIGHT_PRICES_PATH.read_text()
        parsed = json.loads(content)
        assert "routes" in parsed


class TestBackup:
    def test_backup_creates_file(self, tmp_store):
        from radar.schema_store import append_observation, backup_store
        import radar.schema_store as ss

        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="amadeus",
        )
        backup_path = backup_store()
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.suffix == ".json"
