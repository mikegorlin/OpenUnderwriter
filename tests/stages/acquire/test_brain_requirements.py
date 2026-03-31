"""Tests for brain_requirements module: brain-to-acquisition derivation.

Tests validate_acquisition_coverage, log_section_requirements, and
derive_brain_requirements graceful fallback. Uses AcquisitionManifest
directly -- no DuckDB required.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from do_uw.knowledge.requirements import AcquisitionManifest
from do_uw.stages.acquire.brain_requirements import (
    derive_brain_requirements,
    log_section_requirements,
    validate_acquisition_coverage,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def full_manifest() -> AcquisitionManifest:
    """Manifest with multiple sources and sections."""
    return AcquisitionManifest(
        required_sources={"SEC_10K", "MARKET_PRICE", "SCAC_SEARCH"},
        required_sections={
            "SEC_10K": {"item_1_business", "item_7_mda", "item_9a_controls"},
            "SCAC_SEARCH": {"federal_securities"},
        },
        source_to_checks={
            "SEC_10K": ["FIN.001", "FIN.002", "GOV.001"],
            "MARKET_PRICE": ["STOCK.001"],
            "SCAC_SEARCH": ["LIT.001", "LIT.002"],
        },
        total_signals=6,
    )


@pytest.fixture()
def empty_manifest() -> AcquisitionManifest:
    """Manifest with no requirements."""
    return AcquisitionManifest(total_signals=0)


# ---------------------------------------------------------------------------
# validate_acquisition_coverage tests
# ---------------------------------------------------------------------------


class TestValidateAcquisitionCoverage:
    """Tests for validate_acquisition_coverage()."""

    def test_full_coverage(self, full_manifest: AcquisitionManifest) -> None:
        """All required sources satisfied."""
        acquired = {"SEC_10K", "MARKET_PRICE", "SCAC_SEARCH", "SEC_10Q"}
        result = validate_acquisition_coverage(full_manifest, acquired)

        assert result["coverage_pct"] == 100.0
        assert sorted(result["satisfied"]) == [
            "MARKET_PRICE",
            "SCAC_SEARCH",
            "SEC_10K",
        ]
        assert result["missing"] == []

    def test_partial_coverage(self, full_manifest: AcquisitionManifest) -> None:
        """Some required sources missing."""
        acquired = {"SEC_10K"}
        result = validate_acquisition_coverage(full_manifest, acquired)

        assert result["coverage_pct"] == pytest.approx(33.33, abs=0.1)
        assert result["satisfied"] == ["SEC_10K"]
        assert sorted(result["missing"]) == ["MARKET_PRICE", "SCAC_SEARCH"]

    def test_no_coverage(self, full_manifest: AcquisitionManifest) -> None:
        """No required sources acquired."""
        result = validate_acquisition_coverage(full_manifest, set())

        assert result["coverage_pct"] == 0.0
        assert result["satisfied"] == []
        assert len(result["missing"]) == 3

    def test_empty_manifest(self, empty_manifest: AcquisitionManifest) -> None:
        """Empty manifest reports 100% coverage (nothing required)."""
        result = validate_acquisition_coverage(empty_manifest, {"SEC_10K"})

        assert result["coverage_pct"] == 100.0
        assert result["satisfied"] == []
        assert result["missing"] == []

    def test_logs_warning_for_missing_sources(
        self, full_manifest: AcquisitionManifest, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Missing sources produce WARNING log messages."""
        with caplog.at_level(logging.WARNING, logger="do_uw.stages.acquire.brain_requirements"):
            validate_acquisition_coverage(full_manifest, {"SEC_10K"})

        warning_messages = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(warning_messages) == 2
        assert any("MARKET_PRICE" in m for m in warning_messages)
        assert any("SCAC_SEARCH" in m for m in warning_messages)


# ---------------------------------------------------------------------------
# log_section_requirements tests
# ---------------------------------------------------------------------------


class TestLogSectionRequirements:
    """Tests for log_section_requirements()."""

    def test_logs_section_details(
        self, full_manifest: AcquisitionManifest, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Logs specific section requirements per source."""
        with caplog.at_level(logging.INFO, logger="do_uw.stages.acquire.brain_requirements"):
            log_section_requirements(full_manifest)

        info_messages = [r.message for r in caplog.records if r.levelno == logging.INFO]
        assert len(info_messages) == 2  # SEC_10K and SCAC_SEARCH
        assert any("SEC_10K" in m and "item_1_business" in m for m in info_messages)
        assert any("SCAC_SEARCH" in m and "federal_securities" in m for m in info_messages)

    def test_no_sections_no_log(
        self, empty_manifest: AcquisitionManifest, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Empty manifest produces no section log messages."""
        with caplog.at_level(logging.INFO, logger="do_uw.stages.acquire.brain_requirements"):
            log_section_requirements(empty_manifest)

        assert len(caplog.records) == 0


# ---------------------------------------------------------------------------
# derive_brain_requirements tests
# ---------------------------------------------------------------------------


class TestDeriveBrainRequirements:
    """Tests for derive_brain_requirements()."""

    def test_returns_none_when_brain_unavailable(self) -> None:
        """Gracefully returns None when BrainLoader fails."""
        # BrainLoader is imported lazily inside the function, so we
        # patch at the source module where it is defined.
        with patch(
            "do_uw.brain.brain_unified_loader.BrainLoader",
            side_effect=FileNotFoundError("brain signals not found"),
        ):
            result = derive_brain_requirements()

        # Should not raise, should return None
        assert result is None

    def test_returns_none_on_import_error(self) -> None:
        """Returns None if BrainLoader cannot be imported."""
        with patch.dict("sys.modules", {"do_uw.brain.brain_unified_loader": None}):
            result = derive_brain_requirements()
        assert result is None

    def test_returns_manifest_on_success(self) -> None:
        """Returns AcquisitionManifest when brain loads successfully."""
        mock_loader = MagicMock()
        mock_loader.load_signals.return_value = {
            "signals": [
                {
                    "id": "FIN.001",
                    "execution_mode": "AUTO",
                    "required_data": ["SEC_10K"],
                    "data_locations": {"SEC_10K": ["item_7_mda"]},
                    "depth": 2,
                    "content_type": "EVALUATIVE_CHECK",
                },
            ],
            "total_signals": 1,
        }
        mock_cls = MagicMock(return_value=mock_loader)

        with patch(
            "do_uw.brain.brain_unified_loader.BrainLoader",
            mock_cls,
        ):
            result = derive_brain_requirements()

        assert result is not None
        assert isinstance(result, AcquisitionManifest)
        assert "SEC_10K" in result.required_sources
        assert result.total_signals == 1

    def test_returns_none_when_no_checks(self) -> None:
        """Returns None when brain has no active checks."""
        mock_loader = MagicMock()
        mock_loader.load_signals.return_value = {"signals": [], "total_signals": 0}
        mock_cls = MagicMock(return_value=mock_loader)

        with patch(
            "do_uw.brain.brain_unified_loader.BrainLoader",
            mock_cls,
        ):
            result = derive_brain_requirements()

        assert result is None
