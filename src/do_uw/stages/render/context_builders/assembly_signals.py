"""Signal results, coverage stats, footnotes, chart thresholds/callouts.

Registered as a builder in assembly_registry. Phase 128-01.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.assembly_registry import register_builder
from do_uw.stages.render.context_builders.audit import (
    build_audit_context,
    build_reconciliation_audit_context,
)
from do_uw.stages.render.html_footnotes import build_footnote_registry
from do_uw.stages.render.html_signals import (
    _compute_coverage_stats,
    _group_signals_by_section,
)

logger = logging.getLogger(__name__)


def _extract_return_decomposition(state: AnalysisState) -> dict[str, Any]:
    """Extract return decomposition and MDD ratio data for HTML template."""
    result: dict[str, Any] = {
        "return_decomposition_1y": None,
        "return_decomposition_5y": None,
        "mdd_ratio_1y": None,
        "mdd_ratio_5y": None,
        "sector_mdd_1y": None,
        "sector_mdd_5y": None,
        "max_drawdown_1y_val": None,
        "max_drawdown_5y_val": None,
    }
    if not state.extracted or not state.extracted.market:
        return result
    stock = state.extracted.market.stock

    def _sv_val(sv: Any) -> float | None:
        if sv is not None and hasattr(sv, "value"):
            return sv.value
        return None

    # 1Y decomposition.
    m1 = _sv_val(stock.returns_1y_market)
    s1 = _sv_val(stock.returns_1y_sector)
    c1 = _sv_val(stock.returns_1y_company)
    if m1 is not None or s1 is not None or c1 is not None:
        total = sum(v for v in (m1, s1, c1) if v is not None)
        result["return_decomposition_1y"] = {
            "market": m1,
            "sector": s1,
            "company": c1,
            "total": round(total, 2),
        }

    # 5Y decomposition.
    m5 = _sv_val(stock.returns_5y_market)
    s5 = _sv_val(stock.returns_5y_sector)
    c5 = _sv_val(stock.returns_5y_company)
    if m5 is not None or s5 is not None or c5 is not None:
        total = sum(v for v in (m5, s5, c5) if v is not None)
        result["return_decomposition_5y"] = {
            "market": m5,
            "sector": s5,
            "company": c5,
            "total": round(total, 2),
        }

    result["mdd_ratio_1y"] = _sv_val(stock.mdd_ratio_1y)
    result["mdd_ratio_5y"] = _sv_val(stock.mdd_ratio_5y)
    result["sector_mdd_1y"] = _sv_val(stock.sector_mdd_1y)
    result["sector_mdd_5y"] = _sv_val(stock.sector_mdd_5y)
    result["max_drawdown_1y_val"] = _sv_val(stock.max_drawdown_1y)
    result["max_drawdown_5y_val"] = _sv_val(stock.max_drawdown_5y)

    return result


def _extract_chart_metrics(state: AnalysisState) -> dict[str, float | None]:
    """Extract key stock metrics as plain floats for template evaluation."""
    m: dict[str, float | None] = {}
    if not state.extracted or not state.extracted.market:
        return m
    mkt = state.extracted.market
    s = mkt.stock
    for field in ("beta_ratio", "volatility_90d", "sector_vol_90d",
                  "max_drawdown_1y", "decline_from_high_pct", "sector_relative_performance",
                  "idiosyncratic_vol"):
        sv = getattr(s, field, None)
        m[field] = sv.value if sv is not None and hasattr(sv, "value") else None

    # Alpha: company return - sector return (1Y).
    ret = s.returns_1y
    sect = s.sector_relative_performance
    if ret is not None and sect is not None:
        m["alpha_1y"] = sect.value
    elif ret is not None and hasattr(ret, "value"):
        m["alpha_1y"] = ret.value

    # Drop counts for evaluation narrative.
    drops = mkt.stock_drops
    all_drops = [*drops.single_day_drops, *drops.multi_day_drops]
    m["total_drop_count"] = float(len(all_drops))
    m["company_specific_drop_count"] = float(
        sum(1 for d in all_drops if d.is_company_specific)
    )
    m["unexplained_drop_count"] = float(
        sum(1 for d in all_drops if d.trigger_category == "unknown")
    )
    return m


def _build_filing_date_lookup(state: AnalysisState) -> dict[str, str]:
    """Build {form_label: filing_date} lookup from acquired filing documents."""
    from do_uw.stages.render.html_footnotes import _SOURCE_LABELS

    lookup: dict[str, str] = {}
    try:
        if not state.acquired_data or not state.acquired_data.filing_documents:
            return lookup
        for form_type, docs in state.acquired_data.filing_documents.items():
            if isinstance(docs, list) and docs:
                date = docs[0].get("filing_date", "")
                if date:
                    label = _SOURCE_LABELS.get(form_type, form_type)
                    lookup[label] = date
    except Exception:
        pass  # Non-fatal -- source column degrades gracefully
    return lookup


@register_builder
def _build_signals_context(
    state: AnalysisState,
    context: dict[str, Any],
    chart_dir: Path | None,
) -> None:
    """Add signal results, coverage stats, footnotes, chart thresholds."""
    # Check results grouped by section for per-section display
    signal_results = {}
    if state.analysis and state.analysis.signal_results:
        signal_results = state.analysis.signal_results
    filing_date_lookup = _build_filing_date_lookup(state)
    context["signal_results_by_section"] = _group_signals_by_section(signal_results, filing_date_lookup)

    # Coverage stats for appendix
    overall_stats, section_coverage = _compute_coverage_stats(signal_results)
    context["coverage_stats"] = overall_stats
    context["coverage_by_section"] = section_coverage

    # Signal disposition audit trail (Phase 78 -- AUDIT-02)
    disp_summary: dict[str, Any] = {}
    if state.analysis and state.analysis.disposition_summary:
        disp_summary = state.analysis.disposition_summary
    audit_ctx = build_audit_context(disp_summary)
    context.update(audit_ctx)

    # XBRL/LLM reconciliation audit (Phase 128-03 -- INFRA-05)
    recon_warnings: list[dict[str, Any]] = []
    if (
        state.extracted
        and state.extracted.financials
        and state.extracted.financials.reconciliation_warnings
    ):
        recon_warnings = state.extracted.financials.reconciliation_warnings
    recon_ctx = build_reconciliation_audit_context(recon_warnings)
    context.update(recon_ctx)

    # Chart metrics (unwrapped floats for template evaluation logic)
    context["chart_metrics"] = _extract_chart_metrics(state)

    # Chart thresholds from signal YAML (Phase 91 -- DISP-01/DISP-02)
    from do_uw.stages.render.context_builders.chart_thresholds import (
        evaluate_chart_callouts,
        extract_chart_thresholds,
    )
    context["thresholds"] = extract_chart_thresholds(state)

    # Chart callouts from signal callout_templates (Phase 91 -- DISP-04)
    callouts = evaluate_chart_callouts(state, context["chart_metrics"], context["thresholds"])
    context["chart_flags"] = callouts["flags"]
    context["chart_positives"] = callouts["positives"]

    # Return decomposition and MDD ratio for stock analysis template.
    context.update(_extract_return_decomposition(state))

    # Footnote registry for data tracing (Sources appendix + inline superscripts)
    footnote_reg = build_footnote_registry(state)
    context["footnote_registry"] = footnote_reg
    context["all_sources"] = footnote_reg.all_sources

    # Section dispatch context for facet-driven rendering (Phase 56-03)
    from do_uw.stages.render.section_renderer import build_section_context
    section_ctx = build_section_context(state=state)
    context.update(section_ctx)

    # SCR narratives and D&O implications (Phase 65-03: NARR-04, NARR-06)
    from do_uw.stages.render.context_builders.narrative import (
        extract_do_implications as _extract_doi,
        extract_scr_narratives as _extract_scr,
        extract_section_narratives as _extract_5layer,
    )
    from do_uw.stages.render.context_builders._bull_bear import (
        extract_bull_bear_cases as _extract_bb,
    )
    context["scr_narratives"] = _extract_scr(state)
    context["do_implications_data"] = _extract_doi(state)

    # 5-layer section narratives (Phase 65-01: NARR-01, NARR-05)
    context["section_narratives"] = _extract_5layer(state)

    # Bull/bear framing data (Phase 65-02: NARR-02)
    context["bull_bear_data"] = _extract_bb(state)

    # Pattern firing panel (Phase 109)
    from do_uw.stages.render.context_builders.pattern_context import (
        build_pattern_context,
    )
    context["pattern_context"] = build_pattern_context(state)

    # Adversarial critique / Devil's Advocate (Phase 110)
    from do_uw.stages.render.context_builders.adversarial_context import (
        build_adversarial_context,
    )
    context["adversarial"] = build_adversarial_context(state)


__all__ = ["_build_signals_context", "_extract_return_decomposition", "_extract_chart_metrics", "_build_filing_date_lookup"]
