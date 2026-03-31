"""Tests for Peer Outlier engine (PAT-02).

Validates:
- Multi-dimensional statistical outlier detection from SEC Frames data
- MAD-based z-score computation
- Graceful degradation on missing/insufficient data
- higher_is_better direction handling
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.scoring import BenchmarkResult, FramesPercentileResult
from do_uw.stages.score.pattern_engine import EngineResult, PatternEngine


def _make_frames_percentile(
    *,
    company_value: float | None = None,
    sector: float | None = None,
    peer_count_sector: int = 0,
    higher_is_better: bool = True,
) -> FramesPercentileResult:
    """Build a FramesPercentileResult for testing."""
    return FramesPercentileResult(
        overall=50.0,
        sector=sector,
        peer_count_overall=100,
        peer_count_sector=peer_count_sector,
        company_value=company_value,
        higher_is_better=higher_is_better,
    )


def _make_state(
    frames_percentiles: dict[str, FramesPercentileResult] | None = None,
) -> MagicMock:
    """Build a mock state with benchmarks.frames_percentiles."""
    state = MagicMock()
    if frames_percentiles is not None:
        state.benchmarks = BenchmarkResult(frames_percentiles=frames_percentiles)
    else:
        state.benchmarks = None
    return state


class TestPeerOutlierProtocol:
    """Verify PeerOutlierEngine implements PatternEngine Protocol."""

    def test_implements_protocol(self) -> None:
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        engine = PeerOutlierEngine()
        assert isinstance(engine, PatternEngine)

    def test_engine_id(self) -> None:
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        engine = PeerOutlierEngine()
        assert engine.engine_id == "peer_outlier"

    def test_engine_name(self) -> None:
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        engine = PeerOutlierEngine()
        assert engine.engine_name == "Peer Outlier"


class TestPeerOutlierFired:
    """Test cases where peer outlier should fire."""

    def test_10_plus_peers_z_gt_3_on_3_metrics_fires(self) -> None:
        """10+ peers and company z > 3.0 on 3+ metrics => fired=True."""
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        # Build frames_percentiles with extreme outlier values
        # Company has very extreme values compared to peers
        frames = {
            "profit_margin": _make_frames_percentile(
                company_value=0.01,  # 1% margin, very low
                sector=50.0,
                peer_count_sector=50,
                higher_is_better=True,
            ),
            "debt_to_equity": _make_frames_percentile(
                company_value=8.0,  # Very high leverage
                sector=50.0,
                peer_count_sector=50,
                higher_is_better=False,
            ),
            "current_ratio": _make_frames_percentile(
                company_value=0.2,  # Very low liquidity
                sector=50.0,
                peer_count_sector=50,
                higher_is_better=True,
            ),
            "revenue_growth": _make_frames_percentile(
                company_value=-0.30,  # -30% decline
                sector=50.0,
                peer_count_sector=50,
                higher_is_better=True,
            ),
        }

        state = _make_state(frames)

        # Provide peer data that makes the company an extreme outlier
        # We inject peer_values directly via constructor for testability
        peer_data = {
            "profit_margin": [0.15, 0.12, 0.18, 0.14, 0.16, 0.13, 0.17, 0.11, 0.19, 0.15, 0.14, 0.16],
            "debt_to_equity": [1.0, 1.2, 0.8, 1.1, 0.9, 1.3, 0.7, 1.0, 1.2, 0.8, 1.1, 0.9],
            "current_ratio": [1.5, 1.8, 1.3, 1.6, 1.4, 1.7, 1.2, 1.5, 1.8, 1.3, 1.6, 1.4],
            "revenue_growth": [0.05, 0.08, 0.03, 0.06, 0.04, 0.07, 0.02, 0.05, 0.08, 0.03, 0.06, 0.04],
        }

        engine = PeerOutlierEngine(peer_data_override=peer_data)
        result = engine.evaluate({}, state=state)

        assert isinstance(result, EngineResult)
        assert result.fired is True
        assert len(result.findings) >= 3

    def test_3_metrics_z_gt_2_multi_dimensional_fires(self) -> None:
        """3 metrics with z > 2.0 (multi-dimensional) but none > 3.0 => fired=True."""
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        frames = {
            "profit_margin": _make_frames_percentile(
                company_value=0.05,  # Moderately low
                sector=50.0,
                peer_count_sector=20,
                higher_is_better=True,
            ),
            "debt_to_equity": _make_frames_percentile(
                company_value=3.0,  # Moderately high
                sector=50.0,
                peer_count_sector=20,
                higher_is_better=False,
            ),
            "current_ratio": _make_frames_percentile(
                company_value=0.6,  # Moderately low
                sector=50.0,
                peer_count_sector=20,
                higher_is_better=True,
            ),
        }

        state = _make_state(frames)

        # Peer data where company is moderately outlying (z ~2.5)
        peer_data = {
            "profit_margin": [0.12, 0.13, 0.14, 0.11, 0.15, 0.12, 0.13, 0.14, 0.11, 0.15,
                              0.12, 0.13, 0.14, 0.11, 0.15, 0.12, 0.13, 0.14, 0.11, 0.15],
            "debt_to_equity": [1.0, 1.1, 0.9, 1.2, 0.8, 1.0, 1.1, 0.9, 1.2, 0.8,
                               1.0, 1.1, 0.9, 1.2, 0.8, 1.0, 1.1, 0.9, 1.2, 0.8],
            "current_ratio": [1.5, 1.6, 1.4, 1.7, 1.3, 1.5, 1.6, 1.4, 1.7, 1.3,
                              1.5, 1.6, 1.4, 1.7, 1.3, 1.5, 1.6, 1.4, 1.7, 1.3],
        }

        engine = PeerOutlierEngine(peer_data_override=peer_data)
        result = engine.evaluate({}, state=state)

        assert result.fired is True

    def test_higher_is_better_false_extreme_high_flagged(self) -> None:
        """higher_is_better=False metric with extreme HIGH value => flagged as outlier."""
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        frames = {
            "debt_to_equity": _make_frames_percentile(
                company_value=10.0,  # Extremely high debt
                sector=50.0,
                peer_count_sector=30,
                higher_is_better=False,
            ),
            "sga_to_revenue": _make_frames_percentile(
                company_value=0.80,  # Very high SGA
                sector=50.0,
                peer_count_sector=30,
                higher_is_better=False,
            ),
            "receivable_days": _make_frames_percentile(
                company_value=120.0,  # Very long receivable period
                sector=50.0,
                peer_count_sector=30,
                higher_is_better=False,
            ),
        }

        state = _make_state(frames)

        peer_data = {
            "debt_to_equity": [1.0, 1.2, 0.8, 1.1, 0.9, 1.3, 0.7, 1.0, 1.2, 0.8,
                               1.1, 0.9, 1.3, 0.7, 1.0, 1.2, 0.8, 1.1, 0.9, 1.3,
                               0.7, 1.0, 1.2, 0.8, 1.1, 0.9, 1.3, 0.7, 1.0, 1.2],
            "sga_to_revenue": [0.25, 0.28, 0.22, 0.30, 0.20, 0.27, 0.23, 0.29, 0.21, 0.26,
                               0.25, 0.28, 0.22, 0.30, 0.20, 0.27, 0.23, 0.29, 0.21, 0.26,
                               0.25, 0.28, 0.22, 0.30, 0.20, 0.27, 0.23, 0.29, 0.21, 0.26],
            "receivable_days": [30, 35, 28, 32, 27, 33, 29, 31, 34, 26,
                                30, 35, 28, 32, 27, 33, 29, 31, 34, 26,
                                30, 35, 28, 32, 27, 33, 29, 31, 34, 26],
        }

        engine = PeerOutlierEngine(peer_data_override=peer_data)
        result = engine.evaluate({}, state=state)

        assert result.fired is True
        # Verify outlier metrics are flagged
        outlier_metrics = {f["metric"] for f in result.findings}
        assert "debt_to_equity" in outlier_metrics


class TestPeerOutlierNotFired:
    """Test cases where peer outlier should NOT fire."""

    def test_fewer_than_10_peers_not_fired(self) -> None:
        """Fewer than 10 peers on all metrics => fired=False."""
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        frames = {
            "profit_margin": _make_frames_percentile(
                company_value=0.01,
                sector=50.0,
                peer_count_sector=5,  # Too few
                higher_is_better=True,
            ),
        }

        state = _make_state(frames)
        engine = PeerOutlierEngine()
        result = engine.evaluate({}, state=state)

        assert result.fired is False
        assert "Insufficient" in result.headline

    def test_z_scores_below_2_not_fired(self) -> None:
        """z-scores all below 2.0 => fired=False."""
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        frames = {
            "profit_margin": _make_frames_percentile(
                company_value=0.13,  # Normal
                sector=50.0,
                peer_count_sector=30,
                higher_is_better=True,
            ),
            "debt_to_equity": _make_frames_percentile(
                company_value=1.1,  # Normal
                sector=50.0,
                peer_count_sector=30,
                higher_is_better=False,
            ),
            "current_ratio": _make_frames_percentile(
                company_value=1.5,  # Normal
                sector=50.0,
                peer_count_sector=30,
                higher_is_better=True,
            ),
        }

        state = _make_state(frames)

        # Peer data similar to company values
        peer_data = {
            "profit_margin": [0.12, 0.14, 0.11, 0.15, 0.13, 0.12, 0.14, 0.11, 0.15, 0.13,
                              0.12, 0.14, 0.11, 0.15, 0.13, 0.12, 0.14, 0.11, 0.15, 0.13,
                              0.12, 0.14, 0.11, 0.15, 0.13, 0.12, 0.14, 0.11, 0.15, 0.13],
            "debt_to_equity": [1.0, 1.2, 0.9, 1.1, 1.0, 1.2, 0.9, 1.1, 1.0, 1.2,
                               0.9, 1.1, 1.0, 1.2, 0.9, 1.1, 1.0, 1.2, 0.9, 1.1,
                               0.9, 1.1, 1.0, 1.2, 0.9, 1.1, 1.0, 1.2, 0.9, 1.1],
            "current_ratio": [1.4, 1.6, 1.3, 1.5, 1.4, 1.6, 1.3, 1.5, 1.4, 1.6,
                              1.3, 1.5, 1.4, 1.6, 1.3, 1.5, 1.4, 1.6, 1.3, 1.5,
                              1.3, 1.5, 1.4, 1.6, 1.3, 1.5, 1.4, 1.6, 1.3, 1.5],
        }

        engine = PeerOutlierEngine(peer_data_override=peer_data)
        result = engine.evaluate({}, state=state)

        assert result.fired is False

    def test_only_1_outlier_metric_not_fired(self) -> None:
        """Only 1 outlier metric => fired=False (needs 3+ per design doc)."""
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        frames = {
            "profit_margin": _make_frames_percentile(
                company_value=0.01,  # Extreme outlier
                sector=50.0,
                peer_count_sector=30,
                higher_is_better=True,
            ),
            "debt_to_equity": _make_frames_percentile(
                company_value=1.0,  # Normal
                sector=50.0,
                peer_count_sector=30,
                higher_is_better=False,
            ),
            "current_ratio": _make_frames_percentile(
                company_value=1.5,  # Normal
                sector=50.0,
                peer_count_sector=30,
                higher_is_better=True,
            ),
        }

        state = _make_state(frames)

        peer_data = {
            "profit_margin": [0.15, 0.12, 0.18, 0.14, 0.16, 0.13, 0.17, 0.11, 0.19, 0.15,
                              0.14, 0.16, 0.15, 0.12, 0.18, 0.14, 0.16, 0.13, 0.17, 0.11,
                              0.19, 0.15, 0.14, 0.16, 0.15, 0.12, 0.18, 0.14, 0.16, 0.13],
            "debt_to_equity": [1.0, 1.1, 0.9, 1.2, 0.8, 1.0, 1.1, 0.9, 1.2, 0.8,
                               1.0, 1.1, 0.9, 1.2, 0.8, 1.0, 1.1, 0.9, 1.2, 0.8,
                               1.0, 1.1, 0.9, 1.2, 0.8, 1.0, 1.1, 0.9, 1.2, 0.8],
            "current_ratio": [1.5, 1.6, 1.4, 1.7, 1.3, 1.5, 1.6, 1.4, 1.7, 1.3,
                              1.5, 1.6, 1.4, 1.7, 1.3, 1.5, 1.6, 1.4, 1.7, 1.3,
                              1.5, 1.6, 1.4, 1.7, 1.3, 1.5, 1.6, 1.4, 1.7, 1.3],
        }

        engine = PeerOutlierEngine(peer_data_override=peer_data)
        result = engine.evaluate({}, state=state)

        assert result.fired is False

    def test_none_company_values_skipped(self) -> None:
        """None company_value metrics should be skipped."""
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        frames = {
            "profit_margin": _make_frames_percentile(
                company_value=None,  # Missing
                sector=50.0,
                peer_count_sector=30,
                higher_is_better=True,
            ),
        }

        state = _make_state(frames)
        engine = PeerOutlierEngine()
        result = engine.evaluate({}, state=state)

        assert result.fired is False

    def test_empty_frames_percentiles_not_fired(self) -> None:
        """Empty frames_percentiles => NOT_FIRED."""
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        state = _make_state({})
        engine = PeerOutlierEngine()
        result = engine.evaluate({}, state=state)

        assert result.fired is False
        assert "Insufficient" in result.headline

    def test_no_benchmarks_not_fired(self) -> None:
        """No benchmarks on state => NOT_FIRED."""
        from do_uw.stages.score.peer_outlier import PeerOutlierEngine

        state = _make_state(None)
        engine = PeerOutlierEngine()
        result = engine.evaluate({}, state=state)

        assert result.fired is False
        assert "Insufficient" in result.headline
