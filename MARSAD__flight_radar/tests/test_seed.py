"""
Tests for the SEED module (Stage 0 — historical price data import).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses temporary directories and in-memory CSV/JSON to avoid touching the real data store.
"""

import csv
import io
import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect all schema_store paths to a temporary directory."""
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


def _write_csv(tmp_path: Path, rows: list[dict]) -> str:
    """Write rows to a temp CSV file; return its path string."""
    csv_path = tmp_path / "seed.csv"
    if rows:
        fieldnames = list(rows[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    else:
        csv_path.write_text("carrier,origin,destination,cabin,outbound_date,return_date,"
                            "price_usd,outbound_duration_hours,return_duration_hours,"
                            "outbound_stops,return_stops,outbound_routing,return_routing\n",
                            encoding="utf-8")
    return str(csv_path)


def _valid_row(**overrides) -> dict:
    base = {
        "carrier": "EK",
        "origin": "CAI",
        "destination": "JFK",
        "cabin": "BUSINESS",
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "price_usd": "3100.0",
        "outbound_duration_hours": "14.5",
        "return_duration_hours": "15.0",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
        "source_name": "hopper",
        "data_quality": "estimated",
    }
    base.update(overrides)
    return base


class TestParseRow:
    def test_valid_row_parses(self):
        from radar.stages.seed import _parse_row
        result = _parse_row(_valid_row())
        assert result is not None
        assert result["carrier"] == "EK"
        assert result["price_usd"] == 3100.0
        assert result["data_quality"] == "estimated"

    def test_missing_required_field_returns_none(self):
        from radar.stages.seed import _parse_row
        row = _valid_row()
        del row["price_usd"]
        assert _parse_row(row) is None

    def test_bad_date_returns_none(self):
        from radar.stages.seed import _parse_row
        result = _parse_row(_valid_row(outbound_date="not-a-date"))
        assert result is None

    def test_non_positive_price_returns_none(self):
        from radar.stages.seed import _parse_row
        assert _parse_row(_valid_row(price_usd="0")) is None
        assert _parse_row(_valid_row(price_usd="-100")) is None

    def test_carrier_uppercased(self):
        from radar.stages.seed import _parse_row
        result = _parse_row(_valid_row(carrier="ek"))
        assert result["carrier"] == "EK"

    def test_cabin_uppercased(self):
        from radar.stages.seed import _parse_row
        result = _parse_row(_valid_row(cabin="business"))
        assert result["cabin"] == "BUSINESS"

    def test_defaults_applied_for_optional_fields(self):
        from radar.stages.seed import _parse_row
        row = _valid_row()
        # Remove optional fields
        row.pop("source_name", None)
        row.pop("data_quality", None)
        result = _parse_row(row)
        assert result is not None
        assert result["source_name"] == "historical_seed"
        assert result["data_quality"] == "estimated"


class TestConstraintFiltering:
    def test_invalid_origin_filtered(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        csv_path = _write_csv(tmp_path, [_valid_row(origin="LHR")])
        stats = run_seed(csv_path=csv_path)
        assert stats["rows_filtered"] == 1
        assert stats["rows_imported"] == 0

    def test_invalid_destination_filtered(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        csv_path = _write_csv(tmp_path, [_valid_row(destination="LHR")])
        stats = run_seed(csv_path=csv_path)
        assert stats["rows_filtered"] == 1

    def test_invalid_cabin_filtered(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        csv_path = _write_csv(tmp_path, [_valid_row(cabin="ECONOMY")])
        stats = run_seed(csv_path=csv_path)
        assert stats["rows_filtered"] == 1

    def test_31_hour_outbound_filtered(self, tmp_store, tmp_path):
        """30-hour independent leg constraint: 31h outbound must be filtered."""
        from radar.stages.seed import run_seed
        csv_path = _write_csv(tmp_path, [_valid_row(outbound_duration_hours="31.0")])
        stats = run_seed(csv_path=csv_path)
        assert stats["rows_filtered"] == 1

    def test_outside_travel_window_filtered(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        # Before window start (2027-03-15)
        csv_path = _write_csv(tmp_path, [_valid_row(
            outbound_date="2027-02-01",
            return_date="2027-02-12",
        )])
        stats = run_seed(csv_path=csv_path)
        assert stats["rows_filtered"] == 1

    def test_too_short_trip_filtered(self, tmp_store, tmp_path):
        """8 nights is below the 9-night minimum."""
        from radar.stages.seed import run_seed
        csv_path = _write_csv(tmp_path, [_valid_row(
            outbound_date="2027-04-01",
            return_date="2027-04-09",  # 8 nights
        )])
        stats = run_seed(csv_path=csv_path)
        assert stats["rows_filtered"] == 1


class TestImport:
    def test_valid_row_imported(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path, [_valid_row()])
        stats = run_seed(csv_path=csv_path)

        assert stats["rows_imported"] == 1
        assert stats["rows_filtered"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["price_usd"] == 3100.0

    def test_observation_type_always_historical_seed(self, tmp_store, tmp_path):
        """observation_type must be 'historical_seed' regardless of input."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path, [_valid_row()])
        run_seed(csv_path=csv_path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert series[0]["observation_type"] == "historical_seed"

    def test_multiple_valid_rows_all_imported(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        rows = [
            _valid_row(outbound_date="2027-04-01", return_date="2027-04-12", price_usd="3100"),
            _valid_row(outbound_date="2027-05-01", return_date="2027-05-12", price_usd="3200"),
            _valid_row(outbound_date="2027-06-01", return_date="2027-06-12", price_usd="2900"),
        ]
        csv_path = _write_csv(tmp_path, rows)
        stats = run_seed(csv_path=csv_path)
        assert stats["rows_imported"] == 3

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 3

    def test_mixed_valid_and_invalid_rows(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed

        rows = [
            _valid_row(),                          # valid
            _valid_row(origin="LHR"),              # filtered — wrong origin
            _valid_row(cabin="ECONOMY"),           # filtered — wrong cabin
            _valid_row(price_usd="0"),             # parse error — non-positive price
        ]
        csv_path = _write_csv(tmp_path, rows)
        stats = run_seed(csv_path=csv_path)
        assert stats["rows_imported"] == 1
        assert stats["rows_filtered"] == 2
        assert stats["rows_parse_error"] == 1

    def test_dry_run_does_not_write(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv_path = _write_csv(tmp_path, [_valid_row()])
        stats = run_seed(csv_path=csv_path, dry_run=True)

        assert stats["dry_run"] is True
        assert stats["rows_imported"] == 1  # "would import" counts as imported in dry_run log

        # But no actual data written — series is empty
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0

    def test_append_only_invariant_preserved(self, tmp_store, tmp_path):
        """Seed import must not overwrite existing observations."""
        from radar.stages.seed import run_seed
        from radar.schema_store import append_observation, get_series

        # Pre-existing baseline observation
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=2800.0,
            outbound_date="2027-03-15", return_date="2027-03-26",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="baseline",
        )
        first_id = get_series("CAI", "JFK", "EK", "BUSINESS")[0]["observation_id"]

        # Now seed an additional historical observation
        csv_path = _write_csv(tmp_path, [_valid_row(price_usd="3100")])
        run_seed(csv_path=csv_path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        # First observation (baseline) must be unchanged
        assert series[0]["observation_id"] == first_id
        assert series[0]["price_usd"] == 2800.0
        assert series[1]["observation_type"] == "historical_seed"


class TestDuplicateDetection:
    def test_same_row_twice_only_imported_once(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        row = _valid_row()
        csv_path = _write_csv(tmp_path, [row])

        # First import
        stats1 = run_seed(csv_path=csv_path)
        assert stats1["rows_imported"] == 1

        # Second import of same file
        stats2 = run_seed(csv_path=csv_path)
        assert stats2["rows_duplicate"] == 1
        assert stats2["rows_imported"] == 0

        # Store should still have only 1 observation
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1

    def test_different_price_same_date_not_duplicate(self, tmp_store, tmp_path):
        """Different price on the same date is a new observation, not a duplicate."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        csv1 = _write_csv(tmp_path, [_valid_row(price_usd="3100")])
        csv2 = _write_csv(tmp_path / "seed2.csv" if False else tmp_path, [_valid_row(price_usd="3200")])

        # Write two different csvs
        (tmp_path / "seed1.csv").write_text(
            "carrier,origin,destination,cabin,outbound_date,return_date,price_usd,"
            "outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,"
            "outbound_routing,return_routing\n"
            "EK,CAI,JFK,BUSINESS,2027-04-01,2027-04-12,3100.0,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI\n",
            encoding="utf-8"
        )
        (tmp_path / "seed2.csv").write_text(
            "carrier,origin,destination,cabin,outbound_date,return_date,price_usd,"
            "outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,"
            "outbound_routing,return_routing\n"
            "EK,CAI,JFK,BUSINESS,2027-04-01,2027-04-12,3200.0,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI\n",
            encoding="utf-8"
        )

        run_seed(csv_path=str(tmp_path / "seed1.csv"))
        stats2 = run_seed(csv_path=str(tmp_path / "seed2.csv"))

        assert stats2["rows_imported"] == 1  # Different price — not a duplicate
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2


class TestJSONImport:
    def test_json_import_works(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series

        records = [
            {
                "carrier": "QR", "origin": "CAI", "destination": "LAX",
                "cabin": "BUSINESS",
                "outbound_date": "2027-04-01", "return_date": "2027-04-12",
                "price_usd": 3400.0,
                "outbound_duration_hours": 18.5, "return_duration_hours": 19.0,
                "outbound_stops": 1, "return_stops": 1,
                "outbound_routing": "CAI-DOH-LAX", "return_routing": "LAX-DOH-CAI",
                "source_name": "hopper", "data_quality": "estimated",
            }
        ]
        json_path = tmp_path / "seed.json"
        json_path.write_text(json.dumps(records), encoding="utf-8")

        stats = run_seed(json_path=str(json_path))
        assert stats["rows_imported"] == 1

        series = get_series("CAI", "LAX", "QR", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["source"] == "hopper"

    def test_json_must_be_array(self, tmp_store, tmp_path):
        from radar.stages.seed import run_seed

        json_path = tmp_path / "seed.json"
        json_path.write_text(json.dumps({"carrier": "EK"}), encoding="utf-8")

        with pytest.raises(ValueError, match="top-level array"):
            run_seed(json_path=str(json_path))


class TestCSVTemplate:
    def test_template_is_valid_csv(self):
        from radar.stages.seed import generate_csv_template
        template = generate_csv_template()
        reader = csv.DictReader(io.StringIO(template))
        rows = list(reader)
        assert len(rows) >= 1

    def test_template_has_required_columns(self):
        from radar.stages.seed import generate_csv_template, _REQUIRED_COLUMNS
        template = generate_csv_template()
        reader = csv.DictReader(io.StringIO(template))
        assert reader.fieldnames is not None
        header_set = set(reader.fieldnames)
        assert _REQUIRED_COLUMNS.issubset(header_set)


class TestCLIEntryPoint:
    def test_no_source_raises(self):
        from radar.stages.seed import run_seed
        with pytest.raises(ValueError, match="Either csv_path or json_path"):
            run_seed()

    def test_missing_csv_raises_file_not_found(self, tmp_store):
        from radar.stages.seed import run_seed
        with pytest.raises(FileNotFoundError):
            run_seed(csv_path="/nonexistent/path/history.csv")
