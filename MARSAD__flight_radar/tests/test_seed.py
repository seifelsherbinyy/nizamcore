"""
Tests for the historical price SEED importer (seed.py).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses a temporary directory to avoid touching the real data store.
"""

import csv
import io
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect schema_store paths to a temp dir — reused from test_schema_store."""
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


def _write_csv(tmp_path: Path, rows: list[dict]) -> Path:
    """Write a CSV file with the seed template header and the given rows."""
    from radar.stages.seed import _TEMPLATE_HEADER
    csv_path = tmp_path / "seed.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_TEMPLATE_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return csv_path


def _valid_row(**overrides) -> dict:
    """Factory for a valid seed CSV row — override fields to test edge cases."""
    base = {
        "carrier": "EK",
        "cabin": "BUSINESS",
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "price_usd": "3100.00",
        "outbound_duration_hours": "14.5",
        "return_duration_hours": "15.0",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
        "source_name": "google_flights",
        "price_egp": "",
        "price_eur": "",
    }
    base.update(overrides)
    return base


class TestExportTemplate:
    def test_template_has_correct_header(self):
        from radar.stages.seed import export_template, _TEMPLATE_HEADER
        content = export_template()
        first_line = content.splitlines()[0]
        for col in _TEMPLATE_HEADER:
            assert col in first_line

    def test_template_writes_to_file(self, tmp_path):
        from radar.stages.seed import export_template
        out = tmp_path / "template.csv"
        export_template(output_path=out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_template_has_example_rows(self):
        from radar.stages.seed import export_template
        lines = export_template().strip().splitlines()
        # header + at least 2 example rows
        assert len(lines) >= 3


class TestSeedCSVImport:
    def test_valid_row_imported(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed_csv
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path, [_valid_row()])
        stats = run_seed_csv(csv_path)

        assert stats["rows_read"] == 1
        assert stats["rows_imported"] == 1
        assert stats["rows_rejected"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["price_usd"] == 3100.0
        assert series[0]["data_quality"] == "estimated"

    def test_destination_extracted_from_routing(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed_csv
        from radar.schema_store import get_series

        row = _valid_row(outbound_routing="CAI-DXB-MIA", return_routing="MIA-DXB-CAI",
                         return_date="2027-04-12")
        csv_path = _write_csv(tmp_path, [row])
        run_seed_csv(csv_path)

        series = get_series("CAI", "MIA", "EK", "BUSINESS")
        assert len(series) == 1

    def test_dry_run_does_not_write_to_store(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed_csv
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path, [_valid_row()])
        stats = run_seed_csv(csv_path, dry_run=True)

        assert stats["rows_imported"] == 1
        assert stats["dry_run"] is True
        # Nothing written to store
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0

    def test_constraint_violation_rejected(self, tmp_store, tmp_path):
        """A 31-hour outbound must be rejected by the constraint engine."""
        from radar.stages.seed import run_seed_csv

        row = _valid_row(outbound_duration_hours="31.0")
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed_csv(csv_path)

        assert stats["rows_rejected"] == 1
        assert stats["rows_imported"] == 0
        assert any("31" in r or "outbound_duration" in r for r in stats["rejection_reasons"])

    def test_economy_cabin_rejected(self, tmp_store, tmp_path):
        """Economy class must be rejected — MARSAD monitors Business and Premium Economy only."""
        from radar.stages.seed import run_seed_csv

        row = _valid_row(cabin="ECONOMY")
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed_csv(csv_path)

        assert stats["rows_rejected"] == 1

    def test_8_nights_duration_rejected(self, tmp_store, tmp_path):
        """Trip duration below 9 nights must be rejected."""
        from radar.stages.seed import run_seed_csv

        row = _valid_row(
            outbound_date="2027-04-01",
            return_date="2027-04-09",   # 8 nights
        )
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed_csv(csv_path)

        assert stats["rows_rejected"] == 1

    def test_out_of_window_date_rejected(self, tmp_store, tmp_path):
        """Departure dates before travel window must be rejected."""
        from radar.stages.seed import run_seed_csv

        row = _valid_row(
            outbound_date="2027-01-15",
            return_date="2027-01-26",
        )
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed_csv(csv_path)

        assert stats["rows_rejected"] == 1

    def test_missing_csv_file_returns_error(self, tmp_store):
        from radar.stages.seed import run_seed_csv

        stats = run_seed_csv(Path("/nonexistent/path/seed.csv"))
        assert "error" in stats

    def test_invalid_price_rejected(self, tmp_store, tmp_path):
        """Non-numeric price_usd must produce a parse error."""
        from radar.stages.seed import run_seed_csv

        row = _valid_row(price_usd="not_a_number")
        csv_path = _write_csv(tmp_path, [row])
        stats = run_seed_csv(csv_path)

        assert stats["rows_rejected"] == 1

    def test_multiple_rows_mixed_validity(self, tmp_store, tmp_path):
        """Valid and invalid rows in the same file — each handled independently."""
        from radar.stages.seed import run_seed_csv

        rows = [
            _valid_row(),
            _valid_row(outbound_duration_hours="35.0"),  # exceeds 30h
            _valid_row(cabin="PREMIUM_ECONOMY",
                       outbound_routing="CAI-DOH-LAX",
                       return_routing="LAX-DOH-CAI",
                       outbound_duration_hours="18.0",
                       return_duration_hours="17.5"),
        ]
        csv_path = _write_csv(tmp_path, rows)
        stats = run_seed_csv(csv_path)

        assert stats["rows_read"] == 3
        assert stats["rows_imported"] == 2
        assert stats["rows_rejected"] == 1

    def test_7_imported_unlocks_cold_start(self, tmp_store, tmp_path):
        """Importing ≥7 observations should set baseline_accelerated=True."""
        from radar.stages.seed import run_seed_csv

        rows = []
        destinations_and_nights = [
            ("JFK", 9), ("JFK", 10), ("JFK", 11), ("JFK", 12), ("JFK", 13), ("JFK", 14),
            ("JFK", 9),  # duplicate date pair is ok — two separate observations
        ]
        for dest, nights in destinations_and_nights:
            from datetime import date, timedelta
            dep = date(2027, 4, 1)
            ret = dep + timedelta(days=nights)
            rows.append(_valid_row(
                outbound_date=dep.isoformat(),
                return_date=ret.isoformat(),
                outbound_routing=f"CAI-DXB-{dest}",
                return_routing=f"{dest}-DXB-CAI",
            ))

        csv_path = _write_csv(tmp_path, rows)
        stats = run_seed_csv(csv_path)

        assert stats["rows_imported"] == 7
        assert stats["baseline_accelerated"] is True

    def test_seed_observation_type_is_historical_seed(self, tmp_store, tmp_path):
        """Every imported row must have observation_type='historical_seed'."""
        from radar.stages.seed import run_seed_csv
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path, [_valid_row(), _valid_row(return_date="2027-04-13")])
        run_seed_csv(csv_path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert all(obs["observation_type"] == "historical_seed" for obs in series)

    def test_source_name_preserved_in_store(self, tmp_store, tmp_path):
        """source_name from CSV should be stored in the observation's source field."""
        from radar.stages.seed import run_seed_csv
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path, [_valid_row(source_name="kayak")])
        run_seed_csv(csv_path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert series[0]["source"] == "kayak"

    def test_append_invariant_preserved(self, tmp_store, tmp_path):
        """Seeding must never overwrite existing observations in the store."""
        from radar.schema_store import append_observation, get_series
        from radar.stages.seed import run_seed_csv

        # First, write an existing observation directly
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=2900.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )
        first_id = get_series("CAI", "JFK", "EK", "BUSINESS")[0]["observation_id"]

        # Now seed a historical price for the same route
        csv_path = _write_csv(tmp_path, [_valid_row(price_usd="3100.00")])
        run_seed_csv(csv_path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        # Original observation must be unchanged
        assert series[0]["observation_id"] == first_id
        assert series[0]["price_usd"] == 2900.0
        # New seed observation appended
        assert series[1]["price_usd"] == 3100.0
        assert series[1]["observation_type"] == "historical_seed"
