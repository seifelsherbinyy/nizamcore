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
├── conftest.py                (pytest sys.path setup)
├── requirements.txt
├── docs/
│   └── historical_seed_research.md  (historical price data sources + integration guide)
├── radar/
│   ├── __init__.py
│   ├── main.py                (entry point — CLI + scheduler bootstrap)
│   ├── config.py              (all env vars and constants loaded here)
│   ├── constraints.py         (ROUTING CONSTRAINT ENGINE — single source of truth)
│   ├── schema_store.py        (append-only JSON store — write-to-temp-then-rename)
│   ├── dashboard.py           (live executive dashboard — http://localhost:7329)
│   ├── scheduler.py           (APScheduler daemon — 06:00 UTC daily)
│   ├── fetcher.py             (staged sequential fetching with rate-limit enforcement)
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py            (abstract flight source interface + shared rate-limit logic)
│   │   ├── generic_base.py    (abstract intel source interface — news/web/scholarly adapters)
│   │   ├── serpapi_source.py  (PRIMARY — SerpApi Google Flights API)
│   │   ├── amadeus_source.py  (DISABLED — Amadeus portal shut down July 2025)
│   │   ├── ita_matrix_source.py  (OPTIONAL — requires ToS review before enabling)
│   │   ├── kiwi_source.py     (DISABLED — invitation-only since 2025; kept for reference)
│   │   └── google_flights_source.py  (PROTOTYPE — validation-only, rate-limited)
│   └── stages/
│       ├── __init__.py
│       ├── discover.py        (Stage 1 — baseline collection)
│       ├── monitor.py         (Stage 2 — daily delta)
│       ├── alert.py           (Stage 3 — BUY_SIGNAL engine)
│       └── forecast.py        (Stage 4 — trend model)
└── tests/
    ├── conftest.py            (inherited from parent)
    ├── test_constraints.py    (EXECUTED_IN_SESSION — 45 tests)
    ├── test_schema_store.py   (EXECUTED_IN_SESSION — 10 tests)
    ├── test_alert.py          (EXECUTED_IN_SESSION — 16 tests)
    ├── test_forecast.py       (EXECUTED_IN_SESSION — 16 tests)
    └── test_generic_base.py   (EXECUTED_IN_SESSION — 4 tests)

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

**Current default: SerpApi** (`DATA_SOURCE=serpapi` in .env)

SerpApi wraps Google Flights with a paid API interface — terms-compliant, no Playwright,
clean JSON responses. Free tier: 250 searches/month. Full daily monitoring requires
paid tier ($25/month for 1,000 searches).

Amadeus for Developers (`DATA_SOURCE=amadeus`) was the original recommendation
but the self-service portal shut down July 2025 — credentials can no longer be obtained.
The source remains implemented as a placeholder for future activation.

ITA Matrix (`DATA_SOURCE=ita_matrix`) is implemented but flagged HIGH RISK:
- Google's ToS prohibits automated access without prior written permission
- Bot detection will likely block headless browser automation within 24 hours
- Use only if you have reviewed the ToS and obtained explicit authorization

See `docs/historical_seed_research.md` for historical price data sources.
See `SWAPPABLE_DEFAULT REGISTRY` at the bottom of this README for all swap instructions.

## Quick Start

```bash
cd MARSAD__flight_radar
cp .env.example .env
# Edit .env — set SERPAPI_KEY at minimum (get one free at serpapi.com)
# Free tier: 250 searches/month. Paid ($25/mo): 1,000/month — needed for full daily monitoring.
# Set SERPAPI_PRIORITY_ONLY=true on free tier to restrict to 8 priority destinations.
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
| Primary source | SerpApi (Google Flights) | ITA Matrix | Set `DATA_SOURCE=ita_matrix` in .env — review ToS first |
| Secondary source | None active (Kiwi invitation-only) | Direct airline site scraping | Custom source implementing `BaseFlightSource` |
| File store | JSON file | PostgreSQL/SQLite | Swap `schema_store.py` implementation |
| Scheduler | APScheduler | cron / GitHub Actions | See `SCHEDULED_AGENTS.md` in NIZAM__system |
| Alert delivery | Console + JSON file | Email/Slack/Webhook | Set `ALERT_DELIVERY=slack` and `SLACK_WEBHOOK_URL` in .env |
| Currency | USD primary | Any | All prices stored in USD; EGP/EUR as supplementary |

## Privacy

Framework code: `private_github` (committed)
Data files (`data/`, `alerts/`): `strict_local` (never committed — gitignored)
Credentials: `.env` — strict_local (never committed)
