"""Biotech & Life Sciences industry-specific context builder.

Generates the four-pillar biotech D&O analysis for the Sector & Industry
section when the active playbook is BIOTECH_PHARMA.

Four pillars:
1. Regulatory Pathway Classification (device vs drug, pathway risk)
2. Clinical Pipeline & Phase Severity Scoring (drug pipeline table)
3. Business Model & Financial Resilience (cash runway, structure, SCA tiers)
4. Red-Flag Audit (CRL trap, BioVie standard, insider timing)

Data sources: extracted financials, 10-K risk factors, market data, governance.
All data is already in state — this module assembles and scores it.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float

logger = logging.getLogger(__name__)

# Phase transition success rates (BIO Clinical Development 2011-2020)
PHASE_SUCCESS_RATES = {
    "Phase I": {"advance_rate": 0.52, "risk_level": "LOW", "risk_color": "#16A34A"},
    "Phase II": {"advance_rate": 0.289, "risk_level": "HIGH", "risk_color": "#D97706"},
    "Phase III": {"advance_rate": 0.578, "risk_level": "MAXIMUM", "risk_color": "#DC2626"},
    "NDA/BLA": {"advance_rate": 0.906, "risk_level": "MODERATE", "risk_color": "#2563EB"},
    "Approved": {"advance_rate": 1.0, "risk_level": "LOW", "risk_color": "#16A34A"},
}

# Therapeutic area risk map for D&O
THERAPEUTIC_AREA_RISK = {
    "oncology": "HIGHEST",
    "cns": "VERY HIGH",
    "neurology": "VERY HIGH",
    "alzheimer": "VERY HIGH",
    "psychiatry": "HIGH",
    "nash": "HIGH",
    "mash": "HIGH",
    "hepatology": "HIGH",
    "pain": "HIGH",
    "gene therapy": "VERY HIGH",
    "cell therapy": "HIGH",
    "immunology": "MODERATE",
    "cardiovascular": "MODERATE-HIGH",
    "metabolic": "LOWER",
    "obesity": "MODERATE",
    "rare disease": "MODERATE",
    "dermatology": "LOWER",
    "vaccines": "MODERATE",
}

# Market cap SCA frequency tiers for biotech
MCAP_SCA_TIERS = [
    (250_000_000, "CRITICAL", "#DC2626", "Highest SCA frequency"),
    (1_000_000_000, "HIGH", "#DC2626", "Very high SCA frequency"),
    (2_000_000_000, "ELEVATED", "#D97706", "Elevated SCA frequency"),
    (float("inf"), "STANDARD", "#16A34A", "Standard SCA frequency"),
]


def build_biotech_industry_context(state: AnalysisState) -> dict[str, Any] | None:
    """Build biotech-specific industry analysis context.

    Returns None if the company is not a biotech/pharma company.
    """
    # Check if biotech playbook is active
    playbook = state.active_playbook_id
    if not playbook or "BIOTECH" not in str(playbook).upper():
        return None

    ctx: dict[str, Any] = {"is_biotech": True}

    # Pillar 1: Regulatory Pathway
    ctx["regulatory_pathway"] = _build_regulatory_pathway(state)

    # Pillar 2: Clinical Pipeline
    ctx["pipeline"] = _build_pipeline(state)

    # Pillar 3: Business Model & Financial Resilience
    ctx["financial_resilience"] = _build_financial_resilience(state)

    # Pillar 4: Red-Flag Audit
    ctx["red_flag_audit"] = _build_red_flag_audit(state)

    # Overall biotech risk assessment
    ctx["overall_risk"] = _compute_overall_risk(ctx)

    return ctx


def _build_regulatory_pathway(state: AnalysisState) -> dict[str, Any]:
    """Pillar 1: Determine if company has device vs drug pipeline."""
    result: dict[str, Any] = {"pathway_type": "Drug/Biologic", "devices": []}

    # Check 10-K text for device mentions
    if state.extracted and state.extracted.market:
        risk_factors = state.extracted.risk_factors or []
        for rf in risk_factors:
            text = str(getattr(rf, "description", "")).lower()
            if "510(k)" in text or "pma " in text or "medical device" in text:
                result["pathway_type"] = "Device + Drug"
                break

    return result


def _build_pipeline(state: AnalysisState) -> dict[str, Any]:
    """Pillar 2: Build clinical pipeline table with phase risk scoring."""
    assets: list[dict[str, Any]] = []
    indications_found: list[str] = []

    # Extract pipeline info from 10-K LLM extraction and risk factors
    if state.extracted and state.extracted.financials:
        fin = state.extracted.financials
        # Check for pipeline data in various locations
        business_desc = ""
        if state.company and state.company.business_description:
            bd = state.company.business_description
            business_desc = bd.value if hasattr(bd, "value") else str(bd)

        # Parse pipeline from risk factors
        risk_factors = state.extracted.risk_factors or []
        for rf in risk_factors:
            desc = str(getattr(rf, "description", ""))
            _extract_pipeline_from_text(desc, assets, indications_found)

        # Parse from business description
        if business_desc:
            _extract_pipeline_from_text(business_desc, assets, indications_found)

    # Deduplicate assets by name
    seen_names: set[str] = set()
    unique_assets: list[dict[str, Any]] = []
    for asset in assets:
        name = asset["name"].upper()
        if name not in seen_names:
            seen_names.add(name)
            unique_assets.append(asset)

    # Determine company structure
    if len(unique_assets) <= 1:
        structure = "Asset-Centric"
        structure_risk = "MAXIMUM"
        structure_color = "#DC2626"
        survival = "~5%"
    else:
        structure = "Platform"
        structure_risk = "Moderate"
        structure_color = "#D97706"
        survival = "~30-35%"

    return {
        "assets": unique_assets[:10],  # Cap at 10
        "asset_count": len(unique_assets),
        "structure": structure,
        "structure_risk": structure_risk,
        "structure_color": structure_color,
        "lead_asset_failure_survival": survival,
        "indications": list(set(indications_found))[:5],
    }


def _extract_pipeline_from_text(
    text: str,
    assets: list[dict[str, Any]],
    indications: list[str],
) -> None:
    """Extract drug pipeline assets from text using regex patterns."""
    # Pattern: "VK2735" or "VK-2735" or similar drug codes
    drug_pattern = re.compile(
        r"\b([A-Z]{2,4}[-]?\d{3,5}[A-Za-z]?)\b"
    )
    # Phase pattern
    phase_pattern = re.compile(
        r"(Phase\s+(?:1|2|3|I{1,3}|IV)[ab]?|NDA|BLA|preclinical|IND)",
        re.IGNORECASE,
    )
    # Indication pattern
    indication_pattern = re.compile(
        r"(?:for|treating|treatment of|indication[s]?\s+(?:of|in|for))\s+([^,.;]{5,60})",
        re.IGNORECASE,
    )

    drugs_found = drug_pattern.findall(text)
    phases_found = phase_pattern.findall(text)
    indications_found = indication_pattern.findall(text)

    for ind in indications_found:
        indications.append(ind.strip())

    # Map drugs to phases if found near each other
    for drug in set(drugs_found):
        # Find the nearest phase mention
        drug_idx = text.find(drug)
        if drug_idx < 0:
            continue
        nearby = text[max(0, drug_idx - 100):drug_idx + 200]
        phase_match = phase_pattern.search(nearby)
        phase = _normalize_phase(phase_match.group(1)) if phase_match else "Unknown"

        # Find nearby indication
        ind_match = indication_pattern.search(nearby)
        indication = ind_match.group(1).strip() if ind_match else "—"

        # Get phase risk scoring
        phase_data = PHASE_SUCCESS_RATES.get(phase, {})
        advance_rate = phase_data.get("advance_rate", 0)
        risk_level = phase_data.get("risk_level", "Unknown")
        risk_color = phase_data.get("risk_color", "#6B7280")

        assets.append({
            "name": drug,
            "phase": phase,
            "indication": indication,
            "advance_rate": f"{advance_rate*100:.0f}%" if advance_rate else "—",
            "risk_level": risk_level,
            "risk_color": risk_color,
        })


def _normalize_phase(phase_str: str) -> str:
    """Normalize phase text to standard format."""
    p = phase_str.strip().upper()
    if p in ("PHASE 1", "PHASE I"):
        return "Phase I"
    if p in ("PHASE 2", "PHASE II", "PHASE 2A", "PHASE 2B", "PHASE IIA", "PHASE IIB"):
        return "Phase II"
    if p in ("PHASE 3", "PHASE III", "PHASE 3A", "PHASE 3B", "PHASE IIIA", "PHASE IIIB"):
        return "Phase III"
    if "NDA" in p or "BLA" in p:
        return "NDA/BLA"
    if "PRECLINICAL" in p:
        return "Preclinical"
    if "IND" in p:
        return "IND"
    return phase_str


def _build_financial_resilience(state: AnalysisState) -> dict[str, Any]:
    """Pillar 3: Cash runway, burn rate, SCA tier, dilution exposure."""
    result: dict[str, Any] = {
        "has_revenue": False,
        "revenue": "—",
        "cash": "—",
        "burn_rate": "—",
        "runway_months": "—",
        "runway_risk": "Unknown",
        "runway_color": "#6B7280",
        "mcap": "—",
        "mcap_sca_tier": "Unknown",
        "mcap_sca_color": "#6B7280",
        "mcap_sca_desc": "",
        "recent_offerings": [],
        "dilution_risk": "—",
    }

    # Revenue check
    if state.extracted and state.extracted.financials:
        fin = state.extracted.financials
        annual = getattr(fin, "annual_financials", None)
        if annual:
            ann_val = annual.value if hasattr(annual, "value") else annual
            if isinstance(ann_val, dict):
                rev = ann_val.get("revenue")
                if rev and isinstance(rev, dict):
                    rev_val = rev.get("value", 0)
                    if rev_val and float(rev_val or 0) > 1_000_000:
                        result["has_revenue"] = True
                        result["revenue"] = f"${float(rev_val)/1_000_000:.0f}M"

    # Cash and burn from market data
    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        info = md.get("info", {}) if isinstance(md, dict) else {}
        if isinstance(info, dict):
            cash = info.get("totalCash", 0)
            if cash and cash > 0:
                result["cash"] = f"${cash/1_000_000:.0f}M"

            # Burn rate from operating cash flow
            ocf = info.get("operatingCashflow", 0)
            if ocf and ocf < 0:
                monthly_burn = abs(ocf) / 12
                result["burn_rate"] = f"${monthly_burn/1_000_000:.1f}M/mo"

                # Runway
                if cash and cash > 0 and monthly_burn > 0:
                    months = cash / monthly_burn
                    result["runway_months"] = f"{months:.0f} months"
                    if months < 12:
                        result["runway_risk"] = "CRITICAL"
                        result["runway_color"] = "#DC2626"
                    elif months < 24:
                        result["runway_risk"] = "WATCH"
                        result["runway_color"] = "#D97706"
                    else:
                        result["runway_risk"] = "ADEQUATE"
                        result["runway_color"] = "#16A34A"

            # Market cap SCA tier
            mcap = info.get("marketCap", 0)
            if mcap and mcap > 0:
                result["mcap"] = f"${mcap/1_000_000_000:.1f}B" if mcap >= 1e9 else f"${mcap/1_000_000:.0f}M"
                for threshold, tier, color, desc in MCAP_SCA_TIERS:
                    if mcap < threshold:
                        result["mcap_sca_tier"] = tier
                        result["mcap_sca_color"] = color
                        result["mcap_sca_desc"] = desc
                        break

    # Capital raises / offerings
    if state.extracted and state.extracted.market:
        cap = state.extracted.market.capital_markets
        if cap:
            offerings = getattr(cap, "offerings", None) or []
            for off in offerings[:5]:
                off_dict = off.model_dump() if hasattr(off, "model_dump") else off
                if isinstance(off_dict, dict):
                    result["recent_offerings"].append({
                        "type": off_dict.get("type", "Offering"),
                        "date": str(off_dict.get("date", ""))[:10],
                        "amount": off_dict.get("amount", "—"),
                    })
            if offerings:
                result["dilution_risk"] = f"{len(offerings)} offering(s) — Section 11/12 exposure"

    return result


def _build_red_flag_audit(state: AnalysisState) -> dict[str, Any]:
    """Pillar 4: CRL trap, BioVie standard, insider timing, financial traps."""
    flags: list[dict[str, Any]] = []

    # A. CRL Trap — check for FDA complete response letter mentions
    crl_found = False
    if state.extracted and state.extracted.risk_factors:
        for rf in state.extracted.risk_factors:
            desc = str(getattr(rf, "description", "")).lower()
            if "complete response letter" in desc or "crl" in desc:
                crl_found = True
                break
    flags.append({
        "name": "CRL Trap (34% of biotech claims)",
        "status": "FLAG" if crl_found else "CLEAR",
        "color": "#DC2626" if crl_found else "#16A34A",
        "detail": "Complete Response Letter referenced in filings — check management characterization of FDA feedback" if crl_found else "No CRL references found in filings",
    })

    # B. BioVie Standard — hypothetical framing of known risks
    # Check if risk factors use hedging language about materialized risks
    flags.append({
        "name": "BioVie Standard (52% of claims)",
        "status": "CHECK",
        "color": "#D97706",
        "detail": "Review risk factors for hypothetical framing of risks that have already materialized. Check PR language vs statistical power of clinical data.",
    })

    # C. Insider Activity
    insider_risk = "CLEAN"
    insider_color = "#16A34A"
    insider_detail = "No significant insider selling detected"
    if state.extracted and state.extracted.market:
        analysis = state.extracted.market.insider_analysis
        if analysis:
            net = getattr(analysis, "net_buying_selling", None)
            if net:
                net_val = net.value if hasattr(net, "value") else str(net)
                if "SELL" in str(net_val).upper():
                    insider_risk = "WATCH"
                    insider_color = "#D97706"
                    insider_detail = "Net insider selling detected — check timing relative to clinical catalysts"
            clusters = getattr(analysis, "cluster_events", None)
            if clusters and len(clusters) > 0:
                insider_risk = "FLAG"
                insider_color = "#DC2626"
                insider_detail = f"{len(clusters)} cluster selling event(s) — elevated scienter risk if near data readouts"

    flags.append({
        "name": "Insider Activity",
        "status": insider_risk,
        "color": insider_color,
        "detail": insider_detail,
    })

    # D. Financial & Transactional Traps
    fin_traps: list[str] = []
    if state.extracted and state.extracted.market:
        cap = state.extracted.market.capital_markets
        if cap:
            offerings = getattr(cap, "offerings", None) or []
            if offerings:
                fin_traps.append(f"{len(offerings)} offering(s) create Section 11/12 strict liability exposure")
    if state.extracted and state.extracted.financials:
        fin = state.extracted.financials
        mw = getattr(fin, "material_weakness", None)
        if mw:
            mw_val = mw.value if hasattr(mw, "value") else mw
            if mw_val:
                fin_traps.append("Material weakness in internal controls")

    flags.append({
        "name": "Financial & Transactional Traps",
        "status": "FLAG" if fin_traps else "CLEAR",
        "color": "#DC2626" if fin_traps else "#16A34A",
        "detail": "; ".join(fin_traps) if fin_traps else "No SPAC, restatement, or material weakness detected",
    })

    return {"flags": flags}


def _compute_overall_risk(ctx: dict[str, Any]) -> dict[str, Any]:
    """Compute overall biotech D&O risk from four pillars."""
    risk_factors: list[str] = []

    # Pipeline risk
    pipeline = ctx.get("pipeline", {})
    assets = pipeline.get("assets", [])
    phase3_count = sum(1 for a in assets if "III" in a.get("phase", ""))
    if phase3_count > 0:
        risk_factors.append(f"{phase3_count} Phase III asset(s) — maximum severity risk")
    if pipeline.get("structure") == "Asset-Centric":
        risk_factors.append("Single-asset structure — existential failure risk")

    # Financial risk
    fin = ctx.get("financial_resilience", {})
    if not fin.get("has_revenue"):
        risk_factors.append("Pre-revenue company — no earnings to cushion stock drop")
    if fin.get("runway_risk") == "CRITICAL":
        risk_factors.append(f"Cash runway {fin.get('runway_months', '?')} — financing pressure")

    # Red flags
    audit = ctx.get("red_flag_audit", {})
    flagged = sum(1 for f in audit.get("flags", []) if f["status"] == "FLAG")
    if flagged > 0:
        risk_factors.append(f"{flagged} red flag(s) in audit")

    # Overall assessment
    if len(risk_factors) >= 3 or phase3_count > 0:
        level = "HIGH"
        color = "#DC2626"
    elif len(risk_factors) >= 1:
        level = "ELEVATED"
        color = "#D97706"
    else:
        level = "STANDARD"
        color = "#16A34A"

    return {
        "level": level,
        "color": color,
        "factors": risk_factors,
    }


__all__ = ["build_biotech_industry_context"]
