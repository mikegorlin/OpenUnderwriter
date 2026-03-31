"""Tests for total liabilities derivation cascade in financial_models.py.

Tests the derive_total_liabilities() function with edge cases:
direct tag, TA-SE derivation, minority interest handling,
L&SE fallback, and graceful None handling.
"""

from __future__ import annotations

import logging

import pytest

from do_uw.stages.analyze.financial_models import derive_total_liabilities


class TestDeriveTotalLiabilitiesDirect:
    """Priority 1: Direct Liabilities tag returns its value."""

    def test_direct_liabilities_returned(self) -> None:
        inputs = {
            "total_liabilities": 200_000.0,
            "total_assets": 500_000.0,
            "stockholders_equity": 300_000.0,
        }
        result = derive_total_liabilities(inputs)
        assert result == 200_000.0

    def test_direct_liabilities_preferred_over_derivation(self) -> None:
        """Even when TA and SE are present, direct value wins."""
        inputs = {
            "total_liabilities": 200_000.0,
            "total_assets": 500_000.0,
            "stockholders_equity": 250_000.0,  # Would derive 250K, but direct wins
        }
        result = derive_total_liabilities(inputs)
        assert result == 200_000.0


class TestDeriveTotalLiabilitiesFromEquation:
    """Priority 2: TA - SE derivation."""

    def test_ta_minus_se_derivation(self) -> None:
        inputs = {
            "total_assets": 500_000.0,
            "stockholders_equity": 300_000.0,
        }
        result = derive_total_liabilities(inputs)
        assert result == 200_000.0


class TestDeriveTotalLiabilitiesMinorityInterest:
    """Priority 3: minority_interest handling."""

    def test_minority_interest_added_when_present(self) -> None:
        """SE tag includes NCI; subtract minority_interest from SE."""
        inputs = {
            "total_assets": 500_000.0,
            "stockholders_equity": 310_000.0,  # Includes 10K NCI
            "minority_interest": 10_000.0,
        }
        # TL = TA - SE + MI = 500K - 310K + 10K = 200K
        result = derive_total_liabilities(inputs)
        assert result == 200_000.0

    def test_minority_interest_zero_ignored(self) -> None:
        """Zero minority interest should not affect derivation."""
        inputs = {
            "total_assets": 500_000.0,
            "stockholders_equity": 300_000.0,
            "minority_interest": 0.0,
        }
        result = derive_total_liabilities(inputs)
        assert result == 200_000.0


class TestDeriveTotalLiabilitiesLSEFallback:
    """Priority 4: LiabilitiesAndStockholdersEquity - SE."""

    def test_lse_minus_se_fallback(self) -> None:
        inputs = {
            "stockholders_equity": 300_000.0,
            "liabilities_and_stockholders_equity": 500_000.0,
        }
        result = derive_total_liabilities(inputs)
        assert result == 200_000.0


class TestDeriveTotalLiabilitiesNone:
    """Returns None when no derivation possible."""

    def test_returns_none_when_nothing_available(self) -> None:
        result = derive_total_liabilities({})
        assert result is None

    def test_returns_none_with_only_ta(self) -> None:
        result = derive_total_liabilities({"total_assets": 500_000.0})
        assert result is None

    def test_returns_none_with_only_se(self) -> None:
        result = derive_total_liabilities({"stockholders_equity": 300_000.0})
        assert result is None

    def test_returns_none_with_only_lse_no_se(self) -> None:
        result = derive_total_liabilities({
            "liabilities_and_stockholders_equity": 500_000.0,
        })
        assert result is None


class TestDeriveTotalLiabilitiesEdgeCases:
    """Edge cases and graceful handling."""

    def test_handles_none_inputs(self) -> None:
        """None values in dict should not raise exceptions."""
        inputs: dict[str, float | None] = {
            "total_liabilities": None,
            "total_assets": None,
            "stockholders_equity": None,
        }
        result = derive_total_liabilities(inputs)
        assert result is None

    def test_tl_greater_than_ta_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """TL > TA should produce a warning (negative equity)."""
        inputs = {
            "total_assets": 100_000.0,
            "stockholders_equity": -50_000.0,  # Negative equity
        }
        # TL = 100K - (-50K) = 150K > 100K TA
        with caplog.at_level(logging.WARNING, logger="do_uw.stages.analyze.financial_models"):
            result = derive_total_liabilities(inputs)
        assert result == 150_000.0
        assert any("negative equity" in record.message for record in caplog.records)

    def test_negative_equity_produces_valid_result(self) -> None:
        """Companies with negative equity should still get valid TL."""
        inputs = {
            "total_assets": 100_000.0,
            "stockholders_equity": -20_000.0,
        }
        result = derive_total_liabilities(inputs)
        assert result == 120_000.0
