"""
HISTORICAL PRICE SEED — Import historical price data into the MARSAD store.

Purpose: Accelerate forecasting model accuracy from day one by seeding the
time-series store with historical observations before the daily monitor has
accumulated 7+ days of data.

With 7+ historical observations injected, the store moves from LOW confidence
(cold-start, no BUY_SIGNAL) to MEDIUM confidence immediately on deployment.

── SOURCES FOR CAI-TO-USA HISTORICAL DATA ──────────────────────────────────────

1. Google Flights Price Calendar (manual export)
   Access:  flights.google.com → set CAI origin + USA destination + cabin
            → "Price graph" view → export/screenshot historical prices
   Depth:   ~12 months back (varies by route)
   Format:  Manual CSV preparation — see CSV_FORMAT below
   Method:  screenshot_to_csv.md (manual workflow, no programmatic access)
   Status:  MANUAL_WORKFLOW — no programmatic API available

2. SerpApi Google Flights price calendar endpoint
   Access:  serpapi.com/google-flights-api — price_calendar engine
   Depth:   Varies — generally 1–3 months back at most
   Format:  JSON via API
   Method:  _seed_from_serpapi_calendar() — implemented below
   Status:  IMPLEMENTED — requires SERPAPI_KEY

3. Kayak price history charts
   Access:  kayak.com → flight search → "Price History" chart
   Depth:   ~6–12 months historical (route-dependent)
   Format:  Manual CSV export
   Method:  Manual workflow → CSV import
   Status:  MANUAL_WORKFLOW

4. Hopper historical pricing
   Access:  hopper.com → watch a trip → historical price graph
   Depth:   ~2 years historical for popular routes
   Format:  Manual extraction only (no public API)
   Method:  Manual workflow → CSV import
   Status:  MANUAL_WORKFLOW (Hopper does not offer a public API)

── CSV FORMAT FOR MANUAL IMPORT ────────────────────────────────────────────────

Expected columns in the CSV file (header required):
  outbound_date,return_date,carrier,cabin,price_usd,
  outbound_duration_hours,return_duration_hours,
  outbound_stops,return_stops,outbound_routing,return_routing,source

Example row:
  2027-04-15,2027-04-26,EK,BUSINESS,3100.00,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI,historical_seed

source field options: hopper | kayak | google_flights | manual | historical_seed

── USAGE ────────────────────────────────────────────────────────────────────────

# Import from CSV file
python -m radar.main seed --csv data/historical_prices.csv

# Seed from SerpApi price calendar (fetches price history for 1 route)
python -m radar.main seed --serpapi --route CAI-JFK --cabin BUSINESS

# Preview without writing
python -m radar.main seed --csv data/historical_prices.csv --dry-run
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation
from radar.sources.base import FlightOffer, SourceResult

logger = logging.getLogger(__name__)

_REQUIRED_COLUMNS = {
    "outbound_date", "return_date", "carrier", "cabin", "price_usd",
    "outbound_duration_hours", "return_duration_hours",
    "outbound_stops", "return_stops", "outbound_routing", "return_routing",
}

_OPTIONAL_COLUMNS = {"source", "price_egp", "price_eur"}


def run_seed_from_csv(
    csv_path: Path,
    origin: str = "CAI",
    dry_run: bool = False,
) -> dict:
    """
    Import historical price observations from a CSV file.

    Applies all routing constraints before writing — invalid rows are logged
    and skipped, never written to the store.

    Returns summary dict with import statistics.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    stats = {
        "stage": "HISTORICAL_SEED",
        "source": str(csv_path),
        "total_rows": 0,
        "imported": 0,
        "skipped_constraint": 0,
        "skipped_error": 0,
        "dry_run": dry_run,
        "constraint_failures": [],
    }

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])

        missing = _REQUIRED_COLUMNS - headers
        if missing:
            raise ValueError(
                f"CSV missing required columns: {missing}. "
                f"See historical_seed.py CSV_FORMAT for expected headers."
            )

        for row_num, row in enumerate(reader, start=2):
            stats["total_rows"] += 1
            try:
                itin = _row_to_itinerary(row, origin)
            except (ValueError, KeyError) as exc:
                logger.warning("Row %d parse error: %s — skipping", row_num, exc)
                stats["skipped_error"] += 1
                continue

            constraint_result = apply_constraints(itin)
            if not constraint_result:
                logger.debug(
                    "Row %d constraint fail: %s — skipping",
                    row_num, constraint_result.failures,
                )
                stats["skipped_constraint"] += 1
                stats["constraint_failures"].extend(constraint_result.failures)
                continue

            if dry_run:
                logger.info(
                    "DRY RUN: would import %s→%s %s %s $%.0f (%s)",
                    itin.origin, itin.destination, itin.carrier, itin.cabin,
                    itin.price_usd, row.get("outbound_date"),
                )
                stats["imported"] += 1
                continue

            source = row.get("source", "historical_seed").strip() or "historical_seed"
            price_egp = _float_or_none(row.get("price_egp"))
            price_eur = _float_or_none(row.get("price_eur"))

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
                outbound_stops=int(row["outbound_stops"]),
                return_stops=int(row["return_stops"]),
                outbound_routing=row["outbound_routing"].strip(),
                return_routing=row["return_routing"].strip(),
                source=source,
                observation_type="historical_seed",
                price_egp=price_egp,
                price_eur=price_eur,
                data_quality="estimated",
            )
            stats["imported"] += 1
            logger.info(
                "Seeded: %s→%s %s %s $%.0f [%s]",
                itin.origin, itin.destination, itin.carrier, itin.cabin,
                itin.price_usd, itin.outbound_date,
            )

    logger.info(
        "HISTORICAL_SEED complete: %d/%d imported, %d constraint skips, %d parse errors",
        stats["imported"], stats["total_rows"],
        stats["skipped_constraint"], stats["skipped_error"],
    )
    return stats


def _row_to_itinerary(row: dict, origin: str) -> FlightItinerary:
    return FlightItinerary(
        origin=origin,
        destination=row["outbound_routing"].strip().split("-")[-1]
        if not row.get("destination")
        else row["destination"].strip().upper(),
        cabin=row["cabin"].strip().upper(),
        outbound_date=date.fromisoformat(row["outbound_date"].strip()),
        return_date=date.fromisoformat(row["return_date"].strip()),
        outbound_duration_hours=float(row["outbound_duration_hours"]),
        return_duration_hours=float(row["return_duration_hours"]),
        carrier=row["carrier"].strip().upper(),
        price_usd=float(row["price_usd"]),
    )


def _float_or_none(val: Optional[str]) -> Optional[float]:
    if not val or val.strip() == "":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def run_seed_from_serpapi_calendar(
    origin: str,
    destination: str,
    cabin: str,
    dry_run: bool = False,
) -> dict:
    """
    Fetch price calendar data from SerpApi Google Flights for historical seeding.

    Note: SerpApi price calendar shows prices for a range of dates but primarily
    for upcoming dates, not historical. This is most useful for building a rapid
    baseline across the travel window rather than for true historical depth.

    For genuine historical depth (6–24 months back), use the CSV import workflow
    with data manually gathered from Hopper or Kayak price history charts.
    """
    from radar.config import SERPAPI_KEY, WINDOW_START, WINDOW_END

    if not SERPAPI_KEY:
        return {
            "stage": "HISTORICAL_SEED",
            "source": "serpapi_calendar",
            "error": "SERPAPI_KEY not configured",
        }

    import requests

    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": WINDOW_START,
        "return_date": None,
        "travel_class": 3 if cabin.upper() == "BUSINESS" else 2,
        "type": 3,  # type=3 is the price calendar / flexible date view
        "adults": 1,
        "currency": "USD",
        "hl": "en",
        "api_key": SERPAPI_KEY,
        "show_hidden": 1,
    }
    params = {k: v for k, v in params.items() if v is not None}

    stats = {
        "stage": "HISTORICAL_SEED",
        "source": "serpapi_calendar",
        "route": f"{origin}-{destination}",
        "cabin": cabin,
        "imported": 0,
        "errors": [],
        "dry_run": dry_run,
    }

    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            stats["errors"].append(data["error"])
            return stats

        # Price calendar returns calendar_months with available prices per date
        calendar_months = data.get("calendar_months") or []
        for month in calendar_months:
            for week in month.get("weeks", []):
                for day_entry in week:
                    price = day_entry.get("price")
                    dep_date_str = day_entry.get("departure_date")
                    if not price or not dep_date_str:
                        continue

                    try:
                        dep_date = date.fromisoformat(dep_date_str)
                    except ValueError:
                        continue

                    # For each available departure date, probe 9 and 14-night returns
                    for nights in [9, 14]:
                        from datetime import timedelta
                        ret_date = dep_date + timedelta(days=nights)

                        itin = FlightItinerary(
                            origin=origin,
                            destination=destination,
                            cabin=cabin,
                            outbound_date=dep_date,
                            return_date=ret_date,
                            outbound_duration_hours=20.0,  # estimated — calendar doesn't provide duration
                            return_duration_hours=20.0,
                            carrier="??",
                            price_usd=float(price),
                        )

                        if not apply_constraints(itin):
                            continue

                        if dry_run:
                            logger.info(
                                "DRY RUN serpapi calendar: %s→%s %s $%.0f (%s)",
                                origin, destination, cabin, float(price), dep_date_str,
                            )
                            stats["imported"] += 1
                            continue

                        append_observation(
                            origin=origin,
                            destination=destination,
                            carrier="??",
                            cabin=cabin,
                            price_usd=float(price),
                            outbound_date=dep_date.isoformat(),
                            return_date=ret_date.isoformat(),
                            outbound_duration_hours=20.0,
                            return_duration_hours=20.0,
                            outbound_stops=1,
                            return_stops=1,
                            outbound_routing=f"{origin}-?-{destination}",
                            return_routing=f"{destination}-?-{origin}",
                            source="serpapi_calendar",
                            observation_type="historical_seed",
                            data_quality="estimated",
                        )
                        stats["imported"] += 1
                        break  # one entry per departure date is enough

    except requests.RequestException as exc:
        stats["errors"].append(str(exc))

    logger.info(
        "HISTORICAL_SEED (serpapi_calendar) complete: %d imported, %d errors",
        stats["imported"], len(stats["errors"]),
    )
    return stats
