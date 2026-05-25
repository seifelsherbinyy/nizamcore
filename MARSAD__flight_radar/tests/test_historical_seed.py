"""
Tests for the HISTORICAL SEED module.

EXECUTED_IN_SESSION: All tests run with pytest.
Uses temporary directories — no real API calls made.
"""

import csv
import tempfile
from pathlib import Path
from unittest import mock

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
    return data_dir


def _write_csv(path: Path, rows: list[dict]) -> Path:
    if not rows:
        return path
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return path


class TestSeedFromCSV:
    def test_valid_row_imports_correctly(self, tmp_store, tmp_path):
        from radar.historical_seed import seed_from_csv
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path / "seed.csv", [{
            "origin": "CAI",
            "destination": "JFK",
            "carrier": "EK",
            "cabin": "BUSINESS",
            "outbound_date": "2027-04-01",
            "return_date": "2027-04-12",
            "price_usd": "3150.0",
            "source_note": "test",
        }])

        stats = seed_from_csv(csv_path, dry_run=False)
        assert stats["rows_imported"] == 1
        assert stats["observations_written"] == 1
        assert stats["rows_failed_constraint"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["price_usd"] == 3150.0
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["data_quality"] == "seed"

    def test_constraint_filtered_row_not_imported(self, tmp_store, tmp_path):
        from radar.historical_seed import seed_from_csv

        csv_path = _write_csv(tmp_path / "seed.csv", [{
            "origin": "CAI",
            "destination": "LHR",   # not in USA_DESTINATIONS
            "carrier": "BA",
            "cabin": "BUSINESS",
            "outbound_date": "2027-04-01",
            "return_date": "2027-04-12",
            "price_usd": "2500.0",
        }])

        stats = seed_from_csv(csv_path, dry_run=False)
        assert stats["rows_imported"] == 0
        assert stats["rows_failed_constraint"] == 1

    def test_economy_cabin_filtered(self, tmp_store, tmp_path):
        from radar.historical_seed import seed_from_csv

        csv_path = _write_csv(tmp_path / "seed.csv", [{
            "origin": "CAI",
            "destination": "JFK",
            "carrier": "EK",
            "cabin": "ECONOMY",   # not allowed
            "outbound_date": "2027-04-01",
            "return_date": "2027-04-12",
            "price_usd": "800.0",
        }])

        stats = seed_from_csv(csv_path, dry_run=False)
        assert stats["rows_failed_constraint"] == 1

    def test_dry_run_does_not_write(self, tmp_store, tmp_path):
        from radar.historical_seed import seed_from_csv
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path / "seed.csv", [{
            "origin": "CAI",
            "destination": "LAX",
            "carrier": "QR",
            "cabin": "BUSINESS",
            "outbound_date": "2027-05-01",
            "return_date": "2027-05-12",
            "price_usd": "3000.0",
        }])

        stats = seed_from_csv(csv_path, dry_run=True)
        assert stats["dry_run"] is True
        assert stats["rows_imported"] == 1  # counted as imported

        # Nothing written to store in dry_run mode
        series = get_series("CAI", "LAX", "QR", "BUSINESS")
        assert len(series) == 0

    def test_missing_required_field_skipped(self, tmp_store, tmp_path):
        from radar.historical_seed import seed_from_csv

        csv_path = _write_csv(tmp_path / "seed.csv", [{
            "origin": "CAI",
            "destination": "JFK",
            # carrier missing
            "cabin": "BUSINESS",
            "outbound_date": "2027-04-01",
            "return_date": "2027-04-12",
            "price_usd": "3000.0",
        }])

        stats = seed_from_csv(csv_path, dry_run=False)
        assert stats["rows_skipped_error"] == 1
        assert stats["rows_imported"] == 0

    def test_multiple_rows_imported(self, tmp_store, tmp_path):
        from radar.historical_seed import seed_from_csv

        rows = [
            {
                "origin": "CAI", "destination": "JFK", "carrier": "EK",
                "cabin": "BUSINESS", "outbound_date": "2027-04-01",
                "return_date": "2027-04-12", "price_usd": str(3000 + i * 50),
            }
            for i in range(5)
        ]
        csv_path = _write_csv(tmp_path / "seed.csv", rows)

        stats = seed_from_csv(csv_path, dry_run=False)
        assert stats["rows_imported"] == 5
        assert stats["observations_written"] == 5

    def test_31_hour_outbound_filtered(self, tmp_store, tmp_path):
        """Seed rows with outbound >30h must be filtered by constraint engine."""
        from radar.historical_seed import seed_from_csv

        csv_path = _write_csv(tmp_path / "seed.csv", [{
            "origin": "CAI",
            "destination": "JFK",
            "carrier": "EK",
            "cabin": "BUSINESS",
            "outbound_date": "2027-04-01",
            "return_date": "2027-04-12",
            "price_usd": "3000.0",
            "outbound_duration_hours": "31.0",  # exceeds 30h limit
            "return_duration_hours": "15.0",
        }])

        stats = seed_from_csv(csv_path, dry_run=False)
        assert stats["rows_failed_constraint"] == 1

    def test_seed_observation_type_is_historical_seed(self, tmp_store, tmp_path):
        """Seeded observations must have observation_type='historical_seed' not 'baseline'."""
        from radar.historical_seed import seed_from_csv
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path / "seed.csv", [{
            "origin": "CAI", "destination": "MIA", "carrier": "AF",
            "cabin": "PREMIUM_ECONOMY", "outbound_date": "2027-06-01",
            "return_date": "2027-06-12", "price_usd": "1800.0",
        }])

        seed_from_csv(csv_path, dry_run=False)
        series = get_series("CAI", "MIA", "AF", "PREMIUM_ECONOMY")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"

    def test_file_not_found_returns_error(self, tmp_store):
        from radar.historical_seed import seed_from_csv
        stats = seed_from_csv(Path("/nonexistent/file.csv"), dry_run=False)
        assert "error" in stats
