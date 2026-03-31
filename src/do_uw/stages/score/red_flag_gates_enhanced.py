"""Enhanced red flag gate logic (CRF-12 through CRF-17).

Critical red flag gates that use analytical engine outputs
(executive_risk, forensic_composites) and enhanced check results.

Split from red_flag_gates.py to stay under 500-line limit.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import ExtractedData


def evaluate_phase26_trigger(
    crf_id: str,
    extracted: ExtractedData,
    analysis_results: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Evaluate CRF-12 through CRF-17 gate conditions.

    Args:
        crf_id: Normalized CRF ID (e.g., "CRF-12").
        extracted: Current extracted data.
        analysis_results: Optional dict with keys from AnalysisResults
            (signal_results, executive_risk, forensic_composites, nlp_signals).

    Returns:
        (triggered: bool, evidence: list[str])
    """
    if analysis_results is None:
        analysis_results = {}

    if crf_id == "CRF-12":
        return _check_doj_enhanced(extracted, analysis_results)
    if crf_id == "CRF-13":
        return _check_altman_distress(extracted)
    if crf_id == "CRF-14":
        return _check_caremark_survived(extracted)
    if crf_id == "CRF-15":
        return _check_executive_aggregate(analysis_results)
    if crf_id == "CRF-16":
        return _check_fis_critical(analysis_results)
    if crf_id == "CRF-17":
        return _check_whistleblower(extracted, analysis_results)
    return False, []


def _check_doj_enhanced(
    extracted: ExtractedData,
    analysis_results: dict[str, Any],
) -> tuple[bool, list[str]]:
    """CRF-12: Active DOJ Criminal Investigation (enhanced).

    Only triggers for CRIMINAL DOJ proceedings. Civil antitrust,
    civil rights, or other non-criminal DOJ actions do not qualify.
    """
    lit = extracted.litigation
    if lit is not None:
        for proc in lit.regulatory_proceedings:
            proc_dict = proc.value
            agency = str(proc_dict.get("agency", "")).upper()
            desc = str(proc_dict.get("description", "")).upper()
            proc_type = str(proc_dict.get("type", "")).upper()
            is_doj = "DOJ" in agency or "DEPARTMENT OF JUSTICE" in agency
            if not is_doj:
                continue
            is_civil = any(
                term in desc or term in proc_type
                for term in ("CIVIL", "ANTITRUST", "CIVIL RIGHTS")
            )
            if is_civil:
                continue
            if "CRIMINAL" in desc or "CRIMINAL" in proc_type:
                return True, [f"DOJ criminal: {proc_type}"]

    # Check check results for explicit criminal DOJ mentions
    signal_results = analysis_results.get("signal_results", {})
    for signal_id, result in signal_results.items():
        if not isinstance(result, dict):
            continue
        if signal_id.startswith("LIT.REG."):
            evidence = str(result.get("evidence", "")).upper()
            if "CRIMINAL" in evidence and "DOJ" in evidence:
                return True, [
                    f"DOJ criminal in {signal_id}"
                ]

    return False, []


def _check_altman_distress(
    extracted: ExtractedData,
) -> tuple[bool, list[str]]:
    """CRF-13: Altman Z-Score below 1.81 (distress zone).

    NEVER triggers on partial scores (missing key inputs like
    total_liabilities or market_cap). A partial Z-Score is unreliable
    and must not drive red flag decisions.
    """
    fin = extracted.financials
    if fin is None:
        return False, []

    az = fin.distress.altman_z_score
    if az is not None and az.score is not None:
        # Reject partial scores — they produce misleading results
        if az.is_partial:
            import logging

            logging.getLogger(__name__).warning(
                "CRF-13: Altman Z-Score %.2f is PARTIAL (missing: %s) "
                "— NOT triggering red flag",
                az.score,
                ", ".join(az.missing_inputs) if az.missing_inputs else "unknown",
            )
            return False, []
        if az.score < 1.81:
            return True, [
                f"Altman Z-Score {az.score:.2f} (zone={az.zone}) "
                f"< 1.81 distress threshold"
            ]

    return False, []


def _check_caremark_survived(
    extracted: ExtractedData,
) -> tuple[bool, list[str]]:
    """CRF-14: Caremark/oversight duty claim survived dismissal."""
    lit = extracted.litigation
    if lit is None:
        return False, []

    for suit in lit.derivative_suits:
        # CaseDetail is a Pydantic model with SourcedValue fields
        # Check coverage_type, legal_theories, and case_name for Caremark indicators
        case_name_str = ""
        if suit.case_name is not None:
            case_name_str = str(suit.case_name.value).upper()

        coverage_str = ""
        if suit.coverage_type is not None:
            coverage_str = str(suit.coverage_type.value).upper()

        theory_strs = [
            str(t.value).upper() for t in suit.legal_theories
        ] if suit.legal_theories else []

        status_str = ""
        if suit.status is not None:
            status_str = str(suit.status.value).upper()

        is_caremark = (
            "CAREMARK" in case_name_str
            or "OVERSIGHT" in case_name_str
            or "CAREMARK" in coverage_str
            or "OVERSIGHT" in coverage_str
            or any("CAREMARK" in t or "OVERSIGHT" in t for t in theory_strs)
        )
        survived = (
            "SURVIVED" in status_str
            or "PAST DISMISSAL" in status_str
            or "ACTIVE" in status_str
        )
        if is_caremark and survived:
            name = suit.case_name.value if suit.case_name is not None else "unknown"
            return True, [f"Caremark claim survived: {name}"]

    return False, []


def _check_executive_aggregate(
    analysis_results: dict[str, Any],
) -> tuple[bool, list[str]]:
    """CRF-15: Executive forensics aggregate risk > 50."""
    exec_risk = analysis_results.get("executive_risk")
    if exec_risk is None or not isinstance(exec_risk, dict):
        return False, []

    weighted_score = exec_risk.get("weighted_score", 0)
    if isinstance(weighted_score, (int, float)) and weighted_score > 50:
        highest = exec_risk.get("highest_risk_individual", "unknown")
        return True, [
            f"Executive aggregate risk {weighted_score:.0f} > 50 "
            f"(highest: {highest})"
        ]

    return False, []


def _check_fis_critical(
    analysis_results: dict[str, Any],
) -> tuple[bool, list[str]]:
    """CRF-16: Financial Integrity Score in CRITICAL zone (< 20)."""
    forensics = analysis_results.get("forensic_composites")
    if forensics is None or not isinstance(forensics, dict):
        return False, []

    fis_data = forensics.get("financial_integrity_score")
    if fis_data is None or not isinstance(fis_data, dict):
        return False, []

    zone = str(fis_data.get("zone", ""))
    score = fis_data.get("overall_score", 100)

    if zone == "CRITICAL" or (isinstance(score, (int, float)) and score < 20):
        return True, [
            f"FIS zone={zone}, score={score:.0f} -- CRITICAL financial integrity"
        ]

    return False, []


def _check_whistleblower(
    extracted: ExtractedData,
    analysis_results: dict[str, Any],
) -> tuple[bool, list[str]]:
    """CRF-17: Whistleblower/qui tam disclosure detected."""
    # Check litigation data directly
    lit = extracted.litigation
    if lit is not None and lit.whistleblower_indicators:
        indicator = lit.whistleblower_indicators[0]
        itype = indicator.indicator_type
        label = itype.value if itype is not None else "unknown"
        return True, [f"Whistleblower indicator: {label}"]

    # Check NLP signals for whistleblower detection
    nlp = analysis_results.get("nlp_signals")
    if nlp is not None and isinstance(nlp, dict):
        whistle = nlp.get("whistleblower")
        if isinstance(whistle, dict) and whistle.get("detected"):
            return True, [
                f"NLP whistleblower signal: {whistle.get('evidence', 'detected')}"
            ]

    # Check signal_results for NLP.WHISTLE.language_detected
    signal_results = analysis_results.get("signal_results", {})
    whistle_result = signal_results.get("NLP.WHISTLE.language_detected")
    if isinstance(whistle_result, dict):
        status = str(whistle_result.get("status", "")).upper()
        if status == "TRIGGERED":
            return True, [
                "NLP.WHISTLE.language_detected TRIGGERED"
            ]

    return False, []


def check_spac_under_5(
    extracted: ExtractedData, company: object | None
) -> tuple[bool, list[str]]:
    """CRF-6: SPAC <18 months AND stock <$5.

    Moved from red_flag_gates.py to stay under 500-line limit.
    """
    from datetime import date

    mkt = extracted.market
    if mkt is None:
        return False, []

    spac_recent = False
    for offering in mkt.capital_markets.offerings_3yr:
        if offering.date is not None:
            otype = offering.offering_type.upper()
            if "SPAC" in otype:
                try:
                    off_date = date.fromisoformat(offering.date.value)
                    months = (date.today() - off_date).days / 30.4
                    if months < 18:
                        spac_recent = True
                except (ValueError, TypeError):
                    pass

    if not spac_recent:
        return False, []

    if mkt.stock.current_price is not None:
        price = mkt.stock.current_price.value
        if price < 5.0:
            return True, [f"SPAC <18mo, stock ${price:.2f} (< $5)"]

    return False, []


def check_short_seller_report(
    extracted: ExtractedData,
) -> tuple[bool, list[str]]:
    """CRF-7: Named in short seller report within 6 months.

    Moved from red_flag_gates.py to stay under 500-line limit.
    """
    from datetime import date

    mkt = extracted.market
    if mkt is None:
        return False, []
    for report in mkt.short_interest.short_seller_reports:
        report_dict = report.value
        report_date_str = report_dict.get("date", "")
        if report_date_str:
            try:
                rpt_date = date.fromisoformat(report_date_str)
                months = (date.today() - rpt_date).days / 30.4
                if months < 6:
                    source = report_dict.get("source", "unknown")
                    return True, [
                        f"Short seller report by {source} "
                        f"({months:.0f} months ago)"
                    ]
            except (ValueError, TypeError):
                pass
    return False, []


def check_catastrophic_decline(
    extracted: ExtractedData,
) -> tuple[bool, list[str]]:
    """CRF-8: Stock decline >60% from 52-week high.

    Moved from red_flag_gates.py to stay under 500-line limit.
    """
    mkt = extracted.market
    if mkt is None:
        return False, []
    if mkt.stock.decline_from_high_pct is not None:
        decline = abs(mkt.stock.decline_from_high_pct.value)
        if decline > 60:
            return True, [f"Stock decline {decline:.1f}% from 52-week high"]
    return False, []


def check_recent_drop(
    extracted: ExtractedData,
    days: int,
    threshold: float,
    label: str,
) -> tuple[bool, list[str]]:
    """Check for significant stock drop within a time window.

    Moved from red_flag_gates.py to stay under 500-line limit.
    """
    from datetime import date

    mkt = extracted.market
    if mkt is None:
        return False, []

    all_drops = (
        mkt.stock_drops.single_day_drops + mkt.stock_drops.multi_day_drops
    )
    for drop in all_drops:
        if drop.date is not None and drop.drop_pct is not None:
            try:
                drop_date = date.fromisoformat(drop.date.value)
                age_days = (date.today() - drop_date).days
                drop_mag = abs(drop.drop_pct.value)
                if age_days <= days and drop_mag >= threshold:
                    return True, [
                        f"{label} drop: {drop_mag:.1f}% "
                        f"({age_days} days ago)"
                    ]
            except (ValueError, TypeError):
                pass
    return False, []


__all__ = [
    "evaluate_phase26_trigger",
    "check_spac_under_5",
    "check_short_seller_report",
    "check_catastrophic_decline",
    "check_recent_drop",
]
