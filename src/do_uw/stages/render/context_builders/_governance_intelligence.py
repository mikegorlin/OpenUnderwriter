"""Governance intelligence context builders for Phase 135.

Three builder functions that format governance intelligence data for templates.
Pure data formatters -- no evaluative logic, no D&O commentary generation.
Each function reads from AnalysisState and returns a dict.

- build_officer_backgrounds: per-officer investigation cards
- build_shareholder_rights: 8-provision checklist with defense posture
- build_per_insider_activity: per-insider trading with 10b5-1 badges
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.governance_intelligence import (
    OfficerBackground,
    ShareholderRightsInventory,
    ShareholderRightsProvision,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.officer_background import (
    aggregate_per_insider,
    assess_suitability,
    detect_serial_defendants,
    extract_prior_companies_from_bio,
    query_officer_prior_sca,
)
from do_uw.stages.render.formatters import format_currency, format_percentage, safe_float
from do_uw.stages.render.state_paths import (
    get_board_profile,
    get_governance_forensics,
    get_insider_transactions,
    get_insider_transactions_yfinance,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shareholder rights provision definitions (8 provisions per D-07)
# (field_name, display_label, is_protective,
#  yes_implication, no_implication, yes_defense, no_defense)
# ---------------------------------------------------------------------------

_RIGHTS_PROVISIONS: list[tuple[str, str, bool, str, str, str, str]] = [
    (
        "classified_board",
        "Board Classification",
        True,
        "Staggered terms limit hostile takeover but increase Revlon duty scrutiny",
        "Annual elections -- shareholders can replace full board",
        "Protective",
        "Shareholder-Friendly",
    ),
    (
        "poison_pill",
        "Poison Pill / Rights Plan",
        True,
        "Deters hostile bids but may entrench management",
        "No poison pill -- vulnerable to hostile acquisition",
        "Protective",
        "Shareholder-Friendly",
    ),
    (
        "supermajority_voting",
        "Supermajority Requirements",
        True,
        "Higher bar for charter/bylaw changes limits shareholder power",
        "Simple majority -- shareholders can effect changes more easily",
        "Protective",
        "Shareholder-Friendly",
    ),
    (
        "proxy_access_threshold",
        "Proxy Access",
        False,
        "Shareholders can nominate directors -- increases board accountability",
        "No proxy access -- board controls nomination process",
        "Shareholder-Friendly",
        "Protective",
    ),
    (
        "cumulative_voting",
        "Cumulative Voting",
        False,
        "Minority shareholders can concentrate votes -- increases board diversity risk",
        "No cumulative voting -- standard plurality/majority",
        "Shareholder-Friendly",
        "Neutral",
    ),
    (
        "written_consent_allowed",
        "Written Consent",
        False,
        "Shareholders can act without meeting -- increases activist power",
        "No written consent -- actions require formal meeting",
        "Shareholder-Friendly",
        "Protective",
    ),
    (
        "special_meeting_threshold",
        "Special Meeting Rights",
        False,
        "Shareholders can call special meetings -- increases responsiveness",
        "No/high threshold -- limits shareholder ability to force votes",
        "Shareholder-Friendly",
        "Protective",
    ),
    (
        "forum_selection_clause",
        "Forum Selection",
        True,
        "Channels litigation to chosen forum -- predictable defense environment",
        "No forum selection -- litigation risk across multiple jurisdictions",
        "Protective",
        "Shareholder-Friendly",
    ),
]


# ---------------------------------------------------------------------------
# Builder 1: Officer Backgrounds (GOV-01, GOV-02)
# ---------------------------------------------------------------------------


def build_officer_backgrounds(state: AnalysisState) -> dict[str, Any]:
    """Build officer background investigation context for template.

    Reads leadership forensic profiles, extracts prior companies from bios,
    cross-references against Supabase SCA database, and flags serial defendants.

    Returns dict with:
        officer_backgrounds: list of dicts (name, title, prior_companies, etc.)
        has_officer_backgrounds: bool
        serial_defendant_count: int
    """
    gov = state.extracted.governance if state.extracted else None
    if gov is None:
        return {"officer_backgrounds": [], "has_officer_backgrounds": False, "serial_defendant_count": 0}

    leadership = gov.leadership if gov else None
    executives = leadership.executives if leadership else None
    if not executives:
        return {"officer_backgrounds": [], "has_officer_backgrounds": False, "serial_defendant_count": 0}

    # Build OfficerBackground objects from leadership profiles
    officers: list[OfficerBackground] = []
    all_prior_company_names: list[str] = []

    for exec_profile in executives:
        name = exec_profile.name.value if hasattr(exec_profile.name, "value") else str(exec_profile.name or "")
        title = exec_profile.title.value if hasattr(exec_profile.title, "value") else str(exec_profile.title or "")

        # Extract bio text
        bio_sv = getattr(exec_profile, "bio_summary", None)
        bio_text = bio_sv.value if bio_sv and hasattr(bio_sv, "value") else ""
        has_full_bio = bool(bio_text and len(str(bio_text)) > 20)

        # Extract prior companies from bio
        prior_companies = extract_prior_companies_from_bio(str(bio_text)) if bio_text else []
        for pc in prior_companies:
            if pc.company_name:
                all_prior_company_names.append(pc.company_name)

        # Collect personal litigation
        prior_lit = getattr(exec_profile, "prior_litigation", None) or []
        personal_litigation = [
            str(lit.value) if hasattr(lit, "value") and hasattr(lit, "source") else str(lit)
            for lit in prior_lit
        ]

        officer = OfficerBackground(
            name=name,
            title=title,
            prior_companies=prior_companies,
            personal_litigation=personal_litigation,
        )
        officers.append(officer)

    # Batch Supabase query for all prior company names
    sca_results: list[dict[str, Any]] = []
    if all_prior_company_names:
        try:
            sca_results = query_officer_prior_sca(all_prior_company_names)
        except Exception:
            logger.warning("Officer prior SCA query failed", exc_info=True)

    # Detect serial defendants
    if sca_results:
        officers = detect_serial_defendants(officers, sca_results)

    # Assess suitability for each officer
    has_litigation_search = bool(sca_results) or bool(all_prior_company_names)
    for officer in officers:
        has_full_bio = bool(officer.prior_companies)  # proxy: bio had extractable companies
        level, reason = assess_suitability(officer, has_full_bio, has_litigation_search)
        officer.suitability = level
        officer.suitability_reason = reason

    # Format for template
    serial_count = sum(1 for o in officers if o.is_serial_defendant)
    officer_dicts: list[dict[str, Any]] = []
    for o in officers:
        officer_dicts.append({
            "name": o.name,
            "title": o.title,
            "prior_companies": [
                {"company_name": pc.company_name, "role": pc.role, "years": pc.years}
                for pc in o.prior_companies
            ],
            "sca_exposures": [
                {
                    "company_name": exp.company_name,
                    "case_caption": exp.case_caption,
                    "class_period": f"{exp.class_period_start} to {exp.class_period_end}",
                    "officer_role_at_time": exp.officer_role_at_time,
                    "settlement": f"${exp.settlement_amount_m:.1f}M" if exp.settlement_amount_m else "N/A",
                }
                for exp in o.sca_exposures
            ],
            "is_serial_defendant": o.is_serial_defendant,
            "personal_litigation": o.personal_litigation,
            "suitability": o.suitability,
            "suitability_reason": o.suitability_reason,
        })

    return {
        "officer_backgrounds": officer_dicts,
        "has_officer_backgrounds": bool(officer_dicts),
        "serial_defendant_count": serial_count,
    }


# ---------------------------------------------------------------------------
# Builder 2: Shareholder Rights Inventory (GOV-03, GOV-04)
# ---------------------------------------------------------------------------


def _get_provision_status(board: Any, field_name: str) -> tuple[str, Any]:
    """Read provision status from BoardProfile field.

    Returns (status_str, raw_value) where status_str is Yes/No/N/A.
    """
    sv = getattr(board, field_name, None)
    if sv is None:
        return ("N/A", None)

    val = sv.value if hasattr(sv, "value") else sv
    if val is None:
        return ("N/A", None)

    # Boolean fields
    if isinstance(val, bool):
        return ("Yes" if val else "No", val)

    # String fields (proxy_access_threshold, special_meeting_threshold, forum_selection_clause)
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("n/a", "none", "null"):
        return ("N/A", None)

    # Non-empty string means provision exists
    return ("Yes", val_str)


def build_shareholder_rights(state: AnalysisState) -> dict[str, Any]:
    """Build shareholder rights inventory context for template.

    Reads board governance provisions, builds 8-provision checklist,
    and computes overall defense posture (Strong/Moderate/Weak).

    Returns dict with:
        shareholder_rights: dict (provisions list, overall_defense_posture, counts)
        has_shareholder_rights: bool
    """
    board = get_board_profile(state)
    if board is None:
        return {"shareholder_rights": {}, "has_shareholder_rights": False}

    provisions: list[dict[str, str]] = []
    protective_count = 0
    shareholder_friendly_count = 0

    for field_name, display_name, is_protective, yes_impl, no_impl, yes_defense, no_defense in _RIGHTS_PROVISIONS:
        status, raw_val = _get_provision_status(board, field_name)
        details = str(raw_val) if raw_val is not None and not isinstance(raw_val, bool) else ""

        if status == "Yes":
            defense_strength = yes_defense
            do_implication = yes_impl
            if defense_strength == "Protective":
                protective_count += 1
            elif defense_strength == "Shareholder-Friendly":
                shareholder_friendly_count += 1
        elif status == "No":
            defense_strength = no_defense
            do_implication = no_impl
            if defense_strength == "Protective":
                protective_count += 1
            elif defense_strength == "Shareholder-Friendly":
                shareholder_friendly_count += 1
        else:
            defense_strength = "Neutral"
            do_implication = "Data not available -- cannot assess"

        provisions.append({
            "provision_name": display_name,
            "status": status,
            "details": details,
            "defense_strength": defense_strength,
            "do_implication": do_implication,
        })

    # Compute defense posture per D-09
    if protective_count >= 5:
        posture = "Strong"
    elif protective_count >= 3:
        posture = "Moderate"
    else:
        posture = "Weak"

    inventory = {
        "provisions": provisions,
        "overall_defense_posture": posture,
        "protective_count": protective_count,
        "shareholder_friendly_count": shareholder_friendly_count,
    }

    return {
        "shareholder_rights": inventory,
        "has_shareholder_rights": True,
    }


# ---------------------------------------------------------------------------
# Builder 3: Per-Insider Activity (GOV-05)
# ---------------------------------------------------------------------------


def build_per_insider_activity(state: AnalysisState) -> dict[str, Any]:
    """Build per-insider trading activity context for template.

    Reads insider transactions, aggregates by insider, formats for display.

    Returns dict with:
        per_insider_activity: list of formatted dicts
        has_per_insider_activity: bool
        insider_count: int
    """
    transactions = get_insider_transactions(state)

    # Fallback: read raw yfinance insider_transactions from acquired_data
    if not transactions:
        per_insider = _aggregate_from_yfinance(state)
        if per_insider:
            formatted: list[dict[str, Any]] = []
            total_sold_all = 0.0
            for pi in per_insider:
                total_sold_all += pi["total_sold_usd"]
                formatted.append(pi)
            return {
                "per_insider_activity": formatted,
                "has_per_insider_activity": True,
                "insider_count": len(formatted),
                "total_insider_sales_fmt": format_currency(total_sold_all, compact=True),
            }
        return {"per_insider_activity": [], "has_per_insider_activity": False, "insider_count": 0}

    # Get shares outstanding for %O/S calculation
    shares_outstanding = _get_shares_outstanding(state)

    # Aggregate using extraction function
    per_insider = aggregate_per_insider(transactions, shares_outstanding)
    if not per_insider:
        return {"per_insider_activity": [], "has_per_insider_activity": False, "insider_count": 0}

    # Format for template
    formatted: list[dict[str, Any]] = []
    total_sold_all = 0.0
    for pi in per_insider:
        total_sold_all += pi.total_sold_usd
        formatted.append({
            "name": pi.name,
            "position": pi.position,
            "total_sold_usd": pi.total_sold_usd,
            "total_sold_fmt": format_currency(pi.total_sold_usd, compact=True),
            "pct_os": format_percentage(pi.total_sold_pct_os) if pi.total_sold_pct_os is not None else "N/A",
            "tx_count": pi.tx_count,
            "ten_b5_1_badge": "10b5-1" if pi.has_10b5_1 else "Discretionary",
            "activity_period": f"{pi.activity_period_start} to {pi.activity_period_end}" if pi.activity_period_start else "N/A",
        })

    return {
        "per_insider_activity": formatted,
        "has_per_insider_activity": True,
        "insider_count": len(formatted),
        "total_insider_sales_fmt": format_currency(total_sold_all, compact=True),
    }


def _aggregate_from_yfinance(state: AnalysisState) -> list[dict[str, Any]]:
    """Aggregate per-insider activity directly from yfinance acquired data.

    Fallback when InsiderTradingProfile.transactions is empty but raw
    yfinance insider_transactions dict is populated in acquired_data.
    """
    it = get_insider_transactions_yfinance(state)
    if not it:
        return []

    names = it.get("Insider", [])
    positions = it.get("Position", [])
    shares_list = it.get("Shares", [])
    dates = it.get("Start Date", [])
    if not names:
        return []

    # Aggregate by insider name
    agg: dict[str, dict[str, Any]] = {}
    for i in range(len(names)):
        name = str(names[i]) if i < len(names) else ""
        if not name:
            continue
        pos = str(positions[i]) if i < len(positions) else ""
        shares = safe_float(shares_list[i] if i < len(shares_list) else 0, 0)
        dt = str(dates[i])[:10] if i < len(dates) else ""

        if name not in agg:
            agg[name] = {
                "name": name, "position": pos, "total_shares": 0,
                "tx_count": 0, "first_date": dt, "last_date": dt,
            }
        entry = agg[name]
        # yfinance insider_transactions reports share counts (positive = sale)
        entry["total_shares"] += abs(shares) if shares else 0
        entry["tx_count"] += 1
        if dt and (not entry["first_date"] or dt < entry["first_date"]):
            entry["first_date"] = dt
        if dt and dt > entry["last_date"]:
            entry["last_date"] = dt

    # Get stock price for dollar estimation
    price = 0.0
    if state.extracted and state.extracted.market and state.extracted.market.stock:
        cp = state.extracted.market.stock.current_price
        price = safe_float(cp.value if cp else 0, 0)

    result = []
    for entry in sorted(agg.values(), key=lambda x: x["total_shares"], reverse=True):
        if entry["total_shares"] == 0:
            continue
        dollar_est = entry["total_shares"] * price if price > 0 else 0
        result.append({
            "name": entry["name"],
            "position": entry["position"],
            "total_sold_usd": dollar_est,
            "total_sold_fmt": format_currency(dollar_est, compact=True) if dollar_est else "N/A",
            "pct_os": "N/A",  # Can't compute without shares_outstanding
            "tx_count": entry["tx_count"],
            "ten_b5_1_badge": "Unknown",  # yfinance doesn't have 10b5-1 data
            "activity_period": f"{entry['first_date']} to {entry['last_date']}" if entry["first_date"] else "N/A",
        })

    return result[:20]  # Top 20 sellers


def _get_shares_outstanding(state: AnalysisState) -> float | None:
    """Get shares outstanding from XBRL or company profile."""
    # Try company-level first
    if state.company:
        company_so = getattr(state.company, "shares_outstanding", None)
        if company_so is not None:
            val = company_so.value if hasattr(company_so, "value") else company_so
            f = safe_float(val, 0.0)
            if f > 0:
                return f

    # Try XBRL financials
    try:
        financials = state.extracted.financials if state.extracted else None
        statements = financials.statements if financials else None
        if statements and isinstance(statements, dict):
            for key in ("shares_outstanding", "CommonStockSharesOutstanding", "EntityCommonStockSharesOutstanding"):
                val = statements.get(key)
                if val is not None:
                    f = safe_float(val, 0.0)
                    if f > 0:
                        return f
    except Exception:
        pass

    return None


__all__ = [
    "build_officer_backgrounds",
    "build_per_insider_activity",
    "build_shareholder_rights",
]
