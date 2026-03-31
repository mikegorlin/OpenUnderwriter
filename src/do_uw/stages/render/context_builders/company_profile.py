"""Company profile context builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.formatters import (
    EMPLOYEE_SPECTRUM, MARKET_CAP_SPECTRUM, REVENUE_SPECTRUM, YEARS_PUBLIC_SPECTRUM,
    compute_spectrum_position, format_currency, format_percentage, na_if_none, safe_float, sv_val,
)


_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "config"


def _lookup_gics_name(gics_code: str) -> str:
    """Look up GICS industry name from the SIC-GICS mapping config."""
    if not gics_code:
        return ""
    mapping_path = _CONFIG_DIR / "sic_gics_mapping.json"
    if not mapping_path.exists():
        return ""
    try:
        data = json.loads(mapping_path.read_text())
        for _sic, entry in data.get("mappings", {}).items():
            if str(entry.get("gics", "")) == gics_code:
                return str(entry.get("gics_name", ""))
    except (json.JSONDecodeError, OSError):
        pass
    return ""


def _get_yfinance_sector(state: AnalysisState) -> str:
    """Get sector name from yfinance data if available."""
    if state.acquired_data is None:
        return ""
    info = state.acquired_data.market_data.get("info")
    if not isinstance(info, dict):
        return ""
    sector = info.get("sector", "")
    return str(sector) if sector else ""


def extract_company(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
    canonical: Any | None = None,
) -> dict[str, Any]:
    """Extract company profile data for template.

    Args:
        state: The analysis state.
        signal_results: Optional pre-computed signal results.
        canonical: Optional CanonicalMetrics object for cross-section consistency.
    """
    from do_uw.stages.render.context_builders.company_business_model import (
        extract_business_model,
    )
    from do_uw.stages.render.context_builders.company_environment import (
        _build_environment_assessment,
        _build_sector_risk,
    )
    from do_uw.stages.render.context_builders.company_events import (
        _build_corporate_events,
    )
    from do_uw.stages.render.context_builders.company_operations import (
        _build_operational_complexity,
        _build_structural_complexity,
    )
    from do_uw.stages.render.context_builders._company_intelligence import (
        build_concentration_assessment,
        build_peer_sca_contagion,
        build_regulatory_map,
        build_risk_factor_review,
        build_sector_do_concerns,
        build_supply_chain_context,
    )

    prof = state.company
    if prof is None:
        return {}
    identity = prof.identity
    from do_uw.stages.render.formatters import clean_company_name
    _raw_name = str(identity.legal_name.value) if identity and identity.legal_name else "N/A"
    legal_name = clean_company_name(_raw_name) if _raw_name != "N/A" else "N/A"
    sic = str(identity.sic_code.value) if identity and identity.sic_code else "N/A"
    sic_desc = str(sv_val(identity.sic_description, "N/A")) if identity else "N/A"
    state_inc = (
        str(identity.state_of_incorporation.value)
        if identity and identity.state_of_incorporation
        else "N/A"
    )
    cik = str(sv_val(identity.cik, "N/A")) if identity else "N/A"
    if canonical is not None and canonical.exchange.raw is not None:
        exchange = canonical.exchange.formatted
    else:
        exchange = str(sv_val(identity.exchange, "N/A")) if identity else "N/A"
    fpi = "Yes" if (identity and identity.is_fpi) else "No"

    # Business description
    biz_desc = None
    if prof.business_description:
        raw = prof.business_description
        val = raw.value if hasattr(raw, "value") else raw
        if val:
            biz_desc = str(val)

    segments: list[dict[str, str]] = []
    raw_segs = prof.revenue_segments or []
    total_rev = sum(
        safe_float(s.value.get("revenue", 0)) for s in raw_segs
    )
    for sv_seg in raw_segs:
        seg = sv_seg.value
        name = str(seg.get("name", seg.get("segment", "Unknown")))
        pct = seg.get("percentage", seg.get("pct"))
        if pct is None and total_rev > 0:
            rev = seg.get("revenue")
            if rev is not None:
                pct = safe_float(rev) / total_rev * 100
        segments.append({"name": name, "pct": format_percentage(safe_float(pct)) if pct is not None else "N/A"})

    # Fallback 1: if XBRL/text extraction found no segments, use dossier segments (LLM-extracted)
    if not segments and state.dossier and state.dossier.segment_dossiers:
        for ds in state.dossier.segment_dossiers:
            seg_name = ds.segment_name or "Unknown"
            seg_pct = ds.revenue_pct or "N/A"
            segments.append({"name": seg_name, "pct": seg_pct})

    # Fallback 2: if still no segments with percentages, derive from geographic_footprint
    # Geographic data often has format like "$178.4B (42.8%)" in the percentage field
    if segments and all(s.get("pct") in ("N/A", "", None) for s in segments):
        import re
        geo_segs: list[dict[str, str]] = []
        for sv_geo in (prof.geographic_footprint or []):
            g = sv_geo.value
            region = str(g.get("region", g.get("jurisdiction", "Unknown")))
            if region in ("Unknown", "", "None"):
                continue
            raw_pct = str(g.get("percentage", ""))
            # Parse "42.8%" or "$178.4B (42.8%)" patterns
            match = re.search(r"(\d+\.?\d*)%", raw_pct)
            pct_str = format_percentage(float(match.group(1))) if match else "N/A"
            geo_segs.append({"name": region, "pct": pct_str})
        if geo_segs and any(s.get("pct") != "N/A" for s in geo_segs):
            segments = geo_segs

    geo: list[dict[str, str]] = []
    for sv_geo in (prof.geographic_footprint or []):
        g = sv_geo.value
        region = str(g.get("jurisdiction", g.get("region", g.get("geography", "Unknown"))))
        if region in ("Unknown", "", "None"):
            continue
        pct = g.get("percentage", g.get("pct"))
        detail = "N/A"
        if pct is not None:
            import re as _re
            pct_str = str(pct)
            # Parse percentage from formats like "$178.4B (42.8%)" or "42.8%"
            pct_match = _re.search(r"(\d+\.?\d*)%", pct_str)
            if pct_match:
                detail = format_percentage(float(pct_match.group(1)))
            else:
                try:
                    detail = format_percentage(safe_float(pct))
                except (ValueError, TypeError):
                    detail = pct_str
        elif g.get("subsidiary_count") is not None:
            count = int(safe_float(g["subsidiary_count"]))
            detail = f"{count} {'subsidiary' if count == 1 else 'subsidiaries'}"
        geo.append({"region": region, "detail": detail})

    # Subsidiaries
    sub_count: str | None = None
    if prof.subsidiary_count is not None:
        sub_count = f"{prof.subsidiary_count.value:,}"

    # D&O exposure factors
    exposure_factors: list[dict[str, str]] = []
    if prof.do_exposure_factors:
        for f_sv in prof.do_exposure_factors:
            factor = f_sv.value
            raw_name = str(factor.get("factor", factor.get("name", "Unknown")))
            name = raw_name.replace("_", " ").title()
            level = str(factor.get("level", "Identified"))
            rationale = str(factor.get("reason", factor.get("rationale", "")))
            if not rationale or rationale == "N/A":
                rationale = ""
            exposure_factors.append({"name": name, "level": level, "rationale": rationale})

    # Customer concentration
    customers: list[dict[str, str]] = []
    for sv_cust in (prof.customer_concentration or []):
        cust = sv_cust.value
        desc = str(cust.get("customer", "Unknown"))
        pct = cust.get("revenue_pct")
        pct_str = format_percentage(safe_float(pct)) if pct and safe_float(pct) > 0 else ""
        customers.append({"description": desc, "pct": pct_str})

    # Supplier concentration
    suppliers: list[dict[str, str]] = []
    for sv_sup in (prof.supplier_concentration or []):
        sup = sv_sup.value
        desc = str(sup.get("supplier", "Unknown"))
        pct = sup.get("cost_pct")
        pct_str = format_percentage(safe_float(pct)) if pct and safe_float(pct) > 0 else ""
        suppliers.append({"description": desc, "pct": pct_str})

    # GICS code + name (state first, then SIC-GICS mapping fallback)
    gics_code = str(sv_val(prof.gics_code, "")) if prof.gics_code else ""
    if not gics_code and sic and sic != "N/A":
        _mp = _CONFIG_DIR / "sic_gics_mapping.json"
        if _mp.exists():
            try:
                _entry = json.loads(_mp.read_text()).get("mappings", {}).get(sic)
                if _entry:
                    gics_code = str(_entry.get("gics", ""))
            except (json.JSONDecodeError, OSError):
                pass
    gics_name = _lookup_gics_name(gics_code) if gics_code else ""

    # NAICS code
    naics_code = (
        str(sv_val(identity.naics_code, ""))
        if identity and identity.naics_code
        else ""
    )

    # Size spectrum data
    mcap_val = prof.market_cap.value if prof.market_cap else None
    rev_val = None
    if state.executive_summary and state.executive_summary.snapshot:
        snap = state.executive_summary.snapshot
        if snap.revenue:
            rev_val = snap.revenue.value
    emp_val = prof.employee_count.value if prof.employee_count else None
    yrs_val = prof.years_public.value if prof.years_public else None

    spectrums = {
        "market_cap": compute_spectrum_position(mcap_val, MARKET_CAP_SPECTRUM),
        "revenue": compute_spectrum_position(rev_val, REVENUE_SPECTRUM),
        "employees": compute_spectrum_position(emp_val, EMPLOYEE_SPECTRUM),
        "years_public": compute_spectrum_position(yrs_val, YEARS_PUBLIC_SPECTRUM),
    }

    # Subsidiary structure (OPS-02)
    sub_structure: dict[str, Any] | None = None
    if prof.subsidiary_structure is not None:
        sub_structure = prof.subsidiary_structure.value

    # Workforce distribution (OPS-03)
    workforce: dict[str, Any] | None = None
    if prof.workforce_distribution is not None:
        workforce = prof.workforce_distribution.value

    # Operational resilience (OPS-04)
    resilience: dict[str, Any] | None = None
    if prof.operational_resilience is not None:
        resilience = prof.operational_resilience.value

    # Environment assessment (Phase 97 ENVR signals)
    env_assessment, has_env_data = _build_environment_assessment(state, signal_results=signal_results)

    # Sector risk
    sector_risk, has_sector_risk = _build_sector_risk(state, signal_results=signal_results)

    # Operational complexity
    ops_complexity, has_ops_complexity = _build_operational_complexity(state, signal_results=signal_results)

    # Corporate events
    corporate_events, has_corporate_events = _build_corporate_events(state, signal_results=signal_results)

    # Structural complexity
    structural_complexity, has_structural_complexity = _build_structural_complexity(state, signal_results=signal_results)

    # Phase 134: Company intelligence sub-sections (each guarded with try/except)
    ci_data: dict[str, Any] = {}
    for _ci_name, _ci_builder in [
        ("risk_factor_review", build_risk_factor_review),
        ("peer_sca_contagion", build_peer_sca_contagion),
        ("concentration_assessment", build_concentration_assessment),
        ("supply_chain_context", build_supply_chain_context),
        ("sector_do_concerns", build_sector_do_concerns),
        ("regulatory_map", build_regulatory_map),
    ]:
        try:
            ci_data.update(_ci_builder(state))
        except Exception:
            import logging as _log
            _log.getLogger(__name__).warning(
                "Company intelligence builder %s failed", _ci_name, exc_info=True,
            )

    result = {
        "legal_name": legal_name,
        "sic_code": sic,
        "sic_description": sic_desc,
        "state_of_inc": state_inc,
        "cik": cik,
        "exchange": exchange,
        "fpi": fpi,
        "market_cap_fmt": format_currency(mcap_val, compact=True),
        "employee_count_fmt": (
            canonical.employees.formatted
            if canonical and canonical.employees.raw is not None
            else na_if_none(
                f"{prof.employee_count.value:,.0f}" if prof.employee_count else (
                    f"{state.extracted.market.stock.employee_count_yf.value:,}"
                    if state.extracted and state.extracted.market
                    and state.extracted.market.stock.employee_count_yf
                    else None
                ),
            )
        ),
        "business_description": biz_desc,
        "revenue_segments": segments,
        "geographic_footprint": geo,
        "subsidiary_count": sub_count,
        "exposure_factors": exposure_factors,
        "customer_concentration": customers,
        "supplier_concentration": suppliers,
        "gics_code": gics_code,
        "gics_name": gics_name,
        "naics_code": naics_code,
        "spectrums": spectrums,
        "business_model": extract_business_model(state, signal_results=signal_results),
        "subsidiary_structure": sub_structure,
        "workforce_distribution": workforce,
        "operational_resilience": resilience,
        "environment_assessment": env_assessment,
        "has_environment_data": has_env_data,
        "sector_risk": sector_risk,
        "has_sector_risk": has_sector_risk,
        "operational_complexity_signals": ops_complexity,
        "has_ops_complexity": has_ops_complexity,
        "corporate_events_signals": corporate_events,
        "has_corporate_events": has_corporate_events,
        "structural_complexity_signals": structural_complexity,
        "has_structural_complexity": has_structural_complexity,
        "event_timeline": _build_event_timeline(prof),
    }
    result.update(ci_data)
    return result


def _build_event_timeline(prof: Any) -> list[dict[str, str]]:
    """Build company event timeline from state."""
    events: list[dict[str, str]] = []
    raw_timeline = getattr(prof, "event_timeline", None)
    if not raw_timeline:
        return events
    for sv_evt in raw_timeline:
        val = sv_evt.value if hasattr(sv_evt, "value") else sv_evt
        if not isinstance(val, dict):
            continue
        events.append({
            "date": str(val.get("date", "N/A")),
            "description": str(val.get("description", "")),
            "type": str(val.get("type", val.get("event_type", "event"))),
        })
    return events


__all__ = [
    "_get_yfinance_sector",
    "_lookup_gics_name",
    "extract_company",
]
