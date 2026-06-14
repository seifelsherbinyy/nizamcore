---
phase: 2
slug: tier-1-ats-sourcing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-15
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (already in NIZAM root) |
| **Config file** | `TARIQ__career_radar/conftest.py` (extend Phase-1 fixtures with HTTP mocks + ATS sample responses) |
| **Quick run command** | `pytest TARIQ__career_radar/tests/test_sources.py -x` |
| **Full suite command** | `pytest TARIQ__career_radar/tests/ -v` |
| **Estimated runtime** | <60s full; <10s quick |
| **Network policy** | NO real network in CI — all ATS calls use recorded JSON fixtures via an injected fake-HTTP transport |

---

## Sampling Rate

- **After every task commit:** Run `pytest TARIQ__career_radar/tests/test_sources.py -x`
- **After every plan wave:** Run `pytest TARIQ__career_radar/tests/ -v` (must keep Phase-1's 13 tests green too)
- **Before `/gsd:verify-work`:** Full suite green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Req | Behavior | Test Type | Automated Command | File Exists | Status |
|-----|----------|-----------|-------------------|-------------|--------|
| SRC-01 | Greenhouse fetches public endpoint, no auth | unit (mock HTTP) | `pytest TARIQ__career_radar/tests/test_sources.py::test_greenhouse_fetch_mocked -x` | ❌ W0 | ⬜ pending |
| SRC-01 | Lever fetches public endpoint, no auth | unit (mock HTTP) | `pytest TARIQ__career_radar/tests/test_sources.py::test_lever_fetch_mocked -x` | ❌ W0 | ⬜ pending |
| SRC-01 | Ashby fetches public endpoint, no auth | unit (mock HTTP) | `pytest TARIQ__career_radar/tests/test_sources.py::test_ashby_fetch_mocked -x` | ❌ W0 | ⬜ pending |
| SRC-01 | Workable fetches public endpoint, no auth | unit (mock HTTP) | `pytest TARIQ__career_radar/tests/test_sources.py::test_workable_fetch_mocked -x` | ❌ W0 | ⬜ pending |
| SRC-04 | Each fetched opportunity normalizes to schema | unit | `pytest TARIQ__career_radar/tests/test_sources.py::test_normalization_to_schema -x` | ❌ W0 | ⬜ pending |
| SRC-04 | Opportunity carries source, source_type, source_url, access_date | unit | `pytest TARIQ__career_radar/tests/test_sources.py::test_required_fields_present -x` | ❌ W0 | ⬜ pending |
| SRC-04 | Salary confidence HIGH when employer-posted, LOW when absent | unit | `pytest TARIQ__career_radar/tests/test_sources.py::test_salary_confidence_tagging -x` | ❌ W0 | ⬜ pending |
| SRC-05 | Network-failed source logged + run continues | integration (mock error) | `pytest TARIQ__career_radar/tests/test_sources.py::test_fetch_network_error_graceful -x` | ❌ W0 | ⬜ pending |
| SRC-05 | Rate-limited (429) returns flag, no retry in-run | unit (mock 429) | `pytest TARIQ__career_radar/tests/test_sources.py::test_429_rate_limit_handled -x` | ❌ W0 | ⬜ pending |
| SRC-05 | Blocked-sources manifest populated on failure | integration | `pytest TARIQ__career_radar/tests/test_sources.py::test_blocked_sources_manifest -x` | ❌ W0 | ⬜ pending |
| SRC-05 | Zero-results run degrades gracefully (no abort) | integration | `pytest TARIQ__career_radar/tests/test_sources.py::test_zero_results_graceful -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `TARIQ__career_radar/tests/fixtures/` — recorded JSON sample responses: `greenhouse_sample_response.json`, `lever_sample_response.json`, `ashby_sample_response.json`, `workable_sample_response.json`
- [ ] `TARIQ__career_radar/conftest.py` — add ATS response fixtures + a fake-HTTP transport fixture (monkeypatch the connectors' request function); never hit the network
- [ ] `TARIQ__career_radar/tests/test_sources.py` — the 11 failing tests above (SRC-01/04/05), RED until connectors exist

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real ATS endpoints still return the expected JSON shape | SRC-01 | Live network + third-party API drift — not for CI | Once, against 1 known board per ATS (e.g. a Greenhouse `board_token`), run a live fetch and diff the field shape against the recorded fixture; refresh fixtures if the API changed |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (fixtures + fake-HTTP transport + test_sources.py)
- [ ] No watch-mode flags; no real network in CI
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
