# Anti-Drift Weekly Check (E2.8)

**Status:** ACTIVE.
**Owner:** Khaldun runs the check; Ammar gates writes; Operator confirms any action.
**Cadence:** Every Sunday between the `weekly_sunday` protocol's `/munawara-weekly-battle` and
`/pop-health` skills.

## Purpose

Measure whether the system's *current model of the operator* still matches the *operator's actual
recent behavior*. If the two have drifted, raise an alert before the drift becomes invisible.

## Definitions

- **System model.** `user.md` + `user_deep.md` + any active Dialectic summary.
- **Operator behavior.** The last 7 days of operator-originated `agent_message` envelopes
  (`from_agent=Operator`), `/feedback` items, SUKOON signals, and decisions logged in
  EVENT_LEDGER / LEARNING_LEDGER.

## The score

`mirroring_fidelity_score` ∈ [0.0, 1.0], stored in `user_deep.md#mirroring_fidelity`.

A score of 1.0 means every recent operator-correctable signal aligns with what the system would
predict from `user.md`/`user_deep.md`. A score of 0.0 means total drift.

### Computation

```python
score = weighted_average(
    voice_alignment    * 0.30,   # operator's /feedback voice has been stable
    values_alignment   * 0.30,   # decisions matched value weights
    focus_alignment    * 0.20,   # operator's actual time matches stated rocks
    guardrail_breaches * 0.10,   # operator violated own guardrails -> drift signal
    sukoon_consistency * 0.10,   # SUKOON state matched the predicted band
)
```

Each sub-score is computed by Khaldun via a small deterministic check plus, for ambiguous cases,
a single ZDR LLM call grounded in concrete EVENT_LEDGER citations.

### Trend

After three weekly measurements, Khaldun sets `trend` to:

- `improving` — score rising ≥ 0.05 week over week.
- `stable` — within ±0.05.
- `drifting` — score falling ≥ 0.05 two weeks in a row.

## Actions per trend

| Trend | Action |
|-------|--------|
| `improving` | Quiet log to LEARNING_LEDGER. No operator nudge. |
| `stable` | Quiet log. |
| `drifting` | Khaldun raises a `kind=alert` envelope (C7 checkpoint). Includes the 3 strongest drift evidence rows. Operator must respond with `/ack` or `/escalate`. If `/escalate`, route to a one-off `/feedback` collection batch. |

## Cost & rate

- Once per week, max one ZDR LLM call (deepseek-flash), capped at $0.10.
- The check is paused when the operator is in `crisis_protocol` mode.

## Failure modes

- **Insufficient data.** Fewer than 5 operator-originated envelopes in the past 7 days → Khaldun
  marks `score = null` and `method = "insufficient_data"`. No alert.
- **All feedback says same thing.** Echo-chamber risk. Khaldun notes the corpus monotony in
  LEARNING_LEDGER and asks the operator for a wider sample on the next `/feedback` opportunity.
- **Drift caused by intentional pivot.** Operator may pre-announce a pivot with
  `/pivot <description>`. Khaldun excludes that week from the drift baseline.

## Acceptance

Implementation lands as a weekly script under `NIZAM__system/governor/anti_drift.py` after E2.6
Honcho spike is in place (Honcho's `dialectic_response` is a key input). The specification (this
document) is enough to schedule the task.
