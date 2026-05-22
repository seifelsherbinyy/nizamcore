"""
MARSAD Historical Price Seed Loader — Stage 0 (pre-DISCOVER).

Loads historical flight price observations from an external file into the JSON
store, tagged as observation_type='historical_seed'. This fast-tracks the
forecasting cold-start period: instead of waiting 7 daily monitor runs for
MEDIUM confidence, seed data can unlock MEDIUM confidence immediately.

═══════════════════════════════════════════════════════════════════════════════
HISTORICAL SOURCE RESEARCH (as of 2026-05-22)
═══════════════════════════════════════════════════════════════════════════════

1. GOOGLE FLIGHTS PRICE HISTORY
   - Depth available:  ~12 months of historical price data per route
   - Access method:    Manual — open Google Flights for a specific route, use
                       the calendar view, inspect network traffic via browser
                       devtools, capture XHR responses from googleapis.com/flights
   - Format:           JSON from `googleapis.com/flights/...` endpoints — price
                       per departure-date entry, requires parsing
   - Integration:      Export to the seed JSON format below, set source='google_flights_history'
   - Limitation:       No programmatic API; manual per-route extraction; no cabin
                       class breakdown in the calendar view (shows mixed-class lowest)
   - Verdict:          LOW VOLUME / MANUAL — useful for 1-2 priority routes, not scalable

2. HOPPER HISTORICAL PRICE DATA
   - Depth available:  12–24 months of historical trend data (in-app only)
   - Access method:    In-app only — no public API, no data export
   - Format:           N/A — not programmatically accessible
   - Verdict:          NOT ACCESSIBLE — Hopper's prediction model is proprietary

3. KAYAK PRICE HISTORY CHARTS
   - Depth available:  ~6–12 months shown in chart view
   - Access method:    Manual — navigate to Kayak, search a specific route, view
                       the "price trends" chart, inspect network XHR for price data
   - Format:           JSON from Kayak's internal API — monthly aggregated prices
   - Integration:      Export monthly average to seed JSON, data_quality='estimated'
   - Limitation:       Monthly averages only (not daily); no cabin class breakdown
   - Verdict:          MEDIUM VALUE — useful for monthly trend context

4. ITA MATRIX HISTORICAL SEARCH
   - Depth available:  NOT available — ITA Matrix only searches future dates
   - Verdict:          NOT APPLICABLE for historical seeding

5. PREVIOUS MARSAD MONITORING RUNS
   - Depth available:  All accumulated observations in flight_prices.json
   - Access method:    Direct — already in the store, no import needed
   - Verdict:          ALREADY IN STORE — the daily monitor accumulates this automatically

6. SERPAPI GOOGLE FLIGHTS (PROGRAMMATIC)
   - Depth available:  Current prices only — no historical depth via SerpApi
   - Verdict:          NOT APPLICABLE for historical seeding

RECOMMENDATION: The fastest path to MEDIUM confidence (7 observations) is
continued daily monitoring (5 more days after DISCOVER). Historical seeding
from Google Flights manual extraction is worth the effort only for the 3–4
highest-priority routes (JFK, MIA, LAX for summer 2027). For full coverage,
let the daily monitor accumulate naturally.

═══════════════════════════════════════════════════════════════════════════════
SEED FILE FORMAT
═══════════════════════════════════════════════════════════════════════════════

JSON format (one observation per element):
[
  {
    "origin": "CAI",                         -- required, must be "CAI"
    "destination": "JFK",                    -- required, must be in USA_DESTINATIONS
    "cabin": "BUSINESS",                     -- required, BUSINESS or PREMIUM_ECONOMY
    "carrier": "EK",                         -- required, IATA carrier code
    "price_usd": 3200.0,                     -- required, USD price
    "outbound_date": "2027-04-01",           -- required, ISO date
    "return_date": "2027-04-12",             -- required, ISO date (9–14 nights)
    "outbound_duration_hours": 14.5,         -- optional, defaults to 15.0 (estimated)
    "return_duration_hours": 15.0,           -- optional, defaults to 15.0 (estimated)
    "outbound_stops": 1,                     -- optional, defaults to 1
    "return_stops": 1,                       -- optional, defaults to 1
    "outbound_routing": "CAI-DXB-JFK",       -- optional, defaults to "CAI-{dest}"
    "return_routing": "JFK-DXB-CAI",         -- optional, defaults to "{dest}-CAI"
    "source": "google_flights_history",      -- optional, free text identifying the data source
    "data_quality": "estimated",             -- optional, "confirmed" or "estimated" (default: "estimated")
    "price_egp": null,                       -- optional supplementary currency
    "price_eur": null                        -- optional supplementary currency
  }
]

CSV format: same field names as column headers, same rules apply.

Usage:
    python -m radar.main seed --file data/seeds/google_flights_jfk.json
    python -m radar.main seed --file data/seeds/history.csv --source kayak_history --dry-run
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from radar.constraints import FlightItinerary, apply_constraints
from radar.schema_store import append_observation

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = {"origin", "destination", "cabin", "carrier", "price_usd", "outbound_date", "return_date"}

_DEFAULTS = {
    "outbound_duration_hours": 15.0,
    "return_duration_hours": 15.0,
    "outbound_stops": 1,
    "return_stops": 1,
    "data_quality": "estimated",
}


def _load_file(path: Path) -> list[dict]:
    """Load JSON or CSV seed file. Returns list of raw row dicts."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"Seed JSON must be a list of observations, got {type(data).__name__}")
        return data
    elif suffix == ".csv":
        rows = []
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        return rows
    else:
        raise ValueError(f"Unsupported seed file format: {suffix!r} — use .json or .csv")


def _coerce_row(raw: dict, default_source: str) -> dict:
    """
    Coerce and apply defaults to a raw seed row.
    Returns a normalized dict ready for apply_constraints and append_observation.
    Raises ValueError if a required field is missing or unparseable.
    """
    missing = _REQUIRED_FIELDS - set(raw.keys())
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    row = dict(raw)

    # Numeric coercions
    row["price_usd"] = float(row["price_usd"])
    row["outbound_duration_hours"] = float(row.get("outbound_duration_hours", _DEFAULTS["outbound_duration_hours"]))
    row["return_duration_hours"] = float(row.get("return_duration_hours", _DEFAULTS["return_duration_hours"]))
    row["outbound_stops"] = int(row.get("outbound_stops", _DEFAULTS["outbound_stops"]))
    row["return_stops"] = int(row.get("return_stops", _DEFAULTS["return_stops"]))

    # Date coercions
    row["outbound_date"] = str(row["outbound_date"])
    row["return_date"] = str(row["return_date"])
    outbound_dt = date.fromisoformat(row["outbound_date"])
    return_dt = date.fromisoformat(row["return_date"])

    # Routing defaults
    dest = row["destination"].upper()
    origin = row["origin"].upper()
    row["outbound_routing"] = str(row.get("outbound_routing") or f"{origin}-{dest}")
    row["return_routing"] = str(row.get("return_routing") or f"{dest}-{origin}")

    # Source and quality
    row["source"] = str(row.get("source") or default_source)
    row["data_quality"] = str(row.get("data_quality") or _DEFAULTS["data_quality"])

    # Optional currency fields
    row["price_egp"] = float(row["price_egp"]) if row.get("price_egp") else None
    row["price_eur"] = float(row["price_eur"]) if row.get("price_eur") else None

    # Attach parsed date objects for constraint engine
    row["_outbound_dt"] = outbound_dt
    row["_return_dt"] = return_dt

    return row


def run_seed(
    path: str | Path,
    source: str = "historical_seed",
    dry_run: bool = False,
) -> dict:
    """
    Load a seed file and import qualifying observations into the store.

    All rows pass through the routing constraint engine before storage.
    Rows that fail constraints are logged and skipped — not rejected outright.

    Returns summary dict with import statistics.
    """
    seed_path = Path(path)
    if not seed_path.exists():
        raise FileNotFoundError(f"Seed file not found: {seed_path}")

    logger.info("SEED: loading %s (source=%r, dry_run=%s)", seed_path, source, dry_run)

    try:
        raw_rows = _load_file(seed_path)
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        raise ValueError(f"Failed to load seed file: {exc}") from exc

    stats = {
        "stage": "SEED",
        "file": str(seed_path),
        "source": source,
        "dry_run": dry_run,
        "total_rows": len(raw_rows),
        "rows_imported": 0,
        "rows_skipped_constraint": 0,
        "rows_skipped_error": 0,
        "constraint_failures": [],
        "import_errors": [],
    }

    for i, raw in enumerate(raw_rows):
        try:
            row = _coerce_row(raw, source)
        except (ValueError, KeyError, TypeError) as exc:
            stats["rows_skipped_error"] += 1
            stats["import_errors"].append(f"Row {i}: {exc}")
            logger.warning("SEED row %d: coerce error — %s", i, exc)
            continue

        itin = FlightItinerary(
            origin=row["origin"],
            destination=row["destination"],
            cabin=row["cabin"],
            outbound_date=row["_outbound_dt"],
            return_date=row["_return_dt"],
            outbound_duration_hours=row["outbound_duration_hours"],
            return_duration_hours=row["return_duration_hours"],
            carrier=row["carrier"],
            price_usd=row["price_usd"],
        )

        constraint_result = apply_constraints(itin)
        if not constraint_result:
            stats["rows_skipped_constraint"] += 1
            stats["constraint_failures"].append({
                "row": i,
                "failures": constraint_result.failures,
            })
            logger.debug("SEED row %d: constraint failed — %s", i, constraint_result.failures)
            continue

        if dry_run:
            stats["rows_imported"] += 1
            logger.info(
                "SEED DRY RUN: %s→%s %s %s $%.0f (%s)",
                row["origin"], row["destination"],
                row["carrier"], row["cabin"],
                row["price_usd"], row["outbound_date"],
            )
            continue

        try:
            observation_id = append_observation(
                origin=row["origin"],
                destination=row["destination"],
                carrier=row["carrier"],
                cabin=row["cabin"],
                price_usd=row["price_usd"],
                outbound_date=row["outbound_date"],
                return_date=row["return_date"],
                outbound_duration_hours=row["outbound_duration_hours"],
                return_duration_hours=row["return_duration_hours"],
                outbound_stops=row["outbound_stops"],
                return_stops=row["return_stops"],
                outbound_routing=row["outbound_routing"],
                return_routing=row["return_routing"],
                source=row["source"],
                observation_type="historical_seed",
                price_egp=row["price_egp"],
                price_eur=row["price_eur"],
                data_quality=row["data_quality"],
            )
            stats["rows_imported"] += 1
            logger.info(
                "SEED imported: %s→%s %s %s $%.0f [%s]",
                row["origin"], row["destination"],
                row["carrier"], row["cabin"],
                row["price_usd"], observation_id[:8],
            )
        except Exception as exc:
            stats["rows_skipped_error"] += 1
            stats["import_errors"].append(f"Row {i}: store write failed — {exc}")
            logger.error("SEED row %d: store write error — %s", i, exc)

    logger.info(
        "SEED complete: %d/%d imported, %d constraint failures, %d errors",
        stats["rows_imported"],
        stats["total_rows"],
        stats["rows_skipped_constraint"],
        stats["rows_skipped_error"],
    )
    return stats
