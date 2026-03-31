"""Quarterly data integration: aggregate post-annual 10-Q extractions.

Bridges the gap between LLM extraction results (TenQExtraction dicts
stored in ``acquired_data.llm_extractions``) and the structured
``QuarterlyUpdate`` model consumed by the renderer.

Only 10-Q/6-K filings dated AFTER the most recent 10-K are included --
earlier quarterlies are superseded by the annual report.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import QuarterlyUpdate
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.llm.schemas.ten_q import TenQExtraction

logger = logging.getLogger(__name__)


def aggregate_quarterly_updates(
    state: AnalysisState,
) -> list[QuarterlyUpdate]:
    """Build QuarterlyUpdate list from post-annual 10-Q LLM extractions.

    Steps:
    1. Find the most recent 10-K filing date from ``filing_documents``.
    2. Iterate ``llm_extractions`` for keys starting with ``10-Q:`` or
       ``6-K:``.
    3. Keep only those filed AFTER the 10-K date.
    4. Convert each ``TenQExtraction`` to a ``QuarterlyUpdate`` with
       ``SourcedValue`` wrapping.
    5. Sort by ``period_end`` descending (most recent first).

    Returns:
        List of QuarterlyUpdate, most recent first. Empty if no
        post-annual 10-Qs exist.
    """
    if state.acquired_data is None:
        return []

    # Step 1: Find most recent 10-K filing date
    annual_date = _find_latest_annual_date(state)

    # Step 2-3: Filter post-annual quarterly extractions
    extractions = state.acquired_data.llm_extractions
    if not extractions:
        return []

    # Get annual revenue for cross-validation of quarterly magnitudes
    annual_revenue = _get_annual_revenue(state)

    updates: list[QuarterlyUpdate] = []
    for key, data in extractions.items():
        if not (key.startswith("10-Q:") or key.startswith("6-K:")):
            continue
        if not isinstance(data, dict):
            continue

        # Extract accession from key (format: "10-Q:accession_number")
        accession = key.split(":", 1)[1] if ":" in key else ""

        # Find filing_date from filing_documents for this accession
        form_type = key.split(":")[0]
        filing_date = _find_filing_date(state, form_type, accession)

        # Skip if filed before the most recent 10-K
        if annual_date and filing_date and filing_date <= annual_date:
            logger.debug(
                "Skipping %s -- filed %s, before 10-K %s",
                key, filing_date, annual_date,
            )
            continue

        # Deserialize to TenQExtraction
        try:
            extraction = TenQExtraction.model_validate(data)
        except Exception:
            logger.warning(
                "Failed to deserialize 10-Q extraction: %s",
                key, exc_info=True,
            )
            continue

        # Step 4: Convert to QuarterlyUpdate (with unit normalization)
        update = _convert_extraction(
            extraction, accession, filing_date or "", form_type,
            annual_revenue=annual_revenue,
        )
        updates.append(update)

    # Step 5: Sort most recent first by period_end
    updates.sort(key=lambda u: u.period_end, reverse=True)

    if updates:
        logger.info(
            "Quarterly updates: %d post-annual %s found",
            len(updates),
            "10-Q/6-K" if len(updates) > 1 else "10-Q/6-K",
        )

    return updates


def _find_latest_annual_date(state: AnalysisState) -> str | None:
    """Find the most recent 10-K/20-F filing date from filing_documents."""
    if state.acquired_data is None:
        return None

    filing_docs = state.acquired_data.filing_documents
    latest: str | None = None

    for form_type in ("10-K", "20-F"):
        docs = filing_docs.get(form_type, [])
        for doc in docs:
            fd = doc.get("filing_date", "")
            if fd and (latest is None or fd > latest):
                latest = fd

    return latest


def _find_filing_date(
    state: AnalysisState, form_type: str, accession: str,
) -> str | None:
    """Look up filing_date for a given accession in filing_documents."""
    if state.acquired_data is None:
        return None

    docs = state.acquired_data.filing_documents.get(form_type, [])
    for doc in docs:
        if doc.get("accession", "") == accession:
            return doc.get("filing_date")

    return None


def _normalize_unit(
    value: float,
    annual_reference: float | None,
    label: str,
) -> float:
    """Normalize LLM-extracted financial values to raw USD.

    LLM extraction from 10-Q text is inconsistent: some filings report in
    millions (1909.895), others in thousands (2113743), others in raw USD.
    We use heuristics + cross-validation against annual revenue to normalize.

    Heuristic thresholds (for revenue-scale values):
    - < 50,000 → likely millions, multiply by 1,000,000
    - 50,000 to 50,000,000 → likely thousands, multiply by 1,000
    - >= 50,000,000 → likely raw dollars, no change

    Cross-validation: if annual reference is available, a quarterly value
    should be roughly 15-35% of annual. We pick the multiplier that puts
    the result closest to 25% of annual.
    """
    if value == 0:
        return value

    abs_val = abs(value)

    # If we have an annual reference, use cross-validation
    if annual_reference is not None and annual_reference > 0:
        target_quarter = annual_reference * 0.25  # Expected quarterly value
        candidates = [
            (value * 1_000_000, "millions"),
            (value * 1_000, "thousands"),
            (value, "raw"),
        ]
        best_val, best_label = min(
            candidates,
            key=lambda c: abs(c[0] - target_quarter),
        )
        if best_label != "raw":
            logger.info(
                "Unit normalization (%s): %.2f → %.0f (detected %s, "
                "target quarterly ~%.0f from annual %.0f)",
                label, value, best_val, best_label,
                target_quarter, annual_reference,
            )
        return best_val

    # Fallback: heuristic based on magnitude
    if abs_val < 50_000:
        logger.info(
            "Unit normalization (%s): %.2f → %.0f (assumed millions)",
            label, value, value * 1_000_000,
        )
        return value * 1_000_000
    if abs_val < 50_000_000:
        logger.info(
            "Unit normalization (%s): %.2f → %.0f (assumed thousands)",
            label, value, value * 1_000,
        )
        return value * 1_000
    return value


def _get_annual_revenue(state: AnalysisState) -> float | None:
    """Get annual revenue from extracted financial statements for cross-validation."""
    if state.extracted is None or state.extracted.financials is None:
        return None
    stmts = state.extracted.financials.statements
    if stmts.income_statement is None:
        return None
    for item in stmts.income_statement.line_items:
        if "revenue" in item.label.lower():
            vals = list(item.values.values())
            if vals and vals[0] is not None:
                return float(vals[0].value)
    return None


def _convert_extraction(
    extraction: TenQExtraction,
    accession: str,
    filing_date: str,
    form_type: str,
    *,
    annual_revenue: float | None = None,
) -> QuarterlyUpdate:
    """Convert a TenQExtraction to a QuarterlyUpdate with SourcedValue wrapping."""
    source = f"{form_type}:{accession}"
    now = datetime.now(tz=UTC)

    # Normalize revenue first to establish scale factor for this filing
    norm_revenue: float | None = None
    revenue_scale: float = 1.0
    if extraction.revenue is not None:
        raw_rev = extraction.revenue
        norm_revenue = _normalize_unit(raw_rev, annual_revenue, "revenue")
        if raw_rev != 0:
            revenue_scale = norm_revenue / raw_rev

    # Wrap financial figures in SourcedValue
    revenue: SourcedValue[float] | None = None
    if norm_revenue is not None:
        revenue = SourcedValue[float](
            value=norm_revenue,
            source=source,
            confidence=Confidence.HIGH,
            as_of=now,
        )

    # Use same scale factor for net_income (consistency within a filing)
    net_income: SourcedValue[float] | None = None
    if extraction.net_income is not None:
        ni_val = extraction.net_income * revenue_scale
        net_income = SourcedValue[float](
            value=ni_val,
            source=source,
            confidence=Confidence.HIGH,
            as_of=now,
        )

    eps: SourcedValue[float] | None = None
    if extraction.eps is not None:
        eps = SourcedValue[float](
            value=extraction.eps,
            source=source,
            confidence=Confidence.HIGH,
            as_of=now,
        )

    # Convert ExtractedLegalProceeding objects to strings
    legal_strings: list[str] = []
    for proc in extraction.new_legal_proceedings:
        parts: list[str] = []
        if proc.case_name:
            parts.append(proc.case_name)
        if proc.allegations:
            parts.append(proc.allegations)
        legal_strings.append(": ".join(parts) if parts else "Undisclosed proceeding")

    # Convert ExtractedRiskFactor objects to strings
    risk_strings: list[str] = [
        rf.title for rf in extraction.new_risk_factors if rf.title
    ]

    return QuarterlyUpdate(
        quarter=extraction.quarter or "",
        period_end=extraction.period_end or "",
        filing_date=filing_date,
        accession=accession,
        revenue=revenue,
        net_income=net_income,
        eps=eps,
        prior_year_revenue=(
            extraction.prior_year_revenue * revenue_scale
            if extraction.prior_year_revenue is not None
            else None
        ),
        prior_year_net_income=(
            extraction.prior_year_net_income * revenue_scale
            if extraction.prior_year_net_income is not None
            else None
        ),
        prior_year_eps=extraction.prior_year_eps,
        new_legal_proceedings=legal_strings,
        legal_proceedings_updates=extraction.legal_proceedings_updates,
        going_concern=extraction.going_concern,
        going_concern_detail=extraction.going_concern_detail,
        material_weaknesses=extraction.material_weaknesses,
        new_risk_factors=risk_strings,
        md_a_highlights=extraction.management_discussion_highlights,
        subsequent_events=extraction.subsequent_events,
    )
