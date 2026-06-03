---
name: marsad-monitor
module: MARSAD
trigger: "/marsad-monitor"
target_folder: MARSAD__flight_radar/data/
naming_pattern: "flight_prices.json (append-only — no new file created)"
template: null
frontmatter_schema: flight_price_observation.schema.json
gates: [HIMAYAH, THABAT]
privacy: private_github
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
entry_point: "cd MARSAD__flight_radar && python -m radar.main monitor"
run_frequency: daily_06:00_UTC (via scheduler daemon) or manual
observation_type: daily
---

## For future Claude

MONITOR is Stage 2 of MARSAD — the daily delta check. It fetches the current best price for each route-carrier-cabin combination in the store, compares it to the previous observation, and appends a new 'daily' observation with delta fields populated.

The scheduler daemon (`python -m radar.main schedule`) runs this automatically at 06:00 UTC. Manual trigger available via this skill command.

## Procedure

1. Check HIMAYAH: confirm no data files are staged for commit.
2. Run `python -m radar.main monitor`.
   - A backup is created in `data/backups/` before any writes.
   - Each series fetches the best qualifying price within the travel window.
   - Delta (USD and %) is calculated against the previous observation.
3. Check log output for:
   - `routes_checked`: total series monitored
   - `routes_with_price_change`: series where price moved
   - `largest_drop_usd`: biggest single-day drop (if any)
   - `fetch_errors`: any source failures
4. After MONITOR completes, run `/marsad-alert` to evaluate BUY_SIGNAL conditions.
5. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"monitor_run","routes_checked":<n>,"routes_changed":<n>,"largest_drop_usd":<n>}`

## Notes

- Backup created before each run: `data/backups/YYYY-MM-DDTHH-MM-SSZ.json`
- Write pattern: write-to-.tmp then os.replace() — original untouched if write fails
- Skip condition: monitor exits early if today > RADAR_WINDOW_END (travel window ended)
- Skip condition: monitor warns if store is empty (run DISCOVER first)
