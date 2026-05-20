# NIZAM Event Ledgers

Append-only `.jsonl` files — one JSON object per line, one line per event.

| File | Privacy | Contents |
|---|---|---|
| `EVENT_LEDGER.jsonl` | strict_local (gitignored) | THABAT gate events from all modules |
| `DECISION_LEDGER.jsonl` | strict_local | QARAR decision records |
| `LEARNING_LEDGER.jsonl` | strict_local | HIKMAH learning entries |

All ledger files are gitignored (see root `.gitignore`). This README is the only committed file in this directory.

## MARSAD event format

Each MARSAD pipeline run appends one event:

```json
{"ts":"2027-03-20T06:01:33Z","module":"MARSAD","event_type":"monitor_run","routes_checked":24,"routes_changed":3,"largest_drop_usd":180}
{"ts":"2027-03-20T06:02:10Z","module":"MARSAD","event_type":"alert_run","buy_signals":0,"watch_signals":1}
{"ts":"2027-03-20T06:02:45Z","module":"MARSAD","event_type":"forecast_run","series_updated":24,"buy_signals":0}
```

`event_type` values: `discover_run` | `monitor_run` | `alert_run` | `forecast_run`
