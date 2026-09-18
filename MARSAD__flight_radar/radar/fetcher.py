"""
Staged sequential fetching pipeline.

Rules enforced here:
- Never fire parallel requests to the same domain
- Randomized delay (3–12s) between requests
- Exponential backoff on 429/503
- Maximum MAX_REQUESTS_PER_SESSION per session
- Each source fetched sequentially, results accumulated

Source priority order:
  1. Amadeus API (primary — terms-compliant)
  2. Kiwi Tequila (secondary aggregator)
  3. Google Flights (validation-only, prototype)
  4. ITA Matrix (optional, requires ToS acceptance)
"""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Optional

from radar.config import DATA_SOURCE, MAX_REQUESTS_PER_SESSION
from radar.constraints import apply_constraints, FlightItinerary
from radar.sources.base import FlightOffer, SourceResult
from radar.sources.serpapi_source import SerpApiSource
from radar.sources.amadeus_source import AmadeusSource
from radar.sources.ita_matrix_source import ITAMatrixSource
from radar.sources.kiwi_source import KiwiSource
from radar.sources.google_flights_source import GoogleFlightsSource

logger = logging.getLogger(__name__)


def _build_source():
    """Return the configured primary source instance."""
    if DATA_SOURCE == "serpapi":
        return SerpApiSource()
    elif DATA_SOURCE == "amadeus":
        return AmadeusSource()
    elif DATA_SOURCE == "kiwi":
        return KiwiSource()
    elif DATA_SOURCE == "ita_matrix":
        return ITAMatrixSource()
    else:
        logger.warning("Unknown DATA_SOURCE=%r — defaulting to SerpApiSource", DATA_SOURCE)
        return SerpApiSource()


def fetch_best_price(
    origin: str,
    destination: str,
    cabin: str,
    window_start: date,
    window_end: date,
    carriers: Optional[list[str]] = None,
    use_secondary: bool = False,
) -> tuple[Optional[FlightOffer], list[str], bool]:
    """
    Fetch the best (lowest price) qualifying offer for a single
    (origin, destination, cabin) combination.

    Applies constraint filtering to all returned results.
    Returns (best_offer, error_list, rate_limited). best_offer is None if no
    qualifying offer found. rate_limited=True means the primary source hit
    persistent 429s (quota exhausted / invalid key) — callers should treat
    this as a signal to stop making further calls this run.

    use_secondary: also queries Kiwi as cross-validation and takes lowest price.
    """
    all_errors: list[str] = []
    qualifying: list[FlightOffer] = []

    # Primary source
    primary = _build_source()
    result = primary.search(
        origin=origin,
        destination=destination,
        cabin=cabin,
        window_start=window_start,
        window_end=window_end,
        carriers=carriers,
    )
    all_errors.extend(result.errors)

    for offer in result.offers:
        itin = FlightItinerary(
            origin=offer.origin,
            destination=offer.destination,
            cabin=offer.cabin,
            outbound_date=offer.outbound_date,
            return_date=offer.return_date,
            outbound_duration_hours=offer.outbound_duration_hours,
            return_duration_hours=offer.return_duration_hours,
            carrier=offer.carrier,
            price_usd=offer.price_usd,
        )
        constraint_result = apply_constraints(itin)
        if constraint_result:
            qualifying.append(offer)
        else:
            logger.debug("Offer filtered: %s", constraint_result.failures)

    # Secondary source (Kiwi) if requested and we have remaining session budget
    if use_secondary and primary._request_count < MAX_REQUESTS_PER_SESSION:
        kiwi = KiwiSource()
        kiwi_result = kiwi.search(
            origin=origin,
            destination=destination,
            cabin=cabin,
            window_start=window_start,
            window_end=window_end,
            carriers=carriers,
        )
        all_errors.extend(kiwi_result.errors)

        for offer in kiwi_result.offers:
            itin = FlightItinerary(
                origin=offer.origin,
                destination=offer.destination,
                cabin=offer.cabin,
                outbound_date=offer.outbound_date,
                return_date=offer.return_date,
                outbound_duration_hours=offer.outbound_duration_hours,
                return_duration_hours=offer.return_duration_hours,
                carrier=offer.carrier,
                price_usd=offer.price_usd,
            )
            if apply_constraints(itin):
                qualifying.append(offer)

    if not qualifying:
        return None, all_errors, result.rate_limited

    best = min(qualifying, key=lambda o: o.price_usd)
    logger.debug(
        "Best offer: %s→%s %s %s $%.0f via %s",
        best.origin, best.destination, best.cabin, best.outbound_date, best.price_usd, best.source,
    )
    return best, all_errors, result.rate_limited


def fetch_all_combinations(
    combinations: list[dict],
    window_start: date,
    window_end: date,
    carriers: Optional[list[str]] = None,
    use_secondary: bool = False,
) -> list[tuple[dict, Optional[FlightOffer], list[str]]]:
    """
    Sequentially fetch best offer for each (origin, destination, cabin) combination.
    Enforces MAX_REQUESTS_PER_SESSION across the full batch.

    Returns list of (combo, best_offer, errors) tuples.
    """
    results = []
    total = len(combinations)
    request_count = 0

    for i, combo in enumerate(combinations):
        if request_count >= MAX_REQUESTS_PER_SESSION:
            logger.warning(
                "MAX_REQUESTS_PER_SESSION=%d reached at combo %d/%d — stopping fetch",
                MAX_REQUESTS_PER_SESSION, i, total,
            )
            remaining = combinations[i:]
            for c in remaining:
                results.append((c, None, ["Session limit reached — re-run to fetch remaining combinations"]))
            break

        logger.info("Fetching %d/%d: %s→%s %s", i + 1, total, combo["origin"], combo["destination"], combo["cabin"])

        best, errors, rate_limited = fetch_best_price(
            origin=combo["origin"],
            destination=combo["destination"],
            cabin=combo["cabin"],
            window_start=window_start,
            window_end=window_end,
            carriers=carriers,
            use_secondary=use_secondary,
        )
        results.append((combo, best, errors))

        if rate_limited:
            logger.error(
                "Source persistently rate-limited (quota exhausted or invalid "
                "key) at combo %d/%d — aborting remaining fetches instead of "
                "retrying each one for nothing. Check credentials/plan quota.",
                i + 1, total,
            )
            remaining = combinations[i + 1:]
            for c in remaining:
                results.append((c, None, ["Skipped — source rate-limited earlier this session"]))
            break

        # Count requests made (approximate — each combo uses multiple sub-requests)
        request_count += 1

        if i < total - 1:
            # Rate limit between combinations
            import random
            from radar.config import FETCH_DELAY_MIN_SEC, FETCH_DELAY_MAX_SEC
            delay = random.uniform(FETCH_DELAY_MIN_SEC, FETCH_DELAY_MAX_SEC)
            time.sleep(delay)

    return results
