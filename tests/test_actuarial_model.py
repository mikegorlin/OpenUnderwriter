"""Tests for actuarial expected loss computation.

RED phase: Tests written before implementation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from do_uw.models.scoring_output import (
    SeverityScenario,
    SeverityScenarios,
)

# Load actual config for integration-level tests
_CONFIG_PATH = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config" / "actuarial.json"


def _load_config() -> dict[str, object]:
    """Load actuarial.json config."""
    with open(_CONFIG_PATH) as f:
        return json.load(f)  # type: ignore[no-any-return]


def _make_severity_scenarios(
    median_settlement: float = 27_000_000.0,
) -> SeverityScenarios:
    """Create SeverityScenarios with controllable median."""
    return SeverityScenarios(
        market_cap=10_000_000_000.0,
        scenarios=[
            SeverityScenario(
                percentile=25,
                label="favorable",
                settlement_estimate=median_settlement * 0.5,
                defense_cost_estimate=median_settlement * 0.5 * 0.15,
                total_exposure=median_settlement * 0.5 * 1.15,
            ),
            SeverityScenario(
                percentile=50,
                label="median",
                settlement_estimate=median_settlement,
                defense_cost_estimate=median_settlement * 0.20,
                total_exposure=median_settlement * 1.20,
            ),
            SeverityScenario(
                percentile=75,
                label="adverse",
                settlement_estimate=median_settlement * 2.0,
                defense_cost_estimate=median_settlement * 2.0 * 0.25,
                total_exposure=median_settlement * 2.0 * 1.25,
            ),
            SeverityScenario(
                percentile=95,
                label="catastrophic",
                settlement_estimate=median_settlement * 4.0,
                defense_cost_estimate=median_settlement * 4.0 * 0.30,
                total_exposure=median_settlement * 4.0 * 1.30,
            ),
        ],
    )


class TestComputeExpectedLoss:
    """Tests for compute_expected_loss function."""

    def test_expected_loss_basic(self) -> None:
        """Filing prob 7.68%, median severity $27M, defense 20%.

        Expected indemnity = 0.0768 * 27,000,000 = 2,073,600
        Expected defense = 2,073,600 * 0.20 = 414,720
        Total = 2,073,600 + 414,720 = 2,488,320
        """
        from do_uw.stages.score.actuarial_model import compute_expected_loss

        config = _load_config()
        scenarios = _make_severity_scenarios(27_000_000.0)

        result = compute_expected_loss(
            filing_probability_pct=7.68,
            severity_scenarios=scenarios,
            case_type="standard_sca",
            actuarial_config=config,
        )

        assert result.has_data is True
        assert result.filing_probability_pct == 7.68
        assert result.median_severity == 27_000_000.0
        assert result.defense_cost_pct == pytest.approx(0.20)

        # Expected indemnity = 0.0768 * 27,000,000 = 2,073,600
        assert result.expected_indemnity == pytest.approx(2_073_600.0, rel=1e-6)

        # Expected defense = 2,073,600 * 0.20 = 414,720
        assert result.expected_defense == pytest.approx(414_720.0, rel=1e-6)

        # Total = 2,073,600 + 414,720 = 2,488,320
        assert result.total_expected_loss == pytest.approx(2_488_320.0, rel=1e-6)

    def test_expected_loss_no_severity(self) -> None:
        """When severity_scenarios is None, returns has_data=False."""
        from do_uw.stages.score.actuarial_model import compute_expected_loss

        config = _load_config()

        result = compute_expected_loss(
            filing_probability_pct=7.68,
            severity_scenarios=None,
            case_type="standard_sca",
            actuarial_config=config,
        )

        assert result.has_data is False
        assert result.total_expected_loss == 0.0

    def test_expected_loss_empty_scenarios(self) -> None:
        """When scenarios list is empty, returns has_data=False."""
        from do_uw.stages.score.actuarial_model import compute_expected_loss

        config = _load_config()
        empty_scenarios = SeverityScenarios(
            market_cap=10_000_000_000.0,
            scenarios=[],
        )

        result = compute_expected_loss(
            filing_probability_pct=7.68,
            severity_scenarios=empty_scenarios,
            case_type="standard_sca",
            actuarial_config=config,
        )

        assert result.has_data is False
        assert result.total_expected_loss == 0.0

    def test_expected_loss_zero_probability(self) -> None:
        """When filing probability is 0, total expected loss is 0."""
        from do_uw.stages.score.actuarial_model import compute_expected_loss

        config = _load_config()
        scenarios = _make_severity_scenarios(27_000_000.0)

        result = compute_expected_loss(
            filing_probability_pct=0.0,
            severity_scenarios=scenarios,
            case_type="standard_sca",
            actuarial_config=config,
        )

        # has_data should be True (data was available, just zero probability)
        assert result.has_data is True
        assert result.total_expected_loss == 0.0
        assert result.expected_indemnity == 0.0
        assert result.expected_defense == 0.0

    def test_scenario_losses_computed(self) -> None:
        """Verify 4 ScenarioLoss entries at each percentile."""
        from do_uw.stages.score.actuarial_model import compute_expected_loss

        config = _load_config()
        scenarios = _make_severity_scenarios(27_000_000.0)

        result = compute_expected_loss(
            filing_probability_pct=7.68,
            severity_scenarios=scenarios,
            case_type="standard_sca",
            actuarial_config=config,
        )

        assert len(result.scenario_losses) == 4

        percentiles = [s.percentile for s in result.scenario_losses]
        assert percentiles == [25, 50, 75, 95]

        labels = [s.label for s in result.scenario_losses]
        assert labels == ["favorable", "median", "adverse", "catastrophic"]

        # Each scenario loss should have positive values
        for sl in result.scenario_losses:
            assert sl.total_expected == sl.expected_indemnity + sl.expected_defense
            assert sl.expected_indemnity >= 0
            assert sl.expected_defense >= 0

    def test_methodology_note_from_config(self) -> None:
        """Verify model_label from config flows through."""
        from do_uw.stages.score.actuarial_model import compute_expected_loss

        config = _load_config()
        scenarios = _make_severity_scenarios(27_000_000.0)

        result = compute_expected_loss(
            filing_probability_pct=7.68,
            severity_scenarios=scenarios,
            case_type="standard_sca",
            actuarial_config=config,
        )

        assert "MODEL-INDICATED" in result.methodology_note
        assert "Underwriter sets final price" in result.methodology_note

    def test_defense_cost_lookup(self) -> None:
        """Verify _get_defense_cost_pct returns correct values for each case type."""
        from do_uw.stages.score.actuarial_model import _get_defense_cost_pct

        config = _load_config()

        assert _get_defense_cost_pct("standard_sca", config) == 0.20
        assert _get_defense_cost_pct("complex_sca", config) == 0.25
        assert _get_defense_cost_pct("sec_enforcement", config) == 0.30
        assert _get_defense_cost_pct("derivative", config) == 0.15
        assert _get_defense_cost_pct("unknown_type", config) == 0.20  # default

    def test_expected_loss_complex_sca(self) -> None:
        """Defense cost of 25% for complex_sca case type."""
        from do_uw.stages.score.actuarial_model import compute_expected_loss

        config = _load_config()
        scenarios = _make_severity_scenarios(27_000_000.0)

        result = compute_expected_loss(
            filing_probability_pct=7.68,
            severity_scenarios=scenarios,
            case_type="complex_sca",
            actuarial_config=config,
        )

        assert result.defense_cost_pct == pytest.approx(0.25)
        # Expected indemnity = 0.0768 * 27M = 2,073,600
        # Expected defense = 2,073,600 * 0.25 = 518,400
        assert result.expected_defense == pytest.approx(518_400.0, rel=1e-6)
        total = 2_073_600.0 + 518_400.0
        assert result.total_expected_loss == pytest.approx(total, rel=1e-6)
