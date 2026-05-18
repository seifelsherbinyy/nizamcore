---
name: marsad-alert
module: MARSAD
trigger: "/marsad-alert"
target_folder: MARSAD__flight_radar/alerts/
naming_pattern: "radar_alerts.json (append-only)"
template: null
frontmatter_schema: flight_price_observation.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
entry_point: "cd MARSAD__flight_radar && python -m radar.main alert"
run_frequency: daily (after monitor) or manual
---

## For future Claude

ALERT is Stage 3 of MARSAD — the BUY_SIGNAL engine. It scans all series in the store for the most recent observation and evaluates three conditions. ALL THREE must be true for a BUY_SIGNAL. Single condition alone is never sufficient.

**BUY_SIGNAL conditions (all three required):**
1. Single-day price drop ≥ threshold (10% OR $200 Business / $100 Premium Economy)
2. Current price < 20th percentile of historical observations for this series
3. forecast_confidence ≥ MEDIUM (≥ 7 observations) — HARD GATE, cannot be bypassed

**Cold-start protection:** BUY_SIGNAL is hard-gated to False for the first 6 days of monitoring (fewer than 7 observations). This prevents false alerts when there is no reliable historical baseline. A WATCH_COLD_START signal may fire during cold start to surface noteworthy drops for manual review.

## Procedure

1. Run `python -m radar.main alert`.
2. Alerts are delivered via ALERT_DELIVERY setting (default: console + `alerts/radar_alerts.json`).
3. Each BUY_SIGNAL alert includes:
   - Carrier, route, cabin
   - Current price, previous price, drop amount and percentage
   - Historical percentile rank
   - Forecast signal (BUY / WATCH / HOLD)
   - Outbound/return dates and routing
4. Check `alerts/radar_alerts.json` for the full alert log.
5. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"alert_run","buy_signals":<n>,"watch_signals":<n>}`

## Acting on a BUY_SIGNAL

A BUY_SIGNAL means: this is the cheapest this route-carrier-cabin combination has been in its recorded history AND the forecast model expects prices to be higher next week. It is a signal to book — not a guarantee. Verify the price directly on the carrier's website before booking.

## Notes

- Alert thresholds configurable in .env: ALERT_THRESHOLD_PCT, ALERT_THRESHOLD_BUSINESS_USD, ALERT_THRESHOLD_PREMIUM_ECONOMY_USD
- Alert delivery configurable: ALERT_DELIVERY=console_and_file | slack | webhook
- BUY_SIGNAL history in `alerts/radar_alerts.json` (append-only — never deleted)
