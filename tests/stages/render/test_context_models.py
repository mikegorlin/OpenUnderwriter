"""Tests for typed context models (Phase 138 - TYPE-01 through TYPE-04).

Tests validate that Pydantic models accept real pipeline output,
produce template-compatible dicts, and fall back gracefully on errors.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict

from do_uw.stages.render.context_models import (
    ExecSummaryContext,
    FinancialContext,
    GovernanceContext,
    LitigationContext,
    MarketContext,
    _validate_context,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

STATE_FILES = [
    "output/AAPL/state.json",
    "output/RPM - RPM INTERNATIONAL/2026-03-18/state.json",
    "output/ULS - UL Solutions/2026-03-25/state.json",
]

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _load_state(state_path: str) -> Any:
    """Load AnalysisState from a state.json file."""
    from do_uw.models.state import AnalysisState

    full_path = PROJECT_ROOT / state_path
    if not full_path.exists():
        pytest.skip(f"State file not found: {full_path}")
    with open(full_path) as f:
        return AnalysisState.model_validate_json(f.read())


# ---------------------------------------------------------------------------
# TYPE-02: All fields Optional -- empty dict validates
# ---------------------------------------------------------------------------


class TestEmptyDictValidation:
    """Every model must accept an empty dict (TYPE-02)."""

    def test_exec_summary_empty_dict(self) -> None:
        ctx = ExecSummaryContext.model_validate({})
        assert isinstance(ctx, ExecSummaryContext)

    def test_financial_empty_dict(self) -> None:
        ctx = FinancialContext.model_validate({})
        assert isinstance(ctx, FinancialContext)

    def test_market_empty_dict(self) -> None:
        ctx = MarketContext.model_validate({})
        assert isinstance(ctx, MarketContext)

    def test_governance_empty_dict(self) -> None:
        ctx = GovernanceContext.model_validate({})
        assert isinstance(ctx, GovernanceContext)

    def test_litigation_empty_dict(self) -> None:
        ctx = LitigationContext.model_validate({})
        assert isinstance(ctx, LitigationContext)


# ---------------------------------------------------------------------------
# TYPE-01: Models have extra="allow" (not "forbid")
# ---------------------------------------------------------------------------


class TestExtraAllow:
    """Models must accept unknown keys (extra='allow') during migration."""

    @pytest.mark.parametrize("model_cls", [
        ExecSummaryContext, FinancialContext, MarketContext,
        GovernanceContext, LitigationContext,
    ])
    def test_extra_allow(self, model_cls: type[BaseModel]) -> None:
        ctx = model_cls.model_validate({"__unknown_future_key__": "test_value"})
        dumped = ctx.model_dump()
        assert "__unknown_future_key__" in dumped
        assert dumped["__unknown_future_key__"] == "test_value"


# ---------------------------------------------------------------------------
# TYPE-01: Models have reasonable field counts
# ---------------------------------------------------------------------------


class TestFieldCounts:
    """Each model must have >5 fields to catch accidentally empty models."""

    @pytest.mark.parametrize("model_cls,min_fields", [
        (ExecSummaryContext, 5),
        (FinancialContext, 10),
        (MarketContext, 5),
        (GovernanceContext, 10),
        (LitigationContext, 5),
    ])
    def test_model_has_fields(self, model_cls: type[BaseModel], min_fields: int) -> None:
        fields = model_cls.model_fields
        assert len(fields) >= min_fields, (
            f"{model_cls.__name__} has only {len(fields)} fields, expected >= {min_fields}"
        )


# ---------------------------------------------------------------------------
# TYPE-03: _validate_context fallback behavior
# ---------------------------------------------------------------------------


class TestValidateContext:
    """_validate_context must fall back to raw dict on error."""

    def test_returns_model_dump_on_valid_input(self) -> None:
        raw: dict[str, Any] = {"tier_label": "FAVORABLE", "thesis": "Test thesis"}
        result = _validate_context(ExecSummaryContext, raw, "executive_summary")
        assert isinstance(result, dict)
        assert result["tier_label"] == "FAVORABLE"
        assert result["thesis"] == "Test thesis"

    def test_returns_raw_dict_on_empty(self) -> None:
        raw: dict[str, Any] = {}
        result = _validate_context(ExecSummaryContext, raw, "executive_summary")
        assert result == {}
        assert result is raw  # Same object, not a copy

    def test_returns_raw_dict_on_validation_error(self) -> None:
        """If model has extra='forbid', validation should fail and return raw."""

        class StrictModel(BaseModel):
            model_config = ConfigDict(extra="forbid")
            name: str = ""

        raw: dict[str, Any] = {"name": "test", "unknown_key": "value"}
        result = _validate_context(StrictModel, raw, "test_section")
        # Should return raw dict unchanged because StrictModel forbids extras
        assert result is raw
        assert result["unknown_key"] == "value"


# ---------------------------------------------------------------------------
# TYPE-04: Real state.json round-trip (model_validate -> model_dump -> key preservation)
# ---------------------------------------------------------------------------


class TestRealStateRoundTrip:
    """model_validate on real builder output must succeed, and model_dump
    must preserve all keys from the raw builder output."""

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_exec_summary_real_state(self, state_path: str) -> None:
        from do_uw.stages.render.context_builders.company_exec_summary import extract_exec_summary

        state = _load_state(state_path)
        raw = extract_exec_summary(state)
        if not raw:
            pytest.skip("Builder returned empty dict (no exec summary data)")
        typed = ExecSummaryContext.model_validate(raw)
        dumped = typed.model_dump()
        for key in raw:
            assert key in dumped, f"Key '{key}' lost in model_dump()"

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_financial_real_state(self, state_path: str) -> None:
        from do_uw.stages.render.context_builders.financials import extract_financials

        state = _load_state(state_path)
        raw = extract_financials(state)
        if not raw:
            pytest.skip("Builder returned empty dict (no financial data)")
        typed = FinancialContext.model_validate(raw)
        dumped = typed.model_dump()
        for key in raw:
            assert key in dumped, f"Key '{key}' lost in model_dump()"

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_market_real_state(self, state_path: str) -> None:
        from do_uw.stages.render.context_builders.market import extract_market

        state = _load_state(state_path)
        raw = extract_market(state)
        if not raw:
            pytest.skip("Builder returned empty dict (no market data)")
        typed = MarketContext.model_validate(raw)
        dumped = typed.model_dump()
        for key in raw:
            assert key in dumped, f"Key '{key}' lost in model_dump()"

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_governance_real_state(self, state_path: str) -> None:
        from do_uw.stages.render.context_builders.governance import extract_governance

        state = _load_state(state_path)
        raw = extract_governance(state)
        if not raw:
            pytest.skip("Builder returned empty dict (no governance data)")
        typed = GovernanceContext.model_validate(raw)
        dumped = typed.model_dump()
        for key in raw:
            assert key in dumped, f"Key '{key}' lost in model_dump()"

    @pytest.mark.parametrize("state_path", STATE_FILES)
    def test_litigation_real_state(self, state_path: str) -> None:
        from do_uw.stages.render.context_builders.litigation import extract_litigation

        state = _load_state(state_path)
        raw = extract_litigation(state)
        if not raw:
            pytest.skip("Builder returned empty dict (no litigation data)")
        typed = LitigationContext.model_validate(raw)
        dumped = typed.model_dump()
        for key in raw:
            assert key in dumped, f"Key '{key}' lost in model_dump()"


# ---------------------------------------------------------------------------
# TYPE-05: All 5 builders covered
# ---------------------------------------------------------------------------


class TestAllBuildersCovered:
    """Verify all 5 target builders have corresponding models."""

    def test_all_five_models_exist(self) -> None:
        models = [
            ExecSummaryContext,
            FinancialContext,
            MarketContext,
            GovernanceContext,
            LitigationContext,
        ]
        assert len(models) == 5
        for model in models:
            assert issubclass(model, BaseModel)
            # Verify extra="allow" config
            assert model.model_config.get("extra") == "allow", (
                f"{model.__name__} must have extra='allow'"
            )
