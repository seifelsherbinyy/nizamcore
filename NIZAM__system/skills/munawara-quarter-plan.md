---
name: munawara-quarter-plan
module: MUNAWARA
trigger: "/munawara-quarter-plan"
target_folder: MUNAWARA__tactical_strategy/quarters/
naming_pattern: "{YYYY-Qn}/plan.md"
template: NIZAM__system/templates/quarter_plan.template.md
frontmatter_schema: NIZAM__system/schemas/tactical_plan.schema.json
gates: [SUKOON, THABAT]
privacy: strict_local
rolls_up_to: MUNAWARA__tactical_strategy/1_year/
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Plan the next quarter. Roll up to 1-year, which rolls up to KABIR_SHERBO. Every quarter target must reference its parent. SUKOON gate enforces realism.

## Procedure

1. Read latest `MUNAWARA__tactical_strategy/1_year/` plan.
2. SUKOON check — last 30 days. If predominantly yellow/red, propose a lighter quarter (fewer objectives, more recovery).
3. Identify 3–5 quarter objectives. Each MUST reference its 1_year parent objective.
4. Break into monthly targets (3 months × N objectives).
5. For each objective, capture: success criteria, owner, deadline, recovery_cost_estimate (green/yellow/red), evidence we can do it.
6. Write `MUNAWARA__tactical_strategy/quarters/{YYYY-Qn}/plan.md` with frontmatter validated against `tactical_plan.schema.json`.
7. Append `event_type: "quarter_planned"` to EVENT_LEDGER.
8. Mirror to `log.md` (sanitized).
