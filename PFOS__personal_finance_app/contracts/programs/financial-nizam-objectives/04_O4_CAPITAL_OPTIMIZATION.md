# Financial NIZAM Objective O4 — Capital Optimization

**Status:** PROPOSED OVERHAUL DESIGN — owner-approved objective, implementation not yet verified  
**Objective ID:** O4  
**Objective name:** Capital Optimization  
**Program:** Financial NIZAM / PFOS / MAL implementation namespace  
**Owner:** Seif ElSherbiny  
**Version:** 0.1.0-design  
**Sensitivity:** review_before_commit  
**Owning phase:** Phase 4 — Capital allocation policy, surplus deployment, and dynamic reallocation  
**Precedence:** safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting subordinate contract → verified runtime evidence → historical/draft material

---

## 1. Objective

**[FACT]** Financial NIZAM must allocate already-verified, presently available capital according to explicit policy after O1 Financial Truth and O2 Financial Protection establish the current state and protected requirements.

**[AGREED]** The long-run operating philosophy is **balanced optimization**: protect a minimum resilience floor first, then allocate resources above that floor dynamically across debt reduction, current life, planned commitments, reserves, savings/investment capacity, and long-term wealth creation according to marginal benefit and strategic impact.

**[AGREED]** The tactical allocation policy is state-dependent. During Survival, the system may rationally prioritize resilience and near-term liquidity. During Stabilization, it can rebuild buffers and reduce structural pressure. During Growth, more capital can move toward productive savings/investment and strategic goals. During Expansion, surplus capital can be deployed toward higher-upside opportunities while preserving the agreed resilience boundary.

**[AGREED]** Financial NIZAM must not rely on abrupt, unrealistic austerity assumptions. Improvement should be behaviorally achievable and may occur through marginal changes day over day, week over week, and month over month while the system measures whether those changes improve the trajectory.

**[FACT]** O4 does not calculate authoritative money conversationally. All monetary amounts, ratios, marginal-return comparisons, safe-to-allocate amounts, debt effects, liquidity effects, and percentage impacts must be supplied by deterministic or explicitly governed statistical engines. The conversational layer may explain those outputs but must not invent or restate authoritative values independently.

---

## 2. Governing source decisions

### 2.1 Existing canonical-candidate rules

**[FACT]** The Financial NIZAM constitution requires evidence before interpretation, reconciliation before optimization, protection of imminent obligations and required liquidity, deterministic monetary truth, one canonical financial state, and human authority over consequential financial actions.

**[FACT]** The budgeting contract defines budget as allocation rather than punishment. Actual budgeting assigns money already available in canonical reconciled state. Forecast allocation is a distinct forecast-only view and must not be treated as current money.

**[FACT]** Existing budget groups include fixed obligations, essential variable spending, debt service, liquidity/emergency buffer, sinking funds, goals/savings, discretionary lifestyle, travel/events, gifts/family, professional/education, and unassigned/contingency.

**[FACT]** Each allocation category requires a purpose, priority, target rule, rollover policy, overspend policy, currency, and active state. Reallocation between categories must expose the tradeoff.

**[FACT]** Sinking funds are reserved availability for known irregular purposes and are not expenses until the associated transaction occurs.

**[FACT]** The debt contract requires this ordering: avoid delinquency/contractual penalty → preserve required minimums → protect near-term liquidity → compare incremental payoff using deterministic cost and cash-flow effects → incorporate explicit relational, ethical, and owner constraints.

**[FACT]** The liquidity engine distinguishes gross cash, reserved cash, available cash, net operational liquidity, and safe-to-spend. Expected income is not current liquidity.

**[FACT]** Existing cash-flow ordering is opening available cash → known income → expected income kept separate → fixed obligations → debt minimums → planned commitments → estimated variable essentials → buffer reservations → uncertainty reserve → projected closing state.

**[FACT]** The Decision Engine requires urgency, liquidity impact, deterministic effective-cost result, penalty/default risk, reversibility, cash-flow timing, goal alignment, option value, uncertainty, complexity/stress cost, and explicit owner constraints for material decisions.

### 2.2 New owner directions incorporated into this overhaul

**[AGREED]** Financial NIZAM is a Personal CFO and Wealth Operating System, not merely a budgeting application.

**[AGREED]** Balanced optimization is the governing philosophy, but the current regime may temporarily shift tactical allocation toward Survival when debts, commitments, or weak liquidity make resilience the dominant constraint.

**[AGREED]** The system should continuously direct attention toward stronger liquidity, lower financial fragility, better capital allocation, increasing net worth, and long-term life goals.

**[AGREED]** Allocation should be dynamically informed by historical trailing days, weeks, months, quarters, and years when evidence exists rather than by static category percentages.

**[AGREED]** The protected-liquidity floor is dynamic and should later incorporate historical essential-spend behavior, upcoming obligations, behavioral variance, emergency reserve needs, current regime, and approved external-risk assumptions.

**[AGREED]** Credit may be used as a timing instrument when it genuinely preserves liquidity and optionality, but the system must distinguish productive timing from dependency that merely rolls one obligation into another.

**[AGREED]** Income-cycle allocation should be prepared before expected salary/income receipt so capital has an intended use before it arrives, while unreceived income remains forecast-only.

**[AGREED]** Allocation policy should be evaluated later against actual outcomes, forecast error, trajectory improvement, and whether the recommendation genuinely improved resilience or wealth capacity.

---

## 3. Scope

O4 governs:

1. capital-allocation policy over verified available resources;
2. determination of allocatable capital after protected requirements are reserved;
3. regime-sensitive allocation priorities;
4. tradeoff exposure across capital uses;
5. debt-paydown versus liquidity comparison interfaces;
6. emergency-reserve and buffer allocation interfaces;
7. sinking-fund and planned-commitment allocation;
8. current-lifestyle and discretionary allocation boundaries;
9. goals/savings allocation;
10. investment-capacity planning interfaces without execution;
11. travel/event/family/professional allocation;
12. unassigned/contingency allocation;
13. income-cycle allocation proposals;
14. reallocation after new evidence or overspending;
15. rollover behavior and period close;
16. opportunity-cost and marginal-benefit comparison;
17. multi-currency allocation references where governed engines exist;
18. allocation confidence, assumptions, and missing-data handling;
19. audit records explaining why capital moved between purposes;
20. forecast-vs-actual evaluation of allocation effectiveness.

O4 does **not** govern:

- transaction ingestion and deduplication;
- account reconciliation;
- protected-floor calculation itself;
- autonomous payments, transfers, investment execution, debt repayment, borrowing, or purchases;
- provider-specific tax or regulatory advice;
- the full economic/news intelligence pipeline;
- final materiality scoring;
- high-friction challenge or override sequencing;
- portfolio security selection or trading;
- canonical net-worth calculation by itself.

Those capabilities remain owned by O1/O2/O3 or later objectives and are consumed through typed interfaces.

---

## 4. Capital-optimization doctrine

**[AGREED]** O4 follows this ordering whenever authoritative inputs are available:

1. verify O1 canonical-state version, freshness, and reconciliation status;
2. verify O2 protection state and all material exceptions;
3. obtain the governed protected-floor and emergency-reserve references;
4. reserve mandatory and already-committed requirements;
5. determine currently allocatable capital through deterministic engines;
6. identify the current financial regime;
7. identify active goals and owner constraints;
8. evaluate candidate capital uses;
9. compare marginal benefit, liquidity cost, reversibility, timing, uncertainty, and strategic contribution;
10. create an allocation proposal, not an execution order;
11. show the main tradeoffs and strongest alternative allocation;
12. require owner approval where policy requires it;
13. persist the approved allocation state without rewriting historical allocations;
14. monitor actual outcomes and reallocate prospectively when reality changes;
15. compare forecast versus actual and feed later policy learning.

**[FACT]** If canonical state is materially stale or unreconciled, O4 cannot present a fully confident allocation plan. It must narrow, defer, or label the proposal according to missing-data policy.

---

## 5. Capital pools and conceptual boundaries

### 5.1 Protected capital

Protected capital is not available for discretionary optimization. It includes governed reservations for mandatory obligations, required minimum debt service, essential near-term expenditure, dynamic protected-floor requirements, emergency reserves where applicable, and already-approved commitments.

**[FACT]** O4 consumes protected values from owning engines. It does not invent them.

### 5.2 Allocatable capital

Allocatable capital is the deterministic remainder that may be assigned among eligible uses under the current policy and regime.

**[FACT]** Future income does not become allocatable current capital until it actually arrives and is reconciled. Forecast allocation may model future income, but it must remain separately labeled.

### 5.3 Contingent capital

Contingent capital is capital whose availability depends on unresolved or uncertain events such as expected reimbursement, uncertain income, pending refund, sale proceeds, or forecasted savings.

Contingent capital may influence scenarios but cannot be treated as already available.

### 5.4 Restricted capital

Restricted capital is owner- or contract-constrained for a specific purpose and may not be reallocated silently. Examples include sinking funds, earmarked family commitments, legally/contractually restricted funds, and explicitly protected owner goals.

---

## 6. Financial regimes and allocation posture

### 6.1 Survival

**Purpose:** prevent deterioration, preserve maneuverability, and avoid new fragility.

Expected allocation bias:

- mandatory obligations first;
- preserve protected liquidity;
- preserve emergency capacity;
- avoid avoidable penalties/default;
- prioritize structural debt pressure where deterministic analysis supports action without breaching liquidity protection;
- constrain new recurring obligations;
- preserve realistic essential and baseline lifestyle spending rather than assuming impossible cuts;
- defer optional capital deployment that materially weakens resilience.

**[AGREED]** Survival is a tactical posture, not a permanent identity or moral judgment.

### 6.2 Stabilization

**Purpose:** move from fragile equilibrium toward dependable resilience.

Expected allocation bias:

- rebuild buffers;
- remove recurring leakage;
- improve debt-service structure;
- establish or repair sinking funds;
- reduce forecast variance;
- reduce dependence on credit timing for ordinary living expenses;
- gradually expand strategic savings capacity.

### 6.3 Growth

**Purpose:** convert stable cash flow into measurable wealth-building capacity.

Expected allocation bias:

- maintain resilience floor;
- fund strategic goals;
- increase productive savings/investment capacity;
- continue debt optimization where marginal benefit remains compelling;
- support capabilities or assets with credible future return;
- preserve lifestyle sustainability rather than maximizing savings at all costs.

### 6.4 Expansion

**Purpose:** deploy true surplus capital into higher-upside opportunities while preserving resilience.

Expected allocation bias:

- maintain robust liquidity and emergency capacity;
- diversify sources of future financial capacity;
- fund high-value strategic opportunities;
- allow more aggressive capital deployment only where downside remains tolerable;
- keep future optionality and concentration risk visible.

### 6.5 Regime transition

**[FACT]** O4 does not autonomously declare a regime. It consumes O7's regime classification when O7 is implemented. Until then, any regime field remains proposed/assumed and must be explicitly labeled.

**[AGREED]** The system must be able to say: **“The long-term strategy has not changed. The current tactical regime has.”**

---

## 7. Allocation categories

### 7.1 Fixed obligations

Capital required for dated, contractual, or otherwise mandatory commitments.

Allocation rule: protected before discretionary optimization.

### 7.2 Essential variable spending

Historically and currently supported essential variable costs required for ordinary functioning.

Allocation rule: use governed historical/forecast ranges rather than unrealistic austerity assumptions.

### 7.3 Debt service

Includes required minimums and approved incremental payoff allocations.

Allocation rule: minimums are protected; incremental payoff competes with other uses only after the protected floor remains intact.

### 7.4 Liquidity and emergency buffer

Capital intentionally reserved to preserve short-term resilience and emergency maneuverability.

Allocation rule: determined by owning resilience engines/policies; not available for ordinary optimization unless the owner explicitly changes policy.

### 7.5 Sinking funds

Capital reserved for known irregular future expenses.

Allocation rule: remain separate from actual expense recognition; reallocation requires explicit tradeoff visibility.

### 7.6 Goals and savings

Capital reserved for named strategic outcomes.

Allocation rule: each goal should expose priority, target, horizon, funding state, reversibility, and tradeoff when capital is moved elsewhere.

### 7.7 Investment capacity

Capital that may become eligible for investment after protection and strategic constraints are satisfied.

**[FACT]** O4 may identify investment capacity but cannot execute investment transactions. Security selection and investment execution remain outside O4 and human-controlled.

### 7.8 Discretionary lifestyle

Capital intentionally available for optional present consumption and quality of life.

**[AGREED]** Lifestyle is not treated as automatically wasteful. O4 should optimize sustainability rather than pursue punitive spending reduction.

### 7.9 Travel and events

Capital reserved for planned travel, social events, celebrations, or other bounded experiences.

Allocation rule: linked to scenario estimates and sinking-fund logic where appropriate; large commitments may invoke O3 decision analysis and O28 materiality.

### 7.10 Gifts and family

Capital associated with family support, gifts, informal obligations, and relational commitments.

Allocation rule: owner values and explicit relational constraints can affect priority and must not be silently replaced by purely financial scoring.

### 7.11 Professional and education

Capital directed toward work capability, learning, tools, certifications, or other capacity-building expenditures.

Allocation rule: treat as strategic spending when evidence supports future capability/income value, while keeping uncertainty explicit.

### 7.12 Unassigned and contingency

Capital intentionally left uncommitted.

Allocation rule: unassigned is a legitimate state. The system must not force every available unit of capital into a category if optionality itself has value.

---

## 8. Marginal-benefit allocation

**[AGREED]** The governing question for capital above the floor is not “Which category has the highest nominal target?” but “Which eligible use creates the greatest expected marginal improvement under the owner's constraints and current regime?”

Required dimensions may include:

- liquidity resilience;
- avoided penalty/default risk;
- reduction in structural monthly pressure;
- deterministic effective financing cost;
- reversibility;
- future optionality;
- strategic-goal contribution;
- expected capability/income contribution where supported;
- uncertainty;
- timing;
- concentration risk;
- complexity/stress cost;
- current regime fit;
- owner values and explicit constraints.

**[FACT]** The LLM may not assign authoritative numerical marginal-benefit values itself. If the system uses a score, ratio, percentage, or optimization output, it must come from a deterministic or governed statistical policy engine with versioned inputs.

### 8.1 Near-tie behavior

If competing uses are numerically close or uncertainty dominates the difference, O4 should not claim a false winner. It should expose the tradeoff, preserve optionality where appropriate, and hand the owner a reversible choice.

### 8.2 Dominated allocation

Where one candidate use is clearly inferior under the explicit objective and constraints, the system may label it dominated, provided the conclusion is supported by engine outputs and no owner value/constraint has been omitted.

---

## 9. Debt versus liquidity allocation

**[FACT]** Debt payoff must not silently consume protected liquidity.

For incremental debt allocation, O4 consumes:

- debt obligation state;
- deterministic effective-cost outputs;
- due dates and penalties;
- current protected floor;
- forecasted cash-flow effect;
- future minimum-payment relief;
- current regime;
- reversibility loss from converting cash into debt reduction;
- explicit family/ethical/relational constraints where relevant.

Possible proposal classes include:

- protect minimums only;
- targeted incremental payoff;
- accelerated payoff when resilience remains safe;
- retain cash because optionality is currently more valuable;
- insufficient data.

**[FACT]** O4 cannot refinance, borrow, restructure, or make a payment.

---

## 10. Credit and liquidity timing

**[AGREED]** Credit may function as a timing instrument when it preserves liquid cash without creating hidden fragility.

O4 must distinguish:

### 10.1 Productive timing

Characteristics may include:

- known settlement date;
- future payment amount already protected;
- no dependency on new borrowing to service the prior cycle;
- no avoidable fee/interest that outweighs the liquidity benefit under governed calculations;
- improved short-term optionality without worsening structural debt pressure beyond policy.

### 10.2 Dependency loop

Warning characteristics may include:

- new credit required to service prior credit;
- settlement obligations exceed realistic future free cash flow;
- repeated roll-forward of ordinary living expenses;
- deteriorating debt ratios or institutional-credit signals where reliable data exists;
- the apparent cash position is maintained only by expanding liabilities.

**[FACT]** O4 may describe these states only from governed debt/liquidity outputs. It must not infer a credit score or provider-specific underwriting outcome without verified evidence.

---

## 11. Emergency reserve and protected floor interface

**[AGREED]** O4 treats the protected operating floor and emergency reserve as conceptually distinct:

- **protected operating floor:** capital required to navigate the expected path safely;
- **emergency reserve:** capital protected against events outside the expected path.

O4 consumes those values from O15 Dynamic Resilience once implemented.

Until O15 exists, O4 must not invent a number. It may use an explicit temporary policy reference if the owner has approved one and the source is recorded.

---

## 12. Income-cycle allocation

**[AGREED]** Allocation planning should begin before expected income arrives, while keeping forecast-only allocation separate from actual allocation.

### 12.1 Pre-income proposal

A forecast proposal may include:

- expected incoming amount reference;
- confidence/freshness of that expectation;
- obligations due before and after expected receipt;
- candidate debt allocation;
- buffer/reserve needs;
- sinking-fund contributions;
- goal contributions;
- lifestyle/discretionary allocation;
- unassigned contingency;
- strategic allocation alternatives.

### 12.2 Receipt event

When income actually lands:

1. O1 reconciles the receipt;
2. O2 rechecks protection state;
3. O4 recomputes actual allocatable capital;
4. the pre-income forecast proposal is compared with actual state;
5. differences are exposed;
6. the owner receives an updated allocation proposal.

**[FACT]** Forecast income is never current available capital before receipt.

---

## 13. Reallocation policy

### 13.1 New evidence

Any material update to balances, obligations, transactions, expected income, planned commitments, or protected-floor inputs may trigger recalculation.

### 13.2 Overspending

Overspending remains visible. It creates prospective reallocation options from lower-priority categories rather than historical rewriting.

### 13.3 Goal priority change

Changing a goal or target affects future allocation. Historical allocation remains intact.

### 13.4 Surprise expense

A surprise expense triggers O2 protection reassessment before O4 proposes redistribution.

### 13.5 Windfall or unexpected income

Unexpected income is reconciled first. O4 then proposes allocation under the current regime rather than assuming all windfalls are disposable.

### 13.6 Reimbursement

Expected reimbursement remains contingent until received and reconciled. It cannot be allocated as actual cash beforehand.

---

## 14. Behavioral realism

**[AGREED]** O4 must not optimize by assuming unrealistic reductions in ordinary life.

Required behavior:

- preserve baseline functioning;
- distinguish structural cost from discretionary variation;
- propose marginal reductions rather than impossible cuts when gradual improvement is more sustainable;
- evaluate whether prior recommendations were followed and whether actual outcomes improved;
- avoid shame language;
- distinguish temporary exceptional spending from persistent structural drift;
- offer reversible trials when uncertainty is high.

**[AGREED]** The Wealth Operating System seeks better trajectory, not maximum deprivation.

---

## 15. Goal-conflict policy

When goals conflict, O4 must expose the tradeoff rather than silently choosing.

Examples:

- debt reduction versus emergency reserve;
- travel versus strategic savings;
- professional capability investment versus debt acceleration;
- discretionary lifestyle versus near-term sinking fund;
- preserving cash versus paying down a high-cost liability;
- investing versus eliminating structural credit dependence.

Required output:

1. competing goals;
2. current priority policy;
3. current regime;
4. deterministic impact references;
5. what is sacrificed by each option;
6. reversibility;
7. uncertainty;
8. recommendation;
9. strongest counter-case;
10. evidence that would change the recommendation.

---

## 16. Opportunity-cost contract

O4 must treat opportunity cost as explicit, not rhetorical.

For a proposed allocation, the system should identify at least the strongest credible alternative use of that capital when one exists.

The opportunity-cost object should contain:

- candidate allocation use;
- alternative allocation use;
- state/snapshot version;
- horizon;
- deterministic quantitative engine references;
- forecast/scenario references;
- qualitative strategic differences;
- reversibility comparison;
- uncertainty;
- omitted factors.

**[FACT]** Counterfactual future benefit remains modeled, not realized, until supported by later evidence.

---

## 17. External intelligence interface

**[AGREED]** Capital allocation may later consume approved external economic intelligence concerning Egypt, MENA, and global conditions.

Examples may include inflation, FX conditions, rates, labor/income risk, major economic shocks, market conditions, and other relevant factors.

**[FACT]** O4 does not directly scrape or score external intelligence. It consumes bounded, provenance-rich signals from O16/O17 or another governed intelligence layer.

External intelligence may change assumptions, risk posture, or scenario weights. It may not overwrite verified balances, transactions, or obligations.

---

## 18. Cross-domain context interface

O4 may consume bounded cross-domain signals where explicitly permitted, such as:

- recovery/capacity signals;
- upcoming travel or calendar commitments;
- strategic career/capability goals;
- explicitly registered journal or decision context;
- owner-stated family obligations.

**[FACT]** Cross-domain context may influence policy or timing, but it does not become financial fact merely because it exists.

**[FACT]** Correlation does not establish causation. O4 cannot claim that a physiological or behavioral state caused better financial outcomes without appropriate evidence.

---

## 19. Allocation proposal object

Every material allocation proposal SHOULD contain:

```yaml
allocation_proposal:
  proposal_id: string
  generated_at: timestamp
  canonical_state_version: string
  policy_version: string
  reconciliation_state: string
  financial_regime_ref: string|null
  protected_floor_ref: string|null
  emergency_reserve_ref: string|null
  allocatable_capital_engine_ref: string
  currency: string
  horizon: string
  candidate_allocations:
    - category_id: string
      purpose: string
      amount_engine_ref: string
      priority: string
      rationale_refs: [string]
      opportunity_cost_ref: string|null
      reversibility: string
  unassigned_amount_engine_ref: string|null
  forecast_refs: [string]
  debt_engine_refs: [string]
  assumptions: [string]
  unknowns: [string]
  confidence_state: string
  recommendation: string
  strongest_counterargument: string
  evidence_that_changes_result: [string]
  approval_required: boolean
  user_decision: null
  audit_refs: [string]
```

**[FACT]** Any amount field is a reference to authoritative engine output, not a number calculated by the LLM.

---

## 20. Allocation ledger event

An allocation change must preserve history.

Minimum event semantics:

```yaml
allocation_event:
  event_id: string
  ts: timestamp
  proposal_id: string
  previous_allocation_version: string|null
  new_allocation_version: string
  reason: string
  trigger: string
  owner_approved: boolean
  source_refs: [string]
  computation_refs: [string]
  affected_categories: [string]
  rollback_ref: string|null
  audit_refs: [string]
```

Historical category states must remain reconstructable.

---

## 21. Computation proof

**[AGREED]** O4 must prove that the required engines actually ran before it presents an authoritative allocation recommendation.

A computation receipt must identify:

- canonical-state version;
- reconciliation status;
- policy version;
- protected-floor engine output reference;
- allocatable-capital output reference;
- obligation/debt engine outputs used;
- forecast/scenario outputs used;
- opportunity-cost comparison output where applicable;
- regime signal used if available;
- assumptions;
- missing inputs;
- generated timestamp;
- checksum or immutable audit reference where supported.

The conversational layer must not claim “I considered liquidity, debt, goals, and the regime” unless the receipt or equivalent evidence proves those inputs were processed.

---

## 22. Agent responsibilities

### 22.1 Orchestrator

Responsible for sequencing O1/O2 prerequisites, requesting O4 computation, routing missing-data exceptions, and returning the final packet.

Prohibited from creating monetary truth.

### 22.2 Budget/Allocation Agent

Responsible for category-policy evaluation, rollover logic, prospective reallocation, and allocation proposal assembly.

Prohibited from writing reconciled transaction truth or executing payments.

### 22.3 Obligation/Debt Agent

Supplies authoritative obligation and debt comparison references.

Prohibited from deciding owner priorities by itself.

### 22.4 Cashflow/Forecast Agent

Supplies liquidity, safe-to-spend, protected-floor interface, and scenario outputs.

Prohibited from labeling expected income as current money.

### 22.5 Decision Agent

Consumes O4 outputs for material choices and may invoke O3 comparison packets.

### 22.6 Audit Agent

Verifies lineage, computation proof, allocation versioning, and no silent history mutation.

### 22.7 Privacy/Approval Agent

Applies the currently governing HIMAYAH policy and future HIMAYAH v2 migration once formally approved and implemented.

---

## 23. Agent-to-agent envelope

O4 work should use the shared structured envelope:

```yaml
task_id: string
request: string
canonical_state_version: string
input_artifacts: [string]
assumptions: [string]
unresolved_items: [string]
expected_output: string
write_permissions: [string]
approval_required: boolean
completion_status: string
audit_refs: [string]
```

Additional O4 fields may include:

```yaml
allocation_context:
  protected_floor_ref: string|null
  financial_regime_ref: string|null
  current_allocation_version: string|null
  active_goal_refs: [string]
  debt_state_refs: [string]
  forecast_refs: [string]
```

Temporary agents may analyze but may not maintain competing private versions of canonical financial truth or approved allocation state.

---

## 24. Write authority

### 24.1 What O4 may write

Subject to the owning repository and implemented policy, O4 may propose or persist:

- allocation proposals;
- approved budget/allocation states;
- allocation-change events;
- rollover decisions after required approval;
- category-target updates after owner approval where needed;
- forecast-only allocation proposals clearly labeled as such;
- audit/learning references.

### 24.2 What O4 may not write

O4 may not independently mutate:

- reconciled transactions;
- account balances;
- liability truth;
- user_decision fields;
- payment status without evidence;
- executed investment positions;
- external bank/provider state;
- secrets/credentials.

---

## 25. Owner authority

**[FACT]** Allocation proposals are recommendations until owner approval where the policy requires it.

The owner may:

- accept;
- reject;
- partially accept;
- re-prioritize goals;
- mark an amount/purpose protected;
- choose a lower-ranked option;
- explicitly override the recommendation.

O4 must preserve the recommendation, owner decision, and later outcome as separate facts.

**[AGREED]** If the owner makes a financially adverse choice, O4 continues to optimize the new reality rather than disengaging or moralizing.

---

## 26. User experience

### 26.1 Ten-second allocation summary

When O4 is relevant, the concise surface should answer:

- current regime, if available;
- whether the protected floor is intact;
- whether allocatable capital exists;
- highest-priority allocation change;
- strongest tradeoff;
- effect on next income cycle;
- effect on long-term trajectory;
- confidence/missing-data state.

### 26.2 Detailed allocation review

On request, show:

- category availability;
- protected reservations;
- debt allocation;
- sinking funds;
- goal funding;
- lifestyle/discretionary capacity;
- contingency/unassigned capital;
- scenario differences;
- opportunity cost;
- evidence and computation receipts.

### 26.3 Language

Use neutral financial language. Avoid “good/bad person,” “discipline failure,” “wasteful” as unsupported moral judgment, or shame-inducing commentary.

---

## 27. Scheduled operating cadence

O4 participates in the owner-approved communication cadence:

### Late morning check-in

- allocation state after overnight/new evidence;
- protected-floor integrity;
- meaningful changed constraints;
- today's allocatable/discretionary state;
- highest-value action if any.

### Afternoon check-in

- intraday drift;
- new transactions/commitments that alter allocation;
- reallocation proposals if required.

### Night close

- actual versus planned category state;
- exceptions;
- tomorrow's protected commitments;
- any allocation decision requiring attention.

### Weekly review

- allocation versus actual;
- drift and recurring leakage;
- forecast error;
- capital moved between categories;
- trajectory effect;
- policy questions for the next week.

### Monthly close

- finalized category actuals;
- approved rollover;
- sinking-fund status;
- debt/liquidity allocation outcome;
- savings/goal progress;
- allocation effectiveness;
- next-period proposal.

### Quarterly review

- regime-aware capital-allocation review;
- resilience versus growth mix;
- debt-pressure trajectory;
- strategic-goal progress;
- whether policy remains appropriate.

---

## 28. Dynamic materiality interface

O4 does not own O28's final materiality formula but must supply relevant dimensions:

- effect on protected liquidity;
- effect on allocatable capital;
- creation/reduction of recurring commitments;
- debt burden impact;
- goal displacement;
- reversibility;
- unusualness versus historical allocation behavior;
- regime conflict;
- concentration of capital into one use;
- opportunity cost.

A materially adverse allocation proposal may hand off to O19 Adversarial Decision Protection.

---

## 29. Forecast-accountability interface

Every material allocation proposal that includes future claims should preserve:

- forecast version;
- assumptions;
- horizon;
- expected impact references;
- confidence;
- later actual outcome references;
- forecast error;
- whether the allocation improved the targeted metric;
- whether policy should be reconsidered.

**[FACT]** A later outcome must not rewrite the original forecast. The system retains both.

---

## 30. Outcome attribution

O4 distinguishes:

- **realized effect:** supported by observed reconciled outcomes;
- **avoided committed cost:** supported by a recorded plan/commitment that was not incurred;
- **forecast benefit:** expected but not yet realized;
- **counterfactual estimate:** modeled difference against an alternate path.

The agent must not report a modeled benefit as realized financial gain.

---

## 31. Failure behavior

### 31.1 Stale account state

Return limited allocation confidence; do not maximize a plan over uncertain current cash.

### 31.2 Unreconciled material transaction

Hold affected allocation dimensions open or conditional.

### 31.3 Missing obligation

Escalate to O2 protection and block any recommendation that could be invalidated materially by the missing item.

### 31.4 Forecast disagreement

Preserve scenario differences; identify dominant assumption; avoid invented precision.

### 31.5 Currency uncertainty

Keep currencies explicit and do not silently convert without approved FX provenance.

### 31.6 Overspend

Do not rewrite history. Offer prospective reallocation.

### 31.7 Goal contradiction

Surface the conflicting priorities and request owner decision where policy cannot resolve them.

### 31.8 Engine unavailable

Return `INSUFFICIENT_DATA` or equivalent limited state. Do not substitute LLM arithmetic.

### 31.9 Policy conflict

Apply precedence and record the conflict. Do not silently merge incompatible rules.

### 31.10 Alert/interaction overload

Consolidate recommendations into the smallest high-impact action set.

---

## 32. Invariants

O4 must preserve the following invariants:

1. only reconciled present capital may be treated as currently allocatable;
2. future income remains forecast-only until received;
3. mandatory obligations and approved protected reserves cannot be silently consumed;
4. no LLM-generated authoritative money values;
5. no silent reallocation of restricted funds;
6. no historical rewriting to hide overspending;
7. no debt-paydown recommendation that bypasses liquidity protection;
8. no investment execution;
9. no automatic change to owner priorities from learned patterns;
10. no false precision when differences are immaterial;
11. no claim of realized gain from an unrealized forecast;
12. all material allocation changes preserve provenance and version history;
13. user decisions remain human-owned;
14. all currencies remain explicit;
15. cross-domain signals remain bounded and provenance-rich.

---

## 33. Required deterministic/statistical interfaces

O4 requires or anticipates interfaces to:

- allocatable-capital engine;
- protected-floor engine;
- safe-to-spend engine;
- obligation schedule engine;
- debt effective-cost engine;
- debt cash-flow relief engine;
- category availability engine;
- rollover engine;
- sinking-fund engine;
- forecast/scenario engine;
- opportunity-cost comparison engine;
- regime classifier/policy engine;
- goal progress engine;
- materiality engine;
- forecast-calibration engine.

**[MISSING]** Exact runtime function names, schemas, and locations must be verified in the repository before implementation. This document does not invent commands or runtime paths.

---

## 34. Data requirements

Minimum inputs include, when relevant:

- canonical reconciled account state;
- current balance quality/freshness;
- obligations and debt schedules;
- current category allocations;
- historical category actuals;
- protected-floor/reserve references;
- known planned commitments;
- active sinking funds;
- owner goals and priority metadata;
- current regime reference;
- forecast scenarios;
- decision constraints;
- current policy version;
- currency metadata;
- relevant external/cross-domain signal references where governed.

Missing material inputs must remain explicit.

---

## 35. Historical analysis requirements

**[AGREED]** Where data exists, O4 should support trailing analysis over:

- days;
- weeks;
- months;
- quarters;
- years.

Historical analysis may inform:

- baseline essential spend;
- discretionary variability;
- category drift;
- recurring commitments;
- seasonal/irregular expense patterns;
- income-cycle behavior;
- historical reallocation frequency;
- debt-pressure trend;
- goal-funding consistency;
- forecast error;
- behavioral realism of proposed changes.

Historical data may inform future policy but must not silently overwrite explicit owner priorities.

---

## 36. Capital-allocation learning loop

O4 should eventually support:

`proposal → owner decision → actual allocation → actual spending/outcome → forecast error → trajectory effect → lesson → policy proposal`

Learning may propose changes to:

- category targets;
- expected ranges;
- contingency needs;
- debt-allocation strategy;
- lifestyle baseline assumptions;
- sinking-fund contribution timing;
- goal contribution cadence;
- regime-specific allocation preferences.

**[FACT]** Learned patterns do not automatically change policy. Material policy changes require governed approval and change-control records.

---

## 37. Capital efficiency without deprivation

**[AGREED]** The system should seek to improve financial efficiency without assuming maximum spend reduction is always desirable.

Examples of valid efficiency improvements may include:

- removing duplicated/unused recurring costs;
- timing payments more intelligently where safe;
- reducing avoidable fees/penalties;
- replacing high-friction debt structures where approved analysis supports it;
- using sinking funds to avoid future shocks;
- smoothing irregular costs;
- protecting sufficient unassigned optionality;
- directing more capital toward capabilities/income expansion when expense reduction alone cannot achieve strategic goals.

This objective is trajectory improvement, not austerity for its own sake.

---

## 38. Income-expansion interface

**[AGREED]** If expense optimization is insufficient to reach strategic goals, Financial NIZAM should surface income expansion as a strategic need.

O4 can identify the capital-allocation consequence of that finding, such as preserving funds for capability-building or opportunity pursuit, but O18 Income Resilience & Expansion owns the deeper income-growth strategy.

O4 must not fabricate expected income returns from capability-building investments. Any return expectation requires an evidence-backed model or remains qualitative/uncertain.

---

## 39. Drive and persistence interface

Under the currently agreed governance direction:

- the VPS/local runtime remains the active governed processing layer;
- Google Drive is the durable evidence/recovery mirror for approved artifacts;
- HIMAYAH v2 is planned to make `trusted_private` the normal readable class for approved personal/financial artifacts within the trusted NIZAM boundary;
- secrets, passwords, tokens, API keys, private keys, `.env`, and credential material remain prohibited from ordinary Drive persistence;
- allocation proposals, approved allocation states, monthly closes, forecast records, and audit artifacts should be mirrored when policy permits;
- a Drive write is not considered landed until the destination is read back and the receipt confirms success.

**[MISSING]** Exact runtime retention/offload thresholds remain future implementation work and must be derived from verified VPS capacity and storage-growth evidence.

---

## 40. Privacy and minimization

**[AGREED]** The intended HIMAYAH v2 philosophy is readable-by-default for ordinary approved personal and financial records inside the Trusted NIZAM Boundary, with hard-secret material separated.

O4 should store only context relevant to capital allocation. Cross-pillar retrieval should be task-relevant rather than indiscriminate.

Sensitive records used in an allocation decision must retain provenance so the owner can inspect why they influenced the recommendation.

---

## 41. Tests — focused functional suite

The implementation should eventually prove at least the following:

### T-O4-001 Protected floor blocks discretionary allocation

Given reconciled capital and protected reservations, allocatable capital excludes protected funds.

### T-O4-002 Future income excluded from current allocation

Expected salary can appear in forecast allocation but not current category availability.

### T-O4-003 Debt minimum protected

Required minimum debt service remains reserved before discretionary deployment.

### T-O4-004 Incremental debt payoff cannot breach liquidity protection

The system rejects or conditions accelerated payoff when it would violate protected liquidity.

### T-O4-005 Sinking fund is not expense

Funding a sinking category does not create transaction expense.

### T-O4-006 Overspending remains historical fact

Reallocation occurs prospectively; past actuals remain unchanged.

### T-O4-007 Rollover obeys category policy

Rollover behavior differs according to category configuration and preserves history.

### T-O4-008 Survival regime biases resilience

When the verified regime is Survival, policy does not allocate true surplus as if the system were in Growth.

### T-O4-009 Growth regime permits strategic deployment

When protection is satisfied and Growth is verified, eligible surplus can move toward approved goals/investment capacity according to policy.

### T-O4-010 Near-tie avoids false precision

Materially indistinguishable alternatives produce tradeoff output rather than fabricated certainty.

### T-O4-011 Restricted allocation cannot silently move

A protected/earmarked category requires explicit governed approval for reallocation.

### T-O4-012 Surprise expense forces protection reassessment

New material expense routes to O2 before O4 reallocation.

### T-O4-013 Windfall reconciles before allocation

Unexpected income is not allocated before O1 recognizes it.

### T-O4-014 Reimbursement remains contingent

Expected reimbursement does not inflate current allocatable capital.

### T-O4-015 Currency explicitness

No cross-currency allocation occurs without conversion provenance from the owning engine.

### T-O4-016 Computation proof required

An authoritative allocation recommendation without required engine references fails validation.

### T-O4-017 Human approval preserved

The agent cannot mark the owner decision or execute a capital move.

### T-O4-018 Historical allocations immutable

A policy/target change cannot rewrite prior allocation states.

### T-O4-019 Counterfactual benefit labeled correctly

A modeled avoided cost or forecast benefit is not reported as realized gain.

### T-O4-020 Engine outage fails closed

If the allocatable-capital engine is unavailable, the LLM cannot substitute arithmetic.

---

## 42. Scenario tests

### S-O4-A Income receipt allocation

Input: reconciled income receipt, current obligations, protected floor, debt, sinking funds, goals, and current regime.

Expected: allocation proposal obeys protection ordering, exposes tradeoffs, preserves unassigned optionality if policy supports it, and waits for owner approval where required.

### S-O4-B Travel versus debt reduction

Input: planned travel sinking-fund need and optional incremental debt payoff.

Expected: compare timing, resilience, goal priority, debt effect, and reversibility without assuming either is morally superior.

### S-O4-C High-cost debt versus emergency reserve

Expected: protect contractual minimums and floor, then compare incremental debt reduction against reserve resilience using governed engine outputs.

### S-O4-D Surprise expense after allocation

Expected: O2 reassesses protection; O4 produces prospective reallocation; historical plan remains visible.

### S-O4-E Credit timing strategy

Expected: productive timing is allowed only when settlement remains protected and the engine shows no hidden dependency; otherwise flag structural risk.

### S-O4-F Forecast salary delay

Expected: current allocation remains based on received capital; scenario shows delayed-income downside separately.

### S-O4-G Owner changes strategic priority

Expected: future allocation proposal changes; historical states do not.

### S-O4-H Large windfall

Expected: reconcile first, then allocate under current regime rather than defaulting to discretionary spend.

---

## 43. Failure-injection tests

Implementation verification should deliberately test:

1. stale material account;
2. missing debt obligation;
3. corrupted allocation version;
4. duplicate income event;
5. forecast-only income mislabeled as actual;
6. unavailable allocatable-capital engine;
7. missing protected-floor reference;
8. missing currency metadata;
9. unauthorized attempt to reallocate a restricted category;
10. unauthorized attempt to execute payment or investment;
11. audit log write failure;
12. Drive mirror failure after local persistence.

The system should fail safely, preserve prior canonical state, and surface an actionable exception.

---

## 44. Migration plan

### Step 1 — inspect existing runtime and contracts

Verify the owning budget/allocation, liquidity, debt, forecast, ledger, privacy, and orchestration implementations before changing code.

### Step 2 — map existing category and allocation objects

Identify canonical schemas, writers, migration needs, and any competing truth stores.

### Step 3 — implement typed interfaces

Introduce or align allocatable-capital, allocation-proposal, allocation-event, and computation-receipt contracts without inventing parallel ledger authority.

### Step 4 — implement regime/protected-floor placeholders only as explicit interfaces

Do not invent O7/O15 logic prematurely. Consume existing verified outputs if they exist; otherwise mark dependency incomplete.

### Step 5 — implement allocation policy engine

Use pure deterministic functions where monetary allocation is calculated. Inject state/policy inputs and produce auditable outputs.

### Step 6 — integrate orchestration and owner-facing synthesis

The LLM explains the engine output but does not become the calculator.

### Step 7 — focused tests

Run O4 unit/contract/scenario tests.

### Step 8 — repository gate

Run the existing repository verification gate without weakening checks.

### Step 9 — tamper proof

Deliberately alter a protected invariant in a test fixture and prove validation fails.

### Step 10 — persistence receipt

Mirror permitted artifacts according to implemented HIMAYAH policy, verify read-back, and record receipt.

---

## 45. Blast radius

Likely affected areas, subject to repository inspection:

- budget/allocation policy contracts;
- budget/category schemas;
- liquidity engine interfaces;
- debt/obligation engine interfaces;
- forecast/scenario interfaces;
- decision-engine interfaces;
- allocation and event ledgers;
- orchestration/router logic;
- owner-facing brief/UI surfaces;
- monthly close;
- validation tests;
- change/decision register;
- Drive mirror/recovery artifacts.

**[MISSING]** Exact files must be identified during repository research. This design does not invent file paths beyond the documented source package.

---

## 46. Acceptance criteria

O4 is implementation-complete only when all of the following are evidenced:

1. allocation consumes O1 reconciled state;
2. O2 protection requirements are evaluated first;
3. current allocatable capital excludes protected capital and future income;
4. regime-sensitive allocation policy is versioned and auditable;
5. debt allocation cannot silently breach liquidity protection;
6. category rollover and overspend preserve historical truth;
7. sinking funds remain reserved availability rather than false expense;
8. opportunity cost is explicit for material reallocations;
9. close decisions avoid false precision;
10. computation receipts prove required engines actually ran;
11. no LLM-created authoritative money values appear;
12. no autonomous payment, transfer, borrowing, or investment occurs;
13. owner priorities remain human-controlled;
14. material allocation changes retain provenance and prior versions;
15. forecast allocation and actual allocation are distinct;
16. later actual outcomes can be compared against the original allocation forecast;
17. failures return limited/unknown states rather than invented answers;
18. permitted durable artifacts are mirrored and read back under the implemented privacy policy;
19. focused tests and repository gate pass;
20. tamper testing proves at least one protection invariant fails when intentionally broken.

---

## 47. Definition of done

O4 is **DESIGNED** when this contract is owner-approved and linked into the objective register.

O4 is **IMPLEMENTED** only when repository code, schemas, tests, orchestration, and ledgers embody the contract.

O4 is **VERIFIED** only when focused tests, the repository gate, deliberate tamper testing, and persistence/read-back receipts have been observed directly.

Until then, no document or conversational response may claim runtime Capital Optimization is operational merely because this design exists.

---

## 48. Dependencies and handoffs

### Upstream

- **O1 Financial Truth:** reconciled canonical state and provenance.
- **O2 Financial Protection:** obligations, exceptions, and protected-state requirements.
- **O3 Decision Intelligence:** material option comparison and recommendation packet.

### Downstream / future objective handoffs

- **O5 Wealth Growth:** converts stable allocatable capacity into long-term wealth trajectory.
- **O7 Regime Management:** authoritative regime classification.
- **O8 Longitudinal Intelligence:** richer historical baselines.
- **O12 Forecast Accountability:** allocation forecast-versus-actual calibration.
- **O13 Income-Cycle Orchestration:** pre-income and receipt workflows.
- **O14 Credit & Liquidity Optimization:** deeper credit timing logic.
- **O15 Dynamic Resilience:** authoritative protected-floor and emergency-reserve model.
- **O16/O17 External Intelligence:** economic and weak-signal inputs.
- **O18 Income Resilience & Expansion:** strategic income-side response.
- **O19 Adversarial Decision Protection:** high-friction challenge for harmful allocation choices.
- **O21 Decision Outcome Attribution:** realized versus counterfactual outcome tracking.
- **O28 Dynamic Materiality:** severity calculation.
- **O29 Computation Proof:** shared proof contract.
- **O31/O32 Drive Persistence:** storage-aware durable mirroring.
- **O33–O43 HIMAYAH / Trusted NIZAM Boundary:** readable trusted-private persistence and cross-pillar analysis governance.

---

## 49. Source basis

This O4 design is grounded in:

- Financial NIZAM Constitution and Tenets;
- Financial NIZAM Budgeting System;
- Financial NIZAM Obligations, Debt and Installments;
- Financial NIZAM Cashflow and Liquidity Engine;
- Financial NIZAM Forecasting and Scenario Engine;
- Financial NIZAM Decision Engine;
- Financial NIZAM Agent Roles and Orchestration;
- Financial NIZAM Ledger and Event Schemas;
- Financial NIZAM Privacy, Security and Approval Policy;
- Financial NIZAM UI and User Journeys;
- Financial NIZAM Validation Tests;
- the owner-approved Financial NIZAM vision-discovery decisions in the current session.

**[FACT]** These architecture-package sources are canonical candidates and remain subordinate to PFOS v1.3 FINAL and verified runtime evidence.

**[MISSING]** Runtime implementation status has not been verified as part of this objective-document build.

---

## 50. Owner-facing north-star statement

**[AGREED]** O4 should make Financial NIZAM behave like a CFO that knows **what must be protected, what is truly available, and where the next unit of capital creates the most useful improvement without making the owner's life unrealistically austere or the financial system more fragile.**
