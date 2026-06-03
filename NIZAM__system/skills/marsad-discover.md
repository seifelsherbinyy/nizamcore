---
name: marsad-discover
module: MARSAD
trigger: "/marsad-discover"
target_folder: MARSAD__flight_radar/data/
naming_pattern: "flight_prices.json (append-only — no new file created)"
template: null
frontmatter_schema: flight_price_observation.schema.json
gates: [HIMAYAH, THABAT]
privacy: private_github
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
entry_point: "cd MARSAD__flight_radar && python -m radar.main discover"
run_frequency: once_on_init (or manual re-trigger after window change)
observation_type: baseline
---

## For future Claude

DISCOVER is Stage 1 of MARSAD — the baseline collection run. It fetches the full price matrix across all 24 combinations (12 USA destinations × 2 cabin classes) within the post-Ramadan 2027 travel window. It runs ONCE on initial deployment to seed the JSON store with baseline prices. Subsequent daily monitoring uses `/marsad-monitor`.

The baseline may not complete in a single run due to API rate limits — the DISCOVER stage is designed to be re-run safely. Each run picks up from where the last left off (combinations already in the store are skipped).

## Procedure

1. Check HIMAYAH: confirm `.env` is not staged for commit and `data/` is gitignored.
2. Run `python -m radar.main validate` to confirm credentials are configured.
3. Run `python -m radar.main discover`.
   - Optional: `--dry-run` to preview scope without writing data.
   - Full baseline covers all 12 destinations × 2 cabins × all configured carriers.
   - Session limit: MAX_REQUESTS_PER_SESSION per run — re-run daily until `baseline_complete: true` in log output.
4. Check log output for:
   - `combinations_fetched`: combinations with at least one qualifying offer found
   - `combinations_no_data`: carriers/routes with no data (logged as PREMIUM_ECONOMY_UNAVAILABLE if applicable)
   - `baseline_complete: True` when all combinations have been seeded
5. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"discover_run","combinations_fetched":<n>,"baseline_complete":<bool>}`

## Notes

- Travel window start: `RADAR_WINDOW_START` env var (default: 2027-03-15 = conservative post-Ramadan buffer)
- Ramadan 2027 estimated end: ~2027-03-09 (±1–2 days, moon-sighting dependent)
- Update `RADAR_WINDOW_START` in `.env` when exact date is confirmed
- Data written to: `MARSAD__flight_radar/data/flight_prices.json` (private_github — committed; backups/ and .tmp excluded by .gitignore)
