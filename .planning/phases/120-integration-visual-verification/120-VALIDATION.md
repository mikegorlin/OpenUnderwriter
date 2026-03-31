---
phase: 120
slug: integration-visual-verification
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 120 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (existing) |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `uv run pytest tests/brain/test_do_context_ci_gate.py tests/test_ci_render_paths.py -x` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~30 seconds (quick), ~120 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green + all 3 pipeline outputs verified
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Criterion | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-----------|-----------|-------------------|-------------|--------|
| 120-01-01 | 01 | 1 | SC-5 | static analysis | `uv run pytest tests/test_do_context_evaluative_coverage.py -x` | W0 | pending |
| 120-02-01 | 02 | 1 | SC-1 | pipeline run | `underwrite HNGE --fresh` | N/A | pending |
| 120-02-02 | 02 | 1 | SC-4 | timing | `PERFORMANCE_TESTS=1 uv run pytest tests/test_performance_budget.py -x` | exists | pending |
| 120-03-01 | 03 | 2 | SC-2,SC-3 | structural + visual | `uv run pytest tests/test_integration_120.py -x` | W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_do_context_evaluative_coverage.py` — CI gate for evaluative column traceability
- [ ] `scripts/do_context_coverage.py` — standalone detailed coverage report
- [ ] `tests/test_integration_120.py` — section-by-section structural verification
- [ ] `tests/test_visual_regression.py` — UPDATE: add v8.0 section IDs

---

## Manual-Only Verifications

| Behavior | Criterion | Why Manual | Test Instructions |
|----------|-----------|------------|-------------------|
| Content correctness | SC-2 | Data accuracy requires human judgment | Open HTML, verify company-specific data in every section |
| Section density scaling | SC-2 | Quality assessment | Compare AAPL (clean) vs ANGI (complex) — sections should vary in density |
| Underwriter value | SC-2 | Subjective quality | Would an underwriter find this useful? |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
