# AHEL Family Privacy Rules (Phase 3 reference)

> The strictest privacy posture in POP. Designed in Phase 2; scaffolded in Phase 3.

## Core rule
**Nothing in `AHEL__family_network/**` syncs anywhere by default.**

- `.gitignore` excludes the entire folder (with exception only for `README.md` and `_index.json` so the folder shell is visible).
- No Obsidian mirror.
- No Notion mirror.
- No automated exports.

## Per-person export
Sharing a person card requires the user to explicitly run:
```
/ahel-export <person_id> --confirm
```
Output goes to a sanitized export location of the user's choice, never an auto-sync surface.

## Schemas (Phase 3)

### `family_person.schema.json`
- `person_id` (slug)
- `display_name`
- `branch` (paternal / maternal / inlaw / chosen)
- `relation` (father / mother / sibling / uncle / aunt / cousin / spouse / child / friend / other)
- `location` (city, country)
- `contact_methods` (phone / whatsapp / email)
- `important_dates` (label + MM-DD)
- `relationship_status` (strong / warm / distant / strained / estranged)
- `contact_cadence` (weekly / monthly / quarterly / annual / adhoc)
- `support_needs` (emotional / financial / logistical / medical / none)
- `notes` (strict-local prose)
- `last_contact` (ISO date)

### `family_support_event.schema.json`
- `ts`, `person_id`, `support_type`, `promised_action`, `deadline`, `status`, `emotional_load`, `follow_up`

## Skills (Phase 3)
- `/ahel-add-person` — create or update a person card.
- `/ahel-support-log` — record a support promise + deadline.
- `/ahel-connection-cadence` — list overdue touchpoints based on cadence + last_contact. Surface 3 to reach this week, no overload.

## Cadence overload protection

`/ahel-connection-cadence` returns at most 3 people to reach in a given week, even if more are technically overdue. Family is a marathon, not a sprint. Avoiding overwhelm is itself a form of family care.

## Sanitization rules for sharing

If user explicitly chooses to discuss family info with AI (without exporting):
- Use aliases or initials in transcripts.
- Never quote names in `log.md` or other public-tracked files.
- After session, scrub session notes if they accidentally captured names.

## When Phase 3 starts

1. Re-read this doc.
2. Scaffold `AHEL__family_network/{family_tree,support_ledger,connection_cadence,important_dates}/`.
3. Write `AHEL__family_network/_index.json` and `README.md` (visible — folder shell only).
4. Write `NIZAM__system/personas/AHEL.json`.
5. Write 3 skills, 2 schemas, 4 templates.
6. Create empty `NIZAM__system/ledgers/FAMILY_LEDGER.jsonl` (gitignored).
7. Update master registers.
8. Snapshot to MAKHZAN. Commit. Push.
