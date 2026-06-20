# Protocol — Crisis: SUKOON Red

> When recovery is red, POP downshifts. This is the protocol that defends rest from ambition's pressure.

## Frontmatter
- **Trigger**: ≥2 red flags in `SUKOON__recovery_first/overload_flags.jsonl` last 24h, OR user-declared crisis state
- **Budget**: as low as possible
- **Gates checked**: SUKOON (overriding), THABAT
- **Skills allowed**: only the recovery-supportive minimum

## What this protocol prevents

When stressed, the instinct is to "push through" — write more plans, double battle counts, force decisions. That's the moment POP must be most disciplined about *less*, not more. This protocol enforces the discipline.

## Allowed skills (recovery-supportive)
- `/sukoon-check` — keep logging signals.
- `/tafrigh-capture` — dump mental load. ALWAYS allowed. Restores clarity.
- `/badan-red-flag-check` — if symptoms warrant.

## Skills to skip (return to when green)
- `/tafrigh-triage` — produces fantasy under red. Capture only.
- `/shura-brainstorm` — heavy cognitive load.
- `/naqd-grill` — auto-switches to "Supportive Reflection" anyway.
- `/munawara-weekly-battle` — auto-cuts 50% but defer entirely if possible.
- `/mal-baseline`, `/mal-decision-score` — financial decisions under stress are biased.
- `/qarar-decide` — defer non-urgent decisions.
- `/tariq-vision`, `/tariq-annual-review` — fantasy fuel.

## Conditional skills
- `/naqd-reconcile` — only if contradiction is blocking active work. Otherwise defer.
- `/badan-daily-signal` — yes, log it. But don't act on single-day spikes.

## Daily during red
1. `/sukoon-check` morning + evening.
2. `/tafrigh-capture` — once, no triage.
3. Sleep priority. Hydration. Walking. Sun. Real food.
4. Tell one trusted person if mental-health language enters TAFRIGH dumps.

## Mental health red-flag escalation

If the TAFRIGH capture contains:
- Suicidal ideation language
- Sustained low mood (≥7 days)
- Panic / dissociation
- Self-harm risk

→ Immediately run `/badan-red-flag-check "mental_health_distress"`.

Egypt resources (also in `CRITICAL_FACTS.md`):
- **National Council for Mental Health**: 762 1602
- **Emergency**: 112
- Trusted person to call: from SOUL.md when filled.

**AI is not a substitute for professional mental-health care.** POP holds the line on this.

## Exit criteria
- ≥ 3 consecutive days of green SUKOON signals → return to normal protocols.
- 1 yellow day after 3+ green → continue normal protocol with light load.

## Anti-patterns under red
- "I'll just do a quick plan" — no.
- "Productivity will help me feel better" — sometimes true for green-fading-to-yellow; almost never true for yellow-to-red.
- Hiding the red state from the system — silence is dangerous. Log it.
- Going to social media for distraction — usually worsens it. TAFRIGH is the safer outlet.

## STRATEGY_LEDGER event
Optional: append `{"event_type":"crisis_protocol_engaged","summary":"red SUKOON triggered crisis protocol on <date>","duration_days":<N>,"exit_state":"green|yellow|red"}` after exit.
