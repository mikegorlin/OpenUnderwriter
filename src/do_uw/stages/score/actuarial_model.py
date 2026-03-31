"""Actuarial expected loss computation.

Core frequency-severity model that turns risk scoring outputs
(filing probability from inherent_risk.py + severity scenarios
from severity_model.py) into dollar expected loss estimates.

Formula:
    Expected indemnity = filing_probability * median_severity
    Expected defense  = expected_indemnity * defense_cost_pct
    Total expected    = expected_indemnity + expected_defense

All parameters are read from actuarial.json config -- nothing hardcoded.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.models.scoring_output import (
    ExpectedLoss,
    ScenarioLoss,
    SeverityScenarios,
)

logger = logging.getLogger(__name__)

_SCENARIO_LABELS: dict[int, str] = {
    25: "favorable",
    50: "median",
    75: "adverse",
    95: "catastrophic",
}

_SCENARIO_PERCENTILES = [25, 50, 75, 95]


def _get_scenario_amount(
    scenarios: SeverityScenarios,
    percentile: int,
) -> float | None:
    """Extract settlement_estimate at a given percentile.

    Args:
        scenarios: SeverityScenarios with scenario list.
        percentile: Target percentile (25, 50, 75, or 95).

    Returns:
        Settlement estimate at that percentile, or None if not found.
    """
    for scenario in scenarios.scenarios:
        if scenario.percentile == percentile:
            return scenario.settlement_estimate
    return None


def _get_defense_cost_pct(
    case_type: str,
    actuarial_config: dict[str, Any],
) -> float:
    """Look up defense cost percentage for a case type from config.

    Falls back to 'default' key, then 0.20 if config is missing.

    Args:
        case_type: Case type key (e.g. 'standard_sca', 'complex_sca').
        actuarial_config: Full actuarial.json config dict.

    Returns:
        Defense cost as a fraction (e.g. 0.20 for 20%).
    """
    defense_factors = actuarial_config.get("defense_cost_factors", {})
    if not isinstance(defense_factors, dict):
        return 0.20

    factors = cast(dict[str, Any], defense_factors)

    # Try exact case type match
    value = factors.get(case_type)
    if value is not None and isinstance(value, (int, float)):
        return float(value)

    # Fall back to default
    default_value = factors.get("default", 0.20)
    if isinstance(default_value, (int, float)):
        return float(default_value)

    return 0.20


def _compute_scenario_losses(
    filing_probability: float,
    scenarios: SeverityScenarios,
    defense_cost_pct: float,
) -> list[ScenarioLoss]:
    """Compute expected loss at each percentile scenario.

    Args:
        filing_probability: Probability as a decimal (e.g. 0.0768).
        scenarios: SeverityScenarios with percentile scenarios.
        defense_cost_pct: Defense cost as a fraction.

    Returns:
        List of ScenarioLoss for each percentile.
    """
    result: list[ScenarioLoss] = []

    for percentile in _SCENARIO_PERCENTILES:
        severity = _get_scenario_amount(scenarios, percentile)
        if severity is None:
            continue

        expected_indemnity = filing_probability * severity
        expected_defense = expected_indemnity * defense_cost_pct
        total = expected_indemnity + expected_defense

        label = _SCENARIO_LABELS.get(percentile, f"p{percentile}")

        result.append(
            ScenarioLoss(
                percentile=percentile,
                label=label,
                expected_indemnity=expected_indemnity,
                expected_defense=expected_defense,
                total_expected=total,
            )
        )

    return result


def compute_expected_loss(
    filing_probability_pct: float,
    severity_scenarios: SeverityScenarios | None,
    case_type: str,
    actuarial_config: dict[str, Any],
) -> ExpectedLoss:
    """Compute expected loss from filing probability and severity scenarios.

    This is the core actuarial computation:
        Expected indemnity = probability * median_severity
        Expected defense  = expected_indemnity * defense_cost_pct
        Total expected    = expected_indemnity + expected_defense

    Scenario losses are computed at 25th/50th/75th/95th percentiles.

    Args:
        filing_probability_pct: Filing probability as percentage
            (e.g. 7.68 means 7.68%).
        severity_scenarios: Severity model output with percentile
            scenarios. None means insufficient data.
        case_type: Case type for defense cost lookup
            (e.g. 'standard_sca', 'complex_sca').
        actuarial_config: Full actuarial.json config dict.

    Returns:
        ExpectedLoss with has_data=False if inputs are missing,
        otherwise populated with loss estimates.
    """
    # Get methodology note from config
    model_label = str(
        actuarial_config.get(
            "model_label",
            "MODEL-INDICATED: Not prescriptive. Underwriter sets final price.",
        )
    )

    # Guard: no severity data
    if severity_scenarios is None or not severity_scenarios.scenarios:
        logger.info("Expected loss: no severity scenarios available")
        return ExpectedLoss(
            has_data=False,
            methodology_note=model_label,
        )

    # Extract median (50th percentile) severity
    median_severity = _get_scenario_amount(severity_scenarios, 50)
    if median_severity is None:
        logger.warning("Expected loss: no 50th percentile scenario found")
        return ExpectedLoss(
            has_data=False,
            methodology_note=model_label,
        )

    # Convert percentage to decimal
    filing_probability = filing_probability_pct / 100.0

    # Look up defense cost percentage
    defense_cost_pct = _get_defense_cost_pct(case_type, actuarial_config)

    # Core computation
    expected_indemnity = filing_probability * median_severity
    expected_defense = expected_indemnity * defense_cost_pct
    total_expected = expected_indemnity + expected_defense

    # Compute scenario losses at each percentile
    scenario_losses = _compute_scenario_losses(
        filing_probability, severity_scenarios, defense_cost_pct
    )

    logger.info(
        "Expected loss: prob=%.2f%% median_sev=$%.0f defense=%.0f%% "
        "total=$%.0f",
        filing_probability_pct,
        median_severity,
        defense_cost_pct * 100,
        total_expected,
    )

    return ExpectedLoss(
        has_data=True,
        filing_probability_pct=filing_probability_pct,
        median_severity=median_severity,
        defense_cost_pct=defense_cost_pct,
        expected_indemnity=expected_indemnity,
        expected_defense=expected_defense,
        total_expected_loss=total_expected,
        scenario_losses=scenario_losses,
        methodology_note=model_label,
    )


__all__ = ["compute_expected_loss"]
