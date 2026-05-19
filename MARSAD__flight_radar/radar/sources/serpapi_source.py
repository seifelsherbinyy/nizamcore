"""
PRIMARY DATA SOURCE — SerpApi Google Flights API.

SWAPPABLE_DEFAULT: Set DATA_SOURCE=serpapi in .env (current default).
Requires SERPAPI_KEY from serpapi.com (free tier: 250 searches/month).

Free tier budget note:
  250 searches/month ≈ 8 searches/day
  Full daily monitoring (12 destinations × 2 cabins) = 24 searches/day → paid tier needed
  Priority-only mode (8 destinations × 2 cabins) = 16 searches/day → still exceeds free tier
  Recommendation: paid tier at $25/month for 1,000 searches covers full monitoring with headroom

  To stay within free tier during testing: set SERPAPI_PRIORITY_ONLY=true in .env
  and run DISCOVER manually (not on daily schedule) until ready to upgrade.

API docs: https://serpapi.com/google-flights-api
Travel class codes: 1=Economy, 2=Premium Economy, 3=Business, 4=First
"""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Optional

import requests

from radar.config import SERPAPI_KEY, SERPAPI_PRIORITY_ONLY, PRIORITY_DESTINATIONS
from radar.sources.base import BaseFlightSource, FlightOffer, SourceResult

logger = logging.getLogger(__name__)

_SERPAPI_ENDPOINT = "https://serpapi.com/search"

_CABIN_CLASS_MAP = {
    "BUSINESS": 3,
    "PREMIUM_ECONOMY": 2,
}

# Sample departure dates spread across the travel window per search
_SAMPLE_DATES_COUNT = 3


class SerpApiSource(BaseFlightSource):
    name = "serpapi"

    def search(
        self,
        origin: str,
        destination: str,
        cabin: str,
        window_start: date,
        window_end: date,
        carriers: Optional[list[str]] = None,
    ) -> SourceResult:
        if not SERPAPI_KEY:
            return SourceResult(
                source_name=self.name,
                offers=[],
                errors=["SERPAPI_KEY not configured — set it in .env"],
            )

        travel_class = _CABIN_CLASS_MAP.get(cabin.upper())
        if not travel_class:
            return SourceResult(
                source_name=self.name,
                offers=[],
                errors=[f"Unknown cabin: {cabin!r}"],
            )

        # In priority-only mode, skip non-priority destinations
        if SERPAPI_PRIORITY_ONLY and destination.upper() not in PRIORITY_DESTINATIONS:
            logger.debug(
                "SERPAPI_PRIORITY_ONLY: skipping %s (not in priority list)", destination
            )
            return SourceResult(source_name=self.name, offers=[], errors=[])

        sample_dates = self._sample_dates(window_start, window_end, _SAMPLE_DATES_COUNT)
        all_offers: list[FlightOffer] = []
        errors: list[str] = []
        start_t = time.time()

        for dep_date in sample_dates:
            # Try two return duration options: 9 nights and 14 nights
            for nights in [9, 14]:
                ret_date = dep_date + timedelta(days=nights)
                if ret_date > window_end:
                    continue

                offers, errs = self._fetch_one(
                    origin=origin,
                    destination=destination,
                    dep_date=dep_date,
                    ret_date=ret_date,
                    travel_class=travel_class,
                    cabin=cabin,
                    carriers=carriers,
                )
                all_offers.extend(offers)
                errors.extend(errs)

                if all_offers:
                    # Found results for this date pair — rate limit before next call
                    self._rate_limited_sleep()

        return SourceResult(
            source_name=self.name,
            offers=all_offers,
            errors=errors,
            fetch_duration_sec=round(time.time() - start_t, 2),
        )

    def _fetch_one(
        self,
        origin: str,
        destination: str,
        dep_date: date,
        ret_date: date,
        travel_class: int,
        cabin: str,
        carriers: Optional[list[str]] = None,
    ) -> tuple[list[FlightOffer], list[str]]:
        """Single SerpApi call with exponential backoff on rate limit."""
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": dep_date.isoformat(),
            "return_date": ret_date.isoformat(),
            "travel_class": travel_class,
            "type": 1,        # round trip
            "adults": 1,
            "currency": "USD",
            "hl": "en",
            "api_key": SERPAPI_KEY,
        }
        if carriers:
            # SerpApi Google Flights: include_airlines filters to specific IATA codes
            params["include_airlines"] = ",".join(carriers)

        for attempt in range(4):
            try:
                resp = requests.get(
                    _SERPAPI_ENDPOINT,
                    params=params,
                    timeout=30,
                )

                if resp.status_code == 429:
                    self._exponential_backoff(attempt)
                    continue

                if resp.status_code == 401:
                    return [], ["SerpApi 401 Unauthorized — check SERPAPI_KEY in .env"]

                if resp.status_code == 400:
                    body = resp.json() if resp.content else {}
                    return [], [f"SerpApi 400: {body.get('error', 'bad request')} — {origin}→{destination} {dep_date}"]

                resp.raise_for_status()
                self._request_count += 1

                data = resp.json()
                if "error" in data:
                    return [], [f"SerpApi error: {data['error']}"]

                offers = self._parse(data, dep_date, ret_date, cabin)
                return offers, []

            except requests.Timeout:
                errors = [f"SerpApi timeout: {origin}→{destination} {dep_date}"]
                if attempt < 3:
                    self._exponential_backoff(attempt)
            except requests.RequestException as exc:
                return [], [f"SerpApi request error: {exc}"]

        return [], [f"SerpApi max retries exceeded: {origin}→{destination} {dep_date}"]

    def _parse(
        self,
        data: dict,
        dep_date: date,
        ret_date: date,
        cabin: str,
    ) -> list[FlightOffer]:
        offers = []

        # SerpApi returns best_flights and other_flights
        for flight_group in (data.get("best_flights") or [], data.get("other_flights") or []):
            # Each group item IS one itinerary in Google Flights results
            # (not a list of lists — each element is a single round-trip option)
            if not isinstance(flight_group, list):
                flight_group = [flight_group]

            for item in flight_group:
                try:
                    offer = self._parse_item(item, dep_date, ret_date, cabin)
                    if offer:
                        offers.append(offer)
                except Exception as exc:
                    logger.debug("SerpApi parse error: %s", exc)

        return offers

    def _parse_item(
        self,
        item: dict,
        dep_date: date,
        ret_date: date,
        cabin: str,
    ) -> Optional[FlightOffer]:
        price = item.get("price")
        if not price:
            return None

        flights = item.get("flights", [])
        if not flights:
            return None

        total_duration_min = item.get("total_duration", 0)
        total_duration_hours = round(total_duration_min / 60, 2) if total_duration_min else 0.0

        # Google Flights returns the full round-trip duration in total_duration
        # For one-way constraints we split roughly 50/50 — actual per-leg data
        # is in the flights array when available
        outbound_flights = [f for f in flights if not f.get("is_return", False)]
        return_flights = [f for f in flights if f.get("is_return", False)]

        outbound_dur = sum(f.get("duration", 0) for f in outbound_flights) if outbound_flights else total_duration_min // 2
        return_dur = sum(f.get("duration", 0) for f in return_flights) if return_flights else total_duration_min // 2

        outbound_hours = round(outbound_dur / 60, 2)
        return_hours = round(return_dur / 60, 2)

        # Extract carrier from first outbound flight segment
        first_seg = outbound_flights[0] if outbound_flights else flights[0]
        carrier_name = first_seg.get("airline", "")
        # Map airline name to IATA code where possible
        carrier_iata = self._name_to_iata(carrier_name) or carrier_name[:2].upper()

        # Build routing strings
        outbound_routing = self._build_routing(outbound_flights or flights[:len(flights)//2 or 1])
        return_routing = self._build_routing(return_flights or flights[len(flights)//2:])

        # Fallback routing from departure/arrival airport codes
        if not outbound_routing and flights:
            dep = flights[0].get("departure_airport", {}).get("id", "")
            arr = flights[0].get("arrival_airport", {}).get("id", "")
            outbound_routing = f"{dep}-{arr}" if dep and arr else ""

        return FlightOffer(
            origin=dep_date and flights[0].get("departure_airport", {}).get("id", "CAI") or "CAI",
            destination=flights[-1].get("arrival_airport", {}).get("id", "???") if flights else "???",
            cabin=cabin,
            carrier=carrier_iata,
            outbound_date=dep_date,
            return_date=ret_date,
            outbound_duration_hours=outbound_hours,
            return_duration_hours=return_hours,
            outbound_stops=max(0, len(outbound_flights) - 1) if outbound_flights else 0,
            return_stops=max(0, len(return_flights) - 1) if return_flights else 0,
            outbound_routing=outbound_routing,
            return_routing=return_routing,
            price_usd=float(price),
            source=self.name,
            raw=item,
        )

    def _build_routing(self, segments: list) -> str:
        if not segments:
            return ""
        codes = []
        for seg in segments:
            dep = seg.get("departure_airport", {}).get("id", "")
            if dep and (not codes or codes[-1] != dep):
                codes.append(dep)
            arr = seg.get("arrival_airport", {}).get("id", "")
            if arr:
                codes.append(arr)
        return "-".join(codes)

    @staticmethod
    def _name_to_iata(name: str) -> Optional[str]:
        """Best-effort airline name → IATA code mapping for major CAI-corridor carriers."""
        _MAP = {
            "egyptair": "MS",
            "emirates": "EK",
            "qatar airways": "QR",
            "air france": "AF",
            "british airways": "BA",
            "lufthansa": "LH",
            "delta": "DL",
            "turkish airlines": "TK",
            "united": "UA",
            "united airlines": "UA",
            "american airlines": "AA",
            "klm": "KL",
            "etihad": "EY",
            "etihad airways": "EY",
        }
        return _MAP.get(name.lower().strip())

    @staticmethod
    def _sample_dates(window_start: date, window_end: date, n: int) -> list[date]:
        """
        Return up to n sample departure dates, probing from window_start forward.

        Caps at the current booking horizon (~10 months / 305 days from today)
        so we never query dates that Google Flights hasn't opened yet.
        As months pass the horizon advances and more dates become available.
        """
        from datetime import date as date_cls
        today = date_cls.today()
        horizon = today + timedelta(days=305)

        effective_end = min(window_end, horizon)
        if effective_end < window_start:
            # Entire window is beyond booking horizon — nothing available yet
            return []

        total_days = (effective_end - window_start).days
        if total_days <= 0:
            return [window_start]

        # Space samples evenly across the AVAILABLE portion of the window
        step = max(7, total_days // (n + 1))  # minimum 7-day spacing
        dates = []
        for i in range(n):
            d = window_start + timedelta(days=step * (i + 1))
            if d > effective_end:
                break
            dates.append(d)

        # Always include window_start itself as first probe
        if window_start not in dates:
            dates.insert(0, window_start)

        return dates[:n]
