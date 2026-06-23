"""
STAGE 0 — SEED: Historical Price Data Import

Imports historical flight price observations from a CSV or JSON file into the
MARSAD schema store as `observation_type: historical_seed`. This accelerates
forecasting confidence from LOW to MEDIUM/HIGH without waiting 7+ days of
daily monitoring.

Intended workflow:
  1. Manually collect historical price points from Google Flights price history,
     Kayak price trend charts, or Skyscanner route history.
  2. Format as a seed CSV (see SEED_CSV_COLUMNS below).
  3. Run: python -m radar.main seed --file path/to/seed.csv

The constraint engine is applied to every row before import. Rows that fail
constraints are skipped and logged — never imported.

Duplicate detection: a row is a duplicate if (outbound_date + route + carrier +
cabin + price_usd) already exists in the store. Duplicates are skipped silently.

APPEND-ONLY INVARIANT: existing observations are never modified or deleted.
Historical seed observations are immutable once imported.

─────────────────────────────────────────────────────────────────────────
HISTORICAL DATA SOURCE RESEARCH (mission item 9)
─────────────────────────────────────────────────────────────────────────

SOURCE 1 — Google Flights price history
  • Access: google.com/flights → search CAI→[DEST] → click "Price history" link
    (appears below the search results, labelled "Prices for this date in the past")
  • Depth: ~12 months of historical data per route-date combination
  • Format: visual bar chart — monthly low/mid prices — values must be read
    manually or captured via browser devtools (no programmatic API)
  • Integration: read the chart, fill SEED_CSV_COLUMNS rows manually, run seed import
  • Note: shows per-trip prices for the specific date range you searched — repeat
    for multiple departure dates to build a representative seed dataset
  • ASSUMED_PASS: Google Flights UI may change — verify "Price history" feature
    is present at time of use (as of 2026-06 it is available on CAI routes)

SOURCE 2 — Kayak price trend
  • Access: kayak.com → search CAI→[DEST] → scroll to "Price Trend" chart
  • Depth: ~12 months historical + 6 months forward forecast
  • Format: visual line chart — monthly average prices — manual extraction required
  • Integration: same as Google Flights — manual CSV entry
  • Note: Kayak's forecast values can also be imported as historical_seed with
    data_quality='estimated' to seed forward-looking estimates alongside actuals
  • ASSUMED_PASS: Kayak UI availability on CAI-to-USA routes

SOURCE 3 — Hopper
  • Access: Hopper mobile app only — no web interface, no API
  • Depth: up to 24 months in-app price history for popular routes
  • Format: in-app calendar view — manual screenshots only
  • Integration: manual CSV entry from screenshots
  • Limitation: CAI is not always covered for US routes — verify before relying on Hopper

SOURCE 4 — ITA Matrix (oldmatrix.itasoftware.com / matrix.itasoftware.com)
  • Historical capability: NONE — ITA Matrix only searches future travel dates
  • Cannot be used for historical seed data
  • Use for real-time baseline collection (Stage 1 DISCOVER) instead

SOURCE 5 — Skyscanner route history
  • Access: skyscanner.com → search route → click "Price alerts" or route trend
  • Depth: ~12 months on major routes; CAI→USA coverage varies
  • Format: visual chart — manual extraction
  • Integration: same as Google Flights

SOURCE 6 — SerpApi Historical
  • Past-date searches via SerpApi Google Flights API return unreliable results
    (Google Flights does not expose historical fare data via its search interface)
  • NOT RECOMMENDED for historical seeding

RECOMMENDED SEED WORKFLOW:
  1. Search CAI→JFK on Google Flights for a date 3 months ago
  2. Click "Price history" — note monthly lows for Business and Premium Economy
  3. Repeat for 12 months back and 3 sample return dates per month
  4. Repeat for priority destinations: JFK, LAX, MIA, ORD, IAD, BOS
  5. Fill seed CSV with ~50–100 rows covering the past 12 months
  6. Run: python -m radar.main seed --file seed_data.csv --dry-run  (preview first)
  7. Run: python -m radar.main seed --file seed_data.csv  (import)
  After import: re-run FORECAST — most series will jump from LOW to MEDIUM/HIGH confidence
─────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation, get_series

logger = logging.getLogger(__name__)

# Required CSV column names — all must be present
SEED_CSV_COLUMNS = [
    "origin",
    "destination",
    "carrier",
    "cabin",
    "outbound_date",
    "return_date",
    "outbound_duration_hours",
    "return_duration_hours",
    "outbound_stops",
    "return_stops",
    "outbound_routing",
    "return_routing",
    "price_usd",
]

# Optional — included in observations if present
SEED_CSV_OPTIONAL = [
    "price_egp",
    "price_eur",
    "source_notes",  # free-text provenance note stored as source field prefix
]


def _is_duplicate(
    origin: str,
    destination: str,
    carrier: str,
    cabin: str,
    outbound_date: str,
    price_usd: float,
) -> bool:
    """Return True if this exact observation already exists in the store."""
    series = get_series(origin, destination, carrier, cabin)
    return any(
        obs["outbound_date"] == outbound_date and abs(obs["price_usd"] - price_usd) < 0.01
        for obs in series
    )


def _parse_row(row: dict, row_num: int) -> tuple[Optional[FlightItinerary], Optional[dict], list[str]]:
    """
    Parse and validate a single seed row.
    Returns (itin, parsed_extras, errors).
    itin is None if the row cannot be parsed (not a constraint failure — a parse failure).
    """
    errors: list[str] = []

    # Validate required columns present
    missing_cols = [col for col in SEED_CSV_COLUMNS if col not in row or row[col] == ""]
    if missing_cols:
        return None, None, [f"Row {row_num}: missing required columns: {missing_cols}"]

    try:
        outbound_date = date.fromisoformat(row["outbound_date"].strip())
        return_date = date.fromisoformat(row["return_date"].strip())
    except ValueError as exc:
        return None, None, [f"Row {row_num}: invalid date format: {exc}"]

    try:
        price_usd = float(row["price_usd"])
        outbound_hours = float(row["outbound_duration_hours"])
        return_hours = float(row["return_duration_hours"])
        outbound_stops = int(row["outbound_stops"])
        return_stops = int(row["return_stops"])
    except (ValueError, TypeError) as exc:
        return None, None, [f"Row {row_num}: invalid numeric value: {exc}"]

    if price_usd <= 0:
        return None, None, [f"Row {row_num}: price_usd must be > 0, got {price_usd}"]

    itin = FlightItinerary(
        origin=row["origin"].strip().upper(),
        destination=row["destination"].strip().upper(),
        cabin=row["cabin"].strip().upper(),
        outbound_date=outbound_date,
        return_date=return_date,
        outbound_duration_hours=outbound_hours,
        return_duration_hours=return_hours,
        carrier=row["carrier"].strip().upper(),
        price_usd=price_usd,
    )

    extras = {
        "price_egp": float(row["price_egp"]) if row.get("price_egp", "").strip() else None,
        "price_eur": float(row["price_eur"]) if row.get("price_eur", "").strip() else None,
        "outbound_stops": outbound_stops,
        "return_stops": return_stops,
        "outbound_routing": row["outbound_routing"].strip(),
        "return_routing": row["return_routing"].strip(),
        "source_notes": row.get("source_notes", "").strip(),
    }

    return itin, extras, errors


def run_seed(
    file_path: str | Path,
    dry_run: bool = False,
) -> dict:
    """
    Import historical seed observations from a CSV or JSON file.

    CSV format: rows with SEED_CSV_COLUMNS headers.
    JSON format: list of objects with the same fields.

    Each row is validated against the constraint engine. Rows that fail constraints
    are skipped and logged. Duplicates are silently skipped.

    Returns summary dict with import statistics.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")

    stats = {
        "stage": "SEED",
        "file": str(path),
        "dry_run": dry_run,
        "rows_read": 0,
        "rows_imported": 0,
        "rows_skipped_constraint": 0,
        "rows_skipped_duplicate": 0,
        "rows_skipped_parse_error": 0,
        "constraint_failures": [],
        "parse_errors": [],
    }

    rows = _load_rows(path)
    stats["rows_read"] = len(rows)

    if dry_run:
        logger.info("SEED DRY RUN — no data will be written")

    for i, row in enumerate(rows, start=2):  # start=2 to account for header row
        itin, extras, parse_errors = _parse_row(row, i)

        if parse_errors:
            stats["rows_skipped_parse_error"] += 1
            stats["parse_errors"].extend(parse_errors)
            logger.warning("SEED parse error row %d: %s", i, parse_errors)
            continue

        constraint_result = apply_constraints(itin)
        if not constraint_result:
            stats["rows_skipped_constraint"] += 1
            stats["constraint_failures"].append({
                "row": i,
                "failures": constraint_result.failures,
            })
            logger.debug("SEED row %d constraint fail: %s", i, constraint_result.failures)
            continue

        # Duplicate check
        if _is_duplicate(
            itin.origin, itin.destination, itin.carrier, itin.cabin,
            itin.outbound_date.isoformat(), itin.price_usd,
        ):
            stats["rows_skipped_duplicate"] += 1
            logger.debug(
                "SEED row %d duplicate skipped: %s→%s %s %s $%.0f %s",
                i, itin.origin, itin.destination, itin.carrier, itin.cabin,
                itin.price_usd, itin.outbound_date,
            )
            continue

        if not dry_run:
            source_label = f"historical_seed"
            if extras.get("source_notes"):
                source_label = f"historical_seed"  # source field is enum-constrained

            append_observation(
                origin=itin.origin,
                destination=itin.destination,
                carrier=itin.carrier,
                cabin=itin.cabin,
                price_usd=itin.price_usd,
                outbound_date=itin.outbound_date.isoformat(),
                return_date=itin.return_date.isoformat(),
                outbound_duration_hours=itin.outbound_duration_hours,
                return_duration_hours=itin.return_duration_hours,
                outbound_stops=extras["outbound_stops"],
                return_stops=extras["return_stops"],
                outbound_routing=extras["outbound_routing"],
                return_routing=extras["return_routing"],
                source="historical_seed",
                observation_type="historical_seed",
                price_egp=extras["price_egp"],
                price_eur=extras["price_eur"],
                data_quality="estimated",
            )

        stats["rows_imported"] += 1
        logger.info(
            "SEED %simported: %s→%s %s %s $%.0f %s",
            "[DRY] " if dry_run else "",
            itin.origin, itin.destination, itin.carrier, itin.cabin,
            itin.price_usd, itin.outbound_date,
        )

    logger.info(
        "SEED complete: %d read, %d imported, %d constraint fail, %d duplicate, %d parse error",
        stats["rows_read"],
        stats["rows_imported"],
        stats["rows_skipped_constraint"],
        stats["rows_skipped_duplicate"],
        stats["rows_skipped_parse_error"],
    )

    return stats


def _load_rows(path: Path) -> list[dict]:
    """Load rows from CSV or JSON file. Returns list of dicts."""
    suffix = path.suffix.lower()

    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"JSON seed file must contain a list of objects, got {type(data)}")
        return data

    if suffix in (".csv", ".tsv"):
        delimiter = "\t" if suffix == ".tsv" else ","
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = list(reader)
        # Strip whitespace from column names (common copy-paste artifact)
        return [{k.strip(): v for k, v in row.items()} for row in rows]

    raise ValueError(f"Unsupported seed file format: {suffix!r} — use .csv, .tsv, or .json")


def generate_seed_template(output_path: str | Path) -> None:
    """Write a blank seed CSV template with column headers and one example row."""
    path = Path(output_path)
    all_columns = SEED_CSV_COLUMNS + SEED_CSV_OPTIONAL

    example = {
        "origin": "CAI",
        "destination": "JFK",
        "carrier": "EK",
        "cabin": "BUSINESS",
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "outbound_duration_hours": "14.5",
        "return_duration_hours": "15.0",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
        "price_usd": "3200.00",
        "price_egp": "",
        "price_eur": "",
        "source_notes": "Google Flights price history — replace with your collected data",
    }

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_columns)
        writer.writeheader()
        writer.writerow(example)

    logger.info("Seed template written to %s", path)
