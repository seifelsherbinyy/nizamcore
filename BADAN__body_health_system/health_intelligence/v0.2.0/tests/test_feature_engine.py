#!/usr/bin/env python3
"""
test_feature_engine.py — Statistical correctness tests for the deterministic engine.

Owning contract: NIZAM-HEALTH-INTELLIGENCE v0.2.0 (BADAN / Health Intelligence)
Phase: cloud-first reconciliation — VPS operational plane

Expectations below are HAND-COMPUTED. If the engine changes, prove the new
number by hand before touching a test.
"""
import math
import os
import sys
from datetime import date, timedelta

# Location-independent import: works from the repo root, from the VPS install
# path, and from inside the sync container where sync/ is mounted elsewhere.
_HERE = os.path.dirname(os.path.abspath(__file__))
_SYNC = os.path.join(os.path.dirname(_HERE), "sync")
if _SYNC not in sys.path:
    sys.path.insert(0, _SYNC)

from feature_engine import (  # noqa: E402
    BADAN_MIN_OBS_7,
    METHODS_VERSION,
    ROBUST_Z_SCALE,
    WINDOWS,
    acceleration_proxy_7,
    assess_data_quality,
    build_metric_features,
    mad,
    mean,
    median,
    ols_slope,
    percentile_rank,
    personal_baseline,
    robust_z,
    sample_sd,
    summarize_window,
)

APPROX = 1e-9


# ───────────────────────────── median ─────────────────────────────
def test_median_odd():
    assert median([3, 1, 2]) == 2


def test_median_even():
    # sorted [1,2,3,4] -> (2+3)/2
    assert median([4, 1, 3, 2]) == 2.5


def test_median_empty_is_none():
    assert median([]) is None


# ───────────────────────────── mean ───────────────────────────────
def test_mean_basic():
    assert mean([1, 2, 3, 4]) == 2.5


def test_mean_empty_is_none():
    assert mean([]) is None


# ─────────────────────────── sample sd ────────────────────────────
def test_sample_sd_three_values():
    # [1,2,3]: mean 2, var = ((1)+(0)+(1))/2 = 1 -> sd 1.0
    assert abs(sample_sd([1, 2, 3]) - 1.0) < APPROX


def test_sample_sd_four_values():
    # [1,2,3,4]: mean 2.5, var = (2.25+0.25+0.25+2.25)/3 = 5/3
    assert abs(sample_sd([1, 2, 3, 4]) - math.sqrt(5.0 / 3.0)) < APPROX


def test_sample_sd_null_when_n_lt_2():
    """Spec guard: return null if n<2. Must not return 0."""
    assert sample_sd([5]) is None
    assert sample_sd([]) is None


# ───────────────────────────── mad ────────────────────────────────
def test_mad_four_values():
    # [1,2,3,4]: median 2.5, deviations [1.5,.5,.5,1.5], median -> 1.0
    assert abs(mad([1, 2, 3, 4]) - 1.0) < APPROX


def test_mad_three_values():
    # [1,2,3]: median 2, deviations [1,0,1], median -> 1.0
    assert abs(mad([1, 2, 3]) - 1.0) < APPROX


def test_mad_identical_values_is_zero():
    assert mad([7, 7, 7]) == 0


# ────────────────────── percentile rank ───────────────────────────
def test_percentile_rank_tie_corrected():
    # [1,2,3,4], x=3 -> (n_less 2 + 0.5*1)/4 = 0.625
    assert abs(percentile_rank([1, 2, 3, 4], 3) - 0.625) < APPROX


def test_percentile_rank_minimum():
    # x=1 -> (0 + 0.5*1)/4 = 0.125
    assert abs(percentile_rank([1, 2, 3, 4], 1) - 0.125) < APPROX


def test_percentile_rank_missing_today_is_none():
    assert percentile_rank([1, 2, 3], None) is None


# ─────────────────────────── robust z ─────────────────────────────
def test_robust_z_zero_mad_returns_none_and_flag():
    """MAD==0 must yield null plus an explicit zero_mad flag, never inf."""
    val, flags = robust_z([10, 10, 10], 12)
    assert val is None
    assert "zero_mad" in flags


def test_robust_z_known_value():
    # [1,2,3,4]: median 2.5, mad 1.0, x=4
    # z = 0.67448975 * (4-2.5)/1.0
    val, flags = robust_z([1, 2, 3, 4], 4)
    assert abs(val - ROBUST_Z_SCALE * 1.5) < APPROX
    assert flags == []


def test_robust_z_missing_today():
    val, flags = robust_z([1, 2, 3], None)
    assert val is None
    assert "today_missing" in flags


# ─────────────────────────── ols slope ────────────────────────────
def test_ols_slope_perfect_line():
    # y = 2x
    assert abs(ols_slope([(0, 0), (1, 2), (2, 4)]) - 2.0) < APPROX


def test_ols_slope_negative():
    assert abs(ols_slope([(0, 10), (1, 8), (2, 6)]) - (-2.0)) < APPROX


def test_ols_slope_flat_is_zero():
    assert abs(ols_slope([(0, 5), (1, 5), (2, 5)]) - 0.0) < APPROX


def test_ols_slope_null_when_single_point():
    assert ols_slope([(0, 1)]) is None


def test_ols_slope_null_when_x_no_variance():
    assert ols_slope([(3, 1), (3, 2)]) is None


# ───────────────────── no-imputation guarantee ────────────────────
def test_missing_values_are_dropped_not_imputed():
    """
    A window with gaps must reduce n_obs/coverage, NOT fill with a mean.
    """
    end = date(2026, 9, 1)
    series = {end: 10.0, end - timedelta(days=1): None, end - timedelta(days=2): 20.0}
    block = summarize_window(series, end, 3, 10.0)
    assert block["n_obs"] == 2
    # coverage is emitted rounded to 4dp for stable JSON; assert that exactly.
    assert block["coverage"] == round(2 / 3, 4)
    # mean of the two present values only — the None must NOT become 15 or 0
    assert abs(block["mean"] - 15.0) < APPROX
    assert block["n_obs"] != 3


def test_empty_window_flags_insufficient_data():
    end = date(2026, 9, 1)
    block = summarize_window({}, end, 7, None)
    assert block["n_obs"] == 0
    assert block["coverage"] == 0.0
    assert block["mean"] is None
    assert "insufficient_data" in block["flags"]


# ──────────────────── BADAN 7-day doctrine ────────────────────────
def test_badan_trend_requires_4_of_7():
    end = date(2026, 9, 1)
    # exactly 3 observations -> not eligible
    s3 = {end - timedelta(days=i): 5.0 for i in range(3)}
    assert summarize_window(s3, end, 7, 5.0)["badan_trend_eligible"] is False
    # exactly 4 observations -> eligible
    s4 = {end - timedelta(days=i): 5.0 for i in range(4)}
    assert summarize_window(s4, end, 7, 5.0)["badan_trend_eligible"] is True
    assert BADAN_MIN_OBS_7 == 4


# ─────────────────── acceleration proxy (7d) ──────────────────────
def test_acceleration_proxy_detects_trend_change():
    """
    Prior 7d flat (slope 0), recent 7d rising (slope +1) -> proxy = +1.
    """
    end = date(2026, 9, 1)
    series = {}
    # previous 7-day block ending end-7: all 10 -> slope 0
    prior_anchor = end - timedelta(days=7)
    for i in range(7):
        series[prior_anchor - timedelta(days=6 - i)] = 10.0
    # recent 7-day block ending end: 10,11,...,16 -> slope +1
    for i in range(7):
        series[end - timedelta(days=6 - i)] = 10.0 + i
    proxy = acceleration_proxy_7(series, end)
    assert abs(proxy - 1.0) < 1e-9


def test_acceleration_proxy_none_when_insufficient():
    end = date(2026, 9, 1)
    assert acceleration_proxy_7({end: 5.0}, end) is None


# ────────────────────── personal baseline ─────────────────────────
def test_personal_baseline_excludes_target_observation():
    """
    The target day must NOT contribute to its own baseline center.
    """
    end = date(2026, 9, 1)
    series = {end: 1000.0}  # outlier today
    for i in range(1, 11):
        series[end - timedelta(days=i)] = 50.0
    bl = personal_baseline(series, end)
    assert bl["center"] == 50.0  # unaffected by today's 1000
    assert bl["basis_window_days"] == 30


def test_personal_baseline_widens_to_90_then_nulls():
    end = date(2026, 9, 1)
    # two observations only, both older than 30d -> must widen to 90
    series = {
        end - timedelta(days=40): 5.0,
        end - timedelta(days=50): 7.0,
    }
    bl = personal_baseline(series, end)
    assert bl["basis_window_days"] == 90
    assert bl["center"] == 6.0
    # no observations at all -> nulls, never a population norm
    empty = personal_baseline({}, end)
    assert empty["center"] is None
    assert empty["dispersion"] is None


# ──────────────────── full metric assembly ────────────────────────
def test_build_metric_features_has_all_windows():
    end = date(2026, 9, 1)
    series = {end - timedelta(days=i): float(50 + i) for i in range(90)}
    feats = build_metric_features(series, end)
    assert set(feats["windows"].keys()) == {str(w) for w in WINDOWS}
    assert feats["today_present"] is True
    assert feats["today"] == 50.0


def test_data_quality_exposes_four_dimensions():
    end = date(2026, 9, 1)
    series = {end - timedelta(days=i): float(50 + i) for i in range(90)}
    feats = {"hrv": build_metric_features(series, end)}
    dq = assess_data_quality(feats)
    for key in ("quantity", "source_quality", "stability", "confounding"):
        assert key in dq
    assert dq["display_label"] in ("low", "medium", "high")
    assert dq["ruleset_version"] == METHODS_VERSION


def test_data_quality_low_when_sparse():
    end = date(2026, 9, 1)
    feats = {"hrv": build_metric_features({end: 50.0}, end)}
    dq = assess_data_quality(feats)
    assert dq["display_label"] == "low"
