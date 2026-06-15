---
phase: 04-deduplication-engine
plan: "03"
subsystem: dedup
tags: [dedup-orchestrator, stages, sqlite, fuzzy-matching, freshness-rule, test-isolation]

# Dependency graph
requires:
  - phase: 04-01
    provides: "RED TDD tests for run_dedup_pass; cross_source_batch fixture"
  - phase: 04-02
    provides: "fuzzy_match_opportunities, is_fresh_repost, DedupeEngine, run_dedup_pass stub"
provides:
  - "run_dedup_pass() orchestrator in radar/stages/dedup.py: full dedup pipeline"
  - "_fetch_first_seen() helper for per-opportunity DB freshness lookup"
  - "stages/dedup.py importable as TARIQ__career_radar.radar.stages.dedup"
  - "_isolate_dedup_db autouse fixture: per-test DB isolation (no production pollution)"
affects: [scoring-engine, tag-engine, run-fetch]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single DedupeEngine instance per run_dedup_pass() call (avoids file-handle leak per opportunity)"
    - "Delegation pattern: dedup_engine.run_dedup_pass() re-exports stages/dedup.run_dedup_pass() for import compat"
    - "Per-test autouse fixture patches _DEFAULT_DB_PATH in both dedup_engine and stages/fetch modules"
    - "_fetch_first_seen() helper isolates the cross-run first_seen DB query for readability"

key-files:
  created:
    - TARIQ__career_radar/radar/stages/dedup.py
  modified:
    - TARIQ__career_radar/radar/dedup_engine.py
    - TARIQ__career_radar/radar/stages/fetch.py
    - TARIQ__career_radar/conftest.py

key-decisions:
  - "Implement run_dedup_pass in stages/dedup.py; dedup_engine.run_dedup_pass delegates to it — preserves existing test import contract (imports from dedup_engine) while cleanly locating logic in stages/"
  - "Function-scoped autouse _isolate_dedup_db fixture in conftest.py patches both dedup_engine._DEFAULT_DB_PATH and stages/fetch._DEFAULT_DB_PATH per test — prevents cross-test dedup contamination without changing test signatures"
  - "Print arrow ASCII -> instead of Unicode -> in stages/fetch.py dedup log line (Windows charmap codec cannot encode U+2192)"

patterns-established:
  - "run_dedup_pass pipeline: check_or_add (cross-run) -> freshness check (DB query) -> fuzzy_match_opportunities (within-run) -> append"
  - "Fallback in run_fetch(): if dedup raises, return raw in_scope_opportunities (never silently drop findings)"

requirements-completed: [DEDUP-03]

# Metrics
duration: 278s
completed: 2026-06-15
---

# Phase 4 Plan 03: Deduplication Engine Wave 2 Implementation Summary

**run_dedup_pass() orchestrator in stages/dedup.py completing Phase 4: SQLite cross-run dedup + within-run fuzzy title matching + 30-day freshness repost rule; 9/9 dedup tests GREEN + 36/36 full suite GREEN**

## Performance

- **Duration:** 278s (~4.6 min)
- **Started:** 2026-06-15T14:07:36Z
- **Completed:** 2026-06-15T14:12:14Z
- **Tasks:** 2
- **Files modified/created:** 4

## Accomplishments

- Created `TARIQ__career_radar/radar/stages/dedup.py` with `run_dedup_pass()` implementing the full 3-step dedup pipeline (cross-run exact + freshness rule + within-run fuzzy)
- Added `_fetch_first_seen()` helper for readable first_seen_date DB lookup
- Updated `dedup_engine.run_dedup_pass()` stub to delegate to `stages/dedup` (preserves test import contract)
- Wired `run_dedup_pass()` into `stages/fetch.run_fetch()` with fallback (never drops findings on dedup failure)
- Added function-scoped autouse `_isolate_dedup_db` fixture to conftest.py preventing cross-test DB contamination
- Cleaned production `seen_roles.sqlite` of test fixture data written before isolation was in place

## Task Commits

1. **Task 1: create stages/dedup.py with run_dedup_pass()** - `5abd0eb` (feat)
2. **Task 2: wire run_dedup_pass into run_fetch(); isolate test dedup DB** - `b2293b3` (feat)

## Files Created/Modified

- `TARIQ__career_radar/radar/stages/dedup.py` — NEW: run_dedup_pass() orchestrator + _fetch_first_seen() helper + __main__ block
- `TARIQ__career_radar/radar/dedup_engine.py` — MODIFIED: stub replaced with delegation to stages/dedup
- `TARIQ__career_radar/radar/stages/fetch.py` — MODIFIED: import run_dedup_pass + _DEFAULT_DB_PATH; dedup block after filter stage
- `TARIQ__career_radar/conftest.py` — MODIFIED: _isolate_dedup_db autouse fixture added (Phase 4 wave 2 note)

## Decisions Made

1. **stages/dedup.py + delegation from dedup_engine**: Test file imports `run_dedup_pass` from `dedup_engine` (existing contract). Rather than duplicate logic, implement in `stages/dedup.py` and have `dedup_engine.run_dedup_pass()` delegate to it. Both import paths work.

2. **Function-scoped autouse `_isolate_dedup_db` in conftest.py**: Once `run_fetch()` was wired to run dedup, existing `test_sources.py` tests that all use the same mock opportunity ("AI Operations Manager" / "Acme Corp") would suppress each other via the shared `_DEFAULT_DB_PATH`. A per-test (function scope) fixture patches both `radar.dedup_engine._DEFAULT_DB_PATH` and `radar.stages.fetch._DEFAULT_DB_PATH` to a unique `tmp_path` per test, then restores originals. This eliminates contamination without changing any test signatures.

3. **ASCII `->` in print statement**: The `→` Unicode character in `f"[DEDUP] {n} raw → {m} unique opportunities"` caused `charmap` codec errors on Windows, which then triggered the fallback path (`except Exception`). Replaced with ASCII `->`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] fetch.py is at stages/fetch.py, not radar/fetch.py**
- **Found during:** Task 2 (wiring run_dedup_pass into run_fetch)
- **Issue:** Plan specified `TARIQ__career_radar/radar/fetch.py` but this file does not exist; `run_fetch()` lives in `TARIQ__career_radar/radar/stages/fetch.py`
- **Fix:** Edited `stages/fetch.py` instead; plan's stated key_links correctly reference `stages/fetch.py` so no functional deviation
- **Files modified:** `TARIQ__career_radar/radar/stages/fetch.py`
- **Committed in:** b2293b3

**2. [Rule 1 - Bug] Cross-test dedup contamination: test_sources.py failures after wiring**
- **Found during:** Task 2 verification — `test_required_fields_present` and `test_salary_confidence_tagging` FAILED (0 results from dedup suppressing them)
- **Issue:** After wiring, `run_fetch()` writes mock opportunities to `_DEFAULT_DB_PATH`. `test_normalization_to_schema` runs first and adds "AI Operations Manager"@"Acme Corp" to the DB; subsequent tests in the same session find 0 unique opportunities.
- **Fix:** Added `_isolate_dedup_db` function-scoped autouse fixture in `conftest.py` that patches `_DEFAULT_DB_PATH` to a fresh `tmp_path` per test and restores it after.
- **Files modified:** `TARIQ__career_radar/conftest.py`
- **Committed in:** b2293b3

**3. [Rule 1 - Bug] Unicode arrow caused charmap codec error on Windows**
- **Found during:** Task 2 verification — `[DEDUP] WARNING: dedup pass failed ('charmap' codec can't encode character '→'...)`
- **Issue:** `→` (U+2192) can't be encoded by Windows cp1252 charmap codec in `print()`; triggered the fallback path
- **Fix:** Replaced `→` with ASCII `->` in `stages/fetch.py` print statement
- **Files modified:** `TARIQ__career_radar/radar/stages/fetch.py`
- **Committed in:** b2293b3

---

**Total deviations:** 3 auto-fixed (1 wrong file path, 1 cross-test state bug, 1 Unicode encoding bug)
**Impact on plan:** All auto-fixes required for correctness. No scope creep. Phase 4 dedup pipeline is production-ready.

## Issues Encountered

None beyond the 3 auto-fixed deviations above. Production `seen_roles.sqlite` was cleaned of 1 test fixture row that was written before isolation was in place.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 4 (Deduplication Engine) is complete: DEDUP-01/02/03 all satisfied
- `run_dedup_pass()` is production-ready in `radar/stages/dedup.py`
- `run_fetch()` returns a deduplicated list; double-runs yield 0 new roles (seen-store blocks all)
- Full test suite: 36 passed, 1 skipped, 0 failed (Phase 1-4 tests all GREEN)
- Phase 5 (Scoring Engine) can begin: it depends only on Phase 4

---
*Phase: 04-deduplication-engine*
*Completed: 2026-06-15*
