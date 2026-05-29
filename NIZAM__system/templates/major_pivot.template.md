---
type: strategy_plan
pop_module: TARIQ
pop_privacy: strict_local
updated: <YYYY-MM-DD>
confidence: high
tags: [major_pivot]
recency_anchor: "<YYYY-MM>"
---

## For future Claude
Major pivot record. Schema-validated. Snapshot affected plans to MAKHZAN before update.

# Major Pivot — <YYYY-MM-DD> — <Topic>

## Pivot summary
- **From**:
- **To**:
- **Affected domains**:

## Why now
<Plain prose. Cite evidence.>

## Evidence
- <file reference or external citation>
- <file reference or external citation>

## Alternatives considered
1. <alt 1> — why rejected
2. <alt 2> — why rejected

## Recovery cost
- Color (green/yellow/red):
- Reasoning:

## Rollback option
<If this pivot fails in 6 months, what does rollback look like? Is it possible?>

## MAKHZAN snapshot
- Path: `MAKHZAN__archive/<ISO8601_UTC>/`
- Files snapshotted: <list>

## Affected plans (updated in-place)
- [[<plan 1>]] — old pillar marked superseded_by
- [[<plan 2>]]

## STRATEGY_LEDGER event
`{"ts":"...", "module":"TARIQ", "privacy_level":"strict_local", "event_type":"major_pivot", "pivot_from":"...", "pivot_to":"...", "summary":"..."}`
