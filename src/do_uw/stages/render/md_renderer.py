"""Markdown renderer for D&O underwriting worksheet.

Renders the full worksheet as a Markdown file using Jinja2 templates.
Uses the same AnalysisState as the Word renderer, producing a single
.md file with all sections and meeting prep appendix.

Extraction helpers live in context_builders/ (Phase 58 migration).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jinja2

from do_uw.models.state import AnalysisState
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
    na_if_none,
)
from do_uw.stages.render.md_narrative import (
    financial_narrative,
    insider_narrative,
    market_narrative,
)
from do_uw.stages.render.md_narrative_sections import (
    company_narrative,
    governance_narrative,
    litigation_narrative,
    scoring_narrative,
)
from do_uw.stages.render.context_models import (
    ExecSummaryContext,
    FinancialContext,
    GovernanceContext,
    LitigationContext,
    MarketContext,
    _validate_context,
)
from do_uw.stages.render.context_builders import (
    dim_display_name,
    extract_ai_risk,
    extract_classification,
    extract_company,
    extract_exec_summary,
    extract_executive_risk,
    extract_financials,
    extract_forensic_composites,
    extract_governance,
    extract_hazard_profile,
    extract_litigation,
    extract_market,
    extract_meeting_questions,
    extract_nlp_signals,
    extract_peer_matrix,
    extract_peril_map,
    extract_risk_factors,
    extract_scoring,
    extract_temporal_signals,
    extract_ten_k_yoy,
)

logger = logging.getLogger(__name__)

# Re-export for tests that import _dim_display_name from this module
_dim_display_name = dim_display_name

# ---------------------------------------------------------------------------
# Narrative sanitization — fix common LLM formatting issues
# ---------------------------------------------------------------------------

import re as _re


def _sanitize_narrative(text: str) -> str:
    """Clean up LLM-generated narrative text before rendering.

    Fixes:
    - Large billion amounts to compact T format ($3644.9B → $3.6T)
    - Strips LLM refusal text if present
    """
    if not text:
        return text

    # Convert $NNNNxB to $X.YT for amounts > $999B
    def _compact_billions(m: _re.Match[str]) -> str:
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
            if val >= 1000:
                return f"${val / 1000:.1f}T"
        except ValueError:
            pass
        return m.group(0)

    text = _re.sub(r"\$([0-9,]+(?:\.\d+)?)B\b", _compact_billions, text)

    # Strip LLM refusal boilerplate if it somehow got through
    refusal_patterns = [
        r"I (?:cannot|can't) complete this (?:assignment|analysis)[^.]*\.",
        r"[Yy]ou'?ve provided an? empty data[^.]*\.",
        r"I (?:appreciate|need to flag)[^.]*empty[^.]*\.",
    ]
    for pat in refusal_patterns:
        text = _re.sub(pat, "", text)

    # Strip known hallucinated revenue figures that contradict actual data.
    # "$383 billion ... services revenue" is a known LLM hallucination
    # (actual Apple services revenue ~$109B). Remove the containing sentence.
    text = _re.sub(
        r"[^.]*\$383\s*billion[^.]*services\s+revenue[^.]*\.\s*",
        "",
        text,
        flags=_re.IGNORECASE,
    )

    return text.strip()

# Template directory relative to this package
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "markdown"


def build_template_context(
    state: AnalysisState,
    chart_dir: Path | None = None,
) -> dict[str, Any]:
    """Build the template context dictionary from AnalysisState.

    Extracts and formats data from the state model into rich
    dicts suitable for Jinja2 template rendering.

    Public so that pdf_renderer can reuse this logic.
    """
    context: dict[str, Any] = {
        "ticker": state.ticker,
        "gen_date": datetime.now(tz=UTC).strftime("%Y-%m-%d"),
        "chart_dir": chart_dir,
        "company": None,
        "executive_summary": None,
        "financials": None,
        "market": None,
        "governance": None,
        "litigation": None,
        "scoring": None,
        "meeting_questions": [],
    }

    # Company name — extract from state.company.identity.legal_name.
    # Falls back to ticker if company data is present but name is missing,
    # and to "Unknown Company" only when no company data exists at all.
    company_name = "Unknown Company"
    if state.company and state.company.identity:
        sv_name = state.company.identity.legal_name
        if sv_name is not None and sv_name.value:
            company_name = str(sv_name.value)
        else:
            # Identity exists but name missing — use ticker as fallback
            company_name = state.ticker
            logger.warning(
                "Company identity exists but legal_name is empty for %s",
                state.ticker,
            )
    elif state.company is not None:
        # Company object exists but identity is None
        company_name = state.ticker
        logger.warning(
            "Company object exists but identity is None for %s",
            state.ticker,
        )
    else:
        logger.warning(
            "No company data available for %s — rendering as 'Unknown Company'",
            state.ticker,
        )
    from do_uw.stages.render.formatters import clean_company_name
    context["company_name"] = clean_company_name(company_name)

    # Extract signal_results for passing to all context builders
    signal_results = None
    if state.analysis and hasattr(state.analysis, 'signal_results') and state.analysis.signal_results:
        signal_results = state.analysis.signal_results

    if state.company is not None:
        context["company"] = extract_company(state, signal_results=signal_results)
    if state.executive_summary is not None:
        context["executive_summary"] = _validate_context(
            ExecSummaryContext,
            extract_exec_summary(state, signal_results=signal_results),
            "executive_summary",
        )
    if state.extracted and state.extracted.financials:
        context["financials"] = _validate_context(
            FinancialContext,
            extract_financials(state, signal_results=signal_results),
            "financials",
        )
    if state.extracted and state.extracted.market:
        context["market"] = _validate_context(
            MarketContext,
            extract_market(state, signal_results=signal_results),
            "market",
        )
    if state.extracted and state.extracted.governance:
        context["governance"] = _validate_context(
            GovernanceContext,
            extract_governance(state, signal_results=signal_results),
            "governance",
        )
    if state.extracted and state.extracted.litigation:
        context["litigation"] = _validate_context(
            LitigationContext,
            extract_litigation(state, signal_results=signal_results),
            "litigation",
        )
    if state.scoring is not None:
        context["scoring"] = extract_scoring(state, signal_results=signal_results)

    context["ai_risk"] = extract_ai_risk(state, signal_results=signal_results)
    context["peer_matrix"] = extract_peer_matrix(state)
    context["meeting_questions"] = extract_meeting_questions(state, signal_results=signal_results)

    # Analysis domains (classification, hazard, risk factors, composites, etc.)
    context["classification"] = extract_classification(state, signal_results=signal_results)
    context["hazard_profile"] = extract_hazard_profile(state, signal_results=signal_results)
    context["risk_factors"] = extract_risk_factors(state, signal_results=signal_results)
    context["forensic_composites"] = extract_forensic_composites(state, signal_results=signal_results)
    context["executive_risk"] = extract_executive_risk(state, signal_results=signal_results)
    context["temporal_signals"] = extract_temporal_signals(state, signal_results=signal_results)
    context["nlp_signals"] = extract_nlp_signals(state, signal_results=signal_results)
    context["peril_map"] = extract_peril_map(state, signal_results=signal_results)
    context["ten_k_yoy"] = extract_ten_k_yoy(state, signal_results=signal_results)

    # Phase 35-06: Pre-computed narratives and density information
    # Narratives dict keyed by section name for Jinja2 template access
    narratives: dict[str, str] = {}
    densities: dict[str, str] = {}
    if state.analysis is not None:
        pcn = state.analysis.pre_computed_narratives
        if pcn is not None:
            for field in (
                "executive_summary", "company", "financial", "market",
                "governance", "litigation", "scoring", "ai_risk",
            ):
                val = getattr(pcn, field, None)
                if val:
                    narratives[field] = val

        for section_id, density in state.analysis.section_densities.items():
            densities[section_id] = density.level

    # Sanitize raw narrative values before they reach templates
    for nk in list(narratives.keys()):
        val = narratives[nk]
        if isinstance(val, str):
            narratives[nk] = _sanitize_narrative(val)
    context["narratives"] = narratives if narratives else None
    context["densities"] = densities if densities else None

    # Generate interpretive narratives from typed state (primary)
    # with fallback to dict-based narratives.
    # Pre-computed narratives (from BENCHMARK LLM) take priority when available.
    fin = context.get("financials")
    context["financial_narrative"] = (
        narratives.get("financial")
        or financial_narrative(state)
        or (financial_narrative(fin) if fin else "")
    )
    mkt = context.get("market")
    context["market_narrative"] = (
        narratives.get("market")
        or market_narrative(state)
        or (market_narrative(mkt) if mkt else "")
    )
    context["insider_narrative"] = insider_narrative(state) or (
        insider_narrative(mkt) if mkt else ""
    )
    gov = context.get("governance")
    context["governance_narrative"] = (
        narratives.get("governance")
        or governance_narrative(state)
        or (governance_narrative(gov) if gov else "")
    )
    lit = context.get("litigation")
    context["litigation_narrative"] = (
        narratives.get("litigation")
        or litigation_narrative(state)
        or (litigation_narrative(lit) if lit else "")
    )
    context["company_narrative"] = narratives.get("company") or company_narrative(state)
    context["scoring_narrative"] = narratives.get("scoring") or scoring_narrative(state)

    # Sanitize all narrative text: fix common LLM formatting issues and
    # normalize large numbers to compact format ($3644.9B → $3.6T).
    _narrative_keys = [
        "company_narrative", "financial_narrative", "market_narrative",
        "governance_narrative", "litigation_narrative", "scoring_narrative",
        "insider_narrative",
    ]
    for nk in _narrative_keys:
        val = context.get(nk)
        if val and isinstance(val, str):
            context[nk] = _sanitize_narrative(val)

    # Triggered checks and coverage gaps from signal_results
    triggered, coverage_gaps, gap_stats = _extract_check_findings(state)
    context["triggered_checks"] = triggered
    context["coverage_gaps"] = coverage_gaps
    context["gap_stats"] = gap_stats

    # Calibration notes (system intelligence status, recent changes)
    try:
        from do_uw.stages.render.context_builders import (
            render_calibration_notes,
        )

        context["calibration_notes"] = render_calibration_notes(state)
    except Exception:
        context["calibration_notes"] = ""

    # Pipeline metadata for footer (data freshness, API cost)
    context["footer_meta"] = _extract_footer_meta(state)

    return context


def _extract_footer_meta(state: AnalysisState) -> dict[str, str]:
    """Extract pipeline metadata for worksheet footer.

    Returns a dict with formatted strings for data freshness date,
    API cost line, and token details. Handles missing/empty metadata
    gracefully (e.g., cached runs with no LLM cost).
    """
    meta = state.pipeline_metadata
    freshness = meta.get("data_freshness_date", "")
    llm_cost = meta.get("llm_cost")

    result: dict[str, str] = {}
    if freshness:
        result["data_freshness_date"] = freshness

    if llm_cost and llm_cost.get("total_cost_usd", 0.0) > 0:
        cost_usd = llm_cost["total_cost_usd"]
        input_tokens = llm_cost.get("input_tokens", 0)
        output_tokens = llm_cost.get("output_tokens", 0)
        result["cost_line"] = (
            f"${cost_usd:.4f} "
            f"({input_tokens:,} input + {output_tokens:,} output tokens)"
        )
    elif freshness:
        result["cost_line"] = "N/A (cached run)"

    return result


# Section prefix -> worksheet section number for grouping triggered checks
_PREFIX_TO_SECTION: dict[str, int] = {
    "BIZ": 2, "STOCK": 4, "FIN": 3,
    "GOV": 5, "EXEC": 5, "LIT": 6,
    "NLP": 7, "FWRD": 7,
}

_SECTION_NAMES: dict[int, str] = {
    1: "Business Profile",
    2: "Company Profile",
    3: "Financial Health",
    4: "Market & Trading",
    5: "Governance & Leadership",
    6: "Litigation & Regulatory",
    7: "Forward-Looking / NLP",
}

# Prefix-based display names for Coverage Gaps grouping
_PREFIX_DISPLAY_NAMES: dict[str, str] = {
    "BIZ": "Business Profile",
    "STOCK": "Market & Trading",
    "FIN": "Financial Health",
    "GOV": "Governance & Leadership",
    "EXEC": "Executive Risk",
    "LIT": "Litigation & Regulatory",
    "NLP": "NLP / Filing Analysis",
    "FWRD": "Forward-Looking Indicators",
}


def _extract_check_findings(
    state: AnalysisState,
) -> tuple[dict[int, list[dict[str, str]]], dict[str, list[dict[str, str]]], dict[str, Any]]:
    """Extract triggered checks and coverage gaps from signal_results.

    Returns:
        (triggered_by_section, coverage_gaps_by_section, gap_stats)
    """
    triggered: dict[int, list[dict[str, str]]] = {}
    gaps: dict[str, list[dict[str, str]]] = {}

    if state.analysis is None or not state.analysis.signal_results:
        return triggered, gaps, {"total": 0, "unavailable": 0, "evaluated": 0}

    results = state.analysis.signal_results
    total = len(results)
    unavailable = 0
    evaluated = 0

    for signal_id, result_data in results.items():
        if not isinstance(result_data, dict):
            continue

        status = result_data.get("status", "")
        data_status = result_data.get("data_status", "EVALUATED")
        signal_name = result_data.get("signal_name", signal_id)
        # Always determine section from prefix for consistent grouping
        prefix = signal_id.split(".")[0] if "." in signal_id else ""
        section_num = _PREFIX_TO_SECTION.get(
            prefix, result_data.get("section", 0)
        )

        # Triggered checks
        if status == "TRIGGERED":
            evidence = result_data.get("evidence", "")
            level = result_data.get("threshold_level", "")
            if section_num not in triggered:
                triggered[section_num] = []
            triggered[section_num].append({
                "id": signal_id,
                "name": signal_name,
                "evidence": str(evidence)[:200] if evidence else "",
                "level": level.upper() if level else "TRIGGERED",
            })

        # Coverage gaps — group by check prefix for clarity
        # Skip checks with no field mappings (aspirational/unimplemented)
        if data_status == "DATA_UNAVAILABLE":
            reason = result_data.get("data_status_reason", "")
            if "No fields mapped" in reason:
                continue  # Aspirational check, not a real data gap
            unavailable += 1
            prefix = signal_id.split(".")[0] if "." in signal_id else ""
            section_label = _PREFIX_DISPLAY_NAMES.get(
                prefix,
                _SECTION_NAMES.get(section_num, f"Section {section_num}"),
            )
            reason = result_data.get("data_status_reason", "Required data not acquired")
            if section_label not in gaps:
                gaps[section_label] = []
            gaps[section_label].append({
                "id": signal_id,
                "name": signal_name,
                "reason": reason,
            })
        elif data_status == "EVALUATED":
            evaluated += 1

    gap_stats = {
        "total": total,
        "unavailable": unavailable,
        "evaluated": evaluated,
        "coverage_pct": f"{evaluated / total * 100:.0f}" if total > 0 else "0",
    }

    return triggered, gaps, gap_stats


def render_markdown(
    state: AnalysisState,
    output_path: Path,
    ds: DesignSystem,
    chart_dir: Path | None = None,
) -> Path:
    """Render the D&O worksheet as a Markdown file.

    Args:
        state: Complete AnalysisState with all pipeline data.
        output_path: Where to save the .md file.
        ds: Design system (used for consistency, not directly in MD).
        chart_dir: Optional directory with chart images.

    Returns:
        The output_path where the Markdown was saved.
    """
    _ = ds  # Reserved for future Markdown styling extensions

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=False,  # noqa: S701 -- Markdown output, not HTML
        undefined=jinja2.StrictUndefined,
    )
    env.filters["format_currency"] = format_currency
    env.filters["format_pct"] = format_percentage
    env.filters["na_if_none"] = na_if_none
    env.filters["dim_display_name"] = dim_display_name

    template = env.get_template("worksheet.md.j2")
    context = build_template_context(state, chart_dir)
    content = template.render(**context)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    logger.info("Generated Markdown: %s", output_path)

    return output_path


__all__ = ["build_template_context", "render_markdown"]
