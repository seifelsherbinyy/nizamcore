# POP Workflows Index

Workflows are **scenario-driven skill chains**. Unlike protocols (cadence-driven, recurring time-based), workflows fire when a specific situation surfaces — any time, any day.

## Decision-making

| Workflow | Trigger scenario | Skills chained |
|---|---|---|
| [idea_to_decision](idea_to_decision.md) | A notable decision is forming | `/tafrigh-capture` → `/shura-brainstorm` → `/naqd-grill` → `/qarar-decide` |
| [contradiction_resolution](contradiction_resolution.md) | New info conflicts with existing POP notes | `/pop-health` (or `/naqd-challenge`) → `/naqd-reconcile` → MAKHZAN snapshot → ledger appends |

## Project + Strategy

| Workflow | Trigger scenario | Skills chained |
|---|---|---|
| [idea_to_project](idea_to_project.md) | An idea has earned execution | `/tafrigh-capture` → `/tafrigh-triage` → `/shura-graduate` → route to INTAJ or MUNAWARA |
| [strategy_rollup](strategy_rollup.md) | Setting up or refreshing the strategic stack | `/tariq-vision` → MUNAWARA 5/3/1-yr → `/munawara-quarter-plan` → `/munawara-weekly-battle` → daily Now |

## Finance

| Workflow | Trigger scenario | Skills chained |
|---|---|---|
| [finance_decision](finance_decision.md) | Financial decision > $1k impact OR cross-currency | `/mal-exchange-rate-check` → `/mal-baseline` → `/mal-scenario` → `/mal-decision-score` → `/qarar-decide` → `/mal-milestone-check` |

## Body

| Workflow | Trigger scenario | Skills chained |
|---|---|---|
| [body_routine](body_routine.md) | Daily / weekly body tracking + red-flag handling | `/badan-daily-signal` → `/badan-weekly-review` → `/badan-red-flag-check` (if symptom matched) |

## Synthesis

| Workflow | Trigger scenario | Skills chained |
|---|---|---|
| [weekly_synthesis](weekly_synthesis.md) | Sunday or quiet hour for interpretation, not just logging | `/pop-recap` → `/shura-emerge` → `/pop-health` → optional `/shura-graduate` |

## How workflows differ from protocols

- **Workflow**: fires on a *scenario* (any time you need that chain).
- **Protocol**: fires on a *cadence* (daily morning, weekly Sunday, etc.).

See [`protocols/_PROTOCOLS_INDEX.md`](../protocols/_PROTOCOLS_INDEX.md).

## How workflows differ from skills

- A **skill** is a single encoded path (`/sukoon-check`).
- A **workflow** is a *scenario-tagged chain* of 2+ skills with decision points.

## Workflows that span phases
- `idea_to_project` references INTAJ (Phase 2 shell-only). Until INTAJ skills are live, fragments accumulate in `SHURA/sessions/` with `phase_2_target` frontmatter.
- `strategy_rollup` requires TARIQ + MUNAWARA (both Phase 2 live).

## When to write a new workflow
- A user repeatedly chains 2+ skills in the same order for the same scenario type.
- A SUKOON or HIMAYAH gate's behavior creates a distinctive decision tree that should be reusable.
- A failure mode keeps recurring and needs a documented recovery procedure.

Write candidate workflows in this folder as drafts (`_draft__name.md`) and let them prove themselves over 2–3 invocations before promoting.
