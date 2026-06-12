"""
KIWI TEQUILA SOURCE — secondary aggregator.

Good Middle East / Egyptian market route coverage.
API docs: https://tequila.kiwi.com/portal/docs/tequila_api/search_api
Requires KIWI_API_KEY (free tier available at tequila.kiwi.com).

Used as: secondary validation source or primary when DATA_SOURCE=kiwi.

Cabin mapping note: Kiwi Tequila uses 'C' for business, 'W' for premium economy.
Coverage of premium economy on CAI-USA corridor should be validated at deployment.
"""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Optional

import requests

from radar.config import KIWI_API_KEY
from radar.sources.base import BaseFlightSource, FlightOffer, SourceResult

logger = logging.getLogger(__name__)

_KIWI_BASE = "https://api.tequila.kiwi.com"
_CABIN_MAP = {
    "BUSINESS": "C",
    "PREMIUM_ECONOMY": "W",
}


class KiwiSource(BaseFlightSource):
    name = "kiwi"

    def search(
        self,
        origin: str,
        destination: str,
        cabin: str,
        window_start: date,
        window_end: date,
        carriers: Optional[list[str]] = None,
    ) -> SourceResult:
        if not KIWI_API_KEY:
            return SourceResult(
                source_name=self.name,
                offers=[],
                errors=["KIWI_API_KEY not configured"],
            )

        kiwi_cabin = _CABIN_MAP.get(cabin.upper())
        if not kiwi_cabin:
            return SourceResult(
                source_name=self.name,
                offers=[],
                errors=[f"Unknown cabin: {cabin!r}"],
            )

        offers, errors = [], []
        start_t = time.time()

        for attempt in range(4):
            try:
                params = {
                    "fly_from": origin,
                    "fly_to": destination,
                    "date_from": window_start.strftime("%d/%m/%Y"),
                    "date_to": window_end.strftime("%d/%m/%Y"),
                    "return_from": (window_start + timedelta(days=9)).strftime("%d/%m/%Y"),
                    "return_to": window_end.strftime("%d/%m/%Y"),
                    "nights_in_dst_from": 9,
                    "nights_in_dst_to": 14,
                    "flight_type": "round",
                    "selected_cabins": kiwi_cabin,
                    "curr": "USD",
                    "limit": 20,
                    "sort": "price",
                }

                resp = requests.get(
                    f"{_KIWI_BASE}/v2/search",
                    params=params,
                    headers={"apikey": KIWI_API_KEY},
                    timeout=30,
                )

                if resp.status_code == 429:
                    self._exponential_backoff(attempt)
                    continue
                resp.raise_for_status()

                self._request_count += 1
                data = resp.json()
                offers = self._parse(data.get("data", []), cabin)
                break

            except requests.RequestException as exc:
                errors.append(f"Kiwi request error: {exc}")
                if attempt < 3:
                    self._exponential_backoff(attempt)

        return SourceResult(
            source_name=self.name,
            offers=offers,
            errors=errors,
            fetch_duration_sec=round(time.time() - start_t, 2),
        )

    def _parse(self, data: list, cabin: str) -> list[FlightOffer]:
        offers = []
        for item in data:
            try:
                price = float(item.get("price", 0))
                routes = item.get("route", [])
                if not routes:
                    continue

                outbound = [r for r in routes if not r.get("return", False)]
                inbound = [r for r in routes if r.get("return", False)]

                dep_ts = item.get("dTimeUTC", 0)
                ret_ts = item.get("aTimeUTC", 0)

                dep_date = date.fromtimestamp(dep_ts) if dep_ts else date.today()
                ret_date = date.fromtimestamp(ret_ts) if ret_ts else dep_date

                outbound_hours = self._calc_duration(outbound)
                return_hours = self._calc_duration(inbound)

                outbound_routing = "-".join(
                    [outbound[0].get("flyFrom", "")] + [r.get("flyTo", "") for r in outbound]
                ) if outbound else ""
                return_routing = "-".join(
                    [inbound[0].get("flyFrom", "")] + [r.get("flyTo", "") for r in inbound]
                ) if inbound else ""

                carrier = routes[0].get("airline", "??") if routes else "??"

                offers.append(FlightOffer(
                    origin=item.get("flyFrom", "CAI"),
                    destination=item.get("flyTo", "???"),
                    cabin=cabin,
                    carrier=carrier,
                    outbound_date=dep_date,
                    return_date=ret_date,
                    outbound_duration_hours=outbound_hours,
                    return_duration_hours=return_hours,
                    outbound_stops=max(0, len(outbound) - 1),
                    return_stops=max(0, len(inbound) - 1),
                    outbound_routing=outbound_routing,
                    return_routing=return_routing,
                    price_usd=price,
                    source=self.name,
                    raw=item,
                ))
            except Exception as exc:
                logger.debug("Kiwi parse error: %s", exc)
        return offers

    def _calc_duration(self, segments: list) -> float:
        total_minutes = 0
        for seg in segments:
            dur_str = seg.get("flyDuration", "0:0")
            parts = dur_str.split(":")
            if len(parts) == 2:
                total_minutes += int(parts[0]) * 60 + int(parts[1])
        return round(total_minutes / 60, 2)
