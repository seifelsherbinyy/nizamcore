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
├─ STAGE 0: SEED (optional — pre-DISCOVER, bootstraps forecast cold start)
│  └─ Imports historical price data from CSV/JSON to seed the forecasting model
│     Observation type: 'historical_seed' | Run: python -m radar.main seed --file <path>
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
│  └─ BUY_SIGNAL fires when ALL THREE: drop ≥ threshold AND price < 20th percentile
│     AND forecast_confidence ≥ MEDIUM (cold-start gate — no BUY_SIGNAL < 7 observations)
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
├── conftest.py                (pytest sys.path setup)
├── radar/
│   ├── __init__.py
│   ├── main.py                (entry point — CLI + scheduler bootstrap)
│   ├── config.py              (all env vars and constants loaded here)
│   ├── constraints.py         (ROUTING CONSTRAINT ENGINE — single source of truth)
│   ├── fetcher.py             (staged sequential fetching — rate limit enforced here)
│   ├── schema_store.py        (append-only JSON store — write-to-temp-then-rename)
│   ├── scheduler.py           (APScheduler 06:00 UTC daily)
│   ├── dashboard.py           (live executive dashboard — http://localhost:7329)
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py            (abstract source interface + shared rate-limit logic)
│   │   ├── serpapi_source.py  (DEFAULT PRIMARY — SerpAPI Google Flights)
│   │   ├── amadeus_source.py  (DISABLED — Amadeus portal shut down July 2025)
│   │   ├── ita_matrix_source.py  (OPTIONAL — requires ToS review before enabling)
│   │   ├── kiwi_source.py     (secondary aggregator — invitation-only as of 2025)
│   │   ├── google_flights_source.py  (prototype — validation-only)
│   │   └── generic_base.py    (intel signal base for non-flight sources — E4.2)
│   └── stages/
│       ├── __init__.py
│       ├── seed.py            (Stage 0 — historical data import, optional)
│       ├── discover.py        (Stage 1 — baseline collection)
│       ├── monitor.py         (Stage 2 — daily delta)
│       ├── alert.py           (Stage 3 — BUY_SIGNAL engine)
│       └── forecast.py        (Stage 4 — trend model)
└── tests/
    ├── test_constraints.py    (81 tests — all EXECUTED_IN_SESSION)
    ├── test_schema_store.py
    ├── test_alert.py
    ├── test_forecast.py
    ├── test_seed.py
    └── test_generic_base.py

NIZAM__system/
├── schemas/
│   └── flight_price_observation.schema.json
└── skills/
    ├── marsad-seed.md
    ├── marsad-discover.md
    ├── marsad-monitor.md
    ├── marsad-alert.md
    └── marsad-forecast.md
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

**Default: SerpAPI / Google Flights** (`DATA_SOURCE=serpapi` in .env)

SerpAPI provides programmatic access to Google Flights results with terms-compliant API
keys. Free tier: 250 searches/month. Paid tier ($25/mo): 1,000 searches/month.
Full daily monitoring (12 destinations × 2 cabins = 24 searches/day) requires the paid tier.
Use `SERPAPI_PRIORITY_ONLY=true` with the free tier to restrict to 8 priority destinations.

**Amadeus for Developers**: Portal shut down July 2025. `AmadeusSource` is retained in the
codebase for future use if the service resumes, but cannot be used for production monitoring.

**Kiwi Tequila**: Invitation-only for new users as of 2025. `KiwiSource` is implemented as
a secondary validation source but requires an active API key to function.

**ITA Matrix** (`DATA_SOURCE=ita_matrix`): Implemented but flagged HIGH RISK:
- Google's ToS prohibits automated access without prior written permission
- Bot detection will likely block headless browser automation within 24 hours
- Enable only after explicit ToS review (`ITA_MATRIX_ENABLED=true` in .env)

See `SWAPPABLE_DEFAULT REGISTRY` below for swap instructions.

## Quick Start

```bash
cd MARSAD__flight_radar
cp .env.example .env
# Edit .env — set SERPAPI_KEY (register free at serpapi.com — 250 searches/month)
# Paid tier ($25/mo, 1,000 searches) required for full daily monitoring coverage
pip install -r requirements.txt

# Validate credentials and config
python -m radar.main validate

# Run baseline collection (Stage 1 — first time only)
# Optional: --dry-run to preview scope without writing data
python -m radar.main discover

# Import historical seed data (optional — bootstraps forecast model faster)
# See HISTORICAL SEED section below for data format and sources
python -m radar.main seed --file historical_prices.csv

# Run daily monitor (Stage 2 — or let scheduler run it)
python -m radar.main monitor

# Run alert check (Stage 3)
python -m radar.main alert

# Run forecast update (Stage 4)
python -m radar.main forecast

# Run all daily stages in sequence
python -m radar.main run-all

# Start scheduler daemon (runs 06:00 UTC daily)
python -m radar.main schedule

# Live dashboard at http://localhost:7329
python -m radar.main dashboard
```

## Booking Horizon Note

Google Flights (via SerpAPI) typically opens availability approximately 305 days in advance.
As of today (2026-06), the full post-Ramadan 2027 window (2027-03-15 → 2027-09-30) is within
the 305-day horizon. Run `python -m radar.main discover --dry-run` to confirm which departure
dates are currently returning prices. Dates beyond the horizon return empty results — the source
handles this gracefully and will pick them up on subsequent runs as they open.

## Historical Seed

The forecasting model requires 7+ observations to exit the LOW confidence cold-start period.
To accelerate this, import historical price data from external sources before running the
daily monitor.

**Step 1 — Gather historical data** from any of these sources:

| Source | Historical depth | Access method | Notes |
|---|---|---|---|
| Google Flights | ~90 days price history graph | Browser: price graph → export not available — manual transcription or screenshot OCR | Available on flight search result page |
| Hopper | 12+ months price history | App only — not programmatic; export via screenshot or manual note | Best historical depth |
| Kayak price history | 6–12 months | Browser: price graph on search result | Requires manual data extraction |
| SerpAPI Google Flights | Current prices only | Programmatic — no history endpoint | Use for live monitoring only |

**Step 2 — Format your data** as CSV (recommended) or JSON:

```csv
carrier,cabin,origin,destination,outbound_date,return_date,price_usd,outbound_duration_hours,return_duration_hours,outbound_stops,return_stops,outbound_routing,return_routing
EK,BUSINESS,CAI,JFK,2027-04-01,2027-04-12,3200.0,14.5,15.0,1,1,CAI-DXB-JFK,JFK-DXB-CAI
QR,BUSINESS,CAI,JFK,2027-04-01,2027-04-12,3100.0,15.0,14.5,1,1,CAI-DOH-JFK,JFK-DOH-CAI
```

**Step 3 — Import**:
```bash
python -m radar.main seed --file historical_prices.csv
python -m radar.main seed --file historical_prices.json  # JSON array also accepted
```

Each imported record is stored as `observation_type: "historical_seed"` — fully
append-only, never overwrites live monitoring data. Records failing routing constraints
are logged and skipped.

## SWAPPABLE_DEFAULT REGISTRY

| Component | Current Default | Swap To | Swap Instructions |
|---|---|---|---|
| Language | Python 3.11 | Any 3.11+ | No changes needed |
| Primary source | SerpAPI (Google Flights) | Kiwi / ITA Matrix | Set `DATA_SOURCE=kiwi` or `DATA_SOURCE=ita_matrix` in .env — review ToS before ITA Matrix |
| Secondary source | disabled | Kiwi Tequila | Set `SECONDARY_SOURCE=kiwi` and `KIWI_API_KEY` in .env |
| File store | JSON file | PostgreSQL/SQLite | Swap `schema_store.py` implementation |
| Scheduler | APScheduler | cron / GitHub Actions | See `SCHEDULED_AGENTS.md` in NIZAM__system |
| Alert delivery | Console + JSON file | Slack/Webhook | Set `ALERT_DELIVERY=slack` and `SLACK_WEBHOOK_URL` in .env |
| Currency | USD primary | Any | All prices stored in USD; EGP/EUR as supplementary |

## Privacy

Framework code: `private_github` (committed)
Data files (`data/`, `alerts/`): `strict_local` (never committed — gitignored)
Credentials: `.env` — strict_local (never committed)
