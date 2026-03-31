"""Tests for frames_benchmarker: true percentile computation from Frames data.

Tests cover direct metric percentiles, derived metric percentiles (join by CIK),
missing company handling, empty SIC mapping, and the overall
compute_frames_percentiles() orchestrator.
"""

from __future__ import annotations

import pytest

from do_uw.models.scoring import FramesPercentileResult
from do_uw.stages.benchmark.frames_benchmarker import (
    DERIVED_METRICS,
    _compute_derived_percentile,
    _compute_direct_percentile,
    compute_frames_percentiles,
)


def _make_entities(cik_val_pairs: list[tuple[int, float]]) -> list[dict]:
    """Build synthetic Frames entity data."""
    return [
        {"cik": cik, "val": val, "entityName": f"Entity{cik}"}
        for cik, val in cik_val_pairs
    ]


# SIC mapping for tests: CIK -> SIC code
SAMPLE_SIC_MAP: dict[int, str] = {
    100: "3674",  # Semiconductors
    200: "3674",  # Same sector
    300: "7372",  # Software
    400: "7372",  # Software
    500: "2800",  # Chemicals
    999: "3674",  # Company under test -- same sector as 100, 200
}


class TestDirectPercentile:
    """Test _compute_direct_percentile for single Frames datasets."""

    def test_company_found_overall_percentile(self) -> None:
        """Company CIK in data -- overall percentile computed."""
        data = _make_entities([
            (100, 10.0), (200, 20.0), (300, 30.0), (400, 40.0), (999, 25.0),
        ])
        result = _compute_direct_percentile(
            company_cik=999,
            frames_data=data,
            sic_mapping=SAMPLE_SIC_MAP,
            company_sic="3674",
            higher_is_better=True,
        )
        assert result.overall is not None
        assert result.company_value == 25.0
        assert result.peer_count_overall == 5
        # 25.0 is above 10 and 20 (2 below), equal to self (1 equal)
        # rank = (2 + 0.5*1)/5 * 100 = 50.0
        assert result.overall == pytest.approx(50.0)

    def test_sector_percentile_filters_by_2digit_sic(self) -> None:
        """Sector percentile uses 2-digit SIC prefix filtering."""
        data = _make_entities([
            (100, 10.0), (200, 20.0), (300, 30.0), (400, 40.0), (999, 25.0),
        ])
        result = _compute_direct_percentile(
            company_cik=999,
            frames_data=data,
            sic_mapping=SAMPLE_SIC_MAP,
            company_sic="3674",
            higher_is_better=True,
        )
        assert result.sector is not None
        # Sector "36" includes CIKs 100(10), 200(20), 999(25)
        assert result.peer_count_sector == 3
        # 25 above 10, 20 (2 below), equal to self (1 equal)
        # rank = (2 + 0.5*1)/3 * 100 = 83.33
        assert result.sector == pytest.approx(83.33, abs=0.01)

    def test_missing_company_returns_none(self) -> None:
        """Company CIK not in Frames data returns None percentile."""
        data = _make_entities([(100, 10.0), (200, 20.0)])
        result = _compute_direct_percentile(
            company_cik=999,
            frames_data=data,
            sic_mapping=SAMPLE_SIC_MAP,
            company_sic="3674",
            higher_is_better=True,
        )
        assert result.overall is None
        assert result.sector is None
        assert result.company_value is None

    def test_empty_sic_mapping_returns_none_sector(self) -> None:
        """No SIC mapping means no sector percentile, but overall still works."""
        data = _make_entities([
            (100, 10.0), (200, 20.0), (999, 15.0),
        ])
        result = _compute_direct_percentile(
            company_cik=999,
            frames_data=data,
            sic_mapping={},
            company_sic="3674",
            higher_is_better=True,
        )
        assert result.overall is not None
        assert result.sector is None
        assert result.peer_count_sector == 0

    def test_lower_is_better_metric(self) -> None:
        """For lower-is-better metrics, lower values get higher percentile."""
        data = _make_entities([
            (100, 50.0), (200, 40.0), (300, 30.0), (999, 20.0),
        ])
        result = _compute_direct_percentile(
            company_cik=999,
            frames_data=data,
            sic_mapping={},
            company_sic=None,
            higher_is_better=False,
        )
        # 999 has lowest value (20), with lower_is_better this is best
        # count_above = 3, count_equal = 1, rank = (3 + 0.5*1)/4 * 100 = 87.5
        assert result.overall == pytest.approx(87.5)


class TestDerivedPercentile:
    """Test _compute_derived_percentile for ratio metrics (join two datasets)."""

    def test_derived_ratio_computed(self) -> None:
        """Derived metric joins two datasets by CIK and computes ratio."""
        numerator = _make_entities([
            (100, 100.0), (200, 200.0), (300, 300.0), (999, 150.0),
        ])
        denominator = _make_entities([
            (100, 50.0), (200, 100.0), (300, 50.0), (999, 100.0),
        ])
        result = _compute_derived_percentile(
            company_cik=999,
            numerator_data=numerator,
            denominator_data=denominator,
            sic_mapping=SAMPLE_SIC_MAP,
            company_sic="3674",
            higher_is_better=True,
        )
        # Ratios: 100->2.0, 200->2.0, 300->6.0, 999->1.5
        # Company ratio = 1.5
        # count_below = 0, count_equal = 1
        # rank = (0 + 0.5*1)/4 * 100 = 12.5
        assert result.overall == pytest.approx(12.5)
        assert result.company_value == pytest.approx(1.5)

    def test_inner_join_skips_missing_entities(self) -> None:
        """Only entities with both numerator and denominator are included."""
        numerator = _make_entities([
            (100, 100.0), (200, 200.0), (999, 150.0),
        ])
        denominator = _make_entities([
            (100, 50.0), (300, 75.0), (999, 100.0),
        ])
        result = _compute_derived_percentile(
            company_cik=999,
            numerator_data=numerator,
            denominator_data=denominator,
            sic_mapping={},
            company_sic=None,
            higher_is_better=True,
        )
        # Only CIKs 100 and 999 have both: 100->2.0, 999->1.5
        assert result.peer_count_overall == 2
        assert result.company_value == pytest.approx(1.5)

    def test_division_by_zero_skipped(self) -> None:
        """Entities with zero denominator are excluded from ratios."""
        numerator = _make_entities([
            (100, 100.0), (200, 200.0), (999, 150.0),
        ])
        denominator = _make_entities([
            (100, 0.0), (200, 100.0), (999, 75.0),
        ])
        result = _compute_derived_percentile(
            company_cik=999,
            numerator_data=numerator,
            denominator_data=denominator,
            sic_mapping={},
            company_sic=None,
            higher_is_better=True,
        )
        # CIK 100 excluded (zero denom): 200->2.0, 999->2.0
        assert result.peer_count_overall == 2
        assert result.company_value == pytest.approx(2.0)

    def test_company_missing_from_derived(self) -> None:
        """Company CIK not in one dataset returns None percentile."""
        numerator = _make_entities([(100, 100.0), (200, 200.0)])
        denominator = _make_entities([(100, 50.0), (200, 100.0), (999, 75.0)])
        result = _compute_derived_percentile(
            company_cik=999,
            numerator_data=numerator,
            denominator_data=denominator,
            sic_mapping={},
            company_sic=None,
            higher_is_better=True,
        )
        assert result.overall is None
        assert result.company_value is None


class TestComputeFramesPercentiles:
    """Test the top-level compute_frames_percentiles orchestrator."""

    def test_returns_dict_with_direct_and_derived_metrics(self) -> None:
        """Result includes both direct and derived metric keys."""
        # Build minimal frames data for revenue + total_assets
        frames_data = {
            "revenue": _make_entities([
                (100, 1000.0), (200, 2000.0), (999, 1500.0),
            ]),
            "total_assets": _make_entities([
                (100, 5000.0), (200, 8000.0), (999, 6000.0),
            ]),
            # Need both components for derived metrics
            "current_assets": _make_entities([
                (100, 500.0), (200, 800.0), (999, 600.0),
            ]),
            "current_liabilities": _make_entities([
                (100, 250.0), (200, 400.0), (999, 200.0),
            ]),
            "total_liabilities": _make_entities([
                (100, 3000.0), (200, 5000.0), (999, 4000.0),
            ]),
            "total_equity": _make_entities([
                (100, 2000.0), (200, 3000.0), (999, 2000.0),
            ]),
            "operating_income": _make_entities([
                (100, 100.0), (200, 200.0), (999, 150.0),
            ]),
            "net_income": _make_entities([
                (100, 80.0), (200, 150.0), (999, 120.0),
            ]),
            "cash_from_operations": _make_entities([
                (100, 200.0), (200, 400.0), (999, 300.0),
            ]),
            "rd_expense": _make_entities([
                (100, 50.0), (200, 100.0), (999, 75.0),
            ]),
        }

        result = compute_frames_percentiles(
            frames_data=frames_data,
            company_cik=999,
            company_sic="3674",
            sic_mapping=SAMPLE_SIC_MAP,
        )

        assert isinstance(result, dict)
        # Should have direct metrics
        assert "revenue" in result
        assert "total_assets" in result
        # Should have derived metrics
        assert "current_ratio" in result
        assert "debt_to_equity" in result
        assert "operating_margin" in result
        assert "net_margin" in result
        assert "roe" in result
        # All should be FramesPercentileResult
        for key, val in result.items():
            assert isinstance(val, FramesPercentileResult), f"{key} not FramesPercentileResult"

    def test_empty_frames_data_returns_empty_dict(self) -> None:
        """No frames data produces empty result."""
        result = compute_frames_percentiles(
            frames_data={},
            company_cik=999,
            company_sic="3674",
            sic_mapping=SAMPLE_SIC_MAP,
        )
        assert result == {}

    def test_missing_metric_skipped_gracefully(self) -> None:
        """Missing metric in frames_data is skipped, not errored."""
        frames_data = {
            "revenue": _make_entities([(100, 1000.0), (999, 500.0)]),
        }
        result = compute_frames_percentiles(
            frames_data=frames_data,
            company_cik=999,
            company_sic=None,
            sic_mapping={},
        )
        # revenue should be present
        assert "revenue" in result
        # derived metrics needing missing data should not be present
        assert "current_ratio" not in result

    def test_all_15_metrics_covered_with_full_data(self) -> None:
        """With full data, all 8 direct + 5 derived = 13 metrics are computed."""
        frames_data = {
            "revenue": _make_entities([(100, 1000.0), (999, 500.0)]),
            "net_income": _make_entities([(100, 100.0), (999, 50.0)]),
            "total_assets": _make_entities([(100, 5000.0), (999, 3000.0)]),
            "total_equity": _make_entities([(100, 2000.0), (999, 1000.0)]),
            "total_liabilities": _make_entities([(100, 3000.0), (999, 2000.0)]),
            "operating_income": _make_entities([(100, 200.0), (999, 100.0)]),
            "cash_from_operations": _make_entities([(100, 300.0), (999, 150.0)]),
            "rd_expense": _make_entities([(100, 50.0), (999, 25.0)]),
            "current_assets": _make_entities([(100, 500.0), (999, 300.0)]),
            "current_liabilities": _make_entities([(100, 250.0), (999, 150.0)]),
        }
        result = compute_frames_percentiles(
            frames_data=frames_data,
            company_cik=999,
            company_sic="3674",
            sic_mapping=SAMPLE_SIC_MAP,
        )
        # 10 direct (incl. 2 component-only) + 5 derived = 15 total
        assert len(result) == 15
