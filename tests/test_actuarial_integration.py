"""Integration tests for actuarial pricing in the BenchmarkStage pipeline.

Validates:
- BenchmarkStage produces actuarial_pricing when severity data exists
- Graceful degradation when severity data is missing
- Non-breaking behavior when build_actuarial_pricing errors
- Layer ROLs decrease monotonically from primary through high excess
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.financials import (
    ExtractedFinancials,
    PeerCompany,
    PeerGroup,
)
from do_uw.models.governance import GovernanceData
from do_uw.models.governance_forensics import GovernanceQualityScore
from do_uw.models.market import MarketSignals, ShortInterestProfile, StockPerformance
from do_uw.models.scoring import (
    ScoringResult,
    Tier,
    TierClassification,
)
from do_uw.models.scoring_output import (
    SeverityScenario,
    SeverityScenarios,
)
from do_uw.models.state import AnalysisState, ExtractedData

NOW = datetime.now(tz=UTC)


def _sv_float(val: float, src: str = "test") -> SourcedValue[float]:
    return SourcedValue(value=val, source=src, confidence=Confidence.MEDIUM, as_of=NOW)


def _sv_str(val: str, src: str = "test") -> SourcedValue[str]:
    return SourcedValue(value=val, source=src, confidence=Confidence.MEDIUM, as_of=NOW)


def _sv_int(val: int, src: str = "test") -> SourcedValue[int]:
    return SourcedValue(value=val, source=src, confidence=Confidence.MEDIUM, as_of=NOW)


def _make_sectors_config() -> dict[str, object]:
    """Minimal sectors.json config for testing."""
    return {
        "claim_base_rates": {
            "TECH": 6.0,
            "FINS": 4.0,
            "DEFAULT": 3.9,
        },
        "market_cap_filing_multipliers": {
            "mega": {"min_cap": 50000000000, "multiplier": 1.56},
            "large": {"min_cap": 10000000000, "multiplier": 1.28},
            "mid": {"min_cap": 2000000000, "multiplier": 1.00},
            "small": {"min_cap": 500000000, "multiplier": 0.90},
            "micro": {"min_cap": 0, "multiplier": 0.77},
        },
        "short_interest": {
            "TECH": {"normal": 4, "elevated": 7, "high": 10},
            "DEFAULT": {"normal": 3, "elevated": 5, "high": 8},
        },
        "volatility_90d": {
            "TECH": {"typical": 2.5, "elevated": 4, "high": 6},
            "DEFAULT": {"typical": 2.5, "elevated": 4, "high": 6},
        },
        "leverage_debt_ebitda": {
            "TECH": {"normal": 2.0, "elevated": 3.0, "critical": 4.0},
            "DEFAULT": {"normal": 2.5, "elevated": 4.0, "critical": 5.5},
        },
        "sector_codes": {
            "mappings": {"TECH": "Technology", "FINS": "Financials"},
        },
    }


def _make_scoring_config() -> dict[str, object]:
    """Minimal scoring.json config for testing."""
    return {
        "severity_ranges": {
            "by_market_cap": [
                {"tier": "MEGA", "min_cap_b": 50, "base_range_m": [25, 150]},
                {"tier": "LARGE", "min_cap_b": 10, "max_cap_b": 50, "base_range_m": [15, 75]},
                {"tier": "MID", "min_cap_b": 2, "max_cap_b": 10, "base_range_m": [8, 40]},
                {"tier": "SMALL", "min_cap_b": 0.5, "max_cap_b": 2, "base_range_m": [4, 20]},
                {"tier": "MICRO", "max_cap_b": 0.5, "base_range_m": [2, 10]},
            ],
        },
    }


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


def _make_state_with_severity(
    quality_score: float = 75.0,
    tier: Tier = Tier.WANT,
    include_severity: bool = True,
) -> AnalysisState:
    """Create a state with scoring, severity, and company data."""
    state = AnalysisState(ticker="TEST")

    # Mark prior stages complete
    for stage in ["resolve", "acquire", "extract", "analyze", "score"]:
        state.mark_stage_running(stage)
        state.mark_stage_completed(stage)

    # Company profile
    state.company = CompanyProfile(
        identity=CompanyIdentity(
            ticker="TEST",
            legal_name=_sv_str("Test Corp"),
            sic_code=_sv_str("3571"),
            sector=_sv_str("TECH"),
            exchange=_sv_str("NASDAQ"),
        ),
        market_cap=_sv_float(5_000_000_000.0),  # $5B (mid-cap)
        employee_count=_sv_int(10000),
    )

    # Scoring result with severity
    state.scoring = ScoringResult(
        quality_score=quality_score,
        composite_score=quality_score,
        tier=TierClassification(
            tier=tier,
            score_range_low=71,
            score_range_high=85,
        ),
        severity_scenarios=(
            _make_severity_scenarios() if include_severity else None
        ),
    )

    # Extracted data with peers
    state.extracted = ExtractedData(
        financials=ExtractedFinancials(
            peer_group=PeerGroup(
                target_ticker="TEST",
                peers=[
                    PeerCompany(
                        ticker="PEER1", name="Peer One",
                        market_cap=3_000_000_000.0,
                        revenue=1_000_000_000.0,
                    ),
                    PeerCompany(
                        ticker="PEER2", name="Peer Two",
                        market_cap=8_000_000_000.0,
                        revenue=4_000_000_000.0,
                    ),
                ],
            ),
        ),
        market=MarketSignals(
            stock=StockPerformance(
                volatility_90d=_sv_float(3.0),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv_float(5.0),
            ),
        ),
        governance=GovernanceData(
            governance_score=GovernanceQualityScore(
                total_score=_sv_float(72.0),
            ),
        ),
    )

    return state


def _mock_loader() -> MagicMock:
    """Create a mock BrainLoader returning test configs."""
    mock_loader = MagicMock()
    mock_brain = MagicMock()
    mock_brain.sectors = _make_sectors_config()
    mock_brain.scoring = _make_scoring_config()
    mock_loader.load_all.return_value = mock_brain
    return mock_loader


class TestBenchmarkActuarialPricing:
    """Integration tests for actuarial pricing through BenchmarkStage."""

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_produces_actuarial_pricing(
        self, mock_loader_cls: MagicMock,
    ) -> None:
        """BenchmarkStage populates actuarial_pricing when severity exists."""
        mock_loader_cls.return_value = _mock_loader()

        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_state_with_severity(include_severity=True)
        stage = BenchmarkStage()
        stage.run(state)

        assert state.scoring is not None
        pricing = state.scoring.actuarial_pricing
        assert pricing is not None
        assert pricing.has_data is True
        assert pricing.expected_loss is not None
        assert pricing.expected_loss.has_data is True
        assert len(pricing.layer_pricing) > 0
        assert pricing.total_indicated_premium > 0
        assert "MODEL-INDICATED" in pricing.methodology_note

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_no_severity_skips_actuarial(
        self, mock_loader_cls: MagicMock,
    ) -> None:
        """When severity_scenarios is None, actuarial_pricing stays None."""
        mock_loader_cls.return_value = _mock_loader()

        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_state_with_severity(include_severity=False)
        stage = BenchmarkStage()
        stage.run(state)

        assert state.scoring is not None
        # Actuarial pricing should be None (skipped, not errored)
        assert state.scoring.actuarial_pricing is None

    @patch("do_uw.stages.benchmark.BrainLoader")
    @patch(
        "do_uw.stages.score.actuarial_pricing_builder.build_actuarial_pricing",
        side_effect=RuntimeError("test error"),
    )
    def test_graceful_on_error(
        self,
        _mock_build: MagicMock,
        mock_loader_cls: MagicMock,
    ) -> None:
        """Pipeline completes when build_actuarial_pricing raises."""
        mock_loader_cls.return_value = _mock_loader()

        from do_uw.models.common import StageStatus
        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_state_with_severity(include_severity=True)
        stage = BenchmarkStage()
        # Should NOT raise
        stage.run(state)

        # Pipeline completed
        assert state.stages["benchmark"].status == StageStatus.COMPLETED
        # Actuarial pricing was never set (error was caught)
        assert state.scoring is not None
        assert state.scoring.actuarial_pricing is None

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_layer_rols_decrease(
        self, mock_loader_cls: MagicMock,
    ) -> None:
        """ROLs decrease from primary through high excess layers.

        This is the key actuarial property: higher layers in the tower
        have lower rate-on-line because losses are less likely to reach
        higher attachment points.
        """
        mock_loader_cls.return_value = _mock_loader()

        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_state_with_severity(include_severity=True)
        stage = BenchmarkStage()
        stage.run(state)

        assert state.scoring is not None
        pricing = state.scoring.actuarial_pricing
        assert pricing is not None
        assert pricing.has_data is True

        # Filter to non-side_a layers (primary + excess)
        non_side_a = [
            lp for lp in pricing.layer_pricing
            if lp.layer_type.lower() != "side_a"
        ]
        assert len(non_side_a) >= 2, "Need at least primary + 1 excess"

        # Verify ROLs decrease monotonically
        rols = [lp.indicated_rol for lp in non_side_a]
        for i in range(len(rols) - 1):
            assert rols[i] > rols[i + 1], (
                f"ROL at layer {i + 1} ({rols[i]:.6f}) should be > "
                f"ROL at layer {i + 2} ({rols[i + 1]:.6f})"
            )

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_assumptions_populated(
        self, mock_loader_cls: MagicMock,
    ) -> None:
        """Verify assumptions list is populated with key parameters."""
        mock_loader_cls.return_value = _mock_loader()

        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_state_with_severity(include_severity=True)
        stage = BenchmarkStage()
        stage.run(state)

        assert state.scoring is not None
        pricing = state.scoring.actuarial_pricing
        assert pricing is not None
        assert pricing.has_data is True
        assert len(pricing.assumptions) > 0

        # Check key assumption strings present
        assumptions_text = " ".join(pricing.assumptions)
        assert "Filing probability" in assumptions_text
        assert "Median severity" in assumptions_text
        assert "ILF alpha" in assumptions_text

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_tower_structure_described(
        self, mock_loader_cls: MagicMock,
    ) -> None:
        """Verify tower structure description is populated."""
        mock_loader_cls.return_value = _mock_loader()

        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_state_with_severity(include_severity=True)
        stage = BenchmarkStage()
        stage.run(state)

        assert state.scoring is not None
        pricing = state.scoring.actuarial_pricing
        assert pricing is not None
        assert pricing.tower_structure_used != ""
        assert "layer" in pricing.tower_structure_used.lower()
