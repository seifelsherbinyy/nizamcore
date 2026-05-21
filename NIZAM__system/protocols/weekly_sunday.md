# Protocol — Weekly Sunday (~30 min)

> Synthesize the week. Plan the next. Audit drift. Recovery-first overrides ambition.

## Frontmatter
- **Cadence**: Sunday evening (or Saturday for Friday-Saturday weekenders)
- **Budget**: ~30 minutes total
- **Gates checked**: SUKOON (each step), THABAT (each step)
- **Skills chained**: `/pop-recap` → (optional `/nizam-almanac`) → `/munawara-weekly-battle` → `/badan-weekly-review` → `/pop-health`

## Procedure

### Step 0 — SUKOON downshift check (1 min)
Read `SUKOON__recovery_first/overload_flags.jsonl` over last 7 days. Count red flags.
- **0 red** → full protocol.
- **1 red** → skip Step 4 (health audit) if time-stressed.
- **≥2 red** → mandatory downshift in Step 2; consider deferring the protocol entirely if recovery debt is acute.

### Step 1 — `/pop-recap` (~10 min)
Synthesize the week from ledgers (EVENT / DECISION / LEARNING).
- Activity counts per module.
- Recovery trend (green/yellow/red day count).
- Top 3 wins, top 3 frictions, recurring themes.
- 3 priorities for next week, 1 to defer, 1 to delete.

### Step 1b — `/nizam-almanac` (optional, ~5 min)
Interpretive weekly review from `YAWMIYAT__journaling/sessions/*.json`: KPIs, blockers, felt-vs-SUKOON divergences, B=MAP themes, one redesign action. Complements Step 1 — does not replace `/pop-recap`.

### Step 2 — `/munawara-weekly-battle` (~10 min)
Apply the Dynamic War Strategy protocol:
1. SUKOON downshift check (if ≥2 red flags → cut battle count 50%).
2. Exploit opportunity surfaced this week.
3. Concentrate force on one biggest leverage move.
4. Defend recovery.
5. Retreat intelligently from a failing battle.
6. Reallocate time / money / attention.
7. Update quarter/month/week targets.

Write `MUNAWARA__tactical_strategy/weeks/{YYYY-Wnn}.md`. Append outcomes from this week to `BATTLE_LEDGER.jsonl`.

### Step 3 — `/badan-weekly-review` (~5 min)
Trend-based body review (7-day moving avg). Nutrient coverage estimate. Training/recovery balance. Red flags raised this week.

Always emits: *"Advisory only — not medical diagnosis."*

### Step 4 — `/pop-health` (~5 min)
Audit POP itself:
- Stale claims (`updated:` > 90 days, `confidence: high`).
- Orphan notes (no backlinks).
- Contradictions (cross-grep opposing claims).
- Schema violations.
- Orphan strategic goals (KABIR_SHERBO objectives without MUNAWARA roll-down).
- Ledger sanity (which haven't grown in 7+ days).

Write audit to `NIZAM__system/docs/health_audit_{YYYY-MM-DD}.md`.

## Anti-patterns
- Running full protocol after a red-flag week — that's punishment masked as discipline. Defer or downshift.
- Skipping `/pop-health` consistently — drift accumulates silently.
- Treating "battles" as moral measurements — they're tactical outcomes, not character verdicts.

## Output
- 1 recap file in `SHURA/sessions/`
- 1 weekly battle file in `MUNAWARA/weeks/`
- 1 weekly review in `BADAN/weekly_reviews/`
- 1 health audit in `NIZAM/docs/`
- Multiple ledger appends (BATTLE, BODY, EVENT)
