"""
STAGE 0 — SEED: Historical Price Import

Imports historical flight price observations from CSV or JSON files into the
schema store as observation_type='historical_seed'. This accelerates the
forecasting model by providing 30+ days of history before the daily monitor
has accumulated them organically.

The seed stage runs once, before DISCOVER, and marks every imported row as
'historical_seed' so it is clearly distinguishable from live monitoring data.

HISTORICAL DATA SOURCES (research as of June 2026):
──────────────────────────────────────────────────
A) Google Flights price history (manual only)
   - Available via google.com/travel/flights — click a date on the price graph.
   - Depth: ~3 months visible in the calendar heat-map; ~12 months via "Price history"
     chart on specific route+date combinations.
   - Access: manual screenshot / CSV export — no public API.
   - Integration: export to the seed CSV format below and run this module.

B) Kayak price history charts
   - Available at kayak.com — "Price trend" panel on search results.
   - Depth: ~60 days shown per route; varies by destination.
   - Access: manual screenshot or Kayak's "Export to CSV" button (available on some
     results pages). No programmatic API.
   - Integration: export to seed CSV format; price is per-route (not per-carrier).

C) Hopper (app only — no web export)
   - Hopper's "Watch this trip" stores history per device for 90 days.
   - Access: manual — no export capability. Useful for cross-validation only.
   - Hopper's published methodology: EWM on 7-day rolling window with promotional
     event detection; aligns with this module's Tier 2 model.

D) Google Flights API via SerpApi (programmatic — preferred)
   - SerpApi does not provide historical prices; each search returns current fares.
   - STRATEGY: run `python -m radar.main discover` repeatedly over N days, then
     run `python -m radar.main seed --source store` to promote baseline observations
     as a rolling history seed.

SEED CSV FORMAT:
───────────────
Required columns (order does not matter):
  route           e.g. "CAI-JFK"
  carrier         IATA code e.g. "EK"
  cabin           BUSINESS or PREMIUM_ECONOMY
  outbound_date   ISO 8601 date e.g. "2027-04-01"
  return_date     ISO 8601 date e.g. "2027-04-12"
  price_usd       e.g. 3200.0
  source          e.g. "google_flights_history" or "kayak_history"
  observed_date   ISO 8601 date when this price was observed e.g. "2026-12-01"

Optional columns (filled with defaults if absent):
  outbound_duration_hours   default 14.0
  return_duration_hours     default 14.0
  outbound_stops            default 1
  return_stops              default 1
  outbound_routing          default "<origin>-<dest>"
  return_routing            default "<dest>-<origin>"
  price_egp                 default null
  price_eur                 default null

Usage:
  python -m radar.main seed --csv path/to/history.csv
  python -m radar.main seed --json path/to/history.json
  python -m radar.main seed --dry-run --csv path/to/history.csv
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from radar.constraints import apply_constraints, FlightItinerary
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_row(row: dict) -> Optional[dict]:
    """
    Parse and validate a single seed row. Returns a normalised dict or None if invalid.
    Applies the routing constraint engine — invalid rows are logged and skipped.
    """
    try:
        route = row.get("route", "").strip().upper()
        parts = route.split("-")
        if len(parts) != 2:
            logger.warning("Seed row skipped: invalid route %r", route)
            return None
        origin, destination = parts[0], parts[1]

        outbound_date = date.fromisoformat(row["outbound_date"].strip())
        return_date = date.fromisoformat(row["return_date"].strip())
        price_usd = float(row["price_usd"])
        carrier = row.get("carrier", "UNKNOWN").strip().upper()
        cabin = row.get("cabin", "BUSINESS").strip().upper()
        source = row.get("source", "historical_seed").strip()

        outbound_hours = float(row.get("outbound_duration_hours", 14.0))
        return_hours = float(row.get("return_duration_hours", 14.0))
        outbound_stops = int(row.get("outbound_stops", 1))
        return_stops = int(row.get("return_stops", 1))
        outbound_routing = row.get("outbound_routing", f"{origin}-{destination}").strip()
        return_routing = row.get("return_routing", f"{destination}-{origin}").strip()

        price_egp_raw = row.get("price_egp", "")
        price_eur_raw = row.get("price_eur", "")
        price_egp = float(price_egp_raw) if price_egp_raw and str(price_egp_raw).strip() else None
        price_eur = float(price_eur_raw) if price_eur_raw and str(price_eur_raw).strip() else None

    except (KeyError, ValueError, TypeError) as exc:
        logger.warning("Seed row parse error: %s — row: %s", exc, row)
        return None

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
    constraint = apply_constraints(itin)
    if not constraint:
        logger.debug("Seed row filtered by constraint engine: %s", constraint.failures)
        return None

    return {
        "origin": origin,
        "destination": destination,
        "carrier": carrier,
        "cabin": cabin,
        "price_usd": price_usd,
        "outbound_date": outbound_date.isoformat(),
        "return_date": return_date.isoformat(),
        "outbound_duration_hours": outbound_hours,
        "return_duration_hours": return_hours,
        "outbound_stops": outbound_stops,
        "return_stops": return_stops,
        "outbound_routing": outbound_routing,
        "return_routing": return_routing,
        "source": source,
        "price_egp": price_egp,
        "price_eur": price_eur,
    }


def _load_csv(csv_path: Path) -> list[dict]:
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def _load_json(json_path: Path) -> list[dict]:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "observations" in data:
        return data["observations"]
    raise ValueError(f"JSON seed file must be a list or a dict with an 'observations' key")


def run_seed(
    csv_path: Optional[Path] = None,
    json_path: Optional[Path] = None,
    dry_run: bool = False,
) -> dict:
    """
    Import historical price seed data into the schema store.

    csv_path: path to seed CSV file (see module docstring for format)
    json_path: path to seed JSON file (list of row dicts)
    dry_run: parse and validate without writing to store

    Returns summary dict with import statistics.
    """
    if csv_path is None and json_path is None:
        return {
            "stage": "SEED",
            "error": "No seed file provided — pass --csv or --json",
            "rows_parsed": 0,
            "rows_imported": 0,
            "rows_filtered": 0,
        }

    raw_rows: list[dict] = []
    if csv_path:
        logger.info("SEED: loading CSV from %s", csv_path)
        raw_rows.extend(_load_csv(csv_path))
    if json_path:
        logger.info("SEED: loading JSON from %s", json_path)
        raw_rows.extend(_load_json(json_path))

    logger.info("SEED: %d raw rows loaded — validating against constraint engine", len(raw_rows))

    if dry_run:
        logger.info("DRY RUN — parsing only, no writes")

    stats = {
        "stage": "SEED",
        "dry_run": dry_run,
        "rows_raw": len(raw_rows),
        "rows_parsed": 0,
        "rows_imported": 0,
        "rows_filtered": 0,
        "rows_error": 0,
    }

    for row in raw_rows:
        parsed = _parse_row(row)
        if parsed is None:
            stats["rows_filtered"] += 1
            continue

        stats["rows_parsed"] += 1

        if dry_run:
            logger.debug(
                "DRY RUN: would import %s→%s %s %s $%.0f on %s",
                parsed["origin"], parsed["destination"],
                parsed["carrier"], parsed["cabin"],
                parsed["price_usd"], parsed["outbound_date"],
            )
            stats["rows_imported"] += 1
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
                source=parsed["source"],
                observation_type="historical_seed",
                price_egp=parsed.get("price_egp"),
                price_eur=parsed.get("price_eur"),
            )
            stats["rows_imported"] += 1
            logger.debug(
                "SEED imported: %s→%s %s %s $%.0f [%s]",
                parsed["origin"], parsed["destination"],
                parsed["carrier"], parsed["cabin"],
                parsed["price_usd"], observation_id[:8],
            )
        except Exception as exc:
            stats["rows_error"] += 1
            logger.error("SEED import failed for row %s: %s", parsed, exc)

    logger.info(
        "SEED complete: %d raw → %d imported, %d filtered, %d errors",
        stats["rows_raw"],
        stats["rows_imported"],
        stats["rows_filtered"],
        stats["rows_error"],
    )

    return stats
