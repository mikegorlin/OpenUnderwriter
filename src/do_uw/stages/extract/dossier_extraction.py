"""Dossier extraction from SEC filings.

Extracts Company Intelligence Dossier fields from 10-K filings using
4 focused LLM extraction prompts targeting specific filing sections.
Populates state.dossier (DossierData) with revenue model details,
ASC 606 elements, unit economics, emerging risks, and revenue flow.

Usage:
    extract_dossier(state)
    # state.dossier is now populated

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.dossier import (
    ASC606Element,
    DossierData,
    EmergingRisk,
    RevenueModelCardRow,
    RevenueSegmentDossier,
    UnitEconomicMetric,
    WaterfallRow,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import get_filing_documents

logger = logging.getLogger(__name__)

# Filing types that contain dossier-relevant content.
_DOSSIER_FILING_TYPES = ("10-K", "20-F")

# Expected extraction fields for reporting.
EXPECTED_FIELDS: list[str] = [
    "revenue_model",
    "asc_606",
    "emerging_risks",
    "unit_economics",
]

# ---------------------------------------------------------------------------
# LLM prompt templates with QUAL-03 analytical context
# ---------------------------------------------------------------------------

_REVENUE_MODEL_PROMPT = """Extract revenue model details from this 10-K filing.

Analytical Context:
Company: {company_name} ({ticker})
Sector: {sector}
Revenue: {revenue}
Revenue Model Type: {revenue_model_type}
Scoring Context: {scoring_summary}

Focus on Items 1 (Business) and 7 (MD&A). Extract:
1. Core revenue model attributes: model type, pricing, quality tier, recognition method
2. Retention/ARPU metrics if disclosed (SaaS companies)
3. Contract duration and concentration risk summary
4. Regulatory overlay on revenue model
5. Revenue flow structure: identify 3-6 key nodes (sources of money, processing steps,
   revenue outputs) and how they connect
6. Per-segment enrichments: for each revenue segment, extract growth rate,
   revenue recognition method, and key risk

For revenue flow, think about: Where does the money come from? What business
processes does it flow through? How is it recognized? Create a simple directed
graph of this flow.
"""

_ASC606_PROMPT = """Extract ASC 606 revenue recognition details from this 10-K filing.

Analytical Context:
Company: {company_name} ({ticker})
Sector: {sector}
Revenue: {revenue}
Revenue Model Type: {revenue_model_type}
Scoring Context: {scoring_summary}

Focus on Note 2 / Revenue Recognition footnote in the financial statements.
Extract:
1. Each element of the five-step ASC 606 model the company applies:
   - Performance obligations identification
   - Transaction price determination
   - Allocation to performance obligations
   - Recognition timing (over time vs point in time)
   - Variable consideration and constraints
2. Key judgments and estimates involved in each element
3. Complexity level for each element (HIGH/MEDIUM/LOW)
4. Billings vs revenue divergence: deferred revenue trends, contract assets/liabilities
5. Overall revenue recognition complexity assessment

If the company does not have complex rev rec (e.g., simple product sales),
note the simplicity and assign LOW complexity.
"""

_EMERGING_RISK_PROMPT = """Extract emerging risks with D&O exposure implications from this 10-K filing.

Analytical Context:
Company: {company_name} ({ticker})
Sector: {sector}
Revenue: {revenue}
Revenue Model Type: {revenue_model_type}
Scoring Context: {scoring_summary}

Focus on Item 1A (Risk Factors) and MD&A forward-looking sections. Extract
risks that are:
1. NEW or EMERGING (not standard boilerplate risks repeated every year)
2. Have specific D&O litigation exposure (could lead to securities class action,
   derivative suit, or regulatory enforcement)
3. Have probability, impact, and timeframe assessments

For each risk, map to a scoring factor reference (F.1-F.10):
- F.1: Financial distress
- F.3: Revenue/earnings quality
- F.7: Stock decline
- F.9: Regulatory/compliance

Filter OUT generic risks like "competition may intensify" or "economic
conditions may worsen" unless the company provides specific details about
current exposure.

NEVER use generic phrases like "warrants further investigation",
"going forward", "demonstrates a commitment", "remains to be seen".
Every risk description MUST include a specific dollar amount, percentage,
date, regulatory body name, or concrete business metric.
"""

_UNIT_ECONOMICS_PROMPT = """Extract unit economics and revenue waterfall from this 10-K filing.

Analytical Context:
Company: {company_name} ({ticker})
Sector: {sector}
Revenue: {revenue}
Revenue Model Type: {revenue_model_type}
Scoring Context: {scoring_summary}

Focus on MD&A (Item 7) and Items 1/7 for operational metrics.

1. First, classify the revenue model category:
   - RECURRING: subscriptions, licenses, maintenance (extract NDR, ARPU, churn, LTV)
   - PROJECT: long-term contracts, construction (extract backlog, win rate, avg contract)
   - TRANSACTION: per-unit sales, fees (extract ASP, volume, market share)
   - HYBRID: mix (extract most relevant from each applicable category)

2. Extract ALL disclosed unit economics metrics. Only mark is_disclosed=True
   for metrics explicitly stated in the filing; inferred metrics get is_disclosed=False.

3. Extract YoY revenue waterfall: decompose current year revenue change into
   components (organic growth, acquisitions, divestitures, FX impact, price/volume,
   new products, etc.). Include prior year starting point and current year ending point.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_analytical_context(state: AnalysisState) -> dict[str, str]:
    """Build QUAL-03 analytical context dict from state."""
    company = state.company
    company_name = ""
    ticker = company.identity.ticker if company else ""

    if company and company.identity.legal_name:
        company_name = company.identity.legal_name.value

    sector = ""
    if company and company.identity.sector:
        sector = company.identity.sector.value

    revenue = "Not available"
    if state.extracted and state.extracted.financials and state.extracted.financials.statements:
        for stmt in state.extracted.financials.statements:
            if hasattr(stmt, "revenue") and stmt.revenue is not None:
                try:
                    rev_val = float(stmt.revenue)
                    if rev_val > 1_000_000:
                        revenue = f"${rev_val / 1_000_000:.1f}M"
                    else:
                        revenue = f"${rev_val:,.0f}"
                except (ValueError, TypeError):
                    pass
                break

    revenue_model_type = "Not classified"
    if company and company.revenue_model_type:
        revenue_model_type = company.revenue_model_type.value

    scoring_summary = "Not yet scored"
    if hasattr(state, "scoring") and state.scoring:
        scoring_obj = state.scoring
        if hasattr(scoring_obj, "composite_score"):
            score = scoring_obj.composite_score
            if score is not None:
                tier = getattr(scoring_obj, "tier", "")
                scoring_summary = f"Score: {score}, Tier: {tier}"

    return {
        "company_name": company_name,
        "ticker": ticker,
        "sector": sector,
        "revenue": revenue,
        "revenue_model_type": revenue_model_type,
        "scoring_summary": scoring_summary,
    }


def _get_filing_text(state: AnalysisState) -> tuple[str, str]:
    """Get the best available 10-K/20-F filing text and accession number.

    Returns (full_text, accession) or ("", "") if unavailable.
    """
    filing_docs = get_filing_documents(state)

    for form_type in _DOSSIER_FILING_TYPES:
        docs = filing_docs.get(form_type, [])
        if not isinstance(docs, list):
            continue
        for doc in docs[:1]:  # Use the most recent filing
            if not isinstance(doc, dict):
                continue
            full_text = doc.get("full_text", "")
            accession = doc.get("accession", "")
            if full_text and accession:
                return full_text, accession

    return "", ""


def _run_llm_extraction(
    filing_text: str,
    form_type: str,
    accession: str,
    system_prompt: str,
    schema_cls: type,
) -> Any | None:
    """Run LLM extraction with a focused prompt and schema.

    Returns the extracted Pydantic model instance, or None on failure.
    """
    try:
        from pathlib import Path

        from do_uw.stages.extract.llm import ExtractionCache, LLMExtractor

        cache = ExtractionCache(db_path=Path(".cache/analysis.db"))
        extractor = LLMExtractor(cache=cache, rate_limit_tpm=100_000_000)

        result = extractor.extract(
            filing_text=filing_text,
            schema=schema_cls,
            accession=accession,
            form_type=f"{form_type}-dossier",
            system_prompt=system_prompt,
            max_tokens=4096,
        )
        return result
    except Exception:
        logger.warning(
            "LLM dossier extraction failed for %s",
            accession,
            exc_info=True,
        )
    return None


def _build_revenue_flow_text(
    nodes: list[dict[str, str]],
    edges: list[dict[str, str]],
) -> str:
    """Convert structured nodes/edges into readable revenue flow text.

    Generates a text-based flow diagram from the LLM extraction output.
    """
    if not nodes and not edges:
        return ""

    lines: list[str] = []

    # Group nodes by type
    sources = [n["label"] for n in nodes if n.get("type") == "source"]
    processes = [n["label"] for n in nodes if n.get("type") == "process"]
    outputs = [n["label"] for n in nodes if n.get("type") == "output"]

    if sources:
        lines.append(f"Sources: {', '.join(sources)}")
    if processes:
        lines.append(f"Processing: {', '.join(processes)}")
    if outputs:
        lines.append(f"Revenue: {', '.join(outputs)}")

    if edges:
        lines.append("")
        lines.append("Flow:")
        for edge in edges:
            from_n = edge.get("from_node", "?")
            to_n = edge.get("to_node", "?")
            label = edge.get("label", "")
            if label:
                lines.append(f"  {from_n} -> {to_n} ({label})")
            else:
                lines.append(f"  {from_n} -> {to_n}")

    return "\n".join(lines)


def _build_revenue_card(extraction: Any) -> list[RevenueModelCardRow]:
    """Build revenue model card rows from RevenueModelExtraction."""
    rows: list[RevenueModelCardRow] = []

    field_map = [
        ("Model Type", "model_type", "Business model classification drives SCA theory selection"),
        ("Pricing Model", "pricing_model", "Pricing complexity affects revenue recognition risk"),
        (
            "Revenue Quality",
            "revenue_quality_tier",
            "Lower quality tiers face higher scrutiny on rev rec",
        ),
        (
            "Recognition Method",
            "recognition_method",
            "Over-time recognition creates more judgment, more SCA surface",
        ),
        (
            "Contract Duration",
            "contract_duration",
            "Short contracts increase revenue volatility and disclosure risk",
        ),
        (
            "Net Dollar Retention",
            "net_dollar_retention",
            "Declining NDR is a leading SCA indicator for SaaS",
        ),
        (
            "Concentration Risk",
            "concentration_risk_summary",
            "High concentration amplifies revenue miss impact",
        ),
        (
            "Regulatory Overlay",
            "regulatory_overlay",
            "Regulated revenue faces compliance-driven SCA risk",
        ),
    ]

    for label, attr, default_risk in field_map:
        value = getattr(extraction, attr, "")
        if value and value not in ("", "Not disclosed", "Not applicable"):
            risk_level = "LOW"
            # Heuristic risk levels for key attributes
            if attr == "revenue_quality_tier" and "Tier 3" in value:
                risk_level = "HIGH"
            elif attr == "revenue_quality_tier" and "Tier 2" in value:
                risk_level = "MEDIUM"
            elif attr == "recognition_method" and "over time" in value.lower():
                risk_level = "MEDIUM"

            rows.append(
                RevenueModelCardRow(
                    attribute=label,
                    value=value,
                    do_risk=default_risk,
                    risk_level=risk_level,
                )
            )

    return rows


# ---------------------------------------------------------------------------
# Sub-extraction functions
# ---------------------------------------------------------------------------


def _extract_revenue_model(state: AnalysisState, filing_text: str, accession: str) -> None:
    """Extract revenue model details and populate state.dossier.

    Also CONSUMES state.company.revenue_segments as authoritative source
    and ENRICHES with growth_rate, rev_rec_method, do_exposure from LLM.
    """
    from do_uw.stages.extract.llm.schemas.dossier import RevenueModelExtraction

    ctx = _get_analytical_context(state)
    prompt = _REVENUE_MODEL_PROMPT.format(**ctx)

    extraction = _run_llm_extraction(
        filing_text, "10-K", accession, prompt, RevenueModelExtraction
    )

    dossier = state.dossier

    # Populate business_description_plain from existing state
    if state.company and state.company.business_description:
        desc = state.company.business_description.value
        dossier.business_description_plain = desc

    if extraction is None:
        logger.warning("Revenue model extraction returned None for %s", accession)
        return

    # Revenue flow diagram
    dossier.revenue_flow_diagram = _build_revenue_flow_text(
        extraction.revenue_flow_nodes,
        extraction.revenue_flow_edges,
    )
    dossier.revenue_flow_narrative = extraction.revenue_flow_narrative

    # Revenue model card
    dossier.revenue_card = _build_revenue_card(extraction)

    # Build segment dossiers: start from existing revenue_segments, enrich with LLM
    enrichments_by_name: dict[str, dict[str, str]] = {}
    for enr in extraction.segment_enrichments:
        name = enr.get("segment_name", "")
        if name:
            enrichments_by_name[name.lower()] = enr

    # CONSUME existing state.company.revenue_segments as authoritative
    segments: list[RevenueSegmentDossier] = []
    if state.company and state.company.revenue_segments:
        for sv in state.company.revenue_segments:
            seg_data = sv.value if hasattr(sv, "value") else sv
            if isinstance(seg_data, dict):
                seg_name = str(seg_data.get("name", seg_data.get("segment", "")))
                rev_pct = str(seg_data.get("percentage", seg_data.get("revenue", "")))

                # Look up enrichment by name (case-insensitive)
                enr = enrichments_by_name.get(seg_name.lower(), {})

                segments.append(
                    RevenueSegmentDossier(
                        segment_name=seg_name,
                        revenue_pct=rev_pct,
                        growth_rate=enr.get("growth_rate", ""),
                        rev_rec_method=enr.get("rev_rec_method", ""),
                        do_exposure=enr.get("key_risk", ""),
                    )
                )

    # Also add segments from LLM enrichment that weren't in state
    existing_names = {s.segment_name.lower() for s in segments}
    for enr in extraction.segment_enrichments:
        name = enr.get("segment_name", "")
        if name and name.lower() not in existing_names:
            segments.append(
                RevenueSegmentDossier(
                    segment_name=name,
                    growth_rate=enr.get("growth_rate", ""),
                    rev_rec_method=enr.get("rev_rec_method", ""),
                    do_exposure=enr.get("key_risk", ""),
                )
            )

    dossier.segment_dossiers = segments

    # Core D&O exposure from concentration + regulatory
    exposure_parts: list[str] = []
    if extraction.concentration_risk_summary:
        exposure_parts.append(extraction.concentration_risk_summary)
    if extraction.regulatory_overlay:
        exposure_parts.append(f"Regulatory: {extraction.regulatory_overlay}")
    if exposure_parts:
        dossier.core_do_exposure = "; ".join(exposure_parts)

    logger.info(
        "Revenue model extraction complete: %d card rows, %d segments",
        len(dossier.revenue_card),
        len(dossier.segment_dossiers),
    )


def _extract_asc_606(state: AnalysisState, filing_text: str, accession: str) -> None:
    """Extract ASC 606 revenue recognition details."""
    from do_uw.stages.extract.llm.schemas.dossier import ASC606Extraction

    ctx = _get_analytical_context(state)
    prompt = _ASC606_PROMPT.format(**ctx)

    extraction = _run_llm_extraction(filing_text, "10-K", accession, prompt, ASC606Extraction)

    if extraction is None:
        logger.warning("ASC 606 extraction returned None for %s", accession)
        return

    dossier = state.dossier

    # Convert to domain models
    dossier.asc_606_elements = [
        ASC606Element(
            element=elem.element,
            approach=elem.approach,
            complexity=elem.complexity,
            do_risk=elem.key_judgment,  # key_judgment maps to do_risk in domain
        )
        for elem in extraction.elements
    ]

    dossier.billings_vs_revenue_narrative = extraction.billings_vs_revenue_gap

    logger.info(
        "ASC 606 extraction complete: %d elements, complexity=%s",
        len(dossier.asc_606_elements),
        extraction.rev_rec_complexity_overall,
    )


def _extract_emerging_risks(state: AnalysisState, filing_text: str, accession: str) -> None:
    """Extract emerging risks with D&O exposure mapping."""
    from do_uw.stages.extract.llm.schemas.dossier import EmergingRiskExtraction

    ctx = _get_analytical_context(state)
    prompt = _EMERGING_RISK_PROMPT.format(**ctx)

    extraction = _run_llm_extraction(
        filing_text, "10-K", accession, prompt, EmergingRiskExtraction
    )

    if extraction is None:
        logger.warning("Emerging risk extraction returned None for %s", accession)
        return

    dossier = state.dossier

    dossier.emerging_risks = [
        EmergingRisk(
            risk=risk.risk,
            probability=risk.probability,
            impact=risk.impact,
            timeframe=risk.timeframe,
            do_factor=risk.scoring_factor_ref,
            status=risk.current_status,
        )
        for risk in extraction.risks
    ]

    logger.info(
        "Emerging risk extraction complete: %d risks",
        len(dossier.emerging_risks),
    )


def _extract_unit_economics(state: AnalysisState, filing_text: str, accession: str) -> None:
    """Extract unit economics and revenue waterfall."""
    from do_uw.stages.extract.llm.schemas.dossier import UnitEconomicsExtraction

    ctx = _get_analytical_context(state)
    prompt = _UNIT_ECONOMICS_PROMPT.format(**ctx)

    extraction = _run_llm_extraction(
        filing_text, "10-K", accession, prompt, UnitEconomicsExtraction
    )

    if extraction is None:
        logger.warning("Unit economics extraction returned None for %s", accession)
        return

    dossier = state.dossier

    # Convert metrics
    dossier.unit_economics = [
        UnitEconomicMetric(
            metric=item.metric_name,
            value=item.value,
            benchmark="",  # Populated in BENCHMARK stage
            assessment="",
            do_risk="",
        )
        for item in extraction.metrics
    ]

    # Convert waterfall
    dossier.waterfall_rows = [
        WaterfallRow(
            label=item.label,
            value=item.value,
            delta="",
            narrative="Growth driver" if item.is_growth_driver else "",
        )
        for item in extraction.waterfall_components
    ]

    logger.info(
        "Unit economics extraction complete: %d metrics, %d waterfall rows",
        len(dossier.unit_economics),
        len(dossier.waterfall_rows),
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_dossier(state: AnalysisState) -> None:
    """Extract Company Intelligence Dossier data from 10-K filings.

    Orchestrates 4 focused LLM extractions targeting specific filing sections.
    Each sub-extraction is try/except wrapped -- failure in one does not block
    others. Modifies state.dossier in-place.

    Args:
        state: Analysis state with acquired filing documents.
    """
    filing_text, accession = _get_filing_text(state)

    if not filing_text:
        logger.warning(
            "No 10-K/20-F filing text available for dossier extraction. Dossier will use defaults."
        )
        return

    # Track which filings we used
    if accession:
        state.dossier.source_filings = [accession]

    # Run 4 focused extractions. Each is independent and fault-tolerant.
    try:
        _extract_revenue_model(state, filing_text, accession)
    except Exception:
        logger.warning("Revenue model extraction failed", exc_info=True)

    try:
        _extract_asc_606(state, filing_text, accession)
    except Exception:
        logger.warning("ASC 606 extraction failed", exc_info=True)

    try:
        _extract_emerging_risks(state, filing_text, accession)
    except Exception:
        logger.warning("Emerging risk extraction failed", exc_info=True)

    try:
        _extract_unit_economics(state, filing_text, accession)
    except Exception:
        logger.warning("Unit economics extraction failed", exc_info=True)

    # Set confidence based on what we got
    filled = 0
    if state.dossier.revenue_card:
        filled += 1
    if state.dossier.asc_606_elements:
        filled += 1
    if state.dossier.emerging_risks:
        filled += 1
    if state.dossier.unit_economics:
        filled += 1

    if filled >= 3:
        state.dossier.extraction_confidence = "HIGH"
    elif filled >= 1:
        state.dossier.extraction_confidence = "MEDIUM"
    else:
        state.dossier.extraction_confidence = "LOW"

    logger.info(
        "Dossier extraction complete: %d/4 sections populated, confidence=%s",
        filled,
        state.dossier.extraction_confidence,
    )
