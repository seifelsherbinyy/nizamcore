"""
STAGE 2 — MONITOR: Daily Delta

Runs daily at 06:00 UTC (via scheduler or: python -m radar.main monitor).
Series in the store are grouped by (origin, destination, cabin) — the primary
source returns every carrier operating a route+cabin in a single fetch, so
carrier series sharing a route+cabin are checked together from ONE source
fetch rather than one redundant fetch per carrier. Groups are processed
stalest-observation-first and capped to a session budget (derived from
MAX_REQUESTS_PER_SESSION) so a single run can never exceed the CI job
timeout; any groups left over roll forward to the next day's run.

For each qualifying offer found, compares to the previous observation for
that carrier series and calculates the delta (absolute and percentage).
Stores the new observation with delta fields populated.
Backs up the store before writing.

Observation type: 'daily'

Output log fields:
- routes_checked: total (route, carrier, cabin) combinations checked
- routes_with_price_change: combinations where price changed from previous
- groups_checked: distinct (route, cabin) source fetches made this run
- groups_skipped_session_budget: groups deferred to the next run
- largest_drop_usd: largest single-day price drop found
- largest_drop_series: which series produced the largest drop
- fetch_errors: any source errors
"""

from __future__ import annotations

import logging
import time
from datetime import date

from radar.config import MAX_REQUESTS_PER_SESSION, WINDOW_END, WINDOW_START
from radar.fetcher import fetch_qualifying_offers
from radar.schema_store import (
    append_observation,
    backup_store,
    get_all_series_keys,
    load_store,
)

logger = logging.getLogger(__name__)

# Each group costs up to 6 source requests (3 sample dates x 2 night options
# in SerpApiSource) — cap how many groups one run processes so the session
# never blows past MAX_REQUESTS_PER_SESSION or the CI job timeout.
_REQUESTS_PER_GROUP = 6

# Hard wall-clock stop, independent of the group budget above — backstops
# the case where retries/backoff on a degraded source eat the per-group
# time estimate. Set comfortably under the 30-minute CI job timeout.
_MAX_RUN_SECONDS = 25 * 60


def _last_observed_at(store: dict, key_info: dict) -> str:
    """Timestamp of the most recent observation for a series, '' if none yet."""
    try:
        series = store["routes"][key_info["route_key"]]["observations"][key_info["series_key"]][
            "observation_series"
        ]
    except KeyError:
        return ""
    return series[-1]["observed_at"] if series else ""


def run_monitor() -> dict:
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

    store = load_store()
    all_keys = get_all_series_keys(store)
    if not all_keys:
        logger.warning("MONITOR: no series in store — run DISCOVER first")
        return {"stage": "MONITOR", "skipped": "no_series_in_store"}

    groups: dict[tuple[str, str, str], list[dict]] = {}
    for key_info in all_keys:
        group_key = (key_info["origin"], key_info["destination"], key_info["cabin"])
        groups.setdefault(group_key, []).append(key_info)

    # Stalest group first so every series eventually gets refreshed even when
    # the session budget can't cover all groups in a single run.
    ordered_groups = sorted(
        groups.items(),
        key=lambda kv: min(_last_observed_at(store, k) for k in kv[1]),
    )

    max_groups = max(1, MAX_REQUESTS_PER_SESSION // _REQUESTS_PER_GROUP)
    groups_to_run = ordered_groups[:max_groups]
    groups_skipped = len(ordered_groups) - len(groups_to_run)
    if groups_skipped:
        logger.info(
            "MONITOR: session budget covers %d/%d groups — %d deferred to next run",
            len(groups_to_run), len(ordered_groups), groups_skipped,
        )

    stats = {
        "stage": "MONITOR",
        "routes_checked": 0,
        "routes_with_price_change": 0,
        "routes_no_data": 0,
        "groups_checked": 0,
        "groups_skipped_session_budget": groups_skipped,
        "largest_drop_usd": 0.0,
        "largest_drop_series": None,
        "fetch_errors": [],
        "observations_written": 0,
    }

    run_start = time.monotonic()

    for i, ((origin, destination, cabin), series_list) in enumerate(groups_to_run):
        if time.monotonic() - run_start > _MAX_RUN_SECONDS:
            remaining = len(groups_to_run) - i
            stats["groups_skipped_session_budget"] += remaining
            logger.warning(
                "MONITOR: wall-clock budget (%ds) reached — %d group(s) deferred to next run",
                _MAX_RUN_SECONDS, remaining,
            )
            break

        logger.info("MONITOR: checking %s→%s %s (%d carriers)", origin, destination, cabin, len(series_list))

        offers, errors = fetch_qualifying_offers(
            origin=origin,
            destination=destination,
            cabin=cabin,
            window_start=window_start,
            window_end=window_end,
        )
        stats["fetch_errors"].extend(errors)
        stats["groups_checked"] += 1

        best_by_carrier: dict[str, object] = {}
        for offer in offers:
            existing = best_by_carrier.get(offer.carrier)
            if existing is None or offer.price_usd < existing.price_usd:
                best_by_carrier[offer.carrier] = offer

        for key_info in series_list:
            carrier = key_info["carrier"]
            stats["routes_checked"] += 1

            best_offer = best_by_carrier.get(carrier)
            if best_offer is None:
                stats["routes_no_data"] += 1
                logger.warning(
                    "MONITOR: no data for %s→%s %s %s",
                    origin, destination, carrier, cabin,
                )
                continue

            series = store["routes"][key_info["route_key"]]["observations"][key_info["series_key"]][
                "observation_series"
            ]
            prev_obs = series[-1] if series else None

            append_observation(
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
