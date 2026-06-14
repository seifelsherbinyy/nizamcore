# Feature Research: TARIQ Career Radar

**Domain:** Strategic career/income intelligence for remote USD opportunities
**Researched:** 2026-06-14
**Confidence:** HIGH (grounded in project constraints + ecosystem research)

## Feature Landscape

### Table Stakes (Users Expect These)

Features that differentiate strategic intelligence from a basic job-alert scraper. Missing these = product feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Opportunity source aggregation** | Must pull opportunities from multiple sources (job boards, ATS, community platforms); single-source systems are incomplete | MEDIUM | Supports Outlier, DataAnnotation, Turing, Toloka, Remotive, We Work Remotely, Wellfound, RemoteOK, Upwork, Contra, Braintrust. Prefer APIs/ATS/RSS over scraping per project constraint. |
| **Evidence discipline (source link + access date + source type)** | Every opportunity must be traceable to its original source; reproducibility + audit trail are non-negotiable for strategic use | MEDIUM | Opportunity data model: title, company, location, remote status, salary, role link, source, source type, access date, confidence, tag, next action, profile gap. |
| **Salary capture with provenance tag** | Raw salary data is useless without knowing its source (employer-posted vs. estimated vs. recruiter-stated vs. community-reported); low-confidence salaries must be labeled | MEDIUM | Tags: employer-posted, estimated, recruiter-stated, guide-based, community-reported. Never invent exact pay. Confidence score reflects data quality. |
| **Duplicate detection and deduplication** | Re-running the radar should not flood the user with repeated opportunities; seen-role store prevents alert fatigue and improves signal-to-noise | MEDIUM | Composite key: company + title + location + URL normalization. Fuzzy matching for near-duplicates above similarity threshold. Critical for repeated runs on same source set. |
| **Opportunity scoring (0–100 with transparent weights)** | Without ranking, users cannot prioritize high-value opportunities from noise. Scoring must be explainable, not black-box. | MEDIUM | Weights: profile fit 25%, salary upside 20%, growth 15%, visa/remote feasibility 10%, company strength 10%, referral leverage 10%, freshness 5%, side-income 5%. Penalties for no-evidence, scam risk, unclear pay, severe mismatch, exploitative unpaid work. |
| **Fit and growth scoring** | Two distinct scoring dimensions that inform decision-making: does it suit my current skills (fit) and does it offer career/income trajectory (growth) | MEDIUM | Both scored separately in the data model; both surfaced in scoring calculation. |
| **Opportunity tagging** | Semantic labels guide action without requiring the user to re-read full details. Tags are decision trees: APPLY NOW, REFERRAL FIRST, WATCHLIST, PROFILE GAP, LOW CONFIDENCE, SIDE INCOME, RELOCATION BET, USD CASHFLOW. | LOW | 8 distinct tags. Can have multiple per opportunity. Each tag signals a specific decision path. |
| **Daily Telegram report (short, action-oriented)** | Users expect a consumable summary: best opportunity, salary insight, main risk/gap, one recommended next action. Full data is in Drive; Telegram is the decision trigger. | MEDIUM | Format: <5 min read, <200 words. Top opp, salary insight, risk, recommended action. Template varies by findings (new roles vs. salary changes vs. company events). |
| **Full Drive evidence report** | Strategic decisions require audit trails. Drive report = annotated source evidence for every finding: sources searched, new/duplicate counts, top roles, salary evidence + confidence, fit/growth scores, feasibility, company strength, profile gaps, application route, next actions, evidence links, errors/blocked sources. | HIGH | Stored in Drive per NIZAM ledger rails. Contains full working links to sources and reasoning. Enables manual verification or follow-up research. |
| **Ledger tracking (JSONL append-only record)** | Evidence of every run: what was searched, what was found, when, what changed since last run. Enables replay and historical comparison. | LOW | Reuses existing `governor/ledger_writer.py` + NIZAM ledger structure. No rebuild needed. |
| **On-demand trigger (operator-invoked, not unattended cron)** | Live data + privacy gates warrant human review before automation. User controls when the radar runs and can review findings before Telegram hits. | LOW | Invoked by operator; output reviewed before Telegram/Drive. Scheduling deferred to v1.x. |
| **Profile seeding (role keywords + target-role taxonomy)** | Scoring fit requires understanding what roles the user is qualified for and what they want. Seed data stays strictly local/private. | LOW | Stored privately; not exposed in Drive/Telegram outputs. Used only for local scoring. Seif's profile: commercial planning, vendor/category management, brand specialist, BI/data analyst, AI operations, LLM evaluation roles. |
| **Source data integrity (no raw profile leakage, no credentials stored)** | Privacy rails must prevent exposure of Seif's personal profile, LinkedIn URL, resume content, or credentials in any output. Sensitive matching stays local. | MEDIUM | Reuses `PRIVACY_CLASSIFICATION` + `SYNC_POLICY` (strict_local = never leaves). Pre-commit leak guard validates. No credentials ever used in automation. |

### Differentiators (Competitive Advantage)

Features that set the career radar apart as strategic intelligence, not a generic job alert. These align directly with project's Core Value: "evidence-backed, scored opportunities enabling better career decisions, relocation optionality, and long-term positioning."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Salary upside scoring + evidence chain** | Most job alerts show posted salary. This radar quantifies upside (market rate vs. posted range) and traces where salary data came from (employer, recruiter, Glassdoor, BLS). Enables informed negotiation. | HIGH | Salary upside = percentile of estimated market rate vs. posted range. Evidence chain = source + confidence + date. Requires baseline salary research per role type (Outlier $50–$300/hr, DataAnnotation $15–$50/hr, etc. — sourced from Glassdoor, community guides). Confidence scoring prevents fabricated numbers. |
| **Company strength scoring** | Beyond "is it a real company?" — scores company financial stability, hiring velocity (growing/stable/contracting), team size, funding/exit potential, reputation in niche. Enables assessment of job security, upward trajectory, and strategic value of role. | MEDIUM | Sources: company pages, Crunchbase (for startups), Glassdoor sentiment, recent hiring patterns on job boards, LinkedIn headcount, public financial data. Weighted by recency. |
| **Referral/application leverage mapping** | Scores not just "does this match my skills" but "can I reference someone in my network / is there an internal champion / what's the warm intro path?" Referrals are 7–10x more likely to convert. | MEDIUM | Cross-references Seif's known network (LinkedIn connections, past colleagues, GitHub collaborators). Flags when internal referral exists. Flags when cold apply is the only path (lower score). Suggests warm-intro approaches. Reuses TARIQ persona reasoning for strategic fit. |
| **Freshness + market trend scoring** | Opportunities posted recently rank higher; same role re-posted multiple times signals either high churn or strong hiring. Trends in remote USD demand (AI/data analyst roles growing, traditional PM roles stable) inform career positioning. | MEDIUM | Tracks post date, re-post delta, hiring velocity per company. Flags if same role reappears after 30 days (possible churn). Aggregates trends per role type. |
| **Multi-dimensional growth scoring** | Not just "does this role pay more" but: skill development potential, domain expertise gain (AI/e-commerce/data), career ladder clarity (IC vs. manager track), optionality expansion (portable skills, network, relocation readiness). | MEDIUM | Scored across: technical skill gain, domain expertise, network quality, visa/relocation optionality, long-term earning potential. Used to recommend RELOCATION BET or WATCHLIST roles. |
| **Visa/remote feasibility assessment** | Every opportunity rated on: remote-first (async-friendly), time-zone tolerance (Egypt UTC+2), visa sponsorship need (if relocation), contractor vs. FTE status. Filters out opportunities that sound good but are operationally infeasible. | MEDIUM | Analyzes job description text for async indicators, geographic requirements, contractor-only language, visa willingness. Surfaces risks (UTC+1..UTC+8 mismatch, FTE-only in countries without remote hiring, etc.). |
| **Cross-pillar connection (income → MAL, strategy → TARIQ, actions → MUNAWARA)** | Links career radar findings to Seif's broader life system: high-income opportunities flow to MAL (income tracking); strategic decisions feed TARIQ (long-horizon planning); next actions queue in MUNAWARA (weekly execution). Creates coherence, not isolated alerts. | MEDIUM | Requires NIZAM multi-agent coordination. Outputs include MAL-formatted income records. TARIQ persona reasons about strategic fit. MUNAWARA gets action items. Deferred to v1.x but architecture must support it. |
| **Evidence links in outputs (Drive report + Telegram previews)** | Every claim (salary, company strength, growth potential) includes a clickable source link + access date + confidence tag. Users can verify or dig deeper. Builds trust in findings. | LOW | Drive report includes full evidence links. Telegram preview includes link to Drive report for full evidence chain. |
| **Side-income opportunity detection** | Flags gig/contract roles that can be combined into multiple-revenue-stream strategy (side stacking). Marks opportunities as SIDE INCOME if they're <20 hrs/week commitment, high hourly rate, low admin overhead. Targets side income potential 2x–3x salary equivalent over time. | MEDIUM | Analyzes role type (gig vs. FTE), time commitment language, hourly rate (if available). Flags flex/project-based work. Scores SIDE INCOME tag for opportunities compatible with full-time primary role. Gig economy trending toward 36% of workforce by 2026. |
| **Risk/red-team reasoning (NAQD hazim perspective)** | Not just "this is a good fit" but "here are the non-obvious risks: founder instability, remote-only role in startup, unclear equity terms, exploitative trial project, scam red flags." Briefly surfaces what NAQD (red-team/risk persona) flags as concerning. | MEDIUM | Requires NAQD persona reasoning. Scores scam risk, exploitative-unpaid-work penalties. Flags common scrapers/fake postings. Brief NAQD comment in top opportunities highlights non-obvious risks. |

### Anti-Features (Deliberately NOT Build)

Features that seem valuable on the surface but create problems. Explicitly excluded per project constraints and ecosystem pitfalls.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Auto-apply / auto-submit applications** | Saves user time; seems efficient. | Violates explicit project hard rule (no approval gates bypass). Credentials at risk. Increases noise to employers (mass applicants get ghosted). Reduces strategic positioning (referral > cold apply, 7-10x conversion uplift). Ethical issue: resume/profile data exposure. | Manual approval for each application. Flag "APPLY NOW" and "REFERRAL FIRST" opportunities; user initiates. Provide templated messages for warm intros. |
| **Auto-message recruiters / auto-contact outreach** | Seems like leverage; could surface more opportunities. | Violates hard rule (no recruiter auto-contact without approval). Destroys relationship trust (mass spam = professional reputation damage). Most valuable opportunities come via warm introductions, not cold recruiter messages. Legal risk (anti-spam regulations in EU/Canada; harassment risk in some jurisdictions). | Identify "REFERRAL FIRST" opportunities and flag internal champions. Suggest warm intro via mutual connection. Operator initiates contact if interested. |
| **Fabricated or estimated salary without confidence tags** | Tempting to provide "estimated market rate" for all roles to enable comparison. | Destroys credibility of entire system. User cannot distinguish employer-posted (high trust) from guess (low trust). Creates false confidence in scoring. Violates project evidence discipline rule. Users make bad decisions on invented numbers. | Every salary must have provenance tag (employer-posted, estimated, recruiter-stated, guide-based, community-reported) + confidence score. Low-confidence salaries flagged visibly. Never invent exact pay; state ranges + source + date only. |
| **Raw LinkedIn profile or resume exposure in Telegram/Drive** | Necessary for matching; seems useful to include. | Violates hard rule (no raw personal-profile data in public files). Privacy risk. Breaks SYNC_POLICY (strict_local data never leaves). Pre-commit hooks should catch and reject. Creates legal/compliance liability. | Sensitive matching stays strictly local/private. Drive and Telegram outputs contain only: anonymized fit score, skills gap analysis (generic, not LinkedIn-derived), recommended profile improvements (text only, no resume excerpts). |
| **Real-time streaming alerts (push notification on every new opportunity)** | Users might fear missing an opportunity if they don't get instant notification. | Creates alert fatigue + reduces signal-to-noise. Most opportunities are not time-critical (posting window is typically 2–4 weeks before role closes). Daily digest is sufficient and more strategic. Requires unattended cron + 24/7 monitoring (not approved for v1). | Daily Telegram report (3 fixed times: 09:00/15:00/21:00 Cairo via Hermes) + optional on-demand trigger. Digest format enables better decision-making than firehose. |
| **Predictive "you will get this job" scoring** | Tempting to build ML model that predicts success rate. | Training data is user-specific and sparse (Seif hasn't applied to 1000 jobs). Model would overfit or fabricate confidence. Users make worse decisions trusting false probabilities. Creates liability (user sues if "75% match" doesn't convert). | Honest scoring across fit, growth, company strength, leverage. Transparent weights. No binary "will you get hired" prediction. Frame as "strategic fit score" + "application leverage" + "next steps" — human decision. |
| **Subscription or paid-tier model** | Seems like revenue model. | Defeats project purpose (strategic intelligence for Seif, not a SaaS product). Monetization pressure creates perverse incentives: promoting high-margin opportunities, hiding risks, inflating scores to drive engagement. NIZAM is internal intelligence system, not commercialized product. | Build for Seif's needs only. No monetization. If value extends to others later, that's future consideration; don't distort intelligence now to support business model. |
| **Profile-matching via external APIs (e.g., LinkedIn candidate matching, third-party skill extraction)** | Richer data; seems like better matching. | Requires credentials or API keys; increases security risk. External APIs go down or change (brittleness). Data exposure risk (credentials + profile sent to third parties). Violates privacy-first principle (SYNC_POLICY). Over-reliance on external systems. | All matching local. Use profile seed (keywords + role taxonomy) stored privately. Extract skills from job description (not resume). Fuzzy-match against Seif's target roles. Simpler, more secure, fully in control. |
| **Generic career advice or "tips to improve your profile"** | Seems helpful; drives engagement. | Adds noise to strategic intelligence. Distracts from actual opportunity evaluation. Generic advice (e.g., "improve LinkedIn") is not actionable and often wrong for remote USD market. Creates false sense of value when core finding is negative. | Focus on specific, evidence-backed profile gaps discovered during opportunity research (e.g., "3 top roles require X certification — consider Y course"). Actionable, grounded, not generic. |
| **Scraping of anti-bot-protected job boards (e.g., LinkedIn, Indeed, with browser automation)** | Tempting to capture more data; competitors do it. | 3 of 5 LinkedIn scrapers got flagged/throttled in June 2026 testing; only 2 survived. Silent data corruption (18–22% ghost jobs, outdated listings). Legal risk (ToS violations, DMCA § 1201, unfair competition laws). Data quality issues when scraper breaks. | Prefer official APIs (Google Jobs API, company career pages via RSS, ATS platforms like Greenhouse/Lever/Ashby, saved-search exports from job boards). Least-privilege browser automation only if unavoidable (Upwork OAuth, Toloka API). Avoid LinkedIn/Indeed scraping entirely. |
| **Cron-scheduled unattended runs (before v1 validation)** | Seems efficient; why wait for operator approval? | Live data + privacy gates warrant human review before automation. Unsupervised execution increases risk of privacy leaks, credential misuse, scrapers breaking silently and corrupting data. Schedule after proving v1 pipeline on 10+ real runs with zero safety incidents. | On-demand trigger (operator-invoked) with output review before Telegram/Drive in v1. Cron scheduling deferred to v1.x after safety validation. |
| **Deleting or re-processing historical records (rewriting history)** | Seems clean; "let's recalculate scoring with new weights". | Violates project constraint (no deletion/move/overwrite). Breaks audit trail (ledger append-only). Undermines reproducibility. Prevents understanding of how recommendations changed over time. | Append-only ledger. New run with updated weights = new ledger entry. Keep old records. Enable comparison ("role X scored 65 in run 5, now 72 in run 10 due to salary update"). |
| **Form-filling or credential entry for automated application tracking** | Tempting to auto-fill applications to save time. | Hard rule violation (never submit personal data without explicit approval). ToS violations on most platforms. Credential storage is security risk. Creates liability if application is wrong or duplicated. | User enters credentials manually for each application. Radar flags "APPLY NOW" opportunities; user opens browser and applies. Lever/Greenhouse forms auto-filled by browser autofill (user controls). Zero credential storage in NIZAM. |

## Feature Dependencies

```
[Opportunity source aggregation (APIs/ATS/RSS)]
    └──requires──> [Source connectors with gating per source]
    └──requires──> [Evidence discipline infrastructure (source link + date + type)]
                       └──requires──> [Opportunity data model spec]
    └──requires──> [Duplicate detection + normalization]
                       └──enhances──> [Seen-role store]

[Salary capture with provenance]
    └──requires──> [Salary source tagging (employer/estimated/recruiter/guide/community)]
    └──requires──> [Confidence scoring (prevents fabrication)]
    └──enhances──> [Salary upside scoring (market rate vs. posted)]

[Opportunity scoring (0–100)]
    └──requires──> [Fit scoring (skills match)]
    └──requires──> [Growth scoring (career trajectory)]
    └──requires──> [Company strength scoring]
    └──requires──> [Profile seeding (role taxonomy, target roles)]
    └──requires──> [Salary upside scoring]
    └──requires──> [Visa/remote feasibility assessment]
    └──requires──> [Referral/leverage mapping]
    └──enhances──> [Opportunity tagging (tags reflect score ranges + fit)]

[Opportunity tagging]
    └──requires──> [Opportunity scoring (APPLY NOW when score >75, for example)]
    └──requires──> [Fit scoring to identify PROFILE GAP]
    └──requires──> [Side-income detection to tag SIDE INCOME]
    └──requires──> [Risk/red-team reasoning (NAQD) to tag and explain LOW CONFIDENCE]

[Daily Telegram report]
    └──requires──> [Opportunity aggregation + scoring]
    └──requires──> [Duplicate detection (no repeat-sends)]
    └──requires──> [Telegram delivery infrastructure (existing NIZAM relay)]
    └──enhances──> [Full Drive evidence report (Telegram links to full findings)]

[Full Drive evidence report]
    └──requires──> [All scoring + tagging dimensions]
    └──requires──> [Evidence links + source URLs]
    └──requires──> [Ledger tracking (run ID, date, completeness)]
    └──requires──> [Google Drive infrastructure (existing rclone-crypt ledger)]

[Cross-pillar connection (income → MAL, strategy → TARIQ, actions → MUNAWARA)]
    └──requires──> [Opportunity scoring + tagging]
    └──requires──> [Multi-agent coordination (Hermes personas)]
    └──enhances──> [Strategic intelligence (not just alerts)]

[Profile seeding (role keywords + target roles)]
    └──requires──> [Privacy classification (strict_local, never leaves)]
    └──enhances──> [Fit scoring]
    └──enhances──> [Referral/leverage mapping]

[Risk/red-team reasoning (NAQD)]
    └──requires──> [NAQD persona availability]
    └──enhances──> [Opportunity tagging (LOW CONFIDENCE)]
    └──enhances──> [Drive evidence report (risk explanation)]

[Referral/leverage mapping]
    └──requires──> [Profile seeding (known contacts)]
    └──requires──> [Company + role data from opportunities]
    └──enhances──> [Opportunity tagging (REFERRAL FIRST)]
    └──enhances──> [Drive evidence report (warm-intro suggestions)]

[Source data integrity (no profile leakage, no credentials)]
    └──requires──> [Privacy classification infrastructure (existing)]
    └──requires──> [Pre-commit leak guards]
    └──conflicts──> [External API matching (API keys, credentials)]
    └──conflicts──> [Auto-apply / auto-contact (credential storage)]
    └──conflicts──> [Raw resume/profile exposure (Drive/Telegram output)]
```

### Dependency Notes

- **Opportunity source aggregation requires Evidence discipline infrastructure:** Without source tracking (link + date + type), aggregated opportunities are untraceable and unverifiable.
- **Opportunity scoring requires multiple sub-dimensions:** Scoring cannot be monolithic. Fit (25%) depends on profile seeding. Growth (15%) and salary upside (20%) depend on independent research. Company strength (10%) requires separate analysis. Referral leverage (10%) depends on network mapping. Each dimension is independently scored, then combined.
- **Opportunity tagging requires completed scoring:** Tags (APPLY NOW, REFERRAL FIRST, etc.) are decision trees derived from score ranges and dimension-specific insights. Cannot generate tags without scoring first.
- **Daily Telegram report requires Duplicate detection:** Re-running the radar should not send the same opportunity twice to Telegram. Seen-role store is prerequisite.
- **Cross-pillar connection requires Multi-agent coordination:** Forwarding income records to MAL, strategic reasoning to TARIQ, actions to MUNAWARA all depend on existing NIZAM multi-agent infrastructure (Hermes). This is post-MVP but architecture must support it.
- **Profile seeding and Referral/leverage mapping enhance (but don't strictly require) each other:** Better profile seeding → better leverage mapping. But basic scoring works without either. Make profile seed v1 MVP, enhance with leverage mapping in v1.x.
- **Privacy/credentials conflict with external API matching, auto-apply, and profile exposure:** These are hard incompatibilities. Choosing privacy-first means accepting local-only matching and manual approval gates.
- **Source data integrity requires avoiding auto-apply / auto-contact:** Once credentials are stored for automation, privacy and safety guarantee fails.

## MVP Definition

### Launch With (v1 — Full-Depth Pipeline, Remote USD Lane Only, On-Demand)

Minimum viable product — proves the complete radar pipeline end-to-end with zero safety incidents.

- [ ] **Opportunity source aggregation (multi-source, no scraping)** — Remote USD opportunities from APIs/ATS/RSS (Outlier, DataAnnotation, Turing, Toloka career pages; Remotive, We Work Remotely, Wellfound, RemoteOK saved searches or APIs; Upwork OAuth; Braintrust API; Contra). Validates that pull architecture works. Target: ≥5 sources, ≥20 new opportunities per run.
- [ ] **Evidence discipline (source link + access date + source type)** — Every opportunity in Telegram and Drive includes clickable source link + timestamp + source platform tag. Users can verify. No exceptions.
- [ ] **Salary capture with provenance + confidence** — Every salary tagged (employer-posted, estimated, recruiter-stated, guide-based, community-reported). Confidence score (HIGH/MEDIUM/LOW) visible. Low-confidence salaries marked. Never invented numbers.
- [ ] **Opportunity data model** — Title, company, location, remote status, salary, role link, source, source type, access date, fit score, growth score, confidence, tag, next action, profile gap stored. Validates schema.
- [ ] **Duplicate detection** — Composite key (company + title + location + URL normalization). Seen-role store prevents same opportunity in multiple runs. Test: re-run 3x, should have zero repeats in Telegram.
- [ ] **Opportunity scoring (0–100 with weights)** — Profile fit 25%, salary upside 20%, growth 15%, visa/remote feasibility 10%, company strength 10%, referral leverage 10%, freshness 5%, side-income 5%. Penalties for no-evidence, scam, unclear pay, severe mismatch, exploitative unpaid. Transparent in Drive report.
- [ ] **Fit + growth scoring** — Two independent dimensions scored and surfaced separately. Users understand what each means.
- [ ] **Opportunity tagging (APPLY NOW / REFERRAL FIRST / WATCHLIST / PROFILE GAP / LOW CONFIDENCE / SIDE INCOME / RELOCATION BET / USD CASHFLOW)** — 8 tags. Rules-based logic (e.g., score >75 + fit good = APPLY NOW; fit <50 = PROFILE GAP). Tags visible in Telegram and Drive.
- [ ] **Daily Telegram report (action-oriented)** — <200 words, <5 min read. Best opportunity + score, salary insight, main risk/gap, one next action. Template-driven. Link to Drive report for full evidence. Test: 3 consecutive daily runs, Telegram text readable and actionable each time.
- [ ] **Full Drive evidence report** — Date, run ID, sources searched, new/duplicate counts, top 5 roles, salary evidence + confidence per opportunity, fit/growth/company strength scores, visa/remote feasibility for each, profile gaps identified, application route (apply now vs. referral first), next actions, evidence links, errors/blocked sources, Telegram summary, ledger IDs/paths. Formatted for human review (not raw JSON). Test: Drive report produced, saved, ledger written, all links valid.
- [ ] **Ledger tracking (append-only JSONL)** — Run record includes timestamp, sources searched, count of new/duplicate/errors, top opportunity (score, title, company), run ID, Telegram message ID, Drive file path. Enables replay and historical tracking.
- [ ] **On-demand trigger** — Operator-invoked (no cron). Output printed to console; operator reviews before Telegram/Drive execute. Prevents unsupervised privacy leaks.
- [ ] **Profile seeding (private, local-only)** — Role keywords and target role taxonomy stored locally (not in shared NIZAM files). Used only for scoring. Seif's profile: e-commerce/commercial/brand/vendor roles, BI/data analyst, AI ops, LLM eval. Test: fit score reflects target roles; off-target roles score low.
- [ ] **Privacy rails (no profile leakage, SYNC_POLICY compliance)** — All sensitive matching local/private. Telegram/Drive outputs contain no resume excerpts, LinkedIn URLs, or personal identifiers. Pre-commit hooks validate no secrets leak. Test: scan outputs with `git secrets`, pass.
- [ ] **Test pass on real source subset** — 10 consecutive runs on 3–4 real sources (Outlier career page, DataAnnotation, Remotive saved search). Validate: extraction correct, salary confidence not fabricated, dedup works, Telegram readable, Drive saves, ledger written, rerun has zero duplicates, zero secret/profile leak. All 10 runs must pass safety checks.

### Add After Validation (v1.x — Enhancements When MVP Proven Safe)

Features to add once core pipeline validated and no safety issues detected.

- [ ] **Salary upside scoring (market rate vs. posted)** — Baseline salary research per role type (Outlier: median $52/hr, range $50–$300/hr depending on expertise; DataAnnotation: $15–$50/hr, etc., sourced from Glassdoor, community guides). Score opportunities by percentile of market rate. Deploy only after salary data proven accurate for 5+ runs.
- [ ] **Company strength scoring** — Company financial stability, hiring velocity, team size, funding/exit potential, Glassdoor reputation. Added dimension to scoring. Requires Crunchbase/financials data source (evaluate APIs).
- [ ] **Referral/leverage mapping** — Cross-reference Seif's LinkedIn connections against companies in opportunities. Flag internal champions. Suggest warm intro paths. Requires LinkedIn API or manual export (evaluate privacy/legal constraints).
- [ ] **Risk/red-team reasoning (NAQD perspective)** — Brief red-team reasoning for top opportunities: founder instability, equity terms, trial project red flags, scam indicators. Requires NAQD persona integration (Hermes multi-agent).
- [ ] **Side-income opportunity detection and stacking** — Tag gig/contract roles compatible with multiple-revenue-stream strategy. Score side-income potential. Research community guides for "side stacking" best practices.
- [ ] **Visa/remote feasibility deep-dive** — Enhanced assessment: async-friendliness, time-zone tolerance, contractor vs. FTE, visa sponsorship appetite. Surfaces operational risks beyond "remote OK". Requires job description text analysis (NLP or rule-based).
- [ ] **Cross-pillar connection (income → MAL, strategy → TARIQ, actions → MUNAWARA)** — Wire top opportunities to MAL (income records), TARIQ (strategic reasoning), MUNAWARA (action queue). Requires multi-agent coordination. Deploy after MVP safety validation.
- [ ] **Cron-scheduled unattended runs (after safety validation)** — Move to 3x daily scheduled Telegram reports (09:00/15:00/21:00 Cairo). Requires ≥10 consecutive on-demand runs with zero safety incidents. Hermes cron integration (existing infrastructure).
- [ ] **Enhanced deduplication (fuzzy matching for near-duplicates)** — Current MVP uses exact composite key. v1.x adds fuzzy-match for titles that differ slightly ("LLM Evaluator" vs. "AI LLM Trainer") same company. Prevents subtle duplicates.

### Future Consideration (v2+ — Post-MVP, Multiple Lanes, Advanced Features)

Features to defer until product-market fit established and MVP pipeline proven on Remote USD lane.

- [ ] **GCC and Europe lanes** — Expand source set for Saudi/UAE/EU opportunities. Different salary bands, visa complexity, remote norms. Deferred until Remote USD pipeline fully stable.
- [ ] **Predictive success scoring** — ML model predicting conversion likelihood. Defer until Seif has 50+ applications with outcomes to train on. Too risky to deploy now.
- [ ] **Profile-matching via external APIs** — LinkedIn candidate matching, third-party skill extraction. Defer until privacy/security audit completes. Local-only matching sufficient for v1.
- [ ] **Scheduled cron runs with auto-publish** — Telegram auto-publish without operator review. Defer until ≥20 runs with zero safety incidents. Manual review gate required for v1 and v1.x.
- [ ] **Monetization or subscription model** — If future value extends beyond Seif, consider. Not a goal in v1 (internal intelligence system, not SaaS).
- [ ] **Real-time streaming alerts** — Push notifications on new opportunities. Defer; daily digest sufficient. Real-time creates alert fatigue without strategic value.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Notes |
|---------|------------|---------------------|----------|-------|
| Opportunity source aggregation (APIs/ATS/RSS) | HIGH | HIGH | P1 | MVP blocker; defines "complete radar" |
| Evidence discipline (source link + date + type) | HIGH | MEDIUM | P1 | Non-negotiable for strategic use |
| Salary capture + provenance | HIGH | MEDIUM | P1 | Core value prop; prevents fabrication |
| Duplicate detection | HIGH | MEDIUM | P1 | Prevents alert fatigue + enables reruns |
| Opportunity scoring (0–100) | HIGH | HIGH | P1 | Enables prioritization |
| Fit + growth scoring | HIGH | MEDIUM | P1 | Two key decision dimensions |
| Opportunity tagging | HIGH | LOW | P1 | Decision trees; guides action |
| Daily Telegram report | HIGH | MEDIUM | P1 | Delivery mechanism; consumer-facing |
| Full Drive evidence report | HIGH | MEDIUM | P1 | Audit trail for strategic decisions |
| Ledger tracking | MEDIUM | LOW | P1 | Reproducibility + historical tracking |
| On-demand trigger + review gate | MEDIUM | LOW | P1 | Privacy safety gate |
| Profile seeding (local/private) | MEDIUM | LOW | P1 | Enables fit scoring |
| Privacy rails (SYNC_POLICY compliance) | HIGH | MEDIUM | P1 | Hard rule; non-negotiable |
| Salary upside scoring (market rate vs. posted) | HIGH | MEDIUM | P2 | High value; deferred until confidence in salary data |
| Company strength scoring | MEDIUM | MEDIUM | P2 | Adds richness; not MVP-blocking |
| Referral/leverage mapping | HIGH | HIGH | P2 | Strategic value (7–10x conversion); high impl cost |
| Risk/red-team reasoning (NAQD) | MEDIUM | MEDIUM | P2 | Surfaces non-obvious risks; requires persona integration |
| Side-income detection | HIGH | MEDIUM | P2 | Aligns with career positioning; deferred |
| Visa/remote feasibility assessment | HIGH | MEDIUM | P2 | Filters infeasible opportunities; deferred |
| Cross-pillar connection (MAL/TARIQ/MUNAWARA) | HIGH | MEDIUM | P2 | Strategic coherence; requires multi-agent coordination |
| Enhanced deduplication (fuzzy matching) | MEDIUM | MEDIUM | P2 | Prevents subtle duplicates; not critical for v1 |
| Cron-scheduled unattended runs | MEDIUM | LOW | P2 | Efficiency; deferred until safety validation |

**Priority Key:**
- **P1 (Must Have for v1 Launch):** Core MVP pipeline. Validates full end-to-end. Proves safety and evidence discipline.
- **P2 (Should Have, Add in v1.x):** High-value features. Deferred until MVP safety validated. Unlock after ≥10 clean runs.
- **P3 (Nice to Have, v2+):** Future expansion. Not blocking. Deferred until multiple lanes, proven scaling, or new constraints arise.

## Feature Comparison: Strategic Radar vs. Basic Job Alert Scraper

| Dimension | Basic Job Alert Scraper | TARIQ Career Radar (Strategic Intelligence) | Our Approach |
|-----------|------------------------|---------------------------------------------|--------------|
| **Data sources** | 1–2 primary boards (Indeed, LinkedIn); supplements with scraping | Multiple platforms (APIs/ATS/RSS preferred); deliberate, curated sources | Outlier, DataAnnotation, Turing, Toloka, Remotive, Wellfound, We Work Remotely, Upwork, Braintrust, Contra. Prefer APIs/ATS/RSS; avoid scraping. |
| **Salary handling** | Raw posted salary only; single data point | Multiple salary sources with provenance tags (employer, estimated, recruiter, guide, community); confidence scoring; upside analysis | Employer-posted (HIGH), estimated vs. guide (MEDIUM), community/recruiter (LOW). Confidence visible. Never invented. |
| **Scoring/ranking** | None, or simplistic keyword match | Multi-dimensional (fit 25%, salary 20%, growth 15%, feasibility 10%, company 10%, leverage 10%, freshness 5%, side-income 5%); transparent weights; penalty framework | Explainable scoring. Users understand each dimension. Can challenge each weight. |
| **Duplicate handling** | Frequent duplicates; re-sends same role weekly | Composite key deduplication; seen-role store prevents repeats even across sources | Title + company + location + URL normalization. Fuzzy match for near-duplicates. Zero repeats in Telegram. |
| **Opportunity tagging** | None, or generic categories | Semantic action tags: APPLY NOW, REFERRAL FIRST, WATCHLIST, PROFILE GAP, LOW CONFIDENCE, SIDE INCOME, RELOCATION BET, USD CASHFLOW | 8-tag taxonomy. Rules-based logic. Each tag = decision trigger. |
| **Evidence/audit trail** | Links, if any, are not curated; no metadata | Every opportunity: source link + access date + source type + confidence. Full evidence report in Drive for manual verification. | Full source traceability. Users verify findings. Supports strategic review. |
| **Fit assessment** | Keyword matching (generic) | Profile-seeded target-role taxonomy. Fit score vs. growth score vs. feasibility. Identifies profile gaps explicitly. | Fit score (25%). Growth score (15%). Feasibility assessment (10%). Gap identification in Drive report. |
| **Company strength** | None | Company growth trajectory, stability, hiring velocity, reputation, team size | Scores company separately. Added to composite score. |
| **Referral leverage** | None | Flags if warm intro exists; suggests referral-first path; scores referral likelihood | Flags internal champions. Suggests warm intro. Boosts score for referral-viable opportunities. |
| **Risk/red-team reasoning** | None | Brief red-team perspective: founder instability, exploitative projects, scam red flags | NAQD persona reasons about risks. Tags LOW CONFIDENCE with explanation. |
| **Delivery** | Email digest or push alerts (usually noisy) | Telegram report (short, action-oriented) + full Drive evidence report + ledger record | Telegram (daily 3x) for decision trigger. Drive for full audit trail. Ledger for historical tracking. |
| **Privacy/safety** | Often leaks personal data; no credential gates | Privacy-first: no profile exposure, no credentials stored, SYNC_POLICY compliance, pre-commit leak guards | All sensitive matching local. No resume excerpts in outputs. Pre-commit validation. Zero credential storage. |
| **Approval gates** | None; fully automated | On-demand trigger; operator review before Telegram/Drive publish; no auto-apply or recruiter contact | Manual activation. Output review before delivery. Approval required per application. |

## Sources

### Career Intelligence & Opportunity Scoring
- [11 Top Talent Intelligence Platforms Transforming Hiring (2026)](https://www.hackerearth.com/blog/talent-intelligence-platforms) — Scoring models, matching frameworks
- [AI Opportunity Scoring: Tools, Models & Results (2026)](https://prospeo.io/s/ai-opportunity-scoring) — Weighted scoring methodologies
- [Guide to Company Growth Opportunities for 2026 Success](https://www.sixpathsconsulting.com/company-growth-opportunities/) — Company strength assessment
- [2026 Talent Management Trends: 12 Trends Shaping the Future of Work](https://www.phenom.com/blog/talent-management-trends) — Growth trajectory and opportunity discovery

### Salary Data & Evidence
- [9 Top Remote Job Boards of 2026](https://scale.jobs/blog/9-best-remote-job-boards-for-2025) — Salary data accuracy and provenance
- [LinkedIn Salary Insights 2026: Find & Compare Pay](https://connectsafely.ai/articles/linkedin-salary-insights-guide) — Salary confidence and source types
- [Outlier AI vs DataAnnotation.tech: Which Pays More in 2026?](https://remotestack.in/blog/outlier-ai-vs-dataannotation-which-pays-more) — AI evaluation role salary evidence

### Application & Referral Strategy
- [Guide to Referral Strategies That Get Interviews in 2026](https://www.jobwizard.ai/blog/guide-to-referral-strategies-that-get-interviews-in-2026) — Referral leverage (7–10x conversion uplift)
- [Why Referrals Beat Cold Applications](https://jobrecruiterdirectory.com/why-referrals-beat-cold-applications/) — Referral vs. cold apply effectiveness

### Job Scraping & Data Quality Pitfalls
- [I Tested 5 LinkedIn Job Scrapers (2026): 3 Got Flagged, 2 Survived](https://applyarc.com/blog/linkedin-job-scraper-tools) — Anti-bot detection escalation; scraper failure modes
- [Job Scraping: Build a Pipeline, Not a Bot](https://www.olostep.com/blog/job-scraping) — Silent data corruption; structural brittleness
- [State of Web Scraping 2026: Trends, Challenges & What's Next](https://www.browserless.io/blog/state-of-web-scraping-2026) — 18–22% ghost jobs; ToS violations; legal risks
- [Job Posting Data Aggregation: Multi-Source Guide for 2026](https://www.promptcloud.com/blog/job-posting-data-aggregation/) — Deduplication and normalization frameworks

### Side Income & Multiple Revenue Streams
- [25 Best Side Hustles You Can Do Remotely in 2026](https://dailyremote.com/advice/best-remote-side-hustles-2026) — Gig economy growth (36% of workforce by 2026); side-stacking trends
- [2026 Gig Economy Trends for Freelancers and Self-Employed Workers](https://carry.com/learn/gig-economy-trends-for-freelancers-and-self-employed-workers) — Gig economy $674B market by 2026

### Job Market & Career Trends
- [Skills, Trust and 2026: Fixing the Employer–Worker Divide](https://www.indeed.com/lead/employers-are-out-of-touch-job-seekers-are-over-it-what-now?co=US) — Candidate value drivers beyond salary (flexibility, growth, impact)

### Privacy & Data Governance
- Project constraint: NIZAM SYNC_POLICY, PRIVACY_CLASSIFICATION, HIMAYAH egress audit — references to internal governance standards

---
*Feature research for: TARIQ Career Radar (Remote USD lane, v1)*
*Researched: 2026-06-14*
*Confidence: HIGH (grounded in project constraints + ecosystem research + precedent from MARSAD radar pattern)*
