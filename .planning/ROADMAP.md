# ROADMAP: TARIQ Career Radar v1

**Project:** TARIQ Career Radar  
**Scope:** Full-depth remote-USD opportunity-radar pipeline, on-demand trigger, additive module on NIZAM rails  
**Granularity:** FINE (13 phases, derived from data-dependency chain)  
**Last Updated:** 2026-06-14

---

## Phases

- [ ] **Phase 1: Foundation & Data Model** - Establish opportunity schema, profile seed, seen-role store, module layout, and ledger registration
- [ ] **Phase 2: Tier 1 ATS Sourcing** - Fetch from no-auth Greenhouse/Lever/Ashby/Workable APIs with error graceful handling
- [ ] **Phase 3: Tier 2 RSS & Manual Sourcing** - Add RSS feeds + operator manual import with role keyword filtering
- [ ] **Phase 4: Deduplication Engine** - Normalize opportunities, fuzzy dedup, persistent seen-store, rerun-no-dup guarantee
- [ ] **Phase 5: Scoring Engine** - Implement deterministic 0–100 weighted scoring (fit 25, salary 20, growth 15, visa 10, company 10, referral 10, freshness 5, side-income 5) + penalties
- [ ] **Phase 6: Salary & Confidence Discipline** - Tag salaries with provenance + confidence, avoid fabrication, ranges only when unclear
- [ ] **Phase 7: Tagging & Profile Matching** - Assign 8 action tags, compute local profile fit, flag scams/unpaid, no raw data egress
- [ ] **Phase 8: Telegram Report** - Build short, action-oriented Telegram summary (best opp, salary, risk, next action)
- [ ] **Phase 9: Drive Evidence Report & Ledger** - Full Drive report (date, run ID, sources, counts, scores, confidence, gaps, next actions, links), ledger append, NAQD risk note
- [ ] **Phase 10: Delivery Continuity (Retry & Safety)** - Guarantee no silent drops; retry Telegram/Drive or print full unsaved output, mark run incomplete on failure
- [ ] **Phase 11: On-Demand Trigger & NIZAM Wiring** - Operator-invoked run via relay/router/TARIQ, cron seam ready (inactive), full pipeline end-to-end
- [ ] **Phase 12: Strategic Routing (MAL/TARIQ/MUNAWARA)** - Route findings to income/strategy/weekly-actions pillars, cross-pillar integration
- [ ] **Phase 13: Validation & Safety Sign-Off** - Test run on small real subset; confirm extraction correct, salary not fabricated, dedup works, no leaks, rerun no-dup

---

## Phase Details

### Phase 1: Foundation & Data Model
**Goal:** Establish the opportunity schema, profile seed, seen-role store, module layout, and ledger registration so all downstream work has a solid data foundation.

**Depends on:** Nothing (first phase)

**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04, DATA-05

**Success Criteria** (what must be TRUE when phase completes):
1. Opportunity record schema is documented (title, company, location, remote_status, salary_low/high, role_link, source, source_type, access_date, fit_score, growth_score, confidence, tags, next_action, profile_gap, run_id, observed_at, lane)
2. Profile seed file exists locally (role keyword groups + target-role taxonomy from Seif's profile), marked as strict_local, never exported
3. Seen-role store (SQLite or JSONL) is initialized and survives across runs with clear schema
4. Module folder structure follows NIZAM conventions (mirroring MARSAD placement)
5. Career Radar ledger is registered in NIZAM/TEMPLE/known-ledgers with privacy path-rules added to PRIVACY_CLASSIFICATION

**Plans:** 2/6 plans executed

Plans:
- [ ] 01-01-PLAN.md — Wave 0: Test scaffold (12 failing tests across all DATA-01..05 requirements)
- [ ] 01-02-PLAN.md — Wave 1: JSON Schema definition for opportunity record (DATA-01)
- [ ] 01-03-PLAN.md — Wave 1: Module folder layout + NIZAM registration (DATA-04)
- [ ] 01-04-PLAN.md — Wave 2: Profile seed file, strict_local_maximum (DATA-02)
- [ ] 01-05-PLAN.md — Wave 2: SQLite dedup engine + normalization (DATA-03)
- [ ] 01-06-PLAN.md — Wave 3: Ledger registration ceremony in 3 live NIZAM files (DATA-05)

---

### Phase 2: Tier 1 ATS Sourcing
**Goal:** Establish reliable API-based sourcing from no-auth public ATS endpoints (Greenhouse, Lever, Ashby, Workable) with graceful error handling.

**Depends on:** Phase 1 (schema, module layout)

**Requirements:** SRC-01, SRC-04, SRC-05

**Success Criteria** (what must be TRUE when phase completes):
1. All four ATS connectors (Greenhouse, Lever, Ashby, Workable) fetch job postings without authentication
2. Each fetched opportunity is normalized into the DATA-01 schema with source link, source type, and access date recorded
3. API errors (connection failures, rate limits, missing endpoints) are logged to blocked-sources list and do not abort the run
4. A run with zero sources returning results degrades gracefully (reports zero opportunities, marks sources as blocked, continues to next phase)

**Plans:** TBD

---

### Phase 3: Tier 2 RSS & Manual Sourcing
**Goal:** Add Tier 2 RSS feeds and operator manual import path, with target-role filtering for remote-USD AI/data/AI-ops/coordination roles.

**Depends on:** Phase 1 (schema, profile seed for keyword filtering), Phase 2 (normalization precedent)

**Requirements:** SRC-02, SRC-03, SRC-06

**Success Criteria** (what must be TRUE when phase completes):
1. RSS feeds (Remotive, We Work Remotely, RemoteOK) are parsed using stdlib `xml.etree.ElementTree` into normalized records
2. Operator can manually import opportunities via structured JSONL/paste input (Outlier, DataAnnotation, Turing, Toloka, Braintrust, Contra, Wellfound)
3. All fetched opportunities are filtered to remote-USD AI/data/AI-ops/coordination roles matching Seif's role keyword groups
4. Combined sources (Tier 1 + Tier 2) yield ≥5 distinct opportunities in a test run

**Plans:** TBD

---

### Phase 4: Deduplication Engine
**Goal:** Normalize opportunities into canonical form, apply fuzzy matching, and maintain a persistent seen-role store so reruns do not surface already-seen roles.

**Depends on:** Phase 1 (schema, seen-store definition), Phases 2–3 (sourcing provides candidate records)

**Requirements:** DEDUP-01, DEDUP-02, DEDUP-03

**Success Criteria** (what must be TRUE when phase completes):
1. Opportunities are normalized (title/company/location/URL canonicalization) into a deterministic dedup key
2. Fuzzy matching with `rapidfuzz` (token_sort_ratio ≥0.88) detects duplicates within a single run (test with 2+ sources reporting the same role)
3. Re-running the radar against the same sources does not re-surface already-seen roles; seen-store is consulted before including in results
4. Freshness rule allows genuine reposts (same role posted >30 days after first seen) to surface as new

**Plans:** TBD

---

### Phase 5: Scoring Engine
**Goal:** Implement a deterministic 0–100 weighted scoring formula with penalty logic so opportunities are ranked by strategic value.

**Depends on:** Phase 1 (schema includes score fields), Phase 4 (only deduplicated opportunities are scored)

**Requirements:** SCORE-01, SCORE-02

**Success Criteria** (what must be TRUE when phase completes):
1. Every opportunity receives a deterministic 0–100 score using weights: fit 25, salary upside 20, growth 15, visa/remote feasibility 10, company strength 10, referral/application leverage 10, freshness 5, side-income 5
2. Same opportunity scored twice produces identical score (deterministic, no LLM injection)
3. Scoring applies penalties (−5 to −20 points) for no-evidence, scam risk, unclear pay, severe skill mismatch, exploitative unpaid work
4. Opportunities are ranked by final score, descending

**Plans:** TBD

---

### Phase 6: Salary & Confidence Discipline
**Goal:** Tag every salary claim with provenance and confidence level; avoid fabrication by using ranges and source evidence only.

**Depends on:** Phase 1 (schema includes salary_low/high, confidence, tags), Phase 5 (scoring includes salary-upside component that depends on confidence)

**Requirements:** SALARY-01, SALARY-02

**Success Criteria** (what must be TRUE when phase completes):
1. Every salary claim is tagged with provenance (employer-posted / estimated / recruiter-stated / guide-based / community-reported)
2. Confidence level (high/medium/low) is recorded; when evidence is unclear, confidence is marked low and no exact number is invented (ranges only, with methodology documented)
3. Low-confidence salaries are flagged in reports and scoring (salary upside component downweighted)
4. No test opportunity has a "fabricated" exact salary without a clear source link

**Plans:** TBD

---

### Phase 7: Tagging & Profile Matching
**Goal:** Assign action labels to each opportunity and compute local profile fit without exposing raw personal data.

**Depends on:** Phase 1 (profile seed definition), Phases 5–6 (scoring and salary provide input for tags)

**Requirements:** TAG-01, TAG-02

**Success Criteria** (what must be TRUE when phase completes):
1. Each opportunity is tagged with one or more of: APPLY NOW / REFERRAL FIRST / WATCHLIST / PROFILE GAP / LOW CONFIDENCE / SIDE INCOME / RELOCATION BET / USD CASHFLOW
2. Scam-prone or exploitative-unpaid platforms are flagged with a caution tag and brief reasoning (no raw data)
3. Profile fit is computed locally against the profile seed (no raw profile data leaves the machine)
4. Tag assignment is deterministic based on score + salary + fit + confidence (same opportunity tagged the same way every run)

**Plans:** TBD

---

### Phase 8: Telegram Report
**Goal:** Build a short, action-oriented Telegram summary suitable for daily delivery.

**Depends on:** Phases 5–7 (scoring, salary, tags provide content), Phase 1 (privacy rules)

**Requirements:** RPT-01

**Success Criteria** (what must be TRUE when phase completes):
1. Telegram report includes: best opportunity + salary insight + main risk/gap + one recommended action
2. Report is concise and action-oriented (≤500 chars target, link-driven, no rambling)
3. Report contains no raw personal-profile data or sensitive matching details (scores/tags only)
4. Report is readable and actionable for Seif in a single glance (text rendering test passed)

**Plans:** TBD

---

### Phase 9: Drive Evidence Report & Ledger
**Goal:** Build a full evidence report for Drive and append a ledger record so the run is documented and discoverable.

**Depends on:** Phases 5–8 (all upstream data ready), Phase 1 (ledger definition, Drive folder rules)

**Requirements:** RPT-02, RPT-03, DELIV-01, DELIV-02

**Success Criteria** (what must be TRUE when phase completes):
1. Full Drive evidence report includes: date, run ID, sources searched, new/duplicate counts, top roles (by score), salary evidence + confidence breakdown, fit/growth scores, feasibility notes, company strength indicators, profile gaps, application route per role, next actions, evidence links, errors/blocked sources, Telegram summary, ledger IDs/paths
2. Drive report is saved to correct NIZAM Drive folder (Records/{lane}/...) with metadata
3. NAQD red-team note briefly explains attractive-but-risky top roles (1–2 paras, reasoning only)
4. Ledger record is appended with run ID, sources searched, counts, file paths, timestamp

**Plans:** TBD

---

### Phase 10: Delivery Continuity (Retry & Safety)
**Goal:** Guarantee that findings are never silently dropped; implement retry logic for Telegram + Drive, or print full unsaved output and mark run incomplete.

**Depends on:** Phases 8–9 (Telegram + Drive reports to deliver), Phase 1 (privacy/egress rules)

**Requirements:** DELIV-03

**Success Criteria** (what must be TRUE when phase completes):
1. On Telegram send failure, the system retries (exponential backoff, ≤3 attempts)
2. On Drive write failure, the system retries (exponential backoff, ≤3 attempts)
3. If both retries fail, the full unsaved output (Telegram + Drive report) is printed to console/log with clear "UNSAVED" marking
4. Run is marked incomplete (ledger flag or status field), never silently succeeds if delivery partially failed

**Plans:** TBD

---

### Phase 11: On-Demand Trigger & NIZAM Wiring
**Goal:** Wire the full pipeline into NIZAM's relay/router/TARIQ system so the operator can invoke a run on-demand with output review before delivery.

**Depends on:** All upstream phases (pipeline complete)

**Requirements:** RUN-01, RUN-02

**Success Criteria** (what must be TRUE when phase completes):
1. Operator can invoke `/tariq-career-radar-run` command (or equivalent) via NIZAM relay
2. Full fetch→dedup→enrich→score→tag→report→deliver→ledger pipeline executes end-to-end for the Remote USD lane
3. A clean seam exists in code to add unattended Hermes-cron daily slots later (built but inactive, marked TODO)
4. Run output is reviewable before final delivery (checkpoint/pause point available, though v1 executes end-to-end)

**Plans:** TBD

---

### Phase 12: Strategic Routing (MAL/TARIQ/MUNAWARA)
**Goal:** Route findings to downstream pillars (income, strategy, weekly actions) so the radar feeds the broader NIZAM intelligence system.

**Depends on:** Phase 11 (run output available), Phase 1 (routing rules defined)

**Requirements:** ROUTE-01

**Success Criteria** (what must be TRUE when phase completes):
1. Income-relevant opportunities (high salary, stable, USD cashflow) are signaled to MAL (income pillar)
2. Long-term strategy insights (growth, positioning, skill-building) are routed to TARIQ (strategy persona)
3. Weekly action items (apply now, referral prep, profile gap work) are routed to MUNAWARA (weekly-actions pillar)
4. Cross-pillar integration is tested (at least one opportunity successfully routed to each pillar in test run)

**Plans:** TBD

---

### Phase 13: Validation & Safety Sign-Off
**Goal:** Run a small real source test to confirm extraction correctness, salary not fabricated, dedup works, privacy preserved, and rerun produces no duplicates — the brief's Step 9 test bar.

**Depends on:** All upstream phases (complete pipeline)

**Requirements:** VAL-01

**Success Criteria** (what must be TRUE when phase completes):
1. Test run over a small real source subset (≥2 ATS APIs + ≥1 RSS feed + manual import) extracts opportunities correctly (field mapping verified against source)
2. Salary confidence is not fabricated (every salary has a provenance tag, ranges used when unclear, no invented exact numbers)
3. Duplicates are removed (2+ sources reporting same role → deduplicated, only 1 copy in results)
4. Telegram report is readable and actionable; Drive report is complete and saved
5. Ledger record is appended with correct paths and run ID
6. Re-running against the same sources produces zero duplicate results (seen-store verified)
7. No secrets, personal profile details, or sensitive matching data leak to public files or Telegram
8. Operator sign-off obtained (written approval that pipeline is trustworthy for daily use)

**Plans:** TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Data Model | 2/6 | In Progress|  |
| 2. Tier 1 ATS Sourcing | 0/? | Not started | — |
| 3. Tier 2 RSS & Manual Sourcing | 0/? | Not started | — |
| 4. Deduplication Engine | 0/? | Not started | — |
| 5. Scoring Engine | 0/? | Not started | — |
| 6. Salary & Confidence Discipline | 0/? | Not started | — |
| 7. Tagging & Profile Matching | 0/? | Not started | — |
| 8. Telegram Report | 0/? | Not started | — |
| 9. Drive Evidence Report & Ledger | 0/? | Not started | — |
| 10. Delivery Continuity (Retry & Safety) | 0/? | Not started | — |
| 11. On-Demand Trigger & NIZAM Wiring | 0/? | Not started | — |
| 12. Strategic Routing (MAL/TARIQ/MUNAWARA) | 0/? | Not started | — |
| 13. Validation & Safety Sign-Off | 0/? | Not started | — |

---

**Roadmap Status:** Ready for planning  
**Next:** `/gsd:plan-phase 1` (Foundation & Data Model)
