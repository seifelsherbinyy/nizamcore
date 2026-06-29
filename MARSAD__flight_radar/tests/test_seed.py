"""
Tests for the HISTORICAL SEED module (Stage 0).

EXECUTED_IN_SESSION: All tests in this file run with pytest.
Uses a temporary directory to avoid touching the real data store.
"""

import pytest


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    """Redirect all schema_store paths to a temporary directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    alerts_dir = tmp_path / "alerts"
    alerts_dir.mkdir()

    monkeypatch.setattr("radar.config.DATA_DIR", data_dir)
    monkeypatch.setattr("radar.config.ALERTS_DIR", alerts_dir)
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr("radar.config.FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr("radar.config.BACKUPS_DIR", data_dir / "backups")

    import radar.schema_store as ss
    monkeypatch.setattr(ss, "FLIGHT_PRICES_PATH", data_dir / "flight_prices.json")
    monkeypatch.setattr(ss, "FLIGHT_PRICES_TMP", data_dir / "flight_prices.tmp")
    monkeypatch.setattr(ss, "BACKUPS_DIR", data_dir / "backups")

    return data_dir


class TestSeedBasicRun:
    def test_seed_writes_observations(self, tmp_store):
        from radar.stages.seed import run_seed
        stats = run_seed(count=7, destinations=["JFK"], cabins=["BUSINESS"])
        assert stats["total_seeded"] == 7
        assert stats["series_seeded"] == 1
        assert stats["series_skipped"] == 0
        assert not stats["dry_run"]

    def test_seed_dry_run_writes_nothing(self, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        stats = run_seed(count=7, destinations=["JFK"], cabins=["BUSINESS"], dry_run=True)
        assert stats["dry_run"] is True
        assert stats["total_seeded"] == 7  # count logged even in dry-run
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        assert len(series) == 0, "dry_run must not write to store"

    def test_seed_reaches_medium_confidence_threshold(self, tmp_store):
        """7 observations → MEDIUM confidence (required for BUY_SIGNAL gate)."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=7, destinations=["LAX"], cabins=["BUSINESS"])
        series = get_series("CAI", "LAX", "EK", "BUSINESS")
        assert len(series) >= 7

    def test_seed_reaches_high_confidence_threshold(self, tmp_store):
        """30 observations → HIGH confidence (Linear Regression model)."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=30, destinations=["ORD"], cabins=["BUSINESS"])
        series = get_series("CAI", "ORD", "TK", "BUSINESS")
        assert len(series) >= 30


class TestSeedObservationFields:
    def test_seed_observation_type_is_historical_seed(self, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=3, destinations=["JFK"], cabins=["BUSINESS"])
        series = get_series("CAI", "JFK", "EK", "BUSINESS")
        for obs in series:
            assert obs["observation_type"] == "historical_seed"

    def test_seed_source_is_historical_seed(self, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=3, destinations=["MIA"], cabins=["PREMIUM_ECONOMY"])
        series = get_series("CAI", "MIA", "BA", "PREMIUM_ECONOMY")
        for obs in series:
            assert obs["source"] == "historical_seed"

    def test_seed_data_quality_is_estimated(self, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=3, destinations=["SFO"], cabins=["BUSINESS"])
        series = get_series("CAI", "SFO", "QR", "BUSINESS")
        for obs in series:
            assert obs["data_quality"] == "estimated"

    def test_seed_prices_are_positive(self, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=10, destinations=["IAD"], cabins=["BUSINESS"])
        series = get_series("CAI", "IAD", "EK", "BUSINESS")
        for obs in series:
            assert obs["price_usd"] > 0

    def test_seed_nights_in_valid_range(self, tmp_store):
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=5, destinations=["BOS"], cabins=["BUSINESS"])
        series = get_series("CAI", "BOS", "QR", "BUSINESS")
        for obs in series:
            assert 9 <= obs["nights"] <= 14


class TestSeedPremiumEconomy:
    def test_pe_price_lower_than_business(self, tmp_store):
        """PREMIUM_ECONOMY seed prices must be lower than BUSINESS for the same route."""
        from radar.stages.seed import run_seed, _BUSINESS_BASE_USD, _PE_FRACTION
        from radar.schema_store import get_series
        run_seed(count=10, destinations=["JFK"], cabins=["BUSINESS", "PREMIUM_ECONOMY"])
        biz = get_series("CAI", "JFK", "EK", "BUSINESS")
        pe = get_series("CAI", "JFK", "EK", "PREMIUM_ECONOMY")
        avg_biz = sum(o["price_usd"] for o in biz) / len(biz)
        avg_pe = sum(o["price_usd"] for o in pe) / len(pe)
        assert avg_pe < avg_biz, "Premium Economy should be cheaper than Business"


class TestSeedIdempotency:
    def test_seed_skips_already_seeded_series(self, tmp_store):
        """Running seed twice with the same count should not add more observations."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=7, destinations=["DFW"], cabins=["BUSINESS"])
        first_count = len(get_series("CAI", "DFW", "AA", "BUSINESS"))
        stats2 = run_seed(count=7, destinations=["DFW"], cabins=["BUSINESS"])
        second_count = len(get_series("CAI", "DFW", "AA", "BUSINESS"))
        assert first_count == second_count, "Second seed run should be a no-op"
        assert stats2["series_skipped"] == 1

    def test_seed_appends_when_count_increased(self, tmp_store):
        """Increasing count should append more observations without overwriting existing."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=7, destinations=["SEA"], cabins=["BUSINESS"])
        ids_before = {o["observation_id"] for o in get_series("CAI", "SEA", "QR", "BUSINESS")}
        run_seed(count=15, destinations=["SEA"], cabins=["BUSINESS"])
        series_after = get_series("CAI", "SEA", "QR", "BUSINESS")
        ids_after = {o["observation_id"] for o in series_after}
        assert ids_before.issubset(ids_after), "Existing observations must not be removed"
        assert len(series_after) == 15


class TestSeedPriceVariation:
    def test_seed_prices_vary_across_series(self, tmp_store):
        """Seed prices must not all be identical — they should show realistic variation."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=10, destinations=["EWR"], cabins=["BUSINESS"])
        series = get_series("CAI", "EWR", "EK", "BUSINESS")
        prices = [o["price_usd"] for o in series]
        assert len(set(prices)) > 1, "Seed prices must vary across observations"

    def test_seed_price_range_realistic_business(self, tmp_store):
        """Business seed prices should stay within ±30% of the known market range."""
        from radar.stages.seed import run_seed
        from radar.schema_store import get_series
        run_seed(count=15, destinations=["LAS"], cabins=["BUSINESS"])
        series = get_series("CAI", "LAS", "EK", "BUSINESS")
        for obs in series:
            assert 2_000 <= obs["price_usd"] <= 8_000, (
                f"Price ${obs['price_usd']:.0f} is outside the realistic range for Business"
            )
