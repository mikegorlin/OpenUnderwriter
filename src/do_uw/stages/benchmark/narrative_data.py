"""Section data extraction for LLM narrative prompts.

Extracts section-relevant data from AnalysisState as primitive-typed
dicts suitable for JSON serialization and LLM prompt construction.

Per-section extractors live in narrative_data_sections.py (split for
500-line compliance). This module provides the public dispatch API.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.narrative_data_sections import (
    extract_company,
    extract_financial,
    extract_governance,
    extract_litigation,
    extract_market,
)
from do_uw.stages.render.sca_counter import count_active_genuine_scas

logger = logging.getLogger(__name__)


def extract_section_data(
    state: AnalysisState, section_id: str,
) -> dict[str, Any]:
    """Extract section-relevant data from state for LLM prompting.

    Returns a dict of key data points for the given section, serialized
    to primitive types suitable for JSON.
    """
    data: dict[str, Any] = {}

    if section_id == "company" and state.company:
        data = extract_company(state)
    elif section_id == "financial" and state.extracted:
        data = extract_financial(state)
    elif section_id == "market" and state.extracted and state.extracted.market:
        data = extract_market(state)
    elif (
        section_id == "governance"
        and state.extracted
        and state.extracted.governance
    ):
        data = extract_governance(state)
    elif (
        section_id == "litigation"
        and state.extracted
        and state.extracted.litigation
    ):
        data = extract_litigation(state)
    elif section_id == "scoring" and state.scoring:
        data = extract_scoring(state)
    elif section_id == "ai_risk" and state.analysis:
        data = extract_ai_risk(state)

    return data


def extract_state_summary(state: AnalysisState) -> dict[str, Any]:
    """Extract high-level state summary for executive thesis."""
    summary: dict[str, Any] = {}
    if state.company:
        identity = state.company.identity
        summary["company"] = (
            identity.legal_name.value if identity.legal_name else state.ticker
        )
        summary["sector"] = (
            str(identity.sector.value) if identity.sector else None
        )
        if state.company.market_cap:
            summary["market_cap"] = float(state.company.market_cap.value)
        if state.company.employee_count:
            summary["employee_count"] = state.company.employee_count.value
    if state.scoring:
        sc = state.scoring
        summary["quality_score"] = sc.quality_score
        summary["composite_score"] = sc.composite_score
        summary["tier"] = sc.tier.tier if sc.tier else None
        summary["tier_action"] = sc.tier.action if sc.tier else None
        if sc.claim_probability:
            summary["claim_band"] = sc.claim_probability.band
            summary["claim_low_pct"] = sc.claim_probability.range_low_pct
            summary["claim_high_pct"] = sc.claim_probability.range_high_pct
        # Top deduction factors
        top_deductions = sorted(
            sc.factor_scores,
            key=lambda f: f.points_deducted,
            reverse=True,
        )[:3]
        summary["top_deductions"] = [
            {"name": f.factor_name, "deducted": f.points_deducted, "max": f.max_points}
            for f in top_deductions
            if f.points_deducted > 0
        ]
    if state.benchmark and state.benchmark.inherent_risk:
        ir = state.benchmark.inherent_risk
        summary["inherent_risk_pct"] = ir.company_adjusted_rate_pct
    if state.executive_summary and state.executive_summary.key_findings:
        kf = state.executive_summary.key_findings
        summary["negative_count"] = len(kf.negatives)
        summary["positive_count"] = len(kf.positives)
        summary["negatives"] = [str(n) for n in kf.negatives[:5]]
        summary["positives"] = [str(p) for p in kf.positives[:5]]
    return summary


def extract_findings(state: AnalysisState) -> dict[str, Any]:
    """Extract key findings for meeting prep question generation."""
    findings: dict[str, Any] = {}
    if state.scoring:
        sc = state.scoring
        findings["tier"] = sc.tier.tier if sc.tier else None
        top_factors = sorted(
            sc.factor_scores,
            key=lambda f: f.points_deducted,
            reverse=True,
        )[:5]
        findings["risk_factors"] = [
            {"name": f.factor_name, "deducted": f.points_deducted}
            for f in top_factors
            if f.points_deducted > 0
        ]
        triggered_flags = [f for f in sc.red_flags if f.triggered]
        findings["red_flags"] = [
            f.flag_name or f.flag_id for f in triggered_flags
        ]
    if state.extracted and state.extracted.litigation:
        # Use canonical SCA counter to exclude DOJ_FCPA and regulatory cases
        findings["active_scas"] = count_active_genuine_scas(state)
    if state.extracted and state.extracted.governance:
        gov = state.extracted.governance
        if gov.board.ceo_chair_duality and gov.board.ceo_chair_duality.value:
            findings["ceo_chair_duality"] = True

    # --- Company-specific context for sector-aware questions ---
    if state.company:
        co = state.company
        if co.identity.legal_name:
            findings["company_name"] = co.identity.legal_name.value
        if co.identity.sic_description:
            findings["sic_description"] = co.identity.sic_description.value
        if co.years_public and co.years_public.value is not None:
            if co.years_public.value <= 3:
                findings["ipo_recent"] = co.years_public.value

    # --- 10-K sector context (regulatory, geographic, related party) ---
    if state.acquired_data and state.acquired_data.llm_extractions:
        llm = state.acquired_data.llm_extractions
        for key in sorted(llm.keys(), reverse=True):
            if not key.startswith("10-K:"):
                continue
            ten_k = llm[key] if isinstance(llm[key], dict) else {}
            if not ten_k:
                continue
            # Regulatory environment (critical for TIC, pharma, banking)
            reg = ten_k.get("regulatory_environment", "")
            if reg:
                findings["regulatory_environment"] = str(reg)[:300]
            # Related party transactions (governance concern)
            rpt = ten_k.get("related_party_transactions", [])
            if isinstance(rpt, list) and rpt:
                findings["related_party_transactions"] = [str(r)[:150] for r in rpt[:3]]
            # Key financial concerns (from management)
            concerns = ten_k.get("key_financial_concerns", [])
            if isinstance(concerns, list) and concerns:
                findings["management_concerns"] = [str(c)[:100] for c in concerns[:3]]
            # Active litigation from 10-K
            procs = ten_k.get("legal_proceedings", [])
            if isinstance(procs, list):
                for p in procs:
                    if isinstance(p, dict) and p.get("status") == "ACTIVE":
                        findings["active_10k_lawsuit"] = {
                            "case": p.get("case_name", "")[:100],
                            "allegations": p.get("allegations", "")[:200],
                        }
                        break
            # Geographic concentration
            geo = ten_k.get("geographic_regions", [])
            if isinstance(geo, list) and len(geo) >= 2:
                findings["geographic_concentration"] = [str(g)[:80] for g in geo[:3]]
            # Dual class / ownership structure
            if ten_k.get("is_dual_class"):
                findings["dual_class"] = True
            break  # Only use most recent 10-K

    return findings


# ---------------------------------------------------------------------------
# Scoring and AI risk extractors (kept here to keep
# narrative_data_sections.py under 500 lines)
# ---------------------------------------------------------------------------
def extract_scoring(state: AnalysisState) -> dict[str, Any]:
    """Extract scoring data for LLM narrative prompt."""
    data: dict[str, Any] = {}
    if not state.scoring:
        return data
    if state.company and state.company.identity.legal_name:
        data["company_name"] = state.company.identity.legal_name.value
    sc = state.scoring
    data["quality_score"] = sc.quality_score
    data["composite_score"] = sc.composite_score
    data["tier"] = sc.tier.tier if sc.tier else None
    data["tier_action"] = sc.tier.action if sc.tier else None
    if sc.tier and sc.tier.probability_range:
        data["tier_probability_range"] = sc.tier.probability_range
    if sc.claim_probability:
        data["claim_band"] = sc.claim_probability.band
        data["claim_range_low"] = sc.claim_probability.range_low_pct
        data["claim_range_high"] = sc.claim_probability.range_high_pct
    if sc.factor_scores:
        all_factors = sorted(
            sc.factor_scores,
            key=lambda f: f.points_deducted,
            reverse=True,
        )
        data["top_risk_factors"] = [
            {
                "name": f.factor_name, "id": f.factor_id,
                "deducted": f.points_deducted, "max": f.max_points,
                "evidence": f.evidence[:3],
            }
            for f in all_factors[:5]
            if f.points_deducted > 0
        ]
        data["total_deductions"] = sum(
            f.points_deducted for f in sc.factor_scores
        )
    triggered_flags = [f for f in sc.red_flags if f.triggered]
    if triggered_flags:
        data["red_flags"] = [
            {"name": f.flag_name or f.flag_id, "ceiling": f.ceiling_applied}
            for f in triggered_flags
        ]
    if sc.binding_ceiling_id:
        data["binding_ceiling"] = sc.binding_ceiling_id
    active_patterns = [p for p in sc.patterns_detected if p.detected]
    if active_patterns:
        data["active_patterns"] = [
            p.pattern_name or p.pattern_id for p in active_patterns
        ]
    return data


def extract_ai_risk(state: AnalysisState) -> dict[str, Any]:
    """Extract AI risk section data."""
    data: dict[str, Any] = {}
    ai = getattr(state, "ai_risk", None)
    if ai:
        data["overall_score"] = getattr(ai, "overall_score", None)
        data["overall_threat"] = getattr(ai, "overall_threat", None)
    return data
