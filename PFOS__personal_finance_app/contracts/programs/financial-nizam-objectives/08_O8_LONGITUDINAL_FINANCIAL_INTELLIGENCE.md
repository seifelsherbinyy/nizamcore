# Financial NIZAM Objective O8 — Longitudinal Financial Intelligence

**Status:** PROPOSED OVERHAUL DESIGN — owner-approved objective, implementation not yet verified  
**Objective ID:** O8  
**Objective name:** Longitudinal Financial Intelligence  
**Program:** Financial NIZAM / PFOS / MAL implementation namespace  
**Owner:** Seif ElSherbiny  
**Version:** 0.1.0-design  
**Sensitivity:** review_before_commit  
**Owning phase:** Phase 8 — historical reconstruction, trailing-window analytics, temporal provenance, trend intelligence, retrospective calibration  
**Precedence:** safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting subordinate contract → verified runtime evidence → historical/draft material

---

## 1. Objective

**[FACT]** O8 consumes canonical financial truth from O1, protection state from O2, decision records from O3, capital-allocation outputs from O4, wealth trajectory from O5, continuity/open-loop context from O6, and financial-regime history from O7. O8 MUST NOT create a second transaction ledger, account balance source, obligation registry, forecast store, regime engine, or decision authority.

**[AGREED]** Financial NIZAM must understand the current financial position in the context of trailing days, weeks, months, quarters, and years whenever evidence exists. A present-state recommendation without relevant historical context is incomplete when history would materially change the interpretation.

**[AGREED]** Historical analysis must be evidence-backed and reconstructable. O8 must preserve which source artifacts, canonical-state versions, transaction records, statement periods, close records, policy versions, and correction events produced each historical conclusion.

**[AGREED]** The system must distinguish what actually happened from retrospective interpretation. Historical facts, computed aggregates, inferences, hypotheses, and unknown periods must remain separately labeled.

**[AGREED]** Financial NIZAM must compare historical predictions and recommendations against later actual outcomes so that forecast confidence, decision quality, communication strategy, and model calibration can improve over time.

**[FACT]** Authoritative monetary totals, ratios, percentages, trends, forecast-error values, rolling-window statistics, and other numeric outputs MUST come from governed deterministic/statistical engines. The conversational layer may explain those outputs but MUST NOT invent or manually calculate them.

**[AGREED]** O8 is not a nostalgia or reporting layer. Its purpose is to make current and future financial decisions better by using durable historical evidence.

---

## 2. Governing source decisions

### 2.1 Existing canonical-candidate rules

**[FACT]** The Financial NIZAM source-lineage contract establishes that current runtime evidence outranks historical/draft material and that older snapshots remain useful only when their date and canonicality are explicit.

**[FACT]** The data-model contract requires stable IDs, provenance, created/updated timestamps, audit linkage, and versioned/superseding corrections instead of destructive rewriting.

**[FACT]** The transaction-ingestion contract preserves raw evidence, normalized transactions, identity/dedupe state, transfer relationships, pending-to-posted relationships, reversals, and manual corrections with auditability.

**[FACT]** The reconciliation contract prohibits optimization from unreconciled balances and requires authoritative balance/statement evidence with explicit as-of time.

**[FACT]** The forecasting contract requires versioned assumptions, scenario/horizon/confidence fields, and persistent forecast-vs-actual error by item type and horizon.

**[FACT]** The monitoring contract defines daily, weekly, monthly, statement-cycle, salary-event, and event-driven review cadences, including forecast-vs-actual review and exception tracking.

**[FACT]** The ledger contract requires append/audit events, policy/schema versions, supersession links, and preservation of historical events rather than silent deletion.

**[FACT]** The monthly-close contract produces immutable/versioned closes and requires later corrections to create successor closes with provenance.

**[FACT]** The research/evidence register distinguishes official/primary evidence, professional synthesis, secondary sources, expert commentary, community/social signals, and unverified anecdotes with freshness and confidence.

### 2.2 Owner decisions incorporated into O8

**[AGREED]** Historical analysis must support selectable periods including trailing days, weeks, months, quarters, years, and all available history.

**[AGREED]** Historical analysis should use bank statements, transaction records, SMS evidence, account/ledger records, obligations, decisions, forecasts, close records, and other registered evidence where available.

**[AGREED]** Financial NIZAM should investigate merchants, spending areas, unusual patterns, financial decisions, and behavior over selected periods.

**[AGREED]** The system should later compare financial behavior with explicitly permitted cross-pillar signals such as wearable/recovery context, while preserving the distinction between correlation and causation.

**[AGREED]** Recommendations should use historical evidence tactically and strategically, including counterfactuals, future consequences, and evidence that can challenge the owner when materiality warrants it.

**[AGREED]** Forecasts and regime classifications must later be evaluated against what actually happened.

**[AGREED]** Google Drive is intended as the durable, readable evidence/recovery mirror for eligible NIZAM data under the owner-approved HIMAYAH v2 direction, while the governed single-writer runtime remains the authority for canonical computed financial state.

---

## 3. Scope

O8 governs:

1. longitudinal financial-history reconstruction;
2. historical-window definitions;
3. trailing-window analytics;
4. historical completeness and coverage metrics;
5. temporal provenance;
6. historical transaction and merchant analytics;
7. historical spending/category analytics;
8. income and obligation history;
9. debt and credit trajectory history;
10. liquidity and protected-floor history;
11. financial-regime timeline analysis;
12. decision-history analysis;
13. forecast-vs-actual history;
14. anomaly and event history;
15. statement-cycle and monthly-close history;
16. historical correction/supersession behavior;
17. current-period comparison to historical baselines;
18. period-over-period and rolling comparisons;
19. seasonality and recurrence detection;
20. confidence based on evidence density and freshness;
21. historical counterfactual support;
22. cross-pillar correlation interfaces;
23. retrospective decision attribution interfaces;
24. historical user-facing briefings;
25. Drive-readable historical persistence;
26. recovery/rebuild requirements;
27. longitudinal computation receipts;
28. validation and tamper proof.

O8 does **not** govern:

- primary transaction ingestion;
- canonical balance calculation;
- real-time account reconciliation;
- protected-floor formula ownership;
- regime-classification policy ownership;
- merchant master-data ownership beyond consuming canonical merchant mappings;
- autonomous budget, payment, debt, borrowing, transfer, or investment action;
- causal claims from correlation alone;
- rewriting historical outcomes because a later model changed;
- silently filling periods where evidence is missing;
- using social/news evidence as a substitute for personal financial facts;
- free-form LLM arithmetic.

---

## 4. Longitudinal doctrine

**[AGREED]** O8 uses the following doctrine:

> **Current financial meaning is stronger when interpreted against verified history.**

The historical layer answers questions such as:

- What changed relative to the recent baseline?
- Is this behavior unusual for Seif or merely seasonally normal?
- Is liquidity improving or deteriorating over multiple windows?
- Are obligations consuming a larger share of available capacity?
- Are debt and credit dependencies increasing or decreasing?
- Which merchants/categories are becoming structurally larger?
- Which forecasts are consistently wrong?
- Which decision patterns later produced better or worse outcomes?
- How often has the financial regime changed, and were those changes justified by later actuals?
- Is a current concern a one-off event or a repeated pattern?

O8 does not answer these questions by rewriting canonical facts. It computes historical views over versioned authoritative records.

---

## 5. Temporal model

O8 must distinguish at least the following temporal concepts:

- **event time** — when the economic event actually occurred;
- **posted time** — when an institution posted the transaction;
- **source time** — timestamp present in the source evidence;
- **ingestion time** — when NIZAM acquired the evidence;
- **reconciliation time** — when the event became reconciled;
- **correction time** — when a later superseding correction was recorded;
- **decision time** — when a financial decision was considered or made;
- **forecast generation time** — when a forecast was produced;
- **forecast horizon** — future interval to which the forecast applied;
- **observation time** — when later actual evidence became available;
- **close time** — when a monthly/period close became authoritative for its version.

**[FACT]** Historical analysis must use the correct temporal field for the question. A transaction's ingestion date must not be treated as its spending date unless the contract explicitly defines that behavior.

---

## 6. Historical window contract

O8 should expose standardized window IDs rather than ad-hoc date arithmetic in prompts.

Minimum canonical window families:

```yaml
historical_windows:
  trailing_1d:
    type: rolling
  trailing_7d:
    type: rolling
  trailing_14d:
    type: rolling
  trailing_30d:
    type: rolling
  trailing_60d:
    type: rolling
  trailing_90d:
    type: rolling
  trailing_180d:
    type: rolling
  trailing_365d:
    type: rolling
  current_week:
    type: calendar
  previous_week:
    type: calendar
  current_month:
    type: calendar
  previous_month:
    type: calendar
  current_quarter:
    type: calendar
  previous_quarter:
    type: calendar
  current_year:
    type: calendar
  previous_year:
    type: calendar
  all_available:
    type: evidence_bound
```

**[PROPOSED]** Additional configurable windows MAY be added later, but the initial implementation should avoid uncontrolled proliferation because comparability matters more than arbitrary flexibility.

---

## 7. Historical coverage object

Before producing a longitudinal conclusion, O8 must know how much of the period is actually evidenced.

Conceptual object:

```yaml
historical_coverage:
  coverage_id: <stable identifier>
  requested_window: <window id>
  effective_start: <timestamp>
  effective_end: <timestamp>
  source_periods:
    - source_ref: <evidence record>
      covered_start: <date>
      covered_end: <date>
      quality_status: <status>
  accounts_expected: []
  accounts_observed: []
  statement_periods_expected: []
  statement_periods_observed: []
  transaction_coverage_status: COMPLETE | PARTIAL | UNKNOWN
  reconciliation_coverage_status: COMPLETE | PARTIAL | UNKNOWN
  known_gaps: []
  stale_segments: []
  correction_segments: []
  confidence: <engine output>
  generated_at: <timestamp>
```

**[FACT]** O8 must never imply full-period certainty when the coverage object says PARTIAL or UNKNOWN.

---

## 8. Historical truth layers

Each longitudinal output must preserve evidence class.

### 8.1 Historical FACT

Examples:

- a posted transaction existed;
- a statement reported a balance;
- a payment was made;
- an obligation due date was recorded;
- a decision record exists;
- an account was reconciled on a given date;
- a monthly close was published.

### 8.2 Historical COMPUTED

Examples:

- total reconciled spending over a window;
- merchant/category share;
- rolling average;
- variance;
- debt-service ratio output from a governed engine;
- forecast error;
- regime duration;
- transaction frequency;
- historical protected-floor distance.

### 8.3 Historical INFERENCE

Examples:

- spending pattern appears to be changing;
- a merchant is becoming structurally recurrent;
- credit dependency appears to be increasing;
- current spending resembles a prior high-pressure period.

### 8.4 Historical HYPOTHESIS

Examples:

- lower recovery may be associated with more discretionary spending;
- a particular payday pattern may predict overspending later in the cycle;
- some merchant clusters may represent a latent lifestyle category.

### 8.5 UNKNOWN

Used when evidence is missing, stale, conflicting, or insufficient for the requested historical statement.

---

## 9. Historical transaction intelligence

O8 should compute transaction history only over the canonical reconciled transaction model.

Required capabilities include:

- counts and values by period;
- pending-versus-posted history;
- reversal/refund history;
- transfer history separated from spending;
- recurring-payment detection history;
- cash-withdrawal history where evidenced;
- fee/interest history;
- duplicate-detection history;
- manually corrected transaction history;
- unresolved exception history;
- posting-lag patterns;
- statement-vs-SMS timing patterns.

**[FACT]** Re-imported duplicate evidence must not inflate historical spending.

---

## 10. Merchant-history intelligence

O8 must preserve both `merchant_raw` and canonical merchant identity from the governed merchant layer.

Historical merchant outputs may include:

- total spend by merchant and window;
- transaction frequency;
- median/mean transaction size from the statistical engine;
- recurring cadence;
- category history;
- first-seen/last-seen dates;
- merchant alias changes;
- refund/reversal history;
- concentration share;
- unusualness relative to owner history;
- historical dispute/exception frequency;
- travel/location context where evidence permits;
- confidence in merchant normalization.

**[AGREED]** Merchant intelligence should support later analysis of where Seif has been spending and whether behavior has changed materially.

---

## 11. Category and spending-pattern history

O8 should support longitudinal analysis by governed category without turning category labels into moral judgments.

Required views include:

- essential versus discretionary where policy defines those classes;
- fixed versus variable;
- recurring versus one-off;
- planned versus unplanned;
- category trend by rolling window;
- category share of reconciled outflows;
- budget variance history;
- overspend recurrence;
- underuse of funded categories;
- category reclassification history;
- structural versus timing variance.

**[AGREED]** The system should prefer realistic behavioral improvement analysis over simplistic declarations that a category should be cut by an arbitrary percentage.

---

## 12. Income-history intelligence

O8 should maintain historical views of:

- actual income events;
- expected-versus-received timing;
- expected-versus-received value;
- recurrence stability;
- missed/delayed income events;
- source concentration;
- income growth/decline when evidence supports it;
- purchasing-power context supplied by later external-intelligence objectives;
- contribution of each source to liquidity and wealth trajectory.

**[FACT]** Expected future income must not be rewritten historically as actual income if it was never received.

---

## 13. Obligation-history intelligence

Historical obligation analysis should include:

- due events;
- minimum required payments;
- amount paid where evidenced;
- lateness/penalty events;
- autopay success/failure where evidenced;
- recurrence;
- obligation additions/removals;
- installment maturation;
- obligation burden relative to governed liquidity/financial-capacity outputs;
- upcoming obligation forecast error;
- unresolved obligation exceptions.

**[FACT]** Later changes to an obligation rule must not erase the historical rule that applied to an earlier period.

---

## 14. Debt and credit trajectory

O8 should reconstruct debt/credit history from governed sources without inventing provider-specific semantics.

Potential historical outputs include:

- total debt trajectory;
- minimum-payment burden;
- debt-service ratio trajectory from governed engines;
- utilization-like metrics only where provider data and policy support them;
- interest/fee trajectory;
- installment burden;
- credit-cycle timing behavior;
- credit used for convenience versus signs of dependency;
- payment punctuality history;
- new credit commitments;
- debt reductions;
- balance transfers or refinancing decisions when evidenced;
- historical effect on protected liquidity.

**[MISSING]** Exact provider/bank credit-score formulas in Egypt are not established by the current architecture package and require current provider/regulatory evidence before being encoded.

---

## 15. Liquidity-history intelligence

O8 should preserve historical observations of liquidity outputs from the canonical engine rather than reconstructing them from chat memory.

Minimum views:

- available cash history;
- reserved/protected cash history;
- protected-floor history once O15 is implemented;
- emergency-reserve history;
- next-7-day and next-30-day outflow history;
- lowest forecast liquidity point versus later actual;
- liquidity breaches;
- near-breach frequency;
- days of maneuverability where a governed engine defines it;
- cash concentration across accounts;
- liquidity changes around payday, statement cycles, travel, major purchases, and irregular obligations.

---

## 16. Regime-history intelligence

O8 consumes O7's authoritative regime transition ledger.

Historical regime views include:

- active regime by date;
- candidate regimes that did not activate;
- transition evidence;
- transition confidence;
- time spent in each regime;
- reason codes;
- critical defensive transitions;
- hysteresis/cooldown effects;
- later actual outcome after each transition;
- false-positive/false-negative transition reviews where governed calibration defines them.

**[FACT]** O8 may evaluate the historical performance of O7 but MUST NOT retroactively overwrite the regime that was active at the time. Corrections create successor interpretations with provenance.

---

## 17. Decision-history intelligence

O8 consumes immutable/versioned DecisionRecords.

Historical decision views should include:

- decision category;
- options considered;
- recommendation at the time;
- evidence available at the time;
- uncertainty at the time;
- materiality at the time when O28 exists;
- challenge/escalation history when O19 exists;
- cooling-period history when O23 exists;
- explicit override history when O25 exists;
- eventual observed outcome;
- counterfactual estimate when later engines can support it;
- lesson carried forward.

**[AGREED]** Later information must not be backfilled into the original decision record as though it had been known at decision time.

---

## 18. Forecast-vs-actual history

O8 must treat forecast accountability as a first-class historical object.

Each evaluation should preserve:

```yaml
forecast_evaluation:
  forecast_id: <original forecast>
  forecast_version: <version>
  generated_at: <timestamp>
  canonical_state_version: <state ref>
  horizon: <horizon>
  scenario: <base/downside/upside/etc>
  predicted_ref: <engine output>
  actual_ref: <later authoritative outcome>
  error_ref: <deterministic/statistical output>
  evidence_available_at_forecast_time: []
  evidence_added_after_forecast: []
  calibration_bucket: <optional>
  conclusion: <engine/policy result>
  audit_refs: []
```

Historical reporting should support forecast error by:

- item type;
- horizon;
- scenario;
- account/category/obligation type where appropriate;
- financial regime;
- evidence-quality band;
- model/policy version.

---

## 19. Historical comparison contract

Any comparison must identify both periods and ensure comparability.

Examples:

- trailing 7 days versus previous 7 days;
- current month-to-date versus comparable previous month-to-date;
- current quarter versus previous quarter;
- current year-to-date versus previous year-to-date;
- payday cycle versus prior payday cycles;
- statement cycle versus prior statement cycles;
- current SURVIVAL period versus previous SURVIVAL periods.

Comparison output should record:

- comparison type;
- current window;
- reference window;
- coverage of both windows;
- normalization applied;
- engine version;
- effect/variance output;
- limitations.

**[FACT]** Non-comparable periods must not be presented as directly comparable without explicit normalization and caveats.

---

## 20. Seasonality and recurrence

O8 may detect seasonality only when enough comparable history exists.

Potential patterns:

- payday-related spending cadence;
- month-start/month-end effects;
- annual travel periods;
- recurring subscription clusters;
- holiday/religious-season spending;
- recurring family commitments;
- statement-cycle behavior;
- periodic fees/insurance/renewals;
- irregular but repeated major expenses.

**[PROPOSED]** The engine should require minimum-observation rules before labeling a pattern seasonal. Exact thresholds belong in governed statistical policy, not prompt prose.

---

## 21. Historical unusualness

O8 provides a historical unusualness interface to O28 Dynamic Materiality.

Unusualness may consider:

- transaction value relative to the owner's own history;
- merchant/category rarity;
- spending frequency spike;
- recurrence deviation;
- timing deviation;
- concentration changes;
- new debt/credit behavior;
- decision divergence from prior behavior;
- liquidity impact relative to historical capacity.

**[FACT]** Unusualness is not equivalent to badness. It is a signal that something differs from the historical baseline.

---

## 22. Structural change detection

O8 should distinguish one-off noise from structural change.

A structural-change candidate may be raised when governed statistical evidence indicates a persistent shift in:

- income;
- fixed obligations;
- discretionary spending;
- merchant/category mix;
- debt-service burden;
- protected liquidity;
- forecast error;
- savings/investment capacity;
- lifestyle baseline;
- credit dependence;
- regime duration/transition frequency.

The output remains a candidate until policy-defined evidence requirements are met.

---

## 23. Cross-pillar longitudinal interface

**[AGREED]** O8 should permit later cross-pillar analysis when the evidence is explicitly allowed under HIMAYAH and relevant to the financial question.

Examples of permitted future joins include:

- financial decisions ↔ WHOOP/recovery context;
- spending ↔ workload/travel context;
- overrides ↔ journal/decision-state context;
- major purchases ↔ subsequent stress or liquidity outcomes;
- income/career events ↔ financial trajectory.

Every cross-pillar join must preserve:

- source artifact IDs;
- timestamps;
- evidence classes;
- permitted-use classification;
- join key/time alignment method;
- missing-data handling;
- confounder notes;
- uncertainty.

**[FACT]** WHOOP or journal context is not a financial source of truth and must not mutate financial facts.

---

## 24. Correlation without causation

O8 must explicitly prevent causal overreach.

A valid output may say:

> **[FACT]** Historically observed financial behavior differed across the compared recovery bands.

> **[INFERENCE]** Recovery state may be useful as a decision-risk signal.

> **[MISSING]** The available evidence does not establish that recovery caused the financial behavior.

O8 must not say:

> “Poor recovery caused overspending.”

unless a future governed causal-analysis framework provides evidence sufficient for that claim.

---

## 25. Historical external-intelligence interface

O8 may later consume versioned economic/news/market context from O16/O17/MARSAD to explain the environment in which historical financial outcomes occurred.

Examples:

- inflation context;
- FX context;
- interest-rate context;
- labor/income-risk context;
- regional/global shock context;
- market-expectation context.

The interface must preserve what was **known at the time** versus what became known later.

**[FACT]** Historical external context may explain or condition analysis but must never overwrite personal canonical financial facts.

---

## 26. Historical reconstruction after late evidence

A bank statement or other source may arrive after a period was initially analyzed.

Required behavior:

1. register the new evidence;
2. reconcile through O1;
3. create corrected/superseding canonical state where required;
4. identify affected historical analytics;
5. recompute affected views;
6. preserve the previous analysis version;
7. mark the new view as successor;
8. explain materially changed conclusions;
9. retain audit linkage.

**[FACT]** O8 must never destructively rewrite history to make the system look as though it always knew the corrected data.

---

## 27. Immutable historical interpretation versions

Each material longitudinal analysis should be versioned.

Conceptual record:

```yaml
longitudinal_analysis:
  analysis_id: <stable id>
  version: <version>
  analysis_type: <trend/comparison/merchant/decision/etc>
  requested_window: <window>
  effective_window: <actual covered range>
  canonical_state_refs: []
  evidence_refs: []
  close_refs: []
  engine_refs: []
  policy_version: <version>
  coverage_ref: <historical coverage object>
  outputs: <references>
  confidence: <engine/policy output>
  limitations: []
  supersedes_analysis_id: <optional>
  generated_at: <timestamp>
  audit_refs: []
```

---

## 28. Longitudinal snapshot object

O8 should expose an owner-facing `longitudinal_financial_snapshot` referencing engine outputs rather than duplicating raw calculations.

```yaml
longitudinal_financial_snapshot:
  snapshot_id: <id>
  as_of: <timestamp>
  canonical_state_version: <O1 state>
  requested_windows: []
  coverage_refs: []
  transaction_history_ref: <engine output>
  merchant_history_ref: <engine output>
  category_history_ref: <engine output>
  income_history_ref: <engine output>
  obligation_history_ref: <engine output>
  debt_credit_history_ref: <engine output>
  liquidity_history_ref: <engine output>
  regime_history_ref: <O7 history>
  forecast_error_ref: <engine output>
  decision_history_ref: <engine output>
  unusualness_ref: <engine output>
  structural_change_candidates: []
  unresolved_items: []
  evidence_quality: <status>
  generated_at: <timestamp>
```

---

## 29. Computation proof contract

Every material O8 output must prove that historical computation actually occurred.

Minimum computation receipt:

```yaml
longitudinal_computation_receipt:
  receipt_id: <id>
  objective: O8
  requested_analysis: <analysis type>
  canonical_state_version: <O1 reference>
  input_windows: []
  evidence_refs: []
  coverage_ref: <coverage object>
  engines_run:
    - engine_id: <id>
      version: <version>
      input_ref: <ref>
      output_ref: <ref>
      status: PASS | DEGRADED | FAILED
  assumptions: []
  missing_inputs: []
  warnings: []
  generated_at: <timestamp>
  audit_refs: []
```

**[FACT]** The conversational agent MUST NOT claim that it analyzed trailing history, merchant behavior, trend, forecast error, or cross-pillar patterns unless the receipt or equivalent runtime evidence proves those computations ran.

---

## 30. Confidence model interface

O8 confidence should consider at least:

- source completeness;
- reconciliation coverage;
- date coverage;
- number of comparable observations;
- stale segments;
- contradictory evidence;
- correction frequency;
- merchant/category confidence;
- forecast model error;
- statistical uncertainty;
- cross-pillar alignment quality where used.

**[FACT]** A long history with poor evidence quality is not automatically high confidence.

---

## 31. Missing-history behavior

When the requested historical window is not sufficiently covered, O8 must:

- identify the uncovered period;
- state which sources are missing;
- narrow the effective window if useful;
- avoid invented interpolation unless a governed statistical method explicitly permits it and labels it as estimated;
- lower confidence;
- provide the smallest evidence request that would materially improve the analysis.

A valid answer may be:

> “Reliable history is available for the trailing 90 days; the prior quarter is incomplete because statements for one account are missing.”

An invalid answer is silently pretending one year of evidence exists because the owner requested one year.

---

## 32. Historical contradiction behavior

If two source records disagree about a historical fact:

1. preserve both sources;
2. apply O1 reconciliation rules;
3. do not average balances or transaction facts;
4. mark affected longitudinal outputs degraded/unknown until resolved;
5. identify which conclusions are affected;
6. recompute after resolution;
7. retain the previous degraded view for audit.

---

## 33. Decision-support integration

O3 may request O8 evidence when evaluating a contemplated decision.

O8 may supply:

- similar past decisions;
- historical liquidity after similar commitments;
- merchant/category behavior;
- prior travel-cycle costs;
- prior recurring-commitment burden;
- forecast accuracy for comparable horizons;
- previous override outcomes;
- historical regime context.

**[FACT]** Historical similarity is evidence, not destiny. O3 remains responsible for current decision analysis.

---

## 34. Protection integration

O2 may consume O8 patterns to identify recurring protection risks such as:

- repeated late obligations;
- recurring fees;
- repeated low-liquidity windows;
- repeated statement-cycle exceptions;
- duplicate-charge patterns;
- recurrent merchant disputes;
- escalating debt-service burden.

O8 does not itself execute protective action.

---

## 35. Capital-allocation integration

O4 may consume O8 history to determine whether capital-allocation assumptions are realistic.

Examples:

- historical essential-spend variance;
- actual lifestyle baseline;
- debt-paydown sustainability;
- sinking-fund recurrence;
- savings consistency;
- historical surplus durability;
- recurring irregular costs.

**[AGREED]** This should help prevent plans that assume unrealistic overnight spending reduction.

---

## 36. Wealth-growth integration

O5 may consume O8 history for:

- realized net-worth trajectory;
- liability trajectory;
- productive-capital history;
- goal-funding progress;
- contribution history;
- liquidity resilience history;
- purchasing-power context when O16 provides it;
- forecast-vs-actual wealth trajectory.

Forecast wealth remains distinct from realized historical wealth.

---

## 37. Cognitive-offloading integration

O6 may use O8 to generate scheduled briefs such as:

- “This week differs from your trailing 90-day pattern in these areas.”
- “This merchant/category is unusually high relative to your baseline.”
- “The current payday cycle is tracking better/worse than comparable cycles.”
- “Your forecast error in this category has improved/deteriorated.”

O6 presents; O8 computes and proves.

---

## 38. User-facing historical brief contract

A concise O8 brief should prefer:

1. **What changed historically?**
2. **Compared with what baseline?**
3. **Is it material?**
4. **What evidence supports the conclusion?**
5. **How complete is the history?**
6. **Why does it matter now?**
7. **What would change the interpretation?**

Example structure:

```markdown
Historical read
- Window: <period>
- Coverage: <status>
- Material change: <engine-backed statement>
- Baseline: <comparison period>
- Evidence: <refs>
- Confidence: <value/band>
- Decision implication: <bounded conclusion>
- Missing: <gap if any>
```

---

## 39. Weekly longitudinal review

The weekly review should consume O8 outputs for:

- trailing 7/30/90-day spending changes;
- merchant/category changes;
- obligations due/missed;
- liquidity trend;
- debt/credit changes;
- forecast-vs-actual error;
- exceptions opened/closed;
- decision outcomes reaching review date;
- regime trajectory;
- one-to-three high-value historical insights.

**[FACT]** Weekly review does not close accounting periods unless the owning close contract says so.

---

## 40. Monthly longitudinal close interface

O8 should consume the immutable monthly-close object and create comparison-ready history.

Monthly historical review may include:

- income change;
- spending change;
- category variance;
- debt movement;
- liquidity movement;
- fees/interest;
- forecast error;
- unusual events;
- regime distribution;
- decision outcomes;
- structural-change candidates.

Later corrections create successor historical interpretations linked to the successor monthly close.

---

## 41. Quarterly and annual review interface

Quarterly/annual views should be used for slower-moving structure rather than daily noise.

Potential outputs:

- regime transitions and duration;
- debt burden direction;
- wealth trajectory;
- income trajectory;
- purchasing-power context;
- capital-allocation effectiveness;
- recurring lifestyle baseline;
- forecast calibration;
- emergency-reserve resilience;
- strategic-goal progress;
- income-expansion necessity;
- repeated decision errors or successful overrides.

---

## 42. Historical outcome attribution

O8 supplies factual history to later O21/O22/O26/O27 attribution and learning objectives.

It must distinguish:

- realized outcome;
- avoided committed cost;
- forecast benefit;
- counterfactual estimate;
- ambiguous outcome.

**[FACT]** O8 must not convert a counterfactual estimate into a realized saving.

---

## 43. Retrospective bias control

O8 must guard against hindsight bias.

Rules:

- preserve evidence available at decision time;
- preserve forecast version at forecast time;
- preserve policy/model version;
- preserve unknowns that existed then;
- do not judge an earlier recommendation using information unavailable at the time without explicitly labeling the retrospective analysis;
- distinguish “the model was wrong given available evidence” from “new information later changed the outcome.”

---

## 44. Historical model-version comparison

When statistical or policy models change, O8 should support controlled comparison:

- old model prediction;
- new model retrospective prediction on the same frozen inputs;
- actual outcome;
- difference in error;
- limitations;
- migration decision.

**[FACT]** The new model must not rewrite the old production record. It may create a retrospective benchmark.

---

## 45. Evidence retention and HIMAYAH v2

**[AGREED]** Under the owner-approved HIMAYAH v2 design direction, ordinary personal NIZAM artifacts should default to `trusted_private` inside the Trusted NIZAM Boundary (VPS + Google Drive), subject to final governance implementation and verification.

For O8 this means the durable mirror should preserve readable historical evidence needed for analysis, including eligible:

- bank statements;
- SMS transaction exports;
- normalized ledgers;
- monthly closes;
- historical analysis outputs;
- decision records;
- forecast evaluations;
- merchant/category mappings;
- research evidence;
- cross-pillar analysis records.

Credentials, passwords, API keys, private keys, tokens, `.env` material, and any artifact explicitly classified `strict_local` or `strict_local_maximum` remain excluded according to the final implemented HIMAYAH policy.

**[FACT]** This section records a proposed owner-approved governance evolution. It is not evidence that the runtime privacy policy has already been migrated.

---

## 46. Drive historical mirror

O8 requires a durable historical manifest for every Drive-eligible longitudinal artifact.

Conceptual mirror record:

```yaml
drive_historical_mirror:
  artifact_id: <local artifact>
  artifact_version: <version>
  classification: <HIMAYAH class>
  local_hash: <hash>
  drive_ref: <reference>
  mirrored_at: <timestamp>
  read_back_hash: <hash>
  read_back_confirmed: true | false
  supersedes_drive_ref: <optional>
  retention_status: <hot/warm/archive>
  audit_refs: []
```

**[FACT]** A successful upload response alone is not sufficient. Read-back or equivalent landed-file proof is required before the mirror is considered complete.

---

## 47. Recovery contract

If the VPS is lost, O8 should be reconstructable from the permitted durable evidence mirror plus schemas/contracts and canonical runtime restoration procedures.

Recovery must be able to reconstruct:

- evidence catalog;
- historical transactions from canonical exports/ledgers;
- monthly closes;
- decision/forecast history;
- regime transition history;
- longitudinal analyses;
- supersession chains;
- computation receipts;
- audit references.

**[INFERENCE]** If a material Drive-eligible historical artifact exists only on the VPS, O8 should flag a recovery-completeness defect.

---

## 48. Storage-aware retention

O8 history can become large. Local retention therefore should be policy-driven.

Retention policy may consider:

- current VPS free capacity;
- historical storage-growth rate;
- retrieval cost;
- active analysis windows;
- successful Drive mirror/read-back status;
- source criticality;
- required hot-cache period;
- rebuild cost.

**[AGREED]** The purpose is to keep operationally useful data locally while preventing historical accumulation from threatening runtime stability.

O8 must not delete the only known copy of a required historical artifact.

---

## 49. Agent responsibilities

### Finance Orchestrator

- requests longitudinal analyses;
- ensures O1 state/reconciliation prerequisites are met;
- routes outputs to O2/O3/O4/O5/O6/O7 and later objectives;
- does not calculate money directly.

### Evidence Ingestion Agent

- registers historical evidence;
- preserves period metadata and source lineage;
- does not declare reconciled history.

### Reconciliation Agent

- resolves canonical transaction/balance history;
- publishes reconciliation references consumed by O8.

### Longitudinal Intelligence Engine/Agent

- requests governed statistical calculations;
- assembles coverage objects and history views;
- records computation receipts;
- cannot overwrite canonical finance truth.

### Monitoring Agent

- consumes O8 changes for trend/anomaly alerts;
- does not execute financial action.

### Decision Agent

- consumes relevant O8 evidence for current decisions;
- preserves current-state precedence.

### Audit Agent

- verifies provenance, supersession, computation receipts, and policy/schema versions.

---

## 50. Agent-to-agent envelope additions

Longitudinal tasks should extend the shared envelope with:

```yaml
longitudinal_request:
  task_id: <id>
  request: <question>
  canonical_state_version: <O1 state>
  requested_windows: []
  historical_coverage_required: <level>
  input_artifacts: []
  allowed_cross_pillar_sources: []
  assumptions: []
  unresolved_items: []
  expected_output: <analysis type>
  write_permissions: <none/analysis-record-only>
  approval_required: <bool>
  completion_status: <status>
  audit_refs: []
```

---

## 51. Write permissions

O8 may write:

- longitudinal analysis records;
- historical coverage objects;
- computation receipts;
- forecast evaluation records;
- audit-linked interpretation versions;
- approved Drive mirror manifests.

O8 may not directly write:

- canonical transactions;
- authoritative account balances;
- obligations;
- actual income records;
- final user decisions;
- payments/transfers/borrowings/investments;
- passwords/tokens/keys;
- unapproved policy changes.

---

## 52. Failure modes

### FM-01 — Missing historical periods

**Risk:** false trend confidence.  
**Required behavior:** coverage downgrade, explicit missing periods, narrowed conclusion.

### FM-02 — Duplicate evidence inflates history

**Risk:** false spending increase.  
**Required behavior:** consume O1 dedupe/reconciliation only; fail if canonical status unavailable.

### FM-03 — Corrected statement rewrites history destructively

**Risk:** audit loss.  
**Required behavior:** successor versions with provenance.

### FM-04 — Pending transaction counted as historical spend twice

**Risk:** inflated actuals.  
**Required behavior:** honor pending/posted relationship contract.

### FM-05 — Transfer counted as expense

**Risk:** distorted spending history.  
**Required behavior:** consume canonical transfer pairing.

### FM-06 — Forecast interpreted as actual

**Risk:** false historical wealth/liquidity.  
**Required behavior:** evidence-class separation.

### FM-07 — Cross-pillar correlation presented as cause

**Risk:** invalid behavioral conclusion.  
**Required behavior:** correlation/inference labeling and causal prohibition.

### FM-08 — Long history with low source quality treated as high confidence

**Risk:** false certainty.  
**Required behavior:** confidence depends on coverage/reconciliation/quality, not duration alone.

### FM-09 — New model rewrites old forecast

**Risk:** calibration fraud.  
**Required behavior:** immutable original forecast plus retrospective benchmark.

### FM-10 — Historical artifact mirrored but not readable

**Risk:** false recovery confidence.  
**Required behavior:** Drive read-back verification.

### FM-11 — VPS accumulation threatens runtime

**Risk:** operational failure.  
**Required behavior:** storage-aware retention after verified durable mirroring.

### FM-12 — LLM claims a trend without engine execution

**Risk:** fabricated intelligence.  
**Required behavior:** require O8 computation receipt.

---

## 53. Validation fixtures

O8 implementation must include synthetic/redacted fixtures for at least:

1. complete 90-day history;
2. missing statement month;
3. duplicated imported statement;
4. pending transaction later posted;
5. refund/reversal after original purchase;
6. transfer between owned accounts;
7. merchant alias change;
8. category correction;
9. late-arriving statement changing a prior period;
10. superseding monthly close;
11. forecast versus actual with measurable error;
12. forecast with missing actual;
13. regime transition history;
14. false regime candidate that never activates;
15. owner decision followed by later observed outcome;
16. override outperforming recommendation;
17. recommendation outperforming override;
18. ambiguous decision outcome;
19. seasonal recurring merchant pattern;
20. one-off outlier that must not become a structural trend;
21. structural change candidate after persistent shift;
22. cross-pillar correlation with no causal conclusion;
23. stale historical source;
24. contradictory historical source;
25. Drive mirror read-back failure;
26. local retention cleanup only after verified mirror;
27. computation receipt missing required engine output;
28. deliberate validator tamper.

---

## 54. Required validation assertions

At minimum, tests must prove:

- missing history lowers confidence;
- duplicates do not inflate totals;
- pending/posted states are not double-counted;
- transfers do not become spending;
- reversals preserve history;
- corrections create successor analysis versions;
- forecasts remain distinct from actuals;
- later evidence does not mutate evidence-at-decision-time;
- structural-change logic does not trigger from a single outlier unless policy explicitly permits it;
- cross-pillar association does not become causal language;
- Drive mirror is not marked complete without read-back proof;
- O8 cannot write canonical transaction truth;
- computation receipt is required for claimed analysis;
- deliberate tamper causes validation failure.

---

## 55. Tamper test requirement

Verification is incomplete until at least one known-valid O8 artifact is intentionally altered and the validator demonstrably fails.

Minimum tamper candidates:

- remove computation-proof section;
- change a FACT forecast result to actual without evidence;
- delete coverage status;
- remove supersedes reference from corrected analysis;
- mark a failed Drive read-back as confirmed;
- remove canonical-state reference.

The repository gate must be restored to green after the tampered fixture is removed.

---

## 56. Audit requirements

Every material historical analysis should preserve:

- actor/agent;
- request;
- canonical-state version;
- requested/effective windows;
- evidence refs;
- coverage ref;
- engine versions;
- policy/schema versions;
- outputs;
- confidence;
- assumptions;
- missing inputs;
- successor/supersession links;
- Drive mirror status where applicable;
- timestamp;
- approval reference if any policy mutation is involved.

---

## 57. Monthly-close audit linkage

Each monthly longitudinal view must reference the monthly close used.

If a close is superseded:

- old view remains auditable;
- new view points to successor close;
- materially changed historical conclusions are enumerated;
- downstream cached analyses are invalidated/rebuilt according to policy.

---

## 58. Historical data-quality metrics

O8 should expose metrics such as:

- evidence coverage percentage/output from governed engine;
- reconciled-period ratio;
- unresolved-exception count;
- stale-period count;
- correction frequency;
- missing-account periods;
- merchant normalization confidence distribution;
- category-confidence distribution;
- forecast-evaluation completion;
- Drive mirror completeness.

**[FACT]** Exact formulas and thresholds belong to deterministic/statistical policy, not this prose contract.

---

## 59. Longitudinal performance metrics

O8 itself should be evaluated on:

- historical query reproducibility;
- evidence traceability;
- coverage accuracy;
- correction propagation accuracy;
- trend false-positive rate where measurable;
- forecast-evaluation completion rate;
- computation-receipt completeness;
- historical rebuild time;
- Drive recovery completeness;
- owner usefulness of longitudinal insights.

---

## 60. Migration plan

### Step 1 — inventory historical sources

Identify available statements, transaction exports, SMS archives, account histories, close records, forecasts, decisions, and existing ledgers.

### Step 2 — register evidence periods

Create EvidenceRecords with explicit period start/end, source location, hash/fingerprint, quality, sensitivity, parser version, and ingestion time.

### Step 3 — reconcile through O1

Do not build history directly from unverified raw source files when canonical reconciliation is required.

### Step 4 — create canonical historical windows

Implement standard rolling/calendar/evidence-bound windows.

### Step 5 — create coverage engine

No longitudinal output should exist without a coverage assessment.

### Step 6 — build deterministic/statistical historical engines

Start with transaction, merchant/category, income, obligation, debt, liquidity, regime, and forecast-error views.

### Step 7 — persist immutable analysis versions

Create successor semantics for corrected history.

### Step 8 — integrate O6 scheduled briefs

Expose high-value changes, not dashboards for their own sake.

### Step 9 — integrate O3/O4/O5/O7 interfaces

Provide historical evidence to decisions/allocation/wealth/regime layers without creating competing truth.

### Step 10 — implement HIMAYAH v2 migration only after the privacy governance contract is formally updated and verified

Do not assume owner-approved design equals deployed policy.

### Step 11 — implement Drive mirror/read-back

Persist eligible history in readable trusted-private form after classification.

### Step 12 — run validation and tamper proof

Only then mark O8 runtime-verified.

---

## 61. Repository implementation guidance

Exact file names and database tables must be derived from the repository after reading the current owning contracts and nearest implementation/tests. Do not invent a schema path or command.

Any new `src/` or `tests/` implementation file should declare its owning contract and phase within the first 20 lines, consistent with the project build rules.

Preferred implementation traits:

- pure historical query functions where possible;
- deterministic/statistical engine ports injected into orchestration;
- explicit as-of semantics;
- immutable/versioned records;
- synthetic/redacted fixtures;
- no provider-specific assumptions without evidence;
- no hidden global state;
- no LLM arithmetic authority.

---

## 62. Definition of done

O8 is complete only when all of the following are true:

1. standard historical windows exist;
2. coverage is computed before longitudinal conclusions;
3. reconciled canonical state is the financial input authority;
4. historical corrections are successor/versioned;
5. merchant/category history is available with provenance;
6. income/obligation/debt/liquidity histories are available;
7. O7 regime history is queryable;
8. decision history preserves evidence available at decision time;
9. forecast-vs-actual evaluation persists;
10. historical comparisons identify comparable windows;
11. missing/stale/conflicting history degrades confidence correctly;
12. cross-pillar interfaces preserve correlation/causation boundaries;
13. computation receipts prove analyses ran;
14. O6 can consume O8 for scheduled owner-facing briefs;
15. O3/O4/O5/O7 can consume O8 without O8 taking their authority;
16. eligible historical artifacts can be mirrored/read back under implemented HIMAYAH policy;
17. recovery from durable records is documented/tested;
18. storage retention protects VPS capacity without deleting the only copy;
19. focused tests pass;
20. repository gate passes;
21. tamper test fails as expected;
22. final artifact is read back and integrity checked.

---

## 63. Acceptance questions

O8 should be rejected if any answer below is “no”:

1. Can the system explain exactly what historical period it actually has evidence for?
2. Can it distinguish transaction time from ingestion/reconciliation time?
3. Can it prove that duplicates, transfers, reversals, and pending/posted states are handled correctly?
4. Can it reconstruct historical merchant/category behavior without inventing missing data?
5. Can it compare forecasts with later actuals without rewriting the original forecast?
6. Can it preserve evidence available at decision time separately from hindsight?
7. Can it say when a trend is unsupported because the period is incomplete?
8. Can it prevent correlation from becoming causation?
9. Can it reproduce a historical analysis from evidence refs and engine versions?
10. Can late-arriving evidence produce a successor view instead of silent mutation?
11. Can the owner inspect eligible historical evidence in Drive after the approved privacy redesign is implemented?
12. Can the system recover historical intelligence after VPS loss?
13. Can it prove the longitudinal engines actually ran?
14. Does a deliberate tamper cause the validation gate to fail?

---

## 64. Evidence classification for this design

### [FACT]

- The supplied Financial NIZAM architecture requires provenance, versioning, append/audit history, reconciliation before optimization, forecast-vs-actual tracking, and immutable/versioned monthly closes.
- Current transaction, account, forecast, decision, evidence, merchant, alert, and audit entities contain the fields needed to support a longitudinal layer conceptually.
- Historical corrections are intended to be versioned/superseding rather than destructive.
- The monitoring contract already includes weekly/monthly forecast-vs-actual review.
- The owner has explicitly required trailing days/weeks/months/quarters/years analysis and later comparison of predictions against actual outcomes.

### [INFERENCE]

- A dedicated historical-coverage object is necessary to prevent false confidence when source periods are incomplete.
- O8 should be an analytical layer over canonical financial history rather than another source of truth.
- Readable Drive history plus versioned runtime indexes best supports the owner’s recovery and longitudinal-analysis goals after HIMAYAH v2 is actually implemented.

### [ASSUMPTION]

- Exact database technology, physical table names, statistical thresholds, minimum observations, and provider-specific retention constraints are intentionally unspecified until repository/runtime research is performed.
- Exact cross-pillar join rules will be finalized by the future privacy/data contracts and owning pillar contracts.

### [MISSING]

- Runtime implementation of O8 has not been inspected or verified in this session.
- Current bank/provider-specific historical APIs and export semantics in Egypt have not been researched for this design document.
- Exact credit-score calculation methodology and provider rules remain unresolved.
- HIMAYAH v2 remains an owner-approved design direction, not verified deployed policy.

---

## 65. Objective handoff

O8 provides the historical intelligence substrate required by later objectives.

Primary handoffs:

- **O9 Merchant & Behavioral Intelligence** consumes merchant/category history and unusualness context.
- **O10 Cross-Domain Decision Intelligence** consumes time-aligned longitudinal finance evidence for cross-pillar correlation.
- **O11 Evidence-Based Reasoning** consumes historical evidence classes, provenance, and confidence.
- **O12 Forecast Accountability** consumes forecast-vs-actual records and model-version history.
- **O15 Dynamic Resilience** consumes historical variance and liquidity-floor history.
- **O19 Adversarial Decision Protection** consumes similar past decisions and later outcomes.
- **O20 Persuasion Learning** consumes communication/decision outcome history.
- **O21/O22/O26/O27** consume realized outcomes, counterfactual context, and immutable decision history.
- **O28 Dynamic Materiality** consumes owner-relative unusualness and historical impact distributions.
- **O35/O39** consume historical mirror/recovery completeness metrics.

**[AGREED]** O8 must remain a historical intelligence layer. It must not become a second financial ledger, a causal psychology engine, or an authority to execute financial action.
