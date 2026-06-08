"""
HISTORICAL SEED IMPORTER — Stage 0 (pre-DISCOVER)

Bootstraps the forecasting model with historical price data before the daily monitor
has accumulated 7+ observations. Without seed data the model runs in LOW confidence
(cold-start) mode for the first 7 days. Seeding 7–29 historical records per series
immediately unlocks MEDIUM confidence and enables the forecasting stage.

Input formats accepted:
  CSV:  carrier,cabin,origin,destination,outbound_date,return_date,price_usd,
        outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,
        outbound_routing,return_routing
        (optional columns: price_egp, price_eur)

  JSON: array of objects with the same field names as CSV columns

Each imported record is validated against apply_constraints() before storage.
Records that fail any constraint are logged and skipped — the store is never
corrupted by constraint violations.

All imported observations are stored with observation_type='historical_seed'
so they are visually distinguishable from live monitoring observations in the store.

Usage:
  python -m radar.main seed --file historical_prices.csv
  python -m radar.main seed --file historical_prices.json
  python -m radar.main seed --file historical_prices.csv --dry-run
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

_REQUIRED_COLUMNS = {
    "carrier", "cabin", "origin", "destination",
    "outbound_date", "return_date", "price_usd",
    "outbound_duration_hours", "return_duration_hours",
    "outbound_stops", "return_stops",
    "outbound_routing", "return_routing",
}


def _parse_record(row: dict, row_num: int) -> Optional[dict]:
    """
    Parse and type-coerce a single raw record dict.
    Returns None on parse failure (logged as a warning).
    Does not apply constraint filtering — that happens in run_seed().
    """
    missing = _REQUIRED_COLUMNS - set(row.keys())
    if missing:
        logger.warning("Row %d: missing columns %s — skipped", row_num, sorted(missing))
        return None

    try:
        return {
            "carrier": str(row["carrier"]).strip().upper(),
            "cabin": str(row["cabin"]).strip().upper(),
            "origin": str(row["origin"]).strip().upper(),
            "destination": str(row["destination"]).strip().upper(),
            "outbound_date": date.fromisoformat(str(row["outbound_date"]).strip()),
            "return_date": date.fromisoformat(str(row["return_date"]).strip()),
            "price_usd": float(row["price_usd"]),
            "outbound_duration_hours": float(row["outbound_duration_hours"]),
            "return_duration_hours": float(row["return_duration_hours"]),
            "outbound_stops": int(row["outbound_stops"]),
            "return_stops": int(row["return_stops"]),
            "outbound_routing": str(row.get("outbound_routing", "")).strip(),
            "return_routing": str(row.get("return_routing", "")).strip(),
            "price_egp": float(row["price_egp"]) if row.get("price_egp") else None,
            "price_eur": float(row["price_eur"]) if row.get("price_eur") else None,
        }
    except (ValueError, KeyError) as exc:
        logger.warning("Row %d: parse error %s — skipped", row_num, exc)
        return None


def _load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _load_json(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"JSON seed file must be an array of objects — got {type(data).__name__}")
    return data


def run_seed(file_path: str | Path, dry_run: bool = False) -> dict:
    """
    Import historical price records from a CSV or JSON file into the schema store.

    file_path: path to CSV or JSON file
    dry_run: log what would be imported without writing to store

    Returns summary dict with import statistics.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")

    ext = path.suffix.lower()
    if ext == ".csv":
        raw_rows = _load_csv(path)
    elif ext == ".json":
        raw_rows = _load_json(path)
    else:
        raise ValueError(f"Unsupported file format: {ext!r} — use .csv or .json")

    logger.info("SEED: loading %d raw records from %s", len(raw_rows), path.name)

    stats = {
        "stage": "SEED",
        "file": str(path),
        "dry_run": dry_run,
        "records_read": len(raw_rows),
        "records_parsed": 0,
        "records_constraint_passed": 0,
        "records_constraint_failed": 0,
        "records_imported": 0,
        "constraint_failures": [],
    }

    for i, raw_row in enumerate(raw_rows, start=1):
        parsed = _parse_record(raw_row, row_num=i)
        if parsed is None:
            continue

        stats["records_parsed"] += 1

        itin = FlightItinerary(
            origin=parsed["origin"],
            destination=parsed["destination"],
            cabin=parsed["cabin"],
            outbound_date=parsed["outbound_date"],
            return_date=parsed["return_date"],
            outbound_duration_hours=parsed["outbound_duration_hours"],
            return_duration_hours=parsed["return_duration_hours"],
            carrier=parsed["carrier"],
            price_usd=parsed["price_usd"],
        )

        constraint_result = apply_constraints(itin)
        if not constraint_result:
            stats["records_constraint_failed"] += 1
            logger.debug(
                "Row %d: constraint violations %s — skipped",
                i, constraint_result.failures,
            )
            stats["constraint_failures"].append({
                "row": i,
                "carrier": parsed["carrier"],
                "route": f"{parsed['origin']}-{parsed['destination']}",
                "cabin": parsed["cabin"],
                "outbound_date": parsed["outbound_date"].isoformat(),
                "failures": constraint_result.failures,
            })
            continue

        stats["records_constraint_passed"] += 1

        if dry_run:
            logger.info(
                "DRY RUN row %d: %s→%s %s %s %s $%.0f — would import",
                i, parsed["origin"], parsed["destination"],
                parsed["carrier"], parsed["cabin"],
                parsed["outbound_date"], parsed["price_usd"],
            )
            continue

        observation_id = append_observation(
            origin=parsed["origin"],
            destination=parsed["destination"],
            carrier=parsed["carrier"],
            cabin=parsed["cabin"],
            price_usd=parsed["price_usd"],
            outbound_date=parsed["outbound_date"].isoformat(),
            return_date=parsed["return_date"].isoformat(),
            outbound_duration_hours=parsed["outbound_duration_hours"],
            return_duration_hours=parsed["return_duration_hours"],
            outbound_stops=parsed["outbound_stops"],
            return_stops=parsed["return_stops"],
            outbound_routing=parsed["outbound_routing"],
            return_routing=parsed["return_routing"],
            source="historical_seed",
            observation_type="historical_seed",
            price_egp=parsed["price_egp"],
            price_eur=parsed["price_eur"],
        )
        stats["records_imported"] += 1

        logger.info(
            "SEED imported: %s→%s %s %s %s $%.0f [%s]",
            parsed["origin"], parsed["destination"],
            parsed["carrier"], parsed["cabin"],
            parsed["outbound_date"], parsed["price_usd"],
            observation_id[:8],
        )

    action = "would import" if dry_run else "imported"
    logger.info(
        "SEED complete: %d read, %d parsed, %d constraint-passed, %d %s, %d constraint-failed",
        stats["records_read"],
        stats["records_parsed"],
        stats["records_constraint_passed"],
        stats["records_imported"] if not dry_run else stats["records_constraint_passed"],
        action,
        stats["records_constraint_failed"],
    )

    return stats
