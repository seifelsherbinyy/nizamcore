# BADAN — Body / Health System

Arabic: بدن — "body."

## Purpose
Advisory tracking of body signals: weight, body composition, sleep, HR/HRV, stress, hydration, nutrition, training, recovery. NOT diagnostic. NOT medical advice.

## Mandatory disclaimer
> "Advisory only — not medical diagnosis. Red flags route to qualified professionals."

Every BADAN output carries this.

## Skills
- `/badan-daily-signal` — log today's signals (all fields optional).
- `/badan-weekly-review` — trend-based weekly review (7-day moving avg minimum).
- `/badan-red-flag-check <symptom>` — route matching symptoms to qualified professionals.

## Red flag list
Chest pain · Unexplained weight change > 5% in 30 days · Persistent fever > 3 days · Shortness of breath at rest · Mental-health distress · Fainting · Unusual bleeding · Neurological symptoms · Severe persistent pain.

Match → output the disclaimer + route to professional. Never diagnose.

## Subfolders
- `daily_signals/{YYYY-MM-DD}.md` — daily entries.
- `weekly_reviews/{YYYY-Wnn}.md` — trend reviews.
- `nutrition/`, `training/`, `sleep_recovery/`, `body_composition/` — domain-specific logs.
- `red_flags/{ts}__{symptom}.md` — red-flag records.

## Data sources supported (Phase 2)
WHOOP / Apple Health / Garmin / smart scale / gym log / manual.

## Mental health
If suicidal ideation or self-harm language detected: stop, route to Egypt mental-health hotline **762 1602** (or emergency **112**) + qualified professional + trusted person.

## Doctrine
[`NIZAM__system/docs/BADAN_HEALTH_ADVISORY_NOTES.md`](../NIZAM__system/docs/BADAN_HEALTH_ADVISORY_NOTES.md)

## Privacy
**strict_local.** All body data `.gitignored`.
