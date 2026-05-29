# Protocol — Monthly Close (~60 min, 1st of month)

> Finance milestone check. Body trend over 4 weeks. AHEL cadence sanity. Pivot opportunity assessment.

## Frontmatter
- **Cadence**: 1st of every month (or first workday)
- **Budget**: ~60 minutes total
- **Gates checked**: HIMAYAH (finance, family), SUKOON, THABAT
- **Skills chained**: `/mal-exchange-rate-check` → `/mal-milestone-check` → BADAN monthly trend → `/ahel-connection-cadence` → optional pivot consideration

## Procedure

### Step 1 — `/mal-exchange-rate-check` (2–3 min)
Fetch EGP↔USD from ≥2 sources. Snapshot to `MAL__financial_engine/exchange_rate_log.jsonl`. Use median.

### Step 2 — `/mal-milestone-check` (~15 min)
Compute 3-month rolling average USD/mo. For each ladder rung ($1.5k / $3k / $5k / $7.5k / $10k+):
- Status: locked / pending / at_risk / achieved.
- Evidence (specific FINANCE_LEDGER entries).
- Primary pathway driving this rung.
- Next action.
- Review date.

If a rung transitions, append `FINANCE_LEDGER` entry with `event_type: "milestone_check"`.

### Step 3 — monthly finance review (~15 min)
Use `monthly_review.template.md`:
- Income actual vs plan.
- Expense actual vs plan.
- Pipeline updates (stage change, EV refresh).
- Next month emphasis: 1 priority pathway, 1 expense to cut, 1 recovery flag.

Write `MAL__financial_engine/monthly_reviews/{YYYY-MM}.md`.

### Step 4 — BADAN monthly trend (~10 min)
Aggregate 4 weekly reviews. Spot patterns:
- Sleep quality direction (improving / stable / declining over 4 weeks).
- Weight trend (only over 30-day window — not 7-day).
- Training/recovery balance pattern.
- Red flags raised: re-verify followed up.

### Step 5 — `/ahel-connection-cadence` review (~10 min)
- Who did you reach in the past month?
- Who is `strong` status but neglected? (Strong relationships under-served is a slow erosion.)
- Are any cadence settings creating unintended pressure? Adjust.

### Step 6 — pivot opportunity assessment (~5–10 min, optional)
Has any TARIQ pillar shown evidence-based weakness this month? Candidate for `/munawara-pivot`? If so, schedule the pivot conversation explicitly — don't pivot on a Sunday.

## Anti-patterns
- Promoting a finance rung after one good month — wait the 3-month rolling window.
- Pivoting strategy on emotional reasons without evidence — pivots require evidence + rollback option.
- Treating AHEL like a checklist — relationships aren't task completion.

## Output
- 1 milestone check in `MAL/baseline/`
- 1 monthly review in `MAL/monthly_reviews/`
- BADAN monthly trend notes (free-form, in `BADAN/weekly_reviews/` with monthly cross-reference)
- Optional pivot record if triggered
- Multiple FINANCE_LEDGER appends
