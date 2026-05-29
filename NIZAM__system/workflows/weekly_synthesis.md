# Workflow — Weekly Synthesis

> Scenario: it's Sunday (or quiet weekend hour) and the week wants to be understood, not just logged.

## Skill chain
1. `/pop-recap` — synthesize the week from ledgers
2. `/shura-emerge` — surface unnamed patterns (last 7–30 days)
3. `/pop-health` — audit POP for drift
4. Optional: `/shura-graduate` for any pattern that has earned promotion

## When to use
- Every Sunday as part of weekly_sunday protocol.
- After a particularly intense week where patterns might be hiding in the noise.
- At month-end / quarter-end to feed bigger reviews.

## How this differs from `/pop-recap` alone
`/pop-recap` is **structural** — it synthesizes ledgers mechanically. This workflow adds the **interpretive** layer: what do those patterns *mean*?

## Procedure

### Step 1 — `/pop-recap` (~10 min)
Mechanical synthesis from EVENT / DECISION / LEARNING ledgers over last 7 days:
- Activity counts per module
- Recovery trend (green/yellow/red day count)
- Top 3 wins, top 3 frictions
- Recurring themes (basic keyword surfacing)
- Next-week priorities

### Step 2 — `/shura-emerge` (~15 min)
30-day window scan across TAFRIGH / SHURA / NAQD / SUKOON. Cluster recurring nouns, verbs, emotions, obligations. Name 3–7 candidate patterns. Tentative labels.

Output: pattern name → ≥3 source files → "is this real or noise?" question.

### Step 3 — User decides which patterns are real
Of the surfaced candidates, the user marks:
- **Real**: deserves a permanent label / dedicated note.
- **Noise**: surfaced for a wrong reason. Discard.
- **Watch**: not yet enough evidence — re-check next week.

### Step 4 — Promote real patterns (optional)
For "real" patterns, run `/shura-graduate "<pattern>"` to promote into HIKMAH (Phase 2) or a dedicated SHURA session for further development.

### Step 5 — `/pop-health` (~5 min)
Audit POP:
- Stale claims (`updated:` > 90 days with high confidence)
- Orphan notes (no inbound or outbound wikilinks)
- Contradictions (cross-grep opposing claims in last 30 days)
- Schema violations
- Orphan strategic goals (TARIQ objectives without MUNAWARA roll-down)
- Ledger sanity (which haven't grown in 7+ days)

Write audit to `NIZAM__system/docs/health_audit_{YYYY-MM-DD}.md`. Recommend specific actions.

### Step 6 — Compress to one paragraph
At the end of synthesis, write ONE paragraph in `log.md` summarizing the week. This is what future-you will skim during the annual review — make it dense.

## Anti-patterns
- Running synthesis on a red SUKOON day — the lens distorts.
- Treating every emerged pattern as real — most are noise. 30% real, 70% noise is a reasonable hit rate.
- Skipping `/pop-health` because "POP is fine" — drift compounds silently.
- Letting the synthesis become its own multi-hour project — 30 minutes max.

## Output
- 1 recap in `SHURA/sessions/`
- 1 emerge session in `SHURA/sessions/`
- 1 health audit in `NIZAM/docs/`
- Optional: graduation artifacts for promoted patterns
- 1 dense paragraph in `log.md`
