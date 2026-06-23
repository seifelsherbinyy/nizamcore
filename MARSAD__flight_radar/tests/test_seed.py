"""
Tests for the SEED module (Stage 0 — historical data import).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses temporary directories and synthetic CSV/JSON seed files.
"""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_ROW = {
    "origin": "CAI",
    "destination": "JFK",
    "carrier": "EK",
    "cabin": "BUSINESS",
    "outbound_date": "2027-04-01",
    "return_date": "2027-04-12",       # 11 nights — within 9–14 constraint
    "outbound_duration_hours": "14.5",
    "return_duration_hours": "15.0",
    "outbound_stops": "1",
    "return_stops": "1",
    "outbound_routing": "CAI-DXB-JFK",
    "return_routing": "JFK-DXB-CAI",
    "price_usd": "3200.00",
    "price_egp": "",
    "price_eur": "",
    "source_notes": "kayak_price_history_2026",
}


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect schema store to a temp directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    alerts_dir = tmp_path / "alerts"
    alerts_dir.mkdir()

    import radar.schema_store as ss
    monkeypatch.setattr(ss, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(ss, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(ss, "BACKUPS_DIR", data_dir / "backups")
    return data_dir


def _write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f)


# ── Parse and constraint tests ────────────────────────────────────────────────

class TestParseRow:
    def test_valid_row_parses(self):
        from radar.stages.seed import _parse_row
        itin, extras, errors = _parse_row(VALID_ROW, 2)
        assert errors == []
        assert itin is not None
        assert itin.origin == "CAI"
        assert itin.destination == "JFK"
        assert itin.carrier == "EK"
        assert itin.cabin == "BUSINESS"
        assert itin.price_usd == 3200.0

    def test_missing_required_column_returns_error(self):
        from radar.stages.seed import _parse_row
        row = {k: v for k, v in VALID_ROW.items() if k != "price_usd"}
        itin, extras, errors = _parse_row(row, 2)
        assert itin is None
        assert any("price_usd" in e for e in errors)

    def test_invalid_date_returns_error(self):
        from radar.stages.seed import _parse_row
        row = {**VALID_ROW, "outbound_date": "2027-13-01"}  # invalid month 13
        itin, extras, errors = _parse_row(row, 2)
        assert itin is None
        assert any("date" in e.lower() for e in errors)

    def test_zero_price_returns_error(self):
        from radar.stages.seed import _parse_row
        row = {**VALID_ROW, "price_usd": "0"}
        itin, extras, errors = _parse_row(row, 2)
        assert itin is None
        assert any("price_usd" in e for e in errors)

    def test_extras_parsed_correctly(self):
        from radar.stages.seed import _parse_row
        row = {**VALID_ROW, "price_egp": "150000.00", "source_notes": "google_flights"}
        itin, extras, errors = _parse_row(row, 2)
        assert extras is not None
        assert extras["price_egp"] == 150000.0
        assert extras["outbound_routing"] == "CAI-DXB-JFK"


class TestConstraintEnforcement:
    """Seed module must apply the routing constraint engine to every row."""

    def test_economy_cabin_fails_constraint(self):
        from radar.stages.seed import _parse_row
        from radar.constraints import apply_constraints
        row = {**VALID_ROW, "cabin": "ECONOMY"}
        itin, extras, errors = _parse_row(row, 2)
        assert itin is not None  # parse succeeds
        result = apply_constraints(itin)
        assert not result.passed

    def test_8_nights_fails_constraint(self):
        """Below 9-night minimum."""
        from radar.stages.seed import _parse_row
        from radar.constraints import apply_constraints
        row = {**VALID_ROW, "return_date": "2027-04-09"}  # 8 nights
        itin, extras, errors = _parse_row(row, 2)
        assert itin is not None
        result = apply_constraints(itin)
        assert not result.passed
        assert any("duration" in f for f in result.failures)

    def test_31_hour_outbound_fails_constraint(self):
        """31-hour outbound violates the 30-hour independent per-leg constraint."""
        from radar.stages.seed import _parse_row
        from radar.constraints import apply_constraints
        row = {**VALID_ROW, "outbound_duration_hours": "31.0"}
        itin, extras, errors = _parse_row(row, 2)
        assert itin is not None
        result = apply_constraints(itin)
        assert not result.passed
        assert any("outbound_duration" in f for f in result.failures)

    def test_non_usa_destination_fails_constraint(self):
        from radar.stages.seed import _parse_row
        from radar.constraints import apply_constraints
        row = {**VALID_ROW, "destination": "LHR"}
        itin, extras, errors = _parse_row(row, 2)
        assert itin is not None
        result = apply_constraints(itin)
        assert not result.passed


# ── CSV import tests ──────────────────────────────────────────────────────────

class TestCSVImport:
    def test_single_valid_row_imported(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        f = tmp_path / "seed.csv"
        _write_csv(f, [VALID_ROW])

        stats = run_seed(f)
        assert stats["rows_read"] == 1
        assert stats["rows_imported"] == 1
        assert stats["rows_skipped_constraint"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["data_quality"] == "estimated"
        assert series[0]["price_usd"] == 3200.0

    def test_constraint_failing_row_skipped(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        bad_row = {**VALID_ROW, "cabin": "ECONOMY"}
        f = tmp_path / "seed.csv"
        _write_csv(f, [bad_row])

        stats = run_seed(f)
        assert stats["rows_imported"] == 0
        assert stats["rows_skipped_constraint"] == 1
        assert len(stats["constraint_failures"]) == 1

    def test_duplicate_row_skipped_silently(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        f = tmp_path / "seed.csv"
        # Two identical rows
        _write_csv(f, [VALID_ROW, VALID_ROW])

        stats = run_seed(f)
        assert stats["rows_imported"] == 1
        assert stats["rows_skipped_duplicate"] == 1

        # Only one observation should exist
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1

    def test_multiple_valid_rows_all_imported(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        row2 = {**VALID_ROW, "outbound_date": "2027-05-01", "return_date": "2027-05-12", "price_usd": "3100.00"}
        row3 = {**VALID_ROW, "outbound_date": "2027-06-01", "return_date": "2027-06-12", "price_usd": "3300.00"}
        f = tmp_path / "seed.csv"
        _write_csv(f, [VALID_ROW, row2, row3])

        stats = run_seed(f)
        assert stats["rows_imported"] == 3
        assert stats["rows_skipped_constraint"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 3

    def test_append_never_overwrites_existing(self, tmp_path, tmp_store):
        """INVARIANT: importing seed data must not overwrite existing observations."""
        from radar.stages.seed import run_seed
        from radar.schema_store import append_observation, get_series

        # Pre-populate with a 'daily' observation
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3500.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="daily",
        )

        # Seed a different price for the same date (not a duplicate — different price)
        seed_row = {**VALID_ROW, "outbound_date": "2027-05-01", "return_date": "2027-05-12", "price_usd": "3200.00"}
        f = tmp_path / "seed.csv"
        _write_csv(f, [seed_row])

        run_seed(f)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        # Original daily observation must be unchanged
        assert series[0]["observation_type"] == "daily"
        assert series[0]["price_usd"] == 3500.0


# ── JSON import tests ─────────────────────────────────────────────────────────

class TestJSONImport:
    def test_json_list_imported(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        f = tmp_path / "seed.json"
        _write_json(f, [VALID_ROW])

        stats = run_seed(f)
        assert stats["rows_imported"] == 1

    def test_non_list_json_raises(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        f = tmp_path / "seed.json"
        with open(f, "w") as g:
            json.dump({"not": "a list"}, g)

        with pytest.raises(ValueError, match="list of objects"):
            run_seed(f)

    def test_unsupported_format_raises(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        f = tmp_path / "seed.xlsx"
        f.write_text("dummy")

        with pytest.raises(ValueError, match="Unsupported seed file format"):
            run_seed(f)


# ── Dry run ───────────────────────────────────────────────────────────────────

class TestDryRun:
    def test_dry_run_does_not_write_to_store(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        f = tmp_path / "seed.csv"
        _write_csv(f, [VALID_ROW])

        stats = run_seed(f, dry_run=True)
        assert stats["rows_imported"] == 1
        assert stats["dry_run"] is True

        # Nothing should be in the store
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0

    def test_dry_run_reports_correct_counts(self, tmp_path, tmp_store):
        from radar.stages.seed import run_seed

        bad_row = {**VALID_ROW, "cabin": "ECONOMY"}
        f = tmp_path / "seed.csv"
        _write_csv(f, [VALID_ROW, bad_row])

        stats = run_seed(f, dry_run=True)
        assert stats["rows_read"] == 2
        assert stats["rows_imported"] == 1      # valid row
        assert stats["rows_skipped_constraint"] == 1  # economy cabin


# ── Template generation ───────────────────────────────────────────────────────

class TestSeedTemplate:
    def test_template_creates_csv_with_headers(self, tmp_path):
        from radar.stages.seed import generate_seed_template, SEED_CSV_COLUMNS

        out = tmp_path / "template.csv"
        generate_seed_template(out)

        assert out.exists()
        with open(out, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Template has one example row
        assert len(rows) == 1
        # All required columns present
        for col in SEED_CSV_COLUMNS:
            assert col in rows[0], f"Required column {col!r} missing from template"

    def test_template_example_row_is_valid(self, tmp_path, tmp_store):
        """The example row in the template must pass constraint validation."""
        from radar.stages.seed import generate_seed_template, run_seed

        out = tmp_path / "template.csv"
        generate_seed_template(out)

        stats = run_seed(out, dry_run=True)
        assert stats["rows_imported"] == 1, (
            f"Template example row must be valid — constraint failures: {stats['constraint_failures']}"
        )


# ── File not found ────────────────────────────────────────────────────────────

class TestFileNotFound:
    def test_missing_file_raises(self, tmp_store):
        from radar.stages.seed import run_seed

        with pytest.raises(FileNotFoundError):
            run_seed("/nonexistent/path/seed.csv")
