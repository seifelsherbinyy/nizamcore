"""
Tests for the staged fetching pipeline — carrier filtering correctness.

EXECUTED_IN_SESSION: All tests in this file run with pytest.
No real API calls — uses mock source results.
"""

from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from radar.sources.base import FlightOffer, SourceResult


def _make_offer(carrier: str, price: float, dest: str = "JFK") -> FlightOffer:
    return FlightOffer(
        origin="CAI",
        destination=dest,
        cabin="BUSINESS",
        carrier=carrier,
        outbound_date=date(2027, 4, 1),
        return_date=date(2027, 4, 12),   # 11 nights
        outbound_duration_hours=14.5,
        return_duration_hours=15.0,
        outbound_stops=1,
        return_stops=1,
        outbound_routing="CAI-X-JFK",
        return_routing="JFK-X-CAI",
        price_usd=price,
        source="serpapi",
    )


def _mock_source(offers: list[FlightOffer]):
    """Return a mock source that yields the given offers."""
    source = MagicMock()
    source._request_count = 1
    source.search.return_value = SourceResult(source_name="serpapi", offers=offers)
    return source


class TestCarrierFiltering:
    """Verify fetch_best_price filters by carrier when carriers are specified."""

    def test_no_carrier_filter_returns_cheapest_overall(self):
        """Without a carrier filter, the globally cheapest qualifying offer wins."""
        offers = [
            _make_offer("EK", 3200.0),
            _make_offer("QR", 2800.0),   # cheapest
            _make_offer("MS", 3000.0),
        ]
        with patch("radar.fetcher._build_source", return_value=_mock_source(offers)):
            from radar.fetcher import fetch_best_price
            best, errors = fetch_best_price(
                origin="CAI", destination="JFK", cabin="BUSINESS",
                window_start=date(2027, 3, 15), window_end=date(2027, 9, 30),
                carriers=None,
            )
        assert best is not None
        assert best.carrier == "QR"
        assert best.price_usd == 2800.0

    def test_carrier_filter_restricts_to_specified_carrier(self):
        """With carriers=['MS'], only MS offers should be considered."""
        offers = [
            _make_offer("EK", 2500.0),   # cheapest overall but wrong carrier
            _make_offer("MS", 3000.0),   # target carrier
            _make_offer("QR", 2800.0),   # wrong carrier
        ]
        with patch("radar.fetcher._build_source", return_value=_mock_source(offers)):
            from radar.fetcher import fetch_best_price
            best, errors = fetch_best_price(
                origin="CAI", destination="JFK", cabin="BUSINESS",
                window_start=date(2027, 3, 15), window_end=date(2027, 9, 30),
                carriers=["MS"],
            )
        assert best is not None
        assert best.carrier == "MS", (
            "Carrier filter must exclude EK and QR — only MS offers qualify"
        )
        assert best.price_usd == 3000.0

    def test_carrier_filter_returns_none_when_carrier_not_found(self):
        """If the requested carrier has no results, best_offer should be None."""
        offers = [
            _make_offer("EK", 2500.0),
            _make_offer("QR", 2800.0),
        ]
        with patch("radar.fetcher._build_source", return_value=_mock_source(offers)):
            from radar.fetcher import fetch_best_price
            best, errors = fetch_best_price(
                origin="CAI", destination="JFK", cabin="BUSINESS",
                window_start=date(2027, 3, 15), window_end=date(2027, 9, 30),
                carriers=["LH"],  # Lufthansa not in offers
            )
        assert best is None

    def test_carrier_filter_case_insensitive(self):
        """carriers=['ek'] (lowercase) must match offers with carrier='EK'."""
        offers = [_make_offer("EK", 3100.0)]
        with patch("radar.fetcher._build_source", return_value=_mock_source(offers)):
            from radar.fetcher import fetch_best_price
            best, errors = fetch_best_price(
                origin="CAI", destination="JFK", cabin="BUSINESS",
                window_start=date(2027, 3, 15), window_end=date(2027, 9, 30),
                carriers=["ek"],
            )
        assert best is not None
        assert best.carrier == "EK"

    def test_multiple_carrier_filter_allows_all_listed(self):
        """carriers=['EK', 'QR'] must allow offers from both, pick cheapest."""
        offers = [
            _make_offer("EK", 3200.0),
            _make_offer("QR", 2900.0),  # cheaper of the two allowed
            _make_offer("MS", 2600.0),  # not in filter
        ]
        with patch("radar.fetcher._build_source", return_value=_mock_source(offers)):
            from radar.fetcher import fetch_best_price
            best, errors = fetch_best_price(
                origin="CAI", destination="JFK", cabin="BUSINESS",
                window_start=date(2027, 3, 15), window_end=date(2027, 9, 30),
                carriers=["EK", "QR"],
            )
        assert best is not None
        assert best.carrier == "QR"
        assert best.price_usd == 2900.0
        assert best.carrier != "MS", "MS must be excluded by carrier filter"

    def test_constraint_violation_still_filtered_even_with_matching_carrier(self):
        """A matching carrier offer that violates routing constraints must still be excluded."""
        offers = [
            FlightOffer(
                origin="CAI", destination="JFK", cabin="BUSINESS",
                carrier="EK",
                outbound_date=date(2027, 4, 1),
                return_date=date(2027, 4, 12),
                outbound_duration_hours=35.0,   # exceeds 30h limit
                return_duration_hours=14.0,
                outbound_stops=2, return_stops=1,
                outbound_routing="CAI-X-Y-JFK", return_routing="JFK-X-CAI",
                price_usd=2000.0,
                source="serpapi",
            )
        ]
        with patch("radar.fetcher._build_source", return_value=_mock_source(offers)):
            from radar.fetcher import fetch_best_price
            best, errors = fetch_best_price(
                origin="CAI", destination="JFK", cabin="BUSINESS",
                window_start=date(2027, 3, 15), window_end=date(2027, 9, 30),
                carriers=["EK"],
            )
        assert best is None, "31h outbound must be filtered even when carrier matches"
