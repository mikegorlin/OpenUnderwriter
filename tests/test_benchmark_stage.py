"""Tests for BENCHMARK stage: percentile engine, inherent risk, peer metrics, stage.

Validates:
- Percentile rank computation with ties and directionality
- Ratio to baseline computation
- Inherent risk baseline multiplicative calculation
- Peer metric extraction and ranking
- BenchmarkStage full run with mocked state
- Executive summary initialization
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.executive_summary import ExecutiveSummary
from do_uw.models.financials import (
    ExtractedFinancials,
    PeerCompany,
    PeerGroup,
)
from do_uw.models.governance import GovernanceData
from do_uw.models.governance_forensics import GovernanceQualityScore
from do_uw.models.market import MarketSignals, ShortInterestProfile, StockPerformance
from do_uw.models.scoring import (
    BenchmarkResult,
    ScoringResult,
    Tier,
    TierClassification,
)
from do_uw.models.state import AnalysisState, ExtractedData
from do_uw.stages.benchmark.inherent_risk import (
    _quality_score_multiplier,
    compute_inherent_risk_baseline,
)
from do_uw.stages.benchmark.peer_metrics import compute_peer_rankings
from do_uw.stages.benchmark.percentile_engine import (
    percentile_rank,
    ratio_to_baseline,
)

NOW = datetime.now(tz=UTC)


def _sv_float(val: float, src: str = "test") -> SourcedValue[float]:
    return SourcedValue(value=val, source=src, confidence=Confidence.MEDIUM, as_of=NOW)


def _sv_str(val: str, src: str = "test") -> SourcedValue[str]:
    return SourcedValue(value=val, source=src, confidence=Confidence.MEDIUM, as_of=NOW)


def _sv_int(val: int, src: str = "test") -> SourcedValue[int]:
    return SourcedValue(value=val, source=src, confidence=Confidence.MEDIUM, as_of=NOW)


def _make_sectors_config() -> dict:
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


def _make_scoring_config() -> dict:
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


def _make_state_with_scoring(
    quality_score: float = 75.0,
    tier: Tier = Tier.WANT,
) -> AnalysisState:
    """Create a state with scoring and company data for benchmark tests."""
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

    # Scoring result
    state.scoring = ScoringResult(
        quality_score=quality_score,
        composite_score=quality_score,
        tier=TierClassification(
            tier=tier,
            score_range_low=71,
            score_range_high=85,
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
                    PeerCompany(
                        ticker="PEER3", name="Peer Three",
                        market_cap=4_000_000_000.0,
                        revenue=2_000_000_000.0,
                    ),
                    PeerCompany(
                        ticker="PEER4", name="Peer Four",
                        market_cap=6_000_000_000.0,
                        revenue=3_000_000_000.0,
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


# -----------------------------------------------------------------------
# Percentile Engine Tests
# -----------------------------------------------------------------------


class TestPercentileRank:
    """Tests for percentile_rank function."""

    def test_basic_middle_value(self) -> None:
        """Company in the middle of 5 peers."""
        result = percentile_rank(50.0, [10, 20, 30, 40, 60])
        # 4 below, 0 equal => (4 + 0) / 5 * 100 = 80
        assert result == 80.0

    def test_empty_peers_returns_50(self) -> None:
        """Empty peer list returns 50th percentile."""
        assert percentile_rank(100.0, []) == 50.0

    def test_lower_is_better_flips(self) -> None:
        """Lower-is-better flips so lowest value gets highest rank."""
        # Company has lowest value (best) among peers
        result = percentile_rank(
            1.0, [2, 3, 4, 5], higher_is_better=False,
        )
        # 4 above, 0 equal => (4 + 0) / 4 * 100 = 100
        assert result == 100.0

    def test_lower_is_better_worst(self) -> None:
        """Lower-is-better: highest value gets lowest rank."""
        result = percentile_rank(
            10.0, [1, 2, 3, 4], higher_is_better=False,
        )
        # 0 above, 0 equal => 0 / 4 * 100 = 0
        assert result == 0.0

    def test_ties_handled(self) -> None:
        """Ties use 0.5 * count_equal."""
        result = percentile_rank(50.0, [50, 50, 50, 50])
        # 0 below, 4 equal => (0 + 0.5*4) / 4 * 100 = 50
        assert result == 50.0

    def test_all_below(self) -> None:
        """Company is best (all peers below)."""
        result = percentile_rank(100.0, [10, 20, 30, 40])
        # 4 below, 0 equal => 100
        assert result == 100.0

    def test_all_above(self) -> None:
        """Company is worst (all peers above)."""
        result = percentile_rank(1.0, [10, 20, 30, 40])
        # 0 below, 0 equal => 0
        assert result == 0.0


class TestRatioToBaseline:
    """Tests for ratio_to_baseline function."""

    def test_basic_ratio(self) -> None:
        """Company is 2x the baseline."""
        assert ratio_to_baseline(10.0, 5.0) == 2.0

    def test_zero_baseline(self) -> None:
        """Zero baseline returns 1.0 (equal)."""
        assert ratio_to_baseline(10.0, 0.0) == 1.0

    def test_below_baseline(self) -> None:
        """Company below baseline gives ratio < 1."""
        result = ratio_to_baseline(2.5, 5.0)
        assert result == 0.5


# -----------------------------------------------------------------------
# Inherent Risk Tests
# -----------------------------------------------------------------------


class TestInherentRiskBaseline:
    """Tests for inherent risk baseline computation."""

    def test_tech_sector_mid_cap(self) -> None:
        """TECH sector, mid-cap company, WANT tier."""
        result = compute_inherent_risk_baseline(
            sector_code="TECH",
            market_cap=5_000_000_000.0,  # $5B (mid)
            quality_score=75.0,
            tier=Tier.WANT,
            sectors_config=_make_sectors_config(),
            scoring_config=_make_scoring_config(),
        )
        assert result.sector_base_rate_pct == 6.0
        assert result.market_cap_multiplier == 1.0  # mid-cap
        assert result.market_cap_adjusted_rate_pct == 6.0
        # WANT tier, score 75: multiplier in 0.6-0.9 range
        assert 0.5 <= result.score_multiplier <= 1.0
        assert result.company_adjusted_rate_pct > 0
        assert result.sector_name == "Technology"
        assert result.market_cap_tier == "MID"
        assert result.methodology_note == "NEEDS CALIBRATION"

    def test_mega_cap_multiplier(self) -> None:
        """Mega-cap gets higher filing multiplier."""
        result = compute_inherent_risk_baseline(
            sector_code="TECH",
            market_cap=100_000_000_000.0,  # $100B (mega)
            quality_score=90.0,
            tier=Tier.WIN,
            sectors_config=_make_sectors_config(),
            scoring_config=_make_scoring_config(),
        )
        assert result.market_cap_multiplier == 1.56
        assert result.market_cap_tier == "MEGA"

    def test_win_tier_multiplier(self) -> None:
        """WIN tier gets low score multiplier (0.3-0.5x)."""
        mult = _quality_score_multiplier(95.0, Tier.WIN)
        assert 0.3 <= mult <= 0.5

    def test_walk_tier_multiplier(self) -> None:
        """WALK tier gets high score multiplier (2.0-3.0x)."""
        mult = _quality_score_multiplier(20.0, Tier.WALK)
        assert 2.0 <= mult <= 3.0

    def test_no_touch_fixed(self) -> None:
        """NO_TOUCH tier gets fixed 3.5x multiplier."""
        mult = _quality_score_multiplier(5.0, Tier.NO_TOUCH)
        assert mult == 3.5

    def test_none_market_cap_defaults_mid(self) -> None:
        """None market cap defaults to mid-cap tier."""
        result = compute_inherent_risk_baseline(
            sector_code="TECH",
            market_cap=None,
            quality_score=60.0,
            tier=Tier.WRITE,
            sectors_config=_make_sectors_config(),
            scoring_config=_make_scoring_config(),
        )
        assert result.market_cap_multiplier == 1.0
        assert result.market_cap_tier == "MID"

    def test_severity_ranges_populated(self) -> None:
        """Severity ranges come from scoring.json by_market_cap."""
        result = compute_inherent_risk_baseline(
            sector_code="TECH",
            market_cap=5_000_000_000.0,
            quality_score=60.0,
            tier=Tier.WRITE,
            sectors_config=_make_sectors_config(),
            scoring_config=_make_scoring_config(),
        )
        # MID tier: base_range_m = [8, 40]
        assert result.severity_range_25th == 8.0
        assert result.severity_range_50th > 8.0
        assert result.severity_range_75th > result.severity_range_50th
        assert result.severity_range_95th == 40.0

    def test_unknown_sector_defaults(self) -> None:
        """Unknown sector code falls back to DEFAULT."""
        result = compute_inherent_risk_baseline(
            sector_code="UNKNOWN",
            market_cap=5_000_000_000.0,
            quality_score=60.0,
            tier=Tier.WRITE,
            sectors_config=_make_sectors_config(),
            scoring_config=_make_scoring_config(),
        )
        assert result.sector_base_rate_pct == 3.9  # DEFAULT


# -----------------------------------------------------------------------
# Peer Metrics Tests
# -----------------------------------------------------------------------


class TestComputePeerRankings:
    """Tests for compute_peer_rankings function."""

    def test_with_peers(self) -> None:
        """Rankings computed when peer data is available."""
        state = _make_state_with_scoring()
        sectors = _make_sectors_config()

        rankings, details = compute_peer_rankings(state, sectors)

        # Should have market_cap ranking (company $5B, peers $3-8B)
        assert "market_cap" in rankings
        assert "market_cap" in details
        assert details["market_cap"].peer_count == 4
        assert details["market_cap"].percentile_rank is not None

    def test_no_peers_graceful(self) -> None:
        """Handles missing peer data gracefully."""
        state = _make_state_with_scoring()
        state.extracted = ExtractedData()  # No financials

        sectors = _make_sectors_config()
        _rankings, details = compute_peer_rankings(state, sectors)

        # market_cap should have no peer count
        assert details["market_cap"].peer_count == 0

    def test_quality_score_included(self) -> None:
        """Quality score metric is present in details."""
        state = _make_state_with_scoring(quality_score=75.0)
        sectors = _make_sectors_config()

        _, details = compute_peer_rankings(state, sectors)

        assert "quality_score" in details
        assert details["quality_score"].company_value == 75.0

    def test_governance_score_included(self) -> None:
        """Governance score metric is extracted."""
        state = _make_state_with_scoring()
        sectors = _make_sectors_config()

        _, details = compute_peer_rankings(state, sectors)

        assert "governance_score" in details
        assert details["governance_score"].company_value == 72.0

    def test_volatility_baseline_comparison(self) -> None:
        """Volatility compared against sector baseline."""
        state = _make_state_with_scoring()
        sectors = _make_sectors_config()

        _, details = compute_peer_rankings(state, sectors)

        vol = details.get("volatility_90d")
        assert vol is not None
        assert vol.company_value == 3.0
        assert vol.baseline_value == 2.5  # TECH typical
        # 3.0 / 2.5 = 1.2 ratio; lower_is_better so percentile < 50
        assert vol.percentile_rank is not None


# -----------------------------------------------------------------------
# BenchmarkStage Tests
# -----------------------------------------------------------------------


class TestBenchmarkStage:
    """Tests for BenchmarkStage.run with mocked BackwardCompatLoader."""

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_stage_runs(self, mock_loader_cls: object) -> None:
        """BenchmarkStage.run completes and populates state."""
        from unittest.mock import MagicMock

        mock_loader = MagicMock()
        mock_brain = MagicMock()
        mock_brain.sectors = _make_sectors_config()
        mock_brain.scoring = _make_scoring_config()
        mock_loader.load_all.return_value = mock_brain
        assert isinstance(mock_loader_cls, MagicMock)
        mock_loader_cls.return_value = mock_loader

        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_state_with_scoring()
        stage = BenchmarkStage()
        stage.run(state)

        # Verify BenchmarkResult populated
        assert state.benchmark is not None
        assert isinstance(state.benchmark, BenchmarkResult)
        assert len(state.benchmark.peer_group_tickers) == 4
        assert state.benchmark.relative_position is not None
        assert state.benchmark.inherent_risk is not None

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_populates_executive_summary(
        self, mock_loader_cls: object,
    ) -> None:
        """BenchmarkStage initializes ExecutiveSummary on state."""
        from unittest.mock import MagicMock

        mock_loader = MagicMock()
        mock_brain = MagicMock()
        mock_brain.sectors = _make_sectors_config()
        mock_brain.scoring = _make_scoring_config()
        mock_loader.load_all.return_value = mock_brain
        assert isinstance(mock_loader_cls, MagicMock)
        mock_loader_cls.return_value = mock_loader

        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_state_with_scoring()
        stage = BenchmarkStage()
        stage.run(state)

        assert state.executive_summary is not None
        assert isinstance(state.executive_summary, ExecutiveSummary)

        # Snapshot
        assert state.executive_summary.snapshot is not None
        assert state.executive_summary.snapshot.ticker == "TEST"
        assert state.executive_summary.snapshot.company_name == "Test Corp"

        # Inherent risk
        assert state.executive_summary.inherent_risk is not None
        assert state.executive_summary.inherent_risk.sector_base_rate_pct == 6.0

        # Deal context is placeholder
        assert state.executive_summary.deal_context.is_placeholder is True

    def test_validates_score_complete(self) -> None:
        """validate_input rejects if score stage not complete."""
        from do_uw.stages.benchmark import BenchmarkStage

        state = AnalysisState(ticker="TEST")
        stage = BenchmarkStage()

        with pytest.raises(ValueError, match="Score stage must be completed"):
            stage.validate_input(state)

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_stage_marks_completed(
        self, mock_loader_cls: object,
    ) -> None:
        """BenchmarkStage marks itself completed on state."""
        from unittest.mock import MagicMock

        mock_loader = MagicMock()
        mock_brain = MagicMock()
        mock_brain.sectors = _make_sectors_config()
        mock_brain.scoring = _make_scoring_config()
        mock_loader.load_all.return_value = mock_brain
        assert isinstance(mock_loader_cls, MagicMock)
        mock_loader_cls.return_value = mock_loader

        from do_uw.models.common import StageStatus
        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_state_with_scoring()
        stage = BenchmarkStage()
        stage.run(state)

        assert state.stages["benchmark"].status == StageStatus.COMPLETED

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_metric_details_populated(
        self, mock_loader_cls: object,
    ) -> None:
        """BenchmarkResult has metric_details dict."""
        from unittest.mock import MagicMock

        mock_loader = MagicMock()
        mock_brain = MagicMock()
        mock_brain.sectors = _make_sectors_config()
        mock_brain.scoring = _make_scoring_config()
        mock_loader.load_all.return_value = mock_brain
        assert isinstance(mock_loader_cls, MagicMock)
        mock_loader_cls.return_value = mock_loader

        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_state_with_scoring()
        stage = BenchmarkStage()
        stage.run(state)

        assert state.benchmark is not None
        assert len(state.benchmark.metric_details) > 0
        assert "market_cap" in state.benchmark.metric_details
        assert "quality_score" in state.benchmark.metric_details
