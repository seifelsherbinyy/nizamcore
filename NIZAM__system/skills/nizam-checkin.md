---
name: nizam-checkin
module: NIZAM
trigger: "/nizam-checkin"
session_type: checkin
prompt_doc: NIZAM__system/docs/NIZAM_CONVERSATIONAL_LAYER.md
persona: NIZAM__system/personas/NIZAM.json
target_folder: YAWMIYAT__journaling/sessions/
naming_pattern: "{YYYY-MM-DD}T{HH-MM-SS}Z__checkin.json"
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

Daily ~60s conversational check-in: felt state, capacity, top pillar vote for the day, SCRIBE JSON. COUNSELOR-first; minimal ASSESSOR.

## Procedure

1. Load `prompt_doc` and `persona`. Operate as NIZAM conversational layer with `session_type: checkin`.
2. **SUKOON gate**: Read `sukoon_sources`. If latest flag is red, downshift — tiny versions only, recovery_item required, skip deep blocks.
3. Optionally read today's `SUKOON__recovery_first/signals/<YYYY-MM-DD>.md` for context only — do not assign numeric scores in COUNSELOR; note divergences in ASSESSOR if useful.
4. Run CHECK-IN loop (§3): felt state → capacity → top vote for the day → confirm → SCRIBE JSON with `session_type: "checkin"`, `needs_human_confirmation: true`.
5. Present JSON in a fenced block. Ask operator to confirm or edit.
6. **Only after confirmation**:
   - Set `needs_human_confirmation: false`, `captured_at` to current ISO8601 UTC with `Z`.
   - Validate against `record_schema`.
   - Write to `target_folder` + `naming_pattern` (filesystem-safe timestamp: colons → hyphens in filename segment if needed; JSON `captured_at` keeps `:` form).
   - Optionally write mirror to `mirror_folder` from `mirror_template`.
   - Append THABAT to `appends_event_to`: `{"ts":"<ISO8601>","actor":"NIZAM","skill":"/nizam-checkin","gate":"THABAT","event":"conversational_session_committed","artifact":"<path>","note":"checkin committed"}`
   - Mirror sanitized one-liner to `log.md` (no felt-state details).
