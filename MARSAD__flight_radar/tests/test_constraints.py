"""
Tests for the ROUTING CONSTRAINT ENGINE.

EXECUTED_IN_SESSION: All tests in this file run with pytest.
These tests use no external dependencies — pure unit tests of constraint logic.
"""

import pytest
from datetime import date

from radar.constraints import (
    FlightItinerary,
    apply_constraints,
    generate_search_combinations,
    is_valid_cabin,
    is_valid_destination,
    is_valid_window,
    validate_search_params,
)


def _base_itin(**overrides) -> FlightItinerary:
    """Factory for a valid baseline itinerary — override fields to test violations."""
    defaults = dict(
        origin="CAI",
        destination="JFK",
        cabin="BUSINESS",
        outbound_date=date(2027, 4, 1),
        return_date=date(2027, 4, 12),   # 11 nights
        outbound_duration_hours=14.5,
        return_duration_hours=15.0,
        carrier="EK",
        price_usd=3200.0,
    )
    defaults.update(overrides)
    return FlightItinerary(**defaults)


class TestValidBaseline:
    def test_valid_itinerary_passes(self):
        result = apply_constraints(_base_itin())
        assert result.passed
        assert result.failures == []


class TestOriginConstraint:
    def test_wrong_origin_fails(self):
        result = apply_constraints(_base_itin(origin="LHR"))
        assert not result.passed
        assert any("origin" in f for f in result.failures)

    def test_lowercase_cai_passes(self):
        result = apply_constraints(_base_itin(origin="cai"))
        assert result.passed


class TestDestinationConstraint:
    def test_non_usa_destination_fails(self):
        result = apply_constraints(_base_itin(destination="LHR"))
        assert not result.passed
        assert any("destination" in f for f in result.failures)

    def test_all_twelve_destinations_valid(self):
        destinations = ["JFK", "LAX", "ORD", "ATL", "MIA", "SFO", "IAD", "BOS", "EWR", "DFW", "SEA", "LAS"]
        for dest in destinations:
            result = apply_constraints(_base_itin(destination=dest))
            assert result.passed, f"{dest} should pass but got: {result.failures}"


class TestCabinConstraint:
    def test_economy_fails(self):
        result = apply_constraints(_base_itin(cabin="ECONOMY"))
        assert not result.passed
        assert any("cabin" in f for f in result.failures)

    def test_first_class_fails(self):
        result = apply_constraints(_base_itin(cabin="FIRST"))
        assert not result.passed

    def test_business_passes(self):
        assert apply_constraints(_base_itin(cabin="BUSINESS")).passed

    def test_premium_economy_passes(self):
        assert apply_constraints(_base_itin(cabin="PREMIUM_ECONOMY")).passed


class TestDurationConstraint:
    def test_8_nights_fails(self):
        """Below minimum of 9 nights."""
        result = apply_constraints(_base_itin(
            outbound_date=date(2027, 4, 1),
            return_date=date(2027, 4, 9),   # 8 nights
        ))
        assert not result.passed
        assert any("duration" in f for f in result.failures)

    def test_9_nights_passes(self):
        result = apply_constraints(_base_itin(
            outbound_date=date(2027, 4, 1),
            return_date=date(2027, 4, 10),  # 9 nights
        ))
        assert result.passed

    def test_14_nights_passes(self):
        result = apply_constraints(_base_itin(
            outbound_date=date(2027, 4, 1),
            return_date=date(2027, 4, 15),  # 14 nights
        ))
        assert result.passed

    def test_15_nights_fails(self):
        """Above maximum of 14 nights."""
        result = apply_constraints(_base_itin(
            outbound_date=date(2027, 4, 1),
            return_date=date(2027, 4, 16),  # 15 nights
        ))
        assert not result.passed


class TestFlightTimeConstraint:
    def test_31_hour_outbound_fails(self):
        """
        KEY TEST: 31-hour outbound must fail even if return is 20 hours.
        The 30-hour limit applies INDEPENDENTLY to each leg — not round-trip total.
        A 28+28=56 hour round trip is valid. A 31+15=46 hour round trip is not.
        """
        result = apply_constraints(_base_itin(
            outbound_duration_hours=31.0,
            return_duration_hours=20.0,
        ))
        assert not result.passed
        assert any("outbound_duration" in f for f in result.failures)
        assert not any("return_duration" in f for f in result.failures), (
            "Return leg (20h) should PASS — only outbound fails"
        )

    def test_31_hour_return_fails(self):
        result = apply_constraints(_base_itin(
            outbound_duration_hours=20.0,
            return_duration_hours=31.0,
        ))
        assert not result.passed
        assert any("return_duration" in f for f in result.failures)
        assert not any("outbound_duration" in f for f in result.failures)

    def test_30_hour_exactly_passes(self):
        """Exactly 30 hours should pass (constraint is > 30, not ≥ 30)."""
        result = apply_constraints(_base_itin(
            outbound_duration_hours=30.0,
            return_duration_hours=30.0,
        ))
        assert result.passed

    def test_28_28_round_trip_passes(self):
        """28+28=56 total hours — valid because each leg is under 30h."""
        result = apply_constraints(_base_itin(
            outbound_duration_hours=28.0,
            return_duration_hours=28.0,
        ))
        assert result.passed


class TestTravelWindowConstraint:
    def test_before_window_fails(self):
        result = apply_constraints(_base_itin(
            outbound_date=date(2027, 3, 1),
            return_date=date(2027, 3, 12),
        ))
        assert not result.passed
        assert any("outbound_date" in f for f in result.failures)

    def test_after_window_fails(self):
        result = apply_constraints(_base_itin(
            outbound_date=date(2027, 9, 28),
            return_date=date(2027, 10, 5),   # return after Sep 30
        ))
        assert not result.passed
        assert any("return_date" in f for f in result.failures)

    def test_first_day_of_window_passes(self):
        result = apply_constraints(_base_itin(
            outbound_date=date(2027, 3, 15),
            return_date=date(2027, 3, 26),  # 11 nights
        ))
        assert result.passed

    def test_last_valid_return_passes(self):
        result = apply_constraints(_base_itin(
            outbound_date=date(2027, 9, 16),
            return_date=date(2027, 9, 30),  # 14 nights, returns on Sep 30
        ))
        assert result.passed


class TestMultipleFailures:
    def test_multiple_violations_all_reported(self):
        """All constraint failures should be reported, not just the first."""
        result = apply_constraints(_base_itin(
            origin="LHR",
            destination="CDG",
            cabin="ECONOMY",
            outbound_duration_hours=35.0,
        ))
        assert not result.passed
        assert len(result.failures) >= 3


class TestSearchCombinations:
    def test_generates_correct_count(self):
        combos = generate_search_combinations()
        # 12 destinations × 2 cabins = 24
        assert len(combos) == 24

    def test_all_combos_have_cai_origin(self):
        combos = generate_search_combinations()
        assert all(c["origin"] == "CAI" for c in combos)

    def test_all_combos_have_valid_cabins(self):
        combos = generate_search_combinations()
        assert all(c["cabin"] in ["BUSINESS", "PREMIUM_ECONOMY"] for c in combos)


class TestHelperFunctions:
    def test_is_valid_destination(self):
        assert is_valid_destination("JFK")
        assert not is_valid_destination("LHR")

    def test_is_valid_cabin(self):
        assert is_valid_cabin("BUSINESS")
        assert is_valid_cabin("PREMIUM_ECONOMY")
        assert not is_valid_cabin("ECONOMY")
        assert not is_valid_cabin("FIRST")

    def test_validate_search_params_valid(self):
        result = validate_search_params("CAI", "JFK", "BUSINESS")
        assert result.passed

    def test_validate_search_params_invalid(self):
        result = validate_search_params("LHR", "CDG", "ECONOMY")
        assert not result.passed
        assert len(result.failures) == 3
