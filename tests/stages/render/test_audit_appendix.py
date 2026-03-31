"""Tests for signal audit appendix context builder and template rendering.

Phase 78-02: AUDIT-02 — visible completeness coverage in HTML output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2
import pytest

from do_uw.stages.render.context_builders.audit import build_audit_context


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _sample_disposition_summary() -> dict[str, Any]:
    """Build a realistic disposition_summary dict for testing."""
    return {
        "total": 470,
        "triggered_count": 24,
        "clean_count": 378,
        "skipped_count": 45,
        "inactive_count": 23,
        "dispositions": [
            {
                "signal_id": "FIN.current_ratio_check",
                "signal_name": "Current Ratio Check",
                "disposition": "TRIGGERED",
                "skip_reason": None,
                "skip_detail": "",
                "section_prefix": "FIN",
                "evidence": "Current ratio 0.8 below threshold 1.0",
            },
            {
                "signal_id": "FIN.revenue_growth",
                "signal_name": "Revenue Growth",
                "disposition": "CLEAN",
                "skip_reason": None,
                "skip_detail": "",
                "section_prefix": "FIN",
                "evidence": "",
            },
            {
                "signal_id": "GOV.board_independence",
                "signal_name": "Board Independence",
                "disposition": "SKIPPED",
                "skip_reason": "DATA_UNAVAILABLE",
                "skip_detail": "Board composition data not extracted",
                "section_prefix": "GOV",
                "evidence": "",
            },
            {
                "signal_id": "LIT.sca_active",
                "signal_name": "Active Securities Class Action",
                "disposition": "SKIPPED",
                "skip_reason": "EXTRACTION_GAP",
                "skip_detail": "AUTO signal not evaluated (data extraction gap)",
                "section_prefix": "LIT",
                "evidence": "",
            },
            {
                "signal_id": "BASE.deprecated_signal",
                "signal_name": "Deprecated Signal",
                "disposition": "INACTIVE",
                "skip_reason": None,
                "skip_detail": "",
                "section_prefix": "BASE",
                "evidence": "",
            },
            {
                "signal_id": "GOV.ceo_tenure",
                "signal_name": "CEO Tenure",
                "disposition": "TRIGGERED",
                "skip_reason": None,
                "skip_detail": "",
                "section_prefix": "GOV",
                "evidence": "CEO tenure 1.2 years below 2-year threshold",
            },
        ],
        "by_section": {
            "FIN": {"triggered": 3, "clean": 45, "skipped": 12, "inactive": 5},
            "GOV": {"triggered": 1, "clean": 20, "skipped": 8, "inactive": 2},
            "LIT": {"triggered": 5, "clean": 30, "skipped": 10, "inactive": 3},
            "BASE": {"triggered": 0, "clean": 50, "skipped": 5, "inactive": 10},
        },
    }


# ---------------------------------------------------------------------------
# Context builder tests
# ---------------------------------------------------------------------------


class TestBuildAuditContextEmpty:
    """build_audit_context with empty/missing disposition_summary."""

    def test_empty_dict_returns_safe_defaults(self) -> None:
        ctx = build_audit_context({})
        assert ctx["audit_total"] == 0
        assert ctx["audit_triggered"] == 0
        assert ctx["audit_clean"] == 0
        assert ctx["audit_skipped"] == 0
        assert ctx["audit_inactive"] == 0
        assert ctx["audit_checked"] == 0
        assert ctx["audit_section_breakdown"] == []
        assert ctx["audit_skipped_signals"] == []
        assert ctx["audit_triggered_signals"] == []

    def test_none_returns_safe_defaults(self) -> None:
        ctx = build_audit_context(None)  # type: ignore[arg-type]
        assert ctx["audit_total"] == 0
        assert ctx["audit_section_breakdown"] == []


class TestBuildAuditContextPopulated:
    """build_audit_context with a sample disposition_summary."""

    @pytest.fixture()
    def ctx(self) -> dict[str, Any]:
        return build_audit_context(_sample_disposition_summary())

    def test_counts_match_summary(self, ctx: dict[str, Any]) -> None:
        assert ctx["audit_total"] == 470
        assert ctx["audit_triggered"] == 24
        assert ctx["audit_clean"] == 378
        assert ctx["audit_skipped"] == 45
        assert ctx["audit_inactive"] == 23

    def test_checked_is_triggered_plus_clean(self, ctx: dict[str, Any]) -> None:
        assert ctx["audit_checked"] == 24 + 378

    def test_skipped_signals_only_skipped(self, ctx: dict[str, Any]) -> None:
        skipped = ctx["audit_skipped_signals"]
        assert len(skipped) == 2
        assert all(s["reason"] for s in skipped)
        assert all(s["detail"] for s in skipped)
        ids = {s["signal_id"] for s in skipped}
        assert "GOV.board_independence" in ids
        assert "LIT.sca_active" in ids

    def test_triggered_signals_only_triggered(self, ctx: dict[str, Any]) -> None:
        triggered = ctx["audit_triggered_signals"]
        assert len(triggered) == 2
        assert all(t["evidence"] for t in triggered)
        ids = {t["signal_id"] for t in triggered}
        assert "FIN.current_ratio_check" in ids
        assert "GOV.ceo_tenure" in ids

    def test_section_breakdown_sorted_alphabetically(self, ctx: dict[str, Any]) -> None:
        breakdown = ctx["audit_section_breakdown"]
        sections = [b["section"] for b in breakdown]
        assert sections == sorted(sections)

    def test_section_breakdown_has_totals(self, ctx: dict[str, Any]) -> None:
        breakdown = ctx["audit_section_breakdown"]
        for row in breakdown:
            assert row["total"] == (
                row["triggered"] + row["clean"] + row["skipped"] + row["inactive"]
            )

    def test_section_breakdown_keys(self, ctx: dict[str, Any]) -> None:
        breakdown = ctx["audit_section_breakdown"]
        assert len(breakdown) == 4
        expected_keys = {"section", "triggered", "clean", "skipped", "inactive", "total"}
        for row in breakdown:
            assert set(row.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Template rendering tests
# ---------------------------------------------------------------------------


_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "src" / "do_uw" / "templates" / "html"


class TestSignalAuditTemplate:
    """signal_audit.html.j2 renders without errors given context."""

    @pytest.fixture()
    def env(self) -> jinja2.Environment:
        _env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
            undefined=jinja2.Undefined,
        )
        _env.filters["humanize_evidence"] = lambda v: str(v) if v else ""
        _env.filters["humanize_source"] = lambda v: str(v) if v else ""
        return _env

    def test_template_renders_with_sample_data(self, env: jinja2.Environment) -> None:
        ctx = build_audit_context(_sample_disposition_summary())
        template = env.get_template("appendices/signal_audit.html.j2")
        html = template.render(**ctx)
        assert "Signal Disposition Audit" in html
        assert "470" in html  # total
        assert "Triggered" in html or "TRIGGERED" in html

    def test_template_renders_with_empty_data(self, env: jinja2.Environment) -> None:
        ctx = build_audit_context({})
        template = env.get_template("appendices/signal_audit.html.j2")
        html = template.render(**ctx)
        assert "Signal Disposition Audit" in html
        # Zero counts should render without error
        assert "0" in html

    def test_template_shows_skipped_details(self, env: jinja2.Environment) -> None:
        ctx = build_audit_context(_sample_disposition_summary())
        template = env.get_template("appendices/signal_audit.html.j2")
        html = template.render(**ctx)
        assert "Board Independence" in html
        assert "DATA_UNAVAILABLE" in html

    def test_template_shows_triggered_evidence(self, env: jinja2.Environment) -> None:
        ctx = build_audit_context(_sample_disposition_summary())
        template = env.get_template("appendices/signal_audit.html.j2")
        html = template.render(**ctx)
        assert "Current Ratio Check" in html
        assert "Current ratio 0.8" in html or "current ratio" in html.lower()

    def test_template_has_section_breakdown(self, env: jinja2.Environment) -> None:
        ctx = build_audit_context(_sample_disposition_summary())
        template = env.get_template("appendices/signal_audit.html.j2")
        html = template.render(**ctx)
        assert "FIN" in html
        assert "GOV" in html
        assert "LIT" in html
