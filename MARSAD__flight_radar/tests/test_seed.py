"""
Tests for the HISTORICAL SEED IMPORTER (Stage 0).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses temporary files and patched store paths — no real data written.
"""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import pytest


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


def _valid_row(**overrides) -> dict:
    defaults = {
        "carrier": "EK",
        "cabin": "BUSINESS",
        "origin": "CAI",
        "destination": "JFK",
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "price_usd": "3200.0",
        "outbound_duration_hours": "14.5",
        "return_duration_hours": "15.0",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
    }
    defaults.update(overrides)
    return defaults


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f)


class TestSeedCSVImport:
    def test_valid_csv_row_imports(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_file = tmp_path / "prices.csv"
        _write_csv(csv_file, [_valid_row()])

        stats = run_seed(csv_file)

        assert stats["records_read"] == 1
        assert stats["records_imported"] == 1
        assert stats["records_constraint_failed"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["source"] == "historical_seed"
        assert series[0]["price_usd"] == 3200.0

    def test_multiple_rows_all_imported(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_file = tmp_path / "prices.csv"
        rows = [
            _valid_row(price_usd="3200.0"),
            _valid_row(price_usd="3100.0", outbound_date="2027-04-15", return_date="2027-04-26"),
            _valid_row(price_usd="2950.0", outbound_date="2027-05-01", return_date="2027-05-12"),
        ]
        _write_csv(csv_file, rows)

        stats = run_seed(csv_file)

        assert stats["records_imported"] == 3
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 3


class TestSeedJSONImport:
    def test_valid_json_array_imports(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed

        json_file = tmp_path / "prices.json"
        _write_json(json_file, [_valid_row()])

        stats = run_seed(json_file)

        assert stats["records_imported"] == 1

    def test_json_non_array_raises(self, tmp_path):
        from radar.stages.seed import run_seed

        json_file = tmp_path / "bad.json"
        with open(json_file, "w") as f:
            json.dump({"not": "an array"}, f)

        with pytest.raises(ValueError, match="array"):
            run_seed(json_file)


class TestSeedConstraintFiltering:
    def test_31_hour_outbound_is_filtered(self, tmp_store, tmp_path):
        """A record with 31-hour outbound must be filtered — constraint engine called."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_file = tmp_path / "prices.csv"
        _write_csv(csv_file, [_valid_row(outbound_duration_hours="31.0")])

        stats = run_seed(csv_file)

        assert stats["records_constraint_failed"] == 1
        assert stats["records_imported"] == 0
        assert get_series("CAI", "JFK", "EK", "BUSINESS") == []

    def test_economy_cabin_filtered(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed

        csv_file = tmp_path / "prices.csv"
        _write_csv(csv_file, [_valid_row(cabin="ECONOMY")])

        stats = run_seed(csv_file)

        assert stats["records_constraint_failed"] == 1
        assert stats["records_imported"] == 0

    def test_out_of_window_date_filtered(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed

        csv_file = tmp_path / "prices.csv"
        # Before WINDOW_START (2027-03-15)
        _write_csv(csv_file, [_valid_row(
            outbound_date="2027-02-01",
            return_date="2027-02-12",
        )])

        stats = run_seed(csv_file)

        assert stats["records_constraint_failed"] == 1
        assert stats["records_imported"] == 0

    def test_mixed_valid_and_invalid_rows(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed

        csv_file = tmp_path / "prices.csv"
        _write_csv(csv_file, [
            _valid_row(price_usd="3000.0"),                            # valid
            _valid_row(cabin="ECONOMY", price_usd="500.0"),            # invalid — economy
            _valid_row(outbound_duration_hours="35.0"),                 # invalid — too long
            _valid_row(price_usd="3100.0", outbound_date="2027-05-01", return_date="2027-05-12"),  # valid
        ])

        stats = run_seed(csv_file)

        assert stats["records_imported"] == 2
        assert stats["records_constraint_failed"] == 2


class TestSeedDryRun:
    def test_dry_run_does_not_write_to_store(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_file = tmp_path / "prices.csv"
        _write_csv(csv_file, [_valid_row()])

        stats = run_seed(csv_file, dry_run=True)

        assert stats["dry_run"] is True
        assert stats["records_imported"] == 0
        # Store must remain empty
        assert get_series("CAI", "JFK", "EK", "BUSINESS") == []

    def test_dry_run_reports_constraint_passed_count(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed

        csv_file = tmp_path / "prices.csv"
        _write_csv(csv_file, [_valid_row(), _valid_row(cabin="ECONOMY")])

        stats = run_seed(csv_file, dry_run=True)

        assert stats["records_constraint_passed"] == 1
        assert stats["records_constraint_failed"] == 1


class TestSeedFileErrors:
    def test_file_not_found_raises(self):
        from radar.stages.seed import run_seed

        with pytest.raises(FileNotFoundError):
            run_seed("/nonexistent/path/prices.csv")

    def test_unsupported_extension_raises(self, tmp_path):
        from radar.stages.seed import run_seed

        bad_file = tmp_path / "prices.xlsx"
        bad_file.touch()

        with pytest.raises(ValueError, match="Unsupported file format"):
            run_seed(bad_file)

    def test_missing_required_column_skips_row(self, tmp_store, tmp_path):
        """Row missing 'price_usd' is skipped, not imported, not a crash."""
        from radar.stages.seed import run_seed

        csv_file = tmp_path / "prices.csv"
        row = _valid_row()
        del row["price_usd"]
        _write_csv(csv_file, [row])

        stats = run_seed(csv_file)

        assert stats["records_imported"] == 0
        assert stats["records_parsed"] == 0


class TestSeedObservationTypeFlaggedCorrectly:
    def test_imported_observations_are_historical_seed_type(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_file = tmp_path / "prices.csv"
        _write_csv(csv_file, [_valid_row(), _valid_row(
            outbound_date="2027-04-15",
            return_date="2027-04-26",
            price_usd="2900.0"
        )])

        run_seed(csv_file)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert all(obs["observation_type"] == "historical_seed" for obs in series)
        assert all(obs["source"] == "historical_seed" for obs in series)
