"""dedup_engine.py — SQLite-backed seen-role store + normalization for TARIQ Career Radar.

Maintains a persistent index of normalized (title, company, location) tuples to detect
duplicate opportunities across runs. Uses stdlib sqlite3 only — no new dependencies.

Pure stdlib.
"""
from __future__ import annotations

import datetime
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

# Default DB path (relative to module root: TARIQ__career_radar/)
_MODULE_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_PATH = _MODULE_ROOT / "data" / "seen_roles.sqlite"

# ---------------------------------------------------------------------------
# Phase 4 constants (fuzzy dedup + freshness rule)
# ---------------------------------------------------------------------------
FUZZY_THRESHOLD: float = 0.88        # Minimum token_sort_ratio to flag as duplicate
REPOST_FRESHNESS_DAYS: int = 30      # Days before a re-seen role is treated as new


# ---------------------------------------------------------------------------
# Normalization functions (deterministic — same input, same output, every run)
# ---------------------------------------------------------------------------


def normalize_title(title: str) -> str:
    """Normalize job title: NFKD Unicode decomposition, strip diacritics, lowercase.

    Example:
        normalize_title("AI Operations Spécialist") -> "ai operations specialist"
        normalize_title("AI Ops Manager")            -> "ai ops manager"
    """
    norm = unicodedata.normalize("NFKD", title.strip())
    # Remove combining diacritical characters (e.g. accent marks) — keep base letters
    ascii_base = "".join(c for c in norm if not unicodedata.combining(c))
    return ascii_base.lower()


def normalize_company(company: str) -> str:
    """Normalize company name: strip legal suffixes, deduplicate whitespace, lowercase.

    Recognized suffixes (case-insensitive): , inc / , inc. / , ltd / , ltd. /
    , llc / , llc. / (space) inc / (space) inc. / (space) ltd / (space) ltd. /
    (space) llc / (space) llc.

    Example:
        normalize_company("Acme, Inc.")  -> "acme"
        normalize_company("Acme LLC")    -> "acme"
        normalize_company("BigCorp Ltd") -> "bigcorp"
    """
    suffixes = [
        ", inc.",
        ", inc",
        ", ltd.",
        ", ltd",
        ", llc.",
        ", llc",
        " inc.",
        " inc",
        " ltd.",
        " ltd",
        " llc.",
        " llc",
    ]
    name = company.strip().lower()
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
            break  # only strip one suffix
    # Collapse internal whitespace
    name = " ".join(name.split())
    return name


def normalize_location(location: str) -> str:
    """Normalize location string: lowercase, collapse "remote" variants.

    If the location contains the word "remote" (anywhere), returns "remote".
    Otherwise returns the lowercased, stripped location.

    Example:
        normalize_location("Remote / Worldwide") -> "remote"
        normalize_location("San Francisco, CA")  -> "san francisco, ca"
    """
    if not location:
        return ""
    loc = location.strip().lower()
    if "remote" in loc:
        return "remote"
    return loc


def compute_dedup_key(title: str, company: str, location: str) -> tuple[str, str, str]:
    """Return normalized (title, company, location) tuple for dedup lookup.

    This function is deterministic: identical inputs always produce identical outputs
    across Python processes, Python versions, and operating systems.

    Example:
        compute_dedup_key("AI Ops", "Acme, Inc.", "Remote / Worldwide")
        -> ("ai ops", "acme", "remote")
    """
    return (
        normalize_title(title),
        normalize_company(company),
        normalize_location(location),
    )


# ---------------------------------------------------------------------------
# Phase 4 functions: fuzzy dedup + freshness rule
# ---------------------------------------------------------------------------


def fuzzy_match_opportunities(
    new_opp: dict,
    candidates: list[dict],
    threshold: float = FUZZY_THRESHOLD,
) -> tuple[bool, float]:
    """Check if new_opp title fuzzy-matches any candidate in this run.

    Uses token_sort_ratio (handles word-order variants like "AI Ops Manager"
    vs "Manager, AI Ops"). Fuzzy match is title-ONLY; company/location are
    not compared (avoid false positives — see RESEARCH.md anti-pattern #3).

    Args:
        new_opp:    dict with at least "title" key
        candidates: list of already-approved dicts from THIS run
        threshold:  minimum score to consider a match (default FUZZY_THRESHOLD=0.88)

    Returns:
        (is_match: bool, best_score: float)
        is_match=True if any candidate scored >= threshold
    """
    # Fuzzy title match only; company/location exact (see RESEARCH.md anti-pattern #3)
    if not candidates:
        return (False, 0.0)
    title_new = normalize_title(new_opp.get("title", ""))
    best_score = 0.0
    for candidate in candidates:
        title_cand = normalize_title(candidate.get("title", ""))
        score = fuzz.partial_token_sort_ratio(title_new, title_cand) / 100.0
        if score > best_score:
            best_score = score
        if best_score >= threshold:
            return (True, best_score)
    return (False, best_score)


def is_fresh_repost(
    first_seen_iso: str,
    current_access_iso: str,
    threshold_days: int = REPOST_FRESHNESS_DAYS,
) -> bool:
    """Return True if gap between first_seen and current_access >= threshold_days.

    Used when check_or_add() finds a duplicate to decide whether the role is a
    genuine repost (gap >= 30 days → surface as new) or still a duplicate (< 30 days).

    Args:
        first_seen_iso:     ISO 8601 string of when role was first stored (UTC)
        current_access_iso: ISO 8601 string of current run's access time (UTC)
        threshold_days:     Days required to treat re-sighting as new (default 30)

    Returns:
        True  → enough time has passed; treat as a new posting
        False → within freshness window; suppress as duplicate
    """
    t_first = datetime.datetime.fromisoformat(first_seen_iso.replace("Z", "+00:00"))
    t_current = datetime.datetime.fromisoformat(current_access_iso.replace("Z", "+00:00"))
    gap_days = (t_current - t_first).days
    return gap_days >= threshold_days


# ---------------------------------------------------------------------------
# run_dedup_pass — delegates to radar.stages.dedup (Plan 04-03 Wave 2 impl)
# ---------------------------------------------------------------------------


def run_dedup_pass(opportunities: list[dict], db_path: Path = _DEFAULT_DB_PATH) -> list[dict]:
    """Deduplicate a batch of opportunities using DedupeEngine + fuzzy matching.

    Full implementation lives in radar.stages.dedup; this entry point preserves
    the import contract for callers that import from dedup_engine directly.

    Args:
        opportunities: list of opportunity dicts with at least title/company/location
        db_path:       Path to SQLite seen_roles.sqlite (defaults to _DEFAULT_DB_PATH)

    Returns:
        list[dict] — deduplicated opportunities, unique in order of first appearance
    """
    from radar.stages.dedup import run_dedup_pass as _run_dedup_pass_impl
    return _run_dedup_pass_impl(opportunities, db_path=db_path)


# ---------------------------------------------------------------------------
# DedupeEngine — SQLite-backed persistent seen-role store
# ---------------------------------------------------------------------------


class DedupeEngine:
    """SQLite-backed store that detects duplicate job opportunities across runs.

    Usage:
        engine = DedupeEngine(Path("data/seen_roles.sqlite"))
        result = engine.check_or_add({"title": ..., "company": ..., "location": ...})
        if result["is_duplicate"]:
            print("Skipping — already seen")

    The database is created automatically on first instantiation.
    The same db_path across Python restarts gives full cross-run persistence.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    # ------------------------------------------------------------------
    # Internal DB setup
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        """Create the seen_roles table if it does not already exist."""
        # Ensure parent directory exists (test fixtures provide tmp_path; prod uses data/)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_roles (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    title_canonical  TEXT NOT NULL,
                    company_canonical TEXT NOT NULL,
                    location_canonical TEXT,
                    first_seen_date  TEXT NOT NULL,
                    last_seen_date   TEXT NOT NULL,
                    hit_count        INTEGER DEFAULT 1,
                    UNIQUE(title_canonical, company_canonical, location_canonical)
                )
                """
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Core dedup operation
    # ------------------------------------------------------------------

    def check_or_add(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        """Check whether opportunity is a duplicate; insert if new.

        Args:
            opportunity: dict with at minimum "title", "company", "location" keys.
                         Missing keys default to empty string.

        Returns:
            dict with keys:
                "is_duplicate" (bool) — True if already in the store
                "key"          (str)  — canonical "title:company:location" string
                "hit_count"    (int)  — total times this role has been observed
        """
        raw_title = opportunity.get("title", "") or ""
        raw_company = opportunity.get("company", "") or ""
        raw_location = opportunity.get("location", "") or ""

        title_c, company_c, location_c = compute_dedup_key(
            raw_title, raw_company, raw_location
        )
        key_str = f"{title_c}:{company_c}:{location_c}"
        now = datetime.datetime.utcnow().isoformat() + "Z"

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, hit_count
                FROM seen_roles
                WHERE title_canonical    = ?
                  AND company_canonical  = ?
                  AND location_canonical = ?
                """,
                (title_c, company_c, location_c),
            )
            row = cursor.fetchone()

            if row is not None:
                row_id, hit_count = row
                new_hit_count = hit_count + 1
                cursor.execute(
                    """
                    UPDATE seen_roles
                    SET last_seen_date = ?,
                        hit_count      = ?
                    WHERE id = ?
                    """,
                    (now, new_hit_count, row_id),
                )
                conn.commit()
                return {
                    "is_duplicate": True,
                    "key": key_str,
                    "hit_count": new_hit_count,
                }

            # Not seen before — insert
            cursor.execute(
                """
                INSERT INTO seen_roles
                    (title_canonical, company_canonical, location_canonical,
                     first_seen_date, last_seen_date, hit_count)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (title_c, company_c, location_c, now, now),
            )
            conn.commit()
            return {
                "is_duplicate": False,
                "key": key_str,
                "hit_count": 1,
            }


# ---------------------------------------------------------------------------
# CLI entry point (CONVENTIONS.md: every module must have an __main__ block)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    db = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT_DB_PATH
    engine = DedupeEngine(db)
    print(f"DedupeEngine initialized. DB: {db}")
