---
phase: 3
slug: tier-2-rss-manual-sourcing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-15
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (already in NIZAM root) |
| **Config file** | `TARIQ__career_radar/conftest.py` (extend with Phase-3 RSS/JSONL fixtures) |
| **Quick run command** | `pytest TARIQ__career_radar/tests/test_sources.py -k "rss or manual or role_filter" -x` |
| **Full suite command** | `pytest TARIQ__career_radar/tests/ -v` |
| **Estimated runtime** | <60s full |
| **Network policy** | NO real network in CI — RSS/JSON via recorded fixtures through the existing conftest `fake_requests_get` monkeypatch fixture. Do NOT extend the import-time `requests.get` patch in `tests/fixtures/__init__.py` (known tech-debt); use proper fixtures/monkeypatch. |

---

## Sampling Rate

- **After every task commit:** Run `pytest TARIQ__career_radar/tests/test_sources.py -k "rss or manual or role_filter" -x`
- **After every plan wave:** Run `pytest TARIQ__career_radar/tests/ -v` (Phase-1's 13 + Phase-2's 11 must stay green)
- **Before `/gsd:verify-work`:** Full suite green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Req | Behavior | Test Type | Automated Command | File Exists | Status |
|-----|----------|-----------|-------------------|-------------|--------|
| SRC-02 | Remotive RSS fetched + parsed (stdlib XML) → SourceResult | unit (mock HTTP) | `pytest TARIQ__career_radar/tests/test_sources.py::test_remotive_rss_mocked -x` | ❌ W0 | ⬜ pending |
| SRC-02 | We Work Remotely RSS parsed (no company field) → normalized | unit (mock HTTP) | `pytest TARIQ__career_radar/tests/test_sources.py::test_weworkremotely_rss_mocked -x` | ❌ W0 | ⬜ pending |
| SRC-02 | RemoteOK feed parsed (salary field) → normalized | unit (mock HTTP) | `pytest TARIQ__career_radar/tests/test_sources.py::test_remoteok_mocked -x` | ❌ W0 | ⬜ pending |
| SRC-02 | Malformed feed XML → logged to blocked_sources, run continues | integration | `pytest TARIQ__career_radar/tests/test_sources.py::test_rss_malformed_xml_graceful -x` | ❌ W0 | ⬜ pending |
| SRC-03 | ManualImportSource reads JSONL → valid normalized records | unit | `pytest TARIQ__career_radar/tests/test_sources.py::test_manual_import_valid_jsonl -x` | ❌ W0 | ⬜ pending |
| SRC-03 | Missing manual-import file handled gracefully (no raise) | unit | `pytest TARIQ__career_radar/tests/test_sources.py::test_manual_import_file_not_found -x` | ❌ W0 | ⬜ pending |
| SRC-03 | Malformed JSONL line rejected + logged, continues | unit | `pytest TARIQ__career_radar/tests/test_sources.py::test_manual_import_malformed_json -x` | ❌ W0 | ⬜ pending |
| SRC-06 | RoleKeywordFilter keeps in-scope titles (matches profile keyword groups) | unit | `pytest TARIQ__career_radar/tests/test_sources.py::test_role_filter_matches -x` | ❌ W0 | ⬜ pending |
| SRC-06 | RoleKeywordFilter drops out-of-scope titles | unit | `pytest TARIQ__career_radar/tests/test_sources.py::test_role_filter_rejects -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `TARIQ__career_radar/tests/fixtures/` — `remotive_sample_rss.xml`, `weworkremotely_sample_rss.xml`, `remoteok_sample_response.json`, `manual_import_sample.jsonl`, plus a malformed-XML fixture
- [ ] `TARIQ__career_radar/conftest.py` — RSS/JSON/JSONL fixture loaders reusing the existing `fake_requests_get` factory (NO import-time global patch)
- [ ] `TARIQ__career_radar/tests/test_sources.py` — the 9 failing tests above (SRC-02/03/06), RED until sources + filter exist

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live RSS feeds still return the expected element shape | SRC-02 | Live network + third-party feed drift — not for CI | Once, fetch each live feed (Remotive/WWR/RemoteOK), diff element/field shape vs the recorded fixture; refresh fixtures if changed |
| Operator manual-import JSONL ingest with a real hand-authored file | SRC-03 | Depends on operator-authored content + gitignored local data | Author a few real rows in `data/manual_imports.jsonl`, run the source, confirm normalized + role-filtered correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (RSS/JSONL fixtures + conftest loaders + test_sources.py)
- [ ] No watch-mode flags; no real network in CI; no extension of the import-time requests.get patch
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
