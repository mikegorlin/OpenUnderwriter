"""Data mapping for H2-H3 dimensions (People/Management, Financial Structure).

Split from data_mapping.py to stay under 500 lines per file.
Uses shared helpers from data_mapping module.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.company import CompanyProfile
from do_uw.models.state import ExtractedData
from do_uw.stages.analyze.layers.hazard.data_mapping import (
    _get_line_item_value,
    _search_risk_factors,
    _sv,
)

# ---------------------------------------------------------------------------
# H2: People & Management mappers
# ---------------------------------------------------------------------------


def map_h2_01(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H2-01 Management Experience."""
    if ext.governance and ext.governance.leadership:
        ls = ext.governance.leadership
        execs = ls.executives or []
        if execs:
            return {
                "executives": [
                    {
                        "title": _sv(e.title) or "",
                        "tenure_years": e.tenure_years,
                        "bio": _sv(e.bio_summary) or "",
                    }
                    for e in execs
                ],
                "avg_tenure": _sv(ls.avg_tenure_years),
                "_data_tier": "primary",
            }
    return {}


def map_h2_02(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H2-02 Industry Expertise Match."""
    sector = _sv(co.identity.sector)
    if ext.governance and ext.governance.leadership:
        execs = ext.governance.leadership.executives or []
        if execs and sector:
            return {
                "sector": sector,
                "exec_bios": [_sv(e.bio_summary) or "" for e in execs[:3]],
                "_data_tier": "primary",
            }
    if ext.governance and ext.governance.governance_score:
        gs = ext.governance.governance_score
        if _sv(gs.total_score) is not None:
            return {"governance_total": _sv(gs.total_score), "_data_tier": "proxy"}
    return {}


def map_h2_03(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H2-03 Scale Experience Mismatch (LOW availability)."""
    hits = _search_risk_factors(ext, ["scale", "rapid growth", "first time"])
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def map_h2_04(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H2-04 Board Quality."""
    if ext.governance:
        board = ext.governance.board
        forensics = ext.governance.board_forensics or []
        if board and (_sv(board.independence_ratio) is not None or forensics):
            overboarded = sum(1 for bf in forensics if bf.is_overboarded)
            return {
                "independence_ratio": _sv(board.independence_ratio),
                "board_size": _sv(board.size),
                "overboarded_count": _sv(board.overboarded_count) or overboarded,
                "avg_tenure": _sv(board.avg_tenure_years),
                "_data_tier": "primary",
            }
    return {}


def map_h2_05(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H2-05 Founder-Led."""
    if ext.governance and ext.governance.leadership:
        execs = ext.governance.leadership.executives or []
        for e in execs:
            title = (_sv(e.title) or "").lower()
            if "ceo" in title or "chief executive" in title:
                bio = (_sv(e.bio_summary) or "").lower()
                is_founder = "founder" in bio or "co-founder" in bio
                return {
                    "is_founder_ceo": is_founder,
                    "ceo_bio": _sv(e.bio_summary) or "",
                    "_data_tier": "primary" if is_founder else "proxy",
                }
    if ext.governance and ext.governance.governance_score:
        gs = ext.governance.governance_score
        if _sv(gs.total_score) is not None:
            return {"governance_total": _sv(gs.total_score), "_data_tier": "proxy"}
    return {}


def map_h2_06(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H2-06 Key Person Dependency (LOW availability)."""
    hits = _search_risk_factors(
        ext, ["key person", "key employee", "key management", "loss of", "depend on"]
    )
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def map_h2_07(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H2-07 Management Turnover."""
    if ext.governance and ext.governance.leadership:
        ls = ext.governance.leadership
        departures = ls.departures_18mo or []
        red_flags = ls.red_flags or []
        if departures or red_flags:
            return {
                "departure_count": len(departures),
                "red_flags": [_sv(f) for f in red_flags],
                "stability_score": _sv(ls.stability_score),
                "_data_tier": "primary",
            }
    return {}


def map_h2_08(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H2-08 Tone at the Top (proxy-based, non-automatable)."""
    result: dict[str, Any] = {}
    tier = "unavailable"
    if ext.governance and ext.governance.sentiment:
        s = ext.governance.sentiment
        tone = _sv(s.management_tone_trajectory)
        evasion = _sv(s.qa_evasion_score)
        if tone or evasion is not None:
            result["tone_trajectory"] = tone
            result["evasion_score"] = evasion
            tier = "proxy"
    if ext.governance and ext.governance.narrative_coherence:
        nc = ext.governance.narrative_coherence
        overall = _sv(nc.overall_assessment)
        if overall:
            result["narrative_coherence"] = overall
            tier = "proxy"
    if tier != "unavailable":
        result["_data_tier"] = tier
        return result
    return {}


# ---------------------------------------------------------------------------
# H3: Financial Structure mappers
# ---------------------------------------------------------------------------


def map_h3_01(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H3-01 Leverage."""
    if ext.financials and ext.financials.leverage:
        lev = _sv(ext.financials.leverage)
        if lev and isinstance(lev, dict):
            return {**lev, "_data_tier": "primary"}
    if ext.financials and ext.financials.statements:
        d2e = _get_line_item_value(
            ext.financials.statements, "balance_sheet", "total debt"
        )
        equity = _get_line_item_value(
            ext.financials.statements, "balance_sheet", "stockholders"
        )
        if d2e is not None and equity is not None and equity != 0:
            return {"debt_to_equity": d2e / equity, "_data_tier": "primary"}
    return {}


def map_h3_02(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H3-02 Off-Balance Sheet."""
    hits = _search_risk_factors(
        ext, ["VIE", "variable interest", "off-balance", "special purpose", "SPE"]
    )
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def map_h3_03(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H3-03 Goodwill-Heavy."""
    if ext.financials and ext.financials.statements:
        goodwill = _get_line_item_value(
            ext.financials.statements, "balance_sheet", "goodwill"
        )
        total_assets = _get_line_item_value(
            ext.financials.statements, "balance_sheet", "total assets"
        )
        if goodwill is not None and total_assets and total_assets > 0:
            return {
                "goodwill": goodwill,
                "total_assets": total_assets,
                "goodwill_pct": goodwill / total_assets * 100,
                "_data_tier": "primary",
            }
    return {}


def map_h3_04(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H3-04 Earnings Quality."""
    if ext.financials and ext.financials.distress:
        d = ext.financials.distress
        m_score = d.beneish_m_score
        if m_score and m_score.score is not None:
            result: dict[str, Any] = {
                "m_score": m_score.score,
                "m_score_zone": m_score.zone,
                "_data_tier": "primary",
            }
            eq = _sv(ext.financials.earnings_quality) if ext.financials.earnings_quality else None
            if eq and isinstance(eq, dict):
                result["earnings_quality"] = eq
            return result
    if ext.financials and ext.financials.earnings_quality:
        eq = _sv(ext.financials.earnings_quality)
        if eq and isinstance(eq, dict):
            return {"earnings_quality": eq, "_data_tier": "primary"}
    return {}


def map_h3_05(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H3-05 Cash Flow Divergence."""
    if ext.financials and ext.financials.statements:
        ocf = _get_line_item_value(ext.financials.statements, "cash_flow", "operating")
        ni = _get_line_item_value(
            ext.financials.statements, "income_statement", "net income"
        )
        if ocf is not None and ni is not None:
            return {"operating_cash_flow": ocf, "net_income": ni, "_data_tier": "primary"}
    return {}


def map_h3_06(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H3-06 Pre-Revenue / Cash Burn."""
    if ext.financials and ext.financials.statements:
        rev = _get_line_item_value(
            ext.financials.statements, "income_statement", "revenue"
        )
        ocf = _get_line_item_value(ext.financials.statements, "cash_flow", "operating")
        cash = _get_line_item_value(ext.financials.statements, "balance_sheet", "cash")
        if rev is not None or ocf is not None:
            return {
                "revenue": rev,
                "operating_cash_flow": ocf,
                "cash": cash,
                "_data_tier": "primary",
            }
    return {}


def map_h3_07(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H3-07 Related Party Transactions."""
    rpt: list[Any] = []
    if ext.governance and ext.governance.comp_analysis:
        rpt = ext.governance.comp_analysis.related_party_transactions or []
    if rpt:
        return {
            "related_party_count": len(rpt),
            "related_party_items": [_sv(r) for r in rpt],
            "_data_tier": "primary",
        }
    hits = _search_risk_factors(
        ext, ["related party", "related-party", "affiliated transaction"]
    )
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def map_h3_08(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H3-08 Capital Markets Activity."""
    if ext.market and ext.market.capital_markets:
        cm = ext.market.capital_markets
        activities: list[str] = []
        if hasattr(cm, "recent_offerings") and cm.recent_offerings:
            activities.extend([_sv(o) or "" for o in cm.recent_offerings])
        if hasattr(cm, "shelf_registrations") and cm.shelf_registrations:
            activities.append("shelf_registration_active")
        if activities:
            return {"activities": activities, "_data_tier": "primary"}
    hits = _search_risk_factors(
        ext, ["offering", "shelf registration", "debt issuance", "equity offering"]
    )
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}
