---
phase: 14-knowledge-index-schema-storage
plan: 04
subsystem: HIKMAH__knowledge_index
tags:
  - knowledge-index
  - versioning
  - schema-evolution
  - makhzan-snapshot
dependency_graph:
  requires:
    - 14-01 (Knowledge Index Schema)
    - 14-02 (HIKMAH Registration)
    - 14-03 (Knowledge Index Initialization)
  provides:
    - increment_schema_version() for atomic version bumps
    - snapshot_indices_to_makhzan() for MAKHZAN snapshots
    - validate_schema_versions() for version consistency checks
    - validate_version_format() for semantic versioning validation
  affects:
    - Phase 15 (Data Refresh & Synchronization)
    - Future schema changes (v1.1, v2.0)
    - Any code that modifies persona indices
tech_stack:
  added:
    - versioning.py (schema evolution and MAKHZAN snapshots)
    - test_versioning.py (14 comprehensive tests)
  modified:
    - schema.py (expanded version pattern to support MAJOR.MINOR)
    - CONTINUITY_PROTOCOL.md (new section for HIKMAH versioning)
  patterns:
    - TDD (14 failing tests written first, then implementation)
    - MAKHZAN snapshot pattern (snapshot before change, MANIFEST.json with metadata)
    - Atomic updates (all 11 personas updated together or none)
    - Semantic versioning (1.0, 1.1, 2.0, etc.)
key_files:
  created:
    - HIKMAH__knowledge_index/index/versioning.py (304 lines, 4 functions)
    - HIKMAH__knowledge_index/tests/test_versioning.py (360 lines, 14 tests)
  modified:
    - HIKMAH__knowledge_index/index/schema.py (version pattern updated)
    - NIZAM__system/docs/CONTINUITY_PROTOCOL.md (84 lines added)
decisions:
  - TDD approach: 14 failing tests written first, then implementation (all passing)
  - MAKHZAN snapshot directory structure: MAKHZAN__archive/{ISO_TIMESTAMP}/HIKMAH__knowledge_index/indices/
  - Manifest format: JSON with trigger, from_version, to_version, change, snapshot_at, indices_backed_up, operator, recovery_note
  - Atomic updates: validate_schema_versions() before snapshot, update all 11 in loop, validate after
  - Version format: Semantic versioning MAJOR.MINOR (e.g., 1.0, 1.1, 2.0, 10.5) via regex ^[1-9][0-9]*\.[0-9]+$
  - Backward compatibility: v1.x versions allow optional new fields; v2.x+ breaks compatibility
metrics:
  completed_date: 2026-06-20
  duration_minutes: ~60
  tasks_completed: 2
  tests_total: 14
  tests_passed: 14
  lines_of_code:
    - versioning.py: 304 lines
    - test_versioning.py: 360 lines
    - CONTINUITY_PROTOCOL.md section: 84 lines
  files_created: 2
  files_modified: 2
  commits: 2
---

# Phase 14 Plan 04: Schema Versioning & MAKHZAN Snapshots Summary

**One-liner:** Implement `increment_schema_version()` with MAKHZAN snapshot pattern to enable backward-compatible schema evolution (v1.x) and breaking changes (v2.0+) while preserving prior indices for rollback.

## Objective

Implement schema versioning support that allows the knowledge index schema to evolve over time (adding optional fields in v1.1, removing fields in v2.0) without breaking existing indices. MAKHZAN snapshots preserve prior states before version bumps, enabling rollback if needed. This foundation enables Phase 15+ to introduce new schema features without disrupting existing personas.

## Work Completed

### Task 1: Implement Versioning Functions in versioning.py

**Status:** COMPLETE

Created `HIKMAH__knowledge_index/index/versioning.py` (304 lines) with 4 core functions:

1. **`validate_version_format(version: str) -> bool`**
   - Validates semantic versioning format: MAJOR.MINOR (e.g., 1.0, 1.1, 2.0, 10.5)
   - Regex pattern: `^[1-9][0-9]*\.[0-9]+$` (no leading zeros, minor can be 0)
   - Rejects: v1.0, 0.5, 1, 1.0.0
   - Used by increment_schema_version() to validate input versions

2. **`validate_schema_versions(indices_dir: Path) -> Tuple[bool, Optional[str]]`**
   - Reads all {PERSONA}_index.json files from indices directory
   - Extracts version field from each index
   - Returns (True, None) if all 11 personas at same version
   - Returns (False, error_msg) if version mismatch detected
   - Raises FileNotFoundError if indices_dir doesn't exist or is empty

3. **`snapshot_indices_to_makhzan(indices_dir, from_version, to_version, change_description) -> Path`**
   - Creates MAKHZAN__archive/{ISO_TIMESTAMP}/ directory structure
   - Copies all 11 persona indices to snapshot location, preserving content exactly
   - Creates MANIFEST.json with metadata:
     - trigger: "schema_version_increment"
     - from_version, to_version, change description
     - snapshot_at timestamp (ISO 8601 UTC)
     - indices_backed_up count (should be 11)
     - operator: "auto_system"
     - recovery_note for rollback instructions
   - Returns Path to snapshot indices directory

4. **`increment_schema_version(indices_dir, old_version, new_version, change_description) -> Dict`**
   - Atomic version bump for all 11 persona indices
   - Procedure: validate old_version → snapshot → update all → validate new
   - For each persona index:
     - Update version field to new_version
     - Update last_updated to current UTC timestamp
     - Validate using validate_index_schema()
     - Write updated file
   - Returns dict: {personas_updated: 11, snapshot_location: Path, manifest_location: Path}
   - Raises ValueError if old_version doesn't match all indices
   - Raises IOError if any file write fails

**Test Coverage:** 14 comprehensive tests covering:
- Schema version matching/mismatching (2 tests)
- MAKHZAN snapshot creation and structure (3 tests)
- Version increment atomicity and all-11-update (5 tests)
- Error handling (2 tests)
- Version format validation (2 tests)

All 14 tests PASS.

### Task 2: Document Versioning Pattern in CONTINUITY_PROTOCOL.md

**Status:** COMPLETE

Updated `NIZAM__system/docs/CONTINUITY_PROTOCOL.md` with new section: "Knowledge Index Schema Evolution (HIKMAH__knowledge_index)" (84 lines).

Content:
- **Versioning Strategy:** v1.x (backward-compatible, new optional fields), v2.x+ (breaking changes)
- **Snapshot Pattern:** Detailed procedure with MANIFEST.json example structure
- **Atomic Updates:** Step-by-step validation → snapshot → update → verify flow
- **Rollback Procedure:** How to restore indices from MAKHZAN snapshot if upgrade fails
- **Future Changes:** Example v1.1 (engagement_patterns array) and v2.0 (remove context_snapshots field)
- **Integration Points:** Links to versioning.py functions and validation endpoints

Documentation is cross-referenced with code and includes example MANIFEST.json structure.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Expanded version format in schema validation**
- **Found during:** Task 1 tests (test_allows_major_version_change_to_2_0)
- **Issue:** Schema validation only accepted v1.x versions; plan requires v2.x support for breaking changes
- **Fix:** Updated VALID_VERSION_PATTERN in schema.py from `^1\.[0-9]+$` to `^[1-9][0-9]*\.[0-9]+$`
- **Files modified:** HIKMAH__knowledge_index/index/schema.py, HIKMAH__knowledge_index/index/versioning.py
- **Impact:** Now supports semantic versioning for any major/minor version (1.0, 1.1, 2.0, 10.5, etc.)

## Verification

All success criteria met:

✓ versioning.py imports successfully: `from HIKMAH__knowledge_index.index.versioning import increment_schema_version`
✓ validate_schema_versions() detects version mismatches correctly (test: mixed versions → (False, error_msg))
✓ snapshot_indices_to_makhzan() creates MAKHZAN__archive/ with correct directory structure
✓ increment_schema_version() atomically updates all 11 persona indices (test: all 11 updated to new version)
✓ CONTINUITY_PROTOCOL.md documents versioning pattern with examples
✓ All functions include proper error handling and validation
✓ Schema evolution properly sequenced: snapshot → validate old → update all → validate new

## Testing Results

| Test Class | Test Count | Passed | Failed |
|-----------|-----------|--------|--------|
| TestValidateSchemaVersions | 2 | 2 | 0 |
| TestSnapshotIndicesToMakhzan | 3 | 3 | 0 |
| TestIncrementSchemaVersion | 7 | 7 | 0 |
| TestValidateVersionFormat | 2 | 2 | 0 |
| **TOTAL** | **14** | **14** | **0** |

## Index-03 Requirement Satisfaction

**Requirement:** INDEX-03 — "Versioning + schema evolution support for future personas"

**Satisfaction:**
- ✓ Schema version field supports semantic versioning (1.0, 1.1, 1.2, 2.0, etc.)
- ✓ increment_schema_version() atomically updates all 11 persona indices to new version
- ✓ Before version increment, MAKHZAN snapshot is created preserving old indices
- ✓ Snapshot includes MANIFEST.json with change description, old version, new version, timestamp
- ✓ Snapshot path follows pattern: MAKHZAN__archive/{ISO_TIMESTAMP}/HIKMAH__knowledge_index/indices/
- ✓ Schema evolution is backward-compatible for 1.x versions (v1.1 adds optional fields, not removes)
- ✓ Version mismatch detection catches indices at different schema versions and raises error
- ✓ MAKHZAN snapshot can be used to rollback indices to prior version if needed

## Impact on Downstream Work

- **Phase 15 (Data Refresh & Synchronization):** Can now safely refresh indices knowing version consistency is maintained
- **Phase 16+ (Message Generation, Delivery, etc.):** Foundation for future schema additions (e.g., engagement_patterns in v1.1)
- **Rollback Safety:** Any future failures during schema evolution can be recovered via MAKHZAN snapshots

## Commits

1. `feat(14-04): implement schema versioning with MAKHZAN snapshot support`
   - Files: versioning.py (304 lines), test_versioning.py (360 lines), schema.py (updated)
   - 14 tests all passing

2. `docs(14-04): document HIKMAH knowledge index versioning pattern in CONTINUITY_PROTOCOL`
   - File: CONTINUITY_PROTOCOL.md (84 lines added)
   - Covers strategy, snapshot pattern, atomic updates, rollback, future changes, integration points
