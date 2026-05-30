"""
HISTORICAL PRICE SEED — Stage 0 (pre-DISCOVER)

Accelerates forecasting model accuracy from day one by loading historical
price observations into the schema store before the daily monitor accumulates
enough data for MEDIUM confidence (7+ observations).

Without seed data: 7-day cold-start before any BUY_SIGNAL is possible.
With seed data: forecasting is immediately meaningful.

HISTORICAL DATA SOURCES — CAI → USA corridor, past 24 months:

  SOURCE A — SerpApi Google Flights Price Calendar
    Mechanism: SerpApi `google_flights` engine with price calendar mode
    API param: type=3 (date picker / price calendar) in SerpApi
    Depth: ~12 months of price calendar data (varies by route)
    Format: JSON price calendar returned per route per cabin
    Access: Requires SERPAPI_KEY — same key as daily monitor
    Programmatic: Yes — run `seed --source serpapi` to fetch and import
    Limitation: Price calendar shows cheapest fare per day, not cabin-specific

  SOURCE B — Google Flights Price History (Manual Export)
    Mechanism: Google Flights "Price History" chart (visible in browser)
    Depth: ~3 months of historical prices shown in UI
    Format: Manual export via screenshot or copy-paste; paste into CSV
    Access: Free — no API key required
    Programmatic: No — requires manual data collection
    Import method: Use `seed --source csv --file historical.csv`

  SOURCE C — Kayak Price History Charts
    Mechanism: Kayak "Price Forecast" feature shows 90-day price history
    Depth: ~90 days visible in chart
    Format: Manual export only; CSV required
    Access: Free browser access
    Programmatic: No — scraping prohibited; use manual export
    Import method: Use `seed --source csv --file historical.csv`

  SOURCE D — Hopper Historical Price Data
    Mechanism: Hopper app shows historical fare trends per route
    Depth: ~12 months displayed in app
    Format: Manual export only
    Access: Free app download required
    Programmatic: No official API; internal API scraping is ToS-prohibited
    Import method: Use `seed --source csv --file historical.csv`

  SOURCE E — Google Flights Price Calendar via SerpApi (Price Range Search)
    API endpoint: serpapi.com/search?engine=google_flights&type=1
    Add param: outbound_dates=YYYY-MM-DD:YYYY-MM-DD (range)
    Depth: Forward-looking only (not historical) — use for upcoming dates
    Best use: Seed the full travel window before DISCOVER baseline run

RECOMMENDED SEED STRATEGY:
  Day 0: Run `seed --source serpapi` to fetch price calendar across travel window
  Day 0: Manually check Google Flights and enter ±5 data points per key route in CSV
  Day 1+: Daily MONITOR accumulates observations; forecasting confidence improves

CSV FORMAT for manual seed data:
  origin,destination,carrier,cabin,outbound_date,return_date,price_usd,source_note
  CAI,JFK,EK,BUSINESS,2027-03-15,2027-03-26,3200,google_flights_manual
  CAI,JFK,QR,BUSINESS,2027-04-01,2027-04-12,2950,kayak_manual
  ...
  Required: origin,destination,carrier,cabin,outbound_date,return_date,price_usd
  Optional: source_note (defaults to 'manual_seed')

Usage:
  python -m radar.historical_seed --source serpapi        # Fetch from SerpApi price calendar
  python -m radar.historical_seed --source csv --file data/seed.csv
  python -m radar.historical_seed --dry-run               # Preview imports without writing
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from radar.config import (
    SERPAPI_KEY,
    WINDOW_END,
    WINDOW_START,
    USA_DESTINATIONS,
    CABINS,
)
from radar.constraints import apply_constraints, FlightItinerary
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)

_DEFAULT_SEED_DURATION_HOURS = 16.0  # conservative estimate for unknown routing
_DEFAULT_STOPS = 1


def seed_from_csv(csv_path: Path, dry_run: bool = False) -> dict:
    """
    Import historical price observations from a CSV file.

    Expected columns (order-independent, header row required):
      origin, destination, carrier, cabin, outbound_date, return_date, price_usd
    Optional columns:
      source_note, outbound_duration_hours, return_duration_hours,
      outbound_stops, return_stops, outbound_routing, return_routing

    Applies full routing constraints before importing.
    Returns import statistics dict.
    """
    if not csv_path.exists():
        logger.error("CSV file not found: %s", csv_path)
        return {"error": f"File not found: {csv_path}"}

    stats = {
        "source": f"csv:{csv_path.name}",
        "rows_read": 0,
        "rows_imported": 0,
        "rows_failed_constraint": 0,
        "rows_skipped_error": 0,
        "observations_written": 0,
        "dry_run": dry_run,
    }

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["rows_read"] += 1
            try:
                result = _import_row(row, dry_run=dry_run)
                if result == "ok":
                    stats["rows_imported"] += 1
                    stats["observations_written"] += 1
                elif result == "filtered":
                    stats["rows_failed_constraint"] += 1
                else:
                    stats["rows_skipped_error"] += 1
            except Exception as exc:
                logger.warning("Row %d error: %s — %s", stats["rows_read"], exc, row)
                stats["rows_skipped_error"] += 1

    logger.info(
        "CSV seed complete: %d read, %d imported, %d filtered, %d errors",
        stats["rows_read"], stats["rows_imported"],
        stats["rows_failed_constraint"], stats["rows_skipped_error"],
    )
    return stats


def _import_row(row: dict, dry_run: bool = False) -> str:
    """
    Validate and import a single CSV row as a historical_seed observation.
    Returns 'ok', 'filtered', or 'error'.
    """
    required = ("origin", "destination", "carrier", "cabin", "outbound_date", "return_date", "price_usd")
    for field in required:
        if field not in row or not row[field].strip():
            logger.warning("Missing required field %r — skipping row", field)
            return "error"

    try:
        outbound_date = date.fromisoformat(row["outbound_date"].strip())
        return_date = date.fromisoformat(row["return_date"].strip())
        price_usd = float(row["price_usd"].strip())
    except ValueError as exc:
        logger.warning("Parse error: %s — skipping row", exc)
        return "error"

    # Apply routing constraints before storing
    itin = FlightItinerary(
        origin=row["origin"].strip().upper(),
        destination=row["destination"].strip().upper(),
        cabin=row["cabin"].strip().upper(),
        outbound_date=outbound_date,
        return_date=return_date,
        outbound_duration_hours=float(row.get("outbound_duration_hours") or _DEFAULT_SEED_DURATION_HOURS),
        return_duration_hours=float(row.get("return_duration_hours") or _DEFAULT_SEED_DURATION_HOURS),
        carrier=row["carrier"].strip().upper(),
        price_usd=price_usd,
    )

    constraint_result = apply_constraints(itin)
    if not constraint_result:
        logger.debug("Constraint filter: %s", constraint_result.failures)
        return "filtered"

    if dry_run:
        logger.info(
            "DRY RUN — would import: %s→%s %s %s $%.0f (%s→%s)",
            itin.origin, itin.destination, itin.carrier, itin.cabin,
            itin.price_usd, itin.outbound_date, itin.return_date,
        )
        return "ok"

    append_observation(
        origin=itin.origin,
        destination=itin.destination,
        carrier=itin.carrier,
        cabin=itin.cabin,
        price_usd=itin.price_usd,
        outbound_date=itin.outbound_date.isoformat(),
        return_date=itin.return_date.isoformat(),
        outbound_duration_hours=itin.outbound_duration_hours,
        return_duration_hours=itin.return_duration_hours,
        outbound_stops=int(row.get("outbound_stops") or _DEFAULT_STOPS),
        return_stops=int(row.get("return_stops") or _DEFAULT_STOPS),
        outbound_routing=row.get("outbound_routing") or f"{itin.origin}-{itin.destination}",
        return_routing=row.get("return_routing") or f"{itin.destination}-{itin.origin}",
        source=f"historical_seed/{row.get('source_note', 'manual').strip()}",
        observation_type="historical_seed",
        data_quality="seed",
    )
    logger.info(
        "Seeded: %s→%s %s %s $%.0f (%s→%s)",
        itin.origin, itin.destination, itin.carrier, itin.cabin,
        itin.price_usd, itin.outbound_date, itin.return_date,
    )
    return "ok"


def seed_from_serpapi_calendar(dry_run: bool = False) -> dict:
    """
    Fetch price calendar data from SerpApi for all destination × cabin combinations
    across the travel window. Stores each day's best price as a historical_seed observation.

    This provides immediate price data across the travel window without waiting for
    7 days of daily monitor observations.

    Rate limit: one request per combination per 8–15 seconds.
    Expected volume: 12 destinations × 2 cabins = 24 requests.
    """
    import random
    import time
    import requests

    if not SERPAPI_KEY:
        return {
            "error": "SERPAPI_KEY not configured — set it in .env",
            "source": "serpapi_calendar",
        }

    stats = {
        "source": "serpapi_calendar",
        "combinations_attempted": 0,
        "observations_written": 0,
        "combinations_no_data": 0,
        "fetch_errors": [],
        "dry_run": dry_run,
    }

    window_start = date.fromisoformat(WINDOW_START)
    window_end = date.fromisoformat(WINDOW_END)

    _CABIN_CLASS_MAP = {"BUSINESS": 3, "PREMIUM_ECONOMY": 2}

    for dest in USA_DESTINATIONS:
        for cabin in CABINS:
            stats["combinations_attempted"] += 1
            travel_class = _CABIN_CLASS_MAP[cabin]

            # Sample dates from across the travel window
            # Google Flights calendar returns prices for the month around the departure date
            sample_dates = _evenly_spaced_dates(window_start, window_end, n=4)

            for dep_date in sample_dates:
                ret_date = dep_date + timedelta(days=11)  # 11-night midpoint
                if ret_date > window_end:
                    ret_date = window_end

                params = {
                    "engine": "google_flights",
                    "departure_id": "CAI",
                    "arrival_id": dest,
                    "outbound_date": dep_date.isoformat(),
                    "return_date": ret_date.isoformat(),
                    "travel_class": travel_class,
                    "type": 1,
                    "adults": 1,
                    "currency": "USD",
                    "hl": "en",
                    "api_key": SERPAPI_KEY,
                }

                logger.info("Seeding calendar: CAI→%s %s %s", dest, cabin, dep_date)

                if dry_run:
                    logger.info("DRY RUN — would fetch %s", params)
                    stats["observations_written"] += 1
                    time.sleep(0.1)
                    continue

                for attempt in range(3):
                    try:
                        resp = requests.get(
                            "https://serpapi.com/search",
                            params=params,
                            timeout=30,
                        )
                        if resp.status_code == 429:
                            backoff = 2 ** (attempt + 1)
                            logger.warning("Rate limited — backing off %ds", backoff)
                            time.sleep(backoff)
                            continue
                        resp.raise_for_status()
                        data = resp.json()
                        if "error" in data:
                            stats["fetch_errors"].append(f"CAI→{dest} {cabin}: {data['error']}")
                            break

                        # Extract best price from response
                        best_price = None
                        carrier = "??"
                        outbound_dur = 16.0
                        for group in (data.get("best_flights") or [], data.get("other_flights") or []):
                            if not isinstance(group, list):
                                group = [group]
                            for item in group:
                                p = item.get("price")
                                if p and (best_price is None or p < best_price):
                                    best_price = float(p)
                                    flights = item.get("flights", [])
                                    if flights:
                                        carrier_name = flights[0].get("airline", "??")
                                        carrier = _name_to_iata(carrier_name) or carrier_name[:2].upper()
                                    dur = item.get("total_duration", 0)
                                    outbound_dur = round(dur / 60, 2) if dur else 16.0

                        if best_price is None:
                            stats["combinations_no_data"] += 1
                            break

                        nights = (ret_date - dep_date).days
                        itin = FlightItinerary(
                            origin="CAI", destination=dest, cabin=cabin,
                            outbound_date=dep_date, return_date=ret_date,
                            outbound_duration_hours=outbound_dur,
                            return_duration_hours=outbound_dur * 0.85,  # estimate
                            carrier=carrier, price_usd=best_price,
                        )
                        if apply_constraints(itin):
                            append_observation(
                                origin="CAI", destination=dest,
                                carrier=carrier, cabin=cabin,
                                price_usd=best_price,
                                outbound_date=dep_date.isoformat(),
                                return_date=ret_date.isoformat(),
                                outbound_duration_hours=outbound_dur,
                                return_duration_hours=round(outbound_dur * 0.85, 2),
                                outbound_stops=1,
                                return_stops=1,
                                outbound_routing=f"CAI-{dest}",
                                return_routing=f"{dest}-CAI",
                                source="historical_seed/serpapi_calendar",
                                observation_type="historical_seed",
                                data_quality="seed",
                            )
                            stats["observations_written"] += 1
                        break

                    except Exception as exc:
                        stats["fetch_errors"].append(f"CAI→{dest} {cabin}: {exc}")
                        break

                # Rate limit between requests
                delay = random.uniform(8, 15)
                time.sleep(delay)

    logger.info(
        "SerpApi calendar seed complete: %d combinations, %d observations, %d no data, %d errors",
        stats["combinations_attempted"], stats["observations_written"],
        stats["combinations_no_data"], len(stats["fetch_errors"]),
    )
    return stats


def _evenly_spaced_dates(start: date, end: date, n: int) -> list[date]:
    total = (end - start).days
    if total <= 0:
        return [start]
    step = max(7, total // (n + 1))
    dates = [start + timedelta(days=step * (i + 1)) for i in range(n)]
    return [d for d in dates if d <= end]


def _name_to_iata(name: str) -> Optional[str]:
    _MAP = {
        "egyptair": "MS", "emirates": "EK", "qatar airways": "QR",
        "air france": "AF", "british airways": "BA", "lufthansa": "LH",
        "delta": "DL", "turkish airlines": "TK", "united airlines": "UA",
        "united": "UA", "american airlines": "AA", "klm": "KL",
        "etihad airways": "EY", "etihad": "EY",
    }
    return _MAP.get(name.lower().strip())


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        prog="python -m radar.historical_seed",
        description="MARSAD Historical Price Seed — import observations before cold start",
    )
    parser.add_argument(
        "--source",
        choices=["csv", "serpapi"],
        required=True,
        help="Data source: csv (manual CSV file) or serpapi (price calendar fetch)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Path to CSV file (required when --source csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview imports without writing to store",
    )

    args = parser.parse_args()

    if args.source == "csv":
        if not args.file:
            print("ERROR: --file is required when --source csv", file=sys.stderr)
            return 1
        stats = seed_from_csv(args.file, dry_run=args.dry_run)
    else:
        stats = seed_from_serpapi_calendar(dry_run=args.dry_run)

    print(f"\nSeed result: {stats}")
    return 0 if "error" not in stats else 1


if __name__ == "__main__":
    sys.exit(main())
