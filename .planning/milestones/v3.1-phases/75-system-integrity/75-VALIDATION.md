---
phase: 75
slug: system-integrity
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 75 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/test_system_integrity_75.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_system_integrity_75.py -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 75-01-01 | 01 | 1 | SYS-01 | unit | `uv run pytest tests/test_system_integrity_75.py -k manifest` | ❌ W0 | ⬜ pending |
| 75-01-02 | 01 | 1 | SYS-02 | unit | `uv run pytest tests/test_system_integrity_75.py -k foundational` | ❌ W0 | ⬜ pending |
| 75-01-03 | 01 | 1 | SYS-03 | unit | `uv run pytest tests/test_system_integrity_75.py -k coverage` | ❌ W0 | ⬜ pending |
| 75-02-01 | 02 | 1 | SYS-04 | unit | `uv run pytest tests/test_system_integrity_75.py -k facet_audit` | ❌ W0 | ⬜ pending |
| 75-02-02 | 02 | 1 | SYS-05 | unit | `uv run pytest tests/test_system_integrity_75.py -k orphan` | ❌ W0 | ⬜ pending |
| 75-03-01 | 03 | 2 | SYS-06 | integration | `uv run pytest tests/test_system_integrity_75.py -k semantic_qa` | ❌ W0 | ⬜ pending |
| 75-03-02 | 03 | 2 | SYS-07 | integration | `uv run pytest tests/test_system_integrity_75.py -k value_match` | ❌ W0 | ⬜ pending |
| 75-04-01 | 04 | 2 | SYS-08 | unit | `uv run pytest tests/test_system_integrity_75.py -k feedback` | ❌ W0 | ⬜ pending |
| 75-04-02 | 04 | 2 | SYS-09 | unit | `uv run pytest tests/test_system_integrity_75.py -k fire_rate` | ❌ W0 | ⬜ pending |
| 75-04-03 | 04 | 2 | SYS-10 | unit | `uv run pytest tests/test_system_integrity_75.py -k lifecycle` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_system_integrity_75.py` — stubs for SYS-01 through SYS-10
- [ ] Fixtures for brain signal YAML loading, template discovery, state.json loading

*Existing pytest infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rendered HTML revenue matches XBRL source | SYS-06 | Requires pipeline output + visual inspection | Run pipeline for WWD, compare HTML revenue to state.json XBRL value |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
