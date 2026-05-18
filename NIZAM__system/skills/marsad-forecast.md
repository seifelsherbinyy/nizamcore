---
name: marsad-forecast
module: MARSAD
trigger: "/marsad-forecast"
target_folder: MARSAD__flight_radar/data/
naming_pattern: "flight_prices.json (forecast block updated — observation_series untouched)"
template: null
frontmatter_schema: flight_price_observation.schema.json
gates: [HIMAYAH, THABAT]
privacy: strict_local
appends_event_to: NIZAM__system/ledgers/EVENT_LEDGER.jsonl
entry_point: "cd MARSAD__flight_radar && python -m radar.main forecast"
run_frequency: daily (after alert) or manual
---

## For future Claude

FORECAST is Stage 4 of MARSAD — the trend model. It reads the accumulated time series for each route-carrier-cabin combination and computes price direction forecasts for the next 7, 14, and 30 days. The model tier is automatically selected based on observation count.

**Three-tier model:**
| Tier | Model | When | Confidence |
|---|---|---|---|
| 1 | Simple Moving Average (SMA) | < 7 observations | LOW |
| 2 | Exponential Weighted Mean (EWM) | 7–29 observations | MEDIUM |
| 3 | Linear Regression (LR) | 30+ observations | HIGH |

**Cold-start period:** For the first ~7 days (fewer than 7 observations), all forecasts are LOW confidence. BUY_SIGNAL is hard-gated to False during this period regardless of model output.

**Output per series:**
- `horizon_7d`, `horizon_14d`, `horizon_30d`: predicted price range {low, mid, high} in USD
- `forecast_confidence`: LOW | MEDIUM | HIGH
- `buy_signal`: True only when current < 7d_low AND current < historical_p20 AND confidence ≥ MEDIUM
- `model_used`: sma | ewm | lr

## Procedure

1. Run `python -m radar.main forecast`.
2. Forecast block is updated in `data/flight_prices.json` for all series.
   - **INVARIANT: `observation_series` is never touched — only the `forecast` block is updated.**
3. Check log output for:
   - `series_updated`: total series with updated forecasts
   - `series_low_confidence`: series in cold-start (< 7 obs)
   - `buy_signals`: series with active BUY_SIGNAL from forecast model
4. Append THABAT event to EVENT_LEDGER:
   `{"ts":"<ISO8601_UTC>","module":"MARSAD","event_type":"forecast_run","series_updated":<n>,"buy_signals":<n>}`

## Notes

- Forecast output feeds the Stage 3 ALERT engine — always run FORECAST after MONITOR + ALERT in the daily pipeline
- Historical seed data (if available) can be imported as `observation_type: historical_seed` observations to accelerate confidence from LOW to MEDIUM/HIGH before the 7-day monitoring period completes
- See Historical Price Seed Research in MARSAD/README.md for seed data sources
