"""
HISTORICAL PRICE SEED — Import external price history into the MARSAD store.

Accelerates forecast model accuracy from day one without waiting for the daily
monitor to accumulate 7+ observations. Seed observations are stored with
observation_type='historical_seed' and source='historical_seed'.

Input format: JSON or CSV file with one observation per row/entry.

Expected JSON structure (list of objects):
  [
    {
      "origin": "CAI",
      "destination": "JFK",
      "carrier": "EK",
      "cabin": "BUSINESS",
      "price_usd": 3200.0,
      "outbound_date": "2027-04-01",
      "return_date": "2027-04-12",
      "outbound_duration_hours": 14.5,
      "return_duration_hours": 15.0,
      "outbound_stops": 1,
      "return_stops": 1,
      "outbound_routing": "CAI-DXB-JFK",
      "return_routing": "JFK-DXB-CAI",
      "data_quality": "estimated"       (optional — defaults to "estimated")
    },
    ...
  ]

Expected CSV columns (same field names, header row required):
  origin,destination,carrier,cabin,price_usd,outbound_date,return_date,
  outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,
  outbound_routing,return_routing[,data_quality]

Usage:
  python -m radar.main seed --file path/to/history.json
  python -m radar.main seed --file path/to/history.csv --dry-run

Historical price sources (ASSUMED_PASS_PENDING_ENVIRONMENT):
  A) Google Flights price history — 3-month rolling window visible in the UI
     Access: manual screenshot or via SerpAPI price_calendar endpoint
     Format: manual entry or SerpAPI response JSON

  B) Kayak price history charts — 6–12 month history visible per route
     Access: manual export (no programmatic API)
     Format: manual CSV

  C) Hopper historical data — 12-month+ history
     Access: Hopper does not expose a public API for historical data
     Format: manual CSV from app export if available

  D) ITA Matrix historical search — not available (current prices only)

Integration note: seed data from manual sources should set data_quality="estimated"
rather than "confirmed" since prices are scraped/entered manually rather than
from a live API response. The forecasting model weights all observations equally
regardless of data_quality — this field is metadata only.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = {
    "origin", "destination", "carrier", "cabin", "price_usd",
    "outbound_date", "return_date",
    "outbound_duration_hours", "return_duration_hours",
    "outbound_stops", "return_stops",
    "outbound_routing", "return_routing",
}


def _parse_record(rec: dict) -> Optional[dict]:
    """
    Parse and type-coerce a raw record dict.
    Returns normalised dict or None on parse failure.
    """
    missing = _REQUIRED_FIELDS - set(rec.keys())
    if missing:
        return None

    try:
        return {
            "origin": str(rec["origin"]).upper(),
            "destination": str(rec["destination"]).upper(),
            "carrier": str(rec["carrier"]).upper(),
            "cabin": str(rec["cabin"]).upper(),
            "price_usd": float(rec["price_usd"]),
            "outbound_date": str(rec["outbound_date"]),
            "return_date": str(rec["return_date"]),
            "outbound_duration_hours": float(rec["outbound_duration_hours"]),
            "return_duration_hours": float(rec["return_duration_hours"]),
            "outbound_stops": int(rec["outbound_stops"]),
            "return_stops": int(rec["return_stops"]),
            "outbound_routing": str(rec["outbound_routing"]),
            "return_routing": str(rec["return_routing"]),
            "data_quality": str(rec.get("data_quality", "estimated")),
        }
    except (ValueError, TypeError) as exc:
        logger.debug("Record parse error: %s — raw: %s", exc, rec)
        return None


def _load_file(path: Path) -> tuple[list[dict], list[str]]:
    """
    Load observations from a JSON or CSV file.
    Returns (records, errors).
    """
    errors: list[str] = []

    if not path.exists():
        return [], [f"File not found: {path}"]

    suffix = path.suffix.lower()

    if suffix == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                return [], ["JSON file must contain a top-level array of observation objects"]
            return data, []
        except json.JSONDecodeError as exc:
            return [], [f"JSON parse error: {exc}"]

    elif suffix == ".csv":
        records: list[dict] = []
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(dict(row))
            return records, []
        except OSError as exc:
            return [], [f"CSV read error: {exc}"]

    else:
        return [], [f"Unsupported file format: {suffix!r} — use .json or .csv"]


def run_seed(
    file_path: Path,
    dry_run: bool = False,
    skip_constraint_errors: bool = True,
) -> dict:
    """
    Import historical price observations from a file into the MARSAD store.

    file_path: path to .json or .csv seed file
    dry_run: validate and log without writing to store
    skip_constraint_errors: if True, constraint-failing records are logged and skipped
                            (default True — seed data from external sources may include
                            routes outside the current travel window)

    Returns summary dict.
    """
    stats = {
        "stage": "SEED",
        "source_file": str(file_path),
        "dry_run": dry_run,
        "records_read": 0,
        "records_valid": 0,
        "records_imported": 0,
        "records_constraint_skipped": 0,
        "records_parse_error": 0,
        "fetch_errors": [],
    }

    raw_records, load_errors = _load_file(file_path)
    if load_errors:
        stats["fetch_errors"].extend(load_errors)
        logger.error("SEED: failed to load %s — %s", file_path, load_errors)
        return stats

    stats["records_read"] = len(raw_records)
    logger.info("SEED: loaded %d records from %s", len(raw_records), file_path)

    for i, raw in enumerate(raw_records):
        parsed = _parse_record(raw)
        if parsed is None:
            stats["records_parse_error"] += 1
            logger.warning("SEED: record %d failed to parse — missing/invalid fields", i + 1)
            continue

        stats["records_valid"] += 1

        # Constraint check
        try:
            outbound_date = date.fromisoformat(parsed["outbound_date"])
            return_date = date.fromisoformat(parsed["return_date"])
        except ValueError as exc:
            stats["records_parse_error"] += 1
            logger.warning("SEED: record %d bad date format: %s", i + 1, exc)
            continue

        itin = FlightItinerary(
            origin=parsed["origin"],
            destination=parsed["destination"],
            cabin=parsed["cabin"],
            outbound_date=outbound_date,
            return_date=return_date,
            outbound_duration_hours=parsed["outbound_duration_hours"],
            return_duration_hours=parsed["return_duration_hours"],
            carrier=parsed["carrier"],
            price_usd=parsed["price_usd"],
        )
        constraint_result = apply_constraints(itin)

        if not constraint_result:
            stats["records_constraint_skipped"] += 1
            if not skip_constraint_errors:
                stats["fetch_errors"].append(
                    f"Record {i+1} failed constraints: {constraint_result.failures}"
                )
            logger.debug(
                "SEED: record %d constraint skip — %s", i + 1, constraint_result.failures
            )
            continue

        if dry_run:
            logger.info(
                "SEED DRY RUN: would import %s→%s %s %s $%.0f %s",
                parsed["origin"], parsed["destination"],
                parsed["carrier"], parsed["cabin"],
                parsed["price_usd"], parsed["outbound_date"],
            )
            stats["records_imported"] += 1
            continue

        try:
            observation_id = append_observation(
                origin=parsed["origin"],
                destination=parsed["destination"],
                carrier=parsed["carrier"],
                cabin=parsed["cabin"],
                price_usd=parsed["price_usd"],
                outbound_date=parsed["outbound_date"],
                return_date=parsed["return_date"],
                outbound_duration_hours=parsed["outbound_duration_hours"],
                return_duration_hours=parsed["return_duration_hours"],
                outbound_stops=parsed["outbound_stops"],
                return_stops=parsed["return_stops"],
                outbound_routing=parsed["outbound_routing"],
                return_routing=parsed["return_routing"],
                source="historical_seed",
                observation_type="historical_seed",
                data_quality=parsed["data_quality"],
            )
            stats["records_imported"] += 1
            logger.info(
                "SEED: imported %s→%s %s %s $%.0f [%s]",
                parsed["origin"], parsed["destination"],
                parsed["carrier"], parsed["cabin"],
                parsed["price_usd"], observation_id[:8],
            )
        except Exception as exc:
            stats["fetch_errors"].append(f"Record {i+1} write error: {exc}")
            logger.error("SEED: record %d write failed: %s", i + 1, exc)

    logger.info(
        "SEED complete: %d read, %d imported, %d constraint-skipped, %d parse-errors, %d write-errors",
        stats["records_read"],
        stats["records_imported"],
        stats["records_constraint_skipped"],
        stats["records_parse_error"],
        len(stats["fetch_errors"]),
    )
    return stats
