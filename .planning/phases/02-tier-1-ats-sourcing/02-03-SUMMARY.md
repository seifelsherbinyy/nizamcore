---
phase: 02-tier-1-ats-sourcing
plan: "03"
subsystem: TARIQ__career_radar
tags: [tdd, ats, ashby, workable, connectors, wave-2]
dependency_graph:
  requires: [02-01, 02-02]
  provides: [AshbySource, WorkableSource]
  affects: [02-04-PLAN]
tech_stack:
  added: []
  patterns: [BaseSource-ABC-pattern, never-raise-connector-contract, USD-only-salary-filter, company-from-response-root]
key_files:
  created:
    - TARIQ__career_radar/radar/sources/ashby_source.py
    - TARIQ__career_radar/radar/sources/workable_source.py
  modified: []
key_decisions:
  - "AshbySource filters salary to None when currency != 'USD'; only populates salary_usd_low/high when Ashby returns a USD salary object"
  - "WorkableSource extracts company_name from data['name'] (response root), not per-job field; config company_name is a fallback only"
  - "Both connectors mirror greenhouse_source.py/lever_source.py exactly: time.monotonic() timing, fetch_duration_sec, per-item try/except, never-raise outer guard"
metrics:
  duration: "~91 seconds"
  completed_date: "2026-06-15"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
requirements: [SRC-01, SRC-04, SRC-05]
---

# Phase 02 Plan 03: AshbySource + WorkableSource Connectors Summary

**One-liner:** AshbySource with USD-only salary extraction (HIGH confidence) and WorkableSource extracting company from API response root (no salary, LOW confidence) — completing the four-connector ATS fleet and turning 6 of 11 tests GREEN.

---

## What Was Built

Wave 1b delivers two new connectors, completing the ATS sourcing layer:

**1. Ashby Connector — `radar/sources/ashby_source.py`**
- Fetches `https://api.ashbyhq.com/posting-api/job-board/{board_name}?includeCompensation=true`
- Extracts `compensation.salary.min/max` only when `currency == "USD"` (else salary_usd_low/high = None)
- Company name injected from config (`board_name` / `company_name`; Ashby API does not embed company per-job)
- 429 → returns SourceResult(rate_limited=True, errors=[...]) — no retry
- Timeout → SourceResult(errors=["Request timeout: ..."])
- Any other exception → SourceResult(errors=["Unexpected error: ..."])
- Never raises from fetch()

**2. Workable Connector — `radar/sources/workable_source.py`**
- Fetches `https://apply.workable.com/api/v1/widget/accounts/{account_subdomain}?details=true`
- Company name sourced from `data["name"]` (response root) — same for all jobs in the response
- Config `company_name` kept as fallback in case response root "name" is absent
- Location assembled from `location.region`, `location.city`, `location.country` joined with ", "
- salary_usd_low/high always None (Workable API does not expose salary)
- Same error-handling pattern: 429/Timeout/Exception all return errors, never raise

---

## Verification Results

```
py -3 -m pytest TARIQ__career_radar/tests/ -v

24 collected
19 passed, 5 failed

PASSED: test_greenhouse_fetch_mocked     (SRC-01 GREEN — from 02-02)
PASSED: test_lever_fetch_mocked          (SRC-01 GREEN — from 02-02)
PASSED: test_ashby_fetch_mocked          (SRC-01 GREEN — NEW)
PASSED: test_workable_fetch_mocked       (SRC-01 GREEN — NEW)
PASSED: test_fetch_network_error_graceful (SRC-05 GREEN — from 02-02)
PASSED: test_429_rate_limit_handled      (SRC-05 GREEN — from 02-02)
PASSED: 13 Phase-1 tests (no regressions)

FAILED (expected RED — 02-04 scope):
  test_normalization_to_schema     (needs radar.stages.fetch.run_fetch)
  test_required_fields_present     (needs radar.stages.fetch.run_fetch)
  test_salary_confidence_tagging   (needs radar.stages.fetch.run_fetch)
  test_blocked_sources_manifest    (needs radar.stages.fetch.run_fetch)
  test_zero_results_graceful       (needs radar.stages.fetch.run_fetch)
```

Connector-level assertions verified:
- `test_ashby_fetch_mocked`: 1 opportunity, title="ML Platform Engineer", salary_usd_low=120000, salary_usd_high=160000, errors=[], rate_limited=False
- `test_workable_fetch_mocked`: 1 opportunity, title="AI Ops Coordinator", company="Acme Corp" (from response root), salary_usd_low=None, errors=[], rate_limited=False

---

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | AshbySource connector with USD salary extraction | e9a74dc |
| 2 | WorkableSource connector extracting company from response root | a887762 |

---

## Deviations from Plan

None — plan executed exactly as written.

Both connectors mirrored the greenhouse_source.py / lever_source.py pattern precisely. No deviations, no extra fixes needed.

---

## Self-Check

- [x] `TARIQ__career_radar/radar/sources/ashby_source.py` — FOUND
- [x] `TARIQ__career_radar/radar/sources/workable_source.py` — FOUND
- [x] Commit e9a74dc — FOUND
- [x] Commit a887762 — FOUND
- [x] test_ashby_fetch_mocked PASSED — VERIFIED
- [x] test_workable_fetch_mocked PASSED — VERIFIED
- [x] Phase-1 13 tests still PASSED — VERIFIED (19 passed total, no regressions)
- [x] 5 remaining RED tests all expect radar.stages.fetch (02-04 scope) — VERIFIED

## Self-Check: PASSED
