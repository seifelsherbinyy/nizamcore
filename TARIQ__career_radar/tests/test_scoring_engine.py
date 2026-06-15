"""test_scoring_engine.py — Phase 5 TDD scaffold (RED phase).

17 failing tests covering SCORE-01 (weighted scoring engine) and SCORE-02
(penalty conditions). All tests are collectible via try/except ImportError
guards — they fail with pytest.fail() rather than causing collection errors.

Run to confirm RED:
    pytest TARIQ__career_radar/tests/test_scoring_engine.py -v
    Expected: 17 FAILED

Requirements covered:
  SCORE-01 (11 tests): weight constants, output range, determinism, breakdown shape
  SCORE-02 (6 tests): scam_risk, unclear_pay, severe_skill_mismatch, exploitative_unpaid,
                       cumulative penalties, score floor at 0
  Integration (1 test): run_scoring_pass batch sort + schema
"""
from __future__ import annotations

import uuid

import pytest

# ---------------------------------------------------------------------------
# Import guards — tests collect even before implementation exists
# ---------------------------------------------------------------------------

try:
    from radar.scoring_engine import ScoringEngine, ScoreBreakdown  # noqa: F401
    _SCORING_ENGINE_AVAILABLE = True
except ImportError:
    _SCORING_ENGINE_AVAILABLE = False
    ScoringEngine = None
    ScoreBreakdown = None

try:
    from radar.stages.score import run_scoring_pass  # noqa: F401
    _SCORE_STAGE_AVAILABLE = True
except ImportError:
    _SCORE_STAGE_AVAILABLE = False
    run_scoring_pass = None


# ---------------------------------------------------------------------------
# Helper: minimal inline opportunity dict for tests that don't use fixtures
# ---------------------------------------------------------------------------

def _base_opp(**overrides) -> dict:
    """Return a minimal valid opportunity dict, overridable by keyword args."""
    base = {
        "opportunity_id": str(uuid.uuid4()),
        "title": "Generic Role",
        "company": "Test Corp",
        "location": "Remote",
        "remote_status": "fully_remote",
        "source": "greenhouse",
        "source_type": "ats",
        "access_date": "2026-06-15T10:00:00Z",
        "observed_at": "2026-06-15T10:00:00Z",
        "salary_usd_high": None,
        "salary_usd_low": None,
        "salary_confidence": "LOW",
        "salary_evidence_type": "not_disclosed",
        "visa_feasibility": "visa_sponsored_unclear",
        "role_category": None,
        "description": "generic role description",
        "fit_score": 0,
        "growth_score": 0,
        "confidence": "LOW",
        "tags": [],
        "lane": "Remote USD",
        "data_quality": "partial",
        "run_id": "test-run-001",
    }
    base.update(overrides)
    return base


# ===========================================================================
# SCORE-01 — Weight constant tests (8 tests)
# ===========================================================================

def test_fit_weight_25_percent():
    """ScoringEngine.WEIGHTS['fit'] must equal 0.25."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    assert ScoringEngine.WEIGHTS["fit"] == 0.25


def test_salary_weight_20_percent():
    """ScoringEngine.WEIGHTS['salary_upside'] must equal 0.20."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    assert ScoringEngine.WEIGHTS["salary_upside"] == 0.20


def test_growth_weight_15_percent():
    """ScoringEngine.WEIGHTS['growth'] must equal 0.15."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    assert ScoringEngine.WEIGHTS["growth"] == 0.15


def test_visa_weight_10_percent():
    """ScoringEngine.WEIGHTS['visa_feasibility'] must equal 0.10."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    assert ScoringEngine.WEIGHTS["visa_feasibility"] == 0.10


def test_company_weight_10_percent():
    """ScoringEngine.WEIGHTS['company_strength'] must equal 0.10."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    assert ScoringEngine.WEIGHTS["company_strength"] == 0.10


def test_referral_weight_10_percent():
    """ScoringEngine.WEIGHTS['referral_leverage'] must equal 0.10."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    assert ScoringEngine.WEIGHTS["referral_leverage"] == 0.10


def test_freshness_weight_5_percent():
    """ScoringEngine.WEIGHTS['freshness'] must equal 0.05."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    assert ScoringEngine.WEIGHTS["freshness"] == 0.05


def test_side_income_weight_5_percent():
    """ScoringEngine.WEIGHTS['side_income'] must equal 0.05."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    assert ScoringEngine.WEIGHTS["side_income"] == 0.05


# ===========================================================================
# SCORE-01 — Scoring behaviour tests (3 tests)
# ===========================================================================

def test_score_output_range_0_100(scored_opportunity, scoring_profile, now_fixture):
    """ScoringEngine.score() returns an int in [0, 100] inclusive."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    score, breakdown = ScoringEngine(scoring_profile).score(scored_opportunity, now_fixture)
    assert isinstance(score, int), f"score must be int, got {type(score)}"
    assert 0 <= score <= 100, f"score {score} out of [0, 100]"


def test_scoring_deterministic(scored_opportunity, scoring_profile, now_fixture):
    """Same opportunity + same now + same profile → identical score on two calls."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    engine = ScoringEngine(scoring_profile)
    s1, b1 = engine.score(scored_opportunity, now_fixture)
    s2, b2 = engine.score(scored_opportunity, now_fixture)
    assert s1 == s2, f"Non-deterministic: first={s1}, second={s2}"
    assert b1.fit == b2.fit, "fit dimension not deterministic"
    assert b1.salary_upside == b2.salary_upside, "salary_upside not deterministic"


def test_breakdown_includes_all_dimensions(scored_opportunity, scoring_profile, now_fixture):
    """ScoreBreakdown must have all 8 dimension attrs plus penalties dict."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    score, breakdown = ScoringEngine(scoring_profile).score(scored_opportunity, now_fixture)
    required_attrs = [
        "fit", "salary_upside", "growth", "visa_feasibility",
        "company_strength", "referral_leverage", "freshness", "side_income",
        "penalties",
    ]
    for attr in required_attrs:
        assert hasattr(breakdown, attr), f"ScoreBreakdown missing attr: {attr}"
    assert isinstance(breakdown.penalties, dict), (
        f"ScoreBreakdown.penalties must be dict, got {type(breakdown.penalties)}"
    )


# ===========================================================================
# SCORE-02 — Penalty tests (6 tests)
# ===========================================================================

def test_penalty_scam_risk(scam_opportunity, scoring_profile, now_fixture):
    """Scam keywords in title → breakdown.penalties['scam_risk'] == 20."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    _, breakdown = ScoringEngine(scoring_profile).score(scam_opportunity, now_fixture)
    assert "scam_risk" in breakdown.penalties, (
        f"Expected 'scam_risk' in penalties, got: {breakdown.penalties}"
    )
    assert breakdown.penalties["scam_risk"] == 20, (
        f"Expected scam_risk penalty == 20, got {breakdown.penalties['scam_risk']}"
    )


def test_penalty_unclear_pay(scoring_profile, now_fixture):
    """salary_confidence==LOW + unclear keyword in description → penalties['unclear_pay'] == 15."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    opp = _base_opp(
        title="Data Science Contractor",
        description="project-based stipend commission",
        salary_confidence="LOW",
        salary_usd_high=50000,
    )
    _, breakdown = ScoringEngine(scoring_profile).score(opp, now_fixture)
    assert "unclear_pay" in breakdown.penalties, (
        f"Expected 'unclear_pay' in penalties, got: {breakdown.penalties}"
    )
    assert breakdown.penalties["unclear_pay"] == 15, (
        f"Expected unclear_pay penalty == 15, got {breakdown.penalties['unclear_pay']}"
    )


def test_penalty_severe_skill_mismatch(scoring_profile, now_fixture):
    """role_category in avoid_flags AND fit < 30 → penalties['severe_skill_mismatch'] == 10."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    opp = _base_opp(
        title="Sales Executive xyz-no-keyword-match",
        company="Sales Co",
        role_category="SALES",
        description="B2B enterprise sales revenue quota pipeline closing",
    )
    _, breakdown = ScoringEngine(scoring_profile).score(opp, now_fixture)
    assert "severe_skill_mismatch" in breakdown.penalties, (
        f"Expected 'severe_skill_mismatch' in penalties, got: {breakdown.penalties}"
    )
    assert breakdown.penalties["severe_skill_mismatch"] == 10, (
        f"Expected severe_skill_mismatch == 10, got {breakdown.penalties['severe_skill_mismatch']}"
    )


def test_penalty_unpaid_work(unpaid_opportunity, scoring_profile, now_fixture):
    """salary_usd_high == 0 → breakdown.penalties['exploitative_unpaid'] == 20."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    _, breakdown = ScoringEngine(scoring_profile).score(unpaid_opportunity, now_fixture)
    assert "exploitative_unpaid" in breakdown.penalties, (
        f"Expected 'exploitative_unpaid' in penalties, got: {breakdown.penalties}"
    )
    assert breakdown.penalties["exploitative_unpaid"] == 20, (
        f"Expected exploitative_unpaid == 20, got {breakdown.penalties['exploitative_unpaid']}"
    )


def test_multiple_penalties_cumulative(scam_opportunity, scoring_profile, now_fixture):
    """scam + unpaid both present → total_penalty >= 40 (both applied cumulatively)."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    opp = dict(scam_opportunity)
    opp["salary_usd_high"] = 0
    opp["description"] = "guaranteed usd income work from home 100% unpaid no salary"
    _, breakdown = ScoringEngine(scoring_profile).score(opp, now_fixture)
    assert "scam_risk" in breakdown.penalties, (
        f"Expected 'scam_risk' in penalties, got: {breakdown.penalties}"
    )
    assert "exploitative_unpaid" in breakdown.penalties, (
        f"Expected 'exploitative_unpaid' in penalties, got: {breakdown.penalties}"
    )
    total = sum(breakdown.penalties.values())
    assert total >= 40, f"Expected cumulative penalties >= 40, got {total}"


def test_score_capped_0_100(unpaid_opportunity, scoring_profile, now_fixture):
    """Penalties exceeding base score → final_score == 0 (not negative), <= 100."""
    if not _SCORING_ENGINE_AVAILABLE:
        pytest.fail("radar.scoring_engine not yet implemented (RED phase)")
    opp = dict(unpaid_opportunity)
    opp["description"] = "unpaid no salary guaranteed usd quick cash no experience required"
    opp["title"] = "Unpaid Quick Cash Scam Role"
    score, _ = ScoringEngine(scoring_profile).score(opp, now_fixture)
    assert score >= 0, f"Score must not go negative, got {score}"
    assert score <= 100, f"Score must not exceed 100, got {score}"


# ===========================================================================
# Integration test — run_scoring_pass (1 test)
# ===========================================================================

def test_run_scoring_pass_batch(scoring_profile, now_fixture):
    """run_scoring_pass returns list sorted by final_score desc, each opp has final_score+score_breakdown."""
    if not _SCORE_STAGE_AVAILABLE:
        pytest.fail("radar.stages.score not yet implemented (RED phase)")

    opps = [
        _base_opp(
            title="AI Operations Manager",
            description="ai operations stakeholder management",
            salary_usd_high=120000,
            salary_confidence="HIGH",
            salary_evidence_type="employer_posted",
            visa_feasibility="visa_sponsored_likely",
            role_category="AI_OPERATIONS",
        ),
        _base_opp(
            title="Quick Cash No Experience",
            description="guaranteed usd income",
            salary_usd_high=None,
            salary_confidence="LOW",
        ),
        _base_opp(
            title="AI Research Assistant (Unpaid)",
            description="unpaid trial no salary",
            salary_usd_high=0,
            salary_usd_low=0,
            salary_confidence="LOW",
        ),
    ]

    result = run_scoring_pass(opps, profile=scoring_profile, now=now_fixture)

    assert len(result) == 3, f"Expected 3 results, got {len(result)}"

    for opp in result:
        assert "final_score" in opp, f"Missing 'final_score' key in: {list(opp.keys())}"
        assert "score_breakdown" in opp, f"Missing 'score_breakdown' key in: {list(opp.keys())}"
        assert isinstance(opp["final_score"], int), (
            f"final_score must be int, got {type(opp['final_score'])}"
        )

    scores = [o["final_score"] for o in result]
    assert scores == sorted(scores, reverse=True), (
        f"Result not sorted descending: {scores}"
    )
