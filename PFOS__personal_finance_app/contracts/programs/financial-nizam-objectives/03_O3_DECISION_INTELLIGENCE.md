# Financial NIZAM Objective O3 — Decision Intelligence

**Status:** PROPOSED OVERHAUL DESIGN — owner-approved objective, implementation not yet verified  
**Objective ID:** O3  
**Objective name:** Decision Intelligence  
**Program:** Financial NIZAM / PFOS / MAL implementation namespace  
**Owner:** Seif ElSherbiny  
**Version:** 0.1.0-design  
**Sensitivity:** review_before_commit  
**Owning phase:** Phase 3 — Decision modeling, scenario comparison, and owner recommendation  
**Precedence:** safety/platform policy → newest explicit owner direction → PFOS v1.3 FINAL → non-conflicting subordinate contract → verified runtime evidence → historical/draft material

---

## 1. Objective

**[FACT]** Financial NIZAM must convert a contemplated financial action into an evidence-backed decision packet that compares credible options across immediate liquidity, obligations, debt/credit effects, forecast consequences, opportunity cost, reversibility, uncertainty, strategic goals, and the current financial regime.

**[AGREED]** The owner-facing question is not merely **“Can I afford this?”** It is: **“What happens to my financial system if I do this, compared with the credible alternatives, across the short and long term?”**

**[AGREED]** O3 is the core analytical decision-partner layer of the Personal CFO / Wealth Operating System. It should help with contemplated purchases, travel, subscriptions, financing plans, debt decisions, savings allocations, investment-related planning, recurring commitments, asset acquisition, and competing uses of capital.

**[FACT]** O3 does not create authoritative monetary values conversationally. Monetary quantities, ratios, effective-cost results, safe-to-spend values, debt metrics, forecast ranges, probability/calibration statistics, and percentage impacts must come from deterministic or explicitly governed statistical engines. The conversational layer explains, challenges, and synthesizes those outputs.

**[FACT]** O3 consumes O1 reconciled truth and O2 protection state. It must fail closed or narrow its conclusion when those prerequisites are stale, unresolved, or materially incomplete.

---

## 2. Governing source decisions

### 2.1 Existing canonical-candidate rules

**[FACT]** The Financial NIZAM constitution and Decision Engine already require:

- evidence before interpretation;
- reconciliation before optimization;
- protection of imminent obligations and required liquidity before discretionary optimization;
- deterministic monetary truth;
- explicit uncertainty;
- forecasts as scenarios rather than guarantees;
- human control over consequential actions;
- reversible choices to be preferred where practical;
- few high-leverage recommendations rather than overwhelming action lists;
- decision usefulness before dashboard complexity.

**[FACT]** The existing Decision Engine requires the following dimensions for a material decision: urgency, liquidity impact, deterministic effective-cost result, penalty/default risk, reversibility, cash-flow timing, goal alignment, option value, uncertainty, complexity/stress cost, and explicit user constraints.

**[FACT]** The existing material-decision packet already requires: decision question; FACTS; MISSING/UNKNOWN; options; hard constraints; deterministic quantitative comparison reference; base recommendation; strongest counterargument; scenario sensitivity; confidence; evidence that could change the result; and approval class.

**[FACT]** No recommendation for borrowing, refinancing, early payoff, liquidation, or major discretionary spending may bypass liquidity and obligation modeling. Interest rate alone must not define debt priority.

**[FACT]** Close numerical calls must not be presented with false precision. The term `optimal` is prohibited unless the objective and constraints are explicit.

### 2.2 New owner directions incorporated into this overhaul

**[AGREED]** Financial NIZAM is expected to act simultaneously as accountant, controller, tactical CFO, financial decision partner, and long-term wealth strategist while preserving one canonical truth layer.

**[AGREED]** Decision analysis must be tactical and strategic. It should show the expected consequence for the immediate period, the next several days, the next income cycle, medium-term planning, and longer-term goals when evidence supports those horizons.

**[AGREED]** Statistical and probabilistic analysis may be used where governed and calibrated, especially for uncertain future scenarios, but uncertainty must remain explicit and predictions must later be compared against actual outcomes.

**[AGREED]** Recommendations should reason with the owner using strong proof and evidence, including historical personal financial patterns, deterministic scenario outputs, counterfactuals, credible alternatives, approved external economic evidence, and later objectives for cross-domain or weak-signal intelligence where those are relevant.

**[AGREED]** Materiality is multi-dimensional. A decision can be material because of liquidity impact, debt burden, recurring commitment, reversibility, regime conflict, unusualness relative to historical behavior, strategic-goal impact, or institutional-credit consequences even when nominal purchase value alone appears modest.

**[AGREED]** The challenge layer may become assertive and high-friction for materially damaging decisions, but O3 itself must hand off to the dedicated challenge/override objectives rather than silently converting recommendation into authority.

**[AGREED]** If the owner proceeds against the recommendation, Financial NIZAM must continue helping and later evaluate whether the override was better calibrated than the system's original position.

---

## 3. Scope

O3 governs:

1. decision-intent capture;
2. material-decision packet construction;
3. decision prerequisite checks;
4. option and alternative generation;
5. deterministic quantitative comparison references;
6. probabilistic/statistical scenario references where governed;
7. cash-flow and liquidity impact comparison;
8. obligation and protected-floor interaction;
9. debt, credit, installment, and recurring-commitment consequences;
10. reversibility and option-value assessment;
11. opportunity-cost analysis;
12. strategic-goal alignment;
13. current financial-regime fit;
14. multi-horizon impact synthesis;
15. uncertainty, missing-data, and sensitivity exposure;
16. base recommendation and strongest counterargument;
17. recommendation labels and decision confidence;
18. materiality/escalation handoff;
19. user decision capture without impersonating the owner;
20. forecast/decision outcome linkage for later learning.

O3 does **not** govern:

- canonical transaction ingestion or account reconciliation;
- the final protected-liquidity-floor formula;
- the full dynamic materiality formula;
- autonomous payments, transfers, borrowing, refinancing, purchases, cancellation, or investment execution;
- final high-friction challenge sequencing;
- cooling-period orchestration;
- override governance;
- the full economic/news/social-signal intelligence pipeline;
- the full behavioral/cross-domain correlation engine;
- long-term portfolio or wealth-allocation policy by itself.

Those capabilities are owned by later objectives and are consumed by O3 through explicit interfaces.

---

## 4. Decision doctrine

**[AGREED]** O3 follows this order for a material decision when the required evidence is available:

1. identify the exact decision question;
2. identify the decision deadline and urgency;
3. identify whether the decision is reversible, semi-reversible, or hard to reverse;
4. verify O1 canonical-state version, freshness, and reconciliation status;
5. verify O2 protection state, obligations, current regime, and material exceptions;
6. identify explicit owner constraints and strategic goals relevant to the decision;
7. build credible options, including delay/reduction/no-action where relevant;
8. request deterministic comparison outputs;
9. request governed forecast/scenario outputs;
10. expose uncertainty and dominant assumptions;
11. compare opportunity cost and option value;
12. synthesize multi-horizon effects;
13. produce a direct recommendation label;
14. state the strongest counterargument against the recommendation;
15. identify evidence that would change the recommendation;
16. hand off to materiality/challenge/approval policy if required;
17. record the owner's actual decision only after the owner decides;
18. link the decision to later observed outcomes and forecast-error review.

**[FACT]** If O1 or O2 is materially unresolved, O3 must not disguise that limitation as confidence. The result becomes limited, conditional, or `INSUFFICIENT_DATA` according to policy.

---

## 5. Decision classes

### 5.1 Discretionary purchase

Examples include consumer goods, entertainment, dining, discretionary services, electronics, and other optional spending.

Required emphasis:

- immediate liquidity effect;
- protected-floor interaction;
- current regime;
- unusualness versus history;
- reversibility/resale/returnability where relevant;
- opportunity cost;
- whether delay materially improves the decision.

### 5.2 Travel and event commitment

Travel is modeled as a bundle of financial events rather than a single booking price.

Required emphasis:

- deposits and non-refundable components;
- transport/lodging/visa/insurance/local spending where evidenced;
- FX exposure where relevant;
- timing relative to income and obligations;
- downside reserve;
- opportunity cost;
- cancellation/change flexibility;
- historical travel-spend variance if available.

### 5.3 Subscription or recurring commitment

A small recurring commitment may be material because it creates structural expenditure.

Required emphasis:

- recurring cadence;
- minimum commitment period;
- cancellation friction;
- total committed future cash-flow reference;
- budget/category impact;
- historical utilization where available;
- strategic usefulness.

### 5.4 Financing, installment, borrowing, or refinancing

Required emphasis:

- deterministic effective-cost engine reference;
- minimum payments and due dates;
- liquidity effect;
- debt burden/ratios where governed;
- fees/penalties;
- term and optionality;
- current financial regime;
- alternative financing/no-financing options;
- institutional-credit implications where reliable data exists.

**[FACT]** O3 may recommend but cannot execute borrowing or refinancing.

### 5.5 Debt payoff or acceleration

Required emphasis:

- delinquency/default protection first;
- protected liquidity;
- deterministic incremental payoff comparison;
- future cash-flow relief;
- emergency-reserve consequence;
- alternative uses of capital;
- reversibility loss when cash is converted into debt reduction.

### 5.6 Saving, sinking fund, or reserve allocation

Required emphasis:

- current liquidity floor;
- current regime;
- future obligation timing;
- target horizon;
- opportunity cost;
- withdrawal/reallocation flexibility.

### 5.7 Investment-related planning

Required emphasis:

- source of investable capital;
- protection of obligations and reserve before allocation;
- horizon;
- liquidity/reversibility;
- risk and loss capacity;
- external research provenance where market assumptions are required;
- explicit separation between personal financial facts and market assumptions.

**[FACT]** Investment execution remains human-controlled.

### 5.8 Asset acquisition

Where the owner asks whether an asset is “worth it,” O3 must separate:

- consumption utility;
- expected retained/resale value;
- maintenance/holding cost;
- liquidity/reversibility;
- uncertainty of future value;
- strategic usefulness;
- opportunity cost.

External assumptions about market value or depreciation require source-backed research and must not be presented as personal financial fact.

---

## 6. Decision packet schema

Every material O3 analysis should resolve into a versioned decision packet with at least:

```yaml
decision_packet:
  decision_id: null
  created_at: null
  decision_question: null
  decision_class: null
  decision_deadline: null
  urgency: null
  canonical_state_version: null
  protection_state_ref: null
  regime_ref: null
  materiality_ref: null
  facts: []
  missing_unknown: []
  user_constraints: []
  strategic_goal_refs: []
  options: []
  hard_constraints: []
  deterministic_comparison_refs: []
  forecast_scenario_refs: []
  probability_calibration_refs: []
  opportunity_cost_refs: []
  counterfactual_refs: []
  sensitivity_refs: []
  strongest_counterargument: null
  base_recommendation: null
  recommendation_label: null
  confidence: null
  evidence_that_changes_result: []
  approval_class: null
  challenge_handoff_required: null
  user_decision: null
  outcome_review_ref: null
  audit_refs: []
```

**[FACT]** `user_decision` remains `null` until the owner explicitly decides. The agent must never infer `Decision Made?` from continued conversation, silence, or execution planning.

---

## 7. Prerequisite gates

O3 must check the following before issuing a high-confidence material recommendation:

### 7.1 Truth gate

Required:

- canonical state ID/version;
- account freshness state;
- reconciliation status;
- unresolved high-impact exceptions;
- currency explicitness.

### 7.2 Protection gate

Required:

- upcoming obligation state;
- protected-floor/reserve references where available;
- critical O2 alerts;
- delayed/missing income risk if relevant;
- current protection regime.

### 7.3 Forecast gate

Required when future consequences are material:

- scenario version;
- horizon;
- assumptions;
- source refs;
- uncertainty representation;
- confidence/calibration state.

### 7.4 Research gate

External/provider/regulatory/market claims require fresh evidence from appropriate sources. O3 must distinguish:

- personal verified fact;
- deterministic engine result;
- external authoritative fact;
- professional analysis;
- market-implied expectation;
- social/weak signal;
- model inference.

### 7.5 Human-authority gate

Consequential execution remains human-controlled. O3 may recommend a choice and prepare an action plan but cannot perform the financial action unless a later governing policy explicitly authorizes a narrow reversible operation and the current platform permits it.

---

## 8. Option generation

**[AGREED]** O3 should not force every problem into `DO` versus `DON'T`.

Credible options may include:

- proceed now;
- proceed at reduced scope;
- delay to a specified condition/time window;
- choose a lower-cost alternative;
- choose a more reversible alternative;
- fund from a different permissible allocation;
- restructure timing;
- wait for new evidence;
- do nothing;
- cancel an existing plan if reversible and owner-approved.

**[FACT]** The set of options must respect hard constraints. An option that violates required obligations or assumes unavailable cash cannot be presented as a valid baseline merely because it is desirable.

**[AGREED]** Alternatives should be realistic for the owner. The system should prefer marginal improvements and feasible substitutions over unrealistic recommendations that assume abrupt lifestyle contraction without evidence the plan is sustainable.

---

## 9. Deterministic quantitative comparison

**[FACT]** O3 must reference, not conversationally recreate, deterministic financial calculations.

Depending on the decision class, referenced outputs may include:

- liquidity before/after decision;
- protected-floor headroom;
- safe-to-spend impact;
- next-obligation coverage;
- debt-service impact;
- effective financing cost;
- recurring-commitment burden;
- cash-flow timing;
- debt-ratio or institutional-credit metric where governed;
- opportunity-cost engine result;
- forecasted lowest-liquidity point;
- scenario closing state.

Every monetary result must retain explicit currency and integer-milliunit source representation in the authoritative engine layer.

**[FACT]** If a deterministic result is unavailable, the LLM must not substitute mental arithmetic. The packet should mark the missing engine result and narrow the recommendation.

---

## 10. Probabilistic and statistical decision support

**[AGREED]** O3 may consume statistical/probabilistic engines to reason about uncertain future outcomes where sufficient history or external evidence exists.

Permitted outputs may include:

- estimated distribution/range of variable spending;
- probability of breaching an approved liquidity threshold;
- forecast uncertainty bands;
- likelihood ranges for timing-sensitive events where a governed model exists;
- scenario-weighted outcome comparisons;
- historical conditional frequencies;
- calibration/error metrics from prior predictions.

**[FACT]** Probabilistic outputs must include model/version, training/reference window, sample sufficiency where relevant, assumptions, calibration state, and uncertainty.

**[FACT]** Probability does not become certainty. Social sentiment, prediction markets, market pricing, and historical correlations must never be presented as guaranteed outcomes.

**[AGREED]** Later actual outcomes must be compared against predictions so the system can measure calibration rather than merely accumulate confident-looking forecasts.

---

## 11. Scenario model

At minimum, a material decision that materially affects future cash should support:

- **BASE:** current best-supported path;
- **DOWNSIDE:** credible adverse conditions;
- **UPSIDE:** credible favorable conditions;
- **USER_DEFINED:** explicit event or assumption requested by the owner;
- **NO_ACTION/STATUS_QUO:** path if the contemplated decision is not taken, when meaningful.

Each scenario must preserve:

- snapshot/state version;
- horizon;
- assumptions;
- source refs;
- engine/calculation version;
- uncertainty representation;
- generated time;
- confidence/calibration state.

**[FACT]** Known dated events outrank averages. Expected future income must not be treated as current liquidity.

---

## 12. Multi-horizon impact analysis

**[AGREED]** O3 should expose impact across the horizons relevant to the decision without manufacturing unsupported long-range precision.

The default decision view should consider, where supported:

1. immediate/today;
2. tomorrow/next settlement events;
3. next seven days;
4. until next expected income cycle;
5. planning horizon such as thirty or ninety days;
6. strategic horizon where evidence supports it.

For each horizon, O3 should answer:

- what changes;
- what remains protected;
- what becomes tighter or more flexible;
- which obligation/goal is affected;
- which assumption dominates;
- whether uncertainty materially changes the conclusion.

---

## 13. Current financial-regime interface

**[AGREED]** O3 must consume the current regime classification rather than using the same decision philosophy in every financial state.

Expected regime family:

- Survival;
- Stabilization;
- Growth;
- Expansion.

**[AGREED]** Balanced optimization is the long-term philosophy, but a temporary Survival posture may make liquidity preservation more valuable than otherwise attractive growth or lifestyle actions.

O3 should be able to explain:

> “The long-term strategy has not changed; the current tactical regime has changed the recommendation.”

O3 does not own the final regime-classification engine, but it must record the regime reference and sensitivity of the recommendation to a regime change.

---

## 14. Protected-floor and emergency-reserve interface

**[AGREED]** A contemplated decision must be evaluated against the current dynamic protected-floor and emergency-reserve outputs once those engines exist.

O3 must distinguish:

- expected operating needs;
- protected obligations;
- protected operating floor;
- emergency reserve;
- discretionary allocatable capacity.

**[FACT]** A decision that breaches the protected floor or relies on unreceived income requires explicit escalation and cannot be described as comfortably affordable.

---

## 15. Debt and credit interface

**[AGREED]** Credit is not treated only as “bad debt.” O3 should consider credit timing, statement cycles, payment dates, available limits, installment structures, fees, and future settlement obligations where verified.

**[AGREED]** Productive timing and dependency must remain distinguishable:

- **productive timing:** credit preserves liquidity while future settlement is already protected;
- **dependency:** new credit is required to service or conceal the prior obligation path.

O3 must not recommend a credit-loop maneuver without explicit modeling of future settlement obligations and O2 protection state.

---

## 16. Opportunity cost and option value

**[AGREED]** A decision should be compared with the credible alternative uses of the same capital or commitment capacity.

Opportunity-cost analysis may consider:

- protected liquidity preserved;
- debt reduction alternative;
- reserve building;
- near-term planned goal;
- income-generation investment in capability where relevant;
- strategic savings/investment path;
- retaining cash optionality.

**[FACT]** O3 must not claim an alternative is superior merely because it has a higher hypothetical return. Risk, liquidity, reversibility, timing, current regime, and owner constraints matter.

**[AGREED]** Option value should be explicit when waiting preserves meaningful future choices.

---

## 17. Reversibility

Every material option should be classified as:

- `REVERSIBLE`;
- `SEMI_REVERSIBLE`;
- `HARD_TO_REVERSE`.

The classification should consider:

- cancellation/return rights;
- contractual commitment;
- transaction fees;
- resale/exit friction;
- debt creation;
- reputational/institutional consequence where relevant;
- time sensitivity.

**[FACT]** More irreversible decisions require stronger evidence and approval discipline.

---

## 18. Strategic-goal alignment

**[AGREED]** O3 must connect decisions to explicit strategic goals rather than assuming that “spend less” is always the objective.

Potential goal references may include:

- resilience/liquidity;
- debt reduction;
- emergency reserve;
- travel or family commitments;
- capital formation;
- savings/investment capacity;
- income expansion;
- major life goals;
- net-worth trajectory.

**[FACT]** Goal priorities must be explicit or governed. O3 must not silently rewrite them because a new decision appears attractive.

---

## 19. Historical behavior interface

**[AGREED]** Where sufficient data exists, O3 should compare the contemplated decision with historical owner behavior.

Potential evidence includes:

- similar prior purchases;
- merchant/category history;
- prior trip-plan actuals versus expected;
- recurring-plan utilization;
- prior financing outcomes;
- past override cases;
- forecast-versus-actual performance;
- later objectives for contextual/cross-domain decision-state evidence.

**[FACT]** Historical association is evidence, not destiny. O3 must not convert past behavior into a deterministic identity label.

---

## 20. External research interface

External research is permitted when the decision depends on facts not contained in canonical personal finance state, such as:

- provider terms;
- regulatory conditions;
- travel costs/requirements;
- product resale/depreciation context;
- market conditions;
- macroeconomic conditions;
- FX/rate context;
- asset-specific risk factors.

Each external claim must record:

- source;
- publication/as-of date;
- source class;
- confidence/reliability;
- whether corroborated;
- whether it is fact, market expectation, professional analysis, social signal, or inference.

**[FACT]** External evidence may change assumptions and scenarios. It does not directly overwrite verified balances, transactions, or obligations.

---

## 21. Recommendation labels

O3 should expose a compact decision label. The initial label set is:

- `YES` — supported under current evidence and constraints;
- `YES_BUT` — acceptable only with stated protections/conditions;
- `DELAY` — timing should change because waiting materially improves the decision or evidence quality;
- `REDUCE` — a smaller scope preserves the main benefit with materially lower downside;
- `NO_RECOMMEND` — current evidence indicates the decision is materially damaging or dominated by credible alternatives;
- `INSUFFICIENT_DATA` — missing/stale/conflicting evidence prevents a responsible recommendation.

**[PROPOSED]** Final naming may be normalized during implementation so it remains compatible with the existing Decision Engine and UI contracts.

Every label must include:

- direct conclusion;
- deterministic status/value references;
- why;
- multi-horizon impact;
- main uncertainty;
- next action;
- optional evidence trail.

---

## 22. Strongest counterargument requirement

**[FACT]** Every material recommendation must include the strongest reasonable argument against itself.

Purpose:

- prevent one-sided confirmation;
- expose fragile assumptions;
- surface close calls;
- prepare the challenge layer;
- make it easier for the owner to disagree intelligently.

The strongest counterargument must be evidence-based and must not be a token disclaimer.

---

## 23. Sensitivity and evidence-that-changes-result

Every material packet should state which assumptions can reverse or materially weaken the recommendation.

Examples of drivers include:

- incoming cash timing;
- obligation amount/date;
- protected-floor level;
- financing terms;
- trip cost range;
- cancellation/refundability;
- exchange-rate assumption;
- resale value;
- regime transition;
- one-off versus recurring status.

Where one or two drivers dominate, the decision packet should link to a sensitivity result produced by the governed engine.

The system should explicitly tell the owner what new evidence would cause it to reconsider.

---

## 24. Materiality and escalation interface

**[AGREED]** O3 consumes, but does not fully define, the dynamic materiality model.

Expected materiality contributors include:

- liquidity impact;
- protected-floor effect;
- debt burden/ratio effect;
- recurring commitment;
- reversibility;
- regime conflict;
- strategic-goal effect;
- unusualness relative to historical behavior;
- institutional-credit implications;
- uncertainty and potential downside.

Materiality output should be referenced as a governed result such as:

- LOW;
- MODERATE;
- HIGH;
- CRITICAL.

**[AGREED]** HIGH/CRITICAL materially adverse recommendations may hand off to the later adversarial challenge objective for stronger friction and evidence escalation.

---

## 25. Challenge and debate handoff

**[AGREED]** Financial NIZAM should be assertive when evidence indicates a materially damaging decision, but the dedicated challenge layer owns the escalation sequence.

O3 must provide that layer with:

- base recommendation;
- strongest evidence class used;
- strongest counterargument;
- missing evidence;
- alternative options;
- counterfactual references;
- expected consequences;
- sensitivity drivers;
- owner-stated reasons for disagreement when available.

The challenge layer may then broaden evidence across personal history, external macro context, approved social/market signals, and other governed sources without forcing O3 to become an unrestricted research agent.

---

## 26. Cooling-period and override handoff

**[AGREED]** A cooling period may be offered for high-impact non-urgent decisions, but only if the owner accepts it.

O3 should be able to produce a reassessment packet containing:

- decision ID;
- current recommendation;
- reason to defer;
- proposed revisit time/condition;
- evidence to refresh before revisit;
- state/context evidence that may be relevant under later governed behavioral objectives.

**[FACT]** The owner retains final override authority. O3 must not convert a recommendation into a financial veto.

After an override, O3 changes posture from **“Should we do this?”** to **“Given that this happened, what is now the best available path?”**

---

## 27. Decision outcome and counterfactual linkage

Every material decision should later be linkable to:

- what was predicted;
- which option was chosen;
- what actually happened;
- forecast error;
- realized financial effects;
- avoided committed cost where demonstrable;
- forecast benefit that remains unrealized;
- counterfactual estimate where modelled;
- whether the system or owner was better calibrated;
- lesson carried forward.

**[FACT]** Realized effects, avoided costs, forecasts, and counterfactual estimates must remain separate. The system must not claim a saving or benefit that has not been established by deterministic evidence.

---

## 28. Agent responsibilities

### 28.1 Finance Orchestrator

Responsible for:

- dependency ordering;
- state-version binding;
- invoking required engines/agents;
- assembling the decision packet;
- enforcing the owner/human-only decision boundary.

Forbidden:

- bypassing O1 reconciliation;
- fabricating missing engine results;
- mutating canonical financial state directly outside authoritative ports.

### 28.2 Decision Agent

Responsible for:

- framing the decision;
- generating credible options;
- requesting comparison outputs;
- synthesizing tradeoffs;
- preparing recommendation and strongest counterargument;
- identifying evidence that changes the result.

Forbidden:

- performing authoritative arithmetic in prose;
- executing the decision;
- marking `user_decision` on the owner's behalf.

### 28.3 Cashflow & Forecast Agent

Responsible for:

- scenario/horizon outputs;
- forecast uncertainty;
- sensitivity;
- forecast-vs-actual linkage.

Forbidden:

- presenting scenarios as guarantees;
- treating expected income as current liquidity.

### 28.4 Obligation/Debt Agent

Responsible for:

- due-state inputs;
- effective-cost references;
- debt/credit consequence analysis;
- recurring burden inputs.

Forbidden:

- optimizing interest rate alone while ignoring liquidity/default risk.

### 28.5 Research Agent

Responsible for:

- fresh provider/regulatory/market evidence where required;
- source class and freshness;
- separating fact from expectation or weak signal.

Forbidden:

- leaking unnecessary private transaction data into external research queries.

### 28.6 Privacy & Approval Gate

Responsible for:

- output classification;
- egress scope;
- owner approval class;
- destination/sensitivity checks.

### 28.7 Audit Agent

Responsible for:

- proving dependency calls occurred;
- proving state version and engine versions used;
- detecting unauthorized mutation;
- preserving decision/audit linkage.

---

## 29. Agent handoff envelope

O3 uses the shared structured envelope:

```yaml
handoff:
  task_id: null
  request: null
  input_artifacts: []
  canonical_state_version: null
  assumptions: []
  unresolved_items: []
  expected_output: null
  write_permissions: []
  approval_required: null
  completion_status: null
  audit_refs: []
```

A material decision packet is invalid if it cannot identify the canonical-state version and calculation/forecast references used for the conclusion.

---

## 30. Conversational contract

**[AGREED]** The owner wants strong evidence and reasoning, not unexplained commands.

The default material-decision response should follow:

1. direct recommendation label;
2. current regime and protection state;
3. what the decision changes;
4. evidence and deterministic result references;
5. immediate and multi-horizon impact;
6. strongest counter-case;
7. uncertainty/sensitivity;
8. better alternative if available;
9. next action;
10. optional deep evidence trail.

**[FACT]** If one missing fact materially changes the conclusion, the system should ask one high-information question rather than generate a long speculative answer.

**[AGREED]** The system may debate strongly under the later challenge objective, but evidence must change and deepen across debate turns rather than simply repeating the same warning more loudly.

---

## 31. Computation-proof requirement

**[AGREED]** Financial NIZAM must prove that the decision analysis actually ran the required engines rather than producing a fast conversational imitation.

Each material recommendation receipt should include:

- decision ID;
- canonical-state version;
- protection-state version/reference;
- engines/agents invoked;
- source artifacts;
- data freshness;
- assumptions;
- missing inputs;
- calculation/model versions;
- scenario IDs;
- materiality reference;
- recommendation label;
- confidence/calibration reference;
- audit IDs;
- approval class.

A missing required computation produces a degraded/conditional recommendation, not fabricated completeness.

---

## 32. Ledger and audit model

O3 should append or update through authoritative ports only.

Required durable event families include:

- `DECISION_OPENED`;
- `DECISION_PACKET_BUILT`;
- `DECISION_OPTION_ADDED`;
- `DECISION_SCENARIOS_REFRESHED`;
- `DECISION_RECOMMENDATION_ISSUED`;
- `DECISION_RECOMMENDATION_CHANGED`;
- `DECISION_CHALLENGE_HANDOFF`;
- `DECISION_COOLING_OFFERED`;
- `DECISION_OVERRIDE_RECORDED`;
- `DECISION_CLOSED`;
- `DECISION_OUTCOME_REVIEWED`.

Every event should preserve:

- actor;
- timestamp;
- entity/decision ID;
- source/evidence refs;
- schema/policy version;
- reason;
- supersession reference where applicable;
- approval reference where applicable;
- result/receipt.

Historical recommendations must not disappear when the recommendation changes. A changed recommendation appends a new event that supersedes the earlier recommendation while retaining the original evidence state.

---

## 33. Failure behavior

### 33.1 Stale or unreconciled truth

Return a limited or `INSUFFICIENT_DATA` recommendation. Identify exactly which source/state must be refreshed.

### 33.2 Missing protected-floor or obligation output

Do not present a high-confidence major discretionary, debt, financing, or liquidation recommendation.

### 33.3 Forecast unavailable

Narrow the horizon, widen uncertainty, or provide qualitative tradeoffs without inventing future numbers.

### 33.4 External research unavailable

Separate personal-state analysis from the unsupported external assumption. Do not fabricate market/provider facts.

### 33.5 Close numerical call

Explain qualitative tradeoffs and dominant uncertainties. Do not claim false superiority.

### 33.6 Conflicting engine outputs

Preserve both outputs, flag the conflict, identify version/input differences, and route to audit/reconciliation. Do not average them.

### 33.7 Challenge-service unavailable

Provide the O3 recommendation and mark escalation as pending rather than pretending the full high-friction process occurred.

### 33.8 Owner overrides

Record the explicit decision and accepted consequence summary, then immediately produce the best post-decision adaptation path permitted by policy.

---

## 34. Acceptance criteria

O3 is contract-complete when all of the following are documented and implementation-ready:

- [ ] every material decision binds to an O1 canonical-state version;
- [ ] every material decision consumes O2 protection state;
- [ ] monetary comparisons are engine-referenced rather than LLM-computed;
- [ ] decision packet exposes FACTS and MISSING/UNKNOWN;
- [ ] option set includes credible alternatives where they exist;
- [ ] future-impact claims carry scenario/horizon/assumption references;
- [ ] probabilistic outputs carry model/calibration metadata;
- [ ] expected income is never treated as current liquidity;
- [ ] protected-floor breaches force escalation/degraded affordability language;
- [ ] debt/credit recommendations model future settlement obligations;
- [ ] opportunity cost and option value are represented;
- [ ] reversibility is explicit;
- [ ] current financial regime is referenced;
- [ ] strategic-goal alignment is explicit;
- [ ] strongest counterargument is required;
- [ ] sensitivity/evidence-that-changes-result is explicit;
- [ ] materiality output is referenced, not guessed;
- [ ] user decision remains unset until explicit human choice;
- [ ] consequential execution remains human-controlled;
- [ ] recommendation revisions preserve prior evidence/history;
- [ ] decision outcome can later be compared against forecast and counterfactual;
- [ ] computation-proof receipt identifies engines and state versions used.

---

## 35. Minimum test matrix

| Test ID | Fixture | Expected result |
|---|---|---|
| O3-T01 | Material purchase with reconciled fresh state | Full decision packet produced |
| O3-T02 | Same purchase with stale material account | `INSUFFICIENT_DATA` or conditional result |
| O3-T03 | Purchase breaches protected floor | Cannot be labeled comfortably affordable; escalation required |
| O3-T04 | Future salary assumed but not received | Not counted as current liquidity |
| O3-T05 | Small recurring commitment with high structural effect | Materiality reference can escalate despite low nominal amount |
| O3-T06 | Large reversible purchase with strong liquidity | Reversibility and regime may reduce severity; amount alone does not decide |
| O3-T07 | Credit-funded purchase with future settlement unmodeled | Recommendation blocked/degraded |
| O3-T08 | Debt payoff improves cost but breaches reserve | Liquidity tradeoff explicitly exposed |
| O3-T09 | Close deterministic comparison | No false precision or `optimal` claim |
| O3-T10 | Market-dependent asset decision | External evidence and assumptions separated from personal facts |
| O3-T11 | Scenario engine unavailable | Horizon narrowed/qualitative tradeoff; no invented numbers |
| O3-T12 | Two engines disagree due to input versions | Conflict preserved and audited, not averaged |
| O3-T13 | Owner asks for decision but key constraint missing | One high-information question requested |
| O3-T14 | Recommendation issued then new statement arrives | Decision packet refreshed with new state version; prior recommendation preserved |
| O3-T15 | Owner explicitly chooses contrary option | `user_decision` recorded only after explicit choice; post-decision support continues |
| O3-T16 | Later actual outcome available | Forecast/outcome linkage created without rewriting original prediction |
| O3-T17 | LLM attempts mental money calculation | Test fails; deterministic engine reference required |
| O3-T18 | Decision Agent bypasses O1 reconciliation | Audit/validation failure |
| O3-T19 | Decision Agent marks `Decision Made?` | Validation failure |
| O3-T20 | No-action option dominates but agent omits it | Decision-option completeness test fails where no-action is credible |

---

## 36. Verification requirements

Implementation verification must follow NIZAM RPV discipline:

1. focused static contract/schema validation;
2. deterministic unit tests for decision-support engines;
3. integration tests with O1/O2/forecast/materiality interfaces;
4. privacy/egress tests for external research;
5. failure injection for stale/missing/conflicting inputs;
6. deliberate tamper proof;
7. UX review for decision clarity and evidence cues;
8. human confirmation test proving the system cannot mark the decision itself;
9. repository gate;
10. read-back of any persisted approved artifact.

**[FACT]** Watching a passing check is not enough. At least one relevant check must be deliberately tampered so it fails for the expected reason.

---

## 37. Migration strategy

### Stage 1 — Decision read model

Build a read-only decision packet over verified O1/O2 state with no write authority except append-only decision/audit events through authoritative ports.

### Stage 2 — Deterministic engine binding

Bind liquidity, obligations, debt/effective cost, safe-to-spend/protected-floor, and opportunity-cost references.

### Stage 3 — Forecast/scenario binding

Add versioned multi-horizon scenarios, uncertainty, sensitivity, and forecast-vs-actual linkage.

### Stage 4 — Materiality/regime binding

Consume the governed dynamic materiality and financial-regime outputs.

### Stage 5 — Challenge/override integration

Connect O3 packets to adversarial challenge, optional cooling, explicit override, and post-override adaptation contracts.

### Stage 6 — Longitudinal learning

Use later decision outcomes, calibration history, merchant/behavioral evidence, and approved contextual signals without altering historical truth.

---

## 38. Required implementation artifacts

The implementation phase should produce, adapt, or formally map equivalent existing files for:

- decision-packet schema;
- decision option schema;
- recommendation label policy;
- decision service/engine adapter;
- deterministic comparison port interfaces;
- scenario/forecast port interfaces;
- materiality/regime port interfaces;
- challenge/override handoff contract;
- decision ledger/event schema extensions;
- computation-proof receipt schema;
- decision outcome review schema;
- synthetic fixtures for every minimum test case;
- static validator;
- integration tests;
- tamper test.

**[FACT]** File names and repository paths are not invented by this design document. The implementation agent must inspect the repository and map these artifacts to the actual owning contracts and existing style before editing.

---

## 39. Dependencies on other objectives

O3 depends directly on:

- **O1 Financial Truth** — canonical evidence/state;
- **O2 Financial Protection** — obligations, protection events, exceptions;
- **O7 Regime Management** — tactical financial regime;
- **O12 Forecast Accountability** — later forecast-vs-actual calibration;
- **O14 Credit & Liquidity Optimization** — deeper credit-cycle logic;
- **O15 Dynamic Resilience** — protected floor/emergency reserve;
- **O19 Adversarial Decision Protection** — high-friction challenge;
- **O20 Persuasion Learning** — communication effectiveness;
- **O21 Decision Outcome Attribution** — realized versus forecast/counterfactual benefit;
- **O22 Closed-Loop Financial Coaching** — recommendation-to-learning loop;
- **O23 Deliberate Cooling & Reassessment** — optional revisit flow;
- **O24 Decision-State Intelligence** — contextual decision-state signals;
- **O25 Explicit Financial Override** — final human override;
- **O26 Override Outcome Learning** — owner-vs-system calibration;
- **O27 Counterfactual Decision Ledger** — alternative-path history;
- **O28 Dynamic Materiality Engine** — severity threshold;
- **O33/O40+ HIMAYAH redesign objectives** — trusted-boundary retrieval and evidence persistence.

O3 must expose interfaces to these objectives without prematurely implementing their internal policy.

---

## 40. Explicit non-goals

O3 must not:

- compute authoritative money values inside the LLM;
- silently assume a balance, salary, debt payment, FX rate, or market return;
- treat forecast income as current cash;
- use interest rate alone to rank debt actions;
- infer that a purchase is “good” because it is affordable;
- infer that a purchase is “bad” because it is discretionary;
- execute financial transactions;
- mark human-only decision fields;
- override O1 reconciliation;
- override O2 protection;
- silently rewrite strategic goals;
- use weak signals as verified facts;
- claim causation from cross-domain correlation;
- present a prediction as a guarantee;
- hide the strongest counterargument;
- erase an earlier recommendation after new evidence arrives.

---

## 41. Definition of done

O3 is **designed** when this contract is approved and mapped to the repository's existing decision/forecast/ledger interfaces.

O3 is **contract-verified** only after the static validator passes and a deliberate tamper fails for the expected reason.

O3 is **runtime-verified** only after actual repository/runtime implementation has been exercised against the minimum test matrix and the observed output is in hand.

O3 is **operationally accepted** only when the owner can ask about a material contemplated decision and receive a decision packet whose conclusion can be traced to reconciled state, protection status, deterministic engines, scenarios, assumptions, alternatives, uncertainty, and audit refs—without the agent fabricating the decision or executing it.

---

## 42. Decision register entries opened by this document

### O3-D01 — Decision Intelligence is comparative, not affordability-only

**Status:** AGREED  
**Decision:** Evaluate contemplated actions against credible alternatives and multi-horizon consequences, not only current affordability.

### O3-D02 — Monetary comparisons are engine-owned

**Status:** AGREED  
**Decision:** The conversational layer may explain numbers but may not be the authoritative calculator.

### O3-D03 — Probabilistic support is allowed but accountable

**Status:** AGREED  
**Decision:** Governed statistical/probabilistic outputs may support decisions but must expose uncertainty and later be compared with actual outcomes.

### O3-D04 — Materiality is multi-dimensional

**Status:** AGREED  
**Decision:** Nominal transaction value alone does not determine whether the high-friction decision process activates.

### O3-D05 — Human decision remains human-only

**Status:** AGREED  
**Decision:** The agent recommends and challenges; the owner decides.

### O3-D06 — Strongest counterargument is mandatory

**Status:** PROPOSED FOR CONTRACT LOCK  
**Decision:** Every material recommendation should present the strongest evidence-backed counter-case against itself.

### O3-D07 — No-action/delay are valid options

**Status:** PROPOSED FOR CONTRACT LOCK  
**Decision:** O3 must include no-action, delay, reduction, or alternative structure when they are credible options.

### O3-D08 — Override does not end support

**Status:** AGREED  
**Decision:** After an explicit override, the system immediately changes to damage-minimization/adaptation and later outcome review.

---

## 43. Open items before implementation

1. map the existing repository's exact decision-engine and schema file paths;
2. confirm current PFOS v1.3 FINAL decision labels and whether `NO_RECOMMEND` needs naming alignment;
3. author O7 before hard-coding financial-regime semantics;
4. author O15 before hard-coding the protected-floor interface;
5. author O28 before hard-coding materiality thresholds;
6. author O19/O23/O25 before enabling high-friction escalation, cooling, or override workflow;
7. define governed statistical-model metadata requirements with O12;
8. confirm which external research sources are allowed and how evidence tiers map into decision confidence;
9. define long-horizon forecast limits after historical data coverage is measured;
10. verify that decision outcome events can be joined to later actuals without mutating the original prediction.

---

## 44. Next objective

**O4 — Capital Optimization** should define how Financial NIZAM allocates resources above the protected resilience floor across debt reduction, present-life requirements, planned goals, savings/investment capacity, optionality, and other competing uses of capital according to marginal benefit and current regime.
