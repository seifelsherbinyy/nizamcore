# Workflow — Family Routine

> Scenario: maintaining the family network as a marathon. Strict-local. Cadence-overload protected.

## Skill chain
1. `/ahel-add-person` — when adding or updating a family member
2. `/ahel-connection-cadence` — weekly (or as part of weekly_sunday protocol)
3. `/ahel-support-log "<person_id>"` — when promising / delivering / following up on support

## When to use
- **Add-person**: initial family-tree seeding, or when a relationship status changes.
- **Cadence**: weekly check, max 3 people surfaced.
- **Support-log**: whenever you commit to or complete a support action.

## Procedure

### Initial seed (one-time setup, ~30 min)
Build the family tree gradually:
1. List the 5–10 most important people across paternal / maternal / inlaw / chosen branches.
2. For each, run `/ahel-add-person` — capture person_id (slug), display_name, branch, relation, location, contact methods, important dates (MM-DD only), relationship status, contact cadence preference, support needs, notes.
3. Don't try to capture 50 people on day 1. Add as relationships surface.

### Weekly — `/ahel-connection-cadence`
Surfaces up to **3 people** overdue based on cadence + last_contact.

**Cadence overload protection**:
- Max 3 per week regardless of how many are technically overdue.
- If SUKOON is red, drop to 1–2 from `strong` status (uplifting, low-effort) instead of `strained`.
- Output is a *helper list*, not a debt collector. Skip without guilt.

For each of the 3, suggest a *light* action: 5-min call, voice note, meaningful text. Not a heavy commitment.

### As-needed — `/ahel-support-log <person_id>`
When you commit to support:
- support_type (emotional / financial / logistical / medical / social / spiritual / other)
- promised_action (plain language)
- deadline
- status (promised → in_progress → delivered)
- emotional_load (1–10)
- **recovery_cost_estimate** (green/yellow/red) — if red, the system flags it back to SUKOON

If recovery_cost is red, a SUKOON `overload_flag` is appended automatically. Recovery-first overrides obligation.

## Privacy boundary (strictest in POP)
- All AHEL content is `.gitignored` except README + `_index.json`.
- `log.md` entries are sanitized — never names, relations, or details.
- Sharing a person card requires explicit `/ahel-export <person_id> --confirm`.

## Mental-health awareness
If a family member shows signs of distress / red flags (see `BADAN_HEALTH_ADVISORY_NOTES.md`), don't try to fix it yourself. Suggest professional support. AHEL is *not* a substitute for qualified mental-health care for anyone, including family.

## Anti-patterns
- Adding 50 people on day 1 — overwhelm.
- Letting weekly cadence become a debt — the helper-not-debt-collector principle is violated.
- Logging support promises you can't keep — erodes trust faster than not logging at all.
- Treating family as task completion — relationships aren't a checklist.

## Output
- Person cards in `AHEL/family_tree/<person_id>.md` (strict_local)
- Weekly cadence-check in `AHEL/connection_cadence/{YYYY-MM-DD}__cadence_check.md` (strict_local)
- Support events in `AHEL/support_ledger/<person_id>__<date>.md` (strict_local)
- FAMILY_LEDGER appends (strict_local)
- Sanitized one-liners in `log.md`
