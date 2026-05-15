# Workflow — Strategy Rollup (10yr → today)

> Scenario: turning a long-horizon vision into something you do this week.

## Skill chain
1. `/kabir-sherbo-vision 10` — set / verify 10-year vision
2. `/kabir-sherbo-vision 15` and `/kabir-sherbo-vision 20` (optional outer horizons)
3. Define MUNAWARA 5-year plan (manual; rolls to KABIR_SHERBO)
4. Define MUNAWARA 3-year plan (rolls to 5-year)
5. Define MUNAWARA 1-year plan (rolls to 3-year)
6. `/munawara-quarter-plan` (rolls to 1-year)
7. Monthly milestones inside the quarter plan
8. `/munawara-weekly-battle` (rolls to month + quarter)
9. Daily morning protocol picks today's Now-item from the week's battles

## When to use
- First time setting up POP's strategic layer.
- After a major life event prompts a re-anchor.
- Annually as part of `/kabir-sherbo-annual-review`.

## Procedure

### Layer 1 — 10/15/20-year vision (KABIR_SHERBO)
Cover all 11 domains (wealth, career, body, family, faith, location, learning, relationships, business, assets, identity). Define 3–5 strategic pillars. Write decisive battles.

### Layer 2 — 5-year plan (MUNAWARA)
For each KABIR_SHERBO strategic pillar, define what year-5 looks like. Each 5-year objective must reference the parent pillar in frontmatter.

### Layer 3 — 3-year plan (MUNAWARA)
For each 5-year objective, define year-3 milestone. This is where speculation starts becoming concrete.

### Layer 4 — 1-year plan (MUNAWARA)
For each 3-year milestone, define what year-1 looks like. 4 quarters × N initiatives.

### Layer 5 — Quarter plan
`/munawara-quarter-plan`. 3–5 objectives. Each must reference the 1-year parent. Recovery_cost estimate per objective.

### Layer 6 — Monthly milestones
Inside the quarter plan, define 3 monthly checkpoints per objective.

### Layer 7 — Weekly battle
`/munawara-weekly-battle`. The Dynamic War Strategy protocol picks 1–N battles for this week (capped 50% if SUKOON ≥2 red).

### Layer 8 — Daily Now-item
The daily morning protocol picks 1 Now-item that should be a step in this week's primary battle.

## The roll-up audit
`/pop-health` flags **orphan strategic goals** — any KABIR_SHERBO objective without MUNAWARA roll-down, or any MUNAWARA objective without a parent reference. Run weekly.

## Anti-patterns
- Building a 10-year vision but never doing the 5/3/1-year work — fantasy.
- Setting weekly battles that don't reference a parent — firefighting.
- Treating each layer as immutable — pivots are expected at annual / quarterly close.

## Output
- 1 KABIR_SHERBO 10-yr vision (minimum)
- 1 MUNAWARA 5-yr plan
- 1 MUNAWARA 3-yr plan
- 1 MUNAWARA 1-yr plan
- 1 MUNAWARA quarter plan per quarter
- Monthly + weekly entries inside the quarter folder
- BATTLE_LEDGER entries at week close
