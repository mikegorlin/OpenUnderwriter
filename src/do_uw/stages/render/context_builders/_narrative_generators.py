"""State-aware D&O implication generators (Phase 119.1-02).

Each generator reads from AnalysisState and returns company-specific
D&O commentary text, or None if the condition lacks data to produce
meaningful text. Replaces the static _DO_IMPLICATIONS_MAP.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from do_uw.models.state import AnalysisState


# ---------------------------------------------------------------------------
# Helper: safe extraction of financial metrics from state
# ---------------------------------------------------------------------------

def _sv(val: Any) -> Any:
    """Extract .value from SourcedValue or return raw value."""
    return getattr(val, "value", val)


def _get_distress(state: AnalysisState) -> dict[str, Any]:
    """Extract distress indicators from state as a flat dict."""
    result: dict[str, Any] = {}
    fin = getattr(getattr(state, "extracted", None), "financials", None)
    if not fin:
        return result
    d = getattr(fin, "distress", None)
    if d:
        az = getattr(d, "altman_z_score", None)
        if az:
            result["altman_z"] = az.score
            result["altman_zone"] = str(az.zone) if az.zone else ""
        pf = getattr(d, "piotroski_f_score", None)
        if pf:
            result["piotroski"] = pf.score
    audit = getattr(fin, "audit", None)
    if audit:
        gc = getattr(audit, "going_concern", None)
        if gc:
            result["going_concern"] = _sv(gc)
    lev = getattr(fin, "leverage", None)
    if lev:
        lev_val = _sv(lev)
        if isinstance(lev_val, dict):
            result["debt_to_equity"] = lev_val.get("debt_to_equity")
            result["interest_coverage"] = lev_val.get("interest_coverage")
    liq = getattr(fin, "liquidity", None)
    if liq:
        liq_val = _sv(liq)
        if isinstance(liq_val, dict):
            result["current_ratio"] = liq_val.get("current_ratio")
    return result


def _get_market(state: AnalysisState) -> dict[str, Any]:
    """Extract market data from state."""
    result: dict[str, Any] = {}
    mkt = getattr(getattr(state, "extracted", None), "market", None)
    if not mkt:
        return result
    stock = getattr(mkt, "stock", None)
    if stock:
        decline = getattr(stock, "decline_from_high_pct", None)
        if decline:
            result["decline_pct"] = _sv(decline)
        vol = getattr(stock, "volatility_90d", None)
        if vol:
            result["volatility_90d"] = _sv(vol)
    si = getattr(mkt, "short_interest", None)
    if si:
        short_pct = getattr(si, "short_pct_shares_out", None)
        if short_pct:
            result["short_pct"] = _sv(short_pct)
    return result


def _get_litigation(state: AnalysisState) -> dict[str, Any]:
    """Extract litigation data from state.

    Counts only ACTIVE *genuine* securities class actions — excludes
    non-securities cases (environmental, product liability, etc.) that
    the LLM extractor placed in the SCA list. Uses the same filter
    as section_assessments.py and red_flag_gates.py for consistency.
    """
    result: dict[str, Any] = {}
    lit = getattr(getattr(state, "extracted", None), "litigation", None)
    if not lit:
        return result
    sca = getattr(lit, "securities_class_actions", None)
    if sca:
        from do_uw.stages.render.sca_counter import get_active_genuine_scas

        active_scas = get_active_genuine_scas(state)
        result["sca_count"] = len(active_scas)
        result["sca_total"] = len(sca)  # total including settled/dismissed/non-SCA
        result["sca_names"] = [str(_sv(getattr(c, "case_name", ""))) or "" for c in active_scas[:3]]
    deriv = getattr(lit, "derivative_suits", None)
    if deriv:
        result["derivative_count"] = len(deriv)
    reg = getattr(lit, "regulatory_proceedings", None)
    if reg:
        result["regulatory_count"] = len(reg)
    return result


def _get_scoring(state: AnalysisState) -> dict[str, Any]:
    """Extract scoring data from state."""
    result: dict[str, Any] = {}
    if not state.scoring:
        return result
    result["score"] = state.scoring.quality_score
    tier = getattr(state.scoring, "tier", None)
    if tier:
        result["tier"] = str(tier.tier.value)
    factors = getattr(state.scoring, "factor_scores", None) or []
    if factors:
        worst = max(factors, key=lambda f: f.points_deducted)
        result["worst_factor_id"] = worst.factor_id
        result["worst_factor_name"] = worst.factor_name
        result["worst_factor_pts"] = worst.points_deducted
        result["worst_factor_max"] = worst.max_points
    return result


# ---------------------------------------------------------------------------
# State-aware implication generators
# ---------------------------------------------------------------------------

def _gen_tier_implication(state: AnalysisState) -> str | None:
    """Generate tier-based D&O implication with score details."""
    s = _get_scoring(state)
    if not s:
        return None
    tier = s.get("tier", "")
    score = s.get("score", 0)
    wf = s.get("worst_factor_name", "unknown")
    wf_id = s.get("worst_factor_id", "")
    wf_pts = s.get("worst_factor_pts", 0)
    wf_max = s.get("worst_factor_max", 0)
    return (
        f"Overall {tier} classification (score: {score:.0f}/100) driven primarily by "
        f"{wf} ({wf_id}: {wf_pts:.0f}/{wf_max} deducted). "
        f"Consider excess layer attachment points appropriate for {tier}-tier risk."
    )


def _gen_negative_findings_implication(state: AnalysisState) -> str | None:
    """Generate negative findings implication with actual finding count."""
    if not state.executive_summary or not state.executive_summary.key_findings:
        return None
    negs = state.executive_summary.key_findings.negatives or []
    if not negs:
        return None
    count = len(negs)
    first_finding = negs[0] if negs else None
    first = getattr(first_finding, "evidence_narrative", str(first_finding)) if first_finding else ""
    return (
        f"{count} negative finding(s) identified. Lead concern: {first}. "
        f"Securities class action or derivative suit exposure warrants review."
    )


def _gen_distress_implication(state: AnalysisState) -> str | None:
    """Generate distress implication based on actual Altman Z, D/E, going concern."""
    d = _get_distress(state)
    z = d.get("altman_z")
    de = d.get("debt_to_equity")
    gc = d.get("going_concern")
    if z is None and de is None and not gc:
        return (
            "Financial distress indicators detected. D&O exposure assessment "
            "should evaluate creditor-oriented claim theories."
        )

    parts: list[str] = []
    if gc:
        parts.append(
            "Going concern qualification places company in Zone of Insolvency "
            "where fiduciary duties expand to include creditors, creating "
            "derivative suit exposure for directors."
        )
        metrics = []
        if z is not None:
            metrics.append(f"Altman Z-Score of {z:.2f}")
        if de is not None:
            metrics.append(f"D/E at {de:.1f}x")
        if metrics:
            parts.append(" with ".join(metrics) + ".")
    elif z is not None and z < 1.81:
        parts.append(f"Altman Z-Score of {z:.2f} (distress zone) ")
        if de is not None:
            parts.append(f"with D/E of {de:.1f}x ")
        parts.append(
            "signals covenant pressure risk. D&O exposure shifts from standard "
            "securities fraud theories toward creditor-oriented claims."
        )
    elif z is not None and z < 2.99:
        parts.append(f"Altman Z-Score of {z:.2f} (grey zone) warrants monitoring. ")
        if de is not None:
            parts.append(f"Current leverage at {de:.1f}x D/E is manageable but ")
        parts.append("deterioration would accelerate D&O claim probability.")
    elif z is not None:
        parts.append(f"Altman Z-Score of {z:.2f} indicates strong financial position. ")
        if de is not None:
            parts.append(f"Leverage at {de:.1f}x D/E. ")
        parts.append(
            "Standard securities fraud theories remain primary D&O exposure vector."
        )
    return "".join(parts)


def _gen_restatement_implication(state: AnalysisState) -> str | None:
    """Generate restatement risk implication.

    Only generates text when there is positive evidence of restatement or
    material weakness. Does NOT fire on Beneish M-Score or other accounting
    quality indicators alone — those have their own earnings_quality generator.
    """
    fin = getattr(getattr(state, "extracted", None), "financials", None)
    audit = getattr(fin, "audit", None) if fin else None

    # Check actual restatements first
    restatements = getattr(audit, "restatements", None) or [] if audit else []
    if restatements:
        return (
            f"{len(restatements)} financial restatement(s) disclosed. "
            f"Restatement risk directly triggers D&O Side A/B/C coverage and "
            f"strengthens Section 10(b) scienter allegations."
        )

    # Check material weaknesses
    mw = getattr(audit, "material_weaknesses", None) or [] if audit else []
    mw_count = len(mw)
    if mw_count > 0:
        return (
            f"{mw_count} material weakness(es) in internal controls identified. "
            f"Restatement risk directly triggers D&O Side A/B/C coverage and "
            f"strengthens Section 10(b) scienter allegations."
        )

    # No positive evidence of restatement — do not generate generic commentary
    return None


def _gen_earnings_quality_implication(state: AnalysisState) -> str | None:
    """Generate earnings quality implication with Beneish M-Score if available."""
    fin = getattr(getattr(state, "extracted", None), "financials", None)
    d = getattr(fin, "distress", None) if fin else None
    beneish = getattr(d, "beneish_m_score", None) if d else None
    if beneish and beneish.score is not None:
        m = beneish.score
        if m > -1.78:
            return (
                f"Beneish M-Score of {m:.2f} (above -1.78 threshold) suggests "
                f"elevated earnings manipulation risk. Supports 10b-5 materiality "
                f"arguments in potential securities litigation."
            )
        return (
            f"Beneish M-Score of {m:.2f} (below -1.78 threshold) does not "
            f"indicate earnings manipulation. Earnings quality risk is low."
        )
    return "Earnings quality concerns detected that may support 10b-5 materiality arguments."


def _gen_board_independence_implication(state: AnalysisState) -> str | None:
    """Generate board independence implication."""
    gov = getattr(getattr(state, "extracted", None), "governance", None)
    if gov:
        comp = getattr(gov, "board_composition", None)
        if comp:
            ratio = getattr(comp, "independence_ratio", None)
            if ratio and _sv(ratio) is not None:
                pct = _sv(ratio) * 100 if _sv(ratio) <= 1.0 else _sv(ratio)
                if pct < 67:
                    return (
                        f"Board independence at {pct:.0f}% (below 2/3 threshold) "
                        f"may weaken Caremark defense and increase derivative suit exposure."
                    )
                return (
                    f"Board independence at {pct:.0f}% meets governance standards. "
                    f"Caremark defense posture is supported."
                )
    return "Board independence gaps may weaken Caremark defense and increase derivative suit exposure."


def _gen_compensation_implication(state: AnalysisState) -> str | None:
    """Generate compensation excess implication."""
    return "Executive compensation concerns detected that may attract shareholder derivative claims for waste."


def _gen_insider_implication(state: AnalysisState) -> str | None:
    """Generate insider activity implication."""
    return (
        "Insider trading patterns detected that strengthen scienter allegations "
        "in potential securities fraud claims."
    )


def _gen_active_securities_implication(state: AnalysisState) -> str | None:
    """Generate active securities litigation implication with case count.

    Reports SCAs and derivatives separately to avoid conflating different
    litigation types into a single misleading count.
    """
    lit = _get_litigation(state)
    sca_count = lit.get("sca_count", 0)
    deriv_count = lit.get("derivative_count", 0)

    parts: list[str] = []
    names = lit.get("sca_names", [])
    name_text = f" ({', '.join(n for n in names if n)})" if any(names) else ""

    if sca_count > 0:
        parts.append(f"{sca_count} active securities class action(s){name_text}")
    if deriv_count > 0:
        parts.append(f"{deriv_count} derivative suit(s)")

    if parts:
        return (
            f"{'. '.join(parts)}. "
            f"Prior suits directly impact D&O loss history and future insurability. "
            f"Review retention levels and pending litigation exclusion dates."
        )
    return "Active securities litigation indicators detected impacting D&O loss history."


def _gen_regulatory_implication(state: AnalysisState) -> str | None:
    """Generate regulatory action implication."""
    lit = _get_litigation(state)
    reg_count = lit.get("regulatory_count", 0)
    if reg_count > 0:
        return (
            f"{reg_count} regulatory enforcement action(s) identified. "
            f"May trigger Side A coverage for individual director defense costs."
        )
    return "Regulatory enforcement indicators may trigger Side A coverage for individual director defense."


def _gen_settlement_implication(state: AnalysisState) -> str | None:
    """Generate settlement history implication."""
    return "Prior settlement patterns should inform expected claim severity and reserve requirements."


def _gen_stock_volatility_implication(state: AnalysisState) -> str | None:
    """Generate stock volatility implication with actual decline data."""
    mkt = _get_market(state)
    decline = mkt.get("decline_pct")
    vol = mkt.get("volatility_90d")
    parts: list[str] = []
    if decline is not None:
        parts.append(f"Stock decline of {abs(decline):.1f}% from 52-week high")
    if vol is not None:
        parts.append(f"90-day volatility at {vol:.1f}%")
    if parts:
        return (
            f"{'; '.join(parts)}. Elevated volatility increases probability of "
            f"event-driven securities class actions and DDL exposure."
        )
    return "Elevated stock volatility increases event-driven securities class action probability."


def _gen_short_interest_implication(state: AnalysisState) -> str | None:
    """Generate short interest implication."""
    mkt = _get_market(state)
    short_pct = mkt.get("short_pct")
    if short_pct is not None:
        return (
            f"Short interest at {short_pct:.1f}% of shares outstanding signals "
            f"market skepticism that may presage disclosure-related claims."
        )
    return "Elevated short interest signals market skepticism and potential disclosure-related claims."


def _gen_peril_implication(state: AnalysisState) -> str | None:
    """Generate peril score implication."""
    s = _get_scoring(state)
    score = s.get("score")
    if score is not None:
        return (
            f"Overall quality score of {score:.0f}/100 indicates elevated D&O "
            f"claim probability across multiple allegation theories."
        )
    return "High peril scores indicate elevated D&O claim probability across multiple allegation theories."


def _gen_hazard_implication(state: AnalysisState) -> str | None:
    """Generate hazard amplification implication."""
    return (
        "Hazard interaction effects detected that may amplify claim severity "
        "beyond individual factor assessment."
    )


def _gen_regulatory_heavy_implication(state: AnalysisState) -> str | None:
    """Generate regulatory-heavy industry implication."""
    return "Regulatory-intensive industry increases compliance-related D&O exposure."


def _gen_international_implication(state: AnalysisState) -> str | None:
    """Generate international operations implication."""
    return (
        "International operations introduce foreign jurisdiction D&O risk "
        "and varying director liability standards."
    )


def _gen_concentration_implication(state: AnalysisState) -> str | None:
    """Generate concentration risk implication."""
    return "Revenue concentration creates event-driven claim risk if key customer/segment deteriorates."


def _gen_analyst_implication(state: AnalysisState) -> str | None:
    """Generate analyst downgrade implication."""
    return "Analyst consensus shifts may correlate with corrective disclosure timing."


def _gen_ai_exposure_implication(state: AnalysisState) -> str | None:
    """Generate AI exposure implication."""
    return (
        "AI/technology governance gaps may create emerging D&O liability "
        "under evolving regulatory frameworks."
    )


def _gen_data_privacy_implication(state: AnalysisState) -> str | None:
    """Generate data privacy implication."""
    return (
        "Data privacy and cybersecurity exposure increasingly triggers D&O "
        "claims via regulatory and shareholder actions."
    )


# ---------------------------------------------------------------------------
# Generator registry: condition_key -> generator function
# ---------------------------------------------------------------------------

IMPLICATION_GENERATORS: dict[str, Callable[[AnalysisState], str | None]] = {
    "tier_high": _gen_tier_implication,
    "negative_findings": _gen_negative_findings_implication,
    "distress_indicators": _gen_distress_implication,
    "restatement_risk": _gen_restatement_implication,
    "earnings_quality": _gen_earnings_quality_implication,
    "board_independence": _gen_board_independence_implication,
    "compensation_excess": _gen_compensation_implication,
    "insider_activity": _gen_insider_implication,
    "active_securities": _gen_active_securities_implication,
    "regulatory_action": _gen_regulatory_implication,
    "settlement_history": _gen_settlement_implication,
    "stock_volatility": _gen_stock_volatility_implication,
    "short_interest": _gen_short_interest_implication,
    "high_peril": _gen_peril_implication,
    "hazard_amplification": _gen_hazard_implication,
    "regulatory_heavy": _gen_regulatory_heavy_implication,
    "international_ops": _gen_international_implication,
    "concentration_risk": _gen_concentration_implication,
    "analyst_downgrades": _gen_analyst_implication,
    "ai_exposure": _gen_ai_exposure_implication,
    "data_privacy": _gen_data_privacy_implication,
}

# ---------------------------------------------------------------------------
# Registry: section -> list of (condition_key, severity)
# ---------------------------------------------------------------------------

DO_IMPLICATIONS_REGISTRY: dict[str, list[tuple[str, str]]] = {
    "executive_summary": [
        ("tier_high", "HIGH"),
        ("negative_findings", "MEDIUM"),
    ],
    "business_profile": [
        ("regulatory_heavy", "MEDIUM"),
        ("international_ops", "LOW"),
        ("concentration_risk", "MEDIUM"),
    ],
    "financial_health": [
        ("distress_indicators", "HIGH"),
        ("restatement_risk", "HIGH"),
        ("earnings_quality", "MEDIUM"),
    ],
    "governance": [
        ("board_independence", "MEDIUM"),
        ("compensation_excess", "MEDIUM"),
        ("insider_activity", "HIGH"),
    ],
    "litigation": [
        ("active_securities", "HIGH"),
        ("regulatory_action", "HIGH"),
        ("settlement_history", "MEDIUM"),
    ],
    "market_activity": [
        ("stock_volatility", "MEDIUM"),
        ("short_interest", "MEDIUM"),
        ("analyst_downgrades", "LOW"),
    ],
    "scoring": [
        ("high_peril", "HIGH"),
        ("hazard_amplification", "MEDIUM"),
    ],
    "ai_risk": [
        ("ai_exposure", "MEDIUM"),
        ("data_privacy", "MEDIUM"),
    ],
}


# ---------------------------------------------------------------------------
# State-aware coverage notes
# ---------------------------------------------------------------------------

def gen_coverage_note(state: AnalysisState, section_id: str) -> str:
    """Generate coverage note that references actual risk factors present."""
    d = _get_distress(state)
    if section_id == "financial_health":
        gc = d.get("going_concern")
        z = d.get("altman_z")
        if gc:
            return (
                "Financial condition exclusion and insolvency provisions are critical. "
                "Going concern qualification requires immediate coverage review."
            )
        if z is not None and z < 1.81:
            return (
                "Evaluate financial condition exclusion applicability. "
                "Distress indicators warrant insolvency provision review."
            )
        if z is not None and z < 2.99:
            return (
                "Monitor financial condition exclusion. Grey zone indicators "
                "may warrant enhanced coverage terms at renewal."
            )
        return "Financial condition exclusion review recommended as part of standard coverage assessment."

    if section_id == "litigation":
        lit = _get_litigation(state)
        sca = lit.get("sca_count", 0)
        if sca > 0:
            return (
                f"Review prior/pending litigation exclusion dates and related claims provisions. "
                f"{sca} active securities action(s) require retention level assessment."
            )
        return "Review prior/pending litigation exclusion dates and related claims provisions."

    if section_id == "executive_summary":
        s = _get_scoring(state)
        tier = s.get("tier", "")
        if tier in ("WALK", "NO_TOUCH"):
            return (
                f"{tier} tier: Side A, B, and C coverage adequacy requires "
                f"enhanced review. Consider excess layer restructuring."
            )
        return "Review Side A, B, and C coverage adequacy relative to identified risk factors."

    _STATIC_NOTES: dict[str, str] = {
        "business_profile": "Consider industry-specific endorsements and territorial coverage scope.",
        "governance": "Assess insured-vs-insured exclusion breadth and entity coverage for derivative claims.",
        "market_activity": "Consider market-driven event response coverage and investigation cost sub-limits.",
        "scoring": "Overall risk profile should inform primary and excess layer structure decisions.",
        "ai_risk": "Evaluate technology E&O carve-backs and emerging AI liability endorsements.",
    }
    return _STATIC_NOTES.get(section_id, "")
