"""
GOOGLE FLIGHTS SOURCE — validation-only, rate-limited.

Used as cross-validation only — NOT as primary or secondary data source.
Google Flights is heavily JS-rendered; Playwright required.
Rate limit aggressively: 1 request per 15 seconds minimum.

PROTOTYPE_GRADE: Full XHR interception implementation pending.
Returns empty result with informational note — available for future implementation.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from radar.sources.base import BaseFlightSource, FlightOffer, SourceResult

logger = logging.getLogger(__name__)


class GoogleFlightsSource(BaseFlightSource):
    name = "google_flights"

    def search(
        self,
        origin: str,
        destination: str,
        cabin: str,
        window_start: date,
        window_end: date,
        carriers: Optional[list[str]] = None,
    ) -> SourceResult:
        # PROTOTYPE_GRADE: Google Flights scraping is legally ambiguous and
        # technically fragile. This source is reserved for future implementation
        # with explicit ToS review. Current use: return empty with informational message.
        logger.debug(
            "GoogleFlightsSource: prototype-grade, returning empty result. "
            "Use AmadeusSource for production data."
        )
        return SourceResult(
            source_name=self.name,
            offers=[],
            errors=["Google Flights source is prototype-grade — use for validation only after implementation"],
        )
