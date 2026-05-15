---
name: shura-connect
module: SHURA
trigger: "/shura-connect <note_A> <note_B>"
target_folder: SHURA__brainstormer/sessions/
naming_pattern: "{YYYY-MM-DD}__connect__{A-slug}--{B-slug}.md"
gates: [THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Bridge two seemingly unrelated POP notes to surface novel ideas. Pure synthesis — no external research unless user explicitly asks.

## Procedure

1. Read both notes A and B fully.
2. Identify: shared entities, shared concepts, shared time periods, shared values, contradicting claims.
3. Generate 3–5 "bridge hypotheses" — connections that, if true, suggest a new idea.
4. Score each bridge for: novelty (1–10), evidence support (1–10), actionability (1–10).
5. Write `SHURA__brainstormer/sessions/<YYYY-MM-DD>__connect__<A>--<B>.md` with frontmatter, then sections: Bridges → Best hypothesis → Suggested next step.
6. Add `[[wikilinks]]` to both source notes.
7. Append THABAT event. Mirror to `log.md`.
