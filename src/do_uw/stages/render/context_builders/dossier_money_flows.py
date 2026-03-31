"""Money flows context builder for the Intelligence Dossier.

Extracts revenue flow diagram, narrative, segment data, geographic
breakdown, margin data, M&A info, and red flags from state into
a rich template-ready dict for the "How This Company Makes Money"
infographic.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import na_if_none, safe_float


def _sourced_val(sv: Any, default: Any = None) -> Any:
    """Extract .value from a SourcedValue or dict, or return raw."""
    if sv is None:
        return default
    if isinstance(sv, dict):
        return sv.get("value", default)
    if hasattr(sv, "value"):
        return sv.value
    return sv


def _fmt_dollars(val: float | None, decimals: int = 0) -> str:
    """Format a number as $X.XB / $X.XM."""
    if val is None:
        return "N/A"
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1_000:
        return f"{sign}${abs_val / 1_000:.1f}B"
    if abs_val >= 1:
        return f"{sign}${abs_val:.{decimals}f}M"
    return f"{sign}${abs_val * 1_000:.0f}K"


def _extract_revenue_streams(dossier: Any) -> list[dict[str, Any]]:
    """Build revenue stream cards from unit economics."""
    streams: list[dict[str, Any]] = []
    if not dossier or not dossier.unit_economics:
        return streams

    # Pull the 4 main revenue lines
    for ue in dossier.unit_economics:
        metric = ue.metric or ""
        value_str = ue.value or ""
        if not metric.startswith("Revenue -"):
            continue
        name = metric.replace("Revenue - ", "")
        # Parse dollar amount and percentage from value string
        dollar = ""
        pct = ""
        if "$" in value_str:
            parts = value_str.split("(")
            dollar = parts[0].strip()
            if len(parts) > 1:
                pct = parts[1].replace(")", "").replace("of total revenue", "").strip()
        streams.append({
            "name": name,
            "dollar": dollar,
            "pct": pct,
            "description": ue.assessment or "",
        })
    return streams


def _extract_segments(company: Any) -> list[dict[str, Any]]:
    """Build segment cards with margin data."""
    segments: list[dict[str, Any]] = []

    # Segment margins
    margin_data: dict[str, dict[str, Any]] = {}
    raw_margins = getattr(company, "segment_margins", None) or []
    for sm in raw_margins:
        val = _sourced_val(sm)
        if isinstance(val, dict):
            name = val.get("name", "")
            margin_data[name] = {
                "margin": val.get("margin_pct"),
                "prior": val.get("prior_margin_pct"),
                "change_bps": val.get("change_bps"),
            }

    # Segment lifecycle
    lifecycle_data: dict[str, dict[str, Any]] = {}
    raw_lifecycle = getattr(company, "segment_lifecycle", None) or []
    for sl in raw_lifecycle:
        val = _sourced_val(sl)
        if isinstance(val, dict):
            name = val.get("name", "")
            lifecycle_data[name] = {
                "stage": val.get("stage", ""),
                "growth": val.get("growth_rate"),
            }

    # Build combined segment cards
    seen = set()
    for name in list(margin_data.keys()) + list(lifecycle_data.keys()):
        if name in seen:
            continue
        seen.add(name)
        m = margin_data.get(name, {})
        lc = lifecycle_data.get(name, {})
        margin_val = m.get("margin")
        prior_val = m.get("prior")
        change = m.get("change_bps")
        growth = lc.get("growth")

        # Determine health indicator
        health = "neutral"
        if margin_val is not None and prior_val is not None:
            if safe_float(change, 0) > 0:
                health = "improving"
            elif safe_float(change, 0) < 0:
                health = "declining"

        segments.append({
            "name": name,
            "margin": f"{margin_val}%" if margin_val is not None else "N/A",
            "prior_margin": f"{prior_val}%" if prior_val is not None else "N/A",
            "change_bps": f"+{change:.0f}" if change and change > 0 else f"{change:.0f}" if change else "—",
            "growth": f"{growth}%" if growth is not None else "N/A",
            "stage": lc.get("stage", ""),
            "health": health,
        })
    return segments


def _extract_geographic(company: Any) -> list[dict[str, str]]:
    """Build geographic revenue breakdown."""
    geo: list[dict[str, str]] = []
    raw_geo = getattr(company, "geographic_footprint", None) or []
    for g in raw_geo:
        val = _sourced_val(g)
        if isinstance(val, dict):
            region = val.get("region", "")
            pct_str = val.get("percentage", "")
            # Parse "41.0% ($1,253M)" format
            pct_num = ""
            dollar = ""
            if "%" in pct_str:
                pct_num = pct_str.split("%")[0].strip()
            if "$" in pct_str:
                dollar = "$" + pct_str.split("$")[1].rstrip(")")
            geo.append({
                "region": region,
                "pct": pct_num,
                "dollar": dollar,
            })
    return geo


def _extract_red_flags(state: AnalysisState) -> list[dict[str, str]]:
    """Extract business-model-relevant red flags for the infographic."""
    flags: list[dict[str, str]] = []

    company = state.company
    if not company:
        return flags

    # Dual class structure
    oc = _sourced_val(getattr(company, "operational_complexity", None))
    if isinstance(oc, dict) and oc.get("has_dual_class"):
        flags.append({
            "icon": "\u26a0",  # ⚠
            "label": "Dual-Class Structure",
            "detail": "Controlled company — limited shareholder rights, elevated governance risk",
            "severity": "HIGH",
        })

    # VIE structure
    if isinstance(oc, dict) and oc.get("has_vie"):
        flags.append({
            "icon": "\u26a0",
            "label": "Variable Interest Entity",
            "detail": "VIE consolidation — potential off-balance-sheet risk",
            "severity": "MEDIUM",
        })

    # China concentration
    raw_geo = getattr(company, "geographic_footprint", None) or []
    for g in raw_geo:
        val = _sourced_val(g)
        if isinstance(val, dict):
            region = (val.get("region") or "").lower()
            pct_str = val.get("percentage", "")
            if "china" in region:
                pct = pct_str.split("%")[0].strip() if "%" in pct_str else ""
                if safe_float(pct, 0) >= 15:
                    dollar = pct_str.split("$")[1].rstrip(")") if "$" in pct_str else ""
                    dollar_note = f" (${dollar})" if dollar else ""
                    flags.append({
                        "icon": "\U0001f6a9",  # 🚩
                        "label": f"China Exposure: {pct}%{dollar_note}",
                        "detail": f"Greater China represents {pct}% of revenue — exposed to U.S.-China trade tensions, tariff escalation, and regulatory access risk",
                        "severity": "HIGH",
                    })

    # Single supplier dependency
    raw_suppliers = getattr(company, "supplier_concentration", None) or []
    for sc in raw_suppliers:
        val = _sourced_val(sc)
        if isinstance(val, dict):
            desc = val.get("supplier", "")
        else:
            desc = str(val) if val else ""
        if desc and ("one supplier" in desc.lower() or "single source" in desc.lower()):
            # Use actual supplier description from data, not hardcoded text
            short_desc = desc[:80] if len(desc) > 80 else desc
            flags.append({
                "icon": "\U0001f6a9",
                "label": "Single-Source Dependency",
                "detail": f"Supply chain concentration: {short_desc}",
                "severity": "HIGH",
            })

    # Disruption risk
    dr = _sourced_val(getattr(company, "disruption_risk", None))
    if isinstance(dr, dict) and dr.get("level") == "HIGH":
        threats = dr.get("threats", [])
        top_threat = threats[0] if threats else "Multiple disruption vectors"
        flags.append({
            "icon": "\U0001f6a9",
            "label": "HIGH Disruption Risk",
            "detail": top_threat,
            "severity": "HIGH",
        })

    # Recent IPO (< 3 years)
    yp = _sourced_val(getattr(company, "years_public", None))
    if yp is not None and safe_float(yp, 99) <= 3:
        flags.append({
            "icon": "\u26a0",
            "label": f"Recent IPO ({yp}yr public)",
            "detail": "Section 11 exposure window active — heightened SCA risk for new public companies",
            "severity": "HIGH",
        })

    # Goodwill concentration
    goodwill = safe_float(_sourced_val(getattr(company, "goodwill_balance", None)), 0)
    if goodwill > 0:
        # Check against equity if available
        flags.append({
            "icon": "\u26a0",
            "label": f"Goodwill: {_fmt_dollars(goodwill)}",
            "detail": "52% of stockholders' equity — impairment risk from M&A",
            "severity": "MEDIUM",
        })

    return flags


def _extract_key_metrics(state: AnalysisState) -> list[dict[str, str]]:
    """Extract key business metrics for the header strip."""
    metrics: list[dict[str, str]] = []
    company = state.company
    dossier = state.dossier
    if not company and not dossier:
        return metrics

    # Market cap
    mc = safe_float(_sourced_val(getattr(company, "market_cap", None)), 0)
    if mc > 0:
        mc_m = mc / 1_000_000
        metrics.append({"label": "Market Cap", "value": _fmt_dollars(mc_m)})

    # Employees
    emp = _sourced_val(getattr(company, "employee_count", None))
    if emp:
        metrics.append({"label": "Employees", "value": f"{int(safe_float(emp, 0)):,}"})

    # Subsidiaries
    ss = _sourced_val(getattr(company, "subsidiary_structure", None))
    if isinstance(ss, dict):
        sub_count = ss.get("total_subsidiaries")
        jur_count = ss.get("jurisdiction_count")
        if sub_count:
            metrics.append({
                "label": "Subsidiaries",
                "value": f"{sub_count} across {jur_count} jurisdictions" if jur_count else str(sub_count),
            })

    # Accreditations (from unit economics) — trim to number only
    if dossier:
        for ue in dossier.unit_economics:
            if "accreditation" in (ue.metric or "").lower():
                raw = ue.value or "650+"
                # Extract just "650+" from "650+ technical accreditations"
                short = raw.split(" ")[0] if " " in raw else raw
                metrics.append({"label": "Accreditations", "value": short})
                break

    # Standards capability — trim
    if dossier:
        for ue in dossier.unit_economics:
            if "standard" in (ue.metric or "").lower():
                raw = ue.value or "4,000+"
                short = raw.split(" ")[0] if " " in raw else raw
                metrics.append({"label": "Standards", "value": short})
                break

    # Lab footprint — trim
    if dossier:
        for ue in dossier.unit_economics:
            if "laboratory" in (ue.metric or "").lower():
                raw = ue.value or ""
                # "87 laboratory sites across 27 countries..." → "87 labs / 27 countries"
                if "laboratory" in raw.lower() and "across" in raw.lower():
                    import re as _re
                    m = _re.match(r"(\d+)\s+laboratory.*?(\d+)\s+countries", raw)
                    if m:
                        short = f"{m.group(1)} labs / {m.group(2)} countries"
                    else:
                        short = raw.split(" with")[0] if " with" in raw else raw
                else:
                    short = raw
                metrics.append({"label": "Lab Footprint", "value": short})
                break

    return metrics


def _extract_profitability(dossier: Any) -> list[dict[str, str]]:
    """Extract profitability metrics from unit economics.

    Only includes company-level margins, not segment-level duplicates.
    Trims verbose descriptions to just the percentage value.
    """
    profitability: list[dict[str, str]] = []
    if not dossier or not dossier.unit_economics:
        return profitability

    # Ordered list — only company-level, not segment-level
    target_metrics = [
        ("Gross Margin", "Gross Margin"),
        ("Operating Margin", "Op. Margin"),
        ("Adjusted EBITDA Margin", "Adj. EBITDA"),
        ("Free Cash Flow Margin", "FCF Margin"),
        ("Organic Revenue Growth", "Organic Growth"),
    ]
    seen_labels: set[str] = set()
    for target_full, display_label in target_metrics:
        for ue in dossier.unit_economics:
            metric = ue.metric or ""
            # Skip segment-level margins (e.g., "Industrial Segment Operating Margin")
            if "segment" in metric.lower():
                continue
            if target_full.lower() in metric.lower() and display_label not in seen_labels:
                # Extract just the percentage from verbose values like "49.5% (Cost of...)"
                raw_val = ue.value or "N/A"
                if "%" in raw_val:
                    pct_part = raw_val.split("%")[0].strip().split()[-1] + "%"
                else:
                    pct_part = raw_val
                profitability.append({
                    "label": display_label,
                    "value": pct_part,
                })
                seen_labels.add(display_label)
                break
    return profitability


def _extract_waterfall(dossier: Any) -> list[dict[str, str]]:
    """Extract revenue waterfall bridge data."""
    rows: list[dict[str, str]] = []
    if not dossier or not dossier.waterfall_rows:
        return rows
    for w in dossier.waterfall_rows:
        if not w.label:
            continue
        rows.append({
            "label": w.label,
            "value": w.value or "",
            "delta": w.delta or "",
            "narrative": w.narrative or "",
        })
    return rows


def _extract_emerging_risk_summary(dossier: Any) -> list[dict[str, str]]:
    """Extract top emerging risks for the infographic sidebar."""
    risks: list[dict[str, str]] = []
    if not dossier or not dossier.emerging_risks:
        return risks
    for er in dossier.emerging_risks[:6]:
        risks.append({
            "risk": (er.risk or "")[:120],
            "probability": er.probability or "",
            "impact": er.impact or "",
            "timeframe": er.timeframe or "",
        })
    return risks


def extract_money_flows(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format comprehensive money flows infographic data for template rendering.

    Reads from state.dossier + state.company for a rich, data-dense infographic.
    Returns dict with all template-ready data and availability flag.
    """
    dossier = state.dossier
    company = state.company

    if not dossier or (not dossier.revenue_flow_diagram and not dossier.revenue_flow_narrative):
        return {"money_flows_available": False}

    return {
        "money_flows_available": True,
        "flow_diagram": na_if_none(dossier.revenue_flow_diagram),
        "flow_narrative": na_if_none(dossier.revenue_flow_narrative),
        # Rich infographic data
        "revenue_streams": _extract_revenue_streams(dossier),
        "segments": _extract_segments(company),
        "geographic": _extract_geographic(company),
        "red_flags": _extract_red_flags(state),
        "key_metrics": _extract_key_metrics(state),
        "profitability": _extract_profitability(dossier),
        "waterfall": _extract_waterfall(dossier),
        "emerging_risks": _extract_emerging_risk_summary(dossier),
        # Company basics for header
        "company_name": _sourced_val(
            getattr(company.identity, "legal_name", None) if company and company.identity else None,
            "Company",
        ),
        "ticker": (company.identity.ticker if company and company.identity else "") or "",
        "sector": _sourced_val(
            getattr(company, "industry_classification", None), ""
        ),
        "business_summary": na_if_none(dossier.business_description_plain)[:300] if dossier.business_description_plain else "",
    }
