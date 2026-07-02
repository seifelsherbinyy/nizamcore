"""
STAGE 2 — MONITOR: Daily Delta

Runs daily at 06:00 UTC (via scheduler or: python -m radar.main monitor).
For each route-carrier-cabin combination in the schema — fetch current best price,
compare to the previous observation, calculate delta (absolute and percentage).
Stores the new observation with delta fields populated.
Backs up the store before writing.

Observation type: 'daily'

Output log fields:
- routes_checked: total (route, carrier, cabin) combinations checked
- routes_with_price_change: combinations where price changed from previous
- largest_drop_usd: largest single-day price drop found
- largest_drop_series: which series produced the largest drop
- fetch_errors: any source errors
"""

from __future__ import annotations

import logging
from datetime import date

from radar.config import MONITOR_RATE_LIMIT_ABORT_THRESHOLD, WINDOW_END, WINDOW_START
from radar.fetcher import fetch_best_price
from radar.schema_store import (
    append_observation,
    backup_store,
    get_all_series_keys,
    load_store,
)

logger = logging.getLogger(__name__)


def run_monitor(use_secondary: bool = False) -> dict:
    """
    Execute daily price monitoring for all known series in the store.

    Returns summary dict with monitoring statistics.
    """
    # Backup before any writes — protects against interrupted mid-write corruption
    backup_path = backup_store()
    if backup_path:
        logger.info("MONITOR: backup created at %s", backup_path)

    window_start = date.fromisoformat(WINDOW_START)
    window_end = date.fromisoformat(WINDOW_END)

    # Skip monitoring if we're past the travel window
    today = date.today()
    if today > window_end:
        logger.info("MONITOR: travel window ended %s — no monitoring needed", window_end)
        return {"stage": "MONITOR", "skipped": "travel_window_ended"}

    all_keys = get_all_series_keys()
    if not all_keys:
        logger.warning("MONITOR: no series in store — run DISCOVER first")
        return {"stage": "MONITOR", "skipped": "no_series_in_store"}

    stats = {
        "stage": "MONITOR",
        "routes_checked": 0,
        "routes_with_price_change": 0,
        "routes_no_data": 0,
        "largest_drop_usd": 0.0,
        "largest_drop_series": None,
        "fetch_errors": [],
        "observations_written": 0,
        "aborted_reason": None,
    }

    consecutive_rate_limited = 0

    for key_info in all_keys:
        origin = key_info["origin"]
        destination = key_info["destination"]
        carrier = key_info["carrier"]
        cabin = key_info["cabin"]

        logger.info(
            "MONITOR: checking %s→%s %s %s",
            origin, destination, carrier, cabin,
        )

        best_offer, errors, rate_limited = fetch_best_price(
            origin=origin,
            destination=destination,
            cabin=cabin,
            window_start=window_start,
            window_end=window_end,
            carriers=[carrier],
            use_secondary=use_secondary,
        )
        stats["fetch_errors"].extend(errors)
        stats["routes_checked"] += 1

        if best_offer is None:
            stats["routes_no_data"] += 1
            logger.warning(
                "MONITOR: no data for %s→%s %s %s",
                origin, destination, carrier, cabin,
            )

            if rate_limited:
                consecutive_rate_limited += 1
                if consecutive_rate_limited >= MONITOR_RATE_LIMIT_ABORT_THRESHOLD:
                    remaining = len(all_keys) - stats["routes_checked"]
                    logger.error(
                        "MONITOR: %d consecutive series rate-limited — source quota likely "
                        "exhausted. Aborting with %d series unchecked instead of retrying "
                        "each one until the job times out.",
                        consecutive_rate_limited, remaining,
                    )
                    stats["aborted_reason"] = "source_rate_limited"
                    stats["routes_unchecked_after_abort"] = remaining
                    break
            else:
                consecutive_rate_limited = 0
            continue

        consecutive_rate_limited = 0

        # Fetch previous price from store for delta display logging
        store = load_store()
        rk = f"{origin}-{destination}"
        sk = f"{carrier}-{cabin}"
        prev_obs = None
        try:
            series = store["routes"][rk]["observations"][sk]["observation_series"]
            if series:
                prev_obs = series[-1]
        except KeyError:
            pass

        observation_id = append_observation(
            origin=best_offer.origin,
            destination=best_offer.destination,
            carrier=best_offer.carrier,
            cabin=best_offer.cabin,
            price_usd=best_offer.price_usd,
            outbound_date=best_offer.outbound_date.isoformat(),
            return_date=best_offer.return_date.isoformat(),
            outbound_duration_hours=best_offer.outbound_duration_hours,
            return_duration_hours=best_offer.return_duration_hours,
            outbound_stops=best_offer.outbound_stops,
            return_stops=best_offer.return_stops,
            outbound_routing=best_offer.outbound_routing,
            return_routing=best_offer.return_routing,
            source=best_offer.source,
            observation_type="daily",
        )
        stats["observations_written"] += 1

        if prev_obs is not None:
            delta = best_offer.price_usd - prev_obs["price_usd"]
            if abs(delta) > 0:
                stats["routes_with_price_change"] += 1
                if delta < 0 and abs(delta) > stats["largest_drop_usd"]:
                    stats["largest_drop_usd"] = abs(delta)
                    stats["largest_drop_series"] = f"{origin}-{destination}/{carrier}/{cabin}"
                logger.info(
                    "MONITOR: %s→%s %s %s: $%.0f → $%.0f (%+.0f USD, %+.1f%%)",
                    origin, destination, carrier, cabin,
                    prev_obs["price_usd"], best_offer.price_usd,
                    delta,
                    (delta / prev_obs["price_usd"] * 100) if prev_obs["price_usd"] else 0,
                )
        else:
            logger.info(
                "MONITOR: %s→%s %s %s: $%.0f (first observation)",
                origin, destination, carrier, cabin, best_offer.price_usd,
            )

    logger.info(
        "MONITOR complete: %d checked, %d changed, %d no data, largest drop $%.0f",
        stats["routes_checked"],
        stats["routes_with_price_change"],
        stats["routes_no_data"],
        stats["largest_drop_usd"],
    )

    return stats
