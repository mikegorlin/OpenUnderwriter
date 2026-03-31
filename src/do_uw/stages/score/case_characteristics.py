"""Case characteristic detection for settlement prediction multipliers.

Inspects AnalysisState to detect case characteristics that affect
settlement prediction multipliers (accounting fraud, insider selling,
SEC investigation, etc.).

Split from settlement_prediction.py for 500-line compliance.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


def detect_case_characteristics(
    state: AnalysisState,
) -> dict[str, bool]:
    """Inspect analysis results to detect case characteristics for multipliers.

    Each characteristic maps to a boolean; all default False if data unavailable.

    Args:
        state: Full analysis state with signal_results, extracted data, etc.

    Returns:
        Dict of characteristic name -> bool.
    """
    chars: dict[str, bool] = {
        "accounting_fraud": False,
        "restatement": False,
        "insider_selling": False,
        "institutional_lead_plaintiff": False,
        "top_tier_counsel": False,
        "sec_investigation": False,
        "class_period_over_1yr": False,
        "multiple_corrective_disclosures": False,
        "going_concern": False,
        "officer_termination": False,
    }

    # Check analysis results for CRF triggers and check results
    signal_results = _get_signal_results(state)

    # accounting_fraud: CRF-01 (restatement) triggered
    chars["accounting_fraud"] = _check_triggered(signal_results, "CRF-01")

    # restatement: CRF-01 or restatement-related checks
    chars["restatement"] = _check_triggered(signal_results, "CRF-01")

    # sec_investigation: CRF-02 or SEC enforcement checks
    chars["sec_investigation"] = _check_triggered(signal_results, "CRF-02")

    # insider_selling: Check F5 factor score or insider trading analysis
    chars["insider_selling"] = _check_insider_selling(state)

    # institutional_lead_plaintiff: Check litigation data
    chars["institutional_lead_plaintiff"] = _check_institutional_plaintiff(state)

    # top_tier_counsel: Check litigation data for tier-1 firms
    chars["top_tier_counsel"] = _check_top_tier_counsel(state)

    # class_period_over_1yr: Check if stock drops span > 1 year
    chars["class_period_over_1yr"] = _check_class_period_over_1yr(state)

    # multiple_corrective_disclosures: > 1 significant stock drop event
    chars["multiple_corrective_disclosures"] = (
        _check_multiple_corrective_disclosures(state)
    )

    # going_concern: Check financial data
    chars["going_concern"] = _check_going_concern(state)

    # officer_termination: Check governance data for recent departures
    chars["officer_termination"] = _check_officer_termination(state)

    return chars


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_signal_results(state: AnalysisState) -> dict[str, Any]:
    """Extract signal_results dict from analysis state."""
    if state.analysis is None:
        return {}
    return state.analysis.signal_results


def _check_triggered(
    signal_results: dict[str, Any], signal_id: str,
) -> bool:
    """Check if a specific check ID was triggered in results."""
    result = signal_results.get(signal_id)
    if result is None:
        return False
    if isinstance(result, dict):
        # Check for triggered/fired/status fields
        if result.get("triggered") is True:
            return True
        if result.get("fired") is True:
            return True
        status = str(result.get("status", "")).upper()
        if status in ("TRIGGERED", "FIRED", "FAILED", "FLAGGED"):
            return True
        # Check for data_status indicating evaluation
        data_status = str(result.get("data_status", "")).upper()
        if data_status == "EVALUATED" and result.get("severity", "").upper() in (
            "HIGH", "CRITICAL",
        ):
            return True
    return False


def _check_insider_selling(state: AnalysisState) -> bool:
    """Check if significant insider selling detected."""
    if state.extracted is None or state.extracted.market is None:
        return False
    market = state.extracted.market
    insider = getattr(market, "insider_trading", None)
    if insider is None:
        return False
    # Check net direction
    net = getattr(insider, "net_buying_selling", None)
    if net is not None:
        val = net.value if hasattr(net, "value") else str(net)
        if str(val).upper() == "NET_SELLING":
            return True
    # Check for cluster events
    clusters = getattr(insider, "cluster_events", None)
    if clusters and len(clusters) > 0:
        return True
    return False


def _check_institutional_plaintiff(state: AnalysisState) -> bool:
    """Check litigation data for institutional lead plaintiff."""
    if state.extracted is None or state.extracted.litigation is None:
        return False
    lit = state.extracted.litigation
    # Check active cases for institutional plaintiff indicators
    cases = getattr(lit, "active_cases", None)
    if cases is None:
        return False
    for case in cases:
        case_dict = case if isinstance(case, dict) else {}
        if isinstance(case, dict):
            plaintiff = str(case_dict.get("lead_plaintiff", "")).lower()
            if any(kw in plaintiff for kw in ["fund", "pension", "trust", "retirement"]):
                return True
    return False


def _check_top_tier_counsel(state: AnalysisState) -> bool:
    """Check litigation data for tier-1 plaintiff firms."""
    if state.extracted is None or state.extracted.litigation is None:
        return False

    # Load tier-1 firms from config
    counsel_config = load_config("lead_counsel_tiers")
    tier1_firms: list[str] = [
        name.lower() for name in counsel_config.get("tier_1", [])
    ]

    if not tier1_firms:
        return False

    lit = state.extracted.litigation
    cases = getattr(lit, "active_cases", None)
    if cases is None:
        return False

    for case in cases:
        if isinstance(case, dict):
            counsel = str(case.get("lead_counsel", "")).lower()
            for firm in tier1_firms:
                if firm in counsel:
                    return True
    return False


def _check_class_period_over_1yr(state: AnalysisState) -> bool:
    """Check if stock drops span more than 1 year."""
    if state.extracted is None or state.extracted.market is None:
        return False
    stock_drops_analysis = getattr(state.extracted.market, "stock_drops", None)
    if stock_drops_analysis is None:
        return False

    # Collect all drop dates
    all_drops = []
    single = getattr(stock_drops_analysis, "single_day_drops", [])
    multi = getattr(stock_drops_analysis, "multi_day_drops", [])
    all_drops.extend(single or [])
    all_drops.extend(multi or [])

    if len(all_drops) < 2:
        return False

    dates: list[str] = []
    for drop in all_drops:
        date_val = getattr(drop, "date", None)
        if date_val is not None:
            d = date_val.value if hasattr(date_val, "value") else str(date_val)
            if d:
                dates.append(str(d)[:10])

    if len(dates) < 2:
        return False

    dates.sort()
    try:
        from datetime import datetime as dt
        first = dt.strptime(dates[0], "%Y-%m-%d")
        last = dt.strptime(dates[-1], "%Y-%m-%d")
        return (last - first).days > 365
    except (ValueError, IndexError):
        return False


def _check_multiple_corrective_disclosures(
    state: AnalysisState,
) -> bool:
    """Check if there are multiple significant stock drop events."""
    if state.extracted is None or state.extracted.market is None:
        return False
    stock_drops_analysis = getattr(state.extracted.market, "stock_drops", None)
    if stock_drops_analysis is None:
        return False

    single = getattr(stock_drops_analysis, "single_day_drops", [])
    count = len(single) if single else 0
    return count > 1


def _check_going_concern(state: AnalysisState) -> bool:
    """Check financial data for going concern opinion."""
    if state.extracted is None or state.extracted.financials is None:
        return False
    fin = state.extracted.financials
    audit = getattr(fin, "audit", None)
    if audit is None:
        return False
    gc = getattr(audit, "going_concern", None)
    if gc is None:
        return False
    val = gc.value if hasattr(gc, "value") else gc
    return val is True


def _check_officer_termination(state: AnalysisState) -> bool:
    """Check governance data for recent executive departures."""
    if state.extracted is None or state.extracted.governance is None:
        return False
    gov = state.extracted.governance
    changes = getattr(gov, "executive_changes", None)
    if changes is None:
        return False
    if isinstance(changes, list) and len(changes) > 0:
        return True
    return False


__all__ = ["detect_case_characteristics"]
