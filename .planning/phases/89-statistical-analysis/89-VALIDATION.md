---
phase: 89
slug: statistical-analysis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 89 — Validation Strategy

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
| 89-01-01 | 01 | 1 | STOCK-02 | unit | `uv run pytest tests/stages/extract/ -k ddl -x -q` | ❌ W0 | ⬜ pending |
| 89-01-02 | 01 | 1 | STOCK-04 | unit | `uv run pytest tests/stages/extract/ -k abnormal -x -q` | ❌ W0 | ⬜ pending |
| 89-01-03 | 01 | 1 | STOCK-05 | unit | `uv run pytest tests/stages/extract/ -k ewma -x -q` | ❌ W0 | ⬜ pending |
| 89-02-01 | 02 | 2 | STOCK-02,04,05 | integration | `uv run pytest tests/stages/render/ -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/stages/extract/test_ddl_exposure.py` — stubs for STOCK-02
- [ ] `tests/stages/extract/test_abnormal_returns.py` — stubs for STOCK-04
- [ ] `tests/stages/extract/test_ewma_volatility.py` — stubs for STOCK-05

*Existing test infrastructure covers framework and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DDL exposure in pricing section | STOCK-02 | Visual check | Open HTML, verify DDL dollar amount and settlement estimate shown |
| Abnormal return flags on drop days | STOCK-04 | Visual check | Open HTML, verify t-stat on significant days |
| EWMA + regime classification visible | STOCK-05 | Visual check | Open HTML, verify dual volatility display with regime labels |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
