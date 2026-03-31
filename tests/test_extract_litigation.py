"""Tests for litigation extraction sub-orchestrator (SECT6).

Tests the run_litigation_extractors orchestrator, summary narrative
generation, timeline event construction, and matter counting.

All individual extractors are mocked at source module level to verify
wiring and failure isolation without triggering real extraction logic.
"""

from __future__ import annotations

from contextlib import ExitStack
from datetime import UTC, date, datetime
from typing import Any
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
from do_uw.models.state import AnalysisState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sourced_str(val: str) -> SourcedValue[str]:
    """Create a test SourcedValue[str]."""
    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_test_state() -> AnalysisState:
    """Build a minimal AnalysisState for sub-orchestrator testing."""
    from do_uw.models.company import CompanyIdentity, CompanyProfile
    from do_uw.models.state import AcquiredData

    identity = CompanyIdentity(
        ticker="TEST",
        cik=_sourced_str("0001234567"),
        sic_code=_sourced_str("7372"),
        sector=_sourced_str("TECH"),
    )
    profile = CompanyProfile(identity=identity)

    acquired = AcquiredData(
        filings={"filing_texts": {"item3": "x" * 250}},
        market_data={},
    )

    state = AnalysisState(
        ticker="TEST",
        company=profile,
        acquired_data=acquired,
    )
    state.mark_stage_running("resolve")
    state.mark_stage_completed("resolve")
    state.mark_stage_running("acquire")
    state.mark_stage_completed("acquire")
    return state


def _mock_case(
    status: str = "ACTIVE",
    name: str = "Test Case",
    filing_date: date | None = None,
    settlement: float | None = None,
) -> CaseDetail:
    """Create a CaseDetail with status and optional fields."""
    case = CaseDetail(
        case_name=_sourced_str(name),
        status=_sourced_str(status),
    )
    if filing_date:
        case.filing_date = SourcedValue[date](
            value=filing_date, source="test",
            confidence=Confidence.HIGH, as_of=datetime.now(tz=UTC),
        )
    if settlement is not None:
        case.settlement_amount = SourcedValue[float](
            value=settlement, source="test",
            confidence=Confidence.HIGH, as_of=datetime.now(tz=UTC),
        )
    return case


# ---------------------------------------------------------------------------
# Sub-orchestrator calls all 10 extractors
# ---------------------------------------------------------------------------


class TestLitigationSubOrchestratorCallsAll:
    """run_litigation_extractors calls all 10 wrapper functions."""

    def test_calls_all_extractors(self) -> None:
        """All 10 extractor wrappers are invoked in order."""
        state = _make_test_state()
        reports: list[Any] = []

        from do_uw.stages.extract.extract_litigation import (
            run_litigation_extractors,
        )

        with ExitStack() as stack:
            mock_sca = stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_sca_extractor",
                return_value=[],
            ))
            mock_sec = stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_sec_enforcement",
                return_value=SECEnforcementPipeline(),
            ))
            mock_deriv = stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_derivative_suits",
                return_value=[],
            ))
            mock_reg = stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_regulatory_proceedings",
                return_value=[],
            ))
            mock_deal = stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_deal_litigation",
                return_value=[],
            ))
            mock_wpe = stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_workforce_product",
                return_value=(WorkforceProductEnvironmental(), []),
            ))
            mock_defense = stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_defense_assessment",
                return_value=DefenseAssessment(),
            ))
            mock_industry = stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_industry_claims",
                return_value=[],
            ))
            mock_sol = stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_sol_mapper",
                return_value=[],
            ))
            mock_contingent = stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_contingent_liabilities",
                return_value=([], None),
            ))
            # Also mock narrative generators
            stack.enter_context(patch(
                "do_uw.stages.extract.litigation_narrative."
                "generate_litigation_summary",
                return_value=MagicMock(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.litigation_narrative."
                "build_timeline_events",
                return_value=[],
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.litigation_narrative."
                "count_active_matters",
                return_value=MagicMock(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.litigation_narrative."
                "count_historical_matters",
                return_value=MagicMock(),
            ))

            result = run_litigation_extractors(state, reports)

        # All 10 extractors called exactly once
        mock_sca.assert_called_once_with(state, reports)
        mock_sec.assert_called_once_with(state, reports)
        mock_deriv.assert_called_once_with(state, reports)
        mock_reg.assert_called_once_with(state, reports)
        mock_deal.assert_called_once_with(state, reports)
        mock_wpe.assert_called_once_with(state, reports)
        mock_defense.assert_called_once_with(state, reports)
        mock_industry.assert_called_once_with(state, reports)
        mock_sol.assert_called_once_with(state, reports)
        mock_contingent.assert_called_once_with(state, reports)

        assert isinstance(result, LitigationLandscape)


# ---------------------------------------------------------------------------
# Failure isolation
# ---------------------------------------------------------------------------


class TestLitigationFailureIsolation:
    """One extractor failing doesn't crash the sub-orchestrator."""

    def test_sca_failure_does_not_crash(self) -> None:
        """SCA extractor failing returns empty list, others proceed."""
        state = _make_test_state()
        reports: list[Any] = []

        from do_uw.stages.extract.extract_litigation import (
            run_litigation_extractors,
        )

        with ExitStack() as stack:
            # SCA raises, all others are mocked successfully
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_sca_extractor",
            ))
            # Make SCA raise inside the wrapper by patching the
            # actual import instead
            stack.enter_context(patch(
                "do_uw.stages.extract.sca_extractor."
                "extract_securities_class_actions",
                side_effect=RuntimeError("SCA failed"),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_sec_enforcement",
                return_value=SECEnforcementPipeline(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_derivative_suits",
                return_value=[],
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_regulatory_proceedings",
                return_value=[],
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_deal_litigation",
                return_value=[],
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_workforce_product",
                return_value=(WorkforceProductEnvironmental(), []),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_defense_assessment",
                return_value=DefenseAssessment(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_industry_claims",
                return_value=[],
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_sol_mapper",
                return_value=[],
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_contingent_liabilities",
                return_value=([], None),
            ))

            result = run_litigation_extractors(state, reports)

        # Should still produce a valid landscape
        assert isinstance(result, LitigationLandscape)
        assert result.litigation_summary is not None


# ---------------------------------------------------------------------------
# Summary narrative
# ---------------------------------------------------------------------------


class TestLitigationSummaryGeneration:
    """Litigation summary is a SourcedValue[str] with LOW confidence."""

    def test_summary_empty_landscape(self) -> None:
        """Empty landscape produces default assessment."""
        from do_uw.stages.extract.litigation_narrative import (
            generate_litigation_summary,
        )

        landscape = LitigationLandscape()
        summary = generate_litigation_summary(landscape)

        assert isinstance(summary.value, str)
        assert summary.confidence == Confidence.LOW
        assert "litigation" in summary.source.lower()
        # Should have at least "No active" sentence
        assert "No active" in summary.value

    def test_summary_with_active_sca(self) -> None:
        """Summary mentions active securities class actions."""
        from do_uw.stages.extract.litigation_narrative import (
            generate_litigation_summary,
        )

        landscape = LitigationLandscape(
            securities_class_actions=[_mock_case("ACTIVE", "SEC v. Corp")],
        )
        summary = generate_litigation_summary(landscape)

        assert "securities class action" in summary.value.lower()
        assert "1" in summary.value

    def test_summary_regulatory_pipeline(self) -> None:
        """Summary includes enforcement pipeline position."""
        from do_uw.stages.extract.litigation_narrative import (
            generate_litigation_summary,
        )

        enforcement = SECEnforcementPipeline(
            highest_confirmed_stage=_sourced_str("WELLS_NOTICE"),
        )
        landscape = LitigationLandscape(sec_enforcement=enforcement)
        summary = generate_litigation_summary(landscape)

        assert "WELLS_NOTICE" in summary.value


# ---------------------------------------------------------------------------
# Timeline events
# ---------------------------------------------------------------------------


class TestTimelineEventConstruction:
    """Timeline events are built from case dates and sorted."""

    def test_timeline_sorted_by_date_descending(self) -> None:
        """Events are sorted most-recent-first."""
        from do_uw.stages.extract.litigation_narrative import (
            build_timeline_events,
        )

        landscape = LitigationLandscape(
            securities_class_actions=[
                _mock_case("ACTIVE", "Old Case", date(2020, 1, 1)),
                _mock_case("ACTIVE", "New Case", date(2024, 6, 15)),
            ],
        )
        events = build_timeline_events(landscape)

        assert len(events) >= 2
        # First event should be the newer one
        assert events[0].event_date == date(2024, 6, 15)
        assert events[1].event_date == date(2020, 1, 1)

    def test_timeline_includes_settlement_events(self) -> None:
        """Settled cases produce both filing and settlement events."""
        from do_uw.stages.extract.litigation_narrative import (
            build_timeline_events,
        )

        landscape = LitigationLandscape(
            securities_class_actions=[
                _mock_case(
                    "SETTLED", "Settled Case",
                    date(2022, 3, 1), settlement=5_000_000,
                ),
            ],
        )
        events = build_timeline_events(landscape)

        types = [
            e.event_type.value for e in events
            if e.event_type
        ]
        assert "case_filing" in types
        assert "settlement" in types

    def test_timeline_enforcement_events(self) -> None:
        """SEC enforcement actions appear in timeline."""
        from do_uw.stages.extract.litigation_narrative import (
            build_timeline_events,
        )

        enforcement = SECEnforcementPipeline(
            actions=[
                SourcedValue[dict[str, str]](
                    value={
                        "date": "2023-05-10",
                        "description": "SEC cease and desist",
                    },
                    source="test",
                    confidence=Confidence.HIGH,
                    as_of=datetime.now(tz=UTC),
                ),
            ],
        )
        landscape = LitigationLandscape(sec_enforcement=enforcement)
        events = build_timeline_events(landscape)

        assert len(events) >= 1
        types = [
            e.event_type.value for e in events
            if e.event_type
        ]
        assert "enforcement_action" in types


# ---------------------------------------------------------------------------
# Matter counting
# ---------------------------------------------------------------------------


class TestMatterCounting:
    """Active and historical matter counts are correct."""

    def test_active_matter_count(self) -> None:
        """Active matters are counted across SCAs and derivatives."""
        from do_uw.stages.extract.litigation_narrative import (
            count_active_matters,
        )

        landscape = LitigationLandscape(
            securities_class_actions=[
                _mock_case("ACTIVE"),
                _mock_case("SETTLED"),
            ],
            derivative_suits=[
                _mock_case("ACTIVE"),
                _mock_case("DISMISSED"),
            ],
        )
        result = count_active_matters(landscape)

        assert result.value == 2
        assert result.confidence == Confidence.MEDIUM

    def test_historical_matter_count(self) -> None:
        """Historical matters count SETTLED and DISMISSED."""
        from do_uw.stages.extract.litigation_narrative import (
            count_historical_matters,
        )

        landscape = LitigationLandscape(
            securities_class_actions=[
                _mock_case("ACTIVE"),
                _mock_case("SETTLED"),
                _mock_case("DISMISSED"),
            ],
        )
        result = count_historical_matters(landscape)

        assert result.value == 2
        assert result.confidence == Confidence.MEDIUM

    def test_zero_matters(self) -> None:
        """Empty landscape returns 0 for both counts."""
        from do_uw.stages.extract.litigation_narrative import (
            count_active_matters,
            count_historical_matters,
        )

        landscape = LitigationLandscape()
        active = count_active_matters(landscape)
        historical = count_historical_matters(landscape)

        assert active.value == 0
        assert historical.value == 0


# ---------------------------------------------------------------------------
# Intermediate state write
# ---------------------------------------------------------------------------


class TestIntermediateStateWrite:
    """Intermediate litigation written to state before SOL mapper."""

    def test_intermediate_state_written_before_sol(self) -> None:
        """State.extracted.litigation is set before SOL mapper runs."""
        state = _make_test_state()
        reports: list[Any] = []

        from do_uw.stages.extract.extract_litigation import (
            run_litigation_extractors,
        )

        captured_state_litigation: list[Any] = []

        def _capture_sol(
            s: AnalysisState, r: list[Any],
        ) -> list[Any]:
            """Capture state.extracted.litigation when SOL runs."""
            if s.extracted and s.extracted.litigation:
                captured_state_litigation.append(s.extracted.litigation)
            return []

        with ExitStack() as stack:
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_sca_extractor", return_value=[],
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_sec_enforcement",
                return_value=SECEnforcementPipeline(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_derivative_suits", return_value=[],
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_regulatory_proceedings", return_value=[],
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_deal_litigation", return_value=[],
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_workforce_product",
                return_value=(WorkforceProductEnvironmental(), []),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_defense_assessment",
                return_value=DefenseAssessment(),
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_industry_claims", return_value=[],
            ))
            # SOL mapper captures state at call time
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_sol_mapper", side_effect=_capture_sol,
            ))
            stack.enter_context(patch(
                "do_uw.stages.extract.extract_litigation."
                "_run_contingent_liabilities",
                return_value=([], None),
            ))

            run_litigation_extractors(state, reports)

        # SOL mapper saw state.extracted.litigation was set
        assert len(captured_state_litigation) == 1
        assert isinstance(captured_state_litigation[0], LitigationLandscape)
