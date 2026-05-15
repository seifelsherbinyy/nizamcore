---
name: ahel-connection-cadence
module: AHEL
trigger: "/ahel-connection-cadence"
sources: [AHEL__family_network/family_tree/]
target_folder: AHEL__family_network/connection_cadence/
naming_pattern: "{YYYY-MM-DD}__cadence_check.md"
gates: [HIMAYAH, SUKOON, THABAT]
privacy: strict_local_maximum
max_people_per_week: 3
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/FAMILY_LEDGER.jsonl]
---

## For future Claude

List who is overdue for contact based on `contact_cadence` + `last_contact`. Cap at 3 people per week to avoid cadence overload.

## Procedure

1. Read all `AHEL__family_network/family_tree/*.md` person cards.
2. For each person, compute days_since_last_contact and target_cadence_days:
   - weekly = 7 days
   - monthly = 30 days
   - quarterly = 90 days
   - annual = 365 days
   - adhoc = no auto-due
3. Overdue if `days_since_last_contact > target_cadence_days`.
4. Sort overdue list by severity (longest overdue first), filtered to non-estranged relationships.
5. **Cap to 3 people for this week.** Even if 10 are overdue, surface 3.
6. For each of the 3, suggest a concrete light action: a 5-min call, a voice note, a meaningful text — not a heavy commitment.
7. Write `AHEL__family_network/connection_cadence/{YYYY-MM-DD}__cadence_check.md` with 3 entries.
8. SUKOON check: if user has been red, reduce to 1–2 people, not 3.
9. Append FAMILY_LEDGER `event_type: "cadence_check"`.
10. Mirror to `log.md`: "- 2026-MM-DD HH:MM | AHEL | cadence check (strict_local — 3 suggested)". NO names.

## Anti-pattern: cadence guilt
The skill is a helper, not a debt collector. If user is overwhelmed:
- Pause cadence enforcement for the week.
- Suggest reaching out to 1 person who is `strong` status (uplifting, low-effort) instead of 3 who are `strained`.
