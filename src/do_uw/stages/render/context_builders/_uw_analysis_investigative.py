"""Investigative analysis layer — data-driven findings for D&O underwriting.

Builds company-specific investigative insights:
1. Revenue-at-Risk Analysis — quantifies revenue exposed to each key risk
2. Earnings Miss Scenario — models downside if consensus is missed
3. Board Cross-Exposure Network — maps director interlocks and conflicts
4. Risk Factor Changes Analysis — analyzes removed/added risk factors for D&O
5. Settlement Tower Visualization — structures tower layers + case characteristics
"""

from __future__ import annotations

import logging
import re
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.uw_analysis_infographics import (
    fmt_large_number,
)
from do_uw.stages.render.formatters import safe_float

logger = logging.getLogger(__name__)


def _get_info(state: AnalysisState) -> dict[str, Any]:
    """Extract yfinance info dict from state."""
    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        if isinstance(md, dict):
            return md.get("info", {})
        if hasattr(md, "info"):
            return getattr(md, "info", {}) or {}
    return {}


def _sv(v: Any) -> Any:
    """Extract .value from SourcedValue dicts."""
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


def build_revenue_at_risk(state: AnalysisState) -> list[dict[str, Any]]:
    """Build revenue-at-risk analysis from risk factors and geographic data.

    Identifies quantifiable revenue streams threatened by specific risks,
    using geographic footprint, segment data, and risk factor disclosures.
    """
    info = _get_info(state)
    revenue = safe_float(info.get("totalRevenue"), 0)
    if not revenue or revenue <= 0:
        return []

    comp = {}
    if state.company:
        if hasattr(state.company, "model_dump"):
            comp = state.company.model_dump()
        elif isinstance(state.company, dict):
            comp = state.company

    # Build geographic revenue map: region -> (pct, amount)
    geo_raw = comp.get("geographic_footprint", []) or []
    geo_map: dict[str, tuple[float, float]] = {}
    for gf in geo_raw:
        v = _sv(gf)
        if isinstance(v, dict):
            region = v.get("region", "")
            pct_str = str(v.get("percentage", ""))
            pct_match = re.search(r"(\d+\.?\d*)%", pct_str)
            if pct_match and region:
                pct = float(pct_match.group(1))
                geo_map[region.lower()] = (pct, revenue * pct / 100)

    # Identify risk factors with quantifiable revenue exposure
    risks: list[dict[str, Any]] = []

    # Geographic concentration risks
    matched_regions: set[str] = set()
    for region_key, keywords in [
        ("china", ["greater china", "china"]),
        ("europe", ["europe"]),
        ("japan", ["japan"]),
    ]:
        if region_key in matched_regions:
            continue
        for kw in keywords:
            found = False
            for geo_name, (pct, amt) in geo_map.items():
                if kw in geo_name and region_key not in matched_regions:
                    if region_key == "china":
                        detail = (
                            f"{pct:.1f}% of revenue ({fmt_large_number(amt)}) "
                            f"exposed to tariff, trade restriction, and geopolitical risk"
                        )
                    elif region_key == "europe":
                        detail = (
                            f"{pct:.1f}% of revenue ({fmt_large_number(amt)}) "
                            f"subject to EU/DMA regulatory requirements"
                        )
                    else:
                        continue
                    risks.append({
                        "risk": f"{geo_name.title()} operations",
                        "amount": fmt_large_number(amt),
                        "pct": f"{pct:.1f}%",
                        "detail": detail,
                        "severity": "HIGH" if pct >= 15 else "MEDIUM",
                    })
                    matched_regions.add(region_key)
                    found = True
                    break
            if found:
                break

    # Extract risk factors from 10-K YoY for keyword matching
    risk_factors = _get_risk_factors(state)

    # Regulatory/antitrust risks tied to revenue
    _check_regulatory_revenue_risk(risks, risk_factors, revenue, comp)

    # Customer concentration as revenue-at-risk
    cust_conc = comp.get("customer_concentration", []) or []
    for cc in cust_conc:
        v = _sv(cc)
        if isinstance(v, dict):
            cust = v.get("customer", "")
            pct = safe_float(v.get("revenue_pct"), None)
            if cust and pct and pct > 5:
                amt = revenue * pct / 100
                risks.append({
                    "risk": f"{cust} dependency",
                    "amount": fmt_large_number(amt),
                    "pct": f"{pct:.1f}%",
                    "detail": (
                        f"{cust} accounts for {pct:.1f}% of revenue "
                        f"({fmt_large_number(amt)}) — loss or renegotiation "
                        f"creates material earnings impact"
                    ),
                    "severity": "HIGH" if pct >= 20 else "MEDIUM",
                })

    # Sort by severity then amount
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    risks.sort(key=lambda r: (severity_order.get(r["severity"], 9),))

    return risks[:6]


def _get_risk_factors(state: AnalysisState) -> list[dict[str, Any]]:
    """Extract risk factor change list from ten_k_yoy."""
    if not state.extracted or not state.extracted.ten_k_yoy:
        return []
    yoy = state.extracted.ten_k_yoy
    return [
        {
            "title": rc.title,
            "category": rc.category,
            "change_type": rc.change_type,
            "current_severity": rc.current_severity,
        }
        for rc in (yoy.risk_factor_changes or [])
    ]


def _check_regulatory_revenue_risk(
    risks: list[dict[str, Any]],
    risk_factors: list[dict[str, Any]],
    revenue: float,
    comp: dict[str, Any],
) -> None:
    """Check for regulatory risks tied to revenue streams."""
    # Look for antitrust/regulatory risk factors
    antitrust_terms = ["antitrust", "competition", "monopol", "app store", "dma"]
    for rf in risk_factors:
        title = (rf.get("title") or "").lower()
        if any(t in title for t in antitrust_terms):
            # Check if services/platform revenue is quantified in segments
            seg_lifecycle = comp.get("segment_lifecycle", []) or []
            services_rev = 0.0
            for seg in seg_lifecycle:
                v = _sv(seg)
                if isinstance(v, dict):
                    name = (v.get("name") or "").lower()
                    if "service" in name or "platform" in name:
                        rev_amt = safe_float(v.get("revenue_amount"), None)
                        if rev_amt:
                            services_rev = rev_amt
                            break
            if services_rev > 0:
                risks.append({
                    "risk": "Regulatory/antitrust",
                    "amount": fmt_large_number(services_rev),
                    "pct": f"{services_rev / revenue * 100:.1f}%",
                    "detail": (
                        f"Services/platform revenue of {fmt_large_number(services_rev)} "
                        f"({services_rev / revenue * 100:.1f}%) exposed to antitrust "
                        f"and regulatory action"
                    ),
                    "severity": "HIGH",
                })
            break


def build_earnings_miss_scenario(state: AnalysisState) -> dict[str, Any] | None:
    """Build earnings miss scenario analysis.

    Models the impact of missing consensus estimates, including:
    - Current quarter consensus revenue and EPS
    - Downside scenario (low estimate miss)
    - Estimated stock drop based on historical patterns
    - Dollar Damage Line (DDL) calculation
    - Beat/miss track record
    """
    info = _get_info(state)
    md = {}
    if state.acquired_data and state.acquired_data.market_data:
        md_raw = state.acquired_data.market_data
        md = md_raw if isinstance(md_raw, dict) else (
            md_raw.model_dump() if hasattr(md_raw, "model_dump") else {}
        )

    rev_est = md.get("revenue_estimate") or md.get("revenueEstimate", {})
    if not rev_est or not isinstance(rev_est, dict):
        return None

    periods = rev_est.get("period", [])
    avgs = rev_est.get("avg", [])
    lows = rev_est.get("low", [])
    highs = rev_est.get("high", [])
    analysts = rev_est.get("numberOfAnalysts", [])
    growth = rev_est.get("growth", [])

    if not periods or not avgs:
        return None

    # Current quarter (0q) data
    cq_idx = None
    for i, p in enumerate(periods):
        if p == "0q":
            cq_idx = i
            break
    if cq_idx is None:
        cq_idx = 0

    cq_avg = safe_float(avgs[cq_idx] if cq_idx < len(avgs) else None, None)
    cq_low = safe_float(lows[cq_idx] if cq_idx < len(lows) else None, None)
    cq_high = safe_float(highs[cq_idx] if cq_idx < len(highs) else None, None)
    cq_analysts = analysts[cq_idx] if cq_idx < len(analysts) else None
    cq_growth = safe_float(growth[cq_idx] if cq_idx < len(growth) else None, None)

    if cq_avg is None:
        return None

    # Miss magnitude = difference between consensus and low estimate
    miss_pct = 0.0
    if cq_low and cq_avg > 0:
        miss_pct = abs((cq_avg - cq_low) / cq_avg * 100)

    # Estimate stock impact: 2-3x revenue miss % is typical for mega-caps
    price = safe_float(info.get("currentPrice") or info.get("previousClose"), None)
    mcap = safe_float(info.get("marketCap"), None)

    stock_drop_low = miss_pct * 1.5  # conservative
    stock_drop_high = miss_pct * 3.0  # aggressive
    ddl = None
    if mcap and stock_drop_high > 0:
        ddl = mcap * stock_drop_high / 100

    # Beat/miss streak from quarterly earnings
    beat_count = 0
    total_quarters = 0
    if state.extracted and state.extracted.financials:
        yq = state.extracted.financials.yfinance_quarterly or []
        eh = md.get("earnings_history") or {}
        if isinstance(eh, dict):
            eps_actual = eh.get("epsActual", [])
            eps_est = eh.get("epsEstimate", [])
            for i in range(min(len(eps_actual), len(eps_est))):
                if eps_actual[i] is not None and eps_est[i] is not None:
                    total_quarters += 1
                    if eps_actual[i] > eps_est[i]:
                        beat_count += 1

    # Full year data
    fy_idx = None
    for i, p in enumerate(periods):
        if p == "0y":
            fy_idx = i
            break

    fy_avg = safe_float(avgs[fy_idx] if fy_idx is not None and fy_idx < len(avgs) else None, None)
    fy_growth = safe_float(growth[fy_idx] if fy_idx is not None and fy_idx < len(growth) else None, None)

    return {
        "cq_consensus": fmt_large_number(cq_avg) if cq_avg else "N/A",
        "cq_low": fmt_large_number(cq_low) if cq_low else "N/A",
        "cq_high": fmt_large_number(cq_high) if cq_high else "N/A",
        "cq_analysts": cq_analysts,
        "cq_growth": f"{cq_growth * 100:+.1f}%" if cq_growth is not None else "N/A",
        "miss_pct": f"{miss_pct:.1f}%",
        "stock_drop_range": f"{stock_drop_low:.0f}-{stock_drop_high:.0f}%",
        "ddl_if_miss": fmt_large_number(ddl) if ddl else "N/A",
        "beat_streak": f"{beat_count}/{total_quarters}" if total_quarters > 0 else "N/A",
        "beat_probability": (
            "HIGH" if total_quarters > 0 and beat_count == total_quarters
            else ("MEDIUM" if total_quarters > 0 and beat_count / total_quarters >= 0.75
                  else "LOW")
        ) if total_quarters > 0 else "N/A",
        "fy_consensus": fmt_large_number(fy_avg) if fy_avg else "N/A",
        "fy_growth": f"{fy_growth * 100:+.1f}%" if fy_growth is not None else "N/A",
    }


def build_board_cross_exposure(state: AnalysisState) -> list[dict[str, Any]]:
    """Build board cross-exposure network from governance data.

    Maps each director's external board seats and flags potential conflicts.
    """
    if not state.extracted or not state.extracted.governance:
        return []

    gov = state.extracted.governance
    if hasattr(gov, "model_dump"):
        gov_d = gov.model_dump()
    elif isinstance(gov, dict):
        gov_d = gov
    else:
        return []

    bf_raw = gov_d.get("board_forensics", []) or []
    directors: list[dict[str, Any]] = []

    for d in bf_raw:
        name = _sv(d.get("name")) or ""
        title = _sv(d.get("title")) or _sv(d.get("committee_roles")) or ""
        is_ind = _sv(d.get("is_independent"))
        ob_raw = d.get("other_boards", []) or []

        other_boards: list[str] = []
        for ob in ob_raw:
            if isinstance(ob, dict) and "value" in ob:
                other_boards.append(str(ob["value"]))
            elif isinstance(ob, str):
                other_boards.append(ob)

        if not other_boards:
            continue

        # Flag overboarding (>4 total boards is ISS/Glass Lewis concern)
        total_seats = 1 + len(other_boards)
        is_overboarded = total_seats > 4 or (
            # CEOs on >2 total boards
            isinstance(title, str) and "ceo" in title.lower() and total_seats > 2
        )

        # Classify exposure sectors for each external board
        board_exposures: list[dict[str, str]] = []
        for board_name in other_boards:
            exposure = _classify_board_exposure(board_name)
            board_exposures.append({
                "company": board_name,
                "exposure": exposure,
            })

        directors.append({
            "name": name,
            "title": title if isinstance(title, str) else ", ".join(title) if isinstance(title, list) else "",
            "independent": bool(is_ind),
            "other_boards": board_exposures,
            "total_seats": total_seats,
            "is_overboarded": is_overboarded,
        })

    # Sort: overboarded first, then by seat count
    directors.sort(key=lambda d: (-int(d["is_overboarded"]), -d["total_seats"]))

    return directors


def _classify_board_exposure(company_name: str) -> str:
    """Classify a company's SCA exposure sector for conflict flagging."""
    name = company_name.lower()

    # Financial services = high SCA exposure
    if any(k in name for k in ["bank", "jpmorgan", "goldman", "morgan stanley",
                                "citigroup", "wells fargo", "capital one"]):
        return "Financial Services (high SCA)"

    # Tech = high SCA exposure
    if any(k in name for k in ["meta", "google", "alphabet", "microsoft",
                                "amazon", "nvidia", "ibm", "oracle", "salesforce"]):
        return "Technology (high SCA)"

    # Retail = moderate exposure
    if any(k in name for k in ["target", "walmart", "nike", "costco",
                                "home depot", "starbucks"]):
        return "Consumer/Retail"

    # Pharma/biotech = high SCA exposure
    if any(k in name for k in ["pfizer", "merck", "johnson", "abbvie",
                                "lilly", "amgen", "bristol", "novartis"]):
        return "Pharma/Biotech (high SCA)"

    return "Other"


def build_risk_factor_changes_analysis(
    state: AnalysisState,
) -> dict[str, Any] | None:
    """Analyze 10-K risk factor changes for D&O implications.

    Focuses on: removed HIGH severity factors, new factors indicating emerging risks,
    and the concealment argument for plaintiffs.
    """
    if not state.extracted or not state.extracted.ten_k_yoy:
        return None

    yoy = state.extracted.ten_k_yoy

    removed_count = yoy.removed_risk_count or 0
    new_count = yoy.new_risk_count or 0
    escalated_count = yoy.escalated_risk_count or 0

    if removed_count == 0 and new_count == 0 and escalated_count == 0:
        return None

    changes = yoy.risk_factor_changes or []

    # Categorize changes
    removed: list[dict[str, Any]] = []
    added: list[dict[str, Any]] = []
    escalated: list[dict[str, Any]] = []
    de_escalated: list[dict[str, Any]] = []

    for rc in changes:
        entry = {
            "title": rc.title,
            "category": rc.category,
            "current_severity": rc.current_severity,
            "prior_severity": rc.prior_severity or "N/A",
            "summary": rc.summary or "",
        }
        if rc.change_type == "REMOVED":
            removed.append(entry)
        elif rc.change_type == "NEW":
            added.append(entry)
        elif rc.change_type == "ESCALATED":
            escalated.append(entry)
        elif rc.change_type == "DE_ESCALATED":
            de_escalated.append(entry)

    # Count high-severity removed factors
    high_removed = [r for r in removed if r["prior_severity"] == "HIGH"]

    # Build D&O implication
    do_implications: list[str] = []
    if high_removed:
        titles = [r["title"][:60] for r in high_removed[:3]]
        do_implications.append(
            f"{len(high_removed)} HIGH-severity factors removed including: "
            f"{'; '.join(titles)}. If these risks materialize, plaintiffs "
            f"can argue management deliberately concealed known risks."
        )
    if removed_count > 10:
        do_implications.append(
            f"Removing {removed_count} risk factors in one year may indicate "
            f"over-aggressive consolidation. Each removed factor that later "
            f"materializes strengthens a 10b-5 omission claim."
        )
    if escalated:
        titles = [e["title"][:60] for e in escalated[:2]]
        do_implications.append(
            f"{len(escalated)} factors escalated in severity: {'; '.join(titles)}. "
            f"Severity upgrades indicate management acknowledges worsening conditions."
        )
    if new_count > 5:
        do_implications.append(
            f"{new_count} new risk factors added — could signal emerging "
            f"threats management previously failed to disclose."
        )

    return {
        "removed_count": removed_count,
        "new_count": new_count,
        "escalated_count": escalated_count,
        "de_escalated_count": len(de_escalated),
        "high_removed_count": len(high_removed),
        "removed": removed[:5],
        "added": added[:5],
        "escalated": escalated[:3],
        "do_implications": do_implications,
        "years": {
            "current": yoy.current_year,
            "prior": yoy.prior_year,
        },
    }


def build_settlement_tower(state: AnalysisState) -> dict[str, Any] | None:
    """Build enhanced settlement tower visualization data.

    Structures tower layers with visual proportions and case characteristics
    as pass/fail badges for at-a-glance risk assessment.
    """
    if not state.analysis:
        return None

    analysis_d = {}
    if hasattr(state.analysis, "model_dump"):
        analysis_d = state.analysis.model_dump()
    elif isinstance(state.analysis, dict):
        analysis_d = state.analysis

    sp = analysis_d.get("settlement_prediction")
    if not sp or not isinstance(sp, dict):
        return None

    ddl = safe_float(sp.get("ddl_amount"), None)

    # Tower layers
    tower = sp.get("tower_risk", {}) or {}
    layer_order = [
        ("primary", "Primary", "#DC2626"),
        ("low_excess", "Low Excess", "#F59E0B"),
        ("mid_excess", "Mid Excess", "#3B82F6"),
        ("high_excess", "High Excess", "#6B7280"),
    ]

    layers: list[dict[str, Any]] = []
    total_loss = 0.0
    for lk, ll, color in layer_order:
        ld = tower.get(lk, {}) or {}
        if not ld:
            continue
        share = safe_float(ld.get("expected_loss_share_pct"), 0)
        loss = safe_float(ld.get("expected_loss_amount"), 0)
        total_loss += loss
        layers.append({
            "key": lk,
            "name": ll,
            "color": color,
            "share_pct": f"{share:.1f}%",
            "share_raw": share,
            "expected_loss": fmt_large_number(loss) if loss else "N/A",
            "loss_raw": loss,
            "characterization": ld.get("risk_characterization", ""),
        })

    if not layers:
        return None

    # Case characteristics as badges
    chars = sp.get("case_characteristics", {}) or {}
    char_labels = {
        "accounting_fraud": ("Accounting Fraud", True),
        "restatement": ("Restatement", True),
        "insider_selling": ("Insider Selling", True),
        "institutional_lead_plaintiff": ("Institutional Lead Plaintiff", True),
        "top_tier_counsel": ("Top-Tier Counsel", True),
        "sec_investigation": ("SEC Investigation", True),
        "class_period_over_1yr": ("Class Period >1yr", True),
        "multiple_corrective_disclosures": ("Multiple Disclosures", True),
        "going_concern": ("Going Concern", True),
        "officer_termination": ("Officer Termination", True),
    }

    badges: list[dict[str, Any]] = []
    present_count = 0
    for ck, (cl, is_aggravating) in char_labels.items():
        cv = chars.get(ck)
        if cv is not None:
            is_present = bool(cv)
            if is_present:
                present_count += 1
            badges.append({
                "label": cl,
                "present": is_present,
                "icon": "X" if is_present else "check",
                "color": "#DC2626" if is_present else "#16A34A",
                "bg": "#FEF2F2" if is_present else "#F0FDF4",
            })

    return {
        "ddl_amount": fmt_large_number(ddl) if ddl else "N/A",
        "ddl_raw": ddl,
        "total_expected_loss": fmt_large_number(total_loss) if total_loss else "N/A",
        "total_loss_raw": total_loss,
        "layers": layers,
        "characteristics": badges,
        "characteristics_present": present_count,
        "characteristics_total": len(badges),
        "model": sp.get("model", ""),
    }


def build_investigative_context(state: AnalysisState) -> dict[str, Any]:
    """Build all investigative analysis contexts for the worksheet.

    Returns a dict with all five analysis components, each keyed
    for template consumption.
    """
    return {
        "revenue_at_risk": build_revenue_at_risk(state),
        "earnings_miss": build_earnings_miss_scenario(state),
        "board_cross_exposure": build_board_cross_exposure(state),
        "risk_factor_analysis": build_risk_factor_changes_analysis(state),
        "settlement_tower": build_settlement_tower(state),
    }
