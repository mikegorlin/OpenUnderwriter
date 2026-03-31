---
phase: 129
slug: bug-fixes-and-data-integrity
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 129 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (via `uv run pytest`) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `uv run pytest tests/ -x -q --timeout=30 -k "sca or crf or meeting or narrative or governance"` |
| **Full suite command** | `uv run pytest tests/ -q` |
| **Estimated runtime** | ~60 seconds (quick), ~300 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q --timeout=30 -k "sca or crf or meeting or narrative or governance"`
- **After each wave:** Run `uv run pytest tests/ -q`
- **Phase gate:** Full suite green + `underwrite AAPL --fresh` visual verification

---

## Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIX-01 | No $383B hallucination in narrative; no DOJ_FCPA misclassification | unit+integration | `uv run pytest tests/render/ tests/stages/ -k "hallucin or fcpa or narrative_valid" -x` | Likely partial |
| FIX-02 | Gender diversity extracted; current GC correct; all board members present | unit | `uv run pytest tests/extract/ -k "gender or governance or board" -x` | Likely partial |
| FIX-03 | Meeting prep questions contain company-specific data | unit | `uv run pytest tests/render/ -k "meeting" -x` | Likely exists |
| FIX-04 | SCA count identical across all render paths | unit | `uv run pytest tests/ -k "sca_count or sca_consist" -x` | Wave 0 needed |
| FIX-05 | CRF insolvency suppressed for healthy companies; ceiling consistent | unit | `uv run pytest tests/ -k "crf or insolvency or ceiling" -x` | Likely partial |

---

## Wave 0 Gaps

- [ ] `tests/render/test_sca_count_consistency.py` — verifies all SCA count paths produce identical results
- [ ] `tests/render/test_crf_insolvency_suppression.py` — verifies insolvency CRF suppressed for Altman Z > 3.0
- [ ] `tests/render/test_crf_ceiling_display.py` — verifies displayed ceiling matches resolved ceiling

---

## Verification Gates

| Gate | When | Command | Pass Criteria |
|------|------|---------|---------------|
| Quick smoke | Per task commit | Quick run command above | 0 failures |
| Wave regression | Per wave | Full suite command | 0 failures |
| Pipeline verification | Phase gate | `underwrite AAPL --fresh` | No hallucinations, consistent SCA counts, correct board data |
