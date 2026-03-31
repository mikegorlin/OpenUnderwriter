---
phase: 90
slug: drop-enhancements
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 90 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/stages/extract/test_stock_performance.py tests/stages/render/charts/test_chart_computations.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds (quick), ~120 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/stages/extract/test_stock_performance.py tests/stages/render/charts/test_chart_computations.py tests/stages/extract/test_stock_drop_enrichment.py -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 90-01-01 | 01 | 1 | STOCK-08 | unit | `uv run pytest tests/stages/render/charts/test_chart_computations.py -k decay -x` | ❌ W0 | ⬜ pending |
| 90-01-02 | 01 | 1 | STOCK-09 | unit | `uv run pytest tests/stages/render/charts/test_chart_computations.py -k decomp -x` | ❌ W0 | ⬜ pending |
| 90-01-03 | 01 | 1 | STOCK-06 | unit | `uv run pytest tests/stages/extract/test_stock_drop_enrichment.py -k reverse -x` | ❌ W0 | ⬜ pending |
| 90-02-01 | 02 | 2 | STOCK-08 | integration | `uv run pytest tests/stages/extract/test_stock_performance.py -k decay -x` | ❌ W0 | ⬜ pending |
| 90-02-02 | 02 | 2 | STOCK-06 | integration | `uv run pytest tests/stages/extract/test_stock_performance.py -k disclosure -x` | ❌ W0 | ⬜ pending |
| 90-02-03 | 02 | 2 | STOCK-08, STOCK-09 | integration | `uv run pytest tests/stages/render/ -k "drop" -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/stages/render/charts/test_chart_computations.py` — add stubs for decay and per-drop decomposition
- [ ] `tests/stages/extract/test_stock_drop_enrichment.py` — add stubs for reverse lookup
- [ ] `tests/stages/extract/test_stock_performance.py` — add stubs for decay wiring and disclosure integration

*Existing infrastructure covers framework and fixture needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Drop table sort order reflects recency | STOCK-08 | Visual verification of HTML output | Run `underwrite RPM --fresh`, open HTML, verify drops sorted by decay-weighted severity |
| Market-Driven badge displays correctly | STOCK-09 | Visual layout check | Inspect drops where market > 50%, verify badge renders |
| Corrective disclosure badge + lag | STOCK-06 | Requires real 8-K data | Run pipeline, verify 8-K matches show "8-K +Nd" badge |

*All other behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
