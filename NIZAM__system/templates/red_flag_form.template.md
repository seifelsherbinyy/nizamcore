---
type: misc
pop_module: BADAN
pop_privacy: strict_local
updated: <YYYY-MM-DD>
confidence: high
tags: [body, red_flag]
recency_anchor: "<YYYY-MM>"
---

## For future Claude
Red-flag form. Triggered by `/badan-red-flag-check`. Always routes to professional — never diagnose.

# Red Flag — <ISO8601_UTC>

> **Disclaimer**: This is a red flag. Please contact a qualified medical professional. If symptoms feel acute, call emergency services. AI advice is not a substitute for medical care.

## Symptom
<plain description>

## Duration
<e.g., "3 days", "persistent", "episodic since YYYY-MM">

## Severity (1–10)
<self-report>

## Matched red-flag category
<chest_pain | unexplained_weight_change | persistent_fever | shortness_of_breath | mental_health_distress | fainting | unusual_bleeding | neurological | severe_pain | other>

## Professional type suggested
<GP | cardiologist | mental health professional | ER | other>

## User acknowledged
<yes/no>

## Followed up
<yes/no — fill later>

## Mental health resources (if matched mental_health_distress)
- Egypt — National Council for Mental Health: 762 1602
- Emergency: 112
- Trusted person to call: <from SOUL.md if filled>

## BODY_LEDGER event
`{"ts":"...","module":"BADAN","privacy_level":"strict_local","event_type":"red_flag_raised","summary":"<symptom>"}`
