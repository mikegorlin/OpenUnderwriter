---
phase: 88
slug: data-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 88 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/stages/extract/test_stock_performance.py tests/stages/render/charts/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q --timeout=60` |
| **Estimated runtime** | ~30 seconds (quick), ~120 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 88-01-01 | 01 | 1 | STOCK-07 | integration | `uv run pytest tests/stages/acquire/ -k market -x -q` | ❌ W0 | ⬜ pending |
| 88-02-01 | 02 | 1 | STOCK-01 | unit | `uv run pytest tests/stages/extract/test_stock_performance.py -x -q` | ❌ W0 | ⬜ pending |
| 88-02-02 | 02 | 1 | STOCK-03 | unit | `uv run pytest tests/stages/extract/test_stock_performance.py -x -q` | ❌ W0 | ⬜ pending |
| 88-03-01 | 03 | 2 | STOCK-01 | integration | `uv run pytest tests/stages/render/charts/ -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/stages/extract/test_return_decomposition.py` — stubs for STOCK-01
- [ ] `tests/stages/extract/test_mdd_ratio.py` — stubs for STOCK-03
- [ ] `tests/stages/acquire/test_market_2y.py` — stubs for STOCK-07

*Existing test infrastructure covers framework and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 2Y chart span visible in HTML | STOCK-07 | Visual check | Open HTML output, verify stock charts span 2 years |
| Return decomposition displayed | STOCK-01 | Visual check | Open HTML output, verify 3-component return breakdown visible |
| MDD ratio displayed | STOCK-03 | Visual check | Open HTML output, verify MDD ratio shown for 1Y and 5Y |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
