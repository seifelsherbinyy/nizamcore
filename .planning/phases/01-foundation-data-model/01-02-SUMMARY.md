---
phase: 01-foundation-data-model
plan: "02"
subsystem: TARIQ Career Radar — Schema & Registry
tags: [schema, json-schema, draft-07, data-model, registry, DATA-01]
dependency_graph:
  requires: ["01-01"]
  provides: ["NIZAM__system/schemas/career_opportunity_record.schema.json", "SCHEMA_INDEX career_opportunity_record entry"]
  affects: ["02-sourcing", "03-rss-sourcing", "04-dedup", "05-scoring"]
tech_stack:
  added: ["jsonschema 4.26.0 (dev dependency, already installed)"]
  patterns: ["JSON Schema draft-07", "additive SCHEMA_INDEX registration"]
key_files:
  created:
    - NIZAM__system/schemas/career_opportunity_record.schema.json
  modified:
    - NIZAM__system/SCHEMA_INDEX.json
key_decisions:
  - "20 required fields in this exact order: opportunity_id, title, company, location, remote_status, source, source_type, source_url, access_date, fit_score, growth_score, confidence, tags, salary_usd_low, salary_usd_high, salary_evidence_type, salary_confidence, observed_at, lane, data_quality"
  - "salary_usd_low/high typed as [number, null] with minimum 0 to accept None in fixture"
  - "Appended to SCHEMA_INDEX.json schemas array additively; 22 entries total, 21 existing untouched"
metrics:
  duration_minutes: 5
  completed_date: "2026-06-14"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 1
requirements: [DATA-01]
---

# Phase 1 Plan 02: Career Opportunity Record Schema Summary

**One-liner:** JSON Schema draft-07 for 20-field career opportunity record with enum constraints on all classification fields, registered in NIZAM SCHEMA_INDEX.

---

## What Was Built

Created `NIZAM__system/schemas/career_opportunity_record.schema.json` — the canonical single source of truth for the TARIQ Career Radar opportunity record format. All 20 required fields are declared with appropriate types, enum constraints, and format strings. Nine optional enrichment fields are also declared.

Registered the schema in `NIZAM__system/SCHEMA_INDEX.json` as an additive append — no existing entries were modified.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write career_opportunity_record.schema.json | 4b6a7e4 | NIZAM__system/schemas/career_opportunity_record.schema.json |
| 2 | Register in SCHEMA_INDEX.json + run DATA-01 tests | 96b12b2 | NIZAM__system/SCHEMA_INDEX.json |

---

## Test Results

**DATA-01 tests: 3/3 PASSED (GREEN)**

```
TARIQ__career_radar/tests/test_opportunity_schema.py::test_schema_validate         PASSED
TARIQ__career_radar/tests/test_opportunity_schema.py::test_schema_required_fields  PASSED
TARIQ__career_radar/tests/test_opportunity_schema.py::test_schema_rejects_missing_title PASSED
3 passed in 1.26s
```

---

## Schema Summary

**File:** `NIZAM__system/schemas/career_opportunity_record.schema.json`

**$schema:** `http://json-schema.org/draft-07/schema#`
**$id:** `https://pop.local/schemas/career_opportunity_record.schema.json`

**Required fields (20):**
- Identity: `opportunity_id` (uuid), `title`, `company`, `location`
- Classification: `remote_status` (enum: 4 values), `lane` (enum: Remote USD/GCC/Europe)
- Sourcing: `source`, `source_type` (enum: 6 values), `source_url` (uri), `access_date` (date-time)
- Scoring: `fit_score` (int 0-100), `growth_score` (int 0-100), `confidence` (enum: HIGH/MEDIUM/LOW)
- Tags: `tags` (array of 8-value enum)
- Salary: `salary_usd_low` (number|null >= 0), `salary_usd_high` (number|null >= 0), `salary_evidence_type` (enum: 6 values), `salary_confidence` (enum: HIGH/MEDIUM/LOW)
- Metadata: `observed_at` (date-time), `data_quality` (enum: confirmed/estimated/partial)

**Optional fields (9):** `role_category`, `salary_usd_annual`, `company_strength_signal`, `visa_feasibility`, `profile_gap`, `next_action`, `run_id`, `is_duplicate_of`, `notes`

---

## SCHEMA_INDEX Entry Added

```json
{
  "name": "career_opportunity_record",
  "phase": 1,
  "path": "schemas/career_opportunity_record.schema.json",
  "describes": "Individual career opportunity record for TARIQ Career Radar: scoring, matching, salary provenance, evidence fields",
  "live": false,
  "scaffolded": true
}
```

Appended at end of existing `schemas` array. All 21 pre-existing entries preserved unchanged.

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Decisions Made

1. **Type for salary_usd_low/high:** `["number", "null"]` with `minimum: 0` — matches fixture which passes `None` for undisclosed salaries.
2. **company_strength_signal null in enum:** JSON Schema draft-07 supports `null` as a literal in enum arrays; used per plan spec.
3. **SCHEMA_INDEX structure:** File uses `"schemas"` key (not a bare array); entry appended inside that array additively.
4. **jsonschema already installed:** 4.26.0 was present; no install action needed. Noted as dev dependency.

---

## Self-Check: PASSED

- FOUND: NIZAM__system/schemas/career_opportunity_record.schema.json
- FOUND: .planning/phases/01-foundation-data-model/01-02-SUMMARY.md
- FOUND commit: 4b6a7e4 (Task 1 — schema file)
- FOUND commit: 96b12b2 (Task 2 — SCHEMA_INDEX registration)
