# Phase 83: Dependency Graph & Visualization - Research

**Researched:** 2026-03-08
**Domain:** Python graphlib (stdlib), D3.js force-directed graph, signal execution ordering
**Confidence:** HIGH

## Summary

Phase 83 adds three capabilities to the brain system: (1) cycle detection at load time using `graphlib.TopologicalSorter`, (2) dependency-ordered signal execution in `signal_engine.execute_signals()`, and (3) an interactive HTML visualization of the signal dependency DAG using D3.js.

The technical foundation is solid. Python 3.12's `graphlib.TopologicalSorter` is stdlib, verified working, and provides both `static_order()` for simple sorting and `prepare()/get_ready()/done()` for layered execution. The `CycleError` exception includes cycle member IDs in `e.args[1]`. D3.js v7 is CDN-available and the established standard for force-directed graph visualization. The existing `audit_report.html` template (639 lines) provides a proven Jinja2 + vanilla JS + CSS variables pattern to follow.

**Primary recommendation:** Build cycle detection into `brain_unified_loader._warn_v3_fields()`, reorder signals in `signal_engine.execute_signals()` by tier then topological sort within tier, and generate a self-contained HTML file using D3.js CDN + Jinja2 template following the audit report pattern.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
1. **Visualization Library: D3.js force-directed graph** -- CDN-loaded, single self-contained HTML file, no build step
2. **Cycle Detection: At load time in BrainLoader** -- integrated into `brain_unified_loader.py`, WARNING at load time (not all signals have depends_on yet), becomes ERROR when all signals populated
3. **Execution Ordering: Tier-based with within-tier topological sort** -- 3 tiers (foundational -> evaluative -> inference), topological sort within each tier, integration point is `signal_engine.execute_signals()`
4. **Visualization Scope: Exploration tool, not execution monitor** -- static HTML artifact, not live dashboard
5. **CLI Command: `brain visualize`** -- Typer sub-command, flags: `--output`, `--section`, `--type`, `--open`

### Claude's Discretion
None specified -- all major decisions locked.

### Deferred Ideas (OUT OF SCOPE)
- Live execution monitoring dashboard
- Parallel signal execution within tiers
- Interactive YAML editing from visualization

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GRAPH-01 | Signal dependency DAG from `depends_on` fields using graphlib.TopologicalSorter | graphlib stdlib verified working in Python 3.12; `static_order()` for full sort, `prepare()/get_ready()/done()` for layered iteration |
| GRAPH-02 | Cycle detection at load time with clear error identifying cycle members | `graphlib.CycleError` provides cycle members in `e.args[1]` as a list; integrate into `_warn_v3_fields()` in brain_unified_loader.py |
| GRAPH-03 | Signals execute in dependency-ordered layers (foundational -> evaluative -> inference) | Reorder `auto_signals` list in `execute_signals()` before the chunk loop; tier from `signal_class`, within-tier from TopologicalSorter |
| GRAPH-04 | Interactive HTML visualization of signal dependency graph | D3.js v7 CDN + Jinja2 template; follow audit_report.html pattern (639-line template with CSS vars, filter bar, stats cards) |
| GRAPH-05 | Visualization with filtering by section/type/tier and signal-to-group-to-section relationships | D3 data model includes section, signal_class, group per node; JS filter toggles show/hide nodes + connected edges |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| graphlib | stdlib (3.12) | TopologicalSorter for DAG ordering + cycle detection | Python stdlib, no dependency; provides CycleError with cycle members |
| D3.js | v7 (CDN) | Force-directed graph layout, zoom/pan, interactive nodes | Industry standard for graph visualization; CDN = no build step |
| Jinja2 | already in project | HTML template rendering for visualization | Already used by audit_report.html; proven pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typer | already in project | CLI sub-command registration | `brain visualize` command |
| rich | already in project | CLI output formatting | Progress/status messages during generation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| D3.js | Cytoscape.js | Cytoscape better for pure graph operations, D3 better for custom layouts; D3 already decided |
| D3.js | vis.js | Simpler API but less control over styling; D3 already decided |
| graphlib | networkx | networkx is heavier, graphlib is stdlib and sufficient |

**Installation:**
```bash
# No new dependencies -- graphlib is stdlib, D3.js is CDN, Jinja2/typer already in project
```

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  brain/
    brain_unified_loader.py   # Add cycle detection in _warn_v3_fields()
    dependency_graph.py       # NEW: DAG construction + topological sort helpers
    templates/
      audit_report.html       # Existing pattern to follow
      dependency_graph.html   # NEW: D3.js visualization template
  stages/
    analyze/
      signal_engine.py        # Modify execute_signals() to reorder by tier+deps
  cli_brain_visualize.py      # NEW: `brain visualize` command
```

### Pattern 1: graphlib.TopologicalSorter for DAG + Cycle Detection
**What:** Build a dependency graph from signal `depends_on` fields, detect cycles, produce execution order.
**When to use:** At signal load time (cycle detection) and before signal execution (ordering).
**Example:**
```python
# Source: Python 3.12 stdlib graphlib
import graphlib

def build_dependency_graph(signals: list[dict]) -> graphlib.TopologicalSorter:
    """Build DAG from signal depends_on fields."""
    graph: dict[str, set[str]] = {}
    for sig in signals:
        sig_id = sig["id"]
        deps = {d["signal"] for d in sig.get("depends_on", []) if d.get("signal")}
        graph[sig_id] = deps
    return graphlib.TopologicalSorter(graph)

def detect_cycles(signals: list[dict]) -> list[str] | None:
    """Return cycle members or None if DAG is valid."""
    ts = build_dependency_graph(signals)
    try:
        ts.prepare()  # Raises CycleError if cycles exist
        return None
    except graphlib.CycleError as e:
        return list(e.args[1])  # e.args[1] is the cycle member list

def topological_order(signals: list[dict]) -> list[str]:
    """Return signal IDs in dependency order."""
    ts = build_dependency_graph(signals)
    return list(ts.static_order())
```

### Pattern 2: Tier-then-Topological Execution Ordering
**What:** Sort signals by signal_class tier first, then topological order within each tier.
**When to use:** In `execute_signals()` before the evaluation loop.
**Example:**
```python
TIER_ORDER = {"foundational": 0, "evaluative": 1, "inference": 2}

def order_signals_for_execution(signals: list[dict]) -> list[dict]:
    """Order signals: tier first, topological within tier."""
    # Group by tier
    by_tier: dict[str, list[dict]] = {"foundational": [], "evaluative": [], "inference": []}
    for sig in signals:
        tier = sig.get("signal_class", "evaluative")
        by_tier.setdefault(tier, []).append(sig)

    ordered = []
    for tier in ("foundational", "evaluative", "inference"):
        tier_signals = by_tier.get(tier, [])
        if not tier_signals:
            continue
        # Build sub-graph for this tier only (cross-tier deps already satisfied)
        sig_ids = {s["id"] for s in tier_signals}
        graph: dict[str, set[str]] = {}
        for sig in tier_signals:
            deps = {d["signal"] for d in sig.get("depends_on", [])
                    if d.get("signal") in sig_ids}  # Only within-tier deps
            graph[sig["id"]] = deps
        try:
            ts = graphlib.TopologicalSorter(graph)
            id_order = list(ts.static_order())
            id_to_sig = {s["id"]: s for s in tier_signals}
            ordered.extend(id_to_sig[sid] for sid in id_order if sid in id_to_sig)
        except graphlib.CycleError:
            # Cycle detection should have caught this at load time
            ordered.extend(tier_signals)
    return ordered
```

### Pattern 3: D3.js Force-Directed Graph with Jinja2 Data Injection
**What:** Render signal graph as interactive HTML with D3.js, injecting data as JSON.
**When to use:** `brain visualize` CLI command.
**Example:**
```python
# In dependency_graph.py or cli_brain_visualize.py
def generate_graph_data(signals: list[dict], manifest) -> dict:
    """Build D3-compatible nodes + links data structure."""
    nodes = []
    links = []
    for sig in signals:
        nodes.append({
            "id": sig["id"],
            "name": sig.get("name", ""),
            "signal_class": sig.get("signal_class", "evaluative"),
            "group": sig.get("group", ""),
            "section": sig.get("report_section", ""),
            "field_path": sig.get("field_path", ""),
        })
        for dep in sig.get("depends_on", []):
            if dep.get("signal"):
                links.append({
                    "source": dep["signal"],
                    "target": sig["id"],
                })
    return {"nodes": nodes, "links": links}
```

### Anti-Patterns to Avoid
- **Building the graph at execution time every run:** Build once at load time, cache the sorted order. The graph structure does not change during a pipeline run.
- **Filtering cross-tier dependencies in TopologicalSorter:** Cross-tier deps (evaluative depending on foundational) are already satisfied by tier ordering. Only include within-tier edges in the per-tier TopologicalSorter to avoid "missing node" errors.
- **Monolithic template:** The audit_report.html is 639 lines. The visualization template will be larger (D3 code). Keep JS logic in template but consider whether D3 setup code should be in a separate `<script>` block with clear sections.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Topological sort | Custom DFS-based sort | `graphlib.TopologicalSorter` | Handles cycles, edge cases, stdlib quality |
| Cycle detection | Custom visited-set traversal | `graphlib.CycleError` from `prepare()` | Reports exact cycle members |
| Graph layout | Manual SVG coordinate calculation | D3.js force simulation | 476 nodes need physics-based layout; manual positioning is infeasible |
| Zoom/pan | Custom SVG transform handlers | D3.js `d3.zoom()` behavior | Touch, wheel, pinch all handled |

**Key insight:** graphlib.TopologicalSorter replaces what would be ~50 lines of hand-rolled graph traversal with cycle detection. D3.js replaces what would be thousands of lines of layout + interaction code.

## Common Pitfalls

### Pitfall 1: Missing Nodes in TopologicalSorter
**What goes wrong:** A signal's `depends_on` references a signal ID that doesn't exist (typo, deleted signal).
**Why it happens:** 55 signals currently have depends_on; referenced signals might not match exact IDs.
**How to avoid:** Before building the graph, validate that all dependency targets exist in the signal set. Log warnings for dangling references and exclude them from the graph.
**Warning signs:** `KeyError` during graph construction or `static_order()`.

### Pitfall 2: Cross-Tier Dependencies in Per-Tier Sort
**What goes wrong:** An evaluative signal depends on a foundational signal. If you include that edge in the evaluative tier's TopologicalSorter, the foundational signal ID won't be in the graph and you get an error.
**Why it happens:** `depends_on` edges cross tiers by design (evaluative depends on foundational).
**How to avoid:** When building per-tier sub-graphs, only include edges where BOTH source and target are in the same tier. Cross-tier ordering is handled by the tier sequence itself.

### Pitfall 3: Foundational Signals Are Currently Skipped
**What goes wrong:** `signal_engine.py:96-98` currently skips foundational signals entirely (`continue`). If execution ordering puts them first, they still won't produce results.
**Why it happens:** Foundational signals are Tier 1 manifest data (acquisition/extraction only, no evaluation).
**How to avoid:** This is correct behavior. Ordering includes all signals conceptually, but the `signal_class == "foundational"` skip remains. The ordering ensures that IF foundational signals ever needed evaluation, they'd run first.

### Pitfall 4: D3 Force Layout with 476 Nodes Performance
**What goes wrong:** Force simulation with 476 nodes and 55+ edges can be slow or produce a tangled layout.
**Why it happens:** Force-directed layouts need tuning for large node counts.
**How to avoid:** Use appropriate force parameters: `d3.forceLink().distance(80)`, `d3.forceManyBody().strength(-100)`, `d3.forceCollide().radius(20)`. Consider initial positions based on tier (y-axis) and section (x-axis) to give the simulation a head start. Also: most signals have NO depends_on edges (421/476), so they'll form disconnected clusters -- the force layout handles this naturally.

### Pitfall 5: Empty depends_on List vs Populated
**What goes wrong:** 421 signals have `depends_on: []` (empty). Graph only has 55 signals with actual edges.
**Why it happens:** Phase 82 populated depends_on but only where clear dependencies exist.
**How to avoid:** In the visualization, distinguish between "has dependencies" and "no dependencies declared". Disconnected nodes should still appear but can be visually de-emphasized. In execution ordering, signals with no depends_on run in any order within their tier.

## Code Examples

### Cycle Detection Integration Point
```python
# In brain_unified_loader.py, add to _warn_v3_fields() or as new function called after it
import graphlib

def _validate_dependency_graph(signals: list[dict[str, Any]]) -> None:
    """Validate signal dependency DAG, warn on cycles."""
    graph: dict[str, set[str]] = {}
    all_ids = {s.get("id", "") for s in signals}

    for sig in signals:
        sig_id = sig.get("id", "")
        deps = set()
        for d in sig.get("depends_on", []):
            dep_id = d.get("signal", "") if isinstance(d, dict) else ""
            if dep_id:
                if dep_id not in all_ids:
                    logger.warning(
                        "Signal %s depends on unknown signal %s", sig_id, dep_id
                    )
                else:
                    deps.add(dep_id)
        graph[sig_id] = deps

    try:
        ts = graphlib.TopologicalSorter(graph)
        ts.prepare()  # Raises CycleError if cycles exist
    except graphlib.CycleError as e:
        cycle_members = e.args[1] if len(e.args) > 1 else []
        logger.error(
            "Circular dependency detected among signals: %s",
            " -> ".join(str(m) for m in cycle_members),
        )
        # WARNING for now (not all signals have depends_on)
        # Will become ERROR when all signals populated
```

### Signal Execution Reordering
```python
# In signal_engine.py execute_signals(), before the chunk loop
def _order_by_dependency(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reorder signals: foundational -> evaluative -> inference, topological within tier."""
    TIER_SEQ = ("foundational", "evaluative", "inference")
    by_tier: dict[str, list[dict[str, Any]]] = {t: [] for t in TIER_SEQ}

    for sig in signals:
        tier = sig.get("signal_class", "evaluative")
        by_tier.setdefault(tier, []).append(sig)

    ordered: list[dict[str, Any]] = []
    for tier in TIER_SEQ:
        tier_sigs = by_tier.get(tier, [])
        if not tier_sigs:
            continue
        tier_ids = {s["id"] for s in tier_sigs}
        graph: dict[str, set[str]] = {}
        for sig in tier_sigs:
            deps = {
                d["signal"] for d in sig.get("depends_on", [])
                if isinstance(d, dict) and d.get("signal") in tier_ids
            }
            graph[sig["id"]] = deps
        try:
            ts = graphlib.TopologicalSorter(graph)
            id_order = list(ts.static_order())
            id_map = {s["id"]: s for s in tier_sigs}
            ordered.extend(id_map[sid] for sid in id_order if sid in id_map)
        except graphlib.CycleError:
            ordered.extend(tier_sigs)  # Fallback: load-time should catch cycles
    return ordered
```

### CLI Command Pattern (following cli_brain.py)
```python
# cli_brain_visualize.py
from do_uw.cli_brain import brain_app

@brain_app.command("visualize")
def visualize(
    output: str = typer.Option("output/brain_dependency_graph.html", "--output", "-o"),
    section: str = typer.Option("", "--section", "-s", help="Filter by manifest section"),
    signal_type: str = typer.Option("", "--type", "-t", help="foundational|evaluative|inference"),
    open_browser: bool = typer.Option(False, "--open", help="Auto-open in browser"),
) -> None:
    """Generate interactive dependency graph visualization."""
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No dependency tracking | `depends_on` field on all 476 signals | Phase 82 (2026-03-08) | Foundation for this phase |
| Flat signal iteration | Chunk-based iteration (CHUNK_SIZE=50) | Earlier phases | Will be wrapped with ordering |
| No execution ordering | signal_class skip for foundational only | Phase 82 | This phase adds full tier ordering |

**Current state of depends_on population:**
- 55/476 signals have non-empty depends_on (11.6%)
- 421/476 have empty depends_on
- All 476 have signal_class populated (26 foundational, 422 evaluative, 28 inference)
- Cross-tier dependencies exist: evaluative signals depend on foundational BASE.* signals

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/brain/test_dependency_graph.py -x` |
| Full suite command | `uv run pytest tests/ -x --timeout=120` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GRAPH-01 | DAG from depends_on via TopologicalSorter | unit | `uv run pytest tests/brain/test_dependency_graph.py::test_build_dag -x` | Wave 0 |
| GRAPH-02 | Cycle detection at load time | unit | `uv run pytest tests/brain/test_dependency_graph.py::test_cycle_detection -x` | Wave 0 |
| GRAPH-03 | Tier-ordered signal execution | unit + integration | `uv run pytest tests/stages/analyze/test_signal_execution_order.py -x` | Wave 0 |
| GRAPH-04 | HTML visualization generation | unit | `uv run pytest tests/brain/test_dependency_graph.py::test_generate_html -x` | Wave 0 |
| GRAPH-05 | Filtering by section/type/tier | unit | `uv run pytest tests/brain/test_dependency_graph.py::test_graph_data_filtering -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/brain/test_dependency_graph.py -x`
- **Per wave merge:** `uv run pytest tests/ -x --timeout=120`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/brain/test_dependency_graph.py` -- covers GRAPH-01, GRAPH-02, GRAPH-04, GRAPH-05
- [ ] `tests/stages/analyze/test_signal_execution_order.py` -- covers GRAPH-03

## Open Questions

1. **depends_on data format: dict vs SignalDependency**
   - What we know: YAML stores `depends_on` as list of dicts `{signal: "...", field: "..."}`. At schema level it's `list[SignalDependency]`. In the loader, signals are returned as raw dicts (not validated Pydantic models).
   - What's unclear: Whether the loader returns depends_on as raw dicts or validated SignalDependency objects.
   - Recommendation: Handle both -- access as `d.get("signal")` for dict, `d.signal` for Pydantic. The loader likely returns raw dicts since `load_signals()` returns `dict[str, Any]`.

2. **Warning vs Error threshold for cycle detection**
   - What we know: CONTEXT.md says WARNING now, ERROR when all signals have depends_on.
   - What's unclear: How to determine "all signals have depends_on" -- is it 100%? 90%?
   - Recommendation: WARNING always. Add a config threshold or hardcode: if >90% have depends_on, treat cycles as ERROR.

## Sources

### Primary (HIGH confidence)
- Python 3.12 graphlib stdlib -- verified via local Python execution
- Project source: `brain_signal_schema.py` lines 132-141 (SignalDependency), 362-378 (V3 fields)
- Project source: `signal_engine.py` lines 44-169 (execute_signals loop)
- Project source: `brain_unified_loader.py` lines 116-168 (_warn_v3_fields)
- Project source: `cli_brain.py` (full file -- CLI pattern for brain commands)
- Project source: `brain/templates/audit_report.html` (639 lines -- HTML template pattern)
- Project source: Signal YAML files with depends_on (46 files, sample format verified)

### Secondary (MEDIUM confidence)
- D3.js v7 force-directed graph API -- well-known library, CDN at `https://d3js.org/d3.v7.min.js`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - graphlib is stdlib, D3.js is well-established, all verified
- Architecture: HIGH - integration points clearly identified in existing code
- Pitfalls: HIGH - derived from actual code inspection (cross-tier deps, empty depends_on, foundational skip)

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (stable -- stdlib + established library)
