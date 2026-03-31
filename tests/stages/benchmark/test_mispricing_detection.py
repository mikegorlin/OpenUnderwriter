"""Tests for model-vs-market mispricing detection.

Tests check_model_vs_market_mispricing() from market_position.py which
compares the actuarial model indicated ROL to market median ROL and
flags divergence exceeding 20%.
"""

from __future__ import annotations

from do_uw.stages.benchmark.market_position import (
    check_model_vs_market_mispricing,
)


class TestModelVsMarketMispricing:
    """Tests for check_model_vs_market_mispricing()."""

    def test_within_threshold_returns_none(self) -> None:
        """Model ROL 10% above market median -> within 20% -> None."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=0.044,
            market_median_rol=0.040,
            peer_count=15,
            ci_low=0.035,
            ci_high=0.045,
        )
        assert result is None

    def test_exactly_at_threshold_returns_none(self) -> None:
        """Model ROL exactly 20% above market -> not strictly greater -> None."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=0.048,
            market_median_rol=0.040,
            peer_count=10,
            ci_low=None,
            ci_high=None,
        )
        assert result is None

    def test_model_above_market_underpriced_alert(self) -> None:
        """Model ROL 25% above market median -> UNDERPRICED BY MARKET alert."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=0.050,
            market_median_rol=0.040,
            peer_count=15,
            ci_low=0.035,
            ci_high=0.045,
        )
        assert result is not None
        assert "MODEL SUGGESTS UNDERPRICED BY MARKET" in result
        assert "0.0500" in result
        assert "0.0400" in result
        assert "n=15" in result
        assert "CI: 0.0350-0.0450" in result

    def test_model_below_market_overpriced_alert(self) -> None:
        """Model ROL 30% below market median -> OVERPRICED BY MARKET alert."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=0.028,
            market_median_rol=0.040,
            peer_count=12,
            ci_low=0.032,
            ci_high=0.048,
        )
        assert result is not None
        assert "MODEL SUGGESTS OVERPRICED BY MARKET" in result
        assert "0.0280" in result
        assert "0.0400" in result
        assert "n=12" in result
        assert "CI: 0.0320-0.0480" in result

    def test_zero_model_rol_returns_none(self) -> None:
        """Zero model ROL -> guard returns None."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=0.0,
            market_median_rol=0.040,
            peer_count=10,
            ci_low=None,
            ci_high=None,
        )
        assert result is None

    def test_zero_market_median_returns_none(self) -> None:
        """Zero market median -> guard returns None."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=0.050,
            market_median_rol=0.0,
            peer_count=10,
            ci_low=None,
            ci_high=None,
        )
        assert result is None

    def test_negative_inputs_return_none(self) -> None:
        """Negative inputs -> guard returns None."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=-0.01,
            market_median_rol=0.040,
            peer_count=10,
            ci_low=None,
            ci_high=None,
        )
        assert result is None

    def test_ci_values_omitted_when_none(self) -> None:
        """CI values omitted from alert string when None."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=0.060,
            market_median_rol=0.040,
            peer_count=8,
            ci_low=None,
            ci_high=None,
        )
        assert result is not None
        assert "CI:" not in result
        assert "n=8" in result

    def test_ci_values_included_when_provided(self) -> None:
        """CI values included in alert when both are provided."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=0.060,
            market_median_rol=0.040,
            peer_count=20,
            ci_low=0.030,
            ci_high=0.050,
        )
        assert result is not None
        assert "CI: 0.0300-0.0500" in result

    def test_underpriced_alert_includes_risk_explanation(self) -> None:
        """UNDERPRICED alert includes risk assessment context."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=0.060,
            market_median_rol=0.040,
            peer_count=15,
            ci_low=None,
            ci_high=None,
        )
        assert result is not None
        assert "Risk assessment indicates higher loss potential" in result

    def test_overpriced_alert_includes_market_context(self) -> None:
        """OVERPRICED alert includes market pricing context."""
        result = check_model_vs_market_mispricing(
            model_indicated_rol=0.028,
            market_median_rol=0.040,
            peer_count=15,
            ci_low=None,
            ci_high=None,
        )
        assert result is not None
        assert "Market pricing exceeds model-indicated risk" in result
