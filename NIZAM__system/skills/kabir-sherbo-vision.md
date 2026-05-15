---
name: kabir-sherbo-vision
module: KABIR_SHERBO
trigger: "/kabir-sherbo-vision <horizon>"
target_folders:
  10_year: KABIR_SHERBO__long_horizon_strategy/10_year/
  15_year: KABIR_SHERBO__long_horizon_strategy/15_year/
  20_year: KABIR_SHERBO__long_horizon_strategy/20_year/
naming_pattern: "{horizon}_vision_{YYYY-MM-DD}.md"
template_lookup:
  10_year: NIZAM__system/templates/10_year_vision.template.md
  15_year: NIZAM__system/templates/15_year_vision.template.md
  20_year: NIZAM__system/templates/20_year_vision.template.md
frontmatter_schema: NIZAM__system/schemas/long_horizon_plan.schema.json
gates: [SUKOON, THABAT]
privacy: strict_local
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/STRATEGY_LEDGER.jsonl]
---

## For future Claude

Craft or update a 10 / 15 / 20-year Long War Map. Cover all 11 domains. Force every objective to have a roll-down path to MUNAWARA. Never let a goal exist without an execution layer.

## Procedure

1. Read `CRITICAL_FACTS.md`, `SOUL.md`, `NIZAM__system/personas/KABIR_SHERBO.json`.
2. Check SUKOON gate. If red, suggest deferring this session (long-horizon planning under recovery debt produces fantasy).
3. Pick the template by horizon argument: 10 / 15 / 20.
4. For each of the 11 domains (wealth, career, body, family, faith, location, learning, relationships, business, assets, identity), elicit:
   - Desired future state (vivid, specific).
   - Current gap (honest delta from baseline).
   - Constraints (capital, time, family, health, geography, regulation).
   - Evidence the future state is feasible (or honest "speculative").
5. Define 3–5 **strategic pillars** — load-bearing bets. Each must reference the domains it serves.
6. List **non-negotiables** (what will NOT be traded — pull from SOUL.md if filled).
7. List risks + contingencies. Alliances.
8. Define 5–10 **decisive battles** — the fights that, if won, change trajectory.
9. For each strategic pillar, REQUIRE a roll-down reference to MUNAWARA 5_year/ or 3_year/. Orphans flagged.
10. Write the file with frontmatter validated against `long_horizon_plan.schema.json`.
11. Append `event_type: "vision_created"` (or `"vision_updated"`) to STRATEGY_LEDGER.jsonl.
12. Append THABAT event to EVENT_LEDGER.jsonl. Mirror sanitized one-liner to `log.md`.
