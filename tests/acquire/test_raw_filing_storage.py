"""Tests for raw filing text storage in output/TICKER/sources/filings/.

Verifies that filing documents with full_text are written to disk,
the manifest includes filing entries, and missing full_text triggers warnings.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.state import AcquiredData, AnalysisState


def _make_state_with_filings(
    filing_documents: dict[str, list[dict[str, Any]]],
) -> MagicMock:
    """Create a mock state with given filing_documents."""
    acquired = AcquiredData(filing_documents=filing_documents)
    state = MagicMock(spec=AnalysisState)
    state.acquired_data = acquired
    return state


class TestFilingTextWrittenToDisk:
    """Test that filing documents with full_text are written as .txt files."""

    def test_filing_with_full_text_written(self, tmp_path: Path) -> None:
        """A filing with full_text should produce a .txt file."""
        from do_uw.stages.render import _save_source_documents

        state = _make_state_with_filings({
            "10-K": [
                {
                    "accession": "0001234567-24-000123",
                    "filing_date": "2024-03-15",
                    "form_type": "10-K",
                    "full_text": "This is the full 10-K filing text content.",
                },
            ],
        })

        _save_source_documents(state, tmp_path)

        filings_dir = tmp_path / "sources" / "filings"
        assert filings_dir.exists()
        txt_files = list(filings_dir.glob("*.txt"))
        assert len(txt_files) == 1
        content = txt_files[0].read_text(encoding="utf-8")
        assert "full 10-K filing text" in content

    def test_multiple_form_types_written(self, tmp_path: Path) -> None:
        """Multiple form types each produce their own .txt files."""
        from do_uw.stages.render import _save_source_documents

        state = _make_state_with_filings({
            "10-K": [
                {
                    "accession": "acc-10k",
                    "filing_date": "2024-01-01",
                    "form_type": "10-K",
                    "full_text": "Annual report content.",
                },
            ],
            "DEF 14A": [
                {
                    "accession": "acc-def14a",
                    "filing_date": "2024-02-01",
                    "form_type": "DEF 14A",
                    "full_text": "Proxy statement content.",
                },
            ],
        })

        _save_source_documents(state, tmp_path)

        filings_dir = tmp_path / "sources" / "filings"
        txt_files = list(filings_dir.glob("*.txt"))
        assert len(txt_files) == 2

    def test_filing_text_is_nonempty(self, tmp_path: Path) -> None:
        """Stored filing text should contain actual SEC filing content."""
        from do_uw.stages.render import _save_source_documents

        text = "ITEM 1. BUSINESS\nThe Company operates..." * 100
        state = _make_state_with_filings({
            "10-K": [
                {
                    "accession": "acc-big",
                    "filing_date": "2024-06-30",
                    "form_type": "10-K",
                    "full_text": text,
                },
            ],
        })

        _save_source_documents(state, tmp_path)

        filings_dir = tmp_path / "sources" / "filings"
        txt_files = list(filings_dir.glob("*.txt"))
        assert len(txt_files) == 1
        stored = txt_files[0].read_text(encoding="utf-8")
        assert len(stored) > 1000  # Non-trivial content


class TestManifestPopulated:
    """Test that manifest.json includes filing entries."""

    def test_manifest_includes_filing(self, tmp_path: Path) -> None:
        """Filing with full_text should appear in manifest.json."""
        from do_uw.stages.render import _save_source_documents

        state = _make_state_with_filings({
            "10-K": [
                {
                    "accession": "acc-manifest",
                    "filing_date": "2024-03-15",
                    "form_type": "10-K",
                    "full_text": "Filing content for manifest test.",
                },
            ],
        })

        _save_source_documents(state, tmp_path)

        manifest_path = tmp_path / "sources" / "manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert len(manifest) >= 1
        filing_entries = [e for e in manifest if e.get("type") == "sec_filing"]
        assert len(filing_entries) == 1
        assert filing_entries[0]["form_type"] == "10-K"
        assert filing_entries[0]["accession"] == "acc-manifest"
        assert filing_entries[0]["size_bytes"] > 0

    def test_manifest_excludes_empty_text(self, tmp_path: Path) -> None:
        """Filings without full_text should NOT appear in manifest."""
        from do_uw.stages.render import _save_source_documents

        state = _make_state_with_filings({
            "10-K": [
                {
                    "accession": "acc-empty",
                    "filing_date": "2024-03-15",
                    "form_type": "10-K",
                    "full_text": "",  # Empty!
                },
            ],
        })

        _save_source_documents(state, tmp_path)

        manifest_path = tmp_path / "sources" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        filing_entries = [e for e in manifest if e.get("type") == "sec_filing"]
        assert len(filing_entries) == 0


class TestSourceLinkJson:
    """Test that source_link.json maps accession numbers to files."""

    def test_source_link_created(self, tmp_path: Path) -> None:
        """source_link.json should be created when filings are saved."""
        from do_uw.stages.render import _save_source_documents

        state = _make_state_with_filings({
            "10-K": [
                {
                    "accession": "acc-link-test",
                    "filing_date": "2024-03-15",
                    "form_type": "10-K",
                    "full_text": "Filing content.",
                },
            ],
        })

        _save_source_documents(state, tmp_path)

        link_path = tmp_path / "sources" / "source_link.json"
        assert link_path.exists()
        links = json.loads(link_path.read_text(encoding="utf-8"))
        assert "acc-link-test" in links
        assert links["acc-link-test"]["form_type"] == "10-K"
        assert links["acc-link-test"]["extraction_cache_key"] == "10-K:acc-link-test"


class TestMissingTextWarning:
    """Test that missing full_text triggers a log warning."""

    def test_warning_logged_for_missing_text(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A filing without full_text should produce a warning log."""
        from do_uw.stages.render import _save_source_documents

        state = _make_state_with_filings({
            "DEF 14A": [
                {
                    "accession": "acc-no-text",
                    "filing_date": "2024-04-01",
                    "form_type": "DEF 14A",
                    "full_text": "",
                },
            ],
        })

        with caplog.at_level(logging.WARNING):
            _save_source_documents(state, tmp_path)

        assert any(
            "has no full_text" in record.message
            for record in caplog.records
        ), f"Expected warning about missing full_text, got: {[r.message for r in caplog.records]}"
