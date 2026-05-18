"""
STAGE 4 — FORECAST: Historical Trend and Price Prediction

Three-tier model, automatically selected by observation count:
  Tier 1 — Simple Moving Average (SMA): < 7 observations (but see cold-start note)
  Tier 2 — Exponential Weighted Mean (EWM): 7–29 observations
  Tier 3 — Linear Regression: 30+ observations

Confidence levels:
  LOW:    < 7 observations (cold-start — BUY_SIGNAL hard-gated to False)
  MEDIUM: 7–29 observations
  HIGH:   30+ observations

Forecast output per series:
  horizon_7d, horizon_14d, horizon_30d: {low, mid, high} price predictions in USD
  buy_signal: True ONLY when current_price < 7d_forecast_low AND current_price < historical_20th_pct
              AND confidence ≥ MEDIUM

Output written to the 'forecast' block in the schema store.
NEVER touches observation_series — append-only invariant maintained.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

from radar.config import (
    FORECAST_LOW_CONFIDENCE_THRESHOLD,
    FORECAST_MEDIUM_CONFIDENCE_THRESHOLD,
    HISTORICAL_PERCENTILE_THRESHOLD,
)
from radar.schema_store import get_all_series_keys, get_series, update_forecast

logger = logging.getLogger(__name__)


def _confidence_level(n: int) -> str:
    if n < FORECAST_LOW_CONFIDENCE_THRESHOLD:
        return "LOW"
    elif n < FORECAST_MEDIUM_CONFIDENCE_THRESHOLD:
        return "MEDIUM"
    return "HIGH"


def _forecast_sma(prices: list[float], horizons: list[int]) -> dict[int, dict]:
    """
    Simple Moving Average forecast.
    Uses last min(7, n) prices. Returns {horizon: {low, mid, high}}.
    Spread: ±1 standard deviation of recent prices.
    """
    window = min(7, len(prices))
    recent = prices[-window:]
    mid = np.mean(recent)
    std = np.std(recent) if len(recent) > 1 else mid * 0.05

    result = {}
    for h in horizons:
        result[h] = {
            "low": round(float(max(0, mid - std)), 2),
            "mid": round(float(mid), 2),
            "high": round(float(mid + std), 2),
        }
    return result


def _forecast_ewm(prices: list[float], horizons: list[int]) -> dict[int, dict]:
    """
    Exponential Weighted Mean forecast.
    span=7 gives recent observations more weight than older ones.
    Trend: difference between EWM and SMA of same window (directional signal).
    """
    s = pd.Series(prices)
    ewm_val = float(s.ewm(span=7, adjust=False).mean().iloc[-1])

    # Estimate trend from last 7 observations
    if len(prices) >= 7:
        recent_trend = (prices[-1] - prices[-7]) / 7  # avg daily change
    else:
        recent_trend = 0.0

    std = float(s.std()) if len(prices) > 1 else ewm_val * 0.05

    result = {}
    for h in horizons:
        projected_mid = ewm_val + recent_trend * h
        result[h] = {
            "low": round(float(max(0, projected_mid - std)), 2),
            "mid": round(float(projected_mid), 2),
            "high": round(float(projected_mid + std), 2),
        }
    return result


def _forecast_linear_regression(prices: list[float], horizons: list[int]) -> dict[int, dict]:
    """
    Linear regression on the time series.
    x = observation index (0..n-1), y = price.
    Extrapolates trend forward by horizon days.
    """
    n = len(prices)
    x = np.arange(n, dtype=float)
    y = np.array(prices, dtype=float)

    # Least squares fit
    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs[0], coeffs[1]

    residuals = y - (slope * x + intercept)
    std = float(np.std(residuals))

    result = {}
    for h in horizons:
        x_future = n - 1 + h
        mid = float(slope * x_future + intercept)
        result[h] = {
            "low": round(float(max(0, mid - 1.5 * std)), 2),
            "mid": round(float(max(0, mid)), 2),
            "high": round(float(mid + 1.5 * std), 2),
        }
    return result


def _select_model(n: int) -> str:
    if n >= FORECAST_MEDIUM_CONFIDENCE_THRESHOLD:
        return "lr"
    elif n >= FORECAST_LOW_CONFIDENCE_THRESHOLD:
        return "ewm"
    return "sma"


def _compute_buy_signal(
    current_price: float,
    forecast_7d: dict,
    historical_20th_pct: Optional[float],
    confidence: str,
) -> bool:
    """
    BUY_SIGNAL requires ALL of:
    1. current_price < 7d_forecast_low
    2. current_price < historical_20th_percentile
    3. confidence ≥ MEDIUM (hard gate — no exceptions)
    """
    if confidence == "LOW":
        return False  # Hard gate: no BUY_SIGNAL during cold-start
    if forecast_7d.get("low") is None:
        return False
    if historical_20th_pct is None:
        return False

    condition_forecast = current_price < forecast_7d["low"]
    condition_percentile = current_price < historical_20th_pct
    return condition_forecast and condition_percentile


def run_forecast() -> dict:
    """
    Update forecast for all series in the store.
    Uses the appropriate model tier based on observation count.

    Returns summary dict.
    """
    all_keys = get_all_series_keys()
    horizons = [7, 14, 30]

    stats = {
        "stage": "FORECAST",
        "series_updated": 0,
        "series_low_confidence": 0,
        "series_medium_confidence": 0,
        "series_high_confidence": 0,
        "buy_signals": 0,
        "models_used": {"sma": 0, "ewm": 0, "lr": 0},
    }

    for key_info in all_keys:
        origin = key_info["origin"]
        destination = key_info["destination"]
        carrier = key_info["carrier"]
        cabin = key_info["cabin"]
        n = key_info["observation_count"]

        if n == 0:
            continue

        series = get_series(origin, destination, carrier, cabin)
        prices = [obs["price_usd"] for obs in series]
        current_price = prices[-1]

        confidence = _confidence_level(n)
        model = _select_model(n)
        stats["models_used"][model] += 1

        # Select and run model
        if model == "lr":
            forecasts = _forecast_linear_regression(prices, horizons)
        elif model == "ewm":
            forecasts = _forecast_ewm(prices, horizons)
        else:
            forecasts = _forecast_sma(prices, horizons)

        historical_p20 = (
            float(np.percentile(prices[:-1], HISTORICAL_PERCENTILE_THRESHOLD))
            if len(prices) > 1
            else None
        )

        buy_signal = _compute_buy_signal(
            current_price=current_price,
            forecast_7d=forecasts.get(7, {}),
            historical_20th_pct=historical_p20,
            confidence=confidence,
        )

        forecast_data = {
            "observation_count": n,
            "forecast_confidence": confidence,
            "horizon_7d": forecasts.get(7, {"low": None, "mid": None, "high": None}),
            "horizon_14d": forecasts.get(14, {"low": None, "mid": None, "high": None}),
            "horizon_30d": forecasts.get(30, {"low": None, "mid": None, "high": None}),
            "buy_signal": buy_signal,
            "historical_20th_percentile": round(historical_p20, 2) if historical_p20 else None,
            "model_used": model,
        }

        update_forecast(origin, destination, carrier, cabin, forecast_data)
        stats["series_updated"] += 1

        if confidence == "LOW":
            stats["series_low_confidence"] += 1
        elif confidence == "MEDIUM":
            stats["series_medium_confidence"] += 1
        else:
            stats["series_high_confidence"] += 1

        if buy_signal:
            stats["buy_signals"] += 1
            logger.info(
                "FORECAST BUY_SIGNAL: %s→%s %s %s current=$%.0f 7d_low=$%.0f p20=$%.0f",
                origin, destination, carrier, cabin,
                current_price,
                forecasts[7]["low"],
                historical_p20 or 0,
            )
        else:
            logger.debug(
                "FORECAST: %s→%s %s %s confidence=%s model=%s 7d_mid=$%.0f",
                origin, destination, carrier, cabin, confidence, model,
                forecasts.get(7, {}).get("mid") or 0,
            )

    logger.info(
        "FORECAST complete: %d updated, %d LOW, %d MEDIUM, %d HIGH, %d buy_signals",
        stats["series_updated"],
        stats["series_low_confidence"],
        stats["series_medium_confidence"],
        stats["series_high_confidence"],
        stats["buy_signals"],
    )

    return stats
