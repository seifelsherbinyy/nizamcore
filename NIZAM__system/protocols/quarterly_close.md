# Protocol — Quarterly Close (~2 hours, every 3 months)

> Plan the next quarter. Cross-domain SHURA. KABIR_SHERBO pillar sanity check.

## Frontmatter
- **Cadence**: end of Q1 / Q2 / Q3 / Q4
- **Budget**: ~2 hours total (split across 2 sessions if SUKOON yellow)
- **Gates checked**: SUKOON, THABAT
- **Skills chained**: `/munawara-quarter-plan` → cross-domain `/shura-brainstorm` → KABIR_SHERBO pillar check

## Procedure

### Step 0 — SUKOON check (5 min)
Quarterly planning under red recovery debt is fantasy. If red, defer 1 week. If yellow, split the protocol into 2 sessions across 2 days.

### Step 1 — close out current quarter (~30 min)
- Read `MUNAWARA__tactical_strategy/quarters/{YYYY-Qn}/plan.md`.
- For each objective: status (done / partial / abandoned / deferred), reasoning, evidence.
- Append outcomes to `BATTLE_LEDGER.jsonl` with `event_type: "quarter_outcome"`.

### Step 2 — `/munawara-quarter-plan` for next quarter (~60 min)
Per `quarter_plan.template.md`:
- SUKOON state at planning — explicit.
- Rolls up to: 1_year objective + 3_year + KABIR_SHERBO pillar reference.
- 3–5 objectives. Each with: domain, success criteria, owner, deadline, recovery_cost_estimate, evidence.
- Monthly milestones for each objective (3 months × N objectives).
- Risks for this quarter.
- Battle ledger forecast.

Write to `MUNAWARA__tactical_strategy/quarters/{YYYY-Q(n+1)}/plan.md`.

### Step 3 — cross-domain `/shura-brainstorm` (~30 min)
One topic: "Looking across wealth, career, body, family, faith, learning — what shifted this quarter that should change my approach next quarter?"

Vault-first: scan POP's last-quarter outputs before reaching for external sources.

Write to `SHURA__brainstormer/sessions/{YYYY-MM-DD}__cross_domain_quarterly.md`.

### Step 4 — KABIR_SHERBO pillar sanity check (~15 min)
For each of 3–5 strategic pillars in active KABIR_SHERBO horizons:
- Has progress this quarter been real or theatrical?
- Is the pillar still relevant?
- Should next quarter explicitly stress-test this pillar via `/naqd-grill`?

If any pillar scored < 5 on relevance for a second quarter running, log a `/munawara-pivot` candidate to STRATEGY_LEDGER (not yet a pivot — just a flag).

## Anti-patterns
- Setting 7+ quarter objectives — that's 4 quarters of work in one.
- Skipping the cross-domain SHURA — quarter plans drift narrow without it.
- Defending a failing pillar emotionally — let it surface honestly. NAQD can argue the case in Q+1 if it deserves rescue.

## Output
- 1 new quarter plan in `MUNAWARA/quarters/`
- 1 cross-domain SHURA session
- BATTLE_LEDGER quarter_outcome entries for current quarter
- Optional STRATEGY_LEDGER pivot-candidate flag
- Updated KABIR_SHERBO pillar scorecards (in 10_year/15_year files)
