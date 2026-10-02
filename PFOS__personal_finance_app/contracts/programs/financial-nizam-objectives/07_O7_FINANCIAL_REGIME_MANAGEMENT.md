# Financial NIZAM Objective O7 — Financial Regime Management

**Status:** PROPOSED OVERHAUL DESIGN — owner-approved objective, implementation not yet verified  
**Objective ID:** O7  
**Objective name:** Financial Regime Management  
**Program:** Financial NIZAM / PFOS / MAL implementation namespace  
**Owner:** Seif ElSherbiny  
**Version:** 0.1.0-design  
**Sensitivity:** review_before_commit  
**Owning phase:** Phase 7 — adaptive financial posture, transition governance, tactical-policy routing  
**Precedence:** safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting subordinate contract → verified runtime evidence → historical/draft material

---

## 1. Objective

**[FACT]** O7 consumes reconciled financial truth from O1, protection state from O2, decision context from O3, allocatable-capital outputs from O4, wealth trajectory from O5, and owner-facing continuity from O6. O7 MUST NOT create a second transaction ledger, balance source, obligation registry, forecast store, wealth store, or decision ledger.

**[AGREED]** Financial NIZAM must explicitly classify the owner’s current financial operating regime and explain why that regime is active. The regime is not a motivational label. It is a governed state that changes which financial tactics receive priority while preserving the same long-term wealth objective.

**[AGREED]** The four owner-approved regimes are:

1. **SURVIVAL** — protect liquidity, critical obligations, and immediate continuity; avoid adding fragility.
2. **STABILIZATION** — rebuild buffers, reduce leakage and costly liabilities, improve reliability, and restore maneuverability.
3. **GROWTH** — deploy genuine surplus toward productive saving/investment, capability, strategic goals, and accelerated wealth creation while preserving resilience.
4. **EXPANSION** — use strong financial capacity and resilient optionality to pursue higher-upside opportunities without compromising the protected base.

**[AGREED]** Balanced optimization remains the governing philosophy. A temporary SURVIVAL posture does not replace the long-term objective of wealth growth; it changes the tactical ordering of actions until the evidence supports a transition.

**[AGREED]** The system must avoid unrealistic austerity. It should prefer sustainable marginal improvement across days, weeks, and months instead of recommending abrupt spending reductions that are unlikely to be maintained unless a genuine critical condition requires emergency action.

**[FACT]** Authoritative monetary amounts, ratios, percentages, forecast outputs, liquidity values, protected-floor values, debt metrics, and materiality scores MUST come from governed deterministic/statistical engines. The conversational layer may explain regime outputs but MUST NOT invent or manually calculate them.

---

## 2. Governing source decisions

### 2.1 Existing canonical-candidate rules

**[FACT]** The Financial NIZAM constitution requires evidence before interpretation, reconciliation before optimization, explicit freshness, one canonical financial state, deterministic monetary truth, human authority, protected liquidity before debt optimization, and explicit treatment of unknown/stale/conflicting evidence.

**[FACT]** The cashflow/liquidity contract distinguishes present liquidity from forecast income, requires obligations and buffers to be modeled before discretionary capacity, and returns limited/unknown state rather than false precision when material evidence is stale or unreconciled.

**[FACT]** The forecasting contract requires versioned assumptions, scenarios, horizon, confidence, error tracking, and degraded confidence when evidence is stale or forecasting error increases.

**[FACT]** The monitoring contract already defines daily, weekly, monthly, statement-cycle, salary-event, and event-driven financial review cadences, with P0–P3 priorities that do not create new authority.

**[FACT]** The decision engine requires liquidity impact, effective cost, penalty/default risk, reversibility, cash-flow timing, goal alignment, option value, uncertainty, complexity/stress cost, and explicit user constraints for material decisions.

**[FACT]** The validation contract requires one canonical current-state model, evidence/assumption tracing, freshness, human gates, forecast persistence, and explicit failure on stale or conflicting financial state.

### 2.2 Owner decisions incorporated into O7

**[AGREED]** Regime classification must be explicit and visible in meaningful Financial NIZAM recommendations.

**[AGREED]** Current conditions can justify a SURVIVAL-first tactical posture even when the long-run strategy remains balanced optimization and wealth growth.

**[AGREED]** Regime classification must consider historical evidence across trailing days, weeks, months, quarters, and years where available, rather than relying only on the latest account snapshot.

**[AGREED]** Regime changes must be explainable with strong proof, including what changed, which pillars were affected, and why the previous tactical posture is no longer appropriate.

**[AGREED]** The system must continuously compare its regime classification and related forecasts against later actual outcomes so that policy thresholds, confidence, and explanations can be recalibrated.

**[AGREED]** External economic intelligence may affect risk assumptions or scenario interpretation but must never directly overwrite verified financial facts.

**[AGREED]** The owner remains final decision-maker. Regime classification changes recommendations and challenge intensity, not spending authority.

---

## 3. Scope

O7 governs:

1. regime taxonomy and semantics;
2. deterministic regime-classification policy interface;
3. regime evidence packet;
4. candidate-to-active transition process;
5. hysteresis and anti-flapping controls;
6. transition confidence and uncertainty;
7. regime-specific tactical priorities;
8. regime-specific recommendation interpretation;
9. regime-sensitive capital-allocation interfaces;
10. regime-sensitive materiality/challenge interfaces;
11. historical regime reconstruction when evidence permits;
12. regime trajectory and duration analytics;
13. transition explanation and owner-facing proof;
14. transition review cadence;
15. transition exception handling;
16. regime forecast-versus-actual learning;
17. regime interaction with external economic risk assumptions;
18. regime interaction with income-cycle planning;
19. regime interaction with dynamic protected liquidity;
20. audit and recovery requirements.

O7 does **not** govern:

- transaction ingestion or reconciliation logic;
- authoritative balance calculation;
- the monetary protected-floor formula itself;
- the materiality formula itself;
- wealth-return calculation;
- autonomous payment, borrowing, refinancing, transfer, investment, or liquidation;
- final owner decision;
- psychological diagnosis;
- unsourced market prediction;
- direct mutation of canonical financial facts from news/social signals;
- free-form LLM selection of thresholds.

---

## 4. Regime doctrine

**[AGREED]** O7 uses the following doctrine:

> **Long-term strategy can remain stable while tactical financial posture changes.**

A regime answers:

> **Given the verified financial state, current risk, near-term obligations, resilience, and trajectory, what class of financial tactics deserves priority now?**

A regime does not answer:

- whether the owner is “good” or “bad” with money;
- whether the owner deserves a purchase;
- whether a single transaction was morally acceptable;
- whether wealth growth is permanently abandoned;
- whether all spending must be cut;
- whether the owner must obey an agent.

**[FACT]** Regime selection is a state classification problem over governed inputs. It is not a conversational opinion.

**[AGREED]** The system must be able to say:

> “Your long-term strategy has not changed. Your current tactical regime has.”

---

## 5. Regime definitions

### 5.1 SURVIVAL

**Purpose:** preserve continuity and prevent avoidable financial damage when resilience is weak or near-term risk is materially elevated.

Typical policy emphasis:

- protect critical obligations;
- preserve required liquidity;
- avoid new high-fragility commitments;
- reduce preventable fees/penalties;
- prevent debt compounding where possible;
- defer non-urgent irreversible commitments when evidence supports doing so;
- narrow action count to the highest-value interventions;
- prioritize evidence quality and reconciliation;
- prefer realistic spending improvements over performative austerity;
- surface income-risk or income-expansion needs when expense reduction alone is insufficient.

**[FACT]** SURVIVAL does not mean “no lifestyle spending.” Any safe-to-spend or discretionary amount still comes from the governed engines.

**[FACT]** SURVIVAL does not authorize the system to liquidate assets, borrow, refinance, or transfer money autonomously.

### 5.2 STABILIZATION

**Purpose:** rebuild maneuverability after fragility has reduced but before the financial system is strong enough for normal growth-oriented deployment.

Typical policy emphasis:

- rebuild protected and emergency reserves;
- resolve recurring leakage;
- improve debt structure and debt-service resilience through governed decision analysis;
- close stale evidence/reconciliation gaps;
- improve forecast accuracy;
- build sinking funds for known irregular costs;
- reduce dependency on fragile credit loops;
- restore predictable positive operating cash behavior;
- increase optionality while avoiding premature risk-taking.

**[AGREED]** STABILIZATION is not punishment after SURVIVAL. It is the bridge between fragility protection and sustained growth.

### 5.3 GROWTH

**Purpose:** use verified surplus capacity to improve long-term wealth while preserving resilience.

Typical policy emphasis:

- fund strategic goals;
- increase productive saving/investment capacity;
- accelerate high-value debt reduction where justified;
- fund capability/income-expansion investments where evidence supports them;
- optimize capital allocation above the protected floor;
- preserve lifestyle sustainability;
- increase net worth and productive assets;
- monitor opportunity cost and long-horizon trajectory.

**[FACT]** GROWTH does not mean every available unit of capital must be invested. O4 governs allocatable capital and O15 will own the dynamic resilience floor.

### 5.4 EXPANSION

**Purpose:** deploy strong, resilient financial capacity toward higher-upside opportunities while preserving the protected base and avoiding hidden concentration risk.

Typical policy emphasis:

- evaluate higher-upside opportunities;
- improve diversification and optionality where relevant;
- fund major strategic life/career/capability goals;
- consider larger capital commitments through O3/O28/O19 controls;
- protect against complacency, concentration, and lifestyle creep;
- maintain strong evidence, reserves, and downside scenarios.

**[FACT]** EXPANSION is not a license for speculative or leveraged action. All consequential transactions remain human-controlled and governed by decision, materiality, protection, and approval contracts.

---

## 6. Authoritative regime-state object

O7 should define a machine-readable `financial_regime_state` object conceptually containing at least:

```yaml
financial_regime_state:
  regime_state_id: <stable identifier>
  canonical_state_version: <O1 reference>
  classification_policy_version: <version>
  active_regime: SURVIVAL|STABILIZATION|GROWTH|EXPANSION|UNKNOWN
  candidate_regime: SURVIVAL|STABILIZATION|GROWTH|EXPANSION|null
  transition_state: STABLE|CANDIDATE|PENDING_CONFIRMATION|TRANSITIONED|DEGRADED|UNKNOWN
  effective_from: <timestamp>
  prior_regime: <regime|null>
  evidence_window:
    short_term: <reference>
    medium_term: <reference>
    long_term: <reference>
  input_refs:
    reconciliation_state: <O1 ref>
    protection_state: <O2 ref>
    decision_state: <O3 refs as relevant>
    capital_state: <O4 ref>
    wealth_state: <O5 ref>
    protected_floor_state: <future O15 ref|null>
    forecast_state: <forecast ref>
    debt_state: <debt/obligation ref>
    income_state: <income refs>
    external_risk_state: <future O16 ref|null>
  signal_results: []
  hard_gates: []
  transition_reasons: []
  counterevidence: []
  confidence_state: HIGH|MEDIUM|LOW|INSUFFICIENT
  freshness_state: FRESH|LIMITED|STALE|CONFLICTING
  explanation_ref: <artifact ref>
  computation_receipt_ref: <receipt>
  generated_at: <timestamp>
```

**[FACT]** This is a design contract, not a claim that the runtime schema already exists.

---

## 7. Classification inputs

O7 MUST consume governed outputs rather than scrape arbitrary chat text.

### 7.1 Core required input families

At minimum, the classifier interface should be able to consume references to:

- canonical reconciled balances/state;
- current and upcoming obligations;
- protected-liquidity status;
- cashflow/forecast path;
- debt-service burden and debt-risk state;
- account/credit utilization state where supported;
- known planned commitments;
- actual-vs-plan behavior;
- recent fees/penalties/default-risk events;
- available discretionary capacity;
- reserve/emergency-buffer state;
- wealth trajectory;
- income reliability and concentration;
- evidence freshness/reconciliation quality.

### 7.2 Historical windows

**[AGREED]** Where evidence permits, classification should consider multiple windows:

- trailing days;
- trailing weeks;
- trailing months;
- trailing quarters;
- trailing years.

The regime engine should not assign equal weight to every window automatically. Weighting MUST be policy-versioned and testable.

### 7.3 External intelligence

**[AGREED]** Egypt/MENA/global economic intelligence may inform risk assumptions when materially relevant.

Permitted flow:

> external evidence → confidence/source assessment → governed risk-assumption update → deterministic/statistical model → regime impact

Prohibited flow:

> headline/rumor → LLM manually changes regime

Social media, prediction markets, community discussion, FX/market signals, and news may contribute to scenario/risk context but cannot become verified personal financial facts.

---

## 8. Signal categories

The exact formulas and thresholds belong in deterministic policy/configuration, not this router document. O7 nevertheless requires explicit signal categories.

### 8.1 Liquidity resilience

Examples of governed signals:

- protected-floor coverage state;
- minimum forecast liquidity point;
- near-term essential-spend coverage;
- emergency-buffer status;
- current cash versus committed outflows;
- expected-income dependency.

### 8.2 Obligation safety

Examples:

- critical obligations due soon;
- overdue/missed obligations;
- debt minimum coverage;
- penalty/default risk;
- installment load;
- recurring commitment burden.

### 8.3 Debt and credit fragility

Examples:

- debt-service burden;
- revolving dependency;
- credit utilization where reliable inputs exist;
- repeated payment-cycle dependency;
- new debt creation;
- settlement coverage.

**[FACT]** Credit-score or institutional-score effects may only be used when reliable, jurisdiction/provider-relevant evidence or a governed proxy contract exists. O7 MUST NOT fabricate a bank score.

### 8.4 Operating cash behavior

Examples:

- persistent operating surplus/deficit state;
- discretionary leakage trend;
- forecast-versus-actual deviation;
- frequency of emergency reallocations;
- dependence on unreceived income.

### 8.5 Wealth and productive-capital trajectory

Examples:

- realized net-worth direction;
- productive-capital growth;
- reserve quality;
- liability reduction;
- strategic-goal funding progress;
- optionality/fragility indicators.

### 8.6 Income resilience

Examples:

- income reliability;
- income concentration;
- purchasing-power erosion risk;
- change in expected income versus commitments;
- need for income-expansion attention.

### 8.7 Evidence quality

A regime classifier MUST incorporate:

- freshness;
- reconciliation completeness;
- source quality;
- missing periods;
- unresolved conflicts;
- forecast calibration quality.

**[FACT]** If material inputs are stale/conflicting, the classifier may return `UNKNOWN` or retain the last reliable regime with degraded confidence. It must not create false precision.

---

## 9. Hard gates

**[PROPOSED]** O7 should distinguish between ordinary weighted signals and hard gates.

A hard gate is a policy condition that prevents entry into a more aggressive regime regardless of aggregate score until the blocking condition is resolved.

Candidate hard-gate families include:

- unreconciled/stale material accounts;
- uncovered imminent critical obligations;
- protected-floor breach;
- unresolved critical debt/default risk;
- missing evidence sufficient to invalidate current liquidity certainty;
- active critical protection event from O2;
- other owner-approved deterministic conditions.

**[FACT]** Exact hard-gate thresholds are **MISSING** until implemented in a governed policy contract. O7 must not invent them conversationally.

---

## 10. Transition policy

### 10.1 Candidate then active

A regime should normally transition through:

1. `STABLE` active regime;
2. deterministic evidence creates a `CANDIDATE` regime;
3. transition policy checks hard gates, minimum evidence, confidence, and hysteresis;
4. if satisfied, `TRANSITIONED` becomes active;
5. prior regime and transition reason remain immutable in history.

### 10.2 No casual jumps

**[AGREED]** One payday, one large inflow, or one good spending day should not automatically move the system from SURVIVAL to GROWTH.

**[AGREED]** One ordinary discretionary overspend should not automatically collapse GROWTH into SURVIVAL.

### 10.3 Critical transitions

A defined critical event may justify rapid defensive transition when protection policy says immediate risk materially changes the financial system.

Examples of event classes that may qualify, depending on deterministic policy:

- loss/delay of expected income;
- newly discovered major obligation;
- material liquidity shortfall;
- missed critical payment;
- material fraud/error impacting available funds;
- sudden debt-service escalation;
- verified external shock with a governed direct personal-finance effect.

**[FACT]** Critical transition conditions MUST be explicitly versioned. “The agent felt worried” is never sufficient.

---

## 11. Hysteresis and anti-flapping

**[PROPOSED]** O7 must implement hysteresis: evidence required to *enter* a more aggressive regime should not be identical to evidence required to *remain* there or exit it.

The purpose is to prevent regime oscillation caused by ordinary transaction noise.

Required anti-flapping controls should include, where appropriate:

- minimum evidence window;
- candidate persistence requirement;
- different enter/exit thresholds;
- hard-gate precedence;
- cooldown/dwell policy;
- confidence floor;
- manual review flag when signals contradict materially.

**[FACT]** Exact durations/thresholds are configuration decisions and remain `MISSING` until deterministic policy is authored and tested.

---

## 12. Regime-sensitive tactical routing

O7 must not itself calculate amounts. It changes policy emphasis and routes upstream/downstream engines accordingly.

### 12.1 SURVIVAL routing

Prioritize:

- O2 protection;
- O15 dynamic resilience when available;
- essential obligation coverage;
- evidence reconciliation;
- low-fragility capital choices;
- short-horizon forecast certainty;
- income continuity/expansion analysis where expense cuts are insufficient;
- aggressive challenge for high-impact fragility-increasing decisions through O19 when materiality warrants.

### 12.2 STABILIZATION routing

Prioritize:

- reserve rebuilding;
- debt/credit dependency reduction;
- leakage correction;
- sinking-fund construction;
- forecast accuracy;
- return to predictable operating surplus;
- removal of hard gates preventing GROWTH.

### 12.3 GROWTH routing

Prioritize:

- O4 capital optimization;
- O5 wealth growth;
- strategic goal funding;
- productive saving/investment capacity;
- capability/income expansion;
- medium/long-horizon scenario analysis;
- preserving resilience while deploying surplus.

### 12.4 EXPANSION routing

Prioritize:

- opportunity analysis;
- concentration/downside review;
- capital deployment with optionality preservation;
- strategic asset/capability expansion;
- higher materiality scrutiny for irreversible commitments;
- continued reserve and protection verification.

---

## 13. Recommendation language contract

A material recommendation should expose the active regime and its consequence.

Example pattern:

> **Regime:** SURVIVAL  
> **Why:** governed protection/liquidity signals remain below the transition policy required for STABILIZATION.  
> **Decision implication:** preserving liquidity currently receives more weight than discretionary acceleration.  
> **What would change this:** the transition evidence packet lists the conditions required for reclassification.

**[AGREED]** The system may say:

> “This would normally be acceptable under GROWTH, but the active SURVIVAL posture makes liquidity preservation more valuable right now.”

It may NOT say:

> “You are in Survival so you are forbidden from buying this.”

Human authority remains unchanged.

---

## 14. Transition explanation contract

Every transition or rejected transition must explain:

1. prior regime;
2. candidate regime;
3. final active regime;
4. canonical-state version;
5. policy version;
6. hard gates evaluated;
7. major supporting signals;
8. material counterevidence;
9. freshness/reconciliation state;
10. confidence;
11. tactical changes caused by the regime;
12. what evidence would move the classification again;
13. audit/computation receipt reference.

**[AGREED]** Explanations must show proof rather than only displaying the label.

---

## 15. Regime trajectory

O7 should preserve historical regime periods:

```yaml
regime_period:
  regime: SURVIVAL|STABILIZATION|GROWTH|EXPANSION
  from: <timestamp>
  to: <timestamp|null>
  entry_reason_ref: <transition ref>
  exit_reason_ref: <transition ref|null>
  policy_version: <version>
  starting_state_ref: <canonical snapshot>
  ending_state_ref: <canonical snapshot|null>
  outcome_summary_ref: <later review|null>
```

This supports questions such as:

- How long was the owner in each regime?
- Which events usually preceded deterioration?
- Which actions preceded sustainable improvement?
- Did a regime transition occur too early or too late?
- Did recommendations during that regime improve later outcomes?

**[FACT]** Historical association does not automatically prove causation.

---

## 16. Historical reconstruction

Where sufficient historical evidence exists, Financial NIZAM may reconstruct historical regime periods.

Requirements:

- use the evidence actually available for the historical period;
- label reconstruction separately from contemporaneous classifications;
- preserve policy/model version used for reconstruction;
- do not claim the system “knew” a regime at the time if classification was created retrospectively;
- include missing periods and confidence limitations.

A reconstructed regime is an analytical artifact, not a rewritten historical fact.

---

## 17. Regime and the dynamic protected floor

**[AGREED]** O15 will own the dynamic protected-liquidity model. O7 may consume its state.

Expected interaction:

- SURVIVAL may require a stronger resilience bias;
- STABILIZATION emphasizes restoring the required floor/reserve sustainably;
- GROWTH permits more capital deployment above the protected base;
- EXPANSION permits broader opportunity analysis while preserving the base.

**[FACT]** O7 must never calculate a floor amount itself.

---

## 18. Regime and capital allocation

O4 remains authoritative for allocatable capital.

O7 supplies the tactical policy context:

```text
O1 truth
  ↓
O2 protection
  ↓
O7 active regime
  ↓
O4 capital-allocation policy weighting
  ↓
O3 decision comparison / O5 wealth trajectory
```

**[FACT]** The regime may change weighting/priorities but cannot make unavailable money allocatable.

---

## 19. Regime and materiality/challenge

O28 will own dynamic materiality and O19 will own adversarial challenge.

O7 must expose the active regime as an input because the same purchase can have different systemic impact under different resilience conditions.

Example:

- under EXPANSION, a reversible discretionary decision may be LOW/MODERATE materiality;
- under SURVIVAL, the same nominal purchase could have greater protected-floor or obligation impact and therefore become more material.

**FACT:** Nominal value alone must never determine this interaction.

---

## 20. Regime and income-cycle planning

The active regime should influence pre-payday planning without predetermining the owner’s allocation decision.

Before the expected income event, the system should prepare:

- current regime;
- transition candidate if any;
- protected obligations;
- protected-floor state reference;
- unresolved protection risks;
- capital-allocation choices conditioned on actual receipt;
- what receipt amount/timing would or would not change the regime.

**[FACT]** Expected income remains forecast-only until received and reconciled.

---

## 21. External macroeconomic risk interaction

O16 will own the Economic Early-Warning Radar.

O7 may consume approved risk-state outputs such as:

- inflation/purchasing-power risk;
- currency risk;
- interest-rate/credit conditions;
- labor/income risk;
- regional/global disruption risk.

The classifier must distinguish:

- verified personal state;
- deterministic derived personal state;
- external observed facts;
- external scenario assumptions;
- weak-signal/speculative context.

A rumor cannot directly change the regime.

---

## 22. Confidence and uncertainty

Regime confidence must reflect the quality of the evidence and the stability of the classification.

Potential confidence degraders:

- stale account evidence;
- unresolved reconciliation conflict;
- missing statement periods;
- high forecast error;
- rapidly changing obligations;
- unverified income assumptions;
- contradictory signal families;
- significant external-risk uncertainty.

When confidence becomes insufficient:

- return `UNKNOWN`, or
- retain last reliable regime with an explicit degraded-confidence flag according to policy.

The system MUST state which behavior the policy used.

---

## 23. Owner disagreement

The owner may disagree with the active regime.

O7 must then provide:

- evidence packet;
- governing policy version;
- supporting signals;
- counterevidence;
- transition requirements;
- missing inputs that could alter classification.

**[FACT]** The owner cannot conversationally rewrite reconciled facts, but may supply corrective evidence. Corrections flow through O1.

**[AGREED]** The system must not use regime labels as rhetorical leverage or shame language.

---

## 24. Forecast accountability

O7 must record regime predictions/expectations sufficiently for later evaluation.

For each transition, later review should ask:

- Did liquidity/resilience improve or deteriorate as expected?
- Did the regime persist or immediately reverse?
- Were hard gates correctly identified?
- Did the tactical recommendations fit observed outcomes?
- Did the system transition too early or too late?
- Did forecast error suggest policy recalibration?

**[AGREED]** The regime engine must be capable of learning from misclassification through controlled policy/model versioning, not silent mutation.

---

## 25. Regime calibration metrics

The implementation should support measurements such as:

- transition count by period;
- median regime duration;
- rapid reversal rate;
- candidate-to-active conversion rate;
- transition confidence versus later stability;
- hard-gate activation frequency;
- stale/unknown classification frequency;
- forecast error before/after transition;
- owner disagreement rate;
- percentage of transitions with complete computation receipts;
- percentage of transitions later assessed as premature/late/correctly timed under an approved evaluation method.

**[FACT]** These are measurement categories. Exact success thresholds remain `MISSING` until the implementation/validation contract defines them.

---

## 26. Computation proof contract

Every authoritative regime classification MUST have proof that the required computation actually ran.

Minimum receipt concept:

```yaml
regime_computation_receipt:
  receipt_id: <id>
  canonical_state_version: <O1 version>
  classification_policy_version: <version>
  inputs_used: []
  engines_or_rules_run: []
  hard_gates_checked: []
  historical_windows_used: []
  external_risk_refs: []
  missing_inputs: []
  freshness_state: <state>
  active_regime: <regime>
  candidate_regime: <regime|null>
  confidence_state: <state>
  result_ref: <regime state object>
  generated_at: <timestamp>
```

**[AGREED]** A chat response that says “I evaluated your regime” without a valid receipt/reference is not proof of computation.

**[FACT]** The router/LLM MUST NOT produce authoritative money values or invent a regime-computation receipt.

---

## 27. Scheduled evaluation cadence

O7 should support:

### Intraday
Regime is normally read, not recomputed from scratch unnecessarily, unless material new evidence changes relevant state.

### Daily
Check whether material state changes create a candidate transition.

### Weekly
Review regime persistence, supporting signals, behavioral/forecast actuals, and transition risk.

### Monthly
Perform a deeper regime reassessment using reconciled close data, debt/liquidity movement, forecast error, and allocation progress.

### Quarterly
Review whether regime policy remains calibrated to long-run wealth strategy and whether macro/income resilience assumptions materially changed.

### Event-driven
Reassess when events materially affect resilience, obligations, income, debt, liquidity, evidence quality, or other configured hard gates.

---

## 28. User-facing cadence integration

O6 remains responsible for communication scheduling.

O7 supplies these fields to O6:

- active regime;
- confidence;
- whether a transition candidate exists;
- why it exists;
- what tactical priorities changed;
- what would change the classification;
- whether owner attention is required.

The morning brief should surface regime state when meaningful. Afternoon/night briefs should surface it again only if state, confidence, transition candidate, or consequences materially changed.

---

## 29. Failure modes

### F1 — Regime from chat memory
**Failure:** agent calls the user “SURVIVAL” based on remembered conversation rather than canonical data.  
**Required response:** refuse authoritative classification; refresh governed state.

### F2 — One-event promotion
**Failure:** one payday promotes SURVIVAL directly to GROWTH.  
**Required response:** transition policy/hysteresis blocks unless explicit critical/exception policy says otherwise.

### F3 — One-event collapse
**Failure:** one ordinary purchase collapses GROWTH to SURVIVAL.  
**Required response:** anti-flapping policy prevents unsupported transition.

### F4 — Stale inputs
**Failure:** material account/obligation evidence is stale.  
**Required response:** degrade confidence, retain/UNKNOWN according to policy, explain missing evidence.

### F5 — External rumor mutation
**Failure:** social rumor changes regime directly.  
**Required response:** reject; route through external-risk evidence/confidence pipeline.

### F6 — Hidden hard gate
**Failure:** system promotes to GROWTH while an uncovered critical obligation exists.  
**Required response:** hard-gate test fails.

### F7 — Threshold drift
**Failure:** agent changes thresholds conversationally.  
**Required response:** reject; require policy version update through governed change process.

### F8 — No computation proof
**Failure:** regime label is shown without valid computation receipt.  
**Required response:** mark unverified; do not present as authoritative.

### F9 — Regime as coercion
**Failure:** label is used to shame or override human authority.  
**Required response:** validation failure; rewrite to factual decision implications.

### F10 — False causation
**Failure:** historical correlation between an action and regime improvement is described as causal without evidence.  
**Required response:** downgrade to inference/hypothesis and preserve alternatives.

---

## 30. Validation fixtures

Implementation tests should include at least:

1. reconciled SURVIVAL fixture with imminent obligations and weak liquidity;
2. STABILIZATION candidate fixture with improving protection but insufficient evidence for GROWTH;
3. GROWTH fixture with protected base and verified allocatable capacity;
4. EXPANSION fixture with strong resilience and higher opportunity capacity;
5. one-payday anti-promotion test;
6. one-small-purchase anti-collapse test;
7. hard-gate prevents promotion test;
8. stale material account returns degraded/UNKNOWN test;
9. conflicting signals test;
10. policy-version persistence test;
11. candidate persistence/hysteresis test;
12. critical defensive transition test;
13. external-rumor cannot directly mutate regime test;
14. external authoritative risk-state may influence configured model test;
15. owner disagreement does not rewrite regime fact test;
16. corrective evidence routes through O1 test;
17. expected income not treated as received test;
18. computation receipt required test;
19. regime history immutable append test;
20. retrospective reconstruction clearly labeled test;
21. rapid reversal calibration test;
22. O4 capital allocation consumes regime but does not duplicate classifier test;
23. O6 brief consumes regime reference, not chat memory test;
24. human authority preserved test;
25. anti-shame language validation test.

---

## 31. Tamper test requirement

A regime-validation gate is not proven merely because it passes a correct artifact.

At least one deliberate tamper must be performed during implementation validation, for example:

- remove `classification_policy_version`;
- remove computation receipt;
- bypass a configured hard gate;
- feed stale account state while claiming HIGH confidence;
- alter active regime without transition history;
- allow a raw social-media rumor to mutate regime directly.

The corresponding validation test MUST fail.

---

## 32. Audit and ledger requirements

Every material regime event should append or reference an immutable audit event containing:

- event timestamp;
- prior regime;
- candidate regime;
- final regime;
- transition state;
- canonical-state version;
- policy version;
- evidence refs;
- hard gates;
- counterevidence;
- confidence/freshness;
- computation receipt;
- explanation artifact;
- actor/system version;
- later outcome-review ref when available.

**[FACT]** Corrections preserve prior state and reason; they do not erase historical classification.

---

## 33. HIMAYAH and persistence

O7 itself should contain no credentials, tokens, API keys, passwords, `.env` content, or secret material.

Under the owner-approved HIMAYAH v2 redesign direction:

- regime states, explanations, audit events, financial evidence refs, and non-secret personal analysis may be `trusted_private` and readable within the Trusted NIZAM Boundary once that policy is formally implemented;
- secrets remain excluded from Drive;
- current runtime behavior must continue to obey the actually implemented policy until HIMAYAH v2 supersession is verified.

**[FACT]** This objective document records the intended redesign; it does not prove the privacy implementation already changed.

---

## 34. Recovery and Drive mirror

Regime history is decision-relevant memory and should be durably recoverable when policy permits.

A successful persistence event requires:

1. artifact generated;
2. HIMAYAH classification;
3. eligible Drive mirror/write;
4. receipt;
5. destination read-back verification;
6. local/VPS retention according to storage policy;
7. recovery manifest update.

If regime history exists only on the VPS and is eligible for durable mirroring, O6/O39 should treat that as a persistence defect.

---

## 35. Migration plan

### Stage 1 — Contract only

- approve O7 taxonomy and boundaries;
- define machine-readable regime-state schema;
- define transition/audit event schema;
- define policy-version interface;
- register dependencies on O1/O2/O4/O5/O6.

### Stage 2 — Deterministic policy implementation

- implement signal adapters using existing authoritative engine outputs;
- implement hard gates;
- implement candidate/active transition state;
- implement hysteresis/anti-flapping;
- implement computation receipts;
- implement immutable history.

### Stage 3 — Historical reconstruction

- run retrospective classification over periods with adequate evidence;
- label reconstructed versus contemporaneous classifications;
- measure rapid reversal/misclassification patterns;
- do not rewrite original financial facts.

### Stage 4 — User interaction

- expose active regime and explanation in O6 briefs;
- connect O7 to O3/O4/O19/O28 interfaces;
- expose “what would change the regime” evidence.

### Stage 5 — Calibration

- compare transitions against later actuals;
- version policy improvements;
- preserve previous policy outputs;
- require regression + tamper tests before promotion.

---

## 36. Repository implementation guidance

When implementation begins, exact file paths MUST be determined from the current repository after reading:

1. repository steering/AGENTS instructions;
2. Financial NIZAM owning contracts;
3. nearest schemas/configuration;
4. existing implementation and tests.

**[FACT]** This design document intentionally does not invent final source-code paths or commands before repository inspection.

Likely artifact classes, subject to inspection, include:

- regime state schema;
- regime transition event schema;
- regime policy/config;
- deterministic classifier module;
- history ledger integration;
- monitoring integration;
- O6 briefing adapter;
- validation fixtures/tests;
- research/calibration report.

---

## 37. Definition of done

O7 is not complete until runtime evidence proves all of the following:

- exactly one authoritative regime state exists for a canonical-state version/policy version;
- active regime is produced by governed deterministic/statistical logic rather than LLM opinion;
- classification inputs trace to authoritative references;
- stale/conflicting inputs degrade or block classification correctly;
- hard gates work;
- hysteresis prevents ordinary regime flapping;
- critical defensive transitions work under defined policy;
- transitions preserve prior regime/history;
- every transition has explanation and computation proof;
- O6 can surface regime state without duplicating its computation;
- O4/O3 can consume regime context without creating competing truth;
- expected income never becomes current liquidity;
- external weak signals cannot directly mutate regime;
- human authority remains intact;
- forecast-vs-actual calibration can assess transition quality;
- privacy/persistence obey the actually implemented HIMAYAH policy;
- recovery mirror/read-back succeeds where eligible;
- focused tests pass;
- repository gate passes;
- at least one deliberate tamper causes the gate to fail.

Until those conditions are observed, runtime status MUST remain **DESIGNED / NOT RUNTIME-VERIFIED**.

---

## 38. Acceptance questions

The implementation should be considered behaviorally aligned only if the owner can answer **yes** to these questions:

1. Can Financial NIZAM tell me which regime I am in and show why?
2. Can it explain what changed when the regime changes?
3. Can it show the evidence and policy version instead of giving me a vague label?
4. Does it avoid changing regimes because of one ordinary event?
5. Does SURVIVAL protect me without pretending my long-term growth strategy disappeared?
6. Does STABILIZATION clearly show what remains before GROWTH becomes justified?
7. Does GROWTH deploy only genuinely available capacity?
8. Does EXPANSION preserve resilience instead of becoming permission for speculation?
9. Can the system admit `UNKNOWN` when the data is insufficient?
10. Can it later evaluate whether its regime transitions were actually well calibrated?

---

## 39. Evidence classification for this design

### FACT

**[FACT]** Existing PFOS contracts require reconciled evidence, freshness, deterministic monetary truth, forecast confidence, human authority, and protection of imminent obligations/liquidity.
**[FACT]** Existing monitoring contracts define recurring and event-driven review.
**[FACT]** Existing decision contracts require liquidity, debt/default risk, reversibility, timing, uncertainty, and user constraints.
**[FACT]** O1–O6 are design artifacts in the current objective sequence; they are not runtime proof by themselves.

### INFERENCE

**[INFERENCE]** A four-regime state machine with hysteresis is the cleanest way to implement the owner’s requested adaptive tactical posture without rewriting long-term strategy.
**[INFERENCE]** Candidate-state transitions, hard gates, and policy-versioning are necessary to avoid unstable or opaque regime changes.
**[INFERENCE]** Regime history can become a high-value input for later forecast calibration, decision learning, and behavioral analysis.

### ASSUMPTION

**[ASSUMPTION]** The current repository does not already contain a fully implemented equivalent four-regime engine. This must be confirmed during implementation research.
**[ASSUMPTION]** Exact thresholds, dwell periods, and transition formulas remain undefined until deterministic policy design and testing.

### MISSING

**[MISSING]** Verified runtime schema/path for regime state.
**[MISSING]** Verified deterministic transition thresholds.
**[MISSING]** Verified hysteresis/dwell configuration.
**[MISSING]** Verified hard-gate policy values.
**[MISSING]** Verified historical regime reconstruction quality.
**[MISSING]** Verified integration with future O15/O16/O18/O19/O28 objectives.

---

## 40. Objective handoff

O7 produces governed regime context for later objectives but does not absorb their responsibilities.

Primary downstream handoffs:

- **O8 Longitudinal Financial Intelligence:** deeper historical interpretation of regime periods and trend context;
- **O11 Evidence-Based Reasoning:** richer proof/explanation presentation;
- **O12 Forecast Accountability:** regime forecast and transition calibration;
- **O13 Income-Cycle Orchestration:** pre-payday regime-sensitive preparation;
- **O15 Dynamic Resilience:** authoritative protected-floor/resilience model;
- **O16 Economic Early-Warning Radar:** macro risk context;
- **O18 Income Resilience & Expansion:** income-side strategic response;
- **O19 Adversarial Decision Protection:** challenge escalation under materially adverse decisions;
- **O28 Dynamic Materiality:** regime-sensitive materiality scoring.

O7 remains the authoritative owner of **financial tactical regime classification and transition governance**.
