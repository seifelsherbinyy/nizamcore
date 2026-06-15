"""rss_source.py — Tier 2 RSS/API source connectors for TARIQ Career Radar.

Implements three connectors:
  - RemotiveSource     : Remotive RSS feed (XML)
  - WeWorkRemotelySource : We Work Remotely RSS feed (XML, no <company> tag)
  - RemoteOKSource     : RemoteOK JSON API (skips legal-notice header object)

All connectors:
  - Subclass BaseSource; implement fetch(constraints) -> SourceResult
  - NEVER raise; errors go into SourceResult.errors
  - Use datetime.now(timezone.utc) — never datetime.utcnow()
  - Use stdlib xml.etree.ElementTree for XML; json() for RemoteOK JSON
  - source_type = "rss_feed" for all three (consistent Tier 2 label)
  - Salary usually absent on RSS feeds → salary_usd_low/high = None
"""
from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

from .base import BaseSource, OpportunityRaw, SourceResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Date helpers (module-level for easy reuse)
# ---------------------------------------------------------------------------


def _parse_rfc2822(date_str: str) -> str:
    """Convert RFC 2822 date string to ISO-8601 UTC string.

    Example input:  "Tue, 14 Jun 2026 10:00:00 GMT"
    Example output: "2026-06-14T10:00:00+00:00Z"

    Falls back to datetime.now(timezone.utc).isoformat() + "Z" on any failure.
    """
    if not date_str:
        return datetime.now(timezone.utc).isoformat() + "Z"
    try:
        dt = datetime.strptime(date_str.strip(), "%a, %d %b %Y %H:%M:%S %Z")
        return dt.replace(tzinfo=timezone.utc).isoformat() + "Z"
    except Exception:
        return datetime.now(timezone.utc).isoformat() + "Z"


def _parse_epoch(ts) -> str:
    """Convert Unix epoch timestamp to ISO-8601 UTC string.

    Falls back to datetime.now(timezone.utc).isoformat() + "Z" on failure.
    """
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat() + "Z"
    except Exception:
        return datetime.now(timezone.utc).isoformat() + "Z"


# ---------------------------------------------------------------------------
# Shared RSS base class
# ---------------------------------------------------------------------------


class _RSSBase(BaseSource):
    """Shared fetch() template for RSS-format XML feeds.

    Subclasses override:
      - name   (str): source name for SourceResult.source_name
      - _parse_item(item: ET.Element) -> OpportunityRaw | None
    """

    name: str = "rss"
    feed_url: str = ""

    def __init__(self, config: dict) -> None:
        self.feed_url: str = config.get("feed_url", "")
        self.enabled: bool = bool(config.get("enabled", False))

    def fetch(self, constraints: dict) -> SourceResult:
        """Fetch and parse the RSS feed.

        Never raises — all errors captured in SourceResult.errors.
        """
        t_start = time.monotonic()
        opportunities: list[OpportunityRaw] = []
        errors: list[str] = []

        if not self.feed_url:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=["feed_url not configured"],
            )

        try:
            logger.info("%s: fetching %s", self.name, self.feed_url)
            resp = requests.get(self.feed_url, timeout=30)

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

            # Parse XML — catch malformed bytes here so we return a clean error
            try:
                root = ET.fromstring(resp.content)
            except ET.ParseError as exc:
                logger.error("%s: XML parse error — %s", self.name, exc)
                return SourceResult(
                    source_name=self.name,
                    opportunities=[],
                    errors=[f"XML parse error: {exc}"],
                    fetch_duration_sec=time.monotonic() - t_start,
                )

            # RSS uses <item>; Atom uses <entry> with namespace
            items = root.findall(".//item") or root.findall(
                ".//{http://www.w3.org/2005/Atom}entry"
            )

            for item in items:
                try:
                    opp = self._parse_item(item)
                    if opp is not None:
                        opportunities.append(opp)
                except Exception as exc:
                    errors.append(f"Item parse error: {exc}")

            logger.info("%s: parsed %d opportunities", self.name, len(opportunities))

        except requests.Timeout as exc:
            logger.error("%s: request timeout — %s", self.name, exc)
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Request timeout: {self.feed_url}"],
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

    def _parse_item(self, item: ET.Element) -> "OpportunityRaw | None":
        """Parse a single RSS <item> element into an OpportunityRaw.

        Subclasses must override this to handle feed-specific field names.
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# RemotiveSource
# ---------------------------------------------------------------------------


class RemotiveSource(_RSSBase):
    """Remotive RSS feed connector (SRC-02).

    Feed: https://remotive.com/remote-jobs/rss-feed
    XML items contain <title>, <link>, <company>, <pubDate>.
    """

    name = "remotive"

    def _parse_item(self, item: ET.Element) -> "OpportunityRaw | None":
        """Parse one Remotive <item> element."""
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        # Remotive includes a custom <company> element; fall back to "Unknown"
        company = (item.findtext("company") or "Unknown").strip()

        if not title or not link:
            return None  # Skip incomplete items silently

        return OpportunityRaw(
            title=title,
            company=company,
            location="Remote",
            source_url=link,
            source=self.name,
            source_type="rss_feed",
            salary_usd_low=None,
            salary_usd_high=None,
            raw_payload={"pub_date": _parse_rfc2822(pub_date)},
        )


# ---------------------------------------------------------------------------
# WeWorkRemotelySource
# ---------------------------------------------------------------------------


class WeWorkRemotelySource(_RSSBase):
    """We Work Remotely RSS feed connector (SRC-02).

    Feed: https://weworkremotely.com/remote-job-rss-feed
    XML items do NOT include a <company> element — company always "Unknown".
    Attribution required in operator credits/reports (WWR legal requirement).
    """

    name = "weworkremotely"

    def _parse_item(self, item: ET.Element) -> "OpportunityRaw | None":
        """Parse one We Work Remotely <item> element."""
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()

        if not title or not link:
            return None

        return OpportunityRaw(
            title=title,
            company="Unknown",  # WWR feed provides no company field
            location="Remote",
            source_url=link,
            source=self.name,
            source_type="rss_feed",
            salary_usd_low=None,
            salary_usd_high=None,
            raw_payload={"pub_date": _parse_rfc2822(pub_date)},
        )


# ---------------------------------------------------------------------------
# RemoteOKSource
# ---------------------------------------------------------------------------


class RemoteOKSource(BaseSource):
    """RemoteOK JSON API connector (SRC-02).

    API: https://remoteok.com/remote-api-jobs
    Returns a JSON array where:
      - First element is a legal-notice object (has "legal" key) — always skipped
      - Remaining objects are job records with fields:
          id, position, company, url, location, salary_min, salary_max, epoch, tags
    """

    name = "remoteok"

    def __init__(self, config: dict) -> None:
        self.api_url: str = config.get("api_url", "")
        self.enabled: bool = bool(config.get("enabled", False))

    def fetch(self, constraints: dict) -> SourceResult:
        """Fetch and parse the RemoteOK JSON API.

        Never raises — all errors captured in SourceResult.errors.
        """
        t_start = time.monotonic()
        opportunities: list[OpportunityRaw] = []
        errors: list[str] = []

        if not self.api_url:
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=["api_url not configured"],
            )

        try:
            logger.info("%s: fetching %s", self.name, self.api_url)
            resp = requests.get(self.api_url, timeout=30)

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

            if not isinstance(data, list):
                return SourceResult(
                    source_name=self.name,
                    opportunities=[],
                    errors=["Unexpected API response format (expected JSON array)"],
                    fetch_duration_sec=time.monotonic() - t_start,
                )

            for record in data:
                # Skip the legal-notice header object (has "legal" key)
                if "legal" in record:
                    continue

                try:
                    title = str(record.get("position") or record.get("title") or "").strip()
                    company = str(record.get("company") or "Unknown").strip()
                    source_url = str(record.get("url") or "").strip()
                    salary_min = record.get("salary_min")
                    salary_max = record.get("salary_max")
                    epoch_ts = record.get("epoch")
                    access_date = _parse_epoch(epoch_ts) if epoch_ts is not None else (
                        datetime.now(timezone.utc).isoformat() + "Z"
                    )

                    # Coerce salary to float or None
                    sal_low: float | None = float(salary_min) if salary_min is not None else None
                    sal_high: float | None = float(salary_max) if salary_max is not None else None

                    opp = OpportunityRaw(
                        title=title,
                        company=company,
                        location=str(record.get("location") or "Remote").strip(),
                        source_url=source_url,
                        source=self.name,
                        source_type="rss_feed",
                        salary_usd_low=sal_low,
                        salary_usd_high=sal_high,
                        raw_payload={"access_date": access_date, "tags": record.get("tags", [])},
                    )
                    opportunities.append(opp)

                except Exception as exc:
                    errors.append(f"Item parse error on record {record.get('id', '?')}: {exc}")

            logger.info("%s: parsed %d opportunities", self.name, len(opportunities))

        except requests.Timeout as exc:
            logger.error("%s: request timeout — %s", self.name, exc)
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Request timeout: {self.api_url}"],
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
        "rss_source.py — Tier 2 RSS/API connectors.\n"
        "Exports: RemotiveSource, WeWorkRemotelySource, RemoteOKSource"
    )
