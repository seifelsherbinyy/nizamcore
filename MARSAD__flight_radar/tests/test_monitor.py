"""
Tests for the MONITOR stage (Stage 2) exhaustion circuit breaker.

EXECUTED_IN_SESSION: All tests in this file run with pytest.

Context: the daily monitor job has a 30-minute CI timeout. When the
configured data source's quota is exhausted, every request 429s and the
job used to burn the full timeout retrying every series before being
force-cancelled with zero data written. `_looks_exhausted` + the
consecutive-failure counter in `run_monitor` detect this pattern and
abort early instead.
"""


class TestLooksExhausted:
    def test_all_rate_limited_errors_look_exhausted(self):
        from radar.stages.monitor import _looks_exhausted
        errors = ["SerpApi max retries exceeded: CAI→JFK 2027-03-15"]
        assert _looks_exhausted(errors)

    def test_mixed_errors_not_exhausted(self):
        from radar.stages.monitor import _looks_exhausted
        errors = ["SerpApi 400: bad request — CAI→JFK 2027-03-15"]
        assert not _looks_exhausted(errors)

    def test_no_errors_not_exhausted(self):
        from radar.stages.monitor import _looks_exhausted
        assert not _looks_exhausted([])

    def test_429_marker_detected(self):
        from radar.stages.monitor import _looks_exhausted
        assert _looks_exhausted(["HTTP 429 from upstream"])


class TestConsecutiveExhaustionAbort:
    def test_aborts_after_limit_consecutive_exhausted_combos(self, monkeypatch, tmp_path):
        from radar.stages import monitor as monitor_module

        keys = [
            {"origin": "CAI", "destination": "JFK", "carrier": "MS", "cabin": "BUSINESS"},
            {"origin": "CAI", "destination": "LAX", "carrier": "MS", "cabin": "BUSINESS"},
            {"origin": "CAI", "destination": "ORD", "carrier": "MS", "cabin": "BUSINESS"},
            {"origin": "CAI", "destination": "ATL", "carrier": "MS", "cabin": "BUSINESS"},
            {"origin": "CAI", "destination": "MIA", "carrier": "MS", "cabin": "BUSINESS"},
        ]

        monkeypatch.setattr(monitor_module, "backup_store", lambda: None)
        monkeypatch.setattr(monitor_module, "get_all_series_keys", lambda: keys)
        monkeypatch.setattr(
            monitor_module,
            "fetch_best_price",
            lambda **kwargs: (None, ["SerpApi max retries exceeded: rate limited"]),
        )

        stats = monitor_module.run_monitor()

        assert stats["aborted_early"] is True
        assert stats["abort_reason"] is not None
        # Aborts at the 3rd consecutive exhausted combo — the remaining
        # 2 of 5 series are never even attempted.
        assert stats["routes_checked"] == monitor_module._CONSECUTIVE_EXHAUSTION_LIMIT

    def test_non_exhaustion_no_data_does_not_abort(self, monkeypatch):
        from radar.stages import monitor as monitor_module

        keys = [
            {"origin": "CAI", "destination": "JFK", "carrier": "MS", "cabin": "BUSINESS"},
            {"origin": "CAI", "destination": "LAX", "carrier": "MS", "cabin": "BUSINESS"},
            {"origin": "CAI", "destination": "ORD", "carrier": "MS", "cabin": "BUSINESS"},
            {"origin": "CAI", "destination": "ATL", "carrier": "MS", "cabin": "BUSINESS"},
        ]

        monkeypatch.setattr(monitor_module, "backup_store", lambda: None)
        monkeypatch.setattr(monitor_module, "get_all_series_keys", lambda: keys)
        monkeypatch.setattr(
            monitor_module,
            "fetch_best_price",
            lambda **kwargs: (None, []),
        )

        stats = monitor_module.run_monitor()

        assert stats["aborted_early"] is False
        assert stats["routes_checked"] == len(keys)
