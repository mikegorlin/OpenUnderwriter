"""Peer context formatting utilities for context-through-comparison.

Provides reusable functions that format any benchmarked metric with its
percentile rank, peer count, baseline value, and named peers. Used by
all section renderers to answer "compared to what?" for every metric.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.financials import PeerCompany
from do_uw.models.scoring import BenchmarkResult, MetricBenchmark
from do_uw.models.state import AnalysisState
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import add_styled_table
from do_uw.stages.render.formatters import format_currency


def _ordinal(n: int) -> str:
    """Convert an integer to its ordinal string representation.

    Examples:
        1 -> "1st", 2 -> "2nd", 3 -> "3rd", 4 -> "4th",
        11 -> "11th", 12 -> "12th", 13 -> "13th",
        21 -> "21st", 22 -> "22nd", 23 -> "23rd",
        111 -> "111th", 112 -> "112th", 113 -> "113th".
    """
    # Special case: 11th, 12th, 13th (and 111th, 112th, 113th, etc.)
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    remainder = n % 10
    if remainder == 1:
        return f"{n}st"
    if remainder == 2:
        return f"{n}nd"
    if remainder == 3:
        return f"{n}rd"
    return f"{n}th"


def format_metric_with_context(
    label: str,
    value: str,
    benchmark: MetricBenchmark | None,
    named_peers: list[str] | None = None,
) -> str:
    """Format a metric with its benchmark context.

    If benchmark data is available, appends percentile rank, peer count,
    and baseline value. Optionally appends up to 3 named peers.

    Args:
        label: Human-readable metric name (e.g., "Market Cap").
        value: Formatted metric value (e.g., "$12.3B").
        benchmark: MetricBenchmark with percentile/peer data, or None.
        named_peers: Optional list of peer ticker strings to display.

    Returns:
        Formatted string with context, e.g.:
        "Market Cap: $12.3B (72nd percentile vs. 15 peers; median $8.1B)"
    """
    if benchmark is None or benchmark.percentile_rank is None:
        return f"{label}: {value}"

    rank = int(round(benchmark.percentile_rank))
    parts = f"{label}: {value} ({_ordinal(rank)} percentile vs. {benchmark.peer_count} peers"

    if benchmark.baseline_value is not None:
        # Format baseline as compact currency if it looks like a dollar amount
        # (market_cap, revenue), otherwise as a plain number
        baseline_str = _format_baseline(benchmark)
        parts += f"; median {baseline_str}"

    parts += ")"

    if named_peers:
        display_peers = named_peers[:3]
        parts += f" [{', '.join(display_peers)}]"

    return parts


def get_peer_context_line(
    metric_key: str,
    benchmark_result: BenchmarkResult | None,
) -> str | None:
    """Get a formatted peer context sentence for a metric.

    Looks up metric_key in benchmark_result.metric_details (structured
    MetricBenchmark) or falls back to peer_rankings (simple percentile).

    Args:
        metric_key: Metric identifier (e.g., "market_cap", "quality_score").
        benchmark_result: BenchmarkResult from state, or None.

    Returns:
        Formatted sentence like "Ranks at the 72nd percentile among 15 peers
        (peer median: $8.1B)", or None if data unavailable.
    """
    if benchmark_result is None:
        return None

    # Try structured metric_details first
    if metric_key in benchmark_result.metric_details:
        mb = benchmark_result.metric_details[metric_key]
        if mb.percentile_rank is None:
            return None
        rank = int(round(mb.percentile_rank))
        line = f"Ranks at the {_ordinal(rank)} percentile among {mb.peer_count} peers"
        if mb.baseline_value is not None:
            baseline_str = _format_baseline(mb)
            line += f" (peer median: {baseline_str})"
        return line

    # Fallback to simple peer_rankings dict
    if metric_key in benchmark_result.peer_rankings:
        rank = int(round(benchmark_result.peer_rankings[metric_key]))
        return f"Ranks at the {_ordinal(rank)} percentile among peers"

    return None


def get_benchmark_for_metric(
    metric_key: str,
    state: AnalysisState,
) -> MetricBenchmark | None:
    """Safely extract a MetricBenchmark from state.

    Args:
        metric_key: Metric identifier (e.g., "market_cap").
        state: The analysis state.

    Returns:
        MetricBenchmark if available, None otherwise.
    """
    if state.benchmark is None:
        return None
    return state.benchmark.metric_details.get(metric_key)


def render_peer_comparison_narrative(
    doc: Any,
    state: AnalysisState,
    ds: DesignSystem,
) -> None:
    """Render a structured peer comparison subsection.

    Shows named peers with their characteristics (ticker, name, market cap,
    quality score, similarity) in a table, plus a narrative paragraph
    describing the company's position within its peer group.

    Args:
        doc: The python-docx Document.
        state: AnalysisState with benchmark and extracted data.
        ds: Design system for styling.
    """
    # Heading
    para: Any = doc.add_paragraph(style="DOHeading3")
    para.add_run("Peer Group Comparison")

    # Guard: no benchmark data
    if state.benchmark is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Peer comparison data not available for this analysis.")
        return

    bm = state.benchmark

    # Build peer lookup from extracted financials
    peer_lookup: dict[str, PeerCompany] = {}
    if (
        state.extracted is not None
        and state.extracted.financials is not None
        and state.extracted.financials.peer_group is not None
    ):
        for pc in state.extracted.financials.peer_group.peers:
            peer_lookup[pc.ticker] = pc

    # Determine which tickers to display
    tickers = bm.peer_group_tickers
    if not tickers and not peer_lookup:
        body = doc.add_paragraph(style="DOBody")
        body.add_run("No peer companies identified for comparison.")
        return

    # If no tickers in benchmark but we have peer_lookup, use those
    if not tickers:
        tickers = list(peer_lookup.keys())

    # Build table rows
    rows: list[list[str]] = []
    for ticker in tickers:
        pc = peer_lookup.get(ticker)
        name = pc.name if pc else ticker
        mcap = format_currency(pc.market_cap, compact=True) if pc and pc.market_cap else "N/A"
        quality = _format_quality_score(ticker, bm)
        similarity = _format_similarity(pc)
        rows.append([ticker, name, mcap, quality, similarity])

    if rows:
        add_styled_table(
            doc,
            ["Ticker", "Name", "Market Cap", "Quality Score", "Similarity"],
            rows,
            ds,
        )

    # Narrative paragraph
    _render_narrative(doc, state, bm, ds)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _format_baseline(mb: MetricBenchmark) -> str:
    """Format a baseline value based on metric context.

    Uses compact currency for large values (market_cap, revenue),
    percentage for rate metrics, plain number otherwise.
    """
    if mb.baseline_value is None:
        return "N/A"
    val = mb.baseline_value
    name_lower = mb.metric_name.lower()
    # Ratio metrics (must check BEFORE currency keywords — "leverage_debt_ebitda" contains "debt")
    if any(kw in name_lower for kw in ("leverage", "ratio", "ebitda", "coverage")):
        return f"{val:.1f}x"
    # Currency metrics
    if any(kw in name_lower for kw in ("market_cap", "revenue", "cap", "debt")):
        return format_currency(val, compact=True)
    # Percentage metrics
    if any(kw in name_lower for kw in ("pct", "percent", "interest", "volatility")):
        return f"{val:.1f}%"
    # Score metrics
    if "score" in name_lower:
        return f"{val:.1f}"
    # Default
    if abs(val) >= 1_000_000:
        return format_currency(val, compact=True)
    return f"{val:,.1f}"


def _format_quality_score(ticker: str, bm: BenchmarkResult) -> str:
    """Format peer quality score if available."""
    score = bm.peer_quality_scores.get(ticker)
    if score is None:
        return "N/A"
    return f"{score:.1f}"


def _format_similarity(pc: PeerCompany | None) -> str:
    """Format peer similarity score/tier."""
    if pc is None:
        return "N/A"
    parts: list[str] = []
    if pc.peer_tier:
        # Humanize tier: "primary_sic" -> "Primary SIC"
        parts.append(pc.peer_tier.replace("_", " ").title())
    if pc.peer_score > 0:
        parts.append(f"{pc.peer_score:.0f}%")
    return " / ".join(parts) if parts else "N/A"


def _render_narrative(
    doc: Any,
    state: AnalysisState,
    bm: BenchmarkResult,
    ds: DesignSystem,
) -> None:
    """Render narrative paragraph about peer group position."""
    company_name = "The company"
    if state.company and state.company.identity:
        if state.company.identity.legal_name:
            company_name = str(state.company.identity.legal_name.value)
        elif state.company.identity.ticker:
            company_name = state.company.identity.ticker

    peer_count = len(bm.peer_group_tickers)

    # Get sector info
    sector = ""
    if (
        state.company
        and state.company.identity
        and state.company.identity.sic_code
    ):
        sector = f" (SIC {state.company.identity.sic_code.value})"

    # Market cap percentile
    mcap_line = get_peer_context_line("market_cap", bm)
    mcap_part = ""
    if mcap_line:
        mcap_part = f" {company_name} {mcap_line.lower()} by market capitalization."

    narrative = (
        f"The peer group of {peer_count} companies shares the same industry"
        f" classification{sector}."
        f"{mcap_part}"
    )

    body: Any = doc.add_paragraph(style="DOBody")
    run: Any = body.add_run(narrative)
    run.font.name = ds.font_body
    run.font.size = ds.size_body
    run.font.color.rgb = ds.color_text
    _ = ds  # used above


__all__ = [
    "format_metric_with_context",
    "get_benchmark_for_metric",
    "get_peer_context_line",
    "render_peer_comparison_narrative",
]
