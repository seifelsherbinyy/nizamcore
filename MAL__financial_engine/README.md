# MAL — Financial Engine

Arabic: مال — "wealth / money."

## Purpose
Personal financial analyst. Track baseline, model scenarios, check milestone ladder progress, verify exchange rates, score decisions.

**Baseline at Phase 2 start**: ~47,000 EGP/mo (~$900 USD/mo, rate-dependent).
**Target**: stable >$10,000 USD/month via the milestone ladder.

## Skills
- `/mal-baseline` — snapshot current financial state.
- `/mal-scenario <pathway>` — what-if income/expense model.
- `/mal-milestone-check` — ladder progress with 3-month rolling avg evidence.
- `/mal-exchange-rate-check` — verify EGP↔USD rate from ≥2 sources, log to `exchange_rate_log.jsonl`.
- `/mal-decision-score <topic>` — 7-factor scoring (EV, effort, risk, cashflow, skill leverage, ethical fit, recovery cost).

## Milestone ladder
$1,500 → $3,000 → $5,000 → $7,500 → $10,000+ /month. Promotion criterion: 3-month rolling avg ≥ target.

## Subfolders
- `baseline/` — snapshots + milestone checks.
- `income_growth/` — 7 pathways (salary_growth, gcc_or_remote_role, business_income, affiliate_or_performance_marketing, consulting, investment_income, automation_products).
- `business_pipelines/` — active business pipelines.
- `expenses_debt_assets/` — granular tracking.
- `monthly_reviews/` — actual vs plan per month.
- `scenario_models/` — what-if models per pathway.
- `exchange_rate_log.jsonl` — verified rate snapshots (append-only).

## Sibling repo reference
[`goldminer`](https://github.com/seifelsherbinyy/goldminer) (MIT) implements Python ETL for personal finance. Consider as upstream library or pattern source when ingesting transaction data.

## PFA — Personal Financial Assistant subsystem

The `pfa/` subfolder holds the consolidated personal financial position:
- `canonical_state.json` — single source of truth (strict_local)
- `ledgers/` — append-only debt events, payments, decisions (strict_local)
- `learnings_log.jsonl` — continuous life-learning capture (strict_local)

Debt architecture tracks: HSBC credit cards (recycling-eligible when current), Halan/Valu/TRU/Souhoola (all BNPL pure-installment — no recycling), and family loans. See [`pfa/README.md`](pfa/README.md) for the full runbook.

Schemas: `pfa_canonical_state`, `pfa_debt_event`, `pfa_payment_event`, `pfa_learning` in `NIZAM__system/schemas/`.

## Doctrine
[`NIZAM__system/docs/MAL_FINANCIAL_LADDER.md`](../NIZAM__system/docs/MAL_FINANCIAL_LADDER.md)

## Disclaimer
Personal financial tracking, not professional financial advice. Decisions affecting major life outcomes warrant a qualified financial advisor.

## Privacy
**strict_local.** All financial data `.gitignored`.
