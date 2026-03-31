"""Tests for F2 scoring with drop-level decay/decomposition/disclosure modifiers.

Phase 90 Plan 02: Verifies compound drop contribution modifiers:
- Time-decay weighting reduces F2 for old drops
- Company-specific weighting reduces F2 for market-driven drops
- Disclosure uplift increases F2 for disclosure-linked drops
- Compound effect: recent + company-specific + disclosure = maximum impact
- Backward compat: no drop_contributions = no modifier (1.0x)
"""

from __future__ import annotations

import pytest

from do_uw.stages.score.factor_scoring import (
    _apply_drop_contribution_modifier,
)


class TestDropContributionModifier:
    """Test _apply_drop_contribution_modifier."""

    def test_no_contributions_returns_unmodified(self) -> None:
        """No drop_contributions key = no modifier applied."""
        data: dict = {"decline_from_high": 20.0}
        evidence: list[str] = []
        rules: list[str] = []
        sub: dict = {}

        result = _apply_drop_contribution_modifier({}, data, 10.0, evidence, rules, sub)
        assert result == 10.0

    def test_empty_contributions_returns_unmodified(self) -> None:
        """Empty drop_contributions list = no modifier."""
        data: dict = {"drop_contributions": []}
        evidence: list[str] = []
        rules: list[str] = []
        sub: dict = {}

        result = _apply_drop_contribution_modifier({}, data, 10.0, evidence, rules, sub)
        assert result == 10.0

    def test_decay_reduces_score_for_old_drops(self) -> None:
        """A drop with decay_weight=0.5 contributes half."""
        data: dict = {
            "drop_contributions": [
                {
                    "magnitude": 10.0,
                    "decay_weight": 0.5,
                    "company_pct_ratio": 1.0,
                    "has_disclosure": False,
                },
            ],
        }
        evidence: list[str] = []
        rules: list[str] = []
        sub: dict = {}

        result = _apply_drop_contribution_modifier({}, data, 10.0, evidence, rules, sub)
        # modifier = (10*0.5*1.0*1.0) / 10 = 0.5
        assert result == pytest.approx(5.0, abs=0.01)
        assert sub["drop_contribution_modifier"] == pytest.approx(0.5, abs=0.01)

    def test_company_specific_reduces_market_driven(self) -> None:
        """A drop with company_pct=30% (70% market) contributes 30%."""
        data: dict = {
            "drop_contributions": [
                {
                    "magnitude": 10.0,
                    "decay_weight": 1.0,
                    "company_pct_ratio": 0.3,
                    "has_disclosure": False,
                },
            ],
        }
        evidence: list[str] = []
        rules: list[str] = []
        sub: dict = {}

        result = _apply_drop_contribution_modifier({}, data, 10.0, evidence, rules, sub)
        # modifier = (10*1.0*0.3*1.0) / 10 = 0.3
        assert result == pytest.approx(3.0, abs=0.01)

    def test_disclosure_uplift(self) -> None:
        """A drop with corrective disclosure gets 1.5x."""
        data: dict = {
            "drop_contributions": [
                {
                    "magnitude": 10.0,
                    "decay_weight": 1.0,
                    "company_pct_ratio": 1.0,
                    "has_disclosure": True,
                },
            ],
        }
        evidence: list[str] = []
        rules: list[str] = []
        sub: dict = {}

        result = _apply_drop_contribution_modifier({}, data, 10.0, evidence, rules, sub)
        # modifier = (10*1.0*1.0*1.5) / 10 = 1.5
        assert result == pytest.approx(15.0, abs=0.01)

    def test_compound_effect(self) -> None:
        """Recent + company-specific + disclosure = maximum impact."""
        data: dict = {
            "drop_contributions": [
                {
                    "magnitude": 10.0,
                    "decay_weight": 0.9,      # recent
                    "company_pct_ratio": 0.8,  # mostly company-specific
                    "has_disclosure": True,     # corrective disclosure
                },
            ],
        }
        evidence: list[str] = []
        rules: list[str] = []
        sub: dict = {}

        result = _apply_drop_contribution_modifier({}, data, 10.0, evidence, rules, sub)
        # modifier = (10*0.9*0.8*1.5) / 10 = 1.08
        assert result == pytest.approx(10.8, abs=0.01)

    def test_multiple_drops_weighted_average(self) -> None:
        """Multiple drops: weighted sum / raw sum."""
        data: dict = {
            "drop_contributions": [
                {
                    "magnitude": 15.0,
                    "decay_weight": 1.0,
                    "company_pct_ratio": 1.0,
                    "has_disclosure": False,
                },
                {
                    "magnitude": 10.0,
                    "decay_weight": 0.25,
                    "company_pct_ratio": 0.5,
                    "has_disclosure": False,
                },
            ],
        }
        evidence: list[str] = []
        rules: list[str] = []
        sub: dict = {}

        result = _apply_drop_contribution_modifier({}, data, 10.0, evidence, rules, sub)
        # raw_sum = 15 + 10 = 25
        # weighted_sum = 15*1.0*1.0*1.0 + 10*0.25*0.5*1.0 = 15 + 1.25 = 16.25
        # modifier = 16.25 / 25 = 0.65
        assert result == pytest.approx(6.5, abs=0.01)

    def test_zero_magnitude_drops_ignored(self) -> None:
        """Drops with zero magnitude don't affect modifier."""
        data: dict = {
            "drop_contributions": [
                {
                    "magnitude": 0.0,
                    "decay_weight": 1.0,
                    "company_pct_ratio": 1.0,
                    "has_disclosure": False,
                },
            ],
        }
        evidence: list[str] = []
        rules: list[str] = []
        sub: dict = {}

        result = _apply_drop_contribution_modifier({}, data, 10.0, evidence, rules, sub)
        # raw_sum = 0, so early return
        assert result == 10.0

    def test_evidence_and_rules_populated(self) -> None:
        """Modifier != 1.0 adds evidence and triggers rule."""
        data: dict = {
            "drop_contributions": [
                {
                    "magnitude": 10.0,
                    "decay_weight": 0.5,
                    "company_pct_ratio": 1.0,
                    "has_disclosure": False,
                },
            ],
        }
        evidence: list[str] = []
        rules: list[str] = []
        sub: dict = {}

        _apply_drop_contribution_modifier({}, data, 10.0, evidence, rules, sub)
        assert len(evidence) == 1
        assert "Drop contribution modifier" in evidence[0]
        assert "drop_contribution_adjustment" in rules
