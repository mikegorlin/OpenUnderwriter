---
phase: 112
slug: signal-driven-scoring
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 112 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/stages/score/ -x -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~60 seconds (score tests), ~300 seconds (full) |

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
| 112-01-01 | 01 | 1 | FSCORE-01 | unit | `uv run pytest tests/stages/score/test_factor_data_signals.py -x` | ❌ W0 | ⬜ pending |
| 112-01-02 | 01 | 1 | FSCORE-01 | unit | `uv run pytest tests/stages/score/test_factor_data_signals.py::test_weighted_aggregation -x` | ❌ W0 | ⬜ pending |
| 112-02-01 | 02 | 2 | FSCORE-02 | integration | `uv run pytest tests/stages/score/test_signal_scoring_influence.py -x` | ❌ W0 | ⬜ pending |
| 112-02-02 | 02 | 2 | FSCORE-03 | unit | `uv run pytest tests/stages/score/test_factor_score_contributions.py -x` | ❌ W0 | ⬜ pending |
| 112-02-03 | 02 | 2 | FSCORE-04 | integration | `uv run pytest tests/stages/score/test_shadow_signal_calibration.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/stages/score/test_factor_data_signals.py` — stubs for FSCORE-01 (signal-driven factor data reads + weighted aggregation)
- [ ] `tests/stages/score/test_signal_scoring_influence.py` — stubs for FSCORE-02 (score changes when signals trigger)
- [ ] `tests/stages/score/test_factor_score_contributions.py` — stubs for FSCORE-03 (factor breakdown shows signal contributions)
- [ ] `tests/stages/score/test_shadow_signal_calibration.py` — stubs for FSCORE-04 (shadow comparison for 3 tickers)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| HTML rendering of signal attribution | FSCORE-03 | Visual layout verification | Run `underwrite RPM`, open HTML, check scoring section shows signal contributions per factor |
| Shadow calibration report readability | FSCORE-04 | Report review | Open calibration report, verify old vs new comparison makes sense to underwriter |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
