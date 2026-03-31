"""Tests for canonical_metrics registry -- single source of truth for cross-section metrics.

Tests use real AAPL state.json when available, falls back to synthetic state.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Try to load real AAPL state.json for integration tests
_AAPL_STATE_PATH = Path(__file__).resolve().parents[1] / "output" / "AAPL" / "state.json"
_MAIN_REPO_AAPL = Path("/Users/gorlin/projects/UW/do-uw/output/AAPL/state.json")


def _load_real_state() -> AnalysisState | None:
    """Load real AAPL state.json if available."""
    for p in (_AAPL_STATE_PATH, _MAIN_REPO_AAPL):
        if p.exists():
            try:
                data = json.loads(p.read_text())
                return AnalysisState.model_validate(data)
            except Exception as exc:
                logger.warning("Failed to load %s: %s", p, exc)
    return None


@pytest.fixture
def real_state() -> AnalysisState:
    """Real AAPL state -- skip if unavailable."""
    st = _load_real_state()
    if st is None:
        pytest.skip("AAPL state.json not available")
    return st


@pytest.fixture
def empty_state() -> AnalysisState:
    """Minimal empty state -- must not crash."""
    return AnalysisState(ticker="TEST")


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------

def test_imports():
    """Module imports cleanly with expected exports."""
    from do_uw.stages.render.canonical_metrics import (
        MetricValue,
        CanonicalMetrics,
        build_canonical_metrics,
    )
    assert MetricValue is not None
    assert CanonicalMetrics is not None
    assert callable(build_canonical_metrics)


# ---------------------------------------------------------------------------
# MetricValue defaults
# ---------------------------------------------------------------------------

def test_metric_value_defaults():
    """MetricValue with all defaults has raw=None, formatted='N/A', etc."""
    from do_uw.stages.render.canonical_metrics import MetricValue

    mv = MetricValue()
    assert mv.raw is None
    assert mv.formatted == "N/A"
    assert mv.source == "none"
    assert mv.confidence == "LOW"
    assert mv.as_of == ""


def test_metric_value_frozen():
    """MetricValue is immutable (frozen)."""
    from do_uw.stages.render.canonical_metrics import MetricValue

    mv = MetricValue(raw=42.0, formatted="$42", source="test", confidence="HIGH")
    with pytest.raises(Exception):
        mv.raw = 99.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Empty state -- graceful degradation
# ---------------------------------------------------------------------------

def test_empty_state_no_crash(empty_state: AnalysisState):
    """build_canonical_metrics(empty_state) returns all N/A defaults without crashing."""
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics

    m = build_canonical_metrics(empty_state)
    assert m.revenue.raw is None
    assert m.revenue.formatted == "N/A"
    assert m.market_cap.raw is None
    assert m.stock_price.raw is None
    assert m.ceo_name.raw is None


# ---------------------------------------------------------------------------
# Real AAPL state -- core metrics populated
# ---------------------------------------------------------------------------

def test_revenue_populated(real_state: AnalysisState):
    """Revenue is populated from XBRL with correct provenance."""
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics

    m = build_canonical_metrics(real_state)
    assert m.revenue.raw is not None
    assert isinstance(m.revenue.raw, (int, float))
    assert m.revenue.raw > 0


def test_revenue_xbrl_source(real_state: AnalysisState):
    """Revenue source starts with 'xbrl:' (XBRL-first priority)."""
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics

    m = build_canonical_metrics(real_state)
    assert m.revenue.source.startswith("xbrl:"), f"Expected xbrl source, got: {m.revenue.source}"


def test_revenue_high_confidence(real_state: AnalysisState):
    """Revenue from XBRL has HIGH confidence."""
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics

    m = build_canonical_metrics(real_state)
    assert m.revenue.confidence == "HIGH"


def test_revenue_as_of(real_state: AnalysisState):
    """Revenue has non-empty as_of field."""
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics

    m = build_canonical_metrics(real_state)
    assert m.revenue.as_of, f"Expected non-empty as_of, got: '{m.revenue.as_of}'"


def test_revenue_formatted(real_state: AnalysisState):
    """Revenue formatted matches pattern like '$XXX.XB'."""
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics

    m = build_canonical_metrics(real_state)
    assert m.revenue.formatted.startswith("$"), f"Expected $ prefix, got: {m.revenue.formatted}"
    assert m.revenue.formatted != "N/A"


def test_all_core_metrics_populated(real_state: AnalysisState):
    """All 8 core metrics are populated (raw is not None) for AAPL."""
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics

    m = build_canonical_metrics(real_state)
    core_fields = [
        ("revenue", m.revenue),
        ("net_income", m.net_income),
        ("market_cap", m.market_cap),
        ("stock_price", m.stock_price),
        ("employees", m.employees),
        ("exchange", m.exchange),
        ("ceo_name", m.ceo_name),
        ("revenue_growth_yoy", m.revenue_growth_yoy),
    ]
    missing = [name for name, mv in core_fields if mv.raw is None]
    assert not missing, f"Core metrics with raw=None: {missing}"


def test_every_populated_metric_has_source(real_state: AnalysisState):
    """Every MetricValue with data has non-empty source and confidence."""
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics, CanonicalMetrics

    m = build_canonical_metrics(real_state)
    for field_name in CanonicalMetrics.model_fields:
        mv = getattr(m, field_name)
        if mv.raw is not None:
            assert mv.source != "none", f"{field_name} has data but source='none'"
            assert mv.confidence in ("HIGH", "MEDIUM", "LOW"), f"{field_name} has invalid confidence"


def test_metric_raw_is_primitive(real_state: AnalysisState):
    """MetricValue.raw is always a primitive (float, int, str, None)."""
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics, CanonicalMetrics
    from do_uw.models.common import SourcedValue

    m = build_canonical_metrics(real_state)
    for field_name in CanonicalMetrics.model_fields:
        mv = getattr(m, field_name)
        assert isinstance(mv.raw, (float, int, str, type(None))), (
            f"{field_name}.raw is {type(mv.raw).__name__}, expected primitive"
        )
        assert not isinstance(mv.raw, SourcedValue), (
            f"{field_name}.raw is a SourcedValue -- must unwrap"
        )


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------

def test_sv_unwraps_sourced_value():
    """_sv helper unwraps SourcedValue to primitive."""
    from do_uw.stages.render.canonical_metrics import _sv
    from do_uw.models.common import SourcedValue, Confidence
    from datetime import datetime, UTC

    sv = SourcedValue(
        value="test_value",
        source="test",
        confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )
    assert _sv(sv) == "test_value"
    assert _sv(None) is None
    assert _sv(42) == 42


def test_xbrl_line_item_extracts_from_real_data(real_state: AnalysisState):
    """_xbrl_line_item extracts value from real AAPL XBRL data."""
    from do_uw.stages.render.canonical_metrics import _xbrl_line_item

    val, period = _xbrl_line_item(
        real_state, "income_statement", ("total_revenue", "revenue", "net_sales")
    )
    assert val is not None, "Expected XBRL revenue value"
    assert isinstance(val, (int, float))
    assert val > 0
    assert period, "Expected non-empty period label"


# ---------------------------------------------------------------------------
# Integration: assembly_registry wiring
# ---------------------------------------------------------------------------

def test_build_html_context_has_canonical():
    """build_html_context stores _canonical and _canonical_obj in context."""
    from do_uw.stages.render.context_builders.assembly_registry import build_html_context

    ctx = build_html_context(AnalysisState(ticker="TEST"))
    assert "_canonical" in ctx, "Missing _canonical dict in context"
    assert "_canonical_obj" in ctx, "Missing _canonical_obj in context"
    assert isinstance(ctx["_canonical"], dict)


def test_build_html_context_canonical_has_revenue():
    """build_html_context canonical dict has revenue entry."""
    from do_uw.stages.render.context_builders.assembly_registry import build_html_context

    ctx = build_html_context(AnalysisState(ticker="TEST"))
    canonical = ctx["_canonical"]
    assert "revenue" in canonical, "Missing revenue in canonical dict"
    assert "formatted" in canonical["revenue"]


# ---------------------------------------------------------------------------
# Integration: builder migration -- backward compatibility
# ---------------------------------------------------------------------------

def test_key_stats_context_backward_compat():
    """build_key_stats_context works without canonical (backward compat)."""
    from do_uw.stages.render.context_builders.key_stats_context import build_key_stats_context

    result = build_key_stats_context(AnalysisState(ticker="TEST"))
    # With no company data, should still return valid dict
    assert isinstance(result, dict)


def test_key_stats_context_with_canonical_none():
    """build_key_stats_context(state, canonical=None) works (backward compat)."""
    from do_uw.stages.render.context_builders.key_stats_context import build_key_stats_context

    result = build_key_stats_context(AnalysisState(ticker="TEST"), canonical=None)
    assert isinstance(result, dict)


def test_scorecard_context_backward_compat():
    """build_scorecard_context works without canonical."""
    from do_uw.stages.render.context_builders.scorecard_context import build_scorecard_context

    result = build_scorecard_context(AnalysisState(ticker="TEST"))
    assert isinstance(result, dict)


def test_uw_analysis_context_backward_compat():
    """build_uw_analysis_context works without canonical."""
    from do_uw.stages.render.context_builders.uw_analysis import build_uw_analysis_context

    result = build_uw_analysis_context(AnalysisState(ticker="TEST"))
    assert isinstance(result, dict)


def test_extract_company_backward_compat():
    """extract_company works without canonical."""
    from do_uw.stages.render.context_builders.company_profile import extract_company

    result = extract_company(AnalysisState(ticker="TEST"))
    assert isinstance(result, dict)


def test_extract_exec_summary_backward_compat():
    """extract_exec_summary works without canonical."""
    from do_uw.stages.render.context_builders.company_exec_summary import extract_exec_summary

    result = extract_exec_summary(AnalysisState(ticker="TEST"))
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Integration: canonical consumption in real state
# ---------------------------------------------------------------------------

def test_key_stats_uses_canonical_revenue(real_state: AnalysisState):
    """When canonical is provided, key_stats revenue_fmt matches canonical.revenue.formatted."""
    from do_uw.stages.render.canonical_metrics import build_canonical_metrics
    from do_uw.stages.render.context_builders.key_stats_context import build_key_stats_context

    canonical = build_canonical_metrics(real_state)
    result = build_key_stats_context(real_state, canonical=canonical)
    if canonical.revenue.raw is not None:
        assert result["revenue_fmt"] == canonical.revenue.formatted, (
            f"key_stats revenue_fmt={result['revenue_fmt']} != canonical={canonical.revenue.formatted}"
        )


def test_build_html_context_canonical_flows_to_key_stats(real_state: AnalysisState):
    """build_html_context passes canonical through to key_stats builder."""
    from do_uw.stages.render.context_builders.assembly_registry import build_html_context
    from do_uw.stages.render.canonical_metrics import CanonicalMetrics

    ctx = build_html_context(real_state)
    canonical_obj = ctx.get("_canonical_obj")
    assert isinstance(canonical_obj, CanonicalMetrics), "Expected CanonicalMetrics object"
    # key_stats should be populated (AAPL has company data)
    key_stats = ctx.get("key_stats", {})
    if key_stats.get("available") and canonical_obj.revenue.raw is not None:
        assert key_stats["revenue_fmt"] == canonical_obj.revenue.formatted
