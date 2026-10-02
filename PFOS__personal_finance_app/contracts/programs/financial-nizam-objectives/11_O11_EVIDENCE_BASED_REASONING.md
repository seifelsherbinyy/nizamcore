# Financial NIZAM Objective O11 — Evidence-Based Reasoning

**Status:** PROPOSED OVERHAUL DESIGN — owner-approved objective, implementation not yet verified  
**Objective ID:** O11  
**Objective name:** Evidence-Based Reasoning  
**Program:** Financial NIZAM / PFOS / MAL implementation namespace  
**Owner:** Seif ElSherbiny  
**Version:** 0.1.0-design  
**Sensitivity:** review_before_commit  
**Owning phase:** Phase 11 — evidence assembly, weighting, contradiction handling, argumentative reasoning, confidence, source-preserving explanation  
**Precedence:** safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting owning subordinate contract → verified runtime evidence → historical/draft material

---

## 1. Objective

**[FACT][AGREED]** O11 defines how Financial NIZAM gathers, classifies, weighs, contradicts, combines, communicates, and audits evidence used to support a material financial recommendation, challenge, forecast interpretation, regime explanation, merchant interpretation, or long-term strategic claim.

**[FACT][AGREED]** O11 does not create financial truth. O1 owns canonical financial facts. O8 owns longitudinal reconstruction. O9 owns merchant/behavioral enrichment. O10 owns cross-domain association validity. O11 consumes those outputs and assembles an evidence-grounded argument that is understandable to the owner.

**[FACT][AGREED]** Financial NIZAM must reason with Seif using clear proof and changing evidence. If the first argument does not resolve the decision, the system should seek a materially different evidence class rather than merely restating the same point more forcefully.

**[FACT][AGREED]** The owner wants the system to be able to draw, when relevant, from personal financial history, deterministic financial-engine outputs, official sources, professional research, market-implied signals, foreign-exchange and macroeconomic evidence, social/community information, prediction/expectation markets, journals, registered conversation history, and other permitted NIZAM evidence.

**[FACT][AGREED]** Source quantity is not authority. Ten social-media posts repeating the same rumor do not outweigh one current authoritative source simply because the count is larger.

**[FACT][AGREED]** Material numeric claims about Seif's finances must come from deterministic/statistical engines or registered source data. The conversational layer may explain outputs but must not invent or manually calculate authoritative money values, percentages, probabilities, confidence scores, or forecast errors.

**[INFERENCE][PROPOSED]** O11 is the epistemic control plane for Financial NIZAM: it determines not what is financially true, but what evidence is admissible for a claim, how strong that evidence is, what contradicts it, what remains unknown, and how forcefully the system may communicate the conclusion.

---

## 2. Governing source decisions

### 2.1 Existing PFOS evidence rules

**[FACT]** The existing Financial NIZAM Research and Evidence Register defines evidence tiers: E1 official/primary, E2 systematic/professional synthesis, E3 reputable secondary, E4 expert commentary, E5 community/social, and E6 unverified anecdote.

**[FACT]** The existing register requires future research objects to preserve claim/question, source, source class, publication/current date, retrieval date, finding, limitations, confidence, architecture implication, contradictory sources, and review date.

**[FACT]** Existing PFOS precedence is safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting subordinate contract → verified runtime evidence → historical/draft material.

**[FACT]** The Decision Engine requires facts, missing/unknown items, options, hard constraints, strongest counterargument, scenario sensitivity, confidence, and evidence references for material decisions.

**[FACT]** The Validation contract requires material state to trace to evidence or explicit assumption, forecast confidence to degrade when evidence is stale/error-prone, and external research queries not to leak unnecessary private transaction data.

**[FACT]** Provider/regulatory claims require fresh authoritative research rather than memory-based reconstruction.

### 2.2 Owner decisions incorporated into O11

**[FACT][AGREED]** Financial NIZAM should debate materially harmful decisions assertively and with high friction, escalating to additional evidence classes when necessary.

**[FACT][AGREED]** Historical financial analysis, quantified future consequences, counterfactuals, better alternatives, external macroeconomic evidence, social signals, prediction-market/expectation signals, and foreign-exchange evidence may each contribute to a challenge when relevant.

**[FACT][AGREED]** If a reasoning method repeatedly fails to help Seif understand or improve decisions, the system should later learn that the communication method was ineffective. O20 will own persuasion-learning; O11 must preserve the evidence and argument trace needed by O20.

**[FACT][AGREED]** External news, public sources, social posts, research artifacts, and other permitted evidence should be preserved readably within the owner-approved Trusted NIZAM Boundary, subject to future HIMAYAH v2 implementation and hard-secret exclusions.

**[FACT][AGREED]** The system should be able to show why a recommendation changed when new evidence arrives.

---

## 3. Scope

O11 governs:

1. claim registration;
2. evidence registration;
3. evidence class and source-class assignment;
4. source independence and duplication analysis;
5. freshness and temporal relevance;
6. geographic and jurisdictional relevance;
7. personal-context relevance;
8. source authority;
9. source reliability history;
10. evidence directness;
11. evidence corroboration;
12. contradiction handling;
13. counterevidence search;
14. missing-evidence registration;
15. assumption registration;
16. weak-signal handling;
17. market-implied and expectation-signal handling;
18. rumor handling;
19. evidence weighting;
20. argument assembly;
21. argument escalation across evidence classes;
22. strongest counterargument requirement;
23. confidence decomposition;
24. evidence-that-would-change-the-conclusion;
25. research freshness requirements;
26. private-context query minimization;
27. evidence snapshots and provenance;
28. evidence-preserving Drive persistence;
29. decision/challenge evidence packets;
30. forecast-claim evidence packets;
31. regime-explanation evidence packets;
32. later outcome linkage;
33. audit and computation receipts;
34. validation and tamper tests.

O11 does **not** govern:

- canonical transaction truth;
- account reconciliation;
- direct money arithmetic;
- regime calculation;
- merchant identity resolution itself;
- statistical cross-domain validity itself;
- autonomous financial execution;
- choosing investments or financial products on behalf of the user;
- inventing legal/regulatory/provider facts;
- converting community sentiment into authoritative truth;
- treating market prices or prediction markets as certain forecasts;
- making medical/psychological causal claims from journals or wearables;
- fabricating citations, sources, source dates, quotes, or research runs.

---

## 4. Evidence doctrine

**[FACT][AGREED]** O11 uses the following doctrine:

> **Preserve the source, separate the classes, search for contradiction, prefer direct and current evidence, show uncertainty, and change the conclusion when the evidence changes.**

Every material evidence-backed claim must answer:

- What exactly is the claim?
- Is the claim about Seif's personal financial state, external reality, an expectation, or a hypothesis?
- Which source owns the underlying fact?
- Is the source current enough for the claim?
- Is the source directly relevant to Egypt/MENA/global conditions as applicable?
- Is the evidence independent or merely repeating another source?
- What evidence contradicts the claim?
- What important evidence is missing?
- Which assumptions bridge evidence to conclusion?
- Which numerical outputs came from deterministic/statistical engines?
- What would change or reverse the conclusion?
- What confidence is justified and why?

---

## 5. Evidence planes

O11 MUST NOT collapse all evidence into one tier ladder. Personal evidence and external evidence answer different questions.

### 5.1 Personal canonical evidence plane

Examples:

- reconciled balances;
- posted transactions;
- verified pending transactions;
- obligations and due dates;
- debt/installment records;
- canonical financial snapshot;
- deterministic engine outputs;
- owner-confirmed goals and decisions.

**[FACT]** For claims about Seif's own finances, current canonical personal evidence has priority over generic external advice.

### 5.2 Personal historical evidence plane

Examples:

- trailing transaction history;
- prior decision packets;
- forecast-vs-actual outcomes;
- merchant/category history;
- prior regime states;
- owner-approved journal/session context;
- prior overrides and later outcomes.

**[FACT]** Historical evidence can support pattern claims only to the extent that O8/O9/O10 have established coverage and validity.

### 5.3 External evidence plane

External evidence uses the PFOS E1–E6 source classes defined below.

### 5.4 Model-output plane

Examples:

- deterministic liquidity outputs;
- scenario-engine outputs;
- statistical association estimates;
- forecast distributions;
- counterfactual estimates;
- risk/materiality outputs.

**[FACT]** Model output is not raw evidence. It is derived evidence and must reference its source inputs, model/version, assumptions, time, and uncertainty.

---

## 6. External evidence tiers

| Tier | Source class | Examples | Normal role | Cannot do alone |
|---|---|---|---|---|
| E1 | Official / primary | central bank, regulator, official statistics, provider terms, issuer documentation, law/regulation, audited issuer disclosure | establish authoritative external facts | prove personal behavior or future outcome |
| E2 | Systematic / professional synthesis | institutional research, peer-reviewed/systematic review where relevant, professional market research, established financial-data analysis | synthesize and contextualize evidence | override fresher primary facts without reason |
| E3 | Reputable secondary | established financial press, reputable reporting, high-quality specialist publications | explain events and provide sourced context | become primary authority for rules/provider terms when E1 is available |
| E4 | Expert commentary | named economist/analyst/practitioner commentary with disclosed reasoning | provide interpretation/scenarios | become verified fact merely by expertise |
| E5 | Community / social | Reddit, Facebook, X, forums, community groups, public comments | detect sentiment, practical friction, emerging weak signals, user experience | establish authoritative policy or truth |
| E6 | Unverified anecdote / rumor | unsourced post, forwarded claim, isolated rumor | early-warning watchlist only | drive canonical fact or high-confidence recommendation alone |

**[FACT]** E-tier is not the same as relevance. A current E3 source directly about an Egyptian rule may be more useful to a specific question than an E1 source from another jurisdiction.

**[FACT]** E-tier is not a numerical vote. Corroboration matters only when sources are sufficiently independent.

---

## 7. Market and expectation signals

Market and expectation signals are a separate evidence dimension rather than an E-tier replacement.

Examples:

- FX spot/forward behavior;
- government yields;
- commodity prices;
- equity/credit market repricing;
- inflation breakevens where relevant;
- prediction-market prices where lawful and methodologically appropriate;
- survey expectations;
- consensus forecasts.

Conceptual object:

```yaml
expectation_signal:
  signal_id: opaque_id
  market_or_source: string
  instrument_or_question: string
  observed_at: timestamp
  horizon: string_or_null
  observed_value_ref: structured_ref
  interpretation: string
  source_class: MARKET|SURVEY|PREDICTION_MARKET|CONSENSUS|OTHER
  liquidity_quality: HIGH|MEDIUM|LOW|UNKNOWN
  manipulation_risk: HIGH|MEDIUM|LOW|UNKNOWN
  jurisdiction_relevance: string
  limitations: []
  provenance_refs: []
```

**[FACT]** A market price or prediction-market probability reflects market participants' aggregate pricing/expectations under that market's structure. It is not certainty and must not be presented as a guaranteed future event.

**[FACT]** Thin, illiquid, manipulable, poorly specified, or irrelevant markets receive lower decision weight.

---

## 8. Claim object

Every material claim should be registered explicitly.

```yaml
claim:
  claim_id: opaque_id
  claim_text: string
  claim_type: PERSONAL_FACT|EXTERNAL_FACT|MODEL_OUTPUT|EXPECTATION|INFERENCE|HYPOTHESIS
  domain: FINANCE|MACRO|FX|CREDIT|MERCHANT|BEHAVIOR|OTHER
  jurisdiction: string_or_null
  time_scope: string
  decision_or_analysis_ref: opaque_ref_or_null
  evidence_refs: []
  counterevidence_refs: []
  assumption_refs: []
  missing_evidence: []
  confidence_class: HIGH|MEDIUM|LOW|INSUFFICIENT
  status: SUPPORTED|CONTESTED|UNRESOLVED|SUPERSEDED
  created_at: timestamp
  review_due_at: timestamp_or_null
  policy_version: string
```

**[FACT]** A claim must not become `SUPPORTED` solely because the conversational model produced plausible prose.

---

## 9. Evidence object

```yaml
evidence_item:
  evidence_id: opaque_id
  source_uri_or_artifact_ref: opaque_ref
  source_title: string_or_null
  source_publisher_or_owner: string
  source_class: PERSONAL_CANONICAL|PERSONAL_HISTORICAL|MODEL_OUTPUT|E1|E2|E3|E4|E5|E6|MARKET_SIGNAL
  publication_or_event_time: timestamp_or_null
  retrieval_time: timestamp
  jurisdiction: string_or_null
  source_span_or_record_ref: opaque_ref_or_null
  finding_summary: string
  directness: DIRECT|INDIRECT|CONTEXTUAL
  independence_group: string_or_null
  freshness: FRESH|AGING|STALE|UNKNOWN
  limitations: []
  contradiction_refs: []
  provenance_hash: string_or_null
  privacy_class: string
  schema_version: string
```

**[FACT]** O11 preserves the original source reference and a bounded summary. It must not replace source evidence with an uncited paraphrase that cannot be traced back.

---

## 10. Independence and duplicate-source control

**[FACT]** Multiple articles may all derive from one press release, one anonymous claim, or one market rumor. Treating them as independent corroboration would inflate confidence.

O11 therefore groups evidence by likely origin:

```yaml
independence_analysis:
  claim_id: opaque_id
  raw_source_count: integer
  independent_origin_count: integer
  origin_groups:
    - origin_group_id: string
      evidence_refs: []
      suspected_common_origin: string_or_null
  duplication_risk: LOW|MEDIUM|HIGH
```

**[FACT][AGREED]** The system should value independent evidence classes and origins over raw source count.

**[INFERENCE][PROPOSED]** The owner's desire for ten or more local/global sources should be implemented as a coverage target for broad research, not as a confidence-voting rule.

---

## 11. Freshness contract

Claims with time-sensitive truth require freshness rules.

Examples include:

- provider terms;
- card/bank fees;
- lending rules;
- current regulations;
- inflation;
- FX conditions;
- policy rates;
- market prices;
- current economic events;
- software/API capabilities.

```yaml
freshness_policy:
  claim_domain: string
  max_age_for_high_confidence: duration_or_policy_ref
  downgrade_after: duration_or_policy_ref
  hard_expiry_after: duration_or_policy_ref
  authoritative_refresh_required: boolean
```

**[FACT]** Stale evidence does not disappear; its confidence and role change.

**[FACT]** When fresh primary evidence is required but unavailable, the system should return `MISSING` or `INSUFFICIENT_DATA`, not reconstruct current truth from memory.

---

## 12. Geographic and jurisdictional relevance

**[FACT][AGREED]** Seif's current financial system primarily operates in Egypt, while MENA and global macro conditions may influence purchasing power, income resilience, assets, and external risk.

O11 should distinguish:

- Egypt-specific evidence;
- MENA regional evidence;
- global evidence;
- foreign evidence used only as analogy.

**[FACT]** A rule, fee, credit-reporting practice, or provider behavior from another jurisdiction must not be presented as directly applicable to Egypt without supporting evidence.

**[INFERENCE][PROPOSED]** Global sources are best used to explain transmission channels and scenarios unless Egypt-specific evidence confirms local applicability.

---

## 13. Relevance scoring dimensions

O11 may use a deterministic evidence-relevance engine. It may consider:

- source authority;
- directness;
- freshness;
- jurisdiction match;
- decision match;
- personal-history match;
- independence;
- corroboration;
- contradiction burden;
- known historical reliability;
- sample quality where statistical;
- model calibration where derived.

**[FACT]** The LLM must not manually invent the final numerical relevance/weight score.

---

## 14. Evidence weighting contract

Conceptual output:

```yaml
evidence_weight_receipt:
  receipt_id: opaque_id
  claim_id: opaque_id
  policy_version: string
  engine_version: string
  evaluated_at: timestamp
  evidence_refs: []
  factors_used: []
  factor_outputs_ref: opaque_ref
  contradiction_penalty_ref: opaque_ref_or_null
  freshness_penalty_ref: opaque_ref_or_null
  independence_adjustment_ref: opaque_ref_or_null
  final_strength_class: STRONG|MODERATE|WEAK|INSUFFICIENT
  confidence_class: HIGH|MEDIUM|LOW|INSUFFICIENT
```

**[FACT]** A high-authority but stale source may be downgraded. A fresh social signal may be timely but remain weak authority. O11 must preserve both dimensions rather than forcing all evidence onto one crude scale.

---

## 15. Contradiction handling

O11 MUST actively look for contradictory evidence for material claims.

Contradiction classes include:

- factual contradiction;
- time-version contradiction;
- jurisdiction mismatch;
- method/model disagreement;
- expectation disagreement;
- personal-history counterexample;
- source-quality conflict;
- definition mismatch.

```yaml
contradiction_record:
  contradiction_id: opaque_id
  claim_id: opaque_id
  evidence_a_ref: opaque_ref
  evidence_b_ref: opaque_ref
  contradiction_type: string
  resolvable_by_precedence: boolean
  resolution_ref: opaque_ref_or_null
  unresolved_reason: string_or_null
  impact_on_confidence: string
```

**[FACT]** O11 must not average contradictory balances, provider rules, or factual statements merely to create one answer.

**[FACT]** If a higher-precedence source clearly resolves the contradiction, the losing source remains in the record as superseded/contradicted evidence.

---

## 16. Counterevidence requirement

For HIGH or CRITICAL materiality recommendations, O11 should require a counterevidence pass.

Questions include:

- What evidence supports doing the opposite?
- What historical examples weaken the recommendation?
- What external scenario makes the recommendation wrong?
- What assumption is most fragile?
- Which missing source could reverse the conclusion?

**[FACT][AGREED]** O11 must support O19's requirement that challenge be evidence-driven rather than merely forceful.

---

## 17. Assumptions and missing evidence

Assumptions must be explicit:

```yaml
assumption:
  assumption_id: opaque_id
  text: string
  owner: ENGINE|RESEARCH|USER|POLICY
  reason_needed: string
  sensitivity: HIGH|MEDIUM|LOW
  evidence_that_would_resolve: string_or_null
```

**[FACT]** An assumption cannot be formatted as a verified fact.

Missing evidence must be explicit:

```yaml
missing_evidence_item:
  missing_id: opaque_id
  claim_or_decision_ref: opaque_ref
  description: string
  materiality: HIGH|MEDIUM|LOW
  acquisition_path: string_or_null
  blocks_conclusion: boolean
```

**[FACT]** When missing evidence blocks a safe conclusion, O11 returns `INSUFFICIENT_DATA` rather than manufacturing confidence.

---

## 18. Weak-signal handling

**[FACT][AGREED]** Social media, Reddit, Facebook, forums, public discussion, rumors, and other weak signals may be useful as early-warning sensors.

Weak signals may support:

- issue discovery;
- sentiment discovery;
- emerging merchant/provider friction;
- rumor watchlists;
- questions to research through stronger sources;
- identifying what market participants/users are discussing.

Weak signals may not alone support:

- canonical financial facts;
- provider/regulatory rules;
- a high-confidence macro claim;
- a high-impact recommendation that contradicts stronger evidence;
- a causal personal-behavior claim.

Conceptual object:

```yaml
weak_signal:
  signal_id: opaque_id
  observed_at: timestamp
  source_platform: string
  source_ref: opaque_ref
  claim_summary: string
  source_class: E5|E6
  repetition_count: integer
  estimated_independent_origin_count: integer
  corroborating_stronger_evidence_refs: []
  contradicting_evidence_refs: []
  status: WATCH|CORROBORATED|DISPROVEN|STALE|UNRESOLVED
```

---

## 19. Rumor escalation protocol

When a rumor is relevant to the owner's finances:

1. preserve the rumor as E6/E5 evidence;
2. identify the underlying claim;
3. search for primary/official corroboration;
4. search professional/reputable secondary coverage;
5. inspect market reaction if relevant;
6. classify whether the rumor is independently repeated or merely copied;
7. identify plausible financial exposure;
8. create a watch condition rather than changing canonical truth;
9. update when stronger evidence arrives;
10. record whether the rumor was later confirmed, disproven, or unresolved.

**[FACT]** Rumor preservation is not rumor endorsement.

---

## 20. Research request contract

```yaml
research_request:
  research_id: opaque_id
  question: string
  decision_or_claim_ref: opaque_ref
  required_source_classes: []
  target_jurisdictions: []
  freshness_requirement: string
  minimum_independent_origins: integer_or_null
  private_context_minimized: boolean
  prohibited_private_fields: []
  expected_output: string
  approval_required: boolean
```

**[FACT]** Research queries should use the minimum personal detail necessary. The system should not send raw transaction histories to external research services merely to answer a generic market question.

---

## 21. Evidence packet for a material decision

```yaml
decision_evidence_packet:
  packet_id: opaque_id
  decision_id: opaque_id
  generated_at: timestamp
  canonical_state_version: string
  regime_ref: opaque_ref
  materiality_ref: opaque_ref_or_null
  personal_fact_refs: []
  historical_evidence_refs: []
  model_output_refs: []
  external_evidence_refs: []
  expectation_signal_refs: []
  weak_signal_refs: []
  counterevidence_refs: []
  assumption_refs: []
  missing_evidence_refs: []
  evidence_strength_receipts: []
  strongest_support_ref: opaque_ref_or_null
  strongest_countercase_ref: opaque_ref_or_null
  confidence_class: HIGH|MEDIUM|LOW|INSUFFICIENT
  evidence_that_changes_result: []
  computation_receipt_ref: opaque_ref
```

**[FACT]** The packet must preserve evidence diversity and conflict rather than flatten everything into one prose summary.

---

## 22. Argument assembly

A material recommendation should normally communicate in this order:

1. direct recommendation or current conclusion;
2. current financial regime and why relevant;
3. strongest personal financial evidence;
4. quantified impact from registered engines;
5. historical comparison where valid;
6. external evidence where relevant;
7. uncertainty and key assumptions;
8. strongest counterargument;
9. alternative action(s);
10. evidence that would change the conclusion.

**[FACT][AGREED]** The system should show enough proof to reason with Seif rather than merely instruct him.

**[INFERENCE][PROPOSED]** Evidence presentation should be progressively disclosed: concise first, deeper on challenge, full audit trail on demand.

---

## 23. Escalating evidence ladder for disagreement

When Seif disputes a materially adverse recommendation, O11 should avoid rhetorical repetition.

A preferred escalation sequence is:

1. canonical personal state and protection facts;
2. historical personal pattern evidence;
3. deterministic future consequence;
4. counterfactual comparison;
5. better alternative with quantified tradeoff;
6. strategic-goal/opportunity-cost evidence;
7. cross-domain evidence if O10 says it is eligible;
8. Egypt/MENA/global macro evidence;
9. market-implied or expectation evidence;
10. social/weak signals as contextual support only.

**[FACT][AGREED]** The exact order may change when one evidence class is clearly more relevant, but each escalation should contribute materially new information.

**[FACT]** O19 owns the high-friction challenge process. O11 supplies the evidence packets and argumentative proof.

---

## 24. Strongest counterargument contract

Every HIGH/CRITICAL decision recommendation should preserve the best evidence-backed counter-case.

```yaml
counterargument:
  counterargument_id: opaque_id
  recommendation_ref: opaque_ref
  alternative_conclusion: string
  supporting_evidence_refs: []
  assumptions: []
  conditions_under_which_it_wins: []
  unresolved_points: []
  confidence_class: HIGH|MEDIUM|LOW|INSUFFICIENT
```

**[FACT]** The counterargument must be substantive. A token sentence such as “there are risks either way” does not satisfy the requirement.

---

## 25. Confidence decomposition

O11 should avoid one mysterious confidence number.

Confidence should decompose into dimensions such as:

- personal-state confidence;
- historical-coverage confidence;
- external-fact confidence;
- model-calibration confidence;
- forecast confidence;
- jurisdiction-relevance confidence;
- cross-domain-signal confidence;
- contradiction burden;
- freshness confidence.

Conceptual object:

```yaml
confidence_profile:
  claim_or_decision_ref: opaque_ref
  dimensions:
    personal_state: class_or_ref
    history: class_or_ref
    external: class_or_ref
    model: class_or_ref
    forecast: class_or_ref
    jurisdiction: class_or_ref
    cross_domain: class_or_ref
  contradiction_burden: LOW|MEDIUM|HIGH
  overall_class: HIGH|MEDIUM|LOW|INSUFFICIENT
  engine_receipt_ref: opaque_ref
```

**[FACT]** Overall confidence is engine/policy-owned. The language model cannot improvise it.

---

## 26. Evidence that would change the conclusion

Every consequential conclusion should state reversal conditions.

Examples:

- a balance correction;
- a new obligation;
- salary/income arriving or being delayed;
- an updated FX/inflation release;
- a provider-policy change;
- a different price/financing offer;
- stronger contradictory historical evidence;
- forecast calibration deterioration;
- a material change in financial regime.

**[FACT][AGREED]** This prevents NIZAM from becoming attached to its own argument after the evidence changes.

---

## 27. Evidence change and conclusion supersession

When new evidence changes a conclusion:

1. preserve the old claim/recommendation;
2. preserve the evidence known at that time;
3. register the new evidence;
4. recompute the affected claim/decision packet;
5. issue a successor conclusion;
6. explain what changed;
7. never rewrite the old recommendation as though the new evidence had always been known.

**[FACT]** This requirement supports O8's anti-hindsight rule and O12's forecast-accountability objective.

---

## 28. Historical personal evidence

Personal-history arguments must specify:

- comparable decision/event definition;
- historical window;
- evidence coverage;
- number of comparable events;
- regime comparability;
- confounders where relevant;
- counterexamples;
- outcome definition;
- whether the pattern was identified before or after the current decision.

**[FACT]** “You always do this” is not an admissible financial argument.

**[FACT]** Historical patterns must come from registered historical analysis rather than conversational impression.

---

## 29. External macroeconomic evidence

O11 may assemble external evidence relating to:

- Egypt inflation;
- monetary policy;
- FX conditions;
- purchasing-power erosion;
- labor/income conditions;
- sovereign/regional risk;
- relevant commodity or import-price channels;
- regional or global shocks;
- banking/credit conditions;
- other material economic developments.

**[FACT]** O16 will own the persistent Economic Early-Warning Radar. O11 may consume O16 outputs once implemented and verified.

**[FACT]** Macro evidence may alter risk scenarios and assumptions, but it does not directly alter verified personal balances or transactions.

---

## 30. Social and community evidence

O11 should preserve public social/community evidence in readable form where policy permits.

For each material social claim, preserve:

- platform/source;
- post/thread reference;
- date/time;
- exact or bounded source span where technically permitted;
- claim summary;
- whether firsthand or repeated;
- known corroboration;
- contradiction;
- relevance;
- confidence limitation.

**[FACT]** Community consensus may be useful for experience patterns, but it remains lower authority than primary evidence for rules, fees, provider policies, or macro statistics.

---

## 31. Source preservation and Drive design

Under the owner-approved HIMAYAH v2 direction:

- public external research may be stored readably;
- permitted personal records default to `trusted_private` or `trusted_sensitive` inside the Trusted NIZAM Boundary;
- security secrets remain excluded from Drive;
- evidence should preserve readable context and provenance;
- Drive acts as durable recovery/evidence mirror, not a second calculation authority;
- canonical financial state remains single-writer governed.

**[FACT]** HIMAYAH v2 remains a design direction until its governing contract is formally updated and runtime implementation is verified.

---

## 32. Agent responsibilities

### 32.1 Finance Orchestrator

- requests evidence packets;
- binds them to canonical state/version;
- ensures required evidence classes are present;
- routes unresolved contradictions;
- does not invent missing evidence.

### 32.2 Research Agent

- executes registered research requests;
- prioritizes required source classes;
- preserves source metadata and findings;
- seeks contradictory sources;
- records freshness and limitations;
- does not decide canonical financial state.

### 32.3 Decision Agent

- consumes O11 evidence packets;
- explains the comparative decision;
- requests deeper evidence when challenged;
- preserves strongest counterargument;
- cannot fabricate engine outputs.

### 32.4 Monitoring / MARSAD interface

- supplies current external signals where relevant;
- keeps rumors/weak signals separate from verified events;
- provides provenance and confidence.

### 32.5 Privacy & Approval Gate

- enforces current policy and future HIMAYAH v2 classification;
- minimizes external query leakage;
- blocks credentials/secrets from Drive/research queries.

### 32.6 Audit Agent

- verifies claims trace to evidence;
- verifies source class and freshness;
- checks counterevidence search occurred when required;
- validates computation receipts;
- detects source laundering and duplicate-source inflation.

---

## 33. Agent handoff envelope

O11 uses the shared PFOS envelope:

```yaml
agent_handoff:
  task_id: opaque_id
  request: string
  canonical_state_version: string
  input_artifacts: []
  assumptions: []
  unresolved_items: []
  expected_output: string
  write_permissions: []
  approval_required: boolean
  completion_status: PENDING|PARTIAL|COMPLETE|FAILED
  audit_refs: []
```

O11-specific fields SHOULD include:

```yaml
  claim_refs: []
  required_source_classes: []
  freshness_policy_ref: opaque_ref
  counterevidence_required: boolean
  jurisdiction_scope: []
  private_query_minimization_ref: opaque_ref
```

---

## 34. Conversational contract

For a material recommendation, the conversational layer should be able to answer:

- What are you recommending?
- What personal facts support it?
- Which calculations were actually run?
- Which historical evidence supports it?
- Which external evidence matters?
- What contradicts the recommendation?
- What are the important assumptions?
- How current is the evidence?
- How confident are we and why?
- What would change the conclusion?

**[FACT][AGREED]** If Seif asks for more proof, the agent should reveal deeper supporting evidence rather than simply repeat the conclusion.

---

## 35. Computation and evidence-proof requirement

Any material O11 output must have an evidence receipt.

```yaml
evidence_reasoning_receipt:
  receipt_id: opaque_id
  generated_at: timestamp
  claim_or_decision_refs: []
  canonical_state_version: string_or_null
  evidence_policy_version: string
  research_runs: []
  evidence_refs: []
  independent_origin_count: integer
  counterevidence_refs: []
  assumption_refs: []
  missing_evidence_refs: []
  model_output_refs: []
  freshness_checks: []
  contradiction_checks: []
  evidence_weight_receipts: []
  confidence_profile_ref: opaque_ref
  evidence_that_changes_result: []
  completion_status: COMPLETE|PARTIAL|FAILED
  failure_reason: string_or_null
```

**[FACT]** The conversational agent cannot claim “I checked the evidence,” “sources agree,” “the market expects,” or “history shows” unless the receipt or source records support that statement.

---

## 36. Ledger and audit model

O11 should append/supersede, never silently overwrite:

- claim registrations;
- evidence registrations;
- contradiction records;
- source-class changes;
- confidence changes;
- evidence snapshots;
- research runs;
- argument packets;
- successor conclusions;
- later outcome links;
- audit findings.

**[FACT]** Evidence that later proves wrong remains part of the audit history and should be marked disproven/superseded rather than deleted from history.

---

## 37. Failure behavior

### 37.1 No authoritative evidence available

Return the best-supported lower-tier evidence with an explicit limitation or `INSUFFICIENT_DATA`; do not pretend authority exists.

### 37.2 Sources conflict

Show the conflict, apply documented precedence where valid, and preserve unresolved disagreement.

### 37.3 Evidence is stale

Downgrade confidence, attempt refresh, and block current-sensitive claims if freshness is required.

### 37.4 Many sources repeat one origin

Collapse them into one independence group; do not increase confidence merely because repetition is high.

### 37.5 Social rumor is widespread

Treat prevalence as a signal of attention, not confirmation of truth.

### 37.6 Prediction market / market signal is thin

Downgrade decision weight and preserve liquidity/manipulation limitations.

### 37.7 External research unavailable

Continue with personal/canonical evidence if sufficient; otherwise return missing evidence rather than fabricate research.

### 37.8 Private-context retrieval unavailable

Do not invent prior journal/session evidence. Continue without it or mark the gap.

### 37.9 Evidence receipt missing

Material evidence-based claim is unproven and must not be presented as verified analysis.

---

## 38. Acceptance criteria

O11 is acceptable only when all of the following are demonstrated:

1. material claims trace to evidence;
2. personal facts and external facts remain separate;
3. model outputs preserve inputs/version/assumptions;
4. E1–E6 source classes are implemented;
5. market/expectation signals remain distinct from factual authority;
6. freshness is enforced;
7. jurisdiction mismatch is visible;
8. duplicate-source inflation is prevented;
9. contradictory sources remain visible;
10. assumptions remain explicit;
11. missing evidence can block a conclusion;
12. weak signals cannot silently become facts;
13. rumors trigger research/watch behavior rather than canonical changes;
14. strongest counterargument exists for required decisions;
15. evidence-that-changes-result is preserved;
16. disagreement escalation uses materially new evidence;
17. private research queries are minimized;
18. readable evidence persistence follows HIMAYAH policy;
19. old conclusions remain reconstructable after evidence changes;
20. every material claim has a successful evidence-reasoning receipt.

---

## 39. Minimum test matrix

1. E1 official rule conflicts with E5 community claim — E1 wins factual authority, E5 retained as experience signal.
2. Ten news stories repeat one press release — independent origin count remains one.
3. Current E3 Egypt report conflicts with stale E1 data release — system distinguishes freshness and claim type rather than blindly ranking by tier.
4. Unverified rumor appears on multiple social platforms — watchlist only.
5. Prediction market moves sharply but is illiquid — low decision weight.
6. Personal canonical balance conflicts with generic financial article — personal state governs personal affordability.
7. Historical pattern has poor coverage — confidence downgraded.
8. User challenges recommendation — second response uses new evidence class, not repetition.
9. Strong counterargument exists — packet preserves it.
10. Research unavailable — system marks gap.
11. Provider terms stale — current-sensitive conclusion blocked pending refresh.
12. Foreign provider rule used for Egypt — jurisdiction mismatch detected.
13. Market signal contradicts official policy guidance — both preserved with different claim roles.
14. Community source identifies practical merchant issue — retained as E5, triggers stronger-source research.
15. Source later disproven — old packet preserved and successor conclusion issued.
16. One source has multiple mirrors/copies — deduplicated by origin.
17. Social source is deleted after capture — preserved evidence snapshot/provenance remains auditable where policy permits.
18. Private journal context unavailable — system does not invent it.
19. LLM attempts to assign a numeric confidence without engine receipt — rejected.
20. Missing receipt but prose says “sources agree” — validation fails.
21. Claim has no counterevidence pass when materiality requires it — validation fails.
22. Research query includes unnecessary raw account identifiers — privacy validation fails.
23. New authoritative evidence reverses conclusion — successor path works without rewriting history.
24. Tamper removes evidence-proof section — document validator fails.

---

## 40. Verification requirements

Focused verification must prove:

- source-class assignment works;
- claim/evidence links are resolvable;
- independence grouping works;
- freshness rules execute;
- contradiction records persist;
- assumptions and missing evidence are distinct;
- weak-signal rules execute;
- market/expectation signal rules execute;
- evidence escalation can fetch a new class;
- strongest counterargument is required where policy says so;
- computation/evidence receipts are emitted;
- private query minimization is enforced;
- source snapshots are read-back verifiable where stored;
- Drive mirror behavior obeys current HIMAYAH policy;
- tampering with a required evidence field or section causes validation failure.

The repository gate must then run. A check observed only to pass is not proven until a deliberate tamper causes it to fail.

---

## 41. Migration strategy

### Stage 1 — Evidence register normalization

Normalize existing research/evidence records into claim/evidence/source-class objects without changing current financial calculations.

### Stage 2 — Research and freshness registry

Implement freshness policies, source metadata, jurisdiction scope, and source preservation.

### Stage 3 — Independence and contradiction engine

Add duplicate-origin grouping, contradiction records, and counterevidence requirements.

### Stage 4 — Decision evidence packets

Bind O11 packets to O3 decisions and O19 challenge workflows.

### Stage 5 — External intelligence integration

Consume O16/O17 external radar and weak-signal outputs when those objectives are implemented.

### Stage 6 — Outcome and persuasion learning

Expose evidence/argument traces to O12/O20/O22 for calibration and communication-effectiveness learning.

---

## 42. Required implementation artifacts

At minimum:

- `evidence_item` schema;
- `claim` schema;
- `contradiction_record` schema;
- `assumption` schema;
- `missing_evidence_item` schema;
- `expectation_signal` schema;
- `weak_signal` schema;
- `research_request` schema;
- `decision_evidence_packet` schema;
- `confidence_profile` schema;
- `evidence_reasoning_receipt` schema;
- source-class policy;
- freshness-policy registry;
- jurisdiction-relevance policy;
- independence/deduplication engine;
- contradiction/counterevidence engine;
- evidence-weight engine;
- research-agent contract;
- evidence snapshot/persistence contract;
- O3/O19 handoff interfaces;
- audit/validation fixtures;
- recovery/read-back tests.

---

## 43. Dependencies on other objectives

O11 depends on:

- O1 Financial Truth for personal canonical facts;
- O3 Decision Intelligence for decision packets;
- O7 Regime Management for regime context;
- O8 Longitudinal Intelligence for historical evidence;
- O9 Merchant & Behavioral Intelligence for merchant/behavioral evidence;
- O10 Cross-Domain Decision Intelligence for cross-pillar signal validity.

O11 provides evidence services to:

- O12 Forecast Accountability;
- O16 Economic Early-Warning Radar;
- O17 Weak-Signal & Expectation Intelligence;
- O19 Adversarial Decision Protection;
- O20 Persuasion Learning;
- O21 Decision Outcome Attribution;
- O22 Closed-Loop Financial Coaching;
- O28 Dynamic Materiality;
- later strategy/review objectives.

**[FACT]** Dependency does not grant write authority. O11 cannot mutate upstream truth stores.

---

## 44. Explicit non-goals

O11 does not aim to:

- maximize the number of citations;
- prove the agent's preferred conclusion;
- scrape the internet indiscriminately;
- convert social consensus into fact;
- provide an illusion of certainty;
- eliminate owner judgment;
- conceal contradictory evidence;
- make every decision slower;
- fetch unrelated intimate context;
- create autonomous financial actions;
- replace regulatory, legal, or professional authority;
- use inaccessible or fabricated sources.

---

## 45. Definition of done

O11 is done only when a material Financial NIZAM recommendation can be reconstructed end-to-end:

> claim → canonical personal evidence → historical evidence → external evidence → source classes → freshness/jurisdiction checks → independence grouping → contradictions → assumptions/missing evidence → model outputs → confidence profile → strongest counterargument → evidence that changes result → conversational explanation → audit receipt → later supersession/outcome.

And when the system can prove that:

- every material claim has source/evidence lineage;
- weak signals remain weak until corroborated;
- source count cannot manufacture confidence;
- contradictory evidence remains visible;
- changing evidence can change the recommendation;
- no authoritative money number was invented by the conversational model;
- evidence used in a challenge is retrievable and auditable;
- the owner can request deeper proof and receive the actual evidence trail.

---

## 46. Decision register entries opened by this document

### O11-D01 — Source count is not authority

**[FACT][PROPOSED]** Confidence must depend on source class, independence, freshness, relevance, contradiction burden, and model validity rather than raw number of sources.

### O11-D02 — Personal truth outranks generic advice for personal-state claims

**[FACT][PROPOSED]** Reconciled personal state governs claims about Seif's own balances, obligations, liquidity, and affordability.

### O11-D03 — Weak signals are sensors, not truth

**[FACT][PROPOSED]** Social/community/rumor evidence may trigger investigation and contextual warnings but cannot silently become canonical facts.

### O11-D04 — Market expectations are not facts

**[FACT][PROPOSED]** Market and prediction-market signals describe pricing/expectations under specific market conditions and must preserve liquidity/manipulation/method limitations.

### O11-D05 — Counterevidence is mandatory for material claims

**[FACT][PROPOSED]** HIGH/CRITICAL decision reasoning requires a substantive search for the best opposing evidence.

### O11-D06 — New evidence creates successor conclusions

**[FACT][PROPOSED]** A changed recommendation must preserve the old evidence state and explain what new evidence caused the change.

### O11-D07 — Evidence escalation must add information

**[FACT][PROPOSED]** Repeating the same reasoning more aggressively does not satisfy the challenge protocol; later rounds should introduce materially different evidence where available.

### O11-D08 — Evidence proof is required

**[FACT][PROPOSED]** The agent cannot claim research, corroboration, history, market expectation, or evidence consensus without source records and a successful reasoning receipt.

---

## 47. Evidence classification for this design document

**[FACT]** The current PFOS Evidence Register defines E1–E6 external evidence tiers and requires future evidence rows to preserve source, source class, dates, findings, limitations, confidence, contradictory sources, and review date.

**[FACT]** The current PFOS Decision Engine requires evidence references, confidence, strongest counterargument, and scenario sensitivity for material decisions.

**[FACT]** The owner explicitly requested aggressive evidence-backed challenge, use of changing evidence classes, historical/counterfactual/macro/social/market signals, and learning from later outcomes.

**[INFERENCE]** Treating market signals as a parallel evidence dimension is preferable to forcing them into the E1–E6 authority hierarchy because market prices represent expectations rather than authoritative statements of fact.

**[ASSUMPTION]** Exact numerical evidence-weighting coefficients, freshness windows, and source-reliability priors will be defined during implementation and must be validated rather than invented in this design document.

**[MISSING]** Runtime evidence proving an implemented O11 evidence engine, research scheduler, contradiction engine, and evidence receipt does not yet exist in this environment.

---

## 48. Open items before implementation

1. Exact freshness windows by claim domain.
2. Exact independence-grouping algorithm.
3. Exact evidence-weighting coefficients and calibration method.
4. Exact local/global research coverage target for O16, distinct from confidence weighting.
5. Exact prediction-market eligibility and jurisdictional/legal constraints.
6. Exact source-snapshot policy for copyrighted/public web evidence.
7. Exact Drive folder taxonomy for evidence snapshots and research registers.
8. Exact relationship between O11 and MARSAD runtime interfaces.
9. Exact research-budget/cost controls.
10. Exact rules for preserving deleted/changed social-media evidence while respecting platform and copyright constraints.
11. Runtime implementation and validation.
12. Formal HIMAYAH v2 contract update.

---

## 49. Next objective

**O12 — Forecast Accountability** should define the closed loop that preserves every material forecast, its assumptions and confidence, observes actual outcomes later, calculates forecast error through deterministic/statistical engines, and adjusts future model weight/calibration without rewriting history.
