---
name: marsad-seed
module: MARSAD
trigger: "/marsad-seed"
target_folder: MARSAD__flight_radar/data/
naming_pattern: "flight_prices.json (append-only — historical_seed observations added)"
template: null
frontmatter_schema: flight_price_observation.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
entry_point: "cd MARSAD__flight_radar && python -m radar.main seed --file <path_to_seed_file>"
run_frequency: manual (once, or whenever new historical data is available)
observation_type: historical_seed
---

## For future Claude

SEED is Stage 0 of MARSAD — an optional pre-DISCOVER step that bootstraps the
forecasting model with historical price data before live monitoring has accumulated
7+ observations. Without seed data the model runs in LOW confidence (cold-start)
mode for the first 7 days — BUY_SIGNAL is hard-gated to False during this period.

Importing 7–29 historical observations per series immediately unlocks MEDIUM confidence
and makes the ALERT and FORECAST stages meaningful from day one.

## Supported file formats

**CSV** (recommended):
```
carrier,cabin,origin,destination,outbound_date,return_date,price_usd,outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,outbound_routing,return_routing
EK,BUSINESS,CAI,JFK,2027-04-01,2027-04-12,3200.0,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI
QR,BUSINESS,CAI,JFK,2027-04-01,2027-04-12,3100.0,15.0,14.5,1,1,CAI-DOH-JFK,JFK-DOH-CAI
```

**JSON** (array of objects with same field names as CSV columns)

## Procedure

1. Check HIMAYAH: confirm `.env` is not staged for commit and `data/` is gitignored.
2. Gather historical price data from external sources (see README Historical Seed section):
   - Google Flights price history graph (browser — manual transcription)
   - Hopper app price history (most depth — manual extraction)
   - Kayak price history charts (browser)
3. Format data as CSV or JSON matching the schema above.
4. Run dry-run to validate before writing:
   `python -m radar.main seed --file <path> --dry-run`
5. Review dry-run output — confirm constraint_passed count is as expected.
6. Import (without --dry-run):
   `python -m radar.main seed --file <path>`
7. Check log output for:
   - `records_imported`: successfully imported observations
   - `records_constraint_failed`: records skipped (constraint violations logged)
8. Run `python -m radar.main forecast` after seeding to pre-compute forecast baselines.
9. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"seed_run","records_imported":<n>,"source_file":"<filename>"}`

## Notes

- All seeded observations are stored as `observation_type: "historical_seed"` and
  `source: "historical_seed"` — distinguishable from live monitoring data in the store.
- The append-only invariant is maintained — existing observations are never overwritten.
- Records failing routing constraints (wrong cabin, out-of-window dates, >30h flight
  time, etc.) are logged and skipped — they never corrupt the store.
- After seeding 7+ records per series, run `/marsad-forecast` to compute initial forecasts.
