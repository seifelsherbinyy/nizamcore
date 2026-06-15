"""workable_source.py — Workable Public API connector for TARIQ Career Radar.

Fetches all public job postings from a Workable account without authentication.
Company name is extracted from the response root ("name" key), not from config.

Endpoint:
    GET https://apply.workable.com/api/v1/widget/accounts/{account_subdomain}?details=true

No authentication required for public job listings.

Note: Salary data is NOT available in the Workable API response; salary_usd_low
and salary_usd_high are always None (normalization confidence = LOW).
Company name comes from data["name"] (response root), same for all jobs
returned by the account. A config fallback is kept for robustness.

Pure stdlib + requests (already pinned in requirements.txt).
"""
from __future__ import annotations

import logging
import time

import requests

from .base import BaseSource, OpportunityRaw, SourceResult

logger = logging.getLogger(__name__)

_WORKABLE_BASE = (
    "https://apply.workable.com/api/v1/widget/accounts/{account_subdomain}?details=true"
)


class WorkableSource(BaseSource):
    """Workable Public API connector (public, no auth required).

    Returns all active job postings for the configured account_subdomain.
    Company name is sourced from the API response root (data["name"]);
    salary data is not available in the Workable public API.
    """

    name = "workable"

    def __init__(self, config: dict) -> None:
        """Initialise from per-account config dict.

        Args:
            config: Must contain at least "account_subdomain".
                    Optional: "company_name" (fallback if response root "name" absent),
                              "enabled" (bool, default False).
        """
        self.account_subdomain: str = config.get("account_subdomain", "")
        # Company name comes from API response root; keep config fallback for robustness
        self.company_name_fallback: str = config.get("company_name", "")
        self.enabled: bool = bool(config.get("enabled", False))
        self.url: str = _WORKABLE_BASE.format(account_subdomain=self.account_subdomain)

    def fetch(self, constraints: dict) -> SourceResult:
        """Fetch all jobs from the Workable account.

        Company name is read from data["name"] (response root), not per-job.
        Salary fields are always None (Workable API does not expose salary).

        Never raises — all errors are captured in SourceResult.errors.

        Returns:
            SourceResult with opportunities list and optional errors.
            rate_limited=True when the API responds with HTTP 429.
        """
        t_start = time.monotonic()
        opportunities: list[OpportunityRaw] = []
        errors: list[str] = []

        if not self.account_subdomain:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=["account_subdomain not configured"],
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

            # Company name comes from response root — same for all jobs
            company_name = data.get("name", "") or self.company_name_fallback

            for job in data.get("jobs", []):
                try:
                    location_obj = job.get("location", {})
                    region = location_obj.get("region", "")
                    city = location_obj.get("city") or ""
                    country = location_obj.get("country", "")
                    location_str = ", ".join(filter(None, [region, city, country]))

                    opp = OpportunityRaw(
                        title=job.get("title", ""),
                        company=company_name,
                        location=location_str,
                        source_url=job.get("job_url", ""),
                        source=self.name,
                        source_type="ats",
                        salary_usd_low=None,   # Workable API does not expose salary
                        salary_usd_high=None,  # Salary confidence = LOW at normalization
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
    print("WorkableSource: Workable Public API connector")
