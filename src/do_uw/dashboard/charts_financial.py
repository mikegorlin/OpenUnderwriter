"""Financial Plotly chart builders for the D&O underwriting dashboard.

Provides interactive figure builders for financial health visualization:
- Distress model gauges (Z-Score, O-Score, M-Score, F-Score)
- Peer comparison bar charts
- Red flag summary chart

All functions accept AnalysisState and return Plotly Figure objects
typed as Any for pyright strict compliance (plotly is untyped).
"""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go  # type: ignore[import-untyped]

from do_uw.models.state import AnalysisState

# Angry Dolphin brand colors
_NAVY = "#1A1446"
_GOLD = "#FFD000"

# Risk spectrum colors (NO green)
_RISK_CRITICAL = "#CC0000"
_RISK_HIGH = "#E67300"
_RISK_ELEVATED = "#FFB800"
_RISK_MODERATE = "#4A90D9"
_RISK_NEUTRAL = "#999999"
_PEER_GRAY = "#999999"


def _empty_figure(message: str = "No data available") -> Any:
    """Return a minimal empty Plotly figure with a message."""
    fig: Any = go.Figure()
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 14, "color": _RISK_NEUTRAL},
            }
        ],
        height=200,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    return fig


def _build_single_distress_gauge(
    score: float | None,
    title: str,
    steps: list[dict[str, Any]],
    axis_range: list[float],
) -> Any:
    """Build a single distress model gauge indicator.

    Args:
        score: The distress score value (None for unavailable).
        title: Gauge title label.
        steps: Colored zone steps for the gauge.
        axis_range: [min, max] range for the gauge axis.

    Returns:
        Plotly Figure.
    """
    if score is None:
        return _empty_figure(f"{title}: No data")

    fig: Any = go.Figure(
        data=[
            go.Indicator(
                mode="gauge+number",
                value=score,
                title={"text": title, "font": {"size": 13, "color": _NAVY}},
                gauge={
                    "axis": {"range": axis_range},
                    "bar": {"color": _NAVY},
                    "steps": steps,
                    "threshold": {
                        "line": {"color": _GOLD, "width": 3},
                        "thickness": 0.8,
                        "value": score,
                    },
                },
                number={"font": {"color": _NAVY, "size": 20}},
            )
        ]
    )
    fig.update_layout(
        height=200,
        margin={"l": 15, "r": 15, "t": 40, "b": 15},
    )
    return fig


def build_distress_gauges(state: AnalysisState) -> dict[str, Any]:
    """Build gauge figures for all four distress models.

    Returns a dict keyed by model name: z_score, o_score, m_score, f_score.
    Each value is a Plotly Figure.

    Zone coloring per model:
    - Z-Score: >2.99 safe (blue), 1.81-2.99 grey zone (neutral), <1.81 distress (red)
    - O-Score: <0.5 safe (blue), >0.5 distress (red) (probability of bankruptcy)
    - M-Score: <-1.78 unlikely (blue), >-1.78 possible (red) (earnings manipulation)
    - F-Score: >=7 strong (blue), 4-6 moderate (amber), <4 weak (red)

    Args:
        state: Analysis state with financial distress data.

    Returns:
        Dict mapping model name to Plotly Figure.
    """
    distress = None
    if state.extracted and state.extracted.financials:
        distress = state.extracted.financials.distress

    z_score = distress.altman_z_score.score if distress and distress.altman_z_score else None
    o_score = distress.ohlson_o_score.score if distress and distress.ohlson_o_score else None
    m_score = distress.beneish_m_score.score if distress and distress.beneish_m_score else None
    f_score = distress.piotroski_f_score.score if distress and distress.piotroski_f_score else None

    return {
        "z_score": _build_single_distress_gauge(
            score=z_score,
            title="Altman Z-Score",
            steps=[
                {"range": [0, 1.81], "color": _RISK_CRITICAL},
                {"range": [1.81, 2.99], "color": _RISK_NEUTRAL},
                {"range": [2.99, 5.0], "color": _RISK_MODERATE},
            ],
            axis_range=[0, 5.0],
        ),
        "o_score": _build_single_distress_gauge(
            score=o_score,
            title="Ohlson O-Score",
            steps=[
                {"range": [0, 0.5], "color": _RISK_MODERATE},
                {"range": [0.5, 1.0], "color": _RISK_CRITICAL},
            ],
            axis_range=[0, 1.0],
        ),
        "m_score": _build_single_distress_gauge(
            score=m_score,
            title="Beneish M-Score",
            steps=[
                {"range": [-3.5, -1.78], "color": _RISK_MODERATE},
                {"range": [-1.78, 0.0], "color": _RISK_CRITICAL},
            ],
            axis_range=[-3.5, 0.0],
        ),
        "f_score": _build_single_distress_gauge(
            score=f_score,
            title="Piotroski F-Score",
            steps=[
                {"range": [0, 4], "color": _RISK_CRITICAL},
                {"range": [4, 7], "color": _RISK_ELEVATED},
                {"range": [7, 9], "color": _RISK_MODERATE},
            ],
            axis_range=[0, 9],
        ),
    }


def build_peer_comparison_bars(
    state: AnalysisState, metric_key: str
) -> Any:
    """Build a horizontal bar chart comparing company against peers.

    Company bar in navy, peer bars in gray. The metric_key selects
    which metric to display from benchmark data.

    Args:
        state: Analysis state with benchmark data.
        metric_key: Metric to compare (quality_score, etc.).

    Returns:
        Plotly Figure.
    """
    if state.benchmark is None:
        return _empty_figure("No peer benchmark data available")

    # Build data from peer_quality_scores for quality_score metric
    if metric_key == "quality_score":
        peer_scores = state.benchmark.peer_quality_scores
        company_score = state.scoring.quality_score if state.scoring else None
        if not peer_scores and company_score is None:
            return _empty_figure("No quality score data")

        tickers: list[str] = []
        values: list[float] = []
        colors: list[str] = []

        # Add company first
        if company_score is not None:
            tickers.append(state.ticker)
            values.append(company_score)
            colors.append(_NAVY)

        # Add peers sorted by score descending
        for ticker, score in sorted(
            peer_scores.items(), key=lambda x: x[1], reverse=True
        ):
            tickers.append(ticker)
            values.append(score)
            colors.append(_PEER_GRAY)

    else:
        # Generic metric from metric_details
        details = state.benchmark.metric_details.get(metric_key)
        if details is None or details.company_value is None:
            return _empty_figure(f"No data for metric: {metric_key}")

        tickers = [state.ticker]
        values = [details.company_value]
        colors = [_NAVY]

        # Add baseline if available
        if details.baseline_value is not None:
            tickers.append("Sector Avg")
            values.append(details.baseline_value)
            colors.append(_PEER_GRAY)

    fig: Any = go.Figure(
        data=[
            go.Bar(
                x=values,
                y=tickers,
                orientation="h",
                marker={"color": colors},
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    f"{metric_key}: " + "%{x:.2f}<br>"
                    "<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        height=max(200, len(tickers) * 35),
        margin={"l": 80, "r": 20, "t": 30, "b": 30},
        xaxis={"title": metric_key.replace("_", " ").title()},
        yaxis={"autorange": "reversed"},
    )
    return fig


def build_red_flag_summary(state: AnalysisState) -> Any:
    """Build a horizontal bar chart of triggered red flags.

    Each bar shows the red flag name, color-coded by whether a ceiling
    was applied (critical impact) or just triggered.

    Args:
        state: Analysis state with scoring red flag results.

    Returns:
        Plotly Figure.
    """
    if state.scoring is None:
        return _empty_figure("No scoring data available")

    triggered = [rf for rf in state.scoring.red_flags if rf.triggered]
    if not triggered:
        return _empty_figure("No red flags triggered")

    names = [rf.flag_name or rf.flag_id for rf in triggered]
    # Use ceiling as bar value (impact severity); default to 50 if no ceiling
    ceilings = [rf.ceiling_applied if rf.ceiling_applied is not None else 50 for rf in triggered]
    colors = [
        _RISK_CRITICAL if (rf.ceiling_applied is not None and rf.ceiling_applied <= 30) else
        _RISK_HIGH if (rf.ceiling_applied is not None and rf.ceiling_applied <= 50) else
        _RISK_ELEVATED
        for rf in triggered
    ]

    fig: Any = go.Figure(
        data=[
            go.Bar(
                x=ceilings,
                y=names,
                orientation="h",
                marker={"color": colors},
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Ceiling: %{x}<br>"
                    "<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        height=max(200, len(triggered) * 40),
        margin={"l": 180, "r": 20, "t": 30, "b": 30},
        xaxis={"title": "Score Ceiling Applied", "range": [0, 100]},
        yaxis={"autorange": "reversed"},
    )
    return fig


__all__ = [
    "build_distress_gauges",
    "build_peer_comparison_bars",
    "build_red_flag_summary",
]
