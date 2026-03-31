"""Litigation helper functions -- extracted to keep litigation.py under 300 lines.

Contains display data extraction functions for SCA cases, SOL windows,
derivative suits, contingent liabilities, workforce/product/environmental
matters, and whistleblower indicators.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.formatters import format_currency

# Duplicated from md_renderer_helpers to avoid circular import
CLAIM_TYPE_NAMES: dict[str, str] = {
    "employment_discrimination": "Employment Discrimination",
    "antitrust": "Antitrust",
    "FCPA": "FCPA",
    "Fcpa": "FCPA",
    "environmental": "Environmental",
    "derivative": "Derivative",
    "ERISA": "ERISA",
    "Erisa": "ERISA",
    "Section_11": "Section 11",
    "Section_14a": "Section 14(a)",
    "10b-5": "Rule 10b-5",
    "10B-5": "Rule 10b-5",
}

COVERAGE_DISPLAY: dict[str, str] = {
    "SCA_SIDE_C": "Side C (Entity)",
    "SCA_SIDE_A": "Side A (D&O)",
    "SCA_SIDE_B": "Side B (Reimb.)",
    "DERIVATIVE_SIDE_A": "Derivative",
    "DERIVATIVE_SIDE_B": "Derivative (B)",
    "SEC_ENFORCEMENT": "SEC Enforcement",
    "SEC_ENFORCEMENT_A": "SEC Enforcement (A)",
    "SEC_ENFORCEMENT_B": "SEC Enforcement (B)",
    "REGULATORY": "Regulatory",
    "REGULATORY_ENTITY": "Regulatory",
    "EMPLOYMENT_ENTITY": "Employment",
    "PRODUCT_ENTITY": "Product Liability",
    "ANTITRUST_ENTITY": "Antitrust",
    "ENVIRONMENTAL_ENTITY": "Environmental",
    "ERISA_ENTITY": "ERISA",
    "SECURITIES": "Securities",
    "COMMERCIAL_ENTITY": "Commercial",
    "COMMERCIAL": "Commercial",
    "IPO_ENTITY": "IPO/Offering",
    "UNKNOWN": "General",
}


# Display names for LegalTheory enum values used by the classifier (Plan 01)
LEGAL_THEORY_DISPLAY: dict[str, str] = {
    "RULE_10B5": "Rule 10b-5",
    "SECTION_11": "Section 11",
    "SECTION_14A": "Section 14(a)",
    "DERIVATIVE_DUTY": "Derivative / Fiduciary Duty",
    "FCPA": "FCPA",
    "ANTITRUST": "Antitrust",
    "EMPLOYMENT_DISCRIMINATION": "Employment Discrimination",
    "ENVIRONMENTAL": "Environmental",
    "PRODUCT_LIABILITY": "Product Liability",
    "CYBER_PRIVACY": "Cyber / Privacy",
    "ERISA": "ERISA",
    "WHISTLEBLOWER": "Whistleblower",
}


def _sv_str(sv: Any, fallback: str = "N/A") -> str:
    """Extract string value from a SourcedValue or return fallback."""
    if sv is None:
        return fallback
    val: Any = sv.value if hasattr(sv, "value") else sv
    return str(val) if val is not None else fallback


def extract_source_references(case: Any) -> str:
    """Format source references for a case.

    Reads the SourcedValue.source from case.case_name (which Plan 01's
    dedup may have enriched with merged sources) and formats as
    "Sources: EFTS/SCAC, 10-K Item 3" etc.
    """
    case_name_sv = getattr(case, "case_name", None)
    if case_name_sv is None:
        return ""
    source = getattr(case_name_sv, "source", None)
    if source is None or not str(source).strip():
        return ""
    source_str = str(source).strip()
    # If multiple sources are comma/semicolon separated, format nicely
    if "," in source_str or ";" in source_str:
        return f"Sources: {source_str}"
    return source_str


def extract_data_quality_flags(
    case: Any,
    cases_needing_recovery: list[dict[str, Any]] | None = None,
) -> str | None:
    """Check if a case has data quality issues and return a warning string.

    Uses cases_needing_recovery from the classifier's flag_missing_fields pass
    to determine which fields are missing. Returns a human-readable warning
    like "Missing: court, case_number" or None if no gaps.
    """
    if not cases_needing_recovery:
        return None
    case_name = _sv_str(getattr(case, "case_name", None), "")
    if not case_name:
        return None
    for recovery_entry in cases_needing_recovery:
        entry_name = recovery_entry.get("case_name", "")
        if entry_name and entry_name == case_name:
            missing = recovery_entry.get("missing_fields", [])
            if missing:
                # Humanize field names
                humanized = [f.replace("_", " ") for f in missing]
                return f"Missing: {', '.join(humanized)}"
    return None


def format_legal_theories(case: Any) -> str:
    """Format legal_theories from a CaseDetail into a human-readable string.

    Uses the LEGAL_THEORY_DISPLAY mapping for classifier-set values and
    falls back to CLAIM_TYPE_NAMES for legacy values. E.g. "Rule 10b-5, Section 11".
    """
    theories = getattr(case, "legal_theories", None)
    if not theories:
        return ""
    display_parts: list[str] = []
    for t in theories:
        raw = _sv_str(t)
        if raw in ("N/A", ""):
            continue
        # Try classifier display names first, then legacy claim type names
        fallback = raw.replace("_", " ").title()
        display = LEGAL_THEORY_DISPLAY.get(
            raw, CLAIM_TYPE_NAMES.get(raw, fallback),
        )
        if display not in display_parts:
            display_parts.append(display)
    return ", ".join(display_parts)


def _extract_sca_cases(lit: Any) -> list[dict[str, str]]:
    """Extract SCA case details for markdown rendering."""
    cases: list[dict[str, str]] = []
    scas: Any = lit.securities_class_actions
    case_list: list[Any]
    if isinstance(scas, list):
        case_list = scas  # pyright: ignore[reportUnknownVariableType]
    elif scas is not None and hasattr(scas, "cases"):
        case_list = scas.cases
    else:
        case_list = []

    from do_uw.stages.score.red_flag_gates import _is_regulatory_not_sca

    for case in case_list:
        genuine_sca = not _is_regulatory_not_sca(case)
        cp_start_sv = case.class_period_start if hasattr(case, "class_period_start") else None
        cp_start = _sv_str(cp_start_sv) if cp_start_sv else "N/A"
        cp_end_sv = case.class_period_end if hasattr(case, "class_period_end") else None
        cp_end = _sv_str(cp_end_sv) if cp_end_sv else "N/A"

        cp_days = ""
        if hasattr(case, "class_period_days") and case.class_period_days:
            cp_days = f"{case.class_period_days}d"
        elif cp_start_sv and cp_end_sv:
            try:
                start_val = cp_start_sv.value if hasattr(cp_start_sv, "value") else cp_start_sv
                end_val = cp_end_sv.value if hasattr(cp_end_sv, "value") else cp_end_sv
                if hasattr(start_val, "toordinal") and hasattr(end_val, "toordinal"):
                    cp_days = f"{(end_val - start_val).days}d"
            except (TypeError, AttributeError):
                pass

        raw_cov = _sv_str(case.coverage_type)
        counsel = _sv_str(getattr(case, "lead_counsel", None))
        counsel_tier = getattr(case, "lead_counsel_tier", None)
        if counsel_tier is not None:
            counsel += f" [T{counsel_tier.value}]"

        settlement: str | None = None
        settle_sv = getattr(case, "settlement_amount", None)
        if settle_sv is not None and settle_sv.value is not None:
            raw_val = settle_sv.value
            if 0 < raw_val < 10_000:
                raw_val = raw_val * 1_000_000
            settlement = format_currency(raw_val, compact=True)

        allegations_list: list[str] = []
        if hasattr(case, "allegations") and case.allegations:
            for a in case.allegations:
                raw_a = _sv_str(a)
                allegations_list.append(CLAIM_TYPE_NAMES.get(raw_a, raw_a.replace("_", " ").title()))

        # Additional detail fields (may be None — template shows gaps)
        case_number = _sv_str(getattr(case, "case_number", None))
        named_defendants = [_sv_str(d) for d in getattr(case, "named_defendants", []) or []] if getattr(case, "named_defendants", None) else []
        legal_theories = [_sv_str(t) for t in getattr(case, "legal_theories", []) or []] if getattr(case, "legal_theories", None) else []
        key_rulings = [_sv_str(r) for r in getattr(case, "key_rulings", []) or []] if getattr(case, "key_rulings", None) else []
        judge = _sv_str(getattr(case, "judge", None))
        lead_plaintiff_type = _sv_str(getattr(case, "lead_plaintiff_type", None))

        # Count populated vs total detail fields for data quality indicator
        detail_fields = {
            "case_number": case_number, "court": _sv_str(getattr(case, "court", None)),
            "filing_date": _sv_str(getattr(case, "filing_date", None)),
            "class_period_start": cp_start, "lead_counsel": counsel,
            "named_defendants": ", ".join(named_defendants) if named_defendants else "N/A",
            "judge": judge,
        }
        populated = sum(1 for v in detail_fields.values() if v and v != "N/A")
        total_detail = len(detail_fields)

        coverage_type = "Securities Class Action" if genuine_sca else COVERAGE_DISPLAY.get(raw_cov, raw_cov.replace("_", " ").title())
        cases.append({
            "name": _sv_str(case.case_name, "Unknown"),
            "status": _sv_str(case.status),
            "coverage": COVERAGE_DISPLAY.get(raw_cov, raw_cov.replace("_", " ").title()),
            "coverage_type": coverage_type,
            "is_genuine_sca": "true" if genuine_sca else "false",
            "class_period_start": cp_start, "class_period_end": cp_end,
            "class_period_days": cp_days,
            "lead_counsel": counsel or None,
            "filing_date": _sv_str(getattr(case, "filing_date", None)),
            "court": _sv_str(getattr(case, "court", None)),
            "settlement": settlement,
            "allegations": ", ".join(allegations_list) if allegations_list else None,
            # Enhanced detail fields (Item 6)
            "case_number": case_number if case_number != "N/A" else None,
            "named_defendants": ", ".join(named_defendants) if named_defendants else None,
            "legal_theories": ", ".join(
                t.replace("_", " ").title() for t in legal_theories
            ) if legal_theories else None,
            "key_rulings": key_rulings if key_rulings else None,
            "judge": judge if judge != "N/A" else None,
            "lead_plaintiff_type": lead_plaintiff_type if lead_plaintiff_type != "N/A" else None,
            "detail_completeness": f"{populated}/{total_detail}",
        })
    return cases


def _extract_sol_windows(lit: Any) -> list[dict[str, str]]:
    """Extract SOL window data for markdown rendering."""
    windows: list[dict[str, str]] = []
    sol_map: Any = lit.sol_map if hasattr(lit, "sol_map") else None
    if sol_map is None:
        return windows
    sol_entries: list[Any]
    if isinstance(sol_map, list):
        sol_entries = sol_map  # pyright: ignore[reportUnknownVariableType]
    elif hasattr(sol_map, "windows") and sol_map.windows:
        sol_entries = list(sol_map.windows)
    else:
        sol_entries = []

    for entry in sol_entries:
        raw_claim = str(getattr(entry, "claim_type", "N/A"))
        trigger_dt = getattr(entry, "trigger_date", None)
        exp_dt = getattr(entry, "sol_expiry", None)
        is_open_val = getattr(entry, "window_open", False)
        trigger_desc_sv = getattr(entry, "trigger_description", None)
        trigger_desc = ""
        conf = "LOW"
        if trigger_desc_sv is not None:
            trigger_desc = str(trigger_desc_sv.value or "") if hasattr(trigger_desc_sv, "value") else str(trigger_desc_sv)
            if hasattr(trigger_desc_sv, "confidence"):
                conf = str(trigger_desc_sv.confidence or "LOW")
        windows.append({
            "claim_type": CLAIM_TYPE_NAMES.get(raw_claim, raw_claim.replace("_", " ").title()),
            "trigger_date": str(trigger_dt) if trigger_dt else "N/A",
            "sol_expiry": str(exp_dt) if exp_dt else "N/A",
            "status": "OPEN" if is_open_val else "CLOSED",
            "trigger_desc": trigger_desc, "confidence": conf,
        })
    return windows


def _extract_derivative_suits(lit: Any) -> list[dict[str, str]]:
    """Extract derivative suit details for markdown rendering."""
    suits: list[dict[str, str]] = []
    if not lit.derivative_suits:
        return suits
    for suit in lit.derivative_suits:
        allegations_list: list[str] = []
        if hasattr(suit, "allegations") and suit.allegations:
            for a in suit.allegations:
                raw_a = _sv_str(a)
                allegations_list.append(CLAIM_TYPE_NAMES.get(raw_a, raw_a.replace("_", " ").title()))
        settlement: str | None = None
        settle_sv = getattr(suit, "settlement_amount", None)
        if settle_sv is not None and settle_sv.value is not None:
            raw_val = settle_sv.value
            if 0 < raw_val < 10_000:
                raw_val = raw_val * 1_000_000
            settlement = format_currency(raw_val, compact=True)
        case_name = _sv_str(getattr(suit, "case_name", None), "Unknown")
        filing_date = _sv_str(getattr(suit, "filing_date", None))
        court = _sv_str(getattr(suit, "court", None))

        # Filter ghost derivative suits — web search extraction creates entries
        # with no meaningful data (no case name, no filing date, no court).
        has_case_name = case_name not in ("Unknown", "N/A", "")
        has_filing_date = filing_date not in ("N/A", "")
        # Require case name OR filing date — court alone is a ghost shell
        if not has_case_name and not has_filing_date:
            continue

        suits.append({
            "case_name": case_name,
            "filing_date": filing_date,
            "court": court,
            "status": _sv_str(getattr(suit, "status", None)),
            "allegations": ", ".join(allegations_list) if allegations_list else None,
            "settlement": settlement,
        })
    return suits


def _normalize_contingent_amount(val: float | None) -> float | None:
    """Normalize contingent liability amounts to full USD.

    LLM extraction stores accrued_amount in millions (15800.0 = $15.8B)
    and range values inconsistently. Values under $1B (1_000_000_000)
    are likely in millions and need multiplication.
    """
    if val is None or val <= 0:
        return val
    # Values under 1B are almost certainly in millions from LLM extraction
    if val < 1_000_000_000:
        return val * 1_000_000
    return val


def _extract_contingent_liabilities(lit: Any) -> list[dict[str, str]]:
    """Extract contingent liability details for markdown rendering."""
    items: list[dict[str, str]] = []
    if not lit.contingent_liabilities:
        return items
    for cont in lit.contingent_liabilities:
        range_low = getattr(cont, "range_low", None)
        range_high = getattr(cont, "range_high", None)
        if range_low is not None and range_high is not None:
            low_val = _normalize_contingent_amount(range_low.value)
            high_val = _normalize_contingent_amount(range_high.value)
            amount_range = f"{format_currency(low_val, compact=True)} - {format_currency(high_val, compact=True)}"
        elif range_low is not None and range_low.value is not None:
            low_val = _normalize_contingent_amount(range_low.value)
            amount_range = f">= {format_currency(low_val, compact=True)}"
        elif range_high is not None and range_high.value is not None:
            high_val = _normalize_contingent_amount(range_high.value)
            amount_range = f"<= {format_currency(high_val, compact=True)}"
        else:
            amount_range = "\u2014"
        items.append({
            "description": _sv_str(getattr(cont, "description", None)),
            "classification": _sv_str(getattr(cont, "asc_450_classification", None)),
            "amount_range": amount_range,
            "source": _sv_str(getattr(cont, "source_note", None)),
        })
    return items


def _extract_workforce_product_env(lit: Any) -> dict[str, list[str]]:
    """Extract workforce, product, and environmental matters."""
    wpe: Any = lit.workforce_product_environmental
    result: dict[str, list[str]] = {"employment": [], "product": [], "environmental": [], "cybersecurity": []}
    if wpe is None:
        return result
    for item in (wpe.employment_matters or []):
        result["employment"].append(_sv_str(item))
    for item in (wpe.eeoc_charges or []):
        result["employment"].append(f"EEOC: {_sv_str(item)}")
    for item in (wpe.warn_notices or []):
        result["employment"].append(f"WARN: {_sv_str(item)}")
    for item in (wpe.product_recalls or []):
        result["product"].append(f"Recall: {_sv_str(item)}")
    for item in (wpe.mass_tort_exposure or []):
        result["product"].append(f"Mass Tort: {_sv_str(item)}")
    for item in (wpe.environmental_actions or []):
        result["environmental"].append(_sv_str(item))
    for item in (wpe.cybersecurity_incidents or []):
        result["cybersecurity"].append(_sv_str(item))
    return result


def _extract_whistleblower_indicators(lit: Any) -> list[dict[str, str]]:
    """Extract whistleblower indicator details for markdown rendering."""
    items: list[dict[str, str]] = []
    if not lit.whistleblower_indicators:
        return items
    for ind in lit.whistleblower_indicators:
        items.append({
            "type": _sv_str(getattr(ind, "indicator_type", None)),
            "description": _sv_str(getattr(ind, "description", None)),
            "date": _sv_str(getattr(ind, "date_identified", None)),
            "significance": _sv_str(getattr(ind, "significance", None)),
        })
    return items
