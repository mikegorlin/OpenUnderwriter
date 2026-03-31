"""Pydantic models for document ingestion results and proposed checks.

Defines structured representations for:
- ProposedCheck: a new check proposed by the ingestion pipeline
- DocumentIngestionResult: outcome of ingesting a document for D&O implications
- IngestionImpactReport: summary of ingestion impact on the knowledge base
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProposedCheck(BaseModel):
    """A new check proposed by document ingestion or pattern discovery.

    Enters the brain as INCUBATING until promoted to ACTIVE by human review.
    """

    signal_id: str
    name: str
    content_type: str = "EVALUATIVE_CHECK"
    threshold_type: str
    threshold_red: str | None = None
    threshold_yellow: str | None = None
    threshold_clear: str | None = None
    report_section: str
    question: str
    rationale: str
    field_key: str | None = None
    required_data: list[str] = Field(default_factory=lambda: [])
    data_source: str | None = None


def _empty_str_list() -> list[str]:
    return []


def _empty_proposed_checks() -> list[ProposedCheck]:
    return []


class DocumentIngestionResult(BaseModel):
    """Result of ingesting a document for D&O underwriting implications.

    Captures the event, its implications, affected checks, and any
    proposed new checks or gap analysis.
    """

    company_ticker: str | None = None
    industry_scope: str = "universal"
    event_type: str
    """Event category: LITIGATION, REGULATORY, SETTLEMENT, SHORT_SELLER, etc."""
    event_summary: str
    do_implications: list[str]
    affected_checks: list[str] = Field(default_factory=_empty_str_list)
    proposed_new_checks: list[ProposedCheck] = Field(
        default_factory=_empty_proposed_checks,
    )
    gap_analysis: str = ""
    confidence: str = "MEDIUM"


class IngestionImpactReport(BaseModel):
    """Summary report of a document ingestion's impact on the knowledge base."""

    document_name: str
    document_type: str
    ingestion_result: DocumentIngestionResult
    checks_affected: int
    gaps_found: int
    proposals_generated: int
    summary: str
