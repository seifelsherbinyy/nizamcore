"""manual_import_source.py — Operator JSONL manual import source for TARIQ Career Radar.

Implements SRC-03: reads a gitignored JSONL file at data/manual_imports.jsonl,
validates each record, converts hourly salary to annual where flagged, and returns
normalized OpportunityRaw records in a SourceResult.

Error contract: NEVER raises — all errors returned in SourceResult.errors.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from .base import BaseSource, OpportunityRaw, SourceResult

logger = logging.getLogger(__name__)

# Annualization factor: 40 hrs/week * 52 weeks/year
_HOURS_TO_ANNUAL = 40 * 52


class ManualImportSource(BaseSource):
    """Operator-provided JSONL import source (SRC-03).

    Reads a gitignored JSONL file (one JSON record per line).
    Gracefully handles: missing file, malformed JSON, missing required fields.

    JSONL record schema (all optional except title + source_url):
      title           str  — job title (required)
      source_url      str  — link to the opportunity (required)
      company         str  — defaults to "Unknown"
      location        str  — defaults to "Remote"
      salary_usd_low  num  — base salary or hourly rate
      salary_usd_high num  — top salary or hourly rate
      salary_per      str  — "annual" (default) | "hour" | "project"
      role_category   str  — optional categorization
      notes           str  — operator notes (stored in raw_payload)
    """

    name = "manual"

    def __init__(self, config: dict) -> None:
        self.import_file_path = Path(config.get("import_file_path", ""))
        self.enabled = bool(config.get("enabled", False))

    def fetch(self, constraints: dict) -> SourceResult:
        """Read JSONL file and return normalized OpportunityRaw records.

        Returns SourceResult; never raises.
        """
        opportunities: list[OpportunityRaw] = []
        errors: list[str] = []

        # Graceful: file not found is a normal condition
        if not self.import_file_path.exists():
            logger.info(
                "manual: import file not found at %s — no manual imports this run",
                self.import_file_path,
            )
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Import file not found: {self.import_file_path}"],
            )

        try:
            with open(self.import_file_path, "r", encoding="utf-8") as fh:
                for line_num, line in enumerate(fh, start=1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue  # Skip blank lines and comment lines

                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        errors.append(f"Line {line_num}: invalid JSON — {exc}")
                        continue

                    # Validate required fields
                    if "title" not in record or "source_url" not in record:
                        errors.append(
                            f"Line {line_num}: missing required field (title, source_url)"
                        )
                        continue

                    # Salary: convert hourly to annual if flagged
                    salary_low: Optional[float] = record.get("salary_usd_low")
                    salary_high: Optional[float] = record.get("salary_usd_high")
                    salary_per = (record.get("salary_per") or "annual").lower()

                    if salary_per == "hour" and salary_low is not None:
                        annual_low = salary_low * _HOURS_TO_ANNUAL
                        annual_high = (
                            salary_high * _HOURS_TO_ANNUAL
                            if salary_high is not None
                            else None
                        )
                        logger.debug(
                            "manual line %d: converted $%.0f–$%.0f/hr to annual $%.0f–$%.0f",
                            line_num,
                            salary_low,
                            salary_high or 0,
                            annual_low,
                            annual_high or 0,
                        )
                        salary_low = annual_low
                        salary_high = annual_high

                    opp = OpportunityRaw(
                        title=record.get("title", ""),
                        company=record.get("company", "Unknown"),
                        location=record.get("location", "Remote"),
                        source_url=record.get("source_url", ""),
                        source=self.name,
                        source_type="manual",
                        salary_usd_low=salary_low,
                        salary_usd_high=salary_high,
                        raw_payload=record,
                    )
                    opportunities.append(opp)

        except Exception as exc:
            # Catch UnicodeDecodeError, PermissionError, or any other file-level error
            return SourceResult(
                source_name=self.name,
                opportunities=[],
                errors=[f"Error reading import file: {type(exc).__name__}: {exc}"],
            )

        logger.info(
            "manual: loaded %d opportunities (%d errors) from %s",
            len(opportunities),
            len(errors),
            self.import_file_path,
        )
        return SourceResult(
            source_name=self.name,
            opportunities=opportunities,
            errors=errors,
        )


if __name__ == "__main__":
    print(
        "ManualImportSource: reads a gitignored JSONL file of operator-provided opportunities.\n"
        "Usage: ManualImportSource({'import_file_path': 'data/manual_imports.jsonl'}).fetch({})"
    )
