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
) -> tuple[Optional[FlightOffer], list[str]]:
    """
    Fetch the best (lowest price) qualifying offer for a single
    (origin, destination, cabin) combination.

    Applies constraint filtering to all returned results.
    Returns (best_offer, error_list). best_offer is None if no qualifying offer found.

    use_secondary: also queries Kiwi as cross-validation and takes lowest price.
    """
    all_errors: list[str] = []
    qualifying: list[FlightOffer] = []

    # Normalise requested carriers for post-fetch filtering (SerpApi and other
    # sources that don't support server-side carrier filtering return all carriers;
    # we filter client-side when the caller specifies a carrier list).
    requested_carriers: set[str] | None = (
        {c.upper() for c in carriers} if carriers else None
    )

    def _accept_offer(offer: FlightOffer) -> bool:
        """Return True if the offer passes constraint + carrier filters."""
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
        if not constraint_result:
            logger.debug("Offer filtered (constraints): %s", constraint_result.failures)
            return False
        if requested_carriers and offer.carrier.upper() not in requested_carriers:
            logger.debug(
                "Offer filtered (carrier): %s not in %s", offer.carrier, requested_carriers
            )
            return False
        return True

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
        if _accept_offer(offer):
            qualifying.append(offer)

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
            if _accept_offer(offer):
                qualifying.append(offer)

    if not qualifying:
        return None, all_errors

    best = min(qualifying, key=lambda o: o.price_usd)
    logger.debug(
        "Best offer: %s→%s %s %s $%.0f via %s",
        best.origin, best.destination, best.cabin, best.outbound_date, best.price_usd, best.source,
    )
    return best, all_errors


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

        best, errors = fetch_best_price(
            origin=combo["origin"],
            destination=combo["destination"],
            cabin=combo["cabin"],
            window_start=window_start,
            window_end=window_end,
            carriers=carriers,
            use_secondary=use_secondary,
        )
        results.append((combo, best, errors))

        # Count requests made (approximate — each combo uses multiple sub-requests)
        request_count += 1

        if i < total - 1:
            # Rate limit between combinations
            import random
            from radar.config import FETCH_DELAY_MIN_SEC, FETCH_DELAY_MAX_SEC
            delay = random.uniform(FETCH_DELAY_MIN_SEC, FETCH_DELAY_MAX_SEC)
            time.sleep(delay)

    return results
