"""Tests for AI risk extraction pipeline (SECT8).

Covers:
- AI disclosure extractor: keyword counting, sentiment, risk factors, YoY trend
- Patent extractor: USPTO API mocking, graceful degradation
- Competitive position extractor: peer comparison, UNKNOWN stance
- Sub-orchestrator: all 3 extractors, failure isolation
- ExtractStage integration: module-namespace mocking
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from do_uw.models.ai_risk import AIDisclosureData
from do_uw.models.state import AcquiredData, AnalysisState

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _state_with_item1a(
    item1a_text: str,
    prior_text: str = "",
) -> AnalysisState:
    """Create state with mock 10-K filing containing Item 1A text."""
    docs: list[dict[str, str]] = [
        {
            "accession": "0001-24-001",
            "filing_date": "2024-06-15",
            "form_type": "10-K",
            # Build full text with Item 1A markers + padding to pass 200-char min
            "full_text": (
                "PART I\n\n"
                "Item 1. Business\n\n"
                "The company operates in technology.\n" + ("x " * 120) + "\n\n"
                "Item 1A. Risk Factors\n\n"
                + item1a_text
                + "\n" + ("y " * 120) + "\n\n"
                "Item 1B. Unresolved Staff Comments\n\n"
                "None.\n"
            ),
        },
    ]
    if prior_text:
        docs.append(
            {
                "accession": "0001-23-001",
                "filing_date": "2023-06-15",
                "form_type": "10-K",
                "full_text": (
                    "PART I\n\n"
                    "Item 1. Business\n\n"
                    "The company operates in technology.\n"
                    + ("x " * 120)
                    + "\n\n"
                    "Item 1A. Risk Factors\n\n"
                    + prior_text
                    + "\n" + ("y " * 120) + "\n\n"
                    "Item 1B. Unresolved Staff Comments\n\n"
                    "None.\n"
                ),
            },
        )
    state = AnalysisState(
        ticker="TEST",
        acquired_data=AcquiredData(filing_documents={"10-K": docs}),
    )
    return state


def _state_with_company_name(name: str) -> AnalysisState:
    """Create state with company identity for patent searches."""
    from do_uw.models.common import Confidence, SourcedValue
    from do_uw.models.company import CompanyIdentity, CompanyProfile

    identity = CompanyIdentity(
        ticker="TEST",
        legal_name=SourcedValue[str](
            value=name,
            source="SEC",
            confidence=Confidence.HIGH,
            as_of=datetime.now(tz=UTC),
        ),
    )
    company = CompanyProfile(identity=identity)
    return AnalysisState(ticker="TEST", company=company)


# ---------------------------------------------------------------------------
# AI disclosure extractor tests
# ---------------------------------------------------------------------------


class TestExtractAIDisclosures:
    """Tests for extract_ai_disclosures."""

    def test_empty_filing_documents(self) -> None:
        """No filing documents -> default disclosure, 0% coverage."""
        from do_uw.stages.extract.ai_disclosure_extract import (
            extract_ai_disclosures,
        )

        state = AnalysisState(ticker="TEST")
        disclosure, report = extract_ai_disclosures(state)

        assert disclosure.mention_count == 0
        assert disclosure.sentiment == "UNKNOWN"
        assert report.coverage_pct == 0.0

    def test_no_ai_keywords(self) -> None:
        """Item 1A with no AI terms -> zero mentions."""
        from do_uw.stages.extract.ai_disclosure_extract import (
            extract_ai_disclosures,
        )

        text = (
            "The company faces general market risks including "
            "economic downturns and supply chain disruptions. "
            "Competition in the industry is significant. " * 5
        )
        state = _state_with_item1a(text)
        disclosure, _report = extract_ai_disclosures(state)

        assert disclosure.mention_count == 0
        assert disclosure.sentiment == "UNKNOWN"

    def test_core_ai_keywords_counted(self) -> None:
        """Core AI terms are counted as mentions."""
        from do_uw.stages.extract.ai_disclosure_extract import (
            extract_ai_disclosures,
        )

        text = (
            "The rapid advancement of artificial intelligence and "
            "machine learning technologies poses significant risks. "
            "Generative AI may disrupt our business model. "
            "Deep learning applications threaten existing revenue streams. "
            "AI-powered competitors challenge our market position. " * 3
        )
        state = _state_with_item1a(text)
        disclosure, _ = extract_ai_disclosures(state)

        assert disclosure.mention_count > 0

    def test_sentiment_threat_classification(self) -> None:
        """Text heavy on threat language near AI -> THREAT sentiment."""
        from do_uw.stages.extract.ai_disclosure_extract import (
            extract_ai_disclosures,
        )

        text = (
            "Artificial intelligence poses a significant risk to our business. "
            "AI technology threatens to disrupt our market. "
            "Machine learning systems may replace traditional approaches. "
            "AI-driven competitors pose challenges that could make our "
            "products obsolete. The threat of AI displacement is real. "
            "Deep learning creates vulnerability in our business model. "
        )
        state = _state_with_item1a(text)
        disclosure, _ = extract_ai_disclosures(state)

        assert disclosure.sentiment == "THREAT"
        assert disclosure.threat_mentions > disclosure.opportunity_mentions

    def test_sentiment_opportunity_classification(self) -> None:
        """Text heavy on opportunity language near AI -> OPPORTUNITY."""
        from do_uw.stages.extract.ai_disclosure_extract import (
            extract_ai_disclosures,
        )

        text = (
            "We see artificial intelligence as a tremendous opportunity. "
            "Machine learning will enhance our products and improve efficiency. "
            "We invest heavily in AI technology to gain competitive advantage. "
            "AI-powered solutions benefit our customers and transform our "
            "operations. We leverage deep learning to adopt new capabilities. "
            "Generative AI adoption enhances our platform significantly. "
        )
        state = _state_with_item1a(text)
        disclosure, _ = extract_ai_disclosures(state)

        assert disclosure.sentiment == "OPPORTUNITY"
        assert disclosure.opportunity_mentions > disclosure.threat_mentions

    def test_sentiment_balanced(self) -> None:
        """Roughly equal threat and opportunity -> BALANCED."""
        from do_uw.stages.extract.ai_disclosure_extract import (
            extract_ai_disclosures,
        )

        text = (
            "Artificial intelligence presents both risks and opportunities. "
            "Machine learning technology could disrupt but also enhance. "
            "AI systems pose a competitive threat but offer benefits. "
            "We invest in AI-enabled solutions to improve performance. "
            "The challenge of AI is matched by the opportunity it provides. "
        )
        state = _state_with_item1a(text)
        disclosure, _ = extract_ai_disclosures(state)

        assert disclosure.sentiment == "BALANCED"

    def test_risk_factors_extracted(self) -> None:
        """AI keyword matches produce context window snippets."""
        from do_uw.stages.extract.ai_disclosure_extract import (
            extract_ai_disclosures,
        )

        text = (
            "Our business is exposed to artificial intelligence disruption. "
            "Machine learning competitors may erode market share. "
            "Deep learning tools could transform how customers interact. "
        ) * 3
        state = _state_with_item1a(text)
        disclosure, _ = extract_ai_disclosures(state)

        assert len(disclosure.risk_factors) > 0
        assert len(disclosure.risk_factors) <= 10

    def test_yoy_trend_increasing(self) -> None:
        """More mentions this year vs last -> INCREASING."""
        from do_uw.stages.extract.ai_disclosure_extract import (
            extract_ai_disclosures,
        )

        current = (
            "Artificial intelligence risk. Machine learning threat. "
            "AI model competition. Deep learning disruption. "
            "Generative AI impact. AI system challenge. "
            "AI technology transformation. Neural network advances. "
        ) * 3
        prior = "Artificial intelligence is a minor concern. "
        state = _state_with_item1a(current, prior_text=prior)
        disclosure, _ = extract_ai_disclosures(state)

        assert disclosure.yoy_trend == "INCREASING"

    def test_yoy_trend_unknown_no_prior(self) -> None:
        """No prior 10-K -> UNKNOWN trend."""
        from do_uw.stages.extract.ai_disclosure_extract import (
            extract_ai_disclosures,
        )

        text = "Artificial intelligence and machine learning are key risks. " * 3
        state = _state_with_item1a(text)
        disclosure, _ = extract_ai_disclosures(state)

        assert disclosure.yoy_trend == "UNKNOWN"


# ---------------------------------------------------------------------------
# Patent extractor tests
# ---------------------------------------------------------------------------


class TestExtractPatentActivity:
    """Tests for extract_patent_activity (pure parser -- no live HTTP calls).

    The USPTO HTTP fetch was moved to ACQUIRE stage (patent_client.py).
    These tests pass raw_results directly to the parser.
    """

    def test_no_raw_results_no_acquired_data(self) -> None:
        """No raw_results and no acquired_data -> default patent data, 0% coverage."""
        from do_uw.stages.extract.ai_patent_extract import (
            extract_patent_activity,
        )

        state = AnalysisState(ticker="TEST")
        patent, report = extract_patent_activity(state, raw_results=[])

        assert patent.ai_patent_count == 0
        assert report.coverage_pct == 0.0

    def test_successful_parse_from_raw_results(self) -> None:
        """Pre-fetched raw_results -> correct patent count and filings."""
        from do_uw.stages.extract.ai_patent_extract import (
            extract_patent_activity,
        )

        raw_results = [
            {
                "patentApplicationNumber": "US20230001",
                "filingDate": "2023-06-15",
                "inventionTitle": "AI-Powered Widget",
            },
            {
                "patentApplicationNumber": "US20240002",
                "filingDate": "2024-01-20",
                "inventionTitle": "Machine Learning System",
            },
        ]
        state = _state_with_company_name("Acme Corp")
        patent, _report = extract_patent_activity(state, raw_results=raw_results)

        assert patent.ai_patent_count == 2
        assert len(patent.recent_filings) == 2

    def test_empty_raw_results(self) -> None:
        """Empty raw_results -> zero patents, UNKNOWN trend."""
        from do_uw.stages.extract.ai_patent_extract import (
            extract_patent_activity,
        )

        state = _state_with_company_name("Unknown Corp")
        patent, _report = extract_patent_activity(state, raw_results=[])

        assert patent.ai_patent_count == 0
        assert patent.filing_trend == "UNKNOWN"

    def test_reads_patent_data_from_acquired_data(self) -> None:
        """When raw_results not passed, reads from state.acquired_data.patent_data."""
        from do_uw.stages.extract.ai_patent_extract import (
            extract_patent_activity,
        )

        raw_results = [
            {
                "patentApplicationNumber": "US20250001",
                "filingDate": "2025-01-10",
                "inventionTitle": "Deep Learning Processor",
            },
        ]
        state = _state_with_company_name("Acme Corp")
        state.acquired_data = AcquiredData(patent_data=raw_results)
        patent, _report = extract_patent_activity(state)

        assert patent.ai_patent_count == 1


# ---------------------------------------------------------------------------
# Competitive position extractor tests
# ---------------------------------------------------------------------------


class TestAssessCompetitivePosition:
    """Tests for assess_competitive_position."""

    def test_no_peer_data_returns_unknown(self) -> None:
        """No peer data available -> UNKNOWN stance."""
        from do_uw.stages.extract.ai_competitive_extract import (
            assess_competitive_position,
        )

        state = AnalysisState(ticker="TEST")
        disclosure = AIDisclosureData(mention_count=10)
        position, report = assess_competitive_position(state, disclosure)

        assert position.adoption_stance == "UNKNOWN"
        assert position.company_ai_mentions == 10
        assert report.coverage_pct == 0.0

    def test_no_extracted_financials_returns_unknown(self) -> None:
        """State with no extracted financials -> UNKNOWN stance."""
        from do_uw.models.state import ExtractedData
        from do_uw.stages.extract.ai_competitive_extract import (
            assess_competitive_position,
        )

        state = AnalysisState(ticker="TEST", extracted=ExtractedData())
        disclosure = AIDisclosureData(mention_count=5)
        position, _report = assess_competitive_position(state, disclosure)

        assert position.adoption_stance == "UNKNOWN"


# ---------------------------------------------------------------------------
# Sub-orchestrator tests
# ---------------------------------------------------------------------------


class TestRunAIRiskExtractors:
    """Tests for run_ai_risk_extractors sub-orchestrator."""

    def test_minimal_state_returns_assessment(self) -> None:
        """Minimal state -> returns AIRiskAssessment with defaults."""
        from do_uw.stages.extract.extract_ai_risk import (
            run_ai_risk_extractors,
        )
        from do_uw.stages.extract.validation import ExtractionReport

        # No acquired_data -> patent_data defaults to empty list (no HTTP call)
        state = AnalysisState(ticker="TEST")
        reports: list[ExtractionReport] = []
        assessment = run_ai_risk_extractors(state, reports)

        assert assessment is not None
        assert assessment.disclosure_data is not None
        assert assessment.patent_activity is not None
        assert assessment.competitive_position is not None
        # Reports should have been appended
        assert len(reports) >= 2  # at least disclosure + patent

    def test_with_item1a_text(self) -> None:
        """State with Item 1A text -> disclosure data populated."""
        from do_uw.stages.extract.extract_ai_risk import (
            run_ai_risk_extractors,
        )
        from do_uw.stages.extract.validation import ExtractionReport

        item1a_text = (
            "Artificial intelligence poses significant risk. "
            "Machine learning threatens our market. "
            "AI-driven disruption. "
        ) * 3
        state = _state_with_item1a(item1a_text)
        reports: list[ExtractionReport] = []
        assessment = run_ai_risk_extractors(state, reports)

        assert assessment.disclosure_data.mention_count > 0
        assert "10-K Item 1A AI disclosures" in assessment.data_sources

    def test_extractor_failure_isolation(self) -> None:
        """One extractor failing doesn't abort the others."""
        from do_uw.stages.extract.extract_ai_risk import (
            run_ai_risk_extractors,
        )
        from do_uw.stages.extract.validation import ExtractionReport

        state = AnalysisState(ticker="TEST")
        reports: list[ExtractionReport] = []

        # Mock the inner extractor to raise inside _run_disclosure wrapper
        with patch(
            "do_uw.stages.extract.ai_disclosure_extract.extract_ai_disclosures",
            side_effect=Exception("Mocked failure"),
        ):
            # Should not crash -- _run_disclosure catches and uses default
            assessment = run_ai_risk_extractors(state, reports)
            assert assessment.disclosure_data.mention_count == 0


# ---------------------------------------------------------------------------
# ExtractStage integration test
# ---------------------------------------------------------------------------


class TestExtractStageAIRiskWiring:
    """Test that ExtractStage wires in run_ai_risk_extractors."""

    def test_extract_stage_calls_ai_risk(self) -> None:
        """ExtractStage.run() calls run_ai_risk_extractors at module namespace."""
        from do_uw.models.ai_risk import AIRiskAssessment
        from do_uw.models.common import Confidence, StageStatus
        from do_uw.stages.extract import ExtractStage

        mock_assessment = AIRiskAssessment()

        state = AnalysisState(ticker="TEST")
        state.stages["acquire"].status = StageStatus.COMPLETED
        state.acquired_data = AcquiredData()

        with (
            patch(
                "do_uw.stages.extract.extract_company_profile",
            ) as mock_profile,
            patch(
                "do_uw.stages.extract.extract_financial_statements",
            ) as mock_stmts,
            patch(
                "do_uw.stages.analyze.financial_models.compute_distress_indicators",
            ) as mock_distress,
            patch(
                "do_uw.stages.analyze.earnings_quality.compute_earnings_quality",
            ) as mock_eq,
            patch(
                "do_uw.stages.extract.extract_debt_analysis",
            ) as mock_debt,
            patch(
                "do_uw.stages.extract.extract_audit_risk",
            ) as mock_audit,
            patch(
                "do_uw.stages.extract.extract_tax_indicators",
            ) as mock_tax,
            patch(
                "do_uw.stages.extract.construct_peer_group",
            ) as mock_peers,
            patch(
                "do_uw.stages.extract.run_market_extractors",
            ) as mock_market,
            patch(
                "do_uw.stages.extract.run_governance_extractors",
            ) as mock_gov,
            patch(
                "do_uw.stages.extract.run_litigation_extractors",
            ) as mock_lit,
            patch(
                "do_uw.stages.extract.run_ai_risk_extractors",
                return_value=mock_assessment,
            ) as mock_ai,
        ):
            # Set up minimal mock returns
            from do_uw.models.company import CompanyIdentity, CompanyProfile
            from do_uw.models.financials import (
                DistressIndicators,
                FinancialStatements,
                PeerGroup,
            )
            from do_uw.models.governance import GovernanceData
            from do_uw.models.litigation import LitigationLandscape
            from do_uw.models.market import MarketSignals
            from do_uw.stages.extract.validation import ExtractionReport

            profile = CompanyProfile(
                identity=CompanyIdentity(ticker="TEST")
            )
            empty_report = ExtractionReport(
                extractor_name="mock",
                expected_fields=[],
                found_fields=[],
                missing_fields=[],
                unexpected_fields=[],
                coverage_pct=100.0,
                confidence=Confidence.HIGH,
                source_filing="mock",
            )
            mock_profile.return_value = (profile, empty_report)
            mock_stmts.return_value = (FinancialStatements(), [empty_report])
            mock_distress.return_value = (DistressIndicators(), [empty_report])
            mock_eq.return_value = (None, empty_report)
            mock_debt.return_value = (None, None, None, None, [empty_report])
            mock_audit.return_value = (MagicMock(), empty_report)
            mock_tax.return_value = (MagicMock(), empty_report)
            mock_peers.return_value = (
                PeerGroup(target_ticker="TEST", peers=[]),
                empty_report,
            )
            mock_market.return_value = MarketSignals()
            mock_gov.return_value = GovernanceData()
            mock_lit.return_value = LitigationLandscape()

            stage = ExtractStage()
            stage.run(state)

            # Verify AI risk extractor was called
            mock_ai.assert_called_once()
            # Verify state.extracted.ai_risk was populated
            assert state.extracted is not None
            assert state.extracted.ai_risk is mock_assessment
