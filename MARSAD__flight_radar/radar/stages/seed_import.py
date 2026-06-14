"""
HISTORICAL PRICE SEED IMPORT — Bootstrap forecasting with pre-existing data.

Purpose:
  The forecast model needs ≥7 observations before producing MEDIUM-confidence
  signals and ≥30 for HIGH-confidence. Without seed data the pipeline runs in
  LOW-confidence mode for the first 7 days of live monitoring.

  Seed import ingests historical price data from external sources (CSV, JSON)
  and stores them as observation_type='historical_seed', giving the forecast
  model a head-start without waiting for monitoring to accumulate enough runs.

Accepted seed sources (all documented in README — Historical Price Seed Research):
  1. CSV export — generic flat file with required columns
  2. JSON array  — list of objects with required fields
  3. Google Flights price-history format (manual export or scrape)

CLI:
  python -m radar.main seed-import --file prices.csv
  python -m radar.main seed-import --file prices.json --format json
  python -m radar.main seed-import --file prices.csv --dry-run

CSV required columns:
  origin, destination, carrier, cabin,
  outbound_date (YYYY-MM-DD), return_date (YYYY-MM-DD),
  price_usd, outbound_duration_hours, return_duration_hours,
  outbound_stops, return_stops, outbound_routing, return_routing
  Optional: price_egp, price_eur, data_quality, observed_at

Observation type stored: 'historical_seed'
Source stored: 'historical_seed'
All records are filtered through apply_constraints() before storage.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_row(row: dict) -> Optional[dict]:
    """
    Parse a single seed record into the fields needed by append_observation.
    Returns None if required fields are missing or unparseable.
    """
    required = [
        "origin", "destination", "carrier", "cabin",
        "outbound_date", "return_date", "price_usd",
        "outbound_duration_hours", "return_duration_hours",
    ]
    for field in required:
        if not row.get(field):
            logger.debug("Seed record missing required field '%s': %s", field, row)
            return None

    try:
        return {
            "origin": str(row["origin"]).strip().upper(),
            "destination": str(row["destination"]).strip().upper(),
            "carrier": str(row["carrier"]).strip().upper(),
            "cabin": str(row["cabin"]).strip().upper(),
            "outbound_date": str(row["outbound_date"]).strip(),
            "return_date": str(row["return_date"]).strip(),
            "price_usd": float(row["price_usd"]),
            "outbound_duration_hours": float(row["outbound_duration_hours"]),
            "return_duration_hours": float(row["return_duration_hours"]),
            "outbound_stops": int(row.get("outbound_stops", 0)),
            "return_stops": int(row.get("return_stops", 0)),
            "outbound_routing": str(row.get("outbound_routing", "")).strip(),
            "return_routing": str(row.get("return_routing", "")).strip(),
            "price_egp": float(row["price_egp"]) if row.get("price_egp") else None,
            "price_eur": float(row["price_eur"]) if row.get("price_eur") else None,
            "data_quality": str(row.get("data_quality", "estimated")).strip(),
        }
    except (ValueError, TypeError) as exc:
        logger.debug("Seed record parse error: %s — %s", exc, row)
        return None


def _load_csv(file_path: Path) -> list[dict]:
    rows = []
    with open(file_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def _load_json(file_path: Path) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "records" in data:
        return data["records"]
    raise ValueError(
        f"JSON seed file must be an array or an object with a 'records' key — got: {type(data)}"
    )


def run_seed_import(
    file_path: str,
    fmt: str = "csv",
    dry_run: bool = False,
    skip_invalid: bool = True,
) -> dict:
    """
    Import historical price observations from a CSV or JSON seed file.

    Args:
        file_path: Path to seed file.
        fmt: 'csv' or 'json'.
        dry_run: If True, validate and count but do not write.
        skip_invalid: If True, log invalid records and continue. If False, abort on first error.

    Returns:
        Summary dict: total_records, imported, filtered_by_constraints, parse_errors, skipped_duplicates.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")

    if fmt == "csv":
        raw_rows = _load_csv(path)
    elif fmt == "json":
        raw_rows = _load_json(path)
    else:
        raise ValueError(f"Unknown format: {fmt!r} — must be 'csv' or 'json'")

    stats = {
        "stage": "SEED_IMPORT",
        "source_file": str(path),
        "format": fmt,
        "dry_run": dry_run,
        "total_records": len(raw_rows),
        "imported": 0,
        "filtered_by_constraints": 0,
        "parse_errors": 0,
        "skipped_duplicates": 0,
    }

    logger.info(
        "SEED_IMPORT: loading %d records from %s (%s)",
        len(raw_rows), path.name, fmt,
    )

    for i, raw in enumerate(raw_rows):
        parsed = _parse_row(raw)
        if parsed is None:
            stats["parse_errors"] += 1
            if not skip_invalid:
                raise ValueError(f"Parse error on record {i}: {raw}")
            continue

        try:
            outbound = date.fromisoformat(parsed["outbound_date"])
            ret = date.fromisoformat(parsed["return_date"])
        except ValueError as exc:
            logger.debug("Date parse error record %d: %s", i, exc)
            stats["parse_errors"] += 1
            continue

        itin = FlightItinerary(
            origin=parsed["origin"],
            destination=parsed["destination"],
            cabin=parsed["cabin"],
            outbound_date=outbound,
            return_date=ret,
            outbound_duration_hours=parsed["outbound_duration_hours"],
            return_duration_hours=parsed["return_duration_hours"],
            carrier=parsed["carrier"],
            price_usd=parsed["price_usd"],
        )
        constraint_result = apply_constraints(itin)
        if not constraint_result:
            logger.debug(
                "Seed record %d filtered: %s", i, constraint_result.failures
            )
            stats["filtered_by_constraints"] += 1
            continue

        if dry_run:
            stats["imported"] += 1
            continue

        try:
            append_observation(
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
                price_egp=parsed.get("price_egp"),
                price_eur=parsed.get("price_eur"),
                data_quality=parsed.get("data_quality", "estimated"),
            )
            stats["imported"] += 1
            logger.debug(
                "Seeded: %s→%s %s %s $%.0f %s",
                parsed["origin"], parsed["destination"],
                parsed["carrier"], parsed["cabin"],
                parsed["price_usd"], parsed["outbound_date"],
            )
        except Exception as exc:
            logger.error("Failed to write seed record %d: %s", i, exc)
            stats["parse_errors"] += 1

    logger.info(
        "SEED_IMPORT complete: %d/%d imported, %d filtered, %d errors%s",
        stats["imported"],
        stats["total_records"],
        stats["filtered_by_constraints"],
        stats["parse_errors"],
        " (DRY RUN)" if dry_run else "",
    )
    return stats


# ── CSV template generator ────────────────────────────────────────────────────

def generate_seed_template(output_path: str = "seed_template.csv") -> str:
    """
    Write a CSV template that shows the expected seed file format.
    Returns the path written.
    """
    path = Path(output_path)
    header = [
        "origin", "destination", "carrier", "cabin",
        "outbound_date", "return_date", "price_usd",
        "outbound_duration_hours", "return_duration_hours",
        "outbound_stops", "return_stops",
        "outbound_routing", "return_routing",
        "price_egp", "price_eur", "data_quality",
    ]
    example_rows = [
        ["CAI", "JFK", "EK", "BUSINESS", "2027-04-01", "2027-04-12", "3200", "14.5", "15.0", "1", "1", "CAI-DXB-JFK", "JFK-DXB-CAI", "", "", "estimated"],
        ["CAI", "JFK", "QR", "PREMIUM_ECONOMY", "2027-05-15", "2027-05-26", "1450", "16.0", "17.0", "1", "1", "CAI-DOH-JFK", "JFK-DOH-CAI", "", "", "estimated"],
        ["CAI", "LAX", "LH", "BUSINESS", "2027-06-01", "2027-06-12", "3800", "16.25", "17.0", "1", "1", "CAI-FRA-LAX", "LAX-FRA-CAI", "", "", "estimated"],
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(example_rows)

    logger.info("Seed template written to %s", path)
    return str(path)
