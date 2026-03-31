"""Core Plotly chart builders for the D&O underwriting dashboard.

Provides interactive figure builders for risk visualization:
- Risk radar (10-factor scoring spider chart)
- Risk heatmap (factor intensity grid)
- Factor bar chart (deduction breakdown)
- Score gauge (generic indicator)
- Tier gauge (quality score indicator)

All functions accept AnalysisState and return Plotly Figure objects
typed as Any for pyright strict compliance (plotly is untyped).
"""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go  # type: ignore[import-untyped]

from do_uw.models.state import AnalysisState

# Angry Dolphin brand colors (mirrors design.py CSS variables)
_NAVY = "#1A1446"
_GOLD = "#FFD000"

# Risk spectrum colors (NO green)
_RISK_CRITICAL = "#CC0000"
_RISK_HIGH = "#E67300"
_RISK_ELEVATED = "#FFB800"
_RISK_MODERATE = "#4A90D9"
_RISK_NEUTRAL = "#999999"

# Risk heatmap colorscale: blue -> amber -> orange -> red
_HEATMAP_COLORSCALE: list[list[Any]] = [
    [0.0, _RISK_MODERATE],
    [0.5, _RISK_ELEVATED],
    [0.75, _RISK_HIGH],
    [1.0, _RISK_CRITICAL],
]


def empty_figure() -> Any:
    """Return a minimal empty Plotly figure."""
    fig: Any = go.Figure()
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": "No scoring data available",
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


def build_risk_radar(state: AnalysisState) -> Any:
    """Build a radar/spider chart of the 10 scoring factors.

    Each axis shows the risk fraction (points_deducted / max_points)
    on a 0-1 scale. Higher values indicate greater risk.

    Args:
        state: Analysis state with scoring data.

    Returns:
        Plotly Figure (typed as Any for pyright strict).
    """
    if state.scoring is None or not state.scoring.factor_scores:
        return empty_figure()

    factors = state.scoring.factor_scores
    names = [f.factor_name for f in factors]
    fractions = [
        f.points_deducted / f.max_points if f.max_points > 0 else 0.0
        for f in factors
    ]

    # Plotly requires explicit re-close for radar fill
    fig: Any = go.Figure(
        data=[
            go.Scatterpolar(
                r=[*fractions, fractions[0]],
                theta=[*names, names[0]],
                fill="toself",
                fillcolor="rgba(26, 20, 70, 0.15)",
                line={"color": _NAVY, "width": 2},
                marker={"color": _NAVY, "size": 6},
                hovertemplate=(
                    "<b>%{theta}</b><br>"
                    "Risk: %{r:.0%}<br>"
                    "<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, 1],
                "tickvals": [0.25, 0.5, 0.75, 1.0],
                "ticktext": ["25%", "50%", "75%", "100%"],
                "gridcolor": "#E0E0E0",
            },
            "angularaxis": {"gridcolor": "#E0E0E0"},
        },
        showlegend=False,
        height=400,
        margin={"l": 60, "r": 60, "t": 40, "b": 40},
    )
    return fig


def build_risk_heatmap(state: AnalysisState) -> Any:
    """Build a compact heatmap of factor risk intensities.

    Single-row heatmap with color intensity from blue (low risk)
    to red (critical risk) using the brand risk spectrum.

    Args:
        state: Analysis state with scoring data.

    Returns:
        Plotly Figure (typed as Any for pyright strict).
    """
    if state.scoring is None or not state.scoring.factor_scores:
        return empty_figure()

    factors = state.scoring.factor_scores
    names = [f.factor_name for f in factors]
    fractions = [
        [
            f.points_deducted / f.max_points if f.max_points > 0 else 0.0
            for f in factors
        ]
    ]

    fig: Any = go.Figure(
        data=[
            go.Heatmap(
                z=fractions,
                x=names,
                y=["Risk Level"],
                colorscale=_HEATMAP_COLORSCALE,
                zmin=0,
                zmax=1,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Risk: %{z:.0%}<br>"
                    "<extra></extra>"
                ),
                showscale=False,
            )
        ]
    )

    fig.update_layout(
        height=120,
        margin={"l": 10, "r": 10, "t": 10, "b": 50},
        xaxis={"tickangle": -45, "tickfont": {"size": 9}},
        yaxis={"visible": False},
    )
    return fig


def _bar_color_for_fraction(fraction: float) -> str:
    """Return risk color based on deduction severity fraction."""
    if fraction >= 0.75:
        return _RISK_CRITICAL
    if fraction >= 0.50:
        return _RISK_HIGH
    if fraction >= 0.25:
        return _RISK_ELEVATED
    return _RISK_MODERATE


def build_factor_bar_chart(state: AnalysisState) -> Any:
    """Build a horizontal bar chart of points deducted per factor.

    Bars are color-coded by deduction severity relative to max points.

    Args:
        state: Analysis state with scoring data.

    Returns:
        Plotly Figure (typed as Any for pyright strict).
    """
    if state.scoring is None or not state.scoring.factor_scores:
        return empty_figure()

    factors = state.scoring.factor_scores
    names = [f.factor_name for f in factors]
    deductions = [f.points_deducted for f in factors]
    fractions = [
        f.points_deducted / f.max_points if f.max_points > 0 else 0.0
        for f in factors
    ]
    colors = [_bar_color_for_fraction(frac) for frac in fractions]

    fig: Any = go.Figure(
        data=[
            go.Bar(
                x=deductions,
                y=names,
                orientation="h",
                marker={"color": colors},
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Deducted: %{x:.1f} pts<br>"
                    "<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        height=max(250, len(factors) * 35),
        margin={"l": 150, "r": 20, "t": 30, "b": 30},
        xaxis={"title": "Points Deducted"},
        yaxis={"autorange": "reversed"},
    )
    return fig


def build_score_gauge(score: float, max_score: float, title: str) -> Any:
    """Build a gauge indicator for a numeric score.

    Steps are colored with the risk spectrum at threshold boundaries:
    0-30 blue, 30-50 amber, 50-75 orange, 75-max red.

    Args:
        score: Current score value.
        max_score: Maximum possible score.
        title: Label displayed below the gauge.

    Returns:
        Plotly Figure (typed as Any for pyright strict).
    """
    fig: Any = go.Figure(
        data=[
            go.Indicator(
                mode="gauge+number",
                value=score,
                title={"text": title, "font": {"size": 14, "color": _NAVY}},
                gauge={
                    "axis": {"range": [0, max_score]},
                    "bar": {"color": _NAVY},
                    "steps": [
                        {"range": [0, 30], "color": _RISK_MODERATE},
                        {"range": [30, 50], "color": _RISK_ELEVATED},
                        {"range": [50, 75], "color": _RISK_HIGH},
                        {"range": [75, max_score], "color": _RISK_CRITICAL},
                    ],
                    "threshold": {
                        "line": {"color": _GOLD, "width": 3},
                        "thickness": 0.8,
                        "value": score,
                    },
                },
                number={"font": {"color": _NAVY}},
            )
        ]
    )
    fig.update_layout(
        height=220,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
    )
    return fig


def build_tier_gauge(quality_score: float) -> Any:
    """Build a specialized gauge for the overall quality score (0-100).

    Steps reflect tier boundaries:
    0-20 critical (red), 20-40 high (orange), 40-60 elevated (amber),
    60-80 moderate (blue), 80-100 neutral (gray).

    Args:
        quality_score: Quality score from 0 to 100.

    Returns:
        Plotly Figure (typed as Any for pyright strict).
    """
    fig: Any = go.Figure(
        data=[
            go.Indicator(
                mode="gauge+number",
                value=quality_score,
                title={
                    "text": "Quality Score",
                    "font": {"size": 14, "color": _NAVY},
                },
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": _NAVY},
                    "steps": [
                        {"range": [0, 20], "color": _RISK_CRITICAL},
                        {"range": [20, 40], "color": _RISK_HIGH},
                        {"range": [40, 60], "color": _RISK_ELEVATED},
                        {"range": [60, 80], "color": _RISK_MODERATE},
                        {"range": [80, 100], "color": _RISK_NEUTRAL},
                    ],
                    "threshold": {
                        "line": {"color": _GOLD, "width": 3},
                        "thickness": 0.8,
                        "value": quality_score,
                    },
                },
                number={"font": {"color": _NAVY}},
            )
        ]
    )
    fig.update_layout(
        height=250,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
    )
    return fig


__all__ = [
    "build_factor_bar_chart",
    "build_risk_heatmap",
    "build_risk_radar",
    "build_score_gauge",
    "build_tier_gauge",
    "empty_figure",
]
