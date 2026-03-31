"""Tests for narrative cross-validation and DOJ_FCPA filtering (Phase 129-02).

Verifies:
1. narrative_data_sections extracts revenue from XBRL-reconciled path
2. validate_narrative_amounts detects >2x divergence from state values
3. SCA data passed to narratives uses canonical get_active_genuine_scas
4. DOJ_FCPA entries are excluded from narrative SCA data
"""

from __future__ import annotations

import re
from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.benchmark.narrative_data_sections import (
    extract_financial,
    extract_litigation,
)
from do_uw.stages.benchmark.narrative_generator import (
    validate_narrative_amounts,
)


def _mock_state_with_revenue(revenue_value: float) -> MagicMock:
    """Create a mock state with a specific revenue in income statement."""
    state = MagicMock()
    state.ticker = "TEST"
    state.company = MagicMock()
    state.company.identity.legal_name.value = "Test Corp"

    # Income statement with revenue
    item = MagicMock()
    item.label = "Total Revenue"
    item.values = {"FY2024": MagicMock(value=revenue_value)}
    state.extracted.financials.statements.income_statement.line_items = [item]

    # Distress models
    state.extracted.financials.distress.altman_z_score = None
    state.extracted.financials.distress.ohlson_o_score = None
    state.extracted.financials.distress.piotroski_f_score = None
    state.extracted.financials.distress.beneish_m_score = None

    # Other financial fields
    state.extracted.financials.debt_structure = None
    state.extracted.financials.liquidity = None
    state.extracted.financials.leverage = None
    state.extracted.financials.earnings_quality = None
    state.extracted.financials.audit = None

    # Scoring
    state.scoring = None
    state.analysis = None

    return state


def _mock_sca(case_name: str, status: str = "ACTIVE", coverage_type: str | None = None) -> MagicMock:
    """Create a mock SCA entry."""
    sca = MagicMock()
    sca.case_name = MagicMock(value=case_name)
    sca.status = MagicMock(value=status)
    sca.class_period_start = MagicMock(value="2023-01-01")
    sca.class_period_end = MagicMock(value="2024-01-01")
    sca.lead_counsel = None
    sca.lead_counsel_tier = None
    if coverage_type:
        sca.coverage_type = MagicMock(value=coverage_type)
    else:
        sca.coverage_type = None
    return sca


# ---------------------------------------------------------------------------
# Test 1: extract_financial uses XBRL-reconciled revenue path
# ---------------------------------------------------------------------------
class TestFinancialDataExtraction:
    def test_revenue_from_income_statement(self) -> None:
        """extract_financial returns revenue from state income statement line items."""
        state = _mock_state_with_revenue(394_000_000_000.0)
        data = extract_financial(state)
        assert "total_revenue" in data
        assert data["total_revenue"] == pytest.approx(394_000_000_000.0)


# ---------------------------------------------------------------------------
# Test 2: validate_narrative_amounts detects >2x divergence
# ---------------------------------------------------------------------------
class TestNarrativeAmountValidation:
    def test_close_amount_passes(self) -> None:
        """$394B narrative when state revenue is $394B passes validation."""
        known_values = {"total_revenue": 394_000_000_000.0}
        narrative = "Apple reported revenue of $394B in FY2024."
        warnings = validate_narrative_amounts(narrative, known_values)
        assert len(warnings) == 0

    def test_hallucinated_amount_fails(self) -> None:
        """$383B narrative when state revenue is $94B fails validation (>2x)."""
        known_values = {"total_revenue": 94_000_000_000.0}
        narrative = "The company reported revenue of $383B in FY2024."
        warnings = validate_narrative_amounts(narrative, known_values)
        assert len(warnings) > 0
        assert any("383" in w for w in warnings)

    def test_reasonable_divergence_passes(self) -> None:
        """$394B narrative when state revenue is $391B passes (within 2x)."""
        known_values = {"total_revenue": 391_000_000_000.0}
        narrative = "Revenue reached $394B for the fiscal year."
        warnings = validate_narrative_amounts(narrative, known_values)
        assert len(warnings) == 0

    def test_no_amounts_no_warnings(self) -> None:
        """Narrative without dollar amounts produces no warnings."""
        known_values = {"total_revenue": 100_000_000.0}
        narrative = "The company showed strong financial health."
        warnings = validate_narrative_amounts(narrative, known_values)
        assert len(warnings) == 0


# ---------------------------------------------------------------------------
# Test 3: DOJ_FCPA entries excluded from narrative SCA data
# ---------------------------------------------------------------------------
class TestDOJFCPAFiltering:
    def test_litigation_uses_genuine_sca_count(self) -> None:
        """extract_litigation uses canonical SCA counter, not raw list."""
        state = MagicMock()
        state.ticker = "TEST"
        state.company = MagicMock()
        state.company.identity.legal_name.value = "Test Corp"

        # Create genuine SCA + DOJ_FCPA regulatory case
        genuine_sca = _mock_sca("In re Test Corp Securities Litigation")
        doj_fcpa = _mock_sca("DOJ v. Test Corp (FCPA)")
        doj_fcpa.coverage_type = MagicMock(value="REGULATORY_ENTITY")

        state.extracted.litigation.securities_class_actions = [genuine_sca, doj_fcpa]
        state.extracted.litigation.settlement_history = []
        state.extracted.litigation.derivative_suits = []
        state.extracted.litigation.sec_enforcement.highest_confirmed_stage = None
        state.extracted.litigation.sol_map = []
        state.extracted.litigation.total_litigation_reserve = None
        state.extracted.litigation.defense = None
        state.extracted.litigation.industry_patterns = []
        state.benchmark = None
        state.scoring = None

        data = extract_litigation(state)
        # The canonical counter should exclude the DOJ_FCPA case
        assert data["active_sca_count"] <= 1, (
            f"Expected <= 1 genuine SCA but got {data['active_sca_count']} -- "
            "DOJ_FCPA case was not filtered"
        )
