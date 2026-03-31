"""Tests for chart threshold extraction from signal YAML.

Validates that extract_chart_thresholds returns correct numeric thresholds
for all chart-evaluated metrics, matching the values defined in signal YAML
evaluation blocks.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


def test_extract_chart_thresholds_returns_expected_keys():
    """extract_chart_thresholds returns dict with keys for all chart metrics."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        extract_chart_thresholds,
    )

    result = extract_chart_thresholds(None)

    expected_keys = {
        "beta_ratio",
        "volatility",
        "idiosyncratic_vol",
        "max_drawdown",
        "decline_from_high",
        "alpha",
        "divergence",
        "mdd_ratio",
        "vol_ratio",
        "drop_severity",
        "volume_spike",
        "company_specific_drops",
        "decline_current",
        "decline_near_high",
        "beta_performance",
    }
    assert expected_keys.issubset(set(result.keys())), (
        f"Missing keys: {expected_keys - set(result.keys())}"
    )


def test_threshold_entries_have_numeric_red_and_yellow():
    """Each threshold entry has numeric .red and .yellow values."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        extract_chart_thresholds,
    )

    result = extract_chart_thresholds(None)

    for key, spec in result.items():
        assert isinstance(spec, dict), f"{key} is not a dict"
        assert "red" in spec, f"{key} missing 'red'"
        assert "yellow" in spec, f"{key} missing 'yellow'"
        assert isinstance(spec["red"], (int, float)), (
            f"{key}.red is not numeric: {spec['red']}"
        )
        assert isinstance(spec["yellow"], (int, float)), (
            f"{key}.yellow is not numeric: {spec['yellow']}"
        )


def test_threshold_values_match_expected():
    """Threshold values match the values previously hardcoded in templates."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        extract_chart_thresholds,
    )

    result = extract_chart_thresholds(None)

    # Beta ratio: template had > 1.3
    assert result["beta_ratio"]["red"] == pytest.approx(1.5)
    assert result["beta_ratio"]["yellow"] == pytest.approx(1.3)

    # Decline from high: template had >= 30 and >= 15
    assert result["decline_from_high"]["red"] == pytest.approx(30.0)
    assert result["decline_from_high"]["yellow"] == pytest.approx(15.0)

    # MDD ratio: template had > 1.5 and > 1.0
    assert result["mdd_ratio"]["red"] == pytest.approx(1.5)
    assert result["mdd_ratio"]["yellow"] == pytest.approx(1.0)

    # Max drawdown: template had < -20
    assert result["max_drawdown"]["red"] == pytest.approx(-20.0)
    assert result["max_drawdown"]["yellow"] == pytest.approx(-15.0)

    # Volatility: template had > 40 and > 35
    assert result["volatility"]["red"] == pytest.approx(40.0)
    assert result["volatility"]["yellow"] == pytest.approx(35.0)

    # Idiosyncratic vol: template had > 30
    assert result["idiosyncratic_vol"]["red"] == pytest.approx(30.0)
    assert result["idiosyncratic_vol"]["yellow"] == pytest.approx(20.0)

    # Vol ratio: template had > 1.3
    assert result["vol_ratio"]["red"] == pytest.approx(1.5)
    assert result["vol_ratio"]["yellow"] == pytest.approx(1.3)

    # Divergence: overlay had 10.0
    assert result["divergence"]["red"] == pytest.approx(20.0)
    assert result["divergence"]["yellow"] == pytest.approx(10.0)

    # Volume spike: overlay had 2.0
    assert result["volume_spike"]["red"] == pytest.approx(2.0)
    assert result["volume_spike"]["yellow"] == pytest.approx(1.5)

    # Drop severity: overlay had -10.0
    assert result["drop_severity"]["red"] == pytest.approx(-10.0)
    assert result["drop_severity"]["yellow"] == pytest.approx(-5.0)

    # Company-specific drops: template had >= 2
    assert result["company_specific_drops"]["red"] == pytest.approx(3.0)
    assert result["company_specific_drops"]["yellow"] == pytest.approx(2.0)

    # Alpha: template had > 10
    assert result["alpha"]["red"] == pytest.approx(15.0)
    assert result["alpha"]["yellow"] == pytest.approx(10.0)

    # Beta performance: template had > 1.5
    assert result["beta_performance"]["red"] == pytest.approx(1.5)
    assert result["beta_performance"]["yellow"] == pytest.approx(1.3)


def test_fallback_when_brain_loader_unavailable():
    """extract_chart_thresholds returns stable defaults when BrainLoader fails."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        extract_chart_thresholds,
    )

    with patch(
        "do_uw.stages.render.context_builders.chart_thresholds.load_signals",
        side_effect=Exception("BrainLoader unavailable"),
    ):
        result = extract_chart_thresholds(None)

    # Should still return complete threshold dict via fallback
    assert "beta_ratio" in result
    assert "mdd_ratio" in result
    assert "decline_from_high" in result
    assert isinstance(result["beta_ratio"]["red"], float)


def test_extract_chart_thresholds_with_none_state():
    """Passing None as state should work (thresholds come from YAML, not state)."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        extract_chart_thresholds,
    )

    result = extract_chart_thresholds(None)
    assert len(result) >= 10, f"Expected at least 10 thresholds, got {len(result)}"
