---
phase: 114
slug: worksheet-restructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 114 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + Playwright (visual regression) |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/stages/render/ -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~15 seconds (render), ~60 seconds (full), ~120 seconds (visual regression) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/stages/render/ -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green + `VISUAL_REGRESSION=1 uv run pytest tests/test_visual_regression.py`
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 114-01-* | 01 | 1 | WS-01 | integration | `uv run pytest tests/stages/render/test_scorecard.py -x` | ❌ W0 | ⬜ pending |
| 114-02-* | 02 | 2 | WS-02, WS-05 | unit | `uv run pytest tests/stages/render/test_hae_badges.py tests/stages/render/test_executive_brief.py -x` | ❌ W0 | ⬜ pending |
| 114-03-* | 03 | 2 | WS-03 | unit | `uv run pytest tests/stages/render/test_epistemological_trace.py -x` | ❌ W0 | ⬜ pending |
| 114-04-* | 04 | 3 | WS-04, WS-06, WS-07, WS-08 | unit + visual | `uv run pytest tests/stages/render/test_print_divergence.py tests/stages/render/test_decision_record.py tests/stages/render/test_reading_paths.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/stages/render/test_scorecard.py` — covers WS-01 (scorecard rendering)
- [ ] `tests/stages/render/test_hae_badges.py` — covers WS-02 (H/A/E badges per section)
- [ ] `tests/stages/render/test_epistemological_trace.py` — covers WS-03 (signal provenance table)
- [ ] `tests/stages/render/test_executive_brief.py` — covers WS-05 (standalone executive brief)
- [ ] `tests/stages/render/test_print_divergence.py` — covers WS-06 (screen vs print behavior)
- [ ] `tests/stages/render/test_decision_record.py` — covers WS-07 (decision documentation)
- [ ] `tests/stages/render/test_reading_paths.py` — covers WS-08 (sidebar TOC + CRF links)
- [ ] Update `SECTION_IDS` in `tests/test_visual_regression.py` for new sections (WS-04)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual quality matches CIQ/S&P standard | ALL | Subjective quality | Open HTML output, compare with CIQ/Bloomberg reference screenshots |
| PDF print layout clean | WS-06 | Page break quality | Print to PDF, verify headers/footers, page breaks at section boundaries |
| Signal heatmap readability | WS-01 | Visual density judgment | Open HTML, verify heatmap cells are readable and hover works |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
