"""LLM-powered document ingestion for D&O underwriting intelligence.

Uses instructor + openai (DeepSeek) to extract structured
D&O implications from external documents: short seller reports,
regulatory actions, news articles, claims studies, etc.

Functions:
    extract_document_intelligence: LLM-powered document analysis
    fetch_url_content: HTTP fetch with HTML-to-text conversion
    generate_impact_report: Compute impact metrics from ingestion result
    store_proposals: Persist proposed checks in brain DuckDB
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, cast

import httpx

from do_uw.knowledge.ingestion_models import (
    DocumentIngestionResult,
    IngestionImpactReport,
    ProposedCheck,
)

logger = logging.getLogger(__name__)

# Default LLM model. Override via DO_UW_LLM_MODEL env var.
_DEFAULT_LLM_MODEL = os.environ.get("DO_UW_LLM_MODEL", "deepseek-chat")

# Maximum text length to send to LLM (stay within token budget)
_MAX_TEXT_CHARS = 50_000

# System prompt for D&O document intelligence extraction
_SYSTEM_PROMPT = (
    "You are a D&O liability insurance expert analyzing documents for "
    "underwriting relevance. Extract:\n"
    "1. What company is affected (ticker if known)\n"
    "2. What happened (event type and summary)\n"
    "3. What are the D&O implications (specific liability concerns)\n"
    "4. Which existing check categories might cover this "
    "(use standard prefixes: BIZ., FIN., GOV., LIT., MKT., REG.)\n"
    "5. What new checks might be needed (with specific thresholds)\n"
    "6. Gap analysis: what risks does this reveal that might not be "
    "covered by standard D&O underwriting checks?\n\n"
    "Be specific and concrete. Use standard D&O terminology. "
    "If you cannot determine a field with confidence, leave it empty "
    "or use a conservative default. Never hallucinate specifics."
)


def extract_document_intelligence(
    text: str,
    doc_type: str,
    model: str = _DEFAULT_LLM_MODEL,
) -> DocumentIngestionResult:
    """Extract D&O underwriting intelligence from document text via LLM.

    Uses instructor + openai (DeepSeek) to parse the document and return a
    structured DocumentIngestionResult. Matches the existing LLMExtractor
    pattern (lazy imports, graceful degradation).

    Args:
        text: Raw document text content.
        doc_type: Document type hint (e.g., "SHORT_SELLER_REPORT").
        model: DeepSeek model ID to use.

    Returns:
        DocumentIngestionResult with extracted intelligence.
        On failure, returns a minimal result with confidence="LOW".
    """
    # Truncate to stay within token budget
    truncated = text[:_MAX_TEXT_CHARS]

    # Lazy import openai and instructor (matching existing pattern)
    try:
        import openai as _openai  # type: ignore[import-untyped]
        import instructor as _instructor
        from instructor import Mode
    except ImportError:
        logger.warning("openai/instructor not installed; returning minimal result")
        return _minimal_result(doc_type)

    # Check API key
    if not os.environ.get("DEEPSEEK_API_KEY"):
        logger.warning("DEEPSEEK_API_KEY not set; returning minimal result")
        return _minimal_result(doc_type)

    # Check API key
    if not os.environ.get("DEEPSEEK_API_KEY"):
        logger.warning("DEEPSEEK_API_KEY not set; returning minimal result")
        return _minimal_result(doc_type)

    try:
        raw_client: Any = _openai.OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            max_retries=10,
        )
        client: Any = _instructor.patch(raw_client, mode=Mode.TOOLS)

        user_message = (
            f"Document type: {doc_type}\n\n---BEGIN DOCUMENT---\n{truncated}\n---END DOCUMENT---"
        )

        result = cast(
            DocumentIngestionResult,
            client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_model=DocumentIngestionResult,
                max_tokens=4096,
                max_retries=2,
            ),
        )

        logger.info(
            "LLM ingestion complete: event_type=%s, %d implications, "
            "%d affected checks, %d proposals",
            result.event_type,
            len(result.do_implications),
            len(result.affected_checks),
            len(result.proposed_new_checks),
        )
        return result

    except Exception as exc:
        logger.warning(
            "LLM document extraction failed (%s): %s",
            type(exc).__name__,
            exc,
        )
        return _minimal_result(doc_type)


def _minimal_result(doc_type: str) -> DocumentIngestionResult:
    """Return a minimal result on extraction failure."""
    return DocumentIngestionResult(
        event_type="UNKNOWN",
        event_summary=f"Document analysis unavailable for {doc_type}",
        do_implications=[],
        confidence="LOW",
    )


# ---------------------------------------------------------------------------
# URL fetching
# ---------------------------------------------------------------------------


def fetch_url_content(url: str) -> str:
    """Fetch URL content and convert to plain text.

    Uses httpx with basic HTML tag stripping. The LLM handles
    messy text well, so aggressive cleaning is not needed.

    Args:
        url: URL to fetch.

    Returns:
        Plain text content, truncated to 50,000 chars.

    Raises:
        httpx.HTTPError: On network/HTTP errors.
    """
    response = httpx.get(
        url,
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": "do-uw/1.0 (D&O underwriting tool)"},
    )
    response.raise_for_status()

    content = response.text

    # Basic HTML-to-text: strip tags, decode entities, collapse whitespace
    content = _strip_html_tags(content)
    content = _decode_html_entities(content)
    content = _collapse_whitespace(content)

    # Truncate to stay within token budget
    return content[:_MAX_TEXT_CHARS]


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags from text."""
    # Remove script and style blocks entirely
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Replace block elements with newlines
    html = re.sub(r"<(br|p|div|h[1-6]|li|tr)[^>]*>", "\n", html, flags=re.IGNORECASE)
    # Remove remaining tags
    return re.sub(r"<[^>]+>", "", html)


def _decode_html_entities(text: str) -> str:
    """Decode common HTML entities."""
    import html

    return html.unescape(text)


def _collapse_whitespace(text: str) -> str:
    """Collapse multiple whitespace to single spaces/newlines."""
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces on a line
    text = re.sub(r"[ \t]+", " ", text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Impact report generation
# ---------------------------------------------------------------------------


def generate_impact_report(
    ingestion_result: DocumentIngestionResult,
    doc_name: str,
    doc_type: str,
) -> IngestionImpactReport:
    """Compute impact metrics from a document ingestion result.

    Args:
        ingestion_result: Result from extract_document_intelligence.
        doc_name: Display name for the document.
        doc_type: Document type classification.

    Returns:
        IngestionImpactReport with computed metrics and summary.
    """
    checks_affected = len(ingestion_result.affected_checks)
    gaps_found = 1 if ingestion_result.gap_analysis.strip() else 0
    proposals_generated = len(ingestion_result.proposed_new_checks)

    summary_parts: list[str] = []
    summary_parts.append(
        f"Analyzed '{doc_name}' ({doc_type}): {ingestion_result.event_type} event"
    )
    if ingestion_result.company_ticker:
        summary_parts.append(f"affecting {ingestion_result.company_ticker}")
    summary_parts.append(
        f"with {checks_affected} existing checks affected, "
        f"{gaps_found} gap(s) identified, "
        f"and {proposals_generated} new check(s) proposed."
    )

    return IngestionImpactReport(
        document_name=doc_name,
        document_type=doc_type,
        ingestion_result=ingestion_result,
        checks_affected=checks_affected,
        gaps_found=gaps_found,
        proposals_generated=proposals_generated,
        summary=" ".join(summary_parts),
    )


# ---------------------------------------------------------------------------
# Proposal storage
# ---------------------------------------------------------------------------


def store_proposals(
    writer: Any,  # BrainWriter — avoid import for lazy loading
    result: DocumentIngestionResult,
    doc_name: str,
) -> int:
    """Store proposed signals from ingestion in brain DuckDB.

    For each proposed new check:
    1. Insert into brain_proposals table (always)
    2. If proposal has sufficient detail (signal_id, threshold, question),
       insert as INCUBATING check via BrainWriter.insert_check

    Args:
        writer: BrainWriter instance (connected to brain.duckdb).
        result: DocumentIngestionResult with proposed_new_checks.
        doc_name: Source document name for provenance.

    Returns:
        Number of proposals stored.
    """
    if not result.proposed_new_checks:
        return 0

    conn = writer._get_conn()
    stored = 0

    for proposal in result.proposed_new_checks:
        # 1. Insert into brain_proposals table
        try:
            proposed_check_json = json.dumps(proposal.model_dump())
            conn.execute(
                """INSERT INTO brain_proposals (
                    source_type, source_ref, signal_id, proposal_type,
                    proposed_check, rationale, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    "INGESTION",
                    doc_name,
                    proposal.signal_id,
                    "NEW_CHECK",
                    proposed_check_json,
                    proposal.rationale,
                    "PENDING",
                ],
            )
            stored += 1
        except Exception as exc:
            logger.warning(
                "Failed to store proposal %s: %s",
                proposal.signal_id,
                exc,
            )
            continue

        # 2. Insert as INCUBATING check if proposal has enough detail
        if _proposal_has_sufficient_detail(proposal):
            try:
                signal_data: dict[str, Any] = {
                    "name": proposal.name,
                    "content_type": proposal.content_type,
                    "lifecycle_state": "INCUBATING",
                    "report_section": proposal.report_section,
                    "threshold_type": proposal.threshold_type,
                    "threshold_red": proposal.threshold_red,
                    "threshold_yellow": proposal.threshold_yellow,
                    "threshold_clear": proposal.threshold_clear,
                    "question": proposal.question,
                    "rationale": proposal.rationale,
                    "field_key": proposal.field_key,
                    "required_data": proposal.required_data,
                }
                writer.insert_check(
                    signal_id=proposal.signal_id,
                    signal_data=signal_data,
                    reason=f"Proposed by ingestion of '{doc_name}'",
                    created_by="ingestion_pipeline",
                )
            except ValueError:
                # Check already exists -- not an error for proposals
                logger.debug(
                    "INCUBATING check %s already exists, skipping insert",
                    proposal.signal_id,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to create INCUBATING check %s: %s",
                    proposal.signal_id,
                    exc,
                )

    logger.info(
        "Stored %d proposals from '%s'",
        stored,
        doc_name,
    )
    return stored


def _proposal_has_sufficient_detail(proposal: ProposedCheck) -> bool:
    """Check if a proposal has enough detail for an INCUBATING check."""
    return bool(
        proposal.signal_id
        and proposal.question
        and (proposal.threshold_red or proposal.threshold_yellow)
    )
