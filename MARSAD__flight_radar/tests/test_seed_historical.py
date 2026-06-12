"""
Tests for the HISTORICAL SEED module (Stage 0).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses temporary directories — no real API calls made.
"""

import csv
import json
import os
import tempfile
from pathlib import Path

import pytest


# ── Fixture: redirect store paths to a tmp dir ────────────────────────────────

@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
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


# ── HistoricalSeedRecord ──────────────────────────────────────────────────────

class TestHistoricalSeedRecord:
    def test_dataclass_instantiation(self):
        from radar.seed_historical import HistoricalSeedRecord
        rec = HistoricalSeedRecord(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            outbound_date="2027-04-01", return_date="2027-04-12",
            price_usd=3200.0,
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="kayak_manual",
        )
        assert rec.origin == "CAI"
        assert rec.data_quality == "estimated"
        assert rec.price_egp is None


# ── import_records (internal) ─────────────────────────────────────────────────

class TestImportRecords:
    def _valid_record(self, **overrides):
        from radar.seed_historical import HistoricalSeedRecord
        defaults = dict(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            outbound_date="2027-04-01", return_date="2027-04-12",
            price_usd=3200.0,
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="test_seed",
        )
        defaults.update(overrides)
        return HistoricalSeedRecord(**defaults)

    def test_valid_record_imports(self, tmp_store):
        from radar.seed_historical import import_records
        from radar.schema_store import get_series

        rec = self._valid_record()
        stats = import_records([rec])

        assert stats["records_imported"] == 1
        assert stats["records_skipped_constraint"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["price_usd"] == 3200.0

    def test_constraint_violation_skipped(self, tmp_store):
        """A record with wrong origin must be silently skipped, not imported."""
        from radar.seed_historical import import_records

        rec = self._valid_record(origin="LHR")
        stats = import_records([rec])

        assert stats["records_imported"] == 0
        assert stats["records_skipped_constraint"] == 1
        assert len(stats["constraint_failures"]) == 1

    def test_outside_window_skipped(self, tmp_store):
        """Departure before WINDOW_START must be rejected by constraint engine."""
        from radar.seed_historical import import_records

        rec = self._valid_record(outbound_date="2026-01-01", return_date="2026-01-12")
        stats = import_records([rec])

        assert stats["records_imported"] == 0
        assert stats["records_skipped_constraint"] == 1

    def test_wrong_cabin_skipped(self, tmp_store):
        from radar.seed_historical import import_records

        rec = self._valid_record(cabin="ECONOMY")
        stats = import_records([rec])

        assert stats["records_imported"] == 0
        assert stats["records_skipped_constraint"] == 1

    def test_multiple_records_independent_series(self, tmp_store):
        """Multiple records for different routes create separate series."""
        from radar.seed_historical import import_records
        from radar.schema_store import get_series

        records = [
            self._valid_record(destination="JFK", price_usd=3200.0),
            self._valid_record(destination="LAX", price_usd=3500.0, carrier="QR",
                               outbound_routing="CAI-DOH-LAX", return_routing="LAX-DOH-CAI"),
        ]
        stats = import_records(records)

        assert stats["records_imported"] == 2
        jfk_series = get_series("CAI", "JFK", "EK", "BUSINESS")
        lax_series = get_series("CAI", "LAX", "QR", "BUSINESS")
        assert len(jfk_series) == 1
        assert len(lax_series) == 1

    def test_seed_observations_are_appended_not_overwritten(self, tmp_store):
        """Historical seed records must append — not overwrite — existing series."""
        from radar.seed_historical import import_records
        from radar.schema_store import get_series, append_observation

        # Pre-existing baseline observation
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=3000.0,
            outbound_date="2027-04-01", return_date="2027-04-12",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )

        # Now seed a historical record for the same series
        rec = self._valid_record(price_usd=2900.0)
        import_records([rec])

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        assert series[0]["observation_type"] == "baseline"
        assert series[0]["price_usd"] == 3000.0
        assert series[1]["observation_type"] == "historical_seed"

    def test_bad_date_logged_as_parse_error(self, tmp_store):
        """A record with an invalid date string must not be imported."""
        from radar.seed_historical import HistoricalSeedRecord, import_records

        rec = HistoricalSeedRecord(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            outbound_date="not-a-date", return_date="2027-04-12",
            price_usd=3200.0,
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="test",
        )
        stats = import_records([rec])

        assert stats["records_imported"] == 0
        assert len(stats["parse_errors"]) == 1


# ── CSV import ─────────────────────────────────────────────────────────────────

class TestCSVImport:
    _CSV_HEADER = (
        "origin,destination,carrier,cabin,outbound_date,return_date,"
        "price_usd,outbound_duration_hours,return_duration_hours,"
        "outbound_stops,return_stops,outbound_routing,return_routing,source"
    )
    _CSV_ROW = (
        "CAI,JFK,EK,BUSINESS,2027-04-01,2027-04-12,"
        "3200.0,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI,kayak_manual"
    )

    def _write_csv(self, tmp_path: Path, rows: list[str]) -> Path:
        p = tmp_path / "seed.csv"
        p.write_text(self._CSV_HEADER + "\n" + "\n".join(rows))
        return p

    def test_valid_csv_imports(self, tmp_store, tmp_path):
        from radar.seed_historical import import_csv_seed

        csv_path = self._write_csv(tmp_path, [self._CSV_ROW])
        stats = import_csv_seed(csv_path)

        assert stats["records_imported"] == 1

    def test_missing_column_raises(self, tmp_path):
        from radar.seed_historical import import_csv_seed

        p = tmp_path / "bad.csv"
        p.write_text("origin,destination\nCAI,JFK\n")
        with pytest.raises(ValueError, match="missing required columns"):
            import_csv_seed(p)

    def test_file_not_found_raises(self):
        from radar.seed_historical import import_csv_seed

        with pytest.raises(FileNotFoundError):
            import_csv_seed("/nonexistent/path.csv")

    def test_bad_price_row_is_logged_not_raised(self, tmp_store, tmp_path):
        """A row with non-numeric price must be logged as parse error, not crash."""
        from radar.seed_historical import import_csv_seed

        bad_row = "CAI,JFK,EK,BUSINESS,2027-04-01,2027-04-12,NOT_A_NUMBER,14.5,15.0,1,1,x,y,src"
        csv_path = self._write_csv(tmp_path, [bad_row])
        stats = import_csv_seed(csv_path)

        assert stats["records_imported"] == 0
        assert len(stats["parse_errors"]) >= 1


# ── JSON import ────────────────────────────────────────────────────────────────

class TestJSONImport:
    _VALID_OBJ = {
        "origin": "CAI", "destination": "LAX", "carrier": "QR",
        "cabin": "BUSINESS",
        "outbound_date": "2027-05-01", "return_date": "2027-05-12",
        "price_usd": 3500.0,
        "outbound_duration_hours": 18.5, "return_duration_hours": 19.0,
        "outbound_stops": 1, "return_stops": 1,
        "outbound_routing": "CAI-DOH-LAX", "return_routing": "LAX-DOH-CAI",
        "source": "hopper_manual",
    }

    def _write_json(self, tmp_path: Path, data: list) -> Path:
        p = tmp_path / "seed.json"
        p.write_text(json.dumps(data))
        return p

    def test_valid_json_imports(self, tmp_store, tmp_path):
        from radar.seed_historical import import_json_seed

        json_path = self._write_json(tmp_path, [self._VALID_OBJ])
        stats = import_json_seed(json_path)

        assert stats["records_imported"] == 1

    def test_non_array_json_raises(self, tmp_path):
        from radar.seed_historical import import_json_seed

        p = tmp_path / "bad.json"
        p.write_text(json.dumps({"key": "value"}))
        with pytest.raises(ValueError, match="array"):
            import_json_seed(p)

    def test_missing_field_logged_not_raised(self, tmp_store, tmp_path):
        from radar.seed_historical import import_json_seed

        bad_obj = {"origin": "CAI", "destination": "JFK"}  # missing many fields
        json_path = self._write_json(tmp_path, [bad_obj])
        stats = import_json_seed(json_path)

        assert stats["records_imported"] == 0
        assert len(stats["parse_errors"]) >= 1

    def test_file_not_found_raises(self):
        from radar.seed_historical import import_json_seed

        with pytest.raises(FileNotFoundError):
            import_json_seed("/nonexistent/path.json")


# ── Probe date generation ──────────────────────────────────────────────────────

class TestProbeDateGeneration:
    def test_generates_dates_at_step_interval(self):
        from datetime import date
        from radar.seed_historical import _generate_probe_dates

        dates = _generate_probe_dates(
            window_start=date(2027, 3, 15),
            window_end=date(2027, 9, 30),
            step_days=30,
        )
        assert len(dates) >= 6
        assert dates[0] == "2027-03-15"
        # Confirm spacing
        from datetime import date as d
        for i in range(1, len(dates)):
            diff = (d.fromisoformat(dates[i]) - d.fromisoformat(dates[i-1])).days
            assert diff == 30

    def test_single_date_window(self):
        from datetime import date
        from radar.seed_historical import _generate_probe_dates

        dates = _generate_probe_dates(
            window_start=date(2027, 6, 1),
            window_end=date(2027, 6, 1),
            step_days=7,
        )
        assert len(dates) == 1
        assert dates[0] == "2027-06-01"
