"""Legacy DDL severity model wrapped as a SeverityLens adapter (Phase 108).

Adapts the existing SeverityScenarios output (from predict_settlement or
model_severity) into a SeverityLensResult for side-by-side comparison
with the new v7.0 severity model.

This is a POST-HOC adapter (same pattern as LegacyScoringLens): it takes
an already-computed SeverityScenarios (via constructor) and wraps it.
It does NOT re-run settlement prediction.

Legacy DDL is NEVER the primary severity model -- the v7.0 damages/
regression/amplifier model drives the worksheet. Legacy is retained
permanently for ongoing calibration comparison.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.severity import (
    ScenarioSeverity,
    SeverityLensResult,
    SeverityZone,
)

__all__ = [
    "LegacySeverityLens",
]

logger = logging.getLogger(__name__)


class LegacySeverityLens:
    """Legacy DDL severity model wrapped as SeverityLens adapter.

    Post-hoc adapter: pass SeverityScenarios (or None) to constructor,
    then call evaluate() to get a SeverityLensResult.

    The evaluate() signature accepts signal_results for compatibility
    but the actual data comes from the SeverityScenarios passed at
    construction time.
    """

    def __init__(self, severity_scenarios: Any | None) -> None:
        """Store the legacy SeverityScenarios for wrapping.

        Args:
            severity_scenarios: A SeverityScenarios from the legacy DDL
                pipeline (or None if no severity data available).
        """
        self._scenarios = severity_scenarios

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        company: Any | None = None,
        liberty_attachment: float | None = None,
        liberty_product: str | None = None,
        hae_result: Any | None = None,
    ) -> SeverityLensResult:
        """Wrap legacy SeverityScenarios as SeverityLensResult.

        Maps legacy scenarios to ScenarioSeverity list.
        Uses median scenario as estimated_settlement.
        Zone derived from settlement amount only (no P context in legacy).

        Returns:
            SeverityLensResult wrapping legacy data.
        """
        if self._scenarios is None or not hasattr(self._scenarios, "scenarios"):
            return SeverityLensResult(
                lens_name="legacy_ddl",
                estimated_settlement=0,
                damages_estimate=0,
                amplifier_results=[],
                scenarios=[],
                defense_costs=0,
                layer_erosion=None,
                zone=SeverityZone.GREEN,
                confidence="LOW",
                metadata={"source": "legacy_ddl", "note": "No severity data available"},
            )

        legacy_scenarios = self._scenarios.scenarios
        if not legacy_scenarios:
            return SeverityLensResult(
                lens_name="legacy_ddl",
                estimated_settlement=0,
                damages_estimate=0,
                amplifier_results=[],
                scenarios=[],
                defense_costs=0,
                layer_erosion=None,
                zone=SeverityZone.GREEN,
                confidence="LOW",
                metadata={"source": "legacy_ddl", "note": "Empty scenarios"},
            )

        # Find median scenario (percentile 50) for point estimate
        estimated_settlement = 0.0
        median_defense = 0.0
        for s in legacy_scenarios:
            if s.percentile == 50:
                estimated_settlement = s.settlement_estimate
                median_defense = s.defense_cost_estimate
                break

        # If no 50th percentile, use the first scenario
        if estimated_settlement == 0 and legacy_scenarios:
            estimated_settlement = legacy_scenarios[0].settlement_estimate
            median_defense = legacy_scenarios[0].defense_cost_estimate

        # DDL amount as damages estimate
        damages_estimate = 0.0
        if legacy_scenarios:
            damages_estimate = legacy_scenarios[0].ddl_amount

        # Convert legacy scenarios to ScenarioSeverity
        scenario_list: list[ScenarioSeverity] = []
        for s in legacy_scenarios:
            scenario_list.append(
                ScenarioSeverity(
                    allegation_type="legacy_ddl",
                    drop_level=s.label,
                    base_damages=s.ddl_amount,
                    settlement_estimate=s.settlement_estimate,
                    amplified_settlement=s.settlement_estimate,  # no amplifiers in legacy
                    defense_cost_estimate=s.defense_cost_estimate,
                    total_exposure=s.total_exposure,
                )
            )

        # Zone from settlement amount (no P in legacy context)
        # Use conservative estimate: P=0.10 (typical) for zone calculation
        zone = SeverityZone.zone_for(0.10, estimated_settlement)

        return SeverityLensResult(
            lens_name="legacy_ddl",
            estimated_settlement=estimated_settlement,
            damages_estimate=damages_estimate,
            amplifier_results=[],
            scenarios=scenario_list,
            defense_costs=median_defense,
            layer_erosion=None,
            zone=zone,
            confidence="MEDIUM",
            metadata={
                "source": "legacy_ddl",
                "market_cap": getattr(self._scenarios, "market_cap", 0),
                "needs_calibration": getattr(self._scenarios, "needs_calibration", True),
            },
        )
