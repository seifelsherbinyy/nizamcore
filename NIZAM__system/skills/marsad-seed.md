---
name: marsad-seed
module: MARSAD
trigger: "/marsad-seed"
target_folder: MARSAD__flight_radar/data/
naming_pattern: "flight_prices.json (append-only — historical_seed observation_type)"
template: null
frontmatter_schema: flight_price_observation.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
entry_point: "cd MARSAD__flight_radar && python -m radar.main seed --csv <path>"
run_frequency: once (before DISCOVER, or when manual historical data becomes available)
observation_type: historical_seed
---

## For future Claude

SEED is Stage 0 of MARSAD — it imports historical price data from an external CSV or
JSON file before the daily monitor has accumulated 30+ days of organic observations.
This seeds the forecasting model so it can produce MEDIUM/HIGH confidence outputs from
day one instead of waiting through a 30-day cold start.

Run this ONCE before DISCOVER, or whenever you acquire a significant batch of historical
price data from Google Flights price history, Kayak price history, or any other source.

## Procedure

1. Prepare a seed CSV with columns:
   `route, carrier, cabin, outbound_date, return_date, price_usd, source,
    outbound_duration_hours, return_duration_hours, outbound_stops, return_stops,
    outbound_routing, return_routing`
2. Dry-run first to validate:
   `python -m radar.main seed --dry-run --csv path/to/history.csv`
3. Verify the output counts: rows_parsed, rows_filtered, rows_imported.
4. If rows_filtered is unexpectedly high — check constraint violations (cabin, window, duration).
5. Run live import:
   `python -m radar.main seed --csv path/to/history.csv`
6. Confirm import via `python -m radar.main status`.
7. Run `/marsad-forecast` immediately after seed to compute initial forecast baselines.
8. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"seed_import","rows_imported":<n>,"rows_filtered":<n>}`

## Historical Data Sources

| Source | Depth | Access | Quality |
|---|---|---|---|
| Google Flights price history | ~12 months via price graph | Manual export only | High |
| Kayak price history charts | ~60 days per route | Manual / "Export CSV" | Medium |
| Hopper "Watch this trip" | 90 days per device | No export | Cross-validation only |
| SerpApi daily fetches | Accumulates with MONITOR | Programmatic | High |

## Notes

- Seed data is tagged `observation_type: historical_seed` — distinguishable from live data.
- The constraint engine filters every row before import — invalid dates, cabin, duration are skipped.
- Append-only invariant holds: existing observations are never overwritten by seed data.
- After seeding 30+ observations per series, the forecasting model upgrades from SMA → LR.
- JSON format also accepted: `python -m radar.main seed --json-file path/to/history.json`
