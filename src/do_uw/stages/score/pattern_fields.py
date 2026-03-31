"""Pattern field value mapping for the pattern detection engine.

Maps pattern trigger field names (from patterns.json) to actual values
in ExtractedData and CompanyProfile models. Split from pattern_detection.py
to stay under 500-line limit.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.company import CompanyProfile
from do_uw.models.state import ExtractedData

logger = logging.getLogger(__name__)


def get_pattern_field_value(
    field_name: str,
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> Any | None:
    """Map pattern field names to actual ExtractedData paths.

    Returns None for fields that don't map to available data.
    """
    # Stock fields
    if field_name == "single_day_drop_pct":
        return _get_max_single_day_drop(extracted)
    if field_name == "decline_from_high":
        return _get_stock_sv(extracted, "decline_from_high_pct")
    if field_name == "peer_avg_drop_pct":
        return _get_peer_avg_drop(extracted)
    if field_name == "volatility_90d":
        return _get_stock_sv(extracted, "volatility_90d")
    if field_name == "stock_price":
        return _get_stock_sv(extracted, "current_price")
    if field_name == "trigger_type":
        return _get_trigger_type(extracted)
    if field_name == "decline_duration_days":
        return _get_decline_duration(extracted)
    if field_name in ("max_bounce_pct", "short_interest_doubled"):
        return None
    if field_name == "short_interest_trend":
        return _get_short_trend(extracted)

    # Peer divergence
    if field_name in (
        "company_vs_peer_30d_pct",
        "company_vs_peer_90d_pct",
        "divergence_gap_pct",
    ):
        return _get_peer_relative(extracted)
    if field_name == "gap_accelerating":
        return None

    # Short interest / market fields
    if field_name == "short_interest_pct":
        return _get_short_pct(extracted)
    if field_name == "short_interest_vs_sector_ratio":
        return _get_short_vs_sector(extracted)
    if field_name == "insider_cluster_selling":
        return _get_insider_cluster(extracted)
    if field_name == "si_rising":
        trend = _get_short_trend(extracted)
        return trend == "RISING" if trend is not None else None

    # Signal count fields (aggregated by pattern)
    if field_name in _SIGNAL_COUNT_FIELDS:
        return _count_signal_matches(field_name, extracted, company)

    # Financial fields
    if field_name == "accruals_ratio":
        return _get_earnings_quality(extracted, "accruals_ratio")
    if field_name == "beneish_m_score_zone":
        return _get_beneish_zone(extracted)
    if field_name == "dso_trend_increasing":
        return None
    if field_name == "ocf_to_ni_divergence":
        return _get_earnings_quality(extracted, "ocf_to_ni")
    if field_name == "debt_to_ebitda":
        return _get_leverage(extracted, "debt_to_ebitda")
    if field_name == "current_ratio":
        return _get_liquidity(extracted, "current_ratio")
    if field_name == "cash_runway_months":
        return None
    if field_name == "revenue_yoy":
        return _get_revenue_growth(extracted)

    # Governance fields
    if field_name == "ceo_tenure_months":
        return _get_exec_tenure(extracted, "CEO")
    if field_name == "cfo_tenure_months":
        return _get_exec_tenure(extracted, "CFO")
    if field_name == "ceo_tenure_years":
        m = _get_exec_tenure(extracted, "CEO")
        return m / 12.0 if m is not None else None
    if field_name == "cfo_tenure_years":
        m = _get_exec_tenure(extracted, "CFO")
        return m / 12.0 if m is not None else None
    if field_name == "board_independence":
        return _get_board_independence(extracted)
    if field_name == "executive_departures":
        return _get_executive_departures(extracted)
    if field_name == "say_on_pay_result":
        return _get_say_on_pay(extracted)

    # Litigation fields
    if field_name == "active_sca_count":
        return _get_active_sca_count(extracted)
    if field_name == "sec_enforcement_active":
        return _get_sec_enforcement_active(extracted)
    if field_name == "derivative_count":
        return _get_derivative_count(extracted)

    # Business fields
    if field_name == "customer_concentration":
        return _get_customer_concentration(company)
    if field_name == "supplier_concentration":
        return _get_supplier_concentration(company)
    if field_name == "business_description_mentions_ai":
        return _get_business_mentions_ai(company)

    # Forward fields
    if field_name in ("guidance_misses_8q", "misses_in_12_quarters",
                      "guidance_misses_in_12q"):
        return _get_guidance_misses(extracted)
    if field_name in ("consecutive_misses", "consecutive_guidance_misses"):
        return _get_consecutive_misses(extracted)

    # Not yet available fields
    if field_name in (
        "consecutive_years_decelerating_revenue",
        "pe_ratio_vs_sector_avg",
        "analyst_consensus",
        "provides_specific_growth_guidance",
        "material_catalyst_in_policy_period",
    ):
        return None

    logger.debug("Unmapped pattern field: %s", field_name)
    return None


# Signal count field names (patterns using aggregated counts)
_SIGNAL_COUNT_FIELDS = frozenset({
    "signals_detected_count",
    "short_attack_signals_count",
    "sustainability_triggers_count",
    "concentration_triggers_count",
    "liquidity_stress_signals_count",
    "turnover_triggers_count",
    "credibility_triggers_count",
    "proxy_advisor_triggers_count",
    "disclosure_triggers_count",
    "narrative_triggers_count",
    "death_spiral_factors_count",
})


# -----------------------------------------------------------------------
# Stock / market helpers
# -----------------------------------------------------------------------


def _get_max_single_day_drop(extracted: ExtractedData) -> float | None:
    mkt = extracted.market
    if mkt is None:
        return None
    events = mkt.stock.single_day_events
    if not events:
        return None
    max_drop = 0.0
    for event in events:
        change = event.value.get("change_pct")
        if change is not None:
            drop = abs(float(change))
            if drop > max_drop:
                max_drop = drop
    return max_drop if max_drop > 0 else None


def _get_stock_sv(extracted: ExtractedData, field: str) -> float | None:
    """Get a stock performance SourcedValue field."""
    mkt = extracted.market
    if mkt is None:
        return None
    sv = getattr(mkt.stock, field, None)
    if sv is None:
        return None
    return float(sv.value)


def _get_trigger_type(extracted: ExtractedData) -> str | None:
    mkt = extracted.market
    if mkt is None:
        return None
    events = mkt.stock.single_day_events
    if not events:
        return None
    largest_drop = 0.0
    trigger: str | None = None
    for event in events:
        change = event.value.get("change_pct")
        if change is not None:
            drop = abs(float(change))
            if drop > largest_drop:
                largest_drop = drop
                t = event.value.get("trigger")
                trigger = str(t) if t is not None else None
    return trigger


def _get_peer_avg_drop(extracted: ExtractedData) -> float | None:
    mkt = extracted.market
    if mkt is None:
        return None
    if mkt.stock.sector_relative_performance is not None:
        return abs(min(0.0, mkt.stock.sector_relative_performance.value))
    return None


def _get_decline_duration(extracted: ExtractedData) -> int | None:
    mkt = extracted.market
    if mkt is None:
        return None
    drops = mkt.stock_drops.multi_day_drops
    if not drops:
        return None
    max_duration = max(e.period_days for e in drops)
    return max_duration if max_duration > 0 else None


def _get_short_trend(extracted: ExtractedData) -> str | None:
    mkt = extracted.market
    if mkt is None:
        return None
    return mkt.short_interest.trend_6m.value if mkt.short_interest.trend_6m else None


def _get_short_pct(extracted: ExtractedData) -> float | None:
    mkt = extracted.market
    if mkt is None:
        return None
    si = mkt.short_interest
    return si.short_pct_float.value if si.short_pct_float else None


def _get_short_vs_sector(extracted: ExtractedData) -> float | None:
    mkt = extracted.market
    if mkt is None:
        return None
    return mkt.short_interest.vs_sector_ratio.value if mkt.short_interest.vs_sector_ratio else None


def _get_peer_relative(extracted: ExtractedData) -> float | None:
    mkt = extracted.market
    if mkt is None:
        return None
    srp = mkt.stock.sector_relative_performance
    return srp.value if srp is not None else None


def _get_insider_cluster(extracted: ExtractedData) -> bool | None:
    mkt = extracted.market
    if mkt is None:
        return None
    return len(mkt.insider_trading.cluster_events) > 0


# -----------------------------------------------------------------------
# Financial helpers
# -----------------------------------------------------------------------


def _get_earnings_quality(extracted: ExtractedData, field: str) -> float | None:
    fin = extracted.financials
    if fin is None or fin.earnings_quality is None:
        return None
    val = fin.earnings_quality.value.get(field)
    return float(val) if val is not None else None


def _get_beneish_zone(extracted: ExtractedData) -> str | None:
    fin = extracted.financials
    if fin is None:
        return None
    bm = fin.distress.beneish_m_score
    return bm.zone.value.upper() if bm is not None else None


def _get_leverage(extracted: ExtractedData, field: str) -> float | None:
    fin = extracted.financials
    if fin is None or fin.leverage is None:
        return None
    val = fin.leverage.value.get(field)
    return float(val) if val is not None else None


def _get_liquidity(extracted: ExtractedData, field: str) -> float | None:
    fin = extracted.financials
    if fin is None or fin.liquidity is None:
        return None
    val = fin.liquidity.value.get(field)
    return float(val) if val is not None else None


def _get_revenue_growth(extracted: ExtractedData) -> float | None:
    fin = extracted.financials
    if fin is None:
        return None
    inc = fin.statements.income_statement
    if inc is None:
        return None
    for item in inc.line_items:
        if item.label.lower() in ("total revenue", "revenue", "net revenue"):
            return item.yoy_change
    return None


# -----------------------------------------------------------------------
# Governance helpers
# -----------------------------------------------------------------------


def _get_exec_tenure(extracted: ExtractedData, role: str) -> float | None:
    """Get executive tenure in months using Phase 4 leadership profiles."""
    gov = extracted.governance
    if gov is None:
        return None
    # Use Phase 4 leadership.executives (LeadershipForensicProfile)
    for ep in gov.leadership.executives:
        if ep.title is not None:
            title = ep.title.value.upper()
            is_match = (
                (role == "CEO" and ("CEO" in title or "CHIEF EXECUTIVE" in title))
                or (role == "CFO" and ("CFO" in title or "CHIEF FINANCIAL" in title))
            )
            if is_match and ep.tenure_years is not None:
                return ep.tenure_years * 12
    return None


def _get_board_independence(extracted: ExtractedData) -> float | None:
    gov = extracted.governance
    if gov is None:
        return None
    ir = gov.board.independence_ratio
    return ir.value if ir is not None else None


def _get_executive_departures(extracted: ExtractedData) -> int:
    gov = extracted.governance
    if gov is None:
        return 0
    return len(gov.leadership.departures_18mo)


def _get_say_on_pay(extracted: ExtractedData) -> float | None:
    gov = extracted.governance
    if gov is None:
        return None
    sop = gov.compensation.say_on_pay_support_pct
    return sop.value if sop is not None else None


# -----------------------------------------------------------------------
# Litigation helpers
# -----------------------------------------------------------------------


def _get_active_sca_count(extracted: ExtractedData) -> int:
    """Count active genuine SCAs using canonical filter criteria.

    Uses the same status set and regulatory filter as sca_counter.py
    for consistency across the codebase.
    """
    from do_uw.stages.score.red_flag_gates import _is_regulatory_not_sca

    lit = extracted.litigation
    if lit is None:
        return 0
    # Same active statuses as sca_counter._ACTIVE_STATUSES
    active_statuses = {"ACTIVE", "PENDING", "N/A", ""}
    count = 0
    for sca in lit.securities_class_actions:
        if _is_regulatory_not_sca(sca):
            continue
        status_obj = getattr(sca, "status", None)
        if status_obj is None:
            count += 1  # Unknown = assume active (conservative)
            continue
        status_str = (
            status_obj.value if hasattr(status_obj, "value") else str(status_obj)
        )
        status_upper = str(status_str).upper() if status_str is not None else ""
        if status_upper in active_statuses:
            count += 1
    return count


def _get_sec_enforcement_active(extracted: ExtractedData) -> bool:
    lit = extracted.litigation
    if lit is None:
        return False
    pp = lit.sec_enforcement.pipeline_position
    if pp is not None:
        return pp.value.upper() not in ("NONE", "")
    return False


def _get_derivative_count(extracted: ExtractedData) -> int:
    lit = extracted.litigation
    if lit is None:
        return 0
    return len(lit.derivative_suits)


# -----------------------------------------------------------------------
# Business / company helpers
# -----------------------------------------------------------------------


def _get_customer_concentration(company: CompanyProfile | None) -> float | None:
    if company is None or not company.customer_concentration:
        return None
    max_pct = 0.0
    for cc in company.customer_concentration:
        pct = cc.value.get("revenue_pct")
        if pct is not None:
            val = float(pct)
            if val > max_pct:
                max_pct = val
    return max_pct if max_pct > 0 else None


def _get_supplier_concentration(company: CompanyProfile | None) -> str | None:
    if company is None or not company.supplier_concentration:
        return None
    for sc in company.supplier_concentration:
        pct = sc.value.get("dependency_pct")
        if pct is not None and float(pct) > 50:
            return "CRITICAL"
    return "NORMAL"


_AI_TERMS = [
    "artificial intelligence", "machine learning", " ai ", " ml ",
    "deep learning", "neural network", "generative ai", "large language model",
]


def _get_business_mentions_ai(company: CompanyProfile | None) -> bool | None:
    if company is None or company.business_description is None:
        return None
    desc = company.business_description.value.lower()
    return any(term in desc for term in _AI_TERMS)


# -----------------------------------------------------------------------
# Forward / guidance helpers
# -----------------------------------------------------------------------


def _get_guidance_misses(extracted: ExtractedData) -> int:
    mkt = extracted.market
    if mkt is None:
        return 0
    return sum(1 for q in mkt.earnings_guidance.quarters[:8]
               if q.result.upper() == "MISS")


def _get_consecutive_misses(extracted: ExtractedData) -> int:
    mkt = extracted.market
    if mkt is None:
        return 0
    max_consec = 0
    current = 0
    for q in mkt.earnings_guidance.quarters[:12]:
        if q.result.upper() == "MISS":
            current += 1
            if current > max_consec:
                max_consec = current
        else:
            current = 0
    return max_consec


def _count_signal_matches(
    count_field: str,
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> int:
    """Count matching signals for patterns using aggregated counts.

    Simplified -- actual signal definitions are in the pattern config
    and are evaluated individually by the trigger system.
    """
    _ = count_field, extracted, company
    return 0
