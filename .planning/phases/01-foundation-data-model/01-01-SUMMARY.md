---
phase: 01-foundation-data-model
plan: "01"
subsystem: testing
tags: [pytest, tdd, wave0, json-schema, sqlite, privacy, career-radar]

# Dependency graph
requires: []
provides:
  - "Wave 0 TDD scaffold: 13 failing tests across 6 test files covering DATA-01..DATA-05"
  - "conftest.py with shared fixtures: tmp_db_path, sample_opportunity, sample_profile, schema_path, repo_root"
  - "TARIQ__career_radar package structure: __init__.py, radar/__init__.py, tests/__init__.py"
  - ".gitignore entries protecting TARIQ__career_radar/data/ from accidental commit"
affects:
  - 01-02-foundation  # schema creation must turn test_opportunity_schema.py GREEN
  - 01-03-foundation  # profile config must turn test_config.py GREEN
  - 01-04-foundation  # dedup engine must turn test_dedup_engine.py GREEN
  - 01-05-foundation  # folder layout must turn test_structure.py GREEN
  - 01-06-foundation  # registration must turn test_registration.py and test_privacy.py GREEN

# Tech tracking
tech-stack:
  added: [pytest-9.0.2 (already installed), jsonschema (importorskip guard)]
  patterns:
    - "try/except ImportError at module level + _require_module() helper for collectible-but-failing TDD tests"
    - "parents[2] from test files in tests/ subdirectory to resolve repo root"
    - "Fixture-injected paths (repo_root, schema_path) decouple tests from hardcoded paths"

key-files:
  created:
    - TARIQ__career_radar/conftest.py
    - TARIQ__career_radar/__init__.py
    - TARIQ__career_radar/radar/__init__.py
    - TARIQ__career_radar/tests/__init__.py
    - TARIQ__career_radar/tests/test_opportunity_schema.py
    - TARIQ__career_radar/tests/test_config.py
    - TARIQ__career_radar/tests/test_dedup_engine.py
    - TARIQ__career_radar/tests/test_structure.py
    - TARIQ__career_radar/tests/test_registration.py
    - TARIQ__career_radar/tests/test_privacy.py
  modified:
    - .gitignore

key-decisions:
  - "Used try/except ImportError + _require_module() helper instead of top-level import in test_config.py and test_dedup_engine.py — allows pytest to collect all 13 tests cleanly while tests still FAIL (ImportError) at runtime"
  - "parents[2] (not parents[3] as plan interface specified) is the correct repo root depth for test files at TARIQ__career_radar/tests/*.py"
  - "test_privacy::test_profile_not_in_egress uses pytest.skip when profile_cache.json absent — vacuously safe; full egress enforcement tested once DATA-02 creates the file"

patterns-established:
  - "TDD-collectible-RED pattern: wrap module-level imports in try/except; re-raise via _require_module() inside each test function"
  - "All test files use Path(__file__).resolve().parents[2] for repo root (2 levels up from TARIQ__career_radar/tests/)"
  - "TARIQ data paths (data/) are gitignored; package source (radar/, tests/) is committable"

requirements-completed: [DATA-01, DATA-02, DATA-03, DATA-04, DATA-05]

# Metrics
duration: 5min
completed: 2026-06-14
---

# Phase 01 Plan 01: Foundation Data Model Wave 0 TDD Scaffold Summary

**pytest Wave 0 scaffold — 13 collectible RED tests covering DATA-01..05 (schema, config, dedup, structure, registration, privacy) with shared conftest fixtures and TARIQ package roots**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-14T20:06:17Z
- **Completed:** 2026-06-14T20:11:05Z
- **Tasks:** 2 of 2
- **Files created:** 10 | **Files modified:** 1

## Accomplishments

- conftest.py with 5 shared fixtures (tmp_db_path, sample_opportunity, sample_profile, schema_path, repo_root) — all synthetic, zero personal data
- 6 test files covering all 5 DATA requirements; 13 tests collected by pytest with 0 collection errors
- All 12 substantive tests FAIL RED for the right reasons (ImportError/FileNotFoundError/AssertionError); 1 test skips correctly (profile_cache absent is expected)
- TARIQ package hierarchy (__init__.py files) and .gitignore data-path exclusions established

## Task Commits

1. **Task 1: conftest.py + tests/__init__.py** — `751a367` (test)
2. **Task 2: all 6 test files + package inits + .gitignore** — `15f2a08` (test)

## Files Created/Modified

- `TARIQ__career_radar/conftest.py` — shared pytest fixtures (tmp_db_path, sample_opportunity, sample_profile, schema_path, repo_root)
- `TARIQ__career_radar/__init__.py` — package root (enables dotted imports from repo root)
- `TARIQ__career_radar/radar/__init__.py` — radar sub-package root
- `TARIQ__career_radar/tests/__init__.py` — tests package for pytest discovery
- `TARIQ__career_radar/tests/test_opportunity_schema.py` — DATA-01: 3 schema validation tests (fail: schema file absent)
- `TARIQ__career_radar/tests/test_config.py` — DATA-02: 2 profile seed tests (fail: radar.config absent)
- `TARIQ__career_radar/tests/test_dedup_engine.py` — DATA-03: 3 SQLite roundtrip/normalization/persistence tests (fail: radar.dedup_engine absent)
- `TARIQ__career_radar/tests/test_structure.py` — DATA-04: 1 folder layout test (fail: radar/*.py files absent)
- `TARIQ__career_radar/tests/test_registration.py` — DATA-04/05: 2 registration tests (fail: _index.json + CAREER_RADAR_LEDGER absent)
- `TARIQ__career_radar/tests/test_privacy.py` — DATA-02/05: 1 fail (privacy rules absent) + 1 skip (profile_cache absent)
- `.gitignore` — added TARIQ__career_radar/data/ exclusions and pycache rules

## Decisions Made

- **try/except + _require_module() pattern**: Plan spec said "do NOT import conditionally" but top-level ImportError blocks pytest collection entirely. Used deferred re-raise pattern to satisfy both: tests are collectible AND fail RED at runtime. This is correct TDD behavior.
- **parents[2] for repo root**: Plan interfaces block specified `parents[3]` but that resolves to `D:\` (drive root) for files at `TARIQ__career_radar/tests/*.py`. Corrected to `parents[2]` which resolves to `D:\NIZAM`.
- **test_profile_not_in_egress skip**: Profile file will not exist until DATA-02 implementation. Using `pytest.skip` is the correct TDD approach — the test exists in the collection and will activate once the file is created.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect repo root path calculation (parents[3] -> parents[2])**
- **Found during:** Task 2 (test_privacy.py first run)
- **Issue:** Plan interfaces block specified `Path(__file__).resolve().parents[3]` which resolves to `D:\` (drive root) for test files at `TARIQ__career_radar/tests/*.py`; PRIVACY_CLASSIFICATION.json path was `D:\NIZAM__system\...` instead of `D:\NIZAM\NIZAM__system\...`
- **Fix:** Changed all 6 test files to use `parents[2]` (2 levels up from tests/ = repo root D:\NIZAM)
- **Files modified:** all 6 test files in TARIQ__career_radar/tests/
- **Verification:** test_privacy.py::test_privacy_rules_defined now produces correct AssertionError (rule absent, not path wrong)
- **Committed in:** 15f2a08 (Task 2 commit)

**2. [Rule 3 - Blocking] Used try/except at module level instead of direct top-level import**
- **Found during:** Task 2 (first pytest --collect-only run)
- **Issue:** Direct `from TARIQ__career_radar.radar.config import ...` at module level caused collection ERROR (not test FAILURE) — pytest stopped collecting those files entirely, so 5 tests were uncollectible
- **Fix:** Wrapped imports in try/except; stored ImportError; re-raised inside each test via `_require_module()` helper
- **Files modified:** test_config.py, test_dedup_engine.py
- **Verification:** All 13 tests collected cleanly; both files show FAILED (not ERROR) in test run
- **Committed in:** 15f2a08 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correct RED-phase TDD behavior. No scope creep.

## Issues Encountered

None — deviations above cover all issues found and how they were resolved.

## User Setup Required

None — no external service configuration required for Wave 0 scaffold.

## Next Phase Readiness

- Wave 0 scaffold complete; all 13 tests collectible and failing RED as designed
- Plans 01-02 through 01-06 can now proceed to turn specific tests GREEN
- Run command: `py -3 -m pytest TARIQ__career_radar/tests/ -v` (< 2 seconds; 12 failed, 1 skipped)
- No blockers; additive-only constraints respected throughout

---
*Phase: 01-foundation-data-model*
*Completed: 2026-06-14*
