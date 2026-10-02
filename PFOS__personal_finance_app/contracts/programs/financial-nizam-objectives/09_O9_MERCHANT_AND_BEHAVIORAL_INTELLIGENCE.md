# Financial NIZAM Objective O9 — Merchant & Behavioral Intelligence

**Status:** PROPOSED OVERHAUL DESIGN — owner-approved objective, implementation not yet verified  
**Objective ID:** O9  
**Objective name:** Merchant & Behavioral Intelligence  
**Program:** Financial NIZAM / PFOS / MAL implementation namespace  
**Owner:** Seif ElSherbiny  
**Version:** 0.1.0-design  
**Sensitivity:** review_before_commit  
**Owning phase:** Phase 9 — merchant resolution, spend-pattern intelligence, recurrence, unusualness, leakage, behavioral baselines, merchant research  
**Precedence:** safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting subordinate contract → verified runtime evidence → historical/draft material

---

## 1. Objective

**[FACT][AGREED]** O9 consumes reconciled transactions and canonical financial facts from O1, protection state from O2, decision records from O3, capital-allocation context from O4, wealth trajectory from O5, attention/continuity state from O6, financial regime from O7, and historical windows/baselines from O8. O9 MUST NOT create a second transaction ledger, account balance source, budget truth, obligation registry, forecast authority, regime engine, or decision authority.

**[FACT][AGREED]** Financial NIZAM must progressively understand merchants and spending behavior well enough to answer where money is going, whether a charge is recurring, whether a merchant identity is already known under a different alias, whether a pattern is unusual for Seif, whether a spending pattern is changing, and whether a merchant/category deserves attention.

**[FACT][AGREED]** Merchant and behavioral intelligence must remain evidence-backed. A merchant resolution, category assignment, recurrence claim, leakage hypothesis, or behavioral pattern must preserve its supporting transactions, source artifacts, historical window, confidence, and policy/model version.

**[FACT][AGREED]** O9 may use deterministic rules, registered merchant mappings, statistical baselines, and bounded model suggestions. The conversational layer may explain these outputs but MUST NOT invent merchant identity, category certainty, behavioral trends, percentages, or monetary totals.

**[FACT][AGREED]** O9 must avoid moralizing spending. The purpose is to detect patterns, inefficiencies, recurring commitments, unusual behavior, and opportunities for better allocation — not to label the owner as irresponsible or to define lifestyle choices as wrong merely because they are discretionary.

**[INFERENCE][PROPOSED]** O9 is the bridge between raw transaction semantics and later decision intelligence: O1 says what transaction occurred; O9 says what merchant/pattern it belongs to and how that pattern behaves over time; O3/O19/O28 decide how much that matters for a contemplated decision.

---

## 2. Governing source decisions

### 2.1 Existing canonical-candidate rules

**[FACT]** `03_FINANCIAL_NIZAM_DATA_MODEL_AND_CONTRACTS.md` defines the canonical `Merchant` entity as `merchant_id, canonical_name, aliases, default_category, category_confidence, country, merchant_type, user_rules` and requires transaction records to preserve both `merchant_raw` and `merchant_normalized`.

**[FACT]** `04_FINANCIAL_NIZAM_TRANSACTION_INGESTION_AND_FORENSICS.md` defines categorization precedence as explicit user rule → verified merchant mapping → high-confidence historical pattern → statement metadata → model suggestion → UNKNOWN/REVIEW.

**[FACT]** The same ingestion contract prohibits deduplication solely on amount/date, requires pending/posted relationship handling, preserves reversals/refunds, distinguishes transfers from spending, and sends low-confidence categories to review instead of forcing classification.

**[FACT]** `21_FINANCIAL_NIZAM_RESEARCH_AND_EVIDENCE_REGISTER.md` distinguishes official/primary evidence from professional synthesis, secondary sources, expert commentary, community/social signals, and unverified anecdote; source freshness and confidence remain explicit.

**[FACT]** `16_FINANCIAL_NIZAM_VALIDATION_TESTS.md` requires deterministic outputs, provenance, one canonical current-state model, protection against transaction double counting, explicit audit events, and failure/tamper testing.

**[FACT]** `13_FINANCIAL_NIZAM_LEDGER_AND_EVENT_SCHEMAS.md` requires corrections to append/supersede historical events rather than erase them and separates model inference from deterministic state.

### 2.2 Owner decisions incorporated into O9

**[FACT][AGREED]** Financial NIZAM should investigate merchants and spending areas across trailing days, weeks, months, quarters, years, and all available history where evidence permits.

**[FACT][AGREED]** The system should recognize duplicate or related evidence across SMS transaction notifications, bank/card statements, exported ledgers, and other registered sources rather than interpreting each occurrence as a new economic event.

**[FACT][AGREED]** Merchant behavior should support detection of recurring commitments, unusualness relative to the owner's own history, category drift, repeated discretionary patterns, and potential leakage or inefficiency.

**[FACT][AGREED]** Merchant evidence may later contribute to dynamic materiality, aggressive challenge, forecast calibration, and cross-pillar analysis, but the later objectives own those decision functions.

**[FACT][AGREED]** Readable financial evidence should be preserved inside the owner-approved Trusted NIZAM Boundary under the proposed HIMAYAH v2 direction, subject to future formal implementation and verification of that governance change.

---

## 3. Scope

O9 governs:

1. canonical merchant identity enrichment;
2. merchant alias resolution;
3. merchant-name normalization;
4. merchant-type classification;
5. merchant-category mapping confidence;
6. merchant research and evidence registration;
7. merchant country/geography when evidence supports it;
8. transaction-channel context where available;
9. recurring-merchant detection;
10. recurring-charge fingerprinting;
11. subscription/commitment candidate detection;
12. merchant concentration analytics;
13. category concentration analytics;
14. spending-frequency analytics;
15. amount-distribution analytics;
16. pay-cycle-relative behavior;
17. day-of-week/time-of-day behavior when timestamps support it;
18. merchant/category trend detection;
19. user-specific behavioral baselines;
20. unusualness scoring inputs;
21. leakage/inefficiency candidate generation;
22. behavioral-pattern evidence packages;
23. merchant/category correction learning;
24. low-confidence review queues;
25. merchant decision-support interfaces;
26. merchant protection interfaces;
27. O8 longitudinal interfaces;
28. O10 cross-domain interfaces;
29. O28 dynamic-materiality interfaces;
30. audit, persistence, Drive mirror, recovery, validation, and tamper proof.

O9 does **not** govern:

- transaction amount truth;
- canonical balance truth;
- payment execution;
- obligation payment execution;
- debt restructuring;
- autonomous cancellation of subscriptions;
- autonomous blocking of merchants;
- direct credit-score calculation without a verified model/data source;
- psychological diagnosis from spending behavior;
- causal claims from correlation alone;
- merchant/category certainty when evidence is weak;
- reclassifying transfers as spending merely because a merchant-like description exists;
- treating cash withdrawal as final merchant spend without downstream evidence;
- inventing merchant geography or corporate ownership;
- live web research without provenance;
- free-form LLM arithmetic.

---

## 4. Merchant intelligence doctrine

**[FACT][AGREED]** O9 follows this doctrine:

> **Resolve identity first, preserve uncertainty, learn from corrections, and interpret behavior against Seif's own verified history.**

A strong merchant system must answer:

- What merchant is this likely to be?
- Has this merchant appeared under other names?
- Is the mapping verified, inferred, or unknown?
- What category usually applies for Seif?
- Is this merchant recurring?
- Is this specific charge part of a recurring series?
- Is the amount/frequency changing?
- Is spending at this merchant/category unusually high or merely normal for the selected period?
- Does the pattern create a recurring liability or commitment?
- Is the pattern materially affecting liquidity, goals, debt, or regime?
- Which source evidence supports the conclusion?
- What evidence would change the conclusion?

---

## 5. Canonical merchant object

O9 MUST reuse the canonical `Merchant` entity rather than create a competing merchant table definition.

Required logical fields:

```yaml
merchant:
  merchant_id: opaque_stable_id
  canonical_name: string
  aliases: []
  default_category: category_id_or_null
  category_confidence: bounded_confidence
  country: string_or_null
  merchant_type: string_or_null
  user_rules: []
```

**[INFERENCE][PROPOSED]** O9 may extend the implementation through subordinate linked records rather than mutating the canonical entity contract in incompatible ways. Suggested linked records include merchant-evidence, merchant-alias, merchant-statistics, recurrence-series, merchant-research, and merchant-correction records.

---

## 6. Merchant alias record

Conceptual subordinate object:

```yaml
merchant_alias:
  alias_id: opaque_id
  merchant_id: canonical_merchant_id
  alias_raw: string
  normalized_form: string
  institution_scope: account_or_provider_scope_or_null
  first_seen_at: timestamp
  last_seen_at: timestamp
  evidence_refs: []
  mapping_method: USER_RULE|VERIFIED_MAPPING|HISTORICAL_PATTERN|STATEMENT_METADATA|MODEL_SUGGESTION
  confidence: bounded_confidence
  status: ACTIVE|REVIEW|REJECTED|SUPERSEDED
  supersedes_alias_id: null_or_id
  policy_version: string
```

**[FACT]** A raw transaction description must remain preserved even after alias normalization.

**[FACT]** A normalized alias is an enrichment layer and does not replace the source description.

---

## 7. Merchant-resolution precedence

O9 must preserve the existing classification hierarchy:

1. explicit owner rule;
2. verified merchant mapping;
3. high-confidence historical pattern;
4. reliable statement/provider metadata;
5. model suggestion;
6. UNKNOWN/REVIEW.

**[FACT]** Lower-precedence evidence cannot silently override a higher-precedence explicit user rule.

**[FACT]** A model suggestion must remain identifiable as model-generated evidence.

**[PROPOSED]** A verified correction may supersede an older explicit rule only through an auditable owner-approved correction workflow.

---

## 8. Merchant-resolution engine contract

Input:

```yaml
merchant_resolution_request:
  transaction_id: id
  merchant_raw: string
  description_raw: string
  institution: string_or_null
  account_id: id
  source_type: string
  source_timestamp: timestamp_or_null
  amount_ref: transaction_amount_reference
  currency: currency
  existing_alias_candidates: []
  historical_context_ref: O8_context_ref_or_null
```

Output:

```yaml
merchant_resolution_result:
  transaction_id: id
  merchant_id: id_or_null
  merchant_normalized: string_or_null
  resolution_method: enum
  confidence: bounded_confidence
  evidence_refs: []
  contradictory_evidence_refs: []
  review_required: boolean
  policy_version: string
  model_version: string_or_null
  computation_receipt_ref: receipt_id
```

**[FACT]** The engine must be idempotent for the same transaction/state/policy inputs.

---

## 9. Merchant identity graph

**[INFERENCE][PROPOSED]** Merchant identity may require a graph-like representation because one economic merchant can surface through:

- different statement descriptors;
- payment processors;
- branch/location suffixes;
- Arabic/English spelling variants;
- abbreviations;
- online versus in-store channels;
- corporate parent versus consumer brand;
- delivery aggregators or marketplaces.

The graph must preserve distinctions rather than flattening all related entities into one name.

Relationship examples:

```yaml
merchant_relationship:
  source_merchant_id: id
  target_merchant_id: id
  relationship_type: ALIAS_OF|BRAND_OF|PROCESSED_BY|MARKETPLACE_SELLER|BRANCH_OF|POSSIBLE_MATCH
  confidence: bounded_confidence
  evidence_refs: []
```

**[FACT]** `POSSIBLE_MATCH` is not canonical identity.

---

## 10. Merchant research contract

Merchant research is permitted when internal evidence is insufficient and the identity/category materially affects analysis.

Research object:

```yaml
merchant_research:
  research_id: id
  merchant_candidate: string
  question: string
  source_records: []
  source_classes: []
  retrieved_at: timestamp
  findings: []
  limitations: []
  confidence: bounded_confidence
  proposed_mapping: merchant_id_or_null
  proposed_category: category_id_or_null
  review_required: boolean
```

**[FACT]** Public web/social research may enrich merchant identity but may not overwrite canonical personal transaction facts.

**[FACT]** Community/social sources are weak evidence for provider policy or merchant identity unless independently corroborated.

---

## 11. Category intelligence contract

O9 consumes canonical budget-category definitions and outputs category evidence for transactions/merchants.

Category assignment must preserve:

- category ID;
- assignment method;
- confidence;
- source evidence;
- historical correction history;
- user-rule precedence;
- model version where applicable.

**[FACT]** Category uncertainty must remain visible.

**[FACT]** O9 must not force every transaction into a category merely to complete a dashboard.

---

## 12. Category-correction learning

When Seif corrects a merchant/category mapping:

1. preserve the old mapping and evidence;
2. append the correction event;
3. update the merchant/user rule where authorized;
4. identify prior affected transactions;
5. determine whether historical views require successor analyses;
6. do not rewrite prior model outputs as if they had always been correct;
7. create learning evidence for future categorization.

**[FACT]** Manual corrections outrank model inference and remain auditable.

---

## 13. Recurrence-series object

Recurring behavior must be represented explicitly rather than inferred every time in chat.

```yaml
recurrence_series:
  series_id: id
  merchant_id: id_or_null
  category_id: id_or_null
  member_transaction_ids: []
  recurrence_type: FIXED|VARIABLE|IRREGULAR|CANDIDATE
  cadence_estimate_ref: engine_output_ref
  amount_distribution_ref: engine_output_ref
  next_expected_window_ref: forecast_ref_or_null
  confidence: bounded_confidence
  obligation_candidate: boolean
  source_evidence_refs: []
  first_observed_at: timestamp
  last_observed_at: timestamp
  status: ACTIVE|DORMANT|ENDED|REVIEW
```

**[FACT]** Recurrence is not automatically an obligation. O7/O2 obligation logic must validate whether a recurring pattern represents a committed liability.

---

## 14. Subscription and recurring-commitment candidates

O9 should detect candidate recurring commitments through:

- regular merchant identity;
- repeated timing pattern;
- repeated or bounded amount pattern;
- statement descriptors;
- explicit owner statements;
- provider metadata where available.

**[INFERENCE][PROPOSED]** Candidate status should be elevated to a formal obligation only through the owning obligation contract rather than O9 silently creating liabilities.

---

## 15. Behavioral baseline object

O9 consumes O8 historical windows to construct user-specific spending baselines.

```yaml
behavioral_baseline:
  baseline_id: id
  dimension: MERCHANT|CATEGORY|CHANNEL|DAY_OF_WEEK|TIME_OF_DAY|PAY_CYCLE_PHASE|CUSTOM
  dimension_key: string
  window_ref: O8_window_ref
  coverage_ref: O8_coverage_ref
  count_ref: engine_output_ref
  amount_distribution_ref: engine_output_ref
  frequency_distribution_ref: engine_output_ref
  recurrence_ref: recurrence_series_or_null
  regime_ref: O7_regime_ref_or_null
  evidence_refs: []
  engine_version: string
```

**[FACT]** Baselines with weak historical coverage must expose lower confidence.

---

## 16. Behavioral dimensions

O9 may analyze at least:

- merchant;
- merchant type;
- category;
- payment channel;
- account/card used;
- weekday/weekend;
- time-of-day when reliable timestamps exist;
- pay-cycle phase;
- before/after income receipt;
- financial regime;
- travel period when registered;
- recurring versus non-recurring spending;
- discretionary versus committed classification where a governed rule exists;
- location/geography only where evidence is reliable and privacy policy permits.

**[FACT]** A behavioral dimension is an analytical grouping, not a psychological diagnosis.

---

## 17. Pay-cycle behavior

O9 should support behavior relative to the income cycle:

- pre-income compression;
- post-income expansion;
- mid-cycle baseline;
- end-of-cycle liquidity pressure;
- credit-cycle interactions;
- recurring-payment clustering.

**[FACT]** Income-cycle anchors must come from registered actual/expected income events and must distinguish actual receipt from forecast expectation.

---

## 18. Merchant concentration analytics

O9 should compute merchant/category concentration using governed analytics engines.

Outputs may include:

- top merchant concentration;
- top category concentration;
- recurring-commitment concentration;
- concentration change by historical window;
- single-merchant dependency candidates;
- spending dispersion.

**[FACT]** Numeric concentration values must come from deterministic/statistical engines.

**[INFERENCE]** High concentration is not automatically bad; interpretation depends on merchant type, regime, obligations, strategic goals, and context.

---

## 19. Spending-frequency intelligence

O9 should measure:

- transaction count by merchant/category;
- active days;
- inter-purchase interval;
- repeated same-day purchase behavior;
- burst versus distributed spending;
- recurrence stability;
- changes in frequency independent of amount.

**[INFERENCE]** Frequency shifts can reveal behavior changes that total spend alone may hide.

---

## 20. Amount-distribution intelligence

For each sufficiently evidenced merchant/category series, O9 may maintain:

- distribution references;
- central tendency references;
- dispersion references;
- upper/lower quantile references;
- historical range;
- outlier candidates;
- regime/window stratification.

**[FACT]** O9 must never manually compute or narratively invent these values.

---

## 21. Unusualness contract

Unusualness is user-relative and context-sensitive.

Conceptual output:

```yaml
unusualness_signal:
  signal_id: id
  entity_type: TRANSACTION|MERCHANT|CATEGORY|SERIES
  entity_id: id
  baseline_ref: behavioral_baseline_id
  historical_window_ref: O8_window_ref
  regime_ref: O7_regime_ref_or_null
  dimensions_considered: []
  unusualness_score_ref: engine_output_ref
  reason_codes: []
  evidence_refs: []
  confidence: bounded_confidence
  materiality_handoff_required: boolean
  status: OPEN|ACKNOWLEDGED|RESOLVED|FALSE_POSITIVE
```

Potential reason codes:

- amount above historical range;
- frequency above baseline;
- new merchant;
- new category;
- new recurring series;
- cadence change;
- amount step-change;
- regime-inconsistent behavior;
- pay-cycle timing anomaly;
- merchant/category concentration shift.

**[FACT]** Unusualness is not wrongdoing and must not be framed as such.

---

## 22. Leakage / inefficiency candidate contract

O9 may generate a **candidate**, not a verdict, when evidence suggests recurring spending that may have low strategic value relative to cost.

Candidate record:

```yaml
leakage_candidate:
  candidate_id: id
  merchant_or_category_ref: id
  window_ref: O8_window_ref
  recurrence_ref: id_or_null
  evidence_refs: []
  cost_ref: engine_output_ref
  strategic_context_refs: []
  owner_value_context: UNKNOWN|KNOWN
  hypothesis: string
  confidence: bounded_confidence
  next_question_or_evidence_needed: string
  status: OPEN|REJECTED|CONFIRMED|SUPERSEDED
```

**[FACT]** O9 must not define leisure, restaurants, travel, subscriptions, gifts, or lifestyle spending as leakage merely because they are discretionary.

**[INFERENCE]** Leakage is better defined as spend whose repeated cost is misaligned with the owner's stated goals/preferences or provides materially less value than alternatives, not simply “non-essential spend.”

---

## 23. Behavioral pattern object

```yaml
behavioral_pattern:
  pattern_id: id
  pattern_type: string
  statement: string
  window_refs: []
  supporting_evidence_refs: []
  counterevidence_refs: []
  coverage_refs: []
  regime_refs: []
  confidence: bounded_confidence
  evidence_class: COMPUTED|INFERENCE|HYPOTHESIS
  first_detected_at: timestamp
  last_evaluated_at: timestamp
  status: ACTIVE|WEAKENED|REJECTED|SUPERSEDED
```

**[FACT]** Pattern statements must preserve counterevidence where material.

---

## 24. Pattern confidence

Pattern confidence should depend on:

- evidence coverage;
- reconciliation quality;
- sample size/observation count;
- stability across windows;
- consistency across source types;
- merchant-resolution confidence;
- category confidence;
- contradictory evidence;
- recency;
- model calibration where applicable.

**[FACT]** Confidence must degrade when upstream evidence quality degrades.

---

## 25. Pattern persistence and expiry

**[INFERENCE][PROPOSED]** Behavioral patterns should not become permanent labels. Each pattern should have a review cadence and may weaken, expire, or be superseded when later evidence contradicts it.

Examples:

- a formerly recurring merchant stops appearing;
- a category spike was temporary travel spending;
- a subscription was cancelled;
- merchant alias resolution was corrected;
- a regime change makes an older baseline less representative.

---

## 26. Historical merchant intelligence

O9 must integrate with O8 rather than duplicate history.

O8 owns:

- standard historical windows;
- historical coverage;
- temporal provenance;
- period-over-period comparison;
- immutable historical analysis versions.

O9 owns:

- merchant/category semantics inside those windows;
- recurrence series;
- behavior baselines;
- unusualness/leakage candidates;
- merchant/category corrections.

---

## 27. Merchant novelty detection

New merchant detection requires checking:

1. canonical merchant ID history;
2. known aliases;
3. likely alias candidates;
4. historical raw descriptions;
5. marketplace/processor relationships;
6. account/provider scope.

**[FACT]** A new raw descriptor is not necessarily a new merchant.

---

## 28. Merchant-location intelligence

Where reliable evidence exists, O9 may capture merchant country, city, branch, or online/in-store context.

**[FACT]** Location inference must not be fabricated from merchant name alone when ambiguous.

**[PROPOSED]** Location should be represented with source and confidence rather than stored as an unqualified fact.

---

## 29. Merchant research source hierarchy

For merchant identity/category research, prefer:

1. official merchant/provider sources;
2. payment-provider or statement metadata;
3. reputable business directories / professional sources;
4. credible secondary sources;
5. community/social discussion as supplementary evidence;
6. unverified anecdote as discovery-only.

**[FACT]** Source count cannot substitute for source quality or independence.

---

## 30. Public/social evidence boundary

**[FACT]** Public/social data may explain what a merchant is, whether a service changed, or what consumers report, but it must not be treated as evidence that Seif personally made a transaction or received a service.

**[FACT]** Personal transaction truth remains grounded in registered financial evidence.

---

## 31. Merchant-rule engine

Owner rules may include:

- merchant → category;
- merchant alias → canonical merchant;
- merchant → recurring/non-recurring hint;
- merchant → strategic tag;
- merchant → review requirement;
- merchant/category exclusion from certain behavioral analyses where justified.

**[FACT]** Rules must be versioned, auditable, and reversible.

---

## 32. Merchant-rule conflict behavior

If rules conflict:

1. detect the conflict;
2. preserve both rule references;
3. apply documented precedence;
4. do not silently merge contradictory categories;
5. raise review if no deterministic precedence resolves the conflict;
6. record the resolution.

---

## 33. Transfer and cash safeguards

**[FACT]** Internal transfers and bank-to-card payments are not merchant spending merely because a statement description resembles a counterparty.

**[FACT]** Cash withdrawal remains a transfer to cash until downstream use is evidenced or intentionally expensed under policy.

**[FACT]** O9 must consume O1/O4 transaction-type classifications before behavioral spending analysis.

---

## 34. Refund/reversal behavior

Merchant behavior must link refunds, reversals, chargebacks, and voids to original transactions where possible.

**[FACT]** Gross outflow and net economic spend may differ; O9 must use governed transaction economics rather than summing visible rows naively.

---

## 35. Installment behavior

Installment merchant analysis must distinguish:

- original purchase economics;
- liability creation;
- installment repayment events;
- fees/interest;
- merchant versus lender/provider.

**[FACT]** O9 must not double-count the original purchase and later liability payments as separate consumption when the governing transaction model says they represent one purchase economics plus financing.

---

## 36. Merchant behavior and protected liquidity

O9 may expose patterns to O2/O15 such as:

- recurring outflow clusters;
- discretionary bursts;
- merchant/category variance;
- emerging recurring series;
- spending compression/expansion around liquidity stress.

**[FACT]** O9 does not calculate the protected floor itself.

---

## 37. Merchant behavior and capital optimization

O9 supplies O4 with:

- recurring discretionary commitments;
- category concentration;
- behavioral trend shifts;
- leakage candidates;
- merchant/category opportunity candidates;
- owner-confirmed low-value recurring costs.

**[FACT]** O4 owns capital reallocation decisions.

---

## 38. Merchant behavior and decision intelligence

O9 supplies O3 with historical context such as:

- prior spend at similar merchants/categories;
- recurring commitment history;
- comparable historical purchase patterns;
- post-purchase consequences where later outcome evidence exists;
- merchant risk/research context.

**[FACT]** O3 owns the recommendation about a contemplated decision.

---

## 39. Merchant behavior and wealth growth

O9 may identify patterns that affect O5 through:

- recurring consumption burden;
- productive-capital purchases;
- strategic capability spending;
- persistent allocation leakage;
- increasing/decreasing lifestyle commitments.

**[INFERENCE]** Classification as productive-capital or lifestyle value requires explicit criteria from O5/O4 and must not be inferred solely from merchant name.

---

## 40. Merchant behavior and regime management

O9 may stratify behavioral analytics by O7 regime.

Examples:

- whether discretionary concentration falls during Survival;
- whether new recurring commitments appear during Stabilization;
- whether Growth-phase allocations actually shift toward strategic goals;
- whether Expansion produces sustained or temporary spending inflation.

**[FACT]** O9 cannot change the active regime.

---

## 41. Merchant behavior and cognitive offloading

O9 supports O6 by surfacing only meaningful merchant/behavior changes rather than flooding the owner with every transaction.

Possible briefing triggers:

- new recurring commitment candidate;
- new merchant with material spend;
- unexpected merchant/category shift;
- repeated low-confidence merchant;
- suspected duplicate/relation anomaly;
- merchant-series amount/frequency step-change;
- owner-confirmed leakage candidate recurrence.

---

## 42. Cross-pillar interface

O9 may expose time-aligned financial behavior records to O10/Third-Eye-style analysis.

Required safeguards:

- explicit time windows;
- only permitted source domains;
- provenance;
- counterevidence;
- confounder awareness;
- no psychological diagnosis;
- no causal language without appropriate evidence.

**[FACT]** O9 itself does not infer psychological causes of spending.

---

## 43. Behavioral context from journals

Under future formally implemented HIMAYAH v2, relevant owner-approved journal context may be retrieved when it materially improves understanding of a financial behavior.

**[FACT]** Journal context remains self-report/context evidence, not financial transaction truth.

**[PROPOSED]** Retrieval should be scoped by relevance and time window rather than loading unrelated intimate material into every finance analysis.

---

## 44. Unusualness versus materiality

O9 unusualness answers:

> “How different is this from Seif's historical behavior?”

O28 materiality answers:

> “How much does this matter across liquidity, debt, goals, regime, reversibility, recurrence, credit impact, and other pillars?”

**[FACT]** A highly unusual purchase can be immaterial; a very normal recurring payment can be materially damaging.

---

## 45. Merchant risk signals

O9 may expose risk signals such as:

- merchant identity unresolved;
- repeated descriptor changes;
- duplicate charge candidates;
- unexpectedly repeated charge;
- changed recurring amount;
- refund/reversal irregularity;
- new foreign-currency merchant;
- fee/interest merchant/provider pattern;
- dormant subscription reactivation candidate.

**[FACT]** O2/O28 determine protection/materiality consequences.

---

## 46. Behavioral explanation contract

User-facing explanations should follow:

> observation → baseline → difference → evidence → uncertainty → possible implication → next action/question

Example conceptual shape:

```yaml
behavior_explanation:
  observation: "merchant/category pattern changed"
  baseline_ref: baseline_id
  difference_ref: engine_output_ref
  supporting_evidence_refs: []
  counterevidence_refs: []
  confidence: bounded_confidence
  implication_class: INFORMATION|REVIEW|PROTECTION_HANDOFF|DECISION_HANDOFF
  next_action: string
```

**[FACT]** If the actual numeric difference has not been computed, the agent must not fabricate it.

---

## 47. Behavioral language policy

Disallowed unsupported language includes:

- “You always overspend when ...”;
- “You are impulsive”;
- “This merchant is bad”;
- “This proves poor recovery causes spending”;
- “You wasted money”;
- “This is extravagant” without defined evidence/criteria.

Preferred evidence language:

- “Spending at this merchant/category is above your registered historical baseline for the selected window.”
- “This is a new recurring-series candidate.”
- “The pattern is unusual, but materiality has not yet been evaluated.”
- “There is an association; causation is not established.”

---

## 48. Merchant intelligence snapshot

```yaml
merchant_intelligence_snapshot:
  snapshot_id: id
  as_of: timestamp
  canonical_state_ref: O1_snapshot_ref
  historical_context_ref: O8_snapshot_ref
  regime_ref: O7_regime_ref
  merchant_resolution_summary_ref: engine_output_ref
  recurrence_summary_ref: engine_output_ref
  concentration_summary_ref: engine_output_ref
  unusualness_signal_refs: []
  leakage_candidate_refs: []
  low_confidence_review_refs: []
  computation_receipt_ref: receipt_id
  policy_version: string
```

---

## 49. Computation proof contract

Every material O9 output must prove that the relevant work actually ran.

Minimum receipt:

```yaml
merchant_computation_receipt:
  receipt_id: id
  requested_at: timestamp
  completed_at: timestamp
  canonical_state_version: string
  historical_snapshot_version: string_or_null
  engine_versions: {}
  policy_version: string
  input_transaction_refs: []
  input_merchant_refs: []
  evidence_refs: []
  window_refs: []
  outputs_generated: []
  unresolved_items: []
  warnings: []
  status: COMPLETE|PARTIAL|FAILED
```

**[FACT]** A chat message saying “I checked your merchant history” without a corresponding successful computation/evidence receipt is not sufficient proof.

---

## 50. Confidence model

O9 confidence should combine at least:

- source quality;
- merchant alias certainty;
- category certainty;
- transaction reconciliation state;
- historical coverage;
- sample/observation sufficiency;
- recency;
- consistency across periods;
- contradictory evidence;
- model calibration where applicable.

**[FACT]** Confidence is metadata about evidence/model quality, not an emotional certainty score.

---

## 51. Low-confidence behavior

When confidence is low:

- preserve UNKNOWN/REVIEW;
- ask for the smallest useful clarification;
- avoid material recommendation based solely on the uncertain mapping;
- retain candidate mappings rather than forcing one;
- record what evidence would resolve the ambiguity;
- allow downstream engines to know the uncertainty exists.

---

## 52. Review queue

Review queue entries should include:

```yaml
merchant_review_item:
  review_id: id
  type: IDENTITY|CATEGORY|RECURRENCE|UNUSUALNESS|LEAKAGE|RELATIONSHIP
  affected_ids: []
  current_hypothesis: string_or_null
  conflicting_evidence_refs: []
  next_evidence_needed: string
  materiality_hint_ref: null_or_O28_ref
  owner: agent_or_human
  age: duration
  status: OPEN|SNOOZED|RESOLVED|REJECTED
```

---

## 53. Duplicate-charge interface

**[FACT]** O9 may flag merchant-pattern similarity, but O1 transaction identity/dedupe logic remains authoritative for whether two evidence rows represent the same economic transaction.

O9 can provide:

- same merchant/amount proximity;
- repeated descriptor similarity;
- cadence mismatch;
- unusual same-day repetition;
- prior duplicate history.

It cannot delete or merge transactions independently.

---

## 54. Merchant decision-memory

**[INFERENCE][PROPOSED]** O9 should remember merchant-specific decision outcomes where relevant:

- prior cancelled recurring cost;
- previously disputed duplicate;
- merchant/category user preference;
- prior challenge/override outcome;
- prior merchant research conclusion;
- prior category correction.

These are references to decision/learning ledgers, not hidden private merchant state.

---

## 55. Forecast interface

O9 may produce inputs to forecasting such as:

- recurrence-series expected windows;
- merchant/category seasonality candidates;
- amount distributions;
- category-frequency changes;
- dormant/reactivated series.

**[FACT]** The forecasting engine owns forecast values and probability distributions.

---

## 56. Counterfactual interface

O9 can support counterfactual analysis by supplying observed historical patterns:

- merchant/category spending under alternative prior periods;
- historical recurrence cost;
- behavior after previous cancellation/reduction;
- merchant substitution evidence.

**[FACT]** Counterfactual financial consequences remain model outputs, not historical facts.

---

## 57. Behavioral learning loop

O9 learning loop:

> ingest → resolve merchant → classify → compare baseline → detect pattern → owner correction/decision → observe later actuals → update evidence/confidence → preserve history

**[FACT]** Learning must never silently rewrite the original source evidence.

---

## 58. False-positive learning

Repeated false positives should update rules/model calibration.

Examples:

- a merchant repeatedly flagged as duplicate but proven legitimate;
- a recurring series that is intentionally variable;
- a category that appears unusual only during travel periods;
- a merchant alias repeatedly misresolved.

**[FACT]** False-positive learning must remain auditable.

---

## 59. False-negative review

O9 should support retrospective review where later evidence reveals that it missed:

- a recurring commitment;
- a material merchant shift;
- a duplicate-charge pattern;
- a category correction;
- a merchant alias relationship.

The missed case should become a validation fixture when appropriate.

---

## 60. User-facing merchant brief

A concise merchant/behavior brief may contain:

1. what materially changed;
2. which merchant/category changed;
3. whether the change is recurring or isolated;
4. historical baseline/context;
5. confidence and evidence coverage;
6. possible financial implication;
7. whether materiality/protection review is needed;
8. next question/action only when necessary.

**[FACT]** It should not overwhelm the owner with every merchant statistic.

---

## 61. Weekly behavioral review

Weekly review should consider:

- newly resolved merchants;
- unresolved merchant/category cases;
- new recurrence candidates;
- recurring-series amount changes;
- concentration shifts;
- unusualness signals;
- confirmed/rejected leakage candidates;
- merchant/category corrections;
- material changes handed to O2/O3/O28;
- forecast inputs generated from recurring behavior.

---

## 62. Monthly behavioral review

Monthly review should include:

- merchant/category concentration changes;
- recurrence burden changes;
- top behavioral shifts;
- category correction rate;
- merchant-resolution accuracy;
- false-positive/false-negative review;
- confirmed recurring costs added/removed;
- regime-relative behavior;
- trends relevant to O4/O5.

---

## 63. Quarterly behavioral review

Quarterly review should answer:

- Are spending patterns structurally changing?
- Are recurring commitments accumulating?
- Is merchant/category concentration improving or worsening relative to goals?
- Are user corrections declining as the system learns?
- Which behavior signals actually mattered to decisions?
- Which pattern detectors create noise?
- Which merchant/category rules should be retired or revised?

---

## 64. Annual behavioral review

Annual review may compare:

- year-over-year merchant/category structure;
- recurring commitment footprint;
- travel/seasonal patterns;
- merchant-resolution improvements;
- concentration shifts;
- confirmed low-value recurring spend removed;
- productive-capital versus consumption patterns where governed classification exists;
- O5 wealth trajectory relationships.

**[FACT]** Annual interpretation must preserve inflation/currency/regime context where relevant rather than comparing nominal values blindly.

---

## 65. HIMAYAH v2 interface

**[FACT][AGREED]** Owner direction proposes `trusted_private` as the normal readable class inside the Trusted NIZAM Boundary (VPS + Google Drive), while secrets/credentials remain prohibited from Drive and explicit strict-local classes remain exceptions.

**[FACT]** This is a proposed governance supersession and is not yet runtime-verified.

O9 artifacts eligible under the future policy may include:

- merchant maps;
- merchant research;
- transaction-category corrections;
- recurrence-series records;
- behavioral baselines;
- unusualness signals;
- leakage candidates;
- review queues;
- behavioral summaries;
- computation receipts.

---

## 66. Drive persistence contract

Eligible O9 records should be mirrored to the approved Drive structure with:

- stable IDs;
- human-readable representation where useful;
- machine-readable structured form;
- provenance;
- policy/schema/model versions;
- checksums where appropriate;
- mirror receipt;
- destination read-back verification.

**[FACT]** Upload success without read-back is not sufficient proof of landed persistence under NIZAM governance.

---

## 67. Storage-aware runtime behavior

O9 should not keep unlimited merchant-analysis artifacts hot on the VPS.

**[PROPOSED]** Retention should consider:

- current free VPS storage;
- growth rate;
- active analysis needs;
- latest verified Drive mirror;
- retrieval cost;
- recovery requirements.

Older eligible merchant-analysis artifacts may be compacted/offloaded only after verified durable persistence.

---

## 68. Recovery contract

After VPS loss, O9 should be rebuildable from:

- canonical O1 transaction/state records;
- Drive-preserved merchant maps and alias history;
- merchant/category correction events;
- recurrence-series history;
- O8 historical snapshots/windows;
- behavioral patterns/baselines;
- model/policy versions;
- computation receipts;
- audit events.

**[MISSING]** The exact deployed recovery commands and physical persistence paths remain unverified until repository implementation.

---

## 69. Agent responsibilities

### Finance Orchestrator

Routes merchant/behavior tasks, enforces dependencies, and prevents O9 from bypassing O1 reconciliation.

### Evidence Ingestion Agent

Preserves source evidence and normalized transaction descriptors without deciding merchant truth beyond its governed role.

### Reconciliation Agent

Provides canonical transaction/economic-event status required before behavioral analysis.

### Merchant Intelligence Agent / Engine

Resolves merchant aliases, category evidence, recurrence, behavioral baselines, unusualness, and review queues within O9 scope.

### Research Agent

Investigates unresolved merchant identity/category/context using registered evidence tiers and provenance.

### Monitoring Agent

Raises meaningful merchant/behavior changes under O6/O2 rules; it cannot execute payments or cancellations.

### Decision Agent

Consumes O9 evidence for contemplated decisions; it cannot modify O9 merchant truth directly.

### Audit Agent

Checks provenance, unauthorized mutation, missing receipts, stale mappings, and supersession integrity.

---

## 70. Agent-to-agent envelope additions

O9 requests should use the existing shared envelope and add merchant-specific fields only where necessary:

```yaml
merchant_task:
  task_id: id
  request: string
  canonical_state_version: string
  longitudinal_snapshot_ref: O8_ref_or_null
  transaction_refs: []
  merchant_refs: []
  requested_windows: []
  assumptions: []
  unresolved_items: []
  expected_output: string
  write_permissions: []
  approval_required: boolean
  completion_status: enum
  audit_refs: []
```

**[FACT]** Agents must not maintain hidden competing merchant ledgers.

---

## 71. Write permissions

O9 may write only authorized enrichment/audit artifacts, such as:

- merchant alias proposals/verified mappings;
- merchant/category evidence records;
- recurrence-series records;
- behavioral baselines/patterns;
- unusualness signals;
- leakage candidates;
- review items;
- merchant research records;
- computation receipts;
- audit events.

O9 may not independently mutate:

- canonical account balances;
- transaction amounts;
- reconciled transaction status;
- budget assignments;
- obligations;
- debt balances;
- forecast actuals;
- regime state;
- owner decisions;
- external payments/transfers.

---

## 72. Failure modes

### FM-01 — Merchant alias false merge

Two distinct merchants are collapsed into one identity.

**Required response:** preserve transactions, reopen identity review, supersede mapping, recalculate affected historical views, audit correction.

### FM-02 — Same merchant fragmented into many aliases

Repeated descriptors are never joined, hiding concentration/recurrence.

**Required response:** alias-candidate detection and review.

### FM-03 — Forced category under low confidence

A model suggestion becomes authoritative without evidence.

**Required response:** UNKNOWN/REVIEW and explicit confidence.

### FM-04 — Transfer treated as merchant spend

Internal transfer or card payment contaminates behavioral spending.

**Required response:** defer to O1 transaction-type truth and remove from spend analysis through successor computation.

### FM-05 — Cash withdrawal treated as final spend

ATM withdrawal is assigned to a merchant/category without downstream evidence.

**Required response:** preserve transfer-to-cash state.

### FM-06 — Refund ignored

Merchant spend remains overstated after refund/reversal.

**Required response:** use linked economic-event state from O1.

### FM-07 — Installment double counting

Original purchase and installment payments are treated as separate consumption.

**Required response:** respect financing/economic-event model.

### FM-08 — Seasonal travel behavior labeled leakage

Temporary contextual spending is treated as a persistent negative pattern.

**Required response:** compare context/window/regime and preserve uncertainty.

### FM-09 — Behavioral correlation presented as psychological cause

Spending pattern is framed as proof of an emotional/health cause.

**Required response:** downgrade to association/hypothesis and route cross-pillar analysis to O10.

### FM-10 — Merchant research contaminates personal truth

A public source is treated as evidence that Seif made a specific transaction.

**Required response:** separate public merchant context from personal transaction evidence.

### FM-11 — Duplicate-alert noise

Every merchant deviation generates repeated alerts.

**Required response:** O6/O2 dedupe, severity, cooldown, and batching rules.

### FM-12 — LLM claims pattern without engine execution

The conversational layer states that merchant spend increased or is unusual without computation proof.

**Required response:** fail the claim, return missing computation receipt, rerun governed engine.

### FM-13 — Correction rewrites history

Later merchant/category correction silently changes past outputs.

**Required response:** successor analysis with preserved original versions.

### FM-14 — Drive mirror claimed but unreadable/missing

O9 says merchant records were persisted but destination cannot be read back.

**Required response:** mirror receipt FAILED and keep persistence defect open.

---

## 73. Validation fixtures

Minimum synthetic fixtures:

1. same merchant with two statement aliases resolves correctly;
2. two distinct merchants with similar names remain separate;
3. provider/processor descriptor does not erase end-merchant ambiguity;
4. explicit user category rule outranks model suggestion;
5. low-confidence merchant stays REVIEW;
6. pending + posted forms do not create duplicate merchant spend;
7. bank-to-card transfer excluded from merchant spend;
8. refund reduces economic merchant spend correctly;
9. installment purchase not double counted;
10. recurring fixed subscription detected;
11. variable recurring utility-like merchant detected as recurring candidate;
12. one-off merchant does not become recurring;
13. new raw alias does not automatically become new merchant;
14. travel-period category spike is contextualized;
15. unusualness signal preserves baseline/window/coverage;
16. leakage candidate requires owner-value context before confirmation;
17. merchant/category correction creates superseding audit event;
18. cross-pillar pattern cannot state causation;
19. public merchant research cannot create personal transaction fact;
20. missing computation receipt blocks claim that history was checked;
21. Drive mirror must be read back;
22. recovery reconstructs merchant maps from durable records.

---

## 74. Required validation assertions

Tests must prove:

- merchant aliases are stable and auditable;
- raw descriptors remain preserved;
- categorization precedence is enforced;
- low-confidence mappings remain reviewable;
- O1 transaction-type truth is respected;
- refunds/reversals/installments do not distort behavior;
- recurrence uses governed historical evidence;
- unusualness is user-relative and windowed;
- leakage is not synonymous with discretionary spend;
- cross-pillar causality is not invented;
- O9 cannot mutate authoritative financial state;
- computation receipts are mandatory for material outputs;
- Drive persistence is read-back verified;
- corrections preserve historical versions.

---

## 75. Tamper test requirement

At least one deliberate negative test must demonstrate that the O9 validator fails when a mandatory contract is removed or corrupted.

Acceptable tamper examples:

- remove the computation-proof section;
- remove categorization precedence;
- change a transfer rule so transfers become spending;
- remove low-confidence REVIEW behavior;
- allow O9 to mutate transaction amounts;
- remove audit/supersession requirement.

A validator only observed passing without a deliberate failure case is not proven.

---

## 76. Audit requirements

Every material O9 mutation or derived record should preserve:

- actor;
- action;
- entity type/id;
- source/evidence refs;
- before/after refs when applicable;
- reason;
- policy/schema/model version;
- approval ref when required;
- result;
- receipt;
- supersession linkage where applicable.

---

## 77. Merchant data-quality metrics

Candidate metrics, each engine-derived:

- unresolved merchant rate;
- low-confidence merchant rate;
- category-review rate;
- user-correction rate;
- alias-fragmentation rate;
- false-merge rate;
- recurrence precision/recall on validated fixtures;
- unusualness false-positive rate;
- stale merchant-rule count;
- merchant-research resolution rate.

**[FACT]** Exact targets remain policy decisions and must not be invented in this design.

---

## 78. Behavioral-intelligence performance metrics

Candidate measures:

- percentage of reconciled spend covered by high-confidence merchant identity;
- percentage covered by high-confidence category mapping;
- recurring-series detection coverage;
- review-queue age;
- confirmed useful unusualness signals;
- confirmed leakage candidates versus false positives;
- number of downstream O2/O3/O4/O28 decisions materially improved by O9 evidence;
- behavioral forecast-input calibration.

**[MISSING]** Runtime baselines and acceptable thresholds remain unverified.

---

## 79. Migration plan

### Step 1 — inventory current merchant fields and rules

Map existing transaction `merchant_raw`, `merchant_normalized`, merchant tables/records, user rules, categories, and any prior alias files.

### Step 2 — verify O1 transaction identity

Do not backfill behavioral intelligence over unreconciled/double-counted financial events without explicit confidence limits.

### Step 3 — establish canonical merchant IDs

Migrate existing merchant mappings without destroying raw descriptors.

### Step 4 — create alias and correction history

Version mappings and preserve prior states.

### Step 5 — integrate O8 windows/coverage

Use standardized historical windows rather than prompt-specific date math.

### Step 6 — build recurrence engine

Detect fixed/variable/irregular recurring-series candidates with auditable evidence.

### Step 7 — build behavioral baselines

Create merchant/category frequency/amount/concentration baselines with coverage confidence.

### Step 8 — build unusualness and review queue

Keep unusualness separate from materiality.

### Step 9 — build merchant research workflow

Use evidence tiers and provenance for unresolved identity/category cases.

### Step 10 — integrate O6 briefs and O2/O3/O4/O28 handoffs

Only meaningful changes should consume owner attention.

### Step 11 — implement HIMAYAH v2 persistence only after the privacy-governance redesign is formally updated and verified

Do not pretend the owner-approved direction is already deployed.

### Step 12 — implement Drive mirror/read-back and recovery

Eligible records must be durably recoverable.

### Step 13 — run validation and deliberate tamper proof

Do not mark O9 runtime verified without observed repository/runtime output.

---

## 80. Repository implementation guidance

**[ASSUMPTION]** Exact repository filenames and physical database tables for O9 are not verified in this environment and must not be invented as existing paths.

Implementation SHOULD locate the current owning merchant/transaction contracts first and then introduce the smallest coherent set of changes, likely including:

- merchant alias schema/model;
- merchant research record;
- recurrence-series schema/model;
- behavioral-baseline output;
- unusualness signal;
- leakage candidate;
- merchant review queue;
- computation receipt extension;
- tests/fixtures;
- documentation/contract registration.

Every implementation file must follow repository ownership/phase headers required by NIZAM build governance.

---

## 81. Definition of done

O9 is contract-complete when:

1. merchant identity and alias rules are unambiguous;
2. categorization precedence is preserved;
3. raw merchant descriptions remain immutable evidence;
4. low-confidence cases route to review;
5. recurrence-series behavior is defined;
6. behavioral baselines use O8 windows and coverage;
7. unusualness is defined independently from materiality;
8. leakage candidates cannot moralize discretionary spending;
9. transfers/refunds/installments are handled through O1 economic-event truth;
10. merchant research has source hierarchy and provenance;
11. cross-pillar correlation cannot become causal diagnosis;
12. user corrections are versioned/auditable;
13. O6/O2/O3/O4/O28 handoffs are explicit;
14. computation receipts are mandatory;
15. validation fixtures exist;
16. deliberate tamper failure is proven;
17. Drive persistence/recovery design is explicit;
18. runtime implementation status is honestly labeled unverified until actual tests run.

O9 is runtime-complete only after the implementation is integrated into the repository, focused tests pass, the repository gate passes, a deliberate tamper/failure injection proves the relevant check fails, eligible persistence is read-back verified, and observed outputs are recorded.

---

## 82. Acceptance questions

Before O9 can be treated as operational, the implementation must answer YES with evidence to all of the following:

- Can the same merchant appear under multiple aliases without fragmenting history?
- Can distinct merchants avoid false merging?
- Are raw descriptors preserved?
- Does explicit owner categorization outrank model inference?
- Can UNKNOWN remain UNKNOWN?
- Are transfers, refunds, reversals and installments economically correct?
- Can recurring-series candidates be detected without automatically becoming obligations?
- Can unusualness be explained against a historical baseline?
- Can discretionary lifestyle spend avoid being automatically labeled leakage?
- Can owner corrections improve future classification without erasing history?
- Can merchant research remain separate from personal transaction truth?
- Can O9 prove which engines and evidence produced a pattern claim?
- Can O9 artifacts survive VPS loss when eligible for Drive persistence?

---

## 83. Evidence classification for this design

### [FACT]

- The supplied PFOS data model already defines a canonical Merchant entity and transaction merchant fields.
- The supplied ingestion contract already defines categorization precedence and low-confidence review behavior.
- Transaction identity, transfer handling, refunds, installments, and raw evidence preservation are governed upstream.
- The validation contract requires deterministic outputs, auditability, human gating, and deliberate tamper testing.
- The research register distinguishes authoritative evidence from weak/community evidence.
- O8 already owns longitudinal windows, coverage, temporal provenance, and immutable historical analysis versions.

### [INFERENCE]

- Merchant identity benefits from an explicit alias/relationship layer because provider descriptors are heterogeneous.
- Behavioral baselines and recurrence-series objects are needed so the system does not recompute merchant meaning ad hoc in conversation.
- Leakage should be framed as a candidate requiring owner-value context rather than a hard rule based on discretionary classification.
- O9 evidence is likely to be a major input into O28 dynamic materiality and O19 adversarial challenge.

### [ASSUMPTION]

- Exact runtime merchant tables, current merchant model code, physical Drive folder paths, and scheduler jobs have not been verified in this environment.
- HIMAYAH v2 is treated as owner-approved future governance direction, not as already deployed policy.

### [MISSING]

- Verified runtime merchant-resolution accuracy baseline.
- Verified runtime category-correction baseline.
- Verified deployed recurrence model.
- Verified repository paths and tests owning merchant intelligence.
- Verified Drive folder taxonomy for merchant intelligence.
- Formal implemented HIMAYAH v2 privacy contract.

---

## 84. Objective handoff

O9 produces merchant identity, category evidence, recurrence, behavioral baselines, unusualness, leakage candidates, merchant research, and correction learning for downstream objectives.

The next objective is:

> **O10 — Cross-Domain Decision Intelligence**

O10 should define how financial evidence can be time-aligned with explicitly permitted non-financial evidence — including recovery/activity and journal context — to test associations that may improve decision quality while preserving provenance, counterevidence, confounders, and the rule that association is not causation.

---

## 85. Contract status

**[FACT]** This document is a design artifact only.

**[MISSING]** No claim is made that O9 is currently implemented, deployed, runtime-verified, or persisted in the production NIZAM repositories.

**[FACT]** Runtime verification requires observed repository/runtime outputs and may not be inferred from this document's existence.
