---
phase: 83
name: Dependency Graph & Visualization
created: 2026-03-08
source: auto-approved (user away, --auto mode)
---

# Phase 83 Context: Dependency Graph & Visualization

## Phase Goal

Signals execute in dependency-ordered layers (foundational first, evaluative second, inference third) with cycle detection at load time, and the brain's signal relationships are explorable through interactive visualization.

## Requirements

- GRAPH-01: Signal dependency DAG from `depends_on` fields using graphlib.TopologicalSorter
- GRAPH-02: Cycle detection at load time with clear error identifying cycle members
- GRAPH-03: Signals execute in dependency-ordered layers
- GRAPH-04: Interactive HTML visualization of signal dependency graph
- GRAPH-05: Visualization with filtering by section/type/tier

## Decisions

### 1. Visualization Library: D3.js force-directed graph

**Decision:** Use D3.js (CDN-loaded) for the interactive DAG visualization, not vanilla SVG.

**Rationale:** 476 signals with 55+ dependency edges is too complex for manual SVG layout. D3's force-directed graph handles node positioning, zoom/pan, and interactive filtering. The audit report (82-04) proved vanilla JS works for tables, but a DAG needs proper graph layout. D3 is the standard for this; no npm build needed — CDN link in template.

**Constraint:** Single self-contained HTML file with inline JS and CDN D3. No build step.

### 2. Cycle Detection: At load time in BrainLoader

**Decision:** Integrate cycle detection into `brain_unified_loader.py` during `_warn_v3_fields()` or as a new validation step after signal loading.

**Rationale:** Load time is the earliest possible detection point. Failing at execution time (in signal_engine) means the pipeline has already spent time on RESOLVE/ACQUIRE/EXTRACT. Fail fast, fail loud. Use `graphlib.TopologicalSorter` (stdlib) which raises `CycleError` with the cycle members.

**Constraint:** Detection is a WARNING at load time (not all signals have depends_on yet). Becomes an ERROR when all signals have depends_on populated.

### 3. Execution Ordering: Tier-based with within-tier topological sort

**Decision:** Execute in 3 tiers (foundational → evaluative → inference), with topological sort within each tier for signals that have depends_on edges to other signals in the same tier.

**Rationale:** Pure topological sort would interleave tier types. The 3-tier model (already in signal_class) provides coarse ordering. Within a tier, depends_on provides fine ordering. Signals without depends_on run in any order within their tier.

**Integration point:** `signal_engine.execute_signals()` — reorder the signal list before the processing loop. No changes to individual signal evaluation logic.

### 4. Visualization Scope: Exploration tool, not execution monitor

**Decision:** The visualization is a static HTML artifact showing the dependency DAG. It is NOT a live execution dashboard.

**Rationale:** The brain audit HTML (82-04) established the pattern — generate once, open in browser. No WebSocket, no live updates. Users open it to understand relationships, not to monitor runs.

**Features:**
- Nodes colored by signal_class (foundational=blue, evaluative=green, inference=orange)
- Edges from depends_on relationships
- Click node → sidebar with signal details (name, group, field_path, thresholds)
- Filter panel: by section (manifest), by signal_class, by group
- Zoom/pan controls
- Stats summary (node/edge counts, tier distribution)

### 5. CLI Command: `brain visualize`

**Decision:** Add as Typer sub-command following existing cli_brain_*.py pattern.

**Flags:** `--output` (path), `--section` (filter), `--type` (foundational/evaluative/inference), `--open` (auto-open browser)

## Code Context

### Reusable Assets
- `brain_signal_schema.py:367-370` — `depends_on: list[SignalDependency]` already defined
- `brain_signal_schema.py:375-378` — `signal_class` field (foundational/evaluative/inference)
- `brain_unified_loader.py:147-148` — Already tracks depends_on coverage at load time
- `brain/templates/audit_report.html` — CSS variables, filter bar, stats cards pattern
- `chain_validator.py` — `ChainReport`, `SignalChainResult` models for structured output
- `brain_audit.py:582-693` — `generate_audit_html()` Jinja2 rendering pattern

### Integration Points
- `signal_engine.py:44-169` — `execute_signals()` loop needs reordering before execution
- `brain_unified_loader.py` — Add cycle detection during/after load
- `cli_brain.py` — Add `visualize` sub-command
- `brain_health.py` — Add dependency coverage metrics

### Key Data
- 476 total signals across 36 YAML files
- 55 signals currently have depends_on populated
- 26 foundational, 422 evaluative, 28 inference (by signal_class)
- 337/476 have field_path populated
- graphlib.TopologicalSorter available in Python 3.12 stdlib

## Deferred Ideas

- Live execution monitoring dashboard (too complex, not needed for D&O analysis)
- Parallel signal execution within tiers (optimization — not in scope for v5.0)
- Interactive YAML editing from visualization (mutation belongs in CLI, not visualization)

## Prior Phase Context

Phase 82 completed: All 476 signals have signal_class, group, depends_on fields. Old type/facet removed. 19 contract tests pass. This phase builds on that foundation.
