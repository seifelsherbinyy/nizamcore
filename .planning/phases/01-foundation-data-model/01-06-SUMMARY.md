---
phase: 01-foundation-data-model
plan: "06"
subsystem: TARIQ Career Radar — Ledger Registration & Privacy Classification
tags:
  - ledger-registration
  - privacy-classification
  - governance
  - data-05
dependency_graph:
  requires:
    - "01-02"
    - "01-03"
    - "01-04"
    - "01-05"
  provides:
    - CAREER_RADAR_LEDGER registered in KNOWN_LEDGERS and NIZAM_TEMPLE.json
    - TARIQ privacy path rules in PRIVACY_CLASSIFICATION.json
    - Empty CAREER_RADAR_LEDGER.jsonl file (gitignored, genesis-ready)
    - DATA-05 requirement fully met
  affects:
    - NIZAM_TEMPLE.json (ledgers section)
    - NIZAM__system/governor/ledger_writer.py (KNOWN_LEDGERS set)
    - NIZAM__system/policies/PRIVACY_CLASSIFICATION.json (rules array)
    - NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl (new file)
tech_stack:
  added: []
  patterns:
    - NIZAM 3-part ledger registration ceremony (TEMPLE.json + ledger_writer.py + PRIVACY_CLASSIFICATION.json)
    - Additive-only governance file edits with per-step JSON/import validation
    - Gitignored append-only JSONL ledger (*.jsonl blocked by NIZAM__system/ledgers/.gitignore)
key_files:
  created:
    - NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl (empty genesis ledger; gitignored)
    - .planning/phases/01-foundation-data-model/01-06-SUMMARY.md
  modified:
    - NIZAM_TEMPLE.json (added CAREER_RADAR_LEDGER to ledgers section)
    - NIZAM__system/governor/ledger_writer.py (added CAREER_RADAR_LEDGER to KNOWN_LEDGERS)
    - NIZAM__system/policies/PRIVACY_CLASSIFICATION.json (added 3 TARIQ path rules)
decisions:
  - "CAREER_RADAR_LEDGER privacy_class defaults to strict_local (ledger_writer.py append default for non-standard ledgers); the PRIVACY_CLASSIFICATION.json rule for the .jsonl path sets it to review_before_commit — these are separate: the JSONL file's sync/commit governance vs the in-row privacy_class field"
  - "Empty file (zero bytes) created for ledger genesis; first real row written by smoke test via append() — ledger_writer handles prev_hash=0*64 automatically"
  - "3 TARIQ privacy rules ordered: profile_cache.json (most specific, strict_local_maximum) first, then data/** (catch-all strict_local), then ledger path (review_before_commit)"
metrics:
  duration: "2 min"
  completed_date: "2026-06-14"
  tasks: 2
  files_changed: 4
requirements_met:
  - DATA-05
---

# Phase 1 Plan 06: Ledger Registration Ceremony Summary

**One-liner:** CAREER_RADAR_LEDGER registered in all 3 NIZAM governance files via additive-only edits, TARIQ privacy path rules added, and Phase 1 test suite turned fully GREEN (13/13 passed).

---

## What Was Done

This was the final DATA-05 plan: completing the 3-part NIZAM ledger registration ceremony to make `CAREER_RADAR_LEDGER` a first-class NIZAM ledger and classify TARIQ module data paths for privacy enforcement.

### Task 1: Three Additive Governance File Edits

All three edits were made with strict additive-only discipline — no existing keys deleted, no lines reordered.

**Step A — NIZAM_TEMPLE.json:**
Added `CAREER_RADAR_LEDGER` to the `ledgers` object after the existing `BODY_LEDGER` entry:
```json
"CAREER_RADAR_LEDGER": {
  "path": "NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl",
  "phase": 1,
  "privacy": "review_before_commit",
  "owner": "Tariq",
  "purpose": "Career radar run events, opportunity counts, delivery status, error tracking"
}
```
Result: 9 ledgers total (was 8). JSON validates cleanly.

**Step B — NIZAM__system/governor/ledger_writer.py:**
Added one line inside the `KNOWN_LEDGERS` set literal:
```python
"CAREER_RADAR_LEDGER",  # TARIQ Career Radar run log
```
Result: 11 ledgers in KNOWN_LEDGERS (was 10). Python import validates cleanly.

**Step C — NIZAM__system/policies/PRIVACY_CLASSIFICATION.json:**
Added 3 entries to the `rules` array (after `log.md` entry, before closing bracket):
```json
{ "path_glob": "TARIQ__career_radar/data/profile_cache.json", "classification": "strict_local_maximum" },
{ "path_glob": "TARIQ__career_radar/data/**",                 "classification": "strict_local" },
{ "path_glob": "NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl", "classification": "review_before_commit" }
```
Result: 40 rules total (was 37). JSON validates cleanly.

**Commit:** `338ae3d` — `chore(01-06): ledger registration ceremony — additive edits to 3 NIZAM governance files`

### Task 2: Empty Ledger File + Test Suite

Created `NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl` as empty file. Confirmed gitignored by `NIZAM__system/ledgers/.gitignore` line 4 (`*.jsonl` pattern). File is non-public as required.

**Test results:**

| Suite | Result |
|-------|--------|
| `TARIQ__career_radar/tests/test_registration.py::test_ledger_registered` | PASSED |
| `TARIQ__career_radar/tests/test_privacy.py::test_privacy_rules_defined` | PASSED |
| `TARIQ__career_radar/tests/test_privacy.py::test_profile_not_in_egress` | PASSED |
| Full `TARIQ__career_radar/tests/` (13 tests) | 13 passed, 0 failed |
| `NIZAM__system/governor/tests/` (33 tests) | 33 passed, 0 failed |

**Ledger write smoke test:** `append('CAREER_RADAR_LEDGER', {...}, actor='Tariq', action='phase_test')` succeeded — returned row_id UUID, no ValueError.

**Privacy classification check:**
- `classify('TARIQ__career_radar/data/profile_cache.json')` → `strict_local_maximum` (correct)
- `classify('TARIQ__career_radar/data/seen_roles.sqlite')` → `strict_local` (correct)
- `classify('NIZAM__system/ledgers/CAREER_RADAR_LEDGER.jsonl')` → `review_before_commit` (correct)

---

## Rollback Notes

If any of the 3 governance edits need to be reverted:

**NIZAM_TEMPLE.json:** Remove the `CAREER_RADAR_LEDGER` key-value block (lines added after `BODY_LEDGER`). Also remove the trailing comma from `BODY_LEDGER` closing brace. Original `BODY_LEDGER` entry ended at `}` before the `}` closing `ledgers`.

**ledger_writer.py:** Remove the line `"CAREER_RADAR_LEDGER",  # TARIQ Career Radar run log` from KNOWN_LEDGERS set. Revert leaves 10 items in the set.

**PRIVACY_CLASSIFICATION.json:** Remove the 3 TARIQ rules (profile_cache.json, data/**, and CAREER_RADAR_LEDGER.jsonl). Also remove the trailing comma added to the `log.md` entry. Revert leaves 37 rules.

**CAREER_RADAR_LEDGER.jsonl:** Simply delete the file (it is gitignored and won't appear in git history). Any rows appended to it during testing are lost on delete, but those were smoke-test rows only.

**Git restore (all 3 files):**
```bash
git show HEAD~1:NIZAM_TEMPLE.json > NIZAM_TEMPLE.json
git show HEAD~1:NIZAM__system/governor/ledger_writer.py > NIZAM__system/governor/ledger_writer.py
git show HEAD~1:NIZAM__system/policies/PRIVACY_CLASSIFICATION.json > NIZAM__system/policies/PRIVACY_CLASSIFICATION.json
```
(HEAD~1 because Task 1 commit is `338ae3d` — one commit back from current HEAD when SUMMARY is committed)

---

## Deviations from Plan

None — plan executed exactly as written. All 3 edits were additive-only. All validations passed on first attempt. No deviation rules triggered.

---

## Pre-Commit Hook Behavior

The NIZAM governor pre-commit hook was active during `git commit` for Task 1's commit (`338ae3d`). The hook did NOT block the commit — which is correct behavior because all 3 files edited (`NIZAM_TEMPLE.json`, `ledger_writer.py`, `PRIVACY_CLASSIFICATION.json`) are classified as `private_github` in PRIVACY_CLASSIFICATION.json, meaning they are allowed to be committed to the private GitHub repo. The hook only blocks `strict_local` and `strict_local_maximum` files. Governance files are safe to commit.

---

## Phase 1 Final Status

All 13 Phase 1 tests GREEN. DATA-01 through DATA-05 requirements met. Phase 1 (Foundation & Data Model) is complete.

| Requirement | Status |
|-------------|--------|
| DATA-01: Opportunity record schema | GREEN |
| DATA-02: Profile seed (strict_local_maximum) | GREEN |
| DATA-03: Dedup store (SQLite) | GREEN |
| DATA-04: Module folder layout (MARSAD pattern) | GREEN |
| DATA-05: Ledger registration + privacy rules | GREEN |
