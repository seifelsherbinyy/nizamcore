---
name: naqd-reconcile
module: NAQD
trigger: "/naqd-reconcile <new_info>"
source_folders: [TAFRIGH__brain_dumper/triaged/, SHURA__brainstormer/sessions/, NAQD__brain_griller/sessions/]
target_folder: NAQD__brain_griller/sessions/
naming_pattern: "{YYYY-MM-DD}__reconcile__{topic-slug}.md"
gates: [HIMAYAH, THABAT]
privacy: strict_local
snapshot_before_rewrite: MAKHZAN__archive/
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/DECISION_LEDGER.jsonl]
---

## For future Claude

Vault evolves, not grows. When new information contradicts existing notes, NAQD owns the resolution. Snapshot prior state to MAKHZAN__archive BEFORE rewriting anything.

## Procedure

1. Identify which existing POP notes the new info contradicts. List with `[[wikilinks]]`.
2. For each affected note, snapshot to `MAKHZAN__archive/<ISO8601_UTC>/<original-path-mirrored>` and add a `MANIFEST.json` entry with SHA256.
3. Decide per note: **Update** (rewrite to reflect new truth, increment `updated:` field), **Append** (new info doesn't invalidate, just adds), or **Mark stale** (note becomes historical, frontmatter `confidence: low` + `superseded_by: [[new note]]`).
4. Write reconciliation summary at `NAQD__brain_griller/sessions/<YYYY-MM-DD>__reconcile__<slug>.md`: which notes touched, what changed, why, prior-state snapshot path.
5. Append events:
   - EVENT_LEDGER: `{"event":"reconciliation_completed", "affected_notes":[...], "snapshot":"<path>"}`
   - DECISION_LEDGER: a one-line decision record on the resolution rationale.
6. Mirror to `log.md`.
