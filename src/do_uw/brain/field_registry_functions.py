"""COMPUTED function implementations for the field registry.

Maps function names (from field_registry.yaml) to pure Python callables.
Each function receives pre-resolved argument values (not paths).
The declarative mapper resolves each arg path, then passes the values here.

Functions must be pure -- no side effects, no state access, no imports of
heavy modules. They transform pre-resolved data only.
"""

from __future__ import annotations

from typing import Any, Callable


def _count_items(items: Any) -> int:
    """Count items in a list. Returns 0 for None or empty."""
    if items is None:
        return 0
    if isinstance(items, (list, tuple)):
        return len(items)
    return 0


def _count_restatements(restatements: Any) -> int:
    """Count financial restatements. Same pattern as count_items."""
    return _count_items(restatements)


def _count_active_scas(scas: Any) -> int:
    """Count active, non-boilerplate securities class actions.

    Filters by:
    - status == "ACTIVE" (SourcedValue-unwrapped)
    - Not boilerplate 10-K language (case_name check)
    """
    if not scas or not isinstance(scas, (list, tuple)):
        return 0

    count = 0
    for sca in scas:
        # Unwrap status if SourcedValue
        status_raw = getattr(sca, "status", None)
        if hasattr(status_raw, "value"):
            status_raw = status_raw.value
        if str(status_raw).upper() != "ACTIVE":
            continue

        # Check for boilerplate
        case_name_raw = getattr(sca, "case_name", None)
        if hasattr(case_name_raw, "value"):
            case_name_raw = case_name_raw.value
        case_name = str(case_name_raw or "").upper()
        boilerplate_markers = [
            "NORMAL COURSE OF BUSINESS",
            "ORDINARY COURSE",
            "ROUTINE LITIGATION",
        ]
        if any(marker in case_name for marker in boilerplate_markers):
            continue

        count += 1
    return count


def _sum_contingent_liabilities(liabilities: Any) -> float:
    """Sum accrued_amount from contingent liabilities list."""
    if not liabilities or not isinstance(liabilities, (list, tuple)):
        return 0.0

    total = 0.0
    for item in liabilities:
        amount = getattr(item, "accrued_amount", None)
        if hasattr(amount, "value"):
            amount = amount.value
        if amount is not None:
            try:
                total += float(amount)
            except (ValueError, TypeError):
                pass
    return total


def _compute_board_independence_pct(independence_ratio: Any) -> float | None:
    """Convert board independence ratio to percentage.

    If ratio is <= 1.0, multiply by 100 (e.g., 0.75 -> 75.0).
    If ratio > 1.0, assume it's already a percentage.
    Returns None if input is None.
    """
    if independence_ratio is None:
        return None
    try:
        ratio = float(independence_ratio)
    except (ValueError, TypeError):
        return None
    if ratio <= 1.0:
        return round(ratio * 100, 1)
    return round(ratio, 1)


def _resolve_say_on_pay_pct(
    comp_analysis_pct: Any, compensation_pct: Any
) -> float | None:
    """Resolve say-on-pay approval percentage.

    Prefers comp_analysis value; falls back to compensation value.
    """
    if comp_analysis_pct is not None:
        try:
            return float(comp_analysis_pct)
        except (ValueError, TypeError):
            pass
    if compensation_pct is not None:
        try:
            return float(compensation_pct)
        except (ValueError, TypeError):
            pass
    return None


def _compute_customer_concentration(concentration_data: Any) -> Any:
    """Pass through or extract top customer concentration percentage.

    If input is a list of customer dicts, extract the highest revenue_pct.
    Otherwise, pass through as-is.
    """
    if concentration_data is None:
        return None
    if isinstance(concentration_data, (list, tuple)):
        if len(concentration_data) == 0:
            return None
        # Extract highest revenue percentage
        max_pct = 0.0
        for item in concentration_data:
            if isinstance(item, dict):
                pct = item.get("revenue_pct") or item.get("percentage") or 0.0
            else:
                pct = getattr(item, "revenue_pct", None) or getattr(
                    item, "percentage", None
                ) or 0.0
            try:
                max_pct = max(max_pct, float(pct))
            except (ValueError, TypeError):
                pass
        return max_pct if max_pct > 0 else None
    return concentration_data


def _compute_cash_burn_months(earnings_quality: Any) -> float | str | None:
    """Compute cash burn runway in months.

    Checks OCF sign from earnings_quality data. If OCF is positive,
    returns "Profitable (OCF positive)" string (qualitative clear).
    If OCF is negative, computes months of cash remaining.
    Returns None if data unavailable.
    """
    if earnings_quality is None:
        return None

    # earnings_quality is a dict like {"ocf_to_ni": 1.2, "accruals_ratio": 0.05}
    if isinstance(earnings_quality, dict):
        ocf_to_ni = earnings_quality.get("ocf_to_ni")
    else:
        ocf_to_ni = getattr(earnings_quality, "ocf_to_ni", None)

    if ocf_to_ni is None:
        return None

    try:
        ocf_val = float(ocf_to_ni)
    except (ValueError, TypeError):
        return None

    if ocf_val > 0:
        return "Profitable (OCF positive)"

    # For cash-burning companies, we'd need cash + burn rate.
    # Without full data, return None to indicate needs more data.
    return None


def _count_within(items: Any, window_years: Any = None) -> int:
    """Count items that fall within a time window.

    If items is a list with date-like attributes (filed_date, date, event_date),
    filters to those within window_years of today. If no dates found or no
    window specified, returns total count.
    """
    if not items or not isinstance(items, (list, tuple)):
        return 0
    if window_years is None:
        return len(items)

    from datetime import datetime, timedelta

    try:
        cutoff = datetime.now() - timedelta(days=float(window_years) * 365.25)
    except (ValueError, TypeError):
        return len(items)

    count = 0
    for item in items:
        # Try common date field names
        date_val = None
        for attr in ("filed_date", "date", "event_date", "as_of"):
            raw = getattr(item, attr, None) if not isinstance(item, dict) else item.get(attr)
            if hasattr(raw, "value"):
                raw = raw.value
            if raw is not None:
                date_val = raw
                break

        if date_val is None:
            count += 1  # No date info → include by default
            continue

        if isinstance(date_val, datetime):
            if date_val >= cutoff:
                count += 1
        elif isinstance(date_val, str):
            try:
                parsed = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                if parsed.replace(tzinfo=None) >= cutoff:
                    count += 1
            except ValueError:
                count += 1  # Unparseable → include
    return count


def _years_since(date_value: Any) -> float | None:
    """Compute years elapsed since a date value.

    Accepts datetime objects, ISO format strings, or SourcedValue-wrapped dates.
    Returns None if input is None or unparseable.
    """
    if date_value is None:
        return None

    from datetime import datetime

    if isinstance(date_value, datetime):
        delta = datetime.now() - date_value
        return round(delta.days / 365.25, 1)

    if isinstance(date_value, str):
        try:
            parsed = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            delta = datetime.now() - parsed.replace(tzinfo=None)
            return round(delta.days / 365.25, 1)
        except ValueError:
            return None

    return None


def _pct_change(current: Any, previous: Any) -> float | None:
    """Compute percentage change from previous to current value.

    Formula: ((current - previous) / abs(previous)) * 100
    Returns None if either value is None or previous is zero.
    """
    if current is None or previous is None:
        return None
    try:
        curr = float(current)
        prev = float(previous)
    except (ValueError, TypeError):
        return None
    if prev == 0:
        return None
    return round(((curr - prev) / abs(prev)) * 100, 2)


# ---------------------------------------------------------------------------
# BMOD computed functions (v6.0)
# ---------------------------------------------------------------------------


def _compute_concentration_risk_composite(
    revenue_segments: Any, customer_concentration: Any, geographic_footprint: Any,
) -> int:
    """Compute concentration risk composite score (0-3).

    Each dimension contributes 1 point if concentrated:
    - Segment: any segment > 50% of revenue
    - Customer: any customer > 10% of revenue
    - Geography: any geography > 40% of revenue
    """
    score = 0

    # Segment concentration
    if revenue_segments and isinstance(revenue_segments, (list, tuple)):
        for seg in revenue_segments:
            pct = _extract_pct_from_item(seg, ("percentage", "pct"))
            if pct is not None and pct > 50:
                score += 1
                break

    # Customer concentration
    if customer_concentration and isinstance(customer_concentration, (list, tuple)):
        for cust in customer_concentration:
            pct = _extract_pct_from_item(cust, ("revenue_pct",))
            if pct is not None and pct > 10:
                score += 1
                break

    # Geographic concentration
    if geographic_footprint and isinstance(geographic_footprint, (list, tuple)):
        for geo in geographic_footprint:
            pct = _extract_pct_from_item(geo, ("percentage", "pct"))
            if pct is not None and pct > 40:
                score += 1
                break

    return score


def _unwrap_sv(item: Any) -> Any:
    """Unwrap a SourcedValue-like object if it has a .value attribute."""
    if hasattr(item, "value") and hasattr(item, "source") and hasattr(item, "confidence"):
        return item.value
    return item


def _extract_pct_from_item(item: Any, keys: tuple[str, ...]) -> float | None:
    """Extract percentage value from a dict-like item, checking multiple keys.

    Handles both raw dicts and SourcedValue-wrapped dicts.
    """
    # Unwrap SourcedValue if needed
    inner = _unwrap_sv(item)
    if isinstance(inner, dict):
        for k in keys:
            val = inner.get(k)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
    else:
        for k in keys:
            val = getattr(inner, k, None)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
    return None


def _compute_key_person_risk_score(key_person_risk: Any) -> int | None:
    """Extract pre-computed risk_score from key person risk dict.

    Returns None if data unavailable (-> signal SKIPPED).
    """
    if key_person_risk is None:
        return None
    inner = _unwrap_sv(key_person_risk)
    if isinstance(inner, dict):
        score = inner.get("risk_score")
    else:
        score = getattr(inner, "risk_score", None)
    if score is None:
        return None
    try:
        return int(score)
    except (ValueError, TypeError):
        return None


def _compute_segment_lifecycle_risk(segment_lifecycle: Any) -> float | None:
    """Compute percentage of revenue from DECLINING segments.

    Returns None if no lifecycle data available (-> signal SKIPPED).
    """
    if not segment_lifecycle or not isinstance(segment_lifecycle, (list, tuple)):
        return None

    total_rev = 0.0
    declining_rev = 0.0

    for raw_seg in segment_lifecycle:
        seg = _unwrap_sv(raw_seg)
        if isinstance(seg, dict):
            stage = str(seg.get("stage", "")).upper()
            rev = seg.get("revenue", 0) or 0
            growth = seg.get("growth_rate")
        else:
            stage = str(getattr(seg, "stage", "")).upper()
            rev = getattr(seg, "revenue", 0) or 0
            growth = getattr(seg, "growth_rate", None)

        try:
            rev_f = float(rev)
        except (ValueError, TypeError):
            rev_f = 0.0

        total_rev += rev_f
        try:
            growth_f = float(growth) if growth is not None else None
        except (ValueError, TypeError):
            growth_f = None
        if stage == "DECLINING" or (growth_f is not None and growth_f < -5):
            declining_rev += rev_f

    if total_rev == 0:
        return None
    return round(declining_rev / total_rev * 100, 1)


def _compute_disruption_risk_level(disruption_risk: Any) -> str | None:
    """Extract disruption risk level from the pre-computed dict.

    Returns None if data unavailable (-> signal SKIPPED).
    """
    if disruption_risk is None:
        return None
    inner = _unwrap_sv(disruption_risk)
    if isinstance(inner, dict):
        level = inner.get("level")
    else:
        level = getattr(inner, "level", None)
    if level is None:
        return None
    return str(level).upper()


def _compute_segment_margin_risk(segment_margins: Any) -> float | None:
    """Compute max absolute margin decline in basis points across segments.

    Returns None if no margin data available (-> signal SKIPPED).
    Returns 0 if all margins stable or improving.
    """
    if not segment_margins or not isinstance(segment_margins, (list, tuple)):
        return None

    max_decline = 0.0
    has_data = False

    for raw_seg in segment_margins:
        seg = _unwrap_sv(raw_seg)
        if isinstance(seg, dict):
            change_bps = seg.get("change_bps")
        else:
            change_bps = getattr(seg, "change_bps", None)

        if change_bps is not None:
            has_data = True
            try:
                decline = abs(float(change_bps)) if float(change_bps) < 0 else 0.0
                max_decline = max(max_decline, decline)
            except (ValueError, TypeError):
                pass

    if not has_data:
        return None
    return max_decline


# ---------------------------------------------------------------------------
# OPS computed functions (v6.0 Phase 99)
# ---------------------------------------------------------------------------


def _compute_ops_complexity_score(
    subsidiary_structure: Any,
    workforce_distribution: Any,
    operational_resilience: Any,
) -> int:
    """Compute composite operational complexity score (0-20 scale).

    Components:
    - Jurisdictions: 1pt per 5, max 5
    - High-reg jurisdictions: 1pt per 2, max 3
    - International workforce %: 1pt per 20%, max 3
    - Unionization > 20%: 2pts
    (Segment count, VIE, dual-class are added by signal_mappers at runtime)
    """
    score = 0

    # Subsidiary structure
    if subsidiary_structure is not None:
        inner = _unwrap_sv(subsidiary_structure)
        if isinstance(inner, dict):
            jurisdiction_count = inner.get("jurisdiction_count", 0) or 0
            high_reg_count = inner.get("high_reg_count", 0) or 0
        else:
            jurisdiction_count = getattr(inner, "jurisdiction_count", 0) or 0
            high_reg_count = getattr(inner, "high_reg_count", 0) or 0

        try:
            score += min(5, int(jurisdiction_count) // 5)
            score += min(3, int(high_reg_count) // 2)
        except (ValueError, TypeError):
            pass

    # Workforce distribution
    if workforce_distribution is not None:
        inner = _unwrap_sv(workforce_distribution)
        if isinstance(inner, dict):
            intl_pct = inner.get("international_pct", 0) or 0
            union_pct = inner.get("unionized_pct", 0) or 0
        else:
            intl_pct = getattr(inner, "international_pct", 0) or 0
            union_pct = getattr(inner, "unionized_pct", 0) or 0

        try:
            score += min(3, int(float(intl_pct)) // 20)
            if float(union_pct) > 20:
                score += 2
        except (ValueError, TypeError):
            pass

    return score


# ---------------------------------------------------------------------------
# Central dispatch dict -- maps YAML function names to callables
# ---------------------------------------------------------------------------

COMPUTED_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "count_items": _count_items,
    "count_restatements": _count_restatements,
    "count_active_scas": _count_active_scas,
    "sum_contingent_liabilities": _sum_contingent_liabilities,
    "compute_board_independence_pct": _compute_board_independence_pct,
    "resolve_say_on_pay_pct": _resolve_say_on_pay_pct,
    "compute_customer_concentration": _compute_customer_concentration,
    "compute_cash_burn_months": _compute_cash_burn_months,
    "count_within": _count_within,
    "years_since": _years_since,
    "pct_change": _pct_change,
    # BMOD (v6.0)
    "compute_concentration_risk_composite": _compute_concentration_risk_composite,
    "compute_key_person_risk_score": _compute_key_person_risk_score,
    "compute_segment_lifecycle_risk": _compute_segment_lifecycle_risk,
    "compute_disruption_risk_level": _compute_disruption_risk_level,
    "compute_segment_margin_risk": _compute_segment_margin_risk,
    # OPS (v6.0 Phase 99)
    "compute_ops_complexity_score": _compute_ops_complexity_score,
}

__all__ = ["COMPUTED_FUNCTIONS"]
