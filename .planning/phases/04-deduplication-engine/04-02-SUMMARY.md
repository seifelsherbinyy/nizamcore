---
phase: 04-deduplication-engine
plan: "02"
subsystem: dedup
tags: [rapidfuzz, fuzzy-matching, sqlite, deduplication, freshness-rule]

# Dependency graph
requires:
  - phase: 04-01
    provides: "RED tests for fuzzy_match_opportunities, is_fresh_repost, run_dedup_pass; conftest fixtures"
provides:
  - "fuzzy_match_opportunities() — title-only partial_token_sort_ratio fuzzy match with threshold 0.88"
  - "is_fresh_repost() — datetime gap check for repost freshness window"
  - "run_dedup_pass() stub — importable placeholder for Plan 04-03"
  - "FUZZY_THRESHOLD=0.88 and REPOST_FRESHNESS_DAYS=30 module constants"
affects: [04-03, scoring-engine, tag-engine]

# Tech tracking
tech-stack:
  added: [rapidfuzz==3.14.5]
  patterns:
    - "Title-only fuzzy match (partial_token_sort_ratio) avoids false positives from company/location variance"
    - "Stub function with NotImplementedError allows multi-phase TDD import block without breaking collection"
    - "Phase-4 symbols co-imported in test module; stub ensures importability"

key-files:
  created: []
  modified:
    - TARIQ__career_radar/radar/dedup_engine.py

key-decisions:
  - "Use partial_token_sort_ratio instead of token_sort_ratio: token_sort_ratio gives 0.80 for 'AI Operations Manager' vs 'AI Ops Manager' (fails >=0.88 contract); partial_token_sort_ratio gives 0.96 while maintaining 0.73 for unrelated titles"
  - "Add run_dedup_pass() stub with NotImplementedError: test module imports all Phase-4 symbols together in one try/except block; without the stub the import fails and all 5 Phase-4 tests fail with ImportError instead of running"

patterns-established:
  - "Phase-N constants pattern: FUZZY_THRESHOLD / REPOST_FRESHNESS_DAYS as typed float/int module constants"
  - "Partial token sort ratio (partial_token_sort_ratio / 100.0) for abbreviation-tolerant title fuzzy match"
  - "Z suffix replacement (replace('Z', '+00:00')) before datetime.fromisoformat() for timezone-aware parsing"

requirements-completed: [DEDUP-01, DEDUP-02]

# Metrics
duration: 145s
completed: 2026-06-15
---

# Phase 4 Plan 02: Deduplication Engine Wave 1 Implementation Summary

**rapidfuzz partial_token_sort_ratio fuzzy title match (threshold 0.88) + 30-day freshness repost rule added to dedup_engine.py; 8/9 tests GREEN, 1 expected RED until Plan 04-03**

## Performance

- **Duration:** 145s (~2.5 min)
- **Started:** 2026-06-15T14:43:01Z
- **Completed:** 2026-06-15T14:45:26Z
- **Tasks:** 2 (implemented together in single file edit)
- **Files modified:** 1

## Accomplishments

- Added `FUZZY_THRESHOLD=0.88` and `REPOST_FRESHNESS_DAYS=30` module-level typed constants
- Implemented `fuzzy_match_opportunities()` using `partial_token_sort_ratio` for abbreviation-tolerant title matching (detects "AI Operations Manager" / "AI Ops Manager" as the same role at 0.963 score)
- Implemented `is_fresh_repost()` using `datetime.fromisoformat()` for 30-day freshness window check
- Added `run_dedup_pass()` stub (NotImplementedError) so all Phase-4 symbols can be imported together without breaking test collection
- Installed `rapidfuzz==3.14.5` (was absent from environment)

## Task Commits

Each task was committed atomically:

1. **Task 1+2: Add constants, fuzzy_match_opportunities, is_fresh_repost, run_dedup_pass stub** - `62d95f1` (feat)

**Plan metadata:** _(forthcoming docs commit)_

## Files Created/Modified

- `TARIQ__career_radar/radar/dedup_engine.py` — Added Phase-4 constants, fuzzy_match_opportunities(), is_fresh_repost(), run_dedup_pass() stub; from rapidfuzz import fuzz

## Decisions Made

1. **partial_token_sort_ratio over token_sort_ratio**: The plan specified `token_sort_ratio` but this gives score=0.80 for "AI Operations Manager" vs "AI Ops Manager" — below the 0.88 threshold the test asserts. `partial_token_sort_ratio` returns 0.963 (matches) while returning 0.727 for "Finance Manager" vs "AI Ops Manager" (no false positive). This satisfies the test contract.

2. **run_dedup_pass() stub required**: The test module imports `fuzzy_match_opportunities`, `is_fresh_repost`, and `run_dedup_pass` all in one `try/except ImportError` block. Without the stub, the entire block fails on ImportError and `_PHASE4_IMPORT_ERROR` is set — causing all 5 Phase-4 tests to fail with ImportError rather than running. The stub makes all three symbols importable while leaving `test_run_dedup_pass_removes_within_run_dups` appropriately RED (it calls the function, which raises NotImplementedError).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] rapidfuzz not installed in environment**
- **Found during:** Task 1 (adding `from rapidfuzz import fuzz` import)
- **Issue:** `from rapidfuzz import fuzz` raised ModuleNotFoundError — package not installed
- **Fix:** `pip install rapidfuzz` → installed rapidfuzz==3.14.5
- **Files modified:** none (environment change only)
- **Verification:** `python -c "from rapidfuzz import fuzz; print('OK')"` exits 0
- **Committed in:** 62d95f1 (included in feat commit)

**2. [Rule 1 - Bug] token_sort_ratio produces 0.80 score below 0.88 threshold**
- **Found during:** Task 1 verification — `test_fuzzy_match_title_variants` FAILED with score=0.800
- **Issue:** Plan specified `fuzz.token_sort_ratio` but "AI Operations Manager" vs "AI Ops Manager" gives ratio 80/100 = 0.80 < 0.88. The test asserts `score >= 0.88`, creating an impossible contract.
- **Fix:** Switched to `fuzz.partial_token_sort_ratio` which gives 0.963 for this pair (abbreviation-tolerant) and 0.727 for "Finance Manager" vs "AI Ops Manager" (no false positive at threshold 0.88)
- **Files modified:** TARIQ__career_radar/radar/dedup_engine.py
- **Verification:** test_fuzzy_match_title_variants PASSED (score=0.963 >= 0.88); test_fuzzy_match_no_false_positive PASSED (score=0.727 < 0.88)
- **Committed in:** 62d95f1

**3. [Rule 3 - Blocking] run_dedup_pass stub needed for Phase-4 import to succeed**
- **Found during:** Task 1 verification — all 5 Phase-4 tests failed with ImportError despite fuzzy functions being present
- **Issue:** Test file imports fuzzy_match_opportunities, is_fresh_repost, AND run_dedup_pass in a single try/except block. ImportError on any one symbol sets _PHASE4_IMPORT_ERROR and causes _require_phase4() to raise in all Phase-4 tests.
- **Fix:** Added `run_dedup_pass()` stub that raises `NotImplementedError` — importable but signals Plan 04-03 needed
- **Files modified:** TARIQ__career_radar/radar/dedup_engine.py
- **Verification:** 5 of 6 Phase-4 tests now GREEN; test_run_dedup_pass_removes_within_run_dups correctly FAILS with NotImplementedError (expected RED)
- **Committed in:** 62d95f1

---

**Total deviations:** 3 auto-fixed (1 blocking dependency, 1 algorithm bug, 1 blocking import structure)  
**Impact on plan:** All auto-fixes required for test contract satisfaction and correct module importability. No scope creep. run_dedup_pass stub is explicitly documented as Plan 04-03 territory.

## Issues Encountered

None beyond the 3 auto-fixed deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `fuzzy_match_opportunities()` and `is_fresh_repost()` are implemented, tested, and committed
- Plan 04-03 (Wave 2) can implement `run_dedup_pass()` replacing the stub — all test infrastructure is ready
- 8 tests GREEN: 3 Phase-1 (persistence/normalization/SQLite), 5 Phase-4 (fuzzy match variants + freshness)
- 1 test RED (test_run_dedup_pass) — correctly awaiting Plan 04-03

---
*Phase: 04-deduplication-engine*
*Completed: 2026-06-15*
