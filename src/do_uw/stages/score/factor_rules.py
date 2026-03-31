"""Per-factor rule matching for the scoring engine.

Determines which scoring rule triggers for each factor (F1-F10)
by comparing rule conditions against extracted factor data.

Split from factor_scoring.py to stay under 500-line limit.
"""

from __future__ import annotations

from typing import Any, cast

from do_uw.stages.score.factor_data import min_settlement_years

# -----------------------------------------------------------------------
# Top-level dispatcher
# -----------------------------------------------------------------------


def rule_matches(
    rule: dict[str, Any], data: dict[str, Any], factor_key: str
) -> bool:
    """Check if a single rule's condition matches the extracted data."""
    condition = str(rule.get("condition", "")).lower()
    rule_id = str(rule.get("id", ""))

    if factor_key == "F1_prior_litigation":
        return _match_f1_rule(rule_id, data)
    if factor_key == "F2_stock_decline":
        return _match_f2_rule(rule_id, data)
    if factor_key == "F3_restatement_audit":
        return _match_f3_rule(rule_id, data)
    if factor_key == "F4_ipo_spac_ma":
        return _match_f4_rule(rule_id, data)
    if factor_key == "F5_guidance_misses":
        return _match_f5_rule(rule_id, data)
    if factor_key == "F6_short_interest":
        return _match_f6_rule(rule_id, data)
    if factor_key == "F7_volatility":
        return _match_f7_rule(rule_id, data)
    if factor_key == "F8_financial_distress":
        return _match_f8_rule(rule_id, data)
    if factor_key == "F9_governance":
        return _match_f9_rule(rule_id, data)
    if factor_key == "F10_officer_stability":
        return _match_f10_rule(rule_id, data)

    # Default: check for "no" or "clean" or "0" in condition -> always match
    if "no " in condition or "clean" in condition or condition == "0 misses":
        return True
    return False


# -----------------------------------------------------------------------
# Per-factor rule matchers
# -----------------------------------------------------------------------


def _match_f1_rule(rule_id: str, data: dict[str, Any]) -> bool:
    """Match F1 (Prior Litigation) rules."""
    active_sca = data.get("active_sca", False)
    settled_scas = cast(list[dict[str, Any]], data.get("settled_scas", []))
    sec_enforcement = data.get("sec_enforcement", False)
    derivative_suits = data.get("derivative_suits", 0)
    min_years = min_settlement_years(settled_scas)

    if rule_id == "F1-001":
        return bool(active_sca)
    if rule_id == "F1-002":
        return min_years is not None and min_years < 3
    if rule_id == "F1-003":
        return min_years is not None and 3 <= min_years < 5
    if rule_id == "F1-004":
        return min_years is not None and 5 <= min_years < 10
    if rule_id == "F1-005":
        return bool(sec_enforcement)
    if rule_id == "F1-006":
        return derivative_suits > 0
    if rule_id == "F1-007":
        return (
            not active_sca
            and not sec_enforcement
            and derivative_suits == 0
            and len(settled_scas) == 0
        )
    return False


def _match_f2_rule(rule_id: str, data: dict[str, Any]) -> bool:
    """Match F2 (Stock Decline) rules."""
    decline = data.get("decline_from_high", 0.0)
    if rule_id == "F2-001":
        return decline > 60
    if rule_id == "F2-002":
        return 50 < decline <= 60
    if rule_id == "F2-003":
        return 40 < decline <= 50
    if rule_id == "F2-004":
        return 30 < decline <= 40
    if rule_id == "F2-005":
        return 20 < decline <= 30
    if rule_id == "F2-006":
        return decline <= 20
    return False


def _match_f3_rule(rule_id: str, data: dict[str, Any]) -> bool:
    """Match F3 (Restatement/Audit) rules incl. Phase 26 amplifiers."""
    restatement_months = data.get("restatement_months_since", None)
    auditor_change_disagreement = data.get("auditor_change_disagreement", False)
    material_weaknesses = data.get("material_weaknesses", 0)
    auditor_routine_change = data.get("auditor_routine_change", False)

    if rule_id == "F3-001":
        return restatement_months is not None and restatement_months < 12
    if rule_id == "F3-002":
        return (
            restatement_months is not None and 12 <= restatement_months < 24
        )
    if rule_id == "F3-003":
        return (
            restatement_months is not None and 24 <= restatement_months < 60
        )
    if rule_id == "F3-004":
        return bool(auditor_change_disagreement)
    if rule_id == "F3-005":
        return material_weaknesses > 0
    if rule_id == "F3-006":
        return bool(auditor_routine_change)
    if rule_id == "F3-007":
        return (
            restatement_months is None
            and not auditor_change_disagreement
            and material_weaknesses == 0
        )
    # Phase 26 amplifiers (not purely additive -- confirmation bonus)
    if rule_id == "F3-P26-DECHOW":
        return data.get("dechow_confirms_beneish", False)
    if rule_id == "F3-P26-MDA":
        return data.get("mda_tone_shift_adverse", False)
    return False


def _match_f4_rule(rule_id: str, data: dict[str, Any]) -> bool:
    """Match F4 (IPO/SPAC/M&A) rules."""
    spac_months = data.get("spac_months_since", None)
    ipo_months = data.get("ipo_months_since", None)
    major_ma = data.get("major_ma", False)

    if rule_id == "F4-001":
        return spac_months is not None and spac_months < 18
    if rule_id == "F4-002":
        return spac_months is not None and 18 <= spac_months < 36
    if rule_id == "F4-003":
        return ipo_months is not None and ipo_months < 18
    if rule_id == "F4-004":
        return ipo_months is not None and 18 <= ipo_months < 36
    if rule_id == "F4-005":
        return bool(major_ma)
    if rule_id == "F4-006":
        return (
            (ipo_months is None or ipo_months >= 36)
            and (spac_months is None or spac_months >= 36)
            and not major_ma
        )
    return False


def _match_f5_rule(rule_id: str, data: dict[str, Any]) -> bool:
    """Match F5 (Guidance Misses) rules."""
    misses = data.get("earnings_misses_8q", 0)
    if rule_id == "F5-001":
        return misses >= 4
    if rule_id == "F5-002":
        return misses == 3
    if rule_id == "F5-003":
        return misses == 2
    if rule_id == "F5-004":
        return misses == 1
    if rule_id == "F5-005":
        return misses == 0
    return False


def _match_f6_rule(rule_id: str, data: dict[str, Any]) -> bool:
    """Match F6 (Short Interest) rules."""
    si_ratio = data.get("si_vs_sector_ratio", 0.0)
    if rule_id == "F6-R01":
        return si_ratio > 3.0
    if rule_id == "F6-R02":
        return 2.0 < si_ratio <= 3.0
    if rule_id == "F6-R03":
        return 1.5 < si_ratio <= 2.0
    if rule_id == "F6-R04":
        return 1.0 < si_ratio <= 1.5
    if rule_id == "F6-R05":
        return si_ratio <= 1.0
    return False


def _match_f7_rule(rule_id: str, data: dict[str, Any]) -> bool:
    """Match F7 (Volatility) rules."""
    vol_ratio = data.get("vol_vs_sector_ratio", 0.0)
    if rule_id == "F7-R01":
        return vol_ratio > 3.0
    if rule_id == "F7-R02":
        return 2.0 < vol_ratio <= 3.0
    if rule_id == "F7-R03":
        return 1.5 < vol_ratio <= 2.0
    if rule_id == "F7-R04":
        return 1.0 < vol_ratio <= 1.5
    if rule_id == "F7-R05":
        return vol_ratio <= 1.0
    return False


def _match_f8_rule(rule_id: str, data: dict[str, Any]) -> bool:
    """Match F8 (Financial Distress) leverage rules + temporal amplifier."""
    leverage_level = data.get("leverage_level", "unknown")
    has_leverage_data = data.get("has_leverage_data", False)
    if rule_id == "F8-L01":
        return leverage_level in ("critical", "distress")
    if rule_id == "F8-L02":
        return leverage_level == "elevated"
    if rule_id == "F8-L03":
        return has_leverage_data and leverage_level == "normal"
    if rule_id == "F8-L04":
        return has_leverage_data and leverage_level == "below_normal"
    # Phase 26: temporal trajectory amplifier
    if rule_id == "F8-P26-TEMPORAL":
        return data.get("deteriorating_temporal_count", 0) >= 3
    return False


def _match_f9_rule(rule_id: str, data: dict[str, Any]) -> bool:
    """Match F9 (Governance) rules + executive forensics amplifier."""
    ceo_chair = data.get("ceo_chair_duality", False)
    independence = data.get("board_independence", 1.0)
    ceo_tenure_months = data.get("ceo_tenure_months", 999)
    cfo_tenure_months = data.get("cfo_tenure_months", 999)

    if rule_id == "F9-001":
        return ceo_chair and independence < 0.50
    if rule_id == "F9-002":
        return ceo_chair and independence >= 0.50
    if rule_id == "F9-003":
        return not ceo_chair and independence < 0.66
    if rule_id == "F9-004":
        return ceo_tenure_months < 6
    if rule_id == "F9-005":
        return cfo_tenure_months < 6
    if rule_id == "F9-006":
        return (
            not ceo_chair
            and independence >= 0.66
            and ceo_tenure_months >= 6
            and cfo_tenure_months >= 6
        )
    # Phase 26: executive aggregate risk amplifier
    if rule_id == "F9-P26-EXEC":
        return data.get("executive_aggregate_risk", 0.0) > 50
    return False


def _match_f10_rule(rule_id: str, data: dict[str, Any]) -> bool:
    """Match F10 (Officer Stability) rules + departure-stress amplifier."""
    ceo_months = data.get("ceo_tenure_months", 999)
    cfo_months = data.get("cfo_tenure_months", 999)
    interim_ceo = data.get("interim_ceo", False)
    interim_cfo = data.get("interim_cfo", False)

    if rule_id == "F10-001":
        return ceo_months >= 24 and cfo_months >= 12
    if rule_id == "F10-002":
        return (ceo_months < 24 or cfo_months < 12) and not (
            ceo_months < 24 and cfo_months < 12
        )
    if rule_id == "F10-003":
        return ceo_months < 24 and cfo_months < 12
    if rule_id == "F10-004":
        return interim_ceo or interim_cfo
    # Phase 26: CFO departure during stress period amplifier
    if rule_id == "F10-P26-STRESS":
        return data.get("cfo_departure_during_stress", False)
    return False
