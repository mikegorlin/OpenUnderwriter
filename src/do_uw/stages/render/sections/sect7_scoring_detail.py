"""Section 7 scoring detail: per-factor detail tables, pattern detection,
allegation mapping, claim probability, and tower position recommendation.

Split from sect7_scoring.py for 500-line compliance. This module
renders the detailed supporting evidence behind the composite score.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.scoring import (
    BenchmarkResult,
    PatternMatch,
    ScoringResult,
)
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_styled_table,
)
from do_uw.stages.render.formatters import format_percentage
from do_uw.stages.render.peer_context import get_peer_context_line

# Mapping from scoring factor IDs to benchmark metric keys.
# Used to add "X percentile vs peers" context inline with factor scores.
_FACTOR_BENCHMARK_MAP: dict[str, str] = {
    "F.6": "short_interest_pct",    # Short Interest -> short interest %
    "F.7": "volatility_90d",        # Volatility -> 90-day volatility
    "F.8": "leverage_debt_ebitda",   # Financial Distress -> leverage ratio
    "F.9": "governance_score",       # Governance -> governance score
}


def _get_scoring(context: dict[str, Any]) -> ScoringResult | None:
    """Extract scoring data from context dict."""
    # TODO(phase-60): use context["scoring"] when it returns ScoringResult
    state = context.get("_state")
    return state.scoring if state is not None else None


def _factor_benchmark_context(
    factor_id: str, benchmark: BenchmarkResult | None
) -> str:
    """Get benchmark context string for a factor, if available.

    Returns e.g. " [35th pctl vs peers]" or empty string.
    """
    if benchmark is None:
        return ""
    metric_key = _FACTOR_BENCHMARK_MAP.get(factor_id)
    if metric_key is None:
        return ""
    ctx = get_peer_context_line(metric_key, benchmark)
    if ctx is None:
        return ""
    # Extract the ordinal from "Ranks at the 35th percentile among N peers"
    if "Ranks at the " in ctx:
        rest = ctx.split("Ranks at the ")[1]
        return f" [{rest}]"
    return f" [{ctx}]"


# ---------------------------------------------------------------------------
# Per-Factor Detail Tables
# ---------------------------------------------------------------------------


def _render_factor_detail(
    doc: Any, scoring: ScoringResult, benchmark: BenchmarkResult | None,
    ds: DesignSystem,
) -> None:
    """Render top contributing checks per factor.

    For each factor with non-zero deductions, shows the top 5
    contributing rules with their evidence. Adds benchmark context
    inline for factors that map to benchmark metrics.
    """
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Factor Detail")

    factors = scoring.factor_scores
    active_factors = [f for f in factors if f.points_deducted > 0]
    if not active_factors:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No factors with risk deductions.")
        return

    headers = [
        "Factor", "Name", "Deducted",
        "Rules Triggered", "Evidence",
    ]
    rows: list[list[str]] = []
    for fs in active_factors:
        rules = ", ".join(fs.rules_triggered[:5]) if fs.rules_triggered else "N/A"
        evidence = "; ".join(fs.evidence[:3]) if fs.evidence else "None"
        # Add benchmark context to the name if available
        name = fs.factor_name
        bm_ctx = _factor_benchmark_context(fs.factor_id, benchmark)
        if bm_ctx:
            name += bm_ctx

        rows.append([
            fs.factor_id, name,
            f"{fs.points_deducted:.1f}",
            rules, evidence,
        ])

    add_styled_table(doc, headers, rows, ds)

    # Sub-component detail for factors with breakdowns
    _render_sub_components(doc, active_factors, ds)


def _render_sub_components(
    doc: Any, factors: list[Any], ds: DesignSystem
) -> None:
    """Render sub-component breakdown for factors that have it."""
    factors_with_subs = [f for f in factors if f.sub_components]
    if not factors_with_subs:
        return

    sub_heading: Any = doc.add_paragraph(style="DOBody")
    sub_run: Any = sub_heading.add_run("Sub-Component Breakdown")
    sub_run.bold = True
    sub_run.font.size = ds.size_body

    headers = ["Factor", "Component", "Value"]
    rows: list[list[str]] = []
    for fs in factors_with_subs:
        for comp_name, comp_val in fs.sub_components.items():
            rows.append([
                fs.factor_id,
                comp_name,
                f"{comp_val:.2f}",
            ])

    if rows:
        add_styled_table(doc, headers, rows, ds)


# ---------------------------------------------------------------------------
# Pattern Detection Results
# ---------------------------------------------------------------------------


def _get_signal_results(ctx: dict[str, Any]) -> dict[str, Any] | None:
    """Extract signal_results dict from context."""
    state = ctx.get("_state")
    if state is None or state.analysis is None:
        return None
    return state.analysis.signal_results


def _render_pattern_detection(
    doc: Any, scoring: ScoringResult, signal_results: dict[str, Any] | None,
    ds: DesignSystem,
) -> None:
    """Render pattern detection results with trigger conditions."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Pattern Detection Results")

    detected = [p for p in scoring.patterns_detected if p.detected]
    if not detected:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No composite patterns detected.")
        return

    headers = ["Pattern", "Severity", "Triggers Matched", "Score Impact"]
    rows: list[list[str]] = []
    for pat in detected:
        triggers = ", ".join(pat.triggers_matched[:3])
        impact = ", ".join(
            f"{k}: +{v:.0f}" for k, v in pat.score_impact.items()
        )
        rows.append([
            pat.pattern_name or pat.pattern_id,
            pat.severity, triggers, impact,
        ])

    add_styled_table(doc, headers, rows, ds)

    # D&O context per pattern from brain signal do_context
    for pat in detected:
        _render_pattern_signal_do_context(doc, pat, signal_results, ds)


def _render_pattern_signal_do_context(
    doc: Any,
    pat: PatternMatch,
    signal_results: dict[str, Any] | None,
    ds: DesignSystem,
) -> None:
    """Render D&O context for a detected pattern from brain signal do_context.

    Replaces the deleted _add_pattern_do_context() function. Uses the
    signal_contributions on the pattern's triggers to find relevant signal
    do_context, falling back to a generic pattern-severity message.
    """
    severity = pat.severity.upper()
    if severity not in ("HIGH", "SEVERE"):
        return

    # Try to find do_context from the pattern's trigger signals
    do_text = ""
    for trigger_id in pat.triggers_matched[:3]:
        sig = safe_get_result(signal_results, trigger_id)
        if sig and sig.do_context:
            do_text = sig.do_context
            break

    if not do_text:
        do_text = (
            f"This {severity} pattern indicates elevated claim "
            f"probability. Verify tower position and retention."
        )

    para: Any = doc.add_paragraph(style="DOBody")
    run: Any = para.add_run(
        f"D&O Context ({pat.pattern_name or pat.pattern_id}): {do_text}"
    )
    run.italic = True
    run.font.size = ds.size_small
    add_risk_indicator(para, severity, ds)


# ---------------------------------------------------------------------------
# Allegation Mapping
# ---------------------------------------------------------------------------


def _render_allegation_mapping(
    doc: Any, scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render allegation theory-to-evidence mapping."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Allegation Theory Mapping")

    am = scoring.allegation_mapping
    if am is None:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Allegation mapping not available.")
        return

    headers = ["Theory", "Exposure", "Factor Sources", "Key Findings"]
    rows: list[list[str]] = []
    for te in am.theories:
        findings = "; ".join(te.findings[:2]) if te.findings else "None"
        sources = ", ".join(te.factor_sources) if te.factor_sources else "N/A"
        rows.append([
            te.theory.value, te.exposure_level,
            sources, findings,
        ])

    add_styled_table(doc, headers, rows, ds)

    # Primary exposure D&O context
    para: Any = doc.add_paragraph(style="DOBody")
    run: Any = para.add_run(
        f"D&O Context: Primary allegation exposure is "
        f"{am.primary_exposure.value}. {am.concentration_analysis}"
    )
    run.italic = True
    run.font.size = ds.size_small


# ---------------------------------------------------------------------------
# Claim Probability Detail
# ---------------------------------------------------------------------------


def _render_claim_probability(
    doc: Any, scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render claim probability estimation detail."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Claim Probability Detail")

    cp = scoring.claim_probability
    if cp is None:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Claim probability not available.")
        return

    rows: list[list[str]] = [
        ["Probability Band", cp.band.value],
        ["Range", f"{format_percentage(cp.range_low_pct)} - "
                  f"{format_percentage(cp.range_high_pct)}"],
    ]
    if cp.industry_base_rate_pct > 0:
        rows.append([
            "Industry Base Rate",
            format_percentage(cp.industry_base_rate_pct),
        ])
    if cp.adjustment_narrative:
        rows.append([
            "Adjustment Rationale",
            cp.adjustment_narrative[:80],
        ])

    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # Risk indicator based on band
    band_risk_map: dict[str, str] = {
        "LOW": "MODERATE",
        "MODERATE": "ELEVATED",
        "ELEVATED": "HIGH",
        "HIGH": "HIGH",
        "VERY_HIGH": "CRITICAL",
    }
    risk_level = band_risk_map.get(cp.band.value, "ELEVATED")
    band_para: Any = doc.add_paragraph(style="DOBody")
    band_run: Any = band_para.add_run(
        f"Claim probability: {cp.band.value}"
    )
    band_run.bold = True
    add_risk_indicator(band_para, risk_level, ds)


# ---------------------------------------------------------------------------
# Tower Position Recommendation Detail
# ---------------------------------------------------------------------------


def _render_tower_recommendation(
    doc: Any, scoring: ScoringResult, ds: DesignSystem
) -> None:
    """Render tower position recommendation detail."""
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Tower Position Recommendation")

    tr = scoring.tower_recommendation
    if tr is None:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("Tower recommendation not available.")
        return

    # Summary
    rows: list[list[str]] = [
        ["Recommended Position", tr.recommended_position.value],
    ]
    if tr.minimum_attachment:
        rows.append(["Minimum Attachment", tr.minimum_attachment])
    if tr.side_a_assessment:
        rows.append(["Side A/DIC Assessment", tr.side_a_assessment[:80]])

    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # Layer detail
    if tr.layers:
        layer_headers = [
            "Position", "Risk Assessment", "Premium Guidance", "Attachment",
        ]
        layer_rows: list[list[str]] = []
        for layer in tr.layers:
            layer_rows.append([
                layer.position.value,
                layer.risk_assessment[:50] if layer.risk_assessment else "N/A",
                layer.premium_guidance[:30] if layer.premium_guidance else "N/A",
                layer.attachment_range or "N/A",
            ])
        add_styled_table(doc, layer_headers, layer_rows, ds)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def render_scoring_detail(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render scoring detail sections.

    Covers per-factor detail with contributing checks, pattern detection
    results with trigger conditions, allegation theory mapping, claim
    probability estimation, and tower position recommendation.

    Phase 60-02: Receives context dict from build_template_context().
    Uses context["_state"] escape hatch for benchmark data.

    Args:
        doc: The python-docx Document.
        context: Shared context dict from build_template_context().
        ds: Design system for styling.
    """
    scoring = _get_scoring(context)
    if scoring is None:
        return

    # TODO(phase-60): move benchmark to context_builders
    state = context.get("_state")
    benchmark = state.benchmark if state is not None else None
    signal_results = _get_signal_results(context)
    _render_factor_detail(doc, scoring, benchmark, ds)
    _render_pattern_detection(doc, scoring, signal_results, ds)
    _render_allegation_mapping(doc, scoring, ds)
    _render_claim_probability(doc, scoring, ds)
    _render_tower_recommendation(doc, scoring, ds)


__all__ = ["render_scoring_detail"]
