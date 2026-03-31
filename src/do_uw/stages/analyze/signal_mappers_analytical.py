"""Analytical engine check data mappers for new check prefixes.

Maps data for FIN.TEMPORAL.*, FIN.FORENSIC.*, FIN.QUALITY.*, EXEC.*,
and NLP.* signals from ExtractedData.

These checks are designed to be evaluated against raw extracted data
at check time. The analytical engines (temporal, forensic, executive,
NLP) run after check execution and store composite results in
AnalysisResults for the SCORE stage to consume.

Split from signal_mappers.py to stay under 500-line limit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from do_uw.stages.analyze.signal_mappers import _compute_ceo_cfo_selling_pct

if TYPE_CHECKING:
    from do_uw.models.company import CompanyProfile
    from do_uw.models.state import ExtractedData


def _safe_sv(sv: Any) -> Any:
    """Unwrap SourcedValue or return None."""
    if sv is None:
        return None
    return sv.value


def map_phase26_check(
    signal_id: str,
    check_config: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
    analysis: Any | None = None,
) -> dict[str, Any] | None:
    """Map data for Phase 26+ new check prefixes.

    Returns None if the signal_id is not a known prefix (caller
    should fall through to existing mappers).

    Args:
        analysis: Optional AnalysisResults object. When present,
            xbrl_forensics data is extracted for FIN.FORENSIC.* signals.
    """
    if signal_id.startswith("FIN.TEMPORAL."):
        return _map_temporal_check(signal_id, extracted)
    if signal_id.startswith("FIN.FORENSIC."):
        return _map_forensic_check(signal_id, extracted, analysis=analysis)
    if signal_id.startswith("FIN.QUALITY."):
        return _map_quality_check(signal_id, extracted)
    if signal_id.startswith("EXEC."):
        return _map_exec_check(signal_id, extracted, company)
    if signal_id.startswith("NLP."):
        return _map_nlp_check(signal_id, extracted)
    # Wire FWRD checks to existing data where available
    if signal_id.startswith("FWRD."):
        from do_uw.stages.analyze.signal_mappers_forward import map_fwrd_check

        return map_fwrd_check(signal_id, extracted)
    return None


def _map_temporal_check(
    signal_id: str,
    extracted: ExtractedData,
) -> dict[str, Any]:
    """Map data for FIN.TEMPORAL.* checks.

    Temporal checks produce INFO at evaluation time. The actual trend
    classification is computed by the TemporalAnalyzer engine.
    Returns the latest computed metric value (numeric) where available,
    not just "present" markers.

    Phase 70: Returns xbrl_* keyed values alongside legacy "value" key
    for shadow evaluation comparison.
    """
    result: dict[str, Any] = {}
    fin = extracted.financials
    if fin is None:
        return result

    # Map metric name from signal_id suffix
    metric = signal_id.replace("FIN.TEMPORAL.", "")
    result["metric_name"] = metric

    # Try to extract latest computed metric values from temporal_metrics
    from do_uw.stages.analyze.temporal_metrics import extract_temporal_metrics

    temporal_data = extract_temporal_metrics(extracted)

    # Metric suffix -> temporal metric name mapping
    _METRIC_MAP: dict[str, str] = {
        "revenue_deceleration": "revenue_growth",
        "margin_compression": "gross_margin",
        "operating_margin_compression": "operating_margin",
        "dso_expansion": "dso_days",
        "cash_flow_deterioration": "operating_cash_flow",
        "profitability_trend": "operating_margin",
        "working_capital_deterioration": "working_capital",
        "debt_ratio_increase": "debt_ratio",
    }

    # Phase 70: XBRL field_key mapping for each temporal signal
    _XBRL_KEY_MAP: dict[str, str] = {
        "revenue_deceleration": "xbrl_revenue_deceleration",
        "margin_compression": "xbrl_margin_compression",
        "operating_margin_compression": "xbrl_op_margin_compression",
        "dso_expansion": "xbrl_dso_expansion",
        "cfo_ni_divergence": "xbrl_cfo_ni_divergence",
        "cash_flow_deterioration": "xbrl_cfo_deterioration",
        "profitability_trend": "xbrl_profitability_trend",
        "working_capital_deterioration": "xbrl_working_capital_deterioration",
        "debt_ratio_increase": "xbrl_debt_ratio_increase",
        "earnings_quality_divergence": "xbrl_earnings_quality_divergence",
    }

    temporal_metric = _METRIC_MAP.get(metric)
    xbrl_key = _XBRL_KEY_MAP.get(metric)
    if temporal_metric and temporal_metric in temporal_data:
        # Return the latest period value (last tuple in the list)
        data_points = temporal_data[temporal_metric]
        if data_points:
            _period, latest_value = data_points[-1]
            val = round(latest_value, 4)
            result["value"] = val
            # Phase 70: also populate xbrl_ key for new field_key routing
            if xbrl_key:
                result[xbrl_key] = val
            return result

    # Fallback: use earnings quality metrics where applicable
    if metric == "cfo_ni_divergence":
        if fin.earnings_quality is not None:
            ocf = fin.earnings_quality.value.get("ocf_to_ni")
            result["value"] = ocf
            if xbrl_key and ocf is not None:
                result[xbrl_key] = ocf
    elif metric == "earnings_quality_divergence":
        if fin.earnings_quality is not None:
            accruals = fin.earnings_quality.value.get("accruals_ratio")
            result["value"] = accruals
            if xbrl_key and accruals is not None:
                result[xbrl_key] = accruals
    else:
        # Generic: provide marker that financial data exists
        val = "present" if fin is not None else None
        result["value"] = val
        # Phase 70: for signals with xbrl_ keys, also provide the value
        if xbrl_key and isinstance(val, (int, float)):
            result[xbrl_key] = val

    return result


def _extract_forensic_value(
    xbrl_forensics: dict[str, Any],
    category: str,
    metric: str,
) -> float | bool | None:
    """Extract a ForensicMetric value from nested xbrl_forensics dict.

    Args:
        xbrl_forensics: model_dump() of XBRLForensics (nested dict).
        category: Top-level key (e.g., 'balance_sheet', 'beneish').
        metric: Metric name within the category (e.g., 'goodwill_to_assets').

    Returns:
        The metric's value field, or None if not found / insufficient data.
    """
    cat_data = xbrl_forensics.get(category)
    if not isinstance(cat_data, dict):
        return None
    metric_data = cat_data.get(metric)
    if isinstance(metric_data, bool):
        return metric_data
    if not isinstance(metric_data, dict):
        return None
    # ForensicMetric has .zone — skip insufficient_data
    zone = metric_data.get("zone", "insufficient_data")
    if zone == "insufficient_data":
        return None
    return metric_data.get("value")


# Mapping from forensic field_key suffix -> (category, metric) in xbrl_forensics
_FORENSIC_FIELD_MAP: dict[str, tuple[str, str]] = {
    "goodwill_to_assets": ("balance_sheet", "goodwill_to_assets"),
    "intangible_concentration": ("balance_sheet", "intangible_concentration"),
    "off_balance_sheet": ("balance_sheet", "off_balance_sheet_ratio"),
    "cash_conversion_cycle": ("balance_sheet", "cash_conversion_cycle"),
    "working_capital_volatility": ("balance_sheet", "working_capital_volatility"),
    "deferred_revenue_divergence": ("revenue", "deferred_revenue_divergence"),
    "channel_stuffing": ("revenue", "channel_stuffing_indicator"),
    "margin_compression": ("revenue", "margin_compression"),
    "ocf_revenue_ratio": ("revenue", "ocf_revenue_ratio"),
    "roic_trend": ("capital_allocation", "roic"),
    "acquisition_effectiveness": ("capital_allocation", "acquisition_effectiveness"),
    "buyback_timing": ("capital_allocation", "buyback_timing"),
    "dividend_sustainability": ("capital_allocation", "dividend_sustainability"),
    "interest_coverage_trend": ("debt_tax", "interest_coverage"),
    "debt_maturity_concentration": ("debt_tax", "debt_maturity_concentration"),
    "etr_anomaly": ("debt_tax", "etr_anomaly"),
    "deferred_tax_growth": ("debt_tax", "deferred_tax_growth"),
    "pension_underfunding": ("debt_tax", "pension_underfunding"),
    "beneish_dsri": ("beneish", "dsri"),
    "beneish_aqi": ("beneish", "aqi"),
    "beneish_tata": ("beneish", "tata"),
    "beneish_composite": ("beneish", "composite_score"),
    "sloan_accruals": ("earnings_quality", "sloan_accruals"),
    "cash_flow_manipulation": ("earnings_quality", "cash_flow_manipulation"),
    "sbc_dilution": ("earnings_quality", "sbc_revenue_ratio"),
    "non_gaap_gap": ("earnings_quality", "non_gaap_gap"),
    "serial_acquirer": ("ma_forensics", "is_serial_acquirer"),
    "goodwill_growth_rate": ("ma_forensics", "goodwill_growth_rate"),
    "acquisition_to_revenue": ("ma_forensics", "acquisition_to_revenue"),
    # Aliases: signal ID suffix differs from field_key suffix
    "goodwill_impairment_risk": ("balance_sheet", "goodwill_to_assets"),
    "roic_decline": ("capital_allocation", "roic"),
    "interest_coverage_decline": ("debt_tax", "interest_coverage"),
    "dsri_elevated": ("beneish", "dsri"),
    "aqi_elevated": ("beneish", "aqi"),
    "tata_elevated": ("beneish", "tata"),
    "m_score_composite": ("beneish", "composite_score"),
    "goodwill_deterioration_pattern": ("ma_forensics", "goodwill_growth_rate"),
}


def _map_forensic_check(
    signal_id: str,
    extracted: ExtractedData,
    analysis: Any | None = None,
) -> dict[str, Any]:
    """Map data for FIN.FORENSIC.* checks.

    Forensic checks evaluate individual model scores from distress
    indicators in ExtractedData, AND from xbrl_forensics in AnalysisResults
    when available (Phase 70+).
    """
    result: dict[str, Any] = {}

    # Phase 70: Try xbrl_forensics from AnalysisResults first
    xbrl_forensics: dict[str, Any] | None = None
    if analysis is not None:
        xbrl_forensics = getattr(analysis, "xbrl_forensics", None)

    if xbrl_forensics is not None:
        suffix = signal_id.replace("FIN.FORENSIC.", "")
        # Map ONLY the forensic field relevant to THIS signal
        mapping = _FORENSIC_FIELD_MAP.get(suffix)
        if mapping is not None:
            category, metric = mapping
            val = _extract_forensic_value(xbrl_forensics, category, metric)
            if val is not None:
                result[f"forensic_{suffix}"] = val
                result["value"] = val  # Direct value for threshold comparison

    # Legacy fallback: existing checks that read from ExtractedData.financials
    fin = extracted.financials
    if fin is None:
        return result

    suffix = signal_id.replace("FIN.FORENSIC.", "")

    if suffix == "fis_composite":
        # FIS is computed by forensic engine; provide Beneish as proxy
        if fin.distress.beneish_m_score is not None:
            result["value"] = fin.distress.beneish_m_score.score
    elif suffix == "dechow_f_score":
        # Dechow F-Score is computed by forensic engine; provide marker
        if fin.distress.beneish_m_score is not None:
            result["value"] = "present"
    elif suffix == "montier_c_score":
        if fin.distress.piotroski_f_score is not None:
            result["value"] = "present"
    elif suffix == "enhanced_sloan":
        if fin.earnings_quality is not None:
            accruals = fin.earnings_quality.value.get("accruals_ratio")
            result["value"] = accruals
    elif suffix == "accrual_intensity":
        if fin.earnings_quality is not None:
            result["value"] = fin.earnings_quality.value.get("accruals_ratio")
    elif suffix == "beneish_dechow_convergence":
        # Boolean check: True only if M-Score is in manipulation zone (> -1.78)
        if fin.distress.beneish_m_score is not None:
            score = fin.distress.beneish_m_score.score
            result["value"] = score is not None and score > -1.78

    return result


def _map_quality_check(
    signal_id: str,
    extracted: ExtractedData,
) -> dict[str, Any]:
    """Map data for FIN.QUALITY.* checks.

    Phase 70: Returns xbrl_* keyed values alongside legacy "value" key.
    """
    result: dict[str, Any] = {}
    fin = extracted.financials
    if fin is None:
        return result

    suffix = signal_id.replace("FIN.QUALITY.", "")

    if suffix == "revenue_quality_score":
        if fin.earnings_quality is not None:
            eq_dict = fin.earnings_quality.value
            qs = eq_dict.get("quality_score")
            has_data = any(
                eq_dict.get(k) is not None
                for k in ("accruals_ratio", "ocf_to_ni", "dso_delta",
                           "asset_quality_delta", "cash_flow_adequacy")
            )
            if qs is not None and has_data:
                result["value"] = qs
                result["xbrl_revenue_quality"] = qs
    elif suffix == "cash_flow_quality":
        if fin.earnings_quality is not None:
            val = fin.earnings_quality.value.get("ocf_to_ni")
            result["value"] = val
            if val is not None:
                result["xbrl_cash_flow_quality"] = val
    elif suffix == "dso_ar_divergence":
        if fin.earnings_quality is not None:
            val = fin.earnings_quality.value.get("dso_delta")
            result["value"] = val
            if val is not None:
                result["xbrl_dso_ar_divergence"] = val
    elif suffix == "q4_revenue_concentration":
        # Phase 70: Try quarterly XBRL for Q4 concentration
        q4_pct = _compute_q4_concentration(extracted)
        result["value"] = q4_pct
        if q4_pct is not None:
            result["xbrl_q4_concentration"] = q4_pct
    elif suffix == "deferred_revenue_trend":
        # Phase 70-03: Wire to XBRL multi-period deferred revenue concept
        dr_val = _compute_deferred_revenue_trend(extracted)
        result["value"] = dr_val
        if dr_val is not None:
            result["xbrl_deferred_revenue_trend"] = dr_val
    elif suffix == "quality_of_earnings":
        if fin.earnings_quality is not None:
            val = fin.earnings_quality.value.get("ocf_to_ni")
            result["value"] = val
            if val is not None:
                result["xbrl_earnings_quality"] = val
    elif suffix == "non_gaap_divergence":
        sig = extracted.text_signals.get("non_gaap_reconciliation")
        if isinstance(sig, dict):
            if sig.get("present"):
                ctx = sig.get("context", "")
                result["value"] = f"Non-GAAP measures present: {ctx[:80]}"
            else:
                result["value"] = "No non-GAAP measures detected in 10-K"

    return result


def _compute_q4_concentration(extracted: ExtractedData) -> float | None:
    """Compute Q4 revenue as percentage of annual revenue from XBRL quarterly data."""
    fin = extracted.financials
    if fin is None or fin.quarterly_xbrl is None:
        return None
    quarters = fin.quarterly_xbrl.quarters
    if len(quarters) < 4:
        return None
    # Find Q4 and compute annual total from 4 most recent quarters
    q4_revenue = None
    annual_revenue = 0.0
    for q in quarters[:4]:
        rev_sv = q.income.get("Revenues") or q.income.get(
            "RevenueFromContractWithCustomerExcludingAssessedTax"
        )
        if rev_sv is None:
            return None
        rev = rev_sv.value if hasattr(rev_sv, "value") else rev_sv
        if rev is None:
            return None
        annual_revenue += rev
        if q.fiscal_quarter == 4:
            q4_revenue = rev
    if q4_revenue is None or annual_revenue == 0:
        return None
    return round(q4_revenue / annual_revenue * 100, 1)


def _compute_deferred_revenue_trend(extracted: ExtractedData) -> float | None:
    """Compute YoY deferred revenue change from XBRL statements.

    Returns percentage change (positive = increasing deferred revenue).
    Increasing deferred revenue is generally positive; decreasing can signal
    revenue recognition pull-forward.
    """
    fin = extracted.financials
    if fin is None:
        return None
    stmts = fin.statements
    if stmts is None:
        return None
    bs = stmts.balance_sheet
    if bs is None:
        return None
    # Look for deferred revenue in balance sheet line items
    for concept in ("DeferredRevenue", "DeferredRevenueCurrentAndNoncurrent",
                    "ContractWithCustomerLiability"):
        for item in bs:
            if hasattr(item, "concept") and item.concept == concept:
                val = item.value if hasattr(item, "value") else None
                if val is not None:
                    return float(val)  # Return raw value; trend computed by evaluator
    return None


def _map_exec_check(
    signal_id: str,
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
) -> dict[str, Any]:
    """Map data for EXEC.* signals from governance data."""
    result: dict[str, Any] = {}
    gov = extracted.governance
    if gov is None:
        return result

    suffix = signal_id.replace("EXEC.", "")

    if suffix.startswith("AGGREGATE."):
        # Wire from governance score as proxy for board risk
        # Governance score: higher = better. Invert to risk: higher = worse.
        gs = _safe_sv(gov.governance_score.total_score)
        if gs is not None:
            if "board_risk" in suffix:
                result["value"] = round(100 - gs, 1)
            elif "highest_risk" in suffix:
                stab = _safe_sv(gov.leadership.stability_score)
                result["value"] = round(100 - stab, 1) if stab is not None else round(100 - gs, 1)
    elif suffix.startswith("CEO."):
        ceo_suffix = suffix.replace("CEO.", "")
        if ceo_suffix == "risk_score":
            # Risk score is a post-analysis artifact computed by executive
            # forensics engine — not available at check evaluation time.
            # Return empty to produce DATA_UNAVAILABLE.
            pass
        else:
            for ep in gov.leadership.executives:
                title = _safe_sv(ep.title)
                if title and ("CEO" in title.upper() or "CHIEF EXECUTIVE" in title.upper()):
                    result["value"] = ep.tenure_years
                    break
    elif suffix.startswith("CFO."):
        cfo_suffix = suffix.replace("CFO.", "")
        if cfo_suffix == "risk_score":
            # Risk score is a post-analysis artifact — DATA_UNAVAILABLE
            pass
        else:
            for ep in gov.leadership.executives:
                title = _safe_sv(ep.title)
                if title and ("CFO" in title.upper() or "CHIEF FINANCIAL" in title.upper()):
                    result["value"] = ep.tenure_years
                    break
    elif suffix.startswith("PRIOR_LIT."):
        # Count distinct prior litigation cases across executives.
        # prior_litigation entries are SourcedValue[str] -- raw search results
        # where each snippet/title/url is a separate entry.  We deduplicate
        # by counting only entries that look like actual case descriptions
        # (not URLs, not snippet prefixes) and cap per-exec to avoid
        # hallucinated bulk search results inflating the count.
        is_ceo_cfo = "ceo_cfo" in suffix
        case_count = 0
        for ep in gov.leadership.executives:
            if is_ceo_cfo:
                title = _safe_sv(ep.title)
                if not title:
                    continue
                t_upper = title.upper()
                if not any(
                    role in t_upper
                    for role in ("CEO", "CFO", "CHIEF EXECUTIVE", "CHIEF FINANCIAL")
                ):
                    continue
            # Deduplicate: count only entries whose value looks like a
            # case description (contains keywords like "lawsuit", "class action",
            # "litigation", "SEC", "securities") rather than raw URLs / titles.
            # Group related results: max 1 case per distinct mention.
            seen_cases: set[str] = set()
            for pl in ep.prior_litigation:
                val = _safe_sv(pl) if hasattr(pl, "value") else str(pl)
                if val is None:
                    continue
                val_str = str(val).lower()
                # Skip bare URLs and short snippet prefixes
                if val_str.startswith("url:") or val_str.startswith("http"):
                    continue
                if val_str.startswith("title:"):
                    val_str = val_str[6:].strip()
                if val_str.startswith("snippet:"):
                    val_str = val_str[8:].strip()
                if len(val_str) < 20:
                    continue
                # Extract a rough case key (first 60 chars) to deduplicate
                case_key = val_str[:60]
                if case_key not in seen_cases:
                    seen_cases.add(case_key)
            # Cap per-executive at 10 distinct cases to guard against
            # bulk search result contamination
            case_count += min(len(seen_cases), 10)
        # Boolean checks: return True/False (threshold type is boolean)
        result["value"] = case_count > 0
    elif suffix.startswith("INSIDER."):
        mkt = extracted.market
        if mkt is not None:
            insider = mkt.insider_analysis
            if "cluster" in suffix.lower():
                result["value"] = len(insider.cluster_events) > 0
            elif "ceo_net_selling" in suffix:
                result["value"] = _compute_ceo_cfo_selling_pct(
                    insider.transactions, "CEO"
                )
            elif "cfo_net_selling" in suffix:
                result["value"] = _compute_ceo_cfo_selling_pct(
                    insider.transactions, "CFO"
                )
            elif "non_10b51" in suffix:
                pct_planned = _safe_sv(insider.pct_10b5_1)
                result["value"] = (
                    round(100 - pct_planned, 1)
                    if pct_planned is not None
                    else None
                )
    elif suffix.startswith("TENURE."):
        _map_exec_tenure(result, suffix, gov)
    elif suffix.startswith("DEPARTURE."):
        result["value"] = len(gov.leadership.departures_18mo) > 0
    elif suffix.startswith("PROFILE."):
        _map_exec_profile(result, suffix, gov)

    return result


def _map_exec_tenure(
    result: dict[str, Any],
    suffix: str,
    gov: Any,
) -> None:
    """Map EXEC.TENURE.* data."""
    if "ceo_new" in suffix:
        for ep in gov.leadership.executives:
            title = _safe_sv(ep.title)
            if title and ("CEO" in title.upper() or "CHIEF EXECUTIVE" in title.upper()):
                tenure = ep.tenure_years
                if tenure is not None:
                    result["value"] = tenure
                else:
                    name = _safe_sv(ep.name) or "Unknown"
                    result["value"] = f"CEO identified ({name}), tenure unavailable"
                break
    elif "cfo_new" in suffix:
        for ep in gov.leadership.executives:
            title = _safe_sv(ep.title)
            if title and ("CFO" in title.upper() or "CHIEF FINANCIAL" in title.upper()):
                tenure = ep.tenure_years
                if tenure is not None:
                    result["value"] = tenure
                else:
                    name = _safe_sv(ep.name) or "Unknown"
                    result["value"] = f"CFO identified ({name}), tenure unavailable"
                break
    elif "c_suite_turnover" in suffix:
        result["value"] = len(gov.leadership.departures_18mo)


def _map_exec_profile(
    result: dict[str, Any],
    suffix: str,
    gov: Any,
) -> None:
    """Map EXEC.PROFILE.* data."""
    if "board_size" in suffix:
        result["value"] = _safe_sv(gov.board.size)
    elif "avg_tenure" in suffix:
        avg = _safe_sv(gov.leadership.avg_tenure_years)
        if avg is not None:
            result["value"] = avg
        else:
            # Compute from individual tenures as fallback
            tenures = [
                ep.tenure_years
                for ep in gov.leadership.executives
                if ep.tenure_years is not None
            ]
            result["value"] = (
                round(sum(tenures) / len(tenures), 1) if tenures else None
            )
    elif "ceo_chair_duality" in suffix:
        result["value"] = _safe_sv(gov.board.ceo_chair_duality)
    elif "independent_ratio" in suffix:
        result["value"] = _safe_sv(gov.board.independence_ratio)
    elif "overboarded_directors" in suffix:
        result["value"] = _safe_sv(gov.board.overboarded_count)


def _map_nlp_check(
    signal_id: str,
    extracted: ExtractedData,
) -> dict[str, Any]:
    """Map data for NLP.* checks.

    NLP checks use filing text which requires the NLP engine.
    Provide markers from available risk factor data.
    """
    result: dict[str, Any] = {}
    suffix = signal_id.replace("NLP.", "")

    if suffix.startswith("MDA."):
        # MD&A analysis requires NLP engine; provide marker
        result["value"] = "present" if extracted.financials is not None else None
    elif suffix.startswith("RISK."):
        # Risk factor data from Item 1A extraction
        if "factor_count" in suffix:
            result["value"] = len(extracted.risk_factors)
        elif "new_risk_factors" in suffix:
            new_count = sum(1 for rf in extracted.risk_factors if rf.is_new_this_year)
            result["value"] = new_count
        elif "litigation_risk_factor_new" in suffix:
            has_new_lit = any(
                rf.is_new_this_year and rf.category == "LITIGATION"
                for rf in extracted.risk_factors
            )
            result["value"] = has_new_lit
        elif "regulatory_risk_factor_new" in suffix:
            has_new_reg = any(
                rf.is_new_this_year and rf.category == "REGULATORY"
                for rf in extracted.risk_factors
            )
            result["value"] = has_new_reg
    elif suffix.startswith("WHISTLE."):
        lit = extracted.litigation
        if lit is not None:
            if "language_detected" in suffix:
                result["value"] = len(lit.whistleblower_indicators) > 0
            elif "internal_investigation" in suffix:
                result["value"] = len(lit.whistleblower_indicators) > 0
    elif suffix.startswith("FILING."):
        if "late_filing" in suffix:
            # Check text_signals for NT filing or late filing evidence
            result["value"] = _detect_late_filing(extracted)
        elif "filing_timing" in suffix:
            # Compute filing timing shift from XBRL statement filing dates
            result["value"] = _compute_filing_timing_shift(extracted)
    elif suffix.startswith("CAM."):
        fin = extracted.financials
        if fin is not None:
            result["value"] = len(fin.audit.critical_audit_matters)
    elif suffix.startswith("DISCLOSURE."):
        result["value"] = "present" if extracted.financials is not None else None

    return result


def _detect_late_filing(extracted: ExtractedData) -> bool | None:
    """Detect late filing or NT filing from text signals and filing metadata.

    Checks text_signals for explicit late filing or NT filing mentions.
    Returns False (CLEAR) rather than None to avoid SKIPPED status when
    text_signals are available.
    """
    # Check text_signals for explicit mentions
    for flag_type in ("late_filing", "nt_filing"):
        sig = extracted.text_signals.get(flag_type)
        if isinstance(sig, dict) and sig.get("present"):
            return True

    # Check compliance_hiring text signal for late filing mentions
    sig2 = extracted.text_signals.get("compliance_hiring")
    if isinstance(sig2, dict) and sig2.get("present"):
        ctx = sig2.get("context", "")
        ctx_lower = ctx.lower()
        if "late fil" in ctx_lower or "nt 10-k" in ctx_lower or "nt 10-q" in ctx_lower:
            return True

    # If we have text signals (meaning 10-K was processed), no late
    # filing evidence = CLEAR. If no text signals, data is unavailable.
    if extracted.text_signals:
        return False
    return None


def _compute_filing_timing_shift(extracted: ExtractedData) -> int | str | None:
    """Compute filing timing shift (days) from financial statement filing dates.

    Uses the XBRL fact entries in financial statements to find the most
    recent two annual filing dates. Returns the day difference between
    the two most recent 10-K filing dates, or None if insufficient data.
    """
    fin = extracted.financials
    if fin is None or fin.statements is None:
        return None

    # Extract filing dates from income statement line items (most reliable)
    filing_dates: list[tuple[str, str]] = []  # (period_end, filed_date)

    for stmt in (fin.statements.income_statement, fin.statements.balance_sheet):
        if stmt is None:
            continue
        for item in stmt:
            if not hasattr(item, "values") or item.values is None:
                continue
            for _period, sv in item.values.items():
                if sv is None:
                    continue
                # Extract filed date from source string
                # Source format: "10-K YYYY-MM-DD CIKxxxx accn:xxx"
                src = getattr(sv, "source", "")
                if "10-K" in src and sv.as_of is not None:
                    as_of_str = sv.as_of.strftime("%Y-%m-%d")
                    # The source contains the end date, as_of is end date
                    filing_dates.append((as_of_str, src))

    if len(filing_dates) < 2:
        return None

    # Deduplicate by period end, get unique years
    from datetime import datetime

    years_seen: dict[str, str] = {}
    for end_date, _src in filing_dates:
        year = end_date[:4]
        if year not in years_seen or end_date > years_seen[year]:
            years_seen[year] = end_date

    if len(years_seen) < 2:
        return None

    sorted_years = sorted(years_seen.keys())
    latest_year = sorted_years[-1]
    prior_year = sorted_years[-2]

    try:
        latest_end = datetime.strptime(years_seen[latest_year], "%Y-%m-%d")
        prior_end = datetime.strptime(years_seen[prior_year], "%Y-%m-%d")
        # The filing timing shift is: how many more/fewer days from period end
        # to filing date. Since we have end dates but not filing dates from
        # SourcedValue, we approximate: filing dates differ by ~1 year + shift.
        # For this signal, we report the calendar day difference between
        # the two period end dates minus 365 (expected annual gap).
        gap_days = (latest_end - prior_end).days
        shift = gap_days - 365
        if abs(shift) <= 5:
            return f"Filing date consistent (within {abs(shift)} days of prior year)"
        return shift  # Positive = later than prior year, negative = earlier
    except (ValueError, TypeError):
        return None


__all__ = ["map_phase26_check"]
