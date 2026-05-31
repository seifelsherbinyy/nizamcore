"""
Tests for the SEED stage — historical price import.

EXECUTED_IN_SESSION: All tests in this file run with pytest.
"""

from __future__ import annotations

import json
import csv
import pytest
from pathlib import Path


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect schema_store paths to a temporary directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    monkeypatch.setattr("radar.config.DATA_DIR", data_dir)
    monkeypatch.setattr("radar.config.ALERTS_DIR", tmp_path / "alerts")
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr("radar.config.BACKUPS_DIR", data_dir / "backups")

    import radar.schema_store as ss
    monkeypatch.setattr(ss, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(ss, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(ss, "BACKUPS_DIR", data_dir / "backups")
    return data_dir


def _valid_record(**overrides) -> dict:
    base = {
        "origin": "CAI",
        "destination": "JFK",
        "carrier": "EK",
        "cabin": "BUSINESS",
        "price_usd": 3200.0,
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "outbound_duration_hours": 14.5,
        "return_duration_hours": 15.0,
        "outbound_stops": 1,
        "return_stops": 1,
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
        "data_quality": "estimated",
    }
    base.update(overrides)
    return base


class TestSeedFromJSON:
    def test_imports_valid_json_record(self, tmp_store, tmp_path):
        seed_file = tmp_path / "history.json"
        seed_file.write_text(json.dumps([_valid_record()]), encoding="utf-8")

        from radar.stages.seed import run_seed
        stats = run_seed(seed_file)

        assert stats["records_read"] == 1
        assert stats["records_imported"] == 1
        assert stats["records_constraint_skipped"] == 0
        assert not stats["fetch_errors"]

    def test_imported_record_has_correct_observation_type(self, tmp_store, tmp_path):
        seed_file = tmp_path / "history.json"
        seed_file.write_text(json.dumps([_valid_record()]), encoding="utf-8")

        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        run_seed(seed_file)
        series = get_series("CAI", "JFK", "EK", "BUSINESS")

        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["source"] == "historical_seed"
        assert series[0]["data_quality"] == "estimated"

    def test_multiple_records_all_imported(self, tmp_store, tmp_path):
        records = [
            _valid_record(price_usd=3200.0, outbound_date="2027-04-01", return_date="2027-04-12"),
            _valid_record(price_usd=3100.0, outbound_date="2027-05-01", return_date="2027-05-12"),
            _valid_record(price_usd=2900.0, outbound_date="2027-06-01", return_date="2027-06-12"),
        ]
        seed_file = tmp_path / "history.json"
        seed_file.write_text(json.dumps(records), encoding="utf-8")

        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        stats = run_seed(seed_file)
        assert stats["records_imported"] == 3

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 3


class TestSeedFromCSV:
    def test_imports_valid_csv_record(self, tmp_store, tmp_path):
        seed_file = tmp_path / "history.csv"
        fieldnames = list(_valid_record().keys())
        with open(seed_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(_valid_record())

        from radar.stages.seed import run_seed
        stats = run_seed(seed_file)

        assert stats["records_imported"] == 1
        assert not stats["fetch_errors"]

    def test_csv_missing_header_fails_gracefully(self, tmp_store, tmp_path):
        seed_file = tmp_path / "bad.csv"
        seed_file.write_text("not,a,valid,header\n1,2,3,4\n", encoding="utf-8")

        from radar.stages.seed import run_seed
        stats = run_seed(seed_file)

        # Records parsed but missing required fields → parse errors
        assert stats["records_imported"] == 0
        assert stats["records_parse_error"] > 0


class TestSeedConstraintFiltering:
    def test_out_of_window_record_is_skipped(self, tmp_store, tmp_path):
        """A record with departure before the travel window must be skipped, not error."""
        rec = _valid_record(outbound_date="2027-01-01", return_date="2027-01-12")
        seed_file = tmp_path / "history.json"
        seed_file.write_text(json.dumps([rec]), encoding="utf-8")

        from radar.stages.seed import run_seed
        stats = run_seed(seed_file)

        assert stats["records_constraint_skipped"] == 1
        assert stats["records_imported"] == 0

    def test_31_hour_outbound_is_skipped(self, tmp_store, tmp_path):
        """A record with outbound > 30 hours must be filtered by the constraint engine."""
        rec = _valid_record(outbound_duration_hours=31.0)
        seed_file = tmp_path / "history.json"
        seed_file.write_text(json.dumps([rec]), encoding="utf-8")

        from radar.stages.seed import run_seed
        stats = run_seed(seed_file)

        assert stats["records_constraint_skipped"] == 1
        assert stats["records_imported"] == 0

    def test_economy_cabin_is_skipped(self, tmp_store, tmp_path):
        rec = _valid_record(cabin="ECONOMY")
        seed_file = tmp_path / "history.json"
        seed_file.write_text(json.dumps([rec]), encoding="utf-8")

        from radar.stages.seed import run_seed
        stats = run_seed(seed_file)

        assert stats["records_constraint_skipped"] == 1

    def test_mixed_valid_and_invalid_records(self, tmp_store, tmp_path):
        """Valid and invalid records in the same file — valid ones imported, invalid skipped."""
        records = [
            _valid_record(price_usd=3200.0),                              # valid
            _valid_record(outbound_date="2026-01-01", return_date="2026-01-12"),  # out of window
            _valid_record(cabin="ECONOMY"),                                # bad cabin
            _valid_record(price_usd=2800.0, outbound_date="2027-05-01", return_date="2027-05-12"),  # valid
        ]
        seed_file = tmp_path / "history.json"
        seed_file.write_text(json.dumps(records), encoding="utf-8")

        from radar.stages.seed import run_seed
        stats = run_seed(seed_file)

        assert stats["records_imported"] == 2
        assert stats["records_constraint_skipped"] == 2


class TestSeedDryRun:
    def test_dry_run_does_not_write(self, tmp_store, tmp_path):
        seed_file = tmp_path / "history.json"
        seed_file.write_text(json.dumps([_valid_record()]), encoding="utf-8")

        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        stats = run_seed(seed_file, dry_run=True)

        assert stats["dry_run"] is True
        assert stats["records_imported"] == 1  # counted as "would import"

        # No data actually written
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0


class TestSeedFileErrors:
    def test_file_not_found_returns_error(self, tmp_store):
        from pathlib import Path
        from radar.stages.seed import run_seed
        stats = run_seed(Path("/nonexistent/path/history.json"))

        assert stats["records_read"] == 0
        assert len(stats["fetch_errors"]) == 1
        assert "not found" in stats["fetch_errors"][0].lower()

    def test_unsupported_extension_returns_error(self, tmp_store, tmp_path):
        bad_file = tmp_path / "history.xlsx"
        bad_file.write_bytes(b"not a supported format")

        from radar.stages.seed import run_seed
        stats = run_seed(bad_file)

        assert stats["records_read"] == 0
        assert len(stats["fetch_errors"]) == 1

    def test_empty_json_array_imports_nothing(self, tmp_store, tmp_path):
        seed_file = tmp_path / "empty.json"
        seed_file.write_text("[]", encoding="utf-8")

        from radar.stages.seed import run_seed
        stats = run_seed(seed_file)

        assert stats["records_read"] == 0
        assert stats["records_imported"] == 0
        assert not stats["fetch_errors"]


class TestSeedAppendOnly:
    def test_seed_appends_to_existing_series(self, tmp_store, tmp_path):
        """Seed data must append to existing observations — not overwrite them."""
        from radar.schema_store import append_observation, get_series

        # Pre-existing baseline observation
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3500.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )

        # Seed one historical record
        seed_file = tmp_path / "history.json"
        seed_file.write_text(json.dumps([_valid_record(price_usd=3200.0)]), encoding="utf-8")

        from radar.stages.seed import run_seed
        run_seed(seed_file)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        # Original observation untouched
        assert series[0]["price_usd"] == 3500.0
        assert series[0]["observation_type"] == "baseline"
        # Seed appended
        assert series[1]["price_usd"] == 3200.0
        assert series[1]["observation_type"] == "historical_seed"
