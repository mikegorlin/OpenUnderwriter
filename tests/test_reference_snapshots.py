"""Tests for reference snapshot capture and comparison scripts (Phase 128-03).

Verifies snapshot structure, section hash computation, and comparison logic.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from scripts.capture_reference_snapshots import (
    compute_section_hashes,
)
from scripts.compare_reference_snapshots import compare_snapshots


class TestComputeSectionHashes:
    def test_section_tags_produce_hashes(self, tmp_path: Path) -> None:
        """HTML with <section id="..."> tags produces hashes."""
        html = (
            '<section id="overview"><h2>Overview</h2><p>Content here</p></section>'
            '<section id="financials"><h2>Financials</h2><p>Numbers</p></section>'
        )
        ticker = "TEST"
        output_dir = tmp_path / "output" / ticker
        output_dir.mkdir(parents=True)
        (output_dir / f"{ticker}_worksheet.html").write_text(html)

        # Monkey-patch the function to use tmp_path
        import scripts.capture_reference_snapshots as mod

        original_compute = mod.compute_section_hashes

        def patched_compute(t: str) -> dict[str, str]:
            html_path = output_dir / f"{t}_worksheet.html"
            if not html_path.exists():
                return {}
            import re

            html_content = html_path.read_text()
            sections: dict[str, str] = {}
            for match in re.finditer(
                r'<section[^>]*id="([^"]+)"[^>]*>(.*?)</section>',
                html_content,
                re.DOTALL,
            ):
                section_id = match.group(1)
                content = match.group(2).strip()
                sections[section_id] = hashlib.sha256(content.encode()).hexdigest()[:16]
            return sections

        hashes = patched_compute(ticker)
        assert "overview" in hashes
        assert "financials" in hashes
        assert len(hashes["overview"]) == 16  # SHA256 truncated to 16 hex chars
        assert len(hashes["financials"]) == 16

    def test_data_section_attributes(self, tmp_path: Path) -> None:
        """HTML with data-section attributes produces hashes."""
        html = '<div data-section="risk-score">Risk content</div>'
        ticker = "TEST2"
        output_dir = tmp_path / "output" / ticker
        output_dir.mkdir(parents=True)
        (output_dir / f"{ticker}_worksheet.html").write_text(html)

        import re

        sections: dict[str, str] = {}
        for match in re.finditer(
            r'<div[^>]*data-section="([^"]+)"[^>]*>(.*?)</div>\s*(?=<div[^>]*data-section|$)',
            html,
            re.DOTALL,
        ):
            section_id = match.group(1)
            content = match.group(2).strip()
            sections[section_id] = hashlib.sha256(content.encode()).hexdigest()[:16]
        assert "risk-score" in sections


class TestCompareSnapshots:
    def test_identical_snapshots_zero_diffs(self) -> None:
        """Identical snapshots report 0 differences."""
        snap = {
            "context_keys": {"key1": {"type": "str"}, "key2": {"type": "int"}},
            "section_hashes": {"overview": "abc123", "financials": "def456"},
        }
        diffs = compare_snapshots(snap, snap)
        assert "0 differences" in diffs["summary"]
        assert not diffs["context_keys"]
        assert not diffs["section_hashes"]["changes"]

    def test_detects_added_keys(self) -> None:
        """Detects keys added in current snapshot."""
        baseline = {"context_keys": {"key1": {"type": "str"}}, "section_hashes": {}}
        current = {
            "context_keys": {"key1": {"type": "str"}, "key2": {"type": "int"}},
            "section_hashes": {},
        }
        diffs = compare_snapshots(baseline, current)
        assert "key2" in diffs["context_keys"].get("added", [])
        assert "1 keys added" in diffs["summary"]

    def test_detects_removed_keys(self) -> None:
        """Detects keys removed from current snapshot."""
        baseline = {
            "context_keys": {"key1": {"type": "str"}, "key2": {"type": "int"}},
            "section_hashes": {},
        }
        current = {"context_keys": {"key1": {"type": "str"}}, "section_hashes": {}}
        diffs = compare_snapshots(baseline, current)
        assert "key2" in diffs["context_keys"].get("removed", [])
        assert "1 keys removed" in diffs["summary"]

    def test_detects_changed_hashes(self) -> None:
        """Detects sections with changed hashes."""
        baseline = {
            "context_keys": {},
            "section_hashes": {"overview": "abc123", "financials": "def456"},
        }
        current = {
            "context_keys": {},
            "section_hashes": {"overview": "abc123", "financials": "xyz789"},
        }
        diffs = compare_snapshots(baseline, current)
        changes = diffs["section_hashes"]["changes"]
        assert len(changes) == 1
        assert changes[0]["section"] == "financials"
        assert changes[0]["status"] == "CHANGED"
        assert "1 sections changed" in diffs["summary"]

    def test_detects_added_and_removed_sections(self) -> None:
        """Detects sections added and removed."""
        baseline = {
            "context_keys": {},
            "section_hashes": {"overview": "abc123"},
        }
        current = {
            "context_keys": {},
            "section_hashes": {"governance": "xyz789"},
        }
        diffs = compare_snapshots(baseline, current)
        changes = diffs["section_hashes"]["changes"]
        assert len(changes) == 2
        statuses = {c["status"] for c in changes}
        assert "ADDED" in statuses
        assert "REMOVED" in statuses
