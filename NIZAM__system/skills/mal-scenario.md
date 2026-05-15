---
name: mal-scenario
module: MAL
trigger: "/mal-scenario <pathway>"
target_folder: MAL__financial_engine/scenario_models/
naming_pattern: "{pathway}_{YYYY-MM-DD}.md"
template: NIZAM__system/templates/scenario_model.template.md
frontmatter_schema: NIZAM__system/schemas/finance_scenario.schema.json
gates: [HIMAYAH, SUKOON, THABAT]
privacy: strict_local
prerequisite_skills: ["/mal-exchange-rate-check"]
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Build a what-if scenario for a single income pathway. Low / expected / high USD outcomes. Effort. Risk. Reversibility. Cashflow timing. Skill leverage. Ethical fit. Recovery cost.

## Procedure

1. Verify the pathway is one of MAL's 7: salary_growth, gcc_or_remote_role, business_income, affiliate_or_performance_marketing, consulting, investment_income, automation_products.
2. Run `/mal-exchange-rate-check` if not done in last 7 days.
3. Elicit per `finance_scenario.schema.json`: ramp_months, monthly_outcomes (low/expected/high USD), effort_hours_weekly, risk_level, reversibility, cashflow_timing_months, skill_leverage_score, ethical_fit_score (cross-check against SOUL.md non-negotiables), recovery_cost_estimate.
4. Write `MAL__financial_engine/scenario_models/{pathway}_{YYYY-MM-DD}.md`.
5. If recovery_cost_estimate is red, flag explicitly: "This pathway threatens recovery. Reconsider or downshift."
6. Append THABAT event.

## Disclaimer line (mandatory)

Scenario modeling is exploratory. Live results require evidence (track 3-month run-rate before promoting a scenario to milestone-rung).
