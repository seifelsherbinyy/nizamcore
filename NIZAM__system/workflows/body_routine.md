# Workflow — Body Routine (daily / weekly / red-flag)

> Scenario: ongoing body / health tracking. Advisory only. Red flags route to professionals.

## Skill chain
1. `/badan-daily-signal` — daily
2. `/badan-weekly-review` — every Sunday (7-day moving avg minimum)
3. `/badan-red-flag-check "<symptom>"` — on any matching symptom

## When to use
- **Daily**: anytime body signals are worth logging (morning ideal).
- **Weekly**: every Sunday as part of weekly_sunday protocol.
- **Red-flag-check**: immediately when a symptom from the red-flag list appears.

## Procedure

### Daily — `/badan-daily-signal`
All fields optional. Log what you have:
- Weight, body fat % (if measured)
- Sleep hours + quality (1–10)
- Resting HR, HRV (if device-derived)
- Stress, mood, energy (1–10)
- Hydration, caffeine, nicotine
- Steps, exercise minutes + type
- Calories, protein, carbs, fat
- Digestion notes, free text

**Auto-scan for red flags**: any matching keyword in free text triggers `/badan-red-flag-check`.

### Weekly — `/badan-weekly-review`
Trend-based (7-day moving avg minimum):
- Weight trend (over 7+ days; single-day swings ignored)
- Sleep quality trend
- Stress trend
- Energy trend
- Training minutes total
- Protein average
- Nutrient coverage %
- Training/recovery balance
- Red flags raised this week

Always emits: *"Advisory only — not medical diagnosis."*

### Red-flag detection — `/badan-red-flag-check`
If symptom matches:
- Chest pain
- Unexplained weight change > 5% in 30 days
- Persistent fever > 3 days
- Shortness of breath at rest
- Mental-health distress (suicidal ideation, sustained low mood, panic)
- Fainting or near-syncope
- Blood in stool / urine / unusual bleeding
- Neurological symptoms (weakness, numbness, vision changes)
- Severe persistent pain

→ Immediate output:
> "This appears to be a red flag. Please contact a qualified medical professional. If symptoms feel acute, call emergency services. AI advice is not a substitute for medical care."

Append to `BODY_LEDGER.jsonl` with `event_type: "red_flag_raised"`.

## Mental-health red-flag escalation
If suicidal ideation / self-harm / sustained distress:
- Egypt: **National Council for Mental Health 762 1602**
- Emergency: **112**
- Recommend trusted person + qualified mental-health professional.
- Never minimize. Never therapize.

## Anti-patterns
- Reacting to single-day spikes — that's noise, not signal.
- Self-diagnosing from BADAN trends — refuse the impulse. Trends inform, professionals diagnose.
- Skipping the disclaimer on any BADAN output — non-negotiable.
- Hiding mental-health distress from the log — silence is dangerous.

## Output
- Daily: 1 `body_signal` entry
- Weekly: 1 `body_weekly_review` entry
- Conditional: 1 `body_red_flag` entry routing to professional
- BODY_LEDGER appends throughout
