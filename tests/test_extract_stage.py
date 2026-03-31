"""Integration tests for the ExtractStage orchestrator.

Tests the full extract stage end-to-end with mocked acquired data,
verifying all extractors are called, state is populated correctly,
and the validation summary is produced.

Phase 4 adds sub-orchestrator tests for market (SECT4) and governance
(SECT5) extraction pipelines.  Phase 5 adds litigation (SECT6).
"""

from __future__ import annotations

import logging
from contextlib import ExitStack
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.common import Confidence, SourcedValue, StageStatus
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.governance import GovernanceData
from do_uw.models.litigation import LitigationLandscape
from do_uw.models.market import MarketSignals
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract import ExtractStage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sourced_str(val: str) -> SourcedValue[str]:
    """Create a test SourcedValue[str]."""
    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_entry(
    val: float | str,
    end: str,
    fy: int = 2024,
    fp: str = "FY",
    form: str = "10-K",
    filed: str = "2025-02-15",
    accn: str = "0001234-24-001",
) -> dict[str, Any]:
    """Build a single XBRL fact entry."""
    return {
        "val": val, "end": end, "fy": fy, "fp": fp,
        "form": form, "filed": filed, "accn": accn,
    }


def _make_company_facts() -> dict[str, Any]:
    """Build Company Facts with data across all statements.

    Provides enough concepts for income statement, balance sheet,
    and cash flow extraction at > 50% coverage (avoids edgartools
    fallback trigger).
    """
    gaap: dict[str, Any] = {}

    def _add(concept: str, unit: str, entries: list[dict[str, Any]]) -> None:
        gaap[concept] = {"units": {unit: entries}}

    # Income statement concepts
    _add("Revenues", "USD", [
        _make_entry(100_000_000, "2024-12-31", 2024),
        _make_entry(80_000_000, "2023-12-31", 2023),
    ])
    _add("NetIncomeLoss", "USD", [
        _make_entry(20_000_000, "2024-12-31", 2024),
        _make_entry(15_000_000, "2023-12-31", 2023),
    ])
    _add("CostOfRevenue", "USD", [
        _make_entry(50_000_000, "2024-12-31", 2024),
        _make_entry(40_000_000, "2023-12-31", 2023),
    ])
    _add("OperatingIncomeLoss", "USD", [
        _make_entry(30_000_000, "2024-12-31", 2024),
        _make_entry(25_000_000, "2023-12-31", 2023),
    ])
    _add("EarningsPerShareBasic", "USD/shares", [
        _make_entry(2.50, "2024-12-31", 2024),
        _make_entry(1.80, "2023-12-31", 2023),
    ])

    # Balance sheet concepts
    _add("Assets", "USD", [
        _make_entry(500_000_000, "2024-12-31", 2024),
        _make_entry(450_000_000, "2023-12-31", 2023),
    ])
    _add("AssetsCurrent", "USD", [
        _make_entry(150_000_000, "2024-12-31", 2024),
        _make_entry(130_000_000, "2023-12-31", 2023),
    ])
    _add("Liabilities", "USD", [
        _make_entry(200_000_000, "2024-12-31", 2024),
        _make_entry(180_000_000, "2023-12-31", 2023),
    ])
    _add("LiabilitiesCurrent", "USD", [
        _make_entry(80_000_000, "2024-12-31", 2024),
        _make_entry(70_000_000, "2023-12-31", 2023),
    ])
    _add("StockholdersEquity", "USD", [
        _make_entry(300_000_000, "2024-12-31", 2024),
        _make_entry(270_000_000, "2023-12-31", 2023),
    ])
    _add("LongTermDebt", "USD", [
        _make_entry(120_000_000, "2024-12-31", 2024),
        _make_entry(110_000_000, "2023-12-31", 2023),
    ])

    # Cash flow concepts
    _add("NetCashProvidedByUsedInOperatingActivities", "USD", [
        _make_entry(40_000_000, "2024-12-31", 2024),
        _make_entry(35_000_000, "2023-12-31", 2023),
    ])
    _add("PaymentsToAcquirePropertyPlantAndEquipment", "USD", [
        _make_entry(10_000_000, "2024-12-31", 2024),
        _make_entry(8_000_000, "2023-12-31", 2023),
    ])

    # DEI concepts (for filer category, etc.)
    dei: dict[str, Any] = {}
    dei["EntityFilerCategory"] = {"units": {"": [
        _make_entry("Large Accelerated Filer", "2024-12-31", 2024),
    ]}}

    # Tax concepts
    _add("IncomeTaxExpenseBenefit", "USD", [
        _make_entry(5_000_000, "2024-12-31", 2024),
        _make_entry(4_000_000, "2023-12-31", 2023),
    ])
    _pretax = (
        "IncomeLossFromContinuingOperations"
        "BeforeIncomeTaxesExtraordinaryItems"
        "NoncontrollingInterest"
    )
    _add(_pretax, "USD", [
        _make_entry(25_000_000, "2024-12-31", 2024),
        _make_entry(19_000_000, "2023-12-31", 2023),
    ])
    _add("InterestExpense", "USD", [
        _make_entry(6_000_000, "2024-12-31", 2024),
        _make_entry(5_000_000, "2023-12-31", 2023),
    ])

    return {
        "cik": 1234567,
        "entityName": "Test Corp",
        "facts": {"us-gaap": gaap, "dei": dei},
    }


def _make_filing_texts() -> dict[str, str]:
    """Build synthetic 10-K section texts."""
    return {
        "item1": (
            "Test Corp is a leading technology company providing "
            "cloud-based enterprise software solutions to businesses "
            "worldwide. The company operates in the Software as a "
            "Service (SaaS) market."
        ),
        "item7": (
            "Revenue increased 25% year-over-year to $100M. "
            "Operating margins improved by 200 basis points. "
            "Major customer Acme Corp accounts for 15% of revenue."
        ),
        "item8": (
            "Report of Independent Registered Public Accounting Firm\n"
            "We, Deloitte & Touche LLP, have audited the financial "
            "statements of Test Corp. In our opinion, the financial "
            "statements present fairly, in all material respects, "
            "the financial position of Test Corp.\n"
            "The company maintained effective internal control over "
            "financial reporting as of December 31, 2024."
        ),
    }


def _mock_yfinance_info(symbol: str) -> dict[str, Any]:
    """Build mock yfinance info dict for a peer candidate."""
    caps: dict[str, float] = {
        "TEST": 25_000_000_000,
        "PEER0": 20_000_000_000,
        "PEER1": 30_000_000_000,
        "PEER2": 22_000_000_000,
        "PEER3": 28_000_000_000,
        "PEER4": 18_000_000_000,
        "PEER5": 35_000_000_000,
    }
    return {
        "marketCap": caps.get(symbol, 25_000_000_000),
        "totalRevenue": 100_000_000,
        "longBusinessSummary": f"{symbol} provides cloud software.",
        "industry": "Software - Application",
        "exchange": "NMS",
        "fullTimeEmployees": 15000,
        "sector": "Technology",
        "shortName": f"{symbol} Inc.",
    }


def _make_full_test_state() -> AnalysisState:
    """Build a complete AnalysisState for end-to-end extract testing.

    Includes resolved company profile, completed acquire stage,
    and comprehensive acquired_data with XBRL, filing texts, and
    market data.
    """
    identity = CompanyIdentity(
        ticker="TEST",
        cik=_sourced_str("0001234567"),
        sic_code=_sourced_str("7372"),
        sector=_sourced_str("TECH"),
    )
    profile = CompanyProfile(identity=identity)

    facts = _make_company_facts()
    texts = _make_filing_texts()

    filings: dict[str, Any] = {
        "company_facts": facts,
        "filing_texts": texts,
        "10-K": [{"accessionNumber": "0001234-24-001", "filingDate": "2025-02-15"}],
    }

    market_data: dict[str, Any] = {
        "info": _mock_yfinance_info("TEST"),
    }

    acquired = AcquiredData(
        filings=filings,
        market_data=market_data,
    )

    state = AnalysisState(
        ticker="TEST",
        company=profile,
        acquired_data=acquired,
    )

    # Mark resolve and acquire as completed
    state.mark_stage_running("resolve")
    state.mark_stage_completed("resolve")
    state.mark_stage_running("acquire")
    state.mark_stage_completed("acquire")

    return state


def _peer_candidates() -> list[dict[str, str]]:
    """Return mock peer candidate list from financedatabase."""
    return [
        {"symbol": f"PEER{i}", "name": f"Peer {i}",
         "sector": "Technology", "industry": "Software"}
        for i in range(6)
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExtractStagePopulatesCompanyProfile:
    """ExtractStage enriches company profile from acquired data."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance"
    )
    def test_extract_stage_populates_company_profile(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
    ) -> None:
        """After running, state.company has enriched fields."""
        mock_fetch.return_value = _peer_candidates()
        mock_enrich.side_effect = _mock_yfinance_info

        state = _make_full_test_state()
        stage = ExtractStage()
        stage.run(state)

        assert state.company is not None
        # Identity enrichment happened
        assert state.company.identity.ticker == "TEST"
        # Business description should be populated
        assert state.company.business_description is not None


class TestExtractStagePopulatesFinancials:
    """ExtractStage populates state.extracted.financials."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance"
    )
    def test_extract_stage_populates_financials(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
    ) -> None:
        """state.extracted.financials has statements, distress, audit."""
        mock_fetch.return_value = _peer_candidates()
        mock_enrich.side_effect = _mock_yfinance_info

        state = _make_full_test_state()
        stage = ExtractStage()
        stage.run(state)

        assert state.extracted is not None
        assert state.extracted.financials is not None
        fin = state.extracted.financials

        # Statements
        assert fin.statements is not None
        assert fin.statements.income_statement is not None

        # Distress indicators
        assert fin.distress is not None

        # Audit profile
        assert fin.audit is not None
        assert fin.audit.auditor_name is not None
        assert fin.audit.auditor_name.value == "Deloitte"


class TestExtractStageValidationSummary:
    """Validation summary logs extraction coverage."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance"
    )
    def test_extract_stage_validation_summary(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Validation summary logs extraction coverage."""
        mock_fetch.return_value = _peer_candidates()
        mock_enrich.side_effect = _mock_yfinance_info

        state = _make_full_test_state()
        stage = ExtractStage()
        with caplog.at_level(logging.INFO, logger="do_uw.stages.extract"):
            stage.run(state)

        # Check that validation summary was logged
        summary_msgs = [
            r.message for r in caplog.records
            if "Extract stage:" in r.message
        ]
        assert len(summary_msgs) >= 1
        assert "extractors" in summary_msgs[0]
        assert "coverage" in summary_msgs[0]


class TestExtractStageMarksComplete:
    """Stage status is COMPLETED after successful run."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance"
    )
    def test_extract_stage_marks_complete(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
    ) -> None:
        """Stage status is COMPLETED after successful run."""
        mock_fetch.return_value = _peer_candidates()
        mock_enrich.side_effect = _mock_yfinance_info

        state = _make_full_test_state()
        stage = ExtractStage()
        stage.run(state)

        result = state.stages["extract"]
        assert result.status == StageStatus.COMPLETED
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0


class TestExtractStageFailsWithoutAcquire:
    """Running without completed acquire raises ValueError."""

    def test_extract_stage_fails_without_acquire(self) -> None:
        """Running without completed acquire -> ValueError."""
        state = AnalysisState(ticker="TEST")
        stage = ExtractStage()

        with pytest.raises(ValueError, match="Acquire stage must be completed"):
            stage.validate_input(state)

    def test_extract_stage_fails_without_acquired_data(self) -> None:
        """Completed acquire but no acquired_data -> ValueError."""
        state = AnalysisState(ticker="TEST")
        state.mark_stage_running("acquire")
        state.mark_stage_completed("acquire")
        # acquired_data is still None
        stage = ExtractStage()

        with pytest.raises(ValueError, match="No acquired data"):
            stage.validate_input(state)


class TestExtractStagePeersOverride:
    """Passing override_peers includes those tickers."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance"
    )
    def test_extract_stage_peers_override(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
    ) -> None:
        """Passing override_peers includes those tickers in peer group."""
        mock_fetch.return_value = _peer_candidates()
        mock_enrich.side_effect = _mock_yfinance_info

        state = _make_full_test_state()
        override = ["AAPL", "MSFT", "GOOG"]
        stage = ExtractStage(peers=override)
        stage.run(state)

        assert state.extracted is not None
        assert state.extracted.financials is not None
        peer_group = state.extracted.financials.peer_group
        assert peer_group is not None

        # Override peers should appear in the peer group
        peer_tickers = [p.ticker for p in peer_group.peers]
        for ticker in override:
            assert ticker in peer_tickers


class TestExtractStageFinancialNarrative:
    """Financial health narrative is generated."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance"
    )
    def test_extract_stage_financial_narrative(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
    ) -> None:
        """Financial health narrative is generated and stored."""
        mock_fetch.return_value = _peer_candidates()
        mock_enrich.side_effect = _mock_yfinance_info

        state = _make_full_test_state()
        stage = ExtractStage()
        stage.run(state)

        assert state.extracted is not None
        assert state.extracted.financials is not None
        narrative = state.extracted.financials.financial_health_narrative
        assert narrative is not None
        assert isinstance(narrative.value, str)
        assert len(narrative.value) > 20
        assert narrative.confidence == Confidence.LOW
        assert "Derived" in narrative.source


class TestExtractStageNoImputation:
    """No fabricated data in output (spot check key fields)."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance"
    )
    def test_extract_stage_no_imputation(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
    ) -> None:
        """No fabricated data -- values trace to source."""
        mock_fetch.return_value = _peer_candidates()
        mock_enrich.side_effect = _mock_yfinance_info

        state = _make_full_test_state()
        stage = ExtractStage()
        stage.run(state)

        assert state.extracted is not None
        fin = state.extracted.financials
        assert fin is not None

        # Check that financial statement values have valid sources
        inc = fin.statements.income_statement
        if inc is not None:
            for item in inc.line_items:
                for _period, sv in item.values.items():
                    if sv is not None:
                        assert sv.source != ""
                        assert sv.confidence in (
                            Confidence.HIGH,
                            Confidence.MEDIUM,
                            Confidence.LOW,
                        )

        # Narrative has LOW confidence (derived)
        if fin.financial_health_narrative is not None:
            assert fin.financial_health_narrative.confidence == Confidence.LOW

        # Audit profile values have source attribution
        if fin.audit.auditor_name is not None:
            assert fin.audit.auditor_name.source != ""


class TestExtractStageMarksFailed:
    """Stage marks FAILED on exception."""

    def test_extract_stage_marks_failed_on_error(self) -> None:
        """Stage marks FAILED when an extractor raises."""
        state = _make_full_test_state()
        # Remove acquired_data.filings to cause an error in extraction
        state.acquired_data = AcquiredData(filings={}, market_data={})

        stage = ExtractStage()
        # The extract stage should still run (acquired_data exists),
        # but individual extractors may fail or produce empty results.
        # Let's force an error by patching company profile to raise.
        with patch(
            "do_uw.stages.extract.extract_company_profile",
            side_effect=RuntimeError("Test error"),
        ):
            with pytest.raises(RuntimeError, match="Test error"):
                stage.run(state)

        result = state.stages["extract"]
        assert result.status == StageStatus.FAILED
        assert result.error is not None
        assert "Test error" in result.error


# ---------------------------------------------------------------------------
# Phase 4: Sub-orchestrator tests
# ---------------------------------------------------------------------------


class TestExtractStageCallsMarketSubOrchestrator:
    """ExtractStage calls run_market_extractors with correct args."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch("do_uw.stages.extract.run_market_extractors")
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance"
    )
    def test_extract_stage_calls_market_sub_orchestrator(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
        mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
    ) -> None:
        """run_market_extractors is called with state and reports list."""
        mock_fetch.return_value = _peer_candidates()
        mock_enrich.side_effect = _mock_yfinance_info
        mock_market.return_value = MarketSignals()

        state = _make_full_test_state()
        stage = ExtractStage()
        stage.run(state)

        mock_market.assert_called_once()
        args = mock_market.call_args
        # First arg is state, second is reports list
        assert args[0][0] is state
        assert isinstance(args[0][1], list)

        # Market signals stored on state
        assert state.extracted is not None
        assert state.extracted.market is not None


class TestExtractStageCallsGovernanceSubOrchestrator:
    """ExtractStage calls run_governance_extractors with correct args."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch("do_uw.stages.extract.run_governance_extractors")
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance"
    )
    def test_extract_stage_calls_governance_sub_orchestrator(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
        _mock_market: MagicMock,
        mock_gov: MagicMock,
        _mock_lit: MagicMock,
    ) -> None:
        """run_governance_extractors is called with state and reports list."""
        mock_fetch.return_value = _peer_candidates()
        mock_enrich.side_effect = _mock_yfinance_info
        mock_gov.return_value = GovernanceData()

        state = _make_full_test_state()
        stage = ExtractStage()
        stage.run(state)

        mock_gov.assert_called_once()
        args = mock_gov.call_args
        # First arg is state, second is reports list
        assert args[0][0] is state
        assert isinstance(args[0][1], list)

        # Governance data stored on state
        assert state.extracted is not None
        assert state.extracted.governance is not None


class TestExtractStageHandlesSubOrchestratorFailure:
    """Sub-orchestrator failure propagates as stage failure."""

    def test_market_sub_orchestrator_failure_fails_stage(self) -> None:
        """Market sub-orchestrator exception marks stage FAILED."""
        state = _make_full_test_state()
        stage = ExtractStage()

        with ExitStack() as stack:
            stack.enter_context(patch(
                "do_uw.stages.extract.peer_group."
                "_fetch_candidates_financedatabase",
                return_value=_peer_candidates(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.peer_group."
                "_enrich_candidate_yfinance",
                side_effect=_mock_yfinance_info,
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.run_market_extractors",
                side_effect=RuntimeError("Market extraction failed"),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.run_governance_extractors",
                return_value=GovernanceData(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.run_litigation_extractors",
                return_value=LitigationLandscape(),
            ))

            with pytest.raises(RuntimeError, match="Market extraction failed"):
                stage.run(state)

        result = state.stages["extract"]
        assert result.status == StageStatus.FAILED
        assert result.error is not None
        assert "Market extraction failed" in result.error

    def test_governance_sub_orchestrator_failure_fails_stage(self) -> None:
        """Governance sub-orchestrator exception marks stage FAILED."""
        state = _make_full_test_state()
        stage = ExtractStage()

        with ExitStack() as stack:
            stack.enter_context(patch(
                "do_uw.stages.extract.peer_group."
                "_fetch_candidates_financedatabase",
                return_value=_peer_candidates(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.peer_group."
                "_enrich_candidate_yfinance",
                side_effect=_mock_yfinance_info,
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.run_market_extractors",
                return_value=MarketSignals(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.run_governance_extractors",
                side_effect=RuntimeError("Governance extraction failed"),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.run_litigation_extractors",
                return_value=LitigationLandscape(),
            ))

            with pytest.raises(
                RuntimeError, match="Governance extraction failed"
            ):
                stage.run(state)

        result = state.stages["extract"]
        assert result.status == StageStatus.FAILED
        assert "Governance extraction failed" in (result.error or "")


class TestMarketSubOrchestratorCallsAllExtractors:
    """run_market_extractors calls all 7 extractor wrappers in order."""

    def test_market_sub_orchestrator_calls_all_extractors(self) -> None:
        """All 7 market extractors are attempted in dependency order."""
        state = _make_full_test_state()
        reports: list[Any] = []

        from do_uw.stages.extract.extract_market import (
            run_market_extractors,
        )

        with ExitStack() as stack:
            mock_stock = stack.enter_context(patch(
                "do_uw.stages.extract.extract_market."
                "_run_stock_performance",
            ))
            mock_stock.return_value = (
                MagicMock(),  # StockPerformance
                MagicMock(),  # StockDropAnalysis
            )
            mock_insider = stack.enter_context(patch(
                "do_uw.stages.extract.extract_market."
                "_run_insider_trading",
                return_value=MagicMock(),
            ))
            mock_short = stack.enter_context(patch(
                "do_uw.stages.extract.extract_market."
                "_run_short_interest",
                return_value=MagicMock(),
            ))
            mock_earnings = stack.enter_context(patch(
                "do_uw.stages.extract.extract_market."
                "_run_earnings_guidance",
                return_value=MagicMock(),
            ))
            mock_analyst = stack.enter_context(patch(
                "do_uw.stages.extract.extract_market."
                "_run_analyst_sentiment",
                return_value=MagicMock(),
            ))
            mock_capital = stack.enter_context(patch(
                "do_uw.stages.extract.extract_market."
                "_run_capital_markets",
                return_value=MagicMock(),
            ))
            mock_adverse = stack.enter_context(patch(
                "do_uw.stages.extract.extract_market."
                "_run_adverse_events",
                return_value=MagicMock(),
            ))

            result = run_market_extractors(state, reports)

        # All extractors called exactly once
        mock_stock.assert_called_once_with(state, reports)
        mock_insider.assert_called_once_with(state, reports)
        mock_short.assert_called_once_with(state, reports)
        mock_earnings.assert_called_once_with(state, reports)
        mock_analyst.assert_called_once_with(state, reports)
        mock_capital.assert_called_once_with(state, reports)
        mock_adverse.assert_called_once_with(state, reports)

        # Result is a MarketSignals instance
        assert isinstance(result, MarketSignals)


class TestGovernanceSubOrchestratorCallsAllExtractors:
    """run_governance_extractors calls all 6 extractor wrappers."""

    def test_governance_sub_orchestrator_calls_all_extractors(
        self,
    ) -> None:
        """All 6 governance extractors are attempted in dependency order."""
        state = _make_full_test_state()
        reports: list[Any] = []

        from do_uw.stages.extract.extract_governance import (
            run_governance_extractors,
        )

        with ExitStack() as stack:
            mock_leadership = stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_leadership",
                return_value=MagicMock(),
            ))
            mock_comp = stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_compensation",
                return_value=MagicMock(),
            ))
            mock_board = stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_board_governance",
            ))
            mock_board.return_value = ([], MagicMock())
            mock_ownership = stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_ownership",
                return_value=MagicMock(),
            ))
            mock_sentiment = stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_sentiment",
                return_value=MagicMock(),
            ))
            mock_coherence = stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_narrative_coherence",
                return_value=MagicMock(),
            ))
            # Also mock the summary generator to avoid reading mock fields
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "generate_governance_summary",
                return_value=MagicMock(),
            ))

            result = run_governance_extractors(state, reports)

        # All extractors called exactly once
        mock_leadership.assert_called_once_with(state, reports)
        mock_comp.assert_called_once_with(state, reports)
        # Board governance receives comp_analysis as 3rd arg
        mock_board.assert_called_once()
        mock_ownership.assert_called_once_with(state, reports)
        mock_sentiment.assert_called_once_with(state, reports)
        mock_coherence.assert_called_once_with(state, reports)

        # Result is a GovernanceData instance
        assert isinstance(result, GovernanceData)


class TestGovernanceNarrativeGenerated:
    """Governance summary is generated after all extractors run."""

    def test_governance_narrative_generated(self) -> None:
        """Governance summary is a SourcedValue[str] with LOW confidence."""
        state = _make_full_test_state()
        reports: list[Any] = []

        from do_uw.stages.extract.extract_governance import (
            run_governance_extractors,
        )

        # Mock all individual extractors to avoid real execution
        with ExitStack() as stack:
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_leadership",
                return_value=MagicMock(
                    red_flags=[], departures_18mo=[],
                    avg_tenure_years=None,
                ),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_compensation",
                return_value=MagicMock(
                    say_on_pay_pct=None,
                    related_party_transactions=[],
                    ceo_pay_ratio=None,
                ),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_board_governance",
                return_value=([], MagicMock(total_score=None)),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_ownership",
                return_value=MagicMock(
                    activist_risk_assessment=None,
                    has_dual_class=None,
                    known_activists=[],
                ),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_sentiment",
                return_value=MagicMock(
                    management_tone_trajectory=None,
                    qa_evasion_score=None,
                ),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_governance."
                "_run_narrative_coherence",
                return_value=MagicMock(overall_assessment=None),
            ))

            result = run_governance_extractors(state, reports)

        # Governance summary is generated
        assert result.governance_summary is not None
        assert isinstance(result.governance_summary.value, str)
        assert result.governance_summary.confidence == Confidence.LOW
        assert "governance" in result.governance_summary.source.lower()


# ---------------------------------------------------------------------------
# Phase 5: Litigation sub-orchestrator tests
# ---------------------------------------------------------------------------


class TestExtractStageCallsLitigationSubOrchestrator:
    """ExtractStage calls run_litigation_extractors with correct args."""

    @patch("do_uw.stages.extract.run_litigation_extractors")
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance"
    )
    def test_extract_stage_calls_litigation_sub_orchestrator(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        mock_lit: MagicMock,
    ) -> None:
        """run_litigation_extractors is called with state and reports list."""
        mock_fetch.return_value = _peer_candidates()
        mock_enrich.side_effect = _mock_yfinance_info
        mock_lit.return_value = LitigationLandscape()

        state = _make_full_test_state()
        stage = ExtractStage()
        stage.run(state)

        mock_lit.assert_called_once()
        args = mock_lit.call_args
        # First arg is state, second is reports list
        assert args[0][0] is state
        assert isinstance(args[0][1], list)

        # Litigation landscape stored on state
        assert state.extracted is not None
        assert state.extracted.litigation is not None


class TestExtractStageHandlesLitigationSubOrchestratorFailure:
    """Litigation sub-orchestrator failure propagates as stage failure."""

    def test_litigation_sub_orchestrator_failure_fails_stage(self) -> None:
        """Litigation sub-orchestrator exception marks stage FAILED."""
        state = _make_full_test_state()
        stage = ExtractStage()

        with ExitStack() as stack:
            stack.enter_context(patch(
                "do_uw.stages.extract.peer_group."
                "_fetch_candidates_financedatabase",
                return_value=_peer_candidates(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.peer_group."
                "_enrich_candidate_yfinance",
                side_effect=_mock_yfinance_info,
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.run_market_extractors",
                return_value=MarketSignals(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.run_governance_extractors",
                return_value=GovernanceData(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.run_litigation_extractors",
                side_effect=RuntimeError("Litigation extraction failed"),
            ))

            with pytest.raises(
                RuntimeError, match="Litigation extraction failed"
            ):
                stage.run(state)

        result = state.stages["extract"]
        assert result.status == StageStatus.FAILED
        assert "Litigation extraction failed" in (result.error or "")
