"""Tests for LLM-powered document ingestion pipeline.

Tests extract_document_intelligence, fetch_url_content,
generate_impact_report, store_proposals, and the CLI ingest command
with mocked Anthropic calls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.knowledge.ingestion_models import (
    DocumentIngestionResult,
    IngestionImpactReport,
    ProposedCheck,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _sample_result() -> DocumentIngestionResult:
    """Create a realistic DocumentIngestionResult for testing."""
    return DocumentIngestionResult(
        company_ticker="ACME",
        industry_scope="technology",
        event_type="SHORT_SELLER_REPORT",
        event_summary="Hindenburg Research published report alleging ACME inflated revenue",
        do_implications=[
            "Securities class action risk from alleged revenue inflation",
            "Potential SEC investigation into accounting practices",
            "D&O Side A exposure for executive misrepresentation",
        ],
        affected_checks=["FIN.RESTATE.restatement", "FIN.AUDIT.auditor_change", "GOV.COMP.clawback"],
        proposed_new_checks=[
            ProposedCheck(
                signal_id="BIZ.SHORTSELL.report_count",
                name="Short seller report frequency",
                content_type="EVALUATIVE_CHECK",
                threshold_type="count",
                threshold_red=">= 2 reports in 12 months",
                threshold_yellow=">= 1 report in 12 months",
                threshold_clear="No reports in 24 months",
                report_section="company",
                question="Has the company been targeted by short sellers?",
                rationale="Short seller reports often precede SCA filings",
                field_key="short_seller_report_count",
            ),
        ],
        gap_analysis="No existing check covers coordinated short seller campaigns",
        confidence="MEDIUM",
    )


def _sample_proposal() -> ProposedCheck:
    """Create a sample proposed check."""
    return ProposedCheck(
        signal_id="LIT.NEW.emerging_risk",
        name="Emerging litigation risk",
        threshold_type="tiered",
        threshold_red="Multiple lawsuits filed",
        report_section="litigation",
        question="Are there emerging litigation patterns?",
        rationale="Detect early litigation signals",
    )


# ---------------------------------------------------------------------------
# extract_document_intelligence tests
# ---------------------------------------------------------------------------


class TestExtractDocumentIntelligence:
    """Tests for LLM-powered document extraction."""

    def test_returns_result_with_mocked_llm(self) -> None:
        """Mocked LLM returns valid DocumentIngestionResult."""
        sample = _sample_result()

        mock_client = MagicMock()
        mock_client.messages.create.return_value = sample

        mock_anthropic_mod = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = MagicMock()

        mock_instructor_mod = MagicMock()
        mock_instructor_mod.from_anthropic.return_value = mock_client

        with (
            patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}),
            patch.dict(
                "sys.modules",
                {"anthropic": mock_anthropic_mod, "instructor": mock_instructor_mod},
            ),
        ):
            # Re-import to pick up mocked modules
            from do_uw.knowledge.ingestion_llm import extract_document_intelligence

            result = extract_document_intelligence(
                "Test document about ACME fraud",
                "SHORT_SELLER_REPORT",
            )

        assert result.event_type == "SHORT_SELLER_REPORT"
        assert result.company_ticker == "ACME"
        assert len(result.do_implications) == 3
        assert len(result.proposed_new_checks) == 1

    def test_returns_minimal_on_missing_api_key(self) -> None:
        """Returns minimal LOW confidence result without API key."""
        with patch.dict("os.environ", {}, clear=True):
            # Remove ANTHROPIC_API_KEY if set
            import os

            os.environ.pop("ANTHROPIC_API_KEY", None)

            from do_uw.knowledge.ingestion_llm import extract_document_intelligence

            result = extract_document_intelligence("test text", "GENERAL")

        assert result.confidence == "LOW"
        assert result.event_type == "UNKNOWN"

    def test_returns_minimal_on_exception(self) -> None:
        """Returns minimal result on LLM exception."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("API error")

        mock_anthropic_mod = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = MagicMock()

        mock_instructor_mod = MagicMock()
        mock_instructor_mod.from_anthropic.return_value = mock_client

        with (
            patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}),
            patch.dict(
                "sys.modules",
                {"anthropic": mock_anthropic_mod, "instructor": mock_instructor_mod},
            ),
        ):
            from do_uw.knowledge.ingestion_llm import extract_document_intelligence

            result = extract_document_intelligence("test", "GENERAL")

        assert result.confidence == "LOW"
        assert result.event_type == "UNKNOWN"


# ---------------------------------------------------------------------------
# fetch_url_content tests
# ---------------------------------------------------------------------------


class TestFetchUrlContent:
    """Tests for URL content fetching."""

    def test_fetches_and_strips_html(self) -> None:
        """Fetches URL and strips HTML tags."""
        mock_response = MagicMock()
        mock_response.text = (
            "<html><head><title>Test</title></head>"
            "<body><h1>Article Title</h1>"
            "<p>This is the article content.</p></body></html>"
        )
        mock_response.raise_for_status = MagicMock()

        with patch("do_uw.knowledge.ingestion_llm.httpx.get", return_value=mock_response):
            from do_uw.knowledge.ingestion_llm import fetch_url_content

            text = fetch_url_content("https://example.com/article")

        assert "Article Title" in text
        assert "article content" in text
        assert "<html>" not in text
        assert "<p>" not in text

    def test_truncates_long_content(self) -> None:
        """Content is truncated to max length."""
        long_content = "A" * 100_000
        mock_response = MagicMock()
        mock_response.text = long_content
        mock_response.raise_for_status = MagicMock()

        with patch("do_uw.knowledge.ingestion_llm.httpx.get", return_value=mock_response):
            from do_uw.knowledge.ingestion_llm import fetch_url_content

            text = fetch_url_content("https://example.com/long")

        assert len(text) <= 50_000

    def test_strips_script_and_style(self) -> None:
        """Script and style blocks are removed."""
        html = (
            "<html><head><style>body{color:red}</style></head>"
            "<body><script>alert('xss')</script>"
            "<p>Visible content</p></body></html>"
        )
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()

        with patch("do_uw.knowledge.ingestion_llm.httpx.get", return_value=mock_response):
            from do_uw.knowledge.ingestion_llm import fetch_url_content

            text = fetch_url_content("https://example.com/xss")

        assert "alert" not in text
        assert "color:red" not in text
        assert "Visible content" in text


# ---------------------------------------------------------------------------
# generate_impact_report tests
# ---------------------------------------------------------------------------


class TestGenerateImpactReport:
    """Tests for impact report generation."""

    def test_computes_metrics_from_result(self) -> None:
        """Impact report correctly computes metrics from ingestion result."""
        from do_uw.knowledge.ingestion_llm import generate_impact_report

        result = _sample_result()
        report = generate_impact_report(result, "test_report.md", "SHORT_SELLER_REPORT")

        assert isinstance(report, IngestionImpactReport)
        assert report.document_name == "test_report.md"
        assert report.document_type == "SHORT_SELLER_REPORT"
        assert report.checks_affected == 3
        assert report.gaps_found == 1
        assert report.proposals_generated == 1
        assert "ACME" in report.summary
        assert "SHORT_SELLER_REPORT" in report.summary

    def test_zero_gaps_when_empty_analysis(self) -> None:
        """Gaps found is 0 when gap_analysis is empty."""
        from do_uw.knowledge.ingestion_llm import generate_impact_report

        result = DocumentIngestionResult(
            event_type="GENERAL",
            event_summary="Nothing significant",
            do_implications=[],
            gap_analysis="",
        )
        report = generate_impact_report(result, "empty.txt", "GENERAL")

        assert report.gaps_found == 0
        assert report.checks_affected == 0
        assert report.proposals_generated == 0

    def test_report_includes_ingestion_result(self) -> None:
        """Impact report contains the full ingestion result."""
        from do_uw.knowledge.ingestion_llm import generate_impact_report

        result = _sample_result()
        report = generate_impact_report(result, "doc.md", "GENERAL")

        assert report.ingestion_result is result
        assert report.ingestion_result.company_ticker == "ACME"


# ---------------------------------------------------------------------------
# store_proposals tests
# ---------------------------------------------------------------------------


class TestStoreProposals:
    """Tests for proposal storage in brain DuckDB."""

    def test_stores_proposals_in_brain(self) -> None:
        """Proposals are inserted into brain_proposals and as INCUBATING checks."""
        from do_uw.knowledge.ingestion_llm import store_proposals

        result = _sample_result()

        # Mock BrainWriter
        mock_writer = MagicMock()
        mock_conn = MagicMock()
        mock_writer._get_conn.return_value = mock_conn
        mock_writer.insert_check.return_value = 1

        count = store_proposals(mock_writer, result, "test_doc.md")

        assert count == 1
        # Verify brain_proposals INSERT was called
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        assert "brain_proposals" in call_args[0][0]
        assert call_args[0][1][0] == "INGESTION"
        assert call_args[0][1][1] == "test_doc.md"

        # Verify INCUBATING check was created
        mock_writer.insert_check.assert_called_once()
        insert_args = mock_writer.insert_check.call_args
        assert insert_args.kwargs["signal_id"] == "BIZ.SHORTSELL.report_count"
        signal_data = insert_args.kwargs["signal_data"]
        assert signal_data["lifecycle_state"] == "INCUBATING"

    def test_returns_zero_for_no_proposals(self) -> None:
        """Returns 0 when no proposals exist."""
        from do_uw.knowledge.ingestion_llm import store_proposals

        result = DocumentIngestionResult(
            event_type="GENERAL",
            event_summary="Nothing",
            do_implications=[],
        )

        mock_writer = MagicMock()
        count = store_proposals(mock_writer, result, "empty.md")

        assert count == 0
        mock_writer._get_conn.assert_not_called()

    def test_skips_incubating_on_existing_check(self) -> None:
        """Skips INCUBATING insert when check already exists."""
        from do_uw.knowledge.ingestion_llm import store_proposals

        result = _sample_result()

        mock_writer = MagicMock()
        mock_conn = MagicMock()
        mock_writer._get_conn.return_value = mock_conn
        mock_writer.insert_check.side_effect = ValueError("already exists")

        count = store_proposals(mock_writer, result, "test.md")

        # Proposal still inserted in brain_proposals
        assert count == 1
        mock_conn.execute.assert_called_once()

    def test_does_not_create_incubating_for_insufficient_detail(self) -> None:
        """Proposals without enough detail skip INCUBATING check creation."""
        from do_uw.knowledge.ingestion_llm import store_proposals

        result = DocumentIngestionResult(
            event_type="GENERAL",
            event_summary="Test",
            do_implications=[],
            proposed_new_checks=[
                ProposedCheck(
                    signal_id="",  # Empty signal_id
                    name="Vague check",
                    threshold_type="tiered",
                    report_section="company",
                    question="",  # Empty question
                    rationale="Too vague",
                ),
            ],
        )

        mock_writer = MagicMock()
        mock_conn = MagicMock()
        mock_writer._get_conn.return_value = mock_conn

        count = store_proposals(mock_writer, result, "vague.md")

        assert count == 1
        # brain_proposals INSERT called, but insert_check NOT called
        mock_conn.execute.assert_called_once()
        mock_writer.insert_check.assert_not_called()


# ---------------------------------------------------------------------------
# CLI ingest file tests
# ---------------------------------------------------------------------------


class TestCliIngestFile:
    """Tests for the `ingest file` CLI command."""

    def test_ingest_file_with_mocked_llm(self, tmp_path: Path) -> None:
        """CLI ingest file command works with mocked LLM."""
        from typer.testing import CliRunner

        from do_uw.cli_ingest import ingest_app

        doc = tmp_path / "report.txt"
        doc.write_text(
            "Hindenburg Research report on ACME Corp\n"
            "Revenue inflated by 40% through channel stuffing\n",
            encoding="utf-8",
        )

        sample = _sample_result()

        with patch(
            "do_uw.knowledge.ingestion_llm.extract_document_intelligence",
            return_value=sample,
        ):
            runner = CliRunner()
            result = runner.invoke(ingest_app, ["file", str(doc)])

        assert result.exit_code == 0
        assert "Document Ingestion Report" in result.output
        assert "SHORT_SELLER_REPORT" in result.output

    def test_ingest_file_not_found(self) -> None:
        """CLI ingest file shows error for missing file."""
        from typer.testing import CliRunner

        from do_uw.cli_ingest import ingest_app

        runner = CliRunner()
        result = runner.invoke(ingest_app, ["file", "/nonexistent/file.txt"])

        assert result.exit_code == 1

    def test_ingest_file_empty(self, tmp_path: Path) -> None:
        """CLI ingest file shows warning for empty file."""
        from typer.testing import CliRunner

        from do_uw.cli_ingest import ingest_app

        doc = tmp_path / "empty.txt"
        doc.write_text("", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(ingest_app, ["file", str(doc)])

        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# llm_extraction_fn tests
# ---------------------------------------------------------------------------


class TestLlmExtractionFn:
    """Tests for the LLM extraction function wired into ingestion.py."""

    def test_llm_extraction_fn_converts_result(self) -> None:
        """llm_extraction_fn converts DocumentIngestionResult to item dicts."""
        from do_uw.knowledge.ingestion import DocumentType, llm_extraction_fn

        sample = _sample_result()

        with patch(
            "do_uw.knowledge.ingestion_llm.extract_document_intelligence",
            return_value=sample,
        ):
            items = llm_extraction_fn("test text", DocumentType.SHORT_SELLER_REPORT)

        # 3 implications -> notes, 1 proposal -> signal_idea, 1 gap -> note
        assert len(items) == 5
        notes = [i for i in items if i["type"] == "note"]
        signal_ideas = [i for i in items if i["type"] == "signal_idea"]
        assert len(notes) == 4  # 3 implications + 1 gap
        assert len(signal_ideas) == 1

    def test_llm_extraction_fn_returns_empty_on_low_confidence(self) -> None:
        """Returns empty list when LLM returns UNKNOWN/LOW result."""
        from do_uw.knowledge.ingestion import DocumentType, llm_extraction_fn

        minimal = DocumentIngestionResult(
            event_type="UNKNOWN",
            event_summary="Unavailable",
            do_implications=[],
            confidence="LOW",
        )

        with patch(
            "do_uw.knowledge.ingestion_llm.extract_document_intelligence",
            return_value=minimal,
        ):
            items = llm_extraction_fn("test text", DocumentType.GENERAL)

        assert items == []

    def test_llm_extraction_fn_returns_empty_on_import_error(self) -> None:
        """Returns empty list when ingestion_llm cannot be imported."""
        from do_uw.knowledge.ingestion import DocumentType, llm_extraction_fn

        # Test with actual function - if ANTHROPIC_API_KEY not set,
        # it returns minimal result which we treat as empty
        import os

        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            items = llm_extraction_fn("test text", DocumentType.GENERAL)
            # Should return empty since LLM is unavailable
            assert items == []
        finally:
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key
