# SCHEDULED_AGENTS

> Automation layer that prompts or runs POP skills on a cadence. Designed; implementation per agent-runner choice.

## Why scheduled agents

Daily / weekly / monthly cadence routines are easy to skip when life gets busy — the exact moments POP is most valuable. Scheduled agents add a gentle nudge or auto-execute the routine.

## Cadence map

| When | Agent | Skill | Purpose |
|---|---|---|---|
| Daily 07:00 | morning_capture | `/sukoon-check` → `/tafrigh-capture` → `/tafrigh-triage` | Open the day intentionally |
| Daily 22:30 | nightly_roll_up | append day's events to `log.md` | Close the day in record |
| Sunday 18:00 | weekly_recap | `/pop-recap` → `/munawara-weekly-battle` → `/badan-weekly-review` → `/pop-health` | Synthesize the week |
| 1st of month | monthly_milestone | `/mal-milestone-check` → `/mal-exchange-rate-check` | Track finance progress |
| 1st of quarter | quarterly_plan | `/munawara-quarter-plan` | Plan next quarter |
| Jan 1 | annual_review | `/kabir-sherbo-annual-review` | Score pillars + identify pivots |
| Daily 08:00 | cadence_check (optional) | `/ahel-connection-cadence` | Surface up to 3 family members |

## Runner choices (pick one, document in this file when chosen)

### Option A — Windows Task Scheduler (simplest, native)
PowerShell scripts in `HIFZ__github_version_control/scripts/` triggered by Task Scheduler. Each script invokes Claude Code with a prompt that calls the appropriate skill.

Pro: zero new dependencies.
Con: assumes laptop is on at the scheduled time.

### Option B — claude-code-router or similar agent-orchestration tool
A persistent agent process polls for scheduled events and dispatches skills.

Pro: more flexible, supports retries.
Con: another tool to maintain.

### Option C — GitHub Actions cron (cloud-side)
A cron workflow in `.github/workflows/` runs a script that posts to your local POP via webhook.

Pro: runs even when laptop is off.
Con: requires network connectivity from laptop AND introduces a public surface (only schedule + script visible; never personal content).

## Recovery-first override (mandatory across all runner choices)

**Every scheduled agent must check SUKOON first.**
- If `SUKOON__recovery_first/overload_flags.jsonl` shows ≥ 2 red flags in last 24h:
  - Skip non-critical agents (cadence_check, monthly_milestone, quarterly_plan).
  - Still run lightweight reflective ones (`/sukoon-check`, `/tafrigh-capture` — they help recovery, not pressure it).
  - Append an `agent_skipped_for_recovery` event to EVENT_LEDGER.

## Implementation status
**Designed only**. Choose a runner when ready (recommend ~2 weeks of manual Phase 1+2 use first so you know which cadences actually matter).

## When implementing

1. Write the runner script(s) in `HIFZ__github_version_control/scripts/`.
2. Document choice + schedules in this file.
3. Test each agent manually before scheduling.
4. Append to EVENT_LEDGER: `event_type: "scheduled_agents_activated"`.
