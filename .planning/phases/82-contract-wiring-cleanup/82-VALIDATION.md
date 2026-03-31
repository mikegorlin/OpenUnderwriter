---
phase: 82
slug: contract-wiring-cleanup
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 82 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/brain/ -x -q --timeout=30` |
| **Full suite command** | `uv run pytest tests/ -x -q --timeout=120` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/brain/ -x -q --timeout=30`
- **After every plan wave:** Run `uv run pytest tests/ -x -q --timeout=120`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 82-01-01 | 01 | 1 | SCHEMA-01 | unit | `uv run pytest tests/brain/test_brain_contract.py -k signal_class` | ❌ W0 | ⬜ pending |
| 82-01-02 | 01 | 1 | SCHEMA-02 | unit | `uv run pytest tests/brain/test_brain_contract.py -k group` | ❌ W0 | ⬜ pending |
| 82-01-03 | 01 | 1 | SCHEMA-03 | unit | `uv run pytest tests/brain/test_brain_contract.py -k depends_on` | ❌ W0 | ⬜ pending |
| 82-01-04 | 01 | 1 | SCHEMA-04 | unit | `uv run pytest tests/brain/test_brain_contract.py -k field_path` | ❌ W0 | ⬜ pending |
| 82-02-01 | 02 | 2 | SCHEMA-05 | integration | `uv run pytest tests/brain/test_brain_migration_v3.py` | ❌ W0 | ⬜ pending |
| 82-02-02 | 02 | 2 | SCHEMA-06 | integration | `uv run pytest tests/brain/test_brain_loader.py -k v3` | ❌ W0 | ⬜ pending |
| 82-03-01 | 03 | 3 | SCHEMA-07 | unit | `uv run pytest tests/brain/test_brain_contract.py -k contract` | ❌ W0 | ⬜ pending |
| 82-03-02 | 03 | 3 | SCHEMA-08 | integration | `uv run pytest tests/brain/test_brain_audit.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/brain/test_brain_contract.py` — extend existing with v3 field validation stubs
- [ ] `tests/brain/test_brain_migration_v3.py` — migration script test stubs
- [ ] `tests/brain/test_brain_audit.py` — audit report generation stubs

*Existing test infrastructure covers framework and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Pipeline output identical before/after | SCHEMA-06 | Full pipeline run required | Run `underwrite RPM --fresh`, diff HTML output against pre-migration baseline |
| Audit HTML visual quality | SCHEMA-08 | Visual quality assessment | Open audit HTML, verify institutional-quality presentation |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
