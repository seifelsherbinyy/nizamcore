---
phase: 01-foundation-data-model
plan: "05"
subsystem: TARIQ__career_radar
tags: [dedup, sqlite, normalization, data-model, stdlib]
dependency_graph:
  requires: [01-03]
  provides: [DedupeEngine, compute_dedup_key, normalize_title, normalize_company, normalize_location]
  affects: []
tech_stack:
  added: []
  patterns: [sqlite3-stdlib, NFKD-normalization, dict-return-pattern]
key_files:
  created: []
  modified:
    - TARIQ__career_radar/radar/dedup_engine.py
decisions:
  - "check_or_add returns dict (not tuple) with 'is_duplicate', 'key', 'hit_count' — matches test fixture expectation"
  - "utcnow().isoformat()+'Z' retained per plan spec (stdlib-only; DeprecationWarning is advisory only on 3.12)"
  - "normalize_company strips only first matched suffix (break after first hit) to avoid double-stripping"
metrics:
  duration_minutes: 8
  completed_date: "2026-06-14T20:23:00Z"
  tasks_completed: 1
  tasks_total: 1
  files_modified: 1
  files_created: 0
---

# Phase 1 Plan 05: DedupeEngine SQLite-Backed Seen-Role Store Summary

**One-liner:** SQLite dedup engine with NFKD title normalization, company suffix stripping, and remote-location detection — 3 DATA-03 tests GREEN, no new dependencies.

## Objective

Implement `TARIQ__career_radar/radar/dedup_engine.py` replacing the Wave 0 stub with a full SQLite-backed seen-role store that detects duplicate opportunities across Python process restarts.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement dedup_engine.py — normalization + DedupeEngine | b83df53 | TARIQ__career_radar/radar/dedup_engine.py |

## Implementation Details

### Normalization Functions

- `normalize_title(title)`: NFKD Unicode decomposition, strips combining diacritical marks (e.g. accent chars), lowercases. Handles "Spécialist" → "specialist".
- `normalize_company(company)`: Strips legal suffixes (, inc / , inc. / , ltd / , ltd. / , llc / , llc. and space-separated variants), collapses internal whitespace, lowercases. "Acme, Inc." → "acme".
- `normalize_location(location)`: If "remote" appears anywhere in the lowercased string, returns "remote". Otherwise returns lowercased stripped location. "Remote / Worldwide" → "remote".
- `compute_dedup_key(title, company, location)`: Returns `(normalize_title, normalize_company, normalize_location)` tuple. Deterministic across all runs.

### DedupeEngine Class

- `__init__(db_path)`: Stores path and calls `_init_db()`.
- `_init_db()`: Creates parent directory if needed, connects to SQLite, creates `seen_roles` table with `UNIQUE(title_canonical, company_canonical, location_canonical)` constraint.
- `check_or_add(opportunity)`: Reads title/company/location via `.get()` with empty-string fallback, computes canonical key, SELECTs for existing row. If found: updates `last_seen_date` + increments `hit_count`, returns `{"is_duplicate": True, ...}`. If not found: INSERTs new row, returns `{"is_duplicate": False, ...}`.

### Return Shape

The tests use `result["is_duplicate"]` (dict access), not tuple unpacking. The RESEARCH.md examples used a tuple; the actual test fixture requires a dict. Implementation follows the test contract.

### Privacy

`TARIQ__career_radar/data/seen_roles.sqlite` is gitignored via `TARIQ__career_radar/.gitignore` line `data/` — confirmed with `git check-ignore`.

## Test Results

```
TARIQ__career_radar/tests/test_dedup_engine.py::test_sqlite_roundtrip          PASSED
TARIQ__career_radar/tests/test_dedup_engine.py::test_normalization_deterministic PASSED
TARIQ__career_radar/tests/test_dedup_engine.py::test_persistence_across_restarts PASSED
3 passed in 0.09s
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Return type is dict, not tuple**
- **Found during:** Task 1 — reading test file before implementation
- **Issue:** RESEARCH.md code examples and PLAN.md interfaces block show `check_or_add` returning `tuple[bool, str]`. The actual test assertions use `result["is_duplicate"]` (dict subscript), not tuple unpacking.
- **Fix:** Implemented `check_or_add` to return `dict{"is_duplicate": bool, "key": str, "hit_count": int}` — matching the test contract.
- **Files modified:** TARIQ__career_radar/radar/dedup_engine.py
- **Commit:** b83df53

## Self-Check: PASSED

- `TARIQ__career_radar/radar/dedup_engine.py` — FOUND
- Commit b83df53 — FOUND
- 3 DATA-03 tests GREEN — CONFIRMED
- db file gitignored — CONFIRMED
- No new dependency added — CONFIRMED (stdlib sqlite3, unicodedata, datetime, pathlib only)
