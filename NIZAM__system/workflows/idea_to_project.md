# Workflow — Idea → Project

> Scenario: a captured idea has graduated from speculation to something you'd actually execute.

## Skill chain
1. `/tafrigh-capture` (already captured during morning protocol)
2. `/tafrigh-triage` → "Reflect" or "Now" bucket
3. `/shura-graduate "<fragment>"` — promote to full project
4. Route to INTAJ (when Phase 2 INTAJ skills are live) OR to MUNAWARA quarter-plan

## When to use
- A brain dump entry has surfaced 3+ times across separate captures.
- A SHURA session ended with "this is worth doing."
- A NAQD grill confirmed a plan is structurally sound.
- An opportunity surfaced that fits a strategic pillar.

## Procedure

### Step 1 — Confirm graduation criterion
Don't promote every idea. Use one of:
- Recurrence (3+ TAFRIGH mentions in last 30 days).
- Strategic fit (maps to a KABIR_SHERBO pillar).
- Time-bounded opportunity (expires if not acted on this quarter).

### Step 2 — `/shura-graduate "<fragment>"`
Builds the promotion artifact with:
- Objective (one sentence)
- Success criteria (specific, measurable)
- Constraints
- Steps (high-level milestones)
- Owner
- Deadline
- Recovery cost estimate (green/yellow/red)

### Step 3 — Route the project
- **Phase 1** (current): output lives in `SHURA__brainstormer/sessions/{YYYY-MM-DD}__graduate__<slug>.md` with `phase_2_target: "INTAJ__output_engine"` in frontmatter.
- **Phase 2** (when INTAJ skills go live): re-route via future `/intaj-promote` to `INTAJ__output_engine/`.
- **Strategic projects**: also add to MUNAWARA quarter plan via `/munawara-quarter-plan` next quarterly close.

### Step 4 — Set the review trigger
Add a calendar reminder or schedule a `/munawara-weekly-battle` mention to check in 2 weeks.

## Anti-patterns
- Promoting every interesting idea — leads to project sprawl. 80% of TAFRIGH ideas should die in triage.
- Graduating without success criteria — produces drift.
- Skipping the recovery cost estimate — burnout fuel.

## Output
- 1 graduation artifact
- 1 future MUNAWARA quarter-plan entry (in next close)
- Updated frontmatter on source TAFRIGH note
