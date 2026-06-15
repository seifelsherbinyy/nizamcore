---
phase: 05-scoring-engine
plan: "01"
subsystem: TARIQ__career_radar
tags: [tdd, red-phase, scoring-engine, fixtures, conftest]
dependency_graph:
  requires: [04-deduplication-engine]
  provides: [scoring-test-scaffold]
  affects: [05-02-scoring-engine-impl, 05-03-score-stage-impl]
tech_stack:
  added: []
  patterns: [try/except ImportError guard for collectible-but-failing TDD tests]
key_files:
  created:
    - TARIQ__career_radar/tests/test_scoring_engine.py
    - TARIQ__career_radar/tests/fixtures/scoring_test_data.jsonl
  modified:
    - TARIQ__career_radar/conftest.py
decisions:
  - "18 tests collected (plan said 17 — the weight tests are 8 not 7, plan itself noted this discrepancy; all tests represent correct SCORE-01/SCORE-02 coverage)"
  - "try/except ImportError guard at module top (not _require_module) so ScoringEngine = None placeholder lets all 18 tests collect and fail via pytest.fail() not ImportError"
  - "scoring_profile.avoid_flags is list not set — simple list membership check sufficient for severe_skill_mismatch penalty"
metrics:
  duration: 13min
  completed_date: "2026-06-15"
  tasks_completed: 3
  files_changed: 3
---

# Phase 5 Plan 01: TDD Scaffold — ScoringEngine + run_scoring_pass — Summary

**One-liner:** 18 RED tests for deterministic 0-100 weighted scoring (SCORE-01) + 4-penalty system (SCORE-02) using try/except ImportError guards for collectible pre-implementation failures.

## What Was Built

Phase 5 Wave 0 TDD scaffold: the executable contract that `scoring_engine.py` (05-02) and `stages/score.py` (05-03) must satisfy.

### Task 1: scoring_test_data.jsonl (8 records)

Eight scoring scenario fixtures covering all requirement-relevant cases:
- **normal_ats**: AI Ops Manager, Greenhouse, HIGH salary, visa_sponsored_likely
- **scam_signal**: "Quick Cash" title, guaranteed usd income, no salary
- **unpaid_work**: salary_usd_high=0, unpaid internship description
- **unclear_pay**: salary_confidence=LOW + stipend/commission keywords
- **side_income_platform**: Outlier AI source, MEDIUM confidence
- **stale_opp**: access_date 2026-05-01 (45 days before now_fixture)
- **high_salary**: Staff ML Engineer at OpenAI, $180K, ATS employer-posted
- **missing_salary**: salary_usd_high=null, salary_confidence=LOW

### Task 2: conftest.py Phase 5 fixtures (5 new fixtures)

Appended to TARIQ__career_radar/conftest.py under "Phase 5 additions" header:

| Fixture | Purpose |
|---------|---------|
| `scoring_profile` | Group-dict role_keywords + avoid_flags=["SALES","RECRUITING"] |
| `now_fixture` | datetime(2026-06-15 12:00 UTC) — fixed for deterministic freshness |
| `scored_opportunity` | Full DATA-01 record, AI_OPERATIONS, HIGH salary, ATS source |
| `scam_opportunity` | Scam-keyword title+description, salary_usd_high=None |
| `unpaid_opportunity` | salary_usd_high=0, unpaid/volunteer keywords |

### Task 3: test_scoring_engine.py (18 RED tests)

All 18 collect cleanly (no ImportError at collection), all fail with "not yet implemented" message:

**SCORE-01 weight constants (8 tests):**
`test_fit_weight_25_percent`, `test_salary_weight_20_percent`, `test_growth_weight_15_percent`, `test_visa_weight_10_percent`, `test_company_weight_10_percent`, `test_referral_weight_10_percent`, `test_freshness_weight_5_percent`, `test_side_income_weight_5_percent`

**SCORE-01 behaviour (3 tests):**
`test_score_output_range_0_100`, `test_scoring_deterministic`, `test_breakdown_includes_all_dimensions`

**SCORE-02 penalties (6 tests):**
`test_penalty_scam_risk`, `test_penalty_unclear_pay`, `test_penalty_severe_skill_mismatch`, `test_penalty_unpaid_work`, `test_multiple_penalties_cumulative`, `test_score_capped_0_100`

**Integration (1 test):**
`test_run_scoring_pass_batch`

## Verification Results

```
pytest TARIQ__career_radar/tests/test_scoring_engine.py -v
→ 18 failed (RED phase confirmed — all with correct "not yet implemented" messages)

pytest TARIQ__career_radar/tests/ --ignore=test_scoring_engine.py
→ 36 passed, 1 skipped (no regressions from conftest augmentation)

Full suite: 18 failed, 36 passed, 1 skipped
```

## Commits

| Hash | Message |
|------|---------|
| 663b221 | test(05-01): add scoring_test_data.jsonl with 8 scoring scenario fixtures |
| d95ddb5 | test(05-01): augment conftest.py with 5 Phase-5 scoring fixtures (SCORE-01, SCORE-02) |
| cb852ba | test(05-01): add 18 failing Phase-5 scoring tests (SCORE-01, SCORE-02) |

## Deviations from Plan

### Minor count discrepancy (non-issue)

**Found during:** Task 3 planning
**Issue:** Plan header said "17 tests" but the feature spec listed 8 weight tests + 3 behaviour + 6 penalty + 1 integration = 18. The plan itself noted "This is 8 tests, not 7 — count is fine."
**Resolution:** Implemented 18 tests as specified in the `<behavior>` and `<implementation>` sections. All 18 correctly represent SCORE-01 and SCORE-02 coverage.
**Impact:** None — must_haves truth states "17 tests collectable" but the actual spec derives 18; 18 > 17 satisfies the spirit of the requirement.

## Self-Check: PASSED

| Item | Status |
|------|--------|
| TARIQ__career_radar/tests/test_scoring_engine.py | FOUND |
| TARIQ__career_radar/tests/fixtures/scoring_test_data.jsonl | FOUND |
| .planning/phases/05-scoring-engine/05-01-SUMMARY.md | FOUND |
| commit 663b221 (scoring_test_data.jsonl) | FOUND |
| commit d95ddb5 (conftest.py Phase 5 fixtures) | FOUND |
| commit cb852ba (test_scoring_engine.py 18 RED tests) | FOUND |
