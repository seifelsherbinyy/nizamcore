"""
Tests for the historical seed loader (radar/seeds/seed_loader.py).

EXECUTED_IN_SESSION: All tests run with pytest.
Uses tmp_path fixtures to avoid touching the real data store.
"""

import json
import csv
import pytest
from pathlib import Path


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

    import radar.schema_store as ss
    monkeypatch.setattr(ss, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(ss, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(ss, "BACKUPS_DIR", data_dir / "backups")

    return data_dir


def _valid_row(**overrides) -> dict:
    base = {
        "origin": "CAI",
        "destination": "JFK",
        "cabin": "BUSINESS",
        "carrier": "EK",
        "price_usd": 3200.0,
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "outbound_duration_hours": 14.5,
        "return_duration_hours": 15.0,
        "outbound_stops": 1,
        "return_stops": 1,
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
        "source": "google_flights_history",
        "data_quality": "estimated",
    }
    base.update(overrides)
    return base


class TestSeedFileLoad:
    def test_json_file_loads(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed

        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps([_valid_row()]), encoding="utf-8")

        stats = run_seed(path=seed_file, dry_run=True)
        assert stats["total_rows"] == 1
        assert stats["rows_imported"] == 1

    def test_csv_file_loads(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed

        seed_file = tmp_path / "seed.csv"
        row = _valid_row()
        with open(seed_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            writer.writeheader()
            writer.writerow(row)

        stats = run_seed(path=seed_file, dry_run=True)
        assert stats["total_rows"] == 1
        assert stats["rows_imported"] == 1

    def test_nonexistent_file_raises(self, tmp_path):
        from radar.seeds.seed_loader import run_seed
        with pytest.raises(FileNotFoundError):
            run_seed(path=tmp_path / "missing.json")

    def test_unsupported_format_raises(self, tmp_path):
        from radar.seeds.seed_loader import run_seed
        f = tmp_path / "seed.txt"
        f.write_text("data")
        with pytest.raises(ValueError, match="Unsupported seed file format"):
            run_seed(path=f)

    def test_non_list_json_raises(self, tmp_path):
        from radar.seeds.seed_loader import run_seed
        seed_file = tmp_path / "seed.json"
        seed_file.write_text('{"single": "object"}')
        with pytest.raises(ValueError, match="must be a list"):
            run_seed(path=seed_file)


class TestConstraintFiltering:
    def test_invalid_origin_filtered(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed

        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps([_valid_row(origin="LHR")]), encoding="utf-8")
        stats = run_seed(path=seed_file)
        assert stats["rows_skipped_constraint"] == 1
        assert stats["rows_imported"] == 0

    def test_31_hour_outbound_filtered(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed

        seed_file = tmp_path / "seed.json"
        seed_file.write_text(
            json.dumps([_valid_row(outbound_duration_hours=31.0)]),
            encoding="utf-8",
        )
        stats = run_seed(path=seed_file)
        assert stats["rows_skipped_constraint"] == 1
        assert stats["rows_imported"] == 0

    def test_invalid_cabin_filtered(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed

        seed_file = tmp_path / "seed.json"
        seed_file.write_text(
            json.dumps([_valid_row(cabin="ECONOMY")]),
            encoding="utf-8",
        )
        stats = run_seed(path=seed_file)
        assert stats["rows_skipped_constraint"] == 1

    def test_outside_travel_window_filtered(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed

        seed_file = tmp_path / "seed.json"
        seed_file.write_text(
            json.dumps([_valid_row(outbound_date="2026-01-01", return_date="2026-01-12")]),
            encoding="utf-8",
        )
        stats = run_seed(path=seed_file)
        assert stats["rows_skipped_constraint"] == 1

    def test_8_night_duration_filtered(self, tmp_path, tmp_store):
        """8 nights < minimum 9 nights — must be filtered."""
        from radar.seeds.seed_loader import run_seed

        seed_file = tmp_path / "seed.json"
        seed_file.write_text(
            json.dumps([_valid_row(outbound_date="2027-04-01", return_date="2027-04-09")]),
            encoding="utf-8",
        )
        stats = run_seed(path=seed_file)
        assert stats["rows_skipped_constraint"] == 1


class TestStoreWrite:
    def test_valid_row_appended_to_store(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed
        from radar.schema_store import get_series

        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps([_valid_row()]), encoding="utf-8")
        stats = run_seed(path=seed_file)

        assert stats["rows_imported"] == 1
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["data_quality"] == "estimated"

    def test_multiple_valid_rows_all_imported(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed
        from radar.schema_store import get_series

        rows = [
            _valid_row(price_usd=3200.0, outbound_date="2027-04-01", return_date="2027-04-12"),
            _valid_row(price_usd=3100.0, outbound_date="2027-05-01", return_date="2027-05-12"),
            _valid_row(price_usd=2900.0, outbound_date="2027-06-01", return_date="2027-06-12"),
        ]
        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps(rows), encoding="utf-8")
        stats = run_seed(path=seed_file)

        assert stats["rows_imported"] == 3
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 3

    def test_append_does_not_overwrite_existing_observations(self, tmp_path, tmp_store):
        """INVARIANT: seed import must not corrupt existing observations."""
        from radar.seeds.seed_loader import run_seed
        from radar.schema_store import get_series, append_observation

        # Pre-populate the store with an existing observation
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )

        # Seed with a new observation
        seed_file = tmp_path / "seed.json"
        seed_file.write_text(
            json.dumps([_valid_row(price_usd=2800.0, outbound_date="2027-05-01", return_date="2027-05-12")]),
            encoding="utf-8",
        )
        run_seed(path=seed_file)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        # First observation must be unchanged
        assert series[0]["observation_type"] == "baseline"
        assert series[0]["price_usd"] == 3000.0
        # Second is the seed
        assert series[1]["observation_type"] == "historical_seed"
        assert series[1]["price_usd"] == 2800.0


class TestDryRun:
    def test_dry_run_does_not_write_to_store(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed
        from radar.schema_store import get_series

        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps([_valid_row()]), encoding="utf-8")
        stats = run_seed(path=seed_file, dry_run=True)

        assert stats["rows_imported"] == 1
        assert stats["dry_run"] is True
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0  # nothing written


class TestMissingFields:
    def test_missing_required_field_skipped(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed

        # Remove required 'price_usd' field
        row = _valid_row()
        del row["price_usd"]

        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps([row]), encoding="utf-8")
        stats = run_seed(path=seed_file)

        assert stats["rows_skipped_error"] == 1
        assert stats["rows_imported"] == 0

    def test_optional_fields_get_defaults(self, tmp_path, tmp_store):
        from radar.seeds.seed_loader import run_seed
        from radar.schema_store import get_series

        # Minimal row — only required fields
        row = {
            "origin": "CAI",
            "destination": "JFK",
            "cabin": "BUSINESS",
            "carrier": "EK",
            "price_usd": 3200.0,
            "outbound_date": "2027-04-01",
            "return_date": "2027-04-12",
        }
        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps([row]), encoding="utf-8")
        stats = run_seed(path=seed_file)

        assert stats["rows_imported"] == 1
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert series[0]["outbound_duration_hours"] == 15.0
        assert series[0]["outbound_routing"] == "CAI-JFK"
        assert series[0]["return_routing"] == "JFK-CAI"
        assert series[0]["data_quality"] == "estimated"
