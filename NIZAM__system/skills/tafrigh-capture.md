---
name: tafrigh-capture
module: TAFRIGH
trigger: "/tafrigh-capture"
target_folder: TAFRIGH__brain_dumper/raw/
naming_pattern: "{ISO8601_UTC_FS}.md"
template: NIZAM__system/templates/brain_dump.template.md
frontmatter_schema: NIZAM__system/schemas/note_frontmatter.schema.json
gates: [THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
overload_check:
  source: SUKOON__recovery_first/overload_flags.jsonl
  rule: "append flag if obligations > 7 OR self-pressure language detected"
---

## For future Claude

This skill captures a brain dump without judgment. Do NOT classify, summarize, or editorialize during capture. Triage is a separate skill (`/tafrigh-triage`) run later.

## Procedure

1. Read `CRITICAL_FACTS.md`, `SOUL.md` (if present), `index.md`.
2. Read `NIZAM__system/personas/TAFRIGH.json` for tone and rules.
3. Open template at `NIZAM__system/templates/brain_dump.template.md`.
4. Capture the user's raw input verbatim into `TAFRIGH__brain_dumper/raw/<ISO8601_UTC_FS>.md` (filename example: `2026-05-15T14-17-30Z.md`).
5. Add the standard frontmatter (per `note_frontmatter.schema.json`):
   ```yaml
   ---
   type: brain_dump
   pop_module: TAFRIGH
   pop_privacy: strict_local
   updated: <YYYY-MM-DD>
   confidence: speculative
   tags: [brain-dump]
   recency_anchor: "<YYYY-MM>"
   ---
   ```
6. Add the `## For future Claude` preamble (1–3 lines on what this dump is for).
7. Append a THABAT event to `NIZAM__system/ledgers/EVENT_LEDGER.jsonl`:
   `{"ts":"<ISO8601_UTC>","actor":"TAFRIGH","skill":"/tafrigh-capture","gate":"THABAT","event":"brain_dump_captured","artifact":"<file path>","session_id":"<id>"}`
8. Mirror a one-line entry to `log.md`.
9. Count obligations in the dump (commitments to self/others). If > 7 OR self-pressure language ("I must", "I have to", "I should already have...") detected, append to `SUKOON__recovery_first/overload_flags.jsonl`:
   `{"ts":"<ISO8601_UTC>","module":"TAFRIGH","privacy_level":"strict_local","event_type":"overload_flag","summary":"<one line reason>","source":"<dump file path>","next_action":"consider downshifting tactical load"}`
10. Do NOT auto-run `/tafrigh-triage`. Tell the user the capture is saved and ask if they want to triage now or later.
