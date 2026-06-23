---
name: marsad-seed
module: MARSAD
trigger: "/marsad-seed"
target_folder: MARSAD__flight_radar/data/
naming_pattern: "flight_prices.json (append-only — historical_seed observations added)"
template: MARSAD__flight_radar/seed_template.csv (generate via seed-template command)
frontmatter_schema: flight_price_observation.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
entry_point: "cd MARSAD__flight_radar && python -m radar.main seed --file path/to/seed.csv"
run_frequency: once (on init to seed historical data) or as-needed when new historical data is available
observation_type: historical_seed
---

## For future Claude

SEED is Stage 0 of MARSAD — the historical data import. It imports price observations from a structured CSV or JSON file into the MARSAD schema store as `observation_type: historical_seed`. Running SEED before starting daily monitoring accelerates the forecasting model from LOW confidence to MEDIUM/HIGH confidence without waiting 7 days.

**Why this matters:** The BUY_SIGNAL is hard-gated to False when `forecast_confidence = LOW` (fewer than 7 observations). Without seed data, MARSAD cannot fire a BUY_SIGNAL for the first 7 days of monitoring. With even 10–20 historical price points per route, the model immediately enters MEDIUM confidence and can fire BUY_SIGNAL from day 1.

## Seed data collection workflow

1. Go to **Google Flights** (google.com/flights)
   - Search CAI → JFK, departure date: 3 months ago, return: 11 nights
   - Click "Price history" below results — note monthly low prices
   - Repeat for: JFK, LAX, MIA, ORD, IAD, BOS (priority destinations)
   - Repeat for BUSINESS and PREMIUM_ECONOMY cabin classes
   - Target: 10–15 historical price points per route-cabin pair over 12 months

2. Also check **Kayak** (kayak.com) → search same routes → "Price Trend" chart
   - Note monthly average and low prices for cross-validation

3. Fill the seed CSV (generate template: `python -m radar.main seed-template`)

4. **Validate before importing:**
   ```
   python -m radar.main seed --file seed_data.csv --dry-run
   ```
   Review constraint failures and parse errors in dry-run output.

5. **Import:**
   ```
   python -m radar.main seed --file seed_data.csv
   ```

6. **Run FORECAST to update confidence levels:**
   ```
   python -m radar.main forecast
   ```
   Series with 7+ historical seed observations will now show MEDIUM confidence
   and can fire BUY_SIGNAL immediately when the daily monitor starts.

## Seed CSV format

Generate a template: `python -m radar.main seed-template --output seed.csv`

Required columns:
  origin, destination, carrier, cabin, outbound_date, return_date,
  outbound_duration_hours, return_duration_hours, outbound_stops, return_stops,
  outbound_routing, return_routing, price_usd

Optional columns (include empty string if unknown):
  price_egp, price_eur, source_notes

All constraints are enforced — rows with invalid cabin, wrong destination, duration
outside 9–14 nights, or outbound/return > 30 hours are rejected and logged.

## Procedure

1. Check HIMAYAH: confirm `.env` is not staged for commit and `data/` is gitignored.
2. Collect historical prices from Google Flights and Kayak (manual process — ~30 min).
3. Generate template: `python -m radar.main seed-template`.
4. Fill template with collected data.
5. Dry-run: `python -m radar.main seed --file seed.csv --dry-run`.
6. Import: `python -m radar.main seed --file seed.csv`.
7. Run FORECAST: `python -m radar.main forecast`.
8. Run STATUS: `python -m radar.main status` — verify observation counts increased.
9. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"seed_import","rows_imported":<n>,"rows_skipped":<n>}`

## Data quality note

Historical seed observations use `data_quality: "estimated"` because they are
manually collected from visual charts — exact prices may have ±5–10% variance
from actual fares that were available at that time. This is acceptable for seeding
the forecasting model but should not be treated as precise historical records.

## Source quality ranking

1. Google Flights price history — best coverage, most reliable for Business Class
2. Kayak price trend — good complementary data, useful for Premium Economy
3. Skyscanner route history — useful for routes not well-covered by the above two
4. Hopper (mobile app) — deep history (24 months) but coverage of CAI routes varies
5. ITA Matrix — CANNOT be used for historical data (future dates only)
