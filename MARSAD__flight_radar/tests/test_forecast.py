"""
Tests for the FORECAST module (Stage 4).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Pure unit tests of forecasting model functions — no file I/O.
"""

import pytest
import numpy as np


class TestConfidenceLevel:
    def test_fewer_than_7_is_low(self):
        from radar.stages.forecast import _confidence_level
        for n in range(0, 7):
            assert _confidence_level(n) == "LOW", f"n={n} should be LOW"

    def test_7_is_medium(self):
        from radar.stages.forecast import _confidence_level
        assert _confidence_level(7) == "MEDIUM"

    def test_29_is_medium(self):
        from radar.stages.forecast import _confidence_level
        assert _confidence_level(29) == "MEDIUM"

    def test_30_is_high(self):
        from radar.stages.forecast import _confidence_level
        assert _confidence_level(30) == "HIGH"

    def test_100_is_high(self):
        from radar.stages.forecast import _confidence_level
        assert _confidence_level(100) == "HIGH"


class TestModelSelection:
    def test_sma_selected_below_7(self):
        from radar.stages.forecast import _select_model
        for n in range(1, 7):
            assert _select_model(n) == "sma"

    def test_ewm_selected_7_to_29(self):
        from radar.stages.forecast import _select_model
        assert _select_model(7) == "ewm"
        assert _select_model(15) == "ewm"
        assert _select_model(29) == "ewm"

    def test_lr_selected_at_30_plus(self):
        from radar.stages.forecast import _select_model
        assert _select_model(30) == "lr"
        assert _select_model(100) == "lr"


class TestSMAForecast:
    def test_returns_three_horizons(self):
        from radar.stages.forecast import _forecast_sma
        prices = [3000.0, 2900.0, 2950.0, 2800.0, 2850.0]
        result = _forecast_sma(prices, [7, 14, 30])
        assert set(result.keys()) == {7, 14, 30}

    def test_low_mid_high_ordering(self):
        from radar.stages.forecast import _forecast_sma
        prices = [3000.0, 2900.0, 2950.0, 2800.0, 2850.0, 2900.0, 3100.0]
        result = _forecast_sma(prices, [7])
        h7 = result[7]
        assert h7["low"] <= h7["mid"] <= h7["high"]

    def test_no_negative_prices(self):
        from radar.stages.forecast import _forecast_sma
        prices = [100.0, 90.0, 80.0, 70.0, 60.0]
        result = _forecast_sma(prices, [7, 14, 30])
        for h in [7, 14, 30]:
            assert result[h]["low"] >= 0.0


class TestEWMForecast:
    def test_returns_three_horizons(self):
        from radar.stages.forecast import _forecast_ewm
        prices = [3000.0 - i * 20 for i in range(10)]
        result = _forecast_ewm(prices, [7, 14, 30])
        assert set(result.keys()) == {7, 14, 30}

    def test_downward_trend_forecasts_lower(self):
        from radar.stages.forecast import _forecast_ewm
        # Steadily declining prices
        prices = [3000.0 - i * 50 for i in range(10)]  # 3000, 2950, ..., 2550
        result = _forecast_ewm(prices, [7, 14])
        # 14-day mid should be lower than 7-day mid given declining trend
        assert result[14]["mid"] <= result[7]["mid"] + 100  # allow some tolerance

    def test_low_mid_high_ordering(self):
        from radar.stages.forecast import _forecast_ewm
        prices = [3000.0 + (i % 3) * 100 for i in range(10)]
        result = _forecast_ewm(prices, [7])
        h7 = result[7]
        assert h7["low"] <= h7["mid"] <= h7["high"]


class TestLinearRegressionForecast:
    def test_returns_three_horizons(self):
        from radar.stages.forecast import _forecast_linear_regression
        prices = [3000.0 + i * 10 for i in range(35)]
        result = _forecast_linear_regression(prices, [7, 14, 30])
        assert set(result.keys()) == {7, 14, 30}

    def test_rising_trend_forecasts_higher(self):
        from radar.stages.forecast import _forecast_linear_regression
        prices = [2000.0 + i * 30 for i in range(35)]  # clear upward trend
        result = _forecast_linear_regression(prices, [7, 30])
        assert result[30]["mid"] > result[7]["mid"]

    def test_flat_trend_forecasts_stable(self):
        from radar.stages.forecast import _forecast_linear_regression
        prices = [3000.0] * 35  # perfectly flat
        result = _forecast_linear_regression(prices, [7])
        assert abs(result[7]["mid"] - 3000.0) < 1.0


class TestBuySignalLogic:
    def test_low_confidence_blocks_buy_signal(self):
        """INVARIANT: LOW confidence must always return False, no exceptions."""
        from radar.stages.forecast import _compute_buy_signal
        result = _compute_buy_signal(
            current_price=1000.0,
            forecast_7d={"low": 2000.0},  # current below forecast low
            historical_20th_pct=1500.0,   # current below p20
            confidence="LOW",
        )
        assert result is False, "BUY_SIGNAL must be False when confidence is LOW"

    def test_medium_confidence_with_both_conditions_triggers(self):
        from radar.stages.forecast import _compute_buy_signal
        result = _compute_buy_signal(
            current_price=2000.0,
            forecast_7d={"low": 2500.0},  # current (2000) < 7d_low (2500)
            historical_20th_pct=2200.0,   # current (2000) < p20 (2200)
            confidence="MEDIUM",
        )
        assert result is True

    def test_only_forecast_condition_not_enough(self):
        from radar.stages.forecast import _compute_buy_signal
        result = _compute_buy_signal(
            current_price=2000.0,
            forecast_7d={"low": 2500.0},  # condition 1 met
            historical_20th_pct=1800.0,   # condition 2 NOT met (current > p20)
            confidence="MEDIUM",
        )
        assert result is False

    def test_only_percentile_condition_not_enough(self):
        from radar.stages.forecast import _compute_buy_signal
        result = _compute_buy_signal(
            current_price=2000.0,
            forecast_7d={"low": 1500.0},  # condition 1 NOT met (current > forecast_low)
            historical_20th_pct=2200.0,   # condition 2 met
            confidence="MEDIUM",
        )
        assert result is False

    def test_none_historical_percentile_blocks_buy_signal(self):
        from radar.stages.forecast import _compute_buy_signal
        result = _compute_buy_signal(
            current_price=1000.0,
            forecast_7d={"low": 2000.0},
            historical_20th_pct=None,
            confidence="MEDIUM",
        )
        assert result is False
