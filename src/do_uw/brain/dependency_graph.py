"""Signal dependency DAG: construction, cycle detection, tier+topo ordering.

Builds a directed acyclic graph from signal ``depends_on`` fields using
``graphlib.TopologicalSorter``. Provides cycle detection at load time and
tier-based topological ordering for signal execution.

Tier order: foundational -> evaluative -> inference.
Within each tier, signals are sorted by topological order of their
within-tier dependency edges. Cross-tier dependencies are excluded
from per-tier sub-graphs (they are already satisfied by tier ordering).

Usage:
    from do_uw.brain.dependency_graph import (
        build_dependency_graph,
        detect_cycles,
        order_signals_for_execution,
        topological_order,
    )
"""

from __future__ import annotations

import logging
from graphlib import CycleError, TopologicalSorter
from typing import Any

logger = logging.getLogger(__name__)

# Tier ordering: lower index = runs first
_TIER_ORDER: dict[str, int] = {
    "foundational": 0,
    "evaluative": 1,
    "inference": 2,
}
_DEFAULT_TIER = "evaluative"


def build_dependency_graph(
    signals: list[dict[str, Any]],
) -> TopologicalSorter[str]:
    """Build a DAG from signal depends_on fields.

    Each signal dict must have ``id`` (str) and ``depends_on``
    (list of dicts with ``signal`` key). Dangling references
    (dependencies on IDs not in the signal set) are logged as
    warnings and excluded from the graph.

    Args:
        signals: List of signal config dicts.

    Returns:
        A ``graphlib.TopologicalSorter`` ready for prepare() or static_order().
    """
    signal_ids = {s["id"] for s in signals}
    ts: TopologicalSorter[str] = TopologicalSorter()

    for sig in signals:
        sid = sig["id"]
        deps: list[dict[str, Any]] = sig.get("depends_on") or []
        valid_deps: list[str] = []

        for dep in deps:
            dep_id = dep.get("signal", "") if isinstance(dep, dict) else str(dep)
            if not dep_id:
                continue
            if dep_id not in signal_ids:
                logger.warning(
                    "Signal '%s' depends on '%s' which was not found in signal set; "
                    "dangling reference excluded from graph",
                    sid,
                    dep_id,
                )
                continue
            valid_deps.append(dep_id)

        ts.add(sid, *valid_deps)

    return ts


def detect_cycles(
    signals: list[dict[str, Any]],
) -> list[str] | None:
    """Detect circular dependencies in the signal DAG.

    Args:
        signals: List of signal config dicts.

    Returns:
        List of cycle member IDs if a cycle exists, None if DAG is valid.
    """
    ts = build_dependency_graph(signals)
    try:
        ts.prepare()
        # Drain the sorter to fully validate
        while ts.is_active():
            nodes = ts.get_ready()
            ts.done(*nodes)
        return None
    except CycleError as e:
        # e.args[1] contains the cycle nodes
        return list(e.args[1]) if len(e.args) > 1 else []


def topological_order(
    signals: list[dict[str, Any]],
) -> list[str]:
    """Return signal IDs in topological (dependency) order.

    Args:
        signals: List of signal config dicts.

    Returns:
        List of signal IDs where dependencies appear before dependents.
    """
    ts = build_dependency_graph(signals)
    return list(ts.static_order())


def order_signals_for_execution(
    signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Order signals for execution: tier ordering + within-tier topological sort.

    Groups signals by signal_class tier (foundational, evaluative, inference).
    Within each tier, builds a sub-graph using ONLY within-tier dependency
    edges and sorts topologically. Cross-tier dependencies are excluded from
    per-tier sub-graphs to avoid missing-node errors.

    Falls back to original order within a tier if CycleError is encountered
    (load-time detection should have caught it, but defensive).

    Args:
        signals: List of signal config dicts.

    Returns:
        Flat list of signal dicts in execution order.
    """
    if not signals:
        return []

    # Group by tier
    tiers: dict[str, list[dict[str, Any]]] = {}
    for sig in signals:
        tier = sig.get("signal_class", _DEFAULT_TIER)
        if tier not in _TIER_ORDER:
            tier = _DEFAULT_TIER
        tiers.setdefault(tier, []).append(sig)

    result: list[dict[str, Any]] = []

    # Process tiers in order
    for tier_name in sorted(_TIER_ORDER, key=lambda t: _TIER_ORDER[t]):
        tier_signals = tiers.get(tier_name, [])
        if not tier_signals:
            continue

        # Build within-tier sub-graph
        tier_ids = {s["id"] for s in tier_signals}
        sig_by_id = {s["id"]: s for s in tier_signals}

        try:
            ts: TopologicalSorter[str] = TopologicalSorter()
            for sig in tier_signals:
                sid = sig["id"]
                deps: list[dict[str, Any]] = sig.get("depends_on") or []
                # Only include deps that are within this tier
                within_tier_deps = []
                for dep in deps:
                    dep_id = dep.get("signal", "") if isinstance(dep, dict) else str(dep)
                    if dep_id in tier_ids:
                        within_tier_deps.append(dep_id)
                ts.add(sid, *within_tier_deps)

            ordered_ids = list(ts.static_order())
            result.extend(sig_by_id[sid] for sid in ordered_ids)
        except CycleError:
            logger.warning(
                "Cycle detected within tier '%s'; using unsorted order",
                tier_name,
            )
            result.extend(tier_signals)

    return result


def generate_graph_data(
    signals: list[dict[str, Any]],
    section_filter: str = "",
    type_filter: str = "",
) -> dict[str, Any]:
    """Build D3-compatible nodes + links data structure.

    Args:
        signals: List of signal config dicts from load_signals().
        section_filter: If set, only include signals in this report_section.
        type_filter: If set, only include signals with this signal_class
            (foundational, evaluative, inference).

    Returns:
        Dict with ``nodes``, ``links``, and ``stats`` keys.
        Each node: {id, name, signal_class, group, section, field_path, ...}
        Each link: {source, target}
        Stats: {total_nodes, total_edges, foundational, evaluative, inference,
                sections, groups}
    """
    # Apply filters
    filtered = signals
    if section_filter:
        section_lower = section_filter.lower()
        filtered = [
            s for s in filtered
            if (s.get("report_section") or "").lower() == section_lower
        ]
    if type_filter:
        type_lower = type_filter.lower()
        filtered = [
            s for s in filtered
            if (s.get("signal_class") or _DEFAULT_TIER).lower() == type_lower
        ]

    filtered_ids = {s["id"] for s in filtered}

    # Build nodes
    nodes: list[dict[str, Any]] = []
    for sig in filtered:
        deps = sig.get("depends_on") or []
        dep_ids = []
        for dep in deps:
            dep_id = dep.get("signal", "") if isinstance(dep, dict) else str(dep)
            if dep_id and dep_id in filtered_ids:
                dep_ids.append(dep_id)

        node: dict[str, Any] = {
            "id": sig["id"],
            "name": sig.get("name", sig["id"]),
            "signal_class": sig.get("signal_class", _DEFAULT_TIER),
            "group": sig.get("group", ""),
            "section": sig.get("report_section", ""),
            "field_path": sig.get("field_path", ""),
            "description": sig.get("description", ""),
            "threshold": sig.get("threshold", ""),
            "category": sig.get("category", ""),
            "depends_on": dep_ids,
            "has_deps": len(dep_ids) > 0,
        }
        nodes.append(node)

    # Build links (source = dependency, target = dependent)
    links: list[dict[str, str]] = []
    for sig in filtered:
        sid = sig["id"]
        deps = sig.get("depends_on") or []
        for dep in deps:
            dep_id = dep.get("signal", "") if isinstance(dep, dict) else str(dep)
            if dep_id and dep_id in filtered_ids:
                links.append({"source": dep_id, "target": sid})

    # Compute stats
    class_counts: dict[str, int] = {}
    section_set: set[str] = set()
    group_set: set[str] = set()
    for node in nodes:
        sc = node["signal_class"]
        class_counts[sc] = class_counts.get(sc, 0) + 1
        if node["section"]:
            section_set.add(node["section"])
        if node["group"]:
            group_set.add(node["group"])

    stats: dict[str, Any] = {
        "total_nodes": len(nodes),
        "total_edges": len(links),
        "foundational": class_counts.get("foundational", 0),
        "evaluative": class_counts.get("evaluative", 0),
        "inference": class_counts.get("inference", 0),
        "sections": sorted(section_set),
        "groups": sorted(group_set),
    }

    return {"nodes": nodes, "links": links, "stats": stats}


__all__ = [
    "build_dependency_graph",
    "detect_cycles",
    "generate_graph_data",
    "order_signals_for_execution",
    "topological_order",
]
