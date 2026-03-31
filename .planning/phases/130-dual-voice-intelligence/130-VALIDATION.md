---
phase: 130
slug: dual-voice-intelligence
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 130 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (via `uv run pytest`) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `uv run pytest tests/ -x -q --timeout=30 -k "commentary or dual_voice or exec_summary or sca_theory"` |
| **Full suite command** | `uv run pytest tests/ -q` |
| **Estimated runtime** | ~60 seconds (quick), ~300 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run quick command above
- **After each wave:** Run full suite
- **Phase gate:** Full suite green + `underwrite AAPL --rerender` visual verification of dual-voice blocks

---

## Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VOICE-01 | Every analytical section shows dual-voice blocks | unit | `uv run pytest tests/render/ -k "dual_voice" -x` | Wave 0 needed |
| VOICE-02 | Commentary generated via batched LLM in BENCHMARK | unit | `uv run pytest tests/stages/benchmark/ -k "commentary" -x` | Wave 0 needed |
| VOICE-03 | Commentary cached, re-render uses cache | unit | `uv run pytest tests/stages/benchmark/ -k "commentary_cache" -x` | Wave 0 needed |
| VOICE-04 | Commentary cross-validates dollar amounts | unit | `uv run pytest tests/stages/benchmark/ -k "commentary_validation" -x` | Wave 0 needed |
| EXEC-01 | Exec narrative connects findings to SCA theories | unit | `uv run pytest tests/render/ -k "exec_summary or sca_theory" -x` | Wave 0 needed |
| EXEC-02 | Key negatives cite finding + magnitude + factor + theory | unit | `uv run pytest tests/render/ -k "key_negative" -x` | Wave 0 needed |
| EXEC-03 | Key positives cite evidence + quantification + theory defeated | unit | `uv run pytest tests/render/ -k "key_positive" -x` | Wave 0 needed |
| EXEC-04 | Recommendation block shows tier + probability + severity + defense cost | unit | `uv run pytest tests/render/ -k "recommendation" -x` | Wave 0 needed |

---

## Wave 0 Gaps

- [ ] `tests/stages/benchmark/test_commentary_generator.py` — commentary generation, caching, cross-validation
- [ ] `tests/render/test_dual_voice_blocks.py` — dual-voice macro rendering in all 8 sections
- [ ] `tests/render/test_exec_summary_overhaul.py` — recommendation, negatives, positives, SCA theories

---

## Verification Gates

| Gate | When | Command | Pass Criteria |
|------|------|---------|---------------|
| Quick smoke | Per task commit | Quick run command above | 0 failures |
| Wave regression | Per wave | Full suite command | 0 failures |
| Visual verification | Phase gate | `underwrite AAPL --rerender` | Dual-voice blocks visible in all 8 sections |
