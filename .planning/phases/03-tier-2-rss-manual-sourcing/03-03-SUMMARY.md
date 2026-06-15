---
phase: 03-tier-2-rss-manual-sourcing
plan: "03"
subsystem: sourcing
tags: [jsonl, manual-import, role-filter, keyword-matching, fail-open, salary-annualization]

# Dependency graph
requires:
  - phase: 03-01
    provides: Wave-0 TDD scaffold with 9 failing Phase-3 tests (fixtures + test stubs for SRC-03, SRC-06)
  - phase: 01-foundation-data-model
    provides: BaseSource, OpportunityRaw, SourceResult dataclasses in radar/sources/base.py

provides:
  - ManualImportSource class in radar/sources/manual_import_source.py (SRC-03)
  - run_filter() function in radar/stages/filter.py (SRC-06)

affects:
  - 03-04-PLAN (Wave-2 integration — uses both ManualImportSource and run_filter)
  - Phase 04 dedup — will receive filtered opportunity lists from run_filter
  - Phase 11 pipeline trigger — orchestrates fetch + filter + dedup

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "JSONL line-by-line parsing with per-line error capture — never raises, all errors in SourceResult.errors"
    - "Hourly salary annualization: salary_usd_low * 40 * 52 when salary_per == 'hour'"
    - "Role-keyword filter: exact substring match of opp['title'].lower() against dict[group_name, list[keyword]]"
    - "Fail-open filter: returns all opportunities in-scope when profile seed unavailable"
    - "Lazy import inside run_filter for load_profile_seed — avoids circular dependency at module load time"

key-files:
  created:
    - TARIQ__career_radar/radar/sources/manual_import_source.py
    - TARIQ__career_radar/radar/stages/filter.py
  modified: []

key-decisions:
  - "Fail-open safety net in run_filter: if profile_seed load fails, all opportunities pass through rather than blocking the pipeline"
  - "Hourly salary annualization uses 40 * 52 = 2080 factor (standard full-time work year) — applied only when salary_per='hour' and salary_usd_low is not None"
  - "ManualImportSource treats missing file as normal condition (not an error that stops execution) — returns SourceResult with 0 opportunities and a descriptive error message"
  - "run_filter mutates opportunity dicts in-place by adding matched_role_group — callers pass copies if immutability needed"

patterns-established:
  - "Error contract: sources NEVER raise — all errors captured in SourceResult.errors list"
  - "Filter stages return structured dict: {in_scope, out_of_scope, filter_summary}"
  - "filter_summary includes filter_rate as float for monitoring and diagnostics"

requirements-completed: [SRC-03, SRC-06]

# Metrics
duration: 2min
completed: 2026-06-15
---

# Phase 03 Plan 03: ManualImportSource + run_filter() Summary

**JSONL manual import source (SRC-03) and role-keyword filter stage (SRC-06) implemented; all 5 remaining Wave-0 failing tests turned GREEN, full suite 30 passed**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-15T12:09:05Z
- **Completed:** 2026-06-15T12:10:35Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- ManualImportSource reads JSONL line-by-line, validates required fields, converts hourly salary to annual, and captures all errors without raising
- run_filter() performs exact substring title-matching against profile_seed role_keywords dict, with fail-open safety net when profile unavailable
- All 5 remaining Phase-3 Wave-0 tests now GREEN (3 manual import + 2 role filter)
- Combined with Plan 02 (RSS source): all 9 Phase-3 tests GREEN; 30-test full suite passes

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement ManualImportSource (SRC-03)** - `a76a8ba` (feat)
2. **Task 2: Implement run_filter() filter stage (SRC-06)** - `6a33393` (feat)

**Plan metadata:** (docs commit — to follow)

## Files Created/Modified
- `TARIQ__career_radar/radar/sources/manual_import_source.py` - ManualImportSource class: JSONL reader with hourly-to-annual salary conversion, error capture, never raises
- `TARIQ__career_radar/radar/stages/filter.py` - run_filter() function + _build_result() + _load_profile_seed_safe() helpers: role-keyword filter with fail-open safety

## Decisions Made
- Fail-open design for run_filter: profile seed failures do not block the pipeline — all opportunities pass through with a warning log
- Hourly salary annualization factor 40 * 52 = 2080 (standard full-time work year)
- ManualImportSource.fetch() treats missing file as normal operational condition: returns SourceResult with 0 opportunities and 1 error message, never raises
- run_filter mutates in-scope opportunity dicts in-place (adds matched_role_group key) — this is documented in the docstring; callers pass copies if immutability needed
- Lazy import of load_profile_seed inside _load_profile_seed_safe() to avoid circular import at module load time

## Deviations from Plan

None — plan executed exactly as written.

Note: manual_import_source.py was found already on disk as untracked (from a prior run). Verified all 3 tests pass before committing. No re-implementation needed.

## Issues Encountered
None — both files implemented cleanly on first attempt, all tests passed immediately.

## User Setup Required
None — no external service configuration required. ManualImportSource reads from a gitignored JSONL file that the operator provides at runtime.

## Next Phase Readiness
- SRC-03 and SRC-06 complete; Plan 03-03 done
- Plan 03-04 (Wave-2 integration) can proceed: both ManualImportSource and run_filter() are available for pipeline integration
- All 9 Phase-3 tests GREEN (combined with Plan 02 RSS source): Phase 3 test suite fully passing
- No blockers for Phase 4 (dedup engine)

---
*Phase: 03-tier-2-rss-manual-sourcing*
*Completed: 2026-06-15*
