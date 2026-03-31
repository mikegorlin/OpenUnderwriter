"""Display-only helpers for market context builders.

Contains insider transaction formatting, stock drop events, earnings
guidance details, and capital markets data -- pure display data with
no evaluative logic.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from do_uw.models.market_events import StockDropEvent
from do_uw.stages.render.formatters import format_currency, format_percentage


_DO_THEORY_BY_CATEGORY: dict[str, str] = {
    "earnings_miss": "Pattern consistent with Section 10b-5 fraud-on-the-market theory",
    "guidance_cut": "Pattern consistent with Section 10b-5 fraud-on-the-market theory",
    "restatement": "Potential Section 10b-5 material misstatement claim",
    "regulatory": "Potential Section 10b-5 failure to disclose regulatory exposure",
    "management_departure": "Management instability may indicate undisclosed issues",
    "litigation": "Existing litigation may expand with additional plaintiff allegations",
    "analyst_downgrade": "Analyst revision may follow undisclosed negative developments",
    "market_wide": "Market-wide event — favorable for loss causation defense (Dura Pharmaceuticals)",
    "unknown": "Requires further investigation for loss causation assessment",
}

_TRIGGER_CATEGORY_LABELS: dict[str, str] = {
    "earnings_miss": "Earnings Miss",
    "guidance_cut": "Guidance Cut",
    "restatement": "Restatement",
    "litigation": "Litigation",
    "regulatory": "Regulatory",
    "management_departure": "Mgmt Change",
    "analyst_downgrade": "Downgrade",
    "acquisition": "M&A",
    "material_impairment": "Impairment",
    "market_wide": "Market-Wide",
    "unknown": "Unattributed",
}

# Patterns that indicate raw quote/ticker data scraped as trigger_description
_GARBAGE_TRIGGER_PATTERNS = (
    "quote price",
    "arrow down",
    "arrow up",
    "NASDAQ",
    "NYSE",
    "52 week range",
    "Volume.",
    "Close.",
    "Find the latest",
    "stock quote, history, news",
    "vital information to help you",
    "make the best investing",
    "finance.yahoo.com",
)


def _format_disclosure_badge(evt: StockDropEvent) -> str:
    """Format corrective disclosure as a badge string (e.g., '8-K +3d')."""
    if not evt.corrective_disclosure_type:
        return ""
    label = evt.corrective_disclosure_type
    lag = f"+{evt.corrective_disclosure_lag_days}d" if evt.corrective_disclosure_lag_days else ""
    return f"{label} {lag}".strip()


def _is_garbage_description(text: str) -> bool:
    """Return True if text looks like raw quote/ticker data, not a real trigger."""
    if not text:
        return False
    for pattern in _GARBAGE_TRIGGER_PATTERNS:
        if pattern in text:
            return True
    return False


def _format_trigger_label(
    raw_trigger: str, category: str, *, is_market_wide: bool = False,
) -> str:
    """Convert raw trigger_event + category into a human-readable label."""
    # Market-wide events get a clear label regardless of other data
    if is_market_wide and (not category or category in ("unknown", "")):
        return "Market-Wide Event"
    if category and category in _TRIGGER_CATEGORY_LABELS:
        return _TRIGGER_CATEGORY_LABELS[category]
    if raw_trigger and raw_trigger != "\u2014":
        return raw_trigger.replace("_", " ").title()
    if is_market_wide:
        return "Market-Wide Event"
    return "Unattributed"


def _clean_trigger_description(description: str) -> str:
    """Clean garbage trigger descriptions (raw quote data → empty string)."""
    if not description:
        return ""
    if _is_garbage_description(description):
        return ""
    return description


def build_insider_data(mkt: Any) -> dict[str, Any]:
    """Build structured insider trading data for HTML table + cluster details."""
    insider_data: dict[str, Any] = {}
    ia = mkt.insider_analysis
    if ia is not None:
        nbs = ia.net_buying_selling
        if nbs is not None:
            insider_data["net_activity"] = str(nbs.value).replace("_", " ").title()
        pct = ia.pct_10b5_1
        if pct is not None:
            insider_data["plan_coverage"] = f"{pct.value:.0f}%"
        clusters = ia.cluster_events
        if clusters:
            insider_data["cluster_events"] = f"{len(clusters)} detected"
            recent = clusters[0]
            names = ", ".join(recent.insiders[:3])
            if len(recent.insiders) > 3:
                names += f" +{len(recent.insiders) - 3} more"
            val = format_currency(recent.total_value, compact=True)
            insider_data["recent_cluster"] = (
                f"{recent.insider_count} insiders ({names}), {val} total"
            )
            insider_data["cluster_details"] = _build_cluster_details(clusters)
        else:
            insider_data["cluster_events"] = "None"
    elif mkt.insider_trading is not None:
        it = mkt.insider_trading
        nbs = it.net_buying_selling
        if nbs is not None:
            insider_data["net_activity"] = str(nbs.value).replace("_", " ").title()
        if it.cluster_events:
            insider_data["cluster_events"] = f"{len(it.cluster_events)} detected"
            insider_data["cluster_details"] = _build_cluster_details(it.cluster_events)
        else:
            insider_data["cluster_events"] = "None"

    # Ownership concentration alerts
    if ia is not None and ia.ownership_alerts:
        alerts: list[dict[str, Any]] = []
        for alert in ia.ownership_alerts[:10]:
            alerts.append({
                "name": alert.insider_name, "role": alert.role,
                "severity": alert.severity,
                "pct_sold": f"{alert.personal_pct_sold:.0f}%",
                "outstanding_pct": (
                    f"{alert.outstanding_pct:.2f}%" if alert.outstanding_pct is not None else None
                ),
                "shares_remaining": f"{alert.shares_remaining:,.0f}",
                "is_10b5_1": alert.is_10b5_1, "is_c_suite": alert.is_c_suite,
            })
        insider_data["ownership_alerts"] = alerts

    # Individual transaction detail rows
    txns_source = ia if ia is not None else (
        mkt.insider_trading if mkt.insider_trading is not None else None
    )
    if txns_source is not None and txns_source.transactions:
        sale_rows, other_rows = _build_transaction_rows(txns_source.transactions)
        insider_data["transactions"] = sale_rows  # ALL transactions — density, not removal
        insider_data["transactions_overflow"] = []
        insider_data["other_transactions"] = other_rows  # ALL — density, not removal
        insider_data["other_transactions_overflow"] = []
        insider_data["sale_count"] = len(sale_rows)
        insider_data["other_count"] = len(other_rows)

    return insider_data


def _build_cluster_details(clusters: list[Any]) -> list[dict[str, str]]:
    """Build cluster detail rows for template."""
    details: list[dict[str, str]] = []
    for ce in clusters[:8]:
        details.append({
            "period": f"{ce.start_date} to {ce.end_date}" if ce.start_date else "N/A",
            "insiders": str(ce.insider_count),
            "names": ", ".join(ce.insiders[:5]) if ce.insiders else "\u2014",
            "total_value": format_currency(ce.total_value, compact=True) if ce.total_value else "N/A",
        })
    return details


def _build_transaction_rows(
    transactions: list[Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build sale and other transaction rows."""
    sale_rows: list[dict[str, Any]] = []
    other_rows: list[dict[str, Any]] = []
    for txn in transactions:
        name = str(txn.insider_name.value) if txn.insider_name else "Unknown"
        title = str(txn.title.value) if txn.title else "N/A"
        date = str(txn.transaction_date.value) if txn.transaction_date else "N/A"
        shares = f"{txn.shares.value:,.0f}" if txn.shares else "N/A"
        value = format_currency(txn.total_value.value, compact=True) if txn.total_value else "\u2014"
        ownership = None
        if txn.shares_owned_following and txn.shares_owned_following.value:
            ownership = f"{txn.shares_owned_following.value:,.0f}"
        row = {
            "name": name, "title": title, "date": date,
            "type": txn.transaction_type or "N/A", "shares": shares,
            "value": value, "ownership_post": ownership,
            "is_10b5_1": bool(txn.is_10b5_1 and txn.is_10b5_1.value),
        }
        ttype = (txn.transaction_type or "").upper()
        if ttype in ("SELL", "S", "SALE"):
            sale_rows.append(row)
        else:
            other_rows.append(row)
    return sale_rows, other_rows


def _consolidate_overlapping_drops(
    drops_list: list[Any],
) -> list[Any]:
    """Consolidate overlapping multi-day drops into single events.

    When the pipeline detects multi-day drops using rolling windows,
    consecutive trading days from the same selloff appear as separate
    rows (e.g., Apr 3, 4, 7, 8 each as a separate 2-day or 5-day
    window). This merges overlapping drops into one event representing
    the full peak-to-trough decline.

    Strategy: sort by date, merge drops whose date ranges overlap
    (within 5 calendar days gap to bridge weekends). Keep the worst
    drop_pct, widest from_price → to_price, best recovery data.
    """
    if len(drops_list) <= 1:
        return drops_list

    # Parse dates and sort chronologically
    dated: list[tuple[date, Any]] = []
    for evt in drops_list:
        try:
            evt_date = date.fromisoformat(str(evt.date.value)[:10]) if evt.date else None
        except (ValueError, TypeError):
            evt_date = None
        if evt_date is not None:
            dated.append((evt_date, evt))
        else:
            dated.append((date.min, evt))

    dated.sort(key=lambda x: x[0])

    groups: list[list[tuple[date, Any]]] = []
    current_group: list[tuple[date, Any]] = [dated[0]]

    for i in range(1, len(dated)):
        prev_date = current_group[-1][0]
        curr_date = dated[i][0]
        # Merge if within 5 calendar days (bridges weekends)
        if (curr_date - prev_date).days <= 5:
            current_group.append(dated[i])
        else:
            groups.append(current_group)
            current_group = [dated[i]]
    groups.append(current_group)

    merged: list[Any] = []
    for group in groups:
        if len(group) == 1:
            merged.append(group[0][1])
            continue

        # Pick the event with the worst (most negative) drop_pct as the representative
        worst_evt = max(
            group,
            key=lambda x: abs(x[1].drop_pct.value) if x[1].drop_pct else 0,
        )[1]

        # Compute the date range for the consolidated event
        first_date = group[0][0]
        last_date = group[-1][0]
        period_days = (last_date - first_date).days + 1

        # Find the true peak-to-trough: highest from_price → lowest close_price
        from_prices = [
            e.from_price for _, e in group
            if e.from_price is not None
        ]
        to_prices = [
            e.close_price for _, e in group
            if e.close_price is not None
        ]
        best_from = max(from_prices) if from_prices else worst_evt.from_price
        worst_to = min(to_prices) if to_prices else worst_evt.close_price

        # Compute true peak-to-trough percentage
        if best_from and worst_to and best_from > 0:
            true_pct = (worst_to - best_from) / best_from * 100.0
        else:
            true_pct = worst_evt.drop_pct.value if worst_evt.drop_pct else 0

        # Use the best recovery data (from the event that ends latest)
        best_recovery = worst_evt.recovery_days
        for _, e in group:
            if e.recovery_days is not None:
                if best_recovery is None or e.recovery_days < best_recovery:
                    best_recovery = e.recovery_days

        # Build a consolidated pseudo-event by mutating worst_evt
        # (safe because these are only used for formatting)
        worst_evt.period_days = period_days
        worst_evt.from_price = best_from
        worst_evt.close_price = worst_to
        worst_evt.recovery_days = best_recovery
        if worst_evt.drop_pct:
            worst_evt.drop_pct.value = round(true_pct, 2)
        # Set the date to a range string for display
        if worst_evt.date:
            if first_date != last_date:
                worst_evt.date.value = f"{first_date.isoformat()} to {last_date.isoformat()}"
            else:
                worst_evt.date.value = first_date.isoformat()
        # Mark as MULTI_DAY if consolidated from multiple dates
        if len(group) > 1:
            worst_evt.drop_type = "MULTI_DAY"
        # Inherit market_wide if ANY constituent was market-wide
        if any(e.is_market_wide for _, e in group):
            worst_evt.is_market_wide = True
        if any(e.is_market_driven for _, e in group):
            worst_evt.is_market_driven = True

        merged.append(worst_evt)

    return merged


def build_drop_events(
    drops: Any, *, lookback_days: int = 365, limit: int = 5,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Build stock drop event rows for template.

    Returns:
        Tuple of (condensed_events, all_events).
        condensed_events: consolidated, de-overlapped events for main body.
        all_events: full sorted list (no date filter, no limit) for audit appendix.
    """
    all_drops = drops.single_day_drops + drops.multi_day_drops
    if not all_drops:
        return [], []

    # Consolidate overlapping multi-day drops into single events
    consolidated = _consolidate_overlapping_drops(all_drops)

    sorted_drops = sorted(
        consolidated,
        key=lambda d: (
            d.decay_weighted_severity if d.decay_weighted_severity is not None
            else abs(d.drop_pct.value) if d.drop_pct else 0
        ),
        reverse=True,
    )

    cutoff = date.today() - timedelta(days=lookback_days)

    def _format_event(evt: Any) -> dict[str, str]:
        date_str = str(evt.date.value) if evt.date else "N/A"
        pct_str = format_percentage(abs(evt.drop_pct.value)) if evt.drop_pct else "N/A"
        trigger_str = str(evt.trigger_event.value) if evt.trigger_event else "\u2014"
        sector_str = (
            format_percentage(abs(evt.sector_return_pct.value))
            if evt.sector_return_pct else "N/A"
        )
        ar_str = f"{evt.abnormal_return_pct:+.1f}%" if evt.abnormal_return_pct is not None else ""
        t_stat_str = f"{evt.abnormal_return_t_stat:.2f}" if evt.abnormal_return_t_stat is not None else ""
        sig_flag = "**" if evt.is_statistically_significant else ""
        category = evt.trigger_category or ""
        raw_description = evt.trigger_description or ""
        description = _clean_trigger_description(raw_description)
        is_mw = bool(evt.is_market_wide)
        trigger_label = _format_trigger_label(trigger_str, category, is_market_wide=is_mw)
        # Severity class for template color coding
        drop_val = abs(evt.drop_pct.value) if evt.drop_pct else 0
        if drop_val >= 15:
            severity_class = "critical"
        elif drop_val >= 10:
            severity_class = "high"
        elif drop_val >= 5:
            severity_class = "moderate"
        else:
            severity_class = "low"
        # D&O litigation theory: prefer evt.do_assessment, fall back to category mapping
        do_theory = evt.do_assessment or _DO_THEORY_BY_CATEGORY.get(
            category, _DO_THEORY_BY_CATEGORY["unknown"],
        )

        # Attribution split percentages
        attribution_split = {
            "market_pct": evt.market_pct if evt.market_pct is not None else 0.0,
            "sector_pct": evt.sector_pct if evt.sector_pct is not None else 0.0,
            "company_pct": evt.company_pct if evt.company_pct is not None else 0.0,
        }

        # Multi-day consolidated days breakdown
        is_multi_day = (evt.drop_type == "MULTI_DAY")
        consolidated_days: list[dict[str, Any]] = []
        if is_multi_day and hasattr(evt, "_constituent_events"):
            for ce in evt._constituent_events:
                ce_date = str(ce.date.value) if ce.date else "N/A"
                ce_pct = ce.drop_pct.value if ce.drop_pct else 0.0
                consolidated_days.append({"date": ce_date, "pct": ce_pct})
        if not consolidated_days:
            consolidated_days = [{"date": date_str, "pct": evt.drop_pct.value if evt.drop_pct else 0.0}]

        return {
            "date": date_str, "drop_pct": pct_str,
            "type": evt.drop_type or "SINGLE_DAY",
            "days": str(evt.period_days), "trigger": trigger_label,
            "trigger_description": description, "trigger_category": category,
            "sector": sector_str,
            "company_specific": "Yes" if evt.is_company_specific else "No",
            "recovery": f"{evt.recovery_days}d" if evt.recovery_days else "N/A",
            "abnormal_return": ar_str, "t_stat": t_stat_str, "significant": sig_flag,
            "decay_weight": f"{evt.decay_weight:.0%}" if evt.decay_weight is not None else "N/A",
            "decay_weighted_severity": f"{evt.decay_weighted_severity:.1f}" if evt.decay_weighted_severity is not None else "N/A",
            "market_pct": f"{evt.market_pct:+.1f}%" if evt.market_pct is not None else "N/A",
            "sector_pct": f"{evt.sector_pct:+.1f}%" if evt.sector_pct is not None else "N/A",
            "company_pct": f"{evt.company_pct:+.1f}%" if evt.company_pct is not None else "N/A",
            "market_driven": "Market-Driven" if evt.is_market_driven else "",
            "disclosure_badge": _format_disclosure_badge(evt),
            "from_price": f"${evt.from_price:.2f}" if evt.from_price is not None else "N/A",
            "to_price": f"${evt.close_price:.2f}" if evt.close_price is not None else "N/A",
            "volume": f"{evt.volume:,}" if evt.volume is not None else "N/A",
            "do_assessment": evt.do_assessment or "",
            "severity_class": severity_class,
            "is_market_wide": "Yes" if evt.is_market_wide else "No",
            # --- Phase 133: D&O theory and attribution ---
            "do_theory": do_theory,
            "attribution_split": attribution_split,
            "recovery_days": evt.recovery_days,
            "consolidated_days": consolidated_days,
            "is_multi_day": is_multi_day,
        }

    # All events formatted — for both main body and audit appendix
    all_events = [_format_event(evt) for evt in sorted_drops]

    # Condensed: within lookback window by severity — for main body
    recent_drops = []
    for evt in sorted_drops:
        try:
            # Handle consolidated date ranges like "2025-04-03 to 2025-04-08"
            date_val = str(evt.date.value) if evt.date else ""
            parse_date = date_val.split(" to ")[0] if " to " in date_val else date_val
            evt_date = date.fromisoformat(parse_date[:10]) if parse_date else None
        except (ValueError, TypeError):
            evt_date = None
        if evt_date is not None and evt_date >= cutoff:
            recent_drops.append(evt)
    condensed_events = [_format_event(evt) for evt in sorted_drops]

    return condensed_events, all_events


def build_earnings_guidance(eg: Any) -> dict[str, Any]:
    """Build earnings guidance context for template."""
    eg_data: dict[str, Any] = {}
    if eg.beat_rate:
        raw = eg.beat_rate.value
        eg_data["beat_rate"] = format_percentage(raw * 100 if raw <= 1.0 else raw)
    eg_data["consecutive_misses"] = str(eg.consecutive_miss_count)
    eg_data["withdrawals"] = str(eg.guidance_withdrawals)
    eg_data["philosophy"] = eg.philosophy or "N/A"
    eg_data["provides_guidance"] = "Yes" if eg.provides_forward_guidance else "No"
    eg_data["guidance_detail"] = eg.guidance_detail or "N/A"
    eg_data["guidance_frequency"] = eg.guidance_frequency or "N/A"
    if eg.guidance_history:
        eg_data["guidance_history"] = eg.guidance_history
    if eg.quarters:
        qtrs: list[dict[str, str]] = []
        for qtr in eg.quarters[:16]:
            low = qtr.consensus_eps_low
            high = qtr.consensus_eps_high
            if low and high:
                guidance_str = (
                    f"${low.value:.2f}" if abs(low.value - high.value) < 0.005
                    else f"${low.value:.2f} - ${high.value:.2f}"
                )
            elif low:
                guidance_str = f"${low.value:.2f}+"
            elif high:
                guidance_str = f"<= ${high.value:.2f}"
            else:
                guidance_str = "N/A"
            # Clamp stock_reaction to ±100% — values beyond that are EPS
            # surprise on near-zero estimates, not real stock returns.
            stock_rxn_val = qtr.stock_reaction_pct.value if qtr.stock_reaction_pct else None
            if stock_rxn_val is not None and abs(stock_rxn_val) > 100:
                stock_rxn_val = None
            qtrs.append({
                "quarter": qtr.quarter or "N/A",
                "guidance": guidance_str,
                "actual": f"${qtr.actual_eps.value:.2f}" if qtr.actual_eps else "N/A",
                "result": qtr.result or "N/A",
                "miss_mag": f"{qtr.miss_magnitude_pct.value:+.1f}%" if qtr.miss_magnitude_pct else ("—" if qtr.result and qtr.result.upper() in ("BEAT", "MEET") else "N/A"),
                "stock_reaction": f"{stock_rxn_val:+.1f}%" if stock_rxn_val is not None else "N/A",
            })
        eg_data["quarters"] = qtrs
    return eg_data
