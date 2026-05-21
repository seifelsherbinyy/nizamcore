---
name: nizam-assess
module: NIZAM
trigger: "/nizam-assess"
session_type: assessment
prompt_doc: NIZAM__system/docs/NIZAM_CONVERSATIONAL_LAYER.md
persona: NIZAM__system/personas/NIZAM.json
target_folder: YAWMIYAT__journaling/sessions/
naming_pattern: "{YYYY-MM-DD}T{HH-MM-SS}Z__assessment.json"
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

Structured evaluation: pillar review, continuity scoring, B=MAP audit on failures, pattern read. ASSESSOR-forward after brief felt-state from COUNSELOR.

## Procedure

1. Load `prompt_doc` and `persona`. Operate with `session_type: assessment`.
2. **SUKOON gate**: Read `sukoon_sources`. On red, limit to continuity-under-stress read + recovery_item; no deep blocks.
3. Brief COUNSELOR felt-state, then ASSESSOR: pillar consistency, B=MAP on named failures (default: behavior too BIG → shrink), capacity + trend, pattern detection.
4. Propose at most 3 priorities + 1 recovery_item + tiny_versions. Confirm with operator.
5. SCRIBE JSON with `session_type: "assessment"`, `needs_human_confirmation: true`.
6. **Only after confirmation**: validate, write files, THABAT + `log.md` as in `nizam-checkin.md`.
7. **Governor (optional):** [`/nizam-governor-push`](nizam-governor.md) with `session_type: assessment` when operator confirms POP externalize; routes Witness + Pulse per governor config.
