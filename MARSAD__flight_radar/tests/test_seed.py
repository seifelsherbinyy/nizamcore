"""
Tests for the historical price seed importer (radar/seed.py).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses temporary files and a patched store to avoid touching real data.
"""

import csv
import json
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


def _write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)


def _valid_row(**overrides) -> dict:
    base = {
        "destination": "JFK",
        "carrier": "EK",
        "cabin": "BUSINESS",
        "price_usd": "3200",
        "outbound_date": "2027-04-15",
        "return_date": "2027-04-26",
    }
    base.update(overrides)
    return base


class TestCSVImport:
    def test_valid_row_is_imported(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv
        from radar.schema_store import get_series

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [_valid_row()])
        stats = import_from_csv(csv_path)

        assert stats["rows_read"] == 1
        assert stats["rows_imported"] == 1
        assert stats["rows_filtered"] == 0
        assert stats["rows_error"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["price_usd"] == 3200.0

    def test_dry_run_does_not_write_to_store(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv
        from radar.schema_store import get_series

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [_valid_row()])
        stats = import_from_csv(csv_path, dry_run=True)

        assert stats["rows_imported"] == 1
        assert stats["dry_run"] is True
        assert get_series("CAI", "JFK", "EK", "BUSINESS") == []

    def test_invalid_destination_is_filtered(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [_valid_row(destination="LHR")])
        stats = import_from_csv(csv_path)

        assert stats["rows_filtered"] == 1
        assert stats["rows_imported"] == 0

    def test_invalid_cabin_is_filtered(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [_valid_row(cabin="ECONOMY")])
        stats = import_from_csv(csv_path)

        assert stats["rows_filtered"] == 1
        assert stats["rows_imported"] == 0

    def test_date_outside_travel_window_is_filtered(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [_valid_row(outbound_date="2026-12-01", return_date="2026-12-12")])
        stats = import_from_csv(csv_path)

        assert stats["rows_filtered"] == 1

    def test_trip_under_9_nights_is_filtered(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv

        csv_path = tmp_path / "prices.csv"
        # 8 nights — below minimum
        _write_csv(csv_path, [_valid_row(outbound_date="2027-04-01", return_date="2027-04-09")])
        stats = import_from_csv(csv_path)

        assert stats["rows_filtered"] == 1

    def test_trip_over_14_nights_is_filtered(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv

        csv_path = tmp_path / "prices.csv"
        # 15 nights — above maximum
        _write_csv(csv_path, [_valid_row(outbound_date="2027-04-01", return_date="2027-04-16")])
        stats = import_from_csv(csv_path)

        assert stats["rows_filtered"] == 1

    def test_missing_price_counted_as_error(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [{"destination": "JFK", "carrier": "EK", "cabin": "BUSINESS",
                                "outbound_date": "2027-04-01", "return_date": "2027-04-12"}])
        stats = import_from_csv(csv_path)

        assert stats["rows_error"] == 1

    def test_multiple_valid_rows_all_imported(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv

        csv_path = tmp_path / "prices.csv"
        rows = [
            _valid_row(price_usd="3200", outbound_date="2027-04-01", return_date="2027-04-12"),
            _valid_row(price_usd="3100", outbound_date="2027-05-01", return_date="2027-05-12"),
            _valid_row(price_usd="2900", outbound_date="2027-06-01", return_date="2027-06-12"),
        ]
        _write_csv(csv_path, rows)
        stats = import_from_csv(csv_path)

        assert stats["rows_imported"] == 3

    def test_mixed_valid_and_invalid_rows(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv

        csv_path = tmp_path / "prices.csv"
        rows = [
            _valid_row(price_usd="3200"),         # valid
            _valid_row(destination="LHR"),         # filtered
            _valid_row(cabin="ECONOMY"),           # filtered
        ]
        _write_csv(csv_path, rows)
        stats = import_from_csv(csv_path)

        assert stats["rows_imported"] == 1
        assert stats["rows_filtered"] == 2

    def test_31_hour_outbound_passes_when_skip_check_is_true(self, tmp_store, tmp_path):
        """skip_flight_time_check=True (default) — 31h outbound should NOT be filtered."""
        from radar.seed import import_from_csv

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [_valid_row(outbound_duration_hours="31")])
        stats = import_from_csv(csv_path, skip_flight_time_check=True)

        assert stats["rows_imported"] == 1

    def test_31_hour_outbound_filtered_when_skip_check_is_false(self, tmp_store, tmp_path):
        """skip_flight_time_check=False — 31h outbound must be filtered."""
        from radar.seed import import_from_csv

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [_valid_row(outbound_duration_hours="31")])
        stats = import_from_csv(csv_path, skip_flight_time_check=False)

        assert stats["rows_filtered"] == 1


class TestJSONImport:
    def test_valid_json_array_imports(self, tmp_store, tmp_path):
        from radar.seed import import_from_json
        from radar.schema_store import get_series

        json_path = tmp_path / "prices.json"
        json_path.write_text(json.dumps([{
            "destination": "LAX", "carrier": "QR", "cabin": "BUSINESS",
            "price_usd": 4200, "outbound_date": "2027-05-01", "return_date": "2027-05-12",
        }]))
        stats = import_from_json(json_path)

        assert stats["rows_imported"] == 1
        series = get_series("CAI", "LAX", "QR", "BUSINESS")
        assert len(series) == 1
        assert series[0]["data_quality"] == "estimated"

    def test_non_array_json_returns_error(self, tmp_store, tmp_path):
        from radar.seed import import_from_json

        json_path = tmp_path / "prices.json"
        json_path.write_text(json.dumps({"not": "an array"}))
        stats = import_from_json(json_path)

        assert "error" in stats
        assert stats["rows_imported"] == 0

    def test_invalid_json_syntax_returns_error(self, tmp_store, tmp_path):
        from radar.seed import import_from_json

        json_path = tmp_path / "prices.json"
        json_path.write_text("{broken json}")
        stats = import_from_json(json_path)

        assert "error" in stats


class TestObservationMetadata:
    def test_observation_type_is_historical_seed(self, tmp_store, tmp_path):
        from radar.seed import import_from_csv
        from radar.schema_store import get_series

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [_valid_row()])
        import_from_csv(csv_path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["source"] == "historical_seed"
        assert series[0]["data_quality"] == "estimated"

    def test_seeding_7_obs_reaches_medium_confidence(self, tmp_store, tmp_path):
        """
        Seeding 7 valid historical observations should push confidence to MEDIUM,
        unblocking the BUY_SIGNAL gate without waiting 7 days of live monitoring.
        """
        from radar.seed import import_from_csv
        from radar.schema_store import get_all_series_keys
        from radar.stages.forecast import _confidence_level

        csv_path = tmp_path / "prices.csv"
        date_pairs = [
            ("2027-03-15", "2027-03-26"),
            ("2027-04-01", "2027-04-12"),
            ("2027-04-15", "2027-04-26"),
            ("2027-05-01", "2027-05-12"),
            ("2027-05-15", "2027-05-26"),
            ("2027-06-01", "2027-06-12"),
            ("2027-06-15", "2027-06-26"),
        ]
        rows = [
            _valid_row(price_usd=str(3000 + i * 50), outbound_date=od, return_date=rd)
            for i, (od, rd) in enumerate(date_pairs)
        ]
        _write_csv(csv_path, rows)
        stats = import_from_csv(csv_path)

        assert stats["rows_imported"] == 7

        all_keys = get_all_series_keys()
        series_key = next(
            (k for k in all_keys if k["destination"] == "JFK" and k["carrier"] == "EK"), None
        )
        assert series_key is not None
        assert _confidence_level(series_key["observation_count"]) == "MEDIUM"

    def test_default_routing_filled_from_destination(self, tmp_store, tmp_path):
        """When routing columns are absent, outbound_routing defaults to CAI-{DEST}."""
        from radar.seed import import_from_csv
        from radar.schema_store import get_series

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [_valid_row()])
        import_from_csv(csv_path)

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert "JFK" in series[0]["outbound_routing"]

    def test_append_invariant_preserved_across_seed_and_daily(self, tmp_store, tmp_path):
        """Seeded observations must not be overwritten when daily observations are appended later."""
        from radar.seed import import_from_csv
        from radar.schema_store import append_observation, get_series

        csv_path = tmp_path / "prices.csv"
        _write_csv(csv_path, [_valid_row(price_usd="3000")])
        import_from_csv(csv_path)

        seed_id = get_series("CAI", "JFK", "EK", "BUSINESS")[0]["observation_id"]

        # Simulate a daily monitor observation appended after seed
        append_observation(
            origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
            price_usd=2900.0,
            outbound_date="2027-04-15", return_date="2027-04-26",
            outbound_duration_hours=14.5, return_duration_hours=15.0,
            outbound_stops=1, return_stops=1,
            outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
            source="serpapi", observation_type="daily",
        )

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        assert series[0]["observation_id"] == seed_id
        assert series[0]["price_usd"] == 3000.0
        assert series[0]["observation_type"] == "historical_seed"
        assert series[1]["observation_type"] == "daily"
