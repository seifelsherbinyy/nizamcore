---
name: badan-weekly-review
module: BADAN
trigger: "/badan-weekly-review"
sources: [BADAN__body_health_system/daily_signals/]
target_folder: BADAN__body_health_system/weekly_reviews/
naming_pattern: "{YYYY-Wnn}.md"
template: NIZAM__system/templates/weekly_review.template.md
frontmatter_schema: NIZAM__system/schemas/body_weekly_review.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
minimum_signals_for_trend: 4
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/BODY_LEDGER.jsonl]
---

## For future Claude

Trend-based weekly review. 7-day moving averages MINIMUM. Refuse single-day overreaction. Always emits the medical disclaimer.

## Procedure

1. Gather last 7 daily signal files. If < 4 are present, write a "insufficient_data" review and skip trend calls.
2. Compute trends for each metric (weight_kg, sleep_quality, stress, energy, training_minutes total, protein average).
3. Score nutrient coverage % (subjective if no precise tracking).
4. Score training/recovery balance: balanced / over_trained / under_trained.
5. Check `BADAN__body_health_system/red_flags/` directory for any new flags this week. List them.
6. Write `BADAN__body_health_system/weekly_reviews/{YYYY-Wnn}.md` with all sections + the mandatory disclaimer.
7. Append BODY_LEDGER entry: `event_type: "weekly_review_completed"` with summary.
8. Append THABAT event. Mirror sanitized line to `log.md`.

## Mandatory output disclaimer

Advisory only — not medical diagnosis. Red flags route to qualified professionals. Trends over 7+ days have signal value; single-day movements do not.
