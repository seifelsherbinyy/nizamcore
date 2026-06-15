---
phase: 05-scoring-engine
plan: "03"
subsystem: pipeline
tags: [python, scoring, pipeline, orchestrator, stages]

# Dependency graph
requires:
  - phase: 05-scoring-engine/05-02
    provides: ScoringEngine + ScoreBreakdown + 8 dimension compute functions
  - phase: 04-deduplication-engine/04-03
    provides: run_dedup_pass() returning deduplicated opportunities list

provides:
  - run_scoring_pass() orchestrator in radar/stages/score.py
  - Pipeline wiring: score stage called after dedup stage in fetch.py
  - Every opportunity exiting run_fetch() has final_score (int) and score_breakdown (dict)
  - Opportunities sorted descending by final_score in pipeline output

affects:
  - 06-salary-confidence (receives scored opportunities)
  - 07-tagging-profile-matching (operates on scored opportunities)
  - 08-telegram-report (displays final_score in reports)
  - 11-on-demand-trigger (end-to-end pipeline complete through scoring)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Orchestrator stage pattern: profile loaded once per batch call (not per-opportunity)"
    - "Graceful degradation: missing required fields → final_score=0, no crash"
    - "Pipeline wiring: additive two-line change (import + call) in fetch.py"
    - "Score breakdown as flat dict with all 8 dimension keys + penalties + final"

key-files:
  created:
    - TARIQ__career_radar/radar/stages/score.py
  modified:
    - TARIQ__career_radar/radar/stages/fetch.py

key-decisions:
  - "Profile loaded once per run_scoring_pass() call, not per-opportunity, for determinism"
  - "Missing REQUIRED_FIELDS → final_score=0 + error breakdown dict, pipeline continues"
  - "score_breakdown dict includes all 8 dimension keys + penalties + final key"
  - "Scoring wired as additive two-line change to fetch.py (import + call after dedup)"

patterns-established:
  - "Stage orchestrators freeze shared state (profile, now) once before iterating opportunities"
  - "Per-opportunity error isolation: bad record gets fallback score, does not crash batch"

requirements-completed:
  - SCORE-01

# Metrics
duration: 2min
completed: 2026-06-15
---

# Phase 5 Plan 03: Scoring Stage Summary

**run_scoring_pass() orchestrator wired into fetch.py pipeline after dedup, enriching every opportunity with final_score (0-100) and score_breakdown dict; all 18 scoring tests GREEN**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-15T14:50:04Z
- **Completed:** 2026-06-15T14:51:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `radar/stages/score.py` with `run_scoring_pass()` orchestrator that applies `ScoringEngine` to every deduplicated opportunity
- Wired scoring stage into `fetch.py` with two additive lines (import + call after `run_dedup_pass`)
- All 18 scoring tests GREEN including `test_run_scoring_pass_batch` (was the sole failing test before this plan)
- Full suite GREEN: 54 passed, 1 skipped, 0 failures — no regressions across all prior phases

## Task Commits

Each task was committed atomically:

1. **Task 1: stages/score.py — run_scoring_pass orchestrator** - `7a26f6f` (feat)
2. **Task 2: Wire score stage into fetch.py pipeline** - `2c7c2b2` (feat)

**Plan metadata:** _(final docs commit — see below)_

## Files Created/Modified

- `TARIQ__career_radar/radar/stages/score.py` — Phase 5 scoring orchestrator: run_scoring_pass() that loads profile once, iterates opportunities, calls ScoringEngine.score(), handles missing-field errors, returns sorted list
- `TARIQ__career_radar/radar/stages/fetch.py` — Added import of run_scoring_pass + call after run_dedup_pass; pipeline now: sources → normalize → filter → dedup → score → return

## Decisions Made

- Profile is loaded once at the top of `run_scoring_pass()` (not per-opportunity) to guarantee determinism across the entire batch
- Missing required fields (`title`, `company`, `source`, `source_type`, `access_date`) result in `final_score=0` and a descriptive `score_breakdown={"error": "missing_required_fields", "missing": [...]}` so the pipeline never crashes on bad data
- `score_breakdown` dict includes all 8 dimension keys plus `penalties` and `final` key for downstream consumers

## Deviations from Plan

None - plan executed exactly as written. The two-line additive change to fetch.py matched the plan specification precisely.

## Issues Encountered

None. The test that was failing (`test_run_scoring_pass_batch`) passed immediately after creating score.py with the correct implementation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 5 (Scoring Engine) is fully complete: SCORE-01 satisfied
- Every opportunity exiting `run_fetch()` now carries `final_score` (int 0-100) and `score_breakdown` (dict with 8 dimensions + penalties)
- Phase 6 (Salary & Confidence Discipline) can proceed — scored opportunities are ready for salary tagging enrichment
- Phase 7 (Tagging & Profile Matching) can also proceed in parallel

---
*Phase: 05-scoring-engine*
*Completed: 2026-06-15*
