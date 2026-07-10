"""
STAGE 1 — DISCOVER: Baseline Collection

Runs once on first deploy (or on manual trigger via: python -m radar.main discover).
Fetches the full price matrix across all carrier × cabin × destination combinations
within the travel window and routing constraints.

Observation type: 'baseline'

This is the most expensive fetch operation. It is split across multiple sessions
(days 1–7) to avoid rate-limit exhaustion. Each run fetches a subset of combinations
and appends to the schema — subsequent runs pick up where the previous left off.

Session limit: MAX_REQUESTS_PER_SESSION per run.
Full baseline completes in approximately 7 days of daily discover runs.

Output log fields:
- total_combinations: total (destination × cabin) combinations in scope
- combinations_fetched: combinations successfully fetched this session
- combinations_no_data: carriers with no qualifying offer returned
- fetch_errors: any source errors encountered
- baseline_complete: True when all combinations have at least one baseline observation
"""

from __future__ import annotations

import logging
from datetime import date

from radar.config import (
    ALL_CARRIERS,
    WINDOW_END,
    WINDOW_START,
)
from radar.constraints import generate_search_combinations
from radar.fetcher import fetch_all_combinations
from radar.schema_store import (
    append_observation,
    get_all_series_keys,
    load_store,
    mark_premium_economy_unavailable,
)
from radar.sources.serpapi_source import is_quota_likely_exhausted

logger = logging.getLogger(__name__)


def run_discover(
    carriers: list[str] | None = None,
    use_secondary: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Execute baseline collection for all (destination, cabin) combinations.

    carriers: restrict to specific carrier IATA codes. None = all carriers.
    use_secondary: also query Kiwi for cross-validation.
    dry_run: log what would be fetched without writing to store.

    Returns summary dict with fetch statistics.
    """
    window_start = date.fromisoformat(WINDOW_START)
    window_end = date.fromisoformat(WINDOW_END)
    target_carriers = carriers or ALL_CARRIERS

    # Determine which combinations already have a baseline observation
    covered_combos = {
        (k["origin"], k["destination"], k["cabin"])
        for k in get_all_series_keys()
        if k["observation_count"] > 0
    }

    combinations = generate_search_combinations()
    pending = [
        c for c in combinations
        if (c["origin"], c["destination"].upper(), c["cabin"].upper()) not in covered_combos
    ]

    logger.info(
        "DISCOVER: %d total combinations, %d pending baseline (%d already have data)",
        len(combinations),
        len(pending),
        len(combinations) - len(pending),
    )

    if dry_run:
        logger.info("DRY RUN — no data will be written")
        return {
            "stage": "DISCOVER",
            "dry_run": True,
            "total_combinations": len(combinations),
            "pending": len(pending),
        }

    results = fetch_all_combinations(
        combinations=pending,
        window_start=window_start,
        window_end=window_end,
        carriers=target_carriers,
        use_secondary=use_secondary,
    )

    stats = {
        "stage": "DISCOVER",
        "total_combinations": len(combinations),
        "combinations_fetched": 0,
        "combinations_no_data": 0,
        "observations_written": 0,
        "fetch_errors": [],
        "baseline_complete": False,
        "aborted_reason": "serpapi_quota_or_rate_limit_exhausted" if is_quota_likely_exhausted() else None,
    }

    for combo, best_offer, errors in results:
        stats["fetch_errors"].extend(errors)

        if best_offer is None:
            stats["combinations_no_data"] += 1
            logger.warning(
                "No qualifying offer: %s→%s %s",
                combo["origin"], combo["destination"], combo["cabin"],
            )
            if combo["cabin"].upper() == "PREMIUM_ECONOMY":
                mark_premium_economy_unavailable(combo["origin"], combo["destination"], "UNKNOWN")
            continue

        stats["combinations_fetched"] += 1

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
            observation_type="baseline",
            price_egp=best_offer.price_egp,
            price_eur=best_offer.price_eur,
        )
        stats["observations_written"] += 1
        logger.info(
            "Baseline: %s→%s %s %s $%.0f [%s]",
            best_offer.origin, best_offer.destination,
            best_offer.carrier, best_offer.cabin,
            best_offer.price_usd, observation_id[:8],
        )

    # Check if all combinations now have at least one observation
    all_keys_after = get_all_series_keys()
    covered = sum(1 for k in all_keys_after if k["observation_count"] > 0)
    stats["baseline_complete"] = covered >= len(combinations)

    logger.info(
        "DISCOVER complete: %d fetched, %d no data, %d errors, baseline_complete=%s",
        stats["combinations_fetched"],
        stats["combinations_no_data"],
        len(stats["fetch_errors"]),
        stats["baseline_complete"],
    )

    return stats
