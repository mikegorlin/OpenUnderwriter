"""Integration tests for LLM-first governance extraction.

Tests the LLM-first, regex-fallback strategy in the governance
sub-orchestrator. Verifies that when LLM DEF14A data is available,
it takes priority for board profiles, compensation, and compensation
flags -- and falls back to regex extractors when absent.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from do_uw.models.common import Confidence
from do_uw.models.governance_forensics import (
    CompensationAnalysis,
    GovernanceQualityScore,
    LeadershipStability,
    NarrativeCoherence,
    OwnershipAnalysis,
    SentimentProfile,
)
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.llm.schemas.common import (
    ExtractedCompensation,
    ExtractedDirector,
)
from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction
from do_uw.stages.extract.validation import ExtractionReport


def _sample_def14a_dict() -> dict[str, object]:
    """Build a realistic DEF14AExtraction as a dict for llm_extractions."""
    extraction = DEF14AExtraction(
        directors=[
            ExtractedDirector(
                name="Alice Johnson",
                age=58,
                independent=True,
                tenure_years=6.0,
                committees=["Audit", "Nominating"],
                other_boards=["Acme Corp"],
            ),
            ExtractedDirector(
                name="Bob Smith",
                age=62,
                independent=False,
                tenure_years=12.0,
                committees=["Compensation"],
                other_boards=["Initech", "Globex", "Umbrella Corp"],
            ),
        ],
        board_size=9,
        independent_count=7,
        classified_board=False,
        ceo_chair_combined=True,
        named_executive_officers=[
            ExtractedCompensation(
                name="Bob Smith",
                title="Chairman and CEO",
                salary=1_500_000.0,
                bonus=750_000.0,
                stock_awards=5_000_000.0,
                option_awards=2_000_000.0,
                total_comp=10_600_000.0,
            ),
            ExtractedCompensation(
                name="Diana Prince",
                title="Chief Financial Officer",
                salary=800_000.0,
                total_comp=4_200_000.0,
            ),
        ],
        say_on_pay_approval_pct=92.5,
        ceo_pay_ratio="256:1",
        golden_parachute_total=15_000_000.0,
        officers_directors_ownership_pct=12.5,
    )
    return extraction.model_dump()


def _make_state(with_llm: bool = True) -> AnalysisState:
    """Create an AnalysisState with or without LLM extractions."""
    state = AnalysisState(ticker="TEST")
    llm_extractions: dict[str, object] = {}
    if with_llm:
        llm_extractions["DEF 14A:0001-24-000001"] = _sample_def14a_dict()
    state.acquired_data = AcquiredData(llm_extractions=llm_extractions)
    return state


def _mock_regex_extractors() -> dict[str, MagicMock]:
    """Create mocks for all regex extractors."""
    report = ExtractionReport(
        extractor_name="mock",
        expected_fields=["f1"],
        found_fields=["f1"],
        missing_fields=[],
        unexpected_fields=[],
        coverage_pct=100.0,
        confidence=Confidence.HIGH,
        source_filing="mock",
    )
    return {
        "leadership": MagicMock(return_value=(LeadershipStability(), report)),
        "compensation": MagicMock(
            return_value=(CompensationAnalysis(), report)
        ),
        "board": MagicMock(
            return_value=(
                ([], GovernanceQualityScore()),
                report,
            )
        ),
        "ownership": MagicMock(return_value=(OwnershipAnalysis(), report)),
        "sentiment": MagicMock(return_value=(SentimentProfile(), report)),
        "coherence": MagicMock(return_value=(NarrativeCoherence(), report)),
    }


def _run_with_mocks(
    state: AnalysisState,
    mocks: dict[str, MagicMock],
) -> tuple[object, list[ExtractionReport]]:
    """Run governance extractors with all regex extractors mocked."""
    reports: list[ExtractionReport] = []
    with (
        patch(
            "do_uw.stages.extract.leadership_profiles.extract_leadership_profiles",
            mocks["leadership"],
        ),
        patch(
            "do_uw.stages.extract.compensation_analysis.extract_compensation",
            mocks["compensation"],
        ),
        patch(
            "do_uw.stages.extract.board_governance.extract_board_governance",
            mocks["board"],
        ),
        patch(
            "do_uw.stages.extract.ownership_structure.extract_ownership",
            mocks["ownership"],
        ),
        patch(
            "do_uw.stages.analyze.sentiment_analysis.extract_sentiment",
            mocks["sentiment"],
        ),
        patch(
            "do_uw.stages.analyze.narrative_coherence.assess_narrative_coherence",
            mocks["coherence"],
        ),
    ):
        from do_uw.stages.extract.extract_governance import (
            run_governance_extractors,
        )

        gov = run_governance_extractors(state, reports)
    return gov, reports


class TestGovernanceWithLLMData:
    """Tests for LLM-first governance extraction path."""

    def test_board_forensics_from_llm(self) -> None:
        """Board forensic profiles populated from LLM directors."""
        state = _make_state(with_llm=True)
        mocks = _mock_regex_extractors()
        gov, _reports = _run_with_mocks(state, mocks)

        from do_uw.models.governance import GovernanceData

        assert isinstance(gov, GovernanceData)
        assert len(gov.board_forensics) == 2
        names = [p.name.value for p in gov.board_forensics if p.name]
        assert "Alice Johnson" in names
        assert "Bob Smith" in names

    def test_compensation_from_llm(self) -> None:
        """Compensation analysis comes from LLM, not regex extractor."""
        state = _make_state(with_llm=True)
        mocks = _mock_regex_extractors()
        gov, _reports = _run_with_mocks(state, mocks)

        from do_uw.models.governance import GovernanceData

        assert isinstance(gov, GovernanceData)
        # CEO salary should be from LLM
        assert gov.comp_analysis.ceo_salary is not None
        assert gov.comp_analysis.ceo_salary.value == 1_500_000.0
        assert gov.comp_analysis.ceo_salary.source == "DEF 14A (LLM)"

        # Regex compensation should NOT be called
        mocks["compensation"].assert_not_called()

    def test_compensation_flags_from_llm(self) -> None:
        """Compensation flags populated from LLM data."""
        state = _make_state(with_llm=True)
        mocks = _mock_regex_extractors()
        gov, _reports = _run_with_mocks(state, mocks)

        from do_uw.models.governance import GovernanceData

        assert isinstance(gov, GovernanceData)
        assert gov.compensation.say_on_pay_support_pct is not None
        assert gov.compensation.say_on_pay_support_pct.value == 92.5
        assert gov.compensation.golden_parachute_value is not None
        assert gov.compensation.golden_parachute_value.value == 15_000_000.0

    def test_board_governance_regex_not_called(self) -> None:
        """Board governance regex extractor not called when LLM has directors."""
        state = _make_state(with_llm=True)
        mocks = _mock_regex_extractors()
        _run_with_mocks(state, mocks)

        mocks["board"].assert_not_called()

    def test_extraction_reports_show_llm_source(self) -> None:
        """ExtractionReports reflect LLM source for LLM-populated extractors."""
        state = _make_state(with_llm=True)
        mocks = _mock_regex_extractors()
        _gov, reports = _run_with_mocks(state, mocks)

        llm_reports = [r for r in reports if r.source_filing == "DEF 14A (LLM)"]
        assert len(llm_reports) >= 2  # compensation + board at minimum
        names = {r.extractor_name for r in llm_reports}
        assert "compensation_analysis" in names
        assert "board_governance" in names

    def test_board_profile_populated(self) -> None:
        """BoardProfile (aggregate) populated from LLM."""
        state = _make_state(with_llm=True)
        mocks = _mock_regex_extractors()
        gov, _reports = _run_with_mocks(state, mocks)

        from do_uw.models.governance import GovernanceData

        assert isinstance(gov, GovernanceData)
        assert gov.board.size is not None
        assert gov.board.size.value == 9
        assert gov.board.independence_ratio is not None

    def test_ownership_supplemented_from_llm(self) -> None:
        """Ownership insider_pct supplemented from LLM proxy data."""
        state = _make_state(with_llm=True)
        mocks = _mock_regex_extractors()
        gov, _reports = _run_with_mocks(state, mocks)

        from do_uw.models.governance import GovernanceData

        assert isinstance(gov, GovernanceData)
        # The regex ownership returns empty, so LLM should fill insider_pct
        assert gov.ownership.insider_pct is not None
        assert gov.ownership.insider_pct.value == 12.5


class TestGovernanceWithoutLLMData:
    """Tests for regex-fallback governance extraction path."""

    def test_falls_back_to_regex(self) -> None:
        """All regex extractors called when no LLM data."""
        state = _make_state(with_llm=False)
        mocks = _mock_regex_extractors()
        _run_with_mocks(state, mocks)

        mocks["compensation"].assert_called_once()
        mocks["board"].assert_called_once()

    def test_compensation_from_regex(self) -> None:
        """Compensation comes from regex when LLM absent."""
        state = _make_state(with_llm=False)
        mocks = _mock_regex_extractors()
        gov, _reports = _run_with_mocks(state, mocks)

        from do_uw.models.governance import GovernanceData

        assert isinstance(gov, GovernanceData)
        # Should be empty default from mock
        assert gov.comp_analysis.ceo_salary is None

    def test_no_llm_extraction_reports(self) -> None:
        """No LLM-source reports when LLM data is absent."""
        state = _make_state(with_llm=False)
        mocks = _mock_regex_extractors()
        _gov, reports = _run_with_mocks(state, mocks)

        llm_reports = [r for r in reports if r.source_filing == "DEF 14A (LLM)"]
        assert len(llm_reports) == 0


class TestGovernanceLLMSupplementsLeadership:
    """Tests for LLM NEO supplementation of leadership profiles."""

    def test_new_neos_added(self) -> None:
        """LLM NEOs not in regex results are added."""
        state = _make_state(with_llm=True)
        mocks = _mock_regex_extractors()
        gov, _reports = _run_with_mocks(state, mocks)

        from do_uw.models.governance import GovernanceData

        assert isinstance(gov, GovernanceData)
        # Regex returns empty leadership, so both LLM NEOs should be added
        exec_names = [
            e.name.value
            for e in gov.leadership.executives
            if e.name and e.name.value
        ]
        assert "Bob Smith" in exec_names
        assert "Diana Prince" in exec_names

    def test_duplicate_neos_not_added(self) -> None:
        """LLM NEOs already found by regex are not duplicated."""
        from do_uw.models.governance_forensics import LeadershipForensicProfile
        from do_uw.stages.extract.sourced import sourced_str

        state = _make_state(with_llm=True)
        mocks = _mock_regex_extractors()

        # Add "Bob Smith" to the regex leadership result
        stability = LeadershipStability()
        existing = LeadershipForensicProfile(
            name=sourced_str("Bob Smith", "8-K", Confidence.HIGH),
        )
        stability.executives.append(existing)

        report = ExtractionReport(
            extractor_name="mock",
            expected_fields=["f1"],
            found_fields=["f1"],
            missing_fields=[],
            unexpected_fields=[],
            coverage_pct=100.0,
            confidence=Confidence.HIGH,
            source_filing="mock",
        )
        mocks["leadership"] = MagicMock(return_value=(stability, report))

        gov, _reports = _run_with_mocks(state, mocks)

        from do_uw.models.governance import GovernanceData

        assert isinstance(gov, GovernanceData)
        # Bob Smith should appear once (from regex), Diana Prince added by LLM
        bob_count = sum(
            1
            for e in gov.leadership.executives
            if e.name and e.name.value and e.name.value.lower() == "bob smith"
        )
        assert bob_count == 1
        diana_count = sum(
            1
            for e in gov.leadership.executives
            if e.name
            and e.name.value
            and e.name.value.lower() == "diana prince"
        )
        assert diana_count == 1
