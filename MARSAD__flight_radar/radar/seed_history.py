"""
MARSAD Historical Price Seed — Stage 0 (pre-DISCOVER)

Imports historical price observations from external manual sources into the schema
store as `historical_seed` observations, accelerating forecasting model accuracy
from day one without waiting 30 days for the daily monitor to accumulate data.

Usage:
    python -m radar.main seed-history --file path/to/seed.csv
    python -m radar.main seed-history --file path/to/seed.json
    python -m radar.main seed-history --dry-run --file path/to/seed.csv

Supported input formats:
    CSV: with column headers matching the FlightSeedRecord fields (see below)
    JSON: list of FlightSeedRecord-shaped dicts

AVAILABLE HISTORICAL SOURCES (as of 2026):
───────────────────────────────────────────

A) Google Flights Price History
   Access:  Open Google Flights for a specific CAI→USA route, click the price
            graph icon (calendar view). Historical prices shown for last 3-6
            months at departure-date granularity. No programmatic API.
   Depth:   3–6 months visible in the calendar heatmap.
   Format:  Manual capture — read prices from the UI and enter into seed CSV.
   Quality: Confirmed (reflects actual search results for that departure date).
   Note:    2027 dates are not yet visible — this source populates relative
            price knowledge for the CAI corridor, not 2027-specific prices.

B) Hopper Historical Price Data
   Access:  Hopper app (iOS/Android) shows a price history graph for a
            specific route over the last 12 months. No public API.
   Depth:   Up to 12 months.
   Format:  Manual capture from app's price history chart.
   Quality: Estimated (derived from Hopper's aggregated purchase data).
   Note:    Hopper's 'Price Prediction' methodology uses 10 billion prices
            from the last 12 months to train models — see Hopper research
            publications for methodology validation.

C) Kayak Price History Charts
   Access:  Kayak.com route pages show a 3-month price history chart.
            URL pattern: kayak.com/flights/CAI-JFK/YYYY-MM-DD/YYYY-MM-DD
   Depth:   3 months.
   Format:  Manual capture from the chart tooltip data.
   Quality: Estimated (aggregated from partner OTA search results).

D) Google Flights Explore View
   Access:  google.com/flights?hl=en → Explore → set origin=CAI.
            Shows a price-by-month heatmap. Useful for seasonal baseline.
   Depth:   Current booking horizon (~11 months out).
   Format:  Manual capture — month-level price estimates.
   Quality: Estimated (price displayed is the lowest found for flexible dates).

E) SerpApi Historical Search (programmatic)
   Access:  SerpApi Google Flights API with past departure dates returns
            cached price data up to ~6 months back.
   Command: python -m radar.main seed-history --serpapi-historical --months 3
   Depth:   ~3–6 months (dependent on SerpApi cache).
   Format:  Automatic via _fetch_serpapi_historical() below.
   Quality: Confirmed (API response).
   Note:    Consumes SERPAPI_KEY quota — ~(12 destinations × 2 cabins × months)
            searches. At 3 months back: ~72 searches from the free tier budget.

INTEGRATION METHOD:
───────────────────
All sources produce observations with:
  observation_type: "historical_seed"
  source: "manual" (for A/B/C/D) or "serpapi" (for E)
  data_quality: "estimated" (for A/B/C/D) or "confirmed" (for E)

Historical seed observations are pre-pended into the store as early observations
so the daily monitor's deltas and the forecast model's percentiles are immediately
grounded in historical context rather than starting blind.

The seed module enforces routing constraints before writing any observation.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from radar.config import (
    ALL_CARRIERS,
    SERPAPI_KEY,
    WINDOW_END,
    WINDOW_START,
)
from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)


@dataclass
class FlightSeedRecord:
    """A single historical price observation for import."""
    origin: str
    destination: str
    carrier: str
    cabin: str
    outbound_date: str          # ISO date string e.g. "2026-10-15"
    return_date: str            # ISO date string
    price_usd: float
    outbound_duration_hours: float = 14.0
    return_duration_hours: float = 14.0
    outbound_stops: int = 1
    return_stops: int = 1
    outbound_routing: str = ""
    return_routing: str = ""
    source: str = "manual"      # "manual" | "serpapi" | "historical_seed"
    data_quality: str = "estimated"


def _validate_record(rec: FlightSeedRecord) -> tuple[bool, list[str]]:
    """Apply routing constraints to a seed record before import."""
    try:
        itin = FlightItinerary(
            origin=rec.origin,
            destination=rec.destination,
            cabin=rec.cabin,
            outbound_date=date.fromisoformat(rec.outbound_date),
            return_date=date.fromisoformat(rec.return_date),
            outbound_duration_hours=rec.outbound_duration_hours,
            return_duration_hours=rec.return_duration_hours,
            carrier=rec.carrier,
            price_usd=rec.price_usd,
        )
    except (ValueError, TypeError) as exc:
        return False, [f"Invalid date or field: {exc}"]

    result = apply_constraints(itin)
    return result.passed, result.failures


def load_from_csv(path: Path) -> list[FlightSeedRecord]:
    """
    Load seed records from a CSV file.

    Required columns: origin, destination, carrier, cabin, outbound_date,
                      return_date, price_usd
    Optional columns: outbound_duration_hours, return_duration_hours,
                      outbound_stops, return_stops, outbound_routing,
                      return_routing, source, data_quality
    """
    records = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            try:
                rec = FlightSeedRecord(
                    origin=row["origin"].strip().upper(),
                    destination=row["destination"].strip().upper(),
                    carrier=row["carrier"].strip().upper(),
                    cabin=row["cabin"].strip().upper(),
                    outbound_date=row["outbound_date"].strip(),
                    return_date=row["return_date"].strip(),
                    price_usd=float(row["price_usd"]),
                    outbound_duration_hours=float(row.get("outbound_duration_hours") or 14.0),
                    return_duration_hours=float(row.get("return_duration_hours") or 14.0),
                    outbound_stops=int(row.get("outbound_stops") or 1),
                    return_stops=int(row.get("return_stops") or 1),
                    outbound_routing=row.get("outbound_routing", "").strip(),
                    return_routing=row.get("return_routing", "").strip(),
                    source=row.get("source", "manual").strip(),
                    data_quality=row.get("data_quality", "estimated").strip(),
                )
                records.append(rec)
            except (KeyError, ValueError) as exc:
                logger.warning("CSV row %d skipped: %s", i, exc)

    logger.info("Loaded %d records from %s", len(records), path)
    return records


def load_from_json(path: Path) -> list[FlightSeedRecord]:
    """
    Load seed records from a JSON file (list of dicts with FlightSeedRecord fields).
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"JSON seed file must be a list of records, got {type(data)}")

    records = []
    for i, item in enumerate(data):
        try:
            rec = FlightSeedRecord(
                origin=str(item["origin"]).upper(),
                destination=str(item["destination"]).upper(),
                carrier=str(item["carrier"]).upper(),
                cabin=str(item["cabin"]).upper(),
                outbound_date=str(item["outbound_date"]),
                return_date=str(item["return_date"]),
                price_usd=float(item["price_usd"]),
                outbound_duration_hours=float(item.get("outbound_duration_hours", 14.0)),
                return_duration_hours=float(item.get("return_duration_hours", 14.0)),
                outbound_stops=int(item.get("outbound_stops", 1)),
                return_stops=int(item.get("return_stops", 1)),
                outbound_routing=str(item.get("outbound_routing", "")),
                return_routing=str(item.get("return_routing", "")),
                source=str(item.get("source", "manual")),
                data_quality=str(item.get("data_quality", "estimated")),
            )
            records.append(rec)
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("JSON record %d skipped: %s", i, exc)

    logger.info("Loaded %d records from %s", len(records), path)
    return records


def run_seed_from_file(
    path: Path,
    dry_run: bool = False,
) -> dict:
    """
    Import historical seed observations from a CSV or JSON file.
    Applies routing constraints before writing any record.

    Returns summary dict with import statistics.
    """
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        records = load_from_csv(path)
    elif suffix == ".json":
        records = load_from_json(path)
    else:
        raise ValueError(f"Unsupported seed file format: {suffix!r} — use .csv or .json")

    stats = {
        "stage": "SEED_HISTORY",
        "source_file": str(path),
        "total_records": len(records),
        "imported": 0,
        "filtered_by_constraints": 0,
        "constraint_failures": [],
        "dry_run": dry_run,
    }

    for rec in records:
        passed, failures = _validate_record(rec)
        if not passed:
            stats["filtered_by_constraints"] += 1
            stats["constraint_failures"].append({
                "record": f"{rec.origin}→{rec.destination} {rec.carrier} {rec.cabin} {rec.outbound_date}",
                "failures": failures,
            })
            logger.debug(
                "Seed record filtered: %s→%s %s %s — %s",
                rec.origin, rec.destination, rec.carrier, rec.cabin, failures,
            )
            continue

        if dry_run:
            logger.info(
                "DRY RUN — would import: %s→%s %s %s %s $%.0f",
                rec.origin, rec.destination, rec.carrier, rec.cabin,
                rec.outbound_date, rec.price_usd,
            )
            stats["imported"] += 1
            continue

        append_observation(
            origin=rec.origin,
            destination=rec.destination,
            carrier=rec.carrier,
            cabin=rec.cabin,
            price_usd=rec.price_usd,
            outbound_date=rec.outbound_date,
            return_date=rec.return_date,
            outbound_duration_hours=rec.outbound_duration_hours,
            return_duration_hours=rec.return_duration_hours,
            outbound_stops=rec.outbound_stops,
            return_stops=rec.return_stops,
            outbound_routing=rec.outbound_routing or f"{rec.origin}-{rec.destination}",
            return_routing=rec.return_routing or f"{rec.destination}-{rec.origin}",
            source=rec.source,
            observation_type="historical_seed",
            data_quality=rec.data_quality,
        )
        stats["imported"] += 1
        logger.info(
            "Seeded: %s→%s %s %s %s $%.0f",
            rec.origin, rec.destination, rec.carrier, rec.cabin,
            rec.outbound_date, rec.price_usd,
        )

    logger.info(
        "SEED_HISTORY %s: %d/%d imported, %d filtered",
        "DRY_RUN" if dry_run else "complete",
        stats["imported"],
        stats["total_records"],
        stats["filtered_by_constraints"],
    )
    return stats


def run_seed_serpapi_historical(
    months_back: int = 3,
    dry_run: bool = False,
) -> dict:
    """
    Fetch historical prices via SerpApi for past departure dates within the
    CAI→USA corridor. Queries sample dates in each past month for all
    destination × cabin combinations.

    months_back: how many months of history to fetch (1–6 recommended)
    dry_run: log what would be fetched without writing

    Quota estimate: (12 destinations × 2 cabins × months_back × 2 sample dates)
    = ~48 × months_back searches. At 3 months: ~144 searches.
    """
    if not SERPAPI_KEY:
        return {
            "stage": "SEED_HISTORY",
            "source": "serpapi_historical",
            "error": "SERPAPI_KEY not configured — set it in .env",
            "imported": 0,
        }

    from datetime import date as date_cls
    from radar.sources.serpapi_source import SerpApiSource
    from radar.constraints import generate_search_combinations

    today = date_cls.today()
    combinations = generate_search_combinations()
    source = SerpApiSource()

    # Build sample dates: first and mid of each past month
    sample_dates: list[date_cls] = []
    for m in range(1, months_back + 1):
        # Approximate: first of month m months ago
        approx_start = today.replace(day=1)
        for _ in range(m):
            approx_start = (approx_start - timedelta(days=1)).replace(day=1)
        sample_dates.append(approx_start)
        sample_dates.append(approx_start.replace(day=15))

    stats = {
        "stage": "SEED_HISTORY",
        "source": "serpapi_historical",
        "months_back": months_back,
        "sample_dates": [d.isoformat() for d in sample_dates],
        "total_combinations": len(combinations),
        "imported": 0,
        "no_data": 0,
        "fetch_errors": [],
        "dry_run": dry_run,
    }

    import time, random as _random

    for combo in combinations:
        for dep_date in sample_dates:
            for nights in [9, 14]:
                ret_date = dep_date + timedelta(days=nights)

                if dry_run:
                    logger.info(
                        "DRY RUN — would fetch: %s→%s %s dep=%s ret=%s",
                        combo["origin"], combo["destination"], combo["cabin"],
                        dep_date, ret_date,
                    )
                    continue

                result = source.search(
                    origin=combo["origin"],
                    destination=combo["destination"],
                    cabin=combo["cabin"],
                    window_start=dep_date,
                    window_end=ret_date,
                    carriers=None,
                )
                stats["fetch_errors"].extend(result.errors)

                qualifying = [
                    o for o in result.offers
                    if apply_constraints(FlightItinerary(
                        origin=o.origin,
                        destination=o.destination,
                        cabin=o.cabin,
                        outbound_date=o.outbound_date,
                        return_date=o.return_date,
                        outbound_duration_hours=o.outbound_duration_hours,
                        return_duration_hours=o.return_duration_hours,
                        carrier=o.carrier,
                        price_usd=o.price_usd,
                    )).passed
                ]

                if not qualifying:
                    stats["no_data"] += 1
                    continue

                best = min(qualifying, key=lambda o: o.price_usd)
                append_observation(
                    origin=best.origin,
                    destination=best.destination,
                    carrier=best.carrier,
                    cabin=best.cabin,
                    price_usd=best.price_usd,
                    outbound_date=best.outbound_date.isoformat(),
                    return_date=best.return_date.isoformat(),
                    outbound_duration_hours=best.outbound_duration_hours,
                    return_duration_hours=best.return_duration_hours,
                    outbound_stops=best.outbound_stops,
                    return_stops=best.return_stops,
                    outbound_routing=best.outbound_routing,
                    return_routing=best.return_routing,
                    source="serpapi",
                    observation_type="historical_seed",
                    data_quality="confirmed",
                )
                stats["imported"] += 1
                logger.info(
                    "Historical seed: %s→%s %s %s %s $%.0f",
                    best.origin, best.destination, best.carrier, best.cabin,
                    best.outbound_date, best.price_usd,
                )

                time.sleep(_random.uniform(3.0, 8.0))

    logger.info(
        "SEED_HISTORY serpapi complete: %d imported, %d no_data, %d errors",
        stats["imported"], stats["no_data"], len(stats["fetch_errors"]),
    )
    return stats
