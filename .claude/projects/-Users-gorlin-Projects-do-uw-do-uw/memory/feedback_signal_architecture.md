---
name: feedback_signal_architecture
description: All new features must follow the signal architecture — no extract→render bypasses allowed
type: feedback
---

Every new feature that renders evaluated/scored content MUST follow the signal architecture:
EXTRACT → ANALYZE (brain signals in YAML) → SCORE → RENDER

**Why:** Audit on 2026-03-14 found ~60% of rendered content bypasses the signal engine. Context builders read `state.extracted.*` directly instead of consuming `state.analysis.signal_results`. The 10-K YoY feature was the example that caught this — it went straight from extraction to template with zero signals.

**How to apply:**
1. When adding a new data point that involves risk evaluation/judgment, create brain signal YAML files first
2. Add a signal mapper in `stages/analyze/signal_mappers.py`
3. Context builders should consume signal results via `state.analysis.signal_results`, not raw `state.extracted.*`
4. Register the signal's group in the output manifest
5. The `TestSignalArchitectureGuardrail` contract test will FAIL CI if a new manifest group has no signals and isn't in DISPLAY_ONLY_GROUPS
6. Raw data display (names, numbers, tables) is exempt — only evaluations need signals
7. Rule of thumb: if context builder has `if/elif/else` mapping to HIGH/MODERATE/LOW, it needs a signal

**Systemic fix planned as v7.0 milestone** — 7 phases to retrofit existing context builders. See `.planning/SIGNAL_ARCHITECTURE_MILESTONE.md`.
