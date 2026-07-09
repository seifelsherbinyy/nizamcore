"""
STAGE 2 — MONITOR: Daily Delta

Runs daily at 06:00 UTC (via scheduler or: python -m radar.main monitor).
For each route-carrier-cabin combination in the schema — fetch current best price,
compare to the previous observation, calculate delta (absolute and percentage).
Stores the new observation with delta fields populated.
Backs up the store before writing.

Observation type: 'daily'

Two cost controls keep this stage within the SerpApi free-tier budget and the
CI job's timeout:

- Lean re-check: reuses the previously observed (outbound_date, return_date)
  pair instead of resampling DISCOVER's full date/night matrix — 1 API call
  per series instead of up to 6. See fetcher.fetch_price_for_known_itinerary.
- Round-robin batching: only MONITOR_KEYS_PER_RUN series are checked per run,
  rotating via a cursor persisted in store metadata, so full coverage rotates
  across multiple days instead of hammering every series (and the API quota)
  in one run.
- Circuit breaker: aborts early after MONITOR_CONSECUTIVE_FAILURE_LIMIT
  consecutive no-data results — almost always means the source is rate/quota
  limited, so retrying every remaining series would just burn the job's
  timeout for nothing.

Output log fields:
- routes_checked: total (route, carrier, cabin) combinations checked
- routes_with_price_change: combinations where price changed from previous
- largest_drop_usd: largest single-day price drop found
- largest_drop_series: which series produced the largest drop
- fetch_errors: any source errors
- aborted_early: True if the circuit breaker cut the run short
"""

from __future__ import annotations

import logging
from datetime import date

from radar.config import MONITOR_CONSECUTIVE_FAILURE_LIMIT, MONITOR_KEYS_PER_RUN, WINDOW_END
from radar.fetcher import fetch_price_for_known_itinerary
from radar.schema_store import (
    append_observation,
    backup_store,
    get_all_series_keys,
    get_monitor_cursor,
    load_store,
    set_monitor_cursor,
)

logger = logging.getLogger(__name__)


def _select_batch(all_keys: list[dict], cursor: int, batch_size: int) -> tuple[list[dict], int]:
    """Round-robin slice of all_keys starting at cursor, wrapping around."""
    n = len(all_keys)
    if n == 0:
        return [], 0
    batch_size = min(batch_size, n)
    start = cursor % n
    batch = [all_keys[(start + i) % n] for i in range(batch_size)]
    next_cursor = (start + batch_size) % n
    return batch, next_cursor


def run_monitor() -> dict:
    """
    Execute daily price monitoring for a rotating batch of known series in the store.

    Returns summary dict with monitoring statistics.
    """
    # Backup before any writes — protects against interrupted mid-write corruption
    backup_path = backup_store()
    if backup_path:
        logger.info("MONITOR: backup created at %s", backup_path)

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

    cursor = get_monitor_cursor()
    batch, next_cursor = _select_batch(all_keys, cursor, MONITOR_KEYS_PER_RUN)

    stats = {
        "stage": "MONITOR",
        "routes_checked": 0,
        "routes_with_price_change": 0,
        "routes_no_data": 0,
        "largest_drop_usd": 0.0,
        "largest_drop_series": None,
        "fetch_errors": [],
        "observations_written": 0,
        "batch_size": len(batch),
        "total_series": len(all_keys),
        "aborted_early": False,
    }

    consecutive_failures = 0

    for key_info in batch:
        origin = key_info["origin"]
        destination = key_info["destination"]
        carrier = key_info["carrier"]
        cabin = key_info["cabin"]

        logger.info(
            "MONITOR: checking %s→%s %s %s",
            origin, destination, carrier, cabin,
        )

        # Re-check the exact previously-observed itinerary — 1 API call.
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

        if prev_obs is None:
            logger.warning(
                "MONITOR: no prior observation for %s→%s %s %s — skipping (run DISCOVER first)",
                origin, destination, carrier, cabin,
            )
            stats["routes_no_data"] += 1
            continue

        best_offer, errors = fetch_price_for_known_itinerary(
            origin=origin,
            destination=destination,
            cabin=cabin,
            carrier=carrier,
            outbound_date=date.fromisoformat(prev_obs["outbound_date"]),
            return_date=date.fromisoformat(prev_obs["return_date"]),
        )
        stats["fetch_errors"].extend(errors)
        stats["routes_checked"] += 1

        if best_offer is None:
            stats["routes_no_data"] += 1
            consecutive_failures += 1
            logger.warning(
                "MONITOR: no data for %s→%s %s %s",
                origin, destination, carrier, cabin,
            )
            if consecutive_failures >= MONITOR_CONSECUTIVE_FAILURE_LIMIT:
                logger.error(
                    "MONITOR: %d consecutive no-data results — source likely rate/quota "
                    "limited, aborting run early instead of retrying the remaining %d series",
                    consecutive_failures, len(batch) - stats["routes_checked"],
                )
                stats["aborted_early"] = True
                break
            continue

        consecutive_failures = 0

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

    # Advance the rotation cursor past this batch regardless of early abort —
    # keeps coverage rotating fairly instead of retrying the same stuck series.
    set_monitor_cursor(next_cursor)

    logger.info(
        "MONITOR complete: %d/%d checked, %d changed, %d no data, largest drop $%.0f%s",
        stats["routes_checked"],
        stats["batch_size"],
        stats["routes_with_price_change"],
        stats["routes_no_data"],
        stats["largest_drop_usd"],
        " (aborted early — likely rate/quota limited)" if stats["aborted_early"] else "",
    )

    return stats
