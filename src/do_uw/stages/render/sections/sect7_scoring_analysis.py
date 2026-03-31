"""Section 7 analysis composites: forensic composites, temporal signals,
and NLP filing analysis for Word renderer.

Split from sect7_scoring.py for the 500-line limit.
Called after scoring detail to render analysis-layer composite signals.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import add_styled_table

# ---------------------------------------------------------------------------
# Forensic Composite Scores (FIS, RQS, CFQS)
# ---------------------------------------------------------------------------


def render_forensic_composites(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render FIS, RQS, CFQS forensic composite scores."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Forensic Composite Scores")

    # TODO(phase-60): use context["analysis"] when available
    state = context.get("_state")
    if state is None or state.analysis is None or state.analysis.forensic_composites is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Forensic composite scores not available.")
        return

    fc = state.analysis.forensic_composites
    rows: list[list[str]] = []

    for key, label in [
        ("fis", "Financial Integrity Score (FIS)"),
        ("rqs", "Reporting Quality Score (RQS)"),
        ("cfqs", "Cash Flow Quality Score (CFQS)"),
    ]:
        data = fc.get(key) or fc.get(key.upper())
        if data is None:
            rows.append([label, "N/A", "Not available"])
            continue

        if isinstance(data, dict):
            score = data.get("score", data.get("value", "N/A"))
            interp = data.get("interpretation", data.get("label", "N/A"))
            score_str = f"{score:.0f}" if isinstance(score, (int, float)) else str(score)
            rows.append([label, score_str, str(interp)])
        else:
            score_str = f"{data:.0f}" if isinstance(data, (int, float)) else str(data)
            rows.append([label, score_str, "N/A"])

    add_styled_table(doc, ["Composite", "Score", "Interpretation"], rows, ds)


# ---------------------------------------------------------------------------
# Temporal Signals
# ---------------------------------------------------------------------------


def render_temporal_signals(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render temporal trend signals table."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Temporal Signals")

    # TODO(phase-60): use context["analysis"] when available
    state = context.get("_state")
    if state is None or state.analysis is None or state.analysis.temporal_signals is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("No temporal signals detected.")
        return

    ts = state.analysis.temporal_signals
    signals = ts.get("signals", ts.get("trends", []))

    # Handle flat structure
    if not signals:
        if "direction" in ts or "type" in ts:
            signals = [ts]
        else:
            body = doc.add_paragraph(style="DOBody")
            body.add_run("No temporal signals detected.")
            return

    rows: list[list[str]] = []
    for sig in signals:
        if not isinstance(sig, dict):
            continue
        sig_type = str(sig.get("type", sig.get("signal_type", "Unknown")))
        direction = str(sig.get("direction", sig.get("trend", "N/A")))
        magnitude = str(sig.get("magnitude", sig.get("change_pct", "N/A")))
        description = str(sig.get("description", sig.get("narrative", "")))
        rows.append([sig_type, direction, magnitude, description])

    if not rows:
        body = doc.add_paragraph(style="DOBody")
        body.add_run("No temporal signals detected.")
        return

    add_styled_table(
        doc,
        ["Type", "Direction", "Magnitude", "Description"],
        rows,
        ds,
    )


# ---------------------------------------------------------------------------
# NLP Filing Analysis
# ---------------------------------------------------------------------------


def render_nlp_signals(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render NLP filing analysis: readability, tone, risk language density."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("NLP Filing Analysis")

    # TODO(phase-60): use context["analysis"] when available
    state = context.get("_state")
    if state is None or state.analysis is None or state.analysis.nlp_signals is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("NLP filing analysis not available.")
        return

    nlp = state.analysis.nlp_signals
    readability = nlp.get("readability_score", nlp.get("readability", "N/A"))
    tone = nlp.get("tone_assessment", nlp.get("tone", "N/A"))
    risk_density = nlp.get("risk_language_density", nlp.get("risk_density", "N/A"))

    readability_str = f"{readability:.1f}" if isinstance(readability, (int, float)) else str(readability)
    risk_str = f"{risk_density:.2f}" if isinstance(risk_density, (int, float)) else str(risk_density)

    rows: list[list[str]] = [
        ["Readability Score", readability_str],
        ["Tone Assessment", str(tone)],
        ["Risk Language Density", risk_str],
    ]

    add_styled_table(doc, ["Metric", "Value"], rows, ds)


# ---------------------------------------------------------------------------
# Executive Risk Profile
# ---------------------------------------------------------------------------


def render_executive_risk(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render executive/board aggregate risk profile."""
    heading: Any = doc.add_paragraph(style="DOHeading2")
    heading.add_run("Executive Risk Profile")

    # TODO(phase-60): use context["analysis"] when available
    state = context.get("_state")
    if state is None or state.analysis is None or state.analysis.executive_risk is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Executive risk profile not available.")
        return

    er = state.analysis.executive_risk
    weighted_score = er.get("weighted_score", er.get("overall_score", "N/A"))
    risk_level = er.get("risk_level", er.get("assessment", "N/A"))
    findings = er.get("findings", er.get("key_findings", []))

    score_str = f"{weighted_score:.0f}" if isinstance(weighted_score, (int, float)) else str(weighted_score)

    rows: list[list[str]] = [
        ["Weighted Score", score_str],
        ["Risk Level", str(risk_level)],
    ]
    add_styled_table(doc, ["Metric", "Value"], rows, ds)

    # Findings list
    if isinstance(findings, list) and findings:
        for finding in findings[:10]:
            fp: Any = doc.add_paragraph(style="DOBody")
            fp.add_run(f"- {finding}")


__all__ = [
    "render_executive_risk",
    "render_forensic_composites",
    "render_nlp_signals",
    "render_temporal_signals",
]
