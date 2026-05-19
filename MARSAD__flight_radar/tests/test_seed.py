"""
Tests for Stage 0 — Historical Price Seed (radar/seed.py).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses temporary files and a mocked schema store to avoid touching real data.
"""

import csv
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(tmp_path: Path, rows: list[dict], filename: str = "seed.csv") -> Path:
    """Write a list of dicts to a CSV and return the path."""
    if not rows:
        return tmp_path / filename
    p = tmp_path / filename
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return p


_VALID_ROW = {
    "outbound_date": "2027-04-01",
    "return_date": "2027-04-12",
    "price_usd": "3000.00",
    "destination": "JFK",
    "carrier": "EK",
    "cabin": "BUSINESS",
    "outbound_duration_hours": "14.5",
    "return_duration_hours": "15.0",
    "outbound_stops": "1",
    "return_stops": "1",
    "outbound_routing": "CAI-DXB-JFK",
    "return_routing": "JFK-DXB-CAI",
    "data_quality": "confirmed",
    "price_egp": "",
    "price_eur": "",
}


# ---------------------------------------------------------------------------
# import_from_csv — file not found
# ---------------------------------------------------------------------------

class TestFileNotFound:
    def test_missing_file_returns_error(self, tmp_path):
        from radar.seed import import_from_csv
        stats = import_from_csv(tmp_path / "nonexistent.csv")
        assert "error" in stats
        assert stats["rows_read"] == 0


# ---------------------------------------------------------------------------
# import_from_csv — valid row
# ---------------------------------------------------------------------------

class TestValidRow:
    def test_valid_row_imported(self, tmp_path):
        from radar.seed import import_from_csv
        p = _write_csv(tmp_path, [_VALID_ROW])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            stats = import_from_csv(p)

        assert stats["rows_read"] == 1
        assert stats["rows_imported"] == 1
        assert stats["rows_filtered"] == 0
        assert stats["rows_error"] == 0
        mock_append.assert_called_once()

    def test_append_called_with_observation_type_historical_seed(self, tmp_path):
        from radar.seed import import_from_csv
        p = _write_csv(tmp_path, [_VALID_ROW])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            import_from_csv(p)

        call_kwargs = mock_append.call_args.kwargs
        assert call_kwargs["observation_type"] == "historical_seed"

    def test_append_called_with_source_manual(self, tmp_path):
        from radar.seed import import_from_csv
        p = _write_csv(tmp_path, [_VALID_ROW])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            import_from_csv(p)

        call_kwargs = mock_append.call_args.kwargs
        assert call_kwargs["source"] == "manual"


# ---------------------------------------------------------------------------
# import_from_csv — dry run
# ---------------------------------------------------------------------------

class TestDryRun:
    def test_dry_run_does_not_call_append(self, tmp_path):
        from radar.seed import import_from_csv
        p = _write_csv(tmp_path, [_VALID_ROW])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            stats = import_from_csv(p, dry_run=True)

        assert stats["rows_imported"] == 1
        mock_append.assert_not_called()


# ---------------------------------------------------------------------------
# import_from_csv — filtering
# ---------------------------------------------------------------------------

class TestFiltering:
    def test_invalid_price_filtered(self, tmp_path):
        from radar.seed import import_from_csv
        row = {**_VALID_ROW, "price_usd": "not_a_number"}
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation"):
            stats = import_from_csv(p)

        assert stats["rows_filtered"] == 1
        assert stats["rows_imported"] == 0

    def test_zero_price_filtered(self, tmp_path):
        from radar.seed import import_from_csv
        row = {**_VALID_ROW, "price_usd": "0"}
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation"):
            stats = import_from_csv(p)

        assert stats["rows_filtered"] == 1

    def test_invalid_date_filtered(self, tmp_path):
        from radar.seed import import_from_csv
        row = {**_VALID_ROW, "outbound_date": "not-a-date"}
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation"):
            stats = import_from_csv(p)

        assert stats["rows_filtered"] == 1

    def test_constraint_violation_filtered(self, tmp_path):
        from radar.seed import import_from_csv
        # Trip duration 1 night — violates 9–14 night constraint
        row = {**_VALID_ROW, "return_date": "2027-04-02"}
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation"):
            stats = import_from_csv(p)

        assert stats["rows_filtered"] == 1

    def test_invalid_destination_filtered(self, tmp_path):
        from radar.seed import import_from_csv
        row = {**_VALID_ROW, "destination": "ZZZ"}
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation"):
            stats = import_from_csv(p)

        assert stats["rows_filtered"] == 1

    def test_filter_reason_recorded(self, tmp_path):
        from radar.seed import import_from_csv
        row = {**_VALID_ROW, "price_usd": "-100"}
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation"):
            stats = import_from_csv(p)

        assert len(stats["filter_reasons"]) == 1
        assert "row 1" in stats["filter_reasons"][0]


# ---------------------------------------------------------------------------
# import_from_csv — duplicate detection
# ---------------------------------------------------------------------------

class TestDuplicateDetection:
    def test_duplicate_seed_skipped(self, tmp_path):
        from radar.seed import import_from_csv
        p = _write_csv(tmp_path, [_VALID_ROW])

        existing_obs = [{
            "outbound_date": "2027-04-01",
            "observation_type": "historical_seed",
        }]

        with patch("radar.seed.get_series", return_value=existing_obs), \
             patch("radar.seed.append_observation") as mock_append:
            stats = import_from_csv(p)

        assert stats["rows_duplicate"] == 1
        assert stats["rows_imported"] == 0
        mock_append.assert_not_called()

    def test_non_seed_obs_does_not_block_import(self, tmp_path):
        from radar.seed import import_from_csv
        p = _write_csv(tmp_path, [_VALID_ROW])

        # Daily observation on same date — should NOT count as duplicate seed
        existing_obs = [{
            "outbound_date": "2027-04-01",
            "observation_type": "daily",
        }]

        with patch("radar.seed.get_series", return_value=existing_obs), \
             patch("radar.seed.append_observation") as mock_append:
            stats = import_from_csv(p)

        assert stats["rows_imported"] == 1
        mock_append.assert_called_once()

    def test_different_date_is_not_duplicate(self, tmp_path):
        from radar.seed import import_from_csv
        p = _write_csv(tmp_path, [_VALID_ROW])

        existing_obs = [{
            "outbound_date": "2027-05-01",
            "observation_type": "historical_seed",
        }]

        with patch("radar.seed.get_series", return_value=existing_obs), \
             patch("radar.seed.append_observation") as mock_append:
            stats = import_from_csv(p)

        assert stats["rows_imported"] == 1
        mock_append.assert_called_once()


# ---------------------------------------------------------------------------
# import_from_csv — defaults applied
# ---------------------------------------------------------------------------

class TestDefaults:
    def test_missing_carrier_defaults_to_unknown(self, tmp_path):
        from radar.seed import import_from_csv
        row = {k: v for k, v in _VALID_ROW.items() if k != "carrier"}
        row["carrier"] = ""
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            import_from_csv(p)

        assert mock_append.call_args.kwargs["carrier"] == "UNKNOWN"

    def test_missing_data_quality_defaults_to_estimated(self, tmp_path):
        from radar.seed import import_from_csv
        row = {**_VALID_ROW, "data_quality": ""}
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            import_from_csv(p)

        assert mock_append.call_args.kwargs["data_quality"] == "estimated"

    def test_invalid_data_quality_coerced_to_estimated(self, tmp_path):
        from radar.seed import import_from_csv
        row = {**_VALID_ROW, "data_quality": "bogus"}
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            import_from_csv(p)

        assert mock_append.call_args.kwargs["data_quality"] == "estimated"

    def test_missing_routing_generates_default(self, tmp_path):
        from radar.seed import import_from_csv
        row = {**_VALID_ROW, "outbound_routing": "", "return_routing": ""}
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            import_from_csv(p)

        kwargs = mock_append.call_args.kwargs
        assert kwargs["outbound_routing"] == "CAI-JFK"
        assert kwargs["return_routing"] == "JFK-CAI"

    def test_price_egp_parsed_when_present(self, tmp_path):
        from radar.seed import import_from_csv
        row = {**_VALID_ROW, "price_egp": "150000.00"}
        p = _write_csv(tmp_path, [row])

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            import_from_csv(p)

        assert mock_append.call_args.kwargs["price_egp"] == 150000.0


# ---------------------------------------------------------------------------
# generate_seed_template
# ---------------------------------------------------------------------------

class TestGenerateSeedTemplate:
    def test_template_creates_file(self, tmp_path):
        from radar.seed import generate_seed_template
        out = tmp_path / "template.csv"
        generate_seed_template(out)
        assert out.exists()

    def test_template_has_header_row(self, tmp_path):
        from radar.seed import generate_seed_template, _TEMPLATE_HEADER
        out = tmp_path / "template.csv"
        generate_seed_template(out)
        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert header == _TEMPLATE_HEADER

    def test_template_has_example_row(self, tmp_path):
        from radar.seed import generate_seed_template
        out = tmp_path / "template.csv"
        generate_seed_template(out)
        with open(out, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            example = next(reader)
        assert example[0] == "2027-04-01"  # outbound_date
        assert example[3] == "JFK"         # destination

    def test_template_creates_parent_dirs(self, tmp_path):
        from radar.seed import generate_seed_template
        out = tmp_path / "subdir" / "deep" / "template.csv"
        generate_seed_template(out)
        assert out.exists()


# ---------------------------------------------------------------------------
# seed_status
# ---------------------------------------------------------------------------

class TestSeedStatus:
    def test_empty_store_returns_empty_dict(self):
        from radar.seed import seed_status
        # seed_status() does a local import from radar.schema_store — patch there
        with patch("radar.schema_store.get_all_series_keys", return_value=[]), \
             patch("radar.schema_store.get_series", return_value=[]):
            result = seed_status()
        assert result == {}

    def test_series_with_seed_obs_included(self):
        from radar.seed import seed_status
        keys = [{"origin": "CAI", "destination": "JFK", "carrier": "EK", "cabin": "BUSINESS", "observation_count": 5}]
        obs = [
            {"observation_type": "historical_seed"},
            {"observation_type": "historical_seed"},
            {"observation_type": "daily"},
        ]
        with patch("radar.schema_store.get_all_series_keys", return_value=keys), \
             patch("radar.schema_store.get_series", return_value=obs):
            result = seed_status()
        assert "CAI-JFK/EK/BUSINESS" in result
        assert result["CAI-JFK/EK/BUSINESS"]["seed_observations"] == 2
        assert result["CAI-JFK/EK/BUSINESS"]["total_observations"] == 5

    def test_series_without_seed_obs_excluded(self):
        from radar.seed import seed_status
        keys = [{"origin": "CAI", "destination": "JFK", "carrier": "EK", "cabin": "BUSINESS", "observation_count": 3}]
        obs = [
            {"observation_type": "daily"},
            {"observation_type": "baseline"},
        ]
        with patch("radar.schema_store.get_all_series_keys", return_value=keys), \
             patch("radar.schema_store.get_series", return_value=obs):
            result = seed_status()
        assert result == {}


# ---------------------------------------------------------------------------
# multi-row import
# ---------------------------------------------------------------------------

class TestMultiRow:
    def test_multiple_rows_all_imported(self, tmp_path):
        from radar.seed import import_from_csv
        rows = [
            {**_VALID_ROW, "outbound_date": "2027-04-01", "return_date": "2027-04-12", "destination": "JFK"},
            {**_VALID_ROW, "outbound_date": "2027-05-01", "return_date": "2027-05-12", "destination": "LAX"},
        ]
        p = _write_csv(tmp_path, rows)

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            stats = import_from_csv(p)

        assert stats["rows_read"] == 2
        assert stats["rows_imported"] == 2
        assert mock_append.call_count == 2

    def test_mixed_valid_invalid_rows(self, tmp_path):
        from radar.seed import import_from_csv
        rows = [
            _VALID_ROW,
            {**_VALID_ROW, "price_usd": "bad"},
        ]
        p = _write_csv(tmp_path, rows)

        with patch("radar.seed.get_series", return_value=[]), \
             patch("radar.seed.append_observation") as mock_append:
            stats = import_from_csv(p)

        assert stats["rows_imported"] == 1
        assert stats["rows_filtered"] == 1
        assert mock_append.call_count == 1
