---
phase: 02-tier-1-ats-sourcing
plan: "02"
subsystem: TARIQ__career_radar
tags: [tdd, ats, greenhouse, lever, connectors, wave-1]
dependency_graph:
  requires: [02-01]
  provides: [BaseSource, SourceResult, OpportunityRaw, GreenhouseSource, LeverSource, config_sources.yaml]
  affects: [02-03-PLAN, 02-04-PLAN]
tech_stack:
  added: []
  patterns: [BaseSource-ABC-pattern, never-raise-connector-contract, skip-limit-pagination, rate-limited-return-not-retry]
key_files:
  created:
    - TARIQ__career_radar/radar/sources/__init__.py
    - TARIQ__career_radar/radar/sources/base.py
    - TARIQ__career_radar/radar/sources/greenhouse_source.py
    - TARIQ__career_radar/radar/sources/lever_source.py
    - TARIQ__career_radar/radar/config_sources.yaml
  modified:
    - TARIQ__career_radar/conftest.py
key_decisions:
  - "conftest.py extended with TARIQ__career_radar/ on sys.path so that radar.* short imports (used by test_sources.py _require_module calls) resolve correctly — Rule 3 fix"
  - "LeverSource pagination stops when len(page) < limit; the single-item fixture (len=1 < limit=100) correctly produces 1 opportunity in one page"
  - "salary_usd_low/high remain None in LeverSource always; salary confidence tagged at normalization layer (run_fetch, 02-04), not in the connector"
  - "test_fetch_network_error_graceful and test_429_rate_limit_handled went GREEN as a bonus — error-handling contract satisfied by GreenhouseSource implementation"
metrics:
  duration: "~3 minutes (191 seconds)"
  completed_date: "2026-06-15"
  tasks_completed: 2
  tasks_total: 2
  files_created: 5
  files_modified: 1
requirements: [SRC-01, SRC-04, SRC-05]
---

# Phase 02 Plan 02: GreenhouseSource + LeverSource Connectors Summary

**One-liner:** BaseSource ABC + SourceResult/OpportunityRaw dataclasses + Greenhouse and Lever connectors with never-raise contract, 429 rate-limit handling, and skip/limit pagination — turning 4 of 11 tests GREEN.

---

## What Was Built

Wave 1a delivers the contract layer and two working connectors:

**1. Contract Layer — `radar/sources/base.py`**
- `OpportunityRaw` dataclass: title, company, location, source_url, source, source_type, salary_usd_low/high (Optional[float]), raw_payload
- `SourceResult` dataclass: source_name, opportunities, errors (default=[]), rate_limited (default=False), fetch_duration_sec (default=0.0)
- `BaseSource` ABC: abstract `fetch(constraints) -> SourceResult`, `_is_enabled(config)`, `_rate_limited_sleep()`, `_exponential_backoff(attempt, base_sec=2.0)`

**2. Package init — `radar/sources/__init__.py`**
Empty file making `radar.sources` a proper Python package.

**3. Greenhouse Connector — `radar/sources/greenhouse_source.py`**
- Fetches `https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`
- Maps: title, company (from response or config fallback), location.name, absolute_url, salary_min/max
- 429 → returns SourceResult(rate_limited=True, errors=[...]) — no retry
- Timeout → SourceResult(errors=["Request timeout: ..."])
- Any other exception → SourceResult(errors=["Unexpected error: ..."])
- Never raises from fetch()

**4. Lever Connector — `radar/sources/lever_source.py`**
- Paginates `https://api.lever.co/v0/postings/{site}?mode=json&skip={skip}&limit={limit}`
- skip/limit loop (limit=100, max_pages=100); stops when response is empty or len < limit
- Company name injected from config (Lever API does not return it)
- salary_usd_low/high always None (salary confidence = LOW, tagged at normalization time)
- 429 → returns immediately with rate_limited=True, no retry
- Timeout/exception per page → stops loop, appends error, returns accumulated results

**5. Seed Config — `radar/config_sources.yaml`**
6 Greenhouse boards (anthropic, openai, scale-ai, deepmind, huggingface, weights-and-biases),
6 Lever boards (airtable, notion, retool, linear, figma, loom),
5 Ashby boards (modal, replicate, together-ai, mistral-ai, runway),
3 Workable boards (deepl, jasper, copy-ai).

---

## Verification Results

```
py -3 -m pytest TARIQ__career_radar/tests/ -v

24 collected
17 passed, 7 failed

PASSED: test_greenhouse_fetch_mocked     (SRC-01 GREEN)
PASSED: test_lever_fetch_mocked          (SRC-01 GREEN)
PASSED: test_fetch_network_error_graceful (SRC-05 GREEN — bonus)
PASSED: test_429_rate_limit_handled      (SRC-05 GREEN — bonus)
PASSED: 13 Phase-1 tests (no regressions)

FAILED (expected RED — later plans):
  test_ashby_fetch_mocked     (02-03)
  test_workable_fetch_mocked  (02-03)
  test_normalization_to_schema (02-04)
  test_required_fields_present (02-04)
  test_salary_confidence_tagging (02-04)
  test_blocked_sources_manifest (02-04)
  test_zero_results_graceful  (02-04)
```

---

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | BaseSource + SourceResult + OpportunityRaw + config_sources.yaml | 236bc11 |
| 2 | GreenhouseSource + LeverSource + conftest sys.path fix | f57eacc |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] conftest.py sys.path missing TARIQ__career_radar/**

- **Found during:** Task 2 (first test run)
- **Issue:** `test_sources.py` calls `_require_module("radar.sources.greenhouse_source")` which needs `radar` importable directly. conftest.py only added NIZAM repo root to sys.path; `TARIQ__career_radar/` was not on sys.path so `radar.*` imports failed with `ModuleNotFoundError: No module named 'radar'`.
- **Fix:** Appended 5-line sys.path block to conftest.py adding `TARIQ__career_radar/` (the conftest's own parent directory). This is additive — no existing logic changed.
- **Files modified:** `TARIQ__career_radar/conftest.py`
- **Commit:** f57eacc

### Bonus Tests GREEN

`test_fetch_network_error_graceful` and `test_429_rate_limit_handled` both turned GREEN as a byproduct of the GreenhouseSource implementation satisfying the SRC-05 error contract. The plan marked these as "remaining RED (Ashby/Workable/orchestrator tests)" but these two are connector-level (GreenhouseSource-only) so they went GREEN now. This is correct — not a deviation from contract.

---

## Self-Check

- [x] `TARIQ__career_radar/radar/sources/__init__.py` — FOUND
- [x] `TARIQ__career_radar/radar/sources/base.py` — FOUND
- [x] `TARIQ__career_radar/radar/sources/greenhouse_source.py` — FOUND
- [x] `TARIQ__career_radar/radar/sources/lever_source.py` — FOUND
- [x] `TARIQ__career_radar/radar/config_sources.yaml` — FOUND
- [x] `TARIQ__career_radar/conftest.py` — modified (FOUND)
- [x] Commit 236bc11 — FOUND
- [x] Commit f57eacc — FOUND
- [x] test_greenhouse_fetch_mocked PASSED — VERIFIED
- [x] test_lever_fetch_mocked PASSED — VERIFIED
- [x] Phase-1 13 tests still PASSED — VERIFIED
- [x] 7 remaining RED tests are all expected (Ashby/Workable/orchestrator) — VERIFIED

## Self-Check: PASSED
