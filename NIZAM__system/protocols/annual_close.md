# Protocol — Annual Close (~half day, late December)

> Score the year honestly. Identify pivots. Refresh horizons. Feed crystallized lessons to HIKMAH.

## Frontmatter
- **Cadence**: late December (or fiscal year close, or birthday — Seif picks an anchor)
- **Budget**: ~4–6 hours, ideally over 1–2 days
- **Gates checked**: SUKOON, THABAT
- **Skills chained**: `/tariq-annual-review` → `/shura-emerge` → HIKMAH learning capture → optional 10/15/20-yr refresh

## Procedure

### Step 0 — SUKOON state baseline (5 min)
Capture the year-end recovery snapshot. This is the lens through which the rest of the review will be read. A year reviewed under red is a different review than one under green.

### Step 1 — `/tariq-annual-review` (~90 min)
Per `annual_review.template.md`:
- Pillar scorecard (1–10): progress, still-relevant, evidence of feasibility.
- Top 5 wins (with evidence file references).
- Top 5 losses / abandoned (with reasoning).
- Learnings — fed to LEARNING_LEDGER with `category: "principle"`.
- Pivots to consider — pillars scoring < 5 on relevance.
- Next year emphasis (3 priorities).

Write to `TARIQ__long_horizon_strategy/reviews/annual/{YYYY}_annual_review.md`.

### Step 2 — `/shura-emerge` over 365 days (~45 min)
Same as 30-day emerge but with a 365-day window. Look for:
- Patterns that recur quarterly or more.
- Identity-level themes the user hasn't yet labeled.
- "I keep saying I want X but never act on it" type loops.

Write to `SHURA__brainstormer/sessions/{YYYY-MM-DD}__year_emerge.md`.

### Step 3 — HIKMAH crystallization (~30 min)
The year produced learnings. Promote the most valuable into `HIKMAH__learnings/principles/`, `mistakes/`, `patterns/`, or `heuristics/`. These should be the lessons you want to remember in 5 years.

(In Phase 2, HIKMAH skills are shell-only — for now, write directly to the folder with frontmatter per `note_frontmatter.schema.json`.)

### Step 4 — 10/15/20-yr horizon refresh (~60 min)
Re-read TARIQ 10-yr / 15-yr / 20-yr plans. Are they still credible? Update non-negotiables, alliances, decisive battles where evidence warrants.

If a major pivot is needed, schedule `/munawara-pivot` for January, not December — pivots under year-end exhaustion are emotional, not evidence-based.

### Step 5 — December STRATEGY_LEDGER snapshot
Append a `year_closed` event with summary of all pivots considered and which were deferred to January.

## Anti-patterns
- Reviewing the year while exhausted — schedule across 2 days minimum.
- Rewriting the 20-year vision dramatically on December 31 — wait until January, when SUKOON has time to recover.
- Conflating bad year with bad strategy — most year-end failures are execution, not direction.
- Skipping HIKMAH because "I'll remember the lessons" — you won't. Crystallize them.

## Output
- 1 annual review in `TARIQ/reviews/annual/`
- 1 year-emerge SHURA session
- 3–10 new HIKMAH entries
- Updated TARIQ 10/15/20-yr plans (if evidence warrants)
- STRATEGY_LEDGER year_closed event
