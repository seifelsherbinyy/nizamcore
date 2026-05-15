---
name: mal-decision-score
module: MAL
trigger: "/mal-decision-score <decision_topic>"
target_folder: MAL__financial_engine/scenario_models/
naming_pattern: "decision_score_{YYYY-MM-DD}__{slug}.md"
template: NIZAM__system/templates/decision_score.template.md
gates: [HIMAYAH, SUKOON, THABAT]
privacy: strict_local
factors: [expected_value, effort, risk, cashflow_timing, skill_leverage, ethical_fit, recovery_cost]
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/DECISION_LEDGER.jsonl]
---

## For future Claude

Score a financial / career / investment decision on 7 factors. Output a clear go / no-go / defer recommendation. Cross-check ethical_fit against SOUL.md.

## Procedure

1. Elicit the decision in one sentence.
2. Run `/mal-exchange-rate-check` if any USD/EGP figure involved and last check > 7 days.
3. Score each factor 1–10:
   - **Expected value** (probability × payoff)
   - **Effort** (lower = better; rate inverse)
   - **Risk** (lower = better; rate inverse — i.e., low risk = 10)
   - **Cashflow timing** (sooner = better)
   - **Skill leverage** (uses existing strengths)
   - **Ethical fit** (alignment with SOUL.md non-negotiables; if any violation → score 1 and recommend "DO NOT")
   - **Recovery cost** (lower = better; if red on SUKOON → score 1 and downshift recommendation)
4. Compute weighted total. Default weights: ethical_fit and recovery_cost are veto factors (any < 3 = veto regardless of other scores).
5. Output: go / no-go / defer + reasoning + watch-outs.
6. Append `event_type: "decision_scored"` to DECISION_LEDGER with full reasoning.
7. Append THABAT event. Mirror to `log.md` (sanitized: "decision scored — strict_local").

## Veto rules

- Any ethical_fit < 3 → veto.
- Any recovery_cost < 3 (red) → veto OR mandatory downshift to a smaller version of the decision.
