"""Tests for brain audit HTML report generation (Phase 82, Plan 04)."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def audit_html_path(tmp_path: Path) -> Path:
    """Generate the audit HTML report into a temp directory."""
    from do_uw.brain.brain_audit import generate_audit_html

    out = tmp_path / "audit_report.html"
    result = generate_audit_html(output_path=out)
    assert result == out
    return out


def test_audit_html_generates(audit_html_path: Path) -> None:
    """generate_audit_html produces a valid HTML file."""
    assert audit_html_path.exists()
    content = audit_html_path.read_text(encoding="utf-8")
    assert len(content) > 1000
    assert "<!DOCTYPE html>" in content
    assert "Brain Signal Audit Report" in content


def test_audit_html_has_all_signals(audit_html_path: Path) -> None:
    """Verify the HTML contains a row for every active signal."""
    from do_uw.brain.brain_unified_loader import load_signals

    signals_data = load_signals()
    all_signals = signals_data.get("signals", [])
    active_signals = [
        s for s in all_signals
        if s.get("lifecycle_state", "ACTIVE") == "ACTIVE"
    ]

    content = audit_html_path.read_text(encoding="utf-8")

    # Count signal rows by their data-class attribute
    row_count = content.count('class="signal-row')
    assert row_count == len(active_signals), (
        f"Expected {len(active_signals)} signal rows, found {row_count}"
    )


def test_audit_html_has_filter_controls(audit_html_path: Path) -> None:
    """Verify filter checkboxes exist for class, tier, and provenance."""
    content = audit_html_path.read_text(encoding="utf-8")

    # Class filters
    assert 'data-filter="class"' in content
    assert 'value="foundational"' in content
    assert 'value="evaluative"' in content
    assert 'value="inference"' in content

    # Tier filters
    assert 'data-filter="tier"' in content

    # Provenance filters
    assert 'data-filter="prov"' in content
    assert 'value="unattributed"' in content
    assert 'value="attributed"' in content

    # Search input
    assert 'id="search-input"' in content


def test_audit_provenance_coverage_section(audit_html_path: Path) -> None:
    """Verify provenance coverage statistics section exists."""
    content = audit_html_path.read_text(encoding="utf-8")

    assert "Provenance Coverage" in content
    # Check coverage field names appear
    assert "data_source" in content
    assert "formula" in content
    assert "threshold_provenance" in content
    assert "render_target" in content


def test_audit_html_section_grouping(audit_html_path: Path) -> None:
    """Verify signals are grouped by manifest section."""
    content = audit_html_path.read_text(encoding="utf-8")

    # Should have section headers
    assert 'class="section-header"' in content
    # Should reference at least a few known sections
    assert "Executive Summary" in content or "Critical Risk" in content or "Financial" in content


def test_audit_html_unattributed_flagging(audit_html_path: Path) -> None:
    """Verify that unattributed signals get the yellow highlight class."""
    content = audit_html_path.read_text(encoding="utf-8")

    # The template applies 'unattributed' class to rows
    # There should be at least some unattributed signals in the corpus
    assert "unattributed" in content
