"""Tests for market position pipeline integration.

Validates:
- get_market_intelligence with and without pricing data
- check_mispricing for overpriced, underpriced, and within-range
- Graceful degradation when pricing module is unavailable
- Segment label formatting
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from do_uw.knowledge.pricing_analytics import MarketPosition
from do_uw.stages.benchmark.market_position import (
    _build_segment_label,  # pyright: ignore[reportPrivateUsage]
    check_mispricing,
    get_market_intelligence,
)


def _make_position(
    peer_count: int = 12,
    confidence_level: str = "MEDIUM",
    median_rate_on_line: float | None = 0.035,
    mean_rate_on_line: float | None = 0.038,
    ci_low: float | None = 0.031,
    ci_high: float | None = 0.045,
    trend_direction: str = "HARDENING",
    trend_magnitude_pct: float | None = 8.5,
    data_window: str = "2024-01 to 2025-06",
) -> MarketPosition:
    """Create a MarketPosition for testing."""
    return MarketPosition(
        peer_count=peer_count,
        confidence_level=confidence_level,
        median_rate_on_line=median_rate_on_line,
        mean_rate_on_line=mean_rate_on_line,
        ci_low=ci_low,
        ci_high=ci_high,
        percentile_25=0.028 if median_rate_on_line else None,
        percentile_75=0.042 if median_rate_on_line else None,
        min_rate=0.020 if median_rate_on_line else None,
        max_rate=0.060 if median_rate_on_line else None,
        trend_direction=trend_direction,
        trend_magnitude_pct=trend_magnitude_pct,
        data_window=data_window,
    )


# -----------------------------------------------------------------------
# check_mispricing Tests
# -----------------------------------------------------------------------


class TestCheckMispricing:
    """Tests for mispricing detection logic."""

    def test_overpriced_alert(self) -> None:
        """Current ROL 30% above median triggers OVERPRICED alert."""
        result = check_mispricing(
            current_premium=130_000.0,
            current_limit=1_000_000.0,
            median_rate_on_line=0.10,
            peer_count=15,
            ci_low=0.085,
            ci_high=0.115,
        )
        assert result is not None
        assert "OVERPRICED" in result
        assert "30.0%" in result
        assert "above" in result
        assert "n=15" in result
        assert "CI: 0.0850-0.1150" in result

    def test_underpriced_alert(self) -> None:
        """Current ROL 25% below median triggers UNDERPRICED alert."""
        result = check_mispricing(
            current_premium=75_000.0,
            current_limit=1_000_000.0,
            median_rate_on_line=0.10,
            peer_count=20,
            ci_low=0.08,
            ci_high=0.12,
        )
        assert result is not None
        assert "UNDERPRICED" in result
        assert "25.0%" in result
        assert "below" in result
        assert "n=20" in result

    def test_within_range_returns_none(self) -> None:
        """Current ROL 10% above median (under 15% threshold) returns None."""
        result = check_mispricing(
            current_premium=110_000.0,
            current_limit=1_000_000.0,
            median_rate_on_line=0.10,
            peer_count=10,
            ci_low=0.08,
            ci_high=0.12,
        )
        assert result is None

    def test_exact_threshold_returns_none(self) -> None:
        """Exactly at 15% deviation is within range (not strictly greater)."""
        result = check_mispricing(
            current_premium=115_000.0,
            current_limit=1_000_000.0,
            median_rate_on_line=0.10,
            peer_count=10,
            ci_low=None,
            ci_high=None,
        )
        assert result is None

    def test_zero_median_returns_none(self) -> None:
        """Zero median rate returns None (no division error)."""
        result = check_mispricing(
            current_premium=100_000.0,
            current_limit=1_000_000.0,
            median_rate_on_line=0.0,
            peer_count=5,
            ci_low=None,
            ci_high=None,
        )
        assert result is None

    def test_zero_limit_returns_none(self) -> None:
        """Zero limit returns None (no division error)."""
        result = check_mispricing(
            current_premium=100_000.0,
            current_limit=0.0,
            median_rate_on_line=0.10,
            peer_count=5,
            ci_low=None,
            ci_high=None,
        )
        assert result is None

    def test_no_ci_in_alert(self) -> None:
        """Alert with None CI values omits CI string."""
        result = check_mispricing(
            current_premium=200_000.0,
            current_limit=1_000_000.0,
            median_rate_on_line=0.10,
            peer_count=8,
            ci_low=None,
            ci_high=None,
        )
        assert result is not None
        assert "CI:" not in result
        assert "n=8" in result


# -----------------------------------------------------------------------
# _build_segment_label Tests
# -----------------------------------------------------------------------


class TestSegmentLabel:
    """Tests for segment label formatting."""

    def test_tier_and_sector(self) -> None:
        """Combines tier and sector with ' / ' separator."""
        assert _build_segment_label("LARGE", "TECH") == "LARGE / TECH"

    def test_tier_only(self) -> None:
        """Only tier when sector is None."""
        assert _build_segment_label("MID", None) == "MID"

    def test_both_empty(self) -> None:
        """Falls back to ALL SEGMENTS when both empty."""
        assert _build_segment_label("", None) == "ALL SEGMENTS"

    def test_lowercase_tier_uppercased(self) -> None:
        """Tier is uppercased."""
        assert _build_segment_label("large", "tech") == "LARGE / TECH"


# -----------------------------------------------------------------------
# get_market_intelligence Tests
# -----------------------------------------------------------------------


class TestGetMarketIntelligence:
    """Tests for get_market_intelligence pipeline function.

    Uses patch on source modules since get_market_intelligence
    does lazy imports inside the function body.
    """

    @patch("do_uw.knowledge.pricing_analytics.MarketPositionEngine")
    @patch("do_uw.knowledge.pricing_store.PricingStore")
    def test_with_data(
        self, mock_store_cls: MagicMock, mock_engine_cls: MagicMock
    ) -> None:
        """Returns populated MarketIntelligence when pricing data exists."""
        mock_engine = MagicMock()
        mock_engine.get_position_for_analysis.return_value = _make_position()
        mock_engine_cls.return_value = mock_engine

        result = get_market_intelligence(
            ticker="AAPL",
            quality_score=75.0,
            market_cap_tier="MEGA",
            sector="TECH",
        )

        assert result.has_data is True
        assert result.peer_count == 12
        assert result.confidence_level == "MEDIUM"
        assert result.median_rate_on_line == 0.035
        assert result.ci_low == 0.031
        assert result.ci_high == 0.045
        assert result.trend_direction == "HARDENING"
        assert result.trend_magnitude_pct == 8.5
        assert result.data_window == "2024-01 to 2025-06"
        assert result.segment_label == "MEGA / TECH"
        assert result.mispricing_alert is None

    @patch("do_uw.knowledge.pricing_analytics.MarketPositionEngine")
    @patch("do_uw.knowledge.pricing_store.PricingStore")
    def test_no_data(
        self, mock_store_cls: MagicMock, mock_engine_cls: MagicMock
    ) -> None:
        """Returns has_data=False when insufficient pricing data."""
        mock_engine = MagicMock()
        mock_engine.get_position_for_analysis.return_value = _make_position(
            peer_count=1,
            confidence_level="INSUFFICIENT",
            median_rate_on_line=None,
            mean_rate_on_line=None,
            ci_low=None,
            ci_high=None,
            trend_direction="STABLE",
            trend_magnitude_pct=None,
            data_window="",
        )
        mock_engine_cls.return_value = mock_engine

        result = get_market_intelligence(
            ticker="TINY",
            quality_score=60.0,
            market_cap_tier="MICRO",
            sector=None,
        )

        assert result.has_data is False
        assert result.peer_count == 1
        assert result.segment_label == "MICRO"

    @patch("do_uw.knowledge.pricing_analytics.MarketPositionEngine")
    @patch("do_uw.knowledge.pricing_store.PricingStore")
    def test_with_mispricing(
        self, mock_store_cls: MagicMock, mock_engine_cls: MagicMock
    ) -> None:
        """Mispricing alert when current ROL deviates >15%."""
        mock_engine = MagicMock()
        mock_engine.get_position_for_analysis.return_value = _make_position(
            peer_count=20,
            confidence_level="MEDIUM",
            median_rate_on_line=0.04,
            mean_rate_on_line=0.042,
            ci_low=0.035,
            ci_high=0.049,
            trend_direction="STABLE",
            trend_magnitude_pct=None,
            data_window="2024-01 to 2025-12",
        )
        mock_engine_cls.return_value = mock_engine

        # Current ROL = 60k / 1M = 0.06 which is 50% above 0.04
        result = get_market_intelligence(
            ticker="RISK",
            quality_score=45.0,
            market_cap_tier="MID",
            sector="TECH",
            current_premium=60_000.0,
            current_limit=1_000_000.0,
        )

        assert result.has_data is True
        assert result.mispricing_alert is not None
        assert "OVERPRICED" in result.mispricing_alert

    @patch(
        "do_uw.knowledge.pricing_store.PricingStore",
        side_effect=Exception("DB error"),
    )
    def test_store_exception_graceful(
        self, mock_store_cls: MagicMock
    ) -> None:
        """Graceful degradation on PricingStore exception."""
        result = get_market_intelligence(
            ticker="FAIL",
            quality_score=60.0,
            market_cap_tier="MID",
            sector="TECH",
        )
        assert result.has_data is False


# -----------------------------------------------------------------------
# BenchmarkStage integration test
# -----------------------------------------------------------------------


class TestBenchmarkStageMarketIntegration:
    """Test that BenchmarkStage works without pricing data."""

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_stage_without_pricing_data(
        self, mock_loader_cls: MagicMock
    ) -> None:
        """BenchmarkStage completes when no pricing data exists.

        This confirms the non-breaking nature of market intelligence
        integration -- the pipeline works identically without it.
        """
        from do_uw.models.common import Confidence, SourcedValue, StageStatus
        from do_uw.models.company import CompanyIdentity, CompanyProfile
        from do_uw.models.scoring import (
            ScoringResult,
            Tier,
            TierClassification,
        )
        from do_uw.models.state import AnalysisState
        from do_uw.stages.benchmark import BenchmarkStage

        now = datetime.now(tz=UTC)

        def _sv_float(val: float) -> SourcedValue[float]:
            return SourcedValue(
                value=val, source="test", confidence=Confidence.MEDIUM, as_of=now
            )

        def _sv_str(val: str) -> SourcedValue[str]:
            return SourcedValue(
                value=val, source="test", confidence=Confidence.MEDIUM, as_of=now
            )

        def _sv_int(val: int) -> SourcedValue[int]:
            return SourcedValue(
                value=val, source="test", confidence=Confidence.MEDIUM, as_of=now
            )

        mock_loader = MagicMock()
        mock_brain = MagicMock()
        mock_brain.sectors = {
            "claim_base_rates": {"TECH": 6.0, "DEFAULT": 3.9},
            "market_cap_filing_multipliers": {
                "mid": {"min_cap": 2000000000, "multiplier": 1.00},
                "small": {"min_cap": 500000000, "multiplier": 0.90},
                "micro": {"min_cap": 0, "multiplier": 0.77},
                "large": {"min_cap": 10000000000, "multiplier": 1.28},
                "mega": {"min_cap": 50000000000, "multiplier": 1.56},
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
                "mappings": {"TECH": "Technology"},
            },
        }
        mock_brain.scoring = {
            "severity_ranges": {
                "by_market_cap": [
                    {"tier": "MID", "min_cap_b": 2, "max_cap_b": 10, "base_range_m": [8, 40]},
                    {"tier": "SMALL", "min_cap_b": 0.5, "max_cap_b": 2, "base_range_m": [4, 20]},
                    {"tier": "MICRO", "max_cap_b": 0.5, "base_range_m": [2, 10]},
                    {"tier": "LARGE", "min_cap_b": 10, "max_cap_b": 50, "base_range_m": [15, 75]},
                    {"tier": "MEGA", "min_cap_b": 50, "base_range_m": [25, 150]},
                ],
            },
        }
        mock_loader.load_all.return_value = mock_brain
        mock_loader_cls.return_value = mock_loader

        state = AnalysisState(ticker="NODATA")
        for stage in ["resolve", "acquire", "extract", "analyze", "score"]:
            state.mark_stage_running(stage)
            state.mark_stage_completed(stage)

        state.company = CompanyProfile(
            identity=CompanyIdentity(
                ticker="NODATA",
                legal_name=_sv_str("No Data Corp"),
                sic_code=_sv_str("3571"),
                sector=_sv_str("TECH"),
                exchange=_sv_str("NASDAQ"),
            ),
            market_cap=_sv_float(5_000_000_000.0),
            employee_count=_sv_int(5000),
        )
        state.scoring = ScoringResult(
            quality_score=65.0,
            composite_score=65.0,
            tier=TierClassification(
                tier=Tier.WRITE,
                score_range_low=51,
                score_range_high=70,
            ),
        )

        bench = BenchmarkStage()
        bench.run(state)

        # Pipeline completed
        assert state.stages["benchmark"].status == StageStatus.COMPLETED
        assert state.benchmark is not None
        assert state.executive_summary is not None
        # Market intelligence is None or has_data=False
        mi = state.executive_summary.deal_context.market_intelligence
        assert mi is None or mi.has_data is False
