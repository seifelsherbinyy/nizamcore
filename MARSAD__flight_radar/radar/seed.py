"""
Historical Price Seed — import external price data as historical_seed observations.

Skips the 7-day cold-start period when external historical data is available.
Seeding 7+ valid observations from any source brings a series to MEDIUM confidence,
enabling the EWM model and unblocking the BUY_SIGNAL gate.

Observation type: 'historical_seed'
Data quality:     'estimated'

Sources supported:
  - CSV file (manual transcription from Google Flights / Kayak price graphs)
  - JSON file (array of objects matching the same field spec)

Available historical data as of May 2026:
  Google Flights price history  — visible in UI only, no API. Access: navigate to
    google.com/flights → select route → check the "Price history" section. Depth:
    ~3 months. Export: manual transcription of monthly average prices.
  Kayak price trend charts      — UI only, no API. "Price trend" tab on route pages.
    Depth: ~6 months. Format: approximate monthly/weekly averages only.
  Hopper                        — consumer app only, no public API or export.
  ITA Matrix                    — no price history, current prices only.

Recommended workflow:
  1. Visit Google Flights for each priority route (JFK, MIA, LAX, EWR).
  2. Note 7–10 monthly price points from the price history graph (mid 2025 – early 2026).
  3. Enter them in prices.csv with estimated outbound dates (use the 15th of each month).
  4. Run: python -m radar.main seed --file prices.csv --dry-run (preview first)
  5. Run: python -m radar.main seed --file prices.csv (import)

CSV format (header row required):
  destination,carrier,cabin,price_usd,outbound_date,return_date
  JFK,EK,BUSINESS,3100,2027-03-15,2027-03-26
  JFK,EK,BUSINESS,2950,2027-04-01,2027-04-12
  ...

Optional CSV columns (with defaults):
  origin (CAI), outbound_duration_hours (0), return_duration_hours (0),
  outbound_stops (1), return_stops (1), outbound_routing, return_routing, source_note

Notes:
  - Flight time constraints are skipped by default for historical seeds because
    duration data is rarely available in manually-collected price data.
  - All prices must be in USD. outbound_date/return_date must be within the
    configured travel window (RADAR_WINDOW_START – RADAR_WINDOW_END).
  - Duration and routing constraints (9–14 nights, valid cabin, valid destination)
    are always enforced — bad rows are filtered and logged.
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


def _parse_row(row: dict, source_note: str = "manual_import") -> Optional[dict]:
    """
    Parse a CSV or JSON row dict into observation fields.
    Returns None and logs a warning on any parse failure.
    """
    try:
        origin = row.get("origin", "CAI").strip().upper()
        destination = row.get("destination", "").strip().upper()
        carrier = row.get("carrier", "XX").strip().upper()
        cabin = row.get("cabin", "BUSINESS").strip().upper()
        price_usd = float(row["price_usd"])
        outbound_date = row["outbound_date"].strip()
        return_date = row["return_date"].strip()
        outbound_hours = float(row.get("outbound_duration_hours") or 0.0)
        return_hours = float(row.get("return_duration_hours") or 0.0)
        outbound_stops = int(row.get("outbound_stops") or 1)
        return_stops = int(row.get("return_stops") or 1)
        outbound_routing = (row.get("outbound_routing") or "").strip() or f"CAI-{destination}"
        return_routing = (row.get("return_routing") or "").strip() or f"{destination}-CAI"

        if not destination:
            logger.warning("Row missing destination — skipping")
            return None

        if price_usd <= 0:
            logger.warning("Invalid price %.2f for %s — skipping", price_usd, destination)
            return None

        # Validate date formats
        date.fromisoformat(outbound_date)
        date.fromisoformat(return_date)

        return {
            "origin": origin,
            "destination": destination,
            "carrier": carrier,
            "cabin": cabin,
            "price_usd": price_usd,
            "outbound_date": outbound_date,
            "return_date": return_date,
            "outbound_duration_hours": outbound_hours,
            "return_duration_hours": return_hours,
            "outbound_stops": outbound_stops,
            "return_stops": return_stops,
            "outbound_routing": outbound_routing,
            "return_routing": return_routing,
            "source_note": row.get("source_note", source_note),
        }
    except (KeyError, ValueError, TypeError) as exc:
        logger.warning("Row parse error: %s — row: %s", exc, row)
        return None


def _passes_constraints(parsed: dict, skip_flight_time_check: bool = True) -> bool:
    """
    Apply routing constraints before storing a seed observation.

    skip_flight_time_check=True by default: historical price data rarely includes
    per-leg duration, so we skip the 30-hour check for seed imports. All other
    constraints (origin, destination, cabin, duration in nights, window) still apply.
    """
    itin = FlightItinerary(
        origin=parsed["origin"],
        destination=parsed["destination"],
        cabin=parsed["cabin"],
        outbound_date=date.fromisoformat(parsed["outbound_date"]),
        return_date=date.fromisoformat(parsed["return_date"]),
        outbound_duration_hours=0.0 if skip_flight_time_check else parsed["outbound_duration_hours"],
        return_duration_hours=0.0 if skip_flight_time_check else parsed["return_duration_hours"],
        carrier=parsed["carrier"],
        price_usd=parsed["price_usd"],
    )
    result = apply_constraints(itin)
    if not result.passed:
        logger.debug("Seed row filtered by constraints: %s", result.failures)
    return result.passed


def _write_observation(parsed: dict, dry_run: bool) -> None:
    if dry_run:
        logger.info(
            "DRY RUN: would seed %s→%s %s %s $%.0f (%s)",
            parsed["origin"], parsed["destination"],
            parsed["carrier"], parsed["cabin"],
            parsed["price_usd"], parsed["outbound_date"],
        )
        return

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
        data_quality="estimated",
    )
    logger.info(
        "Seeded: %s→%s %s %s $%.0f (%s)",
        parsed["origin"], parsed["destination"],
        parsed["carrier"], parsed["cabin"],
        parsed["price_usd"], parsed["outbound_date"],
    )


def _process_rows(
    rows: list[dict],
    source_note: str,
    skip_flight_time_check: bool,
    dry_run: bool,
) -> dict:
    stats = {
        "rows_read": len(rows),
        "rows_imported": 0,
        "rows_filtered": 0,
        "rows_error": 0,
        "dry_run": dry_run,
    }
    for row in rows:
        parsed = _parse_row(row, source_note=source_note)
        if parsed is None:
            stats["rows_error"] += 1
            continue
        if not _passes_constraints(parsed, skip_flight_time_check=skip_flight_time_check):
            stats["rows_filtered"] += 1
            continue
        _write_observation(parsed, dry_run=dry_run)
        stats["rows_imported"] += 1
    return stats


def import_from_csv(
    filepath: Path,
    source_note: str = "manual_import",
    skip_flight_time_check: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Import historical price observations from a CSV file.

    Required CSV columns: destination, carrier, cabin, price_usd,
                          outbound_date, return_date
    Optional columns: origin (CAI), outbound_duration_hours, return_duration_hours,
                      outbound_stops, return_stops, outbound_routing, return_routing,
                      source_note

    Returns import statistics dict with keys: rows_read, rows_imported,
    rows_filtered, rows_error, dry_run.
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except (OSError, csv.Error) as exc:
        logger.error("CSV read error: %s", exc)
        return {"source": str(filepath), "rows_read": 0, "rows_imported": 0,
                "rows_filtered": 0, "rows_error": 0, "dry_run": dry_run, "error": str(exc)}

    stats = _process_rows(rows, source_note=source_note,
                          skip_flight_time_check=skip_flight_time_check, dry_run=dry_run)
    stats["source"] = str(filepath)
    logger.info(
        "CSV seed complete: %d read, %d imported, %d filtered, %d errors",
        stats["rows_read"], stats["rows_imported"], stats["rows_filtered"], stats["rows_error"],
    )
    return stats


def import_from_json(
    filepath: Path,
    source_note: str = "manual_import",
    skip_flight_time_check: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Import historical price observations from a JSON file.

    JSON must be an array of objects. Fields: same as CSV.

    Returns import statistics dict.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON root must be an array of objects")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.error("JSON read error: %s", exc)
        return {"source": str(filepath), "rows_read": 0, "rows_imported": 0,
                "rows_filtered": 0, "rows_error": 0, "dry_run": dry_run, "error": str(exc)}

    stats = _process_rows(data, source_note=source_note,
                          skip_flight_time_check=skip_flight_time_check, dry_run=dry_run)
    stats["source"] = str(filepath)
    logger.info(
        "JSON seed complete: %d read, %d imported, %d filtered, %d errors",
        stats["rows_read"], stats["rows_imported"], stats["rows_filtered"], stats["rows_error"],
    )
    return stats
