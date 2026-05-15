---
type: misc
pop_module: MAL
pop_privacy: strict_local
updated: <YYYY-MM-DD>
confidence: high
tags: [finance_baseline]
recency_anchor: "<YYYY-MM>"
---

## For future Claude
Finance baseline snapshot. Schema: `NIZAM__system/schemas/finance_baseline.schema.json`. EGP + USD with verified exchange rate.

# Finance Baseline — <YYYY-MM-DD>

> **Disclaimer**: Personal financial tracking, not professional financial advice. For major decisions, consult a qualified financial advisor.

## Exchange rate
- Verified: <true/false>
- Sources used: <list, e.g., XE, CBE>
- Median EGP per USD: <number>
- Median USD per EGP: <number>
- Log entry: `MAL__financial_engine/exchange_rate_log.jsonl` line <N>

## Income
- Stable gross monthly (EGP):
- Stable net monthly (EGP):
- Stable net monthly (USD equiv):
- Variable monthly avg (EGP):
- One-off recent (EGP):

## Fixed costs (monthly, EGP)
- Rent / housing:
- Utilities:
- Transport:
- Subscriptions:
- Insurance:
- Other:
- **Total fixed**:

## Variable costs (monthly avg, EGP)
- Food:
- Personal:
- Family support:
- Other:
- **Total variable**:

## Debt
| Name | Principal (EGP) | Rate % | Term months | Min payment |
|---|---|---|---|---|

## Savings
- Liquid (EGP):
- Investment (EGP):

## Assets
| Name | Category | Value (EGP) |
|---|---|---|

## Liabilities
| Name | Value (EGP) |
|---|---|

## Runway
- liquid_savings / monthly_burn = <X months>

## Skill assets (monetizable)
-

## Business pipelines
| Name | Stage | Expected value USD/mo | Effort hours/week |
|---|---|---|---|

## FINANCE_LEDGER event
`{"event_type":"baseline_snapshot","privacy_level":"strict_local","summary":"baseline at <date>"}`
