"""
Tests for the HISTORICAL PRICE SEED IMPORT module.

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses temporary files and directories — no live data store is touched.
"""

from __future__ import annotations

import csv
import json
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

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


@pytest.fixture()
def valid_csv_file(tmp_path) -> Path:
    """Write a valid CSV seed file with one qualifying record."""
    path = tmp_path / "seed.csv"
    header = [
        "origin", "destination", "carrier", "cabin",
        "outbound_date", "return_date", "price_usd",
        "outbound_duration_hours", "return_duration_hours",
        "outbound_stops", "return_stops",
        "outbound_routing", "return_routing",
        "price_egp", "price_eur", "data_quality",
    ]
    rows = [
        ["CAI", "JFK", "EK", "BUSINESS", "2027-04-01", "2027-04-12", "3200",
         "14.5", "15.0", "1", "1", "CAI-DXB-JFK", "JFK-DXB-CAI", "", "", "estimated"],
        ["CAI", "LAX", "QR", "PREMIUM_ECONOMY", "2027-05-15", "2027-05-26", "1450",
         "16.0", "17.0", "1", "1", "CAI-DOH-LAX", "LAX-DOH-CAI", "", "", "estimated"],
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    return path


@pytest.fixture()
def valid_json_file(tmp_path) -> Path:
    """Write a valid JSON seed file with one qualifying record."""
    path = tmp_path / "seed.json"
    records = [
        {
            "origin": "CAI", "destination": "JFK", "carrier": "EK",
            "cabin": "BUSINESS", "outbound_date": "2027-04-01",
            "return_date": "2027-04-12", "price_usd": 3200.0,
            "outbound_duration_hours": 14.5, "return_duration_hours": 15.0,
            "outbound_stops": 1, "return_stops": 1,
            "outbound_routing": "CAI-DXB-JFK", "return_routing": "JFK-DXB-CAI",
            "data_quality": "estimated",
        }
    ]
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


# ── ParseRow unit tests ───────────────────────────────────────────────────────

class TestParseRow:
    def test_valid_row_parses(self):
        from radar.stages.seed_import import _parse_row
        row = {
            "origin": "CAI", "destination": "JFK", "carrier": "EK",
            "cabin": "BUSINESS", "outbound_date": "2027-04-01",
            "return_date": "2027-04-12", "price_usd": "3200",
            "outbound_duration_hours": "14.5", "return_duration_hours": "15.0",
            "outbound_stops": "1", "return_stops": "1",
            "outbound_routing": "CAI-DXB-JFK", "return_routing": "JFK-DXB-CAI",
        }
        result = _parse_row(row)
        assert result is not None
        assert result["origin"] == "CAI"
        assert result["price_usd"] == 3200.0
        assert result["outbound_duration_hours"] == 14.5

    def test_missing_required_field_returns_none(self):
        from radar.stages.seed_import import _parse_row
        row = {
            "origin": "CAI", "destination": "JFK", "carrier": "EK",
            "cabin": "BUSINESS", "outbound_date": "2027-04-01",
            # missing return_date, price_usd, etc.
        }
        assert _parse_row(row) is None

    def test_bad_price_returns_none(self):
        from radar.stages.seed_import import _parse_row
        row = {
            "origin": "CAI", "destination": "JFK", "carrier": "EK",
            "cabin": "BUSINESS", "outbound_date": "2027-04-01",
            "return_date": "2027-04-12", "price_usd": "not_a_number",
            "outbound_duration_hours": "14.5", "return_duration_hours": "15.0",
        }
        assert _parse_row(row) is None

    def test_uppercase_normalization(self):
        from radar.stages.seed_import import _parse_row
        row = {
            "origin": "cai", "destination": "jfk", "carrier": "ek",
            "cabin": "business", "outbound_date": "2027-04-01",
            "return_date": "2027-04-12", "price_usd": "3200",
            "outbound_duration_hours": "14.5", "return_duration_hours": "15.0",
        }
        result = _parse_row(row)
        assert result["origin"] == "CAI"
        assert result["destination"] == "JFK"
        assert result["carrier"] == "EK"
        assert result["cabin"] == "BUSINESS"


# ── Constraint enforcement ────────────────────────────────────────────────────

class TestSeedConstraintFiltering:
    def test_economy_cabin_filtered(self, tmp_store, tmp_path):
        """Economy cabin must be filtered out by constraint engine."""
        from radar.stages.seed_import import run_seed_import

        path = tmp_path / "economy_seed.csv"
        header = ["origin","destination","carrier","cabin","outbound_date","return_date",
                  "price_usd","outbound_duration_hours","return_duration_hours",
                  "outbound_stops","return_stops","outbound_routing","return_routing"]
        row = ["CAI","JFK","EK","ECONOMY","2027-04-01","2027-04-12","800",
               "14.5","15.0","1","1","CAI-DXB-JFK","JFK-DXB-CAI"]
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(row)

        stats = run_seed_import(str(path), fmt="csv", dry_run=True)
        assert stats["filtered_by_constraints"] == 1
        assert stats["imported"] == 0

    def test_31_hour_outbound_filtered(self, tmp_store, tmp_path):
        """Itineraries with outbound > 30h must be filtered by constraint engine."""
        from radar.stages.seed_import import run_seed_import

        path = tmp_path / "long_flight.csv"
        header = ["origin","destination","carrier","cabin","outbound_date","return_date",
                  "price_usd","outbound_duration_hours","return_duration_hours",
                  "outbound_stops","return_stops","outbound_routing","return_routing"]
        row = ["CAI","JFK","EK","BUSINESS","2027-04-01","2027-04-12","3200",
               "31.0","15.0","2","1","CAI-X-Y-JFK","JFK-X-CAI"]
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(row)

        stats = run_seed_import(str(path), fmt="csv", dry_run=True)
        assert stats["filtered_by_constraints"] == 1
        assert stats["imported"] == 0

    def test_outside_window_filtered(self, tmp_store, tmp_path):
        """Departures before the travel window start must be filtered."""
        from radar.stages.seed_import import run_seed_import

        path = tmp_path / "early.csv"
        header = ["origin","destination","carrier","cabin","outbound_date","return_date",
                  "price_usd","outbound_duration_hours","return_duration_hours",
                  "outbound_stops","return_stops","outbound_routing","return_routing"]
        row = ["CAI","JFK","EK","BUSINESS","2027-01-01","2027-01-12","3000",
               "14.5","15.0","1","1","CAI-DXB-JFK","JFK-DXB-CAI"]
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(row)

        stats = run_seed_import(str(path), fmt="csv", dry_run=True)
        assert stats["filtered_by_constraints"] == 1


# ── Dry-run mode ──────────────────────────────────────────────────────────────

class TestDryRun:
    def test_dry_run_counts_but_does_not_write(self, tmp_store, valid_csv_file):
        from radar.stages.seed_import import run_seed_import
        from radar.schema_store import get_all_series_keys

        stats = run_seed_import(str(valid_csv_file), fmt="csv", dry_run=True)
        assert stats["dry_run"] is True
        assert stats["imported"] == 2

        # Store must still be empty (dry run did not write)
        keys = get_all_series_keys()
        assert len(keys) == 0

    def test_live_run_writes_to_store(self, tmp_store, valid_csv_file):
        from radar.stages.seed_import import run_seed_import
        from radar.schema_store import get_all_series_keys, get_series

        stats = run_seed_import(str(valid_csv_file), fmt="csv", dry_run=False)
        assert stats["imported"] == 2

        keys = get_all_series_keys()
        assert len(keys) == 2

        # Verify observation type is 'historical_seed'
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["source"] == "historical_seed"


# ── JSON format ───────────────────────────────────────────────────────────────

class TestJSONFormat:
    def test_json_import(self, tmp_store, valid_json_file):
        from radar.stages.seed_import import run_seed_import
        from radar.schema_store import get_series

        stats = run_seed_import(str(valid_json_file), fmt="json", dry_run=False)
        assert stats["imported"] == 1

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["price_usd"] == 3200.0

    def test_json_with_records_key(self, tmp_store, tmp_path):
        from radar.stages.seed_import import run_seed_import

        path = tmp_path / "wrapped.json"
        data = {
            "records": [
                {
                    "origin": "CAI", "destination": "JFK", "carrier": "EK",
                    "cabin": "BUSINESS", "outbound_date": "2027-04-01",
                    "return_date": "2027-04-12", "price_usd": 3200.0,
                    "outbound_duration_hours": 14.5, "return_duration_hours": 15.0,
                    "outbound_stops": 1, "return_stops": 1,
                    "outbound_routing": "CAI-DXB-JFK", "return_routing": "JFK-DXB-CAI",
                }
            ]
        }
        path.write_text(json.dumps(data), encoding="utf-8")

        stats = run_seed_import(str(path), fmt="json", dry_run=True)
        assert stats["imported"] == 1


# ── Error handling ────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_missing_file_raises(self, tmp_store):
        from radar.stages.seed_import import run_seed_import
        with pytest.raises(FileNotFoundError):
            run_seed_import("/nonexistent/path/seed.csv")

    def test_parse_errors_counted_and_skipped(self, tmp_store, tmp_path):
        from radar.stages.seed_import import run_seed_import

        path = tmp_path / "bad.csv"
        header = ["origin","destination","carrier","cabin","outbound_date","return_date",
                  "price_usd","outbound_duration_hours","return_duration_hours",
                  "outbound_stops","return_stops","outbound_routing","return_routing"]
        rows = [
            # Good record
            ["CAI","JFK","EK","BUSINESS","2027-04-01","2027-04-12","3200",
             "14.5","15.0","1","1","CAI-DXB-JFK","JFK-DXB-CAI"],
            # Bad record — price is not a number
            ["CAI","JFK","EK","BUSINESS","2027-04-01","2027-04-12","NOT_A_PRICE",
             "14.5","15.0","1","1","CAI-DXB-JFK","JFK-DXB-CAI"],
        ]
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        stats = run_seed_import(str(path), fmt="csv", dry_run=True, skip_invalid=True)
        assert stats["total_records"] == 2
        assert stats["imported"] == 1
        assert stats["parse_errors"] == 1

    def test_append_never_overwrites_existing_history(self, tmp_store, valid_json_file):
        """Importing the same seed file twice must create two separate observations (no dedup)."""
        from radar.stages.seed_import import run_seed_import
        from radar.schema_store import get_series

        run_seed_import(str(valid_json_file), fmt="json", dry_run=False)
        run_seed_import(str(valid_json_file), fmt="json", dry_run=False)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        # Store is append-only — both imports succeed, no overwrite
        assert len(series) == 2
        assert series[0]["price_usd"] == series[1]["price_usd"]


# ── Template generation ───────────────────────────────────────────────────────

class TestTemplateGeneration:
    def test_template_creates_csv(self, tmp_path):
        from radar.stages.seed_import import generate_seed_template

        out = str(tmp_path / "template.csv")
        result = generate_seed_template(out)
        assert Path(result).exists()

        with open(result, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert "origin" in header
        assert "price_usd" in header
        assert "outbound_routing" in header
