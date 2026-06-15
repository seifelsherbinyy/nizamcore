"""base.py — Abstract BaseSource interface + shared dataclasses for TARIQ Career Radar.

Mirrors the MARSAD__flight_radar/radar/sources/base.py pattern exactly.
All concrete connectors inherit from BaseSource and must implement fetch().

Pure stdlib — no new dependencies.
"""
from __future__ import annotations

import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass
class OpportunityRaw:
    """Raw opportunity record before normalization.

    Populated by each ATS connector from the platform's native JSON.
    Normalization (title/company/location canonicalization, salary confidence
    tagging, remote_status inference, UUID assignment) happens in the fetch
    orchestrator (radar.stages.fetch).
    """

    title: str
    company: str
    location: str
    source_url: str
    source: str
    source_type: str = "ats"
    salary_usd_low: Optional[float] = None
    salary_usd_high: Optional[float] = None
    raw_payload: Optional[dict] = None  # Original JSON for audit trail


@dataclass
class SourceResult:
    """Aggregated result returned by one ATS connector after fetch().

    Connectors NEVER raise — all errors are captured in .errors.
    If rate_limited is True the caller must not retry in the same run.
    """

    source_name: str
    opportunities: list  # list[OpportunityRaw]
    errors: list = field(default_factory=list)  # list[str]
    rate_limited: bool = False
    fetch_duration_sec: float = 0.0


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class BaseSource(ABC):
    """Abstract base for all ATS source connectors.

    Subclasses must set a class-level `name` attribute and implement fetch().
    """

    name: str = "base"

    @abstractmethod
    def fetch(self, constraints: dict) -> SourceResult:
        """Fetch opportunities from the source.

        Args:
            constraints: Caller-supplied filter hints (e.g., location, keywords).
                         Connectors MAY use them for server-side filtering but
                         are not required to.  Downstream stages filter further.

        Returns:
            SourceResult with opportunities and/or errors.

        Contract: NEVER raise an exception — return errors in SourceResult.errors.
        """
        ...

    def _is_enabled(self, config: dict) -> bool:
        """Return True when config["enabled"] is truthy."""
        return bool(config.get("enabled", False))

    def _rate_limited_sleep(self) -> None:
        """Sleep a random stagger delay between requests (good-citizen throttle)."""
        delay = random.uniform(0.5, 2.0)
        logger.debug("%s: sleeping %.1fs (rate-limit stagger)", self.name, delay)
        time.sleep(delay)

    def _exponential_backoff(self, attempt: int, base_sec: float = 2.0) -> None:
        """Backoff on 429/503: 2 s, 4 s, 8 s, 16 s, ...

        Args:
            attempt: 0-based retry attempt index.
            base_sec: Base sleep duration before exponential scaling.
        """
        delay = base_sec * (2 ** attempt)
        logger.warning(
            "%s: rate limited — backing off %.0fs (attempt %d)",
            self.name,
            delay,
            attempt + 1,
        )
        time.sleep(delay)


if __name__ == "__main__":
    print("BaseSource: abstract interface. Implement a concrete subclass.")
