---
name: naqd-grill
module: NAQD
trigger: "/naqd-grill <topic>"
target_folder: NAQD__brain_griller/sessions/
naming_pattern: "{YYYY-MM-DD}__grill__{topic-slug}.md"
template: NIZAM__system/templates/griller.template.md
frontmatter_schema: NIZAM__system/schemas/note_frontmatter.schema.json
gates: [SUKOON, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
emotional_state_check:
  source: SUKOON__recovery_first/overload_flags.jsonl
  window_hours: 24
  fallback_mode: supportive_reflection
---

## For future Claude

Aggressively stress-test the user's position. ATTACK THE IDEA, NEVER THE PERSON. End with a strengthened version if it survives critique.

## Procedure

1. **Emotional-state gate FIRST**: read `SUKOON__recovery_first/overload_flags.jsonl`. If a `severity: red` or `event_type: "overload_flag"` flag appears in last 24 hours, SWITCH to "Supportive Reflection" mode: gentle questions, no aggressive critique. Tell the user explicitly: "I'm in Supportive Reflection mode because SUKOON is red. Want to red-team this anyway, or talk through it gently?"
2. If green, proceed with assertive red-team:
   - Identify hidden assumptions.
   - Force definitions for vague terms.
   - Demand evidence for strong claims.
   - List 5–10 weak points with reasoning.
   - List 3–5 counterarguments — strongest first.
   - List 5+ pressure-test questions.
3. **Defense strategy**: how would the user respond to each counterargument? Help draft it.
4. **Revised position**: a strengthened version of the user's idea after surviving critique. Make it concrete.
5. **Confidence score** (1–10): how strong is the revised position?
6. Write `NAQD__brain_griller/sessions/<YYYY-MM-DD>__grill__<slug>.md` with frontmatter and the 5-section structure: Weak points → Counterarguments → Pressure-test questions → Defense strategy → Revised position + confidence score.
7. Append a THABAT event. Mirror to `log.md` (sanitized one-liner).
