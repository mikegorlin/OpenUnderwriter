"""Tests for chart callout generation from signal YAML templates.

Verifies that evaluate_chart_callouts reads callout_templates from signal
YAML, evaluates metrics against thresholds, interpolates {value}/{threshold}
placeholders, and returns properly categorized flags/positives lists.
"""

from __future__ import annotations

import pytest


def test_evaluate_returns_flags_and_positives_keys():
    """Test 1: evaluate_chart_callouts returns dict with flags and positives."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        evaluate_chart_callouts,
    )

    result = evaluate_chart_callouts(None, {}, {})
    assert "flags" in result
    assert "positives" in result
    assert isinstance(result["flags"], list)
    assert isinstance(result["positives"], list)


def test_beta_ratio_above_yellow_produces_flag():
    """Test 2: beta_ratio=1.4 (above yellow=1.3) produces flag with '1.40'."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        evaluate_chart_callouts,
        extract_chart_thresholds,
    )

    thresholds = extract_chart_thresholds(None)
    metrics = {"beta_ratio": 1.4}
    result = evaluate_chart_callouts(None, metrics, thresholds)
    assert len(result["flags"]) >= 1
    beta_flags = [f for f in result["flags"] if "1.40" in f]
    assert len(beta_flags) >= 1, f"Expected beta callout with '1.40', got: {result['flags']}"


def test_alpha_positive_produces_positive():
    """Test 3: alpha_1y=15 (above 10) produces positive with '+15.0%'."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        evaluate_chart_callouts,
        extract_chart_thresholds,
    )

    thresholds = extract_chart_thresholds(None)
    metrics = {"alpha_1y": 15.0}
    result = evaluate_chart_callouts(None, metrics, thresholds)
    assert len(result["positives"]) >= 1
    alpha_pos = [p for p in result["positives"] if "15.0" in p]
    assert len(alpha_pos) >= 1, f"Expected alpha callout with '15.0', got: {result['positives']}"


def test_moderate_metrics_produce_empty_lists():
    """Test 4: When all metrics are moderate, flags and positives are empty."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        evaluate_chart_callouts,
        extract_chart_thresholds,
    )

    thresholds = extract_chart_thresholds(None)
    # All values within safe range
    metrics = {
        "beta_ratio": 1.0,
        "volatility_90d": 0.15,
        "sector_vol_90d": 0.20,
        "max_drawdown_1y": -8.0,
        "decline_from_high_pct": -5.0,
        "alpha_1y": 3.0,
        "idiosyncratic_vol": 10.0,
        "company_specific_drop_count": 0.0,
        "total_drop_count": 1.0,
    }
    result = evaluate_chart_callouts(None, metrics, thresholds)
    assert result["flags"] == [], f"Expected no flags for moderate metrics, got: {result['flags']}"
    assert result["positives"] == [] or all(
        "within" in p.lower() or "below" in p.lower() or "no significant" in p.lower() or "at or below" in p.lower()
        for p in result["positives"]
    ), f"Expected no risk positives, got: {result['positives']}"


def test_callout_text_has_do_context():
    """Test 5: Callout text includes D&O-specific underwriting terms."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        evaluate_chart_callouts,
        extract_chart_thresholds,
    )

    thresholds = extract_chart_thresholds(None)
    metrics = {
        "beta_ratio": 1.6,
        "max_drawdown_1y": -30.0,
        "idiosyncratic_vol": 35.0,
    }
    result = evaluate_chart_callouts(None, metrics, thresholds)
    all_text = " ".join(result["flags"])
    # D&O terms should appear
    do_terms = ["SCA", "loss causation", "plaintiff", "litigation", "securities"]
    found = [t for t in do_terms if t.lower() in all_text.lower()]
    assert len(found) >= 2, f"Expected D&O terms in callout text, found: {found} in: {all_text[:200]}"


def test_no_raw_placeholders_in_output():
    """Test 6: No {value} or {threshold} placeholders remain in output."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        evaluate_chart_callouts,
        extract_chart_thresholds,
    )

    thresholds = extract_chart_thresholds(None)
    metrics = {
        "beta_ratio": 1.6,
        "max_drawdown_1y": -30.0,
        "decline_from_high_pct": -35.0,
        "alpha_1y": 20.0,
        "idiosyncratic_vol": 35.0,
        "company_specific_drop_count": 4.0,
        "total_drop_count": 0.0,
    }
    result = evaluate_chart_callouts(None, metrics, thresholds)
    for text in result["flags"] + result["positives"]:
        assert "{value}" not in text, f"Raw {{value}} in: {text}"
        assert "{threshold}" not in text, f"Raw {{threshold}} in: {text}"


def test_none_metrics_silently_skipped():
    """Test 7: When metrics are None/missing, no KeyError raised."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        evaluate_chart_callouts,
        extract_chart_thresholds,
    )

    thresholds = extract_chart_thresholds(None)
    metrics: dict[str, float | None] = {
        "beta_ratio": None,
        "max_drawdown_1y": None,
    }
    result = evaluate_chart_callouts(None, metrics, thresholds)
    # Should not crash, may return empty lists
    assert isinstance(result["flags"], list)
    assert isinstance(result["positives"], list)


def test_drawdown_red_flag():
    """Max drawdown exceeding red threshold produces flag with D&O context."""
    from do_uw.stages.render.context_builders.chart_thresholds import (
        evaluate_chart_callouts,
        extract_chart_thresholds,
    )

    thresholds = extract_chart_thresholds(None)
    metrics = {"max_drawdown_1y": -25.0}
    result = evaluate_chart_callouts(None, metrics, thresholds)
    dd_flags = [f for f in result["flags"] if "drawdown" in f.lower() or "25" in f]
    assert len(dd_flags) >= 1, f"Expected drawdown flag, got: {result['flags']}"
