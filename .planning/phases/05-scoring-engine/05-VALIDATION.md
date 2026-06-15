---
phase: 5
slug: scoring-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-15
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for scoring engine (deterministic formula, penalty logic, reproducibility).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | TARIQ__career_radar/pytest.ini |
| **Quick run command** | `pytest TARIQ__career_radar/tests/test_scoring_engine.py -v` |
| **Full suite command** | `pytest TARIQ__career_radar/tests/ -v --tb=short` |
| **Estimated runtime** | ~35 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest TARIQ__career_radar/tests/test_scoring_engine.py -v` (quick)
- **After every plan wave:** Run full suite: `pytest TARIQ__career_radar/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green (all phases)
- **Max feedback latency:** 35 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | SCORE-01 | unit | `pytest -k test_determinism` | ⬜ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | SCORE-02 | unit | `pytest -k test_penalty` | ⬜ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | SCORE-01 | unit | `pytest -k test_fit_dimension` | ✅ to build | ⬜ pending |
| 05-02-02 | 02 | 2 | SCORE-01 | unit | `pytest -k test_salary_dimension` | ✅ to build | ⬜ pending |
| 05-02-03 | 02 | 2 | SCORE-01 | unit | `pytest -k test_growth_dimension` | ✅ to build | ⬜ pending |
| 05-02-04 | 02 | 2 | SCORE-01 | unit | `pytest -k test_visa_dimension` | ✅ to build | ⬜ pending |
| 05-02-05 | 02 | 2 | SCORE-01 | unit | `pytest -k test_company_dimension` | ✅ to build | ⬜ pending |
| 05-02-06 | 02 | 2 | SCORE-01 | unit | `pytest -k test_referral_dimension` | ✅ to build | ⬜ pending |
| 05-02-07 | 02 | 2 | SCORE-01 | unit | `pytest -k test_freshness_dimension` | ✅ to build | ⬜ pending |
| 05-02-08 | 02 | 2 | SCORE-01 | unit | `pytest -k test_side_income_dimension` | ✅ to build | ⬜ pending |
| 05-02-09 | 02 | 2 | SCORE-02 | unit | `pytest -k test_all_penalties_applied` | ✅ to build | ⬜ pending |
| 05-03-01 | 03 | 3 | SCORE-01 | integration | `pytest -k test_scoring_pass_e2e` | ✅ to build | ⬜ pending |
| 05-03-02 | 03 | 3 | SCORE-01 | integration | `pytest -k test_ranked_output` | ✅ to build | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `TARIQ__career_radar/tests/test_scoring_engine.py` — stubs for SCORE-01, SCORE-02 (determinism + penalties, 17 RED tests)
- [ ] `TARIQ__career_radar/tests/conftest.py` — Phase 5 fixtures (sample opportunities, profile_cache mock, scoring_test_data.jsonl)
- [ ] `TARIQ__career_radar/radar/scoring_engine.py` — existing Phase 1 foundation verified importable

*Phase 1 already has scoring_engine.py stub; Phase 5 Wave 0 adds tests + fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Penalty calibration (−5 to −20 ranges) | SCORE-02 | Optimal values require real opportunity domain knowledge | Run Phase 5 Wave 0 + 2 with 50+ real opportunities from Tier 1 ATS APIs; measure false-negative and false-positive penalty rates; adjust thresholds if outliers detected |
| Company strength heuristics | SCORE-01 | Text-based inference needs human validation on real postings | Phase 13 validation: review 20+ opportunity postings; verify company tier inferences match ground truth (public signals only, no proprietary data) |
| Growth dimension sufficiency | SCORE-01 | Role category + tier heuristics may need enhancement | Phase 5 Wave 2: test against diverse roles (data engineer → staff, manager → director); if growth scores cluster heavily, enhance with linguistic signals in Phase 13+ |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING test references (test_scoring_engine.py, fixtures)
- [ ] No watch-mode flags
- [ ] Feedback latency < 35s per task
- [ ] `nyquist_compliant: true` set in frontmatter (after verification passes)

**Approval:** pending

---

*Phase 5 Validation: Scoring Engine (deterministic 0–100 formula, 8 dimensions, penalty logic)*
*Validated infrastructure: Phase 1 scoring_engine.py + Phase 5 TDD tests*
