"""Tests for P x S matrix chart and severity context builder.

Phase 108 Plan 02 Task 2: TDD RED then GREEN.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.severity import (
    AmplifierResult,
    LayerErosionResult,
    ScenarioSeverity,
    SeverityLensResult,
    SeverityResult,
    SeverityZone,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _make_severity_result(
    *,
    probability: float = 0.15,
    settlement: float = 50_000_000,
    attachment: float | None = None,
) -> SeverityResult:
    """Build a test SeverityResult with all required fields."""
    amplifier_results = [
        AmplifierResult(
            amplifier_id="amp_restatement",
            name="Restatement Amplifier",
            fired=True,
            multiplier=1.3,
            trigger_signals_matched=["FIN.ACCT.restatement"],
            explanation="Restatement detected",
        ),
        AmplifierResult(
            amplifier_id="amp_sec",
            name="SEC Investigation",
            fired=False,
            multiplier=1.0,
            trigger_signals_matched=[],
            explanation="",
        ),
    ]

    scenarios = [
        ScenarioSeverity(
            allegation_type="guidance_miss",
            drop_level="worst_actual",
            base_damages=80_000_000,
            settlement_estimate=60_000_000,
            amplified_settlement=78_000_000,
            defense_cost_estimate=12_000_000,
            total_exposure=90_000_000,
        ),
        ScenarioSeverity(
            allegation_type="guidance_miss",
            drop_level="sector_median",
            base_damages=50_000_000,
            settlement_estimate=40_000_000,
            amplified_settlement=52_000_000,
            defense_cost_estimate=8_000_000,
            total_exposure=60_000_000,
        ),
        ScenarioSeverity(
            allegation_type="guidance_miss",
            drop_level="catastrophic",
            base_damages=120_000_000,
            settlement_estimate=100_000_000,
            amplified_settlement=130_000_000,
            defense_cost_estimate=20_000_000,
            total_exposure=150_000_000,
        ),
    ]

    layer_erosion = None
    if attachment is not None:
        layer_erosion = [
            LayerErosionResult(
                attachment=attachment,
                limit=attachment,
                product="ABC",
                penetration_probability=0.45,
                liberty_severity=25_000_000,
                effective_expected_loss=11_250_000,
            )
        ]

    primary = SeverityLensResult(
        lens_name="v7_severity_scoring",
        estimated_settlement=settlement,
        damages_estimate=80_000_000,
        amplifier_results=amplifier_results,
        scenarios=scenarios,
        defense_costs=10_000_000,
        layer_erosion=layer_erosion,
        zone=SeverityZone.zone_for(probability, settlement),
        confidence="MEDIUM",
        metadata={
            "primary_allegation_type": "guidance_miss",
            "regression_estimate": 45_000_000,
            "combined_amplifier_multiplier": 1.3,
            "turnover_rate": 0.5,
            "class_period_return": 0.25,
            "market_cap": 20_000_000_000,
        },
    )

    legacy = SeverityLensResult(
        lens_name="legacy_ddl",
        estimated_settlement=40_000_000,
        damages_estimate=60_000_000,
        zone=SeverityZone.YELLOW,
        confidence="MEDIUM",
        metadata={"source": "legacy_ddl"},
    )

    return SeverityResult(
        primary=primary,
        legacy=legacy,
        probability=probability,
        severity=settlement,
        expected_loss=probability * settlement,
        zone=SeverityZone.zone_for(probability, settlement),
        scenario_table=scenarios,
    )


# ---------------------------------------------------------------------------
# P x S Matrix Chart tests
# ---------------------------------------------------------------------------


class TestRenderPxSMatrix:
    """render_pxs_matrix produces chart bytes."""

    def test_render_pxs_matrix_produces_bytes(self) -> None:
        """Chart produces PNG bytes > 1000."""
        from do_uw.stages.render.charts.pxs_matrix_chart import (
            render_pxs_matrix,
        )

        result = _make_severity_result()
        output = render_pxs_matrix(result)
        assert isinstance(output, bytes)
        assert len(output) > 1000

    def test_pxs_chart_handles_no_attachment(self) -> None:
        """Chart renders without liberty attachment line."""
        from do_uw.stages.render.charts.pxs_matrix_chart import (
            render_pxs_matrix,
        )

        result = _make_severity_result(attachment=None)
        output = render_pxs_matrix(result)
        assert isinstance(output, bytes)
        assert len(output) > 1000

    def test_pxs_chart_handles_attachment(self) -> None:
        """Chart renders with horizontal dashed line for attachment."""
        from do_uw.stages.render.charts.pxs_matrix_chart import (
            render_pxs_matrix,
        )

        result = _make_severity_result(attachment=25_000_000)
        output = render_pxs_matrix(result)
        assert isinstance(output, bytes)
        assert len(output) > 1000

    def test_pxs_chart_zone_colors(self) -> None:
        """Chart creates matplotlib patches for 4 zones."""
        from do_uw.stages.render.charts.pxs_matrix_chart import (
            render_pxs_matrix,
        )

        # This test verifies the chart generates without error
        # for different zone positions
        for p, s in [
            (0.05, 5_000_000),     # GREEN
            (0.15, 15_000_000),    # YELLOW
            (0.30, 30_000_000),    # ORANGE
            (0.40, 80_000_000),    # RED
        ]:
            result = _make_severity_result(probability=p, settlement=s)
            output = render_pxs_matrix(result)
            assert isinstance(output, bytes)
            assert len(output) > 1000

    def test_render_pxs_matrix_html(self) -> None:
        """HTML rendering produces base64-encoded PNG string."""
        from do_uw.stages.render.charts.pxs_matrix_chart import (
            render_pxs_matrix_html,
        )

        result = _make_severity_result()
        html = render_pxs_matrix_html(result)
        assert isinstance(html, str)
        assert "data:image/png;base64," in html or "<img" in html


# ---------------------------------------------------------------------------
# Severity Context Builder tests
# ---------------------------------------------------------------------------


class TestSeverityContext:
    """build_severity_context returns all required template data."""

    def _make_mock_state(
        self, severity_result: SeverityResult | None = None,
    ) -> MagicMock:
        """Build mock state with optional severity_result."""
        state = MagicMock()
        if severity_result is None:
            state.scoring = None
        else:
            state.scoring = MagicMock()
            state.scoring.severity_result = severity_result
            state.scoring.hae_result = MagicMock()
            state.scoring.hae_result.composites = {
                "host": 0.10, "agent": 0.20, "environment": 0.08,
            }
            state.scoring.hae_result.tier = MagicMock()
            state.scoring.hae_result.tier.value = "ELEVATED"
        return state

    def test_severity_context_keys(self) -> None:
        """Context returns all required keys when severity available."""
        from do_uw.stages.render.context_builders.severity_context import (
            build_severity_context,
        )

        result = _make_severity_result()
        state = self._make_mock_state(result)
        ctx = build_severity_context(state)

        assert ctx["severity_available"] is True
        assert "damages_breakdown" in ctx
        assert "amplifiers_fired" in ctx
        assert "amplifiers_full" in ctx
        assert "pxs_chart_b64" in ctx
        assert "scenario_table" in ctx
        assert "expected_loss" in ctx
        assert "probability" in ctx
        assert "severity" in ctx
        assert "zone" in ctx
        assert "defense_costs_total" in ctx

    def test_severity_context_unavailable(self) -> None:
        """None severity -> severity_available=False."""
        from do_uw.stages.render.context_builders.severity_context import (
            build_severity_context,
        )

        state = self._make_mock_state(None)
        ctx = build_severity_context(state)

        assert ctx["severity_available"] is False

    def test_severity_context_amplifiers_split(self) -> None:
        """Fired amplifiers in main section, all in appendix."""
        from do_uw.stages.render.context_builders.severity_context import (
            build_severity_context,
        )

        result = _make_severity_result()
        state = self._make_mock_state(result)
        ctx = build_severity_context(state)

        # Fired amplifiers only
        fired = ctx["amplifiers_fired"]
        assert len(fired) == 1
        assert fired[0]["name"] == "Restatement Amplifier"

        # Full list includes both fired and not
        full = ctx["amplifiers_full"]
        assert len(full) >= 2

    def test_severity_context_layer_erosion(self) -> None:
        """Attachment provided -> layer_erosion populated."""
        from do_uw.stages.render.context_builders.severity_context import (
            build_severity_context,
        )

        result = _make_severity_result(attachment=25_000_000)
        state = self._make_mock_state(result)
        ctx = build_severity_context(state)

        erosion = ctx.get("layer_erosion")
        assert erosion is not None
        assert "penetration_probability" in erosion
        assert erosion["attachment"] == 25_000_000

    def test_severity_context_legacy_comparison(self) -> None:
        """Legacy comparison data present when legacy lens available."""
        from do_uw.stages.render.context_builders.severity_context import (
            build_severity_context,
        )

        result = _make_severity_result()
        state = self._make_mock_state(result)
        ctx = build_severity_context(state)

        legacy = ctx.get("legacy_comparison")
        assert legacy is not None
        assert "legacy_estimate" in legacy
