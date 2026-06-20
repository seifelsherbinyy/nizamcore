---
phase: 15
slug: data-refresh-synchronization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-20
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.0+ with google-api-python-client mocking (unittest.mock + Mock Drive service) |
| **Config file** | `.planning/phases/15-data-refresh-synchronization/conftest.py` (Phase 15 shared fixtures) |
| **Quick run command** | `pytest HIKMAH__knowledge_index/refresh/tests/ -v -k "not integration"` |
| **Full suite command** | `pytest HIKMAH__knowledge_index/refresh/tests/ -v` |
| **Estimated runtime** | ~15 seconds (full suite), ~5 seconds (unit tests only) |

---

## Sampling Rate

- **After every task commit:** Run `pytest HIKMAH__knowledge_index/refresh/tests/ -v -k "not integration"` (unit tests only, < 5 sec)
- **After every plan wave:** Run `pytest HIKMAH__knowledge_index/refresh/tests/ -v` (includes mocked integration tests, ~15 sec)
- **Before `/gsd:verify-work`:** Full suite must be green + manual spot-check (operator runs with `--tb=short` and verifies audit ledger entries)
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | REFRESH-01 | integration | `pytest HIKMAH__knowledge_index/refresh/tests/test_drive_client.py::test_find_folder_by_name -v` | ❌ W0 | ⬜ pending |
| 15-01-02 | 01 | 1 | REFRESH-02 | unit | `pytest HIKMAH__knowledge_index/refresh/tests/test_merge_strategy.py::test_merge_preserves_stalled_work -v` | ❌ W0 | ⬜ pending |
| 15-01-03 | 01 | 1 | REFRESH-03 | unit | `pytest HIKMAH__knowledge_index/refresh/tests/test_refresh_fallback.py::test_fallback_on_network_error -v` | ❌ W0 | ⬜ pending |
| 15-01-04 | 01 | 1 | (Implicit audit) | unit | `pytest HIKMAH__knowledge_index/refresh/tests/test_audit_logging.py::test_audit_ledger_appended -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `HIKMAH__knowledge_index/refresh/__init__.py` — public API (refresh_persona_index, load_cached_index, etc.)
- [ ] `HIKMAH__knowledge_index/refresh/drive_client.py` — Google Drive API wrapper with retry logic
- [ ] `HIKMAH__knowledge_index/refresh/merge_strategy.py` — Activity merge with stalled_work preservation
- [ ] `HIKMAH__knowledge_index/refresh/ledger_writer.py` — Audit trail JSONL appender
- [ ] `HIKMAH__knowledge_index/refresh/tests/__init__.py` — test package marker
- [ ] `HIKMAH__knowledge_index/refresh/tests/conftest.py` — Shared pytest fixtures (MockDriveService, sample indices, mock credentials)
- [ ] `HIKMAH__knowledge_index/refresh/tests/test_drive_client.py` — mocked Drive API queries, credential loading, error handling
- [ ] `HIKMAH__knowledge_index/refresh/tests/test_merge_strategy.py` — activity merge logic, stalled_work preservation, validation
- [ ] `HIKMAH__knowledge_index/refresh/tests/test_refresh_fallback.py` — graceful degradation on Drive errors, cached index fallback
- [ ] `HIKMAH__knowledge_index/refresh/tests/test_audit_logging.py` — audit ledger JSONL append, success/failure logging

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Service account credentials resolve from secrets | REFRESH-01 | Requires access to NIZAM-secrets.json; credentials are environment-specific | Operator verifies: `from NIZAM__system.governor import load_credentials; creds = load_credentials("GOOGLE_SERVICE_ACCOUNT"); assert creds is not None` returns valid service account object |
| Drive folder structure matches assumptions | REFRESH-01 | Requires knowledge of actual Google Drive layout (YAWMIYAT/sessions folder location, file naming conventions) | Operator inspects actual Drive structure and confirms folder IDs match Phase 15 assumptions; documents any adjustments needed |
| Audit ledger persists across restarts | REFRESH-03 | Requires full process restart cycle | Operator: (1) Run one refresh cycle (check ledger writes), (2) Stop process, (3) Restart, (4) Run second refresh, (5) Verify both entries in ledger (no overwrite) |

---

## Validation Sign-Off

- [ ] All tasks have automated verify OR Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING file references (all listed files created)
- [ ] No watch-mode flags in test commands
- [ ] Feedback latency < 15s per phase commitment
- [ ] Manual verifications completed (credentials, folder structure, ledger persistence)
- [ ] `nyquist_compliant: true` set in frontmatter when complete

**Approval:** pending

---
