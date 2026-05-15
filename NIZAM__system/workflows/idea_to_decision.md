# Workflow — Idea → Decision

> Scenario: a notable decision is forming. Take it through the full cognitive stack before committing.

## Skill chain
1. `/tafrigh-capture` — surface the idea fully
2. `/shura-brainstorm "<topic>"` — co-think, vault-first research
3. `/naqd-grill "<topic>"` — stress-test, get confidence score
4. `/qarar-decide "<topic>"` — record as ADR
5. Append to `DECISION_LEDGER.jsonl`

## When to use
- Career moves (taking a role, leaving a role)
- Major financial decisions (>$1k impact)
- Relationship boundaries
- Strategic pivots before they reach `/munawara-pivot`
- Any decision you'd regret making at 11 PM under pressure

## Procedure

### Step 1 — Capture the raw idea
`/tafrigh-capture` — get it out of your head. No filtering. Look for: emotions attached, assumptions made, what's NOT being said.

### Step 2 — SHURA brainstorm
`/shura-brainstorm "<one-line title>"`. SHURA runs vault-first research: scans POP for anything you've previously captured on this topic. Produces a delta report — what's new vs. what's already in your notes.

Output: options + tradeoffs + recommendation + next actions + research questions.

### Step 3 — NAQD grill (if confidence still < 7/10)
`/naqd-grill "<topic>"`. NAQD's emotional-state gate fires first — if SUKOON is red, switches to Supportive Reflection. Otherwise: weak points → counterarguments → pressure-test questions → defense strategy → revised position → confidence score.

If the revised position survives critique, you have a defensible decision.

### Step 4 — QARAR decide
`/qarar-decide "<topic>"`. ADR format:
- Title
- Status (proposed / accepted / superseded)
- Context
- Decision
- Reasoning
- Alternatives considered
- Consequences (positive + negative + **recovery cost**)
- Review date

### Step 5 — Ledger append
DECISION_LEDGER.jsonl gets a structured line with confidence, expected outcome, and review date.

## Variations

### Fast-track (low-stakes decision)
Skip Step 3 (NAQD). Skip Step 5 (ledger). Just `/qarar-decide` directly with what's in your head.

### Slow-track (life-altering decision)
After Step 3, **wait 24–72 hours**. Don't fast-forward to QARAR. Revisit Steps 1–3 with fresh state. Especially if SUKOON was yellow during the first pass.

### Cross-domain decision
For decisions touching multiple POP domains (e.g., a job offer affecting wealth, family, location):
- After Step 2, also run `/shura-connect "[[this idea]]" "[[relevant SOUL.md non-negotiable]]"` to surface conflicts.
- After Step 3, score per `/mal-decision-score` if financial dimension is significant.

## Anti-patterns
- Skipping SHURA and going straight to QARAR — produces shallow decisions.
- Treating NAQD's grill as personal attack — it's testing the idea.
- Recording the decision without the review date — defeats half the value.

## Output
- 1 TAFRIGH capture
- 1 SHURA session
- 1 NAQD session (if used)
- 1 QARAR ADR
- 1 DECISION_LEDGER append
