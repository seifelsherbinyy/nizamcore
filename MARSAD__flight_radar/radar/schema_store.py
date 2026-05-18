"""
Append-only JSON schema store for MARSAD flight price observations.

INVARIANT: Historical data is never overwritten or deleted.
New observations are always appended to their route-carrier-cabin series.

Write pattern: write to .tmp → validate → os.replace() to target.
On any failure before replace(), the original file is untouched.

Schema path: MARSAD__flight_radar/data/flight_prices.json
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from radar.config import (
    BACKUPS_DIR,
    FLIGHT_PRICES_PATH,
    FLIGHT_PRICES_TMP,
    SCHEMA_VERSION,
    WINDOW_END,
    WINDOW_START,
)

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _empty_store() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "module": "MARSAD",
        "created_at": _utcnow(),
        "last_updated": _utcnow(),
        "metadata": {
            "travel_window_start": WINDOW_START,
            "travel_window_end": WINDOW_END,
            "origin": "CAI",
            "cabins": ["BUSINESS", "PREMIUM_ECONOMY"],
            "destinations": [
                "JFK", "LAX", "ORD", "ATL", "MIA",
                "SFO", "IAD", "BOS", "EWR", "DFW", "SEA", "LAS",
            ],
            "carriers_premium_economy_unavailable": [],
        },
        "routes": {},
    }


def load_store() -> dict:
    """Load the flight prices store. Creates an empty store if none exists."""
    FLIGHT_PRICES_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not FLIGHT_PRICES_PATH.exists():
        logger.info("No existing store — initialising empty store at %s", FLIGHT_PRICES_PATH)
        store = _empty_store()
        _safe_write(store)
        return store

    try:
        with open(FLIGHT_PRICES_PATH, "r", encoding="utf-8") as f:
            store = json.load(f)
        logger.debug("Loaded store: %d route entries", len(store.get("routes", {})))
        return store
    except json.JSONDecodeError as exc:
        logger.error("Store JSON parse error: %s — attempting backup recovery", exc)
        return _recover_from_backup()


def _safe_write(store: dict) -> None:
    """
    Write store to .tmp, validate JSON round-trip, then atomically replace target.
    If anything fails before os.replace(), the original file is untouched.
    """
    FLIGHT_PRICES_PATH.parent.mkdir(parents=True, exist_ok=True)
    store["last_updated"] = _utcnow()

    try:
        serialized = json.dumps(store, indent=2, ensure_ascii=False)
        # Validate round-trip before touching the real file
        json.loads(serialized)

        FLIGHT_PRICES_TMP.write_text(serialized, encoding="utf-8")
        os.replace(FLIGHT_PRICES_TMP, FLIGHT_PRICES_PATH)
        logger.debug("Store written atomically to %s", FLIGHT_PRICES_PATH)
    except Exception as exc:
        logger.error("Safe write failed: %s — original store untouched", exc)
        if FLIGHT_PRICES_TMP.exists():
            FLIGHT_PRICES_TMP.unlink(missing_ok=True)
        raise


def backup_store() -> Optional[Path]:
    """Copy current store to BACKUPS_DIR with timestamp. Called before each monitor run."""
    if not FLIGHT_PRICES_PATH.exists():
        return None

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    backup_path = BACKUPS_DIR / f"{ts}.json"
    shutil.copy2(FLIGHT_PRICES_PATH, backup_path)
    logger.info("Backup created: %s", backup_path)
    return backup_path


def _recover_from_backup() -> dict:
    """Return the most recent valid backup, or an empty store if none found."""
    if not BACKUPS_DIR.exists():
        logger.warning("No backups directory — starting with empty store")
        return _empty_store()

    backups = sorted(BACKUPS_DIR.glob("*.json"), reverse=True)
    for backup in backups:
        try:
            with open(backup, "r", encoding="utf-8") as f:
                store = json.load(f)
            logger.warning("Recovered from backup: %s", backup)
            return store
        except json.JSONDecodeError:
            continue

    logger.warning("No valid backups found — starting with empty store")
    return _empty_store()


def _route_key(origin: str, destination: str) -> str:
    return f"{origin.upper()}-{destination.upper()}"


def _series_key(carrier: str, cabin: str) -> str:
    return f"{carrier.upper()}-{cabin.upper()}"


def _ensure_series(store: dict, origin: str, destination: str, carrier: str, cabin: str) -> None:
    """Ensure the nested route → series structure exists in the store."""
    rk = _route_key(origin, destination)
    sk = _series_key(carrier, cabin)

    if rk not in store["routes"]:
        store["routes"][rk] = {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "observations": {},
        }

    if sk not in store["routes"][rk]["observations"]:
        store["routes"][rk]["observations"][sk] = {
            "carrier": carrier.upper(),
            "cabin": cabin.upper(),
            "route_key": rk,
            "premium_economy_status": "unknown",
            "observation_series": [],
            "forecast": {
                "observation_count": 0,
                "forecast_confidence": "LOW",
                "last_forecasted_at": None,
                "horizon_7d": {"low": None, "mid": None, "high": None},
                "horizon_14d": {"low": None, "mid": None, "high": None},
                "horizon_30d": {"low": None, "mid": None, "high": None},
                "buy_signal": False,
                "historical_20th_percentile": None,
                "model_used": None,
            },
        }


def append_observation(
    origin: str,
    destination: str,
    carrier: str,
    cabin: str,
    price_usd: float,
    outbound_date: str,
    return_date: str,
    outbound_duration_hours: float,
    return_duration_hours: float,
    outbound_stops: int,
    return_stops: int,
    outbound_routing: str,
    return_routing: str,
    source: str,
    observation_type: str = "daily",
    price_egp: Optional[float] = None,
    price_eur: Optional[float] = None,
    data_quality: str = "confirmed",
) -> str:
    """
    Append a new price observation to the store.
    Returns the observation_id.
    INVARIANT: never overwrites existing observations.
    """
    store = load_store()
    _ensure_series(store, origin, destination, carrier, cabin)

    rk = _route_key(origin, destination)
    sk = _series_key(carrier, cabin)
    series = store["routes"][rk]["observations"][sk]["observation_series"]

    # Calculate delta against most recent previous observation
    prev_price = series[-1]["price_usd"] if series else None
    delta_usd = round(price_usd - prev_price, 2) if prev_price is not None else None
    delta_pct = (
        round((delta_usd / prev_price) * 100, 2)
        if (prev_price is not None and prev_price > 0)
        else None
    )

    observation_id = str(uuid4())
    obs = {
        "observation_id": observation_id,
        "observation_type": observation_type,
        "observed_at": _utcnow(),
        "outbound_date": outbound_date,
        "return_date": return_date,
        "nights": (
            (datetime.fromisoformat(return_date) - datetime.fromisoformat(outbound_date)).days
        ),
        "price_usd": price_usd,
        "price_egp": price_egp,
        "price_eur": price_eur,
        "outbound_duration_hours": outbound_duration_hours,
        "return_duration_hours": return_duration_hours,
        "outbound_stops": outbound_stops,
        "return_stops": return_stops,
        "outbound_routing": outbound_routing,
        "return_routing": return_routing,
        "source": source,
        "delta_from_previous_usd": delta_usd,
        "delta_pct": delta_pct,
        "alert_flag": False,
        "data_quality": data_quality,
    }

    series.append(obs)
    store["routes"][rk]["observations"][sk]["forecast"]["observation_count"] = len(series)

    _safe_write(store)
    logger.debug(
        "Observation appended: %s %s %s %s $%.0f (delta: %s%%)",
        rk, carrier, cabin, outbound_date, price_usd,
        f"{delta_pct:+.1f}" if delta_pct is not None else "N/A",
    )
    return observation_id


def mark_alert(
    origin: str,
    destination: str,
    carrier: str,
    cabin: str,
    observation_id: str,
) -> bool:
    """Set alert_flag=True on a specific observation. Returns True if found and updated."""
    store = load_store()
    rk = _route_key(origin, destination)
    sk = _series_key(carrier, cabin)

    try:
        series = store["routes"][rk]["observations"][sk]["observation_series"]
    except KeyError:
        return False

    for obs in series:
        if obs["observation_id"] == observation_id:
            obs["alert_flag"] = True
            _safe_write(store)
            return True
    return False


def update_forecast(
    origin: str,
    destination: str,
    carrier: str,
    cabin: str,
    forecast_data: dict,
) -> None:
    """Replace the forecast block for a route-carrier-cabin series. Never touches observation_series."""
    store = load_store()
    rk = _route_key(origin, destination)
    sk = _series_key(carrier, cabin)

    try:
        store["routes"][rk]["observations"][sk]["forecast"].update(forecast_data)
        store["routes"][rk]["observations"][sk]["forecast"]["last_forecasted_at"] = _utcnow()
        _safe_write(store)
    except KeyError as exc:
        logger.error("update_forecast: key not found %s", exc)


def mark_premium_economy_unavailable(origin: str, destination: str, carrier: str) -> None:
    """Log that Premium Economy is not available on this carrier/route."""
    store = load_store()
    rk = _route_key(origin, destination)
    sk = _series_key(carrier, "PREMIUM_ECONOMY")

    _ensure_series(store, origin, destination, carrier, "PREMIUM_ECONOMY")
    store["routes"][rk]["observations"][sk]["premium_economy_status"] = "unavailable"

    meta_list = store["metadata"].setdefault("carriers_premium_economy_unavailable", [])
    entry = f"{carrier.upper()}/{rk}"
    if entry not in meta_list:
        meta_list.append(entry)

    _safe_write(store)
    logger.info("Marked PREMIUM_ECONOMY unavailable: %s on %s", carrier.upper(), rk)


def get_series(
    origin: str,
    destination: str,
    carrier: str,
    cabin: str,
) -> list[dict]:
    """Return the full observation series for a route-carrier-cabin combination."""
    store = load_store()
    rk = _route_key(origin, destination)
    sk = _series_key(carrier, cabin)

    try:
        return store["routes"][rk]["observations"][sk]["observation_series"]
    except KeyError:
        return []


def get_all_series_keys(store: Optional[dict] = None) -> list[dict]:
    """Return all (origin, destination, carrier, cabin) combinations in the store."""
    if store is None:
        store = load_store()

    keys = []
    for rk, route_data in store.get("routes", {}).items():
        for sk, series_data in route_data.get("observations", {}).items():
            keys.append({
                "origin": route_data["origin"],
                "destination": route_data["destination"],
                "carrier": series_data["carrier"],
                "cabin": series_data["cabin"],
                "route_key": rk,
                "series_key": sk,
                "observation_count": series_data["forecast"]["observation_count"],
            })
    return keys
