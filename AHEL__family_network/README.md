# AHEL — Family Network

Arabic: أهل — "family / kin."

## Purpose
Map the family network and maintain it as a marathon, not a sprint. Person cards, support ledger, connection cadence, important dates. Seif's role as life-support for family members is honored without performance martyrdom.

## Strictest privacy in POP
- Entire `AHEL__family_network/**` is `.gitignored` **except** this README and `_index.json`.
- Never syncs to Obsidian, Notion, or GitHub.
- Sharing requires explicit `/ahel-export <person_id> --confirm`.
- `log.md` entries are sanitized — no names, relations, or details.

## Skills
- `/ahel-add-person` — create or update a person card.
- `/ahel-support-log <person_id>` — record a support promise / delivery / overdue.
- `/ahel-connection-cadence` — surface up to 3 people overdue this week. SUKOON-aware (downshifts to 1–2 if red).

## Subfolders (all gitignored beyond this README)
- `family_tree/` — one card per person.
- `support_ledger/` — support events per person per date.
- `connection_cadence/` — weekly cadence-check records.
- `important_dates/` — acknowledgment records.

## Cadence overload protection
At most **3 people per week** surfaced even if more are technically overdue. If SUKOON is red, reduce to 1–2 from `strong` status (low-effort, uplifting) instead of `strained`.

## Anti-pattern: cadence guilt
This module is a helper, not a debt collector. It pauses on overwhelm.

## Doctrine
[`NIZAM__system/docs/AHEL_FAMILY_PRIVACY_RULES.md`](../NIZAM__system/docs/AHEL_FAMILY_PRIVACY_RULES.md)

## Status
Phase 3 scaffolded — skills + schemas + templates live. Person cards are added as Seif chooses, on his timing.
