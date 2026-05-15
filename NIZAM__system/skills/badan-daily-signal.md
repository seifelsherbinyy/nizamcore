---
name: badan-daily-signal
module: BADAN
trigger: "/badan-daily-signal"
target_folder: BADAN__body_health_system/daily_signals/
naming_pattern: "{YYYY-MM-DD}.md"
frontmatter_schema: NIZAM__system/schemas/body_signal.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/BODY_LEDGER.jsonl]
---

## For future Claude

Log today's body signals. ALL fields optional (record what you have). Routes to red-flag-check if user mentions a matching symptom.

## Procedure

1. If file exists for today, ask "update or add evening entry?"
2. Read source preference from `NIZAM__system/personas/BADAN.json` (WHOOP / Apple Health / manual / etc.) — set `data_source` field accordingly.
3. Prompt user (each optional, blank allowed):
   - weight_kg, body_fat_pct
   - sleep_hours, sleep_quality_1_10
   - resting_hr_bpm, hrv_ms (if device-derived)
   - stress_1_10, mood_1_10, energy_1_10
   - hydration_l, caffeine_mg, nicotine
   - steps, exercise_minutes, exercise_type
   - calories_kcal, protein_g, carbs_g, fat_g
   - digestion_notes
   - free_text
4. **Scan free_text + digestion_notes for red-flag keywords** (chest pain, shortness of breath, blood, severe pain, etc.). If matched, immediately invoke `/badan-red-flag-check` flow.
5. Write `BADAN__body_health_system/daily_signals/{YYYY-MM-DD}.md` with frontmatter per schema.
6. Append BODY_LEDGER entry: `event_type: "daily_signal_logged"`.
7. Append THABAT event. Mirror sanitized line ("body signal logged — strict_local") to `log.md`.

## Mandatory output disclaimer

Advisory only — not medical diagnosis. Red flags route to qualified professionals.
