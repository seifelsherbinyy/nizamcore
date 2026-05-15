---
name: mal-baseline
module: MAL
trigger: "/mal-baseline"
target_folder: MAL__financial_engine/baseline/
naming_pattern: "baseline_{YYYY-MM-DD}.md"
template: NIZAM__system/templates/finance_baseline.template.md
frontmatter_schema: NIZAM__system/schemas/finance_baseline.schema.json
gates: [HIMAYAH, SUKOON, THABAT]
privacy: strict_local
prerequisite_skills: ["/mal-exchange-rate-check"]
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/FINANCE_LEDGER.jsonl]
---

## For future Claude

Snapshot current financial baseline. Income / costs / debt / savings / assets / liabilities / runway / skill assets / business pipelines. Always store BOTH EGP and USD with verified rate.

## Procedure

1. Run `/mal-exchange-rate-check` first to capture today's rate. Use median of ≥2 sources.
2. Read `NIZAM__system/personas/MAL.json` for baseline current_baseline_at_phase_2_start (stable_monthly_egp ≈ 47000).
3. Elicit each field per `finance_baseline.schema.json`:
   - Income: stable_gross, stable_net, variable_avg, one_off_recent.
   - Fixed + variable costs (categorized).
   - Debt list (principal, rate, term, min payment).
   - Savings (liquid, investment).
   - Assets and liabilities.
   - Skill assets (catalog of monetizable skills).
   - Business pipelines (stage + expected value + effort).
4. Compute runway_months = liquid_savings / (fixed_costs + variable_avg_costs).
5. Write `MAL__financial_engine/baseline/baseline_{YYYY-MM-DD}.md` with frontmatter validated against schema. **rate_verified: true** mandatory.
6. Append FINANCE_LEDGER entry: `event_type: "baseline_snapshot"`.
7. Append THABAT event. Mirror sanitized line to `log.md` (e.g., "baseline snapshot taken — details strict-local").

## Disclaimer line (mandatory on output)

This is personal financial tracking, not professional financial advice. Decisions affecting major life outcomes warrant a qualified financial advisor.
