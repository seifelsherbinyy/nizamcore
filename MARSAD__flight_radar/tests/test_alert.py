"""
Tests for the ALERT engine (Stage 3).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses synthetic observation series to test BUY_SIGNAL conditions.
"""

import pytest
from unittest.mock import patch


class TestDropThreshold:
    def test_pct_threshold_business(self):
        from radar.stages.alert import _drop_threshold_met
        # 10% drop on Business — meets threshold
        assert _drop_threshold_met(drop_usd=300.0, drop_pct=10.0, cabin="BUSINESS")

    def test_below_pct_and_below_abs_threshold(self):
        from radar.stages.alert import _drop_threshold_met
        # 5% drop and $50 — neither threshold met for Business ($200 abs)
        assert not _drop_threshold_met(drop_usd=50.0, drop_pct=5.0, cabin="BUSINESS")

    def test_abs_threshold_business(self):
        from radar.stages.alert import _drop_threshold_met
        # $200 exact — meets abs threshold for Business
        assert _drop_threshold_met(drop_usd=200.0, drop_pct=5.0, cabin="BUSINESS")

    def test_abs_threshold_premium_economy(self):
        from radar.stages.alert import _drop_threshold_met
        # $100 exact — meets abs threshold for Premium Economy
        assert _drop_threshold_met(drop_usd=100.0, drop_pct=5.0, cabin="PREMIUM_ECONOMY")

    def test_synthetic_15pct_drop_triggers(self):
        """A 15% drop must trigger the threshold regardless of absolute amount."""
        from radar.stages.alert import _drop_threshold_met
        assert _drop_threshold_met(drop_usd=450.0, drop_pct=15.0, cabin="BUSINESS")


class TestConfidenceGate:
    def test_cold_start_gate_blocks_buy_signal(self):
        """BUY_SIGNAL MUST be False when fewer than 7 observations (LOW confidence)."""
        from radar.stages.alert import _confidence_gate_passed
        assert not _confidence_gate_passed(6)
        assert not _confidence_gate_passed(0)
        assert not _confidence_gate_passed(1)

    def test_7_observations_passes_gate(self):
        from radar.stages.alert import _confidence_gate_passed
        assert _confidence_gate_passed(7)

    def test_30_observations_passes_gate(self):
        from radar.stages.alert import _confidence_gate_passed
        assert _confidence_gate_passed(30)


class TestPercentileRank:
    def test_below_median_ranks_low(self):
        from radar.stages.alert import _percentile_rank
        prices = [3000, 3100, 3200, 3300, 3400, 3500, 3600, 3700, 3800, 3900]
        rank = _percentile_rank(prices, 3000)
        assert rank <= 20.0

    def test_above_median_ranks_high(self):
        from radar.stages.alert import _percentile_rank
        prices = [3000, 3100, 3200, 3300, 3400, 3500, 3600, 3700, 3800, 3900]
        rank = _percentile_rank(prices, 3900)
        assert rank > 80.0

    def test_empty_prices_returns_50(self):
        from radar.stages.alert import _percentile_rank
        assert _percentile_rank([], 3000) == 50.0


class TestHistoricalPercentile:
    def test_20th_percentile_computed(self):
        from radar.stages.alert import _historical_20th_percentile
        import numpy as np
        prices = list(range(100, 1100, 100))  # [100, 200, ..., 1000]
        p20 = _historical_20th_percentile(prices)
        expected = float(np.percentile(prices, 20))
        assert abs(p20 - expected) < 0.01

    def test_single_price_returns_none(self):
        from radar.stages.alert import _historical_20th_percentile
        assert _historical_20th_percentile([3000.0]) is None


class TestBuySignalConditions:
    """
    BUY_SIGNAL requires ALL THREE conditions:
    1. drop ≥ threshold
    2. current < 20th percentile
    3. confidence ≥ MEDIUM (obs_count ≥ 7)
    """

    def _make_series_prices(self, n: int, current: float, history_base: float = 3000.0) -> list[float]:
        """Build a price series of n observations where the last is `current`."""
        history = [history_base + (i * 10) for i in range(n - 1)]
        return history + [current]

    def test_all_three_conditions_met_triggers_buy(self):
        """Synthetic: 15% single-day drop, below p20, 10 observations → BUY_SIGNAL."""
        from radar.stages.alert import _drop_threshold_met, _confidence_gate_passed, _historical_20th_percentile, _percentile_rank

        obs_count = 10
        prev_price = 3000.0
        current_price = 2550.0  # 15% drop
        history = [3000, 3050, 3100, 3150, 3200, 3250, 3300, 3350, 3400]  # 9 historical

        drop_usd = prev_price - current_price
        drop_pct = drop_usd / prev_price * 100

        p20 = _historical_20th_percentile(history)
        cond1 = _drop_threshold_met(drop_usd, drop_pct, "BUSINESS")
        cond2 = current_price < p20
        cond3 = _confidence_gate_passed(obs_count)

        assert cond1, "Condition 1 (threshold) must be met"
        assert cond2, "Condition 2 (below p20) must be met"
        assert cond3, "Condition 3 (confidence gate) must be met"

    def test_cold_start_blocks_buy_signal_even_with_large_drop(self):
        """Even a 50% drop must NOT trigger BUY_SIGNAL when confidence is LOW."""
        from radar.stages.alert import _drop_threshold_met, _confidence_gate_passed

        obs_count = 4  # cold start
        drop_usd = 1500.0
        drop_pct = 50.0
        cabin = "BUSINESS"

        cond1 = _drop_threshold_met(drop_usd, drop_pct, cabin)
        cond3 = _confidence_gate_passed(obs_count)

        assert cond1, "Threshold is met"
        assert not cond3, "Confidence gate must block BUY_SIGNAL during cold start"
        # BUY_SIGNAL = cond1 AND cond2 AND cond3 → False because cond3 is False
        buy_signal = cond1 and True and cond3  # assuming cond2=True (best case)
        assert not buy_signal

    def test_condition_1_alone_insufficient(self):
        """Price drop threshold alone is NOT enough for BUY_SIGNAL."""
        from radar.stages.alert import _drop_threshold_met, _confidence_gate_passed, _historical_20th_percentile

        # Large drop but price still above p20
        history = [2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800]
        p20 = _historical_20th_percentile(history)
        current_price = 2400.0  # above p20 despite a drop from 2800

        cond1 = _drop_threshold_met(drop_usd=400.0, drop_pct=14.3, cabin="BUSINESS")
        cond2 = current_price < p20  # likely False since current is ~median

        assert cond1
        assert not cond2  # p20 of this series is around 2160 — 2400 is above it
        buy_signal = cond1 and cond2 and True
        assert not buy_signal
