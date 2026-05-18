"""
STAGE 3 — ALERT: Price Drop Signal Detection

BUY_SIGNAL requires ALL THREE of:
  1. Single-day price drop ≥ threshold (ALERT_THRESHOLD_PCT% OR absolute drop)
  2. Current price < 20th percentile of all historical observations for this series
  3. forecast_confidence ≥ MEDIUM (i.e. ≥ 7 observations) — hard gate, no exceptions

A single condition alone is insufficient. The cold-start gate (condition 3) prevents
false alerts during the first 7 days when there is no reliable historical baseline.

Alert thresholds (configurable via .env):
  Business Class:    10% single-day drop OR $200 absolute drop
  Premium Economy:   10% single-day drop OR $100 absolute drop

Alert output: written to ALERTS_DIR/radar_alerts.json + console (configurable via ALERT_DELIVERY).

Alert record fields:
  alert_id, triggered_at, carrier, route, cabin, current_price, previous_price,
  drop_usd, drop_pct, historical_percentile, forecast_signal (buy/watch/hold),
  buy_signal (bool), observation_id, confidence_gate_passed (bool)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

import numpy as np

from radar.config import (
    ALERT_DELIVERY,
    ALERT_THRESHOLD_BUSINESS_USD,
    ALERT_THRESHOLD_PCT,
    ALERT_THRESHOLD_PREMIUM_ECONOMY_USD,
    ALERTS_DIR,
    FORECAST_LOW_CONFIDENCE_THRESHOLD,
    HISTORICAL_PERCENTILE_THRESHOLD,
    RADAR_ALERTS_PATH,
)
from radar.schema_store import get_all_series_keys, get_series, load_store, mark_alert

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _percentile_rank(prices: list[float], current_price: float) -> float:
    """Return the percentile rank of current_price within prices (0–100)."""
    if not prices:
        return 50.0
    return float(np.sum(np.array(prices) <= current_price) / len(prices) * 100)


def _historical_20th_percentile(prices: list[float]) -> Optional[float]:
    if len(prices) < 2:
        return None
    return float(np.percentile(prices, HISTORICAL_PERCENTILE_THRESHOLD))


def _drop_threshold_met(drop_usd: float, drop_pct: float, cabin: str) -> bool:
    """Check if the price drop meets the alert threshold (percentage OR absolute)."""
    abs_threshold = (
        ALERT_THRESHOLD_BUSINESS_USD
        if cabin.upper() == "BUSINESS"
        else ALERT_THRESHOLD_PREMIUM_ECONOMY_USD
    )
    pct_met = drop_pct >= ALERT_THRESHOLD_PCT
    abs_met = drop_usd >= abs_threshold
    return pct_met or abs_met


def _confidence_gate_passed(observation_count: int) -> bool:
    """Hard gate: BUY_SIGNAL cannot fire with fewer than FORECAST_LOW_CONFIDENCE_THRESHOLD observations."""
    return observation_count >= FORECAST_LOW_CONFIDENCE_THRESHOLD


def run_alert() -> dict:
    """
    Scan all series for the most recent observation and evaluate BUY_SIGNAL conditions.

    Returns summary dict with alert statistics.
    """
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)

    store = load_store()
    all_keys = get_all_series_keys(store)

    stats = {
        "stage": "ALERT",
        "series_scanned": 0,
        "buy_signals_triggered": 0,
        "watch_signals_triggered": 0,
        "alerts": [],
    }

    for key_info in all_keys:
        origin = key_info["origin"]
        destination = key_info["destination"]
        carrier = key_info["carrier"]
        cabin = key_info["cabin"]
        obs_count = key_info["observation_count"]

        series = get_series(origin, destination, carrier, cabin)
        if len(series) < 2:
            # Need at least 2 observations to calculate a delta
            continue

        stats["series_scanned"] += 1

        current_obs = series[-1]
        previous_obs = series[-2]

        current_price = current_obs["price_usd"]
        previous_price = previous_obs["price_usd"]

        drop_usd = previous_price - current_price
        drop_pct = (drop_usd / previous_price * 100) if previous_price > 0 else 0.0

        if drop_usd <= 0:
            # Price didn't drop — no alert evaluation needed
            continue

        all_prices = [obs["price_usd"] for obs in series]
        p20 = _historical_20th_percentile(all_prices[:-1])  # percentile from history excluding current
        current_pct_rank = _percentile_rank(all_prices[:-1], current_price)

        # Evaluate all three BUY_SIGNAL conditions
        condition_1_threshold = _drop_threshold_met(drop_usd, drop_pct, cabin)
        condition_2_below_p20 = (p20 is not None and current_price < p20)
        condition_3_confidence = _confidence_gate_passed(obs_count)

        buy_signal = condition_1_threshold and condition_2_below_p20 and condition_3_confidence

        # Watch signal: conditions 1 met but cold-start gate blocks BUY_SIGNAL
        watch_signal = condition_1_threshold and not condition_3_confidence

        if not (buy_signal or watch_signal or condition_1_threshold):
            continue

        # Determine forecast signal from store
        rk = f"{origin}-{destination}"
        sk = f"{carrier}-{cabin}"
        forecast = {}
        try:
            forecast = store["routes"][rk]["observations"][sk]["forecast"]
        except KeyError:
            pass

        forecast_signal = "HOLD"
        if buy_signal:
            forecast_signal = "BUY"
        elif watch_signal:
            forecast_signal = "WATCH_COLD_START"
        elif condition_1_threshold:
            forecast_signal = "WATCH"

        alert = {
            "alert_id": str(uuid4()),
            "triggered_at": _utcnow(),
            "carrier": carrier,
            "route": f"{origin}-{destination}",
            "cabin": cabin,
            "current_price_usd": current_price,
            "previous_price_usd": previous_price,
            "drop_usd": round(drop_usd, 2),
            "drop_pct": round(drop_pct, 2),
            "historical_20th_percentile": round(p20, 2) if p20 is not None else None,
            "current_percentile_rank": round(current_pct_rank, 1),
            "observation_count": obs_count,
            "forecast_signal": forecast_signal,
            "buy_signal": buy_signal,
            "condition_1_threshold_met": condition_1_threshold,
            "condition_2_below_p20": condition_2_below_p20,
            "condition_3_confidence_gate_passed": condition_3_confidence,
            "observation_id": current_obs["observation_id"],
            "outbound_date": current_obs["outbound_date"],
            "return_date": current_obs["return_date"],
            "outbound_routing": current_obs["outbound_routing"],
            "forecast_horizon_7d": forecast.get("horizon_7d"),
        }

        stats["alerts"].append(alert)
        if buy_signal:
            stats["buy_signals_triggered"] += 1
        if watch_signal:
            stats["watch_signals_triggered"] += 1

        # Mark the observation in the store
        mark_alert(origin, destination, carrier, cabin, current_obs["observation_id"])

        # Deliver the alert
        _deliver_alert(alert)

    logger.info(
        "ALERT complete: %d scanned, %d BUY_SIGNAL, %d WATCH",
        stats["series_scanned"],
        stats["buy_signals_triggered"],
        stats["watch_signals_triggered"],
    )

    # Append all alerts to the alerts log
    if stats["alerts"]:
        _append_alerts_log(stats["alerts"])

    return stats


def _deliver_alert(alert: dict) -> None:
    """Deliver an alert via the configured delivery method."""
    message = _format_alert_text(alert)

    if ALERT_DELIVERY in ("console_and_file", "console"):
        _print_alert(message, alert)

    if ALERT_DELIVERY in ("console_and_file", "file"):
        pass  # Written in batch via _append_alerts_log

    if ALERT_DELIVERY == "slack":
        _send_slack(message)

    if ALERT_DELIVERY == "webhook":
        _send_webhook(alert)


def _format_alert_text(alert: dict) -> str:
    signal_emoji = "🚨 BUY_SIGNAL" if alert["buy_signal"] else "👀 WATCH"
    return (
        f"\n{'='*60}\n"
        f"MARSAD ALERT — {signal_emoji}\n"
        f"{'='*60}\n"
        f"Carrier:        {alert['carrier']}\n"
        f"Route:          {alert['route']}\n"
        f"Cabin:          {alert['cabin']}\n"
        f"Current Price:  ${alert['current_price_usd']:,.0f} USD\n"
        f"Previous Price: ${alert['previous_price_usd']:,.0f} USD\n"
        f"Drop:           ${alert['drop_usd']:,.0f} ({alert['drop_pct']:.1f}%)\n"
        f"Percentile:     {alert['current_percentile_rank']:.0f}th (20th = ${alert['historical_20th_percentile'] or 'N/A'})\n"
        f"Observations:   {alert['observation_count']}\n"
        f"Forecast:       {alert['forecast_signal']}\n"
        f"Depart:         {alert['outbound_date']} → {alert['return_date']}\n"
        f"Routing:        {alert['outbound_routing']}\n"
        f"Triggered at:   {alert['triggered_at']}\n"
        f"{'='*60}\n"
    )


def _print_alert(message: str, alert: dict) -> None:
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        color = "bold red" if alert["buy_signal"] else "bold yellow"
        console.print(Panel(message, style=color))
    except ImportError:
        print(message)


def _append_alerts_log(alerts: list[dict]) -> None:
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)

    existing = []
    if RADAR_ALERTS_PATH.exists():
        try:
            with open(RADAR_ALERTS_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            existing = []

    existing.extend(alerts)

    tmp_path = RADAR_ALERTS_PATH.with_suffix(".tmp")
    try:
        serialized = json.dumps(existing, indent=2, ensure_ascii=False)
        json.loads(serialized)  # validate round-trip
        tmp_path.write_text(serialized, encoding="utf-8")
        import os
        os.replace(tmp_path, RADAR_ALERTS_PATH)
        logger.info("Alerts log updated: %d total alerts", len(existing))
    except Exception as exc:
        logger.error("Failed to write alerts log: %s", exc)
        tmp_path.unlink(missing_ok=True)


def _send_slack(message: str) -> None:
    from radar.config import SLACK_WEBHOOK_URL
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not configured")
        return
    try:
        import requests
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Slack alert sent")
    except Exception as exc:
        logger.error("Slack alert failed: %s", exc)


def _send_webhook(alert: dict) -> None:
    from radar.config import ALERT_WEBHOOK_URL
    if not ALERT_WEBHOOK_URL:
        logger.warning("ALERT_WEBHOOK_URL not configured")
        return
    try:
        import requests
        resp = requests.post(ALERT_WEBHOOK_URL, json=alert, timeout=10)
        resp.raise_for_status()
        logger.info("Webhook alert sent")
    except Exception as exc:
        logger.error("Webhook alert failed: %s", exc)
