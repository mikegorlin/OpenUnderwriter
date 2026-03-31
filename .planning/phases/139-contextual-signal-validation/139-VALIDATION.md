---
phase: 139
slug: contextual-signal-validation
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-03-27
---

# Phase 139 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` ([tool.pytest.ini_options]) |
| **Quick run command** | `uv run pytest tests/stages/analyze/test_contextual_validator.py -x` |
| **Full suite command** | `uv run pytest tests/stages/analyze/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/stages/analyze/test_contextual_validator.py -x`
- **After every plan wave:** Run `uv run pytest tests/stages/analyze/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 139-01-01 | 01 | 1 | SIG-01, SIG-02, SIG-03, SIG-04, SIG-05, SIG-06, SIG-07 | unit | `uv run pytest tests/stages/analyze/test_contextual_validator.py -x` | TDD (created in task) | ⬜ pending |
| 139-01-02 | 01 | 1 | SIG-01 | integration | `uv run pytest tests/stages/analyze/ -x` | TDD (created in task) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Note: Task 1 follows TDD-within-task pattern — test file created first with failing tests, then implementation. No separate Wave 0 task needed.*

---

## Wave 0 Requirements

*Existing pytest infrastructure covers all framework needs. Test file created via TDD within Task 1 (tests written RED first, then implementation makes them GREEN). No separate Wave 0 pre-creation needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| AAPL worksheet shows zero unannotated IPO signals | SIG-01 | Requires full pipeline run + HTML inspection | Run `underwrite AAPL --fresh`, open HTML, search for IPO/offering signals, verify all have context annotations |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (TDD-within-task pattern)
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
