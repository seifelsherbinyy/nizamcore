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

**Recommended: Amadeus for Developers API** (`DATA_SOURCE=amadeus` in .env)

ITA Matrix (`DATA_SOURCE=ita_matrix`) is implemented but flagged:
- Google's ToS prohibits automated access without prior written permission
- Bot detection will likely block headless browser automation within 24 hours
- Use only if you have reviewed the ToS and accept the risk

See `SWAPPABLE_DEFAULT REGISTRY` at the bottom of this README for all swap instructions.

## Quick Start

```bash
cd MARSAD__flight_radar
cp .env.example .env
# Edit .env — set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET at minimum
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
| Primary source | Amadeus API | ITA Matrix | Set `DATA_SOURCE=ita_matrix` in .env — review ToS first |
| Secondary source | Kiwi Tequila | Kayak/Momondo scrape | Set `SECONDARY_SOURCE=scrape` in .env |
| File store | JSON file | PostgreSQL/SQLite | Swap `schema_store.py` implementation |
| Scheduler | APScheduler | cron / GitHub Actions | See `SCHEDULED_AGENTS.md` in NIZAM__system |
| Alert delivery | Console + JSON file | Email/Slack/Webhook | Set `ALERT_DELIVERY=slack` and `SLACK_WEBHOOK_URL` in .env |
| Currency | USD primary | Any | All prices stored in USD; EGP/EUR as supplementary |

## SerpApi Quota Incident (discovered 2026-07-08)

**Every scheduled MONITOR run since 2026-05-19 (51 consecutive daily runs) failed
silently.** The baseline (`discover`) collection on 2026-05-18 was the *only* run
that ever wrote observations to the store. Since then:

- SerpApi returned `429 Too Many Requests` on **every single request**, all day,
  every day — the free tier's 250 searches/month cannot cover daily monitoring of
  ~12 destinations × 7+ carriers × 2 cabins (that workload needs several thousand
  searches/month even in priority-only mode).
- The MONITOR stage had no circuit breaker and no time budget, so it retried
  every combination through exhaustion (4 backoff attempts each) for the full
  30 minutes, then GitHub Actions hard-cancelled the job before the "commit
  data store" step ever ran. Zero observations were written; nothing looked
  broken in the workflow's own summary because it never got the chance to log
  a failure — it just silently ran out the clock, daily, for 7 weeks.
- Separately, `.github/workflows/marsad_monitor.yml` had pinned `checkout` to an
  ephemeral session branch (`claude/charming-shannon-E6moy`) that was never
  merged into `main`, instead of checking out the default branch.

**Fixes applied:**
1. `radar/sources/serpapi_source.py` — class-level circuit breaker. After 2
   consecutive full-retry exhaustions (8 total 429s), stop making SerpApi calls
   for the rest of the run instead of retrying futilely.
2. `radar/stages/monitor.py` — wall-clock budget (`MONITOR_MAX_RUNTIME_SEC`,
   default 1200s / 20 min). The stage now always stops with time to spare so
   the workflow's commit step still runs, even if a source hangs or a future
   circuit breaker has a gap.
3. `.github/workflows/marsad_monitor.yml` — checkout no longer pins a stale
   branch; `SERPAPI_PRIORITY_ONLY=true` set as an immediate volume reduction.

**Still unresolved — requires a decision, not code:** the free SerpApi tier
cannot sustain daily monitoring at this route×carrier×cabin count even with
priority-only mode. Pick one:
- Upgrade to the SerpApi paid tier ($25/mo, 1,000 searches) — comfortably
  covers priority-only daily monitoring.
- Reduce scheduler cadence (e.g. every 3 days, or weekly) to fit the free tier.
- Shrink `PRIORITY_DESTINATIONS` further and/or drop `SECONDARY_CARRIERS`.

Until one of these is chosen, expect most daily runs to still return `no data`
for most combinations — the fix above stops the CI-time waste and data loss,
it does not manufacture search quota that doesn't exist.

## Privacy

Framework code: `private_github` (committed)
Data files (`data/`, `alerts/`): `strict_local` (never committed — gitignored)
Credentials: `.env` — strict_local (never committed)
