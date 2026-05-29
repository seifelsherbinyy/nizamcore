---
name: pop-health
module: NIZAM
trigger: "/pop-health"
scan_paths: [TAFRIGH__brain_dumper/, SHURA__brainstormer/, NAQD__brain_griller/, SUKOON__recovery_first/, NIZAM__system/]
target_folder: NIZAM__system/docs/
naming_pattern: "health_audit_{YYYY-MM-DD}.md"
gates: [THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Audit POP for stale claims, orphan notes, contradictions, schema violations, and gaps. This is the vault-evolves-not-grows hygiene routine.

## Procedure

1. **Stale claims**: list notes with `updated:` older than 90 days that carry `confidence: high`. Suggest re-verification.
2. **Orphans**: list notes with no `related:` backlinks AND no inbound `[[wikilinks]]` from any other note.
3. **Contradictions**: cross-grep for opposing claims (heuristic: same key noun + opposite valence within 30 days).
4. **Schema violations**: list notes missing required frontmatter fields per `NIZAM__system/schemas/note_frontmatter.schema.json`.
5. **Orphan strategic goals** (Phase 2 awareness): list TARIQ objectives without MUNAWARA roll-down entries. (Phase 1: noop, just note "Phase 2 not yet scaffolded".)
6. **Ledger sanity**: count entries per ledger, flag any that haven't grown in 7+ days (suggests skill not being used).
7. **Drive mirror drift** (if credentials available): compare GitHub `main` tree SHA to `_Archive/.mirror_state.json` on Drive via `nizam_drive_mirror.py --dry-run`; note pending creates/updates in audit §7.
8. Write `NIZAM__system/docs/health_audit_<YYYY-MM-DD>.md` with 7 sections + recommended actions.
9. Append THABAT event. Mirror summary to `log.md`.
