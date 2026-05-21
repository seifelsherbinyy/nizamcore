---
name: nizam-counsel
module: NIZAM
trigger: "/nizam-counsel"
session_type: counseling
prompt_doc: NIZAM__system/docs/NIZAM_CONVERSATIONAL_LAYER.md
persona: NIZAM__system/personas/NIZAM.json
target_folder: YAWMIYAT__journaling/sessions/
naming_pattern: "{YYYY-MM-DD}T{HH-MM-SS}Z__counseling.json"
mirror_folder: YAWMIYAT__journaling/mirrors/
mirror_template: NIZAM__system/templates/conversational_session_mirror.template.md
record_schema: NIZAM__system/schemas/conversational_session.schema.json
sukoon_sources:
  - SUKOON__recovery_first/overload_flags.jsonl
  - SUKOON__recovery_first/signals/
gates: [SUKOON, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Counseling session when something is heavy. Mostly COUNSELOR; ASSESSOR only if asked. End by reflecting the decision the operator reached, not one you imposed.

## Procedure

1. Load `prompt_doc` and `persona`. Operate with `session_type: counseling`.
2. **SUKOON gate**: Read `sukoon_sources`. On red, prioritize presence and recovery; defer assessment and file writes unless operator insists.
3. **COUNSELING loop**: One question at a time. Do not interrogate. ASSESSOR only on request.
4. Before SCRIBE, reflect back the decision **they** reached in plain language.
5. Emit SCRIBE JSON with `session_type: "counseling"`, `needs_human_confirmation: true`. Put human-confirmed decisions only in `decisions[]`.
6. **Only after confirmation**: validate, write `target_folder` + `naming_pattern`, optional mirror, THABAT event `conversational_session_committed`, sanitized `log.md` line.
