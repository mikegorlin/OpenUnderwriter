"""Company intelligence context builders for Phase 134.

Six builder functions that format company intelligence data for templates.
Pure data formatters -- no evaluative logic, no D&O commentary generation.
Each function reads from AnalysisState and returns a dict.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState, RiskFactorProfile
from do_uw.stages.render.formatters import safe_float
from do_uw.stages.render.state_paths import (
    get_filings,
    get_regulatory_proceedings,
    get_risk_factors,
    get_ten_k_yoy,
)

logger = logging.getLogger(__name__)

# config/ is at project root (6 parents up from this file)
_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "config"


def build_risk_factor_review(state: AnalysisState) -> dict[str, Any]:
    """Build risk factor review with classification and YoY deltas."""
    risk_factors = get_risk_factors(state)
    if not risk_factors:
        return {"has_risk_factor_review": False}

    from do_uw.stages.extract.risk_factor_classify import classify_risk_factors

    # Build YoY delta lookup
    yoy_changes: dict[str, str] = {}
    ten_k_yoy = get_ten_k_yoy(state)
    if ten_k_yoy:
        for rc in getattr(ten_k_yoy, "risk_factor_changes", None) or []:
            title = rc.get("title", "") if isinstance(rc, dict) else getattr(rc, "title", "")
            change = rc.get("change_type", "") if isinstance(rc, dict) else getattr(rc, "change_type", "")
            if title and change:
                yoy_changes[title.lower()] = change

    classified = classify_risk_factors(risk_factors, None)

    rows: list[dict[str, Any]] = []
    for f in classified:
        rows.append({
            "title": f.title, "classification": f.classification, "severity": f.severity,
            "yoy_delta": _get_yoy_delta(f, yoy_changes), "do_implication": f.do_implication,
            "source_passage": f.source_passage, "category": f.category,
        })

    _co = {"ELEVATED": 0, "NOVEL": 1, "STANDARD": 2}
    _so = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    rows.sort(key=lambda r: (_co.get(r["classification"], 9), _so.get(r["severity"], 9)))

    return {
        "risk_factor_review": rows,
        "has_risk_factor_review": bool(rows),
        "risk_factor_summary": {
            "total": len(rows),
            "novel": sum(1 for r in rows if r["classification"] == "NOVEL"),
            "elevated": sum(1 for r in rows if r["classification"] == "ELEVATED"),
            "high_severity": sum(1 for r in rows if r["severity"] == "HIGH"),
        },
    }


def _get_yoy_delta(factor: RiskFactorProfile, yoy_changes: dict[str, str]) -> str:
    """Determine YoY delta label for a risk factor."""
    title_lower = factor.title.lower()
    if title_lower in yoy_changes:
        change = yoy_changes[title_lower].upper()
        if change in ("NEW", "ADDED"):
            return "Added"
        if change in ("REMOVED", "DELETED"):
            return "Removed"
        if change in ("ESCALATED",):
            return "Escalated"
        if change in ("REORGANIZED",):
            return "Reorganized"
    return "Added" if factor.is_new_this_year else "Unchanged"


def build_peer_sca_contagion(state: AnalysisState) -> dict[str, Any]:
    """Build peer SCA contagion table with peer profiles."""
    peer_tickers: list[str] = []
    peer_names: dict[str, str] = {}
    if state.extracted and state.extracted.financials and state.extracted.financials.peer_group:
        for peer in state.extracted.financials.peer_group.peers[:6]:
            peer_tickers.append(peer.ticker)
            peer_names[peer.ticker] = peer.name

    if not peer_tickers:
        return {"has_peer_sca": True, "peer_sca_records": [],
                "peer_sca_summary": "No peer group available for SCA contagion analysis",
                "peer_profiles": []}

    try:
        from do_uw.stages.acquire.clients.supabase_litigation import query_peer_sca_filings
        sca_records = query_peer_sca_filings(peer_tickers)
    except Exception:
        logger.warning("Peer SCA query failed")
        sca_records = []

    formatted: list[dict[str, Any]] = []
    for rec in sca_records:
        formatted.append({
            "ticker": rec.ticker,
            "company_name": rec.company_name or peer_names.get(rec.ticker, rec.ticker),
            "case_caption": rec.case_caption, "filing_date": rec.filing_date,
            "status": rec.status,
            "settlement_amount_m": f"${rec.settlement_amount_m:.1f}M" if rec.settlement_amount_m is not None else "",
            "allegation_type": rec.allegation_type,
            "is_active": rec.status.lower() in ("active", "pending", "open"),
        })

    sca_by_ticker: dict[str, int] = {}
    for rec in sca_records:
        sca_by_ticker[rec.ticker] = sca_by_ticker.get(rec.ticker, 0) + 1

    profiles: list[dict[str, Any]] = []
    if state.extracted and state.extracted.financials and state.extracted.financials.peer_group:
        for peer in state.extracted.financials.peer_group.peers[:6]:
            mcap = peer.market_cap
            mcap_fmt = ""
            if mcap is not None:
                v = safe_float(mcap)
                mcap_fmt = f"${v / 1e9:.1f}B" if v and v >= 1e9 else (f"${v / 1e6:.0f}M" if v and v >= 1e6 else "")
            profiles.append({"ticker": peer.ticker, "name": peer.name, "market_cap_fmt": mcap_fmt,
                             "industry": peer.industry or "", "sca_count": sca_by_ticker.get(peer.ticker, 0)})

    active = sum(1 for r in formatted if r.get("is_active"))
    n = len(peer_tickers)
    summary = (f"{active} active SCA{'s' if active != 1 else ''} among {n} peers analyzed"
               if formatted else f"No active SCAs detected among {n} peers analyzed")
    return {"peer_sca_records": formatted, "has_peer_sca": True,
            "peer_sca_summary": summary, "peer_profiles": profiles}


def build_concentration_assessment(state: AnalysisState) -> dict[str, Any]:
    """Build 4-dimension concentration assessment (Customer, Geographic, Product, Channel)."""
    dims = [
        _assess_customer(state), _assess_geographic(state),
        _assess_product(state),
        {"dimension": "Channel", "level": "MEDIUM",
         "key_data": "Not assessed -- channel breakdown not available in standard filings",
         "do_implication": "Channel concentration not determinable from available disclosures"},
    ]
    levels = [d["level"] for d in dims]
    overall = "HIGH" if "HIGH" in levels else ("MEDIUM" if "MEDIUM" in levels else "LOW")
    return {"concentration_dims": dims, "has_concentration": True, "concentration_risk_level": overall}


_CONC_IMPL: dict[str, dict[str, str]] = {
    "Customer": {
        "HIGH": "Customer loss would trigger revenue miss SCA -- concentration risk material to guidance",
        "MEDIUM": "Moderate customer concentration -- loss of top customer could impact disclosed guidance",
        "LOW": "Diversified customer base reduces revenue miss SCA risk",
    },
    "Geographic": {
        "HIGH": "Single-region dominance creates geopolitical and regulatory concentration risk for D&O",
        "MEDIUM": "Regional concentration present -- geopolitical disruption could impact operations",
        "LOW": "Diversified geographic footprint reduces regional concentration risk",
    },
    "Product": {
        "HIGH": "Single product/service dominance creates SCA risk if segment faces disruption",
        "MEDIUM": "Moderate product concentration -- segment-specific headwinds could impact guidance",
        "LOW": "Diversified product/service mix reduces segment-specific SCA risk",
    },
}


def _assess_customer(state: AnalysisState) -> dict[str, Any]:
    prof = state.company
    if not prof or not prof.customer_concentration:
        return {"dimension": "Customer", "level": "LOW",
                "key_data": "No major customer concentration disclosed",
                "do_implication": _CONC_IMPL["Customer"]["LOW"]}
    max_pct, top = 0.0, ""
    for sv in prof.customer_concentration:
        pct = safe_float(sv.value.get("revenue_pct", 0))
        if pct and pct > max_pct:
            max_pct, top = pct, str(sv.value.get("customer", ""))
    level = "HIGH" if max_pct > 15 else "MEDIUM" if max_pct > 5 else "LOW"
    key = f"Top customer ({top}): {max_pct:.1f}% of revenue" if top else f"Max customer: {max_pct:.1f}%"
    return {"dimension": "Customer", "level": level, "key_data": key, "do_implication": _CONC_IMPL["Customer"][level]}


def _assess_geographic(state: AnalysisState) -> dict[str, Any]:
    prof = state.company
    if not prof or not prof.geographic_footprint:
        return {"dimension": "Geographic", "level": "MEDIUM",
                "key_data": "No geographic breakdown disclosed",
                "do_implication": "Lack of geographic disclosure limits risk assessment"}
    max_pct, top = 0.0, ""
    for sv in prof.geographic_footprint:
        g = sv.value
        m = re.search(r"(\d+\.?\d*)%?", str(g.get("percentage", "")))
        if m:
            pct = safe_float(m.group(1))
            if pct and pct > max_pct:
                max_pct, top = pct, str(g.get("region", g.get("jurisdiction", "")))
    level = "HIGH" if max_pct > 80 else "MEDIUM" if max_pct > 50 else "LOW"
    key = f"Top region ({top}): {max_pct:.1f}%" if top else "Geographic data available but percentages unclear"
    return {"dimension": "Geographic", "level": level, "key_data": key, "do_implication": _CONC_IMPL["Geographic"][level]}


def _assess_product(state: AnalysisState) -> dict[str, Any]:
    prof = state.company
    if not prof or not prof.revenue_segments:
        return {"dimension": "Product/Service", "level": "MEDIUM",
                "key_data": "No product/service segment breakdown available",
                "do_implication": "Lack of segment disclosure limits concentration assessment"}
    max_pct, top = 0.0, ""
    total_rev = sum(safe_float(s.value.get("revenue", 0)) for s in prof.revenue_segments)
    for sv in prof.revenue_segments:
        seg = sv.value
        pct = safe_float(seg.get("percentage", seg.get("pct", 0)))
        if not pct and total_rev > 0:
            rev = safe_float(seg.get("revenue", 0))
            pct = (rev / total_rev * 100) if rev else 0
        if pct and pct > max_pct:
            max_pct, top = pct, str(seg.get("name", seg.get("segment", "")))
    level = "HIGH" if max_pct > 60 else "MEDIUM" if max_pct > 40 else "LOW"
    key = f"Top segment ({top}): {max_pct:.1f}%" if top else f"Max segment: {max_pct:.1f}%"
    return {"dimension": "Product/Service", "level": level, "key_data": key, "do_implication": _CONC_IMPL["Product"][level]}


def build_supply_chain_context(state: AnalysisState) -> dict[str, Any]:
    """Build supply chain dependency table from 10-K text."""
    item1_text, item1a_text = "", ""
    filings = get_filings(state)
    if filings:
        if isinstance(filings, dict):
            for key, value in filings.items():
                if isinstance(value, dict):
                    text = value.get("text", "") or value.get("content", "")
                    if isinstance(text, str):
                        lk = str(key).lower()
                        if "item_1a" in lk or "item1a" in lk:
                            item1a_text = text[:50000]
                        elif "item_1" in lk or "item1" in lk:
                            item1_text = text[:50000]
    if not item1_text and state.extracted and state.extracted.text_signals:
        item1_text = str(state.extracted.text_signals.get("item_1_text", ""))[:50000]
    if not item1a_text and state.extracted and state.extracted.text_signals:
        item1a_text = str(state.extracted.text_signals.get("item_1a_text", ""))[:50000]
    if not item1_text and not item1a_text:
        return {"has_supply_chain": False}

    company_name = ""
    if state.company and state.company.identity and state.company.identity.legal_name:
        company_name = str(state.company.identity.legal_name.value)
    try:
        from do_uw.stages.extract.supply_chain_extract import extract_supply_chain
        deps = extract_supply_chain(item1_text, item1a_text, company_name)
    except Exception:
        logger.warning("Supply chain extraction failed")
        return {"has_supply_chain": False}
    if not deps:
        return {"has_supply_chain": False}

    rows = [{"provider": d.provider or "Undisclosed", "dependency_type": d.dependency_type,
             "concentration": d.concentration, "switching_cost": d.switching_cost,
             "do_exposure": d.do_exposure, "source": d.source} for d in deps]
    risk = "HIGH" if any(d["dependency_type"] == "sole-source" for d in rows) else "MEDIUM"
    return {"supply_chain_deps": rows, "has_supply_chain": True, "supply_chain_risk": risk}


def build_sector_do_concerns(state: AnalysisState) -> dict[str, Any]:
    """Build sector-specific D&O concerns from config."""
    if not state.company or not state.company.identity:
        return {"has_sector_concerns": False}
    sic_sv = state.company.identity.sic_code
    if not sic_sv:
        return {"has_sector_concerns": False}
    sic = int(safe_float(sic_sv.value)) if sic_sv.value else 0
    if not sic:
        return {"has_sector_concerns": False}

    config_path = _CONFIG_DIR / "sector_do_concerns.json"
    if not config_path.exists():
        logger.warning("sector_do_concerns.json not found at %s", config_path)
        return {"has_sector_concerns": False}
    try:
        data = json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"has_sector_concerns": False}

    matched_sector = ""
    concerns: list[dict[str, Any]] = []
    for sector in data.get("sectors", []):
        for sr in sector.get("sic_ranges", []):
            if len(sr) == 2 and sr[0] <= sic <= sr[1]:
                matched_sector = sector["name"]
                concerns = [{"concern": c.get("concern", ""), "sector_relevance": c.get("relevance", "MEDIUM"),
                             "company_exposure": c.get("relevance", "MEDIUM"),
                             "do_implication": c.get("do_implication", "")} for c in sector.get("concerns", [])]
                break
        if matched_sector:
            break
    return {"sector_concerns": concerns, "has_sector_concerns": bool(concerns), "matched_sector": matched_sector}


def build_regulatory_map(state: AnalysisState) -> dict[str, Any]:
    """Build regulatory environment map from litigation proceedings."""
    proceedings = get_regulatory_proceedings(state)
    if not proceedings:
        return {"has_regulatory_map": False}

    rows: list[dict[str, Any]] = []
    for sv_proc in proceedings:
        proc = sv_proc.value if hasattr(sv_proc, "value") else sv_proc
        if not isinstance(proc, dict):
            continue
        agency = str(proc.get("agency", proc.get("regulator", "Unknown")))
        status = str(proc.get("status", "Unknown"))
        exposure = "HIGH" if status.lower() in ("active", "ongoing", "pending") else "MEDIUM"
        rows.append({"agency": agency, "jurisdiction": str(proc.get("jurisdiction", "Federal")),
                      "exposure_level": exposure, "current_status": status,
                      "risk_level": exposure, "description": str(proc.get("description", proc.get("type", "")))})
    return {"regulatory_map": rows, "has_regulatory_map": bool(rows), "regulatory_count": len(rows)}


__all__ = [
    "build_concentration_assessment", "build_peer_sca_contagion",
    "build_regulatory_map", "build_risk_factor_review",
    "build_sector_do_concerns", "build_supply_chain_context",
]
