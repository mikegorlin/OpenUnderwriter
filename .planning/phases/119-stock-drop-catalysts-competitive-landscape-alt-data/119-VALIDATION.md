---
phase: 119
slug: stock-drop-catalysts-competitive-landscape-alt-data
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 119 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (existing) |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `uv run pytest tests/ -x -q -k "stock_catalyst or competitive or alt_data or multi_horizon or pattern_detect"` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~30 seconds (phase-specific), ~120 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run quick run command (phase-specific tests)
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 119-01-01 | 01 | 1 | STOCK-01,02,04 | unit | `uv run pytest tests/stages/extract/test_stock_catalyst.py -x` | ❌ W0 | ⬜ pending |
| 119-02-01 | 02 | 2 | DOSSIER-07 | unit | `uv run pytest tests/stages/extract/test_competitive_extraction.py -x` | ❌ W0 | ⬜ pending |
| 119-03-01 | 03 | 2 | STOCK-03,05 ALTDATA-01..04 | unit | `uv run pytest tests/stages/benchmark/test_stock_drop_narrative.py -x` | ❌ W0 | ⬜ pending |
| 119-04-01 | 04 | 3 | STOCK-01..06 | unit | `uv run pytest tests/stages/render/test_stock_catalyst_context.py -x` | ❌ W0 | ⬜ pending |
| 119-05-01 | 05 | 3 | DOSSIER-07 ALTDATA-01..04 | unit | `uv run pytest tests/stages/render/test_alt_data_context.py -x` | ❌ W0 | ⬜ pending |
| 119-06-01 | 06 | 4 | ALL | integration | `uv run pytest tests/stages/render/test_119_integration.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/stages/extract/test_stock_catalyst.py` — stock drop catalyst + D&O assessment
- [ ] `tests/stages/extract/test_competitive_extraction.py` — competitive landscape LLM extraction
- [ ] `tests/stages/benchmark/test_stock_drop_narrative.py` — D&O narrative + alt data enrichment
- [ ] `tests/stages/render/test_stock_catalyst_context.py` — stock drop context builders
- [ ] `tests/stages/render/test_alt_data_context.py` — alt data + competitive landscape context builders
- [ ] `tests/stages/render/test_119_integration.py` — end-to-end integration

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual layout matches gold standard | ALL | Layout quality requires human judgment | Open rendered HTML, compare against HNGE PDF |
| D&O commentary is company-specific | ALL | Narrative quality requires human review | Verify no boilerplate |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
