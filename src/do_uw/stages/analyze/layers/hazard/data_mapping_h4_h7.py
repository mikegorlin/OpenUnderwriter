"""Data mapping for H4-H7 dimensions (Governance, Maturity, Environment, Emerging).

Split from data_mapping.py to stay under 500 lines per file.
Uses shared helpers from data_mapping module.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.company import CompanyProfile
from do_uw.models.state import ExtractedData
from do_uw.stages.analyze.layers.hazard.data_mapping import _search_risk_factors, _sv

# ---------------------------------------------------------------------------
# H4: Governance Structure mappers
# ---------------------------------------------------------------------------


def map_h4_01(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H4-01 CEO/Chair Combined."""
    if ext.governance and ext.governance.board:
        val = _sv(ext.governance.board.ceo_chair_duality)
        if val is not None:
            return {"ceo_chair_combined": val, "_data_tier": "primary"}
    if ext.governance and ext.governance.governance_score:
        ccs = ext.governance.governance_score.ceo_chair_score
        return {"ceo_chair_score": ccs, "_data_tier": "proxy"}
    return {}


def map_h4_02(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H4-02 Board Independence."""
    if ext.governance and ext.governance.board:
        ratio = _sv(ext.governance.board.independence_ratio)
        if ratio is not None:
            return {"independence_ratio": ratio, "_data_tier": "primary"}
    if ext.governance and ext.governance.governance_score:
        return {
            "independence_score": ext.governance.governance_score.independence_score,
            "_data_tier": "proxy",
        }
    return {}


def map_h4_03(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H4-03 Anti-Takeover Provisions."""
    if ext.governance and ext.governance.board:
        b = ext.governance.board
        classified = _sv(b.classified_board)
        if classified is not None:
            return {"classified_board": classified, "_data_tier": "primary"}
    if ext.governance and ext.governance.governance_score:
        return {
            "governance_total": _sv(ext.governance.governance_score.total_score),
            "_data_tier": "proxy",
        }
    return {}


def map_h4_04(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H4-04 Audit Committee Quality."""
    if ext.governance and ext.governance.governance_score:
        gs = ext.governance.governance_score
        return {
            "committee_score": gs.committee_score,
            "governance_total": _sv(gs.total_score),
            "_data_tier": "proxy",
        }
    return {}


def map_h4_05(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H4-05 Shareholder Rights."""
    if ext.governance and ext.governance.governance_score:
        gs = ext.governance.governance_score
        if _sv(gs.total_score) is not None:
            return {"governance_total": _sv(gs.total_score), "_data_tier": "proxy"}
    return {}


def map_h4_06(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H4-06 Compensation Structure."""
    if ext.governance and ext.governance.comp_analysis:
        ca = ext.governance.comp_analysis
        comp_mix = ca.comp_mix or {}
        clawback = _sv(ca.has_clawback)
        pay_ratio = _sv(ca.ceo_pay_ratio)
        sop = _sv(ca.say_on_pay_pct)
        if comp_mix or clawback is not None or pay_ratio or sop:
            return {
                "comp_mix": comp_mix,
                "has_clawback": clawback,
                "ceo_pay_ratio": pay_ratio,
                "say_on_pay_pct": sop,
                "_data_tier": "primary",
            }
    return {}


def map_h4_07(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H4-07 Compliance Infrastructure."""
    if ext.financials and ext.financials.audit:
        audit = ext.financials.audit
        mw = audit.material_weaknesses or []
        gc = _sv(audit.going_concern)
        if mw or gc is not None:
            return {
                "material_weaknesses": [_sv(w) for w in mw],
                "going_concern": gc,
                "_data_tier": "primary",
            }
    if ext.governance and ext.governance.governance_score:
        return {
            "governance_total": _sv(ext.governance.governance_score.total_score),
            "_data_tier": "proxy",
        }
    return {}


def map_h4_08(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H4-08 State of Incorporation."""
    state = _sv(co.identity.state_of_incorporation)
    if state:
        return {"state": state, "_data_tier": "primary"}
    return {}


# ---------------------------------------------------------------------------
# H5: Public Company Maturity mappers
# ---------------------------------------------------------------------------


def map_h5_01(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H5-01 IPO Recency."""
    yp = _sv(co.years_public)
    if yp is not None:
        return {"years_public": yp, "_data_tier": "primary"}
    return {}


def map_h5_02(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H5-02 Method of Going Public."""
    hits = _search_risk_factors(ext, ["SPAC", "special purpose acquisition", "de-SPAC"])
    if hits:
        return {"keyword_hits": hits, "method": "SPAC", "_data_tier": "proxy"}
    desc = _sv(co.business_model_description) or ""
    if "spac" in desc.lower() or "de-spac" in desc.lower():
        return {"method": "SPAC", "_data_tier": "proxy"}
    return {}


def map_h5_03(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H5-03 Exchange/Index Membership."""
    exchange = _sv(co.identity.exchange)
    if exchange:
        return {"exchange": exchange, "_data_tier": "primary"}
    return {}


def map_h5_04(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H5-04 FPI/ADR Status."""
    is_fpi = co.identity.is_fpi
    return {"is_fpi": is_fpi, "_data_tier": "primary"}


def map_h5_05(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H5-05 Seasoning/Track Record."""
    yp = _sv(co.years_public)
    lit_count = 0
    if ext.litigation and hasattr(ext.litigation, "active_cases"):
        active = getattr(ext.litigation, "active_cases", []) or []
        lit_count = len(active)
    if yp is not None:
        return {
            "years_public": yp,
            "prior_litigation_count": lit_count,
            "_data_tier": "primary",
        }
    return {}


# ---------------------------------------------------------------------------
# H6: External Environment mappers
# ---------------------------------------------------------------------------


def map_h6_01(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H6-01 Market Cycle (config default)."""
    return {"_data_tier": "proxy"}


def map_h6_02(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H6-02 Industry Regulatory Spotlight."""
    sector = _sv(co.identity.sector)
    sic = _sv(co.identity.sic_code)
    if sector or sic:
        return {"sector": sector, "sic_code": sic, "_data_tier": "primary"}
    return {}


def map_h6_03(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H6-03 Industry Litigation Wave."""
    sector = _sv(co.identity.sector)
    if sector:
        return {"sector": sector, "_data_tier": "primary"}
    return {}


def map_h6_04(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H6-04 Political/Policy Environment (config default)."""
    return {"_data_tier": "proxy"}


def map_h6_05(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H6-05 Interest Rate Environment (config default)."""
    return {"_data_tier": "proxy"}


def map_h6_06(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H6-06 Plaintiff Attorney Activity (config default)."""
    return {"_data_tier": "proxy"}


def map_h6_07(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H6-07 Geopolitical Risk."""
    geo = co.geographic_footprint or []
    if geo:
        return {
            "geographic_regions": len(geo),
            "geographic_footprint": [_sv(g) for g in geo],
            "_data_tier": "primary",
        }
    hits = _search_risk_factors(ext, ["geopolitical", "sanctions", "trade war", "tariff"])
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


# ---------------------------------------------------------------------------
# H7: Emerging / Modern Hazards mappers
# ---------------------------------------------------------------------------


def map_h7_01(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H7-01 AI Adoption/Governance."""
    if ext.ai_risk:
        return {
            "ai_score": ext.ai_risk.overall_score,
            "disclosure_data": {
                "mention_count": ext.ai_risk.disclosure_data.mention_count,
                "sentiment": ext.ai_risk.disclosure_data.sentiment,
            },
            "_data_tier": "primary",
        }
    hits = _search_risk_factors(ext, ["artificial intelligence", "AI", "machine learning"])
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def map_h7_02(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H7-02 Cybersecurity Governance."""
    hits = _search_risk_factors(
        ext, ["cybersecurity", "data breach", "cyber", "information security", "privacy"]
    )
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def map_h7_03(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H7-03 ESG/Climate Exposure."""
    sector = _sv(co.identity.sector)
    hits = _search_risk_factors(
        ext, ["ESG", "climate", "carbon", "environmental", "sustainability"]
    )
    if hits:
        return {"keyword_hits": hits, "sector": sector, "_data_tier": "proxy"}
    if sector:
        return {"sector": sector, "_data_tier": "proxy"}
    return {}


def map_h7_04(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H7-04 Crypto/Digital Asset."""
    hits = _search_risk_factors(
        ext, ["crypto", "digital asset", "blockchain", "bitcoin", "token"]
    )
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def map_h7_05(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H7-05 Social Media/Public Persona (LOW availability)."""
    if ext.governance and ext.governance.sentiment:
        sm = _sv(ext.governance.sentiment.social_media_sentiment)
        if sm:
            return {"social_media_sentiment": sm, "_data_tier": "proxy"}
    return {}


def map_h7_06(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H7-06 Workforce/Labor Model."""
    hits = _search_risk_factors(
        ext, ["gig economy", "contractor", "workforce", "labor", "employee classification"]
    )
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    emp = _sv(co.employee_count)
    if emp is not None:
        return {"employee_count": emp, "_data_tier": "proxy"}
    return {}
