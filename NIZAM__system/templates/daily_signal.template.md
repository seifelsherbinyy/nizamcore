---
type: body_signal
pop_module: BADAN
pop_privacy: strict_local
updated: <YYYY-MM-DD>
confidence: high
tags: [body, daily_signal]
recency_anchor: "<YYYY-MM>"
---

## For future Claude
Daily body signal entry. All fields optional. Schema: `body_signal.schema.json`. Always emit medical disclaimer.

# Body Signal — <YYYY-MM-DD>

> **Disclaimer**: Advisory only — not medical diagnosis. Red flags route to qualified professionals.

## Data source
<WHOOP | Apple Health | Garmin | smart_scale | gym_log | manual | other>

## Morning entry
- Weight (kg):
- Body fat %:
- Sleep hours:
- Sleep quality (1–10):
- Resting HR (bpm):
- HRV (ms):

## Now / midday entry
- Stress (1–10):
- Mood (1–10):
- Energy (1–10):
- Hydration (L):
- Caffeine (mg):
- Nicotine:

## Movement / training
- Steps:
- Exercise minutes:
- Exercise type:

## Nutrition
- Calories:
- Protein (g):
- Carbs (g):
- Fat (g):

## Notes
- Digestion:
- Free text:

## Red-flag scan
(Auto: if any free-text matches red-flag list, route to `/badan-red-flag-check`.)
