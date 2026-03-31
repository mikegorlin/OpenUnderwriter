"""HTML-specific context: densities, narratives, charts, logos, identity fields.

Registered as a builder in assembly_registry. Phase 128-01.
"""

from __future__ import annotations

import base64
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from do_uw.models.density import PreComputedNarratives
from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.assembly_registry import (
    _should_suppress_insolvency_crf,
    register_builder,
)
from do_uw.stages.render.formatters import (
    format_percentage,
    sector_display_name,
    sv_val,
)

logger = logging.getLogger(__name__)


@register_builder
def _build_html_extras(
    state: AnalysisState,
    context: dict[str, Any],
    chart_dir: Path | None,
) -> None:
    """Add HTML-specific context that doesn't fit other categories."""
    # Densities for conditional rendering
    densities: dict[str, Any] = {}
    if state.analysis and state.analysis.section_densities:
        densities = state.analysis.section_densities
    context["densities"] = densities

    # Pre-computed narratives -- sanitize LLM-generated text before rendering
    narratives = PreComputedNarratives()
    if state.analysis and state.analysis.pre_computed_narratives:
        narratives = state.analysis.pre_computed_narratives
        from do_uw.stages.render.md_renderer import _sanitize_narrative
        for field in ("company", "financial", "governance", "litigation",
                      "market", "scoring", "ai_risk", "executive_summary"):
            val = getattr(narratives, field, None)
            if isinstance(val, str):
                cleaned = _sanitize_narrative(val)
                if cleaned != val:
                    object.__setattr__(narratives, field, cleaned)
    context["narratives"] = narratives

    # Chart images as base64 (fallback for templates not yet migrated to SVG)
    from do_uw.stages.render.pdf_renderer import _load_chart_images
    context["chart_images"] = _load_chart_images(chart_dir)

    # Inline SVG charts (preferred path -- resolution-independent)
    from do_uw.stages.render import _generate_chart_svgs
    from do_uw.stages.render.design_system import DesignSystem as _DS
    context["chart_svgs"] = _generate_chart_svgs(state, _DS())

    # Generation date
    context["generation_date"] = datetime.now(tz=UTC).strftime("%Y-%m-%d")

    # IPO date for identity block
    ipo_date_str = ""
    if state.company and state.company.years_public:
        yp = state.company.years_public.value if hasattr(state.company.years_public, "value") else state.company.years_public
        if yp is not None:
            approx_ipo = datetime.now(tz=UTC) - timedelta(days=int(yp) * 365)
            ipo_date_str = str(approx_ipo.year)
    context["ipo_date"] = ipo_date_str

    # Angry Dolphin logo as base64 for sticky topbar
    logo_path = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        context["logo_b64"] = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    else:
        context["logo_b64"] = ""

    # Company logo for topbar identity block
    company_logo_b64 = ""
    if state.acquired_data and state.acquired_data.company_logo_b64:
        company_logo_b64 = state.acquired_data.company_logo_b64
    context["company_logo_b64"] = company_logo_b64

    # Blind spot discovery status (on AcquiredData)
    blind_spot: dict[str, Any] = {}
    if state.acquired_data and state.acquired_data.blind_spot_results:
        bsr = state.acquired_data.blind_spot_results
        blind_spot = {
            "search_configured": bsr.get("search_configured", False),
            "findings_count": len(bsr.get("findings", [])),
        }
    context["blind_spot_status"] = blind_spot

    # Gap search re-evaluation summary for QA audit template (Phase 46)
    gap_search_summary: dict[str, Any] = {}
    if state.analysis and hasattr(state.analysis, "gap_search_summary"):
        gap_search_summary = state.analysis.gap_search_summary or {}
    context["gap_search_summary"] = gap_search_summary

    # HTML-specific executive summary enrichments (from Word renderer parity)
    from do_uw.stages.render.sections.sect1_executive_tables import (
        build_ceiling_line,
        build_factor_breakdown,
    )
    from do_uw.stages.render.sections.sect1_findings import (
        build_negative_narrative,
        build_positive_narrative,
    )

    # Ensure _state is in context for backward-compat escape hatch
    context["_state"] = state

    # Factor breakdown and ceiling line
    context["factor_breakdown"] = build_factor_breakdown(context)
    context["ceiling_line"] = build_ceiling_line(context)

    # Enrich key findings with narrative builder output (title + rich body)
    # Also attach SCA theory/defense text per D-11/D-12/D-13 (Phase 130-02).
    from do_uw.stages.render.context_builders.company_exec_summary import (
        _SCA_DEFENSE_MAP,
        _SCA_THEORY_MAP,
    )

    es_ctx = context.get("executive_summary") or {}
    if es_ctx and state.executive_summary and state.executive_summary.key_findings:
        kf = state.executive_summary.key_findings
        # Filter out insolvency CRF when conditions don't warrant it
        negatives = [f for f in kf.negatives[:5]
                     if not _should_suppress_insolvency_crf(state, f)]
        enriched_neg: list[dict[str, str]] = []
        for idx, finding in enumerate(negatives, 1):
            title, body = build_negative_narrative(finding, idx, context)
            sca_theory = _SCA_THEORY_MAP.get(
                finding.theory_mapping, finding.theory_mapping or ""
            )
            enriched_neg.append({
                "title": title, "body": body, "sca_theory": sca_theory,
            })
        es_ctx["negatives_enriched"] = enriched_neg

        enriched_pos: list[dict[str, str]] = []
        _seen_pos_titles: set[str] = set()
        for idx, finding in enumerate(kf.positives[:5], 1):
            title, body = build_positive_narrative(finding, idx, context)
            if title not in _seen_pos_titles:
                sca_defense = _SCA_DEFENSE_MAP.get(
                    finding.theory_mapping, finding.theory_mapping or ""
                )
                enriched_pos.append({
                    "title": title, "body": body, "sca_defense": sca_defense,
                })
                _seen_pos_titles.add(title)
        es_ctx["positives_enriched"] = enriched_pos

    # Sector display for header -- prefer yfinance, fall back to SIC mapping.
    sector = ""
    from do_uw.stages.render.context_builders.company_profile import _get_yfinance_sector
    yf_sector = _get_yfinance_sector(state)
    if yf_sector:
        sector = yf_sector
    elif state.company and state.company.identity:
        ident = state.company.identity
        if ident.sic_code and ident.sic_code.value:
            from do_uw.stages.resolve.sec_identity import sic_to_sector
            sector_code = sic_to_sector(str(ident.sic_code.value))
            sector = sector_display_name(sector_code)
        elif ident.sector:
            raw_sector = ident.sector
            sector = sector_display_name(str(raw_sector.value)) if raw_sector.value else ""
    context["sector"] = sector

    # SIC, FPI, FYE from identity
    if state.company and state.company.identity:
        ident = state.company.identity
        context["sic_code"] = str(sv_val(ident.sic_code, "N/A")) if ident.sic_code else "N/A"
        context["sic_description"] = str(sv_val(ident.sic_description, "N/A")) if ident.sic_description else "N/A"
        context["fpi_status"] = "Yes" if ident.is_fpi else "No"
        context["fiscal_year_end"] = str(sv_val(ident.fiscal_year_end, "N/A")) if ident.fiscal_year_end else "N/A"
    else:
        context["sic_code"] = "N/A"
        context["sic_description"] = "N/A"
        context["fpi_status"] = "No"
        context["fiscal_year_end"] = "N/A"

    # GICS, NAICS, and spectrum data from company context
    co = context.get("company") or {}
    context["gics_code"] = co.get("gics_code", "")
    context["gics_name"] = co.get("gics_name", "")
    context["naics_code"] = co.get("naics_code", "")
    context["spectrums"] = co.get("spectrums", {})

    # PDF mode flag: False by default (browser HTML), set True by _build_pdf_html
    context["pdf_mode"] = False


__all__ = ["_build_html_extras"]
