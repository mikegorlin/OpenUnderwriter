---
phase: 133
slug: stock-and-market-intelligence
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 133 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/stages/render/test_market*.py tests/stages/extract/test_stock*.py tests/stages/extract/test_volume*.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds (quick), ~120 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 133-01-01 | 01 | 1 | STOCK-01 | unit | `uv run pytest tests/stages/extract/test_stock_drop_decomposition.py -x -q` | ✅ | ⬜ pending |
| 133-01-02 | 01 | 1 | STOCK-03 | unit | `uv run pytest tests/stages/extract/test_stock_performance*.py -x -q` | ✅ | ⬜ pending |
| 133-01-03 | 01 | 1 | STOCK-04 | unit | `uv run pytest tests/stages/extract/test_stock_performance*.py -x -q` | ✅ | ⬜ pending |
| 133-02-01 | 02 | 1 | STOCK-07 | unit | `uv run pytest tests/stages/extract/test_volume*.py -x -q` | ✅ | ⬜ pending |
| 133-02-02 | 02 | 1 | STOCK-08 | unit | `uv run pytest tests/stages/render/test_market*.py -x -q` | ❌ W0 | ⬜ pending |
| 133-03-01 | 03 | 2 | STOCK-01,02 | integration | `uv run pytest tests/stages/render/test_market*.py -x -q` | ✅ | ⬜ pending |
| 133-03-02 | 03 | 2 | STOCK-04,05 | integration | `uv run pytest tests/stages/render/test_market*.py -x -q` | ✅ | ⬜ pending |
| 133-03-03 | 03 | 2 | STOCK-06 | integration | `uv run pytest tests/stages/render/test_market*.py -x -q` | ✅ | ⬜ pending |
| 133-03-04 | 03 | 2 | STOCK-07,08 | integration | `uv run pytest tests/stages/render/test_market*.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/stages/render/test_market_correlation.py` — stubs for STOCK-08 correlation metrics
- [ ] `tests/stages/extract/test_earnings_reaction.py` — stubs for STOCK-04/05 multi-day returns

*Existing infrastructure covers most phase requirements via existing test files.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Drop event cards render visually correct | STOCK-01 | Visual layout verification | Run pipeline for test ticker, open HTML, verify drop cards have attribution split |
| Earnings table shows all columns | STOCK-04 | Visual layout verification | Check earnings table has EPS, revenue, day-of/next-day/1-week columns |
| Volume anomaly cross-referencing | STOCK-07 | Requires real data | Run pipeline, verify volume spikes show 8-K/news catalysts |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
