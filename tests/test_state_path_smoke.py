"""Smoke test: verify state path accessors against real pipeline output.

Loads a real state.json from the most recent pipeline run and calls every
typed accessor from state_paths.py. Verifies return types and flags paths
that return empty/None when data should be present.

This test catches the class of bug where context builders navigate to
state paths that don't exist on the real model but pass in MagicMock tests.

Run: uv run pytest tests/test_state_path_smoke.py -v
Skip: Requires output/*/state.json from a prior pipeline run.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Find the most recent state.json
_OUTPUT_DIR = Path("output")


def _find_latest_state_json() -> Path | None:
    """Find most recent state.json in output directory."""
    candidates = list(_OUTPUT_DIR.glob("*/state.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


STATE_JSON = _find_latest_state_json()

pytestmark = pytest.mark.skipif(
    STATE_JSON is None,
    reason="No state.json found in output/ — run pipeline first",
)


@pytest.fixture(scope="module")
def state():
    """Load real AnalysisState from pipeline output."""
    from do_uw.models.state import AnalysisState

    with open(STATE_JSON) as f:  # type: ignore[arg-type]
        raw = json.load(f)
    return AnalysisState.model_validate(raw)


class TestStatePathAccessors:
    """Verify every accessor returns the expected type without exceptions."""

    def test_get_insider_transactions(self, state):
        from do_uw.stages.render.state_paths import get_insider_transactions

        result = get_insider_transactions(state)
        assert isinstance(result, list)

    def test_get_insider_transactions_yfinance(self, state):
        from do_uw.stages.render.state_paths import get_insider_transactions_yfinance

        result = get_insider_transactions_yfinance(state)
        assert isinstance(result, dict)
        # AAPL should have insider data
        if result:
            assert "Insider" in result or "insider" in str(result.keys()).lower()

    def test_get_market_history(self, state):
        from do_uw.stages.render.state_paths import get_market_history

        result = get_market_history(state)
        assert isinstance(result, dict)
        if result:
            assert "Date" in result or "Close" in result

    def test_get_earnings_dates(self, state):
        from do_uw.stages.render.state_paths import get_earnings_dates

        result = get_earnings_dates(state)
        assert isinstance(result, dict)

    def test_get_eps_revisions(self, state):
        from do_uw.stages.render.state_paths import get_eps_revisions

        result = get_eps_revisions(state)
        assert isinstance(result, dict)

    def test_get_analyst_price_targets(self, state):
        from do_uw.stages.render.state_paths import get_analyst_price_targets

        result = get_analyst_price_targets(state)
        assert isinstance(result, dict)

    def test_get_filing_documents(self, state):
        from do_uw.stages.render.state_paths import get_filing_documents

        result = get_filing_documents(state)
        assert isinstance(result, dict)

    def test_get_filings(self, state):
        from do_uw.stages.render.state_paths import get_filings

        # May be None or a model — just verify no crash
        from do_uw.stages.render.state_paths import get_filings

        get_filings(state)  # No exception = pass

    def test_get_risk_factors(self, state):
        from do_uw.stages.render.state_paths import get_risk_factors

        result = get_risk_factors(state)
        assert isinstance(result, list)

    def test_get_ten_k_yoy(self, state):
        from do_uw.stages.render.state_paths import get_ten_k_yoy

        # May be None if < 2 10-K extractions
        get_ten_k_yoy(state)

    def test_get_board_profile(self, state):
        from do_uw.stages.render.state_paths import get_board_profile

        get_board_profile(state)

    def test_get_governance_forensics(self, state):
        from do_uw.stages.render.state_paths import get_governance_forensics

        get_governance_forensics(state)

    def test_get_securities_class_actions(self, state):
        from do_uw.stages.render.state_paths import get_securities_class_actions

        result = get_securities_class_actions(state)
        assert isinstance(result, list)

    def test_get_regulatory_proceedings(self, state):
        from do_uw.stages.render.state_paths import get_regulatory_proceedings

        result = get_regulatory_proceedings(state)
        assert isinstance(result, list)

    def test_get_forward_looking(self, state):
        from do_uw.stages.render.state_paths import get_forward_looking

        get_forward_looking(state)

    def test_get_scoring(self, state):
        from do_uw.stages.render.state_paths import get_scoring

        get_scoring(state)


class TestContextBuildersAgainstRealState:
    """Verify context builders produce non-empty output from real state."""

    def test_earnings_trust_has_data(self, state):
        from do_uw.stages.render.context_builders._market_acquired_data import (
            build_earnings_trust,
        )

        result = build_earnings_trust(state)
        assert result.get("earnings_reaction"), "Earnings reaction should have data"

    def test_correlation_metrics_has_data(self, state):
        from do_uw.stages.render.context_builders._market_correlation import (
            build_correlation_metrics,
        )

        result = build_correlation_metrics(state)
        cm = result.get("correlation_metrics", {})
        assert cm.get("corr_spy") != "N/A", "Correlation vs SPY should have data"

    def test_risk_factor_review_has_data(self, state):
        from do_uw.stages.render.context_builders._company_intelligence import (
            build_risk_factor_review,
        )

        result = build_risk_factor_review(state)
        assert result.get("has_risk_factor_review"), "Risk factor review should have data"

    def test_per_insider_has_data(self, state):
        from do_uw.stages.render.context_builders._governance_intelligence import (
            build_per_insider_activity,
        )

        result = build_per_insider_activity(state)
        assert result.get("has_per_insider_activity"), "Per-insider should have data (yfinance fallback)"

    def test_forward_scenarios_has_data(self, state):
        from do_uw.stages.render.context_builders._forward_scenarios import (
            build_forward_scenarios,
        )

        result = build_forward_scenarios(state)
        assert result.get("scenarios_available"), "Forward scenarios should be available"
        assert len(result.get("scenarios", [])) >= 3, "Should have at least 3 scenarios"
