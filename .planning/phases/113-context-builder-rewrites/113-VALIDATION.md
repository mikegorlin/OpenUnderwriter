---
phase: 113
slug: context-builder-rewrites
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 113 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/stages/render/ -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~10 seconds (render), ~60 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/stages/render/ -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 113-01-* | 01 | 1 | BUILD-01 | unit + smoke | `uv run pytest tests/stages/render/ -x -q -k "company"` | Partial | ⬜ pending |
| 113-02-* | 02 | 1 | BUILD-02 | unit | `uv run pytest tests/stages/render/ -x -q -k "financial"` | Partial | ⬜ pending |
| 113-03-* | 03 | 1 | BUILD-03 | unit | `uv run pytest tests/stages/render/ -x -q -k "market"` | Partial | ⬜ pending |
| 113-04-* | 04 | 1 | BUILD-04 | unit | `uv run pytest tests/stages/render/ -x -q -k "governance"` | Partial | ⬜ pending |
| 113-05-* | 05 | 2 | BUILD-05 | unit | `uv run pytest tests/stages/render/ -x -q -k "litigation"` | Partial | ⬜ pending |
| 113-06-* | 06 | 2 | BUILD-06, BUILD-08 | unit | `uv run pytest tests/stages/render/ -x -q -k "scoring or analysis or hae"` | Partial | ⬜ pending |
| W0-01 | W0 | 0 | BUILD-07 | smoke | `wc -l src/do_uw/stages/render/context_builders/*.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/stages/render/test_builder_line_limits.py` — verify all builders <300 lines (BUILD-07)
- [ ] `tests/stages/render/test_signal_consumption.py` — verify each builder consumes signals for evaluative content
- [ ] `tests/stages/render/test_hae_context.py` — H/A/E radar chart context (BUILD-08)
- [ ] Existing 790 render tests provide regression coverage — no additional framework needed

*Existing infrastructure covers framework needs. Wave 0 adds phase-specific verification.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| HTML output renders correctly after rewrites | ALL | Visual regression | Run `underwrite RPM --fresh`, open HTML, compare section-by-section |
| Signal fallback produces equivalent content | ALL | Content quality | Compare evaluative text before/after rewrite for same ticker |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
