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
entry_point: "cd MARSAD__flight_radar && python -m radar.main seed --file <path>"
run_frequency: once_on_init (or when new historical data is available)
observation_type: historical_seed
---

## For future Claude

SEED is the historical data import tool for MARSAD. It reads a CSV or JSON file of historical flight prices and imports them as `observation_type: historical_seed` observations. This accelerates the forecasting model from LOW confidence to MEDIUM (7+ observations) or HIGH (30+ observations) without waiting for the daily monitor to accumulate data over 7–30 days.

All imported observations pass through the routing constraint engine (`apply_constraints()`) before being stored. Economy fares, itineraries over 30 hours, durations outside 9–14 nights, and dates outside the travel window are all silently filtered.

## When to use

- On first deployment: seed with 1–3 months of historical Google Flights price history (manually transcribed)
- When adding a new route: seed with available historical context before starting daily monitoring
- After a long monitoring gap: seed any manually collected prices to fill the gap

## Procedure

1. Check HIMAYAH: confirm `.env` is not staged and `data/` is gitignored.
2. Prepare seed file (CSV or JSON — see format below).
3. Dry run to validate:
   ```
   python -m radar.main seed --file /path/to/history.csv --dry-run
   ```
4. Check output for rows_skipped_constraint and rows_skipped_error.
5. Import for real:
   ```
   python -m radar.main seed --file /path/to/history.csv
   ```
6. Run `/marsad-forecast` to update confidence levels and activate BUY_SIGNAL eligibility.
7. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"seed_run","observations_imported":<n>,"rows_skipped":<n>}`

## CSV format

Required columns (header row required):

```
origin,destination,carrier,cabin,price_usd,outbound_date,return_date,outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,outbound_routing,return_routing,source
```

Optional columns: `price_egp`, `price_eur`

Example row:
```
CAI,JFK,EK,BUSINESS,3200.00,2027-04-15,2027-04-26,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI,historical_seed
```

## JSON format

Top-level array of objects with the same field names as CSV:

```json
[
  {
    "origin": "CAI", "destination": "JFK", "carrier": "EK", "cabin": "BUSINESS",
    "price_usd": 3200.00, "outbound_date": "2027-04-15", "return_date": "2027-04-26",
    "outbound_duration_hours": 14.5, "return_duration_hours": 15.0,
    "outbound_stops": 1, "return_stops": 1,
    "outbound_routing": "CAI-DXB-JFK", "return_routing": "JFK-DXB-CAI",
    "source": "historical_seed"
  }
]
```

## Historical price sources

See `MARSAD__flight_radar/README.md` → Historical Price Seed Research for documented sources.
