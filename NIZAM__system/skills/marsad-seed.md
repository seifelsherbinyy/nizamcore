---
name: marsad-seed
module: MARSAD
trigger: "/marsad-seed"
target_folder: MARSAD__flight_radar/data/
naming_pattern: "flight_prices.json (append-only — no new file created)"
template: null
frontmatter_schema: flight_price_observation.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
entry_point: "cd MARSAD__flight_radar && python -m radar.main seed --csv <path>"
run_frequency: once_before_first_monitor (or any time new historical data is available)
observation_type: historical_seed
---

## For future Claude

SEED is Stage 0 of MARSAD — the historical price import shortcut. It imports manually-researched price data as `observation_type: "historical_seed"` observations, accelerating the forecast model from LOW confidence to MEDIUM (7+ observations) before the 7-day daily monitoring cold-start period completes.

**Why seeding matters:**
The BUY_SIGNAL hard gate requires `forecast_confidence ≥ MEDIUM` (≥ 7 observations). Without seeding, the pipeline sits in LOW confidence for the first 7 days regardless of how good or anomalous a price is. Seeding with 7+ historical observations from Hopper, Google Flights calendars, or Kayak price history allows BUY_SIGNAL to fire from day 1.

**BUY_SIGNAL cold-start timeline WITHOUT seeding:**
- Days 1–6: LOW confidence → BUY_SIGNAL hard-gated to False
- Day 7+: MEDIUM confidence → BUY_SIGNAL can fire

**BUY_SIGNAL timeline WITH 7+ seed observations:**
- Day 1: MEDIUM confidence → BUY_SIGNAL can fire immediately

## CSV template

```
python -m radar.main seed-template --output seed_template.csv
# Edit seed_template.csv with historical prices
python -m radar.main seed --csv seed_template.csv --dry-run
python -m radar.main seed --csv seed_template.csv
```

Required CSV columns:
| Column | Description | Example |
|---|---|---|
| carrier | IATA code | EK |
| origin | Must be CAI | CAI |
| destination | USA airport IATA | JFK |
| cabin | BUSINESS or PREMIUM_ECONOMY | BUSINESS |
| outbound_date | YYYY-MM-DD | 2027-04-01 |
| return_date | YYYY-MM-DD | 2027-04-12 |
| price_usd | Round-trip price USD | 3100.0 |
| outbound_duration_hours | One-way flight time | 14.5 |
| return_duration_hours | One-way flight time | 15.0 |
| outbound_stops | Number of stops | 1 |
| return_stops | Number of stops | 1 |
| outbound_routing | e.g. CAI-DXB-JFK | CAI-DXB-JFK |
| return_routing | e.g. JFK-DXB-CAI | JFK-DXB-CAI |

Optional columns: `source_name` (default: historical_seed), `data_quality` (default: estimated), `price_egp`, `price_eur`

## Historical price sources

| Source | Historical Depth | Access Method | Format |
|---|---|---|---|
| **Hopper** (hopper.com) | 12 months in-app | Screenshot price calendar → manual CSV | Visual only |
| **Google Flights price calendar** | 1–3 months future range | Open calendar view, hover dates for prices | Visual only |
| **Kayak price history** (kayak.com) | 3 months chart | Hover price history chart at bottom | Visual only |
| **ITA Matrix** (matrix.itasoftware.com) | Current prices for any future date | Manual searches for specific travel dates | Manual entry after ToS review |
| **SerpApi multi-date probe** | Not historical — current prices for multiple future dates | Run DISCOVER with increased SAMPLE_DATES_COUNT | Via discover.py |

**Most practical approach for immediate MEDIUM confidence:**
Run `python -m radar.main discover` 3× over 3 days (each run samples 3 departure dates per route × 2 cabins × 12 destinations = 72 price points). After 3 runs, most series will have 9 observations → MEDIUM confidence.

Alternatively: research 7+ dates on Google Flights price calendar and enter as CSV seed.

## Procedure

1. Check HIMAYAH: confirm `.env` is not staged for commit and `data/` is gitignored.
2. Generate template: `python -m radar.main seed-template --output my_seed.csv`
3. Fill in the CSV with historical prices from Hopper, Google Flights, Kayak.
   - Each row = one price observation for one (carrier, route, cabin, departure date) combination
   - data_quality: use "estimated" for manually-transcribed values (not from live API)
4. Dry run to validate: `python -m radar.main seed --csv my_seed.csv --dry-run`
5. Import: `python -m radar.main seed --csv my_seed.csv`
6. Verify: `python -m radar.main status` — check observation counts increased
7. Run FORECAST: `python -m radar.main forecast` — model confidence should now be MEDIUM or HIGH
8. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"seed_run","rows_imported":<n>,"rows_filtered":<n>}`

## Constraints enforced on import

All routing constraints apply — any row that fails is logged and skipped:
- Origin must be CAI
- Destination must be in the 12 USA major airports
- Cabin must be BUSINESS or PREMIUM_ECONOMY
- Trip duration must be 9–14 nights
- Outbound flight time ≤ 30h (independently checked)
- Return flight time ≤ 30h (independently checked)
- Outbound date must be within travel window (2027-03-15 to 2027-09-30)

Duplicate detection: same (carrier, route, cabin, outbound_date, price_usd) on a re-run is skipped — safe to re-import the same CSV without creating duplicates.

## Notes

- All seed observations are marked `observation_type: "historical_seed"` regardless of input
- Seeded observations count toward `observation_count` and `forecast_confidence`
- Append-only invariant: existing observations (including prior seeds) are never modified
- Data written to: `MARSAD__flight_radar/data/flight_prices.json` (private_github)
