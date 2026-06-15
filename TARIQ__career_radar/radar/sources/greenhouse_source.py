"""greenhouse_source.py — Greenhouse Job Board API connector for TARIQ Career Radar.

Fetches all public job postings from a Greenhouse job board without authentication.

Endpoint:
    GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true

No authentication required for public boards.
Pure stdlib + requests (already pinned in requirements.txt).
"""
from __future__ import annotations

import logging
import time

import requests

from .base import BaseSource, OpportunityRaw, SourceResult

logger = logging.getLogger(__name__)

_GREENHOUSE_BASE = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"


class GreenhouseSource(BaseSource):
    """Greenhouse Job Board API connector (public, no auth required).

    Returns all active job postings for the configured board_token.
    Salary fields (salary_min, salary_max) are present when the employer
    chooses to publish them — confidence is HIGH at normalization time.
    """

    name = "greenhouse"

    def __init__(self, config: dict) -> None:
        """Initialise from per-board config dict.

        Args:
            config: Must contain at least "board_token".
                    Optional: "company_name" (fallback when response omits it),
                              "enabled" (bool, default False).
        """
        self.board_token: str = config.get("board_token", "")
        self.company_name: str = config.get("company_name", "")
        self.enabled: bool = bool(config.get("enabled", False))
        self.url: str = _GREENHOUSE_BASE.format(board_token=self.board_token)

    def fetch(self, constraints: dict) -> SourceResult:
        """Fetch all jobs from the Greenhouse board.

        Never raises — all errors are captured in SourceResult.errors.

        Returns:
            SourceResult with opportunities list and optional errors.
            rate_limited=True when the API responds with HTTP 429.
        """
        t_start = time.monotonic()
        opportunities: list[OpportunityRaw] = []
        errors: list[str] = []

        if not self.board_token:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=["board_token not configured"],
            )

        try:
            logger.info("%s: fetching %s", self.name, self.url)
            resp = requests.get(self.url, timeout=30)

            if resp.status_code == 429:
                logger.warning("%s: rate limited (429)", self.name)
                return SourceResult(
                    source_name=self.name,
                    opportunities=[],
                    errors=["Rate limited (429); will retry next run"],
                    rate_limited=True,
                    fetch_duration_sec=time.monotonic() - t_start,
                )

            resp.raise_for_status()
            data = resp.json()

            for job in data.get("jobs", []):
                try:
                    opp = OpportunityRaw(
                        title=job.get("title", ""),
                        company=job.get("company_name") or self.company_name,
                        location=job.get("location", {}).get("name", ""),
                        source_url=job.get("absolute_url", ""),
                        source=self.name,
                        source_type="ats",
                        salary_usd_low=job.get("salary_min"),
                        salary_usd_high=job.get("salary_max"),
                        raw_payload=job,
                    )
                    opportunities.append(opp)
                except Exception as parse_exc:
                    errors.append(
                        f"Parse error on job {job.get('id', '?')}: {parse_exc}"
                    )

            logger.info(
                "%s: fetched %d opportunities", self.name, len(opportunities)
            )

        except requests.Timeout as exc:
            logger.error("%s: request timeout — %s", self.name, exc)
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Request timeout: {exc}"],
                fetch_duration_sec=time.monotonic() - t_start,
            )
        except Exception as exc:
            logger.error("%s: unexpected error — %s", self.name, exc)
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Unexpected error: {type(exc).__name__}: {exc}"],
                fetch_duration_sec=time.monotonic() - t_start,
            )

        return SourceResult(
            source_name=self.name,
            opportunities=opportunities,
            errors=errors,
            rate_limited=False,
            fetch_duration_sec=time.monotonic() - t_start,
        )


if __name__ == "__main__":
    print(
        "GreenhouseSource: fetches public Greenhouse job boards.\n"
        "Usage: GreenhouseSource({'board_token': 'acme', 'enabled': True}).fetch({})"
    )
