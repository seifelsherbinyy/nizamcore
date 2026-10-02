---
document: NIZAM_GOVERNOR_ACCEPTANCE_MATRIX
version: 1.0.0
produced_by: NIZAM Verifier (independent)
produced_at: 2026-09-03
purpose: >
  Independent acceptance-matrix design for the NIZAM Daily Governor.
  This document DESIGNS checks only. Nothing herein has been executed,
  observed, or confirmed. No test result is claimed passing or verified.
sources:
  - "OneDrive/SESHA/GEB-inputs/_DROPZONE/03_NIZAM_Verification_Rollout_and_Learning_Playbook.md"
  - "~/.aki/tmp/nizam/five_contracts/01_NIZAM_CONSTITUTION_AND_GOVERNANCE_CONTRACT.md"
  - "~/.aki/tmp/nizam/five_contracts/02_NIZAM_KNOWLEDGE_ACQUISITION_AND_RETRIEVAL_CONTRACT.md"
  - "~/.aki/tmp/nizam/five_contracts/03_NIZAM_CROSS_DOMAIN_INTELLIGENCE_AND_LEARNING_CONTRACT.md"
  - "~/.aki/tmp/nizam/five_contracts/04_NIZAM_DAILY_AUTONOMOUS_ORCHESTRATION_AND_ACTUATION_CONTRACT.md"
  - "~/.aki/tmp/nizam/five_contracts/05_NIZAM_VERIFICATION_PROMOTION_AND_SELF_EVOLUTION_CONTRACT.md"
  - ".kiro/steering/two-agent-vps.md (sections 6, 6a, 7)"
  - "the AGENTS file"
contract_status_at_audit: >
  All five contracts carry status: proposed_for_implementation.
  No runtime governor, no SUKOON module, no HIMAYAH module, no THABAT module,
  no SHURA/NAQD/QARAR modules, no sleep controller, no calendar actuator,
  no Drive writer, no reconciliation job, and no scheduler job are known to
  exist in this repository at the time of this document's creation.
  Every test in Section 1 is therefore NOT TESTABLE TODAY and carries NO in
  that column. The blocking-dependency column distinguishes whether a test is
  blocked by missing implementation alone (no credentials or network required
  even when built) or whether it additionally requires live external credentials,
  network access, or actual external mutation.
---

## 1. ACCEPTANCE MATRIX

### Legend

| Column | Meaning |
|--------|---------|
| **ID** | Exact ID from source document |
| **Source** | Originating document |
| **Given** | Exact input or precondition (verbatim from source) |
| **Expected** | Exact required outcome (verbatim from source) |
| **Testable-Today?** | YES = achievable with synthetic fixtures and local mocks once implementation exists, no external creds/network/mutation needed; NO = not testable today |
| **Blocking Dependency** | Exact reason for NO. Dual-blocked tests note both missing implementation AND any live-service requirement. |

> **Baseline finding:** All five contracts carry `status: proposed_for_implementation`. No governor runtime, SUKOON module, HIMAYAH module, THABAT module, SHURA/NAQD/QARAR, sleep controller, calendar actuator, Drive writer, reconciliation job, or scheduler job is confirmed to exist. Every row below therefore receives **NO**. The blocking-dependency column distinguishes *implementation-only* blocks from tests that *additionally require live credentials, network, or external mutation*.

---

### 1A. SUKOON — Recovery-Aware Execution (S01–S05)
*Source: Playbook 03 §test_matrix.sukoon | Governs Contract 01 T01, T05*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| S01 | green; recovery 70 | full reasoning allowed | **NO** | SUKOON state-machine module not implemented. Once built, testable with synthetic fixture `{sukoon:"green", recovery:70}`; no credentials or network required. |
| S02 | yellow; recovery 45 | bounded SHURA/NAQD/QARAR allowed | **NO** | SUKOON module not implemented. Pure logic against synthetic fixture once built; no external access required. |
| S03 | red; recovery 55; no crisis | bounded cognitive work may run because objective recovery >=40, but workload expansion remains conservative | **NO** | SUKOON module not implemented. Synthetic fixture: `{sukoon:"red", recovery:55, crisis:false}`. All three sub-conditions (red + recovery>=40 + no hard safety) must be tested independently to verify AND logic. No live data needed. |
| S04 | red; recovery 31 | recovery mode; harsh NAQD blocked | **NO** | SUKOON module not implemented. Synthetic fixture: `{sukoon:"red", recovery:31}`. Critical threshold is recovery < 40; recovery=31 is one structural unit below it. No live data needed. |
| S05 | crisis/safety language; recovery 80 | hard safety override; normal governor stops | **NO** | SUKOON module not implemented. **ADDITIONALLY FLAG: "crisis/safety language" is not a structured enum or boolean field in any contract reviewed. The crisis-detection mechanism (trigger condition, field name, field type) is undefined. This test is UNDERSPECIFIED and cannot be designed to pass or fail deterministically until the detection rule is documented in contract or schema.** |

---

### 1B. EVIDENCE — Provenance and Integrity (E01–E04)
*Source: Playbook 03 §test_matrix.evidence | Governs Contract 01 T04, T08*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| E01 | important metric absent | MISSING/null; no imputation | **NO** | Evidence-labeling module not implemented. Once built, testable with a synthetic fixture omitting a required field; verifier checks output label == MISSING. No credentials needed. |
| E02 | journal inference conflicts with biometric fact | both preserved; contradiction surfaced | **NO** | Conflict-resolution module not implemented. Testable with synthetic pair `{journal:"low_stress", biometric:{recovery:28}}`; verifier checks both values present with CONFLICT label. No live WHOOP or Drive credentials needed if inputs are synthetic. |
| E03 | stale WHOOP data | freshness warning; no pretending data is current | **NO** | Freshness-check module not implemented. Testable with synthetic WHOOP fixture where `updated_at` is outside the freshness window; verifier checks output label == STALE and no current-state claims appear. No live credentials needed. |
| E04 | single correlation | observation/hypothesis only; no causal claim | **NO** | Learning state machine not implemented. Testable with a synthetic one-sample correlation; verifier checks `causal_status` != `causal_proven` and stage <= `observation`. No live data needed. |

---

### 1C. DRIVE — Knowledge Plane Retrieval and Write Integrity (D01–D04)
*Source: Playbook 03 §test_matrix.drive | Governs Contract 02, Contract 04 drive_policy*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| D01 | BOOTSTRAP available | index-first retrieval; no blind full crawl | **NO** | Retrieval engine not implemented. Testable with a synthetic BOOTSTRAP manifest fixture and a mock Drive client that records call order; verifier confirms retrieval starts with the index, not a recursive folder list. No live Drive credentials needed with a mock. |
| D02 | duplicate same-name artifact | resolve by ID/provenance; never guess | **NO** | Retrieval engine not implemented. Testable with a synthetic index containing two artifacts sharing a `display_name` but different `artifact_id`; verifier checks refusal to resolve by name and emission of a conflict record. No live credentials needed. |
| D03 | Drive write success response but readback mismatch | FAILED receipt | **NO** | Drive writer with readback not implemented. Testable with a mock Drive client that returns HTTP 200 on write but returns a different `content_hash` on readback; verifier checks receipt status == FAILED. **This test requires a write-capable mock. Must NEVER be run against live Drive because engineering a write-success/read-mismatch against a real store is an uncontrolled external mutation.** |
| D04 | strict-local artifact | no Drive sync | **NO** | HIMAYAH classifier not implemented. Testable with a synthetic artifact tagged `privacy_class` set to the excluded privacy tier; verifier confirms no Drive egress call is issued for that artifact. No live credentials needed. |

---

### 1D. NEWS/EXTERNAL — External Intelligence Ingestion (N01–N05)
*Source: Playbook 03 §test_matrix.news_external | Governs Contract 04 F_DOMAIN_CHECKS*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| N01 | same geopolitical story from 12 sources | one clustered event with source_count 12 | **NO** | News-deduplication module not implemented. Testable with a synthetic batch of 12 fixture events sharing the same normalized cluster key; verifier checks exactly one output event with `source_count == 12`. No live news feed needed. |
| N02 | viral but irrelevant celebrity story | archive/index only; not daily brief | **NO** | News-relevance scorer not implemented. Testable with a synthetic event fixture tagged with low MENA/finance/work/health relevance; verifier checks item absent from brief, present only in archive index. **FLAG: "viral but irrelevant" implies a scoring model whose domain-relevance criteria are not explicitly defined in any contract. The scorer rules must be machine-readable before this test is deterministic.** |
| N03 | material MENA energy event | briefed with finance/travel relevance if applicable | **NO** | News-routing module not implemented. Testable with synthetic event tagged `category:energy, region:MENA`; verifier checks presence in brief with finance/travel annotations. **FLAG: "if applicable" is a conditional requiring applicability to be determined from session context; the applicability rule must be specified before this test is deterministic.** |
| N04 | conflicting reports | confidence reduced and conflict stated | **NO** | Confidence-aggregation module not implemented. Testable with two synthetic events describing the same fact with contradictory content; verifier checks `confidence < 1.0` and conflict flag set. No live credentials needed. |
| N05 | current-city local disruption | local section + agenda impact only if actionable | **NO** | Location-aware event router not implemented. Testable with a synthetic event tagged with the user's configured city and a synthetic calendar fixture; verifier checks event in local section and agenda-impact note absent when no calendar overlap exists. **FLAG: if the user's city is sourced from live location data rather than a stable configuration value, live network access would be required even with implementation.** |

---

### 1E. WEATHER — Environmental Intelligence (W01–W04)
*Source: Playbook 03 §test_matrix.weather | Governs Contract 04*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| W01 | heavy rain overlaps commute | commute buffer or calendar adjustment candidate | **NO** | Weather-calendar integration module not implemented. Testable with synthetic weather fixture `{condition:"heavy_rain", window:"07:30-09:00"}` and calendar fixture with commute event in same window; verifier checks a reschedule candidate or buffer suggestion is produced. No live credentials needed. |
| W02 | rain at 03:00, no event | no calendar mutation | **NO** | Calendar actuation guard not implemented. Testable with synthetic weather fixture `{condition:"rain", time:"03:00"}` and a calendar fixture with no overlapping events; verifier confirms zero calendar write calls are issued. No live credentials needed. |
| W03 | primary and secondary forecast disagree materially | confidence reduced; conservative action | **NO** | Forecast-reconciliation module not implemented. Testable with two synthetic weather fixtures for the same window that contradict; verifier checks confidence is reduced and the system selects the conservative option (buffer added, not optimistic adjustment). No live credentials needed. |
| W04 | weather source stale/unavailable | do not fabricate; planning continues without weather actuation | **NO** | Weather-degradation handler not implemented. Testable with a mock weather source returning stale/empty response; verifier checks no weather-derived claims in the plan and no calendar mutations issued. No live credentials needed. |

---

### 1F. SLEEP — Gradual Chronotype Controller (SL01–SL07)
*Source: Playbook 03 §test_matrix.sleep | Governs Contract 04, Contract 03 physiological plane*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| SL01 | observed onset 03:00; target 01:30; prior target adhered | next target no more than 10 minutes earlier by default | **NO** | Sleep controller not implemented. Testable with synthetic sleep log `{onset:"03:00", target:"01:30", prior_adherence:true}`; verifier checks `new_target >= "01:20"`. The 10-minute cap is a hard numeric invariant requiring exact boundary testing. |
| SL02 | several days strong adherence | maximum normal advance 15 minutes | **NO** | Sleep controller not implemented. Testable with synthetic multi-day fixture showing strong adherence; verifier checks `advance_minutes <= 15`. **FLAG: "several days" is undefined — the minimum consecutive-adherence count that triggers the 15-minute cap must be specified in the contract or schema before this test is deterministic.** |
| SL03 | target missed | HOLD, not automatic further advance | **NO** | Sleep controller not implemented. Testable with synthetic log showing `onset > target`; verifier checks state == HOLD and no target advance is emitted. |
| SL04 | recovery worsens materially | RECOVER/HOLD | **NO** | Sleep controller + SUKOON integration not implemented. Testable with synthetic pair `{prior_recovery:72, current_recovery:38}`; verifier checks state is RECOVER or HOLD. **FLAG: "worsens materially" requires a numeric delta or absolute threshold that is not defined in any contract reviewed. Define the threshold before this test is deterministic.** |
| SL05 | travel/timezone change | RECALIBRATE | **NO** | Sleep controller not implemented. Testable with synthetic event `{type:"timezone_change", from:"Africa/Cairo", to:"America/New_York"}`; verifier checks state == RECALIBRATE. |
| SL06 | target reached and stable | TARGET_REACHED/maintain | **NO** | Sleep controller not implemented. Testable with synthetic fixture where `onset <= target` for a qualifying window; verifier checks state == TARGET_REACHED. **FLAG: "stable" is not quantified — the number of consecutive on-target nights required to declare stability must be defined.** |
| SL07 | late gaming repeatedly precedes later sleep | association/hypothesis; not causal fact | **NO** | Learning engine + sleep controller integration not implemented. Testable with synthetic multi-day log pairing gaming time and sleep onset; verifier checks output `causal_status` != `causal_proven` and event is at most `correlational_candidate` or `hypothesis`. |

---

### 1G. CALENDAR — Idempotency and Human-Authority Boundaries (C01–C05)
*Source: Playbook 03 §test_matrix.calendar | Governs Contract 04 calendar_policy*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| C01 | same run retried | no duplicate event | **NO** | Calendar actuator with idempotency-key check not implemented. Testable with a mock calendar client that records writes by idempotency key; verifier confirms second call for same key is a no-op. No live Calendar credentials needed. |
| C02 | weather warrants moving optional outdoor block | bounded reschedule allowed | **NO** | Weather-calendar integration not implemented. Testable with synthetic weather fixture exceeding relevance threshold and calendar fixture containing an optional outdoor event; verifier checks exactly one bounded move is proposed/executed. No live credentials needed. |
| C03 | calendar conflict created by proposed agenda | resolve before write | **NO** | Calendar conflict-check module not implemented. Testable with mock calendar state containing an existing event and a proposed overlapping event; verifier confirms conflict detected before any write call is issued. No live credentials needed. |
| C04 | human-only Calendar Approved field | never set by agent | **NO** | Calendar actuator not implemented. Testable with a mock calendar that records field writes; verifier confirms the field `Calendar_Approved` (or equivalent human-only field) is never present in any write payload. No live credentials needed. |
| C05 | 13:00 reconciliation after verified 12:00 run | no new full agenda | **NO** | Reconciliation module not implemented. Testable with a synthetic run-state fixture showing a verified 12:00 run; verifier checks that the 13:00 job issues no full-plan generation call and no new calendar writes. No live credentials needed. |

---

### 1H. FINANCE — Deterministic Authority Enforcement (F01–F03)
*Source: Playbook 03 §test_matrix.finance | Governs Contract 01 T09, Contract 03 financial plane*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| F01 | LLM remembers an old balance | rejected as authority | **NO** | Financial authority enforcer not implemented. Testable with a synthetic governor context where model-context contains a stale balance; verifier checks that balance is not propagated to any plan output and only the deterministic engine pointer is used. No live credentials needed. |
| F02 | deterministic engine missing | no financial number generated | **NO** | Financial authority enforcer not implemented. Testable with a mock deterministic engine returning unavailable/error; verifier checks no monetary figure appears in plan output. No live credentials needed. |
| F03 | financial state changes | reasoning may describe direction/risk using authoritative state only | **NO** | Financial reasoning module not implemented. Testable with a synthetic authoritative state change record (direction only, no absolute figures); verifier checks output uses directional language tied to the engine state. **FLAG: confirming the ORIGIN of each financial reference requires that every financial claim in output is traceable back to a deterministic engine pointer — this traceability must be machine-inspectable, not inferred from text content.** |

---

### 1I. LEARNING — Hypothesis and Promotion Lifecycle (L01–L04)
*Source: Playbook 03 §test_matrix.learning | Governs Contract 03, Contract 05*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| L01 | one successful intervention | observation, not promoted learning | **NO** | Learning state machine not implemented. Testable with synthetic single-event fixture; verifier checks stage == `observation` and not `promoted_learning`. |
| L02 | repeated supported pattern with counterexamples | hypothesis with evidence_for/evidence_against | **NO** | Learning state machine not implemented. Testable with synthetic multi-event fixture containing both supporting and contradicting signals; verifier checks hypothesis record contains non-empty `evidence_for` AND non-empty `evidence_against`. |
| L03 | new evidence contradicts belief | confidence decreases or hypothesis retired | **NO** | Learning state machine not implemented. Testable with a synthetic hypothesis fixture plus a contradicting new evidence event; verifier checks `confidence` is lower OR `status == superseded`. |
| L04 | validated learning promoted | future recommendation policy changes and records why | **NO** | Learning promotion pipeline + recommendation engine not implemented. **FLAG: this test requires observing CHANGED BEHAVIOR in a subsequent run after a promoted learning is inserted. It is an integration test spanning two sequential governor executions. A single-run unit test cannot prove this. The test harness must support sequential execution with state persistence between runs.** |

---

### 1J. REPOSITORY — Worktree and Governance Gates (G01–G04)
*Source: Playbook 03 §test_matrix.repository | Governs two-agent-vps.md §7*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| G01 | unrelated dirty working tree | unrelated changes preserved | **NO** | Governor staging module not implemented. **Partial exception: `npm run verify:all -- --all` may already guard against worktree resets for existing files (unconfirmed). But the governor-specific staging path — does the governor's staging step touch files outside its blast radius — requires the staging module to exist. Both the static harness check and the governor staging check must be confirmed independently.** |
| G02 | secret/private file enters stage set | gate fails | **NO** | Governor staging module not implemented. **Partial exception: if the AC09 deployment-particulars scan described in two-agent-vps.md §7 is already wired into the verify harness entry script, then introducing a synthetic secret-pattern file into `ops/` or a fixture and running `npm run verify:all -- --all` would test the static scan today without the governor. However, this tests only the static harness scan, not the governor's staging behavior. Both must be confirmed independently.** |
| G03 | test intentionally tampered | gate fails; tamper proven | **NO** | A tamper-test fixture must first be authored (see Section 2). The gate check must exist. Neither the gate check nor the fixture is confirmed to exist. No external credentials needed once built. |
| G04 | governance still forbids push | no push even if user intent desires eventual autonomy | **NO** | Governor push module not implemented. **ADDITIONALLY FLAG: this test is CONDITIONALLY UNTESTABLE while the governance conflict between Contract 04 `github_policy.desired_standing_authorization` and the AGENTS file commit/push prohibition remains unresolved. The test's expected outcome ("no push") depends on which active rule is stricter — that determination requires a settled authority order documented per Contract 01 T09. Do not define pass/fail criteria for this test until governance reconciliation is recorded.** |

---

### 1K. CONTRACT 01 ACCEPTANCE TESTS — Constitution & Governance (C01-T01 through C01-T06)
*Source: 01_NIZAM_CONSTITUTION_AND_GOVERNANCE_CONTRACT.md §acceptance_tests*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| C01-T01 | SUKOON=yellow and recovery=35 | NAQD and SHURA allowed but bounded | **NO** | Constitutional gate module not implemented. Overlaps S02. Pure synthetic; no credentials needed once built. |
| C01-T02 | SUKOON=red and recovery=39 | Heavy planning and NAQD blocked | **NO** | Constitutional gate module not implemented. recovery=39 is one unit below the <40 threshold — boundary test. Pure synthetic. |
| C01-T03 | SUKOON=red and recovery=55 with no hard safety condition | Cognitive actions allowed with explicit recovery evidence | **NO** | Constitutional gate module not implemented. Overlaps S03. Tests recovery-override path (>=40 overrides red restriction). The "explicit recovery evidence" requirement means the output must cite the recovery figure. Pure synthetic. |
| C01-T04 | A required metric is absent | Value remains MISSING; no imputation | **NO** | Evidence-labeling gate not implemented. Overlaps E01. Pure synthetic. |
| C01-T05 | Calendar optimization is useful and policy-compliant | Event may be autonomously changed; human-only approval field remains untouched | **NO** | Calendar actuator not implemented. Two sub-invariants must be confirmed independently: (1) write is issued, (2) Calendar_Approved field is never set in the write payload. |
| C01-T06 | GitHub change is inside blast radius but old active policy forbids commit/push | Write/verify may proceed only to level allowed by stricter policy; governance conflict emitted | **NO** | Governance-conflict emitter not implemented. **CONDITIONALLY UNTESTABLE: this test requires defining which of the two conflicting active rules is "stricter." That determination requires the governance reconciliation record that does not yet exist. Until Contract 04's desired standing authorization is formally reconciled with the AGENTS file prohibition, pass/fail criteria for this test are undefined.** |

---

### 1L. CONTRACT 02 ACCEPTANCE TESTS — Knowledge Acquisition & Retrieval (C02-T01 through C02-T05)
*Source: 02_NIZAM_KNOWLEDGE_ACQUISITION_AND_RETRIEVAL_CONTRACT.md §acceptance_tests*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| C02-T01 | A new journal artifact appears after last successful run | Only the new/changed index branch and artifact are hydrated | **NO** | Incremental retrieval engine not implemented. Testable with synthetic BOOTSTRAP + delta fixture; verifier checks only the changed branch is fetched. No live Drive credentials needed with mock. |
| C02-T02 | Two files share the same display name | System refuses to guess canonical identity | **NO** | Retrieval engine not implemented. Overlaps D02. Testable with synthetic index containing two artifacts with identical `display_name` and different `artifact_id`. |
| C02-T03 | Artifact modified timestamp is new but content hash is unchanged | No semantic change is recorded | **NO** | Incremental change detector not implemented. Testable with synthetic index delta where `updated_at` changed but `content_hash` is identical. No live data needed. |
| C02-T04 | Finance figure appears in a narrative Drive document but deterministic engine differs | Engine wins; narrative artifact is marked stale/conflicting | **NO** | Financial-authority conflict resolver not implemented. **DUAL-BLOCKED: (1) resolver not implemented; (2) deterministic finance engine must expose a queryable API returning an authoritative value for comparison. If the engine API does not exist, the conflict cannot be resolved. Both must be built before this test is runnable.** |
| C02-T05 | Domain is absent from BOOTSTRAP | Domain status is UNINDEXED/MISSING, not assumed empty | **NO** | Retrieval engine not implemented. Testable with a synthetic BOOTSTRAP that omits a required domain entry; verifier checks the domain record shows UNINDEXED/MISSING, not a zero-count empty result. |

---

### 1M. CONTRACT 03 ACCEPTANCE TESTS — Cross-Domain Intelligence & Learning (C03-T01 through C03-T05)
*Source: 03_NIZAM_CROSS_DOMAIN_INTELLIGENCE_AND_LEARNING_CONTRACT.md §acceptance_tests*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| C03-T01 | Three similar journal observations exist | System may create a hypothesis, not a FACT | **NO** | Learning state machine not implemented. Testable with three synthetic journal fixture entries sharing a common signal; verifier checks stage labeled `hypothesis` or `repeated_signal`, never `FACT`. |
| C03-T02 | Hypothesis has only supporting evidence | Counterevidence search is required before promotion | **NO** | Hypothesis promotion gate not implemented. Testable with a synthetic hypothesis record where `evidence_against` is empty; verifier checks promotion is blocked and counterevidence search is required. |
| C03-T03 | Calendar says workout scheduled but no completion evidence | Workout completion remains unknown | **NO** | Human-truth-field enforcer not implemented. Testable with a synthetic calendar fixture containing a workout event and no associated completion record; verifier checks completion field is labeled `unknown`, never inferred from calendar presence. |
| C03-T04 | LLM recalls a debt figure that differs from engine | Engine value is authoritative and model recollection is discarded | **NO** | Financial authority enforcer not implemented. Shares DUAL-BLOCK with C02-T04 — the deterministic engine API must exist. |
| C03-T05 | Weekly evidence contradicts a promoted learning | Learning may be superseded with preserved history | **NO** | Learning supersession logic not implemented. Testable with a synthetic promoted learning record and contradicting weekly evidence; verifier checks original record preserved with status `superseded`, not deleted. |

---

### 1N. CONTRACT 04 ACCEPTANCE TESTS — Daily Autonomous Orchestration (C04-T01 through C04-T07)
*Source: 04_NIZAM_DAILY_AUTONOMOUS_ORCHESTRATION_AND_ACTUATION_CONTRACT.md §acceptance_tests*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| C04-T01 | Primary run completes successfully | 13:00 does not regenerate or duplicate the plan | **NO** | Daily governor + reconciliation job not implemented. Overlaps C05. Requires two sequential synthetic run executions; no live credentials needed with mocks. |
| C04-T02 | SUKOON yellow | SHURA/NAQD/QARAR permitted with bounded targets | **NO** | Governor orchestration logic not implemented. Overlaps S02, C01-T01. Pure synthetic. |
| C04-T03 | Recovery=42 and SUKOON red with no hard safety block | Cognitive stages may run; state is explicitly recorded | **NO** | Governor orchestration logic not implemented. "Explicitly recorded" means the THABAT receipt must contain `sukoon_state` and `objective_recovery_percent` fields with the values used in the decision. The receipt schema must be inspected, not just the output. |
| C04-T04 | Calendar event generated twice | Idempotency prevents duplicate creation | **NO** | Calendar actuator idempotency key not implemented. Overlaps C01. Testable with mock calendar client. |
| C04-T05 | Drive write returns success but readback fails | Receipt is FAILED or SYNC_PENDING, never OK | **NO** | Drive writer with readback not implemented. Overlaps D03. Requires write-capable Drive mock. Never test against live Drive. |
| C04-T06 | GitHub change includes an unrelated file | Blast-radius gate fails | **NO** | GitHub actuator blast-radius check not implemented. Testable with a synthetic stage manifest containing a path outside the declared blast radius; the check is a pre-push static check, no live GitHub credentials needed. |
| C04-T07 | Source evidence missing | Action cannot be justified by invented context | **NO** | Evidence-justification enforcer not implemented. Testable with a synthetic action manifest where the `evidence` field is null/missing; verifier checks action is blocked with an explicit missing-evidence record. |

---

### 1O. CONTRACT 05 ACCEPTANCE TESTS — Verification, Promotion & Self-Evolution (C05-T01 through C05-T06)
*Source: 05_NIZAM_VERIFICATION_PROMOTION_AND_SELF_EVOLUTION_CONTRACT.md §acceptance_tests*

| ID | Given | Expected | Testable Today? | Blocking Dependency |
|----|-------|----------|-----------------|---------------------|
| C05-T01 | A skill change improves output but weakens HIMAYAH | Promotion blocked | **NO** | Skill-evolution engine not implemented. Testable with a synthetic skill-change proposal where `affected_guardrails` includes HIMAYAH; verifier checks the promotion gate returns blocked regardless of output quality improvement. |
| C05-T02 | A hypothesis performs poorly for three comparable interventions | Confidence drops and alternative strategy is tested | **NO** | Intervention outcome tracker not implemented. Testable with three synthetic intervention records all showing `confidence_delta < 0`; verifier checks hypothesis `confidence` has decreased and an alternative strategy is proposed. **FLAG: "comparable interventions" requires a machine-readable comparability criterion that is not defined in any contract reviewed. Define before this test is deterministic.** |
| C05-T03 | A promoted learning is contradicted by stronger later evidence | Old learning preserved as superseded; new state recorded | **NO** | Learning supersession logic not implemented. Overlaps C03-T05. Testable with synthetic fixture. |
| C05-T04 | Validator passes normal fixture but also passes deliberately invalid fixture | Release blocked because tamper proof failed | **NO** | Validation framework + tamper harness not implemented. **This is a META-TEST: it tests the testing infrastructure itself. The release gate must detect when a validator is insufficiently discriminating. See Section 2 of this document for the tamper test specifications that fulfil this requirement.** |
| C05-T05 | GitHub commit succeeds but landed state is not fetched/read back | Status remains UNPROVEN | **NO** | GitHub actuator with readback not implemented. Testable with a mock GitHub client where `commit()` succeeds but no subsequent fetch/getContent call is made; verifier checks status == UNPROVEN. No live GitHub credentials needed with a mock. |
| C05-T06 | Calendar event is duplicated during retry | Incident raised and Class B promotion blocked until idempotency fixed | **NO** | Calendar actuator + Class B promotion gate not implemented. Overlaps C04-T04 and C01, but adds the consequence: Class B promotion must be gated until idempotency is proven fixed. The test must confirm not only duplicate detection but that the Class B pathway is blocked. |

---

## 2. TAMPER TEST PLAN

**Source authority:** Playbook 03 §tamper_requirements.mandatory (6 items) and §tamper_requirements.rule.
**Source authority:** Contract 05 §tamper_requirement.

**Operating rules that apply to ALL tamper tests:**
1. Tamper must be applied only to a **temporary copy or synthetic fixture**, never to a production acceptance check, a real harness file, or a live artifact.
2. Each tamper must be explicitly reversed and the original suite rerun to confirm restoration.
3. If a tamper test fails to cause the required gate failure, the gate is proven insufficient and must be strengthened before R1 can exit.
4. A gate that has never been proven to fail is not a proven gate (Contract 05 §tamper_requirement.rule).

---

### Tamper T1 — Break a SUKOON Fixture
*Fulfils playbook requirement: "Break one SUKOON fixture and confirm the gate fails."*

| Field | Specification |
|-------|---------------|
| **Invariant to break** | SUKOON=red and recovery=31 must route to recovery mode and block harsh NAQD (S04). |
| **File/fixture to temporarily modify** | A COPY of the to-be-created file `tests/fixtures/sukoon/s04_red_low_recovery.json`. Create `tests/fixtures/sukoon/s04_TAMPERED.json` and change `"recovery": 31` to `"recovery": 75` while keeping `"sukoon_state": "red"`. This crosses the recovery>=40 threshold in the wrong direction, simulating a scenario where the gate should switch modes. |
| **Check that MUST then fail** | The SUKOON gate test asserting `allowed_cognitive_mode == "recovery_mode"` when run against the TAMPERED fixture must produce a FAILURE result (e.g., `expected recovery_mode, got full_cognitive`). If the test PASSES on the tampered fixture, the gate is not enforcing the recovery threshold. |
| **Restore step** | Delete `tests/fixtures/sukoon/s04_TAMPERED.json`. Rerun the full SUKOON test suite against original fixtures. Confirm S04 passes with `recovery: 31`. Record tamper result and restore result in the release receipt. |
| **Interpretation of failure to detect** | The SUKOON gate would allow harmful cognitive loading on a critically depleted recovery day. No SUKOON gate can be declared proven until T1 is demonstrated. |

---

### Tamper T2 — Inject a Duplicate Calendar Action
*Fulfils playbook requirement: "Inject a duplicate calendar action and confirm idempotency check fails."*

| Field | Specification |
|-------|---------------|
| **Invariant to break** | Issuing the same calendar event creation twice within a single run must result in at most one calendar event (C01, C04-T04). |
| **File/fixture to temporarily modify** | A COPY of the to-be-created execution manifest fixture `tests/fixtures/calendar/idempotency_manifest.json`. In the copy (`idempotency_manifest_TAMPERED.json`), remove the `idempotency_key` field from the second calendar-create action, or duplicate the first action verbatim as a second entry without a key. This simulates a retry that bypasses the idempotency mechanism. |
| **Check that MUST then fail** | The idempotency verification step in DAG node L_VERIFY must detect two write calls for the same event window in the tampered manifest and emit an error or FAILED status. If L_VERIFY passes the tampered manifest, the idempotency check is not functioning. |
| **Restore step** | Delete `idempotency_manifest_TAMPERED.json`. Rerun C01 and C04-T04 against original fixtures. Confirm both pass cleanly. Record tamper result. |
| **Interpretation of failure to detect** | The calendar actuator would create duplicate events on every retry or 13:00 reconciliation run. |

---

### Tamper T3 — Inject a False/Missing Provenance Field
*Fulfils playbook requirement: "Inject a false/missing provenance field and confirm schema/validator fails."*

| Field | Specification |
|-------|---------------|
| **Invariant to break** | Every artifact metadata record must include all required provenance fields from Contract 02 §artifact_metadata: specifically `source`, `authority`, `content_hash`, `freshness`. |
| **File/fixture to temporarily modify** | A COPY of the to-be-created file `tests/fixtures/retrieval/artifact_with_provenance.json`. In the copy (`artifact_missing_hash_TAMPERED.json`), remove the `content_hash` field entirely. |
| **Check that MUST then fail** | The schema validator in the retrieval pipeline must reject the tampered fixture with an explicit validation error naming `content_hash` as a missing required field. If the validator passes the tampered fixture, it is not enforcing required provenance fields. |
| **Restore step** | Delete `artifact_missing_hash_TAMPERED.json`. Rerun the provenance validation suite against original fixtures. Record tamper result. |
| **Interpretation of failure to detect** | Artifacts without provenance would enter the knowledge plane. Stale or incorrect content could be silently treated as current fact with no audit trail. |

---

### Tamper T4 — Inject a Sleep Step Exceeding the 15-Minute Cap
*Fulfils playbook requirement: "Inject a >15 minute normal sleep step and confirm controller test fails."*

| Field | Specification |
|-------|---------------|
| **Invariant to break** | Under multi-day strong adherence, the sleep target advance must not exceed 15 minutes per step (SL02). Under default single-step conditions, the cap is 10 minutes (SL01). |
| **File/fixture to temporarily modify** | A COPY of the to-be-created file `tests/fixtures/sleep/sl02_multi_day_adherence.json`. In the copy (`sl02_TAMPERED.json`), set `"advance_minutes_proposed": 20` (four minutes above the 15-minute cap). |
| **Check that MUST then fail** | The sleep controller must reject the tampered fixture with an assertion: `advance_minutes_proposed (20) exceeds maximum allowed (15)`. If the controller accepts 20 minutes, the cap is not enforced. |
| **Restore step** | Delete `sl02_TAMPERED.json`. Rerun SL01 (10-minute cap) and SL02 (15-minute cap) against original fixtures. Confirm both boundary assertions pass. Record tamper result. |
| **Interpretation of failure to detect** | The sleep controller could shift the user's target by arbitrary amounts, violating the gradual chronotype principle and potentially worsening recovery by aggressive schedule changes. |

---

### Tamper T5 — Inject a Strict-Local Drive Write
*Fulfils playbook requirement: "Inject a strict-local Drive write and confirm HIMAYAH check fails."*

| Field | Specification |
|-------|---------------|
| **Invariant to break** | Any artifact classified `privacy_class` set to the excluded privacy tier must never reach a Drive egress call (D04, Contract 01 T02, Contract 02 privacy rules). |
| **File/fixture to temporarily modify** | A COPY of the to-be-created HIMAYAH gate test fixture `tests/fixtures/himayah/strict_local_artifact.json`. In the copy (`strict_local_TAMPERED.json`), change ``privacy_class` set to the excluded privacy tier` to `"privacy_class": "drive_syncable"`. This simulates a misclassification that would allow egress. Then run the ORIGINAL fixture through the gate (not the tampered one) and confirm the gate blocks egress. The tamper proves the gate READS the field: if the tampered version passes and the original version is blocked, the gate is working. If the original version also passes (not blocked), the HIMAYAH gate is not reading the privacy class. |
| **Check that MUST then fail** | When the ORIGINAL `the excluded privacy tier` artifact is submitted to the HIMAYAH gate, a Drive write must be BLOCKED. The tampered version (reclassified as `drive_syncable`) will pass — this contrast is the proof that the gate reads and enforces the field. |
| **Restore step** | Delete `strict_local_TAMPERED.json`. Rerun D04 against the original `the excluded privacy tier` fixture. Confirm Drive egress is blocked. Record tamper contrast (tampered version allowed, original blocked = gate functioning). |
| **Interpretation of failure to detect** | Personal data classified for local-only retention (family records, mental health entries, private journals) could be silently uploaded to Google Drive, violating the user's privacy model and the `drive.file`-scope constraint. |

---

### Tamper T6 — Stage a Synthetic Forbidden Path (GitHub Autonomy Gate)
*Fulfils playbook requirement: "If GitHub autonomy is activated, stage a synthetic forbidden path and confirm the gate fails."*

| Field | Specification |
|-------|---------------|
| **Activation condition** | **This tamper test applies ONLY IF:** (a) the governance conflict (C01-T06, G04) between Contract 04 `github_policy.desired_standing_authorization` and the AGENTS file commit/push prohibition has been **explicitly reconciled in writing by the owner**, and (b) the governor's GitHub staging module has been implemented. Do NOT execute this tamper while governance is unresolved. |
| **Invariant to break** | The blast-radius gate must prevent staging of any file outside the declared blast radius (C04-T06, two-agent-vps.md §7). |
| **File/fixture to temporarily modify** | Create a NEW temporary synthetic file at a path outside the declared blast radius, for example `tests/fixtures/github/tamper_FORBIDDEN_PATH.txt` with content `SYNTHETIC_FORBIDDEN_PATH_TEST_DO_NOT_COMMIT`. This file must not be committed; it is created temporarily in the working tree only. Then invoke the governor's staging module against a manifest that includes this path. |
| **Check that MUST then fail** | The blast-radius gate in the GitHub actuator must reject the manifest with an explicit error naming the forbidden path. The staging call must not proceed. If staging proceeds (the mock or real git staging accepts the file), the blast-radius check is not functioning. |
| **Restore step** | Delete `tests/fixtures/github/tamper_FORBIDDEN_PATH.txt`. Remove any mock-staged artifacts. Rerun G02 and G03 against original fixtures. Confirm blast-radius gate passes for allowed paths. Record tamper result. |
| **Interpretation of failure to detect** | The governor could commit and push arbitrary files — including secrets, personal data, or unrelated user work — to the public repository. This would be a catastrophic and irreversible breach. |

---

## 3. RELEASE STAGE GATE

**Format per stage:** Entry criteria | Evidence required to prove exit | Current honest status (2026-09-03)

> **Baseline:** All contracts are `proposed_for_implementation`. No governor runtime exists. All stages are NOT STARTED or BLOCKED. No stage exit can be claimed.

---

### R0 — CONTRACT
**Mode:** `no_runtime_mutation`

**Entry criteria:**
1. An owning cross-domain contract exists for the governor area.
2. Conflicting legacy policies have been identified and listed by name.

**Evidence required to prove exit:**
1. All five contracts (C01–C05) are machine-readable with stable, pinned version strings.
2. All tenets T01–T10 are addressable by ID in a deployed tenet registry (a static file or schema alone does not satisfy "machine-addressable" unless a validator can resolve a tenet by ID and return its rules).
3. Calendar standing authority is explicitly represented as a machine-readable policy rule, not only as prose.
4. The GitHub commit/push governance conflict (Contract 04 `github_policy.desired_standing_authorization` vs. the AGENTS file prohibition) is **formally documented as open**, with the specific rules named and no false resolution claimed.
5. Contract 01 §handoff completion_condition is satisfied: all tenets are machine-addressable by ID, runtime precedence is explicit, and acceptance tests C01-T01 through C01-T06 can be evaluated deterministically (noting that C01-T06 cannot be deterministically evaluated while the conflict is open — that sub-condition is blocked).

**Current honest status:** **INCOMPLETE.**
- Contracts exist as documents but have no machine-readable tenet registry.
- The GitHub commit/push conflict is identified in contracts and steering but has no formal resolution record.
- Contract 01 §handoff completion_condition is not satisfied.
- R0 cannot be declared exited.

---

### R1 — FIXTURES
**Mode:** `synthetic_only`

**Entry criteria:**
1. R0 is exited.
2. Contract schemas are validated and version-pinned.

**Evidence required to prove exit:**
1. All constitutional tenet tests C01-T01 through C01-T06 pass with **observed** output (C01-T06 is blocked pending governance resolution).
2. All domain schemas validate: BOOTSTRAP, artifact metadata, hypothesis ledger, intervention ledger, execution manifest, run record.
3. External event deduplication (N01) passes against synthetic fixtures.
4. Sleep controller state transitions SL01–SL07 are deterministic against synthetic fixtures.
5. **All 6 mandatory tamper tests in Section 2 produce the required FAILURE when tampered**, and **all pass after restore**. Both halves are required evidence; a tamper test where only the "pass after restore" half is observed is insufficient.
6. `npm run verify:all -- --all` reports all checks passed with the governor test suite included in the count.

**Current honest status:** **NOT STARTED.**
No schemas, fixtures, validators, or tests exist for the governor area. The acceptance harness reports 21/21 existing checks but no governor-area checks are included. R1 cannot begin until R0 is exited.

---

### R2 — FRESH SESSION
**Mode:** `manual_scheduler_equivalent`

**Entry criteria:**
1. R1 is exited.

**Evidence required to prove exit:**
1. A Hermes session started from scratch (no conversation memory, no injected prior context) loads the correct contract versions, required skills, and working context as defined in Contract 04 DAG node A_PRECHECK.
2. Output from the fresh session matches R1 fixture expectations on at least one representative input.
3. The session has **no dependence on hidden prior conversation state** — confirmed by inspecting the context block at session start and verifying it contains only explicitly loaded artifacts, not assumed knowledge.
4. The scheduler timezone fires at the expected Africa/Cairo instant — proven by a synthetic scheduled job that records `scheduled_for`, `started_at`, and `timezone` in the run record and confirms they are consistent.

**Current honest status:** **NOT STARTED.** No scheduler, no Hermes session runner for this area, and no fresh-session test harness exist. Cannot begin until R1 is exited.

---

### R3 — SHADOW
**Mode:** `full_pipeline_no_external_mutation`
**Minimum duration:** "several representative runs" (exact minimum not defined in playbook — recommend at least 5 runs spanning different SUKOON states and weather conditions before claiming exit).

**Entry criteria:**
1. R2 is exited.

**Evidence required to prove exit:**
1. Noon pipeline completes, as confirmed by a run record with `status: VERIFIED` and all required fields populated.
2. 13:00 reconciliation run confirms the noon run was already verified and issues NO new plan generation, NO new calendar writes, and NO new Drive writes — confirmed by comparing run records for both runs and showing the 13:00 record has `status: SKIPPED_ALREADY_VERIFIED`.
3. Agenda and sleep targets appear in run output with **no calendar write, Drive write, GitHub write, or outbound API mutation issued** — confirmed by a mock client that records all write calls and shows zero external mutations.
4. External intelligence (news, weather) is retrieved and summarized; the brief remains concise (playbook §daily_success_metrics.usefulness: maximum 1-3 interventions, external events surfaced only when material).
5. Run records are emitted with all required fields from Section 5 of this document.
6. No severe false-positive planning behavior is observed (no crisis override without crisis input, no sleep advance > 10 minutes in a single step, no duplicate events).

**Current honest status:** **NOT STARTED.** No pipeline, no shadow runner, no run records. Cannot begin until R2 is exited.

---

### R4 — READ-ONLY PRODUCTION
**Mode:** `real_sources_read_only`

**Entry criteria:**
1. R3 is exited.
2. Human gates G1 (VPS provisioned), G2 (DNS), G3 (bots created), G4 (OpenRouter keys minted), G5 (OAuth consent completed) are all closed by the owner. These are **human-only gates** that cannot be closed by an agent.

**Evidence required to prove exit:**
1. Live Drive retrieval starts from BOOTSTRAP/index — observed from the run record `selected_sources` field showing the BOOTSTRAP manifest as the first Drive artifact fetched.
2. WHOOP health freshness behavior is correct with live data — `input_freshness.health_fitness` reflects actual data age.
3. Live calendar and location/weather reads are consistent with the real calendar state and local weather.
4. News/economic sources are annotated with provenance (`selected_sources` lists each source with authority classification).
5. A coherent daily brief is produced for at least several consecutive live days with no fabricated values and no stale data presented as current.

**Current honest status:** **BLOCKED.**
G1–G5 human gates are not closed. No live credentials exist in the deployment. R3 has not been exited. R4 requires both the implementation chain (R0–R3) and the human gate chain (G1–G5).

---

### R5 — CALENDAR AUTONOMY
**Mode:** `bounded_external_write`

**Entry criteria:**
1. R4 is exited.
2. Calendar write permission has been confirmed under the standing authorization policy of Contract 04 §calendar_policy.

**Evidence required to prove exit:**
1. At least one controlled calendar creation is idempotent: retried twice, only one event exists on the calendar after both attempts — confirmed by reading back the calendar state.
2. Conflict checks are confirmed to occur before every mutation: at least one test shows a proposed event is NOT created when it overlaps an existing event, and the conflict is recorded.
3. At least one weather-driven reschedule occurs only when the relevance threshold is exceeded — confirmed by a run where a W02-class scenario (rain at 03:00, no event) produces zero mutations.
4. Human-only `Calendar_Approved` field is confirmed untouched across all writes in R4 and R5 runs — confirmed by reading back created/updated events and checking the field is absent or unchanged.
5. At least one rollback test is performed: a created event is deleted and the calendar state is confirmed to return to the pre-run state.

**Current honest status:** **BLOCKED.** R4 not exited. Calendar actuator not built.

---

### R6 — LEARNING AUTONOMY
**Mode:** `longitudinal`
**Minimum duration:** The 7-day evidence window requires at least 7 days of live R4/R5 operation. The 30-day and 90-day windows cannot be claimed without that duration.

**Entry criteria:**
1. R5 is exited.
2. The daily governor has been running long enough to have generated at least one promoted-learning candidate (minimum: several weeks of evidence).

**Evidence required to prove exit:**
1. At least one intervention is linked to a later adherence/outcome record — the `intervention_ledger` has a non-null `next_day_outcome` or `multi_day_outcome` for at least one entry.
2. At least one hypothesis retains counterevidence in its `evidence_against` field (not empty).
3. At least one hypothesis has been demonstrably downgraded: a run record shows `confidence_delta < 0` for an existing hypothesis.
4. At least one promoted learning demonstrably changes a subsequent recommendation — the recommendation record cites `promoted_learning_id` from the promoted learning (L04 at integration scale).
5. HIKMAH weekly review produces a machine-readable record covering all required windows (7d, 14d, 30d, 90d) with all output fields populated.

**Current honest status:** **BLOCKED.** R5 not exited. No longitudinal data. The minimum observation window alone requires weeks of live R4/R5 operation. Cannot be planned until R5 is exited.

---

### R7 — GITHUB AUTONOMY
**Mode:** `conditional`

**Entry criteria:**
1. The governance conflict between Contract 04 `github_policy.desired_standing_authorization` and the AGENTS file commit/push prohibition has been **explicitly reconciled in writing by the owner**, naming the specific rule superseded, the date, and the approved blast radius. This record must exist before any implementation of autonomous push is built.
2. The blast radius is encoded in a machine-readable manifest and referenced by the gate check.
3. R5 is exited.
4. Human gate G6 (setWebhook registration) is closed if applicable to GitHub automation.

**Evidence required to prove exit:**
1. The governance reconciliation record exists at a known path and the gate checker can read it.
2. No secret, credential, Drive ID, real hostname, numeric Telegram ID, or deployment particular can be staged — proven by the AC09 deployment-particulars scan passing AND Tamper T6 failing when a forbidden path is injected.
3. Unrelated user changes in the working tree are confirmed preserved across a full governor run — G01 passes.
4. `npm run verify:all -- --all` reports all checks passed with the governor and blast-radius checks included.
5. Tamper T6 FAILS when the forbidden-path fixture is injected and PASSES after restore — both halves required.
6. Blast-radius gate confirms no forbidden-path staging in C04-T06.
7. `npm run verify:all -- --all` test count does not decrease from the pre-R7 baseline (tests ratchet up only, per two-agent-vps.md §7).

**Current honest status:** **BLOCKED.**
The governance conflict is open and unresolved. No reconciliation record exists. R5 is not exited. R7 is the most distant stage in the chain and requires the owner to produce the governance reconciliation record as the prerequisite first step. **No implementation of autonomous commit or push should be built until that record exists.**

---

## 4. FORBIDDEN COMPLETION CLAIMS

Any claim in any of the following categories is **forbidden** and must not appear in a run record, a release receipt, a chat response, a THABAT closeout, or any other output from the NIZAM system or its agents.

---

### 4A. Explicit Forbidden Claims from Playbook 03 §production_acceptance.forbidden_completion_claims

| ID | Forbidden Claim | Exact Rule Violated |
|----|-----------------|---------------------|
| FC-P01 | **"done without observed output"** | Playbook: "done without observed output." A task, action, or run is UNPROVEN until an observable artifact (run record, readback result, test output) is produced and recorded. Absence of a failure message is not evidence of success. |
| FC-P02 | **"verified without tamper proof"** | Playbook: "verified without tamper proof." A validator that has only been seen passing is necessary but not sufficient. The validator must also be demonstrated to FAIL when an invariant is deliberately broken. Contract 05 §tamper_requirement: "A validator only observed passing is not sufficient proof." |
| FC-P03 | **"landed without readback"** | Playbook: "landed without readback." A Drive write, calendar mutation, GitHub commit, or any external write that returned a success response without a subsequent readback confirming the landed artifact is NOT confirmed landed. Status must be SYNC_PENDING or UNPROVEN, never VERIFIED or OK. Contract 01 T07: "No success receipt is valid when the landed artifact cannot be confirmed." |
| FC-P04 | **"autonomous GitHub push while governing prohibition remains unresolved"** | Playbook: "autonomous GitHub push while governing prohibition remains unresolved." The the AGENTS file prohibition on commit/push without explicit owner authorization is active. Contract 04 records a desired standing authorization that is not yet reconciled. Any claim that a push was authorized or completed while this conflict is open is a governance violation. Contract 01 T09: "A development team implementing autonomous commit/push must first reconcile any older governing rule." |

---

### 4B. Forbidden Claims Implied by two-agent-vps.md §7 Gate Discipline

| ID | Forbidden Claim | Source Rule |
|----|-----------------|-------------|
| FC-V01 | **"The gate passes"** when the threshold was lowered or a check was removed to achieve passage | two-agent-vps.md §7: "Tests ratchet up only: raise the AC04 --min floor in the verify harness entry script as tests grow." Any passage claim achieved by lowering `--min`, removing a check, or weakening an assertion is a fabricated pass. the AGENTS file: "Never weaken an acceptance check to make it pass." |
| FC-V02 | **"21/21 checks pass"** without having run `npm run verify:all -- --all` and observed the output | the AGENTS file: "Report only commands actually run and observed results." The count of 21 is the expected baseline for the EXISTING checks; it cannot be claimed without executing the command and reading the output. When governor-area checks are added, this number will be higher; claiming 21 after adding new checks would itself be a false claim. |
| FC-V03 | **"G1 [or G2/G3/G4/G5/G6/G8] is closed"** based on work that approached but did not complete the gate | two-agent-vps.md §2: "Never claim a gated item is done" and "A gate is done when observed and the observation is recorded." G1–G8 are human-only gates (VPS provisioned, DNS, BotFather bots, OpenRouter keys, OAuth consent, setWebhook, age keypair). None can be closed by an agent; none can be claimed closed without the owner's direct confirmation. G7 is CLOSED as WONT-DO (§0b); do not re-open it. |
| FC-V04 | **"A credential is confirmed"** without a scoped call that returned observable evidence | two-agent-vps.md §2a: "Confirm a credential by making a scoped call, never by echoing it — the value still never reaches a message, a log, a commit or a report." A credential's existence cannot be assumed or claimed without a live, observed, scoped probe whose result is recorded (not printed). |
| FC-V05 | **"No deployment particulars are present in ops/ or fixtures"** without the deployment-particulars scan running and passing | two-agent-vps.md §7: "add a check that `ops/**` and all fixtures contain no deployment particular... Wire it into the harness so it fails closed." The claim requires the AC09 scan to have run and reported pass. A visual inspection or "I checked and didn't see any" is not sufficient. |
| FC-V06 | **"The model registry is production-eligible"** when the registry is marked `provisional: true` | two-agent-vps.md §3: "A provisional registry may never promote a model for live routing." A registry built without live dev-key calls, or with an absent/exhausted dev key, is provisional. Claiming production eligibility from a provisional registry is forbidden. |
| FC-V07 | **"nizamcore patches are applied"** without cross-checking against `ops/NIZAMCORE_VERIFIED_STATE.md` | two-agent-vps.md §6a: "Check each [patch] against the verified state before applying it, and do not apply one the verified state contradicts." Claiming patch application without that cross-check and without the verified-state file confirming no contradiction is a forbidden completion claim. |
| FC-V08 | **"Shadow run R3 is complete"** without machine-readable run records for ALL representative runs | Playbook §production_acceptance: "Shadow runs produce no critical defect" requires observed run records, not a summary assertion. Each shadow run must emit a run record with all required fields from Section 5; a run with no machine-readable record is not a shadow run for R3 exit purposes. |

---

### 4C. Forbidden Claims Implied by the AGENTS file and Contract Authority

| ID | Forbidden Claim | Source Rule |
|----|-----------------|-------------|
| FC-A01 | **"Calendar write is idempotent"** without both a write attempt AND a confirmed readback showing no duplicate | Playbook §verification_principles: "A connector success response is not persistence until the destination is read back." Idempotency is proven by two writes and one result, confirmed by reading the calendar state after both. |
| FC-A02 | **"SUKOON gate is proven"** without tamper T1 having been run and documented | Contract 05 §tamper_requirement: tamper applies to constitutional gate tests. A SUKOON gate that has never been tamper-tested cannot be called proven, regardless of how many passing runs have been observed. |
| FC-A03 | **"Governance conflict is resolved"** without an owner-authored resolution record | Contract 01 T09 and two-agent-vps.md §7 require an explicit reconciliation. An agent's determination that the conflict is "probably" resolved, or that the contracts "effectively" agree, is not a resolution. Only the owner can resolve it, and only in writing. |
| FC-A04 | **"No real data in fixtures"** based on inspection alone | the AGENTS file: "Use synthetic fixtures and redacted identifiers. Never track real ledgers, secrets, credentials, hostnames, IPs, Drive IDs, webhook paths, Telegram IDs, or deployment particulars." The AC09 scan must confirm this, not a manual assertion. |
| FC-A05 | **"UNPROVEN actions closed the run successfully"** | Contract 05 §verification_model and Section 5 of this document: UNPROVEN must never appear in a final THABAT receipt. A run that closes with any action in UNPROVEN state must have `status: FAILED`, not VERIFIED. |

---

## 5. OBSERVABILITY

Every implementation of the NIZAM Daily Governor MUST emit a structured run record. An implementation that emits a subset of the required fields, uses an unofficial status, omits the thabat_receipt, or closes any run with actions in UNPROVEN state produces an UNVERIFIABLE run that cannot satisfy any release stage exit criterion.

---

### 5A. Required Run Record Fields
*Source: Playbook 03 §observability run_record_fields (14 fields) | Supplemented by Contract 01 §required_runtime_receipt (additional required content within thabat_receipt)*

| Field | Type | Notes |
|-------|------|-------|
| `run_id` | string (UUID or equivalent globally unique) | Stable across retries within the same logical run instance. Two runs for the same scheduled slot that are retries of each other must share a `run_id`. |
| `scheduled_for` | ISO 8601 datetime with IANA timezone | The intended fire time from the scheduler. Must include timezone offset. Must be `Africa/Cairo` for production runs unless `RECALIBRATE` is in effect. |
| `started_at` | ISO 8601 datetime with IANA timezone | Actual moment the run acquired the lock and began A_PRECHECK. |
| `finished_at` | ISO 8601 datetime with IANA timezone | Moment of THABAT closeout. Must be >= `started_at`. |
| `timezone` | IANA timezone string | Must match the timezone in `scheduled_for` and `started_at`. Failure to match is a consistency error. |
| `stage` | enum (R0–R7) | The release stage in which this run was executed. Allows filtering run records by operational phase. |
| `status` | enum (see §5B) | The final outcome of the run. Must reflect observed outcome, not intent. |
| `input_freshness` | map of `{domain_id: freshness_status}` | One entry per domain consulted. Each value must be one of the six freshness statuses from Contract 02 §freshness_policy: `fresh`, `observed`, `stale`, `unknown`, `missing`, `conflict`. Domains not consulted must not appear. Domains that failed to respond must appear with `missing` or `unknown`. |
| `selected_sources` | list of `{source_id, authority_class, freshness_status}` | Sources actually consulted, with authority classification from Contract 01 §authority_order. Must not include sources that were not reached. |
| `authorization_basis` | list of `{contract_id, version, tenet_id}` | The specific contracts and tenets authorizing the actions taken in this run. Must cite version strings. An action without an `authorization_basis` entry is unauthorized. |
| `actions_attempted` | integer >= 0 | Count of actions submitted to the execution manifest. Zero is valid (e.g., a BLOCKED run). |
| `actions_verified` | integer >= 0, <= actions_attempted | Count of actions whose readback confirmed the landed state. Must never exceed `actions_attempted`. |
| `retries` | integer >= 0 | Count of action-level retries within this run. Does not count run-level retries (those are separate run records). |
| `failures` | list of `{action_id, reason, recovery_step}` | Structured list of action failures. An empty list `[]` is acceptable when there are no failures. `null` is not acceptable — omitting this field is a schema violation. |
| `thabat_receipt` | object (see below) | Machine-readable THABAT closeout block. Required on every run regardless of status. |

**Required fields within `thabat_receipt`** (Contract 01 §required_runtime_receipt):

| Field | Notes |
|-------|-------|
| `timestamp` | ISO 8601 datetime. May duplicate `finished_at` for self-contained readability. |
| `contract_versions` | map of `{contract_id: version}` for all contracts governing this run. Must include all five contract IDs. |
| `sukoon_state` | One of: `green`, `yellow`, `red`, `crisis`. Never null when biometric data is available. |
| `objective_recovery_percent` | Integer 0–100. Must be labeled MISSING (not omitted) when WHOOP data is unavailable. |
| `himayah_classification` | Privacy classification of all outputs produced in this run. |
| `modules_invoked` | List of DAG node IDs (A_PRECHECK through M_THABAT) that were invoked. |
| `actions_attempted` | Duplicates top-level field; included for receipt self-containment. |
| `actions_verified` | Duplicates top-level field; included for receipt self-containment. |
| `blocked_actions` | List of `{action_id, gate_name, rule_violated}` for actions that were blocked. Empty list is acceptable; null is not. |
| `evidence_summary` | Structured record of evidence sources used, each labeled with FACT/INFERENCE/ASSUMPTION/MISSING and freshness status. |
| `open_loops` | List of unresolved items requiring human truth or future follow-up. Empty list is acceptable; null is not. |
| `next_action` | Top recommended next action for the operator, if any. Must be empty string `""` rather than null when there is nothing to recommend. |

---

### 5B. Allowed Run Statuses
*Source: Playbook 03 §observability allowed_statuses (7 values) | Supplemented by Contract 05 §verification_model.statuses (adds SYNC_PENDING, UNPROVEN)*

| Status | Source | Meaning | When to use | Terminal? |
|--------|--------|---------|-------------|-----------|
| `PLANNED` | Playbook | Run is scheduled but has not started. | Emitted by the scheduler before lock acquisition. | No — transitions to STARTED or BLOCKED |
| `STARTED` | Playbook | Run has acquired the run lock and begun A_PRECHECK. | Emitted at lock acquisition. | No — must resolve to a terminal status at THABAT closeout |
| `VERIFIED` | Playbook | Run completed and ALL attempted actions were confirmed via readback. `actions_verified == actions_attempted`. | The only status that satisfies a release-gate "run completed" requirement. A run with any unverified write must NOT use this status. | Yes |
| `FAILED` | Playbook | Run completed but one or more actions failed or a readback mismatch occurred. `failures` is non-empty. | Drive write with readback mismatch (D03/C04-T05), blast-radius gate failure, schema validation failure, any readback returning different content than written. | Yes |
| `BLOCKED` | Playbook | Run could not proceed because a mandatory pre-condition was not met. Zero actions were attempted. | SUKOON crisis override; kill switch active (`NIZAM_KILL_ALL=1`); contract version mismatch; lock already held by an active run. | Yes |
| `NEEDS_CONFIRMATION` | Playbook | Run completed but one or more actions require human confirmation of a human-only field or decision. | Human truth field absent; conflicting sources requiring owner resolution; Calendar_Approved field encountered that requires human action. | Yes (for this run; requires human follow-up) |
| `SKIPPED_ALREADY_VERIFIED` | Playbook | The 13:00 reconciliation run confirmed the 12:00 run was already VERIFIED; no work was performed. | Used EXCLUSIVELY by the reconciliation run (13:00); NEVER by the primary run (12:00). | Yes |
| `SYNC_PENDING` | Contract 05 | A write was attempted and returned success but readback has not yet been performed or is retrying. | Intermediate state only. Must resolve to VERIFIED or FAILED before THABAT closeout. A run that closes with any action in SYNC_PENDING must use `status: FAILED`. | No — intermediate only |
| `UNPROVEN` | Contract 05 | An action returned a success response but no readback was performed. | Must NEVER appear in a final THABAT receipt. If a run closes with any action in UNPROVEN state, the overall run status must be FAILED. If this status ever appears in a finalized receipt, it is a schema violation and a forbidden completion claim (FC-A05). | Never terminal — its presence in a closed receipt is itself a defect |

**Anti-metric rule (Contract 05 §observability anti_metric_rule):** Metrics must not incentivize the implementation to infer human completion, hide failures, over-promote hypotheses, or reduce safety blocking. Specifically:
- `VERIFIED` must never be assigned when `actions_verified < actions_attempted`.
- `SKIPPED_ALREADY_VERIFIED` must never be assigned by the primary noon run.
- `UNPROVEN` must never appear in a finalized THABAT receipt.
- `NEEDS_CONFIRMATION` must not be used to defer recording a failure — if an action failed (e.g., blast-radius gate rejected it), the status is FAILED, not NEEDS_CONFIRMATION.

---

*End of NIZAM_GOVERNOR_ACCEPTANCE_MATRIX v1.0.0.*
*Produced: 2026-09-03 by NIZAM Verifier (independent).*
*This document is a DESIGN artifact. No test has been executed. No status is claimed passing or verified. All blocking dependencies listed in Section 1 are active as of the production date.*
*Next required action: Owner provides governance reconciliation record for the GitHub commit/push conflict (R0 exit prerequisite and prerequisite for C01-T06, G04, and R7).*
