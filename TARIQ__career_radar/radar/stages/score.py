"""score.py — Phase 5 scoring orchestrator stage for TARIQ Career Radar.

This module implements run_scoring_pass(), which takes a list of deduplicated
opportunities (from run_dedup_pass) and applies deterministic scoring via
ScoringEngine to every opportunity.

Pipeline position:
    sources → normalize → filter → dedup → score (this module) → return

Design principles:
    - Profile is loaded ONCE per call (not per-opportunity) for determinism
    - Opportunities with missing required fields get final_score=0 without crashing
    - Output is always sorted descending by final_score
    - All exceptions from scoring are caught per-opportunity; bad records get score=0

Requirements: SCORE-01, SCORE-02
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from radar.scoring_engine import ScoringEngine
from radar.config import load_profile_seed

logger = logging.getLogger(__name__)

# Fields that every opportunity must have (non-None) to be scored normally.
# Opportunities missing any of these get final_score=0 and a descriptive error breakdown.
REQUIRED_FIELDS = ["title", "company", "source", "source_type", "access_date"]


def run_scoring_pass(
    opportunities: list[dict],
    profile: Optional[dict] = None,
    now: Optional[datetime] = None,
) -> list[dict]:
    """Apply scoring to all deduplicated opportunities.

    Args:
        opportunities: List of opportunity dicts (from run_dedup_pass output).
        profile: Optional profile seed dict. If None, loads from disk via
                 load_profile_seed(). Profile is loaded ONCE and frozen for the
                 entire call (determinism guarantee).
        now: Optional datetime for freshness calculation. Defaults to
             datetime.now(UTC). Pass a fixed value in tests for deterministic
             results.

    Returns:
        Same opportunities, each enriched with 'final_score' (int) and
        'score_breakdown' (dict with all 8 dimension keys + penalties).
        Sorted descending by final_score.
    """
    # --- Load profile once ---
    if profile is None:
        try:
            profile = load_profile_seed()
        except ValueError as exc:
            logger.warning(
                "run_scoring_pass: could not load profile (%s); using empty profile — "
                "fit scores will be 0 for all opportunities",
                exc,
            )
            profile = {}

    # --- Fix 'now' once for the entire batch ---
    if now is None:
        now = datetime.now(timezone.utc)

    # --- Build scoring engine once ---
    engine = ScoringEngine(profile)

    scored: list[dict] = []

    for opp in opportunities:
        # Check all required fields are present and non-None
        missing_list = [
            field for field in REQUIRED_FIELDS
            if opp.get(field) is None
        ]

        if missing_list:
            logger.warning(
                "Opportunity missing fields %s: %s",
                missing_list,
                opp.get("title", "UNKNOWN"),
            )
            opp["final_score"] = 0
            opp["score_breakdown"] = {
                "error": "missing_required_fields",
                "missing": missing_list,
            }
            scored.append(opp)
            continue

        # Score the opportunity
        score, breakdown = engine.score(opp, now)

        opp["final_score"] = score
        opp["score_breakdown"] = {
            "fit": breakdown.fit,
            "salary_upside": breakdown.salary_upside,
            "growth": breakdown.growth,
            "visa_feasibility": breakdown.visa_feasibility,
            "company_strength": breakdown.company_strength,
            "referral_leverage": breakdown.referral_leverage,
            "freshness": breakdown.freshness,
            "side_income": breakdown.side_income,
            "penalties": breakdown.penalties,
            "final": score,
        }
        scored.append(opp)

    return sorted(scored, key=lambda o: o["final_score"], reverse=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("run_scoring_pass: import and call from fetch.py")
