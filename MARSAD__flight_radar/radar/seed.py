"""
STAGE 0 — HISTORICAL PRICE SEED

Imports historical price observations from an external CSV file and stores
them as observation_type='historical_seed' in the schema store.

This accelerates the forecasting model from LOW confidence to MEDIUM (7 obs)
without waiting 7 days of daily monitoring. Particularly useful at first deploy
when you have manual price research from the past months.

═══════════════════════════════════════════════════════════════════════════════
HISTORICAL DATA SOURCES — RESEARCH SUMMARY (as of 2026-05)
═══════════════════════════════════════════════════════════════════════════════

(A) Google Flights price graph
    Depth:   3–6 months of price history visible in the browser calendar view
    Access:  Manual only — JavaScript canvas rendering, no public API
    Format:  Date → approximate price range, no carrier or cabin breakdown
    Use:     Capture prices manually for specific dates you're tracking
    Quality: data_quality='estimated' (aggregate, not fare-class specific)

(B) Kayak price history widget
    Depth:   ~3 months of fare calendar history
    Access:  Manual capture — ToS prohibits scraping
    Format:  Weekly price trend chart, lowest fare visible
    Use:     Supplement Google Flights with a second data point
    Quality: data_quality='estimated'

(C) Momondo / Skyscanner fare calendars
    Depth:   1–3 months, route-dependent
    Access:  Manual capture
    Quality: data_quality='estimated'

(D) Hopper app price history
    Depth:   Up to 12 months for frequently searched routes (CAI→JFK is likely cached)
    Access:  In-app screen capture — no export feature, no public API
    Format:  Weekly/monthly trend graph — read approximate values manually
    Quality: data_quality='estimated'

(E) Personal price research (RECOMMENDED SEED SOURCE)
    If you have tracked prices manually over the past months, enter them into
    the CSV template (python -m radar.main seed --template seed_template.csv)
    and import with: python -m radar.main seed --file my_prices.csv
    Quality: data_quality='confirmed' if from a real booking engine quote

PRACTICAL NOTE:
  The fastest path to MEDIUM confidence (7 observations = BUY_SIGNAL eligible)
  is 7 daily MONITOR runs. Historical seeding compresses the cold-start period
  when you have price data from the past 6 months. Without seed data, the
  first real BUY_SIGNAL fires on day 8 (after 7 daily observations).

═══════════════════════════════════════════════════════════════════════════════
CSV FORMAT
═══════════════════════════════════════════════════════════════════════════════

Required columns:
  outbound_date        YYYY-MM-DD departure from CAI
  return_date          YYYY-MM-DD return to CAI
  price_usd            Round-trip price in USD
  destination          IATA code (JFK, LAX, ORD, etc.)

Optional columns (defaults applied if missing):
  carrier              IATA code (default: UNKNOWN)
  cabin                BUSINESS or PREMIUM_ECONOMY (default: BUSINESS)
  outbound_duration_hours  (default: 14.0)
  return_duration_hours    (default: 14.0)
  outbound_stops       Number of stops (default: 1)
  return_stops         Number of stops (default: 1)
  outbound_routing     e.g. CAI-DXB-JFK (default: CAI-DEST)
  return_routing       e.g. JFK-DXB-CAI (default: DEST-CAI)
  data_quality         confirmed | estimated (default: estimated)
  price_egp            EGP equivalent — optional
  price_eur            EUR equivalent — optional

Generate a blank template: python -m radar.main seed --template seed_data.csv
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation, get_series

logger = logging.getLogger(__name__)

_REQUIRED_CSV_FIELDS = {"outbound_date", "return_date", "price_usd", "destination"}

_DEFAULTS: dict[str, str] = {
    "carrier": "UNKNOWN",
    "cabin": "BUSINESS",
    "outbound_duration_hours": "14.0",
    "return_duration_hours": "14.0",
    "outbound_stops": "1",
    "return_stops": "1",
    "outbound_routing": "",
    "return_routing": "",
    "data_quality": "estimated",
    "price_egp": "",
    "price_eur": "",
}

_TEMPLATE_HEADER = [
    "outbound_date", "return_date", "price_usd", "destination",
    "carrier", "cabin",
    "outbound_duration_hours", "return_duration_hours",
    "outbound_stops", "return_stops",
    "outbound_routing", "return_routing",
    "data_quality", "price_egp", "price_eur",
]

_TEMPLATE_EXAMPLE = [
    "2027-04-01", "2027-04-12", "2800.00", "JFK",
    "EK", "BUSINESS",
    "14.5", "15.0",
    "1", "1",
    "CAI-DXB-JFK", "JFK-DXB-CAI",
    "confirmed", "", "",
]


def import_from_csv(
    csv_path: Path,
    origin: str = "CAI",
    dry_run: bool = False,
) -> dict:
    """
    Import historical price observations from a CSV file.

    All rows pass through apply_constraints() before storage.
    Observations are stored with observation_type='historical_seed'.
    Duplicate detection: same outbound_date + destination + carrier + cabin.

    Returns summary dict with: rows_read, rows_imported, rows_filtered,
                                rows_duplicate, rows_error, filter_reasons.
    """
    stats: dict = {
        "stage": "SEED",
        "source": str(csv_path),
        "dry_run": dry_run,
        "rows_read": 0,
        "rows_imported": 0,
        "rows_filtered": 0,
        "rows_duplicate": 0,
        "rows_error": 0,
        "filter_reasons": [],
    }

    if not csv_path.exists():
        logger.error("Seed file not found: %s", csv_path)
        stats["error"] = f"File not found: {csv_path}"
        return stats

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    stats["rows_read"] = len(rows)
    logger.info("SEED: reading %d rows from %s", len(rows), csv_path)

    for i, row in enumerate(rows, start=1):
        try:
            outcome, reason = _import_row(row, origin, dry_run, i)
            if outcome == "imported":
                stats["rows_imported"] += 1
            elif outcome == "filtered":
                stats["rows_filtered"] += 1
                if reason:
                    stats["filter_reasons"].append(f"row {i}: {reason}")
            elif outcome == "duplicate":
                stats["rows_duplicate"] += 1
        except Exception as exc:
            stats["rows_error"] += 1
            logger.warning("SEED row %d unexpected error: %s", i, exc)

    logger.info(
        "SEED complete: %d read, %d imported, %d filtered, %d duplicate, %d errors",
        stats["rows_read"],
        stats["rows_imported"],
        stats["rows_filtered"],
        stats["rows_duplicate"],
        stats["rows_error"],
    )
    return stats


def _import_row(
    row: dict,
    origin: str,
    dry_run: bool,
    row_num: int,
) -> tuple[str, Optional[str]]:
    """
    Process one CSV row.
    Returns (outcome, reason) where outcome is 'imported' | 'filtered' | 'duplicate'.
    """
    # Apply defaults for missing/empty optional columns
    for field, default in _DEFAULTS.items():
        if not row.get(field, "").strip():
            row[field] = default

    # Parse required fields
    destination = row.get("destination", "").strip().upper()
    cabin = row.get("cabin", "BUSINESS").strip().upper()
    carrier = row.get("carrier", "UNKNOWN").strip().upper()

    price_str = row.get("price_usd", "").strip()
    try:
        price_usd = float(price_str)
        if price_usd <= 0:
            return "filtered", f"price_usd must be positive, got {price_str!r}"
    except ValueError:
        return "filtered", f"invalid price_usd={price_str!r}"

    outbound_str = row.get("outbound_date", "").strip()
    return_str = row.get("return_date", "").strip()
    try:
        outbound_date = date.fromisoformat(outbound_str)
        return_date = date.fromisoformat(return_str)
    except ValueError as exc:
        return "filtered", f"invalid date: {exc}"

    try:
        outbound_hours = float(row.get("outbound_duration_hours") or 14.0)
        return_hours = float(row.get("return_duration_hours") or 14.0)
        outbound_stops = int(row.get("outbound_stops") or 1)
        return_stops = int(row.get("return_stops") or 1)
    except (ValueError, TypeError):
        outbound_hours, return_hours = 14.0, 14.0
        outbound_stops, return_stops = 1, 1

    # Apply routing constraints — same engine used by all four pipeline stages
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
        reason = "; ".join(constraint.failures)
        logger.debug("SEED row %d filtered: %s", row_num, reason)
        return "filtered", reason

    # Duplicate check: same outbound_date + destination + carrier + cabin (seed obs only)
    existing = get_series(origin, destination, carrier, cabin)
    for obs in existing:
        if (
            obs.get("outbound_date") == outbound_str
            and obs.get("observation_type") == "historical_seed"
        ):
            logger.debug(
                "SEED row %d duplicate: %s→%s %s %s %s already seeded",
                row_num, origin, destination, carrier, cabin, outbound_str,
            )
            return "duplicate", None

    if dry_run:
        logger.info(
            "SEED DRY RUN row %d: %s→%s %s %s %s $%.0f",
            row_num, origin, destination, carrier, cabin, outbound_str, price_usd,
        )
        return "imported", None

    # Build routing strings
    routing_out = row.get("outbound_routing", "").strip() or f"{origin}-{destination}"
    routing_ret = row.get("return_routing", "").strip() or f"{destination}-{origin}"
    data_quality = row.get("data_quality", "estimated").strip()
    if data_quality not in ("confirmed", "estimated", "unavailable"):
        data_quality = "estimated"

    price_egp: Optional[float] = None
    price_eur: Optional[float] = None
    try:
        if row.get("price_egp", "").strip():
            price_egp = float(row["price_egp"])
    except ValueError:
        pass
    try:
        if row.get("price_eur", "").strip():
            price_eur = float(row["price_eur"])
    except ValueError:
        pass

    append_observation(
        origin=origin,
        destination=destination,
        carrier=carrier,
        cabin=cabin,
        price_usd=price_usd,
        outbound_date=outbound_str,
        return_date=return_str,
        outbound_duration_hours=outbound_hours,
        return_duration_hours=return_hours,
        outbound_stops=outbound_stops,
        return_stops=return_stops,
        outbound_routing=routing_out,
        return_routing=routing_ret,
        source="manual",
        observation_type="historical_seed",
        price_egp=price_egp,
        price_eur=price_eur,
        data_quality=data_quality,
    )
    logger.info(
        "SEED imported: %s→%s %s %s %s $%.0f",
        origin, destination, carrier, cabin, outbound_str, price_usd,
    )
    return "imported", None


def generate_seed_template(output_path: Path) -> None:
    """Write a CSV template with headers and one example row to output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_TEMPLATE_HEADER)
        writer.writerow(_TEMPLATE_EXAMPLE)
    logger.info("Seed template written to %s", output_path)


def seed_status() -> dict:
    """Return count of historical_seed observations per series that has any."""
    from radar.schema_store import get_all_series_keys, get_series

    result: dict = {}
    for k in get_all_series_keys():
        series = get_series(k["origin"], k["destination"], k["carrier"], k["cabin"])
        seed_count = sum(1 for obs in series if obs.get("observation_type") == "historical_seed")
        if seed_count:
            key = f"{k['origin']}-{k['destination']}/{k['carrier']}/{k['cabin']}"
            result[key] = {
                "seed_observations": seed_count,
                "total_observations": k["observation_count"],
            }
    return result
