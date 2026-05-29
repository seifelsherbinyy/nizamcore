"""
HISTORICAL PRICE SEED IMPORTER

Imports historical flight price observations from a CSV file into the schema store.
Imported observations are tagged observation_type='historical_seed' and immediately
expand the time series so the forecasting model exits LOW confidence faster.

--- Historical data sources (as of 2026-05-29) ---

Google Flights price history
  - Available via: google.com/flights → select route → "Price history" chart
  - Depth: ~3–6 months of daily price points for future departure dates
  - Access: manual screenshot + transcription, OR SerpApi google_flights_chart endpoint
    (SERPAPI_KEY required; endpoint: engine=google_flights_chart)
  - Format: date + price pairs — no cabin breakdown on chart
  - Limitation: chart shows lowest Economy fare by default; Business/PE requires
    cabin filter applied before viewing history chart
  - Integration: use the export_template CSV, populate manually or via SerpApi

Kayak price history charts
  - Available via: kayak.com → search route → "Price Trend" tab
  - Depth: ~6 months historical + 3 months forecast
  - Access: manual only (no programmatic API — scraping violates ToS)
  - Limitation: aggregated across all cabins unless filtered
  - Integration: manual transcription into export_template CSV

Hopper historical price data
  - Available via: hopper.com mobile app → "Watch trip" → price history
  - Depth: ~12 months for popular routes
  - Access: manual (no public API; institutional API requires partnership)
  - Limitation: EgyptAir and some Middle East routes have sparse coverage
  - Integration: manual transcription into export_template CSV

Google Flights SerpApi historical chart endpoint
  - SERPAPI_KEY required
  - endpoint: engine=google_flights_chart, departure_id, arrival_id, type
  - Depth: typically 12 months of low-fare history
  - Access: programmatic via SerpApi (paid tier: $25/month for 1000 calls)
  - Limitation: returns Economy fares only — no Business/PE breakdown
  - Integration: ASSUMED_PASS_PENDING_ENVIRONMENT — SerpApi chart endpoint may not
    support cabin class filtering; verify before using as primary seed source

--- Template CSV format ---

Use `python -m radar.main seed-csv --export-template template.csv` to generate
a pre-filled template. Minimum required columns:

  carrier,cabin,outbound_date,return_date,price_usd,
  outbound_duration_hours,return_duration_hours,
  outbound_stops,return_stops,outbound_routing,return_routing,source_name

Optional columns: price_egp,price_eur

--- Usage ---

  python -m radar.main seed-csv --file /path/to/history.csv [--dry-run]

--- Status ---

PROTOTYPE_GRADE: CSV parsing and store import are EXECUTED_IN_SESSION (tested).
SerpApi chart endpoint integration is ASSUMED_PASS_PENDING_ENVIRONMENT.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)


# CSV template header — exported by --export-template flag
_TEMPLATE_HEADER = [
    "carrier", "cabin", "outbound_date", "return_date",
    "price_usd", "outbound_duration_hours", "return_duration_hours",
    "outbound_stops", "return_stops", "outbound_routing", "return_routing",
    "source_name", "price_egp", "price_eur",
]

# Columns that must be present (price_egp and price_eur are optional)
_REQUIRED_COLUMNS = {
    "carrier", "cabin", "outbound_date", "return_date",
    "price_usd", "outbound_duration_hours", "return_duration_hours",
    "outbound_stops", "return_stops", "outbound_routing", "return_routing",
    "source_name",
}

_EXAMPLE_ROWS = [
    {
        "carrier": "EK",
        "cabin": "BUSINESS",
        "outbound_date": "2027-04-01",
        "return_date": "2027-04-12",
        "price_usd": "3100.00",
        "outbound_duration_hours": "14.5",
        "return_duration_hours": "15.0",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DXB-JFK",
        "return_routing": "JFK-DXB-CAI",
        "source_name": "google_flights",
        "price_egp": "",
        "price_eur": "",
    },
    {
        "carrier": "QR",
        "cabin": "PREMIUM_ECONOMY",
        "outbound_date": "2027-05-15",
        "return_date": "2027-05-26",
        "price_usd": "1850.00",
        "outbound_duration_hours": "18.0",
        "return_duration_hours": "17.5",
        "outbound_stops": "1",
        "return_stops": "1",
        "outbound_routing": "CAI-DOH-LAX",
        "return_routing": "LAX-DOH-CAI",
        "source_name": "kayak",
        "price_egp": "",
        "price_eur": "",
    },
]


def export_template(output_path: Optional[Path] = None) -> str:
    """
    Write a template CSV with header + two example rows.
    Returns the CSV content as a string. Also writes to output_path if provided.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_TEMPLATE_HEADER)
    writer.writeheader()
    for row in _EXAMPLE_ROWS:
        writer.writerow(row)

    content = buf.getvalue()

    if output_path is not None:
        output_path.write_text(content, encoding="utf-8")
        logger.info("Template written to %s", output_path)

    return content


def _parse_row(row: dict, row_num: int) -> tuple[Optional[FlightItinerary], dict, list[str]]:
    """
    Parse and validate a single CSV row.
    Returns (FlightItinerary, enriched_row, errors).
    enriched_row is filled with typed values needed for append_observation.
    errors is empty on success.
    """
    errors: list[str] = []

    # Check required columns present
    missing = _REQUIRED_COLUMNS - set(row.keys())
    if missing:
        return None, {}, [f"row {row_num}: missing columns {missing}"]

    # Parse numeric fields
    try:
        price_usd = float(row["price_usd"])
    except ValueError:
        errors.append(f"row {row_num}: price_usd={row['price_usd']!r} is not a valid number")

    try:
        outbound_hours = float(row["outbound_duration_hours"])
        return_hours = float(row["return_duration_hours"])
    except ValueError:
        errors.append(f"row {row_num}: duration fields must be numbers")

    try:
        outbound_stops = int(row["outbound_stops"])
        return_stops = int(row["return_stops"])
    except ValueError:
        errors.append(f"row {row_num}: stop count fields must be integers")

    # Parse dates
    try:
        outbound_date = date.fromisoformat(row["outbound_date"])
        return_date = date.fromisoformat(row["return_date"])
    except ValueError:
        errors.append(f"row {row_num}: dates must be ISO 8601 (YYYY-MM-DD)")

    if errors:
        return None, {}, errors

    # Optional currency conversions
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

    itin = FlightItinerary(
        origin="CAI",
        destination=row["carrier"].upper()[:3],   # placeholder — destination extracted from routing
        cabin=row["cabin"].upper(),
        outbound_date=outbound_date,
        return_date=return_date,
        outbound_duration_hours=outbound_hours,
        return_duration_hours=return_hours,
        carrier=row["carrier"].upper(),
        price_usd=price_usd,
    )

    # Extract destination from outbound_routing (last airport code in CAI-X-Y-DEST)
    routing = row.get("outbound_routing", "").strip()
    if routing:
        parts = [p.strip() for p in routing.split("-") if p.strip()]
        if parts:
            itin = FlightItinerary(
                origin="CAI",
                destination=parts[-1],
                cabin=row["cabin"].upper(),
                outbound_date=outbound_date,
                return_date=return_date,
                outbound_duration_hours=outbound_hours,
                return_duration_hours=return_hours,
                carrier=row["carrier"].upper(),
                price_usd=price_usd,
            )

    enriched = {
        "carrier": row["carrier"].upper(),
        "cabin": row["cabin"].upper(),
        "destination": itin.destination,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "price_usd": price_usd,
        "outbound_duration_hours": outbound_hours,
        "return_duration_hours": return_hours,
        "outbound_stops": outbound_stops,
        "return_stops": return_stops,
        "outbound_routing": routing,
        "return_routing": row.get("return_routing", "").strip(),
        "source_name": row.get("source_name", "historical_seed").strip() or "historical_seed",
        "price_egp": price_egp,
        "price_eur": price_eur,
    }

    return itin, enriched, []


def run_seed_csv(
    csv_path: Path,
    dry_run: bool = False,
) -> dict:
    """
    Import historical price observations from a CSV file.

    Each row is validated through the routing constraint engine before storage.
    Observations are stored with observation_type='historical_seed'.
    The origin field is always forced to 'CAI' (MARSAD is CAI-origin only).

    Returns a stats dict:
      rows_read, rows_imported, rows_rejected, rejection_reasons, baseline_accelerated
    """
    if not csv_path.exists():
        return {
            "stage": "SEED",
            "error": f"CSV file not found: {csv_path}",
            "rows_read": 0,
            "rows_imported": 0,
            "rows_rejected": 0,
        }

    stats: dict = {
        "stage": "SEED",
        "csv_path": str(csv_path),
        "dry_run": dry_run,
        "rows_read": 0,
        "rows_imported": 0,
        "rows_rejected": 0,
        "rejection_reasons": [],
        "observation_ids": [],
    }

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # row 1 is header
            stats["rows_read"] += 1

            itin, enriched, parse_errors = _parse_row(row, row_num)

            if parse_errors:
                stats["rows_rejected"] += 1
                stats["rejection_reasons"].extend(parse_errors)
                logger.warning("Seed row %d parse error: %s", row_num, parse_errors)
                continue

            # Run constraint engine
            constraint_result = apply_constraints(itin)
            if not constraint_result:
                stats["rows_rejected"] += 1
                reason = f"row {row_num}: constraint failed — {constraint_result.failures}"
                stats["rejection_reasons"].append(reason)
                logger.debug("Seed row %d rejected: %s", row_num, constraint_result.failures)
                continue

            if dry_run:
                stats["rows_imported"] += 1
                logger.info(
                    "DRY_RUN: would import %s→%s %s %s $%.0f",
                    "CAI", enriched["destination"], enriched["carrier"],
                    enriched["cabin"], enriched["price_usd"],
                )
                continue

            observation_id = append_observation(
                origin="CAI",
                destination=enriched["destination"],
                carrier=enriched["carrier"],
                cabin=enriched["cabin"],
                price_usd=enriched["price_usd"],
                outbound_date=enriched["outbound_date"].isoformat(),
                return_date=enriched["return_date"].isoformat(),
                outbound_duration_hours=enriched["outbound_duration_hours"],
                return_duration_hours=enriched["return_duration_hours"],
                outbound_stops=enriched["outbound_stops"],
                return_stops=enriched["return_stops"],
                outbound_routing=enriched["outbound_routing"],
                return_routing=enriched["return_routing"],
                source=enriched["source_name"],
                observation_type="historical_seed",
                price_egp=enriched["price_egp"],
                price_eur=enriched["price_eur"],
                data_quality="estimated",
            )

            stats["rows_imported"] += 1
            stats["observation_ids"].append(observation_id)

            logger.info(
                "Seeded: CAI→%s %s %s %s $%.0f [%s]",
                enriched["destination"], enriched["carrier"], enriched["cabin"],
                enriched["outbound_date"].isoformat(), enriched["price_usd"],
                observation_id[:8],
            )

    stats["baseline_accelerated"] = stats["rows_imported"] >= 7

    if not dry_run:
        logger.info(
            "SEED complete: %d read, %d imported, %d rejected. "
            "baseline_accelerated=%s (≥7 imported = forecast exits cold-start)",
            stats["rows_read"], stats["rows_imported"],
            stats["rows_rejected"], stats["baseline_accelerated"],
        )
    else:
        logger.info(
            "SEED DRY_RUN: %d rows would be imported, %d rejected",
            stats["rows_imported"], stats["rows_rejected"],
        )

    return stats
