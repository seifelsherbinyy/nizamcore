---
name: ahel-support-log
module: AHEL
trigger: "/ahel-support-log <person_id>"
target_folder: AHEL__family_network/support_ledger/
naming_pattern: "{person_id}__{YYYY-MM-DD}.md"
frontmatter_schema: NIZAM__system/schemas/family_support_event.schema.json
template: NIZAM__system/templates/support_event.template.md
gates: [HIMAYAH, SUKOON, THABAT]
privacy: strict_local_maximum
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/FAMILY_LEDGER.jsonl]
---

## For future Claude

Log a support event for a family member: a promise made, an action delivered, an overdue follow-up. Recovery_cost estimate is mandatory — supporting family at red is unsustainable.

## Procedure

1. Verify `person_id` exists in `AHEL__family_network/family_tree/`. If not, prompt user to run `/ahel-add-person` first.
2. SUKOON check — if last 7 days show ≥2 red flags, ask: "You're at recovery debt. Is this support promise sustainable, or should we defer / scale it down?"
3. Elicit per `family_support_event.schema.json`:
   - `event_type` (support_promised / support_delivered / support_overdue / contact_made / important_date_acknowledged / support_completed)
   - `support_type` (emotional / financial / logistical / medical / social / spiritual / other)
   - `promised_action` (plain language, ≤ 280 chars)
   - `deadline` (if applicable)
   - `status` (promised / in_progress / delivered / overdue / cancelled)
   - `emotional_load_1_10`
   - `recovery_cost_estimate` (green / yellow / red)
   - `follow_up`
4. Write to `AHEL__family_network/support_ledger/{person_id}__{YYYY-MM-DD}.md`.
5. Update the person's last_contact date in their person card.
6. Append to FAMILY_LEDGER with the full schema.
7. Append sanitized EVENT_LEDGER entry: `{"event":"support_event_logged","note":"strict_local — details not logged"}`.
8. Mirror sanitized line to `log.md`: "- 2026-MM-DD HH:MM | AHEL | support event logged (strict_local)". NO person_id, NO details.

## Recovery_cost downshift

If recovery_cost_estimate is red, append a SUKOON overload_flag:
`{"ts":"...","module":"AHEL","privacy_level":"strict_local","event_type":"overload_flag","severity":"yellow","summary":"family support promise at red recovery cost — consider scaling","source":"<support event file>","next_action":"reconsider scope or timeline"}`
