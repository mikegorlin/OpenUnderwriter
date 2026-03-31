"""Tests for weighted CRF compounding algorithm.

Verifies that multiple triggered CRFs compound downward, with a floor at 5.
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.models.scoring import RedFlagResult
from do_uw.stages.score.red_flag_gates import apply_crf_ceilings


def _make_scoring_config() -> dict[str, Any]:
    """Build scoring config with severity weights on all CRFs."""
    return {
        "critical_red_flag_ceilings": {
            "ceilings": [
                {
                    "id": "CRF-001",
                    "max_quality_score": 30,
                    "max_tier": "WALK",
                    "size_severity_matrix": {
                        "mega_cap": {"threshold_usd": 100_000_000_000, "ceiling": 70, "max_tier": "WRITE"},
                        "large_cap": {"threshold_usd": 10_000_000_000, "ceiling": 55, "max_tier": "WRITE"},
                        "mid_cap": {"threshold_usd": 2_000_000_000, "ceiling": 40, "max_tier": "WATCH"},
                        "small_cap": {"threshold_usd": 500_000_000, "ceiling": 30, "max_tier": "WALK"},
                        "micro_cap": {"threshold_usd": 0, "ceiling": 25, "max_tier": "WALK"},
                    },
                    "severity_weight": 0.30,
                },
                {"id": "CRF-002", "max_quality_score": 30, "max_tier": "WALK", "severity_weight": 0.25},
                {"id": "CRF-003", "max_quality_score": 30, "max_tier": "WALK", "severity_weight": 0.30},
                {"id": "CRF-004", "max_quality_score": 50, "max_tier": "WATCH", "severity_weight": 0.20},
                {"id": "CRF-005", "max_quality_score": 50, "max_tier": "WATCH", "severity_weight": 0.20},
                {"id": "CRF-006", "max_quality_score": 50, "max_tier": "WATCH", "severity_weight": 0.10},
                {"id": "CRF-007", "max_quality_score": 50, "max_tier": "WATCH", "severity_weight": 0.10},
                {
                    "id": "CRF-008",
                    "max_quality_score": 50,
                    "max_tier": "WATCH",
                    "size_severity_matrix": {
                        "mega_cap": {"threshold_usd": 100_000_000_000, "ceiling": 65, "max_tier": "WRITE"},
                        "large_cap": {"threshold_usd": 10_000_000_000, "ceiling": 55, "max_tier": "WRITE"},
                        "mid_cap": {"threshold_usd": 2_000_000_000, "ceiling": 45, "max_tier": "WATCH"},
                        "small_cap": {"threshold_usd": 500_000_000, "ceiling": 35, "max_tier": "WALK"},
                        "micro_cap": {"threshold_usd": 0, "ceiling": 25, "max_tier": "WALK"},
                    },
                    "severity_weight": 0.20,
                },
                {"id": "CRF-009", "max_quality_score": 50, "max_tier": "WATCH", "severity_weight": 0.05},
                {"id": "CRF-010", "max_quality_score": 50, "max_tier": "WATCH", "severity_weight": 0.08},
                {"id": "CRF-011", "max_quality_score": 50, "max_tier": "WATCH", "severity_weight": 0.10},
                {
                    "id": "CRF-013",
                    "max_quality_score": 25,
                    "max_tier": "WALK",
                    "distress_graduation": {
                        "going_concern": {"ceiling": 15, "max_tier": "NO_TOUCH"},
                        "severe": {"z_max": 1.0, "negative_equity": True, "ceiling": 20, "max_tier": "WALK"},
                        "distress": {"z_max": 1.81, "ceiling": 40, "max_tier": "WATCH"},
                        "gray": {"z_max": 2.99, "ceiling": 55, "max_tier": "WRITE"},
                    },
                    "severity_weight": 0.25,
                },
            ]
        }
    }


def _rf(flag_id: str) -> RedFlagResult:
    """Shorthand for a triggered RedFlagResult."""
    return RedFlagResult(
        flag_id=flag_id,
        flag_name=f"Test {flag_id}",
        triggered=True,
        ceiling_applied=30,
        max_tier="WALK",
        evidence=["test"],
    )


class TestSingleCRFNoCompounding:
    """With 1 CRF, no compounding occurs."""

    def test_single_crf_no_compounding(self) -> None:
        """1 triggered CRF: ceiling equals that CRF's size-resolved ceiling."""
        cfg = _make_scoring_config()
        results = [_rf("CRF-1")]
        score, binding_id, details = apply_crf_ceilings(
            composite_score=90.0,
            red_flag_results=results,
            scoring_config=cfg,
            market_cap=3.6e12,  # mega-cap
        )
        # CRF-1 mega-cap ceiling is 70, no compounding
        assert score == 70.0


class TestMultipleCRFsCompound:
    """Multiple CRFs compound downward."""

    def test_multiple_crfs_compound_downward(self) -> None:
        """3 triggered CRFs produce a lower ceiling than primary alone."""
        cfg = _make_scoring_config()
        results = [_rf("CRF-1"), _rf("CRF-2"), _rf("CRF-8")]
        score, binding_id, details = apply_crf_ceilings(
            composite_score=90.0,
            red_flag_results=results,
            scoring_config=cfg,
            market_cap=3.26e8,  # micro-cap
        )
        # Primary ceiling: CRF-8 micro=25 or CRF-1 micro=25 (both 25)
        # Additional CRFs compound downward
        assert score < 25.0

    def test_17_crfs_compound_severely(self) -> None:
        """17 triggered CRFs produce ceiling in 5-15 range."""
        cfg = _make_scoring_config()
        # Build 17 triggered CRFs (use all from config + extras)
        all_ids = [
            "CRF-1", "CRF-2", "CRF-3", "CRF-4", "CRF-5",
            "CRF-6", "CRF-7", "CRF-8", "CRF-9", "CRF-10",
            "CRF-11", "CRF-13",
            # Additional CRFs not in config (use default weight)
            "CRF-12", "CRF-14", "CRF-15", "CRF-16", "CRF-17",
        ]
        results = [_rf(cid) for cid in all_ids]
        score, binding_id, details = apply_crf_ceilings(
            composite_score=84.5,
            red_flag_results=results,
            scoring_config=cfg,
            market_cap=3.26e8,  # micro-cap
        )
        assert 5 <= score <= 15

    def test_compounding_floor_at_5(self) -> None:
        """Even extreme compounding never goes below 5."""
        cfg = _make_scoring_config()
        # Many high-weight CRFs
        results = [_rf(f"CRF-{i}") for i in range(1, 20)]
        score, binding_id, details = apply_crf_ceilings(
            composite_score=100.0,
            red_flag_results=results,
            scoring_config=cfg,
            market_cap=3.26e8,
        )
        assert score >= 5.0


class TestCompoundingDetails:
    """Verify ceiling_details are returned for debugging."""

    def test_details_returned(self) -> None:
        """apply_crf_ceilings returns ceiling_details list."""
        cfg = _make_scoring_config()
        results = [_rf("CRF-1"), _rf("CRF-2")]
        _, _, details = apply_crf_ceilings(
            composite_score=90.0,
            red_flag_results=results,
            scoring_config=cfg,
            market_cap=5e10,
        )
        assert isinstance(details, list)
        assert len(details) >= 2
        # Each detail should have crf_id and resolved_ceiling
        for d in details:
            assert "crf_id" in d
            assert "resolved_ceiling" in d
