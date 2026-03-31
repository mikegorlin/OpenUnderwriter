"""Tests for epistemological trace appendix template (Phase 114-03).

Renders epistemological_trace.html.j2 with mock context and verifies
structural correctness: H/A/E groups, 9 columns, status badges,
graceful degradation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html"


def _env() -> Environment:
    from do_uw.stages.render.formatters_humanize import humanize_source

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
    )
    env.filters["format_signal_value"] = lambda v: str(v) if v else "N/A"
    env.filters["humanize_source"] = humanize_source
    return env


def _make_trace_context(
    *,
    host_rows: list | None = None,
    agent_rows: list | None = None,
    env_rows: list | None = None,
    trace_available: bool = True,
) -> dict:
    rows: dict[str, list] = {}
    if host_rows is not None:
        rows["host"] = host_rows
    if agent_rows is not None:
        rows["agent"] = agent_rows
    if env_rows is not None:
        rows["environment"] = env_rows
    total = sum(len(v) for v in rows.values())
    return {
        "epistemological_trace": {
            "trace_available": trace_available,
            "rows_by_dimension": rows,
            "trace_total": total,
        },
    }


def _make_row(
    signal_id: str = "SIG_01",
    status: str = "TRIGGERED",
    value: object = 1.0,
    source: str = "10-K 2025",
    confidence: str = "HIGH",
    source_type: str = "audited",
    threshold_level: str = "red",
    threshold_context: str = ">0.5",
    mechanism: str = "threshold",
    rap_subcategory: str = "financial_health",
) -> dict:
    return {
        "signal_id": signal_id,
        "status": status,
        "value": value,
        "source": source,
        "confidence": confidence,
        "source_type": source_type,
        "threshold_level": threshold_level,
        "threshold_context": threshold_context,
        "mechanism": mechanism,
        "rap_subcategory": rap_subcategory,
    }


class TestEpistemologicalTraceTemplate:
    def test_renders_with_all_statuses(self) -> None:
        """Template renders triggered, clean, skipped, and deferred signals."""
        ctx = _make_trace_context(
            host_rows=[
                _make_row(signal_id="H_TRIG", status="TRIGGERED"),
                _make_row(signal_id="H_CLEAR", status="CLEAR", confidence="MEDIUM"),
                _make_row(signal_id="H_SKIP", status="SKIPPED", confidence="LOW"),
                _make_row(signal_id="H_DEFER", status="DEFERRED", confidence="LOW"),
            ],
        )
        env = _env()
        tmpl = env.get_template("appendices/epistemological_trace.html.j2")
        html = tmpl.render(**ctx)

        assert "H_TRIG" in html
        assert "H_CLEAR" in html
        assert "H_SKIP" in html
        assert "H_DEFER" in html

    def test_three_hae_groups_appear(self) -> None:
        """All three H/A/E dimension groups render with correct headers."""
        ctx = _make_trace_context(
            host_rows=[_make_row(signal_id="HOST_1")],
            agent_rows=[_make_row(signal_id="AGENT_1")],
            env_rows=[_make_row(signal_id="ENV_1")],
        )
        env = _env()
        html = env.get_template("appendices/epistemological_trace.html.j2").render(**ctx)

        assert "Host (Structural Risk)" in html
        assert "Agent (Behavioral Risk)" in html
        assert "Environment (External Risk)" in html

    def test_all_nine_columns_present(self) -> None:
        """All 9 required columns appear in the table header."""
        ctx = _make_trace_context(
            host_rows=[_make_row()],
        )
        env = _env()
        html = env.get_template("appendices/epistemological_trace.html.j2").render(**ctx)

        required_columns = [
            "Signal ID",
            "Status",
            "Raw Data",
            "Source",
            "Threshold Applied",
            "Confidence",
            "Source Type",
            "Evaluation Result",
            "Score Contribution",
        ]
        for col in required_columns:
            assert col in html, f"Missing column header: {col}"

    def test_trace_total_matches(self) -> None:
        """Summary bar shows correct total matching sum of all groups."""
        ctx = _make_trace_context(
            host_rows=[_make_row(signal_id="H1"), _make_row(signal_id="H2")],
            agent_rows=[_make_row(signal_id="A1")],
        )
        env = _env()
        html = env.get_template("appendices/epistemological_trace.html.j2").render(**ctx)

        # Total should be 3
        assert ">3<" in html.replace(" ", "").replace("\n", "")

    def test_graceful_degradation_empty(self) -> None:
        """Template renders gracefully when trace data is unavailable."""
        ctx = {"epistemological_trace": {"trace_available": False}}
        env = _env()
        html = env.get_template("appendices/epistemological_trace.html.j2").render(**ctx)

        assert 'id="epistemological-trace"' in html
        assert "No signal evaluation data available" in html
        # Should NOT have the trace table
        assert "trace-table" not in html

    def test_status_badges_have_correct_classes(self) -> None:
        """Each status type gets the correct CSS class on its badge."""
        ctx = _make_trace_context(
            host_rows=[
                _make_row(signal_id="T", status="TRIGGERED"),
                _make_row(signal_id="C", status="CLEAR"),
                _make_row(signal_id="S", status="SKIPPED"),
                _make_row(signal_id="D", status="DEFERRED"),
                _make_row(signal_id="E", status="ELEVATED"),
            ],
        )
        env = _env()
        html = env.get_template("appendices/epistemological_trace.html.j2").render(**ctx)

        assert "trace-status--triggered" in html
        assert "trace-status--clear" in html
        assert "trace-status--skipped" in html
        assert "trace-status--deferred" in html
        assert "trace-status--elevated" in html

    def test_confidence_badges(self) -> None:
        """Confidence badges render with correct classes."""
        ctx = _make_trace_context(
            host_rows=[
                _make_row(signal_id="H1", confidence="HIGH"),
                _make_row(signal_id="H2", confidence="MEDIUM"),
                _make_row(signal_id="H3", confidence="LOW"),
            ],
        )
        env = _env()
        html = env.get_template("appendices/epistemological_trace.html.j2").render(**ctx)

        assert "confidence--high" in html
        assert "confidence--medium" in html
        assert "confidence--low" in html

    def test_no_context_key_graceful(self) -> None:
        """Template renders safely when epistemological_trace key is missing."""
        env = _env()
        html = env.get_template("appendices/epistemological_trace.html.j2").render()

        assert 'id="epistemological-trace"' in html
        assert "No signal evaluation data available" in html
