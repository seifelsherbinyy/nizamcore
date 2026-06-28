"""
Tests for the HISTORICAL PRICE SEED module (Stage 0 / pre-pipeline seeder).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses a temporary directory to avoid touching the real data store.
"""

import csv
import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect schema_store and seed paths to a temporary directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    import radar.schema_store as ss
    import radar.config as cfg

    monkeypatch.setattr(ss, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(ss, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(ss, "BACKUPS_DIR", data_dir / "backups")
    monkeypatch.setattr(cfg, "DATA_DIR", data_dir)
    monkeypatch.setattr(cfg, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(cfg, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(cfg, "BACKUPS_DIR", data_dir / "backups")

    return data_dir


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


_VALID_ROW = {
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
}


class TestSeedValidRow:
    def test_valid_row_imports_successfully(self, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_path = tmp_store / "seed.csv"
        _write_csv(csv_path, [_VALID_ROW])

        stats = run_seed(seed_file=csv_path)

        assert stats["rows_read"] == 1
        assert stats["rows_imported"] == 1
        assert stats["rows_constraint_failed"] == 0
        assert stats["rows_parse_error"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["price_usd"] == 3200.0

    def test_dry_run_does_not_write(self, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_path = tmp_store / "seed.csv"
        _write_csv(csv_path, [_VALID_ROW])

        stats = run_seed(seed_file=csv_path, dry_run=True)

        assert stats["dry_run"] is True
        assert stats["rows_imported"] == 1  # counted as "would import"
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0, "dry_run must not write to store"


class TestConstraintFiltering:
    def test_31_hour_outbound_filtered(self, tmp_store):
        """Seed row with 31-hour outbound must be rejected by constraint engine."""
        from radar.stages.seed import run_seed

        bad_row = {**_VALID_ROW, "outbound_duration_hours": "31.0"}
        csv_path = tmp_store / "seed.csv"
        _write_csv(csv_path, [bad_row])

        stats = run_seed(seed_file=csv_path)

        assert stats["rows_imported"] == 0
        assert stats["rows_constraint_failed"] == 1

    def test_wrong_cabin_filtered(self, tmp_store):
        """Economy class must be rejected."""
        from radar.stages.seed import run_seed

        bad_row = {**_VALID_ROW, "cabin": "ECONOMY"}
        csv_path = tmp_store / "seed.csv"
        _write_csv(csv_path, [bad_row])

        stats = run_seed(seed_file=csv_path)

        assert stats["rows_constraint_failed"] == 1
        assert stats["rows_imported"] == 0

    def test_outside_travel_window_filtered(self, tmp_store):
        """Departure before window start must be rejected."""
        from radar.stages.seed import run_seed

        bad_row = {
            **_VALID_ROW,
            "outbound_date": "2027-02-01",
            "return_date": "2027-02-12",
        }
        csv_path = tmp_store / "seed.csv"
        _write_csv(csv_path, [bad_row])

        stats = run_seed(seed_file=csv_path)

        assert stats["rows_constraint_failed"] == 1
        assert stats["rows_imported"] == 0

    def test_wrong_destination_filtered(self, tmp_store):
        """Non-USA destination must be rejected."""
        from radar.stages.seed import run_seed

        bad_row = {**_VALID_ROW, "destination": "LHR"}
        csv_path = tmp_store / "seed.csv"
        _write_csv(csv_path, [bad_row])

        stats = run_seed(seed_file=csv_path)

        assert stats["rows_constraint_failed"] == 1


class TestMixedRows:
    def test_mixed_valid_and_invalid(self, tmp_store):
        """Valid rows are imported; invalid rows are counted but do not block valid ones."""
        from radar.stages.seed import run_seed

        rows = [
            _VALID_ROW,                                       # valid
            {**_VALID_ROW, "cabin": "ECONOMY"},               # invalid
            {**_VALID_ROW, "destination": "LAX"},             # valid (different dest)
        ]
        csv_path = tmp_store / "seed.csv"
        _write_csv(csv_path, rows)

        stats = run_seed(seed_file=csv_path)

        assert stats["rows_read"] == 3
        assert stats["rows_imported"] == 2
        assert stats["rows_constraint_failed"] == 1


class TestJsonFormat:
    def test_json_seed_imports_successfully(self, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        json_data = [
            {
                "origin": "CAI", "destination": "MIA", "carrier": "AF",
                "cabin": "PREMIUM_ECONOMY", "price_usd": 1800.0,
                "outbound_date": "2027-05-01", "return_date": "2027-05-12",
                "outbound_duration_hours": 18.0, "return_duration_hours": 18.0,
                "outbound_stops": 1, "return_stops": 1,
                "outbound_routing": "CAI-CDG-MIA", "return_routing": "MIA-CDG-CAI",
                "source": "hopper_manual",
            }
        ]
        json_path = tmp_store / "seed.json"
        json_path.write_text(json.dumps(json_data), encoding="utf-8")

        stats = run_seed(seed_file=json_path)

        assert stats["rows_imported"] == 1
        series = get_series("CAI", "MIA", "AF", "PREMIUM_ECONOMY")
        assert len(series) == 1
        assert series[0]["source"] == "hopper_manual"


class TestTemplateWrite:
    def test_write_template_creates_csv(self, tmp_store):
        from radar.stages.seed import run_seed

        template_dest = tmp_store / "seed_template.csv"
        stats = run_seed(write_template=True, template_dest=template_dest)

        assert template_dest.exists()
        assert "template_written" in stats
        # Verify it's valid CSV with expected columns
        with open(template_dest, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert "origin" in reader.fieldnames
            assert "cabin" in reader.fieldnames
            assert "price_usd" in reader.fieldnames


class TestSchemaAppendInvariant:
    def test_seed_never_overwrites_existing_observations(self, tmp_store):
        """INVARIANT: seeding must append — existing observations must not be modified."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series, append_observation

        # First: write a real observation
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3100.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi",
        )
        first_id = get_series("CAI", "JFK", "EK", "BUSINESS")[0]["observation_id"]

        # Seed a second observation for the same series
        csv_path = tmp_store / "seed.csv"
        _write_csv(csv_path, [_VALID_ROW])
        run_seed(seed_file=csv_path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        # Original observation untouched
        assert series[0]["observation_id"] == first_id
        assert series[0]["price_usd"] == 3100.0
        # Seed observation appended
        assert series[1]["observation_type"] == "historical_seed"
