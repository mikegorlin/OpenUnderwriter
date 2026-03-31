---
phase: 78
slug: signal-disposition-audit-trail
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 78 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/brain/test_signal_disposition.py -x -q` |
| **Full suite command** | `uv run pytest tests/brain/test_signal_disposition.py tests/stages/render/test_audit_appendix.py -x -q` |
| **Estimated runtime** | ~8 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/brain/test_signal_disposition.py -x -q`
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 8 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 78-01-01 | 01 | 1 | AUDIT-01 | unit | `uv run pytest tests/brain/test_signal_disposition.py -x -q` | No W0 | pending |
| 78-01-02 | 01 | 1 | AUDIT-01 | integration | `uv run pytest tests/brain/test_signal_disposition.py -x -q` | No W0 | pending |
| 78-02-01 | 02 | 2 | AUDIT-02, AUDIT-03 | integration | `uv run pytest tests/stages/render/test_audit_appendix.py -x -q` | No W0 | pending |
| 78-02-02 | 02 | 2 | AUDIT-02, AUDIT-03 | integration | `uv run pytest tests/stages/render/test_audit_appendix.py -x -q` | No W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/brain/test_signal_disposition.py` — stubs for AUDIT-01 (disposition tagging)
- [ ] `tests/stages/render/test_audit_appendix.py` — stubs for AUDIT-02, AUDIT-03 (HTML appendix rendering)

*Existing test infrastructure (pytest, conftest) covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Audit appendix visual layout | AUDIT-02 | HTML rendering quality | Run pipeline on test ticker, open HTML, verify audit appendix section renders with disposition counts and per-section drill-down |
| Skipped signal reasons readable | AUDIT-03 | Content quality check | Verify each SKIPPED signal has a human-readable categorized reason in the appendix |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 8s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
