# Requirements: TARIQ Career Radar

**Defined:** 2026-06-14
**Core Value:** Every run produces evidence-backed, scored opportunities (each with source link, access date, source type, honest confidence) delivered to Telegram + Drive — never fabricated salaries, never leaked personal data, never silently dropped findings.

> **v1 scope:** full-depth radar pipeline proven on the **Remote USD** lane only, **on-demand** trigger. GCC/Europe lanes and unattended cron are v2 (deferred). Additive module on existing NIZAM rails.

## v1 Requirements

### Foundation & Data Model

- [x] **DATA-01**: Canonical opportunity record schema exists (title, company, location, remote_status, salary_low/high, role_link, source, source_type, access_date, fit_score, growth_score, confidence, tags, next_action, profile_gap, run_id, observed_at, lane)
- [x] **DATA-02**: Profile seed (role keyword groups + target-role taxonomy from Seif's profile) is stored as a local-only file, never exported
- [x] **DATA-03**: A persistent seen-role store (SQLite or JSONL) survives across runs
- [x] **DATA-04**: Module folder/layout follows NIZAM conventions, mirroring the MARSAD radar module placement
- [x] **DATA-05**: A dedicated append-only Career Radar ledger is registered with NIZAM (TEMPLE/known-ledgers) and privacy path-rules are added to PRIVACY_CLASSIFICATION

### Sourcing

- [x] **SRC-01**: System fetches opportunities from Tier 1 public ATS APIs (Greenhouse, Lever, Ashby, Workable) with no scraping
- [x] **SRC-02**: System fetches opportunities from Tier 2 public RSS/feeds (Remotive, We Work Remotely, RemoteOK) using stdlib parsing
- [x] **SRC-03**: Operator can manually import opportunities (e.g., from Outlier/DataAnnotation/Turing/Toloka) via a structured JSONL/paste path
- [x] **SRC-04**: Each fetched opportunity is normalized into the DATA-01 schema with source link, source type, and access date recorded
- [x] **SRC-05**: A blocked/failed source is logged (errors/blocked-sources list) and the run degrades gracefully instead of aborting
- [x] **SRC-06**: Sourcing targets remote-USD AI/data/AI-ops/coordination + analyst roles matched to Seif's role keyword groups

### Deduplication

- [x] **DEDUP-01**: Opportunities are normalized (title/company/location/URL canonicalization) into a dedup key
- [x] **DEDUP-02**: Exact + fuzzy matching (rapidfuzz) detects duplicates across sources within a run
- [x] **DEDUP-03**: Re-running the radar does not re-surface already-seen roles (seen-store consulted), with a freshness rule for genuine reposts

### Scoring, Salary & Tagging

- [x] **SCORE-01**: Every opportunity receives a deterministic 0–100 score using weights: fit 25, salary upside 20, growth 15, visa/remote feasibility 10, company strength 10, referral/application leverage 10, freshness 5, side-income 5
- [x] **SCORE-02**: Scoring applies penalties for no-evidence, scam risk, unclear pay, severe skill mismatch, and exploitative unpaid work
- [ ] **SCORE-03**: Profile fit is computed locally against the profile seed (no raw profile data leaves the machine)
- [ ] **SALARY-01**: Every salary claim is tagged with provenance (employer-posted / estimated / recruiter-stated / guide-based / community-reported) and a confidence level
- [ ] **SALARY-02**: When salary evidence is unclear, confidence is marked low and no exact number is invented (ranges only, with methodology)
- [ ] **TAG-01**: Each opportunity is tagged with one or more of: APPLY NOW / REFERRAL FIRST / WATCHLIST / PROFILE GAP / LOW CONFIDENCE / SIDE INCOME / RELOCATION BET / USD CASHFLOW
- [ ] **TAG-02**: Scam-prone or exploitative-unpaid platforms are flagged with a caution tag and reasoning

### Reports & Delivery

- [ ] **RPT-01**: A short, action-oriented daily Telegram report is produced (best opportunity, salary insight, main risk/gap, one recommended action) and contains no raw personal-profile data
- [ ] **RPT-02**: A full Google Drive evidence report is produced (date, run ID, sources searched, new/duplicate counts, top roles, salary evidence + confidence, fit/growth scores, feasibility, company strength, profile gaps, application route, next actions, evidence links, errors/blocked sources, Telegram summary, ledger IDs/paths)
- [ ] **RPT-03**: A risk/red-team (NAQD-style) note briefly explains attractive-but-risky top roles
- [ ] **DELIV-01**: The Telegram report is sent via the existing relay and the Drive report saved to the correct NIZAM Drive folder
- [ ] **DELIV-02**: Each run appends a record to the Career Radar ledger with run ID and saved file paths
- [ ] **DELIV-03**: On Telegram/Drive failure the system retries, and if it still fails prints the full unsaved output and marks the run incomplete (findings never silently dropped)

### Trigger & Run Control

- [ ] **RUN-01**: An operator-invoked on-demand run executes the full fetch→dedup→enrich→score→tag→report→deliver→ledger pipeline for the Remote USD lane
- [ ] **RUN-02**: Run output can be reviewed before/at delivery; a clean seam exists to add an unattended Hermes-cron daily slot later (built but inactive)

### Strategic Routing

- [ ] **ROUTE-01**: Findings affecting income/cashflow are connected to MAL; long-term strategy to TARIQ; weekly action items to MUNAWARA

### Validation

- [ ] **VAL-01**: A test run over a small real source subset confirms: extraction correct, salary confidence not fabricated, duplicates removed, Telegram readable, Drive saves, ledger written, rerun produces no duplicates, and no secrets/personal-profile details leak

## v2 Requirements

Deferred to future milestones. Tracked, not in current roadmap.

### Lanes
- **LANE-GCC-01**: Replicate the proven pipeline to the GCC lane (sources, feasibility, weights)
- **LANE-EU-01**: Replicate the proven pipeline to the Europe lane

### Automation & Depth
- **AUTO-01**: Enable unattended scheduled (Hermes cron) daily runs after validation sign-off
- **DEPTH-01**: Company-strength scoring from external signals
- **DEPTH-02**: Referral/leverage mapping (warm-intro suggestions)
- **DEPTH-03**: Visa/relocation feasibility deep-dive per region
- **SRC-BROWSER-01**: Tier 4 browser automation (Playwright/Apify) for sources not reachable via API/RSS/manual

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Auto-apply to jobs / auto-submit applications | Hard rule — no application without explicit per-action approval |
| Auto-message / auto-contact recruiters | Hard rule — destroys trust; referral-first flagging instead |
| Filling forms / using credentials / submitting personal data | Hard rule — never without explicit approval |
| Raw LinkedIn / resume / personal-profile data in public files or Telegram | Privacy — sensitive matching stays local/private |
| Fabricated exact salaries | Credibility — provenance + confidence or omit |
| Scraping anti-bot-protected boards (LinkedIn/Indeed/Glassdoor) | Legal/ToS + reliability — prefer APIs/ATS/RSS/manual |
| Unattended cron before validation | Safety — on-demand + review first |
| Real-time streaming alerts | Alert fatigue — daily digest model |
| Generic career advice | Drift — evidence-backed opportunities only; long-term guidance via MAL/TARIQ/MUNAWARA |
| Deleting/moving/overwriting existing NIZAM files | Safety — additive only |

## Traceability

Which phases cover which requirements. Populated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1: Foundation & Data Model | Complete |
| DATA-02 | Phase 1: Foundation & Data Model | Complete |
| DATA-03 | Phase 1: Foundation & Data Model | Complete |
| DATA-04 | Phase 1: Foundation & Data Model | Complete |
| DATA-05 | Phase 1: Foundation & Data Model | Complete |
| SRC-01 | Phase 2: Tier 1 ATS Sourcing | Complete |
| SRC-02 | Phase 3: Tier 2 RSS & Manual Sourcing | Complete |
| SRC-03 | Phase 3: Tier 2 RSS & Manual Sourcing | Complete |
| SRC-04 | Phase 2: Tier 1 ATS Sourcing | Complete |
| SRC-05 | Phase 2: Tier 1 ATS Sourcing | Complete |
| SRC-06 | Phase 3: Tier 2 RSS & Manual Sourcing | Complete |
| DEDUP-01 | Phase 4: Deduplication Engine | Complete |
| DEDUP-02 | Phase 4: Deduplication Engine | Complete |
| DEDUP-03 | Phase 4: Deduplication Engine | Complete |
| SCORE-01 | Phase 5: Scoring Engine | Complete |
| SCORE-02 | Phase 5: Scoring Engine | Complete |
| SCORE-03 | Phase 7: Tagging & Profile Matching | Pending |
| SALARY-01 | Phase 6: Salary & Confidence Discipline | Pending |
| SALARY-02 | Phase 6: Salary & Confidence Discipline | Pending |
| TAG-01 | Phase 7: Tagging & Profile Matching | Pending |
| TAG-02 | Phase 7: Tagging & Profile Matching | Pending |
| RPT-01 | Phase 8: Telegram Report | Pending |
| RPT-02 | Phase 9: Drive Evidence Report & Ledger | Pending |
| RPT-03 | Phase 9: Drive Evidence Report & Ledger | Pending |
| DELIV-01 | Phase 9: Drive Evidence Report & Ledger | Pending |
| DELIV-02 | Phase 9: Drive Evidence Report & Ledger | Pending |
| DELIV-03 | Phase 10: Delivery Continuity (Retry & Safety) | Pending |
| RUN-01 | Phase 11: On-Demand Trigger & NIZAM Wiring | Pending |
| RUN-02 | Phase 11: On-Demand Trigger & NIZAM Wiring | Pending |
| ROUTE-01 | Phase 12: Strategic Routing (MAL/TARIQ/MUNAWARA) | Pending |
| VAL-01 | Phase 13: Validation & Safety Sign-Off | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30 (100% coverage) ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-14*
*Last updated: 2026-06-14 after roadmap creation*
