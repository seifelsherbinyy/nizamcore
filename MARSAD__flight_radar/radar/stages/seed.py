"""
STAGE 0 — SEED: Historical Price Data Import

Imports historical or external price observations as observation_type='historical_seed'.
Used to accelerate model confidence past the LOW threshold before 7 daily observations
accumulate naturally (cold-start shortcut).

Why this matters:
  The forecast model requires 7+ observations before producing MEDIUM confidence signals
  and BUY_SIGNAL can fire. Without seeding, the pipeline spends 7 days in LOW confidence
  mode regardless of how good the prices are. Historical seed data from manual research
  (Hopper, Google Flights price history, Kayak charts) can bootstrap the model.

Input formats:
  CSV — columns required (in any order):
    carrier, origin, destination, cabin,
    outbound_date (YYYY-MM-DD), return_date (YYYY-MM-DD),
    price_usd, outbound_duration_hours, return_duration_hours,
    outbound_stops, return_stops, outbound_routing, return_routing
  Optional CSV columns:
    source_name (default: "historical_seed"), data_quality (default: "estimated"),
    price_egp, price_eur

  JSON — list of dicts with same field names as CSV columns.

Constraints:
  - All routing constraints applied before import (same as DISCOVER/MONITOR).
  - Append-only invariant: existing observations are never modified.
  - observation_type is always set to "historical_seed".
  - data_quality defaults to "estimated" (not from live API call — may be less accurate).
  - Duplicate detection: an observation is skipped if a historical_seed entry already
    exists in the series for the same outbound_date and price_usd combination.

Usage:
  python -m radar.main seed --csv path/to/history.csv
  python -m radar.main seed --json path/to/history.json
  python -m radar.main seed --dry-run --csv path/to/history.csv

CSV template (save as history.csv):
  carrier,origin,destination,cabin,outbound_date,return_date,price_usd,
  outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,
  outbound_routing,return_routing,source_name,data_quality
  EK,CAI,JFK,BUSINESS,2027-04-01,2027-04-12,3100.0,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI,hopper,estimated

Historical price sources:
  - Hopper (hopper.com): Price history charts available in app — screenshot and transcribe
  - Google Flights: Price calendar view shows range of prices — manual transcription
  - Kayak price history: kayak.com — hover over price graph to extract values
  - ITA Matrix: Manual search of specific past dates (data as-of search date, not booking date)
  See MARSAD README "Historical Price Seed Research" section for detailed source notes.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation, get_series

logger = logging.getLogger(__name__)

_REQUIRED_COLUMNS = {
    "carrier", "origin", "destination", "cabin",
    "outbound_date", "return_date", "price_usd",
    "outbound_duration_hours", "return_duration_hours",
    "outbound_stops", "return_stops",
    "outbound_routing", "return_routing",
}


def _parse_row(row: dict) -> Optional[dict]:
    """
    Parse and type-cast a single input row.
    Returns None if any required field is missing or unparseable.
    """
    missing = _REQUIRED_COLUMNS - set(row.keys())
    if missing:
        logger.warning("Row missing required columns %s: %s", missing, row)
        return None

    try:
        outbound_date = date.fromisoformat(row["outbound_date"].strip())
        return_date = date.fromisoformat(row["return_date"].strip())
    except ValueError as exc:
        logger.warning("Date parse error: %s in row %s", exc, row)
        return None

    try:
        price_usd = float(row["price_usd"])
        outbound_duration_hours = float(row["outbound_duration_hours"])
        return_duration_hours = float(row["return_duration_hours"])
        outbound_stops = int(row["outbound_stops"])
        return_stops = int(row["return_stops"])
    except (ValueError, TypeError) as exc:
        logger.warning("Numeric parse error: %s in row %s", exc, row)
        return None

    if price_usd <= 0:
        logger.warning("Non-positive price %.2f — skipping row: %s", price_usd, row)
        return None

    return {
        "carrier": row["carrier"].strip().upper(),
        "origin": row["origin"].strip().upper(),
        "destination": row["destination"].strip().upper(),
        "cabin": row["cabin"].strip().upper(),
        "outbound_date": outbound_date,
        "return_date": return_date,
        "price_usd": price_usd,
        "outbound_duration_hours": outbound_duration_hours,
        "return_duration_hours": return_duration_hours,
        "outbound_stops": outbound_stops,
        "return_stops": return_stops,
        "outbound_routing": row.get("outbound_routing", "").strip(),
        "return_routing": row.get("return_routing", "").strip(),
        "source_name": row.get("source_name", "historical_seed").strip() or "historical_seed",
        "data_quality": row.get("data_quality", "estimated").strip() or "estimated",
        "price_egp": float(row["price_egp"]) if row.get("price_egp") else None,
        "price_eur": float(row["price_eur"]) if row.get("price_eur") else None,
    }


def _is_duplicate(origin: str, destination: str, carrier: str, cabin: str,
                  outbound_date: date, price_usd: float) -> bool:
    """
    Return True if a historical_seed entry already exists in the series for
    the same outbound_date and price_usd combination.
    Prevents double-importing the same data on successive seed runs.
    """
    series = get_series(origin, destination, carrier, cabin)
    for obs in series:
        if (obs.get("observation_type") == "historical_seed"
                and obs.get("outbound_date") == outbound_date.isoformat()
                and abs(obs.get("price_usd", 0) - price_usd) < 0.01):
            return True
    return False


def _import_row(row_data: dict, dry_run: bool) -> str:
    """
    Validate constraints and append one seed observation.
    Returns: "imported", "filtered", "duplicate", "error".
    """
    itin = FlightItinerary(
        origin=row_data["origin"],
        destination=row_data["destination"],
        cabin=row_data["cabin"],
        outbound_date=row_data["outbound_date"],
        return_date=row_data["return_date"],
        outbound_duration_hours=row_data["outbound_duration_hours"],
        return_duration_hours=row_data["return_duration_hours"],
        carrier=row_data["carrier"],
        price_usd=row_data["price_usd"],
    )

    constraint_result = apply_constraints(itin)
    if not constraint_result:
        logger.debug(
            "Seed row filtered: %s→%s %s %s — %s",
            row_data["origin"], row_data["destination"],
            row_data["carrier"], row_data["cabin"],
            constraint_result.failures,
        )
        return "filtered"

    if _is_duplicate(
        row_data["origin"], row_data["destination"],
        row_data["carrier"], row_data["cabin"],
        row_data["outbound_date"], row_data["price_usd"],
    ):
        logger.debug(
            "Seed duplicate skipped: %s→%s %s %s %s $%.0f",
            row_data["origin"], row_data["destination"],
            row_data["carrier"], row_data["cabin"],
            row_data["outbound_date"], row_data["price_usd"],
        )
        return "duplicate"

    if dry_run:
        logger.info(
            "DRY RUN — would import: %s→%s %s %s %s $%.0f",
            row_data["origin"], row_data["destination"],
            row_data["carrier"], row_data["cabin"],
            row_data["outbound_date"], row_data["price_usd"],
        )
        return "imported"

    try:
        append_observation(
            origin=row_data["origin"],
            destination=row_data["destination"],
            carrier=row_data["carrier"],
            cabin=row_data["cabin"],
            price_usd=row_data["price_usd"],
            outbound_date=row_data["outbound_date"].isoformat(),
            return_date=row_data["return_date"].isoformat(),
            outbound_duration_hours=row_data["outbound_duration_hours"],
            return_duration_hours=row_data["return_duration_hours"],
            outbound_stops=row_data["outbound_stops"],
            return_stops=row_data["return_stops"],
            outbound_routing=row_data["outbound_routing"],
            return_routing=row_data["return_routing"],
            source=row_data["source_name"],
            observation_type="historical_seed",
            price_egp=row_data.get("price_egp"),
            price_eur=row_data.get("price_eur"),
            data_quality=row_data["data_quality"],
        )
        logger.info(
            "Seed imported: %s→%s %s %s %s $%.0f",
            row_data["origin"], row_data["destination"],
            row_data["carrier"], row_data["cabin"],
            row_data["outbound_date"], row_data["price_usd"],
        )
        return "imported"
    except Exception as exc:
        logger.error("Seed import error: %s", exc)
        return "error"


def run_seed(
    csv_path: Optional[str] = None,
    json_path: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """
    Import historical seed observations from a CSV or JSON file.

    csv_path:  path to CSV file (required columns: see module docstring)
    json_path: path to JSON file (list of dicts with same field names)
    dry_run:   log what would be imported without writing to store

    Returns summary dict with import statistics.
    """
    if not csv_path and not json_path:
        raise ValueError("Either csv_path or json_path must be provided")

    stats = {
        "stage": "SEED",
        "dry_run": dry_run,
        "source_file": csv_path or json_path,
        "rows_read": 0,
        "rows_imported": 0,
        "rows_filtered": 0,
        "rows_duplicate": 0,
        "rows_parse_error": 0,
        "rows_import_error": 0,
    }

    rows: list[dict] = []

    if csv_path:
        input_path = Path(csv_path)
        if not input_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        with open(input_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

    elif json_path:
        input_path = Path(json_path)
        if not input_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON file must contain a top-level array of observation dicts")
        rows = data

    stats["rows_read"] = len(rows)

    for raw_row in rows:
        parsed = _parse_row(raw_row if isinstance(raw_row, dict) else dict(raw_row))
        if parsed is None:
            stats["rows_parse_error"] += 1
            continue

        result = _import_row(parsed, dry_run=dry_run)
        if result == "imported":
            stats["rows_imported"] += 1
        elif result == "filtered":
            stats["rows_filtered"] += 1
        elif result == "duplicate":
            stats["rows_duplicate"] += 1
        elif result == "error":
            stats["rows_import_error"] += 1

    logger.info(
        "SEED %s: %d read, %d imported, %d filtered, %d duplicate, %d parse_error, %d import_error",
        "(DRY RUN)" if dry_run else "complete",
        stats["rows_read"],
        stats["rows_imported"],
        stats["rows_filtered"],
        stats["rows_duplicate"],
        stats["rows_parse_error"],
        stats["rows_import_error"],
    )

    return stats


def generate_csv_template() -> str:
    """Return a CSV template string that can be saved and filled in manually."""
    header = ",".join([
        "carrier", "origin", "destination", "cabin",
        "outbound_date", "return_date", "price_usd",
        "outbound_duration_hours", "return_duration_hours",
        "outbound_stops", "return_stops",
        "outbound_routing", "return_routing",
        "source_name", "data_quality",
        "price_egp", "price_eur",
    ])
    example_rows = [
        "EK,CAI,JFK,BUSINESS,2027-04-01,2027-04-12,3100.0,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI,hopper,estimated,,",
        "QR,CAI,LAX,BUSINESS,2027-05-01,2027-05-12,3400.0,18.5,19.0,1,1,CAI-DOH-LAX,LAX-DOH-CAI,google_flights_calendar,estimated,,",
        "EK,CAI,MIA,PREMIUM_ECONOMY,2027-06-01,2027-06-12,2100.0,14.5,15.0,1,1,CAI-DXB-MIA,MIA-DXB-CAI,kayak_history,estimated,,",
    ]
    return header + "\n" + "\n".join(example_rows) + "\n"
