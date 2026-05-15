---
name: shura-emerge
module: SHURA
trigger: "/shura-emerge"
window_days: 30
sources: [TAFRIGH__brain_dumper/raw/, TAFRIGH__brain_dumper/triaged/, SHURA__brainstormer/sessions/, NAQD__brain_griller/sessions/, SUKOON__recovery_first/signals/]
target_folder: SHURA__brainstormer/sessions/
naming_pattern: "{YYYY-MM-DD}__emerge.md"
gates: [THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Surface unnamed patterns from the last 30 days of POP activity. The goal is to name a recurring thread the user hasn't yet labeled.

## Procedure

1. Glob the `sources` listed in frontmatter for files modified in last 30 days.
2. Extract recurring nouns, verbs, emotions, and obligations. Tally frequency.
3. Cluster into 3–7 candidate patterns. Give each a tentative name.
4. For each pattern: cite ≥3 source files as evidence. Recency anchor.
5. Write `SHURA__brainstormer/sessions/<YYYY-MM-DD>__emerge.md` with: Pattern name → Evidence (≥3 cites) → Suggested label → "Is this real or is it noise?" question to user.
6. End with: "Which of these patterns deserves a permanent label and dedicated note?" → if user says yes, offer `/shura-graduate`.
7. Append THABAT event.
