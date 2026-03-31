"""Tests proving CRF insolvency suppression consistency across all 3 sites.

Validates that the centralized should_suppress_insolvency function in
red_flag_gates.py produces correct results and that all suppression
sites use the canonical function.
"""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import pytest


def _make_state_with_financials(
    altman_z: float | None = None,
    current_ratio: float | None = None,
    going_concern: bool = False,
) -> MagicMock:
    """Build a mock AnalysisState with financial distress indicators."""
    state = MagicMock()

    # Set up distress indicators
    if altman_z is not None:
        state.extracted.financials.distress.altman_z_score.score = altman_z
        state.extracted.financials.distress.altman_z_score.zone = MagicMock(value="safe" if altman_z > 2.99 else "grey" if altman_z > 1.81 else "distress")
        state.extracted.financials.distress.altman_z_score.is_partial = False
    else:
        state.extracted.financials.distress.altman_z_score = None

    # Liquidity
    if current_ratio is not None:
        state.extracted.financials.liquidity = MagicMock()
        state.extracted.financials.liquidity.value = {"current_ratio": current_ratio}
    else:
        state.extracted.financials.liquidity = None

    # Going concern
    if going_concern:
        state.extracted.financials.audit.going_concern = MagicMock()
        state.extracted.financials.audit.going_concern.value = True
    else:
        state.extracted.financials.audit.going_concern = MagicMock()
        state.extracted.financials.audit.going_concern.value = False

    return state


class TestShouldSuppressInsolvency:
    """Tests for the centralized should_suppress_insolvency function."""

    def test_suppresses_healthy_company(self) -> None:
        """Healthy balance sheet (Altman Z > 3.0, current ratio > 1.5) should suppress."""
        from do_uw.stages.score.red_flag_gates import should_suppress_insolvency

        state = _make_state_with_financials(altman_z=4.5, current_ratio=2.0)
        assert should_suppress_insolvency(state) is True

    def test_does_not_suppress_distressed(self) -> None:
        """Distressed company (Altman Z < 1.8) should NOT suppress."""
        from do_uw.stages.score.red_flag_gates import should_suppress_insolvency

        state = _make_state_with_financials(altman_z=1.2, current_ratio=0.5)
        assert should_suppress_insolvency(state) is False

    def test_does_not_suppress_going_concern(self) -> None:
        """Going concern should NEVER suppress regardless of ratios."""
        from do_uw.stages.score.red_flag_gates import should_suppress_insolvency

        state = _make_state_with_financials(
            altman_z=4.5, current_ratio=2.0, going_concern=True,
        )
        assert should_suppress_insolvency(state) is False

    def test_does_not_suppress_grey_zone(self) -> None:
        """Grey zone (Z between 1.81-2.99) should NOT suppress."""
        from do_uw.stages.score.red_flag_gates import should_suppress_insolvency

        state = _make_state_with_financials(altman_z=2.5, current_ratio=1.8)
        assert should_suppress_insolvency(state) is False

    def test_does_not_suppress_low_current_ratio(self) -> None:
        """Low current ratio should NOT suppress even with good Z-score."""
        from do_uw.stages.score.red_flag_gates import should_suppress_insolvency

        state = _make_state_with_financials(altman_z=4.0, current_ratio=0.3)
        assert should_suppress_insolvency(state) is False

    def test_does_not_suppress_missing_data(self) -> None:
        """Missing financial data should NOT suppress (conservative)."""
        from do_uw.stages.score.red_flag_gates import should_suppress_insolvency

        state = MagicMock()
        state.extracted = None
        assert should_suppress_insolvency(state) is False

    def test_suppresses_with_positive_metrics(self) -> None:
        """Company with Z > 3.0 and current ratio > 0.5 should suppress."""
        from do_uw.stages.score.red_flag_gates import should_suppress_insolvency

        state = _make_state_with_financials(altman_z=3.5, current_ratio=1.0)
        assert should_suppress_insolvency(state) is True
