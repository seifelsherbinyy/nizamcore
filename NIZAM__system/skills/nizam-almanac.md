---
name: nizam-almanac
module: NIZAM
trigger: "/nizam-almanac"
session_type: weekly_review
prompt_doc: NIZAM__system/docs/NIZAM_CONVERSATIONAL_LAYER.md
persona: NIZAM__system/personas/NIZAM.json
window_days: 7
sources:
  - YAWMIYAT__journaling/sessions/
  - SUKOON__recovery_first/signals/
  - SUKOON__recovery_first/overload_flags.jsonl
target_folder: YAWMIYAT__journaling/weekly/
naming_pattern: "{YYYY-Wnn}__almanac.md"
mirror_template: NIZAM__system/templates/conversational_session_mirror.template.md
record_schema: NIZAM__system/schemas/conversational_session.schema.json
gates: [THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Interpretive weekly Almanac from conversational session JSON. Complements `/pop-recap` (structural ledger synthesis) — does not replace it.

## Procedure

1. Load `prompt_doc` and `persona`. Operate with `session_type: weekly_review`.
2. Load all `sources[0]` `*.json` files from the last `window_days` days. Validate each against `record_schema` if present; skip malformed with a note.
3. Optionally cross-read SUKOON signals for **felt-vs-reported divergences** (conversational felt_state vs numeric sukoon metrics).
4. Produce Almanac sections in conversation, then in markdown:
   - **KPIs**: session count by type, capacity distribution, pillar vote/miss themes
   - **Blockers**: recurring `open_questions` and `contrary_urges`
   - **Divergences**: felt vs SUKOON numeric where both exist
   - **Fewer-repeated-failures**: B=MAP themes from `bmap_audit` fields
   - **One redesign action**: single concrete change for next week
5. If `/pop-recap` was run this week, cross-link `SHURA__brainstormer/sessions/<date>__recap_week.md` in `related` frontmatter when path exists.
6. Write `target_folder` + `naming_pattern` with frontmatter:
   ```yaml
   ---
   type: conversational_session_mirror
   pop_module: NIZAM
   pop_privacy: strict_local
   updated: <YYYY-MM-DD>
   confidence: medium
   tags: [almanac, weekly_review]
   ---
   ```
7. Emit companion SCRIBE JSON summary (can be embedded in markdown § Canonical JSON) with `session_type: "weekly_review"`. Operator confirms before treating as committed.
8. On confirm: append THABAT `conversational_almanac_committed`, mirror `log.md` one-liner.
