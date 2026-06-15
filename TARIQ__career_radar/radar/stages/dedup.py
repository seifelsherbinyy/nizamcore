"""dedup.py — Phase 4 dedup orchestrator stage for TARIQ Career Radar.

Provides run_dedup_pass(): the full deduplication pipeline that combines
SQLite cross-run exact dedup (via DedupeEngine) with within-run fuzzy title
matching (fuzzy_match_opportunities) and the 30-day freshness repost rule
(is_fresh_repost).

Intended to be called from radar/stages/fetch.py after all sources are
combined into a flat list.
"""
from __future__ import annotations

import datetime
import sqlite3
from pathlib import Path

from radar.dedup_engine import (
    DedupeEngine,
    compute_dedup_key,
    fuzzy_match_opportunities,
    is_fresh_repost,
)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _fetch_first_seen(
    db_path: Path,
    title_c: str,
    company_c: str,
    location_c: str,
) -> str | None:
    """Return first_seen_date ISO string for the given canonical key, or None.

    Performs a single SELECT against seen_roles — used by run_dedup_pass to
    retrieve the first_seen date for the freshness-rule check after
    engine.check_or_add() reports is_duplicate=True.

    Args:
        db_path:    Path to the SQLite seen_roles.sqlite database.
        title_c:    Normalized (canonical) title string.
        company_c:  Normalized company string.
        location_c: Normalized location string.

    Returns:
        ISO 8601 string (first_seen_date column) or None if row not found.
    """
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute(
            "SELECT first_seen_date FROM seen_roles "
            "WHERE title_canonical=? AND company_canonical=? AND location_canonical=?",
            (title_c, company_c, location_c),
        ).fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_dedup_pass(
    opportunities: list[dict],
    db_path: Path,
) -> list[dict]:
    """Apply full dedup pipeline to a list of sourced opportunities.

    Pipeline per opportunity:
      1. call engine.check_or_add() — exact-key cross-run check
         a. If NOT duplicate → continue to step 2
         b. If IS duplicate → fetch first_seen_date from DB
            - If is_fresh_repost(first_seen, access_date) → treat as new (continue to step 2)
            - Else → skip (suppress)
      2. fuzzy_match_opportunities(opp, seen_in_run) — within-run fuzzy check
         - If IS match → skip (suppress within-run dup)
         - Else → add to results AND seen_in_run buffer

    A single DedupeEngine instance is used for the entire call (avoids
    opening/closing the DB file-handle per opportunity).

    Args:
        opportunities: list of opportunity dicts with at least title/company/location
        db_path:       Path to SQLite seen_roles.sqlite

    Returns:
        list[dict] — deduplicated opportunities (unique, in order of first appearance)
    """
    engine = DedupeEngine(db_path)
    results: list[dict] = []
    seen_in_run: list[dict] = []

    for opp in opportunities:
        # --- Step 1: cross-run seen-store check ---
        check_result = engine.check_or_add(opp)

        if check_result["is_duplicate"]:
            # Determine access_date for freshness calculation
            access_date = opp.get(
                "access_date",
                datetime.datetime.utcnow().isoformat() + "Z",
            )

            # Fetch first_seen_date from DB (check_or_add does not expose it)
            title_c, company_c, location_c = compute_dedup_key(
                opp.get("title", ""),
                opp.get("company", ""),
                opp.get("location", ""),
            )
            first_seen = _fetch_first_seen(db_path, title_c, company_c, location_c)

            if first_seen and is_fresh_repost(first_seen, access_date):
                # Genuine repost — treat as new; fall through to fuzzy check below
                pass
            else:
                # Still within freshness window — suppress
                continue

        # --- Step 2: within-run fuzzy dedup ---
        is_match, _score = fuzzy_match_opportunities(opp, seen_in_run)
        if is_match:
            # Fuzzy duplicate within this run — suppress
            continue

        # Passes both checks — keep it
        results.append(opp)
        seen_in_run.append(opp)

    return results


# ---------------------------------------------------------------------------
# CLI entry point (CONVENTIONS.md: every module must have an __main__ block)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("run_dedup_pass: import and call from fetch.py")
