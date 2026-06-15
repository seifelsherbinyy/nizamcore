---
phase: 4
slug: deduplication-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-15
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for deduplication engine (fuzzy matching, seen-store persistence, freshness rules).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | TARIQ__career_radar/pytest.ini |
| **Quick run command** | `pytest TARIQ__career_radar/tests/test_dedup.py -v` |
| **Full suite command** | `pytest TARIQ__career_radar/tests/ -v --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest TARIQ__career_radar/tests/test_dedup.py -v` (quick)
- **After every plan wave:** Run full suite: `pytest TARIQ__career_radar/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green (all phases)
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | DEDUP-01 | unit | `pytest -k test_normalize` | ⬜ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | DEDUP-02 | unit | `pytest -k test_fuzzy_match` | ⬜ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | DEDUP-03 | unit | `pytest -k test_seen_store` | ⬜ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | DEDUP-01 | integration | `pytest -k test_dedup_full_run` | ✅ to build | ⬜ pending |
| 04-03-01 | 03 | 3 | DEDUP-02, DEDUP-03 | integration | `pytest -k test_freshness_rule` | ✅ to build | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `TARIQ__career_radar/tests/test_dedup.py` — stubs for DEDUP-01, DEDUP-02, DEDUP-03 (RED tests)
- [ ] `TARIQ__career_radar/tests/conftest.py` — Phase 4 fixtures (sample opportunities, mock seen-store)
- [ ] `TARIQ__career_radar/radar/dedup_engine.py` — existing Phase 1 implementation verified importable

*Phase 1 already has dedup_engine.py; Phase 4 Wave 0 adds tests + fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fuzzy threshold calibration | DEDUP-02 | Optimal 0.88 ratio requires real job-title dataset | Run Phase 4 Wave 2 with 50+ real job titles from Greenhouse + Remotive; measure false-positive/false-negative rates; adjust threshold if > 5% error |
| Freshness rule business logic | DEDUP-03 | 30-day threshold is product policy, not algorithmic | Verify business stakeholder approval for freshness threshold; document in phase completion |
| Long-term seen-store performance | Implicit | O(n²) fuzzy matching may slow on 1000+ roles | Benchmark with production-scale data; if >10s latency, optimize or document limitation |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING test references (test_dedup.py, fixtures)
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s per task
- [ ] `nyquist_compliant: true` set in frontmatter (after verification passes)

**Approval:** pending

---

*Phase 4 Validation: Deduplication Engine (fuzzy matching, seen-store, freshness rules)*
*Validated infrastructure: Phase 1 dedup_engine.py + Phase 4 TDD tests*
