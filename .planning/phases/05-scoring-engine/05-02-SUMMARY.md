---
phase: 05-scoring-engine
plan: "02"
subsystem: TARIQ__career_radar
tags: [scoring-engine, deterministic, integer-arithmetic, penalties, tdd-green]

requires:
  - phase: 05-01
    provides: 18 RED scoring tests (SCORE-01 weight/behaviour, SCORE-02 penalties, integration)
provides:
  - scoring_config.py: all scoring constants (WEIGHTS, PENALTY_VALUES, thresholds, platform sets)
  - scoring_engine.py: ScoringEngine class + ScoreBreakdown dataclass + 8 compute_* functions
affects: [05-03-score-stage-impl, 06-salary-confidence, 07-tagging-profile-matching]

tech-stack:
  added: []
  patterns:
    - "Integer arithmetic for deterministic base_score: (fit*25 + ... + side_income*5) // 100"
    - "All penalty checks independent (no cascade, no early return) — SCORE-02 requirement"
    - "WEIGHTS class attribute on ScoringEngine exposes constants for direct test assertions"
    - "compute_fit_score handles both list and dict[str, list] role_keywords formats"

key-files:
  created:
    - TARIQ__career_radar/radar/scoring_config.py
    - TARIQ__career_radar/radar/scoring_engine.py
  modified: []

key-decisions:
  - "Integer arithmetic throughout: WEIGHTS_INT (25,20,15,10,10,10,5,5) used for base_score to prevent float non-determinism"
  - "WEIGHTS (floats) kept separate from WEIGHTS_INT (ints) — tests assert on WEIGHTS, engine computes with WEIGHTS_INT"
  - "_compute_penalties checks all 4 conditions independently regardless of other results — cumulative not exclusive"
  - "compute_fit_score flattens both list and dict profile formats for forward-compatibility with profile schema evolution"

patterns-established:
  - "Pure function scoring: ScoringEngine.score() takes only opportunity + now — no I/O, no globals mutation"
  - "ScoreBreakdown dataclass: all 8 dims as int fields + penalties dict + total_penalty() method"
  - "scoring_config.py as locked constants module: no classes, no functions — only module-level assignments"

requirements-completed: [SCORE-01, SCORE-02]

duration: 12min
completed: "2026-06-15"
---

# Phase 5 Plan 02: ScoringEngine Implementation — Summary

**Deterministic 0-100 weighted ScoringEngine with integer arithmetic, ScoreBreakdown dataclass, 8 dimension functions, and 4-penalty system turning 17 RED SCORE-01/SCORE-02 tests GREEN.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-15T15:25:57Z
- **Completed:** 2026-06-15T15:37:00Z
- **Tasks:** 2
- **Files modified:** 2 (both created new)

## Accomplishments

- `scoring_config.py`: pure constants module with WEIGHTS (floats, sum=1.0), WEIGHTS_INT (ints, sum=100), PENALTY_VALUES, VISA_SCORE_MAP, SALARY_THRESHOLDS, SALARY_CONFIDENCE_MULTIPLIER, TIER1_COMPANIES, all platform/keyword sets, growth/freshness constants
- `scoring_engine.py`: ScoreBreakdown dataclass + 8 independent compute_* functions + ScoringEngine class with integer arithmetic base_score computation and independent 4-penalty system
- 17/17 target tests GREEN; 1 deferred (test_run_scoring_pass_batch needs 05-03 stages/score.py); 36/36 prior tests still GREEN

## Task Commits

Each task was committed atomically:

1. **Task 1: scoring_config.py — all constants** - `aa72a0d` (feat)
2. **Task 2: scoring_engine.py — ScoringEngine + 8 dimension functions + penalty logic** - `e976e66` (feat)

## Files Created/Modified

- `TARIQ__career_radar/radar/scoring_config.py` — All scoring constants: WEIGHTS, WEIGHTS_INT, PENALTY_VALUES, VISA_SCORE_MAP, SALARY_THRESHOLDS, SALARY_CONFIDENCE_MULTIPLIER, TIER1_COMPANIES, SIDE_INCOME_PLATFORMS, ATS_PLATFORMS, SCAM_KEYWORDS, UNCLEAR_PAY_KEYWORDS, UNPAID_KEYWORDS, GROWTH_CATEGORIES, freshness thresholds, SIDE_INCOME_SCORE
- `TARIQ__career_radar/radar/scoring_engine.py` — ScoreBreakdown dataclass; 8 compute_* pure functions; ScoringEngine class with WEIGHTS class attr, score() returning (int, ScoreBreakdown), _compute_penalties() with 4 independent checks

## Decisions Made

- **Integer arithmetic only**: WEIGHTS_INT dict (25,20,15,10,10,10,5,5) used for base_score = (...) // 100. WEIGHTS (floats) kept solely for test assertions via `ScoringEngine.WEIGHTS`. Prevents float accumulation across calls.
- **Separate WEIGHTS/WEIGHTS_INT**: Two dicts maintained — WEIGHTS for the `ScoringEngine.WEIGHTS` class attribute tests check, WEIGHTS_INT for arithmetic. No float arithmetic touches base_score.
- **All penalties independent**: `_compute_penalties()` computes all 4 checks unconditionally, collects into dict, returns at end. No early returns, no cascade — ensures cumulative penalty tests work correctly.
- **compute_fit_score dual-format support**: Handles both `list[str]` and `dict[str, list[str]]` profile.role_keywords — forwards-compatible with Phase 1 profile schema which uses the dict format.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `ScoringEngine` + `ScoreBreakdown` fully implemented and tested
- 05-03 can import `from radar.scoring_engine import ScoringEngine, ScoreBreakdown` and implement `stages/score.py` to pass `test_run_scoring_pass_batch`
- Determinism verified: same opp + same profile + same `now` → identical score (Score: 66 on spot-check)
- No regressions: 36 prior tests still GREEN

---
*Phase: 05-scoring-engine*
*Completed: 2026-06-15*
