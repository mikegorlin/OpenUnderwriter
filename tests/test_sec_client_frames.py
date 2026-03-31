"""Tests for SEC Frames API client.

Tests acquisition of cross-filer XBRL data via Frames API and
incremental CIK-to-SIC mapping from SEC submissions API.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_frames_response(
    tag: str = "Revenues",
    period: str = "CY2024",
    entity_count: int = 3,
) -> dict[str, Any]:
    """Build a synthetic Frames API JSON response."""
    data = [
        {
            "accn": f"0000{i:06d}-24-000001",
            "cik": 100 + i,
            "entityName": f"Corp {i}",
            "loc": "US",
            "end": "2024-12-31",
            "val": (i + 1) * 1_000_000,
        }
        for i in range(entity_count)
    ]
    return {
        "taxonomy": "us-gaap",
        "tag": tag,
        "ccp": period,
        "uom": "USD",
        "label": tag,
        "description": f"Test {tag}",
        "pts": entity_count,
        "data": data,
    }


def _make_submissions_response(cik: int, sic: str = "3571") -> dict[str, Any]:
    """Build a synthetic submissions API response."""
    return {
        "cik": str(cik),
        "entityType": "operating",
        "sic": sic,
        "sicDescription": "Test Industry",
        "name": f"Corp {cik}",
    }


@pytest.fixture()
def mock_cache() -> MagicMock:
    """Return a mock AnalysisCache that always misses."""
    cache = MagicMock()
    cache.get.return_value = None
    return cache


# ---------------------------------------------------------------------------
# _build_period_string tests
# ---------------------------------------------------------------------------

class TestBuildPeriodString:
    """Test period string construction for Frames API."""

    def test_duration_format(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            _build_period_string,
        )
        assert _build_period_string("duration", 2024) == "CY2024"

    def test_instant_format(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            _build_period_string,
        )
        assert _build_period_string("instant", 2024) == "CY2024I"

    def test_duration_different_year(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            _build_period_string,
        )
        assert _build_period_string("duration", 2023) == "CY2023"

    def test_instant_different_year(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            _build_period_string,
        )
        assert _build_period_string("instant", 2023) == "CY2023I"


# ---------------------------------------------------------------------------
# _determine_best_period tests
# ---------------------------------------------------------------------------

class TestDetermineBestPeriod:
    """Test period selection logic."""

    def test_uses_company_10k_year(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            _determine_best_period,
        )
        assert _determine_best_period(2024) == 2024

    def test_falls_back_to_prior_year_when_none(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            _determine_best_period,
        )
        # When no 10-K year provided, should use current_year - 1
        result = _determine_best_period(None)
        # Should be a reasonable recent year
        assert isinstance(result, int)
        assert result >= 2023


# ---------------------------------------------------------------------------
# FRAMES_METRICS registry tests
# ---------------------------------------------------------------------------

class TestFramesMetricsRegistry:
    """Test the metric registry has all required entries."""

    def test_registry_has_10_entries(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            FRAMES_METRICS,
        )
        assert len(FRAMES_METRICS) == 10

    def test_registry_has_all_required_tags(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            FRAMES_METRICS,
        )
        required_tags = {
            "Revenues",
            "NetIncomeLoss",
            "Assets",
            "StockholdersEquity",
            "Liabilities",
            "OperatingIncomeLoss",
            "NetCashProvidedByOperatingActivities",
            "ResearchAndDevelopmentExpense",
            "AssetsCurrent",
            "LiabilitiesCurrent",
        }
        actual_tags = {m.xbrl_tag for m in FRAMES_METRICS}
        assert actual_tags == required_tags

    def test_registry_period_types(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            FRAMES_METRICS,
        )
        tag_to_period = {m.xbrl_tag: m.period_type for m in FRAMES_METRICS}
        # Duration metrics (income statement / cash flow)
        assert tag_to_period["Revenues"] == "duration"
        assert tag_to_period["NetIncomeLoss"] == "duration"
        # Instant metrics (balance sheet)
        assert tag_to_period["Assets"] == "instant"
        assert tag_to_period["StockholdersEquity"] == "instant"
        assert tag_to_period["AssetsCurrent"] == "instant"

    def test_metric_names_unique(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            FRAMES_METRICS,
        )
        names = [m.metric_name for m in FRAMES_METRICS]
        assert len(names) == len(set(names))


# ---------------------------------------------------------------------------
# acquire_frames tests
# ---------------------------------------------------------------------------

class TestAcquireFrames:
    """Test Frames API acquisition with mocked HTTP."""

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_returns_dict_keyed_by_metric_name(
        self, mock_sec_get: MagicMock, mock_cache: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_frames,
        )

        mock_sec_get.return_value = _make_frames_response()
        result = acquire_frames(
            company_cik=100, company_10k_year=2024, cache=mock_cache,
        )
        assert isinstance(result, dict)
        # Should have entries for each metric
        assert "revenue" in result
        assert "total_assets" in result

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_returns_data_list_per_metric(
        self, mock_sec_get: MagicMock, mock_cache: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_frames,
        )

        mock_sec_get.return_value = _make_frames_response(entity_count=5)
        result = acquire_frames(
            company_cik=100, company_10k_year=2024, cache=mock_cache,
        )
        # Each metric value should be a list of entity dicts
        for metric_data in result.values():
            assert isinstance(metric_data, list)
            if metric_data:  # Non-empty
                assert "cik" in metric_data[0]
                assert "val" in metric_data[0]

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_caches_with_180_day_ttl_for_completed_period(
        self, mock_sec_get: MagicMock, mock_cache: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_frames,
        )

        mock_sec_get.return_value = _make_frames_response()
        # Use a year well in the past (definitely completed)
        acquire_frames(
            company_cik=100, company_10k_year=2023, cache=mock_cache,
        )
        # Cache should have been called with 180-day TTL
        set_calls = mock_cache.set.call_args_list
        assert len(set_calls) > 0
        for c in set_calls:
            ttl = c.kwargs.get("ttl") or c[1].get("ttl", 0)
            assert ttl == 180 * 24 * 3600, f"Expected 180-day TTL, got {ttl}"

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_uses_cache_hit(
        self, mock_sec_get: MagicMock, mock_cache: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_frames,
        )

        # Make cache return data for ALL keys
        cached_data = [{"cik": 100, "val": 999}]
        mock_cache.get.return_value = cached_data

        result = acquire_frames(
            company_cik=100, company_10k_year=2024, cache=mock_cache,
        )
        # Should NOT have called sec_get since cache hit
        mock_sec_get.assert_not_called()
        # All metrics should have the cached data
        for metric_data in result.values():
            assert metric_data == cached_data

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_handles_api_error_gracefully(
        self, mock_sec_get: MagicMock, mock_cache: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_frames,
        )

        # First call succeeds, rest fail
        mock_sec_get.side_effect = [
            _make_frames_response(),  # First metric succeeds
        ] + [Exception("API Error")] * 20  # Rest fail

        result = acquire_frames(
            company_cik=100, company_10k_year=2024, cache=mock_cache,
        )
        # Should have partial results (at least one metric)
        assert isinstance(result, dict)
        non_empty = [k for k, v in result.items() if v]
        assert len(non_empty) >= 1

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_works_without_cache(
        self, mock_sec_get: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_frames,
        )

        mock_sec_get.return_value = _make_frames_response()
        result = acquire_frames(
            company_cik=100, company_10k_year=2024, cache=None,
        )
        assert isinstance(result, dict)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# acquire_sic_mapping tests
# ---------------------------------------------------------------------------

class TestAcquireSicMapping:
    """Test CIK-to-SIC mapping acquisition."""

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_returns_cik_to_sic_dict(
        self, mock_sec_get: MagicMock, mock_cache: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_sic_mapping,
        )

        mock_sec_get.return_value = _make_submissions_response(100, "3571")
        result = acquire_sic_mapping({100}, cache=mock_cache)
        assert isinstance(result, dict)
        assert result[100] == "3571"

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_caches_with_90_day_ttl(
        self, mock_sec_get: MagicMock, mock_cache: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_sic_mapping,
        )

        mock_sec_get.return_value = _make_submissions_response(100, "3571")
        acquire_sic_mapping({100}, cache=mock_cache)

        set_calls = mock_cache.set.call_args_list
        assert len(set_calls) > 0
        for c in set_calls:
            ttl = c.kwargs.get("ttl") or c[1].get("ttl", 0)
            assert ttl == 90 * 24 * 3600

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_skips_cached_ciks(
        self, mock_sec_get: MagicMock, mock_cache: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_sic_mapping,
        )

        # CIK 100 is cached, CIK 200 is not
        def cache_get(key: str) -> Any:
            if key == "sec:sic:100":
                return "3571"
            return None

        mock_cache.get.side_effect = cache_get
        mock_sec_get.return_value = _make_submissions_response(200, "7372")

        result = acquire_sic_mapping({100, 200}, cache=mock_cache)
        assert result[100] == "3571"  # From cache
        assert result[200] == "7372"  # From API
        # Should only have called sec_get once (for CIK 200)
        assert mock_sec_get.call_count == 1

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_limits_batch_to_500_ciks(
        self, mock_sec_get: MagicMock, mock_cache: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_sic_mapping,
        )

        # Create 600 CIKs
        ciks = set(range(1, 601))
        mock_sec_get.return_value = _make_submissions_response(1, "3571")

        result = acquire_sic_mapping(ciks, cache=mock_cache)
        # Should have only fetched 500
        assert mock_sec_get.call_count == 500

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_handles_fetch_failure_gracefully(
        self, mock_sec_get: MagicMock, mock_cache: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_sic_mapping,
        )

        mock_sec_get.side_effect = Exception("Network error")
        result = acquire_sic_mapping({100, 200}, cache=mock_cache)
        # Should return empty dict (all fetches failed)
        assert isinstance(result, dict)
        assert len(result) == 0

    @patch("do_uw.stages.acquire.clients.sec_client_frames.sec_get")
    def test_works_without_cache(
        self, mock_sec_get: MagicMock,
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client_frames import (
            acquire_sic_mapping,
        )

        mock_sec_get.return_value = _make_submissions_response(100, "3571")
        result = acquire_sic_mapping({100}, cache=None)
        assert result[100] == "3571"
