"""
Tests for the historical seed import module.

EXECUTED_IN_SESSION: All tests run with pytest.
Uses temporary directories — no real data store is touched.
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
    alerts_dir = tmp_path / "alerts"
    alerts_dir.mkdir()

    import radar.schema_store as ss
    monkeypatch.setattr(ss, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(ss, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(ss, "BACKUPS_DIR", data_dir / "backups")
    return data_dir


def _valid_row() -> dict:
    return {
        "origin": "CAI",
        "destination": "JFK",
        "carrier": "EK",
        "cabin": "BUSINESS",
        "price_usd": "3200.00",
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "outbound_duration_hours": "14.5",
        "return_duration_hours": "15.0",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
        "source": "google_flights_manual",
        "price_egp": "",
        "price_eur": "",
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, rows: list[dict]) -> None:
    # Convert CSV-style strings to appropriate types for JSON format
    normalised = []
    for r in rows:
        n = dict(r)
        for key in ("price_usd", "outbound_duration_hours", "return_duration_hours"):
            if n.get(key):
                n[key] = float(n[key])
        for key in ("outbound_stops", "return_stops"):
            if n.get(key):
                n[key] = int(n[key])
        normalised.append(n)
    path.write_text(json.dumps(normalised, indent=2), encoding="utf-8")


class TestLoadSeedCSV:
    def test_valid_csv_loads_one_record(self, tmp_path):
        from radar.seed_historical import load_seed_csv
        path = tmp_path / "seed.csv"
        _write_csv(path, [_valid_row()])
        records = load_seed_csv(path)
        assert len(records) == 1
        assert records[0]["origin"] == "CAI"
        assert records[0]["cabin"] == "BUSINESS"
        assert records[0]["price_usd"] == 3200.0

    def test_invalid_cabin_filtered(self, tmp_path):
        from radar.seed_historical import load_seed_csv
        row = _valid_row()
        row["cabin"] = "ECONOMY"
        path = tmp_path / "seed.csv"
        _write_csv(path, [row])
        records = load_seed_csv(path)
        assert len(records) == 0

    def test_31_hour_outbound_filtered(self, tmp_path):
        """31-hour outbound must be rejected by the constraint engine."""
        from radar.seed_historical import load_seed_csv
        row = _valid_row()
        row["outbound_duration_hours"] = "31.0"
        path = tmp_path / "seed.csv"
        _write_csv(path, [row])
        records = load_seed_csv(path)
        assert len(records) == 0

    def test_pre_window_date_filtered(self, tmp_path):
        from radar.seed_historical import load_seed_csv
        row = _valid_row()
        row["outbound_date"] = "2027-02-01"
        row["return_date"] = "2027-02-12"
        path = tmp_path / "seed.csv"
        _write_csv(path, [row])
        records = load_seed_csv(path)
        assert len(records) == 0

    def test_missing_required_field_filtered(self, tmp_path):
        from radar.seed_historical import load_seed_csv
        row = _valid_row()
        del row["price_usd"]
        path = tmp_path / "seed.csv"
        _write_csv(path, [row])
        records = load_seed_csv(path)
        assert len(records) == 0

    def test_multiple_rows_loaded(self, tmp_path):
        from radar.seed_historical import load_seed_csv
        rows = [_valid_row() for _ in range(5)]
        for i, r in enumerate(rows):
            r["outbound_date"] = f"2027-04-{i + 1:02d}"
            r["return_date"] = f"2027-04-{i + 12:02d}"
            r["price_usd"] = str(3000 + i * 100)
        path = tmp_path / "seed.csv"
        _write_csv(path, rows)
        records = load_seed_csv(path)
        assert len(records) == 5


class TestLoadSeedJSON:
    def test_valid_json_loads(self, tmp_path):
        from radar.seed_historical import load_seed_json
        path = tmp_path / "seed.json"
        _write_json(path, [_valid_row()])
        records = load_seed_json(path)
        assert len(records) == 1

    def test_json_not_array_raises(self, tmp_path):
        from radar.seed_historical import load_seed_json
        path = tmp_path / "seed.json"
        path.write_text(json.dumps({"not": "an array"}), encoding="utf-8")
        with pytest.raises(ValueError):
            load_seed_json(path)


class TestRunSeed:
    def test_dry_run_does_not_write(self, tmp_path, tmp_store):
        from radar.seed_historical import run_seed
        from radar.schema_store import get_series

        path = tmp_path / "seed.csv"
        _write_csv(path, [_valid_row()])
        stats = run_seed(str(path), dry_run=True)

        assert stats["dry_run"] is True
        assert stats["records_imported"] == 1
        # No actual write — series should be empty
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0

    def test_import_writes_to_store(self, tmp_path, tmp_store):
        from radar.seed_historical import run_seed
        from radar.schema_store import get_series

        path = tmp_path / "seed.csv"
        _write_csv(path, [_valid_row()])
        stats = run_seed(str(path), dry_run=False)

        assert stats["records_imported"] == 1
        assert stats["records_skipped"] == 0
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["price_usd"] == 3200.0

    def test_nonexistent_file_returns_error(self, tmp_store):
        from radar.seed_historical import run_seed
        stats = run_seed("/nonexistent/path/seed.csv")
        assert "error" in stats
        assert stats["records_imported"] == 0

    def test_import_seven_records_enables_medium_confidence(self, tmp_path, tmp_store):
        """After 7 seed observations, forecasting confidence must be MEDIUM or higher."""
        from radar.seed_historical import run_seed
        from radar.stages.forecast import _confidence_level
        from radar.schema_store import get_series

        rows = []
        for i in range(7):
            r = _valid_row()
            r["outbound_date"] = f"2027-0{4 + (i // 28):01d}-{(i % 28) + 1:02d}"
            # Keep dates valid and within window
            dep = f"2027-04-{i + 1:02d}"
            ret = f"2027-04-{i + 12:02d}"
            r["outbound_date"] = dep
            r["return_date"] = ret
            r["price_usd"] = str(3000 + i * 50)
            rows.append(r)

        path = tmp_path / "seed7.csv"
        _write_csv(path, rows)
        stats = run_seed(str(path), dry_run=False)
        assert stats["records_imported"] == 7

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 7
        assert _confidence_level(len(series)) == "MEDIUM"


class TestSeedTemplate:
    def test_template_creates_file(self, tmp_path):
        from radar.seed_historical import generate_seed_template
        out = generate_seed_template(str(tmp_path / "template.csv"))
        assert Path(out).exists()

    def test_template_has_required_headers(self, tmp_path):
        from radar.seed_historical import generate_seed_template, _REQUIRED_FIELDS
        out_path = tmp_path / "template.csv"
        generate_seed_template(str(out_path))
        with open(out_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])
        for field in _REQUIRED_FIELDS:
            assert field in headers, f"Missing header: {field}"
