---
name: kabir-sherbo-annual-review
module: KABIR_SHERBO
trigger: "/kabir-sherbo-annual-review"
sources:
  - KABIR_SHERBO__long_horizon_strategy/10_year/
  - MUNAWARA__tactical_strategy/quarters/
  - NIZAM__system/ledgers/STRATEGY_LEDGER.jsonl
  - NIZAM__system/ledgers/BATTLE_LEDGER.jsonl
  - NIZAM__system/ledgers/DECISION_LEDGER.jsonl
  - NIZAM__system/ledgers/LEARNING_LEDGER.jsonl
target_folder: KABIR_SHERBO__long_horizon_strategy/reviews/annual/
naming_pattern: "{YYYY}_annual_review.md"
template: NIZAM__system/templates/annual_review.template.md
gates: [SUKOON, THABAT]
privacy: strict_local
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/STRATEGY_LEDGER.jsonl]
---

## For future Claude

Annual review of long-horizon plans. Score each strategic pillar honestly. Identify pivots needed. Update 10/15/20-yr documents in-place via NAQD reconciliation if material change needed.

## Procedure

1. Read all active 10/15/20-year plans.
2. For each strategic pillar, score 1–10 on: (a) progress, (b) still-relevant, (c) honest evidence of feasibility.
3. List wins this year (top 5, with evidence).
4. List losses / abandoned (top 5, with reasoning).
5. List learnings — feed to LEARNING_LEDGER.jsonl with `category: principle`.
6. Identify candidate pivots: if any pillar scored < 5 on relevance, propose a pivot via `/munawara-pivot` follow-up.
7. Write `{YYYY}_annual_review.md` with sections: Pillar scorecard → Wins → Losses → Learnings → Pivots → Next year emphasis.
8. Append events:
   - STRATEGY_LEDGER: `event_type: "annual_review_completed"`.
   - EVENT_LEDGER: THABAT close.
9. Mirror to `log.md`.
