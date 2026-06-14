---
phase: 02-tier-1-ats-sourcing
plan: "01"
subsystem: TARIQ__career_radar
tags: [tdd, ats, fixtures, test-scaffold, wave-0]
dependency_graph:
  requires: [01-foundation-data-model]
  provides: [ats-fixture-json, conftest-fake-http, test_sources-red]
  affects: [02-02-PLAN, 02-03-PLAN]
tech_stack:
  added: []
  patterns: [_require_module-tdd-pattern, fake-requests-get-factory, recorded-fixture-json]
key_files:
  created:
    - TARIQ__career_radar/tests/fixtures/greenhouse_sample_response.json
    - TARIQ__career_radar/tests/fixtures/lever_sample_response.json
    - TARIQ__career_radar/tests/fixtures/ashby_sample_response.json
    - TARIQ__career_radar/tests/fixtures/workable_sample_response.json
    - TARIQ__career_radar/tests/test_sources.py
  modified:
    - TARIQ__career_radar/conftest.py
key_decisions:
  - "fake_requests_get is a fixture returning a factory (make_fake_get) so each test can independently configure status_code, json_data, or raise_exc without shared state"
  - "test_salary_confidence_tagging verifies salary_confidence via run_fetch normalized output (not raw SourceResult) — matches the normalization contract defined in 02-RESEARCH.md"
metrics:
  duration: "~3 minutes (149 seconds)"
  completed_date: "2026-06-15"
  tasks_completed: 3
  tasks_total: 3
  files_created: 5
  files_modified: 1
requirements: [SRC-01, SRC-04, SRC-05]
---

# Phase 02 Plan 01: Wave 0 ATS Test Scaffold Summary

**One-liner:** TDD scaffold for Tier-1 ATS sourcing — 4 recorded fixture JSONs, fake-HTTP factory in conftest, 11 RED tests encoding the full SRC-01/04/05 contract.

---

## What Was Built

Wave 0 establishes the test contract before any production connector code exists. Three categories of work:

**1. Recorded Fixture JSON Files** (`tests/fixtures/`)
Four ATS API response snapshots in their native shapes, used by conftest loaders to serve fake HTTP responses without any network access:
- `greenhouse_sample_response.json` — `{"jobs": [...]}` with `salary_min`/`salary_max` fields
- `lever_sample_response.json` — flat list `[...]` with `categories.location` and no salary
- `ashby_sample_response.json` — `{"jobPostings": [...]}` with `compensation.salary.min/max`
- `workable_sample_response.json` — `{"name": "...", "jobs": [...]}` with `location.region`

**2. conftest.py Extensions** (appended to existing Phase-1 fixtures)
- `fixtures_dir` — resolves `tests/fixtures/` relative to conftest, loader-safe on all platforms
- `mock_greenhouse_response`, `mock_lever_response`, `mock_ashby_response`, `mock_workable_response` — JSON-loaded dicts/lists from the fixture files
- `fake_requests_get` — a pytest fixture returning a `make_fake_get(status_code, json_data, raise_exc)` factory; injected via `monkeypatch.setattr(requests, "get", ...)` so no real HTTP is ever made

**3. test_sources.py** — 11 failing TDD tests
Uses `_require_module()` (identical pattern to Phase-1 Plan 01-01): each test imports the not-yet-existing connector via `importlib`, catches `ModuleNotFoundError`, and calls `pytest.fail("MISSING — implement in Wave 1/2: ...")`. This produces **FAILED** (not **ERROR**) status — tests are collected cleanly, and the GREEN assertion logic is written now as dead code so Wave-1 implementors know exactly what to satisfy.

---

## Verification Results

```
py -3 -m pytest TARIQ__career_radar/tests/test_sources.py -v
11 collected, 11 failed — all FAILED (no ERROR, no network)

py -3 -m pytest TARIQ__career_radar/tests/ -v
11 failed, 13 passed — Phase-1 still 13/13 GREEN
```

All 11 failures are `Failed: MISSING — implement in Wave 1/2:` — the canonical RED state.

---

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | 4 ATS fixture JSON files created under tests/fixtures/ | d794004 |
| 2 | conftest.py extended with fake_requests_get + mock_*_response fixtures | 33156d4 |
| 3 | test_sources.py with 11 RED tests (SRC-01/04/05 contract) | 37cf3d2 |

---

## Deviations from Plan

None — plan executed exactly as written.

The `test_salary_confidence_tagging` test references `run_fetch` from `radar.stages.fetch` (rather than only the raw `SourceResult`) to verify salary_confidence at the normalization layer, which is where the plan specifies it lives. This is consistent with the GREEN contract in 02-RESEARCH.md and the plan's `<behavior>` spec.

---

## Self-Check

- [x] `TARIQ__career_radar/tests/fixtures/greenhouse_sample_response.json` — FOUND
- [x] `TARIQ__career_radar/tests/fixtures/lever_sample_response.json` — FOUND
- [x] `TARIQ__career_radar/tests/fixtures/ashby_sample_response.json` — FOUND
- [x] `TARIQ__career_radar/tests/fixtures/workable_sample_response.json` — FOUND
- [x] `TARIQ__career_radar/tests/test_sources.py` — FOUND
- [x] `TARIQ__career_radar/conftest.py` — extended (FOUND)
- [x] Commit d794004 — FOUND
- [x] Commit 33156d4 — FOUND
- [x] Commit 37cf3d2 — FOUND
- [x] 11 tests collected, 11 FAILED, 0 ERROR — VERIFIED
- [x] Phase-1 13 tests still PASSED — VERIFIED

## Self-Check: PASSED
