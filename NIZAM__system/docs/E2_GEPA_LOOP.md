# GEPA Prompt-Evolution Loop Specification (E2.7)

**Status:** SPEC. Implementation behind multiple checkpoints. Operator approval required to
adopt any optimized prompt.
**Owner:** Khaldun runs the loop; Ammar gates every adoption; Operator confirms via C1.

## Goal

Adopt the **GEPA (Genetic-Pareto)** reflective prompt-evolution algorithm to incrementally improve
the prompts that pillar agents use, grounded in real `/feedback` from the operator. We use the
DSPy implementation (`dspy.GEPA`) so we inherit a maintained library rather than write our own
optimizer.

GEPA's core property: it learns from *natural-language feedback*, not from numeric reward only.
That is exactly the shape of `/feedback voice ...` style notes. The operator's feedback can be
ingested directly.

## Why GEPA over RLHF or vanilla prompt tuning

- **Sample efficient.** GEPA shows substantial gains within ~10–100 reflective rounds, far below
  RLHF's data scale. For a solo operator with handful-of-`/feedback`-per-day budget, this is the
  only realistic option.
- **Reflective traces are auditable.** Each iteration logs *why* a candidate prompt won, in natural
  language. We can therefore enforce the C1 operator-confirm before adopting any winner.
- **Pareto-frontier maintained.** Keeps multiple non-dominated candidates instead of collapsing to
  a single "best." That matches how operator feedback varies by mood, hour, and SUKOON state.

## Inputs

For each pillar agent (Salman, Hazim, Tariq, Khalid, Tahir, …):

- **Trainset.** ≥ 30 recent operator turns where that agent was the primary respondent. Pulled from
  EVENT_LEDGER + the agent's session folder.
- **Feedback corpus.** All `/feedback` items tagged with that agent (e.g., `agent:Hazim ...`) plus
  general `voice`/`values` feedback tagged "applies broadly."
- **Persona invariants.** The 14 soul fields of the agent's persona file. GEPA may **not** propose
  changes to invariants; the optimizer's search space is bounded to the prompt template plus
  optional few-shot exemplars.

## The loop

```text
                  +---- collect_window (7 days of operator interaction)
                  v
[capture]  ---> [feedback corpus]
                  v
            +---- dspy.GEPA(metric=natural_lang_feedback)
            |              |
            |              v
            |     [candidate prompts on Pareto frontier]
            |              v
            |     [Hazim red-teams each candidate vs persona invariants]
            v              v
       LEARNING_LEDGER  [proposals dossier] --> Operator (Telegram)
                                                 v
                                            C1: /go | /halt
                                                 v
                                          adopt or discard
```

## Cadence

- **Once per week**, Khaldun runs one GEPA cycle.
- The cycle is **scoped to one pillar agent per week** to keep the operator's review load tractable.
- A full pass through 8 pillars takes ~2 months; the loop is intentionally slow.

## Constraints

1. **Persona invariants are sacred.** GEPA's search space excludes any field listed in the
   persona's `voice_constraints`, `opening_voice`, `outputs`, or `gates` sections. Hazim verifies
   each candidate.
2. **Cost ceiling.** A single GEPA cycle may not exceed $5 in LLM spend. Cost ceiling enforces
   this; over-budget cycles abort and emit a DEAD_LETTER row.
3. **Operator-only adoption.** Khaldun never auto-adopts. Always proposes; operator confirms.
4. **Signed adoption.** When the operator confirms, the adopted prompt is written with a
   `gepa_signature` field in `version_meta` so future audits can trace lineage.
5. **Rollback path.** Every adoption MAKHZAN-snapshots the prior prompt; one `/rollback <agent>`
   command reverts to the previous version.

## Schema interaction

- **Trainset / feedback corpus.** Derived from EVENT_LEDGER + per-agent session folders. No new
  schema needed.
- **Proposals.** Written as `LEARNING_LEDGER` rows with `kind=gepa_proposal`, `actor=Khaldun`,
  payload includes the diff against the prior persona snapshot.
- **Adoption.** Updates the persona file's `prompt_template` field and bumps version_meta. The
  v1.1 runtime block is untouched.

## Honcho interplay (E2.6)

When Honcho is online, Khaldun MAY consult the Dialectic API to ground each candidate against the
operator's current peer profile. Honcho's response becomes another input to GEPA's metric.

## Acceptance

Spec is complete (this document) — implementation lands after the Honcho spike has produced ≥ 4
weeks of operator interaction, ensuring enough data for the first GEPA cycle.
