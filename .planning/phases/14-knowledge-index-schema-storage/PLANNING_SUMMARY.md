# Phase 14: Knowledge Index Schema & Storage — Planning Summary

**Date:** 2026-06-20  
**Phase:** 14-knowledge-index-schema-storage  
**Status:** Planning Complete — Ready for Execution  
**Total Plans:** 5 plans across 4 waves

---

## Overview

Phase 14 establishes the foundational data model and infrastructure for persona-driven knowledge indexing. This phase delivers:

1. **INDEX-01**: JSON schema with topics, completions, activity_history, stalled_work, context_snapshots
2. **INDEX-02**: Per-persona local storage in strict_local directory with privacy enforcement
3. **INDEX-03**: Versioning support with MAKHZAN snapshot pattern for schema evolution
4. **INDEX-04**: Test run validates all 11 persona indices are valid and readable

**Core deliverable:** HIKMAH__knowledge_index module with per-persona knowledge indices that Phase 15-20 will build upon.

---

## Wave Structure

### Wave 1: Schema Definition & Module Setup (Parallel, Independent)

**Plan 01: Schema Definition & Validation (14-01)**
- Files: `HIKMAH__knowledge_index/index/schema.py`, `__init__.py`
- Deliverable: Complete TypedDict definitions for all index fields + validation function
- Requirement: INDEX-01
- Time: ~45 min

**Plan 02: Module Registration & Privacy Enforcement (14-02)**
- Files: README.md, _index.json, NIZAM_TEMPLE.json, PRIVACY_CLASSIFICATION.json, .gitignore
- Deliverable: Module registered in NIZAM governance; privacy rules locked in
- Requirement: INDEX-02
- Time: ~40 min

**Wave 1 Total:** 2 parallel plans, ~85 min

---

### Wave 2: Implementation (Depends on Wave 1)

**Plan 03: Index Initialization Logic (14-03)**
- Files: `main.py`, `writer.py`, `data/init_manifest.json`
- Deliverable: initialize_persona_index() + initialize_all_personas() functions for all 11 personas
- Requirements: INDEX-02, INDEX-04
- Depends on: Plan 01 (schema validation)
- Time: ~50 min

**Wave 2 Total:** 1 plan, ~50 min

---

### Wave 3: Versioning & Integration (Depends on Wave 1-2)

**Plan 04: Schema Versioning & Snapshots (14-04)**
- Files: `versioning.py`, CONTINUITY_PROTOCOL.md
- Deliverable: increment_schema_version() with MAKHZAN snapshots; schema evolution pattern documented
- Requirement: INDEX-03
- Depends on: Plans 01, 03
- Time: ~45 min

**Wave 3 Total:** 1 plan, ~45 min

---

### Wave 4: Testing & Validation (Depends on Waves 1-3)

**Plan 05: Comprehensive Test Suite (14-05)**
- Files: `tests/test_schema_validation.py`, `test_index_initialization.py`, `test_versioning.py`, `conftest.py`
- Deliverable: Full pytest suite with 40+ test cases, >80% coverage
- Requirements: INDEX-01, INDEX-02, INDEX-03, INDEX-04
- Depends on: Plans 01, 03, 04
- Time: ~60 min

**Wave 4 Total:** 1 plan, ~60 min

---

## Dependency Graph

```
Wave 1 (Parallel):
  Plan 01 ─┐
           ├─→ Wave 2
  Plan 02 ─┤
           └─→ Plan 03 ─┐
                        ├─→ Wave 3
                Plan 04 ─┤
                         └─→ Plan 05 (Wave 4)
```

**Total Execution Time:** ~240 min (~4 hours)  
**Critical Path:** 01/02 → 03 → 04 → 05

---

## Requirement Coverage

| Req ID | Description | Plan(s) | Status |
|--------|-------------|---------|--------|
| INDEX-01 | Schema with topics, completions, history, stalled_work, context_snapshots | 01, 05 | Planned |
| INDEX-02 | Per-persona index in strict_local directory, never egressed | 02, 03, 05 | Planned |
| INDEX-03 | Versioning + MAKHZAN snapshot pattern | 04, 05 | Planned |
| INDEX-04 | Test run creates valid index files for all 11 personas | 03, 05 | Planned |

**Coverage:** 4/4 requirements (100%)

---

## Key Design Decisions

### Schema Structure (Plan 01)
- **TypedDicts for type safety:** Full type hints (TopicDict, CompletionDict, PersonaIndexDict, etc.)
- **Context tags whitelist:** Enforced at write-time to prevent PII leakage
  - Allowed: technical, health, financial, strategic, personal
  - Denied: raw names (Seif), health conditions, financial amounts, family identifiers
- **Version field:** Semantic versioning (1.0, 1.1, 1.2) with MAKHZAN snapshot on breaking changes

### Storage (Plan 02)
- **Module name:** HIKMAH__knowledge_index (per-persona indices under Khaldun's synthesist remit)
- **Indices location:** HIKMAH__knowledge_index/indices/{PERSONA}_index.json (strict_local, never committed)
- **Ledger:** PERSONA_KNOWLEDGE_INDEX.jsonl (append-only, hash-chained audit trail)
- **Privacy enforcement:** SYNC_POLICY + HIMAYAH gate (proven pattern in BADAN, MAL, TARIQ)
- **.gitignore:** Prevents indices/ and ledger from accidental commits

### Initialization (Plan 03)
- **Per-persona JSON files:** 11 separate files enable independent versioning if needed later
- **Empty scaffold:** Topics, completions, stalled_work arrays initialized empty
- **Initial activity_history:** One entry (index_initialized event)
- **Initial context_snapshots:** One entry with zero metrics (baseline state)
- **Validation on creation:** All indices must pass validate_index_schema() before write

### Versioning (Plan 04)
- **MAKHZAN snapshot pattern:** Before version bump, snapshot all indices + create MANIFEST.json
- **Atomic updates:** All 11 indices updated together; no partial updates
- **Backward-compatible 1.x:** v1.1 can add optional fields without breaking v1.0 readers
- **Breaking v2.0:** Requires migration guide + manual operator intervention (not auto-executed)
- **Rollback procedure:** Restore from MAKHZAN snapshot if version bump causes issues

### Testing (Plan 05)
- **Test framework:** pytest (NIZAM standard)
- **Coverage target:** >80% for schema.py, main.py, versioning.py, writer.py
- **Test count:** 40+ test cases across 3 test modules
- **Shared fixtures:** conftest.py provides temp_indices_dir, valid_personas, sample_index_dict, context_tags_whitelist
- **Privacy validation:** Explicit tests for context_tags whitelist and PII rejection

---

## Technical Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.11+ | NIZAM stdlib-first pattern |
| Serialization | json (stdlib) | NIZAM standard; human-readable |
| File I/O | pathlib (stdlib) | Modern, locale-independent |
| IDs | uuid (stdlib) | Per-topic unique identifiers |
| Hashing | hashlib (stdlib) | Ledger hash-chaining (integrity) |
| Timestamps | datetime (stdlib) | ISO 8601 UTC format (NIZAM standard) |
| Type hints | typing (stdlib) | Full type safety for schema |
| Testing | pytest | NIZAM standard test framework |
| **New dependencies** | **NONE** | All stdlib |

---

## Privacy & Security

### Strict Local Enforcement
- **Classification:** strict_local per SYNC_POLICY
- **Never egressed to:** GitHub, Google Drive, Telegram, or any external service
- **Physical storage:** Laptop/encrypted volume only (assumed OS-level encryption)
- **HIMAYAH gate:** Blocks any sync attempts to external surfaces
- **.gitignore:** Prevents commits to version control

### Context Tags Whitelist
- **Allowed:** technical, health, financial, strategic, personal
- **Denied:** Any raw personal data (names, health conditions, amounts, identifiers)
- **Validation:** Enforced at write-time in schema validation
- **Audit:** Phase 20 validates all created indices contain no raw PII

### No Downstream Egress
- Index data stays local (never exported to Telegram or Drive)
- Phase 16 (Message Generation) reads index but generates fresh messages (not dumping raw data)
- Phase 17 (Delivery) sends only persona-tone messages, not raw index content

---

## Integration Points

### Upstream Dependencies
- **Phase 13 completion:** NIZAM system (personas, ledgers, governance) fully functional
- **NIZAM modules used:** MAKHZAN (snapshots), HIMAYAH (privacy gates), SYNC_POLICY, NIZAM_TEMPLE

### Downstream Consumers
- **Phase 15 (Data Refresh):** Reads index schema; merges Google Drive activity into indices
- **Phase 16 (Message Generation):** Reads index per persona; pulls topics + accomplishments; generates fresh messages
- **Phase 17 (Delivery & Response Tracking):** Reads message_id tracking; records response timestamps
- **Phase 18 (Adaptation):** Reads response rates; logs format changes to ledger
- **Phase 20 (Privacy Validation):** Audits index for PII; validates context_tags whitelist; sign-off gate

---

## Known Gaps (Deferred to Later Phases)

| Gap | Why Deferred | Phase |
|----|---|---|
| Google Drive conversation log format | Not researched yet; Phase 15 will investigate | Phase 15 |
| Response tracking storage model | Depends on Telegram relay integration | Phase 17 |
| Cross-persona synthesis | v1.1 uses separate indices; merging deferred to v1.2 | v1.2 |
| Activity history cleanup policy | Implemented in Phase 15 refresh task | Phase 15 |
| ML-based tone optimization | Manual persona tuning sufficient for v1.1 | v1.2+ |
| Multi-channel delivery | Telegram proven; add email/Slack after v1 validation | v1.2+ |

---

## Success Criteria (Phase Gate)

Phase 14 is complete when:

✓ All 5 plans executed successfully  
✓ HIKMAH__knowledge_index module exists with proper structure  
✓ Schema.py exports validate_index_schema() + all TypedDicts  
✓ All 11 persona indices created in HIKMAH__knowledge_index/indices/  
✓ All indices pass validate_index_schema() with (True, None)  
✓ NIZAM_TEMPLE.json includes module + ledger registrations  
✓ PRIVACY_CLASSIFICATION.json enforces strict_local on indices + ledger  
✓ .gitignore prevents indices and ledger from accidental commits  
✓ versioning.py implements increment_schema_version() + MAKHZAN snapshots  
✓ Full pytest suite runs with >80% coverage, all tests passing  
✓ Context_tags whitelist prevents PII leakage (validated by tests)  
✓ CONTINUITY_PROTOCOL.md documents versioning pattern  

**Acceptance gate:** All 5 plans complete + test suite green + no PII detected in any created index

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Schema version mismatch across personas | validate_schema_versions() enforces uniform version; atomic updates only | Plan 04 |
| PII accidentally leaked in context_tags | Whitelist enforced at write-time; tests reject bad tags; Phase 20 audits | Plans 01, 05 |
| Activity history explosion (1000s of rows) | Cleanup task deferred to Phase 15; retention policy in README | Plan 02 |
| Indices accidentally committed to GitHub | .gitignore patterns + PRIVACY_CLASSIFICATION rules | Plan 02 |
| Indices synced to Google Drive | HIMAYAH gate blocks sync; strict_local classification | Plan 02 |
| Schema backward-compatibility break | 1.x changes backward-compatible; v2.0 requires migration guide | Plan 04 |
| MAKHZAN snapshot missing before version bump | increment_schema_version() enforces snapshot-first pattern | Plan 04 |

---

## Metrics & Estimates

| Metric | Value |
|--------|-------|
| Total plans | 5 |
| Waves | 4 |
| Requirements covered | 4/4 (100%) |
| Test cases | 40+ |
| Target coverage | >80% |
| Personas initialized | 11 |
| Lines of code (estimate) | ~1200 (schema, main, writer, versioning) |
| Total execution time | ~240 min (~4 hours) |
| Critical path | 01/02 → 03 → 04 → 05 |

---

## Files to be Created/Modified

### New Files
- HIKMAH__knowledge_index/README.md
- HIKMAH__knowledge_index/_index.json
- HIKMAH__knowledge_index/conftest.py
- HIKMAH__knowledge_index/index/__init__.py
- HIKMAH__knowledge_index/index/schema.py
- HIKMAH__knowledge_index/index/main.py
- HIKMAH__knowledge_index/index/writer.py
- HIKMAH__knowledge_index/index/versioning.py
- HIKMAH__knowledge_index/data/init_manifest.json
- HIKMAH__knowledge_index/tests/conftest.py
- HIKMAH__knowledge_index/tests/test_schema_validation.py
- HIKMAH__knowledge_index/tests/test_index_initialization.py
- HIKMAH__knowledge_index/tests/test_versioning.py

### Modified Files
- NIZAM__system/NIZAM_TEMPLE.json (add module + ledger)
- NIZAM__system/policies/PRIVACY_CLASSIFICATION.json (add rules)
- NIZAM__system/docs/CONTINUITY_PROTOCOL.md (add versioning pattern)
- .gitignore (add patterns to prevent index commits)

---

## Next Steps

1. **Execute Plan 01 & 02 in parallel** (Wave 1)
   - Define schema and set up module structure
   - Register in NIZAM governance and enforce privacy

2. **Execute Plan 03** (Wave 2)
   - Implement initialization logic for all 11 personas
   - Create empty index scaffolds

3. **Execute Plan 04** (Wave 3)
   - Implement versioning and MAKHZAN snapshot pattern
   - Document in CONTINUITY_PROTOCOL

4. **Execute Plan 05** (Wave 4)
   - Create comprehensive test suite
   - Verify all requirements satisfied
   - Confirm >80% coverage

5. **Phase acceptance gate:** All plans green + tests passing + privacy audit clean

---

## Success Signal for Executor

When Phase 14 is complete, you should be able to:

```python
# Test 1: Import and use schema
from HIKMAH__knowledge_index.index.schema import validate_index_schema
from HIKMAH__knowledge_index.index.main import initialize_all_personas
from pathlib import Path

# Test 2: Initialize all 11 personas
indices = initialize_all_personas(Path("HIKMAH__knowledge_index/indices"))
assert len(indices) == 11
assert all(path.exists() for path in indices.values())

# Test 3: Validate all indices
for persona, path in indices.items():
    import json
    index = json.loads(path.read_text())
    valid, error = validate_index_schema(index)
    assert valid is True, f"{persona}: {error}"

# Test 4: Verify privacy (no raw PII)
assert "Seif" not in index  # Names forbidden
assert index["topics"][0]["context_tags"] in [["technical"], ["health"], ...]  # Whitelist only

# Test 5: Version support
from HIKMAH__knowledge_index.index.versioning import increment_schema_version
increment_schema_version(Path("HIKMAH__knowledge_index/indices"), "1.0", "1.1", "Test bump")
# All 11 indices now at v1.1, MAKHZAN snapshot created
```

---

**Phase 14 planning complete. Ready for `/gsd:execute-phase 14`**

*Planning date: 2026-06-20*  
*Estimated execution: 4 hours*  
*Confidence: HIGH (grounded in existing NIZAM patterns, no new dependencies)*
