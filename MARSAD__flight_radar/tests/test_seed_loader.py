"""
Tests for the HISTORICAL SEED LOADER (Stage 0).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses temporary files and in-memory data — no external dependencies.
"""

import csv
import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect schema_store paths to a temporary directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
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
        "outbound_date": "2027-04-15",
        "return_date": "2027-04-26",
        "outbound_duration_hours": "14.5",
        "return_duration_hours": "15.0",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
        "source": "historical_seed",
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("origin,destination,carrier,cabin,price_usd\n")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, ensure_ascii=False))


class TestSeedLoaderCSV:
    def test_valid_csv_row_imported(self, tmp_store):
        from radar.stages.seed_loader import run_seed
        from radar.schema_store import get_series

        f = tmp_store / "seed.csv"
        _write_csv(f, [_valid_row()])

        stats = run_seed(str(f))
        assert stats["observations_imported"] == 1
        assert stats["rows_skipped_constraint"] == 0
        assert stats["rows_skipped_error"] == 0

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 1
        assert series[0]["observation_type"] == "historical_seed"
        assert series[0]["price_usd"] == 3200.0

    def test_constraint_failing_row_skipped(self, tmp_store):
        from radar.stages.seed_loader import run_seed

        row = _valid_row()
        row["outbound_duration_hours"] = "35.0"  # exceeds 30h limit

        f = tmp_store / "bad.csv"
        _write_csv(f, [row])

        stats = run_seed(str(f))
        assert stats["observations_imported"] == 0
        assert stats["rows_skipped_constraint"] == 1

    def test_economy_cabin_skipped_by_constraint(self, tmp_store):
        from radar.stages.seed_loader import run_seed

        row = _valid_row()
        row["cabin"] = "ECONOMY"  # not in CABINS list

        f = tmp_store / "economy.csv"
        _write_csv(f, [row])

        stats = run_seed(str(f))
        assert stats["observations_imported"] == 0
        assert stats["rows_skipped_constraint"] == 1

    def test_31_hour_outbound_skipped(self, tmp_store):
        """KEY: 31-hour outbound must be filtered — same as constraint unit test."""
        from radar.stages.seed_loader import run_seed

        row = _valid_row()
        row["outbound_duration_hours"] = "31.0"
        row["return_duration_hours"] = "20.0"

        f = tmp_store / "long.csv"
        _write_csv(f, [row])

        stats = run_seed(str(f))
        assert stats["observations_imported"] == 0
        assert stats["rows_skipped_constraint"] == 1

    def test_missing_price_skipped(self, tmp_store):
        from radar.stages.seed_loader import run_seed

        row = _valid_row()
        row["price_usd"] = "0"

        f = tmp_store / "zero.csv"
        _write_csv(f, [row])

        stats = run_seed(str(f))
        assert stats["rows_skipped_error"] == 1

    def test_dry_run_does_not_write(self, tmp_store):
        from radar.stages.seed_loader import run_seed
        from radar.schema_store import get_series

        f = tmp_store / "seed.csv"
        _write_csv(f, [_valid_row()])

        stats = run_seed(str(f), dry_run=True)
        assert stats["dry_run"] is True
        assert stats["observations_imported"] == 1  # counted but not written

        # Store should be empty — dry run never calls append_observation
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0

    def test_file_not_found_returns_error(self, tmp_store):
        from radar.stages.seed_loader import run_seed

        stats = run_seed("/nonexistent/path/seed.csv")
        assert stats["observations_imported"] == 0
        assert "error" in stats


class TestSeedLoaderJSON:
    def test_valid_json_rows_imported(self, tmp_store):
        from radar.stages.seed_loader import run_seed
        from radar.schema_store import get_series

        rows = [_valid_row(), {**_valid_row(), "outbound_date": "2027-05-01", "return_date": "2027-05-12"}]
        f = tmp_store / "seed.json"
        _write_json(f, rows)

        stats = run_seed(str(f))
        assert stats["observations_imported"] == 2

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        assert all(o["observation_type"] == "historical_seed" for o in series)

    def test_non_list_json_raises_error(self, tmp_store):
        from radar.stages.seed_loader import run_seed

        f = tmp_store / "bad.json"
        f.write_text('{"not": "a list"}')

        stats = run_seed(str(f))
        assert stats["observations_imported"] == 0
        assert "error" in stats

    def test_multiple_routes_all_imported(self, tmp_store):
        from radar.stages.seed_loader import run_seed

        rows = [
            _valid_row(),                              # CAI-JFK EK BUSINESS
            {**_valid_row(), "destination": "LAX"},    # CAI-LAX EK BUSINESS
            {**_valid_row(), "cabin": "PREMIUM_ECONOMY"},  # CAI-JFK EK PREMIUM_ECONOMY
        ]
        f = tmp_store / "multi.json"
        _write_json(f, rows)

        stats = run_seed(str(f))
        assert stats["observations_imported"] == 3


class TestSeedObservationFields:
    def test_observation_has_historical_seed_type(self, tmp_store):
        from radar.stages.seed_loader import run_seed
        from radar.schema_store import get_series

        f = tmp_store / "seed.csv"
        _write_csv(f, [_valid_row()])
        run_seed(str(f))

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert series[0]["observation_type"] == "historical_seed"

    def test_observation_has_estimated_data_quality(self, tmp_store):
        from radar.stages.seed_loader import run_seed
        from radar.schema_store import get_series

        f = tmp_store / "seed.csv"
        _write_csv(f, [_valid_row()])
        run_seed(str(f))

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert series[0]["data_quality"] == "estimated"

    def test_seed_does_not_overwrite_existing_observations(self, tmp_store):
        """INVARIANT: seed appends to existing series — never overwrites."""
        from radar.stages.seed_loader import run_seed
        from radar.schema_store import append_observation, get_series

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

        f = tmp_store / "seed.csv"
        _write_csv(f, [_valid_row()])
        run_seed(str(f))

        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 2
        assert series[0]["observation_type"] == "baseline"
        assert series[0]["price_usd"] == 3000.0
        assert series[1]["observation_type"] == "historical_seed"
