"""
Tests for STAGE 0 — SEED: historical price importer.

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses temporary directories to avoid touching the real data store.
"""

import csv
import json
import tempfile
from pathlib import Path

import pytest


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


def _valid_row(**overrides) -> dict:
    base = {
        "route": "CAI-JFK",
        "carrier": "EK",
        "cabin": "BUSINESS",
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "price_usd": "3200.0",
        "source": "google_flights_history",
        "outbound_duration_hours": "14.5",
        "return_duration_hours": "15.0",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
    }
    base.update(overrides)
    return base


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


class TestSeedCSVImport:
    def test_valid_row_imports_as_historical_seed(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_path = tmp_path / "seed.csv"
        _write_csv(csv_path, [_valid_row()])

        stats = run_seed(csv_path=csv_path)
        assert stats["rows_imported"] == 1
        assert stats["rows_filtered"] == 0
        assert stats["rows_error"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["price_usd"] == 3200.0
        assert series[0]["source"] == "google_flights_history"

    def test_multiple_rows_accumulate(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        rows = [
            _valid_row(price_usd="3200.0", outbound_date="2027-04-01", return_date="2027-04-12"),
            _valid_row(price_usd="3100.0", outbound_date="2027-04-08", return_date="2027-04-19"),
            _valid_row(price_usd="3050.0", outbound_date="2027-04-15", return_date="2027-04-26"),
        ]
        csv_path = tmp_path / "seed.csv"
        _write_csv(csv_path, rows)

        stats = run_seed(csv_path=csv_path)
        assert stats["rows_imported"] == 3

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 3
        assert all(obs["observation_type"] == "historical_seed" for obs in series)

    def test_economy_cabin_filtered(self, tmp_store, tmp_path):
        """Economy class must be rejected by constraint engine."""
        from radar.stages.seed import run_seed

        csv_path = tmp_path / "seed.csv"
        _write_csv(csv_path, [_valid_row(cabin="ECONOMY")])

        stats = run_seed(csv_path=csv_path)
        assert stats["rows_imported"] == 0
        assert stats["rows_filtered"] == 1

    def test_31_hour_outbound_filtered(self, tmp_store, tmp_path):
        """31-hour outbound must be rejected by constraint engine (independent per-leg limit)."""
        from radar.stages.seed import run_seed

        csv_path = tmp_path / "seed.csv"
        _write_csv(csv_path, [_valid_row(outbound_duration_hours="31.0", return_duration_hours="20.0")])

        stats = run_seed(csv_path=csv_path)
        assert stats["rows_imported"] == 0
        assert stats["rows_filtered"] == 1

    def test_8_nights_filtered(self, tmp_store, tmp_path):
        """8-night trip must be rejected (minimum 9 nights)."""
        from radar.stages.seed import run_seed

        csv_path = tmp_path / "seed.csv"
        _write_csv(csv_path, [_valid_row(outbound_date="2027-04-01", return_date="2027-04-09")])

        stats = run_seed(csv_path=csv_path)
        assert stats["rows_imported"] == 0
        assert stats["rows_filtered"] == 1

    def test_before_window_filtered(self, tmp_store, tmp_path):
        """Dates before travel window start must be rejected."""
        from radar.stages.seed import run_seed

        csv_path = tmp_path / "seed.csv"
        _write_csv(csv_path, [_valid_row(outbound_date="2027-01-01", return_date="2027-01-12")])

        stats = run_seed(csv_path=csv_path)
        assert stats["rows_imported"] == 0
        assert stats["rows_filtered"] == 1

    def test_dry_run_does_not_write(self, tmp_store, tmp_path):
        """Dry run must parse and count without writing to the store."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_path = tmp_path / "seed.csv"
        _write_csv(csv_path, [_valid_row()])

        stats = run_seed(csv_path=csv_path, dry_run=True)
        assert stats["dry_run"] is True
        assert stats["rows_imported"] == 1  # counted but not written

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0, "Dry run must not write to the store"


class TestSeedJSONImport:
    def test_valid_json_list_imports(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        json_path = tmp_path / "seed.json"
        json_path.write_text(json.dumps([_valid_row()]), encoding="utf-8")

        stats = run_seed(json_path=json_path)
        assert stats["rows_imported"] == 1

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert series[0]["observation_type"] == "historical_seed"

    def test_json_with_observations_key(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed

        json_path = tmp_path / "seed.json"
        json_path.write_text(json.dumps({"observations": [_valid_row()]}), encoding="utf-8")

        stats = run_seed(json_path=json_path)
        assert stats["rows_imported"] == 1


class TestSeedNoFileError:
    def test_no_file_returns_error(self, tmp_store):
        from radar.stages.seed import run_seed

        stats = run_seed()
        assert "error" in stats
        assert stats["rows_imported"] == 0


class TestSeedPreservesHistory:
    def test_seed_then_daily_series_preserved(self, tmp_store, tmp_path):
        """After seeding, daily observations must append without overwriting seed data."""
        from radar.stages.seed import run_seed
        from radar.schema_store import append_observation, get_series

        csv_path = tmp_path / "seed.csv"
        rows = [_valid_row(price_usd=str(3000 + i * 50)) for i in range(5)]
        _write_csv(csv_path, rows)
        run_seed(csv_path=csv_path)

        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=2800.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="daily",
        )

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 6
        assert series[0]["observation_type"] == "historical_seed"
        assert series[-1]["observation_type"] == "daily"
        assert series[-1]["price_usd"] == 2800.0

        first_price = series[0]["price_usd"]
        assert first_price == 3000.0, "Seed history must not be overwritten"
