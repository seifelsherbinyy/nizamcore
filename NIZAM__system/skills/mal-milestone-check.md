---
name: mal-milestone-check
module: MAL
trigger: "/mal-milestone-check"
target_folder: MAL__financial_engine/baseline/
naming_pattern: "milestone_check_{YYYY-MM-DD}.md"
frontmatter_schema: NIZAM__system/schemas/finance_milestone.schema.json
gates: [HIMAYAH, SUKOON, THABAT]
privacy: strict_local
ladder_usd: [1500, 3000, 5000, 7500, 10000]
prerequisite_skills: ["/mal-exchange-rate-check"]
appends_event_to: [NIZAM__system/ledgers/EVENT_LEDGER.jsonl, NIZAM__system/ledgers/FINANCE_LEDGER.jsonl]
---

## For future Claude

Check progress on the $1.5k → $3k → $5k → $7.5k → $10k+ /month milestone ladder. Evidence required at each rung (3-month rolling run-rate).

## Procedure

1. Run `/mal-exchange-rate-check`.
2. Read latest 3 months of `MAL__financial_engine/monthly_reviews/*.md` (or relevant FINANCE_LEDGER entries).
3. Compute current_run_rate_3mo_avg_usd.
4. For each rung (1500, 3000, 5000, 7500, 10000):
   - Status: `locked` (rung achieved sustainably), `pending` (not yet reached), `at_risk` (was at this rung last month, now below), `achieved` (just reached this month).
   - If achieved or locked, capture entry_date, evidence (link to specific FINANCE_LEDGER entries), primary_pathway.
   - Define next_action and review_date.
5. Write `MAL__financial_engine/baseline/milestone_check_{YYYY-MM-DD}.md` with one block per rung.
6. Append FINANCE_LEDGER entry: `event_type: "milestone_check"` with summary of any rung transition.
7. Append THABAT event. Mirror to `log.md` (sanitized: "milestone check completed").

## Disclaimer line (mandatory)

Status transitions require 3-month sustained evidence to call `locked`. Single-month spikes do not count.
