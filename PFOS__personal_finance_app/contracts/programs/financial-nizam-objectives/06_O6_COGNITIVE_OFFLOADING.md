# Financial NIZAM Objective O6 — Cognitive Offloading

**Status:** PROPOSED OVERHAUL DESIGN — owner-approved objective, implementation not yet verified  
**Objective ID:** O6  
**Objective name:** Cognitive Offloading  
**Program:** Financial NIZAM / PFOS / MAL implementation namespace  
**Owner:** Seif ElSherbiny  
**Version:** 0.1.0-design  
**Sensitivity:** review_before_commit  
**Owning phase:** Phase 6 — Attention management, continuity, scheduled/event-driven financial cognition  
**Precedence:** safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting subordinate contract → verified runtime evidence → historical/draft material

---

## 1. Objective

**[FACT]** O6 consumes reconciled financial truth from O1, protection state from O2, decision intelligence from O3, capital-allocation outputs from O4, and wealth trajectory from O5. It MUST NOT create a second transaction ledger, balance source, obligation store, budget truth, forecast truth, or wealth-state store.

**[AGREED]** Financial NIZAM must continuously carry routine financial monitoring, memory, follow-up, reconciliation awareness, due-date awareness, evidence discovery, exception tracking, and review preparation so the owner does not need to hold those details mentally.

**[AGREED]** The owner should primarily spend attention on decisions that materially require human judgment, approval, tradeoff ownership, or new information. Repetitive remembering, checking, searching, matching, and status tracking should be offloaded to the system where governance permits.

**[AGREED]** Cognitive offloading does not mean silent paternalism. The system must preserve uncertainty, show when evidence is stale or missing, surface meaningful changes, and make it easy for the owner to inspect why a recommendation or alert exists.

**[AGREED]** The conversational layer should be concise by default but evidence-rich on demand. It should not force the owner to reconstruct context from prior chats, statements, SMS messages, spreadsheets, or Drive folders when the information is already available through permitted sources.

**[FACT]** Authoritative money values, ratios, percentages, protected-floor amounts, debt effects, forecast outputs, and wealth effects MUST come from governed deterministic/statistical engines. O6 may route, summarize, compare references, and prioritize attention; it does not calculate authoritative monetary truth itself.

---

## 2. Governing source decisions

### 2.1 Existing canonical-candidate rules

**[FACT]** The Financial NIZAM constitution requires evidence before interpretation, reconciliation before optimization, explicit freshness, one canonical state, bounded cross-domain signals, few high-leverage actions, anti-shame language, human authority, and deterministic monetary truth.

**[FACT]** Monitoring contracts already define recurring and event-driven checks for transactions, daily state, weekly review, monthly close, statement cycles, salary events, and material financial events.

**[FACT]** Alerts must earn attention. They must state what changed, why it matters, evidence/confidence, deadline, and the smallest permitted action; duplicates are suppressed unless severity or deadline materially changes.

**[FACT]** The existing UI contract says the short summary should answer current reliability/status, safe-to-spend engine result, next protected obligation, what changed, whether trajectory is improving, highest-priority action, and the effect of a contemplated decision.

**[FACT]** The Agent Runbook requires refresh/register evidence → freshness → normalize/dedupe → reconcile → canonical snapshot → derived budget/obligation state → forecast → monitoring → few high-impact recommendations → approval → authorized write → audit → verification → THABAT.

**[FACT]** High financial stress should reduce cognitive load and action count rather than increase pressure.

### 2.2 New owner directions incorporated into this overhaul

**[AGREED]** Financial NIZAM is expected to communicate proactively three times per day under normal operations: late morning around 11:00–12:00, afternoon around 15:00–16:00, and night around 21:00–22:00 in the owner’s applicable local timezone.

**[AGREED]** New user-provided evidence or direct conversation is event-driven and should trigger a relevant refresh and explanation rather than waiting for the next scheduled brief.

**[AGREED]** Google Drive is a durable trusted NIZAM evidence/recovery mirror for artifacts permitted under the redesigned HIMAYAH model; the VPS remains replaceable runtime/working compute and must not become the only place where important recoverable memory exists.

**[AGREED]** Financial NIZAM should inspect registered Drive financial evidence at least twice daily for new or modified artifacts, so the owner does not need to remember to announce every upload.

**[AGREED]** The system should maintain continuity across statements, transaction SMS, account evidence, prior conversations, decision records, forecasts, and approved cross-pillar context, while preserving provenance and source boundaries.

**[AGREED]** The system should learn which kinds of evidence and communication patterns actually help the owner make better decisions, but learned communication preferences may not silently change financial policy or authority.

**[AGREED]** If a contested decision is deferred with owner agreement, the system must remember the future reassessment condition/time and bring the issue back at the appropriate checkpoint.

---

## 3. Scope

O6 governs:

1. owner-facing financial attention management;
2. scheduled daily briefing orchestration;
3. event-driven re-briefing after new evidence or owner interaction;
4. twice-daily registered Drive evidence discovery interface;
5. unresolved-item continuity;
6. reminder and reassessment continuity for accepted cooling periods;
7. exception queue ownership and resurfacing;
8. stale-data and missing-evidence visibility;
9. summary compression and drill-down behavior;
10. alert batching, deduplication, and attention prioritization interfaces;
11. owner-facing context packets assembled from authoritative references;
12. cross-session continuity without using chat memory as financial truth;
13. transaction/merchant/statement investigation handoff tracking;
14. weekly/monthly/pay-cycle review preparation;
15. post-decision follow-up reminders and outcome observation;
16. evidence provenance and audit references in user-facing summaries;
17. cognitive-load reduction under stress or high exception volume;
18. recovery completeness awareness for important financial memory;
19. retrieval of approved historical context when materially relevant;
20. proof that the system actually refreshed required upstream state before summarizing it.

O6 does **not** govern:

- transaction reconciliation logic itself;
- balance calculation;
- protected-floor calculation;
- debt-ratio calculation;
- budget assignment math;
- forecast generation math;
- wealth-growth calculation;
- autonomous spending, payment, transfer, borrowing, investment, or refinancing;
- final materiality scoring;
- the full challenge/override policy;
- independent psychological diagnosis;
- unrestricted reading of every NIZAM record for every finance request;
- changing HIMAYAH policy without the formal redesign process.

---

## 4. Cognitive-offloading doctrine

**[AGREED]** O6 uses the following doctrine:

> **The system remembers the system; the owner remembers the decision.**

The operating order is:

1. know what financial evidence exists;
2. know what changed since the last reliable state;
3. know what remains unresolved;
4. know what is due and when;
5. know which upstream engines are fresh enough to support a claim;
6. know which decisions are pending owner action;
7. know which prior recommendations require follow-up;
8. know which future review/checkpoint has been accepted;
9. bring only the highest-value items into the owner’s active attention;
10. retain drill-down paths to full evidence and history;
11. close the loop after the owner acts or new evidence arrives.

**[FACT]** O6 does not replace the O1 ledger with memory. A reminder such as “card statement due soon” must still trace to an obligation/evidence object, not a remembered chat sentence.

**[AGREED]** A missing reminder is a system defect if the underlying governed record existed, was fresh enough, and the reminder policy required surfacing it.

---

## 5. Offload taxonomy

### 5.1 Remembering

O6 should remember, through durable references:

- unresolved transactions;
- unmatched transfers;
- pending statement reconciliation;
- due obligations;
- accepted follow-up dates;
- pending owner approvals;
- contested decisions awaiting reassessment;
- expected income events;
- statement-cycle checkpoints;
- planned travel/purchase commitments already registered;
- forecast assumptions requiring later validation;
- post-decision outcome checks;
- Drive artifacts discovered but not yet fully reconciled;
- alerts currently OPEN/ACKNOWLEDGED/SNOOZED;
- missing evidence requests;
- pending merchant-resolution work.

### 5.2 Checking

O6 should orchestrate recurring checks for:

- evidence freshness;
- reconciliation state;
- next protected obligations;
- liquidity-risk indicators supplied by O2/O15;
- new fees and penalties;
- new/modified Drive evidence;
- duplicate-suspect or anomaly queues;
- scheduled income events;
- forecast-vs-actual observations;
- unresolved decision outcomes;
- mirror/read-back persistence exceptions;
- VPS/storage health signals when available from infrastructure monitoring.

### 5.3 Preparing

O6 should prepare, but not autonomously decide:

- morning/afternoon/night briefs;
- weekly behavioral/forecast review packet;
- monthly close packet;
- quarterly regime/trajectory review packet;
- pre-payday allocation packet;
- material purchase decision packet;
- cooling-period reassessment packet;
- exception-resolution queue;
- evidence/provenance drill-down bundle.

### 5.4 Escalating

O6 escalates attention when upstream policy marks an item material, urgent, unresolved beyond tolerance, or confidence-degrading. Escalation changes attention priority, not financial authority.

---

## 6. Daily communication cadence

### 6.1 Late-morning brief — 11:00–12:00

**[AGREED]** The late-morning brief is the primary daily orientation.

It should answer, using upstream engine references:

1. Is the current financial state reliable enough to act on?
2. What changed materially since the prior close?
3. What is the current financial regime reference?
4. What is the current protected-liquidity status reference?
5. What is safe to spend now, if the engine has sufficient evidence?
6. What is the next protected obligation?
7. What decision or exception deserves the owner’s attention most?
8. What changed in trajectory or forecast confidence?
9. Did new Drive evidence arrive?
10. Is any accepted reassessment/cooling checkpoint due today?

**[AGREED]** The default brief should remain concise. The owner can request the full evidence chain.

### 6.2 Afternoon brief — 15:00–16:00

The afternoon brief focuses on intraday change:

- newly ingested transactions/evidence;
- material deviation from morning assumptions;
- transaction inbox changes;
- emerging liquidity/protection issues;
- pending owner decisions;
- newly relevant merchant/anomaly findings;
- whether the day plan requires adjustment;
- whether no material change occurred.

**[PROPOSED]** If nothing material changed, the afternoon brief SHOULD explicitly say that no material change requires action rather than generate artificial content.

### 6.3 Night brief — 21:00–22:00

The night brief closes the day:

- what actually happened versus the latest plan;
- unresolved items carried forward;
- tomorrow’s known obligations/events;
- any data still pending or stale;
- whether a forecast/outcome checkpoint matured;
- whether a contested decision is scheduled for reassessment;
- one-to-three highest-value items for the next day;
- persistence/mirror exception if any important artifact failed to land.

### 6.4 Timezone and availability

**[PROPOSED]** Scheduled briefs must use a configured owner timezone and explicit scheduler state. They must not infer timezone from model memory.

**[FACT]** Scheduling does not grant authority to move money or make a decision on the owner’s behalf.

---

## 7. Event-driven cognitive refresh

### 7.1 User message

A direct financial question should trigger retrieval of the minimum required current state before substantive advice.

If the question requires current monetary truth, the sequence is:

`request → source/freshness check → reconciliation requirement check → relevant engine calls → decision/protection analysis → concise answer → evidence drill-down`.

### 7.2 New SMS/transaction evidence

When a transaction SMS or transaction record is supplied:

1. register source evidence;
2. match against existing pending/posted/known transaction candidates;
3. update the reconciliation queue;
4. rebuild affected canonical/derived state through authoritative writers;
5. rerun affected protection/forecast/decision surfaces;
6. tell the owner what changed and what did not;
7. avoid duplicate counting;
8. preserve unresolved ambiguity.

### 7.3 New statement/PDF/export

A new statement or export should trigger:

- artifact registration;
- source hashing/provenance;
- statement-period identification;
- duplicate/import-idempotency checks;
- account/balance reconciliation handoff;
- obligation update where relevant;
- exception generation for mismatches;
- affected forecast/state refresh;
- owner-facing summary only after the evidence pipeline reaches an appropriate state.

### 7.4 Material contemplated decision

A contemplated purchase/trip/plan should route to O3 after O1/O2 freshness gates. O6 owns continuity of the conversation, not the calculation.

### 7.5 Owner correction

A human correction should be recorded as explicit user evidence and routed through O1 correction policy. O6 must not simply overwrite the remembered value in chat context.

---

## 8. Registered Drive evidence discovery

### 8.1 Discovery cadence

**[AGREED]** Financial NIZAM should inspect the registered Financial NIZAM Drive scope at least twice daily for new or modified artifacts.

**[PROPOSED]** Discovery windows SHOULD be coordinated with the late-morning and afternoon operating cycles, with additional event-driven discovery when the owner explicitly asks the system to inspect Drive.

### 8.2 Discovery does not equal canonical mutation

A discovered Drive file is evidence, not automatically current truth.

Required sequence:

`discover → classify → register → extract/normalize → dedupe → reconcile → authoritative write → derived refresh → audit → mirror/read-back where applicable`.

### 8.3 Discovery receipt

Each discovery run should produce an internal receipt containing:

```yaml
drive_discovery_receipt:
  run_id: <id>
  started_at: <timestamp>
  completed_at: <timestamp>
  registered_scope_ref: <scope-ref>
  files_seen: <count-ref-or-runtime-output>
  new_artifacts: []
  modified_artifacts: []
  ignored_artifacts: []
  classification_exceptions: []
  ingestion_failures: []
  reconciliation_effects: []
  canonical_state_changed: <true|false|unknown>
  follow_up_required: []
  audit_refs: []
```

**[FACT]** Documentation examples must not fabricate runtime counts or monetary effects.

### 8.4 Readability policy interface

**[AGREED]** Under the proposed HIMAYAH v2 direction, approved personal/financial records should generally remain readable inside the Trusted NIZAM Boundary (VPS + Drive), while credentials, tokens, API keys, passwords, private keys, and other hard secrets remain prohibited from ordinary Drive storage.

**[FACT]** This owner direction is a proposed governance redesign and must be implemented through the formal HIMAYAH change-control artifact before runtime behavior is claimed.

---

## 9. Attention budget and prioritization

### 9.1 Core principle

**[AGREED]** More detected events must not automatically mean more interruptions.

O6 should prioritize by:

- severity from governed monitoring/materiality policy;
- deadline proximity;
- protected-liquidity impact;
- obligation risk;
- confidence/freshness;
- reversibility;
- owner action requirement;
- whether the item has already been acknowledged;
- whether new evidence materially changed the case.

### 9.2 One-to-three high-value actions

**[FACT]** Existing PFOS doctrine favors few high-leverage actions.

**[PROPOSED]** Routine briefs SHOULD surface at most one-to-three owner actions by default, while preserving a full queue accessible on demand.

### 9.3 No-action state

The system must be able to say:

> No owner action is required from the financial system at this checkpoint.

This is a valid high-quality outcome.

### 9.4 Alert fatigue

P2/P3 items should be batched when possible. P0/P1 items remain prominent under monitoring policy, but urgency cannot be fabricated.

---

## 10. Unresolved-item continuity

### 10.1 Open-loop object

**[PROPOSED]** Every unresolved financial item requiring future attention should have a durable object rather than exist only in conversation history.

```yaml
financial_open_loop:
  loop_id: <stable-id>
  type: <evidence|reconciliation|obligation|decision|forecast|follow_up|other>
  opened_at: <timestamp>
  canonical_state_version: <ref>
  source_refs: []
  description: <text>
  owner_action_required: <true|false>
  system_action_pending: <true|false>
  next_check_at: <timestamp|null>
  next_condition: <condition-ref|null>
  severity_ref: <ref|null>
  status: <OPEN|ACKNOWLEDGED|SNOOZED|RESOLVED|SUPERSEDED>
  resolution_ref: <ref|null>
  audit_refs: []
```

### 10.2 No orphaned obligations

If an obligation or exception is materially relevant and unresolved, it must remain discoverable until resolved/superseded under governing policy.

### 10.3 Conversation closure

Ending a chat does not close a financial open loop. Resolution requires a durable state transition.

---

## 11. Cooling-period and reassessment continuity

**[AGREED]** A cooling period occurs only when the owner accepts it.

When accepted, O6 must create a durable reassessment object containing:

- decision reference;
- current recommendation reference;
- reason for deferral;
- owner-accepted revisit time or condition;
- evidence to refresh before revisit;
- optional contextual state signal to check;
- reminder channel/cadence where configured;
- eventual outcome/override reference.

**[AGREED]** A condition such as “after workout,” “tomorrow,” or another owner-approved context change may be used as a revisit trigger, but O6 must not claim that the condition improves decision quality unless historical evidence supports that association.

**[PROPOSED]** If the condition cannot be machine-verified, manual confirmation is sufficient unless the owner explicitly requested stronger proof.

---

## 12. Context retrieval contract

### 12.1 Minimum relevant context

O6 should retrieve only context needed to support the active financial task.

Possible sources include:

- O1 canonical financial snapshot and evidence refs;
- O2 protection state;
- O3 decision records;
- O4 allocation records;
- O5 wealth goals/trajectory;
- transaction/merchant history;
- prior forecast-versus-actual records;
- approved journal/behavioral context;
- approved BADAN/WHOOP-derived signals;
- approved MARSAD external-intelligence signals;
- THABAT decisions/open loops;
- relevant Drive artifacts.

### 12.2 Chat memory is not truth

**[FACT]** Conversation memory may help locate a likely record or explain owner preference, but authoritative financial facts must be re-resolved to canonical/evidence sources.

### 12.3 Cross-pillar relevance gate

**[PROPOSED]** Cross-pillar retrieval should require a relevance reason, not unrestricted bulk ingestion.

Example:

```yaml
cross_pillar_context_request:
  task_id: <id>
  financial_question: <text>
  requested_pillar: <YAWMIYAT|BADAN|MARSAD|QARAR|THABAT|other>
  relevance_reason: <text>
  permitted_scope_ref: <ref>
  source_refs: []
  output_label: <FACT|INFERENCE|HYPOTHESIS|UNKNOWN>
```

### 12.4 No hidden psychological authority

Behavioral/journal context may support hypotheses or communication strategy but must not become a covert authority that overrides financial evidence or owner agency.

---

## 13. Briefing object

**[PROPOSED]** Every scheduled/event-driven owner briefing should be generated from a structured briefing object.

```yaml
financial_brief:
  brief_id: <id>
  brief_type: <morning|afternoon|night|event|weekly|monthly|quarterly|pre_payday>
  generated_at: <timestamp>
  canonical_state_version: <ref>
  freshness_state: <fresh|partial|stale|unknown>
  reconciliation_state: <ref>
  financial_regime_ref: <ref|null>
  protected_liquidity_ref: <ref|null>
  safe_to_spend_ref: <ref|null>
  next_obligation_ref: <ref|null>
  changed_since_ref: <prior-brief-or-snapshot>
  material_changes: []
  unresolved_items: []
  owner_actions: []
  system_actions_completed: []
  system_actions_failed: []
  drive_discovery_ref: <ref|null>
  persistence_health_ref: <ref|null>
  trajectory_ref: <ref|null>
  confidence: <label>
  evidence_refs: []
  audit_refs: []
```

**[FACT]** If evidence is insufficient for a field, the object should use null/unknown rather than fabricate a clean value.

---

## 14. What the owner sees

### 14.1 Default response shape

**[AGREED]** Default financial communication should be direct and compact:

1. **What matters now**
2. **What changed**
3. **What is protected / at risk**
4. **What requires your decision**
5. **What the system already handled**
6. **What happens next**
7. **Evidence available on request**

### 14.2 Evidence escalation

If the owner challenges the recommendation, O6 can expand the evidence presentation but delegates substantive high-friction challenge logic to O19.

### 14.3 No fake precision

O6 must not convert qualitative uncertainty into invented percentages merely to sound analytical.

### 14.4 No repetitive burden

If the owner has already answered a question and the answer is durably recorded and still current, O6 should not ask it again.

---

## 15. Weekly, monthly, quarterly, and pay-cycle preparation

### 15.1 Weekly packet

O6 should prepare:

- what changed materially;
- forecast versus actual references;
- unresolved exception queue;
- major merchant/category behavior changes;
- decisions taken versus recommended;
- upcoming obligations;
- evidence freshness gaps;
- one-to-three high-value actions;
- open loops requiring owner attention.

### 15.2 Monthly packet

O6 should assemble the monthly-close inputs from authoritative sources and ensure unresolved gaps are visible before review.

### 15.3 Quarterly packet

O6 should prepare the regime/trajectory review inputs without independently deciding the regime.

### 15.4 Pre-payday packet

**[AGREED]** The system should prepare the upcoming income-allocation conversation approximately two days before the expected salary event, adjusted to the actual weekday/holiday/income evidence policy rather than assuming the nominal date blindly.

The packet should reference:

- expected income evidence/forecast;
- current obligations;
- protected-floor requirement;
- debt/credit settlement requirements;
- planned commitments;
- current regime;
- candidate O4 allocations;
- uncertainty if income timing or value is not verified.

---

## 16. Post-decision follow-up

O6 should remember to observe later outcomes for material decisions.

For each tracked decision it should retain:

- decision record ref;
- predicted consequences ref;
- date/horizon of expected observation;
- actual evidence when available;
- outcome-attribution request;
- unresolved status if the counterfactual cannot be proven;
- whether the case should update O12/O20/O22 learning.

**[AGREED]** Financial NIZAM should later explain when a prior decision measurably improved or weakened the trajectory, but realized effect, avoided cost, forecast benefit, and counterfactual estimate must remain distinct.

---

## 17. Stale data and uncertainty handling

### 17.1 Stale canonical state

If current state is stale, O6 should say so before presenting action-oriented claims.

### 17.2 Missing source

If a required statement/account/transaction period is missing, the system should identify the gap and narrow the conclusion rather than invent continuity.

### 17.3 Conflicting evidence

Conflicting balances or duplicated-looking events stay in the exception queue until reconciled. O6 does not average or choose the convenient source.

### 17.4 Partial brief

A partial brief is allowed when some data is unavailable, provided missing areas are explicit.

### 17.5 Confidence degradation

Low freshness, unresolved reconciliation, high historical forecast error, or weak evidence should reduce confidence or widen uncertainty through upstream policy.

---

## 18. Agent-to-agent handoff contract

**[FACT]** Specialist agents may analyze but must not maintain private financial truth.

**[PROPOSED]** O6 should require handoffs to use a structured envelope:

```yaml
financial_task_envelope:
  task_id: <id>
  request: <text>
  canonical_state_version: <ref>
  input_artifacts: []
  assumptions: []
  unresolved_items: []
  expected_output: <type>
  write_permissions: []
  approval_required: <true|false>
  completion_status: <status>
  audit_refs: []
```

O6 owns continuity of the task and owner-facing synthesis; the specialist owns only its bounded output.

---

## 19. Human authority and anti-dependency design

### 19.1 Human decision fields remain human

O6 may remind, explain, and prepare but cannot populate `Decision Made?`, execute money actions, or impersonate approval.

### 19.2 Offload does not equal learned helplessness

**[PROPOSED]** Major financial briefs should preserve enough reasoning that the owner can understand the decision rather than merely obey a black box.

### 19.3 Owner disagreement

A disagreement is not a system failure. It becomes a decision/learning event.

### 19.4 Owner absence

If the owner does not respond, O6 may continue monitoring and preserving evidence but must not execute consequential financial actions unless a future explicit policy independently authorizes that action class.

---

## 20. HIMAYAH v2 interface

### 20.1 Current-state warning

**[FACT]** Existing NIZAM governance currently contains stricter local-only rules for some personal material.

**[AGREED]** The owner has directed a formal redesign proposal where ordinary NIZAM personal artifacts can default to a readable trusted-private class across the Trusted NIZAM Boundary (VPS + Google Drive), while hard secrets remain excluded.

### 20.2 O6 dependency

O6 must not pretend that this redesign is already implemented.

Until the HIMAYAH v2 contract is accepted and verified, O6 must follow the current enforced privacy classification at runtime.

### 20.3 Intended future classes

The future design should support:

- `public_safe`;
- `trusted_private`;
- `trusted_sensitive`;
- `strict_local`;
- `strict_local_maximum`;
- `secret`.

**[PROPOSED]** `trusted_private` becomes the normal class for owner-approved readable NIZAM personal records inside VPS + Drive after governance migration.

---

## 21. Persistence and recovery continuity

### 21.1 VPS is replaceable runtime

**[AGREED]** The VPS must not be the only location containing important recoverable NIZAM memory.

### 21.2 Drive mirror/recovery awareness

O6 should track whether important eligible artifacts expected in Drive actually landed and can be read back.

### 21.3 Persistence exception

A failed mirror/read-back becomes an operational open loop if the artifact is required for recovery continuity.

### 21.4 Recovery question

The system should periodically be able to answer:

> If the VPS disappeared now, which important permitted records would be lost?

Anything important and expected to be durable but missing from the recovery mirror is a persistence defect.

### 21.5 Storage pressure

O6 may surface infrastructure storage warnings supplied by runtime monitoring but does not independently derive storage thresholds unless governed by an infrastructure policy.

---

## 22. Failure modes

### FM-01 — Chat-memory substitution

**Failure:** agent uses remembered balance or debt value without canonical refresh.  
**Response:** block authoritative claim; retrieve O1 state/evidence.

### FM-02 — Silent stale brief

**Failure:** brief presents current recommendation from stale evidence without warning.  
**Response:** mark stale/partial; narrow action recommendation.

### FM-03 — Alert storm

**Failure:** many low-value alerts overwhelm the owner.  
**Response:** dedupe/batch; surface highest-leverage items only.

### FM-04 — Forgotten Drive upload

**Failure:** owner uploads relevant evidence but never tells the agent.  
**Response:** twice-daily Drive discovery should detect/register it.

### FM-05 — Discovery mistaken for truth

**Failure:** new file directly overwrites canonical state.  
**Response:** route through ingestion/reconciliation and single writer.

### FM-06 — Orphaned cooling period

**Failure:** accepted reassessment is never resurfaced.  
**Response:** durable open-loop/reassessment object + scheduler check.

### FM-07 — Duplicate question

**Failure:** agent repeatedly asks for information already durably captured and still fresh.  
**Response:** retrieve existing record first.

### FM-08 — Hidden unresolved exception

**Failure:** clean summary hides a material unresolved balance/transaction issue.  
**Response:** brief must expose unresolved material uncertainty.

### FM-09 — Cross-pillar overreach

**Failure:** finance agent indiscriminately reads personal context unrelated to the task.  
**Response:** relevance-gated retrieval with audit references.

### FM-10 — Financial action by monitoring agent

**Failure:** reminder/monitoring path triggers payment or transfer.  
**Response:** hard authority denial + audit event.

### FM-11 — Drive sync failure treated as success

**Failure:** connector returns success but destination is absent/unreadable.  
**Response:** require read-back before `OK` receipt.

### FM-12 — Fake completion

**Failure:** brief says an upstream calculation was performed when no engine receipt exists.  
**Response:** computation-proof contract blocks claim.

---

## 23. Computation and refresh proof

**[AGREED]** O6 must be able to prove that required upstream work actually occurred before making a material summary or recommendation.

**[PROPOSED]** Each material briefing should reference a refresh receipt:

```yaml
financial_refresh_proof:
  refresh_id: <id>
  triggered_by: <scheduled|event|owner_request|review>
  canonical_state_before: <ref|null>
  evidence_refresh_refs: []
  reconciliation_refs: []
  derived_engine_refs: []
  forecast_refs: []
  monitoring_refs: []
  drive_discovery_ref: <ref|null>
  canonical_state_after: <ref>
  freshness_after: <state>
  unresolved_material_items: []
  completed_at: <timestamp>
  audit_refs: []
```

**[FACT]** The conversational agent may not claim “I checked/reconciled/recalculated” unless the relevant receipt exists or the runtime output was directly observed.

---

## 24. Data requirements

O6 requires references to, but does not own:

- canonical financial snapshot;
- evidence freshness/reconciliation state;
- obligations;
- protected-liquidity engine outputs;
- safe-to-spend engine outputs;
- budget state;
- forecasts/scenarios;
- materiality/severity;
- financial regime;
- decision records;
- Drive evidence index;
- alert queue;
- open-loop ledger;
- persistence mirror receipts;
- owner-approved schedule configuration;
- approved cross-pillar context permissions.

---

## 25. Proposed storage objects

**[PROPOSED]** O6 likely requires durable objects for:

1. `financial_open_loop`;
2. `financial_brief`;
3. `financial_refresh_proof`;
4. `drive_discovery_receipt`;
5. `decision_reassessment_trigger`;
6. `attention_queue_item`;
7. `owner_schedule_profile`;
8. `persistence_exception`;
9. `cross_pillar_context_request`;
10. `review_packet_manifest`.

**[FACT]** Exact filenames/schemas must be reconciled against the repository before implementation. This document does not invent canonical file paths.

---

## 26. Migration plan

### Phase A — Contract alignment

1. register O6 in the objective/program index;
2. map existing monitoring, runbook, UI, ledger, THABAT, Drive, and scheduler contracts;
3. identify current open-loop/reminder structures;
4. identify existing Drive polling/discovery behavior;
5. identify the enforced HIMAYAH version;
6. define ownership and single-writer boundaries.

### Phase B — Schemas

Create or extend the minimum schemas for briefing, open loops, refresh proof, Drive discovery receipt, and reassessment triggers.

### Phase C — Orchestration

Implement scheduled and event-driven triggers using existing runtime style and injected ports.

### Phase D — Owner-facing synthesis

Implement concise briefing generation over verified refs without LLM monetary calculation.

### Phase E — Persistence/recovery

Connect mirror/read-back state and storage-health signals.

### Phase F — Verification

Run deterministic fixtures, integration tests, failure injection, privacy egress, scheduling tests, deliberate tamper, and human confirmation.

---

## 27. Acceptance tests

### O6-T01 Scheduled cadence

Given a configured timezone and healthy state, the scheduler produces the expected late-morning, afternoon, and night briefing jobs without granting new financial authority.

### O6-T02 No duplicate cognitive burden

Given no material state change, the afternoon brief states that no material owner action is required rather than manufacturing new recommendations.

### O6-T03 Event refresh

A newly supplied transaction causes evidence registration/reconciliation refresh and a changed-state summary only after authoritative state updates.

### O6-T04 Drive discovery

A new file placed in the registered Drive scope is discovered by the next configured discovery run even if the owner never mentions it in chat.

### O6-T05 Discovery is not truth

A discovered statement with conflicting balance creates an exception and does not overwrite canonical state.

### O6-T06 Open-loop survival across sessions

An unresolved obligation/exception remains open after chat closure and resurfaces under policy until resolved/superseded.

### O6-T07 Cooling-period reminder

An owner-accepted deferred decision is resurfaced at the agreed time/condition with refreshed evidence.

### O6-T08 Chat memory rejection

A stale remembered value cannot be used as authoritative monetary truth when O1 state is unavailable.

### O6-T09 Alert dedupe

Repeated unchanged P2/P3 condition is batched/suppressed according to monitoring policy.

### O6-T10 Material unresolved visibility

A material reconciliation conflict appears in the brief and cannot be hidden by a clean summary.

### O6-T11 Cross-pillar relevance gate

A finance task can retrieve approved journal/WHOOP context only when a relevance reason and permitted scope exist.

### O6-T12 Human authority

No scheduled job, reminder, Drive discovery run, or monitoring event can execute payment, borrowing, transfer, investment, commit, or push without explicit authorized flow.

### O6-T13 Refresh proof

A material owner-facing statement that claims a refresh occurred must reference the upstream execution receipt.

### O6-T14 Drive read-back

A persistence receipt cannot become `OK` until the mirrored destination is read back successfully.

### O6-T15 Stale state

A stale/partial canonical state visibly degrades the brief and narrows action claims.

### O6-T16 Recovery defect detection

If an important Drive-eligible artifact exists only on VPS beyond policy tolerance, the system creates a persistence exception.

### O6-T17 Tamper

Removing a mandatory authority/freshness/computation-proof clause must cause contract validation to fail.

---

## 28. Deliberate failure-injection scenarios

1. Scheduler runs while canonical state is stale.
2. Drive contains a modified statement conflicting with the current balance.
3. Two identical transaction messages arrive from separate ingestion channels.
4. A low-confidence merchant anomaly repeats every hour.
5. A cooling-period trigger is scheduled and runtime restarts before the due time.
6. A Drive mirror reports success but read-back fails.
7. A specialist agent returns a monetary number without engine provenance.
8. Owner asks a decision question while reconciliation is incomplete.
9. Cross-pillar retrieval attempts to load unrelated private journal content.
10. VPS disk pressure rises while Drive mirror status is incomplete.
11. A prior open loop is accidentally marked resolved without resolution evidence.
12. A new chat begins with outdated conversation memory but newer canonical state exists.

Expected behavior must preserve truth, surface uncertainty, reduce cognitive burden, and retain human authority.

---

## 29. Observability and metrics

**[PROPOSED]** O6 runtime observability should track operational metrics without turning them into owner-worth scores:

- briefing jobs scheduled/completed/failed;
- event refresh latency;
- Drive discovery success/failure;
- unresolved-item aging;
- duplicate-alert suppression;
- owner-action queue size;
- stale-state occurrences;
- evidence gaps detected;
- reassessment triggers fired/missed;
- persistence exceptions;
- read-back failures;
- false or redundant owner prompts;
- percentage of material briefs with complete refresh proof;
- retrieval relevance denials;
- post-decision follow-up completion.

**[FACT]** Any percentage or score shown to the owner must come from a deterministic metric engine or stored measurement, not conversational estimation.

---

## 30. Relationship to later objectives

O6 intentionally delegates:

- O7 financial regime classification;
- O8 longitudinal financial intelligence;
- O9 merchant/behavior intelligence;
- O10 cross-domain decision intelligence;
- O11 evidence-based reasoning presentation;
- O12 forecast accountability;
- O13 income-cycle orchestration;
- O14 credit/liquidity optimization;
- O15 dynamic resilience floor;
- O16 economic radar;
- O17 weak-signal intelligence;
- O18 income expansion;
- O19 adversarial decision protection;
- O20 persuasion learning;
- O21 outcome attribution;
- O22 closed-loop financial coaching;
- O23 cooling/reassessment policy details;
- O24 decision-state intelligence;
- O25 explicit override;
- O26 override learning;
- O27 counterfactual decision ledger;
- O28 dynamic materiality;
- O29 computation proof program-wide;
- O30 Drive evidence discovery expansion;
- O31/O32 storage and mirroring;
- O33+ HIMAYAH redesign and trusted boundary.

O6 is the **attention/continuity layer** that keeps those systems usable without making the owner manually orchestrate them.

---

## 31. Implementation constraints

1. No new financial authority.
2. No LLM-authored authoritative money arithmetic.
3. No second canonical financial state.
4. No silent reconciliation bypass.
5. No Drive-discovered artifact mutates truth before reconciliation.
6. No alert may fabricate urgency.
7. No automatic closure of unresolved material items without evidence.
8. No cross-pillar bulk retrieval without relevance and permission.
9. No claim that a workflow ran without execution evidence.
10. No persistence success without destination read-back where the contract requires it.
11. No HIMAYAH v2 behavior may be claimed before governance migration is implemented and verified.
12. Existing owner-approved schedule windows are configuration inputs, not hard-coded assumptions in unrelated modules.

---

## 32. Definition of done

O6 is **designed** when this document is accepted as the cognitive-offloading objective contract.

O6 is **contract-verified** only when:

- the owning schemas/contracts are identified;
- static validation passes;
- required authority/freshness/single-writer clauses are machine-checked;
- deliberate tamper causes validation failure.

O6 is **runtime-verified** only when observed repository/runtime evidence proves:

1. scheduled daily briefs run at configured windows;
2. event-driven refresh works;
3. twice-daily Drive discovery works against the registered scope;
4. open loops survive session/runtime restarts;
5. cooling/reassessment triggers persist;
6. briefs expose freshness/reconciliation uncertainty;
7. computation/refresh receipts exist for material claims;
8. cross-pillar retrieval respects scope;
9. Drive mirror/read-back exceptions surface;
10. no monitoring path can execute consequential financial actions;
11. failure-injection tests pass;
12. a deliberate tamper is detected by the repository gate.

Until those conditions are observed, runtime status remains **DESIGNED / NOT RUNTIME-VERIFIED**.

---

## 33. Owner-facing north-star statement

**[AGREED]** O6 should make Financial NIZAM feel like this:

> I do not have to remember every financial detail, check every source manually, or keep every unresolved issue in my head. NIZAM keeps the financial system current, remembers what must be revisited, notices new evidence, prepares the right analysis, and brings me only the decisions and exceptions that genuinely need me. When I want proof, the evidence chain is there.

---

## 34. Evidence summary

### Facts

- Existing PFOS contracts already require one canonical state, freshness, reconciliation, alert dedupe, few high-leverage actions, human authority, and evidence-backed financial claims.
- Existing monitoring contracts define transaction, daily, weekly, monthly, statement, salary, and event-driven cadences.
- Existing runbook requires evidence refresh through audit and THABAT closeout.
- Existing UI guidance prioritizes concise decision-useful summaries.

### Agreed owner decisions

- Three proactive financial check-ins per day: late morning, afternoon, and night.
- Event-driven refresh when new evidence or financial questions arrive.
- At least twice-daily inspection of registered Drive financial evidence.
- Durable reminders/open loops for accepted cooling/reassessment periods.
- VPS should be replaceable runtime; important permitted memory should be durably mirrored.
- Ordinary approved personal/financial records are intended to become readable across VPS + Drive under HIMAYAH v2 after formal governance migration.

### Inferences

- Durable open-loop objects are necessary to make offloading reliable across sessions.
- A briefing object and refresh-proof object are needed to prevent conversational claims of unexecuted work.
- Cross-pillar retrieval should be relevance-gated to preserve analytical quality and privacy boundaries.

### Missing / implementation blockers

- Exact repository schemas and runtime scheduler implementation have not been inspected in this environment.
- HIMAYAH v2 has been owner-approved as a design direction but not yet implemented/verified.
- Drive polling/discovery runtime has not been observed.
- Persistent reminder behavior across VPS restart has not been tested.

---

## 35. Change-control note

This objective expands the operating model beyond the 2026-09-15 PFOS package by adding owner-approved scheduled brief windows, twice-daily Drive evidence discovery, durable cognitive open loops, accepted cooling-period continuity, trusted-boundary recovery expectations, and the planned HIMAYAH v2 interface.

Implementation MUST record the old/new rules, affected contracts, migration, rollback, tests, owner approval, and verification evidence under the project change-control mechanism before those changes are called canonical runtime behavior.
