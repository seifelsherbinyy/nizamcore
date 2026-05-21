---
name: nizam-consult
module: NIZAM
trigger: "/nizam-consult <topic>"
session_type: consultation
prompt_doc: NIZAM__system/docs/NIZAM_CONVERSATIONAL_LAYER.md
persona: NIZAM__system/personas/NIZAM.json
target_folder: YAWMIYAT__journaling/sessions/
naming_pattern: "{YYYY-MM-DD}T{HH-MM-SS}Z__consultation.json"
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

Decision consultation on a specific topic. Lay out options as a decision tree with trade-offs; give honest recommendation; operator chooses.

## Procedure

1. Load `prompt_doc` and `persona`. Parse `<topic>` from trigger. Operate with `session_type: consultation`.
2. **SUKOON gate**: Read `sukoon_sources`. On red, narrow to minimum viable decision or defer.
3. Brief felt-state, then consultation: options tree, trade-offs, honest recommendation. Operator chooses — record only their choice in `decisions[]`.
4. If decision warrants ADR, suggest `/qarar-decide <topic>` after this session commits.
5. SCRIBE JSON with `session_type: "consultation"`, `needs_human_confirmation: true`.
6. **Only after confirmation**: validate, write files, THABAT + `log.md` as in `nizam-checkin.md`.
