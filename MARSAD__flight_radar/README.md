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
│   ├── main.py                (entry point — CLI: discover/monitor/alert/forecast/schedule/dashboard/status/validate)
│   ├── config.py              (all env vars and constants loaded here — single load point)
│   ├── constraints.py         (ROUTING CONSTRAINT ENGINE — single source of truth, called by all four stages)
│   ├── schema_store.py        (append-only JSON store — write-to-temp-then-rename, backup before monitor)
│   ├── fetcher.py             (staged sequential fetching — rate limits, backoff, session budget)
│   ├── scheduler.py           (APScheduler daemon — 06:00 UTC: MONITOR → ALERT → FORECAST)
│   ├── dashboard.py           (live HTTP dashboard at http://localhost:7329 — Chart.js, auto-refresh 60s)
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py            (abstract source interface + shared rate-limit / backoff utilities)
│   │   ├── serpapi_source.py  (PRIMARY — SerpApi Google Flights API, DATA_SOURCE=serpapi)
│   │   ├── kiwi_source.py     (secondary aggregator — DATA_SOURCE=kiwi)
│   │   ├── amadeus_source.py  (DISABLED — Amadeus portal shut down July 2025; kept as reference)
│   │   ├── ita_matrix_source.py  (GATED — Google ToS prohibits automated access; requires ITA_MATRIX_ENABLED=true)
│   │   ├── google_flights_source.py  (prototype-grade — validation-only, not for production)
│   │   └── generic_base.py    (abstract intel source for non-flight signals — Signal/SourceBundle contract)
│   └── stages/
│       ├── __init__.py
│       ├── discover.py        (Stage 1 — baseline collection, runs once on init)
│       ├── monitor.py         (Stage 2 — daily delta, backs up store before each run)
│       ├── alert.py           (Stage 3 — three-condition BUY_SIGNAL engine)
│       └── forecast.py        (Stage 4 — SMA→EWM→LR trend model, 7/14/30-day horizons)
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

**Current primary: SerpApi Google Flights API** (`DATA_SOURCE=serpapi` in .env, default)

SerpApi provides programmatic access to Google Flights results. Register at serpapi.com.
- Free tier: 250 searches/month (suitable for limited testing)
- Paid ($25/mo): 1,000 searches/month — required for full daily monitoring (24 searches/day)
- Set `SERPAPI_PRIORITY_ONLY=true` to restrict to 8 priority destinations on free tier

**Disabled sources:**
- **Amadeus for Developers** (`DATA_SOURCE=amadeus`) — portal shut down July 2025, kept as reference only
- **Kiwi Tequila** (`DATA_SOURCE=kiwi`) — invitation-only for new users as of 2025

**Gated source:**
- **ITA Matrix** (`DATA_SOURCE=ita_matrix`) — Google's ToS prohibits automated access without written permission; bot detection blocks headless browsers within 24 hours; requires `ITA_MATRIX_ENABLED=true` plus ToS acceptance

See `SWAPPABLE_DEFAULT REGISTRY` at the bottom of this README for all swap instructions.

## Quick Start

```bash
cd MARSAD__flight_radar
cp .env.example .env
# Edit .env — set SERPAPI_KEY at minimum (get key at serpapi.com)
pip install -r requirements.txt

# Run baseline collection (Stage 1 — first time only)
python -m radar.main discover

# Run daily monitor (Stage 2 — or let scheduler run it)
python -m radar.main monitor

# Run alert check (Stage 3)
python -m radar.main alert

# Run forecast update (Stage 4)
python -m radar.main forecast

# Run all stages in sequence
python -m radar.main run-all

# Start scheduler daemon (runs 06:00 UTC daily)
python -m radar.main schedule
```

## SWAPPABLE_DEFAULT REGISTRY

| Component | Current Default | Swap To | Swap Instructions |
|---|---|---|---|
| Language | Python 3.11 | Any 3.11+ | No changes needed |
| Primary source | SerpApi (Google Flights) | ITA Matrix (ToS risk) | Set `DATA_SOURCE=ita_matrix` + `ITA_MATRIX_ENABLED=true` — review ToS first |
| Priority mode | Full 12 destinations | 8 priority destinations | Set `SERPAPI_PRIORITY_ONLY=true` in .env (free tier usage) |
| Secondary source | Kiwi Tequila | Other aggregator | Set `SECONDARY_SOURCE=kiwi` in .env |
| File store | JSON file | PostgreSQL/SQLite | Swap `schema_store.py` implementation |
| Scheduler | APScheduler | cron / GitHub Actions | See `SCHEDULED_AGENTS.md` in NIZAM__system |
| Alert delivery | Console + JSON file | Slack | Set `ALERT_DELIVERY=slack` and `SLACK_WEBHOOK_URL` in .env |
| Alert delivery | Console + JSON file | Webhook | Set `ALERT_DELIVERY=webhook` and `ALERT_WEBHOOK_URL` in .env |
| Currency | USD primary | Any | All prices stored in USD; EGP/EUR as supplementary fields |

## Privacy

Framework code: `private_github` (committed)
Data files (`data/`, `alerts/`): `strict_local` (never committed — gitignored)
Credentials: `.env` — strict_local (never committed)
