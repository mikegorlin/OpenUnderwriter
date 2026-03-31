---
phase: 145
slug: rename-deduplication
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 145 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/brain/ tests/stages/render/ -x -q --timeout=30` |
| **Full suite command** | `uv run pytest tests/ -x -q --timeout=60` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/brain/ tests/stages/render/ -x -q --timeout=30`
- **After every plan wave:** Run `uv run pytest tests/ -x -q --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 145-01-01 | 01 | 1 | NAME-01 | grep | `grep -r "beta_report" src/ tests/ \| wc -l` → 0 | ✅ | ⬜ pending |
| 145-01-02 | 01 | 1 | NAME-02 | unit | `uv run pytest tests/ -x -q --timeout=60` | ✅ | ⬜ pending |
| 145-02-01 | 02 | 2 | DEDUP-01 | grep | `grep -c "revenue" output/*/uw_analysis_worksheet.html` sections | ✅ | ⬜ pending |
| 145-02-02 | 02 | 2 | DEDUP-02 | unit | `uv run pytest tests/stages/render/ -x -q` | ✅ | ⬜ pending |
| 145-02-03 | 02 | 2 | DEDUP-03 | grep | header bar check for MCap/Revenue/Price/Employees | ✅ | ⬜ pending |
| 145-02-04 | 02 | 2 | DEDUP-04 | unit | `uv run pytest tests/brain/test_contract_enforcement.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Tests in `tests/stages/render/` and `tests/brain/` already exercise context builders and template rendering.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual dedup in rendered HTML | DEDUP-01 | Requires visual inspection of rendered output | Open worksheet HTML, verify revenue only in Financial + header |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
