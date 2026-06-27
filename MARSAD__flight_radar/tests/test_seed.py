"""
Tests for the SEED module (Stage 0 — historical price data import).

EXECUTED_IN_SESSION: All tests run with pytest.
Uses temporary directories to avoid touching the real data store.
"""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect schema_store paths to a temporary directory."""
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


def _write_csv(tmp_path: Path, rows: list[dict]) -> Path:
    if not rows:
        return tmp_path / "empty.csv"
    path = tmp_path / "seed.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _write_json(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


def _valid_row(**overrides) -> dict:
    defaults = {
        "origin": "CAI",
        "destination": "JFK",
        "carrier": "EK",
        "cabin": "BUSINESS",
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "price_usd": "3200.0",
        "source": "google_flights_manual",
        "outbound_duration_hours": "14.5",
        "return_duration_hours": "15.0",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
    }
    defaults.update(overrides)
    return defaults


class TestCSVImport:
    def test_valid_csv_writes_observation(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path, [_valid_row()])
        stats = run_seed(csv_path)

        assert stats["records_written"] == 1
        assert stats["records_parsed"] == 1
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["price_usd"] == 3200.0
        assert series[0]["observation_type"] == "historical_seed"

    def test_constraint_violation_skipped(self, tmp_path, tmp_store):
        """31-hour outbound must be filtered by constraint engine."""
        from radar.stages.seed import run_seed

        row = _valid_row(outbound_duration_hours="31.0")
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed(csv_path)

        assert stats["records_written"] == 0
        assert stats["records_parsed"] == 0  # constraint failure drops it in parse

    def test_economy_cabin_skipped(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        row = _valid_row(cabin="ECONOMY")
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed(csv_path)

        assert stats["records_written"] == 0

    def test_wrong_destination_skipped(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        row = _valid_row(destination="LHR")
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed(csv_path)

        assert stats["records_written"] == 0

    def test_out_of_window_date_skipped(self, tmp_path, tmp_store):
        """Departure before travel window must be rejected."""
        from radar.stages.seed import run_seed

        row = _valid_row(outbound_date="2027-01-15", return_date="2027-01-26")
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed(csv_path)

        assert stats["records_written"] == 0

    def test_multiple_rows_all_valid(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        rows = [
            _valid_row(outbound_date="2027-04-01", return_date="2027-04-12", price_usd="3200.0"),
            _valid_row(outbound_date="2027-05-01", return_date="2027-05-12", price_usd="3100.0"),
            _valid_row(outbound_date="2027-06-01", return_date="2027-06-12", price_usd="3050.0"),
        ]
        csv_path = _write_csv(tmp_path, rows)
        stats = run_seed(csv_path)

        assert stats["records_written"] == 3
        assert stats["records_parsed"] == 3

    def test_mixed_valid_invalid(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        rows = [
            _valid_row(outbound_date="2027-04-01", return_date="2027-04-12", price_usd="3200.0"),
            _valid_row(cabin="ECONOMY", outbound_date="2027-05-01", return_date="2027-05-12"),
            _valid_row(outbound_date="2027-06-01", return_date="2027-06-12", price_usd="2900.0"),
        ]
        csv_path = _write_csv(tmp_path, rows)
        stats = run_seed(csv_path)

        assert stats["records_written"] == 2

    def test_missing_required_column_skipped(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        row = _valid_row()
        del row["price_usd"]
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed(csv_path)

        assert stats["records_written"] == 0

    def test_invalid_price_skipped(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        row = _valid_row(price_usd="-50.0")
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed(csv_path)

        assert stats["records_written"] == 0


class TestJSONImport:
    def test_valid_json_writes_observation(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        rows = [_valid_row()]
        # Convert string values to appropriate types for JSON
        rows[0]["price_usd"] = 3200.0
        rows[0]["outbound_duration_hours"] = 14.5
        rows[0]["return_duration_hours"] = 15.0
        rows[0]["outbound_stops"] = 1
        rows[0]["return_stops"] = 1

        json_path = _write_json(tmp_path, rows)
        stats = run_seed(json_path)

        assert stats["records_written"] == 1
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"

    def test_non_array_json_raises(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        json_path = tmp_path / "bad.json"
        json_path.write_text(json.dumps({"not": "an array"}), encoding="utf-8")

        with pytest.raises(ValueError, match="top-level array"):
            run_seed(json_path)


class TestDuplicateHandling:
    def test_duplicate_outbound_date_skipped_by_default(self, tmp_path, tmp_store):
        """By default, re-importing the same outbound_date is skipped."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        rows = [_valid_row(price_usd="3200.0")]
        csv_path = _write_csv(tmp_path, rows)

        run_seed(csv_path)  # first import
        stats = run_seed(csv_path)  # second import — same outbound_date

        assert stats["records_skipped_duplicate"] == 1
        assert stats["records_written"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1

    def test_allow_duplicates_writes_both(self, tmp_path, tmp_store):
        """With allow_duplicates=True, same outbound_date can be written twice."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        rows = [_valid_row(price_usd="3200.0")]
        csv_path = _write_csv(tmp_path, rows)

        run_seed(csv_path, allow_duplicates=True)
        stats = run_seed(csv_path, allow_duplicates=True)

        assert stats["records_written"] == 1
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2

    def test_different_dates_both_written(self, tmp_path, tmp_store):
        """Two rows with different outbound_dates must both be accepted."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        rows = [
            _valid_row(outbound_date="2027-04-01", return_date="2027-04-12", price_usd="3200.0"),
            _valid_row(outbound_date="2027-05-01", return_date="2027-05-12", price_usd="3100.0"),
        ]
        csv_path = _write_csv(tmp_path, rows)

        run_seed(csv_path)
        run_seed(csv_path)  # second pass — both dates already seen

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2


class TestDryRun:
    def test_dry_run_does_not_write(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path, [_valid_row()])
        stats = run_seed(csv_path, dry_run=True)

        assert stats["dry_run"] is True
        assert stats["records_written"] == 0
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0

    def test_dry_run_reports_parsed_count(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        rows = [
            _valid_row(outbound_date="2027-04-01", return_date="2027-04-12"),
            _valid_row(outbound_date="2027-05-01", return_date="2027-05-12"),
        ]
        csv_path = _write_csv(tmp_path, rows)
        stats = run_seed(csv_path, dry_run=True)

        assert stats["records_parsed"] == 2


class TestHistoricalObservationType:
    def test_observation_type_is_historical_seed(self, tmp_path, tmp_store):
        """Seeded observations must carry observation_type='historical_seed'."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path, [_valid_row()])
        run_seed(csv_path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert series[0]["observation_type"] == "historical_seed"

    def test_seeded_obs_count_unlocks_forecast_medium_confidence(self, tmp_path, tmp_store):
        """7 historical_seed observations move confidence from LOW to MEDIUM."""
        from radar.stages.seed import run_seed
        from radar.stages.forecast import _confidence_level

        rows = [
            _valid_row(
                outbound_date=f"2027-0{4 + i // 30}-{(1 + i) % 28 or 1:02d}",
                return_date=f"2027-0{4 + i // 30}-{(12 + i) % 28 or 12:02d}",
                price_usd=str(3200 - i * 50),
            )
            for i in range(7)
        ]
        # Build valid dates manually
        seed_rows = [
            _valid_row(outbound_date="2027-04-01", return_date="2027-04-12", price_usd="3200.0"),
            _valid_row(outbound_date="2027-04-15", return_date="2027-04-26", price_usd="3150.0"),
            _valid_row(outbound_date="2027-05-01", return_date="2027-05-12", price_usd="3100.0"),
            _valid_row(outbound_date="2027-05-15", return_date="2027-05-26", price_usd="3050.0"),
            _valid_row(outbound_date="2027-06-01", return_date="2027-06-12", price_usd="3000.0"),
            _valid_row(outbound_date="2027-06-15", return_date="2027-06-26", price_usd="2950.0"),
            _valid_row(outbound_date="2027-07-01", return_date="2027-07-12", price_usd="2900.0"),
        ]
        csv_path = _write_csv(tmp_path, seed_rows)
        stats = run_seed(csv_path)

        assert stats["records_written"] == 7
        assert _confidence_level(7) == "MEDIUM"


class TestUnsupportedFormat:
    def test_unknown_extension_raises(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        bad_path = tmp_path / "data.xlsx"
        bad_path.write_text("not a real xlsx", encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported file format"):
            run_seed(bad_path)

    def test_missing_file_raises(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        with pytest.raises(FileNotFoundError):
            run_seed(tmp_path / "does_not_exist.csv")
