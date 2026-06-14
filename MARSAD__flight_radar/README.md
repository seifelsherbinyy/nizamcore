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
│   │   ├── forecast.py        (Stage 4 — trend model)
│   │   └── seed_import.py     (Historical seed import — bypasses cold-start)
│   └── scheduler.py           (APScheduler 06:00 UTC daily)
└── tests/
    ├── test_constraints.py
    ├── test_schema_store.py
    ├── test_alert.py
    ├── test_forecast.py
    └── test_seed_import.py

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

**Active default: SerpAPI** (`DATA_SOURCE=serpapi` in .env)

SerpAPI proxies the Google Flights endpoint and handles CAPTCHAs, so no
browser automation is required. Set `SERPAPI_KEY` in `.env` — free tier
is sufficient for daily monitoring at this route count.

Source status as of 2025:

| Source | Status | Notes |
|---|---|---|
| SerpAPI (Google Flights) | **Active default** | Works reliably; no ToS issues |
| Amadeus for Developers | Deprecated | Amadeus developer portal shut down July 2025 |
| ITA Matrix | Avoid | Google ToS prohibits automated access; bot detection ~24 h |
| Kiwi Tequila | Invitation-only | Closed to new partners as of 2025 |

See `SWAPPABLE_DEFAULT REGISTRY` at the bottom of this README for all swap instructions.

## Quick Start

```bash
cd MARSAD__flight_radar
cp .env.example .env
# Edit .env — set SERPAPI_KEY at minimum
pip install -r requirements.txt

# Optional: import historical prices to bypass the 7-observation cold start
python -m radar.main seed-import --file prices.csv
python -m radar.main seed-import --template seed_template.csv  # write example CSV

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

## Historical Price Seed Research

The forecast model requires ≥ 7 observations for MEDIUM confidence and ≥ 30 for HIGH.
Without seed data the pipeline stays in LOW-confidence (BUY_SIGNAL hard-gated off) for
the first week of live monitoring. `seed-import` ingests historical data to bypass this.

### Viable Sources for CAI → USA Historical Prices

**Google Flights price calendar (manual export)**

Google Flights shows a ±3-month price calendar on individual route searches. For each
`CAI → DESTINATION` pair in your target window, open the price calendar view and note the
lowest Business/Premium Economy fare shown per week. Export to a CSV manually. This is
the most reliable free source because the data comes directly from Google's index.

Steps:
1. Go to flights.google.com, set CAI → destination, cabin = Business (or Premium Economy)
2. Click the price calendar icon (grid view)
3. Screenshot or manually record fare + date pairs for the Mar–Sep 2027 window
4. Fill in `seed_template.csv` (generate with `python -m radar.main seed-import --template out.csv`)
5. Set `data_quality=estimated` for calendar prices (they show range midpoints, not exact quotes)

**Hopper**

Hopper's "Watch a trip" feature shows a 12-month price history chart per route. CAI routes
may have limited coverage depending on the destination. Hopper does not provide data export;
you must read prices from the chart visually. Set `data_quality=estimated`.

**Kayak Price Forecast / Explore**

Kayak shows historical price trends on the Explore map and on individual search results.
Data granularity is weekly. Coverage for CAI is inconsistent; Business cabin data is often
absent for specific carrier/date combos. Read from chart, set `data_quality=estimated`.

**Manual agency quotes**

If you have quotes from a travel agent covering the target window, these are the highest
quality seed data. Set `data_quality=confirmed` for exact quoted prices. Include the
carrier, routing, cabin, and outbound/return dates precisely.

### CSV Seed Format

Required columns:
```
origin, destination, carrier, cabin, outbound_date, return_date, price_usd,
outbound_duration_hours, return_duration_hours, outbound_stops, return_stops,
outbound_routing, return_routing
```

Optional columns: `price_egp`, `price_eur`, `data_quality` (defaults to `estimated`)

Generate a template with:
```bash
python -m radar.main seed-import --template seed_template.csv
```

### Importing

```bash
# Dry run — validate and count without writing
python -m radar.main seed-import --file prices.csv --dry-run

# Live import
python -m radar.main seed-import --file prices.csv

# JSON format
python -m radar.main seed-import --file prices.json --format json

# Abort on first parse error instead of skipping
python -m radar.main seed-import --file prices.csv --strict
```

All records are filtered through the routing constraint engine before storage.
Economy cabin, flights > 30 hours, and dates outside the travel window are silently dropped.
Importing the same file twice is safe — the store is append-only and does not deduplicate.

---

## SWAPPABLE_DEFAULT REGISTRY

| Component | Current Default | Swap To | Swap Instructions |
|---|---|---|---|
| Language | Python 3.11 | Any 3.11+ | No changes needed |
| Primary source | SerpAPI | Any source in `sources/` | Set `DATA_SOURCE=<name>` in .env |
| File store | JSON file | PostgreSQL/SQLite | Swap `schema_store.py` implementation |
| Scheduler | APScheduler | cron / GitHub Actions | See `.github/workflows/marsad_monitor.yml` |
| Alert delivery | Console + JSON file | Slack/Webhook | Set `ALERT_DELIVERY=slack` and `SLACK_WEBHOOK_URL` in .env |
| Currency | USD primary | Any | All prices stored in USD; EGP/EUR as supplementary |

## Privacy

Framework code (`radar/`): `private_github` (committed)
Price data (`data/flight_prices.json`): `private_github` (committed — price history, no personal data)
Backups (`data/backups/`): `strict_local` (gitignored — redundant copies)
Alert log (`alerts/`): `strict_local` (gitignored)
Credentials (`.env`): `strict_local` (never committed)
