"""Tests for brain-aware AcquisitionOrchestrator integration.

Verifies:
- Orchestrator accepts brain_manifest=None (backward compat)
- Orchestrator with manifest logs brain-driven requirements
- _determine_acquired_sources maps AcquiredData to source names
- Post-acquisition validation stores brain_coverage in metadata
- AcquireStage.run() derives brain requirements before orchestrator

Uses mocked AcquiredData and manifests -- no real network or DuckDB.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from do_uw.knowledge.requirements import AcquisitionManifest
from do_uw.models.state import AcquiredData
from do_uw.stages.acquire.orchestrator import (
    AcquisitionOrchestrator,
    _determine_acquired_sources,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def brain_manifest() -> AcquisitionManifest:
    """Sample brain-derived manifest."""
    return AcquisitionManifest(
        required_sources={"SEC_10K", "MARKET_PRICE", "SCAC_SEARCH"},
        required_sections={
            "SEC_10K": {"item_1_business", "item_7_mda"},
        },
        source_to_checks={
            "SEC_10K": ["FIN.001", "FIN.002"],
            "MARKET_PRICE": ["STOCK.001"],
            "SCAC_SEARCH": ["LIT.001"],
        },
        total_signals=4,
    )


# ---------------------------------------------------------------------------
# _determine_acquired_sources tests
# ---------------------------------------------------------------------------


class TestDetermineAcquiredSources:
    """Tests for _determine_acquired_sources helper."""

    def test_empty_acquired_data(self) -> None:
        """Empty AcquiredData produces empty source set."""
        acquired = AcquiredData()
        assert _determine_acquired_sources(acquired) == set()

    def test_sec_filings_mapped(self) -> None:
        """SEC filing form types are mapped to source names."""
        acquired = AcquiredData(
            filings={
                "10-K": [{"accession": "123"}],
                "10-Q": [{"accession": "456"}],
                "DEF 14A": [{"accession": "789"}],
            }
        )
        sources = _determine_acquired_sources(acquired)
        assert "SEC_10K" in sources
        assert "SEC_10Q" in sources
        assert "SEC_DEF14A" in sources

    def test_fpi_filings_mapped(self) -> None:
        """FPI filing types (20-F, 6-K) map to domestic equivalents."""
        acquired = AcquiredData(
            filings={
                "20-F": [{"accession": "123"}],
                "6-K": [{"accession": "456"}],
            }
        )
        sources = _determine_acquired_sources(acquired)
        assert "SEC_10K" in sources  # 20-F -> SEC_10K
        assert "SEC_10Q" in sources  # 6-K -> SEC_10Q

    def test_empty_filings_not_counted(self) -> None:
        """Filing keys with empty data are not counted."""
        acquired = AcquiredData(filings={"10-K": []})
        sources = _determine_acquired_sources(acquired)
        assert "SEC_10K" not in sources

    def test_market_data(self) -> None:
        """Non-empty market_data maps to MARKET_PRICE."""
        acquired = AcquiredData(market_data={"prices": [100, 101]})
        sources = _determine_acquired_sources(acquired)
        assert "MARKET_PRICE" in sources

    def test_market_short_interest(self) -> None:
        """Short interest data adds MARKET_SHORT."""
        acquired = AcquiredData(
            market_data={"prices": [100], "short_interest": {"ratio": 0.05}}
        )
        sources = _determine_acquired_sources(acquired)
        assert "MARKET_PRICE" in sources
        assert "MARKET_SHORT" in sources

    def test_litigation_data(self) -> None:
        """Non-empty litigation_data maps to SCAC_SEARCH."""
        acquired = AcquiredData(litigation_data={"cases": [{"id": "1"}]})
        sources = _determine_acquired_sources(acquired)
        assert "SCAC_SEARCH" in sources

    def test_regulatory_data(self) -> None:
        """Non-empty regulatory_data maps to SEC_ENFORCEMENT."""
        acquired = AcquiredData(regulatory_data={"actions": [{"id": "1"}]})
        sources = _determine_acquired_sources(acquired)
        assert "SEC_ENFORCEMENT" in sources

    def test_filing_documents_also_counted(self) -> None:
        """filing_documents (promoted by orchestrator) also maps to sources."""
        acquired = AcquiredData(
            filing_documents={
                "8-K": [{"accession": "123", "full_text": "..."}],
            }
        )
        sources = _determine_acquired_sources(acquired)
        assert "SEC_8K" in sources

    def test_form4_mapping(self) -> None:
        """Form 4 filings map to SEC_FORM4."""
        acquired = AcquiredData(
            filings={"4": [{"accession": "123"}]}
        )
        sources = _determine_acquired_sources(acquired)
        assert "SEC_FORM4" in sources

    def test_comprehensive_scenario(self) -> None:
        """Full acquisition maps all source types."""
        acquired = AcquiredData(
            filings={
                "10-K": [{"accession": "1"}],
                "10-Q": [{"accession": "2"}],
                "DEF 14A": [{"accession": "3"}],
                "8-K": [{"accession": "4"}],
                "4": [{"accession": "5"}],
                "frames": {"Assets": {"value": 100}},
            },
            market_data={
                "prices": [100],
                "short_interest": {"ratio": 0.1},
                "insider_transactions": [{"shares": 1000}],
            },
            litigation_data={"cases": [{"id": "1"}]},
            regulatory_data={"actions": [{"id": "1"}]},
            web_search_results={"blind_spot": [{"title": "test"}]},
        )
        sources = _determine_acquired_sources(acquired)
        expected = {
            "SEC_10K", "SEC_10Q", "SEC_DEF14A", "SEC_8K", "SEC_FORM4",
            "SEC_FRAMES", "MARKET_PRICE", "MARKET_SHORT", "INSIDER_TRADES",
            "SCAC_SEARCH", "SEC_ENFORCEMENT", "WEB_SEARCH",
        }
        assert sources == expected


# ---------------------------------------------------------------------------
# AcquisitionOrchestrator brain integration tests
# ---------------------------------------------------------------------------


class TestOrchestratorBrainIntegration:
    """Tests for brain-aware orchestrator behavior."""

    def test_no_manifest_backward_compat(self) -> None:
        """Orchestrator without brain_manifest works as before."""
        orch = AcquisitionOrchestrator(search_budget=0)
        assert orch._brain_manifest is None

    def test_manifest_stored(self, brain_manifest: AcquisitionManifest) -> None:
        """Orchestrator stores brain_manifest when provided."""
        orch = AcquisitionOrchestrator(
            search_budget=0, brain_manifest=brain_manifest
        )
        assert orch._brain_manifest is brain_manifest

    @patch("do_uw.stages.acquire.orchestrator._run_discovery_hook")
    @patch("do_uw.stages.acquire.orchestrator.AcquisitionOrchestrator._run_blind_spot_sweep", return_value=[])
    @patch("do_uw.stages.acquire.orchestrator.AcquisitionOrchestrator._acquire_frames_data")
    @patch("do_uw.stages.acquire.orchestrator.check_gates", return_value=[])
    def test_brain_requirements_logged(
        self,
        _mock_gates: MagicMock,
        _mock_frames: MagicMock,
        _mock_bss: MagicMock,
        _mock_disc: MagicMock,
        brain_manifest: AcquisitionManifest,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Orchestrator logs brain-driven requirements at run start."""
        orch = AcquisitionOrchestrator(
            search_budget=0, brain_manifest=brain_manifest
        )
        # Mock all clients to no-op
        orch._sec_client = MagicMock()
        orch._sec_client.acquire = MagicMock(return_value={})
        orch._market_client = MagicMock()
        orch._market_client.acquire = MagicMock(return_value={})
        orch._litigation_client = MagicMock()
        orch._litigation_client.acquire = MagicMock(return_value={})
        orch._news_client = MagicMock()
        orch._news_client.acquire = MagicMock(return_value={})
        orch._courtlistener_client = MagicMock(
            search_cases=MagicMock(return_value=None),
        )

        state = MagicMock()
        state.ticker = "TEST"
        state.company = None

        with caplog.at_level(logging.INFO):
            acquired = orch.run(state)

        # Check brain-driven acquisition log message
        brain_msgs = [
            r.message for r in caplog.records
            if "Brain-driven acquisition" in r.message
        ]
        assert len(brain_msgs) == 1
        assert "3 sources" in brain_msgs[0]
        assert "4 signals" in brain_msgs[0]

    @patch("do_uw.stages.acquire.orchestrator._run_discovery_hook")
    @patch("do_uw.stages.acquire.orchestrator.AcquisitionOrchestrator._run_blind_spot_sweep", return_value=[])
    @patch("do_uw.stages.acquire.orchestrator.AcquisitionOrchestrator._acquire_frames_data")
    @patch("do_uw.stages.acquire.orchestrator.check_gates", return_value=[])
    def test_brain_coverage_stored_in_metadata(
        self,
        _mock_gates: MagicMock,
        _mock_frames: MagicMock,
        _mock_bss: MagicMock,
        _mock_disc: MagicMock,
        brain_manifest: AcquisitionManifest,
    ) -> None:
        """Post-acquisition validation stores brain_coverage in metadata."""
        orch = AcquisitionOrchestrator(
            search_budget=0, brain_manifest=brain_manifest
        )
        # Mock all clients, SEC returns some filings
        orch._sec_client = MagicMock()
        orch._sec_client.acquire = MagicMock(
            return_value={"10-K": [{"accession": "1"}]}
        )
        orch._market_client = MagicMock()
        orch._market_client.acquire = MagicMock(
            return_value={"prices": [100]}
        )
        orch._litigation_client = MagicMock()
        orch._litigation_client.acquire = MagicMock(return_value={})
        orch._news_client = MagicMock()
        orch._news_client.acquire = MagicMock(return_value={})
        orch._courtlistener_client = MagicMock(
            search_cases=MagicMock(return_value=None),
        )

        state = MagicMock()
        state.ticker = "TEST"
        state.company = None

        acquired = orch.run(state)

        assert "brain_coverage" in acquired.acquisition_metadata
        coverage = acquired.acquisition_metadata["brain_coverage"]
        assert isinstance(coverage, dict)
        assert "satisfied" in coverage
        assert "missing" in coverage
        assert "coverage_pct" in coverage
        # SEC_10K and MARKET_PRICE satisfied, SCAC_SEARCH missing
        assert "SEC_10K" in coverage["satisfied"]
        assert "MARKET_PRICE" in coverage["satisfied"]
        assert "SCAC_SEARCH" in coverage["missing"]

    @patch("do_uw.stages.acquire.orchestrator.check_gates", return_value=[])
    def test_no_manifest_no_brain_coverage(
        self,
        _mock_gates: MagicMock,
    ) -> None:
        """Without manifest, no brain_coverage in metadata."""
        orch = AcquisitionOrchestrator(search_budget=0)
        orch._sec_client = MagicMock()
        orch._sec_client.acquire = MagicMock(return_value={})
        orch._market_client = MagicMock()
        orch._market_client.acquire = MagicMock(return_value={})
        orch._litigation_client = MagicMock()
        orch._litigation_client.acquire = MagicMock(return_value={})
        orch._news_client = MagicMock()
        orch._news_client.acquire = MagicMock(return_value={})

        state = MagicMock()
        state.ticker = "TEST"
        state.company = None

        acquired = orch.run(state)
        assert "brain_coverage" not in acquired.acquisition_metadata
