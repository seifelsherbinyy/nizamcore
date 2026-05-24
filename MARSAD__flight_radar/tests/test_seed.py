"""
Tests for the HISTORICAL SEED module (Stage 0).

EXECUTED_IN_SESSION: All tests run with pytest.
Uses temporary directories to avoid touching the real data store.
Tests cover CSV import, constraint validation, and dry-run mode.
"""

import csv
import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect schema_store paths to a temporary directory."""
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


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


_VALID_ROW = {
    "origin": "CAI",
    "destination": "JFK",
    "carrier": "EK",
    "cabin": "BUSINESS",
    "outbound_date": "2027-04-01",
    "return_date": "2027-04-12",
    "price_usd": "3200.0",
    "outbound_duration_hours": "14.5",
    "return_duration_hours": "15.0",
    "outbound_stops": "1",
    "return_stops": "1",
    "outbound_routing": "CAI-DXB-JFK",
    "return_routing": "JFK-DXB-CAI",
    "source": "test_manual",
}


class TestCSVImport:
    def test_valid_row_imports(self, tmp_store, tmp_path):
        csv_path = tmp_path / "seed.csv"
        _write_csv(csv_path, [_VALID_ROW])

        from radar.stages.seed import run_seed_from_csv
        stats = run_seed_from_csv(csv_path)

        assert stats["rows_read"] == 1
        assert stats["rows_imported"] == 1
        assert stats["rows_skipped_constraint"] == 0

    def test_invalid_origin_filtered(self, tmp_store, tmp_path):
        """Rows with wrong origin are filtered by constraint engine."""
        csv_path = tmp_path / "seed.csv"
        row = {**_VALID_ROW, "origin": "LHR"}
        _write_csv(csv_path, [row])

        from radar.stages.seed import run_seed_from_csv
        stats = run_seed_from_csv(csv_path)

        assert stats["rows_read"] == 1
        assert stats["rows_imported"] == 0
        assert stats["rows_skipped_constraint"] == 1

    def test_31_hour_outbound_filtered(self, tmp_store, tmp_path):
        """31-hour outbound must be filtered — constraint engine enforces 30h max independently."""
        csv_path = tmp_path / "seed.csv"
        row = {**_VALID_ROW, "outbound_duration_hours": "31.0"}
        _write_csv(csv_path, [row])

        from radar.stages.seed import run_seed_from_csv
        stats = run_seed_from_csv(csv_path)

        assert stats["rows_skipped_constraint"] == 1
        assert stats["rows_imported"] == 0

    def test_economy_cabin_filtered(self, tmp_store, tmp_path):
        """Economy cabin rows are filtered before import."""
        csv_path = tmp_path / "seed.csv"
        row = {**_VALID_ROW, "cabin": "ECONOMY"}
        _write_csv(csv_path, [row])

        from radar.stages.seed import run_seed_from_csv
        stats = run_seed_from_csv(csv_path)

        assert stats["rows_skipped_constraint"] == 1

    def test_dry_run_does_not_write(self, tmp_store, tmp_path):
        """Dry run must not write any observations to the store."""
        csv_path = tmp_path / "seed.csv"
        _write_csv(csv_path, [_VALID_ROW])

        from radar.stages.seed import run_seed_from_csv
        from radar.schema_store import get_series

        stats = run_seed_from_csv(csv_path, dry_run=True)

        assert stats["rows_imported"] == 1  # counted but not written
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0, "Dry run must not write observations"

    def test_missing_required_column_returns_error(self, tmp_store, tmp_path):
        """CSV missing a required column should return an error, not crash."""
        csv_path = tmp_path / "seed_bad.csv"
        # Omit 'price_usd'
        bad_row = {k: v for k, v in _VALID_ROW.items() if k != "price_usd"}
        _write_csv(csv_path, [bad_row])

        from radar.stages.seed import run_seed_from_csv
        stats = run_seed_from_csv(csv_path)

        assert "error" in stats

    def test_observation_type_is_historical_seed(self, tmp_store, tmp_path):
        """Imported rows must be tagged as 'historical_seed', not 'baseline' or 'daily'."""
        csv_path = tmp_path / "seed.csv"
        _write_csv(csv_path, [_VALID_ROW])

        from radar.stages.seed import run_seed_from_csv
        from radar.schema_store import get_series

        run_seed_from_csv(csv_path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"

    def test_multiple_rows_all_imported(self, tmp_store, tmp_path):
        csv_path = tmp_path / "seed.csv"
        rows = [
            {**_VALID_ROW, "outbound_date": "2027-04-01", "return_date": "2027-04-12", "price_usd": "3200"},
            {**_VALID_ROW, "outbound_date": "2027-05-01", "return_date": "2027-05-12", "price_usd": "3100"},
            {**_VALID_ROW, "outbound_date": "2027-06-01", "return_date": "2027-06-12", "price_usd": "2950"},
        ]
        _write_csv(csv_path, rows)

        from radar.stages.seed import run_seed_from_csv
        stats = run_seed_from_csv(csv_path)

        assert stats["rows_imported"] == 3

    def test_file_not_found_returns_error(self, tmp_store):
        from radar.stages.seed import run_seed_from_csv
        stats = run_seed_from_csv(Path("/nonexistent/path.csv"))
        assert "error" in stats


class TestSeedResearch:
    def test_print_seed_research_runs(self, capsys):
        from radar.stages.seed import print_seed_research
        print_seed_research()
        captured = capsys.readouterr()
        assert "SOURCE A" in captured.out
        assert "SerpApi" in captured.out
