"""
HISTORICAL PRICE SEED — Stage 0 (pre-baseline data import)

Accelerates forecasting model accuracy from day one by seeding the JSON schema
with historical price observations collected manually or from external sources.

Without seed data: forecasting stays in LOW confidence for 7 days after DISCOVER.
With seed data: HIGH confidence (30+ obs) is achievable from launch if historical
data is available for the route-carrier-cabin combinations being monitored.

─────────────────────────────────────────────────────────────────────────────
HISTORICAL SOURCES FOR CAI→USA — RESEARCH SUMMARY (2026-05-24)
─────────────────────────────────────────────────────────────────────────────

SOURCE A: Google Flights Price History (flights.google.com)
  Depth:    ~12 months visible in the "Price history" panel per route/date
  Access:   Manual — no API. Visible in the UI when clicking a specific
            flight on Google Flights. Playwright can extract the chart data
            from the JS context (window.__qs__ or XHR to googleflights.com).
  Format:   Price per month chart (not daily). Useful for seasonal baseline.
  Integrate: Import as observation_type='historical_seed', source='google_flights_history'
  Limitation: Monthly granularity only. No carrier breakdown per historical point.

SOURCE B: Hopper (hopper.com — app-only)
  Depth:    ~6 months historical displayed in-app, up to 12 with premium
  Access:   App-only, no public API. Hopper's price predictions use a
            proprietary model (published methodology: negative binomial
            regression on GDS data). Not programmatically accessible.
  Format:   Daily low price per route with "buy now / wait" recommendation.
  Integrate: Manual export not available. Useful for benchmarking BUY_SIGNAL
             threshold calibration against Hopper's published buy windows.
  Limitation: Cannot be automated — app only, no export.

SOURCE C: Kayak Price History (kayak.com/flights/...)
  Depth:    ~12 months. Accessible via the "Price History" tab on route pages.
  Access:   Semi-programmatic. Kayak's price history API endpoint:
            GET https://www.kayak.com/s/horizon/flights/calendar/...
            The endpoint is discoverable via browser DevTools XHR inspection.
            Returns JSON with monthly price ranges. Rate limit: ~5 req/min.
  Format:   Monthly min/max/avg price. No carrier breakdown.
  Integrate: Import as observation_type='historical_seed', source='kayak_history'
  Limitation: Monthly granularity. TOS: automated access requires review.

SOURCE D: ITA Matrix Historical Search (matrix.itasoftware.com)
  Depth:    Can search past dates — returns cached GDS fares (±2 weeks).
  Access:   Playwright browser automation. ToS prohibits without written
            permission. Use ONLY after ToS review.
  Format:   Full fare breakdown, carrier, routing, exact price.
            Best historical fidelity of all sources.
  Integrate: Use ITAMatrixSource (ITA_MATRIX_ENABLED=true) with past departure dates.

SOURCE E: Serpapi Google Flights API — historical dates
  Depth:    Can be queried with past departure dates. SerpApi charges per query.
  Access:   Same API as daily monitoring (SERPAPI_KEY required).
            Query with past departure dates in the same format.
  Format:   Full flight offer with price, routing, carrier.
  Integrate: Directly compatible with existing schema — same parser as MONITOR.
  Recommendation: This is the easiest programmatic historical seed source.
                  Run SEED with past departure dates to build a 30-day history
                  quickly. Cost: ~$0.025 per query on paid tier.

─────────────────────────────────────────────────────────────────────────────
RECOMMENDED SEED STRATEGY FOR MARSAD
─────────────────────────────────────────────────────────────────────────────

Option 1 (fastest to HIGH confidence): SerpApi historical query
  - Query each (destination, cabin) combo for ~30 past departure dates
  - Each query costs 1 SerpApi credit — 24 combos × 30 dates = 720 queries
  - At paid tier ($25/mo for 1,000 queries): fits in monthly budget with headroom
  - Unlocks HIGH confidence forecasting immediately on day 1

Option 2 (free): Manual Kayak/Google Flights price history export
  - Collect monthly price data manually via browser
  - Use `python -m radar.main seed --from-csv <file>` to import
  - Achieves MEDIUM confidence (7+ obs) with ~7 monthly observations per route

Option 3 (highest fidelity): ITA Matrix with ToS clearance
  - Use ITAMatrixSource with past dates after obtaining written permission
  - Provides exact fares with routing and carrier breakdown

─────────────────────────────────────────────────────────────────────────────
CSV IMPORT FORMAT
─────────────────────────────────────────────────────────────────────────────

To import historical data from a manually-collected CSV:

  Required columns:
    origin, destination, carrier, cabin, outbound_date, return_date,
    price_usd, outbound_duration_hours, return_duration_hours,
    outbound_stops, return_stops, outbound_routing, return_routing, source

  Optional columns:
    price_egp, price_eur, data_quality

  Example row:
    CAI,JFK,EK,BUSINESS,2027-04-01,2027-04-12,3200.0,14.5,15.0,1,1,
    CAI-DXB-JFK,JFK-DXB-CAI,manual_kayak_export

  All rows are validated against the routing constraint engine before import.
  Rows failing constraints are logged and skipped — schema integrity preserved.

Usage:
  python -m radar.main seed --from-csv /path/to/historical_prices.csv
  python -m radar.main seed --backfill-days 30   # query SerpApi for past 30 days
  python -m radar.main seed --dry-run            # validate CSV without writing
"""

from __future__ import annotations

import csv
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from radar.constraints import apply_constraints, FlightItinerary
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)

_REQUIRED_COLS = {
    "origin", "destination", "carrier", "cabin",
    "outbound_date", "return_date", "price_usd",
    "outbound_duration_hours", "return_duration_hours",
    "outbound_stops", "return_stops",
    "outbound_routing", "return_routing", "source",
}


def run_seed_from_csv(
    csv_path: Path,
    dry_run: bool = False,
) -> dict:
    """
    Import historical price observations from a CSV file into the schema store.

    All rows are validated against the routing constraint engine before import.
    Observation type is set to 'historical_seed' for all imported records.

    Returns summary dict with import statistics.
    """
    if not csv_path.exists():
        logger.error("CSV file not found: %s", csv_path)
        return {"stage": "SEED", "error": f"File not found: {csv_path}"}

    stats = {
        "stage": "SEED",
        "source_file": str(csv_path),
        "dry_run": dry_run,
        "rows_read": 0,
        "rows_imported": 0,
        "rows_skipped_constraint": 0,
        "rows_skipped_parse_error": 0,
        "errors": [],
    }

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        missing_cols = _REQUIRED_COLS - set(reader.fieldnames or [])
        if missing_cols:
            msg = f"CSV missing required columns: {missing_cols}"
            logger.error(msg)
            return {"stage": "SEED", "error": msg}

        for i, row in enumerate(reader, start=1):
            stats["rows_read"] += 1
            try:
                itin = _row_to_itinerary(row)
            except (ValueError, KeyError) as exc:
                stats["rows_skipped_parse_error"] += 1
                stats["errors"].append(f"Row {i}: parse error — {exc}")
                continue

            result = apply_constraints(itin)
            if not result:
                stats["rows_skipped_constraint"] += 1
                logger.debug("Row %d skipped: %s", i, result.failures)
                continue

            if not dry_run:
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
                    outbound_stops=int(row.get("outbound_stops", 0)),
                    return_stops=int(row.get("return_stops", 0)),
                    outbound_routing=row.get("outbound_routing", ""),
                    return_routing=row.get("return_routing", ""),
                    source=row.get("source", "historical_seed"),
                    observation_type="historical_seed",
                    price_egp=_optional_float(row.get("price_egp")),
                    price_eur=_optional_float(row.get("price_eur")),
                    data_quality=row.get("data_quality", "historical_import"),
                )
            stats["rows_imported"] += 1

    logger.info(
        "SEED%s: %d/%d rows imported, %d constraint failures, %d parse errors",
        " [DRY RUN]" if dry_run else "",
        stats["rows_imported"],
        stats["rows_read"],
        stats["rows_skipped_constraint"],
        stats["rows_skipped_parse_error"],
    )
    return stats


def run_seed_backfill(
    days: int = 30,
    dry_run: bool = False,
) -> dict:
    """
    Backfill historical data by querying the configured data source for past
    departure dates within the travel window. Uses the same source as MONITOR.

    Each past departure date probed = 1 API request per (destination, cabin).
    For 12 destinations × 2 cabins × 30 dates = 720 total API requests.

    days: number of days back from today to probe (capped at travel window start)

    ASSUMPTION: Travel window departure dates are used even if they're in the
    past relative to today — the source may return cached/estimated fares.
    SerpApi returns historical data for past dates on some routes.
    """
    from radar.config import ALL_CARRIERS, WINDOW_START, WINDOW_END
    from radar.constraints import generate_search_combinations
    from radar.fetcher import fetch_best_price

    today = date.today()
    window_start = date.fromisoformat(WINDOW_START)
    window_end = date.fromisoformat(WINDOW_END)

    # Build list of probe dates: today back `days` days, capped at window_start
    probe_dates: list[date] = []
    for d in range(1, days + 1):
        probe_date = today - timedelta(days=d)
        if probe_date < window_start:
            break
        if probe_date <= window_end:
            probe_dates.append(probe_date)

    if not probe_dates:
        logger.info(
            "SEED backfill: no probe dates in travel window "
            "(window starts %s, today - %d days = %s)",
            WINDOW_START, days, today - timedelta(days=days),
        )
        return {
            "stage": "SEED",
            "skipped": "no_dates_in_window",
            "travel_window_start": WINDOW_START,
            "days_back": days,
        }

    combos = generate_search_combinations()
    stats = {
        "stage": "SEED",
        "mode": "backfill",
        "dry_run": dry_run,
        "probe_dates": len(probe_dates),
        "combinations": len(combos),
        "total_queries": len(probe_dates) * len(combos),
        "observations_written": 0,
        "no_data_count": 0,
        "fetch_errors": [],
    }

    logger.info(
        "SEED backfill: %d probe dates × %d combos = %d queries",
        len(probe_dates), len(combos), stats["total_queries"],
    )

    if dry_run:
        logger.info("SEED [DRY RUN]: no queries will be made")
        return stats

    for dep_date in probe_dates:
        # return date: probe at window_start + 11 nights (mid-range)
        ret_date = dep_date + timedelta(days=11)
        if ret_date > window_end:
            ret_date = dep_date + timedelta(days=9)
        if ret_date > window_end:
            logger.debug("Skipping %s — no valid return date in window", dep_date)
            continue

        for combo in combos:
            best, errors = fetch_best_price(
                origin=combo["origin"],
                destination=combo["destination"],
                cabin=combo["cabin"],
                window_start=dep_date,
                window_end=dep_date,  # single date
                carriers=ALL_CARRIERS,
            )
            stats["fetch_errors"].extend(errors)

            if best is None:
                stats["no_data_count"] += 1
                continue

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
                source=best.source,
                observation_type="historical_seed",
                data_quality="backfill",
            )
            stats["observations_written"] += 1

    logger.info(
        "SEED backfill complete: %d written, %d no data, %d errors",
        stats["observations_written"],
        stats["no_data_count"],
        len(stats["fetch_errors"]),
    )
    return stats


def _row_to_itinerary(row: dict) -> FlightItinerary:
    return FlightItinerary(
        origin=row["origin"].strip().upper(),
        destination=row["destination"].strip().upper(),
        cabin=row["cabin"].strip().upper(),
        carrier=row["carrier"].strip().upper(),
        outbound_date=date.fromisoformat(row["outbound_date"].strip()),
        return_date=date.fromisoformat(row["return_date"].strip()),
        outbound_duration_hours=float(row["outbound_duration_hours"]),
        return_duration_hours=float(row["return_duration_hours"]),
        price_usd=float(row["price_usd"]),
    )


def _optional_float(val: Optional[str]) -> Optional[float]:
    if val is None or val.strip() == "":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def print_seed_research() -> None:
    """Print the historical source research summary to console."""
    print(__doc__)
