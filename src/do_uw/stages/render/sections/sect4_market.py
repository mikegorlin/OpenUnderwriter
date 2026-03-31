"""Section 4: Market & Trading Analysis renderer.

Renders stock charts (1Y + 5Y), drop detail tables, short interest,
earnings guidance, analyst consensus. Delegates stock drops and
insider trading to sect4_market_events.py.

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from do_uw.models.density import DensityLevel
from do_uw.models.market import MarketSignals
from do_uw.models.market_events import (
    EarningsQuarterRecord,
)
from do_uw.stages.render.chart_helpers import embed_chart
from do_uw.stages.render.charts.stock_charts import (
    create_stock_performance_chart,
    create_stock_performance_chart_5y,
)
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_sourced_paragraph,
    add_styled_table,
    set_cell_shading,
)
from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
)
from do_uw.stages.render.md_narrative import market_narrative
from do_uw.stages.render.peer_context import (
    get_peer_context_line,
)
from do_uw.stages.render.sections.sect4_drop_tables import (
    get_drops_for_period,
    render_drop_detail_table,
)
from do_uw.stages.render.sections.sect4_market_events import (
    render_market_events,
)
from do_uw.stages.render.sections.sect4_market_helpers import (
    embed_chart_from_disk,
    render_stock_stats,
    sv_float,
    sv_pct,
    sv_str,
)
from do_uw.stages.render.tier_helpers import (
    add_meeting_prep_ref,
    render_objective_signal,
    render_scenario_context,
)


def _read_density_clean(context: dict[str, Any], section: str) -> bool:
    """Read pre-computed density from ANALYZE stage.

    Returns True when section density is CLEAN.
    Defaults to False (conservative -- show full detail) when density is not
    populated, which causes the render to show full detail rather than
    suppressing content. This is safer than the old default of True.
    """
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    if state.analysis is not None:
        density = state.analysis.section_densities.get(section)
        if density is not None:
            return density.level == DensityLevel.CLEAN
    return False


def render_section_4(
    doc: Any, context: dict[str, Any], ds: DesignSystem,
    chart_dir: Path | None = None,
) -> None:
    """Render Section 4: Market & Trading Analysis.

    Layout order:
    1. Section heading
    2. Market narrative (analyst-quality prose)
    3. Stock performance charts (1Y + 5Y)
    4. Short interest summary
    5. Earnings guidance track record
    6. Analyst consensus
    7. Market events (stock drops, insider trading, 8-K) via sub-module
    """
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    _render_heading(doc)
    market = _get_market(context)
    _render_narrative(doc, context, ds)
    _render_stock_charts(doc, context, ds, market, chart_dir=chart_dir)
    _render_short_interest(doc, market, context, ds)
    _render_earnings_guidance(doc, market, ds)
    _render_analyst_consensus(doc, market, ds)
    mkt_clean = _read_density_clean(context, "market")
    render_market_events(doc, context, ds, market_clean=mkt_clean)


def _get_market(context: dict[str, Any]) -> MarketSignals | None:
    """Safely extract market data from context."""
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    if state.extracted is None:
        return None
    return state.extracted.market


def _render_heading(doc: Any) -> None:
    """Add section heading."""
    doc.add_paragraph(style="DOHeading1").add_run("Section 4: Market & Trading Analysis")


def _render_narrative(doc: Any, context: dict[str, Any], ds: DesignSystem) -> None:
    """Render interpretive market narrative (OUT-03)."""
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    text = market_narrative(state)
    if text:
        add_sourced_paragraph(doc, text, "", ds)
    else:
        doc.add_paragraph(style="DOBody").add_run("Market and trading data not available.")


def _render_stock_charts(
    doc: Any,
    context: dict[str, Any],
    ds: DesignSystem,
    market: MarketSignals | None,
    chart_dir: Path | None = None,
) -> None:
    """Embed 1-year and 5-year stock performance charts with stats.

    If chart_dir is provided and contains pre-generated PNGs, embeds
    from disk. Otherwise falls back to inline chart generation.
    """
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Stock Performance")

    # TODO(phase-60): move to context_builders
    state = context["_state"]
    stock = market.stock if market else None

    # 1-Year chart: prefer pre-generated from disk (CHART-01: charts first)
    chart_1y_embedded = False
    if chart_dir is not None:
        chart_1y_embedded = embed_chart_from_disk(
            doc, chart_dir / "stock_1y.png", ds,
        )
    if not chart_1y_embedded:
        chart_1y = create_stock_performance_chart(state, period="1Y", ds=ds)
        if chart_1y is not None:
            embed_chart(doc, chart_1y, width=ds.chart_width)
            chart_1y_embedded = True
    if chart_1y_embedded:
        cap: Any = doc.add_paragraph(style="DOCaption")
        cap.add_run(
            "1-Year Performance (Indexed to 100). "
            "Red triangles mark single-day drops >= 8%. "
            "Orange bands mark multi-day declines >= 15%."
        )
    else:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("1-year stock price data not available.")

    # 5-Year chart: prefer pre-generated from disk
    chart_5y_embedded = False
    if chart_dir is not None:
        chart_5y_embedded = embed_chart_from_disk(
            doc, chart_dir / "stock_5y.png", ds,
        )
    if not chart_5y_embedded:
        chart_5y = create_stock_performance_chart_5y(state, ds=ds)
        if chart_5y is not None:
            embed_chart(doc, chart_5y, width=ds.chart_width)
            chart_5y_embedded = True
    if chart_5y_embedded:
        cap = doc.add_paragraph(style="DOCaption")
        cap.add_run("5-Year Performance (Indexed to 100)")
    else:
        body = doc.add_paragraph(style="DOBody")
        body.add_run("5-year stock price data not available.")

    # --- Drop analysis charts ---
    _embed_optional_chart(doc, chart_dir, "drop_analysis_1y.png", ds,
                          "Drop Event Analysis (12 Months)")
    _embed_optional_chart(doc, chart_dir, "drop_analysis_5y.png", ds,
                          "Drop Event Analysis (5 Years)")
    _embed_optional_chart(doc, chart_dir, "drop_scatter_1y.png", ds,
                          "Drop Events: Company vs Sector (12 Months)")

    # --- Drawdown charts ---
    _embed_optional_chart(doc, chart_dir, "drawdown_1y.png", ds,
                          "Drawdown Analysis (12 Months)")
    _embed_optional_chart(doc, chart_dir, "drawdown_5y.png", ds,
                          "Drawdown Analysis (5 Years)")

    # --- Volatility & Beta chart ---
    _embed_optional_chart(doc, chart_dir, "volatility_1y.png", ds,
                          "Volatility & Beta Analysis (12 Months)")

    # --- Relative Performance charts ---
    _embed_optional_chart(doc, chart_dir, "relative_1y.png", ds,
                          "Relative Performance (12 Months)")
    _embed_optional_chart(doc, chart_dir, "relative_5y.png", ds,
                          "Relative Performance (5 Years)")

    # Key statistics (after charts per CHART-01)
    render_stock_stats(doc, stock, context, ds)

    # Drop detail tables below charts
    if market:
        drops_1y = get_drops_for_period(market, "1Y")
        if drops_1y:
            render_drop_detail_table(doc, drops_1y, "1Y", ds)

        drops_5y = get_drops_for_period(market, "5Y")
        if drops_5y:
            render_drop_detail_table(doc, drops_5y, "5Y", ds)


def _render_short_interest(
    doc: Any, market: MarketSignals | None, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render short interest analysis with peer context and D&O context.

    For clean markets, renders a concise one-liner with peer context.
    For elevated markets, renders full detail table and D&O context.
    """
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Short Interest")

    si = market.short_interest if market else None
    if si is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Short interest data not available.")
        return

    # Peer context for short interest
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    si_ctx = get_peer_context_line("short_interest_pct", state.benchmark)

    # Concise rendering for clean market
    si_mkt_clean = _read_density_clean(context, "market")
    if si_mkt_clean and si.short_pct_float:
        si_str = format_percentage(si.short_pct_float.value)
        concise = f"Short Interest: {si_str}"
        if si_ctx:
            concise += f" ({si_ctx})"
        concise += ". No elevated short interest concerns identified."
        body = doc.add_paragraph(style="DOBody")
        body.add_run(concise)
        return

    rows: list[list[str]] = []
    si_pct_str = sv_pct(si.short_pct_float)
    if si_ctx:
        si_pct_str = f"{si_pct_str} ({si_ctx})"
    rows.append(["Short % of Float", si_pct_str])
    rows.append(["Days to Cover", sv_float(si.days_to_cover)])
    rows.append(["6-Month Trend", sv_str(si.trend_6m)])
    rows.append(["vs Sector Ratio", sv_float(si.vs_sector_ratio)])

    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # Tier 2: Objective signal for elevated short interest
    if si.short_pct_float and si.short_pct_float.value > 10.0:
        render_objective_signal(
            doc, ds,
            f"Elevated Short Interest: {si.short_pct_float.value:.1f}%",
            "HIGH",
            "Signals significant bearish sentiment; vulnerability to short seller reports",
        )
        render_scenario_context(
            doc, ds,
            "Cluster insider selling within 90 days of a stock drop "
            "correlates with securities class actions in 42% of cases.",
        )
        add_meeting_prep_ref(doc, ds, "Short Interest & Market Sentiment")

    # Short seller reports
    if si.short_seller_reports:
        render_objective_signal(
            doc, ds,
            f"Short Seller Reports: {len(si.short_seller_reports)} identified",
            "CRITICAL",
            "Short seller reports often trigger stock drops and subsequent SCAs",
        )


def _render_earnings_guidance(
    doc: Any, market: MarketSignals | None, ds: DesignSystem
) -> None:
    """Render earnings guidance track record with quarter detail."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Earnings Guidance Track Record")

    eg = market.earnings_guidance if market else None
    if eg is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Earnings guidance data not available.")
        return

    # Summary metrics
    summary_rows: list[list[str]] = []
    if eg.beat_rate:
        summary_rows.append([
            "Beat Rate",
            format_percentage(eg.beat_rate.value),
        ])
    summary_rows.append([
        "Consecutive Misses",
        str(eg.consecutive_miss_count),
    ])
    summary_rows.append([
        "Guidance Withdrawals",
        str(eg.guidance_withdrawals),
    ])
    summary_rows.append([
        "Philosophy",
        eg.philosophy or "N/A",
    ])
    add_styled_table(doc, ["Metric", "Value"], summary_rows, ds)

    # Quarter-by-quarter detail (trailing 8-16 quarters)
    if eg.quarters:
        _render_quarter_table(doc, eg.quarters, ds)

    # Tier 2/3: Persistent misses objective signal + scenario context
    if eg.consecutive_miss_count >= 2:
        render_objective_signal(
            doc, ds,
            f"Consecutive Earnings Misses: {eg.consecutive_miss_count}",
            "HIGH",
            "Primary trigger for 10(b) SCAs; demonstrates scienter",
        )
        render_scenario_context(
            doc, ds,
            "Companies with 2+ consecutive misses face SCA filing "
            "rates 4.1x the industry baseline.",
        )


def _render_quarter_table(
    doc: Any,
    quarters: list[EarningsQuarterRecord],
    ds: DesignSystem,
) -> None:
    """Render quarter-by-quarter earnings guidance table."""
    headers = [
        "Quarter",
        "Est. EPS",
        "Actual EPS",
        "Result",
        "Miss Magnitude",
        "Stock Reaction",
    ]
    rows: list[list[str]] = []
    for qtr in quarters[:16]:
        # Build guidance range string
        guidance_str = _format_guidance_range(qtr)
        actual_str = (
            f"${qtr.actual_eps.value:.2f}" if qtr.actual_eps else "N/A"
        )
        result_str = qtr.result or "N/A"
        miss_str = (
            f"{qtr.miss_magnitude_pct.value:+.1f}%"
            if qtr.miss_magnitude_pct
            else "N/A"
        )
        react_str = (
            f"{qtr.stock_reaction_pct.value:+.1f}%"
            if qtr.stock_reaction_pct
            else "N/A"
        )
        rows.append([
            qtr.quarter or "N/A",
            guidance_str,
            actual_str,
            result_str,
            miss_str,
            react_str,
        ])

    table: Any = add_styled_table(doc, headers, rows, ds)

    # Conditional formatting: highlight misses in red, beats in blue
    for row_idx, qtr in enumerate(quarters[:16]):
        result_cell: Any = table.rows[row_idx + 1].cells[3]  # Result column
        if qtr.result == "MISS":
            set_cell_shading(result_cell, "FCE8E6")  # Red
        elif qtr.result == "BEAT":
            set_cell_shading(result_cell, "DCEEF8")  # Blue (NO green)


def _format_guidance_range(qtr: EarningsQuarterRecord) -> str:
    """Format EPS guidance range for display."""
    low = qtr.consensus_eps_low
    high = qtr.consensus_eps_high
    if low and high:
        if abs(low.value - high.value) < 0.005:
            return f"${low.value:.2f}"
        return f"${low.value:.2f} - ${high.value:.2f}"
    if low:
        return f"${low.value:.2f}+"
    if high:
        return f"<= ${high.value:.2f}"
    return "N/A"


def _render_analyst_consensus(
    doc: Any, market: MarketSignals | None, ds: DesignSystem
) -> None:
    """Render analyst consensus section."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Analyst Consensus")

    analyst = market.analyst if market else None
    if analyst is None or (
        analyst.coverage_count is None and analyst.target_price_mean is None
    ):
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Analyst consensus data not available.")
        return

    rows: list[list[str]] = []
    if analyst.coverage_count:
        rows.append(["Analyst Coverage", str(analyst.coverage_count.value)])
    if analyst.consensus:
        rows.append(["Consensus Rating", str(analyst.consensus.value)])
    if analyst.recommendation_mean:
        rows.append([
            "Mean Recommendation",
            f"{analyst.recommendation_mean.value:.2f} (1=Strong Buy, 5=Sell)",
        ])
    if analyst.target_price_mean:
        rows.append([
            "Mean Target Price",
            format_currency(analyst.target_price_mean.value),
        ])
    if analyst.target_price_high:
        rows.append([
            "Target Price High",
            format_currency(analyst.target_price_high.value),
        ])
    if analyst.target_price_low:
        rows.append([
            "Target Price Low",
            format_currency(analyst.target_price_low.value),
        ])

    # Rating distribution: upgrades/downgrades
    if analyst.recent_upgrades or analyst.recent_downgrades:
        rows.append([
            "Recent Upgrades (90d)",
            str(analyst.recent_upgrades),
        ])
        rows.append([
            "Recent Downgrades (90d)",
            str(analyst.recent_downgrades),
        ])

    if rows:
        add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # D&O context: downgrade trend
    if analyst.recent_downgrades >= 3:
        fp: Any = doc.add_paragraph(style="DOBody")
        fp.add_run(
            f"Analyst Downgrade Trend ({analyst.recent_downgrades} in 90 days): "
            "Multiple analyst downgrades often precede or accompany securities "
            "litigation as they reflect deteriorating confidence in management "
            "guidance credibility."
        )
        add_risk_indicator(fp, "ELEVATED", ds)


def _embed_optional_chart(
    doc: Any,
    chart_dir: Path | None,
    filename: str,
    ds: DesignSystem,
    caption: str,
) -> None:
    """Embed a chart PNG from disk if it exists, with caption."""
    if chart_dir is None:
        return
    path = chart_dir / filename
    if embed_chart_from_disk(doc, path, ds):
        cap: Any = doc.add_paragraph(style="DOCaption")
        cap.add_run(caption)


__all__ = ["render_section_4"]
