---
phase: 04-deduplication-engine
plan: "01"
subsystem: TARIQ__career_radar
tags: [tdd, wave-0, dedup, fixtures, red-tests]
dependency_graph:
  requires: []
  provides:
    - dedup_test_data.jsonl (52-record fixture for fuzzy/freshness/cross-source tests)
    - conftest.py Phase-4 fixtures (dedup_opp_pairs, dedup_fresh_record, cross_source_batch)
    - test_dedup_engine.py Phase-4 RED tests (6 contracts for DEDUP-01/02/03)
  affects:
    - TARIQ__career_radar/tests/test_dedup_engine.py
    - TARIQ__career_radar/conftest.py
tech_stack:
  added: []
  patterns:
    - _require_phase4() import guard for collectible-but-failing TDD (same as existing _require_module pattern)
    - JSONL fixture with title-variant pairs for fuzzy matching acceptance contracts
key_files:
  created:
    - TARIQ__career_radar/tests/fixtures/dedup_test_data.jsonl
  modified:
    - TARIQ__career_radar/conftest.py
    - TARIQ__career_radar/tests/test_dedup_engine.py
decisions:
  - "test_run_dedup_pass asserts len(result)==3 (not 2 as plan comment stated): cross_source_batch has 4 opps with 1 duplicate pair, yielding 3 unique — plan comment was internally inconsistent with fixture definition"
  - "datetime import added to conftest.py for dedup_fresh_record fixture (utcnow - timedelta)"
metrics:
  duration: "154s"
  completed_date: "2026-06-15"
  tasks_completed: 2
  files_modified: 3
---

# Phase 04 Plan 01: Wave 0 TDD Scaffold for Deduplication Engine Summary

Wave 0 TDD scaffold for Phase 4 dedup engine: 52-record JSONL fixture plus 6 collectible RED tests defining acceptance contracts for fuzzy matching (DEDUP-02), freshness rule (DEDUP-03), and cross-source dedup (DEDUP-02).

## What Was Built

Three deliverables that establish the RED baseline for Phase 4 Wave 1/2 implementation:

1. **`dedup_test_data.jsonl`** — 52 synthetic opportunity records organized as 26 title-variant pairs. Includes 5 cross-source pairs (same role from greenhouse + remotive), 3 records with `access_date` set to `2026-01-10T10:00:00Z` (>30 days before current date for freshness tests). All companies are synthetic (Acme Corp, Beta Inc, Gamma LLC, etc.).

2. **`conftest.py` Phase-4 section** — Three new pytest fixtures appended after the Phase-3 section:
   - `dedup_opp_pairs(fixtures_dir)`: loads `dedup_test_data.jsonl`, returns `list[dict]`
   - `dedup_fresh_record()`: returns `{"first_seen_date": ..., "last_seen_date": ..., "hit_count": 1}` with `first_seen` 45 days ago
   - `cross_source_batch()`: hardcoded 4-item list with one cross-source duplicate pair

3. **`test_dedup_engine.py` Phase-4 RED tests** — 6 new test functions with `_require_phase4()` guard that fails RED cleanly until Wave 1 adds the missing symbols.

## Test Results

```
pytest TARIQ__career_radar/tests/test_dedup_engine.py -v
3 passed, 6 failed, 0 errors
```

- `test_sqlite_roundtrip` — PASSED (DATA-03, Phase-1)
- `test_normalization_deterministic` — PASSED (DATA-03, Phase-1)
- `test_persistence_across_restarts` — PASSED (DATA-03, Phase-1)
- `test_fuzzy_match_title_variants` — FAILED RED (DEDUP-02)
- `test_fuzzy_match_no_false_positive` — FAILED RED (DEDUP-02)
- `test_fuzzy_match_same_company_exact_location` — FAILED RED (DEDUP-02)
- `test_is_fresh_repost_old_role_surfaces` — FAILED RED (DEDUP-03)
- `test_is_fresh_repost_recent_stays_hidden` — FAILED RED (DEDUP-03)
- `test_run_dedup_pass_removes_within_run_dups` — FAILED RED (DEDUP-02, DEDUP-03)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed inconsistent assertion in test_run_dedup_pass**
- **Found during:** Task 2
- **Issue:** Plan comment said "len(result) == 2 (only 2 unique roles; 2 cross-source duplicates removed)" but `cross_source_batch` has 4 items with only 1 duplicate pair — removing 1 duplicate from 4 items yields 3 unique results, not 2.
- **Fix:** Used `assert len(result) == 3` which correctly reflects: AI Ops Manager (1st occurrence kept), Finance Manager (distinct), Data Annotator (distinct). The duplicate "AI Ops Manager" from remotive is removed.
- **Files modified:** `TARIQ__career_radar/tests/test_dedup_engine.py`
- **Commit:** 83e69b6

## Commits

| Hash | Message |
|------|---------|
| 597d970 | feat(04-01): add dedup_test_data.jsonl fixture and Phase-4 conftest fixtures |
| 83e69b6 | test(04-01): append 6 failing Phase-4 RED tests to test_dedup_engine.py (Wave 0) |

## Self-Check: PASSED

- [x] `TARIQ__career_radar/tests/fixtures/dedup_test_data.jsonl` exists with 52 records
- [x] `TARIQ__career_radar/conftest.py` updated with 3 Phase-4 fixtures
- [x] `TARIQ__career_radar/tests/test_dedup_engine.py` has 9 collectible tests (3 GREEN + 6 RED)
- [x] Commits 597d970 and 83e69b6 present in git log
