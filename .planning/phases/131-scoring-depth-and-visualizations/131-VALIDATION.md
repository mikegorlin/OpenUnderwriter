---
phase: 131
slug: scoring-depth-and-visualizations
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 131 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x via uv |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/stages/render/ -x -q --timeout=60` |
| **Full suite command** | `uv run pytest tests/ -x -q --timeout=120` |
| **Estimated runtime** | ~30 seconds (quick), ~120 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan completion:** Run full suite
- **Visual verification:** Re-render AAPL worksheet and inspect scoring section

---

## Key Verification Points

1. Waterfall SVG renders with correct factor contributions and tier threshold lines
2. Radar chart shows 10-factor distribution with risk concentration visible
3. Probability decomposition shows 7+ components with calibration badges
4. Scenario table shows 5-7 company-specific scenarios with score deltas and tier changes
5. Tornado SVG ranks scenarios by impact magnitude
6. Factor cards include dual-voice commentary (factual + D&O bullets)
7. Zero-scored factors show clean documentation
8. No factor codes (F1-F10) in prose text (only in chart labels/tables)
