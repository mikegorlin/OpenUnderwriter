---
phase: 83
slug: dependency-graph-visualization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 83 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/brain/test_dependency_graph.py tests/brain/test_brain_contract.py -x -q` |
| **Full suite command** | `uv run pytest tests/brain/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/brain/test_dependency_graph.py -x -q`
- **After every plan wave:** Run `uv run pytest tests/brain/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 83-01-01 | 01 | 1 | GRAPH-01 | unit | `uv run pytest tests/brain/test_dependency_graph.py::TestDAGConstruction -x -q` | ❌ W0 | ⬜ pending |
| 83-01-02 | 01 | 1 | GRAPH-02 | unit | `uv run pytest tests/brain/test_dependency_graph.py::TestCycleDetection -x -q` | ❌ W0 | ⬜ pending |
| 83-01-03 | 01 | 1 | GRAPH-03 | unit | `uv run pytest tests/brain/test_dependency_graph.py::TestTieredExecution -x -q` | ❌ W0 | ⬜ pending |
| 83-02-01 | 02 | 2 | GRAPH-03 | integration | `uv run pytest tests/brain/test_dependency_graph.py::TestSignalEngineOrdering -x -q` | ❌ W0 | ⬜ pending |
| 83-03-01 | 03 | 3 | GRAPH-04 | unit | `uv run pytest tests/brain/test_brain_visualize.py::TestDAGVisualization -x -q` | ❌ W0 | ⬜ pending |
| 83-03-02 | 03 | 3 | GRAPH-05 | unit | `uv run pytest tests/brain/test_brain_visualize.py::TestVisualizationFiltering -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/brain/test_dependency_graph.py` — stubs for GRAPH-01, GRAPH-02, GRAPH-03
- [ ] `tests/brain/test_brain_visualize.py` — stubs for GRAPH-04, GRAPH-05

*Existing test infrastructure (pytest, conftest) covers all shared fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Interactive HTML visualization renders correctly in browser | GRAPH-04 | Visual/interactive output | Open generated HTML in browser, verify nodes clickable, zoom/pan works |
| Filter panel updates graph display correctly | GRAPH-05 | Visual interaction | Use filter checkboxes to filter by section/type/tier, verify graph updates |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
