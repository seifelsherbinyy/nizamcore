"""
Abstract base for all flight data sources + shared rate-limit utilities.

All sources must return List[FlightOffer]. The constraint engine is applied
AFTER fetch — sources return raw results; callers filter with apply_constraints().
"""

from __future__ import annotations

import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from radar.config import FETCH_DELAY_MIN_SEC, FETCH_DELAY_MAX_SEC

logger = logging.getLogger(__name__)


@dataclass
class FlightOffer:
    """Normalised flight offer returned by every source."""
    origin: str
    destination: str
    cabin: str
    carrier: str
    outbound_date: date
    return_date: date
    outbound_duration_hours: float
    return_duration_hours: float
    outbound_stops: int
    return_stops: int
    outbound_routing: str       # e.g. "CAI-DXB-JFK"
    return_routing: str         # e.g. "JFK-DXB-CAI"
    price_usd: float
    source: str
    price_egp: Optional[float] = None
    price_eur: Optional[float] = None
    data_quality: str = "confirmed"
    raw: dict = field(default_factory=dict)


@dataclass
class SourceResult:
    source_name: str
    offers: list[FlightOffer]
    errors: list[str] = field(default_factory=list)
    rate_limited: bool = False
    fetch_duration_sec: float = 0.0


class SourceExhausted(Exception):
    """
    Raised when a source has hit sustained rate-limiting (consecutive full
    backoff-cycle failures) — signals callers to abort the run early instead of
    grinding through every remaining combination for the full backoff duration
    each. Typically means an API quota is exhausted or the credential is invalid.
    """


class BaseFlightSource(ABC):
    """Abstract base class for all flight data sources."""

    name: str = "base"
    _request_count: int = 0

    @abstractmethod
    def search(
        self,
        origin: str,
        destination: str,
        cabin: str,
        window_start: date,
        window_end: date,
        carriers: Optional[list[str]] = None,
    ) -> SourceResult:
        """
        Search for flights matching the given parameters.
        Returns raw results — caller applies constraint filtering.
        """
        ...

    def _rate_limited_sleep(self) -> None:
        """Sleep a randomized delay between requests to the same domain."""
        delay = random.uniform(FETCH_DELAY_MIN_SEC, FETCH_DELAY_MAX_SEC)
        logger.debug("%s: sleeping %.1fs (rate limit)", self.name, delay)
        time.sleep(delay)

    def _exponential_backoff(self, attempt: int, base_sec: float = 2.0) -> None:
        """Exponential backoff: 2s, 4s, 8s, 16s on 429/503 responses."""
        delay = base_sec * (2 ** attempt)
        logger.warning("%s: rate limited — backing off %.0fs (attempt %d)", self.name, delay, attempt + 1)
        time.sleep(delay)

    def _parse_duration_to_hours(self, iso_duration: str) -> float:
        """
        Parse ISO 8601 duration string (e.g. 'PT14H30M') to decimal hours.
        Returns 0.0 on parse failure.
        """
        import re
        match = re.match(r"PT?(?:(\d+)H)?(?:(\d+)M)?", iso_duration)
        if not match:
            return 0.0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        return round(hours + minutes / 60, 2)
