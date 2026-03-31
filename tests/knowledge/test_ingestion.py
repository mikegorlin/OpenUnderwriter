"""Tests for document ingestion pipeline.

Validates extraction of knowledge items from external documents,
creation of incubating checks, and note storage in the knowledge store.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from do_uw.knowledge.ingestion import (
    DocumentType,
    IngestionResult,
    extract_knowledge_items,
    ingest_document,
    ingest_text,
)
from do_uw.knowledge.store import KnowledgeStore


@pytest.fixture(autouse=True)
def _disable_llm_extraction():
    """Disable LLM extraction in all ingestion tests to test rule-based logic."""
    with patch("do_uw.knowledge.ingestion.llm_extraction_fn", return_value=[]):
        yield


@pytest.fixture()
def store() -> KnowledgeStore:
    """Create an in-memory knowledge store."""
    return KnowledgeStore(db_path=None)


# -----------------------------------------------------------------------
# extract_knowledge_items tests
# -----------------------------------------------------------------------


class TestExtractKnowledgeItems:
    """Tests for rule-based knowledge extraction."""

    def test_risk_prefix_creates_signal_ideas(self) -> None:
        """Lines starting with RISK: are extracted as signal_ideas."""
        text = (
            "RISK: Excessive executive compensation without clawback\n"
            "RISK: Recent restatement of financial results\n"
            "Some other text\n"
        )
        items = extract_knowledge_items(text, DocumentType.SHORT_SELLER_REPORT)

        signal_ideas = [i for i in items if i["type"] == "signal_idea"]
        assert len(signal_ideas) >= 2
        assert any("clawback" in str(i["content"]) for i in signal_ideas)
        assert any("restatement" in str(i["content"]) for i in signal_ideas)

    def test_check_prefix_creates_signal_ideas(self) -> None:
        """Lines starting with CHECK: are extracted as signal_ideas."""
        text = "CHECK: Verify auditor has not been recently changed\n"
        items = extract_knowledge_items(text, DocumentType.CLAIMS_STUDY)

        signal_ideas = [i for i in items if i["type"] == "signal_idea"]
        assert len(signal_ideas) == 1
        assert "auditor" in signal_ideas[0]["content"]

    def test_note_prefix_creates_notes(self) -> None:
        """Lines starting with NOTE: are extracted as notes."""
        text = (
            "NOTE: Companies in this sector have higher claim frequency\n"
            "NOTE: D&O pricing has softened in recent quarters\n"
        )
        items = extract_knowledge_items(text, DocumentType.INDUSTRY_ANALYSIS)

        notes = [i for i in items if i["type"] == "note"]
        assert len(notes) == 2
        assert notes[0]["tags"] == "industry"

    def test_observation_prefix_creates_notes(self) -> None:
        """Lines starting with OBSERVATION: are extracted as notes."""
        text = "OBSERVATION: Regulatory environment is tightening\n"
        items = extract_knowledge_items(text, DocumentType.REGULATORY_GUIDANCE)

        notes = [i for i in items if i["type"] == "note"]
        assert len(notes) == 1
        assert "regulatory" in notes[0]["tags"]

    def test_bullet_points_under_headers(self) -> None:
        """Bullet points under KEY FINDINGS headers become notes."""
        text = (
            "## KEY FINDINGS\n"
            "- Board independence ratio is below industry average\n"
            "- Multiple related-party transactions detected\n"
            "\n"
            "## Other Section\n"
            "Some other content\n"
        )
        items = extract_knowledge_items(text, DocumentType.GENERAL)

        notes = [i for i in items if i["type"] == "note"]
        assert len(notes) >= 2
        assert any("Board independence" in str(n["content"]) for n in notes)

    def test_bullets_under_conclusions_header(self) -> None:
        """Bullet points under CONCLUSIONS header are extracted."""
        text = (
            "# CONCLUSIONS\n"
            "- Management credibility is questionable\n"
            "- Governance score is in bottom quartile\n"
        )
        items = extract_knowledge_items(text, DocumentType.GENERAL)

        notes = [i for i in items if i["type"] == "note"]
        assert len(notes) >= 2

    def test_numbered_items_create_signal_ideas(self) -> None:
        """Numbered list items are extracted as signal_ideas."""
        text = (
            "1. Verify insider selling patterns are within normal range\n"
            "2. Check for recent SEC comment letters\n"
            "3. Short\n"  # Too short, should be skipped
        )
        items = extract_knowledge_items(text, DocumentType.UNDERWRITER_NOTES)

        signal_ideas = [i for i in items if i["type"] == "signal_idea"]
        # Only items with >10 chars content should be included
        assert len(signal_ideas) == 2

    def test_empty_text_returns_empty(self) -> None:
        """Empty text produces no items."""
        items = extract_knowledge_items("", DocumentType.GENERAL)
        assert items == []

    def test_no_patterns_returns_empty(self) -> None:
        """Text without any matching patterns returns empty list."""
        text = "This is just regular text without any special markers.\n"
        items = extract_knowledge_items(text, DocumentType.GENERAL)
        # Only numbered items might match, but content is too short
        assert len(items) == 0

    def test_custom_extraction_fn(self) -> None:
        """Custom extraction_fn is used when provided."""
        def custom_fn(
            text: str, doc_type: DocumentType,
        ) -> list[dict[str, Any]]:
            return [{"type": "note", "title": "custom", "content": text, "tags": "custom"}]

        items = extract_knowledge_items(
            "test text", DocumentType.GENERAL, extraction_fn=custom_fn,
        )
        assert len(items) == 1
        assert items[0]["title"] == "custom"

    def test_doc_type_tags(self) -> None:
        """Each document type produces the correct tag."""
        for doc_type, expected_tag in [
            (DocumentType.SHORT_SELLER_REPORT, "short_seller"),
            (DocumentType.CLAIMS_STUDY, "claims_study"),
            (DocumentType.UNDERWRITER_NOTES, "underwriter"),
            (DocumentType.INDUSTRY_ANALYSIS, "industry"),
            (DocumentType.REGULATORY_GUIDANCE, "regulatory"),
            (DocumentType.GENERAL, "general"),
        ]:
            text = f"RISK: Test risk for {doc_type.value}\n"
            items = extract_knowledge_items(text, doc_type)
            assert len(items) >= 1
            assert items[0]["tags"] == expected_tag

    def test_case_insensitive_prefixes(self) -> None:
        """RISK: and risk: both match (case-insensitive prefix check)."""
        text = "risk: lowercase risk prefix detected\n"
        items = extract_knowledge_items(text, DocumentType.GENERAL)
        signal_ideas = [i for i in items if i["type"] == "signal_idea"]
        assert len(signal_ideas) == 1


# -----------------------------------------------------------------------
# ingest_document tests
# -----------------------------------------------------------------------


class TestIngestDocument:
    """Tests for document ingestion from files."""

    def test_creates_incubating_checks(
        self, store: KnowledgeStore, tmp_path: Path,
    ) -> None:
        """Ingesting a document with RISK: lines creates incubating checks."""
        doc = tmp_path / "report.md"
        doc.write_text(
            "RISK: Excessive CEO pay ratio\n"
            "RISK: Board lacks cybersecurity expertise\n",
            encoding="utf-8",
        )

        result = ingest_document(store, doc, DocumentType.SHORT_SELLER_REPORT)

        assert result.checks_created == 2
        assert result.document_name == "report.md"
        assert result.doc_type == "SHORT_SELLER_REPORT"

        # Verify checks exist in store
        checks = store.query_checks(status="INCUBATING", limit=100)
        assert len(checks) >= 2

    def test_creates_notes(
        self, store: KnowledgeStore, tmp_path: Path,
    ) -> None:
        """Ingesting a document with NOTE: lines creates notes."""
        doc = tmp_path / "notes.txt"
        doc.write_text(
            "NOTE: Industry pricing is softening\n"
            "NOTE: New regulation expected Q3\n",
            encoding="utf-8",
        )

        result = ingest_document(store, doc, DocumentType.UNDERWRITER_NOTES)

        assert result.notes_added == 2
        assert result.document_name == "notes.txt"

    def test_empty_document_returns_zero(
        self, store: KnowledgeStore, tmp_path: Path,
    ) -> None:
        """Empty document produces zero results."""
        doc = tmp_path / "empty.txt"
        doc.write_text("", encoding="utf-8")

        result = ingest_document(store, doc, DocumentType.GENERAL)

        assert result.checks_created == 0
        assert result.notes_added == 0
        assert len(result.errors) == 0

    def test_unsupported_extension_raises(
        self, store: KnowledgeStore, tmp_path: Path,
    ) -> None:
        """Unsupported file extension raises ValueError."""
        doc = tmp_path / "report.pdf"
        doc.write_text("some content", encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported file extension"):
            ingest_document(store, doc, DocumentType.GENERAL)

    def test_missing_file_raises(
        self, store: KnowledgeStore, tmp_path: Path,
    ) -> None:
        """Missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ingest_document(
                store,
                tmp_path / "nonexistent.txt",
                DocumentType.GENERAL,
            )

    def test_mixed_content(
        self, store: KnowledgeStore, tmp_path: Path,
    ) -> None:
        """Document with both RISK: and NOTE: creates both types."""
        doc = tmp_path / "mixed.md"
        doc.write_text(
            "RISK: Accounting irregularities detected\n"
            "NOTE: CFO recently departed\n"
            "Some regular text\n"
            "CHECK: Verify revenue recognition policy\n",
            encoding="utf-8",
        )

        result = ingest_document(store, doc, DocumentType.CLAIMS_STUDY)

        assert result.checks_created == 2  # RISK + CHECK
        assert result.notes_added == 1     # NOTE


# -----------------------------------------------------------------------
# ingest_text tests
# -----------------------------------------------------------------------


class TestIngestText:
    """Tests for raw text ingestion."""

    def test_ingest_from_raw_text(
        self, store: KnowledgeStore,
    ) -> None:
        """Raw text ingestion works without a file."""
        text = (
            "RISK: Potential whistleblower claims\n"
            "NOTE: Company under SEC investigation\n"
        )
        result = ingest_text(
            store, text, "manual_input", DocumentType.GENERAL,
        )

        assert result.checks_created == 1
        assert result.notes_added == 1
        assert result.document_name == "manual_input"

    def test_ingest_empty_text(
        self, store: KnowledgeStore,
    ) -> None:
        """Empty text produces zero results."""
        result = ingest_text(
            store, "", "empty", DocumentType.GENERAL,
        )

        assert result.checks_created == 0
        assert result.notes_added == 0


# -----------------------------------------------------------------------
# IngestionResult tests
# -----------------------------------------------------------------------


class TestIngestionResult:
    """Tests for IngestionResult dataclass."""

    def test_default_values(self) -> None:
        """Default values are zero/empty."""
        result = IngestionResult(
            document_name="test", doc_type="GENERAL",
        )
        assert result.checks_created == 0
        assert result.notes_added == 0
        assert result.errors == []

    def test_errors_list_isolation(self) -> None:
        """Each IngestionResult has its own errors list."""
        r1 = IngestionResult(document_name="a", doc_type="X")
        r2 = IngestionResult(document_name="b", doc_type="Y")
        r1.errors.append("err1")
        assert r2.errors == []
