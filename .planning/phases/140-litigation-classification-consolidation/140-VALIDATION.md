---
phase: 140
slug: litigation-classification-consolidation
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-03-28
---

# Phase 140 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` ([tool.pytest.ini_options]) |
| **Quick run command** | `uv run pytest tests/stages/extract/test_litigation_classifier.py -x` |
| **Full suite command** | `uv run pytest tests/stages/extract/ -x` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/stages/extract/test_litigation_classifier.py -x`
- **After every plan wave:** Run `uv run pytest tests/stages/extract/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 140-01-01 | 01 | 1 | LIT-01, LIT-02, LIT-03, LIT-04, LIT-05 | unit | `uv run pytest tests/stages/extract/test_litigation_classifier.py -x` | TDD | ⬜ pending |
| 140-01-02 | 01 | 1 | LIT-01, LIT-04 | integration | `uv run pytest tests/stages/extract/ -x` | TDD | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Note: TDD-within-task pattern — tests written first, then implementation.*

---

## Wave 0 Requirements

*Existing pytest infrastructure covers all framework needs. Test files created via TDD within tasks.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| AAPL worksheet shows classified, deduplicated litigation entries with year suffixes | LIT-01, LIT-02, LIT-03 | Requires full pipeline run + HTML inspection | Run `underwrite AAPL --fresh`, open HTML, check litigation section for case classifications, dedup, year labels |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (TDD-within-task)
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
