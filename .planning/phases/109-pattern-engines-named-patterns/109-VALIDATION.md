---
phase: 109
slug: pattern-engines-named-patterns
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 109 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing, 5,687+ tests) |
| **Config file** | `pyproject.toml` (existing) |
| **Quick run command** | `uv run pytest tests/stages/score/ -x -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/stages/score/ -x -q`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 109-01-xx | 01 | 1 | PAT-01 | unit | `uv run pytest tests/stages/score/test_conjunction_scan.py -x` | ❌ W0 | ⬜ pending |
| 109-01-xx | 01 | 1 | PAT-02 | unit | `uv run pytest tests/stages/score/test_peer_outlier.py -x` | ❌ W0 | ⬜ pending |
| 109-02-xx | 02 | 1 | PAT-03 | unit | `uv run pytest tests/stages/score/test_migration_drift.py -x` | ❌ W0 | ⬜ pending |
| 109-02-xx | 02 | 1 | PAT-04 | unit | `uv run pytest tests/stages/score/test_precedent_match.py -x` | ❌ W0 | ⬜ pending |
| 109-02-xx | 02 | 1 | PAT-05 | unit + validation | `uv run pytest tests/stages/score/test_case_library.py -x` | ❌ W0 | ⬜ pending |
| 109-03-xx | 03 | 2 | PAT-06 | unit + validation | `uv run pytest tests/stages/score/test_archetypes.py -x` | ❌ W0 | ⬜ pending |
| 109-03-xx | 03 | 2 | PAT-07 | unit | `uv run pytest tests/stages/score/test_pattern_context.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/stages/score/test_conjunction_scan.py` — stubs for PAT-01
- [ ] `tests/stages/score/test_peer_outlier.py` — stubs for PAT-02
- [ ] `tests/stages/score/test_migration_drift.py` — stubs for PAT-03
- [ ] `tests/stages/score/test_precedent_match.py` — stubs for PAT-04
- [ ] `tests/stages/score/test_case_library.py` — stubs for PAT-05 (validates 20 cases load, Pydantic validates)
- [ ] `tests/stages/score/test_archetypes.py` — stubs for PAT-06 (validates 6 archetypes, signal IDs resolve)
- [ ] `tests/stages/score/test_pattern_runner.py` — integration of all engines
- [ ] `tests/stages/score/test_pattern_context.py` — stubs for PAT-07 (firing panel context builder)

*Existing infrastructure covers all phase requirements — no new framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Firing panel visual layout | PAT-07 | HTML rendering quality | Run pipeline on AAPL, open HTML, verify 10-card grid renders with correct colors/badges |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
