"""
STAGE 0 — SEED: Historical Price Data Import

Loads historical flight price data from external sources into the schema as
'historical_seed' observations. Seeding accelerates forecasting accuracy from
day one — without it, the forecasting model runs in LOW confidence mode for
the first 7 days of daily monitoring.

INPUT FORMATS SUPPORTED
-----------------------
CSV (--from-csv):
  Required columns: origin, destination, carrier, cabin, outbound_date,
                    return_date, price_usd, source
  Optional:  outbound_duration_hours, return_duration_hours,
             outbound_stops, return_stops, outbound_routing, return_routing,
             price_egp, price_eur

JSON array (--from-json):
  Each element: same fields as CSV above

HISTORICAL DATA SOURCES (manual extraction required — no programmatic access)
-------------------------------------------------------------------------------
Google Flights price history:
  - Depth: ~6 months of historical calendar view prices
  - Access: Manual — click calendar view on Google Flights for each route
  - Format: Scrape or manually record date/price pairs → CSV
  - Coverage: Best for JFK, LAX, MIA, ORD, ATL (most-searched CAI routes)

Kayak price history:
  - Depth: ~12 months via Kayak price calendar (mobile app shows longer range)
  - Access: Manual — Kayak price calendar for each route and class
  - Format: Manual CSV entry
  - Coverage: Business class on major connector hubs (DXB, DOH via EK/QR)

Momondo price history:
  - Depth: ~6 months
  - Access: Manual — flight price chart in Momondo search results
  - Coverage: Aggregator data, useful for cross-validation

Hopper (iOS/Android):
  - Depth: ~12 months of historical predictions stored internally
  - Access: App screenshots / manual CSV entry only (no API)
  - Coverage: Popular routes — CAI-JFK, CAI-LAX via Hopper Egypt
  - Note: Hopper's historical accuracy methodology:
    Uses 5-day moving average over historical 3-year window.
    For the CAI corridor, Hopper shows significant March-April price spikes
    (post-Ramadan demand) and summer (July-August) premium.

ITA Matrix (manual search):
  - Depth: ~11 months forward only (not historical)
  - Access: Manual search at https://matrix.itasoftware.com/search
  - Note: ToS prohibits automated access — manual price extraction only

INTEGRATION PATTERN
-------------------
1. Manually collect historical prices from sources above into a CSV
2. Run: python -m radar.main seed --from-csv historical_prices.csv
3. DISCOVER stage will skip routes already seeded (observation_count > 0)
4. Forecasting model upgrades from LOW → MEDIUM after 7 observations

EXAMPLE CSV FORMAT
------------------
origin,destination,carrier,cabin,outbound_date,return_date,price_usd,source,outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,outbound_routing,return_routing
CAI,JFK,EK,BUSINESS,2026-04-01,2026-04-12,3200.0,google_flights_manual,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI
CAI,JFK,QR,BUSINESS,2026-04-15,2026-04-26,3450.0,kayak_manual,16.0,16.5,1,1,CAI-DOH-JFK,JFK-DOH-CAI
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

# Columns required in every seed record
_REQUIRED_COLUMNS = {
    "origin", "destination", "carrier", "cabin",
    "outbound_date", "return_date", "price_usd", "source",
}

# Columns with safe defaults when absent
_DEFAULTS = {
    "outbound_duration_hours": 15.0,
    "return_duration_hours": 15.0,
    "outbound_stops": 1,
    "return_stops": 1,
    "outbound_routing": "",
    "return_routing": "",
    "price_egp": None,
    "price_eur": None,
}


def _parse_record(row: dict, row_num: int) -> Optional[dict]:
    """Parse and validate a single seed record. Returns None on validation failure."""
    missing = _REQUIRED_COLUMNS - set(row.keys())
    if missing:
        logger.warning("Row %d: missing required columns %s — skipping", row_num, missing)
        return None

    try:
        outbound_date = date.fromisoformat(row["outbound_date"].strip())
        return_date = date.fromisoformat(row["return_date"].strip())
        price_usd = float(row["price_usd"])
    except (ValueError, AttributeError) as exc:
        logger.warning("Row %d: parse error %s — skipping", row_num, exc)
        return None

    if price_usd <= 0:
        logger.warning("Row %d: price_usd=%s is not positive — skipping", row_num, price_usd)
        return None

    def _float(key: str, default: float) -> float:
        val = row.get(key, "").strip() if isinstance(row.get(key), str) else row.get(key)
        if val is None or val == "":
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def _int(key: str, default: int) -> int:
        val = row.get(key, "").strip() if isinstance(row.get(key), str) else row.get(key)
        if val is None or val == "":
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def _opt_float(key: str) -> Optional[float]:
        val = row.get(key, "").strip() if isinstance(row.get(key), str) else row.get(key)
        if val is None or val == "":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    outbound_dur = _float("outbound_duration_hours", _DEFAULTS["outbound_duration_hours"])
    return_dur = _float("return_duration_hours", _DEFAULTS["return_duration_hours"])

    # Apply routing constraints before accepting the record
    itin = FlightItinerary(
        origin=row["origin"].strip().upper(),
        destination=row["destination"].strip().upper(),
        cabin=row["cabin"].strip().upper(),
        outbound_date=outbound_date,
        return_date=return_date,
        outbound_duration_hours=outbound_dur,
        return_duration_hours=return_dur,
        carrier=row["carrier"].strip().upper(),
        price_usd=price_usd,
    )
    constraint_result = apply_constraints(itin)
    if not constraint_result:
        logger.debug(
            "Row %d: constraint failures %s — skipping",
            row_num, constraint_result.failures,
        )
        return None

    return {
        "origin": itin.origin,
        "destination": itin.destination,
        "carrier": itin.carrier,
        "cabin": itin.cabin,
        "outbound_date": outbound_date.isoformat(),
        "return_date": return_date.isoformat(),
        "price_usd": price_usd,
        "source": row.get("source", "manual").strip(),
        "outbound_duration_hours": outbound_dur,
        "return_duration_hours": return_dur,
        "outbound_stops": _int("outbound_stops", _DEFAULTS["outbound_stops"]),
        "return_stops": _int("return_stops", _DEFAULTS["return_stops"]),
        "outbound_routing": row.get("outbound_routing", "").strip() or _DEFAULTS["outbound_routing"],
        "return_routing": row.get("return_routing", "").strip() or _DEFAULTS["return_routing"],
        "price_egp": _opt_float("price_egp"),
        "price_eur": _opt_float("price_eur"),
    }


def _load_records_from_csv(path: Path) -> list[dict]:
    """Load seed records from a CSV file."""
    records = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            parsed = _parse_record(dict(row), i)
            if parsed is not None:
                records.append(parsed)
    return records


def _load_records_from_json(path: Path) -> list[dict]:
    """Load seed records from a JSON array file."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError(f"JSON seed file must contain a top-level array, got {type(raw).__name__}")

    records = []
    for i, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            logger.warning("Record %d: not a dict — skipping", i)
            continue
        parsed = _parse_record(item, i)
        if parsed is not None:
            records.append(parsed)
    return records


def run_seed(
    source_path: Path,
    allow_duplicates: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Import historical price observations from a CSV or JSON file.

    source_path: path to CSV or JSON file
    allow_duplicates: if False (default), skip records where the series already
                      has an observation on the same outbound_date
    dry_run: parse and validate without writing to store

    Returns summary dict.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Seed file not found: {source_path}")

    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        records = _load_records_from_csv(source_path)
    elif suffix == ".json":
        records = _load_records_from_json(source_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix!r} — use .csv or .json")

    stats = {
        "stage": "SEED",
        "source_file": str(source_path),
        "records_parsed": len(records),
        "records_written": 0,
        "records_skipped_duplicate": 0,
        "records_constraint_filtered": 0,
        "dry_run": dry_run,
    }

    if dry_run:
        logger.info("SEED DRY RUN: %d records parsed, 0 written", len(records))
        return stats

    for rec in records:
        if not allow_duplicates:
            existing_series = get_series(
                rec["origin"], rec["destination"], rec["carrier"], rec["cabin"]
            )
            existing_dates = {obs["outbound_date"] for obs in existing_series}
            if rec["outbound_date"] in existing_dates:
                logger.debug(
                    "SEED: duplicate %s→%s %s %s on %s — skipping",
                    rec["origin"], rec["destination"],
                    rec["carrier"], rec["cabin"], rec["outbound_date"],
                )
                stats["records_skipped_duplicate"] += 1
                continue

        append_observation(
            origin=rec["origin"],
            destination=rec["destination"],
            carrier=rec["carrier"],
            cabin=rec["cabin"],
            price_usd=rec["price_usd"],
            outbound_date=rec["outbound_date"],
            return_date=rec["return_date"],
            outbound_duration_hours=rec["outbound_duration_hours"],
            return_duration_hours=rec["return_duration_hours"],
            outbound_stops=rec["outbound_stops"],
            return_stops=rec["return_stops"],
            outbound_routing=rec["outbound_routing"],
            return_routing=rec["return_routing"],
            source=rec["source"],
            observation_type="historical_seed",
            price_egp=rec["price_egp"],
            price_eur=rec["price_eur"],
        )
        stats["records_written"] += 1
        logger.info(
            "SEED: wrote %s→%s %s %s %s $%.0f",
            rec["origin"], rec["destination"],
            rec["carrier"], rec["cabin"],
            rec["outbound_date"], rec["price_usd"],
        )

    logger.info(
        "SEED complete: %d parsed, %d written, %d duplicate skipped",
        stats["records_parsed"],
        stats["records_written"],
        stats["records_skipped_duplicate"],
    )
    return stats
