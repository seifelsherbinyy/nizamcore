"""ashby_source.py — Ashby Job Posting API connector for TARIQ Career Radar.

Fetches all public job postings from an Ashby job board without authentication.
Includes compensation data when available (salary_usd_low/high = HIGH confidence).

Endpoint:
    GET https://api.ashbyhq.com/posting-api/job-board/{board_name}?includeCompensation=true

No authentication required for public boards.

Note: Company name must come from config (Ashby job postings do not embed
the company name per-job; use board_name/company_name from caller config).

Pure stdlib + requests (already pinned in requirements.txt).
"""
from __future__ import annotations

import logging
import time

import requests

from .base import BaseSource, OpportunityRaw, SourceResult

logger = logging.getLogger(__name__)

_ASHBY_BASE = "https://api.ashbyhq.com/posting-api/job-board/{board_name}"


class AshbySource(BaseSource):
    """Ashby Job Posting API connector (public, no auth required).

    Returns all active job postings for the configured board_name.
    Salary fields are extracted from compensation.salary.min/.max when
    currency == "USD" — confidence is HIGH at normalization time.
    Company name must come from config (Ashby API does not return it per-job).
    """

    name = "ashby"

    def __init__(self, config: dict) -> None:
        """Initialise from per-board config dict.

        Args:
            config: Must contain at least "board_name".
                    Optional: "company_name" (Ashby does not return company per-job),
                              "include_compensation" (bool, default True),
                              "enabled" (bool, default False).
        """
        self.board_name: str = config.get("board_name", "")
        self.company_name: str = config.get("company_name", "")
        self.include_compensation: bool = bool(config.get("include_compensation", True))
        self.enabled: bool = bool(config.get("enabled", False))
        self.url: str = _ASHBY_BASE.format(board_name=self.board_name)
        if self.include_compensation:
            self.url += "?includeCompensation=true"

    def fetch(self, constraints: dict) -> SourceResult:
        """Fetch all jobs from the Ashby job board.

        Never raises — all errors are captured in SourceResult.errors.

        Returns:
            SourceResult with opportunities list and optional errors.
            rate_limited=True when the API responds with HTTP 429.
            Salary fields populated from compensation.salary when currency == "USD".
        """
        t_start = time.monotonic()
        opportunities: list[OpportunityRaw] = []
        errors: list[str] = []

        if not self.board_name:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=["board_name not configured"],
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

            for posting in data.get("jobPostings", []):
                try:
                    # Extract salary from compensation.salary — only if currency == "USD"
                    comp = posting.get("compensation", {})
                    salary_obj = comp.get("salary", {})
                    currency = salary_obj.get("currency", "USD")
                    if currency == "USD":
                        salary_usd_low = salary_obj.get("min")
                        salary_usd_high = salary_obj.get("max")
                    else:
                        salary_usd_low = None
                        salary_usd_high = None

                    opp = OpportunityRaw(
                        title=posting.get("title", ""),
                        company=self.company_name,
                        location=posting.get("location", ""),
                        source_url=posting.get("url", ""),
                        source=self.name,
                        source_type="ats",
                        salary_usd_low=salary_usd_low,
                        salary_usd_high=salary_usd_high,
                        raw_payload=posting,
                    )
                    opportunities.append(opp)
                except Exception as parse_exc:
                    errors.append(
                        f"Parse error on posting {posting.get('id', '?')}: {parse_exc}"
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
    print("AshbySource: Ashby Job Posting API connector")
