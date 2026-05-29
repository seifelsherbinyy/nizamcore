---
name: munawara-pivot
module: MUNAWARA
trigger: "/munawara-pivot"
target_folder: TARIQ__long_horizon_strategy/major_pivots/
naming_pattern: "pivot_{YYYY-MM-DD}__{topic-slug}.md"
template: NIZAM__system/templates/major_pivot.template.md
frontmatter_schema: NIZAM__system/schemas/strategy_pivot.schema.json
gates: [SUKOON, THABAT]
privacy: strict_local
snapshot_before_rewrite: MAKHZAN__archive/
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/STRATEGY_LEDGER.jsonl]
---

## For future Claude

Record a major pivot — changing a strategic pillar, swapping a domain priority, or extending/compressing a horizon. Snapshot prior state BEFORE updating affected plans.

## Procedure

1. Identify which TARIQ or MUNAWARA plans this pivot affects. List with `[[wikilinks]]`.
2. Snapshot each affected plan to `MAKHZAN__archive/<ISO8601_UTC>/` with MANIFEST.json (SHA256).
3. Capture per `strategy_pivot.schema.json`:
   - pivot_from, pivot_to, affected_domains
   - why_now (with evidence — file refs, external citations)
   - alternatives_considered
   - recovery_cost (green/yellow/red)
   - rollback_option
4. Update the affected plans in-place to reflect the pivot. Mark old strategic pillars `superseded_by: [[<new pillar>]]` in frontmatter, don't delete them.
5. Write the pivot record at `TARIQ__long_horizon_strategy/major_pivots/pivot_{YYYY-MM-DD}__{slug}.md`.
6. Append `event_type: "major_pivot"` to STRATEGY_LEDGER.
7. Append THABAT event to EVENT_LEDGER. Mirror to `log.md`.
