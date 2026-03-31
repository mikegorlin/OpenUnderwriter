"""Forward-looking statement extraction from SEC filings.

Extracts forward-looking statements, catalyst events, and growth estimates
from 10-K and 8-K filings using LLM extraction, plus yfinance market data
for analyst growth estimates.

Usage:
    statements, catalysts, growth_ests, report = extract_forward_statements(state)
    state.forward_looking.forward_statements = statements
    state.forward_looking.catalysts = catalysts
    state.forward_looking.growth_estimates = growth_ests

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

import logging
import math
from typing import Any, cast

from do_uw.models.forward_looking import (
    CatalystEvent,
    ForwardStatement,
    GrowthEstimate,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_documents,
    get_market_data,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Filing types that contain forward-looking statements.
_FORWARD_FILING_TYPES = ("10-K", "20-F", "8-K")

# Expected extraction fields for the report.
EXPECTED_FIELDS: list[str] = [
    "forward_statements",
    "catalysts",
    "growth_estimates",
]

# LLM extraction prompt for forward-looking statements.
_FORWARD_EXTRACTION_PROMPT = """Extract all forward-looking statements from this SEC filing.

For each forward-looking statement, capture:
- The metric being guided (revenue, EPS, margin, growth rate, etc.)
- The target value or range (specific numbers if provided)
- Numeric low and high bounds if quantitative
- The timeframe (FY2025, Q2 2026, next 12 months)
- Whether quantitative (specific numbers) or qualitative (general outlook)
- The filing section where found (MD&A, Risk Factors, Outlook, etc.)
- Surrounding context (max 300 chars)

Also extract:
- Catalyst events: upcoming events that could materially impact value
- Guidance changes: any raises, cuts, withdrawals, or reaffirmations
- Whether the company provides explicit numeric guidance

Capture BOTH quantitative guidance (numbers) and qualitative outlook statements
("We expect continued growth in our cloud segment").
"""


def _run_llm_extraction(
    filing_text: str,
    form_type: str,
    accession: str,
) -> dict[str, Any] | None:
    """Run LLM extraction on filing text for forward-looking statements.

    Returns a dict matching ForwardLookingExtraction schema, or None if
    LLM extraction is unavailable or fails.
    """
    try:
        from do_uw.stages.extract.llm import LLMExtractor, ExtractionCache
        from do_uw.stages.extract.llm.schemas.forward_looking import (
            ForwardLookingExtraction,
        )
        from pathlib import Path

        cache = ExtractionCache(db_path=Path(".cache/analysis.db"))
        extractor = LLMExtractor(cache=cache, rate_limit_tpm=100_000_000)

        result = extractor.extract(
            filing_text=filing_text,
            schema=ForwardLookingExtraction,
            accession=accession,
            form_type=form_type,
            system_prompt=_FORWARD_EXTRACTION_PROMPT,
            max_tokens=4096,
        )
        if result is not None:
            return result.model_dump()
    except Exception:
        logger.warning(
            "LLM forward-looking extraction failed for %s (%s)",
            accession,
            form_type,
            exc_info=True,
        )
    return None


def _safe_float(value: Any) -> float | None:
    """Safely extract a float, handling NaN/Inf/None."""
    if value is None:
        return None
    try:
        f = float(value)
    except (ValueError, TypeError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _convert_forward_statement(
    extracted: dict[str, Any],
    form_type: str,
    accession: str,
    filing_date: str,
) -> ForwardStatement:
    """Convert an ExtractedForwardStatement dict to a ForwardStatement model."""
    is_quant = extracted.get("is_quantitative", False)

    # Compute midpoint from low/high bounds.
    low = _safe_float(extracted.get("target_numeric_low"))
    high = _safe_float(extracted.get("target_numeric_high"))
    midpoint: float | None = None
    if low is not None and high is not None:
        midpoint = (low + high) / 2.0
    elif low is not None:
        midpoint = low
    elif high is not None:
        midpoint = high

    return ForwardStatement(
        metric_name=extracted.get("metric", ""),
        guidance_claim=extracted.get("target_value", "") or extracted.get("context", ""),
        guidance_midpoint=midpoint if is_quant else None,
        guidance_type="QUANTITATIVE" if is_quant else "QUALITATIVE",
        source_filing=f"{form_type}:{accession}",
        source_date=filing_date,
        confidence="MEDIUM",
    )


def _convert_catalyst(
    extracted: dict[str, Any],
) -> CatalystEvent:
    """Convert an ExtractedCatalyst dict to a CatalystEvent model."""
    return CatalystEvent(
        event=extracted.get("event", ""),
        timing=extracted.get("expected_timing", ""),
        impact_if_negative=extracted.get("potential_impact", ""),
        # litigation_risk left empty -- populated by miss_risk enrichment
        source="LLM extraction from SEC filing",
    )


def _extract_growth_estimates(
    market_data: dict[str, Any],
) -> list[GrowthEstimate]:
    """Extract growth estimates from yfinance market data.

    Pulls forward EPS, trailing EPS, revenue growth, and earnings growth
    from yfinance info dict to build GrowthEstimate models.
    """
    raw_info = market_data.get("info")
    if raw_info is None or not isinstance(raw_info, dict):
        return []
    info = cast(dict[str, Any], raw_info)

    estimates: list[GrowthEstimate] = []

    # Forward EPS estimate.
    forward_eps = _safe_float(info.get("forwardEps"))
    trailing_eps = _safe_float(info.get("trailingEps"))
    if forward_eps is not None:
        trend = "FLAT"
        if trailing_eps is not None and trailing_eps != 0:
            change_pct = (forward_eps - trailing_eps) / abs(trailing_eps) * 100
            if change_pct > 2:
                trend = "UP"
            elif change_pct < -2:
                trend = "DOWN"
        estimates.append(
            GrowthEstimate(
                period="Forward",
                metric="EPS",
                estimate=f"${forward_eps:.2f}",
                estimate_numeric=forward_eps,
                trend=trend,
                source="yfinance",
            )
        )

    # Revenue growth rate.
    rev_growth = _safe_float(info.get("revenueGrowth"))
    if rev_growth is not None:
        pct = rev_growth * 100
        trend = "UP" if pct > 2 else ("DOWN" if pct < -2 else "FLAT")
        estimates.append(
            GrowthEstimate(
                period="Current Y",
                metric="Revenue Growth",
                estimate=f"{pct:.1f}%",
                estimate_numeric=pct,
                trend=trend,
                source="yfinance",
            )
        )

    # Earnings growth rate.
    earn_growth = _safe_float(info.get("earningsGrowth"))
    if earn_growth is not None:
        pct = earn_growth * 100
        trend = "UP" if pct > 2 else ("DOWN" if pct < -2 else "FLAT")
        estimates.append(
            GrowthEstimate(
                period="Current Y",
                metric="Earnings Growth",
                estimate=f"{pct:.1f}%",
                estimate_numeric=pct,
                trend=trend,
                source="yfinance",
            )
        )

    return estimates


def extract_forward_statements(
    state: AnalysisState,
) -> tuple[list[ForwardStatement], list[CatalystEvent], list[GrowthEstimate], ExtractionReport]:
    """Extract forward-looking statements from SEC filings and market data.

    Processes 10-K and 8-K filings via LLM extraction for forward statements
    and catalyst events, and extracts growth estimates from yfinance data.

    Args:
        state: Analysis state with acquired filing documents and market data.

    Returns:
        Tuple of (forward_statements, catalysts, growth_estimates, report).
    """
    found_fields: list[str] = []
    warnings: list[str] = []
    all_statements: list[ForwardStatement] = []
    all_catalysts: list[CatalystEvent] = []

    # Get filing documents for LLM extraction.
    filing_docs = get_filing_documents(state)

    # Process each relevant filing type.
    for form_type in _FORWARD_FILING_TYPES:
        docs = filing_docs.get(form_type, [])
        if not isinstance(docs, list):
            continue

        for doc in docs[:3]:  # Cap at 3 per filing type.
            if not isinstance(doc, dict):
                continue
            full_text = doc.get("full_text", "")
            accession = doc.get("accession", "")
            filing_date = doc.get("filing_date", "")

            if not full_text or not accession:
                continue

            extraction = _run_llm_extraction(full_text, form_type, accession)
            if extraction is None:
                warnings.append(f"LLM extraction failed for {form_type}:{accession}")
                continue

            # Convert forward statements.
            raw_stmts = extraction.get("forward_statements", [])
            for raw in raw_stmts:
                if isinstance(raw, dict):
                    stmt = _convert_forward_statement(
                        raw,
                        form_type,
                        accession,
                        filing_date,
                    )
                    all_statements.append(stmt)

            # Convert catalyst events.
            raw_cats = extraction.get("catalyst_events", [])
            for raw in raw_cats:
                if isinstance(raw, dict):
                    cat = _convert_catalyst(raw)
                    all_catalysts.append(cat)

    if all_statements:
        found_fields.append("forward_statements")
    if all_catalysts:
        found_fields.append("catalysts")

    # Extract growth estimates from yfinance data.
    market_data = get_market_data(state)
    growth_estimates = _extract_growth_estimates(market_data)
    if growth_estimates:
        found_fields.append("growth_estimates")

    if not filing_docs:
        warnings.append("No filing documents available for extraction")

    report = create_report(
        extractor_name="forward_statements",
        expected=EXPECTED_FIELDS,
        found=found_fields,
        source_filing="10-K/8-K LLM extraction + yfinance",
        warnings=warnings,
    )
    log_report(report)

    return all_statements, all_catalysts, growth_estimates, report
