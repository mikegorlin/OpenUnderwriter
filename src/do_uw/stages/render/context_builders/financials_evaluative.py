"""Signal-backed evaluative content for financial context builders.

Extracts distress indicators, earnings quality, leverage, tax risk, and
liquidity assessments from brain signal results with graceful fallback
to direct state reads when signals are unavailable.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.context_builders._distress_do_context import (
    build_altman_trajectory,
    build_piotroski_components,
)
from do_uw.stages.render.context_builders._signal_consumer import (
    signal_to_display_level,
)
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.formatters import (
    format_currency, format_percentage, humanize_check_evidence,
)


def _extract_distress_signals(
    signal_results: dict[str, Any] | None,
    fin: Any,
    sic_code: str | None = None,
) -> dict[str, Any]:
    """Extract distress indicator zones with D&O interpretation context."""
    result: dict[str, Any] = {}

    # Financial sector caveat: Altman Z, DSCR, supply chain are inapplicable to banks
    is_financial = bool(sic_code and sic_code[:2] in ("60", "61", "62", "63", "64", "65", "66", "67"))
    result["is_financial_sector"] = is_financial
    if is_financial:
        result["sector_caveat"] = (
            "Note: Altman Z-Score, Ohlson O-Score, and Debt Service Coverage Ratio "
            "are calibrated for industrial companies. Financial institutions structurally "
            "carry high leverage and deposit-funded debt that produces misleading scores "
            "under these models. Use CET1, Tier 1 Capital, and Loan Loss Reserves instead."
        )
    z = fin.distress.altman_z_score
    o = fin.distress.ohlson_o_score
    b = fin.distress.beneish_m_score
    p = fin.distress.piotroski_f_score

    # --- Altman Z-Score ---
    if z and z.is_partial:
        result["z_score"] = f"{z.score:.2f}*" if z.score is not None else "N/A"
        result["z_zone"] = f"partial (missing: {', '.join(z.missing_inputs)})"
    else:
        result["z_score"] = f"{z.score:.2f}" if z and z.score is not None else "N/A"
        result["z_zone"] = z.zone if z else "N/A"
    z_signal = safe_get_result(signal_results, "FIN.ACCT.quality_indicators")
    z_dc = z_signal.do_context if z_signal and z_signal.do_context else ""
    # Fallback: generate D&O context from actual zone when signal result unavailable
    if not z_dc and z and z.score is not None and z.zone:
        zone_lower = str(z.zone).lower()
        s = f"{z.score:.2f}"
        if zone_lower in ("distress",):
            z_dc = (f"Altman Z-Score of {s} is in the distress zone (below 1.81) — historically associated "
                    "with 2-3x higher D&O claim frequency and increased exposure to insolvency-related claims.")
        elif zone_lower in ("grey", "gray"):
            z_dc = (f"Altman Z-Score of {s} is in the grey zone (1.81-2.99) — moderate financial stress "
                    "that could amplify D&O claim severity if stock price declines coincide with negative disclosures.")
        else:
            z_dc = (f"Altman Z-Score of {s} is in the safe zone (above 2.99) — low bankruptcy probability, "
                    "a protective factor for D&O risk.")
    result["z_do_context"] = z_dc
    result["z_trajectory"] = build_altman_trajectory(z)

    # --- Beneish M-Score --- try m_score_composite first (active signal)
    m_result = safe_get_result(signal_results, "FIN.FORENSIC.m_score_composite")
    _m_has_value = m_result and m_result.value is not None and getattr(m_result, "status", "") != "SKIPPED"
    if _m_has_value:
        try:
            _bv = float(m_result.value) if m_result.value is not None else None
        except (ValueError, TypeError):
            _bv = None
        result["beneish_score"] = f"{_bv:.3f}" if _bv is not None else (
            str(m_result.value) if m_result.value is not None else "N/A")
        result["beneish_zone"] = (b.zone if b and b.zone else None) or m_result.evidence or "N/A"
        result["beneish_level"] = signal_to_display_level(m_result.status, m_result.threshold_level)
    else:
        result["beneish_score"] = f"{b.score:.2f}" if b and b.score is not None else "N/A"
        result["beneish_zone"] = b.zone if b else "N/A"
    beneish_sig = m_result if m_result and m_result.do_context else safe_get_result(signal_results, "FIN.ACCT.earnings_manipulation")
    result["beneish_do_context"] = beneish_sig.do_context if beneish_sig and beneish_sig.do_context else ""

    # --- Ohlson O-Score ---
    result["o_score"] = f"{o.score:.2f}" if o and o.score is not None else "N/A"
    result["o_zone"] = o.zone if o else "N/A"
    o_signal = safe_get_result(signal_results, "FIN.ACCT.ohlson_o_score")
    result["o_do_context"] = o_signal.do_context if o_signal and o_signal.do_context else ""

    # --- Piotroski F-Score ---
    result["piotroski_score"] = f"{p.score:.0f}" if p and p.score is not None else "N/A"
    result["piotroski_zone"] = p.zone if p else "N/A"
    p_signal = safe_get_result(signal_results, "FIN.FORENSIC.dechow_f_score")
    result["piotroski_do_context"] = p_signal.do_context if p_signal and p_signal.do_context else ""
    result["piotroski_components"] = build_piotroski_components(p)

    # Enrich from FIN.FORENSIC prefix signals for additional distress context
    forensic_signals = safe_get_signals_by_prefix(signal_results, "FIN.FORENSIC.")
    triggered_forensics = [
        s for s in forensic_signals if s.status == "TRIGGERED"
    ]
    if triggered_forensics:
        result["forensic_alert_count"] = len(triggered_forensics)

    # D&O context for individual forensic indicators
    _forensic_do_context_map = {
        "dso_do_context": "FIN.FORENSIC.dsri_elevated",
        "sloan_do_context": "FIN.FORENSIC.sloan_accruals",
        "accrual_do_context": "FIN.FORENSIC.accrual_intensity",
        "channel_stuffing_do_context": "FIN.FORENSIC.channel_stuffing",
        "cash_flow_manip_do_context": "FIN.FORENSIC.cash_flow_manipulation",
        "non_gaap_do_context": "FIN.FORENSIC.non_gaap_gap",
        "goodwill_do_context": "FIN.FORENSIC.goodwill_impairment_risk",
        "fis_do_context": "FIN.FORENSIC.fis_composite",
        "montier_do_context": "FIN.FORENSIC.montier_c_score",
        "enhanced_sloan_do_context": "FIN.FORENSIC.enhanced_sloan",
        "margin_compression_do_context": "FIN.FORENSIC.margin_compression",
        "sbc_dilution_do_context": "FIN.FORENSIC.sbc_dilution",
    }
    for ctx_key, sig_id in _forensic_do_context_map.items():
        sig = safe_get_result(signal_results, sig_id)
        result[ctx_key] = sig.do_context if sig and sig.do_context else ""

    return result


def _extract_earnings_quality_signals(
    signal_results: dict[str, Any] | None,
    fin: Any,
) -> dict[str, Any]:
    """Extract earnings quality assessments from FIN.QUALITY signals."""
    result: dict[str, Any] = {}

    quality_result = safe_get_result(
        signal_results, "FIN.QUALITY.quality_of_earnings",
    )
    revenue_quality = safe_get_result(
        signal_results, "FIN.QUALITY.revenue_quality_score",
    )

    eq_parts: list[str] = []
    eq_detail: dict[str, str] = {}

    if quality_result and quality_result.value is not None:
        try:
            _qs = f"{float(quality_result.value):.2f}"
        except (ValueError, TypeError):
            _qs = str(quality_result.value)
        eq_parts.append(f"Quality: {_qs}")
        eq_detail["quality_score"] = _qs
        result["earnings_quality_level"] = signal_to_display_level(
            quality_result.status, quality_result.threshold_level,
        )
    if revenue_quality and revenue_quality.value is not None:
        eq_detail["revenue_quality"] = str(revenue_quality.value)

    cash_flow_q = safe_get_result(
        signal_results, "FIN.QUALITY.cash_flow_quality",
    )
    if cash_flow_q and cash_flow_q.value is not None:
        eq_detail["cash_flow_quality"] = str(cash_flow_q.value)

    dso_ar = safe_get_result(
        signal_results, "FIN.QUALITY.dso_ar_divergence",
    )
    if dso_ar and dso_ar.value is not None:
        eq_detail["dso_ar_divergence"] = str(dso_ar.value)

    # Fallback to direct state if no signal data
    if not eq_parts and fin.earnings_quality is not None:
        eq = fin.earnings_quality.value
        ocf = eq.get("ocf_to_ni")
        if ocf is not None:
            eq_parts.append(f"OCF/NI: {ocf:.2f}")
            eq_detail["ocf_to_ni"] = f"{ocf:.2f}"
        acr = eq.get("accruals_ratio")
        if acr is not None:
            eq_parts.append(f"Accruals: {acr:.4f}")
            eq_detail["accruals_ratio"] = f"{acr:.4f}"
        dso = eq.get("dso_delta")
        if dso is not None:
            eq_detail["dso_delta"] = f"{dso:+.1f}%"
        cfa = eq.get("cash_flow_adequacy")
        if cfa is not None:
            eq_detail["cash_flow_adequacy"] = f"{cfa:.2f}x"
        qs = eq.get("quality_score")
        if qs is not None:
            eq_detail["quality_score"] = f"{qs:.2f}"

    result["earnings_quality"] = " | ".join(eq_parts) if eq_parts else None
    result["earnings_quality_detail"] = eq_detail if eq_detail else None

    # D&O context for earnings quality indicators
    _eq_do_context_map = {
        "earnings_quality_do_context": "FIN.QUALITY.quality_of_earnings",
        "revenue_quality_do_context": "FIN.QUALITY.revenue_quality_score",
        "cash_flow_quality_do_context": "FIN.QUALITY.cash_flow_quality",
        "dso_ar_do_context": "FIN.QUALITY.dso_ar_divergence",
        "rev_recognition_do_context": "FIN.QUALITY.revenue_recognition_risk",
    }
    for ctx_key, sig_id in _eq_do_context_map.items():
        sig = safe_get_result(signal_results, sig_id)
        result[ctx_key] = sig.do_context if sig and sig.do_context else ""

    return result


def _extract_leverage_signals(
    signal_results: dict[str, Any] | None,
    fin: Any,
) -> dict[str, Any]:
    """Extract leverage/debt assessments from FIN.DEBT signals."""
    result: dict[str, Any] = {}

    debt_structure = safe_get_result(signal_results, "FIN.DEBT.structure")
    debt_coverage = safe_get_result(signal_results, "FIN.DEBT.coverage")

    parts: list[str] = []
    if debt_structure and debt_structure.value is not None:
        parts.append(f"Structure: {debt_structure.evidence or debt_structure.value}")
        result["leverage_level"] = signal_to_display_level(
            debt_structure.status, debt_structure.threshold_level,
        )
    if debt_coverage and debt_coverage.value is not None:
        parts.append(f"Coverage: {debt_coverage.evidence or debt_coverage.value}")

    # Fallback to direct state
    if not parts and fin.leverage is not None:
        lev = fin.leverage.value
        dte = lev.get("debt_to_equity")
        if dte is not None:
            parts.append(f"D/E ratio: {dte:.2f}")
        ic = lev.get("interest_coverage")
        if ic is not None:
            parts.append(f"Interest coverage: {ic:.1f}x")

    result["debt_summary"] = " | ".join(parts) if parts else None

    # D&O context for leverage indicators
    debt_struct_sig = safe_get_result(signal_results, "FIN.DEBT.structure")
    result["debt_structure_do_context"] = debt_struct_sig.do_context if debt_struct_sig and debt_struct_sig.do_context else ""
    debt_cov_sig = safe_get_result(signal_results, "FIN.DEBT.coverage")
    result["debt_coverage_do_context"] = debt_cov_sig.do_context if debt_cov_sig and debt_cov_sig.do_context else ""

    return result


def _extract_tax_signals(
    signal_results: dict[str, Any] | None,
    fin: Any,
) -> dict[str, Any]:
    """Extract tax risk flags from FIN.FORENSIC.etr_anomaly signal."""
    result: dict[str, Any] = {}

    etr_signal = safe_get_result(signal_results, "FIN.FORENSIC.etr_anomaly")

    if etr_signal and etr_signal.value is not None:
        result["tax_etr"] = (
            format_percentage(float(etr_signal.value) * 100)
            if isinstance(etr_signal.value, (int, float))
            else str(etr_signal.value)
        )
        result["tax_level"] = signal_to_display_level(
            etr_signal.status, etr_signal.threshold_level,
        )
    elif fin.tax_indicators is not None:
        tax = fin.tax_indicators.value
        etr = tax.get("effective_tax_rate")
        if etr is not None:
            result["tax_etr"] = f"{etr * 100:.1f}%"
    else:
        result["tax_etr"] = None

    # Tax risk detail always from state (complex nested data)
    result["tax_risk"] = None
    if fin.tax_indicators is not None:
        tax = fin.tax_indicators.value
        tax_detail: dict[str, str] = {}
        haven_count = tax.get("tax_haven_subsidiary_count")
        if haven_count is not None and haven_count > 0:
            tax_detail["haven_count"] = str(haven_count)
            havens = tax.get("tax_haven_details", {})
            all_names: list[str] = []
            if isinstance(havens, dict):
                for _category, jurisdictions in havens.items():
                    if isinstance(jurisdictions, list):
                        all_names.extend(jurisdictions)
            elif isinstance(havens, list):
                all_names = [str(h) for h in havens]
            if all_names:
                tax_detail["haven_jurisdictions"] = ", ".join(all_names)
        haven_pct = tax.get("tax_haven_pct")
        if haven_pct is not None:
            tax_detail["haven_concentration"] = f"{haven_pct:.1f}%"
        tp_risk = tax.get("transfer_pricing_risk_flag")
        if tp_risk:
            tax_detail["transfer_pricing_risk"] = "Flagged"
        utb = tax.get("unrecognized_tax_benefits")
        if utb is not None:
            tax_detail["unrecognized_benefits"] = format_currency(utb, compact=True)
        deferred = tax.get("deferred_tax_net")
        if deferred is not None:
            tax_detail["deferred_tax_net"] = format_currency(deferred, compact=True)
        etr_trend = tax.get("etr_trend")
        if etr_trend:
            tax_detail["etr_trend"] = str(etr_trend)
        if tax_detail:
            result["tax_risk"] = tax_detail

    # D&O context for tax risk
    etr_do_sig = safe_get_result(signal_results, "FIN.FORENSIC.etr_anomaly")
    result["etr_do_context"] = etr_do_sig.do_context if etr_do_sig and etr_do_sig.do_context else ""

    return result


def _extract_liquidity_signals(
    signal_results: dict[str, Any] | None,
    fin: Any,
) -> dict[str, Any]:
    """Extract liquidity zone assessments from FIN.LIQ signals."""
    result: dict[str, Any] = {}

    liq_position = safe_get_result(signal_results, "FIN.LIQ.position")
    liq_trend = safe_get_result(signal_results, "FIN.LIQ.trend")
    cash_burn = safe_get_result(signal_results, "FIN.LIQ.cash_burn")

    liq_parts: list[str] = []
    if liq_position and liq_position.value is not None:
        _liq_ev = liq_position.evidence or str(liq_position.value)
        liq_parts.append(
            f"Position: {humanize_check_evidence(_liq_ev)}",
        )
        result["liquidity_level"] = signal_to_display_level(
            liq_position.status, liq_position.threshold_level,
        )
    if liq_trend and liq_trend.status == "TRIGGERED":
        liq_parts.append(f"Trend: {liq_trend.evidence or 'Deteriorating'}")
    if cash_burn and cash_burn.status == "TRIGGERED":
        liq_parts.append(f"Cash Burn: {cash_burn.evidence or 'Alert'}")

    # Fallback to direct state
    if not liq_parts and fin.liquidity is not None:
        liq = fin.liquidity.value
        cr = liq.get("current_ratio")
        if cr is not None:
            liq_parts.append(f"Current: {cr:.2f}")
        qr = liq.get("quick_ratio")
        if qr is not None:
            liq_parts.append(f"Quick: {qr:.2f}")

    result["liquidity"] = " | ".join(liq_parts) if liq_parts else None

    # D&O context for liquidity indicators
    liq_pos_sig = safe_get_result(signal_results, "FIN.LIQ.position")
    result["liquidity_do_context"] = liq_pos_sig.do_context if liq_pos_sig and liq_pos_sig.do_context else ""
    cash_burn_sig = safe_get_result(signal_results, "FIN.LIQ.cash_burn")
    result["cash_burn_do_context"] = cash_burn_sig.do_context if cash_burn_sig and cash_burn_sig.do_context else ""

    return result


__all__ = ["_extract_distress_signals", "_extract_earnings_quality_signals",
    "_extract_leverage_signals", "_extract_liquidity_signals", "_extract_tax_signals"]
