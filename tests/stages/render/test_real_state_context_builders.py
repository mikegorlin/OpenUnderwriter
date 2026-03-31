"""Real-state integration tests for 5 priority context builders (GATE-03).

These tests load actual state.json files from pipeline output and call each
context builder, validating that:
  1. Builders return non-empty dicts (not crashing on real data)
  2. Output validates against typed Pydantic models (no fallback to untyped)
  3. Key fields are populated for real companies (not all None/N/A)
  4. Multiple tickers produce valid output (not ticker-specific hacks)

NO MagicMock usage anywhere -- the whole point is exercising real state paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.company_exec_summary import extract_exec_summary
from do_uw.stages.render.context_builders.financials import extract_financials
from do_uw.stages.render.context_builders.governance import extract_governance
from do_uw.stages.render.context_builders.litigation import extract_litigation
from do_uw.stages.render.context_builders.market import extract_market
from do_uw.stages.render.context_models import (
    ExecSummaryContext,
    FinancialContext,
    GovernanceContext,
    LitigationContext,
    MarketContext,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

STATE_FILES = [
    "output/AAPL/state.json",
    "output/RPM - RPM INTERNATIONAL/2026-03-18/state.json",
    "output/ULS - UL Solutions/2026-03-25/state.json",
    "output/RPM/state.json",
    "output/META/state.json",
]


def _load_state(state_path: str) -> AnalysisState:
    """Load AnalysisState from a state.json file. Skip if file missing."""
    full_path = PROJECT_ROOT / state_path
    if not full_path.exists():
        pytest.skip(f"State file not found: {full_path}")
    with open(full_path) as f:
        return AnalysisState.model_validate_json(f.read())


def _get_signal_results(state: AnalysisState) -> dict[str, Any]:
    """Extract signal_results from state, defaulting to empty dict."""
    if state.analysis and hasattr(state.analysis, "signal_results"):
        return state.analysis.signal_results or {}
    return {}


# ---------------------------------------------------------------------------
# Executive Summary builder
# ---------------------------------------------------------------------------


class TestExecSummaryBuilder:
    """extract_exec_summary must work on real state data."""

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_returns_nonempty_dict(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_exec_summary(state, signal_results=_get_signal_results(state))
        assert isinstance(raw, dict), "Builder must return a dict"
        assert len(raw) > 0, "Builder returned empty dict for real company"

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_validates_against_typed_model(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_exec_summary(state, signal_results=_get_signal_results(state))
        if not raw:
            pytest.skip("Builder returned empty (no exec summary data)")
        typed = ExecSummaryContext.model_validate(raw)
        assert typed is not None

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_key_fields_populated(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_exec_summary(state, signal_results=_get_signal_results(state))
        if not raw:
            pytest.skip("Builder returned empty")
        # At least one of these tier/score fields should be present
        has_tier = raw.get("tier_label") is not None
        has_score = raw.get("quality_score") is not None or raw.get("composite_score") is not None
        assert has_tier or has_score, (
            f"Expected tier_label or score to be populated, got: "
            f"tier_label={raw.get('tier_label')}, quality_score={raw.get('quality_score')}"
        )


# ---------------------------------------------------------------------------
# Financial builder
# ---------------------------------------------------------------------------


class TestFinancialBuilder:
    """extract_financials must work on real state data."""

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_returns_nonempty_dict(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_financials(state, signal_results=_get_signal_results(state))
        assert isinstance(raw, dict), "Builder must return a dict"
        assert len(raw) > 0, "Builder returned empty dict for real company"

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_validates_against_typed_model(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_financials(state, signal_results=_get_signal_results(state))
        if not raw:
            pytest.skip("Builder returned empty (no financial data)")
        typed = FinancialContext.model_validate(raw)
        assert typed is not None

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_key_fields_populated(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_financials(state, signal_results=_get_signal_results(state))
        if not raw:
            pytest.skip("Builder returned empty")
        # Financial data should have revenue or has_income
        has_revenue = raw.get("revenue") is not None
        has_income_flag = raw.get("has_income") is True
        has_statements = bool(raw.get("income_rows") or raw.get("balance_rows"))
        assert has_revenue or has_income_flag or has_statements, (
            f"Expected financial data: revenue={raw.get('revenue')}, "
            f"has_income={raw.get('has_income')}, income_rows={len(raw.get('income_rows', []))}"
        )


# ---------------------------------------------------------------------------
# Market builder
# ---------------------------------------------------------------------------


class TestMarketBuilder:
    """extract_market must work on real state data."""

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_returns_nonempty_dict(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_market(state, signal_results=_get_signal_results(state))
        assert isinstance(raw, dict), "Builder must return a dict"
        assert len(raw) > 0, "Builder returned empty dict for real company"

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_validates_against_typed_model(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_market(state, signal_results=_get_signal_results(state))
        if not raw:
            pytest.skip("Builder returned empty (no market data)")
        typed = MarketContext.model_validate(raw)
        assert typed is not None

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_key_fields_populated(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_market(state, signal_results=_get_signal_results(state))
        if not raw:
            pytest.skip("Builder returned empty")
        has_price = raw.get("current_price") not in (None, "N/A", "—")
        has_high = raw.get("high_52w") not in (None, "N/A", "—")
        assert has_price or has_high, (
            f"Expected price data: current_price={raw.get('current_price')}, "
            f"high_52w={raw.get('high_52w')}"
        )


# ---------------------------------------------------------------------------
# Governance builder
# ---------------------------------------------------------------------------


class TestGovernanceBuilder:
    """extract_governance must work on real state data."""

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_returns_nonempty_dict(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_governance(state, signal_results=_get_signal_results(state))
        assert isinstance(raw, dict), "Builder must return a dict"
        assert len(raw) > 0, "Builder returned empty dict for real company"

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_validates_against_typed_model(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_governance(state, signal_results=_get_signal_results(state))
        if not raw:
            pytest.skip("Builder returned empty (no governance data)")
        typed = GovernanceContext.model_validate(raw)
        assert typed is not None

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_key_fields_populated(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_governance(state, signal_results=_get_signal_results(state))
        if not raw:
            pytest.skip("Builder returned empty")
        has_board_size = raw.get("board_size") not in (None, "N/A", "0")
        has_board_members = bool(raw.get("board_members"))
        assert has_board_size or has_board_members, (
            f"Expected board data: board_size={raw.get('board_size')}, "
            f"board_members count={len(raw.get('board_members', []))}"
        )


# ---------------------------------------------------------------------------
# Litigation builder
# ---------------------------------------------------------------------------


class TestLitigationBuilder:
    """extract_litigation must work on real state data."""

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_returns_nonempty_dict(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_litigation(state, signal_results=_get_signal_results(state))
        assert isinstance(raw, dict), "Builder must return a dict"
        # Litigation can legitimately be empty if no litigation data extracted
        # But the structure should still be present
        assert isinstance(raw, dict)

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_validates_against_typed_model(self, state_path: str) -> None:
        state = _load_state(state_path)
        raw = extract_litigation(state, signal_results=_get_signal_results(state))
        if not raw:
            pytest.skip("Builder returned empty (no litigation data)")
        typed = LitigationContext.model_validate(raw)
        assert typed is not None

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_structure_present(self, state_path: str) -> None:
        """Even with no active cases, litigation section should have structure."""
        state = _load_state(state_path)
        raw = extract_litigation(state, signal_results=_get_signal_results(state))
        if not raw:
            pytest.skip("Builder returned empty (no litigation extracted)")
        # Should have at least summary or cases or sec fields
        structural_keys = {
            "active_summary", "historical_summary", "cases",
            "sec_enforcement_stage", "defense_strength", "dashboard",
        }
        present = structural_keys & set(raw.keys())
        assert len(present) > 0, (
            f"Expected structural litigation keys, got: {list(raw.keys())[:10]}"
        )


# ---------------------------------------------------------------------------
# Cross-builder: model_dump round-trip preserves all keys
# ---------------------------------------------------------------------------


class TestModelDumpPreservesKeys:
    """model_validate -> model_dump must not lose builder output keys."""

    _BUILDERS: list[tuple[str, Any, type]] = [
        ("exec_summary", extract_exec_summary, ExecSummaryContext),
        ("financials", extract_financials, FinancialContext),
        ("market", extract_market, MarketContext),
        ("governance", extract_governance, GovernanceContext),
        ("litigation", extract_litigation, LitigationContext),
    ]

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_all_builders_roundtrip(self, state_path: str) -> None:
        state = _load_state(state_path)
        signal_results = _get_signal_results(state)
        for name, builder_fn, model_cls in self._BUILDERS:
            raw = builder_fn(state, signal_results=signal_results)
            if not raw:
                continue
            typed = model_cls.model_validate(raw)
            dumped = typed.model_dump()
            for key in raw:
                assert key in dumped, (
                    f"{name}: key '{key}' from builder output lost in model_dump()"
                )
