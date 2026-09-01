#!/usr/bin/env python3
"""
feature_engine.py — Deterministic rolling health feature engine.

Owning contract: NIZAM-HEALTH-INTELLIGENCE v0.2.0 (BADAN / Health Intelligence)
Phase: cloud-first reconciliation — VPS operational plane
Storage class: vps_private / strict_local (VPS-only; never Drive-synced raw)

DOCTRINE (03_METRIC_DICTIONARY_AND_CALCULATION_SPEC.md):
  * All arithmetic here is deterministic Python. No LLM computes or sources a value.
  * Missing inputs yield null / insufficient_data. NEVER imputed.
  * Provider metrics are stored, not recomputed.
  * Personal baselines, not population norms.
  * Every rule is versioned by METHODS_VERSION and is recalibratable.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Sequence

METHODS_VERSION = "nhi-0.2.0-mvp1"
WINDOWS: tuple[int, ...] = (3, 7, 14, 30, 90)

# 0.67448975 == Phi^-1(0.75); scales MAD to a normal-consistent sigma.
ROBUST_Z_SCALE = 0.67448975

# BADAN doctrine: a 7-day trend requires at least 4 of 7 daily signals.
BADAN_MIN_OBS_7 = 4


# ─────────────────────────── pure statistics ────────────────────────────
# These are intentionally dependency-free and side-effect-free so they can be
# unit-tested against hand-computed expectations.

def _clean(values: Iterable[Optional[float]]) -> List[float]:
    """Drop None/NaN. Never substitutes a replacement value."""
    out: List[float] = []
    for v in values:
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isnan(f) or math.isinf(f):
            continue
        out.append(f)
    return out


def mean(values: Sequence[float]) -> Optional[float]:
    vals = _clean(values)
    if not vals:
        return None
    return sum(vals) / len(vals)


def median(values: Sequence[float]) -> Optional[float]:
    vals = sorted(_clean(values))
    n = len(vals)
    if n == 0:
        return None
    mid = n // 2
    if n % 2 == 1:
        return vals[mid]
    return (vals[mid - 1] + vals[mid]) / 2.0


def sample_sd(values: Sequence[float]) -> Optional[float]:
    """Sample standard deviation (n-1). Null if n < 2, per spec guard."""
    vals = _clean(values)
    n = len(vals)
    if n < 2:
        return None
    m = sum(vals) / n
    var = sum((x - m) ** 2 for x in vals) / (n - 1)
    return math.sqrt(var)


def mad(values: Sequence[float]) -> Optional[float]:
    """Median absolute deviation: median(|x - median(x)|)."""
    vals = _clean(values)
    if not vals:
        return None
    med = median(vals)
    if med is None:
        return None
    return median([abs(x - med) for x in vals])


def percentile_rank(values: Sequence[float], x: Optional[float]) -> Optional[float]:
    """
    Empirical percentile rank of x within values, tie-corrected:
        (n_less + 0.5 * n_equal) / n
    Returns 0..1. Null if x is missing or window empty.
    """
    if x is None:
        return None
    vals = _clean(values)
    n = len(vals)
    if n == 0:
        return None
    n_less = sum(1 for v in vals if v < x)
    n_equal = sum(1 for v in vals if v == x)
    return (n_less + 0.5 * n_equal) / n


def robust_z(values: Sequence[float], x_today: Optional[float]) -> tuple[Optional[float], List[str]]:
    """
    robust_z = ROBUST_Z_SCALE * (x_today - median) / mad
    Returns (value, flags). MAD == 0 yields (None, ['zero_mad']) per spec.
    """
    flags: List[str] = []
    if x_today is None:
        return None, ["today_missing"]
    vals = _clean(values)
    if not vals:
        return None, ["insufficient_data"]
    med = median(vals)
    m = mad(vals)
    if m is None:
        return None, ["insufficient_data"]
    if m == 0:
        flags.append("zero_mad")
        return None, flags
    return ROBUST_Z_SCALE * (float(x_today) - med) / m, flags


def ols_slope(points: Sequence[tuple[float, float]]) -> Optional[float]:
    """
    Ordinary-least-squares slope of value versus elapsed day.
    points = [(elapsed_day, value), ...]. Null if n < 2 or x has zero variance.
    Carries no causal meaning; callers must expose n and coverage alongside.
    """
    pts = [(float(a), float(b)) for a, b in points
           if a is not None and b is not None
           and not math.isnan(float(b)) and not math.isinf(float(b))]
    n = len(pts)
    if n < 2:
        return None
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    num = sum((p[0] - mx) * (p[1] - my) for p in pts)
    den = sum((p[0] - mx) ** 2 for p in pts)
    if den == 0:
        return None
    return num / den


# ───────────────────── windowed summary construction ────────────────────

def summarize_window(
    series: Dict[date, Optional[float]],
    end_date: date,
    window_days: int,
    today_value: Optional[float],
) -> Dict[str, object]:
    """
    Build the deterministic stat block for one metric over one window.

    `series` maps Cairo local date -> value (or None). The window is the
    `window_days` calendar days ending at and including `end_date`.
    coverage distinguishes missingness from stability.
    """
    start_date = end_date - timedelta(days=window_days - 1)
    dates = [start_date + timedelta(days=i) for i in range(window_days)]

    pairs: List[tuple[float, float]] = []
    values: List[float] = []
    for i, d in enumerate(dates):
        v = series.get(d)
        if v is None:
            continue
        values.append(float(v))
        pairs.append((float(i), float(v)))

    n_obs = len(values)
    coverage = n_obs / window_days if window_days else None

    rz, rz_flags = robust_z(values, today_value)

    block: Dict[str, object] = {
        "window_days": window_days,
        "date_range": [start_date.isoformat(), end_date.isoformat()],
        "n_obs": n_obs,
        "coverage": round(coverage, 4) if coverage is not None else None,
        "mean": _r(mean(values)),
        "median": _r(median(values)),
        "sd": _r(sample_sd(values)),
        "mad": _r(mad(values)),
        "pctl_today": _r(percentile_rank(values, today_value)),
        "robust_z": _r(rz),
        "slope_per_day": _r(ols_slope(pairs)),
        "flags": rz_flags,
    }

    if n_obs == 0:
        block["flags"] = list(block["flags"]) + ["insufficient_data"]

    # Preserve existing BADAN doctrine for the 7-day window.
    if window_days == 7:
        block["badan_trend_eligible"] = n_obs >= BADAN_MIN_OBS_7
        block["badan_min_obs_required"] = BADAN_MIN_OBS_7

    return block


def acceleration_proxy_7(series: Dict[date, Optional[float]], end_date: date) -> Optional[float]:
    """
    slope(last 7d) - slope(previous 7d).
    A trend-CHANGE proxy. Not a physical acceleration. Null if either
    sub-window cannot produce a slope.
    """
    def _slope_for(anchor: date) -> Optional[float]:
        start = anchor - timedelta(days=6)
        pts = []
        for i in range(7):
            d = start + timedelta(days=i)
            v = series.get(d)
            if v is not None:
                pts.append((float(i), float(v)))
        return ols_slope(pts)

    recent = _slope_for(end_date)
    prior = _slope_for(end_date - timedelta(days=7))
    if recent is None or prior is None:
        return None
    return recent - prior


def personal_baseline(
    series: Dict[date, Optional[float]],
    end_date: date,
) -> Dict[str, object]:
    """
    Personal baseline, never a population norm.
      center     = trailing 30d median EXCLUDING the target observation
      dispersion = trailing 30d MAD
    Widen to 90d when 30d evidence is insufficient. Null when both insufficient.
    """
    def _collect(days: int) -> List[float]:
        start = end_date - timedelta(days=days)          # exclusive of end_date
        vals = []
        d = start
        while d < end_date:
            v = series.get(d)
            if v is not None:
                vals.append(float(v))
            d += timedelta(days=1)
        return vals

    for window in (30, 90):
        vals = _collect(window)
        if len(vals) >= 2:
            return {
                "center": _r(median(vals)),
                "dispersion": _r(mad(vals)),
                "basis_window_days": window,
                "n_obs": len(vals),
                "policy": "trailing_median_excl_target",
            }
    return {
        "center": None,
        "dispersion": None,
        "basis_window_days": None,
        "n_obs": len(_collect(90)),
        "policy": "trailing_median_excl_target",
        "flags": ["insufficient_data"],
    }


def build_metric_features(
    series: Dict[date, Optional[float]],
    end_date: date,
) -> Dict[str, object]:
    """Full deterministic feature set for a single metric."""
    today_value = series.get(end_date)
    return {
        "today": _r(today_value),
        "today_present": today_value is not None,
        "baseline": personal_baseline(series, end_date),
        "acceleration_proxy_7": _r(acceleration_proxy_7(series, end_date)),
        "windows": {
            str(w): summarize_window(series, end_date, w, today_value)
            for w in WINDOWS
        },
    }


def assess_data_quality(
    metric_features: Dict[str, Dict[str, object]],
) -> Dict[str, object]:
    """
    Four visible confidence dimensions rather than one opaque score.
    The display label comes from a versioned deterministic ruleset.
    """
    cov7: List[float] = []
    signs: List[int] = []
    for feats in metric_features.values():
        w = feats.get("windows", {})
        b7 = w.get("7") if isinstance(w, dict) else None
        if isinstance(b7, dict) and b7.get("coverage") is not None:
            cov7.append(float(b7["coverage"]))
        slopes = []
        for wd in ("7", "14", "30"):
            blk = w.get(wd) if isinstance(w, dict) else None
            if isinstance(blk, dict) and blk.get("slope_per_day") is not None:
                slopes.append(float(blk["slope_per_day"]))
        if len(slopes) >= 2:
            signs.append(1 if all(s >= 0 for s in slopes) or all(s <= 0 for s in slopes) else 0)

    avg_cov7 = (sum(cov7) / len(cov7)) if cov7 else 0.0
    stability = (sum(signs) / len(signs)) if signs else None

    if avg_cov7 >= 0.85 and (stability is None or stability >= 0.6):
        label = "high"
    elif avg_cov7 >= 0.55:
        label = "medium"
    else:
        label = "low"

    return {
        "quantity": {
            "avg_coverage_7d": round(avg_cov7, 4),
            "metrics_evaluated": len(metric_features),
        },
        "source_quality": "provider_objective_wearable",
        "stability": {
            "slope_sign_agreement": round(stability, 4) if stability is not None else None
        },
        "confounding": "unknown",
        "display_label": label,
        "ruleset_version": METHODS_VERSION,
    }


def _r(v: Optional[float], places: int = 6) -> Optional[float]:
    """Round for stable JSON output. None passes through untouched."""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, places)
