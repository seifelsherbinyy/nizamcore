# Workflow — Finance Decision

> Scenario: a financial decision is forming. Run through MAL's stack before committing.

## Skill chain
1. `/mal-exchange-rate-check` — if any EGP↔USD conversion involved
2. `/mal-baseline` — if last baseline > 30 days old
3. `/mal-scenario "<pathway>"` — model low/expected/high outcomes
4. `/mal-decision-score "<decision>"` — 7-factor scoring, ethical_fit and recovery_cost as vetoes
5. `/qarar-decide "<decision>"` — record as ADR
6. `/mal-milestone-check` — does this move the ladder?

## When to use
- Income pathway shifts (taking a remote role, starting a side business)
- Investments > $1k impact
- Recurring expense changes ($100+/mo)
- Career moves with compensation impact
- Major purchases

## Procedure

### Step 0 — privacy reminder
MAL is **strict_local**. Every output stays on disk. The decision artifact itself can be a QARAR ADR (review_before_commit) — but financial figures stay in MAL.

### Step 1 — Exchange-rate verification (mandatory for cross-currency)
`/mal-exchange-rate-check`. Two sources minimum. Median. Snapshot to `MAL/exchange_rate_log.jsonl`. **Decision-grade math requires `rate_verified: true`.**

### Step 2 — Baseline freshness check
If last `MAL/baseline/baseline_*.md` is > 30 days old, run `/mal-baseline` first. Decisions on stale baselines are wishful thinking.

### Step 3 — Scenario modeling
`/mal-scenario "<pathway>"` where pathway is one of MAL's 7:
- salary_growth / gcc_or_remote_role / business_income / affiliate_or_performance_marketing / consulting / investment_income / automation_products

Output: low/expected/high USD outcomes + effort hours + risk level + reversibility + cashflow timing + skill leverage + ethical fit + recovery cost.

### Step 4 — 7-factor decision score
`/mal-decision-score "<decision>"`. Veto rules:
- ethical_fit < 3 → veto regardless of EV.
- recovery_cost < 3 (red) → veto OR mandatory downshift to smaller version.

### Step 5 — QARAR record
`/qarar-decide "<decision>"`. Includes review date — date when you re-check whether the actual outcome matches the modeled outcome.

### Step 6 — Milestone check (post-decision)
After the decision is executed and 3 months pass, run `/mal-milestone-check`. Did this move the ladder rung? Update status.

## Variations

### Quick estimate (non-decision-grade)
For "should I take this taxi or Uber" type questions: skip Step 1, 2, 3, 4. Mental math is fine. Tag any captured note with `rate_verified: false`.

### Multi-pathway comparison
For "salary growth at current vs. GCC remote role" type: run `/mal-scenario` twice, once per pathway. Compare scenarios side-by-side in the QARAR record.

### Multi-year financial commitment (mortgage, etc.)
Add an explicit roll-up reference to TARIQ 10-yr wealth domain in the QARAR record. Schedule a NAQD grill at month 6 of the commitment.

## Anti-patterns
- Skipping exchange-rate verification because "the rate is roughly X" — when EGP fluctuates 10%+ in a quarter, "roughly" produces wrong decisions.
- Running scenario modeling but ignoring recovery_cost — leads to financially correct, recovery-bankrupt outcomes.
- Promoting a milestone rung after one good month — wait the 3-month rolling window.

## Output
- Optional new exchange_rate_log line
- Optional new MAL baseline
- 1 MAL scenario model
- 1 MAL decision score
- 1 QARAR ADR
- Optional MAL milestone update
- FINANCE_LEDGER entries throughout
