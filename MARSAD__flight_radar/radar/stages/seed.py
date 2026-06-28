"""
HISTORICAL PRICE SEED: Import past observations to accelerate cold-start.

WHY: The forecasting model needs ≥ 7 observations for MEDIUM confidence and
≥ 30 for HIGH. Daily monitoring accumulates these over time, but we can
jumpstart accuracy by seeding with manually-collected historical data.

SOURCES for CAI→USA historical price data:
  A. Google Flights Explore (flights.google.com/explore)
     - Shows 12-month price calendar per route, per cabin
     - Access: manual — click through route, screenshot or note prices
     - Depth: up to 12 months back
     - Format: manual CSV entry using the template below
     - Integration: run `python -m radar.main seed --file data/seed.csv`

  B. Hopper (mobile app)
     - Shows 12-month historical price chart per route
     - Access: manual — screenshot + note prices per month
     - Depth: 12 months back
     - Format: manual CSV entry
     - Integration: same as A

  C. Kayak Price History (kayak.com — flight results → "Price History" tab)
     - Shows ~6–12 month chart for specific routes
     - Access: manual screenshot per route
     - Depth: 6–12 months
     - Format: manual CSV entry
     - Integration: same as A

  D. ITA Matrix historical search (requires ToS review)
     - Allows searching historical dates — results accessible via Playwright
     - Access: programmatic (but bot-detection risk)
     - Depth: up to 11 months back
     - Format: parsed from page results

RECOMMENDATION: Use Google Flights Explore (A) as the fastest manual source.
For each of the 12 USA destinations × 2 cabins, open the price calendar,
note the cheapest Business/Premium Economy price for each month (up to 12
months back), and enter into the CSV template.

CSV TEMPLATE: data/seed_template.csv
  Columns: origin,destination,carrier,cabin,price_usd,outbound_date,
           return_date,outbound_duration_hours,return_duration_hours,
           outbound_stops,return_stops,outbound_routing,return_routing,source

  Example row:
  CAI,JFK,EK,BUSINESS,3200.00,2027-04-01,2027-04-12,14.5,15.0,1,1,
  CAI-DXB-JFK,JFK-DXB-CAI,google_flights_manual

IMPORTANT: Seed observations go through the routing constraint engine.
Any row that fails constraints (wrong cabin, duration out of range, etc.)
is logged and skipped — the schema is never corrupted by invalid seed data.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)

# Fields required in CSV/JSON seed input
_REQUIRED_CSV_FIELDS = {
    "origin", "destination", "carrier", "cabin", "price_usd",
    "outbound_date", "return_date",
}

# Fields optional in CSV/JSON seed input — defaults applied when missing
_OPTIONAL_CSV_DEFAULTS = {
    "outbound_duration_hours": 15.0,
    "return_duration_hours": 15.0,
    "outbound_stops": 1,
    "return_stops": 1,
    "outbound_routing": "",
    "return_routing": "",
    "source": "historical_seed_manual",
}

# Written as a CSV to data/ on first run if it doesn't exist
SEED_TEMPLATE_CONTENT = (
    "origin,destination,carrier,cabin,price_usd,outbound_date,return_date,"
    "outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,"
    "outbound_routing,return_routing,source\n"
    "CAI,JFK,EK,BUSINESS,3200.00,2027-04-01,2027-04-12,14.5,15.0,1,1,"
    "CAI-DXB-JFK,JFK-DXB-CAI,google_flights_manual\n"
    "CAI,JFK,QR,PREMIUM_ECONOMY,1450.00,2027-04-01,2027-04-12,17.5,18.0,1,1,"
    "CAI-DOH-JFK,JFK-DOH-CAI,google_flights_manual\n"
)


def _parse_date(s: str) -> date:
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def _row_to_itin(row: dict) -> tuple[Optional[FlightItinerary], Optional[str]]:
    """Convert a parsed row dict to a FlightItinerary. Returns (itin, error)."""
    missing = _REQUIRED_CSV_FIELDS - set(row)
    if missing:
        return None, f"missing required fields: {missing}"

    try:
        outbound_date = _parse_date(row["outbound_date"])
        return_date = _parse_date(row["return_date"])
        price_usd = float(row["price_usd"])
        out_dur = float(row.get("outbound_duration_hours", _OPTIONAL_CSV_DEFAULTS["outbound_duration_hours"]))
        ret_dur = float(row.get("return_duration_hours", _OPTIONAL_CSV_DEFAULTS["return_duration_hours"]))
    except (ValueError, TypeError) as exc:
        return None, f"parse error: {exc}"

    itin = FlightItinerary(
        origin=row["origin"].strip().upper(),
        destination=row["destination"].strip().upper(),
        cabin=row["cabin"].strip().upper(),
        carrier=row["carrier"].strip().upper(),
        outbound_date=outbound_date,
        return_date=return_date,
        outbound_duration_hours=out_dur,
        return_duration_hours=ret_dur,
        price_usd=price_usd,
    )
    return itin, None


def _load_csv(path: Path) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def _load_json(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "observations" in data:
        return data["observations"]
    raise ValueError("JSON seed file must be a list of observation dicts")


def _write_seed_template(dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(SEED_TEMPLATE_CONTENT, encoding="utf-8")
    logger.info("Seed template written to %s", dest)


def run_seed(
    seed_file: Optional[Path] = None,
    write_template: bool = False,
    template_dest: Optional[Path] = None,
    dry_run: bool = False,
) -> dict:
    """
    Import historical price observations from a CSV or JSON seed file.

    seed_file: Path to CSV or JSON file with historical observations.
    write_template: If True, write a CSV template to template_dest (or data/seed_template.csv).
    dry_run: Validate and log without writing to the schema store.

    Returns summary dict with import statistics.

    CLI: python -m radar.main seed --file data/seed.csv
         python -m radar.main seed --write-template
    """
    from radar.config import DATA_DIR

    stats = {
        "stage": "SEED",
        "dry_run": dry_run,
        "rows_read": 0,
        "rows_imported": 0,
        "rows_constraint_failed": 0,
        "rows_parse_error": 0,
        "constraint_failures": [],
    }

    if write_template:
        dest = template_dest or (DATA_DIR / "seed_template.csv")
        _write_seed_template(dest)
        stats["template_written"] = str(dest)
        logger.info("Seed template written — fill in historical prices and re-run with --file")
        return stats

    if seed_file is None:
        logger.error("SEED: --file required (or use --write-template to create a template)")
        return stats

    if not seed_file.exists():
        logger.error("SEED: file not found: %s", seed_file)
        return stats

    # Load rows
    suffix = seed_file.suffix.lower()
    try:
        if suffix == ".csv":
            rows = _load_csv(seed_file)
        elif suffix == ".json":
            rows = _load_json(seed_file)
        else:
            logger.error("SEED: unsupported format %r — use .csv or .json", suffix)
            return stats
    except Exception as exc:
        logger.error("SEED: failed to load %s: %s", seed_file, exc)
        return stats

    stats["rows_read"] = len(rows)
    logger.info("SEED: %d rows loaded from %s", len(rows), seed_file)

    for i, row in enumerate(rows, 1):
        itin, parse_error = _row_to_itin(row)

        if parse_error:
            stats["rows_parse_error"] += 1
            logger.warning("SEED row %d: parse error — %s", i, parse_error)
            continue

        constraint_result = apply_constraints(itin)
        if not constraint_result:
            stats["rows_constraint_failed"] += 1
            detail = f"row {i}: {constraint_result.failures}"
            stats["constraint_failures"].append(detail)
            logger.warning("SEED %s", detail)
            continue

        if dry_run:
            logger.info(
                "SEED DRY_RUN row %d: %s→%s %s %s $%.0f ✓",
                i, itin.origin, itin.destination, itin.carrier, itin.cabin, itin.price_usd,
            )
            stats["rows_imported"] += 1
            continue

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
            outbound_stops=int(row.get("outbound_stops", _OPTIONAL_CSV_DEFAULTS["outbound_stops"])),
            return_stops=int(row.get("return_stops", _OPTIONAL_CSV_DEFAULTS["return_stops"])),
            outbound_routing=str(row.get("outbound_routing", _OPTIONAL_CSV_DEFAULTS["outbound_routing"])),
            return_routing=str(row.get("return_routing", _OPTIONAL_CSV_DEFAULTS["return_routing"])),
            source=str(row.get("source", _OPTIONAL_CSV_DEFAULTS["source"])),
            observation_type="historical_seed",
        )
        stats["rows_imported"] += 1
        logger.info(
            "SEED imported row %d: %s→%s %s %s $%.0f",
            i, itin.origin, itin.destination, itin.carrier, itin.cabin, itin.price_usd,
        )

    logger.info(
        "SEED complete: %d read, %d imported, %d constraint failures, %d parse errors",
        stats["rows_read"],
        stats["rows_imported"],
        stats["rows_constraint_failed"],
        stats["rows_parse_error"],
    )
    return stats
