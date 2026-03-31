"""Tests for render output modules: Markdown, PDF, and meeting prep.

Tests cover:
- Markdown renderer produces valid .md with expected sections
- Markdown renderer handles None/empty state gracefully
- PDF renderer returns None when WeasyPrint unavailable
- Meeting prep question generation from state model
- Meeting prep question priority sorting
- RenderStage produces Word + Markdown files
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.state import AnalysisState

_NOW = datetime.now(tz=UTC)

from do_uw.stages.render.design_system import DesignSystem  # noqa: E402
from do_uw.stages.render.md_renderer import (  # noqa: E402
    build_template_context,
    render_markdown,
)
from do_uw.stages.render.pdf_renderer import render_pdf  # noqa: E402
from do_uw.stages.render.sections.meeting_questions import (  # noqa: E402
    MeetingQuestion,
    generate_clarification_questions,
    generate_forward_indicator_questions,
)
from do_uw.stages.render.sections.meeting_questions_gap import (  # noqa: E402
    generate_credibility_test_questions,
    generate_gap_filler_questions,
)


@pytest.fixture()
def ds() -> DesignSystem:
    """Create a DesignSystem for testing."""
    return DesignSystem()


@pytest.fixture()
def empty_state() -> AnalysisState:
    """Create a minimal AnalysisState with no data."""
    return AnalysisState(ticker="TEST")


@pytest.fixture()
def state_with_low_confidence() -> AnalysisState:
    """Create state with LOW confidence data for clarification questions."""
    from do_uw.models.company import CompanyIdentity, CompanyProfile

    state = AnalysisState(ticker="LOW")
    state.company = CompanyProfile(
        identity=CompanyIdentity(
            ticker="LOW",
            legal_name=SourcedValue(
                value="Low Confidence Corp",
                source="web",
                confidence=Confidence.LOW,
                as_of=_NOW,
            ),
        ),
        market_cap=SourcedValue(
            value=1_000_000_000.0,
            source="web-estimate",
            confidence=Confidence.LOW,
            as_of=_NOW,
        ),
    )
    return state


class TestMarkdownRenderer:
    """Test Markdown output generation."""

    def test_render_markdown_produces_file(
        self, tmp_path: Path, empty_state: AnalysisState, ds: DesignSystem
    ) -> None:
        """render_markdown creates a .md file at the specified path."""
        output = tmp_path / "test_worksheet.md"
        result = render_markdown(empty_state, output, ds)
        assert result == output
        assert output.exists()

    def test_render_markdown_contains_ticker(
        self, tmp_path: Path, empty_state: AnalysisState, ds: DesignSystem
    ) -> None:
        """Markdown output contains the ticker symbol."""
        output = tmp_path / "test.md"
        render_markdown(empty_state, output, ds)
        content = output.read_text(encoding="utf-8")
        assert "TEST" in content

    def test_render_markdown_contains_sections(
        self, tmp_path: Path, empty_state: AnalysisState, ds: DesignSystem
    ) -> None:
        """Markdown output contains all major section headings."""
        output = tmp_path / "test.md"
        render_markdown(empty_state, output, ds)
        content = output.read_text(encoding="utf-8")
        assert "## Section 1: Executive Summary" in content
        assert "## Section 2: Company Profile" in content
        assert "## Section 3: Financial Health" in content
        assert "## Section 4: Market & Trading" in content
        assert "## Section 5: Governance & Leadership" in content
        assert "## Section 6: Litigation & Regulatory" in content
        assert "## Section 7: D&O Risk Scoring" in content
        assert "## Appendix: Meeting Prep Companion" in content

    def test_render_markdown_none_fields_safe(
        self, tmp_path: Path, empty_state: AnalysisState, ds: DesignSystem
    ) -> None:
        """Markdown renders without errors when all state fields are None."""
        output = tmp_path / "test.md"
        render_markdown(empty_state, output, ds)
        content = output.read_text(encoding="utf-8")
        assert "not available" in content.lower()

    def test_build_template_context_empty_state(
        self, empty_state: AnalysisState
    ) -> None:
        """Template context has expected keys even with empty state."""
        ctx = build_template_context(empty_state)
        assert ctx["ticker"] == "TEST"
        assert ctx["company_name"] == "Unknown Company"
        assert ctx["company"] is None
        assert ctx["scoring"] is None
        assert isinstance(ctx["meeting_questions"], list)

    def test_markdown_creates_parent_dirs(
        self, tmp_path: Path, empty_state: AnalysisState, ds: DesignSystem
    ) -> None:
        """Markdown renderer creates parent directories if needed."""
        output = tmp_path / "deep" / "nested" / "test.md"
        render_markdown(empty_state, output, ds)
        assert output.exists()


class TestPdfRenderer:
    """Test PDF output generation."""

    def test_render_pdf_returns_none_without_weasyprint(
        self, tmp_path: Path, empty_state: AnalysisState, ds: DesignSystem
    ) -> None:
        """PDF renderer returns None when WeasyPrint is not installed."""
        # WeasyPrint is not installed in test env, so this should return None
        output = tmp_path / "test.pdf"
        result = render_pdf(empty_state, output, ds)
        assert result is None
        assert not output.exists()

    def test_render_pdf_with_mocked_weasyprint(
        self, tmp_path: Path, empty_state: AnalysisState, ds: DesignSystem
    ) -> None:
        """PDF renderer calls WeasyPrint when available."""
        mock_html_cls = MagicMock()
        mock_html_instance = MagicMock()
        mock_html_cls.return_value = mock_html_instance

        output = tmp_path / "test.pdf"
        with patch.dict(
            "sys.modules",
            {"weasyprint": MagicMock(HTML=mock_html_cls)},
        ):
            result = render_pdf(empty_state, output, ds)

        # The mock was called
        mock_html_cls.assert_called_once()
        mock_html_instance.write_pdf.assert_called_once()
        assert result == output


class TestMeetingPrepQuestions:
    """Test meeting prep question generation."""

    def test_empty_state_no_questions(
        self, empty_state: AnalysisState
    ) -> None:
        """Empty state generates no clarification questions."""
        questions = generate_clarification_questions(empty_state)
        assert questions == []

    def test_low_confidence_generates_clarification(
        self, state_with_low_confidence: AnalysisState
    ) -> None:
        """LOW confidence data generates clarification questions."""
        questions = generate_clarification_questions(
            state_with_low_confidence
        )
        assert len(questions) > 0
        assert all(q.category == "CLARIFICATION" for q in questions)

    def test_forward_indicator_empty_state(
        self, empty_state: AnalysisState
    ) -> None:
        """Empty state generates no forward indicator questions."""
        questions = generate_forward_indicator_questions(empty_state)
        assert questions == []

    def test_gap_filler_no_extracted_gets_litigation_gap(
        self, empty_state: AnalysisState
    ) -> None:
        """No extracted data generates litigation gap question."""
        questions = generate_gap_filler_questions(empty_state)
        # Litigation gap check fires when extracted is None
        assert len(questions) == 1
        assert questions[0].category == "GAP_FILLER"
        assert "litigation" in questions[0].question.lower()

    def test_gap_filler_with_extracted_no_governance(self) -> None:
        """Extracted data with no governance generates gap question."""
        from do_uw.models.state import ExtractedData

        state = AnalysisState(ticker="GAP")
        state.extracted = ExtractedData()
        questions = generate_gap_filler_questions(state)
        gap_cats = [q for q in questions if q.category == "GAP_FILLER"]
        assert len(gap_cats) > 0

    def test_credibility_empty_state(
        self, empty_state: AnalysisState
    ) -> None:
        """Empty state generates no credibility test questions."""
        questions = generate_credibility_test_questions(empty_state)
        assert questions == []

    def test_question_priority_sorting(self) -> None:
        """Questions sort by priority descending."""
        questions = [
            MeetingQuestion(
                question="Low",
                category="CLARIFICATION",
                priority=1.0,
                context="",
                good_answer="",
                bad_answer="",
                follow_up="",
            ),
            MeetingQuestion(
                question="High",
                category="FORWARD_INDICATOR",
                priority=9.0,
                context="",
                good_answer="",
                bad_answer="",
                follow_up="",
            ),
            MeetingQuestion(
                question="Mid",
                category="GAP_FILLER",
                priority=5.0,
                context="",
                good_answer="",
                bad_answer="",
                follow_up="",
            ),
        ]
        questions.sort(key=lambda q: q.priority, reverse=True)
        assert questions[0].question == "High"
        assert questions[1].question == "Mid"
        assert questions[2].question == "Low"

    def test_question_has_all_fields(self) -> None:
        """MeetingQuestion has all required fields."""
        q = MeetingQuestion(
            question="Test?",
            category="CLARIFICATION",
            priority=5.0,
            context="D&O context",
            good_answer="Good",
            bad_answer="Bad",
            follow_up="Follow up",
        )
        assert q.question == "Test?"
        assert q.category == "CLARIFICATION"
        assert q.priority == 5.0
        assert q.context == "D&O context"
        assert q.good_answer == "Good"
        assert q.bad_answer == "Bad"
        assert q.follow_up == "Follow up"

    def test_four_categories_exist(self) -> None:
        """All four question categories are valid."""
        valid = {
            "CLARIFICATION",
            "FORWARD_INDICATOR",
            "GAP_FILLER",
            "CREDIBILITY_TEST",
        }
        for cat in valid:
            q = MeetingQuestion(
                question="Test",
                category=cat,
                priority=1.0,
                context="",
                good_answer="",
                bad_answer="",
                follow_up="",
            )
            assert q.category == cat


class TestRenderStageIntegration:
    """Test RenderStage produces expected output files."""

    @patch("do_uw.stages.render.render_word_document")
    @patch("do_uw.stages.render.render_markdown")
    @patch("do_uw.stages.render.render_html_pdf")
    def test_render_stage_calls_all_renderers(
        self,
        mock_pdf: MagicMock,
        mock_md: MagicMock,
        mock_docx: MagicMock,
        tmp_path: Path,
    ) -> None:
        """RenderStage calls Word, Markdown, and PDF (Playwright) renderers."""
        from do_uw.models.common import StageStatus
        from do_uw.stages.render import RenderStage

        state = AnalysisState(ticker="AAPL")
        state.mark_stage_running("benchmark")
        state.mark_stage_completed("benchmark")

        mock_docx.return_value = tmp_path / "AAPL_worksheet.docx"
        mock_md.return_value = tmp_path / "AAPL_worksheet.md"
        mock_pdf.return_value = None  # Playwright not available

        stage = RenderStage(output_dir=tmp_path)
        stage.run(state)

        mock_docx.assert_called_once()
        mock_md.assert_called_once()
        mock_pdf.assert_called_once()
        assert state.stages["render"].status == StageStatus.COMPLETED

    @patch("do_uw.stages.render.render_word_document")
    @patch("do_uw.stages.render.render_markdown")
    @patch("do_uw.stages.render.render_pdf")
    def test_render_stage_handles_secondary_failure(
        self,
        mock_pdf: MagicMock,
        mock_md: MagicMock,
        mock_docx: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Secondary renderer failure doesn't crash pipeline."""
        from do_uw.models.common import StageStatus
        from do_uw.stages.render import RenderStage

        state = AnalysisState(ticker="FAIL")
        state.mark_stage_running("benchmark")
        state.mark_stage_completed("benchmark")

        mock_docx.return_value = tmp_path / "FAIL_worksheet.docx"
        mock_md.side_effect = RuntimeError("Template error")
        mock_pdf.return_value = None

        stage = RenderStage(output_dir=tmp_path)
        stage.run(state)

        # Pipeline still completes despite Markdown failure
        assert state.stages["render"].status == StageStatus.COMPLETED
