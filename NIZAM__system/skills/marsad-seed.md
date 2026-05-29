---
name: marsad-seed
module: MARSAD
trigger: "/marsad-seed"
target_folder: MARSAD__flight_radar/data/
naming_pattern: "flight_prices.json (append-only — historical_seed observations appended)"
template: null
frontmatter_schema: flight_price_observation.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
entry_point: "cd MARSAD__flight_radar && python -m radar.main seed-csv --file <path.csv>"
run_frequency: once (or as needed to import new historical data)
observation_type: historical_seed
---

## For future Claude

SEED is the historical price importer for MARSAD. It accelerates the forecasting cold-start
period by importing manually collected historical prices into the schema store. Without seed
data, the forecasting model runs in LOW confidence (BUY_SIGNAL hard-gated to False) for the
first 7 days of monitoring. With ≥7 seeded observations, the model exits cold-start immediately.

Imported observations are tagged `observation_type: "historical_seed"` and `data_quality: "estimated"`.
They contribute to percentile calculations and forecasting but are clearly distinguished from
live monitored prices (`observation_type: "daily"` or `"baseline"`).

## Procedure

1. Generate a template CSV:
   `python -m radar.main seed-csv --export-template ~/marsad_seed_template.csv`

2. Fill in the template with historical prices. Sources in priority order:
   - **Google Flights price history**: google.com/flights → select route + cabin → "Price history" chart
     → manually transcribe monthly price points
   - **Kayak price trend**: kayak.com → search route → "Price Trend" tab → transcribe 6-month history
   - **Hopper**: mobile app → Watch a trip → price history → transcribe
   - **SerpApi chart endpoint**: engine=google_flights_chart (Economy fares only — less useful for Business)

3. Validate before importing (dry run):
   `python -m radar.main seed-csv --file ~/marsad_seed_template.csv --dry-run`
   - Review rejected rows and their constraint failure reasons.

4. Run the import:
   `python -m radar.main seed-csv --file ~/marsad_seed_template.csv`

5. Run FORECAST to activate updated confidence levels:
   `python -m radar.main forecast`

6. Check ALERT — if ≥7 observations now exist for any series, BUY_SIGNAL becomes eligible:
   `python -m radar.main alert`

7. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"seed_run","rows_imported":<n>,"rows_rejected":<n>,"baseline_accelerated":<bool>}`

## CSV Template Format

Minimum required columns:
```
carrier,cabin,outbound_date,return_date,price_usd,
outbound_duration_hours,return_duration_hours,
outbound_stops,return_stops,outbound_routing,return_routing,source_name
```

Optional: `price_egp`, `price_eur`

All routing constraints are enforced during import — rows that fail are rejected and logged:
- Origin extracted from `outbound_routing` (first segment) — must be CAI
- Destination extracted from `outbound_routing` (last segment) — must be a USA major airport
- Cabin: BUSINESS or PREMIUM_ECONOMY only
- Trip duration: 9–14 nights
- One-way flight time: ≤30 hours each leg (INDEPENDENT constraint)
- Outbound date: within RADAR_WINDOW_START → RADAR_WINDOW_END

## Notes

- Append-only invariant applies: existing observations are never overwritten by seeding
- The CSV may contain data for any number of routes/carriers/cabins — one row per price point
- `source_name` in the CSV should identify the actual source (e.g. "google_flights", "kayak", "hopper", "manual")
- Historical prices from 2024/2025 for the same seasonal window (March–September) can be useful
  as directional benchmarks even though exact prices will differ in 2027
- ASSUMED_PASS_PENDING_ENVIRONMENT: SerpApi chart endpoint (engine=google_flights_chart) has not
  been tested for Business/Premium Economy cabin filtering — verify before using as primary seed source
