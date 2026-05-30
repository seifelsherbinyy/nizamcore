"""
Tests for the SEED_HISTORY module (Stage 0).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses a temporary directory to avoid touching the real data store.
"""

import csv
import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect schema_store paths to a temporary directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    import radar.schema_store as ss
    monkeypatch.setattr(ss, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(ss, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(ss, "BACKUPS_DIR", data_dir / "backups")
    monkeypatch.setattr("radar.config.DATA_DIR", data_dir)
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr("radar.config.BACKUPS_DIR", data_dir / "backups")
    return data_dir


def _make_csv(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "seed.csv"
    if not rows:
        return path
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return path


def _make_json(tmp_path: Path, records: list[dict]) -> Path:
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


_VALID_ROW = {
    "origin": "CAI",
    "destination": "JFK",
    "carrier": "EK",
    "cabin": "BUSINESS",
    "outbound_date": "2027-04-01",
    "return_date": "2027-04-12",  # 11 nights
    "price_usd": "3000.00",
    "outbound_duration_hours": "14.5",
    "return_duration_hours": "15.0",
    "outbound_stops": "1",
    "return_stops": "1",
    "outbound_routing": "CAI-DXB-JFK",
    "return_routing": "JFK-DXB-CAI",
    "source": "manual",
    "data_quality": "estimated",
}


class TestLoadFromCSV:
    def test_loads_valid_csv(self, tmp_path):
        from radar.seed_history import load_from_csv
        path = _make_csv(tmp_path, [_VALID_ROW])
        records = load_from_csv(path)
        assert len(records) == 1
        assert records[0].origin == "CAI"
        assert records[0].destination == "JFK"
        assert records[0].price_usd == 3000.0
        assert records[0].cabin == "BUSINESS"

    def test_skips_malformed_rows(self, tmp_path):
        from radar.seed_history import load_from_csv
        bad_row = {**_VALID_ROW, "price_usd": "not_a_number"}
        path = _make_csv(tmp_path, [_VALID_ROW, bad_row])
        records = load_from_csv(path)
        # Only the valid row is loaded
        assert len(records) == 1

    def test_loads_multiple_rows(self, tmp_path):
        from radar.seed_history import load_from_csv
        row2 = {**_VALID_ROW, "destination": "LAX", "price_usd": "2800.00"}
        path = _make_csv(tmp_path, [_VALID_ROW, row2])
        records = load_from_csv(path)
        assert len(records) == 2


class TestLoadFromJSON:
    def test_loads_valid_json(self, tmp_path):
        from radar.seed_history import load_from_json
        record = {
            "origin": "CAI", "destination": "MIA", "carrier": "QR",
            "cabin": "BUSINESS", "outbound_date": "2027-05-01",
            "return_date": "2027-05-12", "price_usd": 3100.0,
        }
        path = _make_json(tmp_path, [record])
        records = load_from_json(path)
        assert len(records) == 1
        assert records[0].destination == "MIA"
        assert records[0].price_usd == 3100.0

    def test_raises_on_non_list_json(self, tmp_path):
        from radar.seed_history import load_from_json
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"not": "a list"}))
        with pytest.raises(ValueError, match="list"):
            load_from_json(path)


class TestConstraintFiltering:
    def test_valid_record_passes_constraints(self):
        from radar.seed_history import _validate_record, FlightSeedRecord
        rec = FlightSeedRecord(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            outbound_date="2027-04-01", return_date="2027-04-12",
            price_usd=3000.0,
        )
        passed, failures = _validate_record(rec)
        assert passed
        assert failures == []

    def test_invalid_origin_fails(self):
        from radar.seed_history import _validate_record, FlightSeedRecord
        rec = FlightSeedRecord(
            origin="LHR", destination="JFK", carrier="EK", cabin="BUSINESS",
            outbound_date="2027-04-01", return_date="2027-04-12",
            price_usd=3000.0,
        )
        passed, failures = _validate_record(rec)
        assert not passed
        assert any("origin" in f for f in failures)

    def test_economy_cabin_fails_constraint(self):
        from radar.seed_history import _validate_record, FlightSeedRecord
        rec = FlightSeedRecord(
            origin="CAI", destination="JFK", carrier="EK", cabin="ECONOMY",
            outbound_date="2027-04-01", return_date="2027-04-12",
            price_usd=1200.0,
        )
        passed, failures = _validate_record(rec)
        assert not passed
        assert any("cabin" in f for f in failures)

    def test_31_hour_outbound_fails_constraint(self):
        from radar.seed_history import _validate_record, FlightSeedRecord
        rec = FlightSeedRecord(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            outbound_date="2027-04-01", return_date="2027-04-12",
            price_usd=3000.0,
            outbound_duration_hours=31.0,
        )
        passed, failures = _validate_record(rec)
        assert not passed
        assert any("outbound_duration" in f for f in failures)


class TestRunSeedFromFile:
    def test_imports_valid_csv(self, tmp_path, tmp_store):
        from radar.seed_history import run_seed_from_file
        from radar.schema_store import get_series
        path = _make_csv(tmp_path, [_VALID_ROW])
        stats = run_seed_from_file(path)
        assert stats["imported"] == 1
        assert stats["filtered_by_constraints"] == 0
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"

    def test_dry_run_does_not_write(self, tmp_path, tmp_store):
        from radar.seed_history import run_seed_from_file
        from radar.schema_store import get_series
        path = _make_csv(tmp_path, [_VALID_ROW])
        stats = run_seed_from_file(path, dry_run=True)
        assert stats["dry_run"] is True
        assert stats["imported"] == 1  # counted as "would import"
        # Nothing written
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0

    def test_filters_economy_records(self, tmp_path, tmp_store):
        from radar.seed_history import run_seed_from_file
        economy_row = {**_VALID_ROW, "cabin": "ECONOMY"}
        path = _make_csv(tmp_path, [economy_row])
        stats = run_seed_from_file(path)
        assert stats["filtered_by_constraints"] == 1
        assert stats["imported"] == 0

    def test_raises_on_missing_file(self, tmp_path, tmp_store):
        from radar.seed_history import run_seed_from_file
        with pytest.raises(FileNotFoundError):
            run_seed_from_file(tmp_path / "nonexistent.csv")

    def test_raises_on_unsupported_format(self, tmp_path, tmp_store):
        from radar.seed_history import run_seed_from_file
        path = tmp_path / "seed.txt"
        path.write_text("some text")
        with pytest.raises(ValueError, match="Unsupported"):
            run_seed_from_file(path)

    def test_historical_seed_preserves_append_invariant(self, tmp_path, tmp_store):
        """Existing observations must not be overwritten when seed is imported."""
        from radar.seed_history import run_seed_from_file
        from radar.schema_store import get_series, append_observation

        # Pre-existing observation
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3500.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.0, return_duration_hours=14.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )

        # Import seed on same route
        path = _make_csv(tmp_path, [_VALID_ROW])
        run_seed_from_file(path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        # Original observation untouched
        assert series[0]["price_usd"] == 3500.0
        assert series[0]["observation_type"] == "baseline"
        # Seed appended
        assert series[1]["price_usd"] == 3000.0
        assert series[1]["observation_type"] == "historical_seed"
