---
name: pop-recap
module: NIZAM
trigger: "/pop-recap"
window_days: 7
sources:
  - NIZAM__system/ledgers/EVENT_LEDGER.jsonl
  - NIZAM__system/ledgers/DECISION_LEDGER.jsonl
  - NIZAM__system/ledgers/LEARNING_LEDGER.jsonl
  - SUKOON__recovery_first/overload_flags.jsonl
target_folder: SHURA__brainstormer/sessions/
naming_pattern: "{YYYY-MM-DD}__recap_week.md"
gates: [THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Synthesize the last 7 days from POP's own ledgers. NOT a brain dump — a structured weekly review built from machine-readable data.

## Procedure

1. Filter all ledger sources to entries in the last 7 days.
2. Section 1 — **Activity**: total captures, brainstorms, grilling sessions, decisions, learnings. One-line per category.
3. Section 2 — **Recovery**: how many green/yellow/red signal days? Trend (improving / stable / declining)?
4. Section 3 — **Wins**: top 3 outcomes worth naming.
5. Section 4 — **Friction**: top 3 obstacles or recurring blockers.
6. Section 5 — **Themes**: recurring topics surfaced by `/shura-emerge`-style pattern detection.
7. Section 6 — **Next week**: 3 priorities (Now-bucket from TAFRIGH triage); 1 to defer; 1 to delete.
8. Write `SHURA__brainstormer/sessions/<YYYY-MM-DD>__recap_week.md` with frontmatter.
9. Append THABAT event. Mirror to `log.md`.
