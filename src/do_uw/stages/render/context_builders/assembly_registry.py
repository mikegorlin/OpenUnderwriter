"""Registry pattern for HTML context assembly (Phase 128-01).

Provides build_html_context as the main entry point, dispatching to
registered builder functions. Each domain module registers itself
via the @register_builder decorator.

Exports:
    build_html_context, register_builder, _risk_class, _BUILDERS
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Type for builder functions: (state, context, chart_dir) -> None (mutates context)
BuilderFn = Callable[[AnalysisState, dict[str, Any], Path | None], None]

# Module-level registry of builder functions
_BUILDERS: list[BuilderFn] = []


def register_builder(fn: BuilderFn) -> BuilderFn:
    """Decorator that registers a builder function in the assembly pipeline."""
    _BUILDERS.append(fn)
    return fn


# Zone-to-status mapping for distress indicator display
_ZONE_STATUS_MAP: dict[str, str] = {
    "distress": "TRIGGERED",
    "danger": "TRIGGERED",
    "grey": "ELEVATED",
    "gray": "ELEVATED",
    "warning": "ELEVATED",
    "safe": "CLEAR",
    "strong": "CLEAR",
    "moderate": "INFO",
    "weak": "TRIGGERED",
    "manipulation likely": "TRIGGERED",
    "manipulation unlikely": "CLEAR",
}


def _risk_class(zone: str) -> str:
    """Jinja2 filter: map distress zone label to CSS risk class."""
    if not zone:
        return ""
    return _ZONE_STATUS_MAP.get(zone.strip().lower(), "")


def _should_suppress_insolvency_crf(
    state: AnalysisState,
    finding: Any,
) -> bool:
    """Suppress insolvency CRF finding when financial health is clearly adequate.

    Delegates to the canonical should_suppress_insolvency() in red_flag_gates.py.
    Only applies to findings with insolvency/going-concern/distress keywords.
    """
    from do_uw.stages.score.red_flag_gates import should_suppress_insolvency

    narrative = getattr(finding, "evidence_narrative", "") or ""
    impact = getattr(finding, "scoring_impact", "") or ""
    # Only target insolvency-related findings
    lower = (narrative + " " + impact).lower()
    if "insolvency" not in lower and "going concern" not in lower and "distress" not in lower:
        return False

    return should_suppress_insolvency(state)


def build_html_context(
    state: AnalysisState,
    chart_dir: Path | None = None,
) -> dict[str, Any]:
    """Build template context for HTML rendering.

    Reuses build_template_context from md_renderer as base, then dispatches
    to all registered builder functions for HTML-specific context additions.
    """
    from do_uw.stages.render.md_renderer import build_template_context

    context = build_template_context(state, chart_dir)

    # Compute canonical metrics ONCE for all builders
    try:
        from do_uw.stages.render.canonical_metrics import build_canonical_metrics

        canonical = build_canonical_metrics(state)
        context["_canonical"] = canonical.model_dump()
    except Exception:
        logger.warning(
            "Canonical metrics computation failed, builders will use legacy paths",
            exc_info=True,
        )
        canonical = None
        context["_canonical"] = {}
    context["_canonical_obj"] = canonical  # CanonicalMetrics object for builders

    # Overlay canonical values onto company and exec_summary contexts
    # (these were built by build_template_context() before canonical existed)
    if canonical:
        cd = canonical.model_dump()
        if "company" in context and isinstance(context["company"], dict):
            for key in ("exchange", "employees", "market_cap", "revenue"):
                if key in cd and cd[key] and cd[key].get("formatted"):
                    context["company"][key] = cd[key]["formatted"]
        if "executive_summary" in context and isinstance(context["executive_summary"], dict):
            for key in ("market_cap", "revenue", "stock_price"):
                if key in cd and cd[key] and cd[key].get("formatted"):
                    context["executive_summary"][key] = cd[key]["formatted"]

    for builder in _BUILDERS:
        try:
            builder(state, context, chart_dir)
        except Exception:
            logger.warning(
                "Assembly builder %s failed",
                getattr(builder, "__name__", repr(builder)),
                exc_info=True,
            )

    # Inject stage failure banners (RES-03)
    from do_uw.stages.render.context_builders.stage_failure_banners import (
        inject_stage_failure_banners,
    )

    inject_stage_failure_banners(state, context)

    # Propagate stage banners into uw_analysis sub-dicts (RES-03 gap closure)
    _propagate_banners_to_uw_analysis(context)

    # Pipeline status for audit section (RES-06 gap closure)
    from do_uw.stages.render.context_builders.pipeline_status import (
        build_pipeline_status_context,
    )

    context["pipeline_status"] = build_pipeline_status_context(state)

    # Post-process: strip "Monitor for deterioration" boilerplate from all do_context fields
    _strip_do_context_boilerplate(context)

    # Auto-answer screening questions after all context (incl. _state) is assembled
    _auto_answer_screening_questions(context)

    return context


# Maps top-level context keys (where banners are injected) to uw_analysis sub-keys
_TOP_TO_BETA_MAP: dict[str, str] = {
    "financials": "fin",
    "governance": "gov",
    "litigation": "lit_detail",
    "market": "market_ext",
    "scoring": "score_detail",
}


def _propagate_banners_to_uw_analysis(context: dict[str, Any]) -> None:
    """Copy _stage_banner from top-level context keys into uw_analysis sub-dicts.

    inject_stage_failure_banners() writes banners to top-level keys like
    context['financials']['_stage_banner'], but report templates read from
    context['uw_analysis']['fin']. This bridges the gap.

    Also handles the case where top-level keys are None (no data extracted)
    but banners exist because inject_stage_failure_banners created dicts
    OR because we can read the banner text from the state embedded in context.
    """
    from do_uw.stages.render.context_builders.stage_failure_banners import (
        STAGE_SECTION_MAP,
    )

    br = context.get("uw_analysis")
    if not br or not isinstance(br, dict):
        return

    # First pass: copy from top-level dict keys that have _stage_banner
    for top_key, beta_key in _TOP_TO_BETA_MAP.items():
        top_section = context.get(top_key)
        if isinstance(top_section, dict) and "_stage_banner" in top_section:
            beta_sub = br.get(beta_key)
            if isinstance(beta_sub, dict):
                beta_sub["_stage_banner"] = top_section["_stage_banner"]
            elif beta_sub is None:
                br[beta_key] = {"_stage_banner": top_section["_stage_banner"]}

    # Second pass: for failed stages, inject banners directly into uw_analysis
    # sub-dicts even when top-level keys are None (no data extracted)
    state = context.get("_state")
    if state is None:
        return
    stages = getattr(state, "stages", None)
    if not stages:
        return
    from do_uw.models.common import StageStatus

    for stage_name, result in stages.items():
        if result.status != StageStatus.FAILED:
            continue
        banner_text = (
            f"Incomplete -- {stage_name.upper()} stage did not complete: "
            f"{result.error or 'unknown error'}"
        )
        affected_sections = STAGE_SECTION_MAP.get(stage_name, [])
        for section_key in affected_sections:
            beta_key = _TOP_TO_BETA_MAP.get(section_key)
            if not beta_key:
                continue
            beta_sub = br.get(beta_key)
            if isinstance(beta_sub, dict) and "_stage_banner" not in beta_sub:
                beta_sub["_stage_banner"] = banner_text
            elif beta_sub is None:
                br[beta_key] = {"_stage_banner": banner_text}


def _auto_answer_screening_questions(context: dict[str, Any]) -> None:
    """Auto-answer risk card screening questions using full render context."""
    lit = context.get("litigation")
    if not lit or not isinstance(lit, dict):
        return
    questions = lit.get("risk_card_screening_questions", [])
    if not questions:
        return
    try:
        from do_uw.stages.render.context_builders.screening_answers import (
            answer_screening_questions,
        )
        lit["risk_card_screening_questions"] = answer_screening_questions(
            questions, context,
        )
    except Exception:
        logger.debug("Screening question auto-answer failed", exc_info=True)


def _strip_do_context_boilerplate(obj: Any, parent_is_do_context: bool = False) -> None:
    """Recursively strip brain YAML boilerplate from do_context values."""
    from do_uw.stages.render.formatters import clean_do_context

    if isinstance(obj, dict):
        for key in obj:
            val = obj[key]
            is_do_key = "do_context" in key if isinstance(key, str) else False
            if isinstance(val, str) and (is_do_key or parent_is_do_context):
                obj[key] = clean_do_context(val)
            elif isinstance(val, (dict, list)):
                _strip_do_context_boilerplate(val, parent_is_do_context=is_do_key)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                _strip_do_context_boilerplate(item, parent_is_do_context)
            elif isinstance(item, str) and parent_is_do_context:
                # Can't mutate list items in-place easily; skip
                pass


# Import domain modules to trigger their @register_builder decorations.
# Order matters: html_extras first (base context), then signals, then dossier.
import do_uw.stages.render.context_builders.assembly_html_extras  # noqa: E402, F401
import do_uw.stages.render.context_builders.assembly_signals  # noqa: E402, F401
import do_uw.stages.render.context_builders.assembly_dossier  # noqa: E402, F401
import do_uw.stages.render.context_builders.assembly_commentary  # noqa: E402, F401
import do_uw.stages.render.context_builders.assembly_uw_analysis  # noqa: E402, F401
import do_uw.stages.render.context_builders.assembly_llm_review  # noqa: E402, F401


__all__ = ["_risk_class", "build_html_context", "register_builder", "_BUILDERS"]
