"""Tests for blind spot discovery hook and calibration notes rendering.

Tests:
- Relevance scoring for D&O keywords
- Processing blind spot results (mocked fetch/LLM)
- Low-relevance results skipped
- Graceful failure handling
- Discovery summary formatting
- Calibration notes rendering (empty and with data)
- Web search hook integration
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.knowledge.discovery import (
    _score_relevance,
    get_discovery_summary,
    process_blind_spot_discoveries,
)


# ---------------------------------------------------------------------------
# test_score_relevance
# ---------------------------------------------------------------------------


class TestScoreRelevance:
    """Verify keyword scoring returns correct scores for known titles."""

    def test_high_relevance_litigation(self) -> None:
        score = _score_relevance(
            "SEC Investigation Into Fraud at XYZ Corp",
            "The SEC has launched an enforcement action involving fraud",
        )
        # "sec" in title (2) + "investigation" in title (2)
        # + "fraud" in title (2) + "enforcement" in snippet (1)
        assert score >= 5

    def test_high_relevance_short_seller(self) -> None:
        score = _score_relevance(
            "Hindenburg Research Short Seller Report",
            "Activist investor alleges whistleblower evidence of fraud",
        )
        # "short seller" in title (2) + "activist" in snippet (1)
        # + "whistleblower" in snippet (1) + "fraud" in snippet (1)
        assert score >= 4

    def test_low_relevance_general_news(self) -> None:
        score = _score_relevance(
            "Company Q2 Earnings Beat Expectations",
            "Revenue grew 15% year over year driven by strong demand",
        )
        assert score < 5

    def test_zero_score_empty_inputs(self) -> None:
        assert _score_relevance("", "") == 0

    def test_score_capped_at_10(self) -> None:
        # Load every keyword into title
        title = (
            "litigation lawsuit sec enforcement fraud settlement "
            "investigation short seller activist whistleblower"
        )
        score = _score_relevance(title, title)
        assert score == 10

    def test_title_counts_double(self) -> None:
        # Same keyword in title vs snippet should differ
        title_score = _score_relevance("lawsuit filed", "")
        snippet_score = _score_relevance("", "lawsuit filed")
        assert title_score > snippet_score


# ---------------------------------------------------------------------------
# test_process_blind_spot_mock
# ---------------------------------------------------------------------------


class TestProcessBlindSpotMock:
    """Mock fetch/LLM and verify proposals generated for high-relevance."""

    def _make_blind_spot_results(
        self, results: list[dict[str, str]]
    ) -> dict[str, Any]:
        return {
            "pre_structured": {
                "litigation": results,
            },
            "post_structured": {},
        }

    @patch("do_uw.knowledge.ingestion_llm.store_proposals")
    @patch("do_uw.knowledge.ingestion_llm.extract_document_intelligence")
    @patch("do_uw.knowledge.ingestion_llm.fetch_url_content")
    @patch("do_uw.brain.brain_writer.BrainWriter")
    def test_high_relevance_processed(
        self,
        mock_writer_cls: MagicMock,
        mock_fetch: MagicMock,
        mock_extract: MagicMock,
        mock_store: MagicMock,
    ) -> None:
        mock_fetch.return_value = "Document content about SEC fraud"

        mock_result = MagicMock()
        mock_result.event_type = "SEC_INVESTIGATION"
        mock_result.proposed_new_checks = [MagicMock()]
        mock_extract.return_value = mock_result

        mock_store.return_value = 1
        mock_writer_instance = MagicMock()
        mock_writer_cls.return_value = mock_writer_instance

        blind_results = self._make_blind_spot_results([
            {
                "title": "SEC Investigation Fraud Lawsuit",
                "url": "https://example.com/sec-fraud",
                "snippet": "Major SEC enforcement action",
            },
        ])

        discoveries = process_blind_spot_discoveries(blind_results, "AAPL")

        assert len(discoveries) == 1
        assert discoveries[0]["event_type"] == "SEC_INVESTIGATION"
        assert discoveries[0]["proposals_generated"] == 1

    def test_empty_results_returns_empty(self) -> None:
        discoveries = process_blind_spot_discoveries({}, "AAPL")
        assert discoveries == []

    def test_no_pre_post_keys(self) -> None:
        discoveries = process_blind_spot_discoveries(
            {"search_configured": True}, "AAPL"
        )
        assert discoveries == []


# ---------------------------------------------------------------------------
# test_process_blind_spot_low_relevance_skipped
# ---------------------------------------------------------------------------


class TestLowRelevanceSkipped:
    """Verify low-scoring results are skipped entirely."""

    def test_low_relevance_not_processed(self) -> None:
        blind_results: dict[str, Any] = {
            "pre_structured": {
                "industry": [
                    {
                        "title": "Company Launches New Product",
                        "url": "https://example.com/product",
                        "snippet": "Exciting new consumer product line",
                    },
                ],
            },
            "post_structured": {},
        }

        discoveries = process_blind_spot_discoveries(blind_results, "AAPL")
        # No high-relevance results, so no discoveries
        assert discoveries == []


# ---------------------------------------------------------------------------
# test_process_blind_spot_fetch_failure
# ---------------------------------------------------------------------------


class TestFetchFailure:
    """Verify graceful handling when URL fetch fails."""

    @patch("do_uw.knowledge.ingestion_llm.fetch_url_content")
    def test_fetch_failure_returns_entry(
        self, mock_fetch: MagicMock
    ) -> None:
        mock_fetch.side_effect = Exception("Connection refused")

        blind_results: dict[str, Any] = {
            "pre_structured": {
                "litigation": [
                    {
                        "title": "SEC Fraud Investigation Lawsuit",
                        "url": "https://example.com/sec",
                        "snippet": "Major enforcement action filed",
                    },
                ],
            },
            "post_structured": {},
        }

        discoveries = process_blind_spot_discoveries(blind_results, "AAPL")

        assert len(discoveries) == 1
        assert discoveries[0]["event_type"] == "FETCH_FAILED"
        assert discoveries[0]["proposals_generated"] == 0


# ---------------------------------------------------------------------------
# test_discovery_summary_formatting
# ---------------------------------------------------------------------------


class TestDiscoverySummaryFormatting:
    """Verify get_discovery_summary output format."""

    def test_summary_with_discoveries(self) -> None:
        discoveries = [
            {"url": "a.com", "title": "A", "event_type": "SEC", "proposals_generated": 2},
            {"url": "b.com", "title": "B", "event_type": "FRAUD", "proposals_generated": 0},
            {"url": "c.com", "title": "C", "event_type": "LAWSUIT", "proposals_generated": 1},
        ]
        summary = get_discovery_summary(discoveries)
        assert "3 document(s) analyzed" in summary
        assert "3 proposal(s) generated" in summary
        assert "blind spot search" in summary

    def test_empty_discoveries_returns_empty(self) -> None:
        assert get_discovery_summary([]) == ""


# ---------------------------------------------------------------------------
# test_render_calibration_notes_empty
# ---------------------------------------------------------------------------


class TestRenderCalibrationNotesEmpty:
    """Verify empty string returned when no data."""

    @patch("do_uw.brain.brain_schema.get_brain_db_path")
    def test_no_brain_db_returns_empty(
        self, mock_path: MagicMock
    ) -> None:
        from do_uw.models.state import AnalysisState
        from do_uw.stages.render.md_renderer_helpers_calibration import (
            render_calibration_notes,
        )

        # Simulate brain.duckdb not existing
        fake_path = MagicMock(spec=Path)
        fake_path.exists.return_value = False
        mock_path.return_value = fake_path

        state = AnalysisState(ticker="TEST")
        result = render_calibration_notes(state)
        assert result == ""


# ---------------------------------------------------------------------------
# test_render_calibration_notes_with_data
# ---------------------------------------------------------------------------


class TestRenderCalibrationNotesWithData:
    """Mock brain DuckDB and verify section renders with data."""

    @patch("do_uw.brain.brain_schema.connect_brain_db")
    @patch("do_uw.brain.brain_schema.get_brain_db_path")
    def test_renders_with_active_checks(
        self,
        mock_path: MagicMock,
        mock_connect: MagicMock,
    ) -> None:
        from do_uw.models.state import AnalysisState
        from do_uw.stages.render.md_renderer_helpers_calibration import (
            render_calibration_notes,
        )

        fake_path = MagicMock(spec=Path)
        fake_path.exists.return_value = True
        mock_path.return_value = fake_path

        # Build a mock connection that returns different results per query
        mock_conn = MagicMock()
        active_result = MagicMock()
        active_result.fetchone.return_value = (396,)
        incubating_result = MagicMock()
        incubating_result.fetchone.return_value = (3,)
        pending_result = MagicMock()
        pending_result.fetchone.return_value = (2,)
        changes_result = MagicMock()
        changes_result.fetchall.return_value = []
        feedback_result = MagicMock()
        feedback_result.fetchall.return_value = []

        mock_conn.execute.side_effect = [
            active_result,
            incubating_result,
            pending_result,
            changes_result,
            feedback_result,
        ]
        mock_connect.return_value = mock_conn

        state = AnalysisState(ticker="AAPL")
        result = render_calibration_notes(state)

        assert "## Calibration Notes" in result
        assert "Checks active" in result
        assert "396" in result
        assert "Checks incubating" in result
        assert "3" in result

    @patch("do_uw.brain.brain_schema.connect_brain_db")
    @patch("do_uw.brain.brain_schema.get_brain_db_path")
    def test_renders_discovery_findings(
        self,
        mock_path: MagicMock,
        mock_connect: MagicMock,
    ) -> None:
        from do_uw.models.state import AcquiredData, AnalysisState
        from do_uw.stages.render.md_renderer_helpers_calibration import (
            render_calibration_notes,
        )

        fake_path = MagicMock(spec=Path)
        fake_path.exists.return_value = True
        mock_path.return_value = fake_path

        mock_conn = MagicMock()
        active_result = MagicMock()
        active_result.fetchone.return_value = (100,)
        incubating_result = MagicMock()
        incubating_result.fetchone.return_value = (0,)
        pending_result = MagicMock()
        pending_result.fetchone.return_value = (0,)
        changes_result = MagicMock()
        changes_result.fetchall.return_value = []
        feedback_result = MagicMock()
        feedback_result.fetchall.return_value = []

        mock_conn.execute.side_effect = [
            active_result,
            incubating_result,
            pending_result,
            changes_result,
            feedback_result,
        ]
        mock_connect.return_value = mock_conn

        acquired = AcquiredData()
        acquired.blind_spot_results["discovery_findings"] = (
            "2 document(s) analyzed, 1 proposal(s) generated"
        )
        state = AnalysisState(ticker="TSLA", acquired_data=acquired)

        result = render_calibration_notes(state)
        assert "2 document(s) analyzed" in result
        assert "Discovery Findings" in result


# ---------------------------------------------------------------------------
# test_web_search_hook_fires
# ---------------------------------------------------------------------------


class TestWebSearchHookFires:
    """Verify discovery hook is called after blind spot search."""

    @patch("do_uw.knowledge.discovery.process_blind_spot_discoveries")
    @patch("do_uw.knowledge.discovery.get_discovery_summary")
    def test_hook_called_with_results(
        self,
        mock_summary: MagicMock,
        mock_process: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.orchestrator import _run_discovery_hook

        mock_process.return_value = [
            {"url": "x.com", "event_type": "SEC", "proposals_generated": 1}
        ]
        mock_summary.return_value = (
            "1 document(s) analyzed, 1 proposal(s) generated"
        )

        blind_spot_results: dict[str, Any] = {
            "pre_structured": {
                "litigation": [{"title": "test", "url": "x.com"}],
            },
            "post_structured": {},
        }

        _run_discovery_hook(blind_spot_results, "AAPL")

        mock_process.assert_called_once()
        assert blind_spot_results.get("discovery_findings") == (
            "1 document(s) analyzed, 1 proposal(s) generated"
        )

    def test_hook_skips_empty_results(self) -> None:
        from do_uw.stages.acquire.orchestrator import _run_discovery_hook

        blind_spot_results: dict[str, Any] = {
            "search_configured": True,
            "search_budget_used": 0,
        }

        # Should not raise, just return silently
        _run_discovery_hook(blind_spot_results, "AAPL")
        assert "discovery_findings" not in blind_spot_results

    @patch("do_uw.knowledge.discovery.process_blind_spot_discoveries")
    def test_hook_non_blocking_on_failure(
        self, mock_process: MagicMock
    ) -> None:
        from do_uw.stages.acquire.orchestrator import _run_discovery_hook

        mock_process.side_effect = RuntimeError("Discovery crashed")

        blind_spot_results: dict[str, Any] = {
            "pre_structured": {"litigation": [{"title": "test"}]},
        }

        # Should not raise
        _run_discovery_hook(blind_spot_results, "AAPL")
