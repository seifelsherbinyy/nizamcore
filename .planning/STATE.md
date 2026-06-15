---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: planning
stopped_at: Completed 03-tier-2-rss-manual-sourcing/03-01-PLAN.md (Wave 0 TDD scaffold; 9 RED + 24 GREEN; SRC-02/03/06 fixtures + tests)
last_updated: "2026-06-15T10:49:10.325Z"
progress:
  total_phases: 13
  completed_phases: 2
  total_plans: 14
  completed_plans: 11
  percent: 79
---

---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: planning
stopped_at: Completed 01-foundation-data-model/01-06-PLAN.md (CAREER_RADAR_LEDGER registration ceremony; DATA-05 GREEN; Phase 1 complete 13/13 tests)
last_updated: "2026-06-14T20:36:53.280Z"
progress:
  total_phases: 13
  completed_phases: 1
  total_plans: 6
  completed_plans: 6
  percent: 100
---

# STATE: TARIQ Career Radar v1

**Last Updated:** 2026-06-14T20:11:05Z  
**Current Milestone:** Phase 1 execution — Plan 01-01 complete (Wave 0 TDD scaffold)

---

## Project Reference

**Project Name:** TARIQ Career Radar v1  
**Core Value:** Every run produces evidence-backed, scored opportunities (each with source link, access date, source type, honest confidence) delivered to Telegram + Drive — never fabricated salaries, never leaked personal data, never silently dropped findings.

**Scope:**  
- Full-depth remote-USD opportunity-radar pipeline  
- On-demand trigger only (no unattended cron in v1)  
- Additive module on existing NIZAM rails  
- 13 phases, 30 requirements, 100% coverage

**Key Constraints (Non-Negotiables):**
- No fabricated salaries; provenance + confidence or omit
- No raw personal-profile data in public files or Telegram
- No auto-apply, auto-contact recruiters, form-filling, credential use without explicit per-action approval
- Never silently drop findings; retry or print full unsaved output
- Additive only; no deletion/move/overwrite of existing NIZAM files
- Privacy enforced via existing SYNC_POLICY/HIMAYAH/PRIVACY_CLASSIFICATION

---

## Current Position

**Phase:** 1 / 13 (Foundation Data Model — in execution)  
**Plan:** 01-01 complete; Plan 01-02 next  
**Status:** Ready to plan
**Progress:** [████████░░] 79%

**Stopped At:** Completed 03-tier-2-rss-manual-sourcing/03-01-PLAN.md (Wave 0 TDD scaffold; 9 RED + 24 GREEN; SRC-02/03/06 fixtures + tests)

**Work Completed:**
- Analyzed 30 v1 requirements
- Derived 13 phases from strict data-dependency chain
- Mapped 100% of requirements to phases (no orphans)
- Documented success criteria (2–5 observable behaviors per phase)
- Honored all non-negotiables as cross-cutting constraints
- **[01-01]** Wave 0 TDD scaffold: 13 tests collectible + failing RED across 6 test files (DATA-01..05); conftest.py fixtures; TARIQ package roots; .gitignore data exclusions

**Phase 1 Execution Decisions:**
- try/except ImportError + _require_module() pattern for collectible-but-failing TDD tests (direct top-level imports cause collection errors, not test failures)
- parents[2] from test files in TARIQ__career_radar/tests/ resolves to repo root (not parents[3] as plan interface specified)
- test_profile_not_in_egress uses pytest.skip when profile_cache.json absent — correct TDD approach

---

## Roadmap Summary

| Phase | Goal | Requirements | Success Criteria |
|-------|------|--------------|------------------|
| 1 | Foundation & Data Model | DATA-01..05 | Schema defined, profile seed local, seen-store initialized, module layout NIZAM-compliant, ledger registered |
| 2 | Tier 1 ATS Sourcing | SRC-01, SRC-04, SRC-05 | Greenhouse/Lever/Ashby/Workable APIs fetch, normalize, error graceful |
| 3 | Tier 2 RSS & Manual Sourcing | SRC-02, SRC-03, SRC-06 | RSS parsed, manual import works, role-keyword filtering, ≥5 sources combined |
| 4 | Deduplication Engine | DEDUP-01..03 | Normalize + fuzzy match ≥0.88, persistent seen-store, rerun no-dup, freshness rule |
| 5 | Scoring Engine | SCORE-01, SCORE-02 | Deterministic 0–100 weighted score, penalties applied, same data → same score |
| 6 | Salary & Confidence Discipline | SALARY-01, SALARY-02 | Salary tagged with provenance + confidence, ranges only when unclear, no fabrication |
| 7 | Tagging & Profile Matching | TAG-01, TAG-02 | 8 action tags, caution flags for scams, local profile fit, no raw egress |
| 8 | Telegram Report | RPT-01 | Short action-oriented summary, best opp + salary + risk + action, no raw profile |
| 9 | Drive Evidence Report & Ledger | RPT-02, RPT-03, DELIV-01, DELIV-02 | Full Drive report + NAQD note, ledger appended, metadata correct |
| 10 | Delivery Continuity (Retry & Safety) | DELIV-03 | Telegram/Drive retry logic, full unsaved output on failure, run marked incomplete |
| 11 | On-Demand Trigger & NIZAM Wiring | RUN-01, RUN-02 | `/tariq-career-radar-run` invocable, full pipeline end-to-end, cron seam ready |
| 12 | Strategic Routing (MAL/TARIQ/MUNAWARA) | ROUTE-01 | Income → MAL, strategy → TARIQ, actions → MUNAWARA, integration tested |
| 13 | Validation & Safety Sign-Off | VAL-01 | Test run confirms extraction/salary/dedup/privacy/rerun-no-dup, operator sign-off |

---

## Performance Metrics

**Roadmap Quality:**
- Requirement coverage: 30/30 (100%) ✓
- Phases derived from data-dependency chain: Yes ✓
- Each phase has 2–5 observable success criteria: Yes ✓
- Non-negotiables encoded as constraints, not phases: Yes ✓

**Granularity Applied:**
- Config granularity: FINE
- Total phases: 13 (focused, smaller phases per data boundary)
- Phase interdependencies: Linear + some parallel (Phases 2–3 depend on Phase 1; Phases 5–7 depend on Phases 2–4)

---

## Accumulated Context

### Key Decisions Locked

| Decision | Rationale | Status |
|----------|-----------|--------|
| Build as additive module on existing NIZAM rails | Telegram/Drive/ledger/privacy/persona infra already live | Locked |
| Mirror MARSAD radar pattern (pluggable sources + connector-gating) | Proven in-repo precedent | Locked |
| v1 = full-depth pipeline on Remote USD lane only | Fastest payoff, lowest risk | Locked |
| On-demand trigger before unattended cron | Live data + privacy warrant human review | Locked |
| Connect findings to MAL/TARIQ/MUNAWARA | Strategic intelligence, not generic alerts | Locked |
| Validation as final phase + explicit gate | Safety bar before automation | Locked |
| Phase 01-foundation-data-model P01 | 5 | 2 tasks | 11 files |
| Phase 01-foundation-data-model P02 | 5 | 2 tasks | 2 files |
| Phase 01 P03 | 6 | 2 tasks | 1 files |
| Phase 01-foundation-data-model P05 | 8 | 1 tasks | 1 files |
| Phase 01-foundation-data-model P04 | 4min | 1 tasks | 2 files |
| Phase 01-foundation-data-model P06 | 2min | 2 tasks | 4 files |
| Phase 02-tier-1-ats-sourcing P01 | 149s | 3 tasks | 6 files |
| Phase 02-tier-1-ats-sourcing P02 | 191s | 2 tasks | 6 files |
| Phase 02-tier-1-ats-sourcing P03 | 91s | 2 tasks | 2 files |
| Phase 02-tier-1-ats-sourcing P04 | 383s | 1 tasks | 3 files |
| Phase 03-tier-2-rss-manual-sourcing P01 | 162 | 3 tasks | 7 files |

### Known Risks & Mitigations

| Risk | Mitigation | Phase |
|------|-----------|-------|
| Fabricated / over-confident salary | Provenance tag + confidence discipline, ranges only | Phases 6, 13 |
| ToS / scraping violations | API-first (Tier 1 + Tier 2), least-privilege, no aggressive scraping | Phases 2–3 |
| Dedup failures (repeat roles) | Normalized seen-store + fuzzy match + freshness rule | Phase 4 |
| Privacy leakage of raw profile | Profile strict_local, matching local, scores-only egress | Phases 1, 7, 13 |
| Scam / exploitative AI-eval platforms | Platform tier system, unpaid-screening, caution tags | Phase 7 |
| Over-automation before trust | All-or-nothing completion, ≥10 validation runs, explicit sign-off | Phases 10, 13 |
| LLM scoring inconsistency | Deterministic base scoring, LLM as explainer-only | Phase 5 |

### Research Flags from Briefing

Phases likely needing deeper research during planning:

- **Phase 2–3 (Sourcing):** Confirm Tier 2 API availability (Remotive/We Work Remotely/RemoteOK); fallback plan if endpoints change
- **Phase 9 (Drive Reports):** Verify existing `google_adapter` `.docx` write path supports full evidence-report shape
- **Phase 6 (Salary):** Operationalize confidence heuristics (high/medium/low decision rules); weight calibration on 10–20 real roles

Phases with standard patterns (can skip deep research):

- **Phase 4 (Dedup), Phase 1 (Ledger), Phase 8 (Telegram), Phase 1 (Privacy)** — MARSAD/NIZAM precedents established; RapidFuzz documented

### Data Dependencies (Strict Order)

```
Phase 1: Foundation (schema, store, layout)
  ↓
Phases 2–3: Sourcing (fetch opportunities)
  ↓
Phase 4: Dedup (normalize, detect duplicates)
  ↓
Phases 5–7: Enrich (score, salary, tags, profile fit)
  ↓
Phases 8–10: Report & Deliver (Telegram, Drive, ledger, continuity)
  ↓
Phase 11: Trigger (operator entry point)
  ↓
Phase 12: Routing (downstream integration)
  ↓
Phase 13: Validation (test bar + sign-off)
```

**Parallel Opportunities:**
- Phases 2 & 3 can be planned/built in parallel (both depend on Phase 1 only)
- Phases 5, 6, 7 can be planned in parallel (all depend on Phase 4 only)
- Phases 8, 9, 10 can be planned in parallel (all depend on Phases 5–7)

---

## Session Continuity

**Handoff to Planning:**
- Roadmap is locked and written to `.planning/ROADMAP.md`
- Requirements are mapped to phases in `.planning/REQUIREMENTS.md` (traceability section updated below)
- Next action: `/gsd:plan-phase 1` to decompose Phase 1 into executable plans

**Context for Next Session:**
- This roadmap is the baseline; revisions via `/gsd:revise-roadmap` if feedback warrants
- Each `/gsd:plan-phase N` will inherit this STATE.md and update the "Current Position" as it progresses
- Validation (Phase 13) is the final gate before any unattended cron; explicit operator sign-off required

---

*Roadmap created: 2026-06-14*  
*Ready for Phase 1 planning*
