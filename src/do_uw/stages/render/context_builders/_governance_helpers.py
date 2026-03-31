"""Governance helper functions — extracted to keep governance.py under 300 lines.

Contains compensation analysis builder, display data builders (executive
profiles, board member profiles), and shared SourcedValue utilities
used by the governance context builder.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
    safe_float,
)


def _sv_str(sv: Any, fallback: str = "N/A") -> str:
    """Extract string value from a SourcedValue or return fallback."""
    if sv is None:
        return fallback
    val: Any = sv.value if hasattr(sv, "value") else sv
    return str(val) if val is not None else fallback


def _sv_bool(sv: Any) -> str:
    """Format a SourcedValue[bool] as Yes/No/N/A."""
    if sv is None:
        return "N/A"
    return "Yes" if sv.value else "No"


def _sv_source(sv: Any) -> str:
    """Extract source string from a SourcedValue, or empty string."""
    return str(sv.source or "") if sv is not None and hasattr(sv, "source") else ""


def _sv_confidence(sv: Any) -> str:
    """Extract confidence level from a SourcedValue, or empty string."""
    return str(sv.confidence or "") if sv is not None and hasattr(sv, "confidence") else ""


def _safe_ceo_comp(comp: Any) -> str:
    """Format CEO compensation, filtering out year-as-comp extraction bugs."""
    if comp.ceo_total_comp is None:
        return "N/A"
    val = comp.ceo_total_comp.value
    if val is None:
        return "N/A"
    fval = safe_float(val)
    if 1990 <= fval <= 2035:
        return "N/A"
    if fval < 50_000:
        return "N/A"
    return format_currency(fval, compact=True)


def _safe_comp_currency(sv: Any) -> str:
    """Format a SourcedValue[float] as compact currency, or N/A."""
    if sv is None:
        return "N/A"
    val = sv.value if hasattr(sv, "value") else sv
    if val is None or safe_float(val) < 0:
        return "N/A"
    return format_currency(safe_float(val), compact=True)


def build_compensation_analysis(comp: Any) -> dict[str, Any]:
    """Build full compensation analysis dict for template rendering.

    Extracts all CompensationAnalysis fields with source attribution
    and confidence tracking for SURF-08 compliance.
    """
    ca: dict[str, Any] = {}

    # CEO pay breakdown
    ca["ceo_total"] = _safe_ceo_comp(comp)
    ca["ceo_salary"] = _safe_comp_currency(comp.ceo_salary)
    ca["ceo_bonus"] = _safe_comp_currency(comp.ceo_bonus)
    ca["ceo_equity"] = _safe_comp_currency(comp.ceo_equity)
    ca["ceo_other"] = _safe_comp_currency(comp.ceo_other)

    # Pay ratio and peer comparison
    pr = comp.ceo_pay_ratio
    ca["ceo_pay_ratio"] = f"{int(pr.value)}:1" if pr and pr.value is not None else "N/A"
    pvpm = comp.ceo_pay_vs_peer_median
    if pvpm is not None and pvpm.value is not None:
        r = safe_float(pvpm.value)
        diff = abs(r - 1.0) * 100
        label = "above" if r >= 1.0 else "below"
        ca["ceo_pay_vs_peer_median"] = f"{r:.2f}x ({diff:.0f}% {label} median)"
    else:
        ca["ceo_pay_vs_peer_median"] = "N/A"

    # Compensation mix
    ca["comp_mix"] = [
        {"name": k.replace("_", " ").title(), "pct": f"{v:.0f}%", "pct_num": f"{v:.0f}"}
        for k, v in comp.comp_mix.items()
    ] if comp.comp_mix else []

    # Performance metrics, say-on-pay, clawback
    ca["performance_metrics"] = [_sv_str(pm) for pm in comp.performance_metrics] if comp.performance_metrics else []
    ca["say_on_pay_pct"] = format_percentage(comp.say_on_pay_pct.value if comp.say_on_pay_pct else None)
    ca["say_on_pay_trend"] = _sv_str(comp.say_on_pay_trend, fallback="N/A")
    ca["has_clawback"] = _sv_bool(comp.has_clawback)
    if comp.clawback_scope is not None:
        scope = str(comp.clawback_scope.value).upper()
        ca["clawback_scope"] = (
            "Broader than Dodd-Frank" if "BROADER" in scope
            else "Dodd-Frank Minimum" if "DODD" in scope
            else str(comp.clawback_scope.value)
        )
    else:
        ca["clawback_scope"] = "N/A"

    # Related-party transactions and perquisites
    ca["related_party_transactions"] = [_sv_str(r) for r in comp.related_party_transactions] if comp.related_party_transactions else []
    ca["notable_perquisites"] = [_sv_str(p) for p in comp.notable_perquisites] if comp.notable_perquisites else []

    # SURF-08: Source attribution and confidence tracking (single pass)
    _sv_fields = [
        ("ceo_total", comp.ceo_total_comp),
        ("ceo_salary", comp.ceo_salary),
        ("ceo_bonus", comp.ceo_bonus),
        ("ceo_equity", comp.ceo_equity),
        ("ceo_other", comp.ceo_other),
        ("ceo_pay_ratio", comp.ceo_pay_ratio),
        ("ceo_pay_vs_peer_median", comp.ceo_pay_vs_peer_median),
        ("say_on_pay_pct", comp.say_on_pay_pct),
        ("say_on_pay_trend", comp.say_on_pay_trend),
        ("has_clawback", comp.has_clawback),
        ("clawback_scope", comp.clawback_scope),
    ]
    sources: dict[str, str] = {}
    confidence: dict[str, str] = {}
    for field_name, sv_field in _sv_fields:
        src = _sv_source(sv_field)
        if src:
            sources[field_name] = src
        conf = _sv_confidence(sv_field)
        if conf:
            confidence[field_name] = conf
    ca["_sources"] = sources
    ca["_confidence"] = confidence

    return ca


def _build_sourced_detail(items: list[Any]) -> list[dict[str, str]]:
    """Build list of dicts with factor/source/confidence from SourcedValue list."""
    return [
        {
            "factor": _sv_str(item),
            "source": str(item.source) if hasattr(item, "source") and item.source else "",
            "confidence": str(item.confidence) if hasattr(item, "confidence") and item.confidence else "LOW",
        }
        for item in items
    ]


def _build_executive_detail(exec_prof: Any) -> dict[str, Any]:
    """Build full executive profile dict with forensic detail and source attribution."""
    name = _sv_str(exec_prof.name)
    title = _sv_str(exec_prof.title)
    tenure = f"{exec_prof.tenure_years:.1f}" if exec_prof.tenure_years is not None else "N/A"
    prior_lit_count = len(exec_prof.prior_litigation)
    shade_detail = _build_sourced_detail(exec_prof.shade_factors)
    forensic_flag_count = (
        len(exec_prof.shade_factors) + len(exec_prof.prior_litigation)
        + len(exec_prof.prior_enforcement) + len(exec_prof.prior_restatements)
    )
    return {
        "name": name, "title": title, "tenure": tenure,
        "status": exec_prof.departure_type or "ACTIVE",
        "prior_litigation": str(prior_lit_count),
        "prior_litigation_details": [_sv_str(lit) for lit in exec_prof.prior_litigation],
        "shade_factors": [_sv_str(s) for s in exec_prof.shade_factors],
        "shade_factors_detail": shade_detail,
        "departure_context": _sv_str(exec_prof.departure_context, fallback="") if exec_prof.departure_context else "",
        "departure_date": exec_prof.departure_date or "",
        "prior_enforcement": [_sv_str(e) for e in exec_prof.prior_enforcement],
        "prior_restatements": [_sv_str(r) for r in exec_prof.prior_restatements],
        "has_forensic_flags": forensic_flag_count > 0,
        "forensic_flag_count": forensic_flag_count,
        "bio": _sv_str(exec_prof.bio_summary, fallback=""),
    }


def _build_board_member_detail(
    bf: Any,
    *,
    executive_names: set[str] | None = None,
    ceo_chair_separated: bool = False,
) -> dict[str, Any]:
    """Build full board member profile dict with forensic detail and source attribution.

    When ceo_chair_separated is True and the board member is NOT in the
    executive_names set, override is_independent to True (standard
    corporate governance: non-management directors are independent
    unless specifically flagged otherwise).
    """
    other_boards: list[str] = [_sv_str(b) for b in bf.other_boards[:4]] if bf.other_boards else []
    prior_lit_count = len(bf.prior_litigation) if bf.prior_litigation else 0
    forensic_flag_count = (
        len(bf.interlocks or []) + len(bf.relationship_flags or [])
        + len(bf.true_independence_concerns or []) + prior_lit_count
    )
    # Determine independence: use state value if available and True,
    # otherwise infer from executive status when ceo_chair_separated
    raw_independent = bf.is_independent.value if bf.is_independent and hasattr(bf.is_independent, "value") else None
    member_name = _sv_str(bf.name)
    if raw_independent is True:
        independent_str = "Yes"
    elif raw_independent is False and ceo_chair_separated and executive_names is not None:
        # Non-executive board member with separated chair = likely independent
        is_exec = any(member_name.lower() in en.lower() or en.lower() in member_name.lower()
                      for en in executive_names)
        independent_str = "No" if is_exec else "Yes"
    elif raw_independent is False:
        independent_str = "No"
    else:
        independent_str = "N/A"
    return {
        "name": member_name,
        "tenure": f"{bf.tenure_years.value:.0f}" if bf.tenure_years else "N/A",
        "independent": independent_str,
        "other_boards": ", ".join(other_boards) if other_boards else "None",
        "committees": ", ".join(bf.committees) if bf.committees else "None",
        "interlocks": [_sv_str(i) for i in bf.interlocks] if bf.interlocks else [],
        "relationship_flags": [_sv_str(f) for f in bf.relationship_flags] if bf.relationship_flags else [],
        "independence_concerns": [_sv_str(c) for c in bf.true_independence_concerns] if bf.true_independence_concerns else [],
        "is_overboarded": "Yes" if bf.is_overboarded else "No",
        "prior_litigation": str(prior_lit_count),
        "prior_litigation_details": [_sv_str(lit) for lit in bf.prior_litigation] if bf.prior_litigation else [],
        "qualifications": _sv_str(bf.qualifications, fallback="") if bf.qualifications else "",
        "interlocks_detail": _build_sourced_detail(bf.interlocks) if bf.interlocks else [],
        "relationship_flags_detail": _build_sourced_detail(bf.relationship_flags) if bf.relationship_flags else [],
        "independence_concerns_detail": _build_sourced_detail(bf.true_independence_concerns) if bf.true_independence_concerns else [],
        "qualification_tags": bf.qualification_tags if bf.qualification_tags else [],
        "age": _sv_str(bf.age, fallback="") if bf.age else "",
        "has_forensic_flags": forensic_flag_count > 0,
        "forensic_flag_count": forensic_flag_count,
    }


def _build_filing_entries(
    filings: list[Any],
    filer_keys: tuple[str, str] = ("filer", "name"),
    date_keys: tuple[str, str] = ("date", "filing_date"),
    pct_keys: tuple[str, str] = ("pct", "percentage"),
) -> list[dict[str, str]]:
    """Build list of dicts from SourcedValue[dict] filing entries (13D, 13G-to-13D)."""
    result: list[dict[str, str]] = []
    for filing in filings:
        info = filing.value if hasattr(filing, "value") else filing
        if isinstance(info, dict):
            filer = str(info.get(filer_keys[0], info.get(filer_keys[1], "Unknown")))
            dt = str(info.get(date_keys[0], info.get(date_keys[1], "N/A")))
            pct = str(info.get(pct_keys[0], info.get(pct_keys[1], "N/A")))
            result.append({"filer": filer, "date": dt, "pct": pct})
        else:
            result.append({"filer": str(info), "date": "N/A", "pct": "N/A"})
    return result


def _build_board_meeting_data(board: Any) -> dict[str, str | None]:
    """Extract board meeting attendance data for Caremark duty assessment."""
    from do_uw.stages.render.formatters import safe_float

    meetings = None
    if board.board_meetings_held and hasattr(board.board_meetings_held, 'value'):
        v = board.board_meetings_held.value
        if isinstance(v, (int, float)):
            meetings = str(int(v))

    attendance = None
    if board.board_attendance_pct and hasattr(board.board_attendance_pct, 'value'):
        v = board.board_attendance_pct.value
        f = safe_float(v)
        if f is not None:
            attendance = format_percentage(f)

    below_75 = None
    if board.directors_below_75_pct_attendance and hasattr(board.directors_below_75_pct_attendance, 'value'):
        v = board.directors_below_75_pct_attendance.value
        if isinstance(v, (int, float)):
            below_75 = str(int(v))

    proposals = None
    if board.shareholder_proposal_count and hasattr(board.shareholder_proposal_count, 'value'):
        v = board.shareholder_proposal_count.value
        if isinstance(v, (int, float)):
            proposals = str(int(v))

    return {
        "board_meetings_held": meetings,
        "board_attendance_pct": attendance,
        "directors_below_75_pct": below_75,
        "shareholder_proposal_count": proposals,
    }


def _build_anti_takeover(board: Any) -> list[dict[str, str]]:
    """Build anti-takeover provisions list from BoardProfile."""
    provisions: list[dict[str, str]] = []
    _defs: list[tuple[str, str, str, str]] = [
        ("classified_board", "Classified Board",
         "Limits hostile takeover risk but increases Revlon duty scrutiny",
         "Standard annual elections"),
        ("dual_class_structure", "Dual-Class Structure",
         "Concentrated voting power limits shareholder remedy options",
         "Single class of common stock"),
        ("poison_pill", "Poison Pill",
         "Shareholder rights plan deters hostile bids but may entrench management",
         "No poison pill in place"),
        ("supermajority_voting", "Supermajority Voting",
         "Higher vote threshold for charter/bylaw changes limits shareholder power",
         "Simple majority voting"),
        ("blank_check_preferred", "Blank Check Preferred",
         "Board can issue preferred stock without shareholder approval \u2014 potential dilution tool",
         "No blank check preferred authorization"),
    ]
    for attr, label, yes_impl, no_impl in _defs:
        sv = getattr(board, attr, None)
        if sv is not None:
            status = "Yes" if sv.value else "No"
            provisions.append({
                "provision": label,
                "status": status,
                "implication": yes_impl if sv.value else no_impl,
            })
    return provisions


def _build_leaders(executives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build leaders list for People Risk table."""
    leaders: list[dict[str, Any]] = []
    for ex in executives:
        flags: list[str] = []
        lit_count = int(ex.get("prior_litigation", "0"))
        if lit_count > 0:
            flags.append(f"{lit_count} prior litigation")
        for detail in ex.get("prior_litigation_details", []):
            flags.append(detail)
        for shade in ex.get("shade_factors", []):
            flags.append(shade)
        if ex.get("status") and ex["status"] != "ACTIVE":
            flags.append(ex["status"])
        leaders.append({
            "name": ex["name"], "title": ex["title"],
            "tenure": f"{ex['tenure']}y" if ex["tenure"] != "N/A" else "N/A",
            "flags": ", ".join(flags) if flags else "None",
            "prior_litigation": str(lit_count),
            "prior_litigation_details": ex.get("prior_litigation_details", []),
            "shade_factors": ex.get("shade_factors", []),
            "shade_factors_detail": ex.get("shade_factors_detail", []),
            "departure_context": ex.get("departure_context", ""),
            "departure_date": ex.get("departure_date", ""),
            "prior_enforcement": ex.get("prior_enforcement", []),
            "prior_restatements": ex.get("prior_restatements", []),
            "has_forensic_flags": ex.get("has_forensic_flags", False),
            "forensic_flag_count": ex.get("forensic_flag_count", 0),
            "bio": ex.get("bio", ""),
        })
    return leaders


def build_skills_matrix(board_forensics: list[Any] | None) -> dict[str, Any] | None:
    """Build board skills matrix from qualification_tags across all directors.

    Returns dict with 'skills' (list of skill dicts) and 'directors' (name list).
    Each skill dict has: skill name, count, director names who have it.
    """
    if not board_forensics:
        return None

    # Canonical skill display names
    _SKILL_DISPLAY: dict[str, str] = {
        "financial_expert": "Finance & Audit",
        "industry_expertise": "Industry",
        "prior_c_suite": "C-Suite Experience",
        "public_company_experience": "Public Co. Governance",
        "technology": "Technology",
        "legal": "Legal / Regulatory",
        "public_policy_and_government": "Government / Policy",
        "international": "International",
        "risk_management": "Risk Management",
        "cybersecurity": "Cybersecurity",
        "esg": "ESG / Sustainability",
        "marketing": "Marketing / Sales",
        "hr_compensation": "HR / Compensation",
        "academic": "Academic",
        "healthcare": "Healthcare",
        "operations": "Operations",
        "m_and_a": "M&A / Strategy",
    }

    # Collect tags per director
    directors: list[str] = []
    skill_map: dict[str, list[str]] = {}
    for bf in board_forensics:
        name = bf.name.value if hasattr(bf.name, "value") else str(bf.name) if bf.name else "Unknown"
        directors.append(str(name))
        tags = bf.qualification_tags or []
        for tag in tags:
            skill_map.setdefault(tag, []).append(str(name))

    if not skill_map:
        return None

    skills: list[dict[str, Any]] = []
    for tag, names in sorted(skill_map.items(), key=lambda x: -len(x[1])):
        skills.append({
            "skill": _SKILL_DISPLAY.get(tag, tag.replace("_", " ").title()),
            "tag": tag,
            "count": len(names),
            "directors": names,
            "coverage_pct": round(len(names) / len(directors) * 100),
        })

    # Identify gaps (common skills with zero coverage)
    all_expected = {"financial_expert", "industry_expertise", "prior_c_suite",
                    "technology", "legal", "public_policy_and_government", "international",
                    "risk_management", "cybersecurity"}
    gaps = [_SKILL_DISPLAY.get(s, s.replace("_", " ").title())
            for s in all_expected - set(skill_map.keys())]

    return {"skills": skills, "directors": directors, "gaps": sorted(gaps)}


def build_committee_detail(board_forensics: list[Any] | None) -> dict[str, Any] | None:
    """Build structured committee membership from board forensics.

    Returns dict with committees (list of committee dicts), each with name,
    chair (if identifiable), and members.
    """
    if not board_forensics:
        return None

    committee_map: dict[str, dict[str, Any]] = {}
    for bf in board_forensics:
        name = bf.name.value if hasattr(bf.name, "value") else str(bf.name) if bf.name else "Unknown"
        name = str(name)
        for comm in (bf.committees or []):
            comm_str = str(comm)
            is_chair = "(Chair)" in comm_str
            clean_comm = comm_str.replace("(Chair)", "").strip()
            if clean_comm not in committee_map:
                committee_map[clean_comm] = {"name": clean_comm, "chair": None, "members": []}
            if is_chair:
                committee_map[clean_comm]["chair"] = name
            committee_map[clean_comm]["members"].append(name)

    if not committee_map:
        return None

    committees = sorted(committee_map.values(), key=lambda c: c["name"])
    return {"committees": committees, "total_committees": len(committees)}
