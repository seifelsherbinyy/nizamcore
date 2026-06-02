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
├─ SEED (optional — run before DISCOVER to accelerate cold-start)
│  └─ Imports historical prices from CSV → observation_type: 'historical_seed'
│     Accepts data from Google Flights history, Kayak, Hopper, manual entry
│     ≥7 seeded observations per series skips the 7-day cold-start period
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
│  └─ BUY_SIGNAL requires ALL THREE: drop ≥ threshold AND price < 20th percentile
│     AND forecast_confidence ≥ MEDIUM (hard gate — no exceptions)
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
│   │   ├── forecast.py        (Stage 4 — trend model)
│   │   └── seed.py            (Historical price importer — CSV → historical_seed observations)
│   └── scheduler.py           (APScheduler 06:00 UTC daily)
└── tests/
    ├── test_constraints.py
    ├── test_schema_store.py
    ├── test_alert.py
    └── test_forecast.py

NIZAM__system/
├── schemas/
│   └── flight_price_observation.schema.json
└── skills/
    ├── marsad-discover.md
    ├── marsad-monitor.md
    ├── marsad-alert.md
    ├── marsad-forecast.md
    └── marsad-seed.md
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

**Current default: SerpApi Google Flights** (`DATA_SOURCE=serpapi` in .env)

SerpApi provides a clean programmatic interface to Google Flights results at $25/month for 1,000
searches. Full daily monitoring (12 destinations × 2 cabins = 24 searches/day) requires the paid
tier. Set `SERPAPI_PRIORITY_ONLY=true` to restrict to 8 priority destinations during free-tier
testing (16 searches/day — still exceeds free tier; treat as paid-only in practice).

**Amadeus for Developers** (`DATA_SOURCE=amadeus`) — portal shut down July 2025. Implementation
retained for reference; disabled by default.

**Kiwi Tequila** (`DATA_SOURCE=kiwi`) — invitation-only for new users as of 2025. Implementation
retained; disabled by default.

ITA Matrix (`DATA_SOURCE=ita_matrix`) is implemented but flagged:
- Google's ToS prohibits automated access without prior written permission
- Bot detection will likely block headless browser automation within 24 hours
- Use only after ToS review — gated behind `ITA_MATRIX_ENABLED=true`

See `SWAPPABLE_DEFAULT REGISTRY` at the bottom of this README for all swap instructions.

## Quick Start

```bash
cd MARSAD__flight_radar
cp .env.example .env
# Edit .env — set SERPAPI_KEY at minimum (get a key at serpapi.com)
pip install -r requirements.txt

# Validate credentials
python -m radar.main validate

# Run baseline collection (Stage 1 — first time only)
python -m radar.main discover

# [Optional] Accelerate forecasting cold-start by importing historical prices
# Generate a CSV template, fill it in, then import:
python -m radar.main seed-csv --export-template seed_template.csv
# ... fill in seed_template.csv with historical prices from Google Flights, Kayak, Hopper ...
python -m radar.main seed-csv --file seed_template.csv --dry-run   # validate first
python -m radar.main seed-csv --file seed_template.csv             # import

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

# Live dashboard at http://localhost:7329
python -m radar.main dashboard
```

## SWAPPABLE_DEFAULT REGISTRY

| Component | Current Default | Swap To | Swap Instructions |
|---|---|---|---|
| Language | Python 3.11 | Any 3.11+ | No changes needed |
| Primary source | SerpApi (Google Flights) | ITA Matrix | Set `DATA_SOURCE=ita_matrix` in .env — review ToS first; or `DATA_SOURCE=kiwi` if invitation obtained |
| Secondary source | (disabled) | Kiwi Tequila | Set `DATA_SOURCE=kiwi` in .env once invitation obtained |
| Historical seed source | Manual CSV | SerpApi chart endpoint | `engine=google_flights_chart` via SerpApi — Economy fares only |
| File store | JSON file | PostgreSQL/SQLite | Swap `schema_store.py` implementation |
| Scheduler | APScheduler | cron / GitHub Actions | See `.github/workflows/marsad_monitor.yml` |
| Alert delivery | Console + JSON file | Slack/Webhook | Set `ALERT_DELIVERY=slack` and `SLACK_WEBHOOK_URL` in .env |
| Currency | USD primary | Any | All prices stored in USD; EGP/EUR as supplementary |
| Travel window start | 2027-03-15 | Confirmed Ramadan end +6 days | Set `RADAR_WINDOW_START=YYYY-MM-DD` in .env once official date confirmed |

## Privacy

Framework code: `private_github` (committed)
Data files (`data/`, `alerts/`): `strict_local` (never committed — gitignored)
Credentials: `.env` — strict_local (never committed)
