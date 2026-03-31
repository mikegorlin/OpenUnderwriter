"""Data mapping bridge: connects ExtractedData/CompanyProfile to dimension inputs.

Each dimension scorer receives a dict of named inputs built by this module.
The mapping implements a 3-tier fallback pattern:
  1. Primary data source (direct structured field)
  2. Proxy signal fallback (alternative/indirect data)
  3. Neutral default (empty dict -> scorer returns neutral score)

Every return dict includes ``_data_tier`` ("primary", "proxy", "unavailable").

H1-H3 mappers are defined here; H4-H7 are in data_mapping_h4_h7.py
to stay under 500 lines per file.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.company import CompanyProfile
from do_uw.models.state import ExtractedData, RiskFactorProfile

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def map_dimension_data(
    dim_id: str,
    extracted: ExtractedData,
    company: CompanyProfile,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Map dimension ID to its data inputs from extracted/company data.

    Returns a dict consumed by the dimension scorer. Always includes
    ``_data_tier`` key. Returns empty dict ``{}`` when no data is
    available at any tier (triggers neutral default score).
    """
    mapper = _get_mappers().get(dim_id)
    if mapper is None:
        return {}
    return mapper(extracted, company, config)


# ---------------------------------------------------------------------------
# Shared helpers (exported for use by data_mapping_h4_h7)
# ---------------------------------------------------------------------------


def _search_risk_factors(
    extracted: ExtractedData,
    keywords: list[str],
) -> list[str]:
    """Search extracted risk factors for keyword matches.

    Returns list of matching risk factor titles/categories.
    Used as proxy signal tier for PARTIAL dimensions.
    """
    hits: list[str] = []
    factors: list[RiskFactorProfile] = extracted.risk_factors or []
    kw_lower = [k.lower() for k in keywords]
    for rf in factors:
        text = f"{rf.title} {rf.source_passage}".lower()
        if any(k in text for k in kw_lower):
            hits.append(f"{rf.category}: {rf.title}")
    return hits


def _sv(val: Any) -> Any:
    """Extract .value from SourcedValue or return val as-is."""
    if val is None:
        return None
    if hasattr(val, "value"):
        return val.value
    return val


def _get_line_item_value(
    statements: Any,
    stmt_type: str,
    label_substr: str,
) -> float | None:
    """Find a financial line item value from statements.

    Searches for label_substr in the most recent period of the given
    statement type. Returns None if not found.
    """
    if statements is None:
        return None
    stmt = getattr(statements, stmt_type, None)
    if stmt is None or not stmt.line_items:
        return None
    for item in stmt.line_items:
        if label_substr.lower() in item.label.lower():
            for period_val in item.values.values():
                if period_val is not None:
                    return float(_sv(period_val))
    return None


# ---------------------------------------------------------------------------
# H1: Business & Operating Model mappers
# ---------------------------------------------------------------------------


def _map_h1_01(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-01 Industry Sector Risk Tier."""
    sector = _sv(co.identity.sector)
    sic = _sv(co.identity.sic_code)
    if sector or sic:
        return {"sector": sector, "sic_code": sic, "_data_tier": "primary"}
    return {}


def _map_h1_02(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-02 Business Complexity."""
    segments = co.revenue_segments or []
    op_complex = _sv(co.operational_complexity) if co.operational_complexity else None
    if segments or op_complex:
        return {
            "segment_count": len(segments),
            "operational_complexity": op_complex or {},
            "_data_tier": "primary",
        }
    hits = _search_risk_factors(ext, ["complex", "segment", "VIE", "variable interest"])
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def _map_h1_03(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-03 Regulatory Intensity (config lookup by SIC)."""
    sic = _sv(co.identity.sic_code)
    sector = _sv(co.identity.sector)
    if sic or sector:
        return {"sic_code": sic, "sector": sector, "_data_tier": "primary"}
    return {}


def _map_h1_04(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-04 Geographic Complexity."""
    geo = co.geographic_footprint or []
    sub_count = _sv(co.subsidiary_count)
    if geo or sub_count:
        return {
            "geographic_regions": len(geo),
            "subsidiary_count": sub_count,
            "geographic_footprint": [_sv(g) for g in geo],
            "_data_tier": "primary",
        }
    hits = _search_risk_factors(ext, ["international", "foreign", "FCPA", "geographic"])
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def _map_h1_05(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-05 Revenue Model Risk."""
    eq = None
    if ext.financials and ext.financials.earnings_quality:
        eq = _sv(ext.financials.earnings_quality)
    if eq and isinstance(eq, dict):
        return {"earnings_quality": eq, "_data_tier": "primary"}
    hits = _search_risk_factors(
        ext, ["revenue recognition", "percentage of completion", "ASC 606", "deferred"]
    )
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def _map_h1_06(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-06 Customer/Supplier Concentration."""
    customers = co.customer_concentration or []
    suppliers = co.supplier_concentration or []
    if customers or suppliers:
        return {
            "customer_concentration": [_sv(c) for c in customers],
            "supplier_concentration": [_sv(s) for s in suppliers],
            "_data_tier": "primary",
        }
    return {}


def _map_h1_07(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-07 Capital Intensity."""
    if ext.financials and ext.financials.statements:
        stmts = ext.financials.statements
        capex = _get_line_item_value(stmts, "cash_flow", "capital expenditure")
        if capex is None:
            capex = _get_line_item_value(stmts, "cash_flow", "capex")
        revenue = _get_line_item_value(stmts, "income_statement", "revenue")
        total_assets = _get_line_item_value(stmts, "balance_sheet", "total assets")
        ppe = _get_line_item_value(stmts, "balance_sheet", "property")
        if any(v is not None for v in [capex, revenue, ppe, total_assets]):
            return {
                "capex": abs(capex) if capex else None,
                "revenue": revenue,
                "total_assets": total_assets,
                "ppe": ppe,
                "_data_tier": "primary",
            }
    return {}


def _map_h1_08(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-08 M&A Activity."""
    changes = co.business_changes or []
    goodwill = None
    total_assets = None
    if ext.financials and ext.financials.statements:
        goodwill = _get_line_item_value(
            ext.financials.statements, "balance_sheet", "goodwill"
        )
        total_assets = _get_line_item_value(
            ext.financials.statements, "balance_sheet", "total assets"
        )
    if changes or goodwill is not None:
        return {
            "business_changes": [_sv(c) for c in changes],
            "goodwill": goodwill,
            "total_assets": total_assets,
            "_data_tier": "primary",
        }
    hits = _search_risk_factors(ext, ["acquisition", "merger", "goodwill", "integrate"])
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def _map_h1_09(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-09 Speed of Growth."""
    revenue_cur = None
    revenue_prev = None
    if ext.financials and ext.financials.statements:
        stmts = ext.financials.statements
        if stmts.income_statement and stmts.income_statement.line_items:
            for item in stmts.income_statement.line_items:
                if "revenue" in item.label.lower():
                    vals = list(item.values.values())
                    sourced = [_sv(v) for v in vals if v is not None]
                    if len(sourced) >= 2:
                        revenue_cur = float(sourced[0])
                        revenue_prev = float(sourced[1])
                    elif len(sourced) == 1:
                        revenue_cur = float(sourced[0])
                    if item.yoy_change is not None:
                        return {
                            "yoy_growth": item.yoy_change,
                            "revenue_current": revenue_cur,
                            "_data_tier": "primary",
                        }
                    break
    emp = _sv(co.employee_count)
    if revenue_cur and revenue_prev and revenue_prev > 0:
        yoy = (revenue_cur - revenue_prev) / abs(revenue_prev) * 100
        return {
            "yoy_growth": yoy,
            "revenue_current": revenue_cur,
            "employee_count": emp,
            "_data_tier": "primary",
        }
    if emp is not None:
        return {"employee_count": emp, "_data_tier": "proxy"}
    return {}


def _map_h1_10(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-10 Dual-Class Structure."""
    op = _sv(co.operational_complexity) if co.operational_complexity else None
    if op and isinstance(op, dict) and "dual_class" in str(op).lower():
        return {"operational_complexity": op, "_data_tier": "primary"}
    if ext.governance and ext.governance.ownership:
        own = ext.governance.ownership
        has_dc = _sv(own.has_dual_class)
        if has_dc is not None:
            return {
                "has_dual_class": has_dc,
                "control_pct": _sv(own.dual_class_control_pct),
                "economic_pct": _sv(own.dual_class_economic_pct),
                "_data_tier": "primary",
            }
    return {}


def _map_h1_11(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-11 Non-GAAP Reliance."""
    eq = None
    if ext.financials and ext.financials.earnings_quality:
        eq = _sv(ext.financials.earnings_quality)
    if eq and isinstance(eq, dict):
        return {"earnings_quality": eq, "_data_tier": "primary"}
    hits = _search_risk_factors(ext, ["non-GAAP", "adjusted EBITDA", "adjusted EPS"])
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def _map_h1_12(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-12 Platform Dependency."""
    hits = _search_risk_factors(
        ext, ["platform", "marketplace", "app store", "API", "distribution partner"]
    )
    if hits:
        return {"keyword_hits": hits, "_data_tier": "proxy"}
    return {}


def _map_h1_13(
    ext: ExtractedData, co: CompanyProfile, cfg: dict[str, Any]
) -> dict[str, Any]:
    """H1-13 IP Dependency."""
    patent_count = 0
    if ext.ai_risk and ext.ai_risk.patent_activity:
        patent_count = ext.ai_risk.patent_activity.ai_patent_count
    hits = _search_risk_factors(
        ext, ["patent", "intellectual property", "trade secret", "IP litigation"]
    )
    if patent_count > 0 or hits:
        return {"patent_count": patent_count, "keyword_hits": hits, "_data_tier": "proxy"}
    return {}


# ---------------------------------------------------------------------------
# Dispatch table: built lazily to avoid circular import from split modules
# ---------------------------------------------------------------------------

_MAPPERS_CACHE: dict[str, Any] | None = None


def _get_mappers() -> dict[str, Any]:
    """Build and cache the full dimension mappers dict."""
    global _MAPPERS_CACHE
    if _MAPPERS_CACHE is not None:
        return _MAPPERS_CACHE

    from do_uw.stages.analyze.layers.hazard import data_mapping_h2_h3 as h23
    from do_uw.stages.analyze.layers.hazard import data_mapping_h4_h7 as h47

    _MAPPERS_CACHE = {
        # H1: Business & Operating Model
        "H1-01": _map_h1_01,
        "H1-02": _map_h1_02,
        "H1-03": _map_h1_03,
        "H1-04": _map_h1_04,
        "H1-05": _map_h1_05,
        "H1-06": _map_h1_06,
        "H1-07": _map_h1_07,
        "H1-08": _map_h1_08,
        "H1-09": _map_h1_09,
        "H1-10": _map_h1_10,
        "H1-11": _map_h1_11,
        "H1-12": _map_h1_12,
        "H1-13": _map_h1_13,
        # H2: People & Management
        "H2-01": h23.map_h2_01,
        "H2-02": h23.map_h2_02,
        "H2-03": h23.map_h2_03,
        "H2-04": h23.map_h2_04,
        "H2-05": h23.map_h2_05,
        "H2-06": h23.map_h2_06,
        "H2-07": h23.map_h2_07,
        "H2-08": h23.map_h2_08,
        # H3: Financial Structure
        "H3-01": h23.map_h3_01,
        "H3-02": h23.map_h3_02,
        "H3-03": h23.map_h3_03,
        "H3-04": h23.map_h3_04,
        "H3-05": h23.map_h3_05,
        "H3-06": h23.map_h3_06,
        "H3-07": h23.map_h3_07,
        "H3-08": h23.map_h3_08,
        # H4: Governance Structure
        "H4-01": h47.map_h4_01,
        "H4-02": h47.map_h4_02,
        "H4-03": h47.map_h4_03,
        "H4-04": h47.map_h4_04,
        "H4-05": h47.map_h4_05,
        "H4-06": h47.map_h4_06,
        "H4-07": h47.map_h4_07,
        "H4-08": h47.map_h4_08,
        # H5: Public Company Maturity
        "H5-01": h47.map_h5_01,
        "H5-02": h47.map_h5_02,
        "H5-03": h47.map_h5_03,
        "H5-04": h47.map_h5_04,
        "H5-05": h47.map_h5_05,
        # H6: External Environment
        "H6-01": h47.map_h6_01,
        "H6-02": h47.map_h6_02,
        "H6-03": h47.map_h6_03,
        "H6-04": h47.map_h6_04,
        "H6-05": h47.map_h6_05,
        "H6-06": h47.map_h6_06,
        "H6-07": h47.map_h6_07,
        # H7: Emerging / Modern Hazards
        "H7-01": h47.map_h7_01,
        "H7-02": h47.map_h7_02,
        "H7-03": h47.map_h7_03,
        "H7-04": h47.map_h7_04,
        "H7-05": h47.map_h7_05,
        "H7-06": h47.map_h7_06,
    }
    return _MAPPERS_CACHE
