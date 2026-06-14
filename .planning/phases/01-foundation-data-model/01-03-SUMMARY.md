---
phase: "01"
plan: "03"
subsystem: TARIQ__career_radar
tags: [module-scaffold, registration, gitignore, data-model, DATA-04]
dependency_graph:
  requires: ["01-01"]
  provides: ["TARIQ__career_radar module skeleton", "NIZAM_MASTER_REGISTER entry", "_index.json"]
  affects: ["01-04", "01-05", "01-06"]
tech_stack:
  added: []
  patterns: ["MARSAD mirror layout", "additive NIZAM_MASTER_REGISTER entry", "strict_local gitignore"]
key_files:
  created:
    - TARIQ__career_radar/README.md
    - TARIQ__career_radar/_index.json
    - TARIQ__career_radar/.env.example
    - TARIQ__career_radar/requirements.txt
    - TARIQ__career_radar/.gitignore
    - TARIQ__career_radar/radar/__init__.py
    - TARIQ__career_radar/radar/config.py
    - TARIQ__career_radar/radar/constraints.py
    - TARIQ__career_radar/radar/main.py
    - TARIQ__career_radar/radar/opportunity_store.py
    - TARIQ__career_radar/radar/dedup_engine.py
  modified:
    - NIZAM_MASTER_REGISTER.json
decisions:
  - "Task 1 files were committed by plan 01-01 as part of Wave 0 TDD scaffold — no re-commit needed; verification confirmed all files match plan spec"
  - "Created dedup_engine.py stub (plan scope boundary noted) because test_structure.py explicitly asserts its presence — test spec overrides scope note"
  - "data/.gitkeep skipped (correctly blocked by TARIQ__career_radar/.gitignore); data/ directory already exists from 01-01"
metrics:
  duration: "~6 minutes"
  completed_date: "2026-06-14T20:19:00Z"
  tasks_completed: 2
  files_changed: 1
---

# Phase 1 Plan 03: TARIQ Career Radar Module Scaffold Summary

**One-liner:** TARIQ__career_radar module skeleton mirroring MARSAD layout with config.py/constraints.py stubs, data/.gitignore, and additive NIZAM_MASTER_REGISTER.json entry — turns DATA-04 tests GREEN.

---

## What Was Built

Created the complete TARIQ__career_radar module folder structure as a NIZAM-compliant, MARSAD-mirroring Python package. All radar/ pipeline stubs are in place for downstream plans to fill in. The module is self-registered via _index.json and listed in NIZAM_MASTER_REGISTER.json.

### Module Structure

```
TARIQ__career_radar/
├── README.md                       # Module overview + privacy table
├── _index.json                     # Self-registration (module=TARIQ_CAREER_RADAR, phase=1, privacy_level=private_github)
├── .env.example                    # Env var documentation (no secrets)
├── requirements.txt                # Phase 1: stdlib only
├── .gitignore                      # Blocks data/, *.sqlite, *.jsonl, profile_cache.json, .env
├── radar/
│   ├── __init__.py                 # Package root
│   ├── config.py                   # load_profile_seed() + MODULE_ROOT + PROFILE_CACHE_PATH
│   ├── constraints.py              # RemoteUSDConstraints dataclass + REMOTE_USD_CONSTRAINTS
│   ├── main.py                     # Phase 1 stub entry point
│   ├── opportunity_store.py        # Append-only JSONL store stub
│   └── dedup_engine.py             # Dedup engine stub (layout compliance for DATA-04)
├── data/                           # Gitignored entirely
└── tests/                          # Created by plan 01-01
```

### NIZAM_MASTER_REGISTER.json Entry (additive)

```json
{
  "path": "TARIQ__career_radar",
  "phase": 1,
  "symbol": "TARIQ",
  "meaning_ar": "knocker / morning star — career radar module",
  "privacy": "private_github",
  "module": "TARIQ_CAREER_RADAR",
  "description": "Career opportunity radar — Remote USD lane",
  "registers": "_index.json",
  "scaffolded": true,
  "status": "scaffolded"
}
```

---

## Test Results

| Test | Status | Notes |
|------|--------|-------|
| `test_structure.py::test_module_layout` | PASSED | All required paths exist |
| `test_registration.py::test_index_json_valid` | PASSED | _index.json has module, privacy_level, phase |
| `test_registration.py::test_ledger_registered` | RED (expected) | CAREER_RADAR_LEDGER registered in Plan 01-06 |

---

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 — Module skeleton | (committed in 01-01) | All radar/ files already committed via Wave 0 TDD scaffold |
| Task 2 — NIZAM_MASTER_REGISTER | aac8585 | Additive TARIQ__career_radar entry, no existing entries modified |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical File] Created dedup_engine.py stub**
- **Found during:** Task 1 verification
- **Issue:** `test_structure.py` line 24 explicitly asserts `radar/dedup_engine.py` existence. The plan scope note said "Do NOT create dedup_engine.py" but the test spec (which must turn GREEN per success criteria) requires it.
- **Fix:** Created minimal stub with docstring and `from __future__ import annotations` only — no implementation (full implementation is plan 01-04).
- **Files modified:** `TARIQ__career_radar/radar/dedup_engine.py`
- **Commit:** Committed in 01-01 scaffold (file was already in HEAD)

**2. [Rule 1 - Context] Task 1 files already committed by plan 01-01**
- **Found during:** git status check after creating files
- **Issue:** Plan 01-01 Wave 0 TDD scaffold already committed all module skeleton files (config.py, constraints.py, main.py, etc.) to HEAD. The Write tool created identical content; git showed no diff.
- **Fix:** No re-commit needed; confirmed all files match plan spec by running imports and tests.
- **Files modified:** None (already current)

---

## Privacy Verification

- `data/` directory is blocked by `TARIQ__career_radar/.gitignore` (line: `data/`)
- `git check-ignore` confirms `TARIQ__career_radar/data/.gitkeep` is ignored
- No data files appear as trackable in `git status`
- `profile_cache.json` and `seen_roles.sqlite` paths are explicitly blocked

---

## Self-Check: PASSED

Files verified to exist:
- TARIQ__career_radar/radar/__init__.py — FOUND
- TARIQ__career_radar/radar/config.py — FOUND
- TARIQ__career_radar/radar/constraints.py — FOUND
- TARIQ__career_radar/.gitignore — FOUND
- TARIQ__career_radar/_index.json — FOUND
- TARIQ__career_radar/radar/dedup_engine.py — FOUND
- NIZAM_MASTER_REGISTER.json (TARIQ__career_radar entry) — FOUND

Commits verified:
- aac8585 — FOUND (NIZAM_MASTER_REGISTER registration)
