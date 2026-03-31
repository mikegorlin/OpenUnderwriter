"""Deep-dive trigger runner: evaluates conditional investigation triggers.

Phase 110-01: Conditional deep-dive triggers that fire when compound
conditions are met. Called as Step 17 in ScoreStage, after pattern engines.

Each trigger uses all_of AND logic to check signal statuses. When all
conditions are satisfied, the trigger fires and produces an investigation
prompt for the underwriter.

NOTE on acquisition loops: Per CONTEXT.md, triggers CAN request additional
acquisition. For v7.0, we implement trigger detection and investigation
prompt generation only. The additional_acquisition field in YAML logs what
data WOULD be requested. Actual acquisition loop is deferred to a future
iteration -- the UW investigation prompts deliver 80% of the value without
the pipeline loop complexity.

Follows _pattern_runner.py pattern: sequential evaluation with per-trigger
try/except for graceful degradation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from do_uw.models.deepdive import DeepDiveResult, DeepDiveTriggerResult

__all__ = ["run_deepdive_triggers"]

logger = logging.getLogger(__name__)

# Path to deep-dive triggers YAML
_TRIGGERS_PATH = (
    Path(__file__).parent.parent.parent
    / "brain"
    / "framework"
    / "deepdive_triggers.yaml"
)


def run_deepdive_triggers(
    state: Any,
    signal_results: dict[str, Any],
    *,
    hae_result: Any | None = None,
) -> DeepDiveResult | None:
    """Run all deep-dive triggers against signal results.

    Each trigger is evaluated independently. Individual trigger failures
    are caught and logged; remaining triggers continue.

    Args:
        state: AnalysisState with company, extracted data.
        signal_results: Signal evaluation results dict.
        hae_result: Optional ScoringLensResult from H/A/E scoring.

    Returns:
        DeepDiveResult with all evaluated triggers, or None if YAML
        is missing or no triggers are defined.
    """
    triggers_data = _load_triggers()
    if not triggers_data:
        return None

    results: list[DeepDiveTriggerResult] = []
    fired_count = 0

    for trigger in triggers_data:
        try:
            result = _evaluate_trigger(trigger, signal_results)
            results.append(result)
            if result.fired:
                fired_count += 1
                logger.info(
                    "Deep-dive trigger fired: %s (%s)",
                    result.trigger_id,
                    result.trigger_name,
                )
                # Log what additional acquisition would be requested
                additional_acq = trigger.get("additional_acquisition", [])
                if additional_acq:
                    logger.info(
                        "  Would request additional acquisition: %s",
                        ", ".join(additional_acq),
                    )
        except Exception as exc:
            logger.warning(
                "Deep-dive trigger %s failed: %s",
                trigger.get("id", "unknown"),
                str(exc),
                exc_info=True,
            )
            # Create a non-fired result for the failed trigger
            results.append(
                DeepDiveTriggerResult(
                    trigger_id=trigger.get("id", "unknown"),
                    trigger_name=trigger.get("name", "Unknown"),
                    description=f"Evaluation failed: {str(exc)[:100]}",
                    fired=False,
                )
            )

    return DeepDiveResult(
        triggers_evaluated=len(results),
        triggers_fired=fired_count,
        results=results,
        computed_at=datetime.now(timezone.utc),
    )


def _evaluate_trigger(
    trigger: dict[str, Any],
    signal_results: dict[str, Any],
) -> DeepDiveTriggerResult:
    """Evaluate a single deep-dive trigger.

    Uses all_of AND logic: ALL conditions must be satisfied for the
    trigger to fire. Each condition specifies a signal ID and expected
    status.

    Args:
        trigger: Trigger definition dict from YAML.
        signal_results: Signal evaluation results.

    Returns:
        DeepDiveTriggerResult indicating whether trigger fired.
    """
    trigger_id = trigger.get("id", "unknown")
    trigger_name = trigger.get("name", "Unknown")
    description = trigger.get("description", "")
    uw_prompt = trigger.get("uw_investigation_prompt", "")
    additional_signals = trigger.get("additional_signals", [])
    rap_dimensions = trigger.get("rap_dimensions", [])

    conditions = trigger.get("trigger_conditions", {})
    all_of = conditions.get("all_of", [])

    if not all_of:
        return DeepDiveTriggerResult(
            trigger_id=trigger_id,
            trigger_name=trigger_name,
            description=description,
            fired=False,
            uw_investigation_prompt=uw_prompt,
            rap_dimensions=rap_dimensions,
        )

    matched: list[str] = []
    all_met = True

    for condition in all_of:
        sig_id = condition.get("signal", "")
        expected_status = condition.get("status", "TRIGGERED")

        entry = signal_results.get(sig_id)
        if entry is None:
            all_met = False
            continue

        actual_status = entry.get("status", "")

        # Match TRIGGERED against both TRIGGERED and RED/YELLOW (legacy compat)
        if expected_status == "TRIGGERED":
            if actual_status in ("TRIGGERED", "RED", "YELLOW"):
                matched.append(f"{sig_id}={actual_status}")
            else:
                all_met = False
        else:
            if actual_status == expected_status:
                matched.append(f"{sig_id}={actual_status}")
            else:
                all_met = False

    return DeepDiveTriggerResult(
        trigger_id=trigger_id,
        trigger_name=trigger_name,
        description=description,
        fired=all_met and len(matched) == len(all_of),
        matched_conditions=matched,
        additional_signals=additional_signals,
        uw_investigation_prompt=uw_prompt if all_met else "",
        rap_dimensions=rap_dimensions,
    )


def _load_triggers() -> list[dict[str, Any]]:
    """Load deep-dive triggers from YAML.

    Returns empty list if file is missing or malformed.
    """
    if not _TRIGGERS_PATH.exists():
        logger.warning("Deep-dive triggers YAML not found: %s", _TRIGGERS_PATH)
        return []

    try:
        with open(_TRIGGERS_PATH) as f:
            data = yaml.safe_load(f)

        if not data or "triggers" not in data:
            logger.warning("Deep-dive triggers YAML has no 'triggers' key")
            return []

        triggers = data["triggers"]
        if not isinstance(triggers, list):
            logger.warning("Deep-dive triggers is not a list")
            return []

        return triggers
    except Exception as exc:
        logger.warning(
            "Failed to load deep-dive triggers: %s", str(exc), exc_info=True
        )
        return []
