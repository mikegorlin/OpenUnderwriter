---
phase: 84
slug: manifest-section-elimination
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 84 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/brain/test_manifest_migration.py tests/stages/render/test_section_renderer.py -x -q` |
| **Full suite command** | `uv run pytest tests/brain/ tests/stages/render/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 84-01-01 | 01 | 1 | MANIF-01, MANIF-02 | unit | `uv run pytest tests/brain/test_manifest_migration.py -x -q` | ❌ W0 | ⬜ pending |
| 84-02-01 | 02 | 2 | SECT-04 | unit | `uv run pytest tests/brain/test_brain_audit.py tests/brain/test_brain_health.py -x -q` | ✅ | ⬜ pending |
| 84-02-02 | 02 | 2 | SECT-03 | unit | `uv run pytest tests/brain/test_cli_brain_trace.py -x -q` | ✅ | ⬜ pending |
| 84-03-01 | 03 | 3 | SECT-01, SECT-02, MANIF-03 | integration | `uv run pytest tests/stages/render/test_section_renderer.py -x -q` | ✅ | ⬜ pending |
| 84-03-02 | 03 | 3 | MANIF-04, MANIF-05 | integration | `uv run pytest tests/stages/render/ -x -q` | ✅ | ⬜ pending |
| 84-04-01 | 04 | 4 | SECT-05 | integration | `uv run pytest tests/brain/ tests/stages/render/ -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/brain/test_manifest_migration.py` — stubs for MANIF-01, MANIF-02 (manifest group objects, signal self-selection)

*Existing test infrastructure covers all other requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| HTML output visually identical to pre-migration | MANIF-03, MANIF-05 | Visual regression | Run pipeline on RPM and V, compare output files |
| Word output visually identical to pre-migration | MANIF-04 | Visual regression | Open Word docs side by side |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
