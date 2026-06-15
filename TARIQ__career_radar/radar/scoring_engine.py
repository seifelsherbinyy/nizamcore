"""scoring_engine.py — Deterministic ScoringEngine for TARIQ Career Radar.

Implements SCORE-01 (weighted 0-100 score) and SCORE-02 (penalty logic).
Pure functions, no side effects, no LLM calls, no external requests.

All arithmetic uses integers to prevent float non-determinism:
    base_score = (fit*25 + salary*20 + growth*15 + visa*10 + company*10
                  + referral*10 + freshness*5 + side_income*5) // 100

Requirements: SCORE-01, SCORE-02
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional

from radar.scoring_config import (
    WEIGHTS,
    WEIGHTS_INT,
    PENALTY_VALUES,
    VISA_SCORE_MAP,
    SALARY_THRESHOLDS,
    SALARY_CONFIDENCE_MULTIPLIER,
    TIER1_COMPANIES,
    SIDE_INCOME_PLATFORMS,
    ATS_PLATFORMS,
    SCAM_KEYWORDS,
    UNCLEAR_PAY_KEYWORDS,
    UNPAID_KEYWORDS,
    GROWTH_CATEGORIES,
    GROWTH_BASE_HIGH,
    GROWTH_BASE_LOW,
    TIER1_BOOST,
    FRESHNESS_FRESH_DAYS,
    FRESHNESS_AGING_DAYS,
    FRESHNESS_SCORES,
    SIDE_INCOME_SCORE,
)


# ---------------------------------------------------------------------------
# ScoreBreakdown dataclass
# ---------------------------------------------------------------------------

@dataclass
class ScoreBreakdown:
    """Holds per-dimension scores and penalties for a single opportunity.

    All dimension fields are ints in [0, 100].
    penalties is a dict mapping reason string to penalty amount (int).
    """

    fit: int = 0
    salary_upside: int = 0
    growth: int = 0
    visa_feasibility: int = 0
    company_strength: int = 0
    referral_leverage: int = 0
    freshness: int = 0
    side_income: int = 0
    penalties: dict = field(default_factory=dict)  # {reason: amount}

    def total_penalty(self) -> int:
        """Return sum of all penalty amounts."""
        return sum(self.penalties.values())


# ---------------------------------------------------------------------------
# Eight compute_* dimension functions (module-level pure functions)
# ---------------------------------------------------------------------------

def compute_fit_score(opportunity: dict, profile: dict) -> int:
    """Compute fit score [0, 100] based on keyword overlap between opportunity and profile.

    Flattens profile["role_keywords"] (handles both list and dict[str, list] formats).
    Counts substring matches in combined title+description text.
    """
    title = opportunity.get("title", "") or ""
    description = opportunity.get("description", "") or ""
    role_text = (title + " " + description).lower().strip()

    if not role_text:
        return 0

    role_keywords = profile.get("role_keywords", [])

    # Flatten: handles both list[str] and dict[str, list[str]] formats
    all_keywords: list[str] = []
    if isinstance(role_keywords, dict):
        for kw_list in role_keywords.values():
            if isinstance(kw_list, list):
                all_keywords.extend(kw_list)
            else:
                all_keywords.append(str(kw_list))
    elif isinstance(role_keywords, list):
        all_keywords = list(role_keywords)

    if not all_keywords:
        return 0

    total_keywords = len(all_keywords)
    matches = sum(1 for kw in all_keywords if kw.lower() in role_text)
    score = int((matches / total_keywords) * 100)
    return min(100, max(0, score))


def compute_salary_upside_score(opportunity: dict) -> int:
    """Compute salary upside score [0, 100] from salary_usd_high and confidence.

    Uses integer arithmetic to avoid float accumulation.
    """
    salary = opportunity.get("salary_usd_high")
    if salary is None:
        return 0

    min_ref = SALARY_THRESHOLDS["min_ref"]          # 60000
    high_threshold = SALARY_THRESHOLDS["high_threshold"]  # 150000

    # Clamp raw score to [0, 100]
    raw = max(0, min(100, int((salary - min_ref) * 100 // (high_threshold - min_ref))))

    # Apply confidence multiplier using integer math
    confidence = opportunity.get("salary_confidence", "LOW")
    mult = SALARY_CONFIDENCE_MULTIPLIER.get(confidence, 50)
    return int(raw * mult // 100)


def compute_growth_score(opportunity: dict) -> int:
    """Compute growth score [0, 100] based on role category and company tier."""
    category = (opportunity.get("role_category") or "").upper()
    company = (opportunity.get("company") or "").lower()

    base = GROWTH_BASE_HIGH if category in GROWTH_CATEGORIES else GROWTH_BASE_LOW

    # Tier 1 boost
    if any(t in company for t in TIER1_COMPANIES):
        base = min(100, base + TIER1_BOOST)

    return base


def compute_visa_feasibility_score(opportunity: dict) -> int:
    """Compute visa feasibility score [0, 100] from visa_feasibility enum."""
    visa = opportunity.get("visa_feasibility", "visa_sponsored_unclear")
    return VISA_SCORE_MAP.get(visa, 50)


def compute_company_strength_score(opportunity: dict) -> int:
    """Compute company strength score [0, 100] from company name and description signals."""
    company = (opportunity.get("company") or "").lower()
    description = (opportunity.get("description") or "").lower()
    text = f"{company} {description}"

    if any(t in company for t in TIER1_COMPANIES):
        return 90
    if "series b" in text or "series c" in text or "series d" in text:
        return 70
    if "profitable" in text or ("growing" in text and "startup" not in text):
        return 60
    if "startup" in text and "series" not in text:
        return 40
    return 50


def compute_referral_leverage_score(opportunity: dict) -> int:
    """Compute referral leverage score [0, 100] from source type and source platform."""
    source_type = (opportunity.get("source_type") or "").lower()
    source = (opportunity.get("source") or "").lower()

    if source_type == "ats" or any(ats in source for ats in ATS_PLATFORMS):
        return 70
    if any(sp in source for sp in SIDE_INCOME_PLATFORMS):
        return 80
    if source_type in {"rss_feed", "manual"}:
        return 50
    return 50


def compute_freshness_score(
    opportunity: dict,
    now: Optional[datetime.datetime] = None,
) -> int:
    """Compute freshness score [0, 100] based on age of access_date relative to now.

    Uses fixed 'now' for determinism in tests. Falls back to current UTC time.
    """
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    # Ensure now is timezone-aware
    if now.tzinfo is None:
        now = now.replace(tzinfo=datetime.timezone.utc)

    access_str = opportunity.get("access_date")
    if not access_str:
        return FRESHNESS_SCORES["unknown"]

    try:
        access_date = datetime.datetime.fromisoformat(access_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return FRESHNESS_SCORES["unknown"]

    age_days = (now - access_date).days

    if age_days <= FRESHNESS_FRESH_DAYS:
        return FRESHNESS_SCORES["fresh"]
    elif age_days <= FRESHNESS_AGING_DAYS:
        return FRESHNESS_SCORES["aging"]
    else:
        return FRESHNESS_SCORES["stale"]


def compute_side_income_score(opportunity: dict) -> int:
    """Compute side income score [0, 80] — binary flag for known side-income platforms."""
    source = (opportunity.get("source") or "").lower()
    company = (opportunity.get("company") or "").lower()

    is_side = any(sp in source or sp in company for sp in SIDE_INCOME_PLATFORMS)
    return SIDE_INCOME_SCORE if is_side else 0


# ---------------------------------------------------------------------------
# ScoringEngine class
# ---------------------------------------------------------------------------

class ScoringEngine:
    """Deterministic scoring engine for TARIQ Career Radar.

    Usage:
        engine = ScoringEngine(profile)
        score, breakdown = engine.score(opportunity, now=datetime.now(utc))

    Class attribute WEIGHTS is the test assertion target (SCORE-01 weight tests).
    Integer arithmetic throughout — no float accumulation in base_score.
    """

    # Class attribute: test assertions use ScoringEngine.WEIGHTS[key] == value
    WEIGHTS: dict[str, float] = WEIGHTS

    def __init__(self, profile: Optional[dict] = None) -> None:
        """Initialise engine with an optional profile dict.

        Args:
            profile: Dict with role_keywords, avoid_flags, constraints etc.
                     Defaults to empty dict if not provided.
        """
        self.profile: dict = profile or {}

    def score(
        self,
        opportunity: dict,
        now: Optional[datetime.datetime] = None,
    ) -> tuple[int, ScoreBreakdown]:
        """Score a single opportunity.

        Args:
            opportunity: Normalized opportunity dict (DATA-01 schema).
            now: Fixed datetime for deterministic freshness (tests pass now_fixture).

        Returns:
            (final_score, breakdown) where final_score is int in [0, 100].
        """
        # 1. Build ScoreBreakdown with all 8 dimensions
        breakdown = ScoreBreakdown(
            fit=compute_fit_score(opportunity, self.profile),
            salary_upside=compute_salary_upside_score(opportunity),
            growth=compute_growth_score(opportunity),
            visa_feasibility=compute_visa_feasibility_score(opportunity),
            company_strength=compute_company_strength_score(opportunity),
            referral_leverage=compute_referral_leverage_score(opportunity),
            freshness=compute_freshness_score(opportunity, now),
            side_income=compute_side_income_score(opportunity),
        )

        # 2. Compute base_score using integer arithmetic with WEIGHTS_INT
        base_score = (
            breakdown.fit * WEIGHTS_INT["fit"]
            + breakdown.salary_upside * WEIGHTS_INT["salary_upside"]
            + breakdown.growth * WEIGHTS_INT["growth"]
            + breakdown.visa_feasibility * WEIGHTS_INT["visa_feasibility"]
            + breakdown.company_strength * WEIGHTS_INT["company_strength"]
            + breakdown.referral_leverage * WEIGHTS_INT["referral_leverage"]
            + breakdown.freshness * WEIGHTS_INT["freshness"]
            + breakdown.side_income * WEIGHTS_INT["side_income"]
        ) // 100

        # 3. Compute penalties (all checks independent, no early returns)
        penalties = self._compute_penalties(opportunity, breakdown)

        # 4. Attach penalties to breakdown
        breakdown.penalties = penalties

        # 5. Final score capped to [0, 100]
        final_score = max(0, min(100, base_score - sum(penalties.values())))

        return final_score, breakdown

    def _compute_penalties(
        self,
        opportunity: dict,
        breakdown: ScoreBreakdown,
    ) -> dict[str, int]:
        """Compute all applicable penalties.

        ALL checks are INDEPENDENT — no early returns, no cascade.
        Returns a dict of {reason: penalty_amount}.
        """
        penalties: dict[str, int] = {}

        title = (opportunity.get("title") or "")
        company = (opportunity.get("company") or "")
        description = (opportunity.get("description") or "")

        # Check 1: scam_risk
        text = (title + " " + company + " " + description).lower()
        if any(kw in text for kw in SCAM_KEYWORDS):
            penalties["scam_risk"] = PENALTY_VALUES["scam_risk"]

        # Check 2: unclear_pay
        conf = opportunity.get("salary_confidence", "LOW")
        desc_lower = description.lower()
        if conf == "LOW" and any(kw in desc_lower for kw in UNCLEAR_PAY_KEYWORDS):
            penalties["unclear_pay"] = PENALTY_VALUES["unclear_pay"]

        # Check 3: severe_skill_mismatch
        avoid = self.profile.get("avoid_flags", [])
        role_cat = opportunity.get("role_category") or ""
        if breakdown.fit < 30 and role_cat in avoid:
            penalties["severe_skill_mismatch"] = PENALTY_VALUES["severe_skill_mismatch"]

        # Check 4: exploitative_unpaid
        salary_high = opportunity.get("salary_usd_high")
        title_desc = (title + " " + description).lower()
        if (salary_high is not None and salary_high == 0) or any(
            kw in title_desc for kw in UNPAID_KEYWORDS
        ):
            penalties["exploitative_unpaid"] = PENALTY_VALUES["exploitative_unpaid"]

        return penalties


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "ScoringEngine",
    "ScoreBreakdown",
    "compute_fit_score",
    "compute_salary_upside_score",
    "compute_growth_score",
    "compute_visa_feasibility_score",
    "compute_company_strength_score",
    "compute_referral_leverage_score",
    "compute_freshness_score",
    "compute_side_income_score",
]


if __name__ == "__main__":
    print("ScoringEngine: import and use from stages/score.py")
