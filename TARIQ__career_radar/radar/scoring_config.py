"""scoring_config.py — Constants for TARIQ ScoringEngine.

All values are LOCKED per REQUIREMENTS.md (SCORE-01, SCORE-02).
Do not adjust without updating tests.

Weights sum to exactly 1.0. Use integer arithmetic in ScoringEngine:
    base_score = (fit*25 + salary*20 + growth*15 + visa*10 + company*10
                  + referral*10 + freshness*5 + side_income*5) // 100
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Weight constants — ScoringEngine.WEIGHTS uses these (test assertion target)
# ---------------------------------------------------------------------------

WEIGHTS: dict[str, float] = {
    "fit": 0.25,
    "salary_upside": 0.20,
    "growth": 0.15,
    "visa_feasibility": 0.10,
    "company_strength": 0.10,
    "referral_leverage": 0.10,
    "freshness": 0.05,
    "side_income": 0.05,
}

# Integer equivalents for base_score arithmetic (sum = 100, no float accumulation)
WEIGHTS_INT: dict[str, int] = {
    "fit": 25,
    "salary_upside": 20,
    "growth": 15,
    "visa_feasibility": 10,
    "company_strength": 10,
    "referral_leverage": 10,
    "freshness": 5,
    "side_income": 5,
}

# ---------------------------------------------------------------------------
# Penalty values (SCORE-02)
# ---------------------------------------------------------------------------

PENALTY_VALUES: dict[str, int] = {
    "scam_risk": 20,
    "unclear_pay": 15,
    "severe_skill_mismatch": 10,
    "exploitative_unpaid": 20,
}

# ---------------------------------------------------------------------------
# Visa scoring map
# ---------------------------------------------------------------------------

VISA_SCORE_MAP: dict[str, int] = {
    "visa_sponsored_likely": 100,
    "visa_sponsored_unclear": 50,
    "visa_not_sponsored": 10,
    "not_applicable": 30,
}

# ---------------------------------------------------------------------------
# Salary thresholds and confidence multipliers
# ---------------------------------------------------------------------------

SALARY_THRESHOLDS: dict[str, int] = {
    "min_ref": 60000,
    "high_threshold": 150000,
}

# Integer percentages — apply as: score = raw * mult // 100
SALARY_CONFIDENCE_MULTIPLIER: dict[str, int] = {
    "HIGH": 100,
    "MEDIUM": 80,
    "LOW": 50,
}

# ---------------------------------------------------------------------------
# Company tier lists
# ---------------------------------------------------------------------------

TIER1_COMPANIES: list[str] = [
    "google",
    "microsoft",
    "aws",
    "apple",
    "meta",
    "openai",
    "anthropic",
    "netflix",
    "amazon",
    "deepmind",
    "stripe",
    "databricks",
    "huggingface",
]

# ---------------------------------------------------------------------------
# Platform sets
# ---------------------------------------------------------------------------

SIDE_INCOME_PLATFORMS: set[str] = {
    "outlier",
    "outlier.ai",
    "dataannotation",
    "turing",
    "toloka",
    "toloka.ai",
    "braintrust",
    "contra",
    "wellfound",
}

ATS_PLATFORMS: set[str] = {
    "greenhouse",
    "lever",
    "ashby",
    "workable",
}

# ---------------------------------------------------------------------------
# Keyword sets for penalty detection
# ---------------------------------------------------------------------------

SCAM_KEYWORDS: set[str] = {
    "nigerian",
    "guaranteed usd",
    "no experience required",
    "quick cash",
    "work from home 100%",
    "make money fast",
    "earn from home",
}

UNCLEAR_PAY_KEYWORDS: set[str] = {
    "stipend",
    "bonus only",
    "commission",
    "performance-based",
    "tbd",
    "to be determined",
    "negotiable",
}

UNPAID_KEYWORDS: set[str] = {
    "unpaid",
    "no salary",
    "free",
    "volunteer",
    "unpaid trial",
    "unpaid internship",
}

# ---------------------------------------------------------------------------
# Growth scoring constants
# ---------------------------------------------------------------------------

GROWTH_CATEGORIES: set[str] = {
    "AI_OPERATIONS",
    "DATA_SCIENCE",
    "DATA_ANNOTATION",
    "MACHINE_LEARNING",
    "ML_ENGINEERING",
    "LLM_EVALUATION",
}

GROWTH_BASE_HIGH: int = 60   # category in GROWTH_CATEGORIES
GROWTH_BASE_LOW: int = 40    # all other categories
TIER1_BOOST: int = 20        # added to base when company is Tier 1

# ---------------------------------------------------------------------------
# Freshness scoring constants
# ---------------------------------------------------------------------------

FRESHNESS_FRESH_DAYS: int = 7
FRESHNESS_AGING_DAYS: int = 30

FRESHNESS_SCORES: dict[str, int] = {
    "fresh": 100,
    "aging": 60,
    "stale": 20,
    "unknown": 50,
}

# ---------------------------------------------------------------------------
# Side income binary score
# ---------------------------------------------------------------------------

SIDE_INCOME_SCORE: int = 80  # binary: is or isn't a side-income platform

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "WEIGHTS",
    "WEIGHTS_INT",
    "PENALTY_VALUES",
    "VISA_SCORE_MAP",
    "SALARY_THRESHOLDS",
    "SALARY_CONFIDENCE_MULTIPLIER",
    "TIER1_COMPANIES",
    "SIDE_INCOME_PLATFORMS",
    "ATS_PLATFORMS",
    "SCAM_KEYWORDS",
    "UNCLEAR_PAY_KEYWORDS",
    "UNPAID_KEYWORDS",
    "GROWTH_CATEGORIES",
    "GROWTH_BASE_HIGH",
    "GROWTH_BASE_LOW",
    "TIER1_BOOST",
    "FRESHNESS_FRESH_DAYS",
    "FRESHNESS_AGING_DAYS",
    "FRESHNESS_SCORES",
    "SIDE_INCOME_SCORE",
]
