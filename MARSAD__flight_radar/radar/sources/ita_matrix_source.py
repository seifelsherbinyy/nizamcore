"""
ITA MATRIX SOURCE — OPTIONAL, requires explicit ToS review before enabling.

RISK FLAG: HIGH
Google's Terms of Service prohibit automated access to ITA Matrix (matrix.itasoftware.com)
without prior written permission from Google. Bot detection will likely block
headless browser access within 24 hours of deployment.

TO ENABLE:
1. Review ITA Matrix / Google Terms of Service
2. Set ITA_MATRIX_ENABLED=true in .env ONLY after accepting the ToS risk
3. Set DATA_SOURCE=ita_matrix in .env

RECOMMENDED ALTERNATIVE: Use SerpApiSource (DATA_SOURCE=serpapi, current default) for terms-compliant access via the SerpApi Google Flights API.

This implementation is provided for completeness and for users who have obtained
appropriate authorization. It is disabled by default and cannot be activated
without the explicit ITA_MATRIX_ENABLED=true flag.
"""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Optional

from radar.config import ITA_MATRIX_ENABLED, ITA_MATRIX_URL
from radar.sources.base import BaseFlightSource, FlightOffer, SourceResult

logger = logging.getLogger(__name__)


class ITAMatrixSource(BaseFlightSource):
    name = "ita_matrix"

    def __init__(self) -> None:
        if not ITA_MATRIX_ENABLED:
            logger.warning(
                "ITAMatrixSource is disabled. Set ITA_MATRIX_ENABLED=true in .env "
                "only after reviewing Google's ToS. Using AmadeusSource instead."
            )

    def search(
        self,
        origin: str,
        destination: str,
        cabin: str,
        window_start: date,
        window_end: date,
        carriers: Optional[list[str]] = None,
    ) -> SourceResult:
        if not ITA_MATRIX_ENABLED:
            return SourceResult(
                source_name=self.name,
                offers=[],
                errors=[
                    "ITA Matrix is disabled. Set ITA_MATRIX_ENABLED=true in .env after ToS review. "
                    "Use DATA_SOURCE=serpapi (SerpApi Google Flights) for terms-compliant access."
                ],
            )

        # PROTOTYPE — actual Playwright automation requires:
        # 1. playwright install chromium
        # 2. Handling Google's CAPTCHA and bot detection (HIGH risk of failure)
        # 3. XHR interception to capture fare data (not HTML scraping)
        # This implementation returns an empty result with a warning.
        # Full Playwright implementation can be added after ToS clearance.

        logger.warning(
            "ITA Matrix source enabled but Playwright automation is PROTOTYPE_GRADE. "
            "Full implementation requires manual ToS review and CAPTCHA handling strategy. "
            "Returning empty result — switch to DATA_SOURCE=serpapi for production use."
        )

        return SourceResult(
            source_name=self.name,
            offers=[],
            errors=[
                "ITA Matrix Playwright automation is prototype-grade. "
                "Production implementation requires ToS clearance. "
                "See README for SerpApi swap instructions (DATA_SOURCE=serpapi)."
            ],
        )
