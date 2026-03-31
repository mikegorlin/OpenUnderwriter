"""Adversarial critique runner -- orchestrates all 4 check types + LLM narratives.

Phase 110-02: Called as Step 18 in ScoreStage pipeline, after deep-dive triggers.
Loads adversarial_rules.yaml, runs all 4 detection functions, enriches top caveats
with LLM-generated narratives, and returns AdversarialResult.

Follows the same graceful degradation pattern as _pattern_runner.py:
- Individual check failures are caught and logged
- YAML missing -> returns None
- LLM failure -> template-based explanations preserved

CRITICAL: Never modifies ScoringResult, quality_score, tier, severity, or patterns.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from do_uw.models.adversarial import AdversarialResult, Caveat
from do_uw.stages.score.adversarial_engine import (
    check_contradictions,
    check_data_completeness,
    check_false_negatives,
    check_false_positives,
)

__all__ = ["generate_caveat_narratives", "run_adversarial_critique"]

logger = logging.getLogger(__name__)

# Path to adversarial rules YAML
_RULES_PATH = (
    Path(__file__).parent.parent.parent / "brain" / "framework" / "adversarial_rules.yaml"
)

# Severity ordering for priority sorting
_SEVERITY_ORDER: dict[str, int] = {
    "warning": 2,
    "caution": 1,
    "info": 0,
}

# Maximum caveats to send to LLM for narrative generation
_MAX_LLM_CAVEATS = 8


def _load_adversarial_rules() -> dict[str, Any] | None:
    """Load adversarial rules from YAML. Returns None if missing."""
    if not _RULES_PATH.exists():
        logger.warning("Adversarial rules YAML not found: %s", _RULES_PATH)
        return None

    with open(_RULES_PATH) as f:
        data = yaml.safe_load(f)

    if not data:
        return None

    return data


def run_adversarial_critique(
    state: Any,
    signal_results: dict[str, Any],
    *,
    scoring_result: Any | None = None,
) -> AdversarialResult | None:
    """Run all 4 adversarial check types and return aggregated result.

    Loads rules from YAML, calls each check function in try/except,
    aggregates caveats, optionally enriches with LLM narratives.

    Args:
        state: AnalysisState with company, extracted, analysis data.
        signal_results: Signal evaluation results dict.
        scoring_result: ScoringResult for context (read-only, never modified).

    Returns:
        AdversarialResult with all caveats, or None if rules YAML missing.
    """
    rules = _load_adversarial_rules()
    if rules is None:
        return None

    all_caveats: list[Caveat] = []

    # Run each check type independently
    check_fns = [
        ("false_positive", check_false_positives, rules.get("false_positive_rules", [])),
        ("false_negative", check_false_negatives, rules.get("false_negative_rules", [])),
        ("contradiction", check_contradictions, rules.get("contradiction_rules", [])),
        ("data_completeness", check_data_completeness, rules.get("data_completeness_rules", [])),
    ]

    for check_name, check_fn, check_rules in check_fns:
        try:
            if check_name in ("false_positive", "false_negative"):
                caveats = check_fn(signal_results, check_rules, state=state)
            else:
                caveats = check_fn(signal_results, check_rules)
            all_caveats.extend(caveats)
        except Exception:
            logger.warning(
                "Adversarial check %s failed; continuing",
                check_name,
                exc_info=True,
            )

    # Enrich with LLM narratives (graceful degradation)
    summary = ""
    try:
        enriched_caveats = generate_caveat_narratives(all_caveats, state)
        all_caveats = enriched_caveats
    except Exception:
        logger.warning("LLM narrative generation failed; using templates", exc_info=True)

    # Compute counts
    fp_count = sum(1 for c in all_caveats if c.caveat_type == "false_positive")
    fn_count = sum(1 for c in all_caveats if c.caveat_type == "false_negative")
    ct_count = sum(1 for c in all_caveats if c.caveat_type == "contradiction")
    dc_count = sum(1 for c in all_caveats if c.caveat_type == "data_completeness")

    # Build summary
    if all_caveats:
        parts = []
        if fp_count:
            parts.append(f"{fp_count} possible false positive(s)")
        if fn_count:
            parts.append(f"{fn_count} potential blind spot(s)")
        if ct_count:
            parts.append(f"{ct_count} contradictory signal(s)")
        if dc_count:
            parts.append(f"{dc_count} data gap(s)")
        summary = f"Adversarial review found {len(all_caveats)} caveats: {', '.join(parts)}."
    else:
        summary = "No adversarial findings -- assessment appears consistent and complete."

    return AdversarialResult(
        caveats=all_caveats,
        false_positive_count=fp_count,
        false_negative_count=fn_count,
        contradiction_count=ct_count,
        completeness_issues=dc_count,
        summary=summary,
        computed_at=datetime.now(timezone.utc),
    )


def generate_caveat_narratives(
    caveats: list[Caveat],
    state: Any,
) -> list[Caveat]:
    """Enrich top caveats with LLM-generated explanations.

    Selects top 8 caveats by severity (warning > caution > info) then
    confidence descending. Sends a single batched prompt to LLM for
    all selected caveats. On LLM failure, preserves template explanations.

    Args:
        caveats: Caveats with template-based explanations.
        state: AnalysisState for company context.

    Returns:
        Same caveats with LLM-enriched explanations where available.
    """
    if not caveats:
        return caveats

    # Sort by severity (descending) then confidence (descending)
    sorted_caveats = sorted(
        caveats,
        key=lambda c: (_SEVERITY_ORDER.get(c.severity, 0), c.confidence),
        reverse=True,
    )

    # Select top N for LLM enrichment
    llm_batch = sorted_caveats[:_MAX_LLM_CAVEATS]
    llm_batch_set = set(id(c) for c in llm_batch)

    # Try LLM enrichment
    try:
        response = _call_llm_for_narratives(llm_batch, state)
        explanations = response.get("explanations", [])

        for i, caveat in enumerate(llm_batch):
            if i < len(explanations) and explanations[i]:
                caveat.explanation = explanations[i]
                caveat.narrative_source = "llm"
    except Exception:
        logger.warning("LLM narrative call failed; keeping template explanations", exc_info=True)

    return caveats


def _call_llm_for_narratives(
    caveats: list[Caveat],
    state: Any,
) -> dict[str, Any]:
    """Call LLM to generate narrative explanations for caveats.

    This is a stub that returns empty results. In production, this would
    call the DeepSeek API with a batched prompt. The runner's try/except
    ensures graceful degradation when LLM is unavailable.

    Args:
        caveats: Caveats to generate narratives for.
        state: AnalysisState for company context.

    Returns:
        Dict with 'explanations' list and 'summary' string.
    """
    # Production implementation would call DeepSeek API here.
    # For now, return empty to preserve template explanations.
    return {"explanations": [], "summary": ""}
