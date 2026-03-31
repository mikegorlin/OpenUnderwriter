"""Tests for the pricing analytics trend analysis module."""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.knowledge.pricing_analytics_trends import (
    TrendPoint,
    compute_trends,
    compute_yoy_changes,
    detect_carrier_rotations,
)


class TestComputeTrendsFromNewModule:
    """Verify compute_trends works from its new location."""

    def test_compute_trends_multiple_periods(self) -> None:
        """Rates across 3 half-years produce 3 TrendPoints."""
        data: list[tuple[float, datetime]] = [
            (0.04, datetime(2024, 3, 1, tzinfo=UTC)),
            (0.045, datetime(2024, 5, 1, tzinfo=UTC)),
            (0.05, datetime(2024, 9, 1, tzinfo=UTC)),
            (0.052, datetime(2024, 11, 1, tzinfo=UTC)),
            (0.06, datetime(2025, 2, 1, tzinfo=UTC)),
            (0.058, datetime(2025, 4, 1, tzinfo=UTC)),
        ]
        points = compute_trends(data)
        assert len(points) == 3
        assert points[0].period == "2024-H1"
        assert points[0].count == 2
        assert points[1].period == "2024-H2"
        assert points[2].period == "2025-H1"

    def test_compute_trends_empty(self) -> None:
        """Empty input returns empty list."""
        assert compute_trends([]) == []

    def test_compute_trends_returns_trend_points(self) -> None:
        """Result is list of TrendPoint dataclass instances."""
        data: list[tuple[float, datetime]] = [
            (0.05, datetime(2025, 1, 15, tzinfo=UTC)),
            (0.06, datetime(2025, 3, 15, tzinfo=UTC)),
        ]
        points = compute_trends(data)
        assert len(points) == 1
        assert isinstance(points[0], TrendPoint)
        assert points[0].period == "2025-H1"
        assert points[0].count == 2


class TestComputeYoYChanges:
    """Test year-over-year change computation."""

    def test_basic_two_years(self) -> None:
        """2 years with full data produces correct pct changes."""
        years = [
            {
                "policy_year": 2024,
                "total_premium": 100_000.0,
                "total_limit": 5_000_000.0,
                "retention": 500_000.0,
                "program_rate_on_line": 0.02,
                "layers": [
                    {"carrier_name": "AIG"},
                    {"carrier_name": "Chubb"},
                ],
            },
            {
                "policy_year": 2025,
                "total_premium": 120_000.0,
                "total_limit": 5_000_000.0,
                "retention": 750_000.0,
                "program_rate_on_line": 0.024,
                "layers": [
                    {"carrier_name": "AIG"},
                    {"carrier_name": "Zurich"},
                ],
            },
        ]
        changes = compute_yoy_changes(years)
        assert len(changes) == 1
        c = changes[0]
        assert c["from_year"] == 2024
        assert c["to_year"] == 2025

        # Premium went from 100k to 120k = +20%
        assert c["premium_change_pct"] is not None
        assert abs(c["premium_change_pct"] - 20.0) < 0.01

        # Limit unchanged = 0%
        assert c["limit_change_pct"] is not None
        assert abs(c["limit_change_pct"]) < 0.01

        # Retention went from 500k to 750k = +50%
        assert c["retention_change_pct"] is not None
        assert abs(c["retention_change_pct"] - 50.0) < 0.01

        # Carrier rotations
        assert c["carriers_added"] == ["Zurich"]
        assert c["carriers_removed"] == ["Chubb"]

    def test_partial_data(self) -> None:
        """None values in premium/limit handled gracefully."""
        years = [
            {
                "policy_year": 2024,
                "total_premium": None,
                "total_limit": 5_000_000.0,
                "retention": None,
                "program_rate_on_line": None,
                "layers": [],
            },
            {
                "policy_year": 2025,
                "total_premium": 120_000.0,
                "total_limit": 5_000_000.0,
                "retention": None,
                "program_rate_on_line": None,
                "layers": [],
            },
        ]
        changes = compute_yoy_changes(years)
        assert len(changes) == 1
        c = changes[0]
        # Premium has one None, so change is None
        assert c["premium_change_pct"] is None
        # Limit both present
        assert c["limit_change_pct"] is not None
        assert abs(c["limit_change_pct"]) < 0.01
        # Retention both None
        assert c["retention_change_pct"] is None
        # ROL both None
        assert c["rol_change_pct"] is None

    def test_single_year(self) -> None:
        """Single year returns empty list."""
        years = [
            {
                "policy_year": 2025,
                "total_premium": 100_000.0,
                "total_limit": 5_000_000.0,
                "retention": 500_000.0,
                "program_rate_on_line": 0.02,
                "layers": [],
            },
        ]
        assert compute_yoy_changes(years) == []

    def test_empty_input(self) -> None:
        """Empty list returns empty list."""
        assert compute_yoy_changes([]) == []

    def test_three_years(self) -> None:
        """3 years produces 2 change records."""
        years = [
            {
                "policy_year": 2023,
                "total_premium": 80_000.0,
                "total_limit": 5_000_000.0,
                "retention": 500_000.0,
                "program_rate_on_line": 0.016,
                "layers": [],
            },
            {
                "policy_year": 2024,
                "total_premium": 100_000.0,
                "total_limit": 5_000_000.0,
                "retention": 500_000.0,
                "program_rate_on_line": 0.02,
                "layers": [],
            },
            {
                "policy_year": 2025,
                "total_premium": 120_000.0,
                "total_limit": 5_000_000.0,
                "retention": 750_000.0,
                "program_rate_on_line": 0.024,
                "layers": [],
            },
        ]
        changes = compute_yoy_changes(years)
        assert len(changes) == 2
        assert changes[0]["from_year"] == 2023
        assert changes[0]["to_year"] == 2024
        assert changes[1]["from_year"] == 2024
        assert changes[1]["to_year"] == 2025

    def test_zero_previous_premium(self) -> None:
        """Zero previous premium gives None pct_change (div by zero)."""
        years = [
            {
                "policy_year": 2024,
                "total_premium": 0.0,
                "total_limit": 5_000_000.0,
                "retention": None,
                "program_rate_on_line": None,
                "layers": [],
            },
            {
                "policy_year": 2025,
                "total_premium": 100_000.0,
                "total_limit": 5_000_000.0,
                "retention": None,
                "program_rate_on_line": None,
                "layers": [],
            },
        ]
        changes = compute_yoy_changes(years)
        assert changes[0]["premium_change_pct"] is None


class TestDetectCarrierRotations:
    """Test carrier rotation detection."""

    def test_carrier_rotation(self) -> None:
        """Carrier enters year 2, another exits."""
        years = [
            {
                "policy_year": 2024,
                "layers": [
                    {"carrier_name": "AIG"},
                    {"carrier_name": "Chubb"},
                ],
            },
            {
                "policy_year": 2025,
                "layers": [
                    {"carrier_name": "AIG"},
                    {"carrier_name": "Zurich"},
                ],
            },
        ]
        rotations = detect_carrier_rotations(years)
        assert len(rotations) == 1
        r = rotations[0]
        assert r["year"] == 2025
        assert r["carriers_in"] == ["Zurich"]
        assert r["carriers_out"] == ["Chubb"]

    def test_no_rotation(self) -> None:
        """Same carriers in both years returns empty list."""
        years = [
            {
                "policy_year": 2024,
                "layers": [
                    {"carrier_name": "AIG"},
                    {"carrier_name": "Chubb"},
                ],
            },
            {
                "policy_year": 2025,
                "layers": [
                    {"carrier_name": "AIG"},
                    {"carrier_name": "Chubb"},
                ],
            },
        ]
        rotations = detect_carrier_rotations(years)
        assert rotations == []

    def test_single_year(self) -> None:
        """Single year returns empty list."""
        years = [
            {
                "policy_year": 2025,
                "layers": [{"carrier_name": "AIG"}],
            },
        ]
        assert detect_carrier_rotations(years) == []

    def test_tbd_carriers_excluded(self) -> None:
        """TBD carrier name is excluded from rotation tracking."""
        years = [
            {
                "policy_year": 2024,
                "layers": [
                    {"carrier_name": "AIG"},
                    {"carrier_name": "TBD"},
                ],
            },
            {
                "policy_year": 2025,
                "layers": [
                    {"carrier_name": "AIG"},
                ],
            },
        ]
        rotations = detect_carrier_rotations(years)
        # TBD not counted as a real carrier
        assert rotations == []

    def test_empty_layers(self) -> None:
        """Empty layers in both years returns no rotations."""
        years = [
            {"policy_year": 2024, "layers": []},
            {"policy_year": 2025, "layers": []},
        ]
        assert detect_carrier_rotations(years) == []
