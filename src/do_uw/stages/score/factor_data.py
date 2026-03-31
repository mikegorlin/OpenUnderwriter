"""Per-factor data extraction for the scoring engine (F1-F10).

Returns dicts consumed by rule matchers in factor_rules.py.

Market/trading factor data (F6, F7) and get_sector_code are in
factor_data_market.py (split for 500-line compliance).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from do_uw.models.company import CompanyProfile
from do_uw.models.state import ExtractedData
from do_uw.stages.score.factor_data_market import (
    _get_f6_data,
    _get_f7_data,
    get_sector_code,
)


def get_factor_data(
    factor_key: str,
    extracted: ExtractedData,
    company: CompanyProfile | None,
    sectors: dict[str, Any],
    analysis_results: dict[str, Any] | None = None,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Dispatch to per-factor data extraction helper.

    signal_results parameter is accepted for API compatibility but not used
    here -- signal-driven scoring is handled in _score_factor before this
    function is called. This function provides rule-based data dicts needed
    by factor modifiers (F2 insider amplifier, F9 dual_class, etc.).
    """
    _ = signal_results  # Reserved for future use
    ar = analysis_results or {}
    if factor_key == "F1_prior_litigation":
        return _get_f1_data(extracted, company)
    if factor_key == "F2_stock_decline":
        return _get_f2_data(extracted)
    if factor_key == "F3_restatement_audit":
        return _get_f3_data(extracted, ar)
    if factor_key == "F4_ipo_spac_ma":
        return _get_f4_data(extracted)
    if factor_key == "F5_guidance_misses":
        return _get_f5_data(extracted)
    if factor_key == "F6_short_interest":
        return _get_f6_data(extracted, sectors, company)
    if factor_key == "F7_volatility":
        return _get_f7_data(extracted, sectors, company)
    if factor_key == "F8_financial_distress":
        return _get_f8_data(extracted, sectors, company, ar)
    if factor_key == "F9_governance":
        return _get_f9_data(extracted, ar)
    if factor_key == "F10_officer_stability":
        return _get_f10_data(extracted, ar)
    return {}


def min_settlement_years(
    settled_scas: list[dict[str, Any]],
) -> float | None:
    """Get minimum years_since from settled SCAs, or None."""
    if not settled_scas:
        return None
    years_vals: list[float] = []
    for sca in settled_scas:
        val = sca.get("years_since")
        if val is not None:
            years_vals.append(float(val))
    if not years_vals:
        return None
    return min(years_vals)


# -----------------------------------------------------------------------
# Per-factor data extraction
# -----------------------------------------------------------------------


def _get_f1_data(
    extracted: ExtractedData, company: CompanyProfile | None
) -> dict[str, Any]:
    """Extract F1 (Prior Litigation) data."""
    _ = company  # Not used for F1 currently
    data: dict[str, Any] = {
        "active_sca": False,
        "settled_scas": [],
        "sec_enforcement": False,
        "derivative_suits": 0,
    }
    lit = extracted.litigation
    if lit is None:
        return data

    from do_uw.stages.score.red_flag_gates import _is_regulatory_not_sca

    for sca in lit.securities_class_actions:
        # Skip non-securities cases misclassified as SCAs
        if _is_regulatory_not_sca(sca):
            continue
        status = sca.status
        # Active SCA detection uses same criteria as canonical sca_counter:
        # status in (ACTIVE, PENDING, N/A, None) = active
        status_str = status.value.upper() if status is not None else ""
        if status_str in ("ACTIVE", "PENDING", "N/A", "") or status is None:
            data["active_sca"] = True
        elif status is not None and status.value.upper() == "SETTLED":
            settled_entry: dict[str, Any] = {}
            if sca.settlement_amount is not None:
                settled_entry["amount"] = sca.settlement_amount.value
            if sca.filing_date is not None:
                days = (date.today() - sca.filing_date.value).days
                settled_entry["years_since"] = days / 365.25
            data["settled_scas"].append(settled_entry)

    enf = lit.sec_enforcement
    if enf.pipeline_position is not None:
        pos = enf.pipeline_position.value.upper()
        # Only flag as SEC enforcement for scoring when either:
        # (a) there are actual enforcement actions on record, or
        # (b) pipeline_position is ENFORCEMENT_ACTION (which the
        #     extraction layer now only sets when actions exist).
        # Text-pattern signals (WELLS_NOTICE and below) indicate
        # regulatory scrutiny but not a completed action — they
        # should NOT trigger the F1-005 "SEC enforcement action" rule.
        if pos == "ENFORCEMENT_ACTION" and enf.actions:
            data["sec_enforcement"] = True

    data["derivative_suits"] = len(lit.derivative_suits)
    return data


def _get_f2_data(extracted: ExtractedData) -> dict[str, Any]:
    """Extract F2 (Stock Decline) data."""
    data: dict[str, Any] = {
        "decline_from_high": 0.0,
        "insider_amplifier_data": {},
        "peer_underperformance_ppts": 0.0,
    }
    mkt = extracted.market
    if mkt is None:
        return data

    if mkt.stock.decline_from_high_pct is not None:
        data["decline_from_high"] = abs(mkt.stock.decline_from_high_pct.value)

    if mkt.stock.sector_relative_performance is not None:
        val = mkt.stock.sector_relative_performance.value
        data["peer_underperformance_ppts"] = abs(min(val, 0))

    # Phase 90: Per-drop contribution data for compound modifier
    drop_contributions: list[dict[str, Any]] = []
    if mkt.stock_drops and (mkt.stock_drops.single_day_drops or mkt.stock_drops.multi_day_drops):
        all_drops = mkt.stock_drops.single_day_drops + mkt.stock_drops.multi_day_drops
        for drop in all_drops:
            contrib: dict[str, Any] = {
                "magnitude": abs(drop.drop_pct.value) if drop.drop_pct else 0,
                "decay_weight": drop.decay_weight if drop.decay_weight is not None else 1.0,
                "company_pct_ratio": (
                    abs(drop.company_pct) / 100.0
                ) if drop.company_pct is not None else 1.0,
                "has_disclosure": bool(drop.corrective_disclosure_type),
            }
            drop_contributions.append(contrib)
    data["drop_contributions"] = drop_contributions

    # Insider amplifier data
    insider = mkt.insider_trading
    amp: dict[str, Any] = {
        "cluster_selling": len(insider.cluster_events) > 0,
        "heavy_selling": False,
        "pre_announcement_selling": False,
    }
    if insider.ceo_cfo_pct_sold is not None and insider.ceo_cfo_pct_sold.value > 25:
        amp["heavy_selling"] = True
    data["insider_amplifier_data"] = amp

    return data


def _get_f3_data(
    extracted: ExtractedData, ar: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract F3 (Restatement/Audit) data with Phase 26 sub-factors."""
    data: dict[str, Any] = {
        "restatement_months_since": None, "auditor_change_disagreement": False,
        "material_weaknesses": 0, "auditor_routine_change": False,
        "dechow_confirms_beneish": False, "mda_tone_shift_adverse": False,
    }
    fin = extracted.financials
    if fin is None:
        return data

    audit = fin.audit
    if audit.restatements:
        for rst in audit.restatements:
            rst_dict = rst.value
            rst_date_str = rst_dict.get("date", "")
            if rst_date_str:
                try:
                    rst_date = date.fromisoformat(rst_date_str)
                    months = (date.today() - rst_date).days / 30.4
                    if (
                        data["restatement_months_since"] is None
                        or months < data["restatement_months_since"]
                    ):
                        data["restatement_months_since"] = months
                except (ValueError, TypeError):
                    pass

    data["material_weaknesses"] = len(audit.material_weaknesses)

    # Phase 26: forensic composite sub-factors
    if ar:
        fc = ar.get("forensic_composites")
        if isinstance(fc, dict):
            fis = fc.get("financial_integrity_score", {})
            if isinstance(fis, dict) and fis.get("zone") in ("CRITICAL", "CONCERN"):
                data["dechow_confirms_beneish"] = True
        nlp = ar.get("nlp_signals")
        if isinstance(nlp, dict):
            tone = nlp.get("tone_shift")
            if isinstance(tone, dict) and tone.get("classification") == "ADVERSE_SHIFT":
                data["mda_tone_shift_adverse"] = True

    return data


def _get_f4_data(extracted: ExtractedData) -> dict[str, Any]:
    """Extract F4 (IPO/SPAC/M&A) data."""
    data: dict[str, Any] = {
        "ipo_months_since": None,
        "spac_months_since": None,
        "major_ma": False,
    }
    mkt = extracted.market
    if mkt is None:
        return data

    cm = mkt.capital_markets
    for offering in cm.offerings_3yr:
        if offering.date is not None:
            otype = offering.offering_type.upper()
            try:
                off_date = date.fromisoformat(offering.date.value)
                months = (date.today() - off_date).days / 30.4
            except (ValueError, TypeError):
                continue
            if "IPO" in otype:
                if (
                    data["ipo_months_since"] is None
                    or months < data["ipo_months_since"]
                ):
                    data["ipo_months_since"] = months
            if "SPAC" in otype:
                if (
                    data["spac_months_since"] is None
                    or months < data["spac_months_since"]
                ):
                    data["spac_months_since"] = months

    return data


def _get_f5_data(extracted: ExtractedData) -> dict[str, Any]:
    """Extract F5 (Guidance Misses) data."""
    data: dict[str, Any] = {
        "earnings_misses_8q": 0,
        "max_miss_magnitude": 0.0,
        "guidance_withdrawn": False,
    }
    mkt = extracted.market
    if mkt is None:
        return data

    eg = mkt.earnings_guidance
    misses = 0
    max_mag = 0.0
    for q in eg.quarters[:8]:
        if q.result.upper() == "MISS":
            misses += 1
            if q.miss_magnitude_pct is not None:
                mag = abs(q.miss_magnitude_pct.value)
                if mag > max_mag:
                    max_mag = mag

    data["earnings_misses_8q"] = misses
    data["max_miss_magnitude"] = max_mag
    data["guidance_withdrawn"] = eg.guidance_withdrawals > 0
    return data


def _get_f8_data(
    extracted: ExtractedData, sectors: dict[str, Any],
    company: CompanyProfile | None, ar: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract F8 (Financial Distress) data with temporal trajectory."""
    data: dict[str, Any] = {
        "leverage_level": "unknown", "has_leverage_data": False,
        "debt_to_ebitda": 0.0, "cash_runway_months": 999,
        "going_concern": False, "covenant_breach": False,
        "missed_debt_payment": False, "credit_downgrade_junk": False,
        "deteriorating_temporal_count": 0,
    }

    # Phase 26: count deteriorating temporal signals
    if ar:
        ts = ar.get("temporal_signals")
        if isinstance(ts, dict):
            signals = ts.get("signals", [])
            det_count = sum(
                1
                for s in signals
                if isinstance(s, dict) and s.get("classification") == "DETERIORATING"
            )
            data["deteriorating_temporal_count"] = det_count

    fin = extracted.financials
    if fin is None:
        return data

    if fin.audit.going_concern is not None:
        data["going_concern"] = fin.audit.going_concern.value

    if fin.leverage is not None:
        lev_dict = fin.leverage.value
        dte = lev_dict.get("debt_to_ebitda")
        if dte is not None:
            data["debt_to_ebitda"] = float(dte)
            data["has_leverage_data"] = True
            sector_code = get_sector_code(company)
            lev_baselines = sectors.get("leverage_debt_ebitda", {})
            sector_lev = lev_baselines.get(
                sector_code, lev_baselines.get("DEFAULT", {})
            )
            normal = float(sector_lev.get("normal", 2.5))
            elevated = float(sector_lev.get("elevated", 4.0))
            critical = float(sector_lev.get("critical", 5.5))
            if data["debt_to_ebitda"] >= critical:
                data["leverage_level"] = "critical"
            elif data["debt_to_ebitda"] >= elevated:
                data["leverage_level"] = "elevated"
            elif data["debt_to_ebitda"] >= normal:
                data["leverage_level"] = "normal"
            else:
                data["leverage_level"] = "below_normal"

    return data


def _get_f9_data(
    extracted: ExtractedData,
    ar: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract F9 (Governance) data with executive forensics."""
    data: dict[str, Any] = {
        "board_independence": 1.0,
        "ceo_chair_duality": False,
        "ceo_tenure_months": 999,
        "cfo_tenure_months": 999,
        "dual_class": False,
        # Phase 26: executive forensics sub-factor
        "executive_aggregate_risk": 0.0,
    }

    # Phase 26: executive forensics aggregate
    if ar:
        er = ar.get("executive_risk")
        if isinstance(er, dict):
            data["executive_aggregate_risk"] = float(er.get("weighted_score", 0))

    gov = extracted.governance
    if gov is None:
        return data

    board = gov.board
    if board.independence_ratio is not None:
        data["board_independence"] = board.independence_ratio.value
    if board.ceo_chair_duality is not None:
        data["ceo_chair_duality"] = board.ceo_chair_duality.value
    if board.dual_class_structure is not None:
        data["dual_class"] = board.dual_class_structure.value

    # Use Phase 4 leadership.executives (LeadershipForensicProfile)
    for exec_profile in gov.leadership.executives:
        if exec_profile.title is not None:
            title = exec_profile.title.value.upper()
            if "CEO" in title or "CHIEF EXECUTIVE" in title:
                if exec_profile.tenure_years is not None:
                    data["ceo_tenure_months"] = exec_profile.tenure_years * 12
            elif "CFO" in title or "CHIEF FINANCIAL" in title:
                if exec_profile.tenure_years is not None:
                    data["cfo_tenure_months"] = exec_profile.tenure_years * 12

    return data


def _get_f10_data(
    extracted: ExtractedData,
    ar: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract F10 (Officer Stability) data with departure timing."""
    data: dict[str, Any] = {
        "ceo_tenure_months": 999,
        "cfo_tenure_months": 999,
        "interim_ceo": False,
        "interim_cfo": False,
        # Phase 26: departure-during-stress amplifier
        "cfo_departure_during_stress": False,
    }

    # Phase 26: check if CFO departed during financial stress period
    if ar:
        er = ar.get("executive_risk")
        if isinstance(er, dict):
            individuals = er.get("individual_scores", [])
            for ind in individuals:
                if isinstance(ind, dict):
                    role = str(ind.get("role", "")).upper()
                    if "CFO" in role or "CHIEF FINANCIAL" in role:
                        if ind.get("departure_timing_score", 0) > 30:
                            data["cfo_departure_during_stress"] = True

    gov = extracted.governance
    if gov is None:
        return data

    # Use Phase 4 leadership.executives (LeadershipForensicProfile)
    for exec_profile in gov.leadership.executives:
        if exec_profile.title is not None:
            title = exec_profile.title.value.upper()
            if "CEO" in title or "CHIEF EXECUTIVE" in title:
                if exec_profile.tenure_years is not None:
                    data["ceo_tenure_months"] = exec_profile.tenure_years * 12
                if exec_profile.is_interim is not None:
                    interim = exec_profile.is_interim.value
                    # Sanity: nobody is interim for >3 years
                    tenure = exec_profile.tenure_years or 0
                    data["interim_ceo"] = interim and tenure <= 3
            elif "CFO" in title or "CHIEF FINANCIAL" in title:
                if exec_profile.tenure_years is not None:
                    data["cfo_tenure_months"] = exec_profile.tenure_years * 12
                if exec_profile.is_interim is not None:
                    interim = exec_profile.is_interim.value
                    tenure = exec_profile.tenure_years or 0
                    data["interim_cfo"] = interim and tenure <= 3

    return data
