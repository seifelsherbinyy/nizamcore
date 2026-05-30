---
name: marsad-seed-history
module: MARSAD
trigger: "/marsad-seed-history"
target_folder: MARSAD__flight_radar/data/
naming_pattern: "flight_prices.json (append-only — historical_seed observations prepended)"
template: null
frontmatter_schema: flight_price_observation.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
entry_point: "cd MARSAD__flight_radar && python -m radar.main seed-history"
run_frequency: once_before_discover (or as needed to add historical depth)
observation_type: historical_seed
---

## For future Claude

SEED_HISTORY is Stage 0 of MARSAD — run before or alongside DISCOVER to import historical
price data from external sources. It accelerates the forecasting cold start by providing
the 7+ observations needed for MEDIUM confidence and BUY_SIGNAL eligibility from day one,
rather than waiting 7 days of daily monitoring.

Historical seed observations use `observation_type: "historical_seed"` and `data_quality: "estimated"`
(for manual sources) or `data_quality: "confirmed"` (for SerpApi historical). The append-only
invariant is maintained — no existing observations are modified.

## Procedure: Option A — Manual CSV/JSON import

1. Collect historical prices from any of these sources:
   - Google Flights calendar view (3–6 month depth, manual capture)
   - Hopper app price history chart (12 month depth, manual capture)
   - Kayak price history charts (3 month depth, manual capture)
2. Create a CSV file with headers:
   `origin,destination,carrier,cabin,outbound_date,return_date,price_usd,outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,outbound_routing,return_routing,source,data_quality`
3. Check HIMAYAH: confirm `.env` not staged, `data/` gitignored.
4. Run: `python -m radar.main seed-history --file path/to/seed.csv --dry-run` to preview.
5. Run: `python -m radar.main seed-history --file path/to/seed.csv` to import.
6. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"seed_history","source":"manual","imported":<n>,"filtered":<n>}`

## Procedure: Option B — SerpApi historical fetch (programmatic)

1. Confirm SERPAPI_KEY is set in `.env`.
2. Run: `python -m radar.main seed-history --serpapi-historical --months-back 3 --dry-run`
   to see what would be fetched (quota: ~144 searches for 3 months).
3. Run: `python -m radar.main seed-history --serpapi-historical --months-back 3`
4. Append THABAT event:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"seed_history","source":"serpapi_historical","months_back":3,"imported":<n>}`

## Available Historical Sources

| Source | Depth | Access | Quality |
|---|---|---|---|
| Google Flights calendar | 3–6 months | Manual UI capture | Confirmed |
| Hopper app | 12 months | Manual app capture | Estimated |
| Kayak price history | 3 months | Manual UI capture | Estimated |
| SerpApi historical | 3–6 months | Programmatic (quota) | Confirmed |

## Notes

- All records filtered through routing constraint engine before import
  (origin=CAI, valid destination, BUSINESS or PREMIUM_ECONOMY, 9–14 nights,
   ≤30h one-way, within travel window)
- Routing constraint filter: travel window check passes for historical dates
  ONLY if constraints.py is configured to allow historical observations.
  Historical dates outside the 2027 window WILL be filtered — this is by design.
  Use historical data primarily for relative price intelligence, not 2027-date-specific.
- Recommended minimum seed: 7 observations per series to exit cold start
- After seeding, run `/marsad-forecast` to update forecast blocks with the new data
