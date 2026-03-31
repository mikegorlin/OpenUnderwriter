"""Integration tests for LLM enrichment in ownership structure extraction.

Tests LLM-first/regex-fallback integration in ownership_structure.py:
- LLM top holders populate when yfinance is empty
- Regex-only fallback when LLM is absent
- Existing insider_pct not overridden by LLM
"""

from __future__ import annotations

from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.sourced import now, sourced_float, sourced_str


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


def _make_state(
    *,
    llm_extractions: dict[str, Any] | None = None,
    institutional_holders: dict[str, Any] | None = None,
    info_overrides: dict[str, Any] | None = None,
) -> AnalysisState:
    """Build a minimal AnalysisState for ownership testing."""
    info: dict[str, Any] = {
        **(info_overrides or {}),
    }
    filings: dict[str, Any] = {
        "info": info,
        "filing_texts": {},
    }
    market_data: dict[str, Any] = {
        "info": info,
    }
    if institutional_holders is not None:
        market_data["institutional_holders"] = institutional_holders

    identity = CompanyIdentity(
        ticker="TEST",
        legal_name=sourced_str("Test Corp", "SEC EDGAR", Confidence.HIGH),
        cik=sourced_str("0001234567", "SEC EDGAR", Confidence.HIGH),
    )
    return AnalysisState(
        ticker="TEST",
        company=CompanyProfile(identity=identity),
        acquired_data=AcquiredData(
            filings=filings,
            market_data=market_data,
            company_facts={},
            llm_extractions=llm_extractions or {},
        ),
    )


def _make_def14a_extraction(
    *,
    top_5_holders: list[str] | None = None,
    officers_directors_ownership_pct: float | None = None,
) -> dict[str, Any]:
    """Build a minimal DEF14AExtraction dict for LLM mocking."""
    return {
        "board_size": None,
        "independent_directors": None,
        "ceo_is_chair": None,
        "lead_independent_director": None,
        "board_diversity_pct": None,
        "directors": [],
        "named_executive_officers": [],
        "ceo_total_comp": None,
        "ceo_salary": None,
        "ceo_bonus": None,
        "ceo_equity_awards": None,
        "ceo_other_comp": None,
        "ceo_pay_ratio": None,
        "say_on_pay_approval_pct": None,
        "has_clawback": None,
        "clawback_type": None,
        "related_party_transactions": [],
        "officers_directors_ownership_pct": officers_directors_ownership_pct,
        "top_5_holders": top_5_holders or [],
        "has_poison_pill": None,
        "classified_board": None,
        "supermajority_vote_required": None,
        "proxy_access": None,
        "annual_meeting_date": None,
    }


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


class TestOwnershipWithLLMTopHolders:
    """LLM top holders populate when yfinance returns nothing."""

    def test_llm_top_holders_fill_empty(self) -> None:
        llm_data = _make_def14a_extraction(
            top_5_holders=[
                "Vanguard Group: 8.2%",
                "BlackRock: 6.5%",
                "State Street: 4.1%",
            ],
        )
        state = _make_state(llm_extractions={"DEF 14A:abc": llm_data})

        from do_uw.stages.extract.ownership_structure import extract_ownership

        ownership, _report = extract_ownership(state)
        assert len(ownership.top_holders) == 3
        names = [sv.value.get("name", "") for sv in ownership.top_holders]
        assert "Vanguard Group" in names
        assert "BlackRock" in names

    def test_llm_insider_pct_fills_empty(self) -> None:
        llm_data = _make_def14a_extraction(
            officers_directors_ownership_pct=21.5,
        )
        state = _make_state(llm_extractions={"DEF 14A:abc": llm_data})

        from do_uw.stages.extract.ownership_structure import extract_ownership

        ownership, _report = extract_ownership(state)
        assert ownership.insider_pct is not None
        assert abs(ownership.insider_pct.value - 21.5) < 0.01
        assert ownership.insider_pct.source == "DEF 14A (LLM)"


class TestOwnershipWithoutLLM:
    """Falls back to yfinance when LLM data is absent."""

    def test_yfinance_holders_used(self) -> None:
        holders = {
            "Holder": ["Vanguard Fund", "Fidelity Fund"],
            "% Out": [0.082, 0.065],
            "Shares": [1000000, 800000],
            "Value": [50000000, 40000000],
        }
        state = _make_state(institutional_holders=holders)

        from do_uw.stages.extract.ownership_structure import extract_ownership

        ownership, _report = extract_ownership(state)
        assert len(ownership.top_holders) == 2
        assert ownership.top_holders[0].source == "yfinance institutional_holders"

    def test_yfinance_insider_pct_used(self) -> None:
        state = _make_state(
            info_overrides={"heldPercentInsiders": 0.05},
        )

        from do_uw.stages.extract.ownership_structure import extract_ownership

        ownership, _report = extract_ownership(state)
        assert ownership.insider_pct is not None
        assert ownership.insider_pct.source == "yfinance info"


class TestOwnershipLLMNoOverrideExisting:
    """Existing yfinance data not overridden by LLM."""

    def test_existing_insider_pct_preserved(self) -> None:
        """If yfinance provides insider_pct, LLM should not override."""
        llm_data = _make_def14a_extraction(
            officers_directors_ownership_pct=50.0,
        )
        state = _make_state(
            llm_extractions={"DEF 14A:abc": llm_data},
            info_overrides={"heldPercentInsiders": 0.05},
        )

        from do_uw.stages.extract.ownership_structure import extract_ownership

        ownership, _report = extract_ownership(state)
        assert ownership.insider_pct is not None
        # yfinance value (5.0%) should win, not LLM (50.0%)
        assert ownership.insider_pct.source == "yfinance info"
        assert abs(ownership.insider_pct.value - 5.0) < 0.1

    def test_existing_top_holders_preserved(self) -> None:
        """If yfinance provides top holders, LLM should not override."""
        llm_data = _make_def14a_extraction(
            top_5_holders=["LLM Holder: 99%"],
        )
        holders = {
            "Holder": ["Vanguard"],
            "% Out": [0.08],
            "Shares": [1000000],
            "Value": [50000000],
        }
        state = _make_state(
            llm_extractions={"DEF 14A:abc": llm_data},
            institutional_holders=holders,
        )

        from do_uw.stages.extract.ownership_structure import extract_ownership

        ownership, _report = extract_ownership(state)
        # yfinance holders should win
        assert len(ownership.top_holders) == 1
        assert ownership.top_holders[0].source == "yfinance institutional_holders"
