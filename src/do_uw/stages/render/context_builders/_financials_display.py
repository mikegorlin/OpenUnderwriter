"""Display-only helpers for financial context builders.

Contains quarterly update formatting, yfinance quarterly trending,
and peer matrix extraction -- pure display data with no evaluative logic.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.charts.sparklines import render_sparkline
from do_uw.stages.render.formatters import (
    format_change_indicator,
    format_currency_accounting as format_currency,
    format_percentage,
)


def _compute_sector_average(bm: Any) -> str:
    """Compute sector average display string.

    Uses sector_average_score if available, otherwise derives from
    peer quality scores. Returns "N/A" only if no data exists.
    """
    if bm.sector_average_score is not None:
        return f"{bm.sector_average_score:.0f}"
    # Derive from peer quality scores as fallback
    if bm.peer_quality_scores:
        scores = list(bm.peer_quality_scores.values())
        avg = sum(scores) / len(scores)
        return f"{avg:.0f}"
    return "\u2014"


def build_quarterly_context(fin: Any) -> list[dict[str, Any]]:
    """Build quarterly update context dicts from QuarterlyUpdate models."""
    if not fin.quarterly_updates:
        return []

    updates: list[dict[str, Any]] = []
    for qu in fin.quarterly_updates:
        rev = format_currency(qu.revenue.value, compact=True) if qu.revenue else "N/A"
        ni = format_currency(qu.net_income.value, compact=True) if qu.net_income else "N/A"
        eps = f"${qu.eps.value:.2f}" if qu.eps else "N/A"

        prior_rev = (
            format_currency(qu.prior_year_revenue, compact=True)
            if qu.prior_year_revenue is not None
            else "N/A"
        )
        prior_ni = (
            format_currency(qu.prior_year_net_income, compact=True)
            if qu.prior_year_net_income is not None
            else "N/A"
        )
        prior_eps = (
            f"${qu.prior_year_eps:.2f}"
            if qu.prior_year_eps is not None
            else "N/A"
        )

        rev_change = ""
        if qu.revenue and qu.prior_year_revenue and qu.prior_year_revenue != 0:
            rev_change = format_change_indicator(qu.revenue.value, qu.prior_year_revenue)
        ni_change = ""
        if qu.net_income and qu.prior_year_net_income and qu.prior_year_net_income != 0:
            ni_change = format_change_indicator(qu.net_income.value, qu.prior_year_net_income)

        updates.append({
            "quarter": qu.quarter,
            "period_end": qu.period_end,
            "filing_date": qu.filing_date,
            "revenue": rev,
            "net_income": ni,
            "eps": eps,
            "prior_revenue": prior_rev,
            "prior_net_income": prior_ni,
            "prior_eps": prior_eps,
            "revenue_change": rev_change,
            "net_income_change": ni_change,
            "new_legal_proceedings": qu.new_legal_proceedings,
            "legal_updates": qu.legal_proceedings_updates,
            "going_concern": qu.going_concern,
            "going_concern_detail": qu.going_concern_detail,
            "material_weaknesses": qu.material_weaknesses,
            "md_a_highlights": qu.md_a_highlights,
            "subsequent_events": qu.subsequent_events,
        })

    return updates


def build_yfinance_quarterly_context(fin: Any) -> dict[str, Any]:
    """Build 8-quarter trending table context from yfinance data."""
    quarters = getattr(fin, "yfinance_quarterly", None)
    if not quarters:
        return {"has_data": False, "periods": [], "metrics": []}
    periods = [q["period"] for q in quarters]
    metric_defs: list[tuple[str, str, str]] = [
        ("revenue", "Revenue", "currency"),
        ("gross_profit", "Gross Profit", "currency"),
        ("operating_income", "Operating Income", "currency"),
        ("net_income", "Net Income", "currency"),
        ("diluted_eps", "Diluted EPS", "eps"),
        ("gross_margin", "Gross Margin", "pct"),
        ("operating_margin", "Operating Margin", "pct"),
        ("ebitda", "EBITDA", "currency"),
        ("total_assets", "Total Assets", "currency"),
        ("total_debt", "Total Debt", "currency"),
        ("stockholders_equity", "Equity", "currency"),
        ("operating_cashflow", "Operating Cash Flow", "currency"),
        ("free_cashflow", "Free Cash Flow", "currency"),
    ]
    metrics: list[dict[str, Any]] = []
    for key, label, fmt in metric_defs:
        values: list[str] = []
        raw_vals: list[float | None] = []
        has_any = False
        for q in quarters:
            val = q.get(key)
            raw_vals.append(val)
            if val is not None:
                has_any = True
                if fmt == "currency":
                    values.append(format_currency(val, compact=True))
                elif fmt == "pct":
                    values.append(f"{val:.1f}%")
                elif fmt == "eps":
                    values.append(f"${val:.2f}")
                else:
                    values.append(f"{val:,.0f}")
            else:
                values.append("N/A")
        if has_any:
            spark = ""
            numeric_vals = [v for v in raw_vals if v is not None]
            if len(numeric_vals) >= 2:
                spark = render_sparkline(list(reversed(numeric_vals)))
            metrics.append({"label": label, "cells": values, "sparkline": spark})
    return {"has_data": bool(metrics), "periods": periods, "metrics": metrics}


def format_metric_value(value: float | None, metric_name: str) -> str:
    """Format a metric value based on its name/type."""
    if value is None:
        return "\u2014"
    name_lower = metric_name.lower()
    if any(kw in name_lower for kw in ("leverage", "ebitda", "coverage")):
        return f"{value:.1f}x"
    if any(kw in name_lower for kw in ("margin", "ratio", "pct", "return", "yield", "volatility")):
        return format_percentage(value)
    if any(kw in name_lower for kw in ("revenue", "income", "cap", "assets", "debt", "cash", "equity")):
        return format_currency(value, compact=True)
    if abs(value) >= 1000:
        return format_currency(value, compact=True)
    return f"{value:.2f}"


def extract_peer_matrix(state: AnalysisState) -> dict[str, Any] | None:
    """Extract full peer comparison matrix for template."""
    bm = state.benchmark
    if bm is None or not bm.metric_details:
        return None
    metrics: list[dict[str, Any]] = []
    for name, mb in bm.metric_details.items():
        pct = mb.percentile_rank
        if pct is not None:
            color = "green" if pct >= 75 else ("gold" if pct >= 40 else "red")
        else:
            color = "gray"
        metrics.append({
            "name": mb.metric_name,
            "key": name,
            "company_value": format_metric_value(mb.company_value, mb.metric_name),
            "percentile_rank": round(pct) if pct is not None else None,
            "peer_count": mb.peer_count,
            "baseline_value": format_metric_value(mb.baseline_value, mb.metric_name),
            "higher_is_better": mb.higher_is_better,
            "section": mb.section,
            "color": color,
        })
    peers: list[dict[str, str]] = []
    for ticker, qscore in bm.peer_quality_scores.items():
        peers.append({"ticker": ticker, "quality_score": f"{qscore:.1f}"})
    return {
        "metrics": metrics,
        "peers": peers,
        "peer_tickers": bm.peer_group_tickers,
        "peer_count": len(bm.peer_group_tickers),
        "relative_position": (bm.relative_position or "\u2014").replace("_", " ").title(),
        "sector_average": _compute_sector_average(bm),
        "peer_rankings": {k: f"{v:.0f}" for k, v in bm.peer_rankings.items()},
    }
