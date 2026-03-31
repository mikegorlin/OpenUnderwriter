"""Section 7 per-factor scoring detail: collapsible 'What Was Found' and
'Underwriting Commentary' sections for each scoring factor (F.1-F.10).

Split from sect7_scoring_detail.py (Phase 116-05) to provide deep factor
drill-down with evidence citations and brain YAML D&O context.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.scoring import FactorScore, ScoringResult
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
)
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import add_styled_table


def build_factor_detail_context(
    scoring: ScoringResult,
    signal_results: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build per-factor detail data for templates.

    For each factor, extracts evidence, source citations, triggered rules,
    and D&O context from contributing brain signals.

    Returns a list of dicts suitable for template rendering.
    """
    factor_details: list[dict[str, Any]] = []

    for fs in scoring.factor_scores:
        detail = _build_single_factor_detail(fs, signal_results)
        factor_details.append(detail)

    return factor_details


def _build_single_factor_detail(
    fs: FactorScore,
    signal_results: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build detail dict for a single FactorScore."""
    # Evidence: join the factor's evidence list
    evidence = "; ".join(fs.evidence) if fs.evidence else ""

    # Source citations from contributing signals
    sources: list[str] = []
    for contrib in fs.signal_contributions:
        sig_id = contrib.get("signal_id", "")
        if not sig_id:
            continue
        sig = safe_get_result(signal_results, sig_id)
        if sig and sig.source:
            sources.append(f"{sig_id}: {sig.source}")

    # Triggered rules
    rules = list(fs.rules_triggered) if fs.rules_triggered else []

    # D&O context from contributing signals
    do_contexts: list[str] = []
    for contrib in fs.signal_contributions:
        sig_id = contrib.get("signal_id", "")
        if not sig_id:
            continue
        sig = safe_get_result(signal_results, sig_id)
        if sig and sig.do_context:
            do_contexts.append(sig.do_context)

    # Strip generic boilerplate from each do_context before joining
    _BOILERPLATE = "Monitor for deterioration"
    cleaned_contexts = []
    for dc in do_contexts:
        if _BOILERPLATE in dc:
            dc = dc.replace(
                "Monitor for deterioration \u2014 trend direction and peer comparison inform the D&O risk assessment.",
                "",
            ).strip()
        if dc:
            cleaned_contexts.append(dc)
    do_context = "\n\n".join(cleaned_contexts) if cleaned_contexts else ""

    # Signal attribution for contributing signals table
    signal_attribution: dict[str, Any] = {}
    if hasattr(fs, "scoring_method") and fs.scoring_method == "signal_driven":
        sorted_contribs = sorted(
            fs.signal_contributions,
            key=lambda c: c.get("contribution", 0.0),
            reverse=True,
        )
        # Enrich top contributions with status from signal_results
        enriched_top: list[dict[str, Any]] = []
        for contrib in sorted_contribs[:5]:
            sig_id = contrib.get("signal_id", "")
            sig_view = safe_get_result(signal_results, sig_id) if sig_id else None
            enriched_top.append({
                "signal_id": sig_id,
                "contribution": contrib.get("contribution", 0.0),
                "status": sig_view.status if sig_view else "",
            })
        coverage_pct = round(fs.signal_coverage * 100) if hasattr(fs, "signal_coverage") else 0
        signal_attribution = {
            "scoring_method": "signal_driven",
            "top_3_signals": enriched_top,
            "full_signal_count": len(fs.signal_contributions),
            "confidence_pct": f"{coverage_pct}%",
        }

    # Sub-components for display
    sub_comps: list[dict[str, str]] = []
    if fs.sub_components:
        for comp_name, comp_val in fs.sub_components.items():
            sub_comps.append({
                "name": comp_name.replace("_", " ").title(),
                "value": f"{comp_val:.1f}",
            })

    return {
        "factor_id": fs.factor_id,
        "factor_name": fs.factor_name,
        "score": f"{fs.points_deducted:.0f}/{fs.max_points}",
        "points_deducted": fs.points_deducted,
        "max_points": fs.max_points,
        "evidence": evidence,
        "sources": "; ".join(sources) if sources else "",
        "rules": rules,
        "do_context": do_context,
        "signal_attribution": signal_attribution,
        "sub_components": sub_comps,
    }


def render_factor_details(
    doc: Any,
    scoring: ScoringResult,
    signal_results: dict[str, Any] | None,
    ds: DesignSystem,
) -> None:
    """Render per-factor scoring detail for Word output.

    For each factor, renders:
    - Header: F.{id} -- {name} ({deducted}/{max})
    - What Was Found: evidence citations + sources
    - Underwriting Commentary: D&O context from brain signal do_context

    Args:
        doc: The python-docx Document.
        scoring: Complete scoring result with factor_scores.
        signal_results: Signal evaluation results for do_context extraction.
        ds: Design system for styling.
    """
    heading: Any = doc.add_paragraph(style="DOHeading3")
    heading.add_run("Per-Factor Detail")

    factor_details = build_factor_detail_context(scoring, signal_results)
    active = [f for f in factor_details if f["points_deducted"] > 0]

    if not active:
        para: Any = doc.add_paragraph(style="DOBody")
        para.add_run("No factors with risk deductions.")
        return

    for detail in active:
        _render_single_factor_word(doc, detail, ds)


def _render_single_factor_word(
    doc: Any,
    detail: dict[str, Any],
    ds: DesignSystem,
) -> None:
    """Render a single factor's detail in Word format."""
    # Factor header
    sub_heading: Any = doc.add_paragraph(style="DOBody")
    run: Any = sub_heading.add_run(
        f"{detail['factor_id']} -- {detail['factor_name']} "
        f"({detail['score']})"
    )
    run.bold = True
    run.font.size = ds.size_body

    # What Was Found
    if detail["evidence"]:
        found_heading: Any = doc.add_paragraph(style="DOBody")
        found_run: Any = found_heading.add_run("What Was Found")
        found_run.bold = True
        found_run.font.size = ds.size_small

        evidence_para: Any = doc.add_paragraph(style="DOBody")
        evidence_para.add_run(detail["evidence"])

        if detail["sources"]:
            src_para: Any = doc.add_paragraph(style="DOBody")
            src_run: Any = src_para.add_run(f"Sources: {detail['sources']}")
            src_run.italic = True
            src_run.font.size = ds.size_small

    # Rules triggered
    if detail["rules"]:
        rules_para: Any = doc.add_paragraph(style="DOBody")
        rules_run: Any = rules_para.add_run(
            f"Rules triggered: {', '.join(detail['rules'])}"
        )
        rules_run.font.size = ds.size_small

    # Underwriting Commentary (from brain signal do_context)
    if detail["do_context"]:
        commentary_heading: Any = doc.add_paragraph(style="DOBody")
        commentary_run: Any = commentary_heading.add_run(
            "Underwriting Commentary"
        )
        commentary_run.bold = True
        commentary_run.font.size = ds.size_small

        commentary_para: Any = doc.add_paragraph(style="DOBody")
        commentary_para.add_run(detail["do_context"])


__all__ = ["build_factor_detail_context", "render_factor_details"]
