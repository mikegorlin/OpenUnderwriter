"""Dossier context builders: company intelligence, forward risk, credibility, etc.

Registered as a builder in assembly_registry. Phase 128-01.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.assembly_registry import register_builder
from do_uw.stages.render.context_builders.render_audit import build_render_audit_context
from do_uw.stages.render.render_audit import compute_render_audit

logger = logging.getLogger(__name__)


@register_builder
def _build_dossier_context(
    state: AnalysisState,
    context: dict[str, Any],
    chart_dir: Path | None,
) -> None:
    """Add dossier, forward risk, credibility, monitoring, posture, quick screen, and new worksheet builders."""
    signal_results = {}
    if state.analysis and state.analysis.signal_results:
        signal_results = state.analysis.signal_results

    # Forward-Looking Intelligence (Phase 117)
    try:
        from do_uw.stages.render.context_builders.forward_risk_map import (
            extract_forward_risk_map,
        )
        context["forward_risk_map"] = extract_forward_risk_map(state, signal_results)
    except Exception:
        logger.debug("Forward risk map context failed", exc_info=True)
        context["forward_risk_map"] = {"forward_available": False}

    try:
        from do_uw.stages.render.context_builders.credibility_context import (
            extract_credibility,
        )
        context["credibility_data"] = extract_credibility(state, signal_results)
    except Exception:
        logger.debug("Credibility context failed", exc_info=True)
        context["credibility_data"] = {"credibility_available": False}

    try:
        from do_uw.stages.render.context_builders.monitoring_context import (
            extract_monitoring_triggers as _extract_mon,
        )
        context["monitoring_data"] = _extract_mon(state, signal_results)
    except Exception:
        logger.debug("Monitoring triggers context failed", exc_info=True)
        context["monitoring_data"] = {"monitoring_available": False}

    try:
        from do_uw.stages.render.context_builders.posture_context import (
            extract_posture,
        )
        context["posture_data"] = extract_posture(state, signal_results)
        # Enhance posture with LLM-synthesized underwriting recommendation
        try:
            from do_uw.stages.render.context_builders.risk_synthesis import (
                synthesize_uw_framework,
            )
            key_findings = context.get("key_findings")
            synth = synthesize_uw_framework(state, key_findings)
            if synth:
                context["posture_data"]["llm_recommendation"] = synth
        except Exception:
            logger.debug("LLM posture synthesis failed (non-fatal)", exc_info=True)
    except Exception:
        logger.debug("Posture context failed", exc_info=True)
        context["posture_data"] = {"posture_available": False}

    try:
        from do_uw.stages.render.context_builders.quick_screen_context import (
            extract_quick_screen,
        )
        context["quick_screen_data"] = extract_quick_screen(state, signal_results)
    except Exception:
        logger.debug("Quick screen context failed", exc_info=True)
        context["quick_screen_data"] = {"quick_screen_available": False}

    # Company Intelligence Dossier (Phase 118)
    try:
        from do_uw.stages.render.context_builders.dossier_what_company_does import (
            extract_what_company_does,
        )
        context["dossier_what"] = extract_what_company_does(
            state, signal_results=signal_results,
        )
    except Exception:
        logger.debug("Dossier what-company-does context failed", exc_info=True)
        context["dossier_what"] = {"what_company_does_available": False}

    try:
        from do_uw.stages.render.context_builders.dossier_money_flows import (
            extract_money_flows,
        )
        context["dossier_flows"] = extract_money_flows(
            state, signal_results=signal_results,
        )
    except Exception:
        logger.debug("Dossier money flows context failed", exc_info=True)
        context["dossier_flows"] = {"money_flows_available": False}

    try:
        from do_uw.stages.render.context_builders.dossier_revenue_card import (
            extract_revenue_model_card,
        )
        context["dossier_card"] = extract_revenue_model_card(
            state, signal_results=signal_results,
        )
    except Exception:
        logger.debug("Dossier revenue card context failed", exc_info=True)
        context["dossier_card"] = {"revenue_card_available": False}

    try:
        from do_uw.stages.render.context_builders.dossier_segments import (
            extract_revenue_segments,
        )
        context["dossier_segments"] = extract_revenue_segments(
            state, signal_results=signal_results,
        )
    except Exception:
        logger.debug("Dossier segments context failed", exc_info=True)
        context["dossier_segments"] = {"segments_available": False}

    try:
        from do_uw.stages.render.context_builders.dossier_unit_economics import (
            extract_unit_economics,
        )
        context["dossier_unit"] = extract_unit_economics(
            state, signal_results=signal_results,
        )
    except Exception:
        logger.debug("Dossier unit economics context failed", exc_info=True)
        context["dossier_unit"] = {"unit_economics_available": False}

    try:
        from do_uw.stages.render.context_builders.dossier_waterfall import (
            extract_revenue_waterfall,
        )
        context["dossier_waterfall"] = extract_revenue_waterfall(
            state, signal_results=signal_results,
        )
    except Exception:
        logger.debug("Dossier waterfall context failed", exc_info=True)
        context["dossier_waterfall"] = {"waterfall_available": False}

    try:
        from do_uw.stages.render.context_builders.dossier_emerging_risks import (
            extract_emerging_risks,
        )
        context["dossier_risks"] = extract_emerging_risks(
            state, signal_results=signal_results,
        )
    except Exception:
        logger.debug("Dossier emerging risks context failed", exc_info=True)
        context["dossier_risks"] = {"emerging_risks_available": False}

    try:
        from do_uw.stages.render.context_builders.dossier_asc606 import (
            extract_asc_606,
        )
        context["dossier_asc"] = extract_asc_606(
            state, signal_results=signal_results,
        )
    except Exception:
        logger.debug("Dossier ASC 606 context failed", exc_info=True)
        context["dossier_asc"] = {"asc_606_available": False}

    # Phase 119: Stock catalyst + performance summary
    try:
        from do_uw.stages.render.context_builders.stock_catalyst_context import (
            build_stock_catalyst_context,
            build_stock_performance_summary,
        )

        drop_events = context.get("drop_events", [])
        patterns = state.stock_patterns
        drop_narrative = state.drop_narrative
        context.update(build_stock_catalyst_context(
            state, drop_events=drop_events, patterns=patterns,
            drop_narrative=drop_narrative,
        ))
        multi_returns = state.multi_horizon_returns
        analyst_consensus = state.analyst_consensus
        context.update(build_stock_performance_summary(
            state, multi_horizon_returns=multi_returns,
            analyst_consensus=analyst_consensus,
        ))
    except Exception:
        logger.warning("Phase 119: Stock catalyst context builder failed", exc_info=True)

    # Phase 119: Competitive landscape
    try:
        from do_uw.stages.render.context_builders.dossier_competitive import (
            build_competitive_landscape_context,
        )

        context.update(build_competitive_landscape_context(
            state, signal_results=signal_results,
        ))
    except Exception:
        logger.warning("Phase 119: Competitive landscape context builder failed", exc_info=True)

    # Phase 119: Alt data — each builder wrapped individually for resilience (Phase 147)
    try:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_esg_context,
        )
        context.update(build_esg_context(state, signal_results=signal_results))
    except Exception:
        logger.warning("ESG context builder failed, suppressing ESG templates", exc_info=True)
        context["has_esg_data"] = False

    try:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_tariff_context,
        )
        context.update(build_tariff_context(state, signal_results=signal_results))
    except Exception:
        logger.warning("Tariff context builder failed, suppressing tariff templates", exc_info=True)
        context["has_tariff_data"] = False

    try:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_ai_washing_context,
        )
        context.update(build_ai_washing_context(state, signal_results=signal_results))
    except Exception:
        logger.warning("AI-washing context builder failed, suppressing AI templates", exc_info=True)
        context["has_ai_data"] = False

    try:
        from do_uw.stages.render.context_builders.alt_data_context import (
            build_peer_sca_context,
        )
        context.update(build_peer_sca_context(state, signal_results=signal_results))
    except Exception:
        logger.warning("Peer SCA context builder failed, suppressing peer SCA templates", exc_info=True)
        context["has_peer_sca"] = False

    # Render audit: preliminary audit for Data Audit appendix (Phase 92 -- REND-01/REND-02)
    # Also builds unified audit summary merging disposition + render audit (Phase 128-01)
    try:
        state_dict = state.model_dump(mode="python")
        preliminary_audit = compute_render_audit(state_dict, "")
        render_audit_ctx = build_render_audit_context(preliminary_audit)
        context.update(render_audit_ctx)

        # Unified audit: re-call build_audit_context with render_audit for dedup
        from do_uw.stages.render.context_builders.audit import build_audit_context
        disp_summary: dict[str, Any] = {}
        if state.analysis and state.analysis.disposition_summary:
            disp_summary = state.analysis.disposition_summary
        unified_ctx = build_audit_context(disp_summary, render_audit=preliminary_audit)
        # Only merge the unified summary keys (don't overwrite disposition keys)
        if "audit_unified_summary" in unified_ctx:
            context["audit_unified_summary"] = unified_ctx["audit_unified_summary"]
        if "audit_dedup_savings" in unified_ctx:
            context["audit_dedup_savings"] = unified_ctx["audit_dedup_savings"]
    except Exception:
        # Non-fatal -- degrade gracefully if audit computation fails
        logger.debug("Render audit context failed", exc_info=True)
        context.setdefault("audit_excluded_count", 0)
        context.setdefault("audit_unrendered_count", 0)
        context.setdefault("audit_excluded_fields", [])
        context.setdefault("audit_unrendered_fields", [])
        context.setdefault("audit_total_extracted", 0)
        context.setdefault("audit_coverage_pct", 0.0)

    # -- New worksheet context builders (Phase 114) --
    # Each builder is wrapped in try/except for graceful degradation.

    try:
        from do_uw.stages.render.context_builders.key_stats_context import (
            build_key_stats_context,
        )
        context["key_stats"] = build_key_stats_context(
            state, canonical=context.get("_canonical_obj"),
        )
    except Exception:
        logger.debug("Key stats context failed", exc_info=True)
        context["key_stats"] = {"available": False}

    try:
        from do_uw.stages.render.context_builders.scorecard_context import (
            build_scorecard_context,
        )
        context["scorecard"] = build_scorecard_context(
            state, canonical=context.get("_canonical_obj"),
        )
    except Exception:
        logger.debug("Scorecard context failed", exc_info=True)
        context["scorecard"] = {"scorecard_available": False}

    try:
        from do_uw.stages.render.context_builders.ddl_context import (
            build_ddl_context,
        )
        context["ddl"] = build_ddl_context(state)
    except Exception:
        logger.debug("DDL context failed", exc_info=True)
        context["ddl"] = {"available": False}

    try:
        from do_uw.stages.render.context_builders.heatmap_context import (
            build_heatmap_context,
        )
        context["heatmap"] = build_heatmap_context(state)
    except Exception:
        logger.debug("Heatmap context failed", exc_info=True)
        context["heatmap"] = {"heatmap_available": False}

    try:
        from do_uw.stages.render.context_builders.crf_bar_context import (
            build_crf_bar_context,
        )
        context["crf_bar"] = build_crf_bar_context(state)
    except Exception:
        logger.debug("CRF bar context failed", exc_info=True)
        context["crf_bar"] = {"alerts": []}

    try:
        from do_uw.stages.render.context_builders.epistemological_trace import (
            build_epistemological_trace,
        )
        context["epistemological_trace"] = build_epistemological_trace(state)
    except Exception:
        logger.debug("Epistemological trace context failed", exc_info=True)
        context["epistemological_trace"] = {"trace_available": False}

    try:
        from do_uw.stages.render.context_builders.decision_context import (
            build_decision_context,
        )
        context["decision"] = build_decision_context(state)
    except Exception:
        logger.debug("Decision context failed", exc_info=True)
        context["decision"] = {"decision_available": False}

    # Phase 147: Manifest audit — classifies all manifest groups (D-08)
    # Must run AFTER all other builders so context is fully populated
    try:
        from do_uw.stages.render.manifest_audit import build_manifest_audit_context
        audit = build_manifest_audit_context(state, context)
        context.update(audit)
    except Exception:
        logger.debug("Manifest audit context failed", exc_info=True)
        context["manifest_audit"] = {
            "total": 0, "renders": 0, "wired": 0, "suppressed": 0, "groups": {},
        }


__all__ = ["_build_dossier_context"]
