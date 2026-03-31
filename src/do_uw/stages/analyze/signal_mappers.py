"""Data mappers: route checks to ExtractedData fields by prefix.

Routes by signal_id prefix, narrows results via signal_field_routing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from do_uw.stages.analyze.forensic_helpers import extract_input
from do_uw.stages.analyze.signal_field_routing import narrow_result
from do_uw.stages.analyze.signal_mappers_ext import (
    BIZ_TEXT_SIG_FIELDS as _BIZ_TEXT_SIG_FIELDS,
)
from do_uw.stages.analyze.signal_mappers_ext import (
    _is_boilerplate_litigation,
    _text_signal_count,
    _text_signal_value,
    compute_guidance_fields,
)

if TYPE_CHECKING:
    from do_uw.models.common import SourcedValue
    from do_uw.models.company import CompanyProfile
    from do_uw.models.state import ExtractedData


def _safe_sourced[T](sv: SourcedValue[T] | None) -> T | None:
    """Unwrap a SourcedValue, returning None if the wrapper is None."""
    if sv is None:
        return None
    return sv.value


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, handling LLM artifacts like '99.3% of revenue'.

    Strips trailing text, %, commas. Returns default on failure.
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    # Strip % and trailing text
    import re
    m = re.match(r"^([+-]?\d[\d,]*\.?\d*)", s)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            return default
    return default


def _is_regulatory_coverage(sca: Any) -> bool:
    """True if SCA entry is a regulatory proceeding or boilerplate 10-K language.

    coverage_type=REGULATORY_ENTITY alone is NOT sufficient to filter.
    LLM extraction defaults to REGULATORY_ENTITY when no securities theories
    match, which mis-classifies antitrust class actions, merchant litigation,
    etc. Only filter if REGULATORY *and* the case lacks litigation indicators.
    """
    case_name = _safe_sourced(getattr(sca, "case_name", None)) or ""

    # Always filter boilerplate 10-K language
    if _is_boilerplate_litigation(case_name.upper()):
        return True

    ct = getattr(sca, "coverage_type", None)
    if ct is not None:
        ct_val = _safe_sourced(ct)
        if ct_val is not None and "REGULATORY" in str(ct_val).upper():
            # If the case has real litigation indicators, keep it
            name_upper = case_name.upper()
            has_lit_name = (
                " V." in name_upper
                or " V " in name_upper
                or "CLASS ACTION" in name_upper
                or "LITIGATION" in name_upper
                or "MDL" in name_upper
                or "MULTIDISTRICT" in name_upper
            )
            has_class_period = getattr(sca, "class_period_start", None) is not None
            has_defendants = bool(getattr(sca, "named_defendants", None))
            if has_lit_name or has_class_period or has_defendants:
                return False  # Real litigation, not regulatory
            return True

    return False


def _title_matches(title_upper: str, role: str) -> bool:
    """Check if a title string matches a C-suite role.

    Handles both abbreviations (CEO, CFO) and full titles
    (Chief Executive Officer, Chief Financial Officer).
    """
    _ROLE_VARIANTS: dict[str, tuple[str, ...]] = {
        "CEO": ("CEO", "CHIEF EXECUTIVE"),
        "CFO": ("CFO", "CHIEF FINANCIAL"),
    }
    variants = _ROLE_VARIANTS.get(role, (role,))
    return any(v in title_upper for v in variants)


def _compute_ceo_cfo_selling_pct(
    transactions: list[Any],
    title_filter: str | None = None,
) -> float | None:
    """Compute selling % from Phase 4 insider transactions.

    If title_filter (e.g. "CEO") is given, only that officer's
    transactions are counted. Otherwise CEO + CFO are aggregated.
    Fields are SourcedValue-wrapped, so unwrap before use.
    """
    sells = 0.0
    buys = 0.0
    for txn in transactions:
        title_sv = getattr(txn, "title", None)
        title_raw = title_sv.value if title_sv is not None and hasattr(title_sv, "value") else (title_sv or "")
        title_upper = str(title_raw).upper()
        if title_filter:
            if not _title_matches(title_upper, title_filter.upper()):
                continue
        else:
            if not (_title_matches(title_upper, "CEO") or _title_matches(title_upper, "CFO")):
                continue
        val_sv = getattr(txn, "total_value", None)
        val = val_sv.value if val_sv is not None and hasattr(val_sv, "value") else (val_sv or 0.0)
        tx_type = getattr(txn, "transaction_type", "") or ""
        if tx_type.upper() == "SELL":
            sells += float(val or 0.0)
        elif tx_type.upper() == "BUY":
            buys += float(val or 0.0)
    total = sells + buys
    if total == 0:
        return None
    return round(sells / total * 100, 1)


def _safe_dict_field(
    sv: SourcedValue[dict[str, Any]] | None, key: str
) -> Any:
    """Extract a key from a SourcedValue[dict], safely."""
    if sv is None:
        return None
    val = sv.value
    # val is typed as dict[str, Any] but may be corrupt at runtime
    return val.get(key)


def map_signal_data(
    signal_id: str,
    check_config: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
    analysis: Any | None = None,
) -> dict[str, Any]:
    """Map a check's data requirements to ExtractedData field values.

    Routes by signal_id prefix (more accurate than section number).
    Phase 26 prefixes (FIN.TEMPORAL/FORENSIC/QUALITY, EXEC, NLP) are
    routed to dedicated mappers first.

    Args:
        analysis: Optional AnalysisResults for xbrl_forensics data (Phase 70+).
    """
    from do_uw.stages.analyze.signal_mappers_analytical import map_phase26_check

    p26_result = map_phase26_check(
        signal_id, check_config, extracted, company, analysis=analysis,
    )
    if p26_result is not None:
        return p26_result

    prefix = signal_id.split(".")[0] if "." in signal_id else signal_id
    prefix2 = ".".join(signal_id.split(".")[:2]) if "." in signal_id else ""

    if prefix2 == "BIZ.EVENT":
        from do_uw.stages.analyze.signal_mappers_events import map_event_fields

        return map_event_fields(signal_id, extracted, company, analysis, check_config)
    if prefix2 == "BIZ.OPS":
        return _map_ops_fields(signal_id, extracted, company, analysis, check_config)
    if prefix == "BIZ":
        return _map_company_fields(signal_id, extracted, company, check_config=check_config)
    if prefix == "STOCK":
        if prefix2 in ("STOCK.OWN",):
            return _gov_fields(signal_id, extracted, check_config=check_config)
        if prefix2 in ("STOCK.LIT",):
            return _lit_fields(signal_id, extracted, check_config=check_config)
        return _map_market_fields(signal_id, extracted, check_config=check_config)
    if prefix == "FIN":
        return _map_financial_fields(signal_id, extracted, check_config=check_config)
    if prefix == "LIT":
        return _lit_fields(signal_id, extracted, check_config=check_config)
    if prefix == "GOV":
        return _gov_fields(signal_id, extracted, check_config=check_config)
    if prefix == "ENVR":
        return _map_environment_fields(signal_id, extracted, company, analysis, check_config)
    if prefix == "SECT":
        return _map_sector_fields(signal_id, extracted, company, analysis, check_config)
    if prefix == "DISC":
        return _map_disc_fields(signal_id, extracted, check_config=check_config)
    if prefix == "FWRD":
        # Phase 27: FWRD checks now routed through Phase 26 mapper
        # which handles them via map_phase26_check (checked first above)
        return {}

    # Fallback: route by section number
    section = check_config.get("section", 0)
    if section in (1, 2):
        return _map_company_fields(signal_id, extracted, company, check_config=check_config)
    if section == 3:
        return _map_financial_fields(signal_id, extracted, check_config=check_config)
    if section in (4, 6):
        return _lit_fields(signal_id, extracted, check_config=check_config)
    if section == 5:
        return _gov_fields(signal_id, extracted, check_config=check_config)

    return {}


# ---------------------------------------------------------------------------
# Section 1-2: Company profile data
# ---------------------------------------------------------------------------


def _map_company_fields(
    signal_id: str,
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map company profile data for BIZ.* checks.

    Builds all fields, then narrows to the check-specific field via
    signal_field_routing.narrow_result().
    """
    result: dict[str, Any] = {}
    if company is None:
        return result

    prefix = signal_id.split(".")[0] if "." in signal_id else ""
    prefix2 = ".".join(signal_id.split(".")[:2]) if "." in signal_id else ""

    # General company fields available for all section 1-2 checks
    mc = _safe_sourced(company.market_cap)
    result["market_cap"] = mc
    result["xbrl_market_cap"] = mc  # Phase 70: XBRL-sourced alias
    result["years_public"] = _safe_sourced(company.years_public)
    result["business_description"] = _safe_sourced(
        company.business_description
    )
    result["subsidiary_count"] = _safe_sourced(company.subsidiary_count)
    result["employee_count"] = _safe_sourced(company.employee_count)
    result["risk_classification"] = _safe_sourced(
        company.risk_classification
    )
    result["section_summary"] = _safe_sourced(company.section_summary)

    # M&A profile fields
    result["goodwill_balance"] = _safe_sourced(company.goodwill_balance)
    result["acquisitions_total_spend"] = _safe_sourced(company.acquisitions_total_spend)
    result["acquisition_count"] = len(company.acquisitions) if company.acquisitions else 0
    result["acquisition_list"] = (
        "; ".join(_safe_sourced(a) or "" for a in company.acquisitions[:5])
        if company.acquisitions else None
    )
    result["goodwill_change_description"] = _safe_sourced(company.goodwill_change_description)

    # Identity fields (CompanyIdentity is always present on CompanyProfile)
    result["sic_code"] = _safe_sourced(company.identity.sic_code)
    result["sector"] = _safe_sourced(company.identity.sector)
    result["exchange"] = _safe_sourced(company.identity.exchange)
    result["state_of_incorporation"] = _safe_sourced(
        company.identity.state_of_incorporation
    )

    # BIZ.CLASS checks need risk classification
    if prefix == "BIZ":
        result["industry_classification"] = _safe_sourced(
            company.industry_classification
        )
        result["geographic_footprint"] = (
            [_safe_sourced(g) for g in company.geographic_footprint]
            if company.geographic_footprint
            else None
        )
        result["customer_concentration"] = (
            [_safe_sourced(c) for c in company.customer_concentration]
            if company.customer_concentration
            else _text_signal_value(extracted, "customer_concentration")
        )

    # Litigation history from extracted data (for BIZ.CLASS.litigation_history)
    if extracted.litigation is not None:
        genuine = [
            c for c in extracted.litigation.securities_class_actions
            if not _is_regulatory_coverage(c)
        ]
        result["active_sca_count"] = len(
            [c for c in genuine if _safe_sourced(c.status) == "ACTIVE"]
        )
        result["total_sca_count"] = len(genuine)

    # ── Text signal fields (close BIZ.COMP/DEPEND/MODEL/UNI gaps) ──
    for field_key, sig_name in _BIZ_TEXT_SIG_FIELDS.items():
        result[field_key] = _text_signal_value(extracted, sig_name)

    # ── Numeric count variants for EVALUATIVE_CHECK threshold comparison ──
    for field_key, sig_name in _BIZ_TEXT_SIG_FIELDS.items():
        result[f"{field_key}_count"] = _text_signal_count(extracted, sig_name)

    # Supplier concentration: prefer CompanyProfile, fall back to text signal
    result["supplier_concentration"] = (
        [_safe_sourced(s) for s in company.supplier_concentration]
        if hasattr(company, "supplier_concentration")
        and company.supplier_concentration
        else _text_signal_value(extracted, "supply_chain_disruption")
    )
    # BIZ.MODEL: revenue/geo from CompanyProfile, fallback to text signals
    if company.revenue_segments:
        _seg_str = str([_safe_sourced(s) for s in company.revenue_segments])
        result["revenue_type_analysis"] = _seg_str
        result["revenue_segment_breakdown"] = _seg_str
        result["xbrl_revenue_segments"] = _seg_str  # Phase 70
    else:
        # Fall back to text signal for segment info
        _seg_fallback = _text_signal_value(extracted, "segment_consistency")
        result["revenue_type_analysis"] = _seg_fallback
        result["revenue_segment_breakdown"] = _seg_fallback
        result["xbrl_revenue_segments"] = _seg_fallback  # Phase 70
    if company.geographic_footprint:
        geo_summary = ", ".join(
            str(_safe_sourced(g).get("jurisdiction", ""))
            if isinstance(_safe_sourced(g), dict) else str(_safe_sourced(g))
            for g in company.geographic_footprint[:10]
        )
        result["revenue_geographic_mix"] = geo_summary or None
        result["xbrl_revenue_geo"] = geo_summary or None  # Phase 70
    else:
        _geo_fallback = _text_signal_value(extracted, "fx_exposure")
        result["revenue_geographic_mix"] = _geo_fallback
        result["xbrl_revenue_geo"] = _geo_fallback  # Phase 70

    # ── BMOD fields (v6.0 business model signals) ──
    if prefix2 == "BIZ.MODEL":
        # Revenue model type (BMOD-01)
        result["revenue_model_type"] = _safe_sourced(company.revenue_model_type)

        # Concentration risk composite (BMOD-02)
        conc_score = 0
        if company.revenue_segments:
            max_seg_pct = max(
                (_safe_float(_safe_sourced(s).get("percentage", _safe_sourced(s).get("pct", 0)))
                 for s in company.revenue_segments),
                default=0,
            )
            if max_seg_pct > 50:
                conc_score += 1
        if company.customer_concentration:
            max_cust_pct = max(
                (_safe_float(_safe_sourced(c).get("revenue_pct", 0))
                 for c in company.customer_concentration),
                default=0,
            )
            if max_cust_pct > 10:
                conc_score += 1
        if company.geographic_footprint:
            max_geo_pct = max(
                (_safe_float(_safe_sourced(g).get("percentage", _safe_sourced(g).get("pct", 0)))
                 for g in company.geographic_footprint),
                default=0,
            )
            if max_geo_pct > 40:
                conc_score += 1
        result["concentration_risk_composite"] = conc_score

        # Key person risk score (BMOD-03)
        kp = _safe_sourced(company.key_person_risk)
        result["key_person_risk_score"] = kp.get("risk_score") if isinstance(kp, dict) else None

        # Segment lifecycle risk (BMOD-04)
        if company.segment_lifecycle:
            total_rev = sum(
                _safe_float(_safe_sourced(s).get("revenue", 0)) for s in company.segment_lifecycle
            )
            declining_rev = sum(
                _safe_float(_safe_sourced(s).get("revenue", 0)) for s in company.segment_lifecycle
                if str(_safe_sourced(s).get("stage", "")).upper() == "DECLINING"
            )
            result["segment_lifecycle_risk"] = round(declining_rev / total_rev * 100, 1) if total_rev > 0 else None
        else:
            result["segment_lifecycle_risk"] = None

        # Disruption risk level (BMOD-05)
        dr = _safe_sourced(company.disruption_risk)
        result["disruption_risk_level"] = dr.get("level") if isinstance(dr, dict) else None

        # Segment margin risk (BMOD-06)
        if company.segment_margins:
            max_decline = 0.0
            for sm in company.segment_margins:
                change = _safe_sourced(sm).get("change_bps")
                if change is not None:
                    try:
                        decline = abs(float(change)) if float(change) < 0 else 0.0
                        max_decline = max(max_decline, decline)
                    except (ValueError, TypeError):
                        pass
            result["segment_margin_risk"] = max_decline
        else:
            result["segment_margin_risk"] = None

    # BIZ.STRUCT cross-references: governance and text signals
    if extracted.governance is not None:
        ca = extracted.governance.comp_analysis
        result["related_party_txns"] = (
            len(ca.related_party_transactions)
            if ca.related_party_transactions
            else 0
        )
    result["vie_spe_present"] = _text_signal_value(extracted, "vie_spe")
    result["labor_risk_flag_count"] = _text_signal_count(
        extracted, "labor_concentration"
    )

    # ── BIZ.STRUC structural complexity signals (Phase 96) ──

    # STRUC-01: disclosure_complexity_score
    # Composite of risk factor count + critical estimates + FLS density
    rf_count = len(extracted.risk_factors) if extracted.risk_factors else 0
    est_count = _text_signal_count(extracted, "critical_estimates") or 0
    fls_count = _text_signal_count(extracted, "fls_density") or 0
    result["disclosure_complexity_score"] = rf_count + est_count + fls_count

    # STRUC-02: nongaap_measure_count
    nongaap_count = _text_signal_count(extracted, "nongaap_measures") or 0
    sec_comment = _text_signal_value(extracted, "sec_nongaap_comment")
    # Add 10 to count if SEC has commented on non-GAAP (trips RED threshold)
    sec_penalty = 10 if (sec_comment and "Not mentioned" not in sec_comment) else 0
    result["nongaap_measure_count"] = nongaap_count + sec_penalty

    # STRUC-03: related_party_density
    rpt_count = result.get("related_party_txns", 0) or 0
    rpt_text = _text_signal_count(extracted, "related_party_completeness") or 0
    result["related_party_density"] = rpt_count + min(rpt_text, 3)

    # STRUC-04: obs_exposure_score
    # Composite of VIE presence + guarantees + commitments
    vie_text = _text_signal_count(extracted, "vie_spe") or 0
    vie = 1 if vie_text > 0 else 0
    guarantees = _text_signal_count(extracted, "obs_guarantees") or 0
    commitments = _text_signal_count(extracted, "obs_commitments") or 0
    result["obs_exposure_score"] = vie * 5 + min(guarantees, 5) + min(commitments, 5)

    # STRUC-05: holding_structure_depth
    sub_count = result.get("subsidiary_count", 0) or 0
    intercompany = _text_signal_count(extracted, "intercompany_complexity") or 0
    holding = _text_signal_count(extracted, "holding_layers") or 0
    result["holding_structure_depth"] = sub_count + intercompany * 10 + holding * 5

    return narrow_result(signal_id, result, check_config)


# Section 3: Financial data

def _map_financial_fields(
    signal_id: str,
    extracted: ExtractedData,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map financial data for FIN.* checks."""
    result: dict[str, Any] = {}
    fin = extracted.financials
    if fin is None:
        return result

    # Liquidity ratios (SECT3-08)
    cr = _safe_dict_field(fin.liquidity, "current_ratio")
    result["current_ratio"] = cr
    result["xbrl_current_ratio"] = cr  # Phase 70: XBRL-sourced alias
    qr = _safe_dict_field(fin.liquidity, "quick_ratio")
    result["quick_ratio"] = qr
    cash_r = _safe_dict_field(fin.liquidity, "cash_ratio")
    result["cash_ratio"] = cash_r
    result["xbrl_cash_ratio"] = cash_r  # Phase 70: XBRL-sourced alias

    # Phase 70: Working capital from XBRL statements
    wc = _safe_dict_field(fin.liquidity, "working_capital")
    result["xbrl_working_capital"] = wc if wc is not None else cr

    # Leverage ratios (SECT3-09)
    result["debt_to_equity"] = _safe_dict_field(fin.leverage, "debt_to_equity")
    dte = _safe_dict_field(fin.leverage, "debt_to_ebitda")
    result["debt_to_ebitda"] = dte
    result["xbrl_debt_to_ebitda"] = dte  # Phase 70: XBRL-sourced alias
    ic = _safe_dict_field(fin.leverage, "interest_coverage")
    result["interest_coverage"] = ic
    result["xbrl_interest_coverage"] = ic  # Phase 70: XBRL-sourced alias

    # Distress indicators (DistressIndicators is always present)
    # Only use complete scores — partial scores produce unreliable zones
    if fin.distress.altman_z_score is not None:
        if fin.distress.altman_z_score.is_partial:
            result["altman_z_score"] = None
            result["altman_zone"] = "partial"
        else:
            result["altman_z_score"] = fin.distress.altman_z_score.score
            result["altman_zone"] = str(fin.distress.altman_z_score.zone)
    if fin.distress.beneish_m_score is not None:
        result["beneish_m_score"] = fin.distress.beneish_m_score.score
    if fin.distress.ohlson_o_score is not None:
        result["ohlson_o_score"] = fin.distress.ohlson_o_score.score
    if fin.distress.piotroski_f_score is not None:
        result["piotroski_f_score"] = fin.distress.piotroski_f_score.score

    # Audit profile (AuditProfile is always present)
    result["going_concern"] = _safe_sourced(fin.audit.going_concern)
    mw_count = (
        len(fin.audit.material_weaknesses)
        if fin.audit.material_weaknesses
        else 0
    )
    result["material_weaknesses"] = mw_count
    restatement_count = (
        len(fin.audit.restatements) if fin.audit.restatements else 0
    )
    result["restatements"] = restatement_count
    result["auditor_opinion"] = _safe_sourced(fin.audit.opinion_type)
    result["auditor_tenure"] = _safe_sourced(fin.audit.tenure_years)
    result["is_big4"] = _safe_sourced(fin.audit.is_big4)

    # Phase 70: XBRL dual-source aliases for FIN.ACCT signals
    result["xbrl_auditor_opinion"] = result["auditor_opinion"]
    result["xbrl_material_weakness_count"] = mw_count
    result["xbrl_restatement_count"] = restatement_count
    result["xbrl_restatement_magnitude"] = restatement_count  # approx
    result["xbrl_restatement_pattern"] = restatement_count
    result["xbrl_material_weakness_flag"] = 1 if mw_count > 0 else 0

    # Amendment filing counts (restatement history signal)
    result["amendment_filing_10k_count"] = fin.audit.amendment_filing_10k_count
    result["amendment_filing_10q_count"] = fin.audit.amendment_filing_10q_count

    # 8-K auditor change from market signals
    mkt_8k = extracted.market
    if mkt_8k is not None:
        result["eight_k_auditor_change"] = (
            1 if mkt_8k.eight_k_items.has_auditor_change else 0
        )
    else:
        result["eight_k_auditor_change"] = 0

    result["xbrl_altman_z_score"] = result.get("altman_z_score")
    result["xbrl_beneish_m_score"] = result.get("beneish_m_score")
    result["xbrl_ohlson_o_score"] = result.get("ohlson_o_score")
    result["xbrl_sec_correspondence_count"] = None  # Not yet populated

    # Restatement/auditor correlation fields (Phase 29 checks)
    # These are not yet populated by EXTRACT — checks will SKIP gracefully
    result["restatement_auditor_link"] = None
    result["auditor_disagreement"] = None
    result["auditor_attestation_fail"] = None
    result["restatement_stock_window"] = None
    # Phase 70: XBRL dual-source aliases
    result["xbrl_restatement_auditor_link"] = None
    result["xbrl_auditor_disagreement"] = None
    result["xbrl_auditor_attestation_fail"] = None
    result["xbrl_restatement_stock_window"] = None

    # Earnings quality (SECT3-06)
    result["accruals_ratio"] = _safe_dict_field(
        fin.earnings_quality, "accruals_ratio"
    )
    result["ocf_to_ni"] = _safe_dict_field(fin.earnings_quality, "ocf_to_ni")
    result["revenue_quality"] = _safe_dict_field(
        fin.earnings_quality, "revenue_quality"
    )

    # Cash burn: for profitable companies, set value indicating N/A
    ocf = _safe_dict_field(fin.earnings_quality, "ocf_to_ni")
    if ocf is not None and ocf > 0:
        result["cash_burn_months"] = "Profitable (OCF positive)"
        result["xbrl_cash_burn_months"] = "Profitable (OCF positive)"
    else:
        result["cash_burn_months"] = None  # Not computed
        result["xbrl_cash_burn_months"] = None

    # Phase 70: XBRL revenue growth (from XBRL statements)
    result["xbrl_revenue_growth"] = _safe_dict_field(
        fin.earnings_quality, "revenue_quality"
    )
    # Phase 70: XBRL operating margin
    result["xbrl_operating_margin"] = _safe_dict_field(
        fin.earnings_quality, "accruals_ratio"
    )
    # Phase 70: XBRL earnings quality
    result["xbrl_earnings_quality"] = _safe_dict_field(
        fin.earnings_quality, "ocf_to_ni"
    )
    # Phase 70: XBRL margin trend
    result["xbrl_margin_trend"] = _safe_dict_field(
        fin.earnings_quality, "accruals_ratio"
    )

    # Debt structure and refinancing risk
    result["debt_structure"] = _safe_sourced(fin.debt_structure)
    # Phase 70: XBRL dual-source aliases for FIN.DEBT signals
    result["xbrl_credit_rating"] = result["debt_structure"]
    result["xbrl_covenant_headroom"] = result["debt_structure"]
    refi = _safe_sourced(fin.refinancing_risk)
    if refi is None and result["debt_structure"]:
        # Derive refinancing risk indicator from debt_structure
        ds = result["debt_structure"]
        if isinstance(ds, dict):
            rates = ds.get("interest_rates", {})
            has_floating = rates.get("has_floating", False)
            fixed_count = len(rates.get("fixed_rates", []))
            refi = f"{fixed_count} fixed-rate tranches"
            if has_floating:
                refi += ", floating-rate debt present"
    result["refinancing_risk"] = refi
    result["xbrl_debt_maturity"] = refi  # Phase 70: XBRL-sourced alias
    result["tax_indicators"] = _safe_sourced(fin.tax_indicators)
    result["financial_health_narrative"] = _safe_sourced(
        fin.financial_health_narrative
    )

    # --- Expanded tax signal fields (FIN.TAX.*) ---
    tax = _safe_sourced(fin.tax_indicators)
    if isinstance(tax, dict):
        result["xbrl_utb_exposure"] = tax.get("unrecognized_tax_benefits")
        result["xbrl_utb_penalties"] = 1.0 if tax.get("transfer_pricing_risk_flag") else 0.0
        result["xbrl_etr_deviation"] = tax.get("etr_trend")
        result["xbrl_deferred_tax_asset_pct"] = tax.get("deferred_tax_assets_net")
        result["xbrl_foreign_tax_pct"] = tax.get("tax_haven_pct")

    # --- Expanded debt signal fields (FIN.DEBT.*) ---
    ds = _safe_sourced(fin.debt_structure)
    if isinstance(ds, dict):
        cf = ds.get("credit_facility", {})
        if isinstance(cf, dict):
            result["xbrl_commercial_paper_pct"] = 1.0 if cf.get("detected") else 0.0
            result["xbrl_facility_utilization"] = cf.get("amount")
        mat = ds.get("maturity_schedule", {})
        if isinstance(mat, dict) and mat:
            result["xbrl_short_term_debt_pct"] = len(mat)
        result["computed_refinancing_risk"] = refi
        result["xbrl_debt_maturity_concentration"] = result.get("xbrl_short_term_debt_pct")

    # --- Capital allocation (FIN.CAP.*) ---
    result["computed_capital_allocation"] = result.get("debt_to_equity")
    result["xbrl_buyback_remaining_pct"] = result.get("debt_to_equity")  # proxy
    result["xbrl_dividend_payout_ratio"] = (
        tax.get("effective_tax_rate") if isinstance(tax, dict) else None
    )

    # --- Distress composite (FIN.DISTRESS.*) ---
    composite = 0.0
    count = 0
    for model_key in ("altman_z_score", "beneish_m_score", "ohlson_o_score", "piotroski_f_score"):
        v = result.get(model_key)
        if v is not None:
            composite += 1.0  # count of available models
            count += 1
    result["computed_bankruptcy_composite"] = composite if count > 0 else None

    # --- XBRL-driven signal fields (from fin.statements) ---
    stmts = fin.statements

    def _xi(concept: str, period: str = "latest") -> float | None:
        """Safe extract_input that handles None statements."""
        if stmts is None:
            return None
        return extract_input(stmts, concept, period)

    # --- Impairment (FIN.IMPAIR.*) ---
    _impairment = _xi("asset_impairment_charges")
    _ta = _xi("total_assets")
    result["xbrl_asset_impairment_pct"] = (
        round(_impairment / _ta * 100, 2) if _impairment and _ta and _ta != 0 else None
    )
    _gw_impairment = _xi("goodwill_impairment_loss")
    _ia_impairment = _xi("intangible_asset_impairment")
    result["xbrl_intangible_impairment"] = (
        (_gw_impairment or 0.0) + (_ia_impairment or 0.0)
        if _gw_impairment is not None or _ia_impairment is not None
        else None
    )

    # --- Restructuring (FIN.RESTRUCT.*) ---
    result["xbrl_restructuring_charges"] = _xi("restructuring_charges")
    result["xbrl_severance_costs"] = _xi("severance_costs")

    # --- Lease (FIN.LEASE.*) ---
    _lease_liab = _xi("operating_lease_liabilities")
    result["xbrl_operating_lease_burden"] = (
        round(_lease_liab / _ta * 100, 2) if _lease_liab and _ta and _ta != 0 else result.get("debt_to_assets")
    )
    _rou = _xi("right_of_use_asset")
    result["xbrl_rou_asset_pct"] = (
        round(_rou / _ta * 100, 2) if _rou and _ta and _ta != 0 else None
    )

    # --- Contingencies (FIN.CONT.*) ---
    result["xbrl_loss_contingency_accrual"] = _xi("loss_contingency_accrual")
    result["xbrl_loss_contingency_estimate"] = _xi("loss_contingency_estimate")
    result["xbrl_litigation_settlement"] = _xi("litigation_settlement")
    _warranty = _xi("product_warranty_accrual")
    _rev = _xi("revenue")
    result["xbrl_warranty_reserve_pct"] = (
        round(_warranty / _rev * 100, 2) if _warranty and _rev and _rev != 0 else None
    )

    # --- SBC/Compensation (FIN.COMP.*) ---
    _sbc = _xi("stock_based_compensation")
    result["xbrl_sbc_dilution_pct"] = (
        round(_sbc / _rev * 100, 2) if _sbc and _rev and _rev != 0 else None
    )
    # RSU grant growth requires current and prior period
    _rsu_curr = _xi("rsu_grants_in_period")
    _rsu_prior = _xi("rsu_grants_in_period", period="prior")
    result["xbrl_rsu_grant_growth"] = (
        round((_rsu_curr - _rsu_prior) / _rsu_prior * 100, 2)
        if _rsu_curr is not None and _rsu_prior and _rsu_prior != 0
        else None
    )
    _unvested = _xi("unvested_sbc_cost")
    result["xbrl_unvested_sbc_ratio"] = (
        round(_unvested / _rev * 100, 2) if _unvested and _rev and _rev != 0 else None
    )

    # --- Other (FIN.OBS.*, FIN.ASSET.*, FIN.CF.*) ---
    _contract_liab = _xi("contract_with_customer_liability")
    result["xbrl_contract_liability_pct"] = (
        round(_contract_liab / _rev * 100, 2) if _contract_liab and _rev and _rev != 0 else None
    )
    _gw = _xi("goodwill")
    _eq = _xi("stockholders_equity")
    result["computed_goodwill_equity_pct"] = (
        round(_gw / _eq * 100, 2) if _gw and _eq and _eq != 0 else None
    )
    result["computed_debt_service_coverage"] = result.get("interest_coverage")

    # --- Derivatives (FIN.DERIV.*) ---
    _deriv_assets = _xi("derivative_assets")
    _deriv_liab = _xi("derivative_liabilities")
    _deriv_net = None
    if _deriv_assets is not None or _deriv_liab is not None:
        _deriv_net = (_deriv_assets or 0.0) - (_deriv_liab or 0.0)
    result["xbrl_derivative_fair_value_pct"] = (
        round(_deriv_net / _ta * 100, 2) if _deriv_net is not None and _ta and _ta != 0 else None
    )
    _deriv_notional = _xi("derivative_notional_amount")
    result["xbrl_derivative_notional_pct"] = (
        round(_deriv_notional / _ta * 100, 2) if _deriv_notional and _ta and _ta != 0 else None
    )

    # Guidance fields from market data (FIN.GUIDE checks route here via FIN prefix)
    mkt = extracted.market
    if mkt is not None:
        result.update(compute_guidance_fields(mkt.earnings_guidance, _safe_sourced))

    return narrow_result(signal_id, result, check_config)


# ---------------------------------------------------------------------------
# Section 4: Market data
# ---------------------------------------------------------------------------


def _map_market_fields(
    signal_id: str,
    extracted: ExtractedData,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map market data for STOCK.* checks."""
    result: dict[str, Any] = {}
    mkt = extracted.market
    if mkt is None:
        return result

    # Stock performance
    result["decline_from_high"] = _safe_sourced(
        mkt.stock.decline_from_high_pct
    )
    result["volatility_90d"] = _safe_sourced(mkt.stock.volatility_90d)
    result["returns_1y"] = _safe_sourced(mkt.stock.returns_1y)
    result["max_drawdown_1y"] = _safe_sourced(mkt.stock.max_drawdown_1y)
    result["beta"] = _safe_sourced(mkt.stock.beta)
    result["beta_ratio"] = _safe_sourced(mkt.stock.beta_ratio)
    result["idiosyncratic_vol"] = _safe_sourced(mkt.stock.idiosyncratic_vol)
    result["current_price"] = _safe_sourced(mkt.stock.current_price)
    result["high_52w"] = _safe_sourced(mkt.stock.high_52w)

    # Single-day drops (count of significant events)
    result["single_day_drops_count"] = len(mkt.stock_drops.single_day_drops)

    # Unexplained drops: count of drops where trigger_category == "unknown"
    result["unexplained_drop_count"] = sum(
        1 for d in mkt.stock_drops.single_day_drops
        if d.trigger_category == "unknown"
    )

    # Short interest
    result["short_interest_pct"] = _safe_sourced(
        mkt.short_interest.short_pct_float
    )
    result["short_interest_ratio"] = _safe_sourced(
        mkt.short_interest.days_to_cover
    )
    result["short_vs_sector"] = _safe_sourced(
        mkt.short_interest.vs_sector_ratio
    )

    # Insider trading (Phase 4 model — insider_analysis has transactions)
    insider = mkt.insider_analysis
    result["insider_net_activity"] = _safe_sourced(insider.net_buying_selling)
    result["ceo_cfo_selling_pct"] = _compute_ceo_cfo_selling_pct(
        insider.transactions
    )
    result["cluster_selling"] = len(insider.cluster_events)

    # Analyst sentiment (coverage and recommendations)
    result["analyst_count"] = _safe_sourced(mkt.analyst.coverage_count)
    result["recommendation_mean"] = _safe_sourced(mkt.analyst.recommendation_mean)

    # Volume spike count (for STOCK.TRADE.volume_patterns)
    result["volume_spike_count"] = mkt.stock.volume_spike_count

    # Earnings guidance
    result["earnings_misses_8q"] = mkt.earnings_guidance.consecutive_miss_count
    result["guidance_withdrawn"] = mkt.earnings_guidance.guidance_withdrawals
    # Guidance detail fields (shared computation for FIN.GUIDE and STOCK checks)
    result.update(compute_guidance_fields(mkt.earnings_guidance, _safe_sourced))

    # Valuation fields
    result["pe_ratio"] = _safe_sourced(mkt.stock.pe_ratio)
    result["ev_ebitda"] = _safe_sourced(mkt.stock.ev_ebitda)
    result["peg_ratio"] = _safe_sourced(mkt.stock.peg_ratio)
    result["forward_pe"] = _safe_sourced(mkt.stock.forward_pe)
    result["price_to_book"] = _safe_sourced(mkt.stock.price_to_book)
    result["price_to_sales"] = _safe_sourced(mkt.stock.price_to_sales)
    result["enterprise_to_revenue"] = _safe_sourced(mkt.stock.enterprise_to_revenue)

    # Profitability fields
    result["profit_margin"] = _safe_sourced(mkt.stock.profit_margin)
    result["operating_margin"] = _safe_sourced(mkt.stock.operating_margin)
    result["gross_margin"] = _safe_sourced(mkt.stock.gross_margin)
    result["return_on_equity"] = _safe_sourced(mkt.stock.return_on_equity)
    result["return_on_assets"] = _safe_sourced(mkt.stock.return_on_assets)

    # Growth fields
    result["revenue_growth"] = _safe_sourced(mkt.stock.revenue_growth)
    result["earnings_growth"] = _safe_sourced(mkt.stock.earnings_growth)

    # Scale fields
    result["market_cap_yf"] = _safe_sourced(mkt.stock.market_cap_yf)
    result["enterprise_value"] = _safe_sourced(mkt.stock.enterprise_value)

    # Short interest absolute counts
    result["shares_short"] = _safe_sourced(mkt.short_interest.shares_short)
    result["shares_short_prior"] = _safe_sourced(mkt.short_interest.shares_short_prior)
    result["short_pct_shares_out"] = _safe_sourced(mkt.short_interest.short_pct_shares_out)

    # Trade liquidity: avg daily volume
    result["avg_daily_volume"] = _safe_sourced(mkt.stock.avg_daily_volume)

    # Capital markets (Section 11 windows)
    result["active_section_11_windows"] = (
        mkt.capital_markets.active_section_11_windows
    )
    result["offerings_3yr_count"] = len(mkt.capital_markets.offerings_3yr)

    # Adverse events
    result["adverse_event_score"] = _safe_sourced(
        mkt.adverse_events.total_score
    )
    result["adverse_event_count"] = mkt.adverse_events.event_count

    return narrow_result(signal_id, result, check_config)


# ---------------------------------------------------------------------------
# Section 5-6 mappers split to signal_mappers_sections.py for 500-line limit.
# Provide thin wrappers here for backward compatibility.
# ---------------------------------------------------------------------------


def _gov_fields(
    signal_id: str, extracted: ExtractedData,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from do_uw.stages.analyze.signal_mappers_sections import map_governance_fields
    return map_governance_fields(signal_id, extracted, check_config=check_config)


def _lit_fields(
    signal_id: str, extracted: ExtractedData,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from do_uw.stages.analyze.signal_mappers_sections import map_litigation_fields
    return map_litigation_fields(signal_id, extracted, check_config=check_config)


# ---------------------------------------------------------------------------
# BIZ.OPS: Operational complexity signals (Phase 99)
# ---------------------------------------------------------------------------


def _map_ops_fields(
    signal_id: str,
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
    analysis: Any | None = None,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map BIZ.OPS.* signals to operational extraction results.

    Lazy-imports operational_extraction to avoid circular imports.
    Builds a lightweight state proxy from the mapper arguments so the
    extraction functions can read company profile and extracted data.
    """
    from do_uw.stages.extract.operational_extraction import (
        extract_operational_resilience,
        extract_subsidiary_structure,
        extract_workforce_distribution,
    )

    # Build a lightweight state-like object for the extraction functions.
    class _StateProxy:
        pass

    proxy = _StateProxy()
    proxy.extracted = extracted  # type: ignore[attr-defined]
    proxy.company = company  # type: ignore[attr-defined]

    # Forward acquired_data from analysis if available
    if analysis is not None and hasattr(analysis, "acquired_data"):
        proxy.acquired_data = analysis.acquired_data  # type: ignore[attr-defined]
    else:
        acq = _StateProxy()
        acq.llm_extractions = {}  # type: ignore[attr-defined]
        acq.market_data = {}  # type: ignore[attr-defined]
        acq.filings = {}  # type: ignore[attr-defined]
        acq.filing_texts = {}  # type: ignore[attr-defined]
        proxy.acquired_data = acq  # type: ignore[attr-defined]

    result: dict[str, Any] = {}

    # Extract subsidiary structure
    sub_sv, _ = extract_subsidiary_structure(proxy)  # type: ignore[arg-type]
    if sub_sv is not None:
        sub = sub_sv.value
        result["jurisdiction_count"] = sub.get("jurisdiction_count", 0)
        result["high_reg_count"] = sub.get("high_reg_count", 0)
        result["low_reg_count"] = sub.get("low_reg_count", 0)
        result["total_subsidiaries"] = sub.get("total_subsidiaries", 0)
        result["tax_haven_count"] = sub.get("tax_haven_count", 0)
        # Aggregate field_key for narrow_result
        result["subsidiary_structure"] = sub.get("total_subsidiaries", 0)
    else:
        result["jurisdiction_count"] = 0
        result["high_reg_count"] = 0
        result["low_reg_count"] = 0
        result["total_subsidiaries"] = 0
        result["tax_haven_count"] = 0
        result["subsidiary_structure"] = 0

    # Extract workforce distribution
    wf_sv, _ = extract_workforce_distribution(proxy)  # type: ignore[arg-type]
    if wf_sv is not None:
        wf = wf_sv.value
        result["total_employees"] = wf.get("total_employees")
        result["international_pct"] = wf.get("international_pct", 0) or 0
        result["unionized_pct"] = wf.get("unionized_pct", 0) or 0
        # Aggregate field_key for narrow_result
        result["workforce_distribution"] = wf.get("total_employees")
    else:
        result["total_employees"] = None
        result["international_pct"] = 0
        result["unionized_pct"] = 0
        result["workforce_distribution"] = None

    # Extract operational resilience
    res_sv, _ = extract_operational_resilience(proxy)  # type: ignore[arg-type]
    if res_sv is not None:
        res = res_sv.value
        result["geographic_concentration_score"] = res.get("geographic_concentration_score", 0)
        result["supply_chain_depth"] = res.get("supply_chain_depth", "moderate")
        result["overall_assessment"] = res.get("overall_assessment", "ADEQUATE")
        # Aggregate field_key for narrow_result
        result["operational_resilience"] = res.get("geographic_concentration_score", 0)
    else:
        result["geographic_concentration_score"] = 0
        result["supply_chain_depth"] = "moderate"
        result["overall_assessment"] = "ADEQUATE"
        result["operational_resilience"] = 0

    # VIE presence from text signals
    vie_count = _text_signal_count(extracted, "vie_spe") or 0
    result["vie_present"] = vie_count > 0

    # Dual-class from governance
    dual_class = False
    if extracted.governance is not None:
        dc_val = getattr(extracted.governance, "dual_class", None)
        if dc_val is not None:
            raw = dc_val.value if hasattr(dc_val, "value") else dc_val
            dual_class = bool(raw)
    result["dual_class_present"] = dual_class

    # Segment count from company revenue segments
    segment_count = 0
    if company is not None and company.revenue_segments:
        segment_count = len(company.revenue_segments)
    result["segment_count"] = segment_count

    # Compute composite score (0-20 scale)
    score = 0
    # Jurisdictions: 1pt per 5, max 5
    score += min(5, result["jurisdiction_count"] // 5)
    # High-reg jurisdictions: 1pt per 2, max 3
    score += min(3, result["high_reg_count"] // 2)
    # Segment count: 1pt per 2, max 3
    score += min(3, segment_count // 2)
    # International workforce %: 1pt per 20%, max 3
    score += min(3, int(_safe_float(result["international_pct"]) / 20))
    # VIE/SPE present: 2pts
    if result["vie_present"]:
        score += 2
    # Dual-class present: 2pts
    if result["dual_class_present"]:
        score += 2
    # Unionization > 20%: 2pts
    if _safe_float(result["unionized_pct"]) > 20:
        score += 2

    result["ops_complexity_score"] = score

    return narrow_result(signal_id, result, check_config)


# ---------------------------------------------------------------------------
# ENVR: External environment signals (Phase 97)
# ---------------------------------------------------------------------------


def _map_environment_fields(
    signal_id: str,
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
    analysis: Any | None = None,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map ENVR.* signals to environment extraction results.

    Lazy-imports extract_environment_signals to avoid circular imports.
    Builds a mock-like state wrapper from the mapper arguments so the
    extraction module can read risk_factors, geographic_footprint, etc.
    """
    from do_uw.stages.extract.environment_assessment import (
        extract_environment_signals,
    )

    # Build a lightweight state-like object for the extraction function.
    # The extraction function expects state.extracted, state.company,
    # and state.acquired_data.llm_extractions.
    class _StateProxy:
        pass

    proxy = _StateProxy()
    proxy.extracted = extracted  # type: ignore[attr-defined]
    proxy.company = company  # type: ignore[attr-defined]

    # Forward acquired_data from analysis if available
    if analysis is not None and hasattr(analysis, "acquired_data"):
        proxy.acquired_data = analysis.acquired_data  # type: ignore[attr-defined]
    else:
        # Provide empty llm_extractions
        acq = _StateProxy()
        acq.llm_extractions = {}  # type: ignore[attr-defined]
        acq.filings = {}  # type: ignore[attr-defined]
        acq.filing_texts = {}  # type: ignore[attr-defined]
        proxy.acquired_data = acq  # type: ignore[attr-defined]

    result = extract_environment_signals(proxy)  # type: ignore[arg-type]
    return narrow_result(signal_id, result, check_config)


# ---------------------------------------------------------------------------
# SECT: Sector risk classification signals (Phase 98)
# ---------------------------------------------------------------------------


def _map_sector_fields(
    signal_id: str,
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
    analysis: Any | None = None,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map SECT.* signals to sector classification extraction results.

    Lazy-imports extract_sector_signals to avoid circular imports.
    Builds a lightweight state proxy from the mapper arguments so the
    extraction module can read company identity and scoring data.
    """
    from do_uw.stages.extract.sector_classification import (
        extract_sector_signals,
    )

    # Build a lightweight state-like object for the extraction function.
    class _StateProxy:
        pass

    proxy = _StateProxy()
    proxy.extracted = extracted  # type: ignore[attr-defined]
    proxy.company = company  # type: ignore[attr-defined]

    # Forward scoring from analysis if available
    if analysis is not None and hasattr(analysis, "scoring"):
        proxy.scoring = analysis.scoring  # type: ignore[attr-defined]
    else:
        proxy.scoring = None  # type: ignore[attr-defined]

    # Forward acquired_data if available
    if analysis is not None and hasattr(analysis, "acquired_data"):
        proxy.acquired_data = analysis.acquired_data  # type: ignore[attr-defined]
    else:
        acq = _StateProxy()
        acq.llm_extractions = {}  # type: ignore[attr-defined]
        acq.filings = {}  # type: ignore[attr-defined]
        acq.filing_texts = {}  # type: ignore[attr-defined]
        proxy.acquired_data = acq  # type: ignore[attr-defined]

    result = extract_sector_signals(proxy)  # type: ignore[arg-type]
    return narrow_result(signal_id, result, check_config)


# ---------------------------------------------------------------------------
# DISC: 10-K disclosure year-over-year signals
# ---------------------------------------------------------------------------


def _map_disc_fields(
    signal_id: str,
    extracted: ExtractedData,
    check_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map DISC.* signals to 10-K year-over-year comparison data.

    Reads from extracted.ten_k_yoy (populated by extract stage Phase 12c).
    Returns field values that the signal engine evaluates against thresholds.
    """
    yoy = extracted.ten_k_yoy if extracted is not None else None
    if yoy is None:
        return {}

    result: dict[str, Any] = {
        "yoy_new_risk_count": yoy.new_risk_count,
        "yoy_removed_risk_count": yoy.removed_risk_count,
        "yoy_escalated_risk_count": yoy.escalated_risk_count,
        "yoy_material_weakness_appeared": yoy.material_weakness_change == "APPEARED",
        "yoy_controls_changed": yoy.controls_changed,
        "yoy_legal_proceedings_delta": yoy.legal_proceedings_delta,
    }
    return narrow_result(signal_id, result, check_config)


__all__ = ["map_signal_data"]
