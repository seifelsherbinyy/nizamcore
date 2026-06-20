---
phase: 14
slug: knowledge-index-schema-storage
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-20
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | NIZAM__system/config/fixtures/intent_priority_test.py (existing) |
| **Quick run command** | `pytest HIKMAH__knowledge_index/tests/test_schema.py -v` |
| **Full suite command** | `pytest HIKMAH__knowledge_index/tests/ -v --cov` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest HIKMAH__knowledge_index/tests/test_schema.py -v`
- **After every plan wave:** Run `pytest HIKMAH__knowledge_index/tests/ -v --cov`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | INDEX-01 | unit | `pytest HIKMAH__knowledge_index/tests/test_schema.py::test_index_schema_structure -v` | ⬜ W0 | ⬜ pending |
| 14-01-02 | 01 | 1 | INDEX-01 | unit | `pytest HIKMAH__knowledge_index/tests/test_schema.py::test_topics_field_validation -v` | ⬜ W0 | ⬜ pending |
| 14-01-03 | 01 | 1 | INDEX-01 | unit | `pytest HIKMAH__knowledge_index/tests/test_schema.py::test_completions_field_validation -v` | ⬜ W0 | ⬜ pending |
| 14-02-01 | 02 | 1 | INDEX-02 | unit | `pytest HIKMAH__knowledge_index/tests/test_storage.py::test_local_storage_per_persona -v` | ⬜ W0 | ⬜ pending |
| 14-02-02 | 02 | 1 | INDEX-02 | integration | `pytest HIKMAH__knowledge_index/tests/test_storage.py::test_strict_local_classification -v` | ⬜ W0 | ⬜ pending |
| 14-03-01 | 03 | 2 | INDEX-03 | unit | `pytest HIKMAH__knowledge_index/tests/test_versioning.py::test_schema_version_field -v` | ⬜ W0 | ⬜ pending |
| 14-03-02 | 03 | 2 | INDEX-03 | unit | `pytest HIKMAH__knowledge_index/tests/test_versioning.py::test_makhzan_snapshot_pattern -v` | ⬜ W0 | ⬜ pending |
| 14-04-01 | 04 | 2 | INDEX-04 | integration | `pytest HIKMAH__knowledge_index/tests/test_initialization.py::test_init_creates_valid_index_all_personas -v` | ⬜ W0 | ⬜ pending |
| 14-04-02 | 04 | 2 | INDEX-04 | integration | `pytest HIKMAH__knowledge_index/tests/test_initialization.py::test_index_file_readable_json -v` | ⬜ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `HIKMAH__knowledge_index/tests/test_schema.py` — stubs for INDEX-01 schema validation
- [ ] `HIKMAH__knowledge_index/tests/test_storage.py` — stubs for INDEX-02 storage & strict_local
- [ ] `HIKMAH__knowledge_index/tests/test_versioning.py` — stubs for INDEX-03 versioning & evolution
- [ ] `HIKMAH__knowledge_index/tests/test_initialization.py` — stubs for INDEX-04 initialization
- [ ] `HIKMAH__knowledge_index/tests/conftest.py` — shared fixtures (persona fixtures, temp storage, mock SYNC_POLICY)
- [ ] `pytest` installed in project (if not already present)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Schema documentation is complete and understandable | INDEX-01 | Readability & clarity subjective | Review HIKMAH__knowledge_index/SCHEMA.md for clarity; test with non-implementer reading |
| Versioning strategy preserves backward compatibility | INDEX-03 | Snapshot validation is manual | Create v1.0 index, bump to v1.1, verify old indices remain readable |
| Privacy gate enforcement in SYNC_POLICY | INDEX-02 + INDEX-04 | Policy file integration requires human audit | Verify SYNC_POLICY includes strict_local classification for `HIKMAH__knowledge_index/indices/`; run `gsd-tools check-policy` if available |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING test file references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending (to be signed off after Wave 0 test stubs written)
