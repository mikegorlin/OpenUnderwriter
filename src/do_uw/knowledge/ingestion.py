"""Document ingestion pipeline for external knowledge.

Accepts external documents (short seller reports, claims studies,
underwriter notes, industry analyses, regulatory guidance) and
extracts knowledge items to create incubating checks and notes
in the knowledge store.

Usage:
    from do_uw.knowledge.ingestion import ingest_document, DocumentType
    from do_uw.knowledge.store import KnowledgeStore

    store = KnowledgeStore()
    result = ingest_document(store, Path("report.md"), DocumentType.SHORT_SELLER_REPORT)
    print(f"Created {result.checks_created} checks, {result.notes_added} notes")
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from do_uw.knowledge.models import Check
from do_uw.knowledge.store import KnowledgeStore

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".txt", ".md"}


def _empty_str_list() -> list[str]:
    """Return empty list of strings (pyright strict compliance)."""
    return []


class DocumentType(StrEnum):
    """Types of external documents that can be ingested."""

    SHORT_SELLER_REPORT = "SHORT_SELLER_REPORT"
    CLAIMS_STUDY = "CLAIMS_STUDY"
    UNDERWRITER_NOTES = "UNDERWRITER_NOTES"
    INDUSTRY_ANALYSIS = "INDUSTRY_ANALYSIS"
    REGULATORY_GUIDANCE = "REGULATORY_GUIDANCE"
    GENERAL = "GENERAL"


@dataclass
class IngestionResult:
    """Result of a document ingestion operation.

    Attributes:
        document_name: Name of the ingested document.
        doc_type: Type classification of the document.
        checks_created: Number of incubating checks created.
        notes_added: Number of notes added to the store.
        errors: List of error messages encountered.
    """

    document_name: str
    doc_type: str
    checks_created: int = 0
    notes_added: int = 0
    errors: list[str] = field(default_factory=_empty_str_list)


# --- Tag mapping for document types ---

_DOC_TYPE_TAGS: dict[DocumentType, str] = {
    DocumentType.SHORT_SELLER_REPORT: "short_seller",
    DocumentType.CLAIMS_STUDY: "claims_study",
    DocumentType.UNDERWRITER_NOTES: "underwriter",
    DocumentType.INDUSTRY_ANALYSIS: "industry",
    DocumentType.REGULATORY_GUIDANCE: "regulatory",
    DocumentType.GENERAL: "general",
}


# --- Rule-based extraction patterns ---

_CHECK_PREFIXES = ("RISK:", "CHECK:")
_NOTE_PREFIXES = ("NOTE:", "OBSERVATION:")
_HEADER_PATTERNS = re.compile(
    r"^#+\s+(KEY FINDINGS|CONCLUSIONS|RECOMMENDATIONS|SUMMARY)\s*$",
    re.IGNORECASE,
)
_BULLET_PATTERN = re.compile(r"^\s*[-*]\s+(.+)$")
_NUMBERED_PATTERN = re.compile(r"^\s*\d+[.)]\s+(.+)$")


def _extract_check_items(
    lines: list[str],
    tag: str,
) -> list[dict[str, Any]]:
    """Extract check ideas from RISK:/CHECK: prefixed lines."""
    items: list[dict[str, Any]] = []
    for line in lines:
        stripped = line.strip()
        for prefix in _CHECK_PREFIXES:
            if stripped.upper().startswith(prefix):
                content = stripped[len(prefix) :].strip()
                if content:
                    items.append(
                        {
                            "type": "signal_idea",
                            "title": content[:100],
                            "content": content,
                            "tags": tag,
                        }
                    )
                break
    return items


def _extract_note_items(
    lines: list[str],
    tag: str,
) -> list[dict[str, Any]]:
    """Extract notes from NOTE:/OBSERVATION: prefixed lines."""
    items: list[dict[str, Any]] = []
    for line in lines:
        stripped = line.strip()
        for prefix in _NOTE_PREFIXES:
            if stripped.upper().startswith(prefix):
                content = stripped[len(prefix) :].strip()
                if content:
                    items.append(
                        {
                            "type": "note",
                            "title": content[:100],
                            "content": content,
                            "tags": tag,
                        }
                    )
                break
    return items


def _extract_header_bullets(
    lines: list[str],
    tag: str,
) -> list[dict[str, Any]]:
    """Extract bullet items under KEY FINDINGS / CONCLUSIONS headers."""
    items: list[dict[str, Any]] = []
    in_section = False

    for line in lines:
        stripped = line.strip()

        # Check if this is a relevant header
        if _HEADER_PATTERNS.match(stripped):
            in_section = True
            continue

        # Exit section on new header or blank line after content
        if in_section and stripped.startswith("#"):
            in_section = False
            continue

        if not in_section:
            continue

        # Extract bullet points
        bullet_match = _BULLET_PATTERN.match(line)
        if bullet_match:
            content = bullet_match.group(1).strip()
            if content:
                items.append(
                    {
                        "type": "note",
                        "title": content[:100],
                        "content": content,
                        "tags": tag,
                    }
                )
            continue

    return items


def _extract_numbered_items(
    lines: list[str],
    tag: str,
) -> list[dict[str, Any]]:
    """Extract numbered list items as potential check ideas."""
    items: list[dict[str, Any]] = []
    for line in lines:
        num_match = _NUMBERED_PATTERN.match(line)
        if num_match:
            content = num_match.group(1).strip()
            if content and len(content) > 10:  # Skip very short items
                items.append(
                    {
                        "type": "signal_idea",
                        "title": content[:100],
                        "content": content,
                        "tags": tag,
                    }
                )
    return items


def extract_knowledge_items(
    text: str,
    doc_type: DocumentType,
    extraction_fn: Callable[[str, DocumentType], list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    """Extract knowledge items from document text.

    Args:
        text: Raw document text content.
        doc_type: Type classification for tag inference.
        extraction_fn: Optional custom extraction function. If provided,
            delegates entirely to this function (hook for future LLM-based
            extraction in Phase 13). Default (None) uses rule-based extraction.

    Returns:
        List of extracted items, each with keys: type, title, content, tags.
    """
    # Use LLM extraction when no custom function provided and anthropic available
    if extraction_fn is not None:
        return extraction_fn(text, doc_type)

    # Try LLM-based extraction as default when available
    if extraction_fn is None:
        llm_items = llm_extraction_fn(text, doc_type)
        if llm_items:
            return llm_items

    tag = _DOC_TYPE_TAGS.get(doc_type, "general")
    lines = text.splitlines()

    items: list[dict[str, Any]] = []
    items.extend(_extract_check_items(lines, tag))
    items.extend(_extract_note_items(lines, tag))
    items.extend(_extract_header_bullets(lines, tag))
    items.extend(_extract_numbered_items(lines, tag))

    return items


def llm_extraction_fn(
    text: str,
    doc_type: DocumentType,
) -> list[dict[str, Any]]:
    """LLM-based extraction function for document ingestion.

    Calls extract_document_intelligence from ingestion_llm.py and
    converts the DocumentIngestionResult to the list[dict] format
    expected by extract_knowledge_items.

    Args:
        text: Raw document text content.
        doc_type: Type classification for the document.

    Returns:
        List of extracted items (signal_ideas and notes).
        Empty list if DeepSeek API is not available or extraction fails.
    """
    try:
        from do_uw.knowledge.ingestion_llm import extract_document_intelligence
    except ImportError:
        return []

    try:
        result = extract_document_intelligence(text, doc_type.value)
    except Exception:
        logger.debug("LLM extraction failed, falling back to rule-based")
        return []

    # Convert LLM result to item dicts
    if result.confidence == "LOW" and result.event_type == "UNKNOWN":
        # LLM returned minimal/failure result, skip
        return []

    items: list[dict[str, Any]] = []
    tag = _DOC_TYPE_TAGS.get(doc_type, "general")

    # D&O implications become notes
    for implication in result.do_implications:
        items.append(
            {
                "type": "note",
                "title": implication[:100],
                "content": implication,
                "tags": tag,
            }
        )

    # Proposed checks become signal_ideas
    for proposal in result.proposed_new_checks:
        items.append(
            {
                "type": "signal_idea",
                "title": proposal.name[:100],
                "content": f"{proposal.question} (threshold: {proposal.threshold_red})",
                "tags": tag,
            }
        )

    # Gap analysis as a note if present
    if result.gap_analysis.strip():
        items.append(
            {
                "type": "note",
                "title": "Gap Analysis",
                "content": result.gap_analysis,
                "tags": tag,
            }
        )

    return items


def _create_incubating_check(
    store: KnowledgeStore,
    item: dict[str, Any],
    source_name: str,
) -> None:
    """Create a single incubating check in the knowledge store."""
    now = datetime.now(UTC)
    signal_id = f"ING-{now.strftime('%Y%m%d%H%M%S')}-{id(item) % 10000:04d}"

    check = Check(
        id=signal_id,
        name=str(item.get("title", "Untitled")),
        section=0,  # Unassigned section for incubating checks
        pillar="INGESTED",
        severity=None,
        execution_mode="MANUAL",
        status="INCUBATING",
        threshold_type=None,
        threshold_value=None,
        required_data=[],
        data_locations={},
        scoring_factor=None,
        scoring_rule=None,
        output_section=None,
        origin="AI_GENERATED",
        created_at=now,
        modified_at=now,
        version=1,
        metadata_json=None,
    )
    store.bulk_insert_checks([check])


def ingest_document(
    store: KnowledgeStore,
    document_path: Path,
    doc_type: DocumentType,
) -> IngestionResult:
    """Ingest an external document into the knowledge store.

    Reads a text or markdown file, extracts knowledge items using
    rule-based patterns, and creates incubating checks and notes.

    Args:
        store: KnowledgeStore instance to write to.
        document_path: Path to a .txt or .md file.
        doc_type: Type classification for the document.

    Returns:
        IngestionResult with counts of created items.

    Raises:
        ValueError: If file extension is not supported.
        FileNotFoundError: If document_path does not exist.
    """
    if document_path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
        msg = (
            f"Unsupported file extension: {document_path.suffix}. "
            f"Supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}"
        )
        raise ValueError(msg)

    if not document_path.exists():
        msg = f"Document not found: {document_path}"
        raise FileNotFoundError(msg)

    text = document_path.read_text(encoding="utf-8")
    return ingest_text(store, text, document_path.name, doc_type)


def ingest_text(
    store: KnowledgeStore,
    text: str,
    source_name: str,
    doc_type: DocumentType,
) -> IngestionResult:
    """Ingest raw text into the knowledge store.

    Extracts knowledge items from text and creates incubating
    checks and notes. Suitable for CLI piping use cases.

    Args:
        store: KnowledgeStore instance to write to.
        text: Raw document text.
        source_name: Name for the source document (for provenance).
        doc_type: Type classification for the document.

    Returns:
        IngestionResult with counts of created items.
    """
    result = IngestionResult(
        document_name=source_name,
        doc_type=doc_type.value,
    )

    items = extract_knowledge_items(text, doc_type)

    for item in items:
        try:
            item_type = str(item.get("type", ""))
            if item_type == "signal_idea":
                _create_incubating_check(store, item, source_name)
                result.checks_created += 1
            elif item_type == "note":
                store.add_note(
                    title=str(item.get("title", "Untitled")),
                    content=str(item.get("content", "")),
                    tags=str(item.get("tags", "")),
                    source=source_name,
                )
                result.notes_added += 1
        except Exception as exc:
            result.errors.append(f"Error processing item: {exc}")
            logger.warning("Ingestion error for %s: %s", source_name, exc)

    logger.info(
        "Ingested %s: %d signals, %d notes from %s",
        source_name,
        result.checks_created,
        result.notes_added,
        doc_type.value,
    )

    return result
