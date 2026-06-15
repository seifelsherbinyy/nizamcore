"""lever_source.py — Lever Postings API connector for TARIQ Career Radar.

Fetches all public job postings from a Lever job board without authentication.
Uses skip/limit pagination to retrieve all pages.

Endpoint:
    GET https://api.lever.co/v0/postings/{site}?mode=json&skip={skip}&limit={limit}

No authentication required for public boards.

Note: Company name must come from config (Lever API does not return it in
job posting responses — it assumes the caller knows their own company name).

Pure stdlib + requests (already pinned in requirements.txt).
"""
from __future__ import annotations

import logging
import time

import requests

from .base import BaseSource, OpportunityRaw, SourceResult

logger = logging.getLogger(__name__)

_LEVER_BASE = "https://api.lever.co/v0/postings/{site}?mode=json&skip={skip}&limit={limit}"


class LeverSource(BaseSource):
    """Lever Postings API connector (public, no auth required).

    Paginates through all postings using skip/limit query parameters.
    Salary data is NOT available in the Lever API response; salary_usd_low
    and salary_usd_high are always None (normalization confidence = LOW).
    """

    name = "lever"

    def __init__(self, config: dict) -> None:
        """Initialise from per-board config dict.

        Args:
            config: Must contain at least "site" (Lever account subdomain).
                    "company_name" is injected into every opportunity
                    (Lever API does not include it in responses).
                    Optional: "enabled" (bool, default False).
        """
        # Note: company name must come from config — Lever API does not return it.
        self.site: str = config.get("site", "")
        self.company_name: str = config.get("company_name", "Unknown")
        self.enabled: bool = bool(config.get("enabled", False))

    def fetch(self, constraints: dict) -> SourceResult:
        """Fetch all job postings from Lever via paginated requests.

        Pagination: skip=0, limit=100, stops when response is empty or
        len(page) < limit. Maximum 100 pages to prevent infinite loops.

        Never raises — all errors are captured in SourceResult.errors.

        Returns:
            SourceResult with opportunities list and optional errors.
            rate_limited=True when the API responds with HTTP 429.
        """
        t_start = time.monotonic()
        opportunities: list[OpportunityRaw] = []
        errors: list[str] = []

        if not self.site:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=["site not configured"],
            )

        limit = 100
        max_pages = 100
        skip = 0

        for page_num in range(max_pages):
            url = _LEVER_BASE.format(site=self.site, skip=skip, limit=limit)
            logger.info("%s: fetching page %d — %s", self.name, page_num + 1, url)

            try:
                resp = requests.get(url, timeout=30)

                if resp.status_code == 429:
                    logger.warning(
                        "%s: rate limited (429) on page %d — stopping fetch",
                        self.name,
                        page_num + 1,
                    )
                    return SourceResult(
                        source_name=self.name,
                        opportunities=opportunities,
                        errors=["Rate limited (429); will retry next run"],
                        rate_limited=True,
                        fetch_duration_sec=time.monotonic() - t_start,
                    )

                resp.raise_for_status()
                page_data = resp.json()

                if not page_data:
                    # Empty response — no more postings
                    break

                for posting in page_data:
                    try:
                        opp = OpportunityRaw(
                            title=posting.get("text", ""),
                            # Company name must come from config —
                            # Lever API does not return it.
                            company=self.company_name,
                            location=posting.get("categories", {}).get("location", ""),
                            source_url=posting.get("url", ""),
                            source=self.name,
                            source_type="ats",
                            salary_usd_low=None,   # Lever API does not expose salary
                            salary_usd_high=None,  # Salary confidence = LOW at normalization
                            raw_payload=posting,
                        )
                        opportunities.append(opp)
                    except Exception as parse_exc:
                        errors.append(
                            f"Parse error on posting {posting.get('id', '?')}: {parse_exc}"
                        )

                if len(page_data) < limit:
                    # Last page — fewer results than requested
                    break

                skip += limit

            except requests.Timeout as exc:
                logger.error(
                    "%s: request timeout on page %d — %s", self.name, page_num + 1, exc
                )
                errors.append(f"Request timeout on page {page_num + 1}: {exc}")
                break
            except Exception as exc:
                logger.error(
                    "%s: unexpected error on page %d — %s", self.name, page_num + 1, exc
                )
                errors.append(
                    f"Unexpected error on page {page_num + 1}: {type(exc).__name__}: {exc}"
                )
                break

        logger.info(
            "%s: fetched %d opportunities across %d page(s)",
            self.name,
            len(opportunities),
            page_num + 1 if "page_num" in dir() else 0,
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
        "LeverSource: fetches public Lever job postings with skip/limit pagination.\n"
        "Usage: LeverSource({'site': 'acme', 'company_name': 'Acme', 'enabled': True}).fetch({})"
    )
