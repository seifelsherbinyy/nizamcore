"""
Tests for SerpApiSource parser — focused on the outbound/return segment split.

EXECUTED_IN_SESSION: All tests run with pytest. No network calls are made;
all tests use synthetic SerpApi response payloads.
"""

from __future__ import annotations

import sys
from pathlib import Path

_MARSAD = Path(__file__).resolve().parents[1]
if str(_MARSAD) not in sys.path:
    sys.path.insert(0, str(_MARSAD))

import pytest
from unittest.mock import patch


def _make_segment(dep: str, arr: str, duration: int, is_return: bool | None = None) -> dict:
    seg = {
        "departure_airport": {"id": dep},
        "arrival_airport": {"id": arr},
        "duration": duration,
        "airline": "EgyptAir",
    }
    if is_return is not None:
        seg["is_return"] = is_return
    return seg


@pytest.fixture()
def source():
    with patch.dict("os.environ", {"SERPAPI_KEY": "fake-key"}):
        from radar.sources.serpapi_source import SerpApiSource
        return SerpApiSource()


class TestSplitOutboundReturn:
    """Unit tests for _split_outbound_return."""

    def test_split_by_is_return_flag(self, source):
        segments = [
            _make_segment("CAI", "JFK", 840, is_return=False),
            _make_segment("JFK", "CAI", 870, is_return=True),
        ]
        outbound, return_ = source._split_outbound_return(segments, "JFK")
        assert len(outbound) == 1 and outbound[0]["departure_airport"]["id"] == "CAI"
        assert len(return_) == 1 and return_[0]["departure_airport"]["id"] == "JFK"

    def test_split_by_destination_when_no_is_return(self, source):
        """Direct flight — SerpApi omits is_return flags; pivot on destination."""
        segments = [
            _make_segment("CAI", "JFK", 840),
            _make_segment("JFK", "CAI", 870),
        ]
        outbound, return_ = source._split_outbound_return(segments, "JFK")
        assert len(outbound) == 1 and outbound[0]["arrival_airport"]["id"] == "JFK"
        assert len(return_) == 1 and return_[0]["departure_airport"]["id"] == "JFK"

    def test_split_connecting_outbound_no_is_return(self, source):
        """CAI → DXB → JFK (outbound, 2 segments) + JFK → DXB → CAI (return, 2 segments)."""
        segments = [
            _make_segment("CAI", "DXB", 240),
            _make_segment("DXB", "JFK", 840),
            _make_segment("JFK", "DXB", 870),
            _make_segment("DXB", "CAI", 240),
        ]
        outbound, return_ = source._split_outbound_return(segments, "JFK")
        assert len(outbound) == 2
        assert outbound[-1]["arrival_airport"]["id"] == "JFK"
        assert len(return_) == 2
        assert return_[0]["departure_airport"]["id"] == "JFK"

    def test_return_routing_points_away_from_destination(self, source):
        """The return routing string must start at destination, not origin."""
        segments = [
            _make_segment("CAI", "JFK", 840),
            _make_segment("JFK", "CAI", 870),
        ]
        _, return_segs = source._split_outbound_return(segments, "JFK")
        routing = source._build_routing(return_segs)
        assert routing.startswith("JFK"), f"Return routing should start with JFK, got: {routing}"
        assert routing.endswith("CAI"), f"Return routing should end with CAI, got: {routing}"

    def test_case_insensitive_destination(self, source):
        segments = [
            _make_segment("CAI", "jfk", 840),
            _make_segment("JFK", "CAI", 870),
        ]
        outbound, return_ = source._split_outbound_return(segments, "JFK")
        assert len(outbound) == 1
        assert len(return_) == 1

    def test_half_split_fallback_when_destination_not_found(self, source):
        """When no segment arrives at destination, fall back to half-split."""
        segments = [
            _make_segment("CAI", "DXB", 240),
            _make_segment("DXB", "LAX", 900),
            _make_segment("LAX", "DXB", 900),
            _make_segment("DXB", "CAI", 240),
        ]
        # destination JFK does not appear — triggers half-split fallback
        outbound, return_ = source._split_outbound_return(segments, "JFK")
        assert len(outbound) + len(return_) == 4


class TestParseItemRoutingDirection:
    """Integration tests: _parse_item must produce correctly directed routing strings."""

    def _make_round_trip_item(self, dep: str, arr: str, dur_min: int = 840) -> dict:
        return {
            "price": 3200,
            "total_duration": dur_min * 2,
            "flights": [
                _make_segment(dep, arr, dur_min),
                _make_segment(arr, dep, dur_min),
            ],
        }

    def test_outbound_routing_starts_at_cai(self, source):
        from datetime import date
        item = self._make_round_trip_item("CAI", "JFK")
        offer = source._parse_item(item, date(2027, 4, 1), date(2027, 4, 12), "BUSINESS", "JFK")
        assert offer is not None
        assert offer.outbound_routing.startswith("CAI")

    def test_return_routing_starts_at_destination(self, source):
        from datetime import date
        item = self._make_round_trip_item("CAI", "JFK")
        offer = source._parse_item(item, date(2027, 4, 1), date(2027, 4, 12), "BUSINESS", "JFK")
        assert offer is not None
        assert offer.return_routing.startswith("JFK"), (
            f"Return routing should start at JFK (destination), got: {offer.return_routing!r}"
        )

    def test_return_routing_ends_at_origin(self, source):
        from datetime import date
        item = self._make_round_trip_item("CAI", "LAX")
        offer = source._parse_item(item, date(2027, 5, 1), date(2027, 5, 12), "PREMIUM_ECONOMY", "LAX")
        assert offer is not None
        assert offer.return_routing.endswith("CAI"), (
            f"Return routing should end at CAI (origin), got: {offer.return_routing!r}"
        )

    def test_per_leg_duration_not_half_total(self, source):
        """Each leg duration must be computed from its segments, not total//2."""
        from datetime import date
        item = {
            "price": 3200,
            "total_duration": 1800,  # 30 hours total
            "flights": [
                _make_segment("CAI", "JFK", 840),   # 14h outbound
                _make_segment("JFK", "CAI", 960),   # 16h return
            ],
        }
        offer = source._parse_item(item, date(2027, 4, 1), date(2027, 4, 12), "BUSINESS", "JFK")
        assert offer is not None
        assert offer.outbound_duration_hours == pytest.approx(14.0, abs=0.1)
        assert offer.return_duration_hours == pytest.approx(16.0, abs=0.1)

    def test_price_none_returns_none(self, source):
        from datetime import date
        offer = source._parse_item({"price": None, "flights": []}, date(2027, 4, 1), date(2027, 4, 12), "BUSINESS", "JFK")
        assert offer is None

    def test_empty_flights_returns_none(self, source):
        from datetime import date
        offer = source._parse_item({"price": 3200, "flights": []}, date(2027, 4, 1), date(2027, 4, 12), "BUSINESS", "JFK")
        assert offer is None
