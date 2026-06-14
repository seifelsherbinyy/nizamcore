---
phase: 1
slug: foundation-data-model
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-14
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (already in NIZAM root) |
| **Config file** | `TARIQ__career_radar/conftest.py` (Wave 0 creates shared fixtures) |
| **Quick run command** | `pytest TARIQ__career_radar/tests/test_dedup_engine.py TARIQ__career_radar/tests/test_config.py -x` |
| **Full suite command** | `pytest TARIQ__career_radar/tests/ -v` |
| **Estimated runtime** | ~30 seconds (full); <10s quick |

---

## Sampling Rate

- **After every task commit:** Run quick command (`test_dedup_engine.py` + `test_config.py`)
- **After every plan wave:** Run `pytest TARIQ__career_radar/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite + NIZAM governor tests (`test_ledger_writer`, `test_pre_commit_check`) must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Req | Behavior | Test Type | Automated Command | File Exists | Status |
|-----|----------|-----------|-------------------|-------------|--------|
| DATA-01 | Opportunity record validates against JSON Schema | unit | `pytest TARIQ__career_radar/tests/test_opportunity_schema.py::test_schema_validate -x` | ❌ W0 | ⬜ pending |
| DATA-02 | Profile seed loads and contains required keys | unit | `pytest TARIQ__career_radar/tests/test_config.py::test_profile_seed_load -x` | ❌ W0 | ⬜ pending |
| DATA-02 | Profile seed never serializes to egress (stdout/Telegram) | integration | `pytest TARIQ__career_radar/tests/test_privacy.py::test_profile_not_in_egress -x` | ❌ W0 | ⬜ pending |
| DATA-03 | Seen-role store round-trip (insert + retrieve) | unit | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_sqlite_roundtrip -x` | ❌ W0 | ⬜ pending |
| DATA-03 | Seen-role store survives process restart | integration | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_persistence_across_restarts -x` | ❌ W0 | ⬜ pending |
| DATA-03 | Dedup normalization is deterministic | unit | `pytest TARIQ__career_radar/tests/test_dedup_engine.py::test_normalization_deterministic -x` | ❌ W0 | ⬜ pending |
| DATA-04 | Module folder structure matches MARSAD pattern | unit | `pytest TARIQ__career_radar/tests/test_structure.py::test_module_layout -x` | ❌ W0 | ⬜ pending |
| DATA-04 | _index.json registers to NIZAM_MASTER_REGISTER | unit | `pytest TARIQ__career_radar/tests/test_registration.py::test_index_json_valid -x` | ❌ W0 | ⬜ pending |
| DATA-05 | Ledger appends with correct envelope | unit | `pytest NIZAM__system/governor/tests/ -k "test_ledger_append" -x` | ✅ Exists | ⬜ pending |
| DATA-05 | Ledger appears in KNOWN_LEDGERS set | unit | `pytest TARIQ__career_radar/tests/test_registration.py::test_ledger_registered -x` | ❌ W0 | ⬜ pending |
| DATA-05 | Privacy rules for module paths defined | unit | `pytest TARIQ__career_radar/tests/test_privacy.py::test_privacy_rules_defined -x` | ❌ W0 | ⬜ pending |
| DATA-05 | Pre-commit hook blocks strict_local files | integration | `pytest NIZAM__system/governor/tests/test_pre_commit_check.py -k tariq -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `TARIQ__career_radar/conftest.py` — shared fixtures (temp db, sample profile, opportunity fixtures)
- [ ] `TARIQ__career_radar/tests/test_opportunity_schema.py` — schema validation + fixture examples (DATA-01)
- [ ] `TARIQ__career_radar/tests/test_config.py` — profile seed loading + key validation (DATA-02)
- [ ] `TARIQ__career_radar/tests/test_dedup_engine.py` — SQLite roundtrip, normalization, persistence (DATA-03)
- [ ] `TARIQ__career_radar/tests/test_structure.py` — folder layout mirrors MARSAD (DATA-04)
- [ ] `TARIQ__career_radar/tests/test_registration.py` — _index.json, NIZAM_MASTER_REGISTER, KNOWN_LEDGERS, privacy rules (DATA-04/05)
- [ ] `TARIQ__career_radar/tests/test_privacy.py` — privacy classification + egress checks (DATA-02/05)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Encrypted-Drive mirror of the seen-store `.db` succeeds as a binary blob | DATA-03/05 | Requires live rclone-crypt + Drive credentials (VPS) — out of CI scope | After Phase 1 lands, run one mirror cycle on VPS and confirm the `.db` ciphertext appears in `drive-crypt:` and `.last_mirror` updates |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
