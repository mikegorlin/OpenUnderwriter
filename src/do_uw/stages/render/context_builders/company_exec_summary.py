"""Executive summary context builder.

Extracts executive summary data (tier, thesis, key findings, snapshot,
claim probability, tower recommendation, inherent risk) into a
template-ready dict. Enriches findings with SCA litigation theory
and defense theory mappings (D-11, D-12, D-13).
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_value,
)
from do_uw.stages.render.context_builders._signal_consumer import (
    signal_to_display_level,
)
from do_uw.stages.render.context_builders.company_profile import (
    _get_yfinance_sector,
)
from do_uw.stages.render.formatters import (
    clean_company_name,
    format_currency,
    format_percentage,
)

# ---------------------------------------------------------------------------
# SCA litigation theory mappings (D-11, D-12, D-13)
# Maps finding type keys to named legal theories for underwriter context.
# ---------------------------------------------------------------------------

_SCA_THEORY_MAP: dict[str, str] = {
    "stock_drop": (
        "enables loss causation argument under Section 10(b)/Rule 10b-5 "
        "(Dura Pharmaceuticals standard)"
    ),
    "earnings_miss": (
        "supports scienter inference — management knew or should have "
        "known guidance was unachievable (Tellabs)"
    ),
    "restatement": (
        "dual exposure under Section 10(b) and Section 11 from material "
        "misstatements in filed documents"
    ),
    "insider_selling": (
        "strengthens scienter inference via motive-and-opportunity "
        "doctrine (insider sales during class period)"
    ),
    "going_concern": (
        "invites going-concern allegations under Section 10(b) for "
        "failure to disclose financial distress"
    ),
    "governance_failure": (
        "supports Caremark duty of oversight claim — board failed to "
        "implement adequate reporting systems"
    ),
    "guidance_miss": (
        "weakens PSLRA safe harbor defense — forward-looking statement "
        "made without meaningful cautionary language"
    ),
    "audit_weakness": (
        "creates SOX Section 302/906 exposure from material weakness "
        "in internal controls"
    ),
    "regulatory_action": (
        "establishes corrective disclosure timeline for loss causation "
        "— SEC enforcement as trigger event"
    ),
    "activist_pressure": (
        "may trigger breach of fiduciary duty derivative claims in "
        "response to activist campaign"
    ),
}

_SCA_DEFENSE_MAP: dict[str, str] = {
    "beat_and_raise": (
        "consistent beat-and-raise pattern removes the primary "
        "allegation vector (forward guidance fraud)"
    ),
    "no_sca_history": (
        "clean litigation history reduces recurrence probability "
        "— no prior SCA filing"
    ),
    "strong_controls": (
        "clean SOX assessment eliminates Section 302 exposure and "
        "strengthens 10(b) defense"
    ),
    "high_independence": (
        "strong board independence reduces Caremark derivative claim "
        "viability"
    ),
    "low_insider_selling": (
        "minimal insider sales undermines scienter "
        "motive-and-opportunity inference"
    ),
    "stable_auditor": (
        "long-tenure Big 4 auditor strengthens audit quality defense "
        "in Section 10(b) claims"
    ),
    "market_driven_decline": (
        "stock decline attributable to market/sector factors — loss "
        "causation defense available (Dura Pharmaceuticals)"
    ),
}


def _enrich_with_risk_factors(
    negatives: list[dict[str, str]],
    state: AnalysisState,
) -> list[dict[str, str]]:
    """Supplement exec summary negatives with 10-K risk factor findings.

    Adds HIGH-severity risk factors from the most recent 10-K that aren't
    already represented in the scoring-stage negatives.
    """
    existing_narratives = {n.get("narrative", "").lower()[:50] for n in negatives}

    ten_k_rfs: list[Any] = []
    if state.extracted:
        # Check llm_extractions for 10-K data with risk_factors
        llm_data = getattr(state.extracted, "llm_extractions", None)
        if isinstance(llm_data, dict):
            for key, val in llm_data.items():
                if "10-K" in key and isinstance(val, dict):
                    rfs = val.get("risk_factors", [])
                    if isinstance(rfs, list) and rfs:
                        ten_k_rfs = rfs
                        break

    added = 0
    for rf in ten_k_rfs:
        if not isinstance(rf, dict):
            continue
        sev = rf.get("severity", "MEDIUM")
        title = rf.get("title", "")
        passage = rf.get("source_passage", "")
        category = rf.get("category", "OTHER")

        if sev != "HIGH":
            continue
        if title.lower()[:50] in existing_narratives:
            continue

        narrative = f"{title}: {passage[:200]}" if passage else title
        theory_key = _risk_category_to_theory(category)
        negatives.append({
            "narrative": narrative,
            "section": "10-K Risk Factors",
            "impact": "HIGH",
            "theory": theory_key,
            "sca_theory": _SCA_THEORY_MAP.get(theory_key, ""),
        })
        existing_narratives.add(title.lower()[:50])
        added += 1
        if added >= 5:
            break

    return negatives


def _risk_category_to_theory(category: str) -> str:
    """Map 10-K risk factor category to SCA theory key."""
    return {
        "LITIGATION": "stock_drop",
        "REGULATORY": "regulatory_action",
        "FINANCIAL": "restatement",
        "CYBER": "governance_failure",
        "AI": "stock_drop",
        "ESG": "governance_failure",
        "OPERATIONAL": "guidance_miss",
    }.get(category, "stock_drop")


def extract_exec_summary(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
    canonical: Any | None = None,
) -> dict[str, Any]:
    """Extract executive summary data for template.

    Args:
        state: The analysis state.
        signal_results: Optional pre-computed signal results.
        canonical: Optional CanonicalMetrics object for cross-section consistency.
    """
    es = state.executive_summary
    if es is None:
        return {}

    tier_label: str | None = None
    tier_action: str | None = None
    quality_score: str | None = None
    composite_score: str | None = None
    if state.scoring is not None:
        quality_score = f"{state.scoring.quality_score:.1f}"
        composite_score = f"{state.scoring.composite_score:.1f}"
        if state.scoring.tier is not None:
            tier_label = state.scoring.tier.tier
            tier_action = state.scoring.tier.action or None

    thesis = es.thesis.narrative if es.thesis else None

    negatives: list[dict[str, str]] = []
    positives: list[dict[str, str]] = []
    if es.key_findings is not None:
        for kf in es.key_findings.negatives:
            negatives.append({
                "narrative": kf.evidence_narrative, "section": kf.section_origin,
                "impact": kf.scoring_impact, "theory": kf.theory_mapping,
                "sca_theory": _SCA_THEORY_MAP.get(
                    kf.theory_mapping, kf.theory_mapping or ""
                ),
            })
        for kf in es.key_findings.positives:
            positives.append({
                "narrative": kf.evidence_narrative, "section": kf.section_origin,
                "impact": kf.scoring_impact, "theory": kf.theory_mapping,
                "sca_defense": _SCA_DEFENSE_MAP.get(
                    kf.theory_mapping, kf.theory_mapping or ""
                ),
            })

    # Supplement with 10-K risk factor findings not already in negatives.
    # Scoring-stage findings only cover factor-driven items. 10-K risk
    # factors and investigative analysis findings add company-specific
    # risks the scoring model may miss.
    negatives = _enrich_with_risk_factors(negatives, state)

    snapshot: dict[str, str] | None = None
    if es.snapshot is not None:
        snap = es.snapshot
        # Prefer canonical for cross-section consistency when available
        if canonical is not None:
            snap_exchange = canonical.exchange.formatted if canonical.exchange.raw else (snap.exchange or "N/A")
            snap_market_cap = canonical.market_cap.formatted if canonical.market_cap.raw is not None else format_currency(snap.market_cap.value if snap.market_cap else None, compact=True)
            snap_revenue = canonical.revenue.formatted if canonical.revenue.raw is not None else format_currency(snap.revenue.value if snap.revenue else None, compact=True)
            snap_employees = canonical.employees.formatted if canonical.employees.raw is not None else (f"{snap.employee_count.value:,.0f}" if snap.employee_count else "N/A")
        else:
            snap_exchange = snap.exchange or "N/A"
            snap_market_cap = format_currency(snap.market_cap.value if snap.market_cap else None, compact=True)
            snap_revenue = format_currency(snap.revenue.value if snap.revenue else None, compact=True)
            snap_employees = f"{snap.employee_count.value:,.0f}" if snap.employee_count else "N/A"
        snapshot = {
            "company_name": clean_company_name(snap.company_name) if snap.company_name else "N/A",
            "ticker": snap.ticker,
            "exchange": snap_exchange, "industry": snap.industry or "N/A",
            "market_cap": snap_market_cap,
            "revenue": snap_revenue,
            "employees": snap_employees,
        }
    claim_prob: dict[str, str] | None = None
    if state.scoring and state.scoring.claim_probability:
        cp = state.scoring.claim_probability
        claim_prob = {
            "band": cp.band.value,
            "range": f"{cp.range_low_pct:.1f}% - {cp.range_high_pct:.1f}%",
            "industry_base": format_percentage(cp.industry_base_rate_pct),
        }
    tower: dict[str, str] | None = None
    if state.scoring and state.scoring.tower_recommendation:
        tr = state.scoring.tower_recommendation
        tower = {
            "position": tr.recommended_position.value.replace("_", " ").title(),
            "min_attachment": tr.minimum_attachment or "N/A",
            "side_a": tr.side_a_assessment or "N/A",
        }
    inherent_risk: dict[str, str] | None = None
    if es.inherent_risk is not None:
        risk = es.inherent_risk
        sector_name = risk.sector_name or "N/A"
        yf_sector = _get_yfinance_sector(state)
        if yf_sector:
            sector_name = yf_sector
        elif state.company and state.company.identity:
            ident = state.company.identity
            if ident.sic_code and ident.sic_code.value:
                from do_uw.stages.render.formatters import sector_display_name
                from do_uw.stages.resolve.sec_identity import sic_to_sector

                sector_name = sector_display_name(sic_to_sector(str(ident.sic_code.value)))
        inherent_risk = {
            "sector": sector_name,
            "market_cap_tier": risk.market_cap_tier or "N/A",
            "sector_base_rate": format_percentage(risk.sector_base_rate_pct),
            "adjusted_rate": format_percentage(risk.company_adjusted_rate_pct),
        }

    # Enrich with signal data if available
    _tier_signal = safe_get_result(signal_results, "BIZ.TIER")
    if _tier_signal and _tier_signal.value and tier_label is None:
        tier_label = str(_tier_signal.value)

    return {
        "tier_label": tier_label,
        "tier_action": tier_action,
        "quality_score": quality_score,
        "composite_score": composite_score,
        "thesis": thesis,
        "key_findings": [n["narrative"] for n in negatives],
        "key_findings_detail": negatives,
        "positive_indicators": [p["narrative"] for p in positives],
        "positive_detail": positives,
        "snapshot": snapshot,
        "claim_probability": claim_prob,
        "tower_recommendation": tower,
        "inherent_risk": inherent_risk,
    }


__all__ = ["extract_exec_summary"]
