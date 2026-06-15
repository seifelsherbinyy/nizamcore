---
phase: 03-tier-2-rss-manual-sourcing
plan: "04"
subsystem: TARIQ__career_radar
tags: [wiring, configuration, integration, tier-2-sources, role-filter]
dependency_graph:
  requires: [03-02-tier2-rss-connectors, 03-03-manual-import-filter]
  provides: [03-04-wave3-wiring]
  affects: [phase-4-dedup, run_fetch-orchestrator]
tech_stack:
  patterns:
    - YAML-based config loading for Tier 2 sources
    - _load_tier2_config() helper function
    - _build_tier2_sources() builder pattern
    - Anchored minimal edit to run_fetch()
    - Filter integration post-normalization
key_files:
  modified:
    - TARIQ__career_radar/radar/stages/fetch.py
    - TARIQ__career_radar/radar/config_sources.yaml
    - TARIQ__career_radar/.gitignore
decisions:
  - "_load_tier2_config() mirrors _load_ats_config() pattern for consistency"
  - "Filter applied after normalization, before return dict — all opportunities normalized first"
  - "Filter return dict additive to run_fetch() return (out_of_scope_opportunities + filter_summary keys)"
  - "Manual import path resolved relative to MODULE_ROOT for portability"
metrics:
  duration: "~5 min"
  completed_date: "2026-06-15"
  tasks_completed: 3
  files_changed: 3
  requirements_covered: [SRC-02, SRC-03, SRC-06]
---

# Phase 03 Plan 04: Wave 3 Wiring & Configuration Summary

**One-liner:** Wire Tier 2 RSS sources, ManualImportSource, and role-keyword filter into run_fetch() orchestrator with minimal, anchored edits. Add config sections and gitignore operator data files.

---

## What Was Built

Three task completion wires the Tier 2 pipeline into the existing run_fetch() orchestrator:

**Task 1 — config_sources.yaml extended** with additive sections:
- `tier_2_rss` section: remotive, weworkremotely, remoteok with feed/API URLs and enabled flags
- `manual_import` section: path to data/manual_imports.jsonl + documentation
- `role_filter` section: enabled flag + tuning notes
- tier_1_ats section unchanged (backward compatible)

**Task 2 — fetch.py extended** (100 lines added):
- New imports: RemotiveSource, WeWorkRemotelySource, RemoteOKSource, ManualImportSource, run_filter
- New helper `_load_tier2_config()`: mirrors _load_ats_config() pattern, returns tier_2_rss/manual_import/role_filter dicts
- New helper `_build_tier2_sources()`: instantiates enabled sources, resolves paths, mirrors _build_sources_from_yaml() pattern
- Extended `_build_sources_from_yaml()`: calls _load_tier2_config() + _build_tier2_sources(), appends results to sources list
- Filter integration in `run_fetch()`: applied after normalization, handles empty opportunities gracefully, logs out-of-scope count
- Updated return dict: adds `out_of_scope_opportunities` and `filter_summary` keys (additive, not breaking)
- Optional: fixed `datetime.utcnow()` to `datetime.now(timezone.utc)` (deprecation fix)

**Task 3 — .gitignore and data directory**:
- Created TARIQ__career_radar/.gitignore with entries for manual_imports.jsonl, profile_cache.json, seen_roles.sqlite, __pycache__, *.pyc
- Created TARIQ__career_radar/data/.gitkeep to track directory in git

---

## Test Results

```
All 30 tests pass, 1 skipped (expected), 0 failures:
- Phase-1 tests (13): GREEN
- Phase-2 tests (11): GREEN
- Phase-3 tests (9): GREEN (all Wave 0 RED tests now GREEN)

Smoke test: run_fetch({}, 'smoke-test-run-01')
- Keys present: opportunities, blocked_sources, out_of_scope_opportunities, filter_summary, fetch_summary
- Result: partial_success (Tier 2 sources hit 404s from real APIs, but no exceptions raised)
- Integration: filter_summary correctly populated, graceful error handling working
```

---

## Decisions Made

1. **_load_tier2_config() mirrors _load_ats_config()** — Consistent pattern, easy to extend
2. **_build_tier2_sources() builds both RSS and manual** — Single helper, parallel with _build_sources_from_yaml()
3. **Filter applied post-normalization** — All opportunities normalized first, then filtered; clearer data flow
4. **Filter return additive to run_fetch()** — out_of_scope_opportunities and filter_summary are new keys, not modifications to existing ones; backward compatible
5. **Manual import path resolved relative to MODULE_ROOT** — Portable across deployment environments
6. **Graceful empty-opportunities handling** — If no opportunities fetched, filter_result initialized with safe defaults, no crash

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Commits

- `0fc8d73`: feat(03-04): add Tier 2 RSS, manual import, and role-filter sections to config
- `d124e3a`: feat(03-04): extend fetch.py to load and wire Tier 2 sources + run_filter
- `200e815`: feat(03-04): add .gitignore and .gitkeep for operator data files

---

## Self-Check

Verifying artifacts exist:
- TARIQ__career_radar/radar/config_sources.yaml — FOUND (tier_2_rss, manual_import, role_filter sections present)
- TARIQ__career_radar/radar/stages/fetch.py — FOUND (imports, _load_tier2_config, _build_tier2_sources, filter integration present)
- TARIQ__career_radar/.gitignore — FOUND (manual_imports.jsonl, profile_cache.json, seen_roles.sqlite entries present)
- TARIQ__career_radar/data/.gitkeep — FOUND

Commits: 3 present in git log

## Self-Check: PASSED
