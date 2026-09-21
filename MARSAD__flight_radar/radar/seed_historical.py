"""
MARSAD — Historical Price Seed Module

Purpose: import manually-compiled or third-party historical price data to warm-start
the forecasting model from day one, bypassing the 7-day cold-start period.

Without seed data, forecasting confidence is LOW for the first 7 daily monitor runs.
With 7+ seed observations, the model is alert-eligible immediately on deployment.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HISTORICAL DATA SOURCE RESEARCH — CAI → USA CORRIDOR, 24-MONTH LOOKBACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOURCE 1: Google Flights Price History (via SerpApi price_history engine)
  Accessibility:   PROGRAMMATIC — SerpApi exposes Google Flights price calendar
  Depth:           1–3 months backward (not 24 months)
  Format:          JSON via SerpApi /search?engine=google_flights_price_chart
  Cabin support:   Yes — travel_class parameter (2=PE, 3=Business)
  CAI coverage:    Yes — Cairo International Airport is indexed
  Integration:     Call SerpApi with historical outbound_date values; price calendar
                   shows price trend over ~2 month window around the search date.
                   Each data point = one seed observation.
  Limitation:      Not a true 24-month lookback — probing past dates returns
                   "no flights available" (booking windows have already closed).
                   Google Flights price history chart (the visual one) is not
                   accessible via SerpApi's structured API — only the calendar grid
                   (±3 months around a search date) is available.
  STATUS:          PARTIAL — use for near-term baseline (1–3 months pre-deploy).

SOURCE 2: Hopper Historical Price Data
  Accessibility:   NO PROGRAMMATIC ACCESS — Hopper does not expose a public API
                   for historical price data.
  Depth:           Hopper shows price history charts in-app (up to 12 months)
  Format:          Manual screenshot / web scrape (unstable)
  CAI coverage:    Cairo routes have limited Hopper coverage vs. Western hubs
  Integration:     MANUAL ONLY — compile price series by hand from Hopper app
                   and import via the seed CSV format defined below.
  Limitation:      Business and Premium Economy data is sparse on Hopper for
                   CAI-origin routes. The price history chart in Hopper typically
                   shows economy fares; premium cabin prices are less reliable.
  STATUS:          MANUAL_ONLY — use for rough Economy reference, not primary.

SOURCE 3: Kayak Price History Charts
  Accessibility:   LIMITED — Kayak price history (the "Price Forecast" chart) is
                   rendered client-side via JS. No stable API endpoint.
  Depth:           Up to 6 months backward on some routes
  Format:          Manual extraction or Playwright scrape (fragile)
  CAI coverage:    Moderate — Kayak indexes major CAI routes
  Integration:     Manual extraction → seed CSV. Playwright scrape is possible
                   but violates Kayak ToS on automated access.
  Limitation:      Cabin-class breakdown in Kayak's price history is Economy-only;
                   Business and Premium Economy history is not shown separately.
  STATUS:          MANUAL_ONLY — cabin-class breakdown not available.

SOURCE 4: ITA Matrix Historical Search
  Accessibility:   NO HISTORICAL ACCESS — ITA Matrix only returns current
                   and future fares; it does not expose historical price data.
  Depth:           Current + future only
  STATUS:          NOT_APPLICABLE for historical seeding.

SOURCE 5: Airline Revenue Management Systems (GDS — Sabre, Amadeus)
  Accessibility:   ENTERPRISE ONLY — requires GDS subscription
  Depth:           Multi-year historical fare data
  Format:          Structured via GDS API
  Limitation:      Not available for personal/self-service use
  STATUS:          NOT_APPLICABLE for personal monitoring pipeline.

SOURCE 6: Manual Compilation (RECOMMENDED)
  Accessibility:   ALWAYS AVAILABLE
  Method:          Visit Google Flights, manually search historical departure dates
                   within the 2027 window and record the prices shown. Google Flights
                   shows prices for future dates even before the booking opens fully —
                   use this to build a 5–10 observation seed set in a single session.
  Best approach:   Search CAI → destination for 3–5 departure dates spread across
                   the travel window (March–September 2027). Record the Business and
                   Premium Economy prices in the seed CSV. This takes ~30 minutes
                   per destination but yields HIGH-quality ground-truth seed data.
  STATUS:          RECOMMENDED_PRIMARY for warm-start seeding.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEED CSV FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Required columns (CSV header must match exactly):
  origin,destination,carrier,cabin,price_usd,outbound_date,return_date,
  outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,
  outbound_routing,return_routing,source

Optional columns (included if available, otherwise leave blank):
  price_egp,price_eur

Notes:
  - cabin values: BUSINESS or PREMIUM_ECONOMY (case-insensitive)
  - outbound_date / return_date: ISO 8601 (YYYY-MM-DD)
  - duration_hours: decimal hours, e.g. 14.5 (not "14h30m")
  - routing: airport codes joined by hyphens, e.g. CAI-DXB-JFK
  - source: free text, e.g. "google_flights_manual", "kayak_manual"

Example row:
  CAI,JFK,EK,BUSINESS,3200.00,2027-04-01,2027-04-12,14.5,15.0,1,1,
  CAI-DXB-JFK,JFK-DXB-CAI,google_flights_manual,,

Usage:
  python -m radar.main seed --file data/seed_prices.csv
  python -m radar.main seed --file data/seed_prices.json
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation, mark_premium_economy_unavailable

logger = logging.getLogger(__name__)


_REQUIRED_FIELDS = {
    "origin", "destination", "carrier", "cabin", "price_usd",
    "outbound_date", "return_date", "outbound_duration_hours",
    "return_duration_hours", "outbound_stops", "return_stops",
    "outbound_routing", "return_routing", "source",
}


def _parse_record(row: dict, row_num: int) -> Optional[dict]:
    """Validate and normalise a single seed record. Returns None on error."""
    missing = _REQUIRED_FIELDS - set(k for k, v in row.items() if v)
    if missing:
        logger.warning("Row %d: missing required fields %s — skipped", row_num, missing)
        return None

    try:
        record = {
            "origin": str(row["origin"]).strip().upper(),
            "destination": str(row["destination"]).strip().upper(),
            "carrier": str(row["carrier"]).strip().upper(),
            "cabin": str(row["cabin"]).strip().upper(),
            "price_usd": float(row["price_usd"]),
            "outbound_date": date.fromisoformat(str(row["outbound_date"]).strip()),
            "return_date": date.fromisoformat(str(row["return_date"]).strip()),
            "outbound_duration_hours": float(row["outbound_duration_hours"]),
            "return_duration_hours": float(row["return_duration_hours"]),
            "outbound_stops": int(row["outbound_stops"]),
            "return_stops": int(row["return_stops"]),
            "outbound_routing": str(row["outbound_routing"]).strip(),
            "return_routing": str(row["return_routing"]).strip(),
            "source": str(row["source"]).strip(),
            "price_egp": float(row["price_egp"]) if row.get("price_egp") else None,
            "price_eur": float(row["price_eur"]) if row.get("price_eur") else None,
        }
    except (ValueError, KeyError) as exc:
        logger.warning("Row %d: parse error %s — skipped", row_num, exc)
        return None

    # Validate against routing constraints
    itin = FlightItinerary(
        origin=record["origin"],
        destination=record["destination"],
        cabin=record["cabin"],
        outbound_date=record["outbound_date"],
        return_date=record["return_date"],
        outbound_duration_hours=record["outbound_duration_hours"],
        return_duration_hours=record["return_duration_hours"],
        carrier=record["carrier"],
        price_usd=record["price_usd"],
    )
    result = apply_constraints(itin)
    if not result:
        logger.warning("Row %d: constraint failures %s — skipped", row_num, result.failures)
        return None

    return record


def load_seed_csv(path: Path) -> list[dict]:
    """Load seed records from a CSV file. Returns validated records only."""
    records = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # row 1 is header
            cleaned = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()}
            record = _parse_record(cleaned, i)
            if record:
                records.append(record)
    return records


def load_seed_json(path: Path) -> list[dict]:
    """Load seed records from a JSON array file. Returns validated records only."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Seed JSON must be an array of objects")

    records = []
    for i, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            logger.warning("Entry %d: not an object — skipped", i)
            continue
        record = _parse_record(row, i)
        if record:
            records.append(record)
    return records


def run_seed(file_path: str, dry_run: bool = False) -> dict:
    """
    Import historical seed observations from a CSV or JSON file.

    Each valid record is appended to the schema store with observation_type='historical_seed'.
    Constraint engine is applied to every record — invalid records are logged and skipped.

    Returns summary dict with import statistics.
    """
    path = Path(file_path)
    if not path.exists():
        return {
            "stage": "SEED",
            "error": f"File not found: {path}",
            "records_loaded": 0,
            "records_imported": 0,
        }

    suffix = path.suffix.lower()
    if suffix == ".csv":
        records = load_seed_csv(path)
    elif suffix == ".json":
        records = load_seed_json(path)
    else:
        return {
            "stage": "SEED",
            "error": f"Unsupported file format: {suffix!r} — use .csv or .json",
            "records_loaded": 0,
            "records_imported": 0,
        }

    stats = {
        "stage": "SEED",
        "file": str(path),
        "dry_run": dry_run,
        "records_loaded": len(records),
        "records_imported": 0,
        "records_skipped": 0,
        "pe_unavailable_noted": [],
    }

    logger.info(
        "SEED: %d valid records from %s (dry_run=%s)",
        len(records), path.name, dry_run,
    )

    for rec in records:
        if dry_run:
            logger.info(
                "SEED [DRY RUN]: would import %s→%s %s %s $%.0f on %s",
                rec["origin"], rec["destination"], rec["carrier"],
                rec["cabin"], rec["price_usd"], rec["outbound_date"],
            )
            stats["records_imported"] += 1
            continue

        try:
            obs_id = append_observation(
                origin=rec["origin"],
                destination=rec["destination"],
                carrier=rec["carrier"],
                cabin=rec["cabin"],
                price_usd=rec["price_usd"],
                outbound_date=rec["outbound_date"].isoformat(),
                return_date=rec["return_date"].isoformat(),
                outbound_duration_hours=rec["outbound_duration_hours"],
                return_duration_hours=rec["return_duration_hours"],
                outbound_stops=rec["outbound_stops"],
                return_stops=rec["return_stops"],
                outbound_routing=rec["outbound_routing"],
                return_routing=rec["return_routing"],
                source=rec["source"],
                observation_type="historical_seed",
                price_egp=rec.get("price_egp"),
                price_eur=rec.get("price_eur"),
            )
            stats["records_imported"] += 1
            logger.info(
                "SEED: imported %s→%s %s %s $%.0f [%s]",
                rec["origin"], rec["destination"], rec["carrier"],
                rec["cabin"], rec["price_usd"], obs_id[:8],
            )
        except Exception as exc:
            logger.error("SEED: failed to import record %s: %s", rec, exc)
            stats["records_skipped"] += 1

    stats["records_skipped"] += stats["records_loaded"] - stats["records_imported"]

    logger.info(
        "SEED complete: %d imported, %d skipped (dry_run=%s)",
        stats["records_imported"], stats["records_skipped"], dry_run,
    )
    return stats


def generate_seed_template(output_path: str = "data/seed_template.csv") -> str:
    """Write an empty seed CSV template with the correct headers to output_path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "origin", "destination", "carrier", "cabin", "price_usd",
        "outbound_date", "return_date", "outbound_duration_hours",
        "return_duration_hours", "outbound_stops", "return_stops",
        "outbound_routing", "return_routing", "source", "price_egp", "price_eur",
    ]
    example = {
        "origin": "CAI",
        "destination": "JFK",
        "carrier": "EK",
        "cabin": "BUSINESS",
        "price_usd": "3200.00",
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "outbound_duration_hours": "14.5",
        "return_duration_hours": "15.0",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
        "source": "google_flights_manual",
        "price_egp": "",
        "price_eur": "",
    }

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerow(example)

    logger.info("Seed template written to %s", path)
    return str(path)
