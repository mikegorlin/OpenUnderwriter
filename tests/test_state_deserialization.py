"""Regression tests for state.json deserialization.

Ensures AnalysisState can load real output files with all key fields populated.
Skips gracefully if state files don't exist (they're gitignored).
"""

import json
from pathlib import Path

import pytest

from do_uw.models.state import AnalysisState

AAPL_STATE = Path("output/AAPL/state.json")
TSLA_STATE = Path("output/TSLA/state.json")


@pytest.fixture
def aapl_state():
    if not AAPL_STATE.exists():
        pytest.skip("No AAPL state.json — run pipeline first")
    with open(AAPL_STATE) as f:
        data = json.load(f)
    return AnalysisState.model_validate(data)


@pytest.fixture
def tsla_state():
    if not TSLA_STATE.exists():
        pytest.skip("No TSLA state.json — run pipeline first")
    with open(TSLA_STATE) as f:
        data = json.load(f)
    return AnalysisState.model_validate(data)


class TestAAPLDeserialization:
    def test_aapl_state_loads(self, aapl_state: AnalysisState) -> None:
        assert aapl_state is not None

    def test_aapl_legal_name(self, aapl_state: AnalysisState) -> None:
        assert aapl_state.company.identity.legal_name.value == "Apple Inc."

    def test_aapl_market_cap_populated(self, aapl_state: AnalysisState) -> None:
        assert aapl_state.company.market_cap is not None
        assert aapl_state.company.market_cap.value is not None

    def test_aapl_employee_count_populated(self, aapl_state: AnalysisState) -> None:
        assert aapl_state.company.employee_count is not None
        assert aapl_state.company.employee_count.value is not None

    def test_aapl_financials_populated(self, aapl_state: AnalysisState) -> None:
        assert aapl_state.extracted is not None
        assert aapl_state.extracted.financials is not None


class TestTSLADeserialization:
    def test_tsla_state_loads(self, tsla_state: AnalysisState) -> None:
        assert tsla_state is not None

    def test_tsla_legal_name(self, tsla_state: AnalysisState) -> None:
        assert tsla_state.company.identity.legal_name.value == "Tesla, Inc."

    def test_tsla_company_populated(self, tsla_state: AnalysisState) -> None:
        assert tsla_state.company is not None


class TestScoringIntegrity:
    def test_score_not_perfect_when_data_exists(self, aapl_state: AnalysisState) -> None:
        """A score of 100/100 with real data is suspicious — deductions should apply."""
        if aapl_state.scoring and aapl_state.scoring.composite_score is not None:
            score = aapl_state.scoring.composite_score
            # composite_score may be a float or a SourcedValue
            if hasattr(score, "value"):
                score = score.value
            if score is not None:
                assert score < 100.0, (
                    f"Perfect score {score} suspicious when data exists"
                )
