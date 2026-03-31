"""Tests for BIZ.OPS.* operational complexity signals (Phase 99).

Tests cover YAML validation, signal mapper routing, composite score
computation, context builder output, and template rendering.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml


# ---------------------------------------------------------------------------
# YAML validation
# ---------------------------------------------------------------------------


class TestOpsYamlValidation:
    """Validate BIZ.OPS signals in operations.yaml."""

    def test_all_signals_validate(self) -> None:
        """All 4 BIZ.OPS signals should validate with BrainSignalEntry."""
        from do_uw.brain.brain_signal_schema import BrainSignalEntry

        with open("src/do_uw/brain/signals/biz/operations.yaml") as f:
            sigs = yaml.safe_load(f)

        assert len(sigs) == 4
        for sig in sigs:
            BrainSignalEntry.model_validate(sig)

    def test_complexity_score_signal_exists(self) -> None:
        """BIZ.OPS.complexity_score signal should exist."""
        with open("src/do_uw/brain/signals/biz/operations.yaml") as f:
            sigs = yaml.safe_load(f)

        ids = [s["id"] for s in sigs]
        assert "BIZ.OPS.complexity_score" in ids

    def test_complexity_score_group(self) -> None:
        """BIZ.OPS.complexity_score should be in operational_complexity group."""
        with open("src/do_uw/brain/signals/biz/operations.yaml") as f:
            sigs = yaml.safe_load(f)

        composite = [s for s in sigs if s["id"] == "BIZ.OPS.complexity_score"][0]
        assert composite["group"] == "operational_complexity"
        assert composite["signal_class"] == "evaluative"
        assert composite["field_path"] == "ops_complexity_score"


# ---------------------------------------------------------------------------
# Composite score computation
# ---------------------------------------------------------------------------


class TestCompositeScoreComputation:
    """Test the composite score formula."""

    def test_zero_score_no_data(self) -> None:
        """Score should be 0 when no operational data present."""
        from do_uw.brain.field_registry_functions import COMPUTED_FUNCTIONS

        fn = COMPUTED_FUNCTIONS["compute_ops_complexity_score"]
        result = fn(None, None, None)
        assert result == 0

    def test_jurisdiction_contribution(self) -> None:
        """Jurisdictions should contribute 1pt per 5, max 5."""
        from do_uw.brain.field_registry_functions import COMPUTED_FUNCTIONS

        fn = COMPUTED_FUNCTIONS["compute_ops_complexity_score"]
        sub = {"jurisdiction_count": 25, "high_reg_count": 0}
        result = fn(sub, None, None)
        assert result == 5  # 25 // 5 = 5, capped at 5

    def test_high_reg_contribution(self) -> None:
        """High-reg jurisdictions should contribute 1pt per 2, max 3."""
        from do_uw.brain.field_registry_functions import COMPUTED_FUNCTIONS

        fn = COMPUTED_FUNCTIONS["compute_ops_complexity_score"]
        sub = {"jurisdiction_count": 0, "high_reg_count": 6}
        result = fn(sub, None, None)
        assert result == 3  # 6 // 2 = 3, capped at 3

    def test_international_pct_contribution(self) -> None:
        """International workforce % should contribute 1pt per 20%, max 3."""
        from do_uw.brain.field_registry_functions import COMPUTED_FUNCTIONS

        fn = COMPUTED_FUNCTIONS["compute_ops_complexity_score"]
        wf = {"international_pct": 60, "unionized_pct": 0}
        result = fn(None, wf, None)
        assert result == 3  # 60 // 20 = 3, capped at 3

    def test_unionization_flag(self) -> None:
        """Unionization > 20% should add 2pts."""
        from do_uw.brain.field_registry_functions import COMPUTED_FUNCTIONS

        fn = COMPUTED_FUNCTIONS["compute_ops_complexity_score"]
        wf = {"international_pct": 0, "unionized_pct": 25}
        result = fn(None, wf, None)
        assert result == 2

    def test_combined_high_score(self) -> None:
        """Combined data should produce expected composite."""
        from do_uw.brain.field_registry_functions import COMPUTED_FUNCTIONS

        fn = COMPUTED_FUNCTIONS["compute_ops_complexity_score"]
        sub = {"jurisdiction_count": 25, "high_reg_count": 6}
        wf = {"international_pct": 60, "unionized_pct": 25}
        result = fn(sub, wf, None)
        # 5 (jurisdictions) + 3 (high_reg) + 3 (intl_pct) + 2 (union) = 13
        assert result == 13


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------


class TestContextBuilder:
    """Test _build_operational_complexity context builder."""

    def _make_state(
        self,
        sub: dict[str, Any] | None = None,
        wf: dict[str, Any] | None = None,
        res: dict[str, Any] | None = None,
    ) -> Any:
        """Create a mock AnalysisState with operational data."""
        state = MagicMock()
        state.company = MagicMock()
        state.company.revenue_segments = []
        state.extracted = MagicMock()
        state.extracted.text_signals = {}
        state.extracted.governance = None

        if sub is not None:
            sv = MagicMock()
            sv.value = sub
            state.company.subsidiary_structure = sv
        else:
            state.company.subsidiary_structure = None

        if wf is not None:
            sv = MagicMock()
            sv.value = wf
            state.company.workforce_distribution = sv
        else:
            state.company.workforce_distribution = None

        if res is not None:
            sv = MagicMock()
            sv.value = res
            state.company.operational_resilience = sv
        else:
            state.company.operational_resilience = None

        return state

    def test_no_data_returns_empty(self) -> None:
        """Should return empty dict when no operational data."""
        from do_uw.stages.render.context_builders.company import (
            _build_operational_complexity,
        )

        state = self._make_state()
        result, has_data = _build_operational_complexity(state)
        assert has_data is False
        assert result == {}

    def test_returns_expected_keys(self) -> None:
        """Should return all expected context keys."""
        from do_uw.stages.render.context_builders.company import (
            _build_operational_complexity,
        )

        state = self._make_state(
            sub={"jurisdiction_count": 10, "high_reg_count": 3},
            wf={"total_employees": 5000, "international_pct": 30, "unionized_pct": 0},
            res={"geographic_concentration_score": 50, "supply_chain_depth": "moderate", "overall_assessment": "ADEQUATE"},
        )
        result, has_data = _build_operational_complexity(state)
        assert has_data is True
        expected_keys = {
            "composite_score", "composite_level", "composite_color",
            "jurisdiction_count", "high_reg_count",
            "total_employees", "international_pct", "unionized_pct",
            "geographic_concentration_score", "supply_chain_depth",
            "overall_assessment", "segment_count", "indicators",
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_score_to_level_high(self) -> None:
        """Score >= 15 should map to HIGH / red."""
        from do_uw.stages.render.context_builders.company import (
            _build_operational_complexity,
        )

        state = self._make_state(
            sub={"jurisdiction_count": 30, "high_reg_count": 8},
            wf={"total_employees": 50000, "international_pct": 60, "unionized_pct": 25},
            res={"geographic_concentration_score": 80, "supply_chain_depth": "shallow", "overall_assessment": "WEAK"},
        )
        # Add VIE presence to push score above 15
        # Score: 5 (jurisdictions) + 3 (high_reg) + 3 (intl_pct) + 2 (union) + 2 (VIE) = 15
        state.extracted.text_signals = {
            "vie_spe": {"present": True, "mention_count": 2},
        }
        result, _ = _build_operational_complexity(state)
        assert result["composite_level"] == "HIGH"
        assert result["composite_color"] == "red"

    def test_score_to_level_moderate(self) -> None:
        """Score >= 8 but < 15 should map to MODERATE / amber."""
        from do_uw.stages.render.context_builders.company import (
            _build_operational_complexity,
        )

        state = self._make_state(
            sub={"jurisdiction_count": 20, "high_reg_count": 4},
            wf={"total_employees": 10000, "international_pct": 40, "unionized_pct": 0},
            res={"geographic_concentration_score": 50, "supply_chain_depth": "moderate", "overall_assessment": "ADEQUATE"},
        )
        result, _ = _build_operational_complexity(state)
        assert result["composite_level"] == "MODERATE"
        assert result["composite_color"] == "amber"

    def test_score_to_level_low(self) -> None:
        """Score < 8 should map to LOW / green."""
        from do_uw.stages.render.context_builders.company import (
            _build_operational_complexity,
        )

        state = self._make_state(
            sub={"jurisdiction_count": 5, "high_reg_count": 1},
            wf={"total_employees": 1000, "international_pct": 10, "unionized_pct": 0},
            res={"geographic_concentration_score": 20, "supply_chain_depth": "deep", "overall_assessment": "STRONG"},
        )
        result, _ = _build_operational_complexity(state)
        assert result["composite_level"] == "LOW"
        assert result["composite_color"] == "green"

    def test_indicators_present(self) -> None:
        """Should include 4 structural indicators."""
        from do_uw.stages.render.context_builders.company import (
            _build_operational_complexity,
        )

        state = self._make_state(
            sub={"jurisdiction_count": 5, "high_reg_count": 1},
        )
        result, _ = _build_operational_complexity(state)
        assert len(result["indicators"]) == 4
        names = [ind["name"] for ind in result["indicators"]]
        assert "VIE / SPE" in names
        assert "Dual-Class" in names


# ---------------------------------------------------------------------------
# Signal field routing
# ---------------------------------------------------------------------------


class TestFieldRouting:
    """Test BIZ.OPS field routing entries."""

    def test_ops_entries_exist(self) -> None:
        """All 4 BIZ.OPS signals should have field routing entries."""
        from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

        assert FIELD_FOR_CHECK["BIZ.OPS.subsidiary_structure"] == "jurisdiction_count"
        assert FIELD_FOR_CHECK["BIZ.OPS.workforce"] == "international_pct"
        assert FIELD_FOR_CHECK["BIZ.OPS.resilience"] == "geographic_concentration_score"
        assert FIELD_FOR_CHECK["BIZ.OPS.complexity_score"] == "ops_complexity_score"
