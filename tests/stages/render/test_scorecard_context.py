"""Tests for scorecard context builder (Phase 114-01)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders.scorecard_context import (
    build_scorecard_context,
)


def _make_state(**overrides: Any) -> MagicMock:
    """Create a minimal mock AnalysisState."""
    state = MagicMock()
    state.scoring = overrides.get("scoring")
    state.company = overrides.get("company")
    state.extracted = overrides.get("extracted")
    state.analysis = overrides.get("analysis")
    return state


def _make_scoring(**kw: Any) -> MagicMock:
    """Create a mock scoring result with factor_scores and red_flags."""
    sc = MagicMock()
    sc.quality_score = kw.get("quality_score", 85.0)
    sc.composite_score = kw.get("composite_score", 72.0)
    sc.tier = MagicMock()
    sc.tier.tier = kw.get("tier", "STANDARD")
    sc.factor_scores = kw.get("factor_scores", [])
    sc.red_flags = kw.get("red_flags", [])
    hae = MagicMock()
    hae.composites = kw.get("composites", {"host": 0.3, "agent": 0.5, "environment": 0.2})
    hae.tier = kw.get("hae_tier", "STANDARD")
    hae.product_score = 0.0
    hae.confidence = "N/A"
    hae.tier_source = ""
    hae.crf_vetoes = []
    sc.hae_result = hae
    # Attributes that _build_* helpers access via getattr
    sc.claim_probability = None
    sc.severity_result = None
    sc.severity_scenarios = None
    sc.tower_recommendation = None
    sc.actuarial_pricing = None
    sc.risk_type = None
    sc.allegation_mapping = None
    return sc


class TestScorecardContext:
    def test_with_scoring_returns_available_true(self) -> None:
        state = _make_state(scoring=_make_scoring())
        ctx = build_scorecard_context(state)
        assert ctx["scorecard_available"] is True
        assert ctx["tier"] == "STANDARD"
        assert ctx["quality_score"] == 85.0

    def test_without_scoring_returns_available_false(self) -> None:
        state = _make_state(scoring=None)
        ctx = build_scorecard_context(state)
        assert ctx["scorecard_available"] is False

    def test_factors_summary_list(self) -> None:
        f1 = MagicMock()
        f1.factor_id = "F1"
        f1.factor_name = "Financial Health"
        f1.points_deducted = 3.0
        f1.max_points = 15.0
        f1.evidence = []
        f1.signal_coverage = None
        f1.signal_contributions = None
        f1.scoring_method = "rule_based"
        f2 = MagicMock()
        f2.factor_id = "F9"
        f2.factor_name = "Governance Quality"
        f2.points_deducted = 7.0
        f2.max_points = 10.0
        f2.evidence = []
        f2.signal_coverage = None
        f2.signal_contributions = None
        f2.scoring_method = "rule_based"
        sc = _make_scoring(factor_scores=[f1, f2])
        state = _make_state(scoring=sc)
        ctx = build_scorecard_context(state)
        assert len(ctx["factors_summary"]) == 2
        # _FACTOR_LABELS maps F1 -> "Prior Litigation"
        assert ctx["factors_summary"][0]["name"] == "Prior Litigation"
        assert ctx["factors_summary"][0]["pct"] == 20  # 3/15

    def test_top_concerns_only_triggered_sorted_by_severity(self) -> None:
        """top_concerns should only include TRIGGERED signals, sorted by threshold_level desc."""
        sr = {
            "SIG_A": {"status": "TRIGGERED", "threshold_level": "yellow", "value": 1.0,
                       "evidence": "a", "source": "s", "confidence": "HIGH"},
            "SIG_B": {"status": "CLEAR", "threshold_level": "", "value": 0.0,
                       "evidence": "", "source": "s", "confidence": "HIGH"},
            "SIG_C": {"status": "TRIGGERED", "threshold_level": "red", "value": 2.0,
                       "evidence": "c", "source": "s", "confidence": "HIGH"},
        }
        state = _make_state(scoring=_make_scoring())
        state.analysis = MagicMock()
        state.analysis.signal_results = sr
        ctx = build_scorecard_context(state)
        # Only TRIGGERED signals
        ids = [c["signal_id"] for c in ctx["top_concerns"]]
        assert "SIG_B" not in ids
        # Red first
        assert ctx["top_concerns"][0]["signal_id"] == "SIG_C"
        assert len(ctx["top_concerns"]) <= 8

    def test_metrics_strip(self) -> None:
        """Metrics strip should return pre-formatted display strings."""
        state = _make_state(scoring=_make_scoring())
        company = MagicMock(spec=[])
        company.employee_count = MagicMock()
        company.employee_count.value = 50000
        company.years_public = MagicMock()
        company.years_public.value = 25
        company.market_cap = MagicMock()
        company.market_cap.value = 10_000_000_000
        state.company = company
        extracted = MagicMock()
        mkt = MagicMock()
        mkt.stock.market_cap_yf = MagicMock()
        mkt.stock.market_cap_yf.value = 10_000_000_000
        extracted.market = mkt
        # Revenue comes from income_statement line_items
        fin = MagicMock()
        income = MagicMock()
        income.periods = ["FY2025"]
        rev_li = MagicMock()
        rev_li.label = "Total revenue / net sales"
        rev_sv = MagicMock()
        rev_sv.value = 5_000_000_000
        rev_li.values = {"FY2025": rev_sv}
        income.line_items = [rev_li]
        stmts = MagicMock()
        stmts.income_statement = income
        fin.statements = stmts
        extracted.financials = fin
        state.extracted = extracted
        ctx = build_scorecard_context(state)
        ms = ctx["metrics_strip"]
        # Values are now pre-formatted display strings
        assert ms["market_cap"] == "$10.0B"
        assert ms["employees"] == "50,000"
        assert ms["years_public"] == "25"
        assert ms["revenue"] == "$5.0B"
