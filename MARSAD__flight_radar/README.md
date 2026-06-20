# MARSAD — Flight Intelligence Module

> مرصد (marsad) = observatory / watchtower

MARSAD is the flight price monitoring and forecasting pipeline within NIZAM.
It watches the Cairo (CAI) → USA major airports corridor for Business Class and
Premium Economy fares, runs daily on a 06:00 UTC schedule, and surfaces
BUY_SIGNAL alerts when a price is genuinely anomalous against its own history.

**Additive only** — MARSAD does not modify any existing NIZAM stable module.

---

## Architecture Overview

```
MARSAD PIPELINE
│
├─ STAGE 1: DISCOVER (baseline collection — runs once on init or manual trigger)
│  └─ Fetches full price matrix across all carrier × cabin × destination
│     Observation type: 'baseline'
│
├─ STAGE 2: MONITOR (daily delta — runs 06:00 UTC via scheduler)
│  └─ Fetches current prices, calculates delta vs previous observation
│     Observation type: 'daily'
│
├─ STAGE 3: ALERT (price drop signal detection)
│  └─ Fires when: single-day drop ≥ threshold AND price < 20th percentile historical
│     BUY_SIGNAL requires BOTH conditions + forecast_confidence ≥ MEDIUM
│
└─ STAGE 4: FORECAST (trend and prediction)
   └─ SMA (< 7 obs) → EWM (7–29 obs) → Linear Regression (30+ obs)
      Confidence: LOW < 7 | MEDIUM 7–29 | HIGH 30+
```

## Module Map

```
MARSAD__flight_radar/
├── README.md                  (this file)
├── _index.json                (NIZAM folder registry — private_github)
├── .env.example               (env var documentation — committed, no secrets)
├── requirements.txt
├── radar/
│   ├── __init__.py
│   ├── main.py                (entry point — CLI + scheduler bootstrap)
│   ├── config.py              (all env vars and constants loaded here)
│   ├── constraints.py         (ROUTING CONSTRAINT ENGINE — single source of truth)
│   ├── schema_store.py        (append-only JSON store — write-to-temp-then-rename)
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py            (abstract source interface + shared rate-limit logic)
│   │   ├── amadeus_source.py  (PRIMARY — Amadeus for Developers API)
│   │   ├── ita_matrix_source.py  (OPTIONAL — requires ToS review before enabling)
│   │   ├── kiwi_source.py     (secondary aggregator)
│   │   └── google_flights_source.py  (validation-only, rate-limited)
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── discover.py        (Stage 1 — baseline collection)
│   │   ├── monitor.py         (Stage 2 — daily delta)
│   │   ├── alert.py           (Stage 3 — BUY_SIGNAL engine)
│   │   └── forecast.py        (Stage 4 — trend model)
│   └── scheduler.py           (APScheduler 06:00 UTC daily)
└── tests/
    ├── test_constraints.py
    ├── test_schema_store.py
    ├── test_alert.py
    └── test_forecast.py

NIZAM__system/
├── schemas/
│   └── flight_price_observation.schema.json  (NEW)
└── skills/
    ├── marsad-discover.md    (NEW)
    ├── marsad-monitor.md     (NEW)
    ├── marsad-alert.md       (NEW)
    └── marsad-forecast.md    (NEW)
```

## Data files (strict_local — never committed)

```
MARSAD__flight_radar/
├── data/
│   ├── flight_prices.json     (primary data store — append-only)
│   ├── flight_prices.tmp      (in-flight write buffer — deleted after rename)
│   └── backups/               (daily snapshots before monitor run)
│       └── YYYY-MM-DDTHH-MM-SSZ.json
└── alerts/
    └── radar_alerts.json      (alert log — append-only)
```

## Routing Constraints

| Constraint | Value |
|---|---|
| Origin | CAI (Cairo International Airport) only |
| Destinations | JFK, LAX, ORD, ATL, MIA, SFO, IAD, BOS, EWR, DFW, SEA, LAS |
| Cabins | BUSINESS, PREMIUM_ECONOMY only |
| Trip duration | 9–14 nights inclusive |
| Max one-way flight time | 30 hours (applied independently to outbound and return) |
| Travel window | 2027-03-15 → 2027-09-30 (configurable via RADAR_WINDOW_START) |

## Ramadan 2027 Note

Ramadan 2027 is estimated to end approximately 2027-03-09 (moon-sighting dependent,
±1–2 days). `RADAR_WINDOW_START` defaults to 2027-03-15 as a conservative
post-Eid buffer. Update when the official announcement is made (~30 days before).

## Primary Data Source Decision

**Default and recommended: SerpApi Google Flights** (`DATA_SOURCE=serpapi` in .env)

- Register at [serpapi.com](https://serpapi.com) — instant approval, no gating
- Free tier: 250 searches/month (covers testing and low-cadence monitoring)
- Paid tier ($25/month): 1,000 searches/month — required for full daily monitoring across all 24 combinations
- Set `SERPAPI_PRIORITY_ONLY=true` in .env to restrict to 8 priority destinations and stay within free tier during setup

Amadeus for Developers (`DATA_SOURCE=amadeus`) — **disabled**: the Amadeus self-service portal shut down in July 2025 and new API keys are no longer issued. The implementation is retained for reference; existing key holders can re-enable.

ITA Matrix (`DATA_SOURCE=ita_matrix`) — **ToS-gated**: Google's Terms of Service prohibit automated access without prior written permission. Bot detection will likely block headless browser automation within 24 hours. Enable only after ToS review by setting `ITA_MATRIX_ENABLED=true` in .env.

See `SWAPPABLE_DEFAULT REGISTRY` at the bottom of this README for all swap instructions.

## Quick Start

```bash
cd MARSAD__flight_radar
cp .env.example .env
# Edit .env — set SERPAPI_KEY at minimum (register free at serpapi.com)
pip install -r requirements.txt

# Confirm credentials and config are valid
python -m radar.main validate

# Run baseline collection (Stage 1 — first time only)
python -m radar.main discover
# Optional: preview scope without writing: --dry-run

# Run daily monitor (Stage 2 — or let scheduler run it)
python -m radar.main monitor

# Run alert check (Stage 3)
python -m radar.main alert

# Run forecast update (Stage 4)
python -m radar.main forecast

# Run all stages in sequence (monitor + alert + forecast)
python -m radar.main run-all
# Include discover in the sequence: --with-discover

# Start scheduler daemon (runs 06:00 UTC daily)
python -m radar.main schedule

# Live executive dashboard at http://localhost:7329
python -m radar.main dashboard

# Print store summary
python -m radar.main status
```

## Historical Price Seed Research

The forecast model needs 7+ observations to exit cold-start (LOW confidence). Seeding with
historical data from external sources accelerates this. All seeds are stored with
`observation_type: historical_seed` in the schema — they never overwrite live observations.

### Available Sources

| Source | Historical Depth | Access Method | Format | Integration |
|---|---|---|---|---|
| Google Flights price history | ~3 months visible in UI | Manual: price graph on Google Flights search results. No public API. | Approximate month-range + price curve | Manual entry as `historical_seed` observations via schema_store.append_observation |
| Hopper historical data | 12–24 months (Hopper app) | Mobile app only — no public API. Hopper's algorithm is proprietary. | In-app price calendar / forecast screen | Manual sampling from app — not bulk-importable |
| Kayak price history charts | ~3 months via Kayak.com/flights price trend feature | Web UI scraping (fragile) — no official API | Monthly price trend chart | Manual extraction; add as `historical_seed` |
| Momondo price trends | ~3 months | Similar to Kayak — web UI only | Monthly chart | Manual extraction |
| SerpApi historical search | Current day only (live API) | Programmatic via SerpApi | JSON | The daily MONITOR stage builds the time series automatically |
| Airline fare filing archives | Up to 24 months | ATPCO (requires enterprise subscription — not viable for personal use) | Structured fare data | Not applicable |

### Practical Seed Strategy

The most viable approach for rapid cold-start exit:

1. **Run DISCOVER once** to seed a baseline observation for all 24 route-cabin combinations.
2. **Run MONITOR daily** — the pipeline exits cold-start after 7 consecutive daily runs (~1 week).
3. **Optional manual seed**: For any route-cabin combination, manually search Google Flights for 3–5 historical price points from the past 30 days and insert via:
   ```python
   from radar.schema_store import append_observation
   append_observation(
       origin="CAI", destination="JFK", carrier="EK", cabin="BUSINESS",
       price_usd=3200.0, outbound_date="2027-04-01", return_date="2027-04-12",
       outbound_duration_hours=14.5, return_duration_hours=15.0,
       outbound_stops=1, return_stops=1,
       outbound_routing="CAI-DXB-JFK", return_routing="JFK-DXB-CAI",
       source="manual", observation_type="historical_seed",
   )
   ```
4. After 7 total observations per series (baseline + seeds + daily), the confidence gate opens and BUY_SIGNAL eligibility activates.

### Why No Hopper-Grade Dataset Exists Here

Hopper's price prediction accuracy comes from 10+ billion price points accumulated over years across all routes. MARSAD operates on a single personal corridor (CAI→USA) with a 6-month travel window. The SMA→EWM→LR three-tier model is calibrated for this constrained dataset — accuracy improves linearly with observation count. By day 30, the linear regression model produces directional forecasts that are reliable enough for booking decision support.

---

## SWAPPABLE_DEFAULT REGISTRY

| Component | Current Default | Swap To | Swap Instructions |
|---|---|---|---|
| Language | Python 3.11 | Any 3.11+ | No changes needed |
| Primary source | SerpApi (Google Flights) | Amadeus API (if key exists) | Set `DATA_SOURCE=amadeus` in .env + `AMADEUS_CLIENT_ID`/`SECRET` |
| Primary source | SerpApi (Google Flights) | ITA Matrix | Set `DATA_SOURCE=ita_matrix` in .env — review ToS first |
| Secondary source | None (disabled) | Kiwi Tequila | Set `SECONDARY_SOURCE=kiwi` and `KIWI_API_KEY` in .env |
| File store | JSON file | PostgreSQL/SQLite | Swap `schema_store.py` implementation |
| Scheduler | APScheduler | cron / GitHub Actions | See `SCHEDULED_AGENTS.md` in NIZAM__system |
| Alert delivery | Console + JSON file | Slack | Set `ALERT_DELIVERY=slack` and `SLACK_WEBHOOK_URL` in .env |
| Alert delivery | Console + JSON file | Webhook | Set `ALERT_DELIVERY=webhook` and `ALERT_WEBHOOK_URL` in .env |
| Currency | USD primary | Any | All prices stored in USD; EGP/EUR as supplementary fields |

## Privacy

Framework code: `private_github` (committed)
Data files (`data/`, `alerts/`): `strict_local` (never committed — gitignored)
Credentials: `.env` — strict_local (never committed)
