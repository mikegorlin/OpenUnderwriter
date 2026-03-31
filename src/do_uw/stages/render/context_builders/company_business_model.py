"""Business model profile context builder.

Extracts revenue model, concentration risk, key person dependency,
segment lifecycle, disruption risk, and segment margins into a
template-ready dict.
"""

from __future__ import annotations

import re
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.context_builders._signal_consumer import (
    signal_to_display_level,
)
from do_uw.stages.render.formatters import (
    format_percentage,
    safe_float,
    sv_val,
)


def extract_business_model(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract business model profile data for template.

    Produces a template-ready dict with all 6 BMOD dimensions:
    revenue model type, concentration risk, key person dependency,
    segment lifecycle, disruption risk, and segment margins.
    """
    prof = state.company
    if prof is None:
        return {}

    # Revenue model type (BMOD-01) — short label only (e.g., "HYBRID"), not full paragraph
    rev_model_raw = sv_val(prof.revenue_model_type, None) if prof.revenue_model_type else None
    if isinstance(rev_model_raw, str) and " - " in rev_model_raw:
        rev_model = rev_model_raw.split(" - ")[0].strip()
    else:
        rev_model = rev_model_raw

    # Concentration risk (BMOD-02) -- composite assessment
    concentration_score = 0
    concentration_flags: list[str] = []
    def _parse_pct(raw: Any) -> float:
        """Safely parse a percentage value that may be a string.

        Handles formats like: 42.8, "42.8%", "$178.4B (42.8%)", "42.8% of revenue".
        When a string contains both a dollar amount and a parenthesized percentage,
        extract the percentage from parentheses — NOT the dollar amount.
        """
        if isinstance(raw, (int, float)):
            return float(raw)
        s = str(raw)
        # First priority: number inside parentheses followed by % — e.g. "(42.8%)"
        m_paren = re.search(r"\((\d+(?:\.\d+)?)%\)", s)
        if m_paren:
            return float(m_paren.group(1))
        # Second priority: number immediately followed by % — e.g. "42.8%"
        m_pct = re.search(r"(\d+(?:\.\d+)?)%", s)
        if m_pct:
            return float(m_pct.group(1))
        # Last resort: first bare number (only if no dollar sign prefix)
        if "$" not in s:
            m_bare = re.search(r"(\d+(?:\.\d+)?)", s)
            if m_bare:
                return float(m_bare.group(1))
        return 0.0

    if prof.revenue_segments:
        max_seg = max(
            (_parse_pct(sv_val(s, {}).get("percentage", sv_val(s, {}).get("pct", 0)) or 0)
             for s in prof.revenue_segments),
            default=0,
        )
        if max_seg > 50:
            concentration_score += 1
            concentration_flags.append(f"Single segment {max_seg:.0f}%")
    if prof.customer_concentration:
        max_cust = max(
            (_parse_pct(sv_val(c, {}).get("revenue_pct", 0) or 0)
             for c in prof.customer_concentration),
            default=0,
        )
        if max_cust > 10:
            concentration_score += 1
            concentration_flags.append(f"Single customer {max_cust:.0f}%")
    if prof.geographic_footprint:
        max_geo = max(
            (_parse_pct(sv_val(g, {}).get("percentage", sv_val(g, {}).get("pct", 0)) or 0)
             for g in prof.geographic_footprint),
            default=0,
        )
        if max_geo > 40:
            concentration_score += 1
            concentration_flags.append(f"Single geography {max_geo:.0f}%")

    concentration_level = (
        "HIGH" if concentration_score >= 3
        else "MODERATE" if concentration_score >= 2
        else "LOW" if concentration_score >= 1
        else "NONE"
    )

    # Enrich with BIZ.CONCENTRATION signals if available
    conc_signals = safe_get_signals_by_prefix(signal_results, "BIZ.CONCENTRATION.")
    for sig in conc_signals:
        if sig.status == "TRIGGERED" and sig.evidence:
            level = signal_to_display_level(sig.status, sig.threshold_level)
            if level == "Critical" and concentration_level != "HIGH":
                concentration_level = "HIGH"

    # Key person (BMOD-03)
    key_person: dict[str, Any] | None = None
    _RISK_SCORE_LABELS = {3: "HIGH", 2: "MODERATE", 1: "LOW", 0: "LOW"}
    if prof.key_person_risk is not None:
        kp = sv_val(prof.key_person_risk, {})
        if isinstance(kp, dict):
            risk_score = kp.get("risk_score", 0)
            key_person = {
                "is_founder_led": kp.get("is_founder_led", False),
                "ceo_tenure_years": kp.get("ceo_tenure_years"),
                "has_succession_plan": kp.get("has_succession_plan"),
                "risk_score": risk_score,
                "risk_level": _RISK_SCORE_LABELS.get(risk_score, "LOW"),
            }

    # Lifecycle (BMOD-04)
    lifecycle: list[dict[str, str]] = []
    for sv_lc in (prof.segment_lifecycle or []):
        lc = sv_val(sv_lc, {})
        if isinstance(lc, dict):
            gr = lc.get("growth_rate")
            lifecycle.append({
                "name": str(lc.get("name", "Unknown")),
                "stage": str(lc.get("stage", "Unknown")),
                "growth_rate": format_percentage(safe_float(gr)) if gr is not None else "N/A",
            })

    # Disruption (BMOD-05)
    disruption: dict[str, Any] | None = None
    if prof.disruption_risk is not None:
        dr = sv_val(prof.disruption_risk, {})
        if isinstance(dr, dict):
            disruption = {
                "level": dr.get("level", "LOW"),
                "threats": dr.get("threats", []),
                "threat_count": dr.get("threat_count", 0),
            }

    # Segment margins (BMOD-06)
    margins: list[dict[str, str]] = []
    for sv_m in (prof.segment_margins or []):
        m = sv_val(sv_m, {})
        if isinstance(m, dict):
            margin = m.get("margin_pct")
            prior = m.get("prior_margin_pct")
            # Only show change_bps when prior is a real value (not 0 or absent)
            prior_valid = prior is not None and safe_float(prior) != 0.0
            change = m.get("change_bps") if prior_valid else None
            margins.append({
                "name": str(m.get("name", "Unknown")),
                "margin": format_percentage(safe_float(margin)) if margin is not None else "N/A",
                "prior_margin": format_percentage(safe_float(prior)) if prior_valid else "N/A",
                "change_bps": str(int(safe_float(change))) if change is not None else "N/A",
            })

    return {
        "revenue_model_type": rev_model,
        "concentration_score": concentration_score,
        "concentration_level": concentration_level,
        "concentration_flags": concentration_flags,
        "key_person": key_person,
        "lifecycle": lifecycle,
        "disruption": disruption,
        "segment_margins": margins,
    }


__all__ = ["extract_business_model"]
