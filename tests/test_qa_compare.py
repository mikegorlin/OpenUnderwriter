"""Tests for cross-ticker QA business profile validation (Phase 92 -- REND-03/REND-04).

Verifies:
- profile_output() populates business profile fields
- compare_profiles() flags missing business profile data with severity
- compare_profiles() validates render_audit presence
- Severity-based reporting categorization
"""

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

import pytest

# Add scripts directory to sys.path so qa_compare can be imported normally
_SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import qa_compare as qa  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    *,
    has_revenue_segs: bool = True,
    has_customer: bool = True,
    has_supplier: bool = True,
    has_geographic: bool = True,
    has_render_audit: bool = True,
    unrendered_count: int = 5,
) -> dict:
    """Build a mock state.json with configurable business profile data."""
    state: dict = {
        "ticker": "TEST",
        "extracted": {
            "financials": {
                "distress": {"altman_z_score": {"score": 3.0}},
            },
            "text_signals": {},
        },
        "pipeline_metadata": {
            "llm_cost": 0.5,
        },
    }

    ts = state["extracted"]["text_signals"]
    if has_revenue_segs:
        ts["revenue_quality_warn"] = {
            "signal_id": "revenue_quality_warn",
            "triggered": True,
            "evidence": ["Revenue segment data available"],
        }
        ts["segment_consistency"] = {
            "signal_id": "segment_consistency",
            "triggered": True,
            "evidence": ["Multiple segments detected"],
        }
    if has_customer:
        ts["customer_concentration"] = {
            "signal_id": "customer_concentration",
            "triggered": True,
            "evidence": ["Top customer 15%"],
        }
    if has_supplier:
        ts["distribution_channels"] = {
            "signal_id": "distribution_channels",
            "triggered": True,
            "evidence": ["Supplier data present"],
        }
    if has_geographic:
        ts["geopolitical_exposure"] = {
            "signal_id": "geopolitical_exposure",
            "triggered": True,
            "evidence": ["International revenue 40%"],
        }

    if has_render_audit:
        state["pipeline_metadata"]["render_audit"] = {
            "total_extracted": 100,
            "total_rendered": 90,
            "total_excluded": 5,
            "coverage_pct": 94.7,
            "unrendered_fields": ["field_a"] * unrendered_count,
        }

    return state


def _make_html(
    *,
    has_data_audit: bool = True,
    has_revenue_sections: bool = True,
    has_customer_sections: bool = True,
    has_geographic_sections: bool = True,
) -> str:
    """Build mock HTML with configurable sections."""
    parts = [
        "<html><body>",
        '<h2>D&O Underwriting Worksheet</h2>',
    ]
    if has_revenue_sections:
        parts.append('<section id="revenue-segments"><h3>Revenue Segments</h3><p>Data here</p></section>')
    if has_customer_sections:
        parts.append('<section id="customer"><h3>Customer Concentration</h3><p>Top customer 15%</p></section>')
    if has_geographic_sections:
        parts.append('<section id="geographic"><h3>Geographic Footprint</h3><p>International 40%</p></section>')
    if has_data_audit:
        parts.append('<section id="data-audit"><details class="appendix-section"><summary>Appendix: Data Audit</summary></details></section>')
    parts.append("</body></html>")
    return "\n".join(parts)


def _setup_output(
    tmpdir: Path,
    ticker: str,
    state: dict,
    html: str,
) -> Path:
    """Create output directory with state.json and HTML."""
    output_dir = tmpdir / ticker
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "state.json").write_text(json.dumps(state))
    (output_dir / f"{ticker}_worksheet.html").write_text(html)
    return output_dir


# ---------------------------------------------------------------------------
# Test: profile_output() business profile fields
# ---------------------------------------------------------------------------


class TestProfileOutputBusinessProfile:
    """Tests that profile_output populates business profile fields."""

    def test_populates_business_profile_fields(self) -> None:
        """profile_output() populates new business profile fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            state = _make_state()
            html = _make_html()
            out_dir = _setup_output(tmppath, "TEST", state, html)

            profile = qa.profile_output("TEST", out_dir)

            assert hasattr(profile, "has_revenue_segments")
            assert hasattr(profile, "has_customer_concentration")
            assert hasattr(profile, "has_supplier_concentration")
            assert hasattr(profile, "has_geographic_footprint")
            assert hasattr(profile, "has_render_audit")
            assert hasattr(profile, "render_audit_unrendered_count")

            assert profile.has_revenue_segments is True
            assert profile.has_customer_concentration is True
            assert profile.has_geographic_footprint is True
            assert profile.has_render_audit is True
            assert profile.render_audit_unrendered_count == 5


# ---------------------------------------------------------------------------
# Test: compare_profiles() severity-based reporting
# ---------------------------------------------------------------------------


class TestCompareProfilesSeverity:
    """Tests for compare_profiles with severity-based business profile validation."""

    def test_flags_missing_render_audit_in_html(self) -> None:
        """compare_profiles validates render_audit appendix is present in HTML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Reference has data audit
            ref_state = _make_state()
            ref_html = _make_html(has_data_audit=True)
            ref_dir = _setup_output(tmppath, "REF", ref_state, ref_html)
            ref = qa.profile_output("REF", ref_dir)

            # Target missing data audit in HTML
            tgt_state = _make_state()
            tgt_html = _make_html(has_data_audit=False)
            tgt_dir = _setup_output(tmppath, "TGT", tgt_state, tgt_html)
            tgt = qa.profile_output("TGT", tgt_dir)

            issues = qa.compare_profiles(ref, tgt)
            audit_issues = [i for i in issues if "render_audit" in i.lower() or "data audit" in i.lower()]
            assert len(audit_issues) >= 1

    def test_flags_missing_render_audit_in_state(self) -> None:
        """compare_profiles validates render_audit key is present in state.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Reference has render_audit
            ref_state = _make_state(has_render_audit=True)
            ref_html = _make_html()
            ref_dir = _setup_output(tmppath, "REF", ref_state, ref_html)
            ref = qa.profile_output("REF", ref_dir)

            # Target missing render_audit in state
            tgt_state = _make_state(has_render_audit=False)
            tgt_html = _make_html()
            tgt_dir = _setup_output(tmppath, "TGT", tgt_state, tgt_html)
            tgt = qa.profile_output("TGT", tgt_dir)

            issues = qa.compare_profiles(ref, tgt)
            audit_issues = [i for i in issues if "render_audit" in i.lower()]
            assert len(audit_issues) >= 1

    def test_flags_missing_business_profile_field(self) -> None:
        """compare_profiles flags MEDIUM severity when business profile field is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Reference has all business profile data
            ref_state = _make_state()
            ref_html = _make_html()
            ref_dir = _setup_output(tmppath, "REF", ref_state, ref_html)
            ref = qa.profile_output("REF", ref_dir)

            # Target missing customer concentration
            tgt_state = _make_state(has_customer=False)
            tgt_html = _make_html()
            tgt_dir = _setup_output(tmppath, "TGT", tgt_state, tgt_html)
            tgt = qa.profile_output("TGT", tgt_dir)

            issues = qa.compare_profiles(ref, tgt)
            biz_issues = [i for i in issues if "MEDIUM" in i or "customer" in i.lower()]
            assert len(biz_issues) >= 1

    def test_severity_categorization(self) -> None:
        """Severity-based reporting categorizes issues as HIGH/MEDIUM/LOW."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Reference has everything
            ref_state = _make_state()
            ref_html = _make_html()
            ref_dir = _setup_output(tmppath, "REF", ref_state, ref_html)
            ref = qa.profile_output("REF", ref_dir)

            # Target missing multiple things
            tgt_state = _make_state(has_customer=False, has_render_audit=False)
            tgt_html = _make_html(has_data_audit=False)
            tgt_dir = _setup_output(tmppath, "TGT", tgt_state, tgt_html)
            tgt = qa.profile_output("TGT", tgt_dir)

            issues = qa.compare_profiles(ref, tgt)

            # Should have severity-tagged issues
            has_severity = any(
                "[HIGH]" in i or "[MEDIUM]" in i or "[LOW]" in i
                for i in issues
            )
            assert has_severity, f"Expected severity tags in issues: {issues}"
