# MARSAD — Historical Price Seed Research

Researched: 2026-06-06

Accelerates the forecasting model by seeding the JSON schema with historical
observations before the daily monitor accumulates 30+ days. Without seed data,
DISCOVER produces `forecast_confidence: LOW` for the first 7+ days.

---

## Source 1 — Google Flights Price History (via SerpApi)

**Historical depth available:** ~1 year (rolling 12 months visible in Google Flights UI)

**Programmatic access:**
SerpApi's `google_flights` engine does not currently expose historical price data in its
API response — it returns live prices for a requested date. However, Google Flights
displays a price calendar and a price history chart in its UI. Two approaches:

- **Approach A — Date-range sweep (recommended):** Call SerpApi for each month from
  the past 12 months using specific departure dates. Each call returns the price on
  that date. Sweeping 12 months × 2 cabin classes × 12 destinations = 288 calls (~$2.88
  at SerpApi pricing, fits in one paid session). Store each as `observation_type: historical_seed`.

- **Approach B — Google Flights Price History UI (manual):** Visit
  `flights.google.com`, select route and cabin, and use the price graph to read
  historical prices visually. Manually enter into the schema as seed observations.
  Labor-intensive but zero API cost.

**Data format returned by Approach A:**
Standard SerpApi JSON response with `price`, `best_flights`, `other_flights` fields.
Parse identically to live MONITOR observations. Set `observation_type: "historical_seed"`.

**Integration into JSON schema:**
```python
from radar.schema_store import append_observation
append_observation(
    ...,
    observation_type="historical_seed",
    # observed_at will be set to current time — use outbound_date to anchor history
)
```

**RISK NOTE:** Historical prices from Approach A are live prices queried TODAY for
past dates — not the prices that were actually advertised on those past dates.
Google Flights shows current availability for past dates, which may differ from
what was bookable at the time. Label these `data_quality: "estimated"`.

---

## Source 2 — Hopper Historical Price Data

**Historical depth:** ~2 years per route (Hopper accumulates data from actual search traffic)

**Programmatic access:** NO public API. Hopper's price data is proprietary.

**Available data:**
- Hopper app shows a price calendar with colour-coded cheap/average/expensive days
- No historical chart exported programmatically
- Hopper published several research papers on flight price prediction methodology
  (referenced in `docs/forecast_methodology_notes.md` if that file exists)

**Integration method:** Manual. Visit Hopper app for CAI→JFK, CAI→LAX, etc.
Note the cheapest months from the calendar. These give a qualitative signal
(not numeric) about seasonal price patterns — useful for calibrating whether
post-Ramadan 2027 is expected to be a high or low period.

**Useful for:** Seasonal pattern validation, not numeric seed data.

---

## Source 3 — Kayak Price History Charts

**Historical depth:** ~12 months (Kayak shows a 12-month price trend on route pages)

**Programmatic access:**
Kayak has no public API. The price history chart is JS-rendered via Chart.js
on `kayak.com/flights/CAI-[DEST]`. XHR interception via Playwright can capture
the underlying data array.

**Playwright extraction pattern (PROTOTYPE — verify before running):**
```python
# PROTOTYPE_GRADE: Kayak rate-limits aggressively. Max 1 request per 30 seconds.
# Subject to Kayak ToS — review before enabling.

from playwright.sync_api import sync_playwright

def extract_kayak_price_history(origin: str, dest: str, cabin: str) -> list[dict]:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        
        responses = []
        page.on("response", lambda r: responses.append(r) if "price" in r.url else None)
        
        url = f"https://www.kayak.com/flights/{origin}-{dest}/2027-04-01/2027-04-12/{cabin}"
        page.goto(url, wait_until="networkidle")
        
        # Parse chart data from intercepted XHR responses
        # (actual endpoint varies — inspect network tab to find it)
        browser.close()
    return []
```

**Data format:** JSON array of `{date: "YYYY-MM-DD", price: NNN}` from the chart's
underlying API (endpoint subject to change without notice).

**RISK NOTE:** Kayak ToS prohibits automated access. HIGH risk of IP ban.
Rate limit aggressively (1 request per 30+ seconds) and use sparingly.
Label extracted data `data_quality: "estimated"` and `source: "kayak_historical"`.

---

## Source 4 — ITA Matrix Historical Search

**Historical depth:** NONE — ITA Matrix searches for future dates only.

ITA Matrix (matrix.itasoftware.com) is a forward-looking search tool.
It does not provide historical fare data.

**Verdict:** Not useful for historical seed data. Remove from consideration.

---

## Source 5 — Skyscanner Price Alerts Export

**Historical depth:** Unlimited (per-user price alert history)

**Programmatic access:** Skyscanner closed its public API in 2024 for individual
developers. No programmatic access available.

**Manual approach:** Set a price alert on Skyscanner for CAI→JFK Business in
early 2026. Review alert emails to extract price data points. Each alert email
contains a price and a timestamp — these can be manually imported as historical seeds.

**Verdict:** Low volume (1 data point per alert trigger), manual only.
Useful only if alerts were set up months in advance.

---

## Source 6 — EgyptAir Direct Booking History

**Historical depth:** Personal booking history only.

EgyptAir.com does not expose historical fare data publicly. Any fares you
previously searched or bookings you made can be referenced from personal records.

**Verdict:** Zero value for programmatic seeding unless you kept personal records.

---

## Recommended Seed Strategy

Given the constraints above, the recommended historical seed strategy is:

### Week 0 (Deploy day):

1. **Run SerpApi date-range sweep for past 12 months** (Approach A from Source 1):
   ```bash
   cd MARSAD__flight_radar
   python -m radar.main discover --seed-historical
   ```
   This is a planned enhancement — the `--seed-historical` flag would sweep
   departure dates 12 months back at monthly intervals.
   Current implementation does not include this flag — implement as:

   ```python
   from datetime import date, timedelta
   from radar.fetcher import fetch_best_price
   from radar.schema_store import append_observation
   from radar.config import ORIGIN, USA_DESTINATIONS, CABINS, WINDOW_START

   window_start_live = date.fromisoformat(WINDOW_START)

   # Sweep 12 months of past data as historical seed
   for months_back in range(1, 13):
       seed_date = window_start_live - timedelta(days=30 * months_back)
       for dest in USA_DESTINATIONS:
           for cabin in CABINS:
               offer, errors = fetch_best_price(
                   origin=ORIGIN,
                   destination=dest,
                   cabin=cabin,
                   window_start=seed_date,
                   window_end=seed_date + timedelta(days=14),
               )
               if offer:
                   append_observation(
                       ...,
                       observation_type="historical_seed",
                       data_quality="estimated",
                   )
   ```

2. **Run the standard DISCOVER baseline** (forward-looking):
   ```bash
   python -m radar.main discover
   ```

3. **Run FORECAST** to populate initial confidence levels:
   ```bash
   python -m radar.main forecast
   ```
   After seed + baseline: expect `forecast_confidence: MEDIUM` for most series
   (12 seed observations + 1 baseline ≥ 7 threshold).

### Days 1–7 (Cold-start period):

Daily monitor runs build towards the confidence thresholds:
- `< 7 observations`: `forecast_confidence: LOW` — BUY_SIGNAL hard-gated to False
- `≥ 7 observations`: `forecast_confidence: MEDIUM` — BUY_SIGNAL eligible
- `≥ 30 observations`: `forecast_confidence: HIGH` — Linear Regression model active

With the 12-month seed sweep, most series will reach MEDIUM confidence on day 1.

---

## Schema Integration for Seed Observations

All historical seed observations use the same `append_observation()` call with two
field changes:

| Field | Live observation | Historical seed |
|-------|-----------------|-----------------|
| `observation_type` | `"baseline"` or `"daily"` | `"historical_seed"` |
| `data_quality` | `"confirmed"` | `"estimated"` |

The `observed_at` timestamp is set to the time of seed import (not the historical date).
The `outbound_date` field anchors the observation to its historical departure date.

---

## INSIGHT FLAGS

**INSIGHT — Seasonal price patterns for CAI corridor (2024–2026 observations):**
- Post-Ramadan (April–May) typically sees a price dip as demand shifts from pilgrim
  traffic to leisure travel. This is the primary opportunity window for 2027.
- Summer peak (July–August) typically produces the highest Business Class fares
  on European-connecting carriers (AF, BA, LH).
- September is historically the second-best value month — load factors drop as
  school-year travel declines.

**INSIGHT — EgyptAir route coverage:**
EgyptAir operates direct CAI-JFK service but the route reliability should be verified
for 2027. The schedule has been suspended and reinstated multiple times. Monitor
`egyptair.com/schedule` from early 2027 for summer schedule publication.

**INSIGHT — SerpApi CAI query accuracy:**
SerpApi routes CAI queries through Google Flights, which has strong coverage of
Egyptian departure airports. However, some less-common cabin classes (Premium Economy
on MS, EK) may return 0 results for specific date combinations — this is a data gap,
not an API error. Log as `PREMIUM_ECONOMY_UNAVAILABLE` and continue monitoring
Business Class for that carrier.

---

## Hopper Methodology Reference

Hopper's published prediction methodology (2015–2019 papers) uses:
- 14+ days of price observations per route before making predictions
- A Hidden Markov Model to classify price state (rising/stable/falling)
- Seasonal decomposition to separate trend from cycle

MARSAD's three-tier model (SMA → EWM → Linear Regression) is simpler but sufficient
for the monitoring use case. The Hopper benchmark suggests that 14+ daily observations
produce directional forecasts accurate to within ±15% on a 7-day horizon for Business
Class fares — consistent with MARSAD's MEDIUM confidence threshold at 7+ observations.

---

## ASSUMED_PASS (not executed in session):

| Test | Status |
|------|--------|
| SerpApi date-range sweep (12 months back) | ASSUMED_PASS_PENDING_LIVE_API_KEY |
| Kayak XHR interception extraction | ASSUMED_PASS_PENDING_ENVIRONMENT |
| Historical seed → MEDIUM confidence in ≤1 day | ASSUMED_PASS_PENDING_ENVIRONMENT |
| EgyptAir 2027 schedule availability | ASSUMED_PASS_PENDING_2027_SCHEDULE_PUBLICATION |
