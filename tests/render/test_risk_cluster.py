"""Tests for risk cluster computation.

Verifies that compute_risk_clusters() groups factors by role dimension,
identifies dominant clusters, and computes correct percentages.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders.scenario_generator import (
    compute_risk_clusters,
)


def _make_factor(
    factor_id: str,
    factor_name: str,
    max_points: int,
    points_deducted: float,
) -> MagicMock:
    """Build a mock FactorScore."""
    mf = MagicMock()
    mf.factor_id = factor_id
    mf.factor_name = factor_name
    mf.max_points = max_points
    mf.points_deducted = points_deducted
    return mf


class TestComputeRiskClusters:
    """Test suite for compute_risk_clusters."""

    def test_groups_by_role_dimension(self) -> None:
        """Test 1: Groups factors into expected role-based clusters."""
        factors = [
            _make_factor("F1", "Prior Litigation", 20, 10.0),
            _make_factor("F2", "Stock Price Analysis", 12, 5.0),
            _make_factor("F3", "Financial Quality", 15, 3.0),
            _make_factor("F4", "IPO/SPAC/M&A", 8, 2.0),
            _make_factor("F5", "Earnings/Guidance", 8, 1.0),
            _make_factor("F6", "Short Interest", 8, 1.0),
            _make_factor("F7", "Volatility", 8, 2.0),
            _make_factor("F8", "Related Party", 5, 1.0),
            _make_factor("F9", "Governance Quality", 8, 3.0),
            _make_factor("F10", "Board Quality", 8, 2.0),
        ]
        result = compute_risk_clusters(factors)
        assert isinstance(result, list)
        names = {c["name"] for c in result}
        assert "Litigation & History" in names
        assert "Stock & Market" in names
        assert "Corporate Actions" in names
        assert "Governance & Leadership" in names

    def test_dominant_cluster_over_50_pct(self) -> None:
        """Test 2: Cluster with >50% of total deductions marked dominant."""
        factors = [
            _make_factor("F1", "Prior Litigation", 20, 20.0),  # Dominant
            _make_factor("F2", "Stock Price", 12, 1.0),
            _make_factor("F3", "Financial Quality", 15, 1.0),
            _make_factor("F4", "IPO", 8, 0.0),
            _make_factor("F5", "Earnings", 8, 1.0),
            _make_factor("F6", "Short Interest", 8, 1.0),
            _make_factor("F7", "Volatility", 8, 1.0),
            _make_factor("F8", "Related Party", 5, 0.0),
            _make_factor("F9", "Governance", 8, 1.0),
            _make_factor("F10", "Board", 8, 0.0),
        ]
        result = compute_risk_clusters(factors)
        lit_cluster = [c for c in result if c["name"] == "Litigation & History"]
        assert len(lit_cluster) == 1
        assert lit_cluster[0]["is_dominant"] is True
        assert lit_cluster[0]["pct_of_total"] > 0.50

    def test_expected_cluster_groupings(self) -> None:
        """Test 3: Correct factor groupings in each cluster."""
        factors = [
            _make_factor("F1", "Prior Litigation", 20, 5.0),
            _make_factor("F2", "Stock Price", 12, 3.0),
            _make_factor("F3", "Financial Quality", 15, 2.0),
            _make_factor("F4", "IPO", 8, 1.0),
            _make_factor("F5", "Earnings", 8, 1.0),
            _make_factor("F6", "Short Interest", 8, 2.0),
            _make_factor("F7", "Volatility", 8, 2.0),
            _make_factor("F8", "Related Party", 5, 1.0),
            _make_factor("F9", "Governance", 8, 3.0),
            _make_factor("F10", "Board", 8, 2.0),
        ]
        result = compute_risk_clusters(factors)
        cluster_map = {c["name"]: c for c in result}

        # Stock & Market = F2 + F5 + F6 + F7
        sm = cluster_map["Stock & Market"]
        assert sm["factor_ids"] == ["F2", "F5", "F6", "F7"]
        assert sm["total_points"] == 3.0 + 1.0 + 2.0 + 2.0

        # Corporate Actions = F4 + F8
        ca = cluster_map["Corporate Actions"]
        assert ca["factor_ids"] == ["F4", "F8"]
        assert ca["total_points"] == 1.0 + 1.0

        # Governance = F9 + F10
        gl = cluster_map["Governance & Leadership"]
        assert gl["factor_ids"] == ["F9", "F10"]
        assert gl["total_points"] == 3.0 + 2.0

    def test_pct_of_total_sums_to_one(self) -> None:
        """Test 4: pct_of_total sums to 1.0 across all clusters."""
        factors = [
            _make_factor("F1", "Prior Litigation", 20, 5.0),
            _make_factor("F2", "Stock Price", 12, 3.0),
            _make_factor("F3", "Financial Quality", 15, 2.0),
            _make_factor("F4", "IPO", 8, 1.0),
            _make_factor("F5", "Earnings", 8, 1.0),
            _make_factor("F6", "Short Interest", 8, 2.0),
            _make_factor("F7", "Volatility", 8, 2.0),
            _make_factor("F8", "Related Party", 5, 1.0),
            _make_factor("F9", "Governance", 8, 3.0),
            _make_factor("F10", "Board", 8, 2.0),
        ]
        result = compute_risk_clusters(factors)
        total_pct = sum(c["pct_of_total"] for c in result)
        assert abs(total_pct - 1.0) < 0.01, f"pct_of_total sums to {total_pct}, expected 1.0"

    def test_distributed_profile_no_dominant(self) -> None:
        """Distributed profile (all factors equal) has no dominant cluster."""
        factors = [
            _make_factor("F1", "Prior Litigation", 20, 5.0),
            _make_factor("F2", "Stock Price", 12, 5.0),
            _make_factor("F3", "Financial Quality", 15, 5.0),
            _make_factor("F4", "IPO", 8, 5.0),
            _make_factor("F5", "Earnings", 8, 5.0),
            _make_factor("F6", "Short Interest", 8, 5.0),
            _make_factor("F7", "Volatility", 8, 5.0),
            _make_factor("F8", "Related Party", 5, 5.0),
            _make_factor("F9", "Governance", 8, 5.0),
            _make_factor("F10", "Board", 8, 5.0),
        ]
        result = compute_risk_clusters(factors)
        dominant = [c for c in result if c["is_dominant"]]
        # With equal factors, Stock & Market (4 factors) = 40% -- not dominant
        # No cluster should be >50%
        assert len(dominant) == 0, f"No cluster should be dominant with equal factors: {dominant}"

    def test_empty_factors(self) -> None:
        """Empty factor list returns empty clusters."""
        result = compute_risk_clusters([])
        assert result == []
