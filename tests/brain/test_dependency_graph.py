"""Tests for brain dependency graph: DAG construction, cycle detection, ordering, visualization."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from do_uw.brain.dependency_graph import (
    build_dependency_graph,
    detect_cycles,
    generate_graph_data,
    order_signals_for_execution,
    topological_order,
)


def _signal(
    sid: str,
    deps: list[str] | None = None,
    signal_class: str = "evaluative",
) -> dict[str, Any]:
    """Helper to build a minimal signal dict."""
    s: dict[str, Any] = {"id": sid, "signal_class": signal_class, "depends_on": []}
    if deps:
        s["depends_on"] = [{"signal": d, "field": ""} for d in deps]
    return s


class TestBuildDependencyGraph:
    """Tests for build_dependency_graph."""

    def test_build_dag_simple(self) -> None:
        """3 signals with linear deps A->B->C, verify static_order."""
        signals = [
            _signal("C"),
            _signal("B", ["C"]),
            _signal("A", ["B"]),
        ]
        ts = build_dependency_graph(signals)
        order = list(ts.static_order())
        assert order.index("C") < order.index("B")
        assert order.index("B") < order.index("A")

    def test_build_dag_no_deps(self) -> None:
        """Signals with empty depends_on produce no error."""
        signals = [_signal("X"), _signal("Y"), _signal("Z")]
        ts = build_dependency_graph(signals)
        order = list(ts.static_order())
        assert set(order) == {"X", "Y", "Z"}

    def test_dangling_reference(self, caplog: pytest.LogCaptureFixture) -> None:
        """Signal depends on non-existent ID: logs warning, excluded from graph."""
        signals = [_signal("A", ["NONEXISTENT"])]
        with caplog.at_level(logging.WARNING):
            ts = build_dependency_graph(signals)
        order = list(ts.static_order())
        assert "A" in order
        assert "NONEXISTENT" not in order
        assert any("dangling" in r.message.lower() or "not found" in r.message.lower() for r in caplog.records)


class TestDetectCycles:
    """Tests for detect_cycles."""

    def test_cycle_detection_none(self) -> None:
        """Acyclic graph returns None."""
        signals = [_signal("A", ["B"]), _signal("B")]
        result = detect_cycles(signals)
        assert result is None

    def test_cycle_detection_found(self) -> None:
        """A->B->A cycle returns cycle members."""
        signals = [_signal("A", ["B"]), _signal("B", ["A"])]
        result = detect_cycles(signals)
        assert result is not None
        assert set(result) >= {"A", "B"}


class TestTopologicalOrder:
    """Tests for topological_order."""

    def test_topological_order(self) -> None:
        """Correct order for known graph."""
        signals = [
            _signal("C"),
            _signal("B", ["C"]),
            _signal("A", ["B"]),
        ]
        order = topological_order(signals)
        assert order.index("C") < order.index("B")
        assert order.index("B") < order.index("A")


class TestOrderSignalsForExecution:
    """Tests for order_signals_for_execution."""

    def test_order_for_execution_tier_ordering(self) -> None:
        """Foundational signals appear before evaluative before inference."""
        signals = [
            _signal("INF1", signal_class="inference"),
            _signal("EVAL1", signal_class="evaluative"),
            _signal("FOUND1", signal_class="foundational"),
        ]
        ordered = order_signals_for_execution(signals)
        ids = [s["id"] for s in ordered]
        assert ids.index("FOUND1") < ids.index("EVAL1")
        assert ids.index("EVAL1") < ids.index("INF1")

    def test_order_for_execution_within_tier(self) -> None:
        """Two evaluative signals with dep edge appear in correct order."""
        signals = [
            _signal("EVAL_B", deps=["EVAL_A"], signal_class="evaluative"),
            _signal("EVAL_A", signal_class="evaluative"),
        ]
        ordered = order_signals_for_execution(signals)
        ids = [s["id"] for s in ordered]
        assert ids.index("EVAL_A") < ids.index("EVAL_B")

    def test_order_for_execution_cross_tier_excluded(self) -> None:
        """Evaluative depending on foundational does not cause error."""
        signals = [
            _signal("FOUND1", signal_class="foundational"),
            _signal("EVAL1", deps=["FOUND1"], signal_class="evaluative"),
        ]
        # Should not raise -- cross-tier dep excluded from per-tier graph
        ordered = order_signals_for_execution(signals)
        ids = [s["id"] for s in ordered]
        assert ids.index("FOUND1") < ids.index("EVAL1")

    def test_order_empty_list(self) -> None:
        """Empty input returns empty output."""
        assert order_signals_for_execution([]) == []


def _rich_signal(
    sid: str,
    deps: list[str] | None = None,
    signal_class: str = "evaluative",
    group: str = "test_group",
    section: str = "financial",
    field_path: str = "",
) -> dict[str, Any]:
    """Helper to build a signal dict with visualization-relevant fields."""
    s: dict[str, Any] = {
        "id": sid,
        "name": sid.replace(".", " ").title(),
        "signal_class": signal_class,
        "group": group,
        "report_section": section,
        "field_path": field_path or f"state.{sid.lower()}",
        "description": f"Test signal {sid}",
        "threshold": "> 0.5",
        "category": "test",
        "depends_on": [],
    }
    if deps:
        s["depends_on"] = [{"signal": d, "field": ""} for d in deps]
    return s


class TestGenerateGraphData:
    """Tests for generate_graph_data (visualization)."""

    def test_structure(self) -> None:
        """Output has nodes, links, stats keys with correct types."""
        signals = [_rich_signal("A"), _rich_signal("B")]
        result = generate_graph_data(signals)
        assert "nodes" in result
        assert "links" in result
        assert "stats" in result
        assert isinstance(result["nodes"], list)
        assert isinstance(result["links"], list)

    def test_node_fields(self) -> None:
        """Each node has required fields."""
        signals = [_rich_signal("X", group="g1", section="company")]
        result = generate_graph_data(signals)
        node = result["nodes"][0]
        assert node["id"] == "X"
        assert node["signal_class"] == "evaluative"
        assert node["group"] == "g1"
        assert node["section"] == "company"
        assert "field_path" in node
        assert "name" in node

    def test_links_from_depends_on(self) -> None:
        """Signals with depends_on produce correct source/target links."""
        signals = [
            _rich_signal("A"),
            _rich_signal("B", deps=["A"]),
            _rich_signal("C", deps=["A", "B"]),
        ]
        result = generate_graph_data(signals)
        links = result["links"]
        assert len(links) == 3  # A->B, A->C, B->C
        sources_targets = {(l["source"], l["target"]) for l in links}
        assert ("A", "B") in sources_targets
        assert ("A", "C") in sources_targets
        assert ("B", "C") in sources_targets

    def test_no_links_to_nonexistent(self) -> None:
        """Links to non-existent nodes are excluded."""
        signals = [_rich_signal("A", deps=["GONE"])]
        result = generate_graph_data(signals)
        assert len(result["links"]) == 0

    def test_section_filter(self) -> None:
        """section_filter only includes matching signals."""
        signals = [
            _rich_signal("A", section="company"),
            _rich_signal("B", section="financial"),
            _rich_signal("C", section="company"),
        ]
        result = generate_graph_data(signals, section_filter="company")
        assert len(result["nodes"]) == 2
        assert all(n["section"] == "company" for n in result["nodes"])

    def test_type_filter(self) -> None:
        """type_filter only includes matching signal_class."""
        signals = [
            _rich_signal("F1", signal_class="foundational"),
            _rich_signal("E1", signal_class="evaluative"),
            _rich_signal("I1", signal_class="inference"),
        ]
        result = generate_graph_data(signals, type_filter="foundational")
        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["signal_class"] == "foundational"

    def test_stats_accuracy(self) -> None:
        """Stats counts match actual data."""
        signals = [
            _rich_signal("F1", signal_class="foundational"),
            _rich_signal("E1", signal_class="evaluative", deps=["F1"]),
            _rich_signal("E2", signal_class="evaluative"),
            _rich_signal("I1", signal_class="inference"),
        ]
        result = generate_graph_data(signals)
        stats = result["stats"]
        assert stats["total_nodes"] == 4
        assert stats["total_edges"] == 1
        assert stats["foundational"] == 1
        assert stats["evaluative"] == 2
        assert stats["inference"] == 1

    def test_real_signals(self) -> None:
        """Load actual signals and verify graph data matches inventory."""
        from do_uw.brain.brain_unified_loader import load_signals

        signals = load_signals()["signals"]
        result = generate_graph_data(signals)
        stats = result["stats"]
        assert stats["total_nodes"] == len(signals)
        assert stats["total_nodes"] >= 400  # At least 400 signals
        # Verify edge count matches signals with depends_on
        expected_edges = sum(
            1
            for s in signals
            for dep in (s.get("depends_on") or [])
            if (dep.get("signal", "") if isinstance(dep, dict) else str(dep))
            in {sig["id"] for sig in signals}
        )
        assert stats["total_edges"] == expected_edges


class TestHtmlTemplateRenders:
    """Tests for the D3.js HTML template."""

    def test_template_renders_with_data(self) -> None:
        """Template renders successfully with sample graph data."""
        from jinja2 import Environment, FileSystemLoader

        signals = [
            _rich_signal("A", signal_class="foundational"),
            _rich_signal("B", deps=["A"], signal_class="evaluative"),
        ]
        data = generate_graph_data(signals)

        templates_dir = Path(__file__).resolve().parents[2] / "src" / "do_uw" / "brain" / "templates"
        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        tmpl = env.get_template("dependency_graph.html")
        html = tmpl.render(graph_data=json.dumps(data))

        assert len(html) > 1000
        assert "d3.v7" in html
        assert "forceSimulation" in html
        assert "filterSection" in html
        assert "detailPanel" in html

    def test_template_renders_with_real_data(self) -> None:
        """Template renders with full signal set without error."""
        from jinja2 import Environment, FileSystemLoader

        from do_uw.brain.brain_unified_loader import load_signals

        signals = load_signals()["signals"]
        data = generate_graph_data(signals)

        templates_dir = Path(__file__).resolve().parents[2] / "src" / "do_uw" / "brain" / "templates"
        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        tmpl = env.get_template("dependency_graph.html")
        html = tmpl.render(graph_data=json.dumps(data))

        assert len(html) > 10000
        assert str(data["stats"]["total_nodes"]) in html


class TestCliVisualize:
    """Tests for the brain visualize CLI command."""

    def test_cli_creates_file(self, tmp_path: Path) -> None:
        """CLI command creates HTML output file."""
        from typer.testing import CliRunner

        from do_uw.cli_brain import brain_app

        output_path = tmp_path / "test_graph.html"
        runner = CliRunner()
        result = runner.invoke(brain_app, ["visualize", "--output", str(output_path)])

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output_path.exists()
        html = output_path.read_text()
        assert "d3.v7" in html
        assert "forceSimulation" in html
        assert len(html) > 10000
