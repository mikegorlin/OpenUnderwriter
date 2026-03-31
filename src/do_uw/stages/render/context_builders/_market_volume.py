"""Volume anomaly context builder for market section.

Detects trading days with volume >2x average and cross-references
with 8-K filings and news articles within proximity windows.

Phase 133-02: STOCK-07/08 requirements.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float


def build_volume_anomalies(state: AnalysisState) -> dict[str, Any]:
    """Build volume anomaly table with 8-K/news cross-reference.

    Reads volume spike events from extracted market data, cross-references
    with 8-K filings (within +/- 2 business days) and news articles
    (within +/- 1 day).

    Returns:
        Dict with "volume_anomalies" key containing template-ready rows,
        or empty dict if no spikes detected.
    """
    if not state.extracted or not state.extracted.market:
        return {}

    stock = state.extracted.market.stock
    spikes = getattr(stock, "volume_spike_events", None) or []
    if not spikes:
        return {}

    # Collect 8-K events for cross-reference
    eight_k_dates: dict[str, str] = {}
    ek = state.extracted.market.eight_k_items
    if ek and ek.filings:
        for f in ek.filings:
            if isinstance(f, dict):
                fd = f.get("filing_date", "") or f.get("date", "")
                items = f.get("items", []) or f.get("items_covered", [])
            else:
                fd = str(f.filing_date) if hasattr(f, "filing_date") else ""
                items = f.items if hasattr(f, "items") else []
            if fd:
                desc = ", ".join(str(i) for i in items[:3]) if items else "8-K"
                eight_k_dates[fd[:10]] = desc

    # Collect news articles for cross-reference
    news_dates: dict[str, str] = {}
    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        news_list = md.get("news", []) if isinstance(md, dict) else []
        for item in news_list[:30]:
            if not isinstance(item, dict):
                continue
            content = item.get("content", {})
            if not isinstance(content, dict):
                continue
            title = content.get("title", "")
            pub = content.get("pubDate", "")
            if pub and title:
                news_dates[str(pub)[:10]] = title[:100]

    rows: list[dict[str, Any]] = []
    for spike in spikes:
        if isinstance(spike, dict):
            spike_date = str(spike.get("date", ""))[:10]
            volume = safe_float(spike.get("volume"), None)
            avg_volume = safe_float(spike.get("avg_volume"), None)
            multiple = safe_float(spike.get("volume_multiple"), None)
            price_change = safe_float(spike.get("price_change_pct"), None)
        else:
            spike_date = str(getattr(spike, "date", ""))[:10]
            volume = safe_float(getattr(spike, "volume", None), None)
            avg_volume = safe_float(getattr(spike, "avg_volume", None), None)
            multiple = safe_float(getattr(spike, "volume_multiple", None), None)
            price_change = safe_float(getattr(spike, "price_change_pct", None), None)

        if not spike_date or volume is None:
            continue

        # Cross-reference: find 8-K within +/- 2 business days
        catalyst = "No known catalyst"
        event_type = "Unknown"
        try:
            sd = date.fromisoformat(spike_date)
            for offset in range(-2, 3):
                check = (sd + timedelta(days=offset)).isoformat()
                if check in eight_k_dates:
                    catalyst = f"8-K: {eight_k_dates[check]}"
                    event_type = "8-K"
                    break
            if event_type == "Unknown":
                for offset in range(-1, 2):
                    check = (sd + timedelta(days=offset)).isoformat()
                    if check in news_dates:
                        catalyst = news_dates[check]
                        event_type = "News"
                        break
        except (ValueError, TypeError):
            pass

        # Severity classification
        severity = "low"
        if multiple is not None and price_change is not None:
            if multiple > 3.0 and price_change < -3.0:
                severity = "high"
            elif multiple > 2.5 or abs(price_change) > 3.0:
                severity = "medium"

        rows.append({
            "date": spike_date,
            "volume": f"{volume:,.0f}" if volume is not None else "N/A",
            "multiple": f"{multiple:.1f}x" if multiple is not None else "N/A",
            "price_change_pct": f"{price_change:+.1f}%" if price_change is not None else "N/A",
            "catalyst": catalyst,
            "event_type": event_type,
            "severity": severity,
        })

    if not rows:
        return {}

    # Sort by date descending
    rows.sort(key=lambda r: r["date"], reverse=True)

    return {"volume_anomalies": rows[:15]}
