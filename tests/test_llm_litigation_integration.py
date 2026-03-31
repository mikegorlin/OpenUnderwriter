"""Integration tests for LLM-first litigation extraction.

Tests the LLM-first, regex-fallback strategy in the litigation
sub-orchestrator. Verifies that LLM legal proceedings supplement SCA
cases, contingent liabilities replace regex when available, forum
provisions from DEF14A populate defense, and risk factors are stored.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import (
    CaseDetail,
    LitigationLandscape,
    SECEnforcementPipeline,
)
from do_uw.models.litigation_details import (
    DefenseAssessment,
    WorkforceProductEnvironmental,
)
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.llm.schemas.common import (
    ExtractedContingency,
    ExtractedLegalProceeding,
    ExtractedRiskFactor,
)
from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction
from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction
from do_uw.stages.extract.sourced import sourced_str
from do_uw.stages.extract.validation import ExtractionReport


def _sample_ten_k_dict() -> dict[str, object]:
    """Build a realistic TenKExtraction as a dict for llm_extractions."""
    extraction = TenKExtraction(
        legal_proceedings=[
            ExtractedLegalProceeding(
                case_name="Smith v. TestCorp",
                court="S.D.N.Y.",
                filing_date="2024-03-15",
                allegations="Violations of Section 10(b) and Rule 10b-5",
                status="Pending",
                named_defendants=["TestCorp Inc.", "John Doe"],
                legal_theories=["RULE_10B5"],
            ),
            ExtractedLegalProceeding(
                case_name="DOJ Investigation into TestCorp",
                allegations="Potential FCPA violations",
                status="Under investigation",
            ),
        ],
        contingent_liabilities=[
            ExtractedContingency(
                description="Securities class action settlement reserve",
                classification="PROBABLE",
                accrued_amount=25_000_000.0,
                range_low=20_000_000.0,
                range_high=35_000_000.0,
            ),
            ExtractedContingency(
                description="Environmental remediation costs",
                classification="REASONABLY_POSSIBLE",
                accrued_amount=5_000_000.0,
            ),
        ],
        risk_factors=[
            ExtractedRiskFactor(
                title="Securities Litigation Risk",
                category="LITIGATION",
                severity="HIGH",
                is_new_this_year=True,
                source_passage="We are subject to securities class actions...",
            ),
            ExtractedRiskFactor(
                title="Cybersecurity Breach Risk",
                category="CYBER",
                severity="MEDIUM",
                source_passage="We may experience data breaches...",
            ),
            ExtractedRiskFactor(
                title="Supply Chain Disruption",
                category="OPERATIONAL",
                severity="LOW",
                source_passage="Our supply chain may be disrupted...",
            ),
        ],
    )
    return extraction.model_dump()


def _sample_def14a_dict() -> dict[str, object]:
    """Build a DEF14AExtraction with forum provisions."""
    extraction = DEF14AExtraction(
        exclusive_forum_provision=True,
        forum_selection_clause="Delaware Court of Chancery for state law claims",
    )
    return extraction.model_dump()


def _make_state(
    *,
    with_ten_k: bool = False,
    with_def14a: bool = False,
) -> AnalysisState:
    """Create an AnalysisState with or without LLM extractions."""
    state = AnalysisState(ticker="TEST")
    llm_extractions: dict[str, object] = {}
    if with_ten_k:
        llm_extractions["10-K:0001-24-000001"] = _sample_ten_k_dict()
    if with_def14a:
        llm_extractions["DEF 14A:0001-24-000002"] = _sample_def14a_dict()
    state.acquired_data = AcquiredData(llm_extractions=llm_extractions)
    return state


def _mock_report() -> ExtractionReport:
    """Create a minimal mock ExtractionReport."""
    return ExtractionReport(
        extractor_name="mock",
        expected_fields=["f1"],
        found_fields=["f1"],
        missing_fields=[],
        unexpected_fields=[],
        coverage_pct=100.0,
        confidence=Confidence.HIGH,
        source_filing="mock",
    )


def _mock_all_regex_extractors() -> dict[str, MagicMock]:
    """Create mocks for all regex-based litigation extractors."""
    report = _mock_report()
    return {
        "sca": MagicMock(return_value=([], report)),
        "sec_enforcement": MagicMock(
            return_value=(SECEnforcementPipeline(), report)
        ),
        "derivative": MagicMock(return_value=([], report)),
        "regulatory": MagicMock(return_value=([], report)),
        "deal": MagicMock(return_value=([], report)),
        "workforce": MagicMock(
            return_value=(WorkforceProductEnvironmental(), [], report)
        ),
        "defense": MagicMock(return_value=(DefenseAssessment(), report)),
        "industry": MagicMock(return_value=([], report)),
        "sol": MagicMock(return_value=([], report)),
        "contingent": MagicMock(return_value=([], None, report)),
    }


def _run_with_mocks(
    state: AnalysisState,
    mocks: dict[str, MagicMock],
) -> tuple[LitigationLandscape, list[ExtractionReport]]:
    """Run litigation extractors with all regex extractors mocked."""
    reports: list[ExtractionReport] = []
    with (
        patch(
            "do_uw.stages.extract.sca_extractor.extract_securities_class_actions",
            mocks["sca"],
        ),
        patch(
            "do_uw.stages.extract.sec_enforcement.extract_sec_enforcement",
            mocks["sec_enforcement"],
        ),
        patch(
            "do_uw.stages.extract.derivative_suits.extract_derivative_suits",
            mocks["derivative"],
        ),
        patch(
            "do_uw.stages.extract.regulatory_extract.extract_regulatory_proceedings",
            mocks["regulatory"],
        ),
        patch(
            "do_uw.stages.extract.deal_litigation.extract_deal_litigation",
            mocks["deal"],
        ),
        patch(
            "do_uw.stages.extract.workforce_product.extract_workforce_product_environmental",
            mocks["workforce"],
        ),
        patch(
            "do_uw.stages.analyze.defense_assessment.extract_defense_assessment",
            mocks["defense"],
        ),
        patch(
            "do_uw.stages.analyze.industry_claims.extract_industry_claim_patterns",
            mocks["industry"],
        ),
        patch(
            "do_uw.stages.extract.sol_mapper.compute_sol_map",
            mocks["sol"],
        ),
        patch(
            "do_uw.stages.extract.contingent_liab.extract_contingent_liabilities",
            mocks["contingent"],
        ),
    ):
        from do_uw.stages.extract.extract_litigation import (
            run_litigation_extractors,
        )

        landscape = run_litigation_extractors(state, reports)
    return landscape, reports


class TestLitigationWithLLMLegalProceedings:
    """Tests for LLM legal proceedings supplementing SCA cases."""

    def test_llm_cases_added_to_sca(self) -> None:
        """LLM legal proceedings with securities theories are added to SCA list.

        Non-securities cases (e.g. DOJ/FCPA investigations) are routed
        away from the SCA list by _classify_case_destination.
        """
        state = _make_state(with_ten_k=True)
        mocks = _mock_all_regex_extractors()
        landscape, _reports = _run_with_mocks(state, mocks)

        # Regex returns 0, LLM adds 1 SCA (Smith v. TestCorp has RULE_10B5)
        # DOJ Investigation has no securities theories/keywords → routed to GENERAL
        assert len(landscape.securities_class_actions) == 1
        names = [
            c.case_name.value
            for c in landscape.securities_class_actions
            if c.case_name and c.case_name.value
        ]
        assert "Smith v. TestCorp" in names

    def test_llm_case_has_correct_source(self) -> None:
        """LLM-sourced cases have 10-K (LLM) source attribution.

        Cross-validation may append corroboration notes to the source.
        """
        state = _make_state(with_ten_k=True)
        mocks = _mock_all_regex_extractors()
        landscape, _reports = _run_with_mocks(state, mocks)

        case = landscape.securities_class_actions[0]
        assert case.case_name is not None
        assert case.case_name.source.startswith("10-K (LLM)")


class TestLitigationWithoutLLMData:
    """Tests for regex-fallback litigation extraction path."""

    def test_falls_back_to_regex(self) -> None:
        """All regex extractors called when no LLM data."""
        state = _make_state(with_ten_k=False)
        mocks = _mock_all_regex_extractors()
        _run_with_mocks(state, mocks)

        mocks["sca"].assert_called_once()
        mocks["contingent"].assert_called_once()

    def test_no_risk_factors_stored(self) -> None:
        """No risk factors stored when LLM 10-K absent."""
        state = _make_state(with_ten_k=False)
        mocks = _mock_all_regex_extractors()
        _run_with_mocks(state, mocks)

        # extracted should exist (from _ensure_extracted_litigation)
        # but risk_factors should be empty
        assert state.extracted is not None
        assert len(state.extracted.risk_factors) == 0


class TestLitigationLLMContingencies:
    """Tests for LLM contingent liabilities replacing regex."""

    def test_contingencies_from_llm(self) -> None:
        """When LLM contingencies exist, regex is skipped."""
        state = _make_state(with_ten_k=True)
        mocks = _mock_all_regex_extractors()
        landscape, _reports = _run_with_mocks(state, mocks)

        assert len(landscape.contingent_liabilities) == 2
        descs = [
            cl.description.value
            for cl in landscape.contingent_liabilities
            if cl.description and cl.description.value
        ]
        assert "Securities class action settlement reserve" in descs
        assert "Environmental remediation costs" in descs

        # Regex contingent should NOT be called
        mocks["contingent"].assert_not_called()

    def test_total_reserve_computed(self) -> None:
        """Total litigation reserve includes only litigation-related contingencies."""
        state = _make_state(with_ten_k=True)
        mocks = _mock_all_regex_extractors()
        landscape, _reports = _run_with_mocks(state, mocks)

        assert landscape.total_litigation_reserve is not None
        # 25M only — environmental remediation (5M) correctly excluded as non-litigation
        assert landscape.total_litigation_reserve.value == 25_000_000.0
        assert landscape.total_litigation_reserve.source == "10-K (LLM)"

    def test_contingencies_fallback_when_no_llm(self) -> None:
        """Regex contingent extractor called when LLM absent."""
        state = _make_state(with_ten_k=False)
        mocks = _mock_all_regex_extractors()
        _run_with_mocks(state, mocks)

        mocks["contingent"].assert_called_once()


class TestLitigationLLMForumProvisions:
    """Tests for DEF14A forum provisions in defense assessment."""

    def test_forum_provisions_from_llm(self) -> None:
        """DEF14A forum provisions populate defense assessment."""
        state = _make_state(with_def14a=True)
        mocks = _mock_all_regex_extractors()
        landscape, _reports = _run_with_mocks(state, mocks)

        forum = landscape.defense.forum_provisions
        assert forum.has_exclusive_forum is not None
        assert forum.has_exclusive_forum.value is True
        assert forum.exclusive_forum_details is not None
        assert "Delaware" in forum.exclusive_forum_details.value

    def test_forum_provisions_not_overwritten(self) -> None:
        """LLM forum provisions do not overwrite existing regex data."""
        state = _make_state(with_def14a=True)
        mocks = _mock_all_regex_extractors()

        # Set up defense mock to return existing forum provisions
        existing_defense = DefenseAssessment()
        from do_uw.stages.extract.sourced import now

        existing_defense.forum_provisions.has_exclusive_forum = (
            SourcedValue[bool](
                value=True,
                source="10-K regex",
                confidence=Confidence.MEDIUM,
                as_of=now(),
            )
        )
        report = _mock_report()
        mocks["defense"] = MagicMock(
            return_value=(existing_defense, report)
        )

        landscape, _reports = _run_with_mocks(state, mocks)

        # Should keep the regex-sourced value (not LLM)
        forum = landscape.defense.forum_provisions
        assert forum.has_exclusive_forum is not None
        assert forum.has_exclusive_forum.source == "10-K regex"


class TestLitigationLLMRiskFactors:
    """Tests for risk factors stored on state.extracted."""

    def test_risk_factors_stored(self) -> None:
        """Risk factors from LLM stored on state.extracted.risk_factors."""
        state = _make_state(with_ten_k=True)
        mocks = _mock_all_regex_extractors()
        _run_with_mocks(state, mocks)

        assert state.extracted is not None
        assert len(state.extracted.risk_factors) == 3

        titles = [rf.title for rf in state.extracted.risk_factors]
        assert "Securities Litigation Risk" in titles
        assert "Cybersecurity Breach Risk" in titles
        assert "Supply Chain Disruption" in titles

    def test_risk_factor_do_relevance(self) -> None:
        """Risk factor D&O relevance inferred from category."""
        state = _make_state(with_ten_k=True)
        mocks = _mock_all_regex_extractors()
        _run_with_mocks(state, mocks)

        assert state.extracted is not None
        rf_map = {
            rf.title: rf for rf in state.extracted.risk_factors
        }
        assert rf_map["Securities Litigation Risk"].do_relevance == "HIGH"
        assert rf_map["Cybersecurity Breach Risk"].do_relevance == "MEDIUM"
        assert rf_map["Supply Chain Disruption"].do_relevance == "LOW"


class TestLitigationLLMDedup:
    """Tests for deduplication of LLM and regex cases."""

    def test_duplicate_case_not_added(self) -> None:
        """LLM case with same name as SCA case is not duplicated."""
        state = _make_state(with_ten_k=True)
        mocks = _mock_all_regex_extractors()

        # SCA extractor already returns "Smith v. TestCorp"
        existing_case = CaseDetail(
            case_name=sourced_str(
                "Smith v. TestCorp", "SCAC", Confidence.HIGH
            ),
        )
        report = _mock_report()
        mocks["sca"] = MagicMock(return_value=([existing_case], report))

        landscape, _reports = _run_with_mocks(state, mocks)

        # Smith v. TestCorp from regex exists; LLM duplicate is skipped.
        # DOJ Investigation has no securities theories → routed to GENERAL (not SCA)
        names = [
            c.case_name.value
            for c in landscape.securities_class_actions
            if c.case_name and c.case_name.value
        ]
        assert names.count("Smith v. TestCorp") == 1
        assert len(landscape.securities_class_actions) == 1
