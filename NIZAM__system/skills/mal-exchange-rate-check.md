---
name: mal-exchange-rate-check
module: MAL
trigger: "/mal-exchange-rate-check"
target_file: MAL__financial_engine/exchange_rate_log.jsonl
required_sources_minimum: 2
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
---

## For future Claude

Verify the current EGP↔USD exchange rate from ≥2 sources before any decision-grade conversion. Append snapshot to `exchange_rate_log.jsonl`. Use median for the calculation.

## Procedure

1. Fetch current EGP/USD rate from at least 2 of these sources (or others credible):
   - XE.com
   - Central Bank of Egypt (CBE)
   - Wise / Remitly
   - Google Finance
2. Compute median rate.
3. Append a line to `MAL__financial_engine/exchange_rate_log.jsonl`:
   `{"ts":"<ISO8601_UTC>","sources":[{"name":"XE","egp_per_usd": <num>},{"name":"CBE","egp_per_usd": <num>}],"median_egp_per_usd": <num>,"median_usd_per_egp": <reciprocal>,"used_for":"<optional context>"}`
4. Return the median rate + acknowledge "rate_verified: true" status.
5. If only 1 source available, return rate with `rate_verified: false` and tell user the limitation.
6. Append THABAT event to EVENT_LEDGER.

## Disclaimer

Exchange rates fluctuate. For transactions > $1k, re-verify within the same hour.
