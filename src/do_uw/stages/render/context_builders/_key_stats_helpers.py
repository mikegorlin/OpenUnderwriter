"""Key Stats helper functions for extraction and formatting.

Split from key_stats_context.py to keep each file under 300 lines.
Contains: formatting, classification, extraction helpers, geo regions,
customer/segment parsing, litigation summary, mountain chart SVG, governing insight.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float


def sv(sourced: object) -> Any:
    """Extract .value from SourcedValue, or return raw value."""
    return getattr(sourced, "value", sourced)


# Keep private alias for internal use in this module
_sv = sv

# Agency name humanization: SCREAMING_SNAKE_CASE -> readable labels
_AGENCY_DISPLAY: dict[str, str] = {
    "DOJ_FCPA": "DOJ/FCPA",
    "DOJ": "DOJ",
    "SEC": "SEC",
    "FTC": "FTC",
    "EPA": "EPA",
    "FDA": "FDA",
    "CFPB": "CFPB",
    "OSHA": "OSHA",
    "DOL": "DOL",
}


def _humanize_agency(raw: str) -> str:
    """Convert agency codes like DOJ_FCPA to human-readable form."""
    if raw in _AGENCY_DISPLAY:
        return _AGENCY_DISPLAY[raw]
    # Generic: replace underscores with slashes for compound agencies
    return raw.replace("_", "/")


def fmt_large_number(val: float | int | None) -> str:
    """Format large numbers: $13.0B, $7.3B, etc."""
    if val is None:
        return "\u2014"
    val = safe_float(val)
    if abs(val) >= 1e12:
        return f"${val / 1e12:.1f}T"
    if abs(val) >= 1e9:
        return f"${val / 1e9:.1f}B"
    if abs(val) >= 1e6:
        return f"${val / 1e6:.0f}M"
    return f"${val:,.0f}"


def fmt_employees(val: int | float | None) -> str:
    """Format employee count with commas."""
    if val is None:
        return "\u2014"
    return f"{int(val):,}"


def maturity_label(years: int | None) -> str:
    """Classify years public into maturity tier."""
    if years is None:
        return "\u2014"
    if years >= 30:
        return "Legacy"
    if years >= 10:
        return "Established"
    if years >= 3:
        return "Growth"
    return "Recent IPO"


def size_tier(market_cap: float | None) -> str:
    """Classify market cap into size tier."""
    if market_cap is None:
        return "\u2014"
    if market_cap >= 200e9:
        return "Mega"
    if market_cap >= 10e9:
        return "Large"
    if market_cap >= 2e9:
        return "Mid"
    if market_cap >= 300e6:
        return "Small"
    if market_cap >= 50e6:
        return "Micro"
    return "Nano"


def spectrum_pct(val: float | int | None, breakpoints: list[float]) -> int:
    """Map a value to a 0-100 percentage across breakpoints."""
    if val is None or val <= 0:
        return 0
    val = safe_float(val)
    if val <= breakpoints[0]:
        return max(3, int(val / breakpoints[0] * 20))
    for i in range(len(breakpoints) - 1):
        if val <= breakpoints[i + 1]:
            seg = (val - breakpoints[i]) / (breakpoints[i + 1] - breakpoints[i])
            return int(20 * (i + 1) + seg * 20)
    return min(98, 100)


def extract_top_customer(company: object) -> str:
    """Extract top customer concentration summary."""
    cc = getattr(company, "customer_concentration", None) or []
    if not cc:
        return ""
    top = cc[0]
    if hasattr(top, "value"):
        top = top.value
    if isinstance(top, dict):
        name = top.get("customer", "")
        if len(name) > 50:
            name = name[:50] + "..."
        return name
    return str(top)[:60] if top else ""


def extract_segments_text(company: object) -> str:
    """Extract segment lifecycle as comma-separated summary string."""
    segs = getattr(company, "segment_lifecycle", None) or []
    if not segs:
        return ""
    parts = []
    for s in segs[:4]:
        val = s.value if hasattr(s, "value") else s
        if isinstance(val, dict):
            name = val.get("name", "")
            stage = val.get("stage", "")
            parts.append(f"{name} ({stage})")
    return ", ".join(parts) if parts else ""


def extract_customer_list(company: object) -> list[dict[str, str]]:
    """Extract customer concentration as a list of {name, detail} dicts."""
    cc = getattr(company, "customer_concentration", None) or []
    if not cc:
        return []
    result: list[dict[str, str]] = []
    for entry in cc:
        sv = _sv(entry) if hasattr(entry, "value") else entry
        if isinstance(sv, dict):
            raw = sv.get("customer", "")
            if not raw:
                continue
            if ":" in raw:
                parts = raw.split(":", 1)
                result.append({"name": parts[0].strip(), "detail": parts[1].strip()})
            else:
                result.append({"name": raw, "detail": ""})
    return result


def extract_segment_list(company: object) -> list[dict[str, str]]:
    """Extract segment lifecycle as a list of {name, stage, growth} dicts."""
    segs = getattr(company, "segment_lifecycle", None) or []
    if not segs:
        return []
    result: list[dict[str, str]] = []
    for s in segs[:6]:
        sv = _sv(s) if hasattr(s, "value") else s
        if isinstance(sv, dict):
            name = sv.get("name", "")
            stage = sv.get("stage", "").title()
            gr = sv.get("growth_rate")
            growth = f"{gr}%" if gr is not None else "\u2014"
            result.append({"name": name, "stage": stage, "growth": growth})
    return result


# --- Geographic region helpers ---

_REGION_MAP: dict[str, str] = {
    "united states": "north_america",
    "us": "north_america",
    "north america": "north_america",
    "canada": "north_america",
    "europe": "europe",
    "european": "europe",
    "asia": "asia",
    "asia pacific": "asia",
    "china": "asia",
    "japan": "asia",
    "latin america": "south_america",
    "south america": "south_america",
    "brazil": "south_america",
    "africa": "africa",
    "middle east": "middle_east",
    "oceania": "oceania",
    "australia": "oceania",
}


def extract_geo_regions(
    company: object,
) -> tuple[list[str], list[dict[str, str]]]:
    """Extract geographic data as (active_region_ids, breakdown_list).

    Returns:
    - active_regions: list of region IDs like ["north_america", "europe", ...]
    - geo_breakdown: list of {region, pct} dicts
    """
    geo_raw = getattr(company, "geographic_footprint", None) or []
    if not geo_raw:
        return [], []

    active_regions: set[str] = set()
    breakdown: list[dict[str, str]] = []

    for g in geo_raw:
        gv = _sv(g) if hasattr(g, "value") else g
        if not isinstance(gv, dict):
            continue
        region_name = gv.get("region", gv.get("country", ""))
        pct_raw = str(gv.get("percentage", gv.get("revenue_pct", "")))
        pct_full = pct_raw

        # Parse percentage — handle formats like:
        #   "71.5%"
        #   "$178.4B (43% of net sales)"
        #   "28.5% (includes Europe, Canada...)"
        import re
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", pct_raw)
        if pct_match:
            pct_str = pct_match.group(1) + "%"
        elif pct_raw.startswith("$"):
            # Dollar amount without percentage — show as-is
            pct_str = pct_raw.split("(")[0].strip()
        else:
            pct_str = pct_raw.split("(")[0].strip()
            if pct_str and not pct_str.endswith("%"):
                pct_str += "%"

        # Also extract dollar amount if present
        dollar_match = re.search(r"\$[\d,.]+[BMK]?", pct_raw)
        revenue_str = dollar_match.group(0) if dollar_match else ""

        if region_name:
            entry: dict[str, str] = {"region": region_name, "pct": pct_str}
            if revenue_str and pct_str != revenue_str:
                entry["revenue"] = revenue_str
            breakdown.append(entry)
            # Match against known region keywords (use full text for detection)
            full_text = (
                f"{region_name} {pct_full}".lower() if pct_full
                else region_name.lower()
            )
            for keyword, region_id in _REGION_MAP.items():
                if keyword in full_text:
                    active_regions.add(region_id)

    return sorted(active_regions), breakdown


# --- Litigation summary ---

def build_litigation_summary(state: AnalysisState) -> dict[str, Any]:
    """Build consolidated litigation summary for key stats display."""
    result: dict[str, Any] = {
        "sca_status": "None on record",
        "sca_list": [],
        "derivative_status": "None confirmed",
        "derivative_note": "",
        "sec_enforcement": "None",
        "regulatory_items": [],
        "contingent_total": 0.0,
        "contingent_fmt": "\u2014",
    }

    ext = state.extracted
    if not ext or not ext.litigation:
        return result

    lit = ext.litigation

    # SCAs — filter out non-securities cases (product liability, environmental, etc.)
    from do_uw.stages.score.red_flag_gates import _is_regulatory_not_sca

    scas = getattr(lit, "securities_class_actions", None) or []
    genuine_scas = [s for s in scas if not _is_regulatory_not_sca(s)]
    if genuine_scas:
        result["sca_status"] = f"{len(genuine_scas)} on record"
        for sca in genuine_scas[:3]:
            name = getattr(sca, "case_name", None)
            result["sca_list"].append(str(_sv(name)) if name else "Unnamed SCA")

    # Derivative suits
    derivs = getattr(lit, "derivative_suits", None) or []
    if derivs:
        low_conf = sum(
            1 for d in derivs
            if getattr(d, "status", None)
            and getattr(d.status, "confidence", "").upper() == "LOW"
        )
        if low_conf == len(derivs):
            result["derivative_status"] = f"{len(derivs)} unconfirmed"
            result["derivative_note"] = "LOW confidence, no case names"
        else:
            confirmed = len(derivs) - low_conf
            result["derivative_status"] = f"{confirmed} confirmed"
            if low_conf:
                result["derivative_note"] = f"+ {low_conf} unconfirmed"

    # SEC enforcement
    se = getattr(lit, "sec_enforcement", None)
    if se:
        pos = _sv(getattr(se, "pipeline_position", None))
        if pos and pos.upper() != "NONE":
            result["sec_enforcement"] = pos

    # Regulatory proceedings
    reg = getattr(lit, "regulatory_proceedings", None) or []
    agency_counts: dict[str, int] = {}
    for r in reg:
        rv = _sv(r) if hasattr(r, "value") else r
        if isinstance(rv, dict):
            agency = _humanize_agency(rv.get("agency", "Unknown"))
            agency_counts[agency] = agency_counts.get(agency, 0) + 1
    for agency, count in agency_counts.items():
        result["regulatory_items"].append(
            f"{count} {agency} proceeding{'s' if count > 1 else ''}"
        )

    # Contingent liabilities
    # accrued_amount values from LLM extraction are in millions (e.g. 15800.0 = $15.8B)
    cont = getattr(lit, "contingent_liabilities", None) or []
    total = 0.0
    for c in cont:
        amt = getattr(c, "accrued_amount", None)
        val = _sv(amt) if amt else None
        if isinstance(val, (int, float)) and val > 0:
            total += val
    if total > 0:
        result["contingent_total"] = total
        # Convert from millions to full USD for compact formatting
        total_usd = total * 1_000_000 if total < 1_000_000 else total
        result["contingent_fmt"] = f"{fmt_large_number(total_usd)} accrued"

    return result


# --- Regulatory oversight ---

# SIC-based primary regulators (beyond SEC which applies to all public cos)
_SIC_REGULATORS: dict[str, list[dict[str, str]]] = {
    "28": [  # Chemicals
        {"agency": "EPA", "scope": "Environmental compliance, TSCA, Clean Air/Water Act"},
        {"agency": "OSHA", "scope": "Workplace safety, chemical handling"},
        {"agency": "DOT", "scope": "Hazardous materials transportation"},
    ],
    "29": [  # Petroleum
        {"agency": "EPA", "scope": "Environmental compliance, emissions"},
        {"agency": "DOE", "scope": "Energy production and distribution"},
    ],
    "35": [  # Industrial machinery
        {"agency": "OSHA", "scope": "Workplace and equipment safety"},
        {"agency": "EPA", "scope": "Manufacturing emissions"},
    ],
    "36": [  # Electronics
        {"agency": "FCC", "scope": "Communications equipment"},
        {"agency": "EPA", "scope": "E-waste, RoHS compliance"},
    ],
    "38": [  # Instruments
        {"agency": "FDA", "scope": "Medical devices (if applicable)"},
    ],
    "48": [  # Communications
        {"agency": "FCC", "scope": "Telecommunications regulation"},
    ],
    "49": [  # Utilities
        {"agency": "FERC", "scope": "Energy markets, transmission"},
        {"agency": "EPA", "scope": "Emissions, environmental compliance"},
    ],
    "60": [  # Banks
        {"agency": "OCC/Fed", "scope": "Banking regulation, capital requirements"},
        {"agency": "FDIC", "scope": "Deposit insurance, resolution authority"},
    ],
    "61": [  # Non-bank finance
        {"agency": "CFPB", "scope": "Consumer financial protection"},
    ],
    "73": [  # Business services/tech
        {"agency": "FTC", "scope": "Consumer protection, data privacy"},
    ],
    "80": [  # Healthcare
        {"agency": "FDA", "scope": "Drug/device approval, manufacturing"},
        {"agency": "CMS", "scope": "Medicare/Medicaid reimbursement"},
    ],
}


def build_regulatory_oversight(state: AnalysisState) -> list[dict[str, str]]:
    """Build list of regulatory agencies with jurisdiction over the company.

    Combines SIC-based regulators, actual regulatory proceedings,
    and international jurisdiction exposure.
    """
    regulators: list[dict[str, str]] = []
    seen_agencies: set[str] = set()

    # SEC always applies to public companies
    regulators.append({"agency": "SEC", "scope": "Securities regulation, periodic reporting, insider trading", "active": False})
    seen_agencies.add("SEC")

    # SIC-based regulators
    c = state.company
    if c and c.identity:
        sic = _sv(c.identity.sic_code) or ""
        sic_prefix = str(sic)[:2]
        for reg in _SIC_REGULATORS.get(sic_prefix, []):
            if reg["agency"] not in seen_agencies:
                regulators.append({**reg, "active": False})
                seen_agencies.add(reg["agency"])

    # Add agencies from actual regulatory proceedings
    company_name = ""
    if c and c.identity:
        cn_sv = c.identity.legal_name
        company_name = (cn_sv.value if hasattr(cn_sv, "value") else str(cn_sv)) if cn_sv else ""
    ext = state.extracted
    if ext and ext.litigation:
        for rp in getattr(ext.litigation, "regulatory_proceedings", None) or []:
            rv = _sv(rp) if hasattr(rp, "value") else rp
            if isinstance(rv, dict):
                agency = rv.get("agency", "")
                # Filter false-positive regulatory proceedings from low-confidence web search
                rp_desc = rv.get("description", "")
                rp_conf = str(rv.get("confidence", getattr(rp, "confidence", ""))).upper()
                rp_src = str(rv.get("source", getattr(rp, "source", ""))).lower()
                if rp_conf == "LOW" and "web" in rp_src:
                    if "[PDF]" in rp_desc or (company_name and company_name.lower() not in rp_desc.lower()):
                        continue
                proc_type = rv.get("type", "proceeding").replace("_", " ")
                status = rv.get("status", "disclosed")
                # Build clean description from structured fields, not raw filing text
                desc = f"{proc_type} ({status})" if proc_type else "Active proceeding"
                if agency and agency not in seen_agencies:
                    regulators.append({"agency": agency, "scope": f"Active: {desc}", "active": True})
                    seen_agencies.add(agency)
                elif agency and agency in seen_agencies:
                    # Agency already listed — upgrade to active
                    for existing in regulators:
                        if existing["agency"] == agency and not existing.get("active"):
                            existing["scope"] += f" | Active: {desc}"
                            existing["active"] = True
                            break

    # International regulatory exposure from subsidiary jurisdictions
    if c and c.subsidiary_structure:
        ss = _sv(c.subsidiary_structure) or {}
        if isinstance(ss, dict):
            high_reg = [
                j["name"] for j in ss.get("jurisdictions", [])
                if j.get("regulatory_regime") == "HIGH_REG"
            ]
            if high_reg:
                regulators.append({
                    "agency": "International",
                    "scope": f"High-regulatory jurisdictions: {', '.join(high_reg[:4])}",
                    "active": False,
                })

    return regulators


# --- Mountain chart SVG ---

def build_mountain_chart(
    closes: list[float],
    width: int = 200,
    height: int = 60,
) -> str:
    """Build a filled mountain/area SVG chart.

    Uses the starting price as the baseline. Area above baseline
    is filled green, area below is filled red. Crisp, compact.
    """
    if not closes or len(closes) < 5:
        return ""

    step = max(1, len(closes) // 100)
    sampled = closes[::step]
    ns = len(sampled)

    lo = min(sampled)
    hi = max(sampled)
    pad = (hi - lo) * 0.05 or 1.0
    lo -= pad
    hi += pad
    y_range = hi - lo

    baseline = sampled[0]
    x_step = width / max(ns - 1, 1)

    def _y(price: float) -> float:
        return height - ((price - lo) / y_range * height)

    points: list[tuple[float, float]] = []
    for i in range(ns):
        points.append((i * x_step, _y(sampled[i])))

    baseline_y = _y(baseline)

    line_d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area_d = line_d + f" L{points[-1][0]:.1f},{height:.1f} L0,{height:.1f} Z"

    uid = f"mc{id(closes) % 99999}"

    svg = f"""<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" style="overflow:visible">
  <defs>
    <clipPath id="above-{uid}"><rect x="0" y="0" width="{width}" height="{baseline_y:.1f}"/></clipPath>
    <clipPath id="below-{uid}"><rect x="0" y="{baseline_y:.1f}" width="{width}" height="{height - baseline_y:.1f}"/></clipPath>
  </defs>
  <line x1="0" y1="{baseline_y:.1f}" x2="{width}" y2="{baseline_y:.1f}"
        stroke="#94a3b8" stroke-width="0.5" stroke-dasharray="3,2"/>
  <path d="{area_d}" fill="#22c55e" opacity="0.15" clip-path="url(#above-{uid})"/>
  <path d="{area_d}" fill="#ef4444" opacity="0.15" clip-path="url(#below-{uid})"/>
  <path d="{line_d}" fill="none" stroke="#22c55e" stroke-width="1.5" clip-path="url(#above-{uid})"/>
  <path d="{line_d}" fill="none" stroke="#ef4444" stroke-width="1.5" clip-path="url(#below-{uid})"/>
  <circle cx="{points[-1][0]:.1f}" cy="{points[-1][1]:.1f}" r="2.5"
          fill="{'#22c55e' if sampled[-1] >= baseline else '#ef4444'}"/>
</svg>"""
    return svg


# --- Governing insight ---

def governing_insight(
    legal_name: str,
    size_tier: str,
    maturity: str,
    industry: str,
    subsidiary_count: int | None,
) -> str:
    """Generate one-sentence governing insight about the company."""
    parts = []

    size_desc = size_tier.lower() + "-cap" if size_tier != "\u2014" else ""
    mat_desc = maturity.lower() if maturity != "\u2014" else ""

    name_short = (
        legal_name.split("/")[0].strip() if "/" in legal_name else legal_name
    )
    parts.append(f"{name_short} is a {size_desc}")
    if mat_desc:
        parts[0] += f", {mat_desc}"
    parts[0] += f" {industry.lower()} company"

    if subsidiary_count and subsidiary_count > 100:
        parts.append(
            f"operating through {subsidiary_count} subsidiaries"
            " across multiple jurisdictions"
        )

    return " ".join(parts) + "."


# --- Revenue model description ---

_REVENUE_MODEL_DESCRIPTIONS: dict[str, str] = {
    "PRODUCT": "Product sales — manufactures and sells physical goods",
    "SERVICE": "Service-based — revenue from professional/managed services",
    "SUBSCRIPTION": "Subscription/recurring — contracted recurring revenue",
    "HYBRID": "Hybrid — combination of product sales and service revenue",
    "PLATFORM": "Platform/marketplace — facilitates transactions between parties",
    "LICENSING": "Licensing/royalties — intellectual property monetization",
}


def describe_revenue_model(raw: str, business_desc: str) -> str:
    """Expand revenue model code into a human-readable description."""
    if not raw or raw == "\u2014":
        return "\u2014"
    code = raw.upper().replace(" ", "_")
    base = _REVENUE_MODEL_DESCRIPTIONS.get(code, raw.replace("_", " ").title())
    if code == "HYBRID" and business_desc:
        desc_lower = business_desc.lower() if isinstance(business_desc, str) else ""
        products = []
        if "manufactur" in desc_lower:
            products.append("manufacturing")
        if "service" in desc_lower or "maintenance" in desc_lower:
            products.append("services")
        if "distribution" in desc_lower or "distribut" in desc_lower:
            products.append("distribution")
        if products:
            base = f"Hybrid — {' + '.join(products)}"
    return base


# --- Risk pulse ---

def build_risk_pulse(state: "AnalysisState") -> list[dict[str, Any]]:
    """Build a compact 'risk pulse' — one-line risk indicators per domain.

    Each item: {domain, label, status (clean/watch/elevated/critical), detail}
    Used for the at-a-glance risk strip on the Key Stats page.
    """
    from do_uw.models.state import AnalysisState as _AS  # noqa: F811
    pulse: list[dict[str, Any]] = []
    scoring = state.scoring
    ext = state.extracted

    # 1. Litigation — filter to genuine SCAs only
    from do_uw.stages.score.red_flag_gates import _is_regulatory_not_sca as _not_sca

    lit_status, lit_detail = "clean", "No active SCAs"
    if ext and ext.litigation:
        scas = getattr(ext.litigation, "securities_class_actions", None) or []
        genuine_scas = [s for s in scas if not _not_sca(s)]
        active = _sv(getattr(ext.litigation, "active_matter_count", None)) or 0
        if genuine_scas:
            lit_status, lit_detail = "critical", f"{len(genuine_scas)} SCA(s)"
        elif active and int(active) > 5:
            lit_status, lit_detail = "elevated", f"{active} active matters"
        elif active and int(active) > 0:
            lit_status, lit_detail = "watch", f"{active} active matters"
    pulse.append({"domain": "litigation", "label": "Litigation", "status": lit_status, "detail": lit_detail})

    # 2. Financial
    fin_status, fin_detail = "clean", "No distress indicators"
    if scoring and scoring.factor_scores:
        for f in scoring.factor_scores:
            if getattr(f, "factor_id", "") == "F3":
                if (getattr(f, "points_deducted", None) or 0) > 3:
                    fin_status, fin_detail = "elevated", "Audit flags"
                elif (getattr(f, "points_deducted", None) or 0) > 0:
                    fin_status, fin_detail = "watch", "Minor flags"
                break
    pulse.append({"domain": "financial", "label": "Financial", "status": fin_status, "detail": fin_detail})

    # 3. Governance
    gov_status, gov_detail = "clean", "Standard governance"
    if scoring and scoring.factor_scores:
        for f in scoring.factor_scores:
            if getattr(f, "factor_id", "") == "F2":
                if (getattr(f, "points_deducted", None) or 0) > 3:
                    gov_status, gov_detail = "elevated", "Governance gaps"
                elif (getattr(f, "points_deducted", None) or 0) > 0:
                    gov_status, gov_detail = "watch", "Minor concerns"
                break
    pulse.append({"domain": "governance", "label": "Governance", "status": gov_status, "detail": gov_detail})

    # 4. Market / Stock
    mkt_status, mkt_detail = "clean", "Stable trading"
    if ext and ext.market and ext.market.stock:
        s = ext.market.stock
        vol = _sv(getattr(s, "volatility_annual", None))
        if vol and safe_float(vol) > 0.50:
            mkt_status, mkt_detail = "elevated", f"High vol ({vol:.0%})"
        elif vol and safe_float(vol) > 0.35:
            mkt_status, mkt_detail = "watch", "Moderate vol"
    pulse.append({"domain": "market", "label": "Market", "status": mkt_status, "detail": mkt_detail})

    # 5. SEC/Regulatory
    sec_status, sec_detail = "clean", "No enforcement"
    if ext and ext.litigation and ext.litigation.sec_enforcement:
        se = ext.litigation.sec_enforcement
        pipeline = _sv(getattr(se, "pipeline_position", None)) or "None"
        if pipeline.lower() not in ("none", "no action", ""):
            sec_status, sec_detail = "critical", pipeline
    pulse.append({"domain": "sec", "label": "SEC", "status": sec_status, "detail": sec_detail})

    return pulse


# Factor ID to human-readable strength/vulnerability labels
_FACTOR_STRENGTHS: dict[str, str] = {
    "F1": "Clean litigation history",
    "F2": "Strong board governance",
    "F3": "Clean audit & accounting",
    "F4": "Healthy financial position",
    "F5": "Reliable guidance track record",
    "F6": "Low regulatory risk",
    "F7": "Favorable market sentiment",
    "F8": "Simple corporate structure",
    "F9": "Stable leadership team",
    "F10": "Conservative insider activity",
}

_FACTOR_VULNERABILITIES: dict[str, str] = {
    "F1": "Prior litigation exposure",
    "F2": "Governance weaknesses",
    "F3": "Audit/accounting concerns",
    "F4": "Financial stress indicators",
    "F5": "Guidance miss history",
    "F6": "Regulatory risk exposure",
    "F7": "Negative market sentiment",
    "F8": "Complex corporate structure",
    "F9": "Leadership instability",
    "F10": "Concerning insider activity",
}


def build_strengths_vulnerabilities(state: "AnalysisState") -> dict[str, list[str]]:
    """Build strengths and vulnerabilities lists from scoring factors."""
    strengths: list[str] = []
    vulnerabilities: list[str] = []

    if not state.scoring or not state.scoring.factor_scores:
        return {"strengths": strengths, "vulnerabilities": vulnerabilities}

    for f in state.scoring.factor_scores:
        fid = getattr(f, "factor_id", "")
        deducted = getattr(f, "points_deducted", None) or 0
        max_pts = getattr(f, "max_points", 10)

        if deducted == 0 and fid in _FACTOR_STRENGTHS:
            strengths.append(_FACTOR_STRENGTHS[fid])
        elif deducted > max_pts * 0.3 and fid in _FACTOR_VULNERABILITIES:
            vulnerabilities.append(_FACTOR_VULNERABILITIES[fid])

    return {
        "strengths": strengths[:4],
        "vulnerabilities": vulnerabilities[:4],
    }
