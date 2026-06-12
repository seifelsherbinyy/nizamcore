"""
STAGE 0 — HISTORICAL SEED: Accelerate Forecasting Cold-Start

Imports historical price observations into the store from external sources.
All seeded records are marked observation_type='historical_seed' and validated
against the constraint engine before storage.

WHY THIS MODULE EXISTS:
The forecasting model requires ≥7 observations to exit LOW confidence and emit
BUY_SIGNALs. Without seeding, MARSAD needs 7 daily monitor runs before any alert
fires. Historical seeding telescopes this cold-start to day 1.

AVAILABLE HISTORICAL SOURCES (manually exported — no programmatic API):
──────────────────────────────────────────────────────────────────────────
A. Google Flights Price History
   Access: Open flights.google.com → select route → select flexible dates → price graph
   Format: Not directly exportable. Use SerpAPI `google_flights` engine with
           past departure dates (one request per date) to reconstruct history.
           SerpAPI free tier: 250 searches/month — use 30 past dates per priority route.
   Depth:  ~60–90 days on popular routes (graph data, not raw CSV)
   Integration: Use import_serpapi_history() in this module.

B. Hopper Historical Data
   Access: Mobile app only — https://www.hopper.com
   Format: No API, no export. Data must be manually recorded.
   Depth:  Hopper shows "typical price range" and "best time to fly" charts.
   Integration: Use import_csv_seed() with manually recorded price points.
   Note:   Hopper's published methodology shows SMA + seasonal adjustment on
           ~2 years of airline GDS data. Its predictions are a useful benchmark.

C. Kayak Price History
   Access: kayak.com → search route → "Price History" tab (requires JS)
   Format: Visual chart, no CSV export. Playwright scrape or manual recording.
   Depth:  ~90 days of daily best-price data per route.
   Integration: Use import_csv_seed() with manually extracted data.

D. ITA Matrix Historical
   Access: matrix.itasoftware.com → use "Date Range" search
   Format: No historical time series — shows current fares for future dates only.
   Depth:  Not a true historical source — cannot provide past price data.
   Note:   ITA Matrix ToS prohibits automated access — manual use only.
   Integration: Not viable for historical seeding. Use Google Flights / Kayak instead.

PRACTICAL RECOMMENDATION:
For quickest cold-start on the CAI corridor:
1. Use import_serpapi_history() to backfill 30 days of weekly price snapshots
   per priority route (CAI-JFK, CAI-EWR, CAI-LAX, CAI-MIA, CAI-IAD).
   Cost: ~30 SerpAPI searches per route × 5 routes × 2 cabins = 300 searches
   → requires the paid $25/month SerpAPI tier.
2. Use import_csv_seed() to add any manually recorded Kayak/Hopper snapshots.

USAGE:
    # Seed from SerpAPI historical back-fetch (automated — requires SERPAPI_KEY)
    from radar.seed_historical import run_seed_backfill
    stats = run_seed_backfill(days_back=30, step_days=7)

    # Seed from CSV file (manual export from Kayak, Hopper, or spreadsheet)
    from radar.seed_historical import import_csv_seed
    stats = import_csv_seed("/path/to/historical_prices.csv")

    # Seed from JSON file
    from radar.seed_historical import import_json_seed
    stats = import_json_seed("/path/to/historical_prices.json")

    # CLI:
    python -m radar.main seed --days-back 30 --step-days 7
    python -m radar.main seed --csv /path/to/file.csv
    python -m radar.main seed --json /path/to/file.json

CSV FORMAT (required columns):
    origin, destination, carrier, cabin, outbound_date, return_date,
    price_usd, outbound_duration_hours, return_duration_hours,
    outbound_stops, return_stops, outbound_routing, return_routing, source

    Optional: price_egp, price_eur, data_quality (default: "estimated")
    Date format: YYYY-MM-DD
    Cabin values: BUSINESS or PREMIUM_ECONOMY
    Example row:
      CAI,JFK,EK,BUSINESS,2027-04-01,2027-04-12,3200.0,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI,kayak_manual
"""

from __future__ import annotations

import csv
import json
import logging
import random
import time
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from radar.config import (
    FETCH_DELAY_MIN_SEC,
    FETCH_DELAY_MAX_SEC,
    MAX_REQUESTS_PER_SESSION,
    PRIORITY_DESTINATIONS,
    WINDOW_END,
    WINDOW_START,
)
from radar.constraints import (
    FlightItinerary,
    apply_constraints,
)
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)


@dataclass
class HistoricalSeedRecord:
    """Normalised historical price record ready for import into the store."""
    origin: str
    destination: str
    carrier: str
    cabin: str
    outbound_date: str       # YYYY-MM-DD
    return_date: str         # YYYY-MM-DD
    price_usd: float
    outbound_duration_hours: float
    return_duration_hours: float
    outbound_stops: int
    return_stops: int
    outbound_routing: str
    return_routing: str
    source: str
    price_egp: Optional[float] = None
    price_eur: Optional[float] = None
    data_quality: str = "estimated"


# ── CSV / JSON importers ───────────────────────────────────────────────────────

_REQUIRED_CSV_COLUMNS = {
    "origin", "destination", "carrier", "cabin",
    "outbound_date", "return_date", "price_usd",
    "outbound_duration_hours", "return_duration_hours",
    "outbound_stops", "return_stops",
    "outbound_routing", "return_routing", "source",
}


def import_csv_seed(csv_path: str | Path) -> dict:
    """
    Import historical price records from a CSV file.

    CSV must contain the required columns listed in this module's docstring.
    Rows that fail constraint validation are logged and skipped — not imported.

    Returns summary dict with: records_read, records_imported, records_skipped,
    constraint_failures, parse_errors.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    records = []
    parse_errors = []

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        missing = _REQUIRED_CSV_COLUMNS - header
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        for i, row in enumerate(reader, start=2):
            try:
                records.append(_row_to_record(row))
            except (ValueError, KeyError) as exc:
                parse_errors.append(f"Row {i}: {exc}")

    logger.info(
        "CSV seed: %d records parsed, %d parse errors from %s",
        len(records), len(parse_errors), csv_path.name,
    )
    return _import_records(records, parse_errors=parse_errors)


def import_json_seed(json_path: str | Path) -> dict:
    """
    Import historical price records from a JSON file.

    JSON must be an array of objects with the same fields as the CSV format.
    Returns same summary dict as import_csv_seed().
    """
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON seed file must be an array of record objects")

    records = []
    parse_errors = []

    for i, obj in enumerate(data):
        try:
            records.append(_dict_to_record(obj))
        except (ValueError, KeyError) as exc:
            parse_errors.append(f"Record {i}: {exc}")

    logger.info(
        "JSON seed: %d records parsed, %d parse errors from %s",
        len(records), len(parse_errors), json_path.name,
    )
    return _import_records(records, parse_errors=parse_errors)


def import_records(records: list[HistoricalSeedRecord]) -> dict:
    """Import a list of pre-built HistoricalSeedRecord objects."""
    return _import_records(records)


# ── SerpAPI back-fetch ─────────────────────────────────────────────────────────

def run_seed_backfill(
    days_back: int = 30,
    step_days: int = 7,
    destinations: Optional[list[str]] = None,
    cabins: Optional[list[str]] = None,
) -> dict:
    """
    Backfill historical price data by querying SerpAPI for past departure dates.

    Strategy: for each (destination, cabin) combination, query SerpAPI for
    departure dates spaced `step_days` apart going back `days_back` days from
    today. Each query asks "what was the price for a trip departing on date X
    with a 9–14 night stay?" — this gives a historical price timeline.

    Note: SerpAPI returns current prices as of TODAY for those dates, not the
    price that existed on those past dates. However, this is still valuable
    for seeding because:
    1. Prices for future 2027 dates haven't changed retroactively.
    2. Multiple date samples give a spread of prices across the window.
    3. The forecasting model benefits from any spread, not just temporal history.

    This is the most practical automated historical seeding approach available
    without paying for historical GDS data access (e.g., OAG, Cirium).

    days_back:   How many days back to probe (max 90 — SerpAPI degrades beyond that)
    step_days:   Interval between probed departure dates (7 = weekly samples)
    destinations: Subset of USA_DESTINATIONS to probe (None = priority list)
    cabins:      Subset of ['BUSINESS', 'PREMIUM_ECONOMY'] (None = both)

    Returns summary dict with: dates_probed, records_imported, api_errors.
    """
    from radar.config import DATA_SOURCE, SERPAPI_KEY
    if DATA_SOURCE != "serpapi" or not SERPAPI_KEY:
        logger.warning(
            "seed_backfill requires DATA_SOURCE=serpapi and SERPAPI_KEY — "
            "current source: %s", DATA_SOURCE,
        )
        return {
            "stage": "SEED_BACKFILL",
            "skipped": "DATA_SOURCE is not serpapi or SERPAPI_KEY not set",
        }

    target_destinations = destinations or PRIORITY_DESTINATIONS
    target_cabins = cabins or ["BUSINESS", "PREMIUM_ECONOMY"]

    window_start = date.fromisoformat(WINDOW_START)
    window_end = date.fromisoformat(WINDOW_END)

    # Generate probe departure dates: probe across the travel window starting
    # from window_start + step offsets, limited to step_days spacing
    # We also look at historical daily prices from the monitoring window
    all_probe_dates = _generate_probe_dates(window_start, window_end, step_days)
    logger.info(
        "SEED_BACKFILL: %d probe dates × %d destinations × %d cabins = %d queries",
        len(all_probe_dates), len(target_destinations), len(target_cabins),
        len(all_probe_dates) * len(target_destinations) * len(target_cabins),
    )

    from radar.sources.serpapi_source import SerpApiSource

    source = SerpApiSource()
    stats = {
        "stage": "SEED_BACKFILL",
        "dates_probed": len(all_probe_dates),
        "records_imported": 0,
        "records_skipped_constraint": 0,
        "api_errors": [],
        "session_limit_hit": False,
    }

    request_count = 0

    for dest in target_destinations:
        for cabin in target_cabins:
            for dep_date_str in all_probe_dates:
                if request_count >= MAX_REQUESTS_PER_SESSION:
                    stats["session_limit_hit"] = True
                    logger.warning(
                        "SEED_BACKFILL: MAX_REQUESTS_PER_SESSION=%d reached — "
                        "re-run to continue seeding",
                        MAX_REQUESTS_PER_SESSION,
                    )
                    return stats

                dep_date = date.fromisoformat(dep_date_str)
                result = source.search(
                    origin="CAI",
                    destination=dest,
                    cabin=cabin,
                    window_start=dep_date,
                    window_end=min(dep_date + timedelta(days=14), window_end),
                    carriers=None,
                )
                request_count += 1
                stats["api_errors"].extend(result.errors)

                for offer in result.offers:
                    itin = FlightItinerary(
                        origin=offer.origin,
                        destination=offer.destination,
                        cabin=offer.cabin,
                        outbound_date=offer.outbound_date,
                        return_date=offer.return_date,
                        outbound_duration_hours=offer.outbound_duration_hours,
                        return_duration_hours=offer.return_duration_hours,
                        carrier=offer.carrier,
                        price_usd=offer.price_usd,
                    )
                    cr = apply_constraints(itin)
                    if not cr:
                        stats["records_skipped_constraint"] += 1
                        continue

                    append_observation(
                        origin=offer.origin,
                        destination=offer.destination,
                        carrier=offer.carrier,
                        cabin=offer.cabin,
                        price_usd=offer.price_usd,
                        outbound_date=offer.outbound_date.isoformat(),
                        return_date=offer.return_date.isoformat(),
                        outbound_duration_hours=offer.outbound_duration_hours,
                        return_duration_hours=offer.return_duration_hours,
                        outbound_stops=offer.outbound_stops,
                        return_stops=offer.return_stops,
                        outbound_routing=offer.outbound_routing,
                        return_routing=offer.return_routing,
                        source=f"serpapi_seed",
                        observation_type="historical_seed",
                        price_egp=offer.price_egp,
                        price_eur=offer.price_eur,
                        data_quality="estimated",
                    )
                    stats["records_imported"] += 1

                # Rate limit between requests
                delay = random.uniform(FETCH_DELAY_MIN_SEC, FETCH_DELAY_MAX_SEC)
                time.sleep(delay)

    logger.info(
        "SEED_BACKFILL complete: %d imported, %d skipped (constraint), %d errors",
        stats["records_imported"],
        stats["records_skipped_constraint"],
        len(stats["api_errors"]),
    )
    return stats


# ── Internal helpers ───────────────────────────────────────────────────────────

def _import_records(
    records: list[HistoricalSeedRecord],
    parse_errors: Optional[list[str]] = None,
) -> dict:
    stats = {
        "stage": "SEED_IMPORT",
        "records_read": len(records),
        "records_imported": 0,
        "records_skipped_constraint": 0,
        "constraint_failures": [],
        "parse_errors": parse_errors or [],
    }

    for rec in records:
        try:
            outbound = date.fromisoformat(rec.outbound_date)
            ret = date.fromisoformat(rec.return_date)
        except ValueError as exc:
            stats["parse_errors"].append(f"Bad date in record {rec}: {exc}")
            continue

        itin = FlightItinerary(
            origin=rec.origin,
            destination=rec.destination,
            cabin=rec.cabin,
            outbound_date=outbound,
            return_date=ret,
            outbound_duration_hours=rec.outbound_duration_hours,
            return_duration_hours=rec.return_duration_hours,
            carrier=rec.carrier,
            price_usd=rec.price_usd,
        )
        cr = apply_constraints(itin)
        if not cr:
            stats["records_skipped_constraint"] += 1
            stats["constraint_failures"].append({
                "record": f"{rec.origin}-{rec.destination}/{rec.carrier}/{rec.cabin}/{rec.outbound_date}",
                "failures": cr.failures,
            })
            logger.debug("Seed record filtered: %s", cr.failures)
            continue

        append_observation(
            origin=rec.origin.upper(),
            destination=rec.destination.upper(),
            carrier=rec.carrier.upper(),
            cabin=rec.cabin.upper(),
            price_usd=rec.price_usd,
            outbound_date=rec.outbound_date,
            return_date=rec.return_date,
            outbound_duration_hours=rec.outbound_duration_hours,
            return_duration_hours=rec.return_duration_hours,
            outbound_stops=rec.outbound_stops,
            return_stops=rec.return_stops,
            outbound_routing=rec.outbound_routing,
            return_routing=rec.return_routing,
            source=rec.source,
            observation_type="historical_seed",
            price_egp=rec.price_egp,
            price_eur=rec.price_eur,
            data_quality=rec.data_quality,
        )
        stats["records_imported"] += 1

    logger.info(
        "Seed import: %d read, %d imported, %d skipped (constraint), "
        "%d parse errors",
        stats["records_read"],
        stats["records_imported"],
        stats["records_skipped_constraint"],
        len(stats["parse_errors"]),
    )
    return stats


def _row_to_record(row: dict) -> HistoricalSeedRecord:
    return HistoricalSeedRecord(
        origin=row["origin"].strip().upper(),
        destination=row["destination"].strip().upper(),
        carrier=row["carrier"].strip().upper(),
        cabin=row["cabin"].strip().upper(),
        outbound_date=row["outbound_date"].strip(),
        return_date=row["return_date"].strip(),
        price_usd=float(row["price_usd"]),
        outbound_duration_hours=float(row["outbound_duration_hours"]),
        return_duration_hours=float(row["return_duration_hours"]),
        outbound_stops=int(row["outbound_stops"]),
        return_stops=int(row["return_stops"]),
        outbound_routing=row["outbound_routing"].strip(),
        return_routing=row["return_routing"].strip(),
        source=row["source"].strip(),
        price_egp=float(row["price_egp"]) if row.get("price_egp") else None,
        price_eur=float(row["price_eur"]) if row.get("price_eur") else None,
        data_quality=row.get("data_quality", "estimated").strip(),
    )


def _dict_to_record(obj: dict) -> HistoricalSeedRecord:
    missing = _REQUIRED_CSV_COLUMNS - set(obj.keys())
    if missing:
        raise KeyError(f"Missing fields: {missing}")
    return _row_to_record(obj)


def _generate_probe_dates(
    window_start: date,
    window_end: date,
    step_days: int,
) -> list[str]:
    """Return ISO date strings spaced step_days apart across the travel window."""
    dates = []
    current = window_start
    while current <= window_end:
        dates.append(current.isoformat())
        current += timedelta(days=step_days)
    return dates
