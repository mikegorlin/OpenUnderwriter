---
phase: 148
slug: question-driven-underwriting-section
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 148 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/render/test_uw_questions.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q --timeout=30` |
| **Estimated runtime** | ~15 seconds (quick), ~120 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/render/test_uw_questions.py -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -x -q --timeout=30`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | 01 | 1 | QFW-01 | unit | `uv run pytest tests/render/test_uw_questions.py -x -q` | ❌ W0 | ⬜ pending |
| TBD | 01 | 1 | QFW-02 | unit | `uv run pytest tests/render/test_uw_questions.py -x -q` | ❌ W0 | ⬜ pending |
| TBD | 02 | 1 | QFW-04 | unit | `uv run pytest tests/render/test_uw_questions.py -x -q` | ❌ W0 | ⬜ pending |
| TBD | 03 | 2 | QFW-03 | integration | `uv run pytest tests/render/test_uw_questions.py -x -q` | ❌ W0 | ⬜ pending |
| TBD | 03 | 2 | QFW-05 | unit | `uv run pytest tests/render/test_uw_questions.py -x -q` | ❌ W0 | ⬜ pending |
| TBD | 04 | 3 | QFW-06 | visual | manual | N/A | ⬜ pending |
| TBD | 04 | 3 | QFW-07 | integration | `uv run pytest tests/render/test_uw_questions.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/render/test_uw_questions.py` — test stubs for answerer coverage, verdict logic, SCA integration
- [ ] `tests/render/test_screening_answers.py` — test stubs for screening answer engine

*Existing infrastructure covers test framework and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Domain + overall verdict badges render correctly | QFW-06 | Visual layout verification | Open ORCL worksheet HTML, verify domain headers show Favorable/Unfavorable/Mixed badges and section header shows overall assessment |
| Print/PDF optimization | QFW-06 | Print media verification | Print worksheet to PDF, verify completeness bars, verdict dots, and small text render cleanly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
