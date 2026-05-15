---
name: ahel-add-person
module: AHEL
trigger: "/ahel-add-person"
target_folder: AHEL__family_network/family_tree/
naming_pattern: "{person_id}.md"
frontmatter_schema: NIZAM__system/schemas/family_person.schema.json
template: NIZAM__system/templates/person_card.template.md
gates: [HIMAYAH, SUKOON, THABAT]
privacy: strict_local_maximum
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/FAMILY_LEDGER.jsonl]
log_md_policy: "sanitized only — no names, no relations, no details"
---

## For future Claude

Create or update a family person card. Strict-local maximum privacy. Never write family details to `log.md` or any non-AHEL location.

## Procedure

1. Read `NIZAM__system/personas/AHEL.json` for tone + rules.
2. Elicit per `family_person.schema.json`:
   - `person_id` (slug — used as filename, lowercase, no spaces)
   - `display_name`
   - `branch` (paternal / maternal / inlaw / chosen)
   - `relation` (father / mother / sibling / etc.)
   - `location`
   - `contact_methods`
   - `important_dates` (MM-DD only; no year for low-noise)
   - `relationship_status` (strong / warm / distant / strained / estranged)
   - `contact_cadence` (weekly / monthly / quarterly / annual / adhoc)
   - `support_needs`
   - `notes` (free prose; strict-local)
3. Compute `next_contact_due` from cadence + last_contact.
4. Write file to `AHEL__family_network/family_tree/{person_id}.md` with frontmatter validated against schema. `privacy_level: "strict_local_maximum"` mandatory.
5. Append FAMILY_LEDGER entry: `{"ts":"...","person_id":"<id>","module":"AHEL","privacy_level":"strict_local_maximum","event_type":"contact_made","support_type":"other","promised_action":"person card created/updated","status":"delivered","summary":"person card created"}`
6. Append EVENT_LEDGER entry (sanitized): `{"ts":"...","actor":"AHEL","skill":"/ahel-add-person","gate":"THABAT","event":"person_card_written","artifact":"<file path>","note":"strict_local — details not logged"}`
7. Mirror sanitized line to `log.md`: "- 2026-MM-DD HH:MM | AHEL | person card updated (strict_local)" — **NO names or details.**

## Privacy enforcement

If the user accidentally types family content into a non-AHEL skill (e.g., `/tafrigh-capture`), surface that and ask: "This looks like family data — route to /ahel-add-person instead?"
