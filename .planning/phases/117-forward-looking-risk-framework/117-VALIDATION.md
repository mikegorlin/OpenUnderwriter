---
phase: 117
slug: forward-looking-risk-framework
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 117 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` ([tool.pytest.ini_options]) |
| **Quick run command** | `uv run pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `uv run pytest tests/ --timeout=60` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `uv run pytest tests/ --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 117-01-01 | 01 | 1 | FORWARD-01 | unit | `uv run pytest tests/stages/extract/ -k forward_looking -x` | ❌ W0 | ⬜ pending |
| 117-01-02 | 01 | 1 | FORWARD-02 | unit | `uv run pytest tests/stages/extract/ -k credibility -x` | ❌ W0 | ⬜ pending |
| 117-01-03 | 01 | 1 | FORWARD-03 | unit | `uv run pytest tests/stages/analyze/ -k miss_risk -x` | ❌ W0 | ⬜ pending |
| 117-02-01 | 02 | 1 | FORWARD-04 | unit | `uv run pytest tests/stages/render/ -k forward_risk -x` | ❌ W0 | ⬜ pending |
| 117-02-02 | 02 | 1 | FORWARD-05 | unit | `uv run pytest tests/stages/render/ -k credibility -x` | ❌ W0 | ⬜ pending |
| 117-02-03 | 02 | 1 | FORWARD-06 | unit | `uv run pytest tests/stages/render/ -k growth_estimates -x` | ❌ W0 | ⬜ pending |
| 117-03-01 | 03 | 2 | TRIGGER-01 | unit | `uv run pytest tests/stages/render/ -k monitoring_trigger -x` | ❌ W0 | ⬜ pending |
| 117-03-02 | 03 | 2 | TRIGGER-02 | unit | `uv run pytest tests/stages/render/ -k quick_screen -x` | ❌ W0 | ⬜ pending |
| 117-03-03 | 03 | 2 | TRIGGER-03 | unit | `uv run pytest tests/stages/render/ -k nuclear_trigger -x` | ❌ W0 | ⬜ pending |
| 117-03-04 | 03 | 2 | SCORE-02 | unit | `uv run pytest tests/stages/render/ -k underwriting_posture -x` | ❌ W0 | ⬜ pending |
| 117-03-05 | 03 | 2 | SCORE-03 | unit | `uv run pytest tests/stages/analyze/ -k posture -x` | ❌ W0 | ⬜ pending |
| 117-03-06 | 03 | 2 | SCORE-05 | unit | `uv run pytest tests/stages/analyze/ -k factor_override -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/stages/extract/test_forward_looking_extraction.py` — stubs for FORWARD-01, FORWARD-02
- [ ] `tests/stages/analyze/test_miss_risk.py` — stubs for FORWARD-03, SCORE-03, SCORE-05
- [ ] `tests/stages/render/test_forward_risk_section.py` — stubs for FORWARD-04, FORWARD-05, FORWARD-06
- [ ] `tests/stages/render/test_trigger_matrix.py` — stubs for TRIGGER-01, TRIGGER-02, TRIGGER-03, SCORE-02

*Existing test infrastructure covers framework setup. Only new test files needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Forward Risk Map visual layout | FORWARD-04 | HTML visual rendering | Run worksheet for HNGE, inspect Forward Risk Map section in browser |
| Nuclear trigger display | TRIGGER-03 | Visual verification of "0/5" display | Check nuclear trigger badge renders correctly in HTML output |
| Quick Screen section routing | TRIGGER-02 | Deep-dive link clicks | Click RED/YELLOW flags and verify anchor navigation to correct sections |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
