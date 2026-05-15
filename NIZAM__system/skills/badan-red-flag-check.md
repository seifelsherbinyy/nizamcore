---
name: badan-red-flag-check
module: BADAN
trigger: "/badan-red-flag-check <symptom>"
target_folder: BADAN__body_health_system/red_flags/
naming_pattern: "{YYYY-MM-DDTHH-MM-SSZ}__{symptom-slug}.md"
frontmatter_schema: NIZAM__system/schemas/body_red_flag.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/BODY_LEDGER.jsonl]
---

## For future Claude

Detect if a symptom matches the red-flag list and **immediately route to a qualified professional**. Never diagnose. Never suggest treatment.

## Procedure

1. Read symptom argument + any context the user provided.
2. Check against red_flag_list in `NIZAM__system/personas/BADAN.json`:
   - chest pain
   - unexplained weight change > 5% in 30 days
   - persistent fever > 3 days
   - shortness of breath at rest
   - mental-health distress (suicidal ideation, sustained low mood, panic)
   - fainting or near-syncope
   - blood in stool / urine / unusual bleeding
   - neurological symptoms (weakness, numbness, vision changes)
   - severe persistent pain
3. If matched OR if user describes acute distress:
   - Immediately output: **"This appears to be a red flag. Please contact a qualified medical professional. If symptoms feel acute, call emergency services. AI advice is not a substitute for medical care."**
   - Suggest the professional type (GP, cardiologist, mental-health professional, ER, etc.) appropriate to the symptom category.
   - Capture per `body_red_flag.schema.json` to `BADAN__body_health_system/red_flags/<ts>__<slug>.md`.
   - Append BODY_LEDGER `event_type: "red_flag_raised"`.
4. If NOT matched, still acknowledge with the mandatory disclaimer and suggest tracking via `/badan-daily-signal`.
5. Append THABAT event. Mirror to `log.md` (no symptom details — just "red_flag_check fired").

## Mandatory output disclaimer

Advisory only — not medical diagnosis. Red flags route to qualified professionals. If acute, call emergency services.

## Mental health note

If the user's input contains language suggesting suicidal ideation or self-harm:
- Stop normal flow.
- Provide local emergency / crisis hotline info (Egypt: 762 1602 — National Council for Mental Health, or 112 emergency).
- Recommend reaching a trusted person + qualified mental-health professional.
- Do NOT minimize. Do NOT pretend to therapize.
