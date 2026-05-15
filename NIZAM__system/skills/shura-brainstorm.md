---
name: shura-brainstorm
module: SHURA
trigger: "/shura-brainstorm <topic>"
target_folder: SHURA__brainstormer/sessions/
naming_pattern: "{YYYY-MM-DD}__{topic-slug}.md"
template: NIZAM__system/templates/brainstorm.template.md
frontmatter_schema: NIZAM__system/schemas/note_frontmatter.schema.json
gates: [SUKOON, THABAT]
privacy: strict_local
research_mode: vault_first
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Co-think a topic. **VAULT-FIRST RESEARCH**: scan POP for existing relevant notes BEFORE any external search. Produce a delta report. Only then fill gaps externally if needed.

## Procedure

1. Read `CRITICAL_FACTS.md`, relevant `SOUL.md` sections, `index.md`.
2. Read `NIZAM__system/personas/SHURA.json`.
3. **Vault-first scan**: grep POP for the topic. List existing notes that touch it. Note recency, confidence levels, and contradictions if any.
4. Produce a **delta report**: what POP already knows vs. what's missing.
5. Only after delta report, fill gaps with external sources if user authorizes. Cite sources verbatim with `(as of YYYY-MM, source)` recency anchors.
6. Open session file `SHURA__brainstormer/sessions/<YYYY-MM-DD>__<slug>.md` with frontmatter:
   ```yaml
   ---
   type: brainstorm
   pop_module: SHURA
   pop_privacy: strict_local
   updated: <YYYY-MM-DD>
   confidence: medium
   sources: [...]
   related: [[...]]
   tags: [brainstorm]
   ---
   ```
7. Use the template structure: Context → Vault-first delta → Options → Tradeoffs → Recommendation → Next actions → Research questions.
8. Use `[[wikilinks]]` for every cross-reference to existing POP notes.
9. SUKOON gate: if distress flag last 24h, lighten the cognitive load — keep session ≤ 20 minutes.
10. Append THABAT event to `EVENT_LEDGER.jsonl`. Mirror to `log.md`.
