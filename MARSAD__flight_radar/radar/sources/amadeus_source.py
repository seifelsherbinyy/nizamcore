"""
PRIMARY DATA SOURCE — Amadeus for Developers API.

SWAPPABLE_DEFAULT: Set DATA_SOURCE=amadeus in .env (default).
Requires AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET.

API: Flight Offers Search v2
Docs: https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search

Coverage verification needed at deployment:
- CAI route coverage — confirm Cairo is in the catalogue
- Business / Premium Economy cabin availability on CAI corridor
- Amadeus sandbox (AMADEUS_ENV=test) uses limited test data — switch to production for real prices

Rate limits (free tier as of 2026): ~1000 requests/month in test, higher in production.
For daily monitoring: estimate ~(12 destinations × 2 cabins) = 24 requests/day → ~720/month.
Fits comfortably in free tier for monitoring; production key needed for DISCOVER baseline.
"""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Optional

from radar.config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET, AMADEUS_ENV
from radar.sources.base import BaseFlightSource, FlightOffer, SourceResult

logger = logging.getLogger(__name__)

# Amadeus cabin code map: Amadeus uses single-char codes
_CABIN_MAP = {
    "BUSINESS": "BUSINESS",
    "PREMIUM_ECONOMY": "PREMIUM_ECONOMY",
}

# Number of sample departure dates to probe within the travel window
# Reduces API call volume while maintaining coverage
_SAMPLE_DATES_PER_SEARCH = 4


class AmadeusSource(BaseFlightSource):
    name = "amadeus"

    def __init__(self) -> None:
        self._client = None
        self._initialized = False

    def _init_client(self) -> bool:
        """Lazy initialise Amadeus client. Returns False if credentials missing."""
        if self._initialized:
            return self._client is not None

        if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
            logger.error("Amadeus credentials not configured — set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in .env")
            self._initialized = True
            return False

        try:
            from amadeus import Client, ResponseError  # noqa: F401
            self._client = Client(
                client_id=AMADEUS_CLIENT_ID,
                client_secret=AMADEUS_CLIENT_SECRET,
                hostname="test" if AMADEUS_ENV == "test" else "production",
            )
            self._initialized = True
            logger.info("Amadeus client initialised (env=%s)", AMADEUS_ENV)
            return True
        except ImportError:
            logger.error("amadeus package not installed — run: pip install amadeus")
            self._initialized = True
            return False
        except Exception as exc:
            logger.error("Amadeus client init failed: %s", exc)
            self._initialized = True
            return False

    def search(
        self,
        origin: str,
        destination: str,
        cabin: str,
        window_start: date,
        window_end: date,
        carriers: Optional[list[str]] = None,
    ) -> SourceResult:
        start_time = time.time()

        if not self._init_client():
            return SourceResult(
                source_name=self.name,
                offers=[],
                errors=["Amadeus client not initialised — check credentials"],
            )

        amadeus_cabin = _CABIN_MAP.get(cabin.upper())
        if not amadeus_cabin:
            return SourceResult(
                source_name=self.name,
                offers=[],
                errors=[f"Unknown cabin class: {cabin!r}"],
            )

        # Sample departure dates spread across the travel window
        sample_dates = self._sample_dates(window_start, window_end, _SAMPLE_DATES_PER_SEARCH)
        all_offers: list[FlightOffer] = []
        errors: list[str] = []

        for dep_date in sample_dates:
            # Return dates: try mid-range (11 nights) and boundaries (9, 14 nights)
            for nights in [9, 11, 14]:
                ret_date = dep_date + timedelta(days=nights)
                if ret_date > window_end:
                    continue

                offers, err = self._fetch_one(
                    origin=origin,
                    destination=destination,
                    dep_date=dep_date,
                    ret_date=ret_date,
                    cabin=amadeus_cabin,
                    carriers=carriers,
                )
                all_offers.extend(offers)
                if err:
                    errors.extend(err)

                if self._request_count < 3:
                    self._rate_limited_sleep()

        return SourceResult(
            source_name=self.name,
            offers=all_offers,
            errors=errors,
            fetch_duration_sec=round(time.time() - start_time, 2),
        )

    def _fetch_one(
        self,
        origin: str,
        destination: str,
        dep_date: date,
        ret_date: date,
        cabin: str,
        carriers: Optional[list[str]],
    ) -> tuple[list[FlightOffer], list[str]]:
        """Single Amadeus flight offers search call with exponential backoff."""
        from amadeus import ResponseError

        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": dep_date.isoformat(),
            "returnDate": ret_date.isoformat(),
            "adults": 1,
            "travelClass": cabin,
            "currencyCode": "USD",
            "max": 10,
        }
        if carriers:
            params["includedAirlineCodes"] = ",".join(carriers)

        for attempt in range(4):
            try:
                response = self._client.shopping.flight_offers_search.get(**params)
                self._request_count += 1
                return self._parse_response(response.data, dep_date, ret_date, cabin), []
            except ResponseError as exc:
                status = getattr(exc, "response", None)
                code = getattr(status, "status_code", 0) if status else 0

                if code in (429, 503):
                    self._exponential_backoff(attempt)
                    continue
                elif code == 400:
                    # Bad request — usually unsupported route or date
                    return [], [f"400 on {origin}-{destination} {dep_date}: {exc}"]
                else:
                    return [], [f"ResponseError {code} on {origin}-{destination} {dep_date}: {exc}"]
            except Exception as exc:
                return [], [f"Unexpected error: {exc}"]

        return [], [f"Max retries exceeded for {origin}-{destination} {dep_date}"]

    def _parse_response(
        self,
        data: list,
        dep_date: date,
        ret_date: date,
        cabin: str,
    ) -> list[FlightOffer]:
        offers = []
        for offer in data or []:
            try:
                price = float(offer["price"]["grandTotal"])
                itineraries = offer.get("itineraries", [])
                if len(itineraries) < 2:
                    continue

                outbound = itineraries[0]
                inbound = itineraries[1]

                outbound_hours = self._parse_duration_to_hours(outbound.get("duration", "PT0H"))
                return_hours = self._parse_duration_to_hours(inbound.get("duration", "PT0H"))

                outbound_segments = outbound.get("segments", [])
                inbound_segments = inbound.get("segments", [])

                carrier = outbound_segments[0].get("carrierCode", "??") if outbound_segments else "??"
                outbound_routing = self._build_routing(outbound_segments)
                return_routing = self._build_routing(inbound_segments)

                offers.append(FlightOffer(
                    origin=outbound_segments[0].get("departure", {}).get("iataCode", "CAI") if outbound_segments else "CAI",
                    destination=outbound_segments[-1].get("arrival", {}).get("iataCode", "???") if outbound_segments else "???",
                    cabin=cabin,
                    carrier=carrier,
                    outbound_date=dep_date,
                    return_date=ret_date,
                    outbound_duration_hours=outbound_hours,
                    return_duration_hours=return_hours,
                    outbound_stops=max(0, len(outbound_segments) - 1),
                    return_stops=max(0, len(inbound_segments) - 1),
                    outbound_routing=outbound_routing,
                    return_routing=return_routing,
                    price_usd=price,
                    source=self.name,
                    raw=offer,
                ))
            except (KeyError, ValueError, IndexError) as exc:
                logger.debug("Offer parse error: %s", exc)
                continue

        return offers

    def _build_routing(self, segments: list) -> str:
        if not segments:
            return ""
        codes = [segments[0].get("departure", {}).get("iataCode", "?")]
        for seg in segments:
            codes.append(seg.get("arrival", {}).get("iataCode", "?"))
        return "-".join(codes)

    @staticmethod
    def _sample_dates(window_start: date, window_end: date, n: int) -> list[date]:
        """Return n evenly-spaced dates within the travel window."""
        total_days = (window_end - window_start).days
        if total_days <= 0:
            return [window_start]
        step = max(1, total_days // (n + 1))
        return [window_start + timedelta(days=step * (i + 1)) for i in range(n)]
