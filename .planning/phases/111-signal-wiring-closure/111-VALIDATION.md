---
phase: 111
slug: signal-wiring-closure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 111 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/stages/analyze/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/stages/analyze/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 111-01-01 | 01 | 1 | WIRE-01 | unit | `uv run pytest tests/brain/test_signal_groups.py -x` | ❌ W0 | ⬜ pending |
| 111-01-02 | 01 | 1 | WIRE-02 | unit | `uv run pytest tests/brain/test_manifest_governance.py -x` | ❌ W0 | ⬜ pending |
| 111-02-01 | 02 | 2 | WIRE-03 | unit | `uv run pytest tests/stages/analyze/test_mechanism_evaluators.py -x` | ✅ | ⬜ pending |
| 111-03-01 | 03 | 3 | WIRE-04 | integration | `uv run pytest tests/stages/analyze/test_skipped_rate.py -x` | ❌ W0 | ⬜ pending |
| 111-03-02 | 03 | 3 | WIRE-05 | unit | `uv run pytest tests/brain/test_field_declarations.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/brain/test_signal_groups.py` — verify all 562 signals have non-empty group mapping to manifest group (WIRE-01)
- [ ] `tests/brain/test_manifest_governance.py` — verify ungoverned groups marked display_only: true (WIRE-02)
- [ ] `tests/stages/analyze/test_skipped_rate.py` — verify SKIPPED rate on test data <5% (WIRE-04)
- [ ] `tests/brain/test_field_declarations.py` — verify YAML field paths resolve against state model (WIRE-05)
- [ ] Extend `tests/stages/analyze/test_mechanism_evaluators.py` with trend + peer_comparison evaluator tests (WIRE-03)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DEFERRED signals show "Data pending" badge in check panels | WIRE-04 | Visual rendering output | Run pipeline on test ticker, open HTML, verify DEFERRED signals display with badge |
| Hydration regression check | WIRE-05 | Requires full pipeline comparison | Run pipeline pre/post mapper migration, diff signal results, verify zero regressions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
