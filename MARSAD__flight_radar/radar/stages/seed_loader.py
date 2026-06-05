"""
HISTORICAL SEED LOADER — import historical price observations into the store.

Seeds the JSON schema with `observation_type: historical_seed` observations
drawn from a CSV or JSON file. This accelerates the forecasting model from
LOW confidence to MEDIUM (7+ observations) or HIGH (30+ observations)
without waiting for the daily monitor to accumulate observations.

Supported input formats:

  CSV (recommended for manual import):
    Required columns: origin, destination, carrier, cabin, price_usd,
                      outbound_date, return_date, outbound_duration_hours,
                      return_duration_hours, outbound_stops, return_stops,
                      outbound_routing, return_routing, source
    Optional columns: price_egp, price_eur

  JSON (list of observation-shaped dicts):
    Same fields as CSV, as a top-level JSON array.

Each row is passed through apply_constraints() before being stored.
Rows that fail constraints are logged and skipped — never written.

Example CSV row (Google Flights price history export — manually transcribed):
  CAI,JFK,EK,BUSINESS,3200.00,2024-04-15,2024-04-26,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI,historical_seed

Usage:
  python -m radar.main seed --file /path/to/history.csv
  python -m radar.main seed --file /path/to/history.json --dry-run

See README for historical seed data source research notes.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)


def _parse_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _parse_int(val: str, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _parse_date(val: str) -> Optional[date]:
    try:
        return date.fromisoformat(val.strip())
    except (ValueError, AttributeError):
        return None


def _row_to_itinerary(row: dict) -> Optional[tuple[FlightItinerary, dict]]:
    """
    Parse a seed row into a FlightItinerary for constraint checking
    and a clean dict for append_observation().
    Returns None if required fields are missing or unparseable.
    """
    origin = row.get("origin", "").strip().upper()
    destination = row.get("destination", "").strip().upper()
    carrier = row.get("carrier", "").strip().upper()
    cabin = row.get("cabin", "").strip().upper()
    source = row.get("source", "historical_seed").strip()

    outbound_date = _parse_date(row.get("outbound_date", ""))
    return_date = _parse_date(row.get("return_date", ""))

    if not all([origin, destination, carrier, cabin, outbound_date, return_date]):
        return None

    price_usd = _parse_float(row.get("price_usd", ""))
    if price_usd <= 0:
        return None

    outbound_hours = _parse_float(row.get("outbound_duration_hours", "0"))
    return_hours = _parse_float(row.get("return_duration_hours", "0"))
    outbound_stops = _parse_int(row.get("outbound_stops", "0"))
    return_stops = _parse_int(row.get("return_stops", "0"))
    outbound_routing = row.get("outbound_routing", "").strip()
    return_routing = row.get("return_routing", "").strip()
    price_egp = _parse_float(row.get("price_egp", "")) or None
    price_eur = _parse_float(row.get("price_eur", "")) or None

    itin = FlightItinerary(
        origin=origin,
        destination=destination,
        cabin=cabin,
        outbound_date=outbound_date,
        return_date=return_date,
        outbound_duration_hours=outbound_hours,
        return_duration_hours=return_hours,
        carrier=carrier,
        price_usd=price_usd,
    )

    obs_kwargs = dict(
        origin=origin,
        destination=destination,
        carrier=carrier,
        cabin=cabin,
        price_usd=price_usd,
        outbound_date=outbound_date.isoformat(),
        return_date=return_date.isoformat(),
        outbound_duration_hours=outbound_hours,
        return_duration_hours=return_hours,
        outbound_stops=outbound_stops,
        return_stops=return_stops,
        outbound_routing=outbound_routing,
        return_routing=return_routing,
        source=source,
        observation_type="historical_seed",
        price_egp=price_egp,
        price_eur=price_eur,
        data_quality="estimated",
    )

    return itin, obs_kwargs


def _load_rows(file_path: Path) -> list[dict]:
    """Load rows from CSV or JSON. Returns a list of dicts."""
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON seed file must be a top-level array of objects")
        return data
    else:
        # Default: treat as CSV
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]


def run_seed(
    file_path: str,
    dry_run: bool = False,
) -> dict:
    """
    Import historical seed observations from a CSV or JSON file.

    Applies apply_constraints() to every row before writing.
    Rows that fail constraints are logged and counted as skipped.

    Returns summary dict with import statistics.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error("Seed file not found: %s", path)
        return {
            "stage": "SEED",
            "error": f"File not found: {path}",
            "observations_imported": 0,
            "rows_total": 0,
            "rows_skipped_constraint": 0,
            "rows_skipped_error": 0,
        }

    try:
        rows = _load_rows(path)
    except Exception as exc:
        logger.error("Failed to load seed file: %s", exc)
        return {
            "stage": "SEED",
            "error": str(exc),
            "observations_imported": 0,
            "rows_total": 0,
            "rows_skipped_constraint": 0,
            "rows_skipped_error": 0,
        }

    stats = {
        "stage": "SEED",
        "file": str(path),
        "rows_total": len(rows),
        "observations_imported": 0,
        "rows_skipped_constraint": 0,
        "rows_skipped_error": 0,
        "dry_run": dry_run,
    }

    logger.info("SEED: loading %d rows from %s", len(rows), path)

    for i, row in enumerate(rows):
        try:
            parsed = _row_to_itinerary(row)
        except Exception as exc:
            logger.warning("SEED row %d: parse error — %s", i + 1, exc)
            stats["rows_skipped_error"] += 1
            continue

        if parsed is None:
            logger.debug("SEED row %d: missing or unparseable required fields — skipped", i + 1)
            stats["rows_skipped_error"] += 1
            continue

        itin, obs_kwargs = parsed

        constraint_result = apply_constraints(itin)
        if not constraint_result:
            logger.debug(
                "SEED row %d: constraint filter — %s", i + 1, constraint_result.failures
            )
            stats["rows_skipped_constraint"] += 1
            continue

        if dry_run:
            logger.info(
                "SEED DRY RUN: %s→%s %s %s %s $%.0f",
                itin.origin, itin.destination, itin.carrier, itin.cabin,
                obs_kwargs["outbound_date"], itin.price_usd,
            )
            stats["observations_imported"] += 1
            continue

        try:
            observation_id = append_observation(**obs_kwargs)
            stats["observations_imported"] += 1
            logger.debug(
                "SEED: %s→%s %s %s %s $%.0f [%s]",
                itin.origin, itin.destination, itin.carrier, itin.cabin,
                obs_kwargs["outbound_date"], itin.price_usd,
                observation_id[:8],
            )
        except Exception as exc:
            logger.error("SEED row %d: append failed — %s", i + 1, exc)
            stats["rows_skipped_error"] += 1

    logger.info(
        "SEED complete: %d imported, %d skipped (constraint), %d skipped (error)",
        stats["observations_imported"],
        stats["rows_skipped_constraint"],
        stats["rows_skipped_error"],
    )

    return stats
