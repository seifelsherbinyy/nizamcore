# POP Protocols Index

Protocols are **chained skill sequences** for routine cadences. Each protocol is a documented procedure that calls 2+ skills in a specific order, with gate checks and adjustment rules.

## Daily

| Protocol | Cadence | Budget | Skills chained |
|---|---|---|---|
| [daily_morning](daily_morning.md) | Every morning | 5–10 min | `/sukoon-check` → `/tafrigh-capture` → `/tafrigh-triage` → pick 1 Now |
| [daily_evening](daily_evening.md) | Optional evening | 5–10 min | (optional `/tafrigh-capture`) → DECISION_LEDGER entry → LEARNING_LEDGER entry |

## Weekly

| Protocol | Cadence | Budget | Skills chained |
|---|---|---|---|
| [weekly_sunday](weekly_sunday.md) | Sunday evening | ~30 min | `/pop-recap` → `/munawara-weekly-battle` → `/badan-weekly-review` → `/pop-health` |

## Monthly / Quarterly / Annual

| Protocol | Cadence | Budget | Skills chained |
|---|---|---|---|
| [monthly_close](monthly_close.md) | 1st of month | ~60 min | `/mal-exchange-rate-check` → `/mal-milestone-check` → monthly review → BADAN monthly trend → `/ahel-connection-cadence` |
| [quarterly_close](quarterly_close.md) | End of quarter | ~2 hr | `/munawara-quarter-plan` → cross-domain `/shura-brainstorm` → TARIQ pillar check |
| [annual_close](annual_close.md) | Late December | ~4–6 hr | `/tariq-annual-review` → `/shura-emerge` 365d → HIKMAH crystallization → 10/15/20-yr refresh |

## Exception protocols

| Protocol | Trigger | Purpose |
|---|---|---|
| [crisis_sukoon_red](crisis_sukoon_red.md) | ≥2 red SUKOON flags / user-declared crisis | Downshift to recovery-supportive minimum; defend rest from ambition |
| [onboarding_first_7_days](onboarding_first_7_days.md) | First-time NIZAM user | Gentle 7-day on-ramp, daily morning habit first |

## Agent communication & governance (Plan v2 §E1)

| Protocol | Purpose | Enforced by |
|---|---|---|
| [agent_delegation_protocol](agent_delegation_protocol.md) | Depth cap, allowed agent→agent edges, escalation rules | Coordinator + `agent_message.schema.json` |
| [conflict_resolution](conflict_resolution.md) | NAQD arbitrates when confidence spread ≤ 0.15 | Hazim (NAQD), Operator override |
| [operator_checkpoints](operator_checkpoints.md) | The 7 mandatory human-in-the-loop pause points | Ammar + Coordinator |

## How protocols differ from skills

- A **skill** is a single encoded path: trigger → target folder → naming → template → gates → procedure.
- A **protocol** is a *sequence of skills* with cadence rules and adjustment logic for SUKOON state.

## How protocols differ from workflows

- A **protocol** is cadence-driven (recurring time-based routine).
- A **workflow** is scenario-driven (e.g., "from idea to decision," any time you need that chain).

See [`workflows/_WORKFLOWS_INDEX.md`](../workflows/_WORKFLOWS_INDEX.md).

## SUKOON state always wins

Every protocol explicitly defines its behavior when SUKOON is green / yellow / red. Recovery-first is non-negotiable across all cadences. The crisis protocol exists specifically to defend this rule from ambition's pressure.
