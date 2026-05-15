# MAL Financial Ladder Doctrine

> $900/mo baseline → $10k+/mo target via staged milestones, evidence-based promotion, exchange-rate verification, and 7-factor decision scoring.

## Baseline as of Phase 2 start
- Stable salary: ~47,000 EGP/month ≈ ~$900/month (rate-dependent).
- Source: user-provided 2026-05-15.
- **Decision-grade conversion always re-verifies the rate** via `/mal-exchange-rate-check`.

## Milestone ladder (USD per month)

| Rung | Target USD/mo | Promotion criterion |
|---|---|---|
| 1 | $1,500 | 3-month rolling avg ≥ $1,500 |
| 2 | $3,000 | 3-month rolling avg ≥ $3,000 |
| 3 | $5,000 | 3-month rolling avg ≥ $5,000 |
| 4 | $7,500 | 3-month rolling avg ≥ $7,500 |
| 5 | $10,000+ | 3-month rolling avg ≥ $10,000 |

A rung is **`locked`** only when the 3-month rolling average sustains the target. Single-month spikes do not count. This prevents premature ambition.

## Seven income pathways

Documented in `MAL__financial_engine/income_growth/`:
1. `salary_growth/` — current employer, negotiation, promotion track.
2. `gcc_or_remote_role/` — relocation or remote-first role at higher comp.
3. `business_income/` — owned product or service business.
4. `affiliate_or_performance_marketing/` — commission-based marketing.
5. `consulting/` — sold expertise hourly or per project.
6. `investment_income/` — passive yield from invested capital.
7. `automation_products/` — software / SaaS / agent products.

Each pathway gets a scenario model (`/mal-scenario`) with low / expected / high USD outcomes, effort, risk, reversibility, cashflow timing, skill leverage, ethical fit, and recovery cost.

## 7-factor decision scoring

For any income / investment / career move, run `/mal-decision-score`:
1. **Expected value** (probability × payoff)
2. **Effort** (lower = better)
3. **Risk** (lower = better)
4. **Cashflow timing** (sooner = better)
5. **Skill leverage** (uses existing strengths)
6. **Ethical fit** (cross-check `SOUL.md` non-negotiables)
7. **Recovery cost** (lower = better; red on SUKOON = veto or downshift)

**Veto rule**: ethical_fit < 3 OR recovery_cost < 3 (red) = no-go regardless of other scores.

## Exchange-rate audit trail

Every decision-grade EGP↔USD conversion calls `/mal-exchange-rate-check` first:
- ≥ 2 sources (XE, CBE, Wise, Google Finance, etc.).
- Snapshot to `MAL__financial_engine/exchange_rate_log.jsonl`.
- Use median for the calculation.
- `rate_verified: true` mandatory on baseline / milestone / scenario entries that drive decisions.
- Non-decision-grade quick estimates can have `rate_verified: false`.

## Reference patterns from sibling repo `goldminer`

`github.com/seifelsherbinyy/goldminer` (MIT) already implements:
- Python ETL pipeline for CSV/Excel transaction ingestion.
- Anomaly detection via Z-score and IQR.
- Moving-average trend analysis.
- Excel export with professional formatting.

**When MAL Phase 2 ingests transaction data**, consider:
- (a) Re-implementing as Python-callable MAL skills, OR
- (b) Treating `goldminer` as an upstream library and calling it from MAL skill procedures, OR
- (c) Cherry-picking specific schemas/algorithms with attribution.

Decision is deferred to a `/qarar-decide` session at the time of first transaction-data ingestion.

## Privacy

MAL is **strict_local**. Every output includes the disclaimer:
> "Personal financial tracking, not professional financial advice. Decisions affecting major life outcomes warrant a qualified financial advisor."

## Anti-patterns

- Promoting a rung after one good month → wait 3 months.
- Using an unverified exchange rate for decision-grade EGP↔USD math.
- Choosing a pathway with red recovery_cost just because EV is high.
- Adding new pathways without retiring failed ones — pathway sprawl.
