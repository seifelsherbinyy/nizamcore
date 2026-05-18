"""
MARSAD Executive Dashboard — live HTTP server at http://localhost:7329

Auto-refreshing price intelligence dashboard backed by flight_prices.json.
Zero external Python dependencies (uses stdlib http.server + Chart.js CDN).

Usage:
    python -m radar.main dashboard            # default port 7329
    python -m radar.main dashboard --port 8080
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger(__name__)

DEFAULT_PORT = 7329
DEFAULT_HOST = "127.0.0.1"

_CARRIER = {
    "MS": "EgyptAir", "EK": "Emirates", "QR": "Qatar Airways",
    "LH": "Lufthansa", "AF": "Air France", "BA": "British Airways",
    "TK": "Turkish", "IT": "ITA Airways", "KL": "KLM",
    "EY": "Etihad", "UA": "United", "AA": "American", "DL": "Delta",
}

_CITY = {
    "JFK": "New York", "LAX": "Los Angeles", "ORD": "Chicago",
    "ATL": "Atlanta", "MIA": "Miami", "SFO": "San Francisco",
    "IAD": "Washington DC", "BOS": "Boston", "EWR": "Newark",
    "DFW": "Dallas", "SEA": "Seattle", "LAS": "Las Vegas",
}

_DEST_ORDER = ["JFK", "EWR", "BOS", "MIA", "ATL", "ORD", "DFW", "IAD", "LAX", "SFO", "SEA", "LAS"]


def _load_store() -> dict:
    from radar.config import FLIGHT_PRICES_PATH
    if not FLIGHT_PRICES_PATH.exists():
        return {"routes": {}, "metadata": {}, "last_updated": ""}
    try:
        return json.loads(FLIGHT_PRICES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"routes": {}, "metadata": {}, "last_updated": ""}


def _api_data() -> dict:
    store = _load_store()
    routes = store.get("routes", {})

    matrix: dict = {}
    all_series: list = []
    buy_signals: list = []
    total_obs = 0
    recent_obs: list = []

    for dest in _DEST_ORDER:
        route_key = f"CAI-{dest}"
        route = routes.get(route_key, {})
        matrix[dest] = {}

        for series_key, sd in sorted(route.get("observations", {}).items()):
            cabin = sd["cabin"]
            carrier = sd.get("carrier", "?")
            series = sd.get("observation_series", [])
            fc = sd.get("forecast", {})
            obs_count = fc.get("observation_count", 0)
            total_obs += obs_count

            if not series:
                matrix[dest][cabin] = {
                    "status": "unavailable", "carrier": carrier,
                    "cn": _CARRIER.get(carrier, carrier), "obs_count": 0, "price": None,
                }
                continue

            latest = series[-1]
            price = latest["price_usd"]
            delta_pct = latest.get("delta_pct")
            history = [{"t": o["observed_at"][:16].replace("T", " "), "p": o["price_usd"]} for o in series]
            buy_signal = fc.get("buy_signal", False)
            confidence = fc.get("forecast_confidence", "LOW")
            p20 = fc.get("historical_20th_percentile")

            entry = {
                "status": "ok",
                "price": price,
                "carrier": carrier,
                "cn": _CARRIER.get(carrier, carrier),
                "delta_pct": delta_pct,
                "obs_count": obs_count,
                "buy_signal": buy_signal,
                "confidence": confidence,
                "p20": p20,
                "outbound_date": latest.get("outbound_date"),
                "history": history,
            }
            matrix[dest][cabin] = entry

            if buy_signal:
                buy_signals.append({
                    "dest": dest, "city": _CITY.get(dest, dest),
                    "cabin": cabin, "carrier": carrier,
                    "cn": _CARRIER.get(carrier, carrier),
                    "price": price, "delta_pct": delta_pct,
                })

            all_series.append({
                "dest": dest, "city": _CITY.get(dest, dest),
                "cabin": cabin, "carrier": carrier,
                "cn": _CARRIER.get(carrier, carrier),
                "price": price, "obs_count": obs_count,
                "delta_pct": delta_pct, "history": history,
                "outbound_date": latest.get("outbound_date"),
                "buy_signal": buy_signal, "confidence": confidence,
            })

            for obs in series:
                recent_obs.append({
                    "dest": dest, "city": _CITY.get(dest, dest),
                    "cabin": cabin, "carrier": carrier,
                    "cn": _CARRIER.get(carrier, carrier),
                    "price": obs["price_usd"],
                    "delta_pct": obs.get("delta_pct"),
                    "observed_at": obs.get("observed_at", ""),
                    "obs_type": obs.get("observation_type", ""),
                    "outbound_date": obs.get("outbound_date", ""),
                })

    recent_obs.sort(key=lambda x: x["observed_at"], reverse=True)
    biz = sorted([x for x in all_series if x["cabin"] == "BUSINESS" and x["price"]], key=lambda x: x["price"])
    pe = sorted([x for x in all_series if x["cabin"] == "PREMIUM_ECONOMY" and x["price"]], key=lambda x: x["price"])

    return {
        "matrix": matrix,
        "buy_signals": buy_signals,
        "all_series": all_series,
        "biz_sorted": biz,
        "pe_sorted": pe,
        "recent_obs": recent_obs[:40],
        "summary": {
            "total_observations": total_obs,
            "buy_signals_active": len(buy_signals),
            "routes_tracked": len([k for k in routes if routes[k]]),
            "series_with_data": len(all_series),
            "last_updated": store.get("last_updated", ""),
            "window_start": store.get("metadata", {}).get("travel_window_start", ""),
            "window_end": store.get("metadata", {}).get("travel_window_end", ""),
            "best_biz": biz[0] if biz else None,
            "best_pe": pe[0] if pe else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MARSAD مرصد — NIZAM Flight Intelligence</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#010d1f;--bg1:#061629;--bg2:#0b2040;--bg3:#102a50;
  --border:#1e3d6e;--border2:#2a5490;
  --text:#e2e8f0;--muted:#64748b;--dim:#1e293b;
  --blue:#3b82f6;--blue-bg:rgba(59,130,246,.12);
  --green:#22c55e;--green-bg:rgba(34,197,94,.12);
  --red:#ef4444;--red-bg:rgba(239,68,68,.12);
  --amber:#f59e0b;--amber-bg:rgba(245,158,11,.12);
  --cyan:#06b6d4;--purple:#a855f7;
}
*{margin:0;padding:0;box-sizing:border-box}
html{font-size:14px}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh;line-height:1.5}
a{color:var(--blue);text-decoration:none}

/* ── TOP BAR ── */
.topbar{background:var(--bg1);border-bottom:1px solid var(--border);padding:10px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.brand{display:flex;align-items:baseline;gap:10px}
.brand-arabic{font-size:22px;font-weight:700;color:var(--blue);letter-spacing:1px}
.brand-name{font-size:18px;font-weight:800;color:var(--text);letter-spacing:2px}
.brand-sub{font-size:11px;color:var(--muted);letter-spacing:1px;text-transform:uppercase}
.status-row{display:flex;align-items:center;gap:20px;font-size:12px;color:var(--muted)}
.live-dot{width:8px;height:8px;border-radius:50%;background:var(--green);display:inline-block;animation:pulse 2s infinite}
.live-label{color:var(--green);font-weight:600;letter-spacing:1px}
.ts-block{display:flex;flex-direction:column;align-items:flex-end;gap:2px}
.ts-main{font-size:12px;color:var(--text)}
.ts-ago{font-size:11px;color:var(--muted)}
.refresh-timer{font-size:11px;color:var(--muted);display:flex;align-items:center;gap:6px}
.timer-ring{width:14px;height:14px;border-radius:50%;border:2px solid var(--dim);border-top-color:var(--blue);animation:spin 60s linear infinite}

/* ── MAIN LAYOUT ── */
.main{padding:20px 24px;max-width:1480px;margin:0 auto}
section{margin-bottom:24px}
.section-title{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;display:flex;align-items:center;gap:8px}
.section-title::after{content:'';flex:1;height:1px;background:var(--border)}

/* ── KPI CARDS ── */
.kpi-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}
.kpi-card{background:var(--bg1);border:1px solid var(--border);border-radius:10px;padding:16px 20px;position:relative;overflow:hidden}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent,var(--blue))}
.kpi-card.green{--accent:var(--green)}
.kpi-card.amber{--accent:var(--amber)}
.kpi-card.red{--accent:var(--red)}
.kpi-card.purple{--accent:var(--purple)}
.kpi-label{font-size:10px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px}
.kpi-value{font-size:28px;font-weight:800;color:var(--text);line-height:1;margin-bottom:6px}
.kpi-sub{font-size:11px;color:var(--muted)}
.kpi-badge{display:inline-flex;align-items:center;gap:4px;font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;margin-top:4px}
.badge-green{background:var(--green-bg);color:var(--green)}
.badge-amber{background:var(--amber-bg);color:var(--amber)}
.badge-red{background:var(--red-bg);color:var(--red)}
.badge-blue{background:var(--blue-bg);color:var(--blue)}
.badge-muted{background:var(--bg2);color:var(--muted)}

/* ── PRICE MATRIX ── */
.matrix-wrap{background:var(--bg1);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.matrix-wrap table{width:100%;border-collapse:collapse}
.matrix-wrap thead th{background:var(--bg2);padding:10px 14px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);text-align:left;border-bottom:1px solid var(--border)}
.matrix-wrap thead th.cabin-header{text-align:center;color:var(--text);font-size:11px}
.matrix-wrap tbody tr{border-bottom:1px solid var(--dim)}
.matrix-wrap tbody tr:last-child{border-bottom:none}
.matrix-wrap tbody tr:hover{background:var(--bg2)}
.cell-route{padding:12px 14px}
.cell-route .dest-code{font-size:16px;font-weight:800;color:var(--text)}
.cell-route .dest-city{font-size:11px;color:var(--muted);margin-top:1px}
.price-cell{padding:10px 14px;text-align:center;min-width:160px}
.price-cell.no-data{color:var(--muted);font-size:12px}
.price-main{font-size:20px;font-weight:800;letter-spacing:-0.5px}
.price-carrier{font-size:10px;color:var(--muted);margin-top:2px;font-weight:500}
.price-meta{display:flex;justify-content:center;align-items:center;gap:8px;margin-top:4px}
.delta-up{color:var(--red);font-size:11px;font-weight:600}
.delta-down{color:var(--green);font-size:11px;font-weight:600}
.delta-flat{color:var(--muted);font-size:11px}
.obs-pip{font-size:10px;color:var(--muted);background:var(--bg2);padding:1px 6px;border-radius:8px}
.conf-badge{font-size:9px;font-weight:700;padding:1px 5px;border-radius:4px;text-transform:uppercase;letter-spacing:.5px}
.conf-LOW{background:var(--dim);color:var(--muted)}
.conf-MEDIUM{background:var(--amber-bg);color:var(--amber)}
.conf-HIGH{background:var(--green-bg);color:var(--green)}
.signal-glow{animation:signalPulse 1.5s infinite}
/* Price heat tiers */
.heat-best{background:rgba(34,197,94,.08)}
.heat-low{background:rgba(34,197,94,.04)}
.heat-mid{background:transparent}
.heat-high{background:rgba(245,158,11,.05)}
.heat-max{background:rgba(239,68,68,.07)}

/* ── CHARTS GRID ── */
.charts-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.chart-card{background:var(--bg1);border:1px solid var(--border);border-radius:10px;padding:20px}
.chart-title{font-size:13px;font-weight:700;color:var(--text);margin-bottom:4px}
.chart-sub{font-size:11px;color:var(--muted);margin-bottom:16px}
.chart-wrap{position:relative}

/* ── TREND LINE SECTION ── */
.trend-card{background:var(--bg1);border:1px solid var(--border);border-radius:10px;padding:20px}
.trend-filters{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.filter-btn{background:var(--bg2);border:1px solid var(--border);color:var(--muted);padding:4px 12px;border-radius:16px;font-size:11px;cursor:pointer;transition:.15s}
.filter-btn.active{background:var(--blue-bg);border-color:var(--blue);color:var(--blue)}
.filter-btn:hover{border-color:var(--border2);color:var(--text)}

/* ── PROGRESS SECTION ── */
.progress-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.progress-card{background:var(--bg1);border:1px solid var(--border);border-radius:10px;padding:16px}
.prog-title{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:12px}
.prog-row{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.prog-label{min-width:120px;font-size:11px;color:var(--text)}
.prog-code{font-size:10px;font-weight:700;color:var(--muted);background:var(--bg2);padding:1px 5px;border-radius:4px;margin-right:2px}
.prog-bar-track{flex:1;height:6px;background:var(--bg2);border-radius:3px;overflow:hidden}
.prog-bar-fill{height:100%;border-radius:3px;transition:width .4s}
.prog-count{font-size:11px;color:var(--muted);min-width:32px;text-align:right}
.prog-check{font-size:13px}

/* ── OBSERVATIONS TABLE ── */
.obs-wrap{background:var(--bg1);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.obs-table{width:100%;border-collapse:collapse}
.obs-table thead th{background:var(--bg2);padding:8px 12px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);text-align:left;border-bottom:1px solid var(--border)}
.obs-table tbody td{padding:8px 12px;border-bottom:1px solid var(--dim);font-size:12px;vertical-align:middle}
.obs-table tbody tr:last-child td{border-bottom:none}
.obs-table tbody tr:hover{background:var(--bg2)}
.type-badge{font-size:9px;font-weight:700;padding:2px 6px;border-radius:4px;text-transform:uppercase;letter-spacing:.5px}
.type-baseline{background:var(--blue-bg);color:var(--blue)}
.type-daily{background:var(--bg2);color:var(--muted)}

/* ── BUY SIGNAL BANNER ── */
.signal-banner{background:linear-gradient(135deg,rgba(34,197,94,.15),rgba(6,182,212,.1));border:1px solid var(--green);border-radius:10px;padding:16px 20px;display:none}
.signal-banner.visible{display:block}
.signal-header{display:flex;align-items:center;gap:10px;font-size:14px;font-weight:800;color:var(--green);margin-bottom:10px}
.signal-item{display:flex;align-items:center;gap:12px;padding:8px 0;border-top:1px solid rgba(34,197,94,.15)}

/* ── FOOTER ── */
.footer{background:var(--bg1);border-top:1px solid var(--border);padding:16px 24px;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--muted);margin-top:8px}
.footer-left{display:flex;gap:20px}

/* ── ANIMATIONS ── */
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes signalPulse{0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,.4)}50%{box-shadow:0 0 0 6px rgba(34,197,94,0)}}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.fade-in{animation:fadeIn .3s ease}

/* ── RESPONSIVE ── */
@media(max-width:900px){
  .kpi-grid{grid-template-columns:repeat(3,1fr)}
  .charts-grid{grid-template-columns:1fr}
  .progress-grid{grid-template-columns:1fr}
}
@media(max-width:600px){
  .kpi-grid{grid-template-columns:1fr 1fr}
  .topbar{flex-direction:column;gap:8px;align-items:flex-start}
}
</style>
</head>
<body>

<!-- ═══ TOP BAR ═══ -->
<header class="topbar">
  <div class="brand">
    <span class="brand-arabic">مرصد</span>
    <span class="brand-name">MARSAD</span>
    <span class="brand-sub">NIZAM Flight Intelligence</span>
  </div>
  <div class="status-row">
    <span class="live-dot"></span>
    <span class="live-label">LIVE</span>
    <div class="ts-block">
      <span class="ts-main" id="ts-main">Loading…</span>
      <span class="ts-ago" id="ts-ago"></span>
    </div>
    <div class="refresh-timer">
      <div class="timer-ring" id="timer-ring"></div>
      <span id="refresh-countdown">60s</span>
    </div>
  </div>
</header>

<div class="main">

  <!-- ═══ BUY SIGNAL BANNER ═══ -->
  <div class="signal-banner" id="signal-banner">
    <div class="signal-header">
      <span>🎯</span><span>BUY_SIGNAL ACTIVE</span>
    </div>
    <div id="signal-items"></div>
  </div>

  <!-- ═══ KPI ROW ═══ -->
  <section>
    <div class="kpi-grid" id="kpi-grid">
      <div class="kpi-card green">
        <div class="kpi-label">Best Business</div>
        <div class="kpi-value" id="kpi-biz-price">—</div>
        <div class="kpi-sub" id="kpi-biz-route">—</div>
      </div>
      <div class="kpi-card blue">
        <div class="kpi-label">Best Premium Eco</div>
        <div class="kpi-value" id="kpi-pe-price">—</div>
        <div class="kpi-sub" id="kpi-pe-route">—</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Routes Tracked</div>
        <div class="kpi-value" id="kpi-routes">—</div>
        <div class="kpi-sub">CAI → USA destinations</div>
      </div>
      <div class="kpi-card purple">
        <div class="kpi-label">Observations</div>
        <div class="kpi-value" id="kpi-obs">—</div>
        <div class="kpi-sub" id="kpi-obs-sub">building baseline</div>
      </div>
      <div class="kpi-card amber" id="kpi-signal-card">
        <div class="kpi-label">BUY_SIGNALs</div>
        <div class="kpi-value" id="kpi-signals">0</div>
        <div class="kpi-sub" id="kpi-signals-sub">needs 7+ observations</div>
      </div>
    </div>
  </section>

  <!-- ═══ PRICE MATRIX ═══ -->
  <section>
    <div class="section-title">Price Matrix — CAI → USA &nbsp; <span style="color:var(--text);font-size:10px;font-weight:400" id="matrix-date"></span></div>
    <div class="matrix-wrap">
      <table>
        <thead>
          <tr>
            <th style="width:160px">Destination</th>
            <th class="cabin-header" colspan="1" style="width:200px">✈ Business Class</th>
            <th class="cabin-header" style="width:40px"></th>
            <th class="cabin-header" colspan="1" style="width:200px">✈ Premium Economy</th>
            <th class="cabin-header" style="width:40px"></th>
          </tr>
        </thead>
        <tbody id="matrix-body"></tbody>
      </table>
    </div>
  </section>

  <!-- ═══ PRICE COMPARISON CHARTS ═══ -->
  <section>
    <div class="section-title">Price Comparison — All Routes</div>
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">Business Class</div>
        <div class="chart-sub" id="biz-chart-sub">Sorted lowest → highest</div>
        <div class="chart-wrap"><canvas id="chart-biz" height="320"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">Premium Economy</div>
        <div class="chart-sub" id="pe-chart-sub">Sorted lowest → highest</div>
        <div class="chart-wrap"><canvas id="chart-pe" height="320"></canvas></div>
      </div>
    </div>
  </section>

  <!-- ═══ PRICE TREND ═══ -->
  <section>
    <div class="section-title">Price Trend Over Time</div>
    <div class="trend-card">
      <div class="trend-filters" id="trend-filters"></div>
      <div class="chart-wrap"><canvas id="chart-trend" height="220"></canvas></div>
    </div>
  </section>

  <!-- ═══ PROGRESS TO BUY_SIGNAL ═══ -->
  <section>
    <div class="section-title">Progress to BUY_SIGNAL &nbsp; <span style="color:var(--muted);font-size:10px;font-weight:400">7 observations unlock alert eligibility per series</span></div>
    <div class="progress-grid">
      <div class="progress-card">
        <div class="prog-title">Business Class</div>
        <div id="prog-biz"></div>
      </div>
      <div class="progress-card">
        <div class="prog-title">Premium Economy</div>
        <div id="prog-pe"></div>
      </div>
    </div>
  </section>

  <!-- ═══ RECENT OBSERVATIONS ═══ -->
  <section>
    <div class="section-title">Observation Log</div>
    <div class="obs-wrap">
      <table class="obs-table">
        <thead>
          <tr>
            <th>Timestamp (UTC)</th>
            <th>Route</th>
            <th>Cabin</th>
            <th>Carrier</th>
            <th>Price (USD)</th>
            <th>Δ vs Prev</th>
            <th>Dep Date</th>
            <th>Type</th>
          </tr>
        </thead>
        <tbody id="obs-body"></tbody>
      </table>
    </div>
  </section>

</div>

<!-- ═══ FOOTER ═══ -->
<footer class="footer">
  <div class="footer-left">
    <span>Source: SerpApi / Google Flights</span>
    <span>Travel window: <span id="ft-window">—</span></span>
    <span>Booking horizon: ~2027-03-19 (305-day cap)</span>
  </div>
  <span id="ft-updated"></span>
</footer>

<script>
// ── State ────────────────────────────────────────────────────────────────────
const S = { data: null, charts: { biz: null, pe: null, trend: null }, refreshAt: null, countdown: 60, activeFilter: 'ALL' };

// ── Destination order ────────────────────────────────────────────────────────
const DEST_ORDER = ["JFK","EWR","BOS","MIA","ATL","ORD","DFW","IAD","LAX","SFO","SEA","LAS"];
const CITY = { JFK:"New York",EWR:"Newark",BOS:"Boston",MIA:"Miami",ATL:"Atlanta",ORD:"Chicago",DFW:"Dallas",IAD:"Washington DC",LAX:"Los Angeles",SFO:"San Francisco",SEA:"Seattle",LAS:"Las Vegas" };

// ── Utilities ─────────────────────────────────────────────────────────────────
function fmt$(n) { return n == null ? '—' : '$' + n.toLocaleString('en-US', {maximumFractionDigits:0}); }
function fmtDelta(pct) {
  if (pct == null) return '<span class="delta-flat">—</span>';
  if (pct > 0.1) return `<span class="delta-up">▲ +${pct.toFixed(1)}%</span>`;
  if (pct < -0.1) return `<span class="delta-down">▼ ${pct.toFixed(1)}%</span>`;
  return '<span class="delta-flat">↔ 0%</span>';
}
function fmtTS(iso) {
  if (!iso) return '—';
  return iso.replace('T',' ').substring(0,16) + ' UTC';
}
function timeAgo(iso) {
  if (!iso) return '';
  const diff = Math.round((Date.now() - new Date(iso)) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}
function heatClass(price, minP, maxP) {
  if (!price || minP === maxP) return '';
  const t = (price - minP) / (maxP - minP);
  if (t < 0.1) return 'heat-best';
  if (t < 0.33) return 'heat-low';
  if (t < 0.67) return 'heat-mid';
  if (t < 0.90) return 'heat-high';
  return 'heat-max';
}
function priceColor(price, minP, maxP) {
  if (!price || minP >= maxP) return '#3b82f6';
  const t = (price - minP) / (maxP - minP);
  const r = Math.round(34  + (239-34)  * t);
  const g = Math.round(197 + (68-197)  * t);
  const b = Math.round(94  + (68-94)   * t);
  return `rgba(${r},${g},${b},0.85)`;
}

// ── Data Fetch ────────────────────────────────────────────────────────────────
async function fetchData() {
  try {
    const r = await fetch('/api/data');
    S.data = await r.json();
    S.refreshAt = new Date();
    renderAll();
  } catch(e) {
    document.getElementById('ts-ago').textContent = 'fetch error — retrying…';
  }
}

// ── Render Orchestrator ───────────────────────────────────────────────────────
function renderAll() {
  const d = S.data;
  if (!d) return;
  renderHeader(d.summary, d.generated_at);
  renderKPIs(d.summary);
  renderSignalBanner(d.buy_signals);
  renderMatrix(d.matrix, d.biz_sorted, d.pe_sorted);
  renderBarCharts(d.biz_sorted, d.pe_sorted);
  renderTrendChart(d.all_series);
  renderProgress(d.all_series);
  renderObsTable(d.recent_obs);
  renderFooter(d.summary);
}

// ── Header ────────────────────────────────────────────────────────────────────
function renderHeader(summary, genAt) {
  const ts = summary.last_updated || genAt;
  document.getElementById('ts-main').textContent = fmtTS(ts);
  document.getElementById('ts-ago').textContent = timeAgo(ts);
  S.countdown = 60;
}

// ── KPI Cards ─────────────────────────────────────────────────────────────────
function renderKPIs(s) {
  if (s.best_biz) {
    document.getElementById('kpi-biz-price').textContent = fmt$(s.best_biz.price);
    document.getElementById('kpi-biz-route').textContent = `${CITY[s.best_biz.dest]||s.best_biz.dest} · ${s.best_biz.cn}`;
  }
  if (s.best_pe) {
    document.getElementById('kpi-pe-price').textContent = fmt$(s.best_pe.price);
    document.getElementById('kpi-pe-route').textContent = `${CITY[s.best_pe.dest]||s.best_pe.dest} · ${s.best_pe.cn}`;
  }
  document.getElementById('kpi-routes').textContent = s.routes_tracked;
  document.getElementById('kpi-obs').textContent = s.total_observations;
  const seriesCount = s.series_with_data || 0;
  const need = Math.max(0, seriesCount * 7 - s.total_observations);
  document.getElementById('kpi-obs-sub').textContent = need > 0
    ? `+${need} obs to unlock all alerts`
    : seriesCount > 0 ? 'all series alert-eligible' : 'building baseline';
  const sigs = s.buy_signals_active;
  document.getElementById('kpi-signals').textContent = sigs;
  document.getElementById('kpi-signals-sub').textContent = sigs > 0
    ? (sigs === 1 ? '1 active signal' : `${sigs} active signals`)
    : `${s.total_observations} obs · need ${seriesCount * 7} total`;
  const card = document.getElementById('kpi-signal-card');
  card.className = 'kpi-card ' + (sigs > 0 ? 'green signal-glow' : 'amber');
}

// ── Signal Banner ─────────────────────────────────────────────────────────────
function renderSignalBanner(signals) {
  const banner = document.getElementById('signal-banner');
  const items = document.getElementById('signal-items');
  if (!signals || signals.length === 0) { banner.classList.remove('visible'); return; }
  banner.classList.add('visible');
  items.innerHTML = signals.map(s =>
    `<div class="signal-item">
       <strong>${s.dest}</strong> <span style="color:var(--muted)">${CITY[s.dest]||s.dest}</span>
       <span style="background:var(--bg2);padding:2px 8px;border-radius:4px;font-size:11px">${s.cabin.replace('_',' ')}</span>
       <span>${s.cn}</span>
       <span style="font-size:18px;font-weight:800;color:var(--green)">${fmt$(s.price)}</span>
       ${fmtDelta(s.delta_pct)}
     </div>`
  ).join('');
}

// ── Price Matrix ──────────────────────────────────────────────────────────────
function renderMatrix(matrix, bizSorted, peSorted) {
  const bizPrices = bizSorted.map(x => x.price);
  const pePrices  = peSorted.map(x => x.price);
  const bizMin = Math.min(...bizPrices), bizMax = Math.max(...bizPrices);
  const peMin  = Math.min(...pePrices),  peMax  = Math.max(...pePrices);

  // Set matrix date from first available outbound date
  const firstBiz = bizSorted[0];
  if (firstBiz && firstBiz.outbound_date) {
    document.getElementById('matrix-date').textContent = `Departure: ${firstBiz.outbound_date}`;
  }

  const tbody = document.getElementById('matrix-body');
  tbody.innerHTML = DEST_ORDER.map(dest => {
    const biz = matrix[dest] && matrix[dest]['BUSINESS'];
    const pe  = matrix[dest] && matrix[dest]['PREMIUM_ECONOMY'];

    function cellHTML(entry, minP, maxP) {
      if (!entry || entry.status === 'unavailable') {
        return `<td class="price-cell no-data" colspan="1">—<br><span style="font-size:10px">no data</span></td><td></td>`;
      }
      const heat = heatClass(entry.price, minP, maxP);
      const signalMark = entry.buy_signal ? ' 🎯' : '';
      return `
        <td class="price-cell ${heat}">
          <div class="price-main" style="color:${priceColor(entry.price,minP,maxP)}">${fmt$(entry.price)}${signalMark}</div>
          <div class="price-carrier">${entry.cn} (${entry.carrier})</div>
          <div class="price-meta">
            ${fmtDelta(entry.delta_pct)}
            <span class="obs-pip">${entry.obs_count}×</span>
            <span class="conf-badge conf-${entry.confidence}">${entry.confidence}</span>
          </div>
        </td>
        <td style="width:10px;padding:0"></td>`;
    }

    return `<tr>
      <td class="cell-route">
        <div class="dest-code">${dest}</div>
        <div class="dest-city">${CITY[dest]||dest}</div>
      </td>
      ${cellHTML(biz, bizMin, bizMax)}
      ${cellHTML(pe, peMin, peMax)}
    </tr>`;
  }).join('');
}

// ── Bar Charts ────────────────────────────────────────────────────────────────
function renderBarCharts(bizSorted, peSorted) {
  renderBarChart('chart-biz', S.charts, 'biz', bizSorted, 'biz');
  renderBarChart('chart-pe',  S.charts, 'pe',  peSorted, 'pe');
}

function renderBarChart(canvasId, charts, key, sorted, type) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !sorted.length) return;

  const labels = sorted.map(x => `${x.dest} · ${x.cn}`);
  const prices = sorted.map(x => x.price);
  const minP = prices[0], maxP = prices[prices.length-1];
  const colors = prices.map(p => priceColor(p, minP, maxP));
  const borderColors = colors.map(c => c.replace('0.85','1'));

  const subEl = document.getElementById(type === 'biz' ? 'biz-chart-sub' : 'pe-chart-sub');
  if (subEl) {
    const range = maxP - minP;
    subEl.textContent = `Range: ${fmt$(minP)} – ${fmt$(maxP)} (spread ${fmt$(range)}) · ${sorted.length} routes`;
  }

  const cfg = {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: prices,
        backgroundColor: colors,
        borderColor: borderColors,
        borderWidth: 1,
        borderRadius: 4,
        borderSkipped: false,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const item = sorted[ctx.dataIndex];
              const d = item.delta_pct != null ? ` (Δ ${item.delta_pct > 0 ? '+' : ''}${item.delta_pct?.toFixed(1)}%)` : '';
              return ` ${fmt$(ctx.raw)}${d} · ${item.obs_count} obs`;
            }
          },
          backgroundColor: '#0b2040',
          borderColor: '#1e3d6e',
          borderWidth: 1,
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(30,61,110,.4)' },
          ticks: { color: '#64748b', font: { size: 11 }, callback: v => '$' + v.toLocaleString() },
          border: { color: '#1e3d6e' }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#94a3b8', font: { size: 11 } },
          border: { color: '#1e3d6e' }
        }
      }
    }
  };

  if (charts[key]) { charts[key].destroy(); }
  charts[key] = new Chart(canvas, cfg);
}

// ── Trend Line Chart ──────────────────────────────────────────────────────────
function renderTrendChart(allSeries) {
  const canvas = document.getElementById('chart-trend');
  if (!canvas) return;

  // Build filter buttons
  const filters = document.getElementById('trend-filters');
  if (!filters.innerHTML) {
    const opts = ['ALL', 'BUSINESS', 'PREMIUM_ECONOMY'];
    filters.innerHTML = opts.map(o =>
      `<button class="filter-btn ${o === S.activeFilter ? 'active' : ''}" onclick="setFilter('${o}')">${o.replace('_',' ')}</button>`
    ).join('');
  }

  const active = S.activeFilter;
  const series = allSeries.filter(s => active === 'ALL' || s.cabin === active);

  // Only show series with > 1 observation (trend needs 2+ points)
  const trendable = series.filter(s => s.history && s.history.length > 1);

  if (!trendable.length) {
    // Show "accumulating" placeholder
    if (S.charts.trend) { S.charts.trend.destroy(); S.charts.trend = null; }
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#1e3d6e';
    ctx.font = '13px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Trend chart populates after 2nd observation per series', canvas.width/2, canvas.height/2 - 10);
    ctx.fillStyle = '#64748b';
    ctx.font = '11px -apple-system, sans-serif';
    ctx.fillText('Next daily monitor run will unlock trend visualization', canvas.width/2, canvas.height/2 + 12);
    return;
  }

  // Collect all unique timestamps
  const allTs = [...new Set(trendable.flatMap(s => s.history.map(h => h.t)))].sort();

  const COLORS = ['#3b82f6','#22c55e','#f59e0b','#ef4444','#a855f7','#06b6d4','#84cc16','#f97316','#ec4899','#14b8a6','#8b5cf6','#fbbf24'];

  const datasets = trendable.map((s, i) => ({
    label: `${s.dest} ${s.cabin === 'BUSINESS' ? 'BIZ' : 'PE'} (${s.cn})`,
    data: allTs.map(t => {
      const pt = s.history.find(h => h.t === t);
      return pt ? pt.p : null;
    }),
    borderColor: COLORS[i % COLORS.length],
    backgroundColor: COLORS[i % COLORS.length] + '20',
    borderWidth: 2,
    pointRadius: 4,
    pointHoverRadius: 6,
    tension: 0.2,
    spanGaps: true,
  }));

  const cfg = {
    type: 'line',
    data: { labels: allTs, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 12, padding: 12 } },
        tooltip: { backgroundColor: '#0b2040', borderColor: '#1e3d6e', borderWidth: 1,
          callbacks: { label: ctx => ` ${ctx.dataset.label}: ${fmt$(ctx.raw)}` } }
      },
      scales: {
        x: { grid: { color: 'rgba(30,61,110,.3)' }, ticks: { color: '#64748b', font: { size: 10 } }, border: { color: '#1e3d6e' } },
        y: { grid: { color: 'rgba(30,61,110,.3)' }, ticks: { color: '#64748b', font: { size: 10 }, callback: v => '$' + v.toLocaleString() }, border: { color: '#1e3d6e' } }
      }
    }
  };

  if (S.charts.trend) { S.charts.trend.destroy(); }
  S.charts.trend = new Chart(canvas, cfg);
}

function setFilter(f) {
  S.activeFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.textContent.replace(' ','_') === f || (f === 'ALL' && b.textContent === 'ALL')));
  if (S.data) renderTrendChart(S.data.all_series);
}

// ── Progress to BUY_SIGNAL ────────────────────────────────────────────────────
function renderProgress(allSeries) {
  const TARGET = 7;
  function rows(series) {
    return series.map(s => {
      const pct = Math.min(100, Math.round((s.obs_count / TARGET) * 100));
      const done = s.obs_count >= TARGET;
      const color = done ? 'var(--green)' : pct >= 50 ? 'var(--blue)' : 'var(--muted)';
      const check = done ? '✓' : '';
      return `<div class="prog-row">
        <div class="prog-label"><span class="prog-code">${s.dest}</span>${s.cn.substring(0,10)}</div>
        <div class="prog-bar-track">
          <div class="prog-bar-fill" style="width:${pct}%;background:${color}"></div>
        </div>
        <div class="prog-count" style="color:${color}">${s.obs_count}/${TARGET}</div>
        <div class="prog-check" style="color:var(--green)">${check}</div>
      </div>`;
    }).join('');
  }

  const biz = allSeries.filter(s => s.cabin === 'BUSINESS').sort((a,b) => a.dest.localeCompare(b.dest));
  const pe  = allSeries.filter(s => s.cabin === 'PREMIUM_ECONOMY').sort((a,b) => a.dest.localeCompare(b.dest));
  document.getElementById('prog-biz').innerHTML = rows(biz);
  document.getElementById('prog-pe').innerHTML  = rows(pe);
}

// ── Observations Table ────────────────────────────────────────────────────────
function renderObsTable(obs) {
  const tbody = document.getElementById('obs-body');
  if (!obs || !obs.length) { tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--muted)">No observations yet</td></tr>'; return; }
  tbody.innerHTML = obs.slice(0, 30).map(o => {
    const typeClass = o.obs_type === 'baseline' ? 'type-baseline' : 'type-daily';
    return `<tr>
      <td style="color:var(--muted);font-size:11px">${fmtTS(o.observed_at)}</td>
      <td><strong>CAI→${o.dest}</strong> <span style="color:var(--muted);font-size:11px">${o.city}</span></td>
      <td style="font-size:11px">${o.cabin.replace('_',' ')}</td>
      <td>${o.cn} <span style="color:var(--muted);font-size:10px">(${o.carrier})</span></td>
      <td style="font-weight:700;color:${o.price ? 'var(--text)' : 'var(--muted)'}">${fmt$(o.price)}</td>
      <td>${fmtDelta(o.delta_pct)}</td>
      <td style="color:var(--muted);font-size:11px">${o.outbound_date||'—'}</td>
      <td><span class="type-badge ${typeClass}">${o.obs_type||'—'}</span></td>
    </tr>`;
  }).join('');
}

// ── Footer ────────────────────────────────────────────────────────────────────
function renderFooter(s) {
  if (s.window_start && s.window_end) {
    document.getElementById('ft-window').textContent = `${s.window_start} → ${s.window_end}`;
  }
  if (s.last_updated) {
    document.getElementById('ft-updated').textContent = `Store updated: ${fmtTS(s.last_updated)}`;
  }
}

// ── Refresh Timer ─────────────────────────────────────────────────────────────
function tick() {
  S.countdown = Math.max(0, S.countdown - 1);
  document.getElementById('refresh-countdown').textContent = `${S.countdown}s`;
  if (S.refreshAt) {
    document.getElementById('ts-ago').textContent = timeAgo(S.refreshAt.toISOString());
  }
  if (S.countdown === 0) {
    S.countdown = 60;
    fetchData();
    // Restart spin animation
    const ring = document.getElementById('timer-ring');
    ring.style.animation = 'none';
    ring.offsetHeight;
    ring.style.animation = 'spin 60s linear infinite';
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────────
fetchData();
setInterval(tick, 1000);
</script>
</body>
</html>"""


class _DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = _HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/data":
            data = _api_data()
            body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass  # suppress per-request access logs


def run_dashboard(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Start the dashboard HTTP server (blocking)."""
    server = HTTPServer((host, port), _DashboardHandler)
    url = f"http://{host}:{port}"
    print(f"\n  MARSAD مرصد Executive Dashboard")
    print(f"  ──────────────────────────────")
    print(f"  URL:       {url}")
    print(f"  API:       {url}/api/data")
    print(f"  Refresh:   every 60 seconds")
    print(f"  Stop:      Ctrl+C\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Dashboard stopped.")
        server.server_close()
