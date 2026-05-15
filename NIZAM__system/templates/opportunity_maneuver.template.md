---
type: battle
pop_module: MUNAWARA
pop_privacy: strict_local
updated: <YYYY-MM-DD>
confidence: medium
tags: [opportunity_maneuver]
recency_anchor: "<YYYY-MM>"
---

## For future Claude
Capture an unplanned opportunity. Decide: promote to current quarter battle, defer to next quarter, or ignore.

# Opportunity — <YYYY-MM-DD> — <name>

## What surfaced
<one paragraph>

## Why this matters now
<evidence — time-sensitive? unique window?>

## Cost to seize
- Time hours/week:
- Money:
- Attention diverted from:

## Cost to ignore
- What is lost if we skip?

## Decision
- [ ] Promote to current quarter (add as battle in `/munawara-weekly-battle`)
- [ ] Defer to next quarter
- [ ] Ignore

## Reasoning
<2–3 sentences>

## BATTLE_LEDGER event
`{"event_type":"opportunity_seized"}` if promoted.
