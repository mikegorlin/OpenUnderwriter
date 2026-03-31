---
name: v7.0 milestone decision and signal-render audit findings
description: Pre-v7.0 audit results showing 7/9 context builders bypass signal results entirely; user confirmed v7.0 Signal-Render Integrity as next milestone
type: project
---

## v7.0 Signal-Render Integrity — Decision Context (2026-03-14)

After shipping v6.0, conducted comprehensive audit of signal architecture coverage.

**Key finding:** Only 2 of 19 context builders actually consume `signal_results`:
- `_bull_bear.py` (18 refs) and `narrative.py` (22 refs) — signal-backed
- `financials.py` (0), `market.py` (0), `governance.py` (0), `litigation.py` (0), `scoring.py` (0), `analysis.py` (0) — **fully bypass signals**
- `company.py` (3 refs) — only v6.0 sections use signals, rest bypasses

**Why:** The brain evaluates 490+ signals but the renderer ignores those results for ~60%+ of output, recomputing evaluations from raw `state.extracted.*` data with inline Python `if/elif/else` threshold logic. This means YAML threshold changes don't affect rendered output — dual maintenance problem.

**How to apply:** v7.0 milestone (Phases 102-108) retrofits all 4 major context builders to consume signal_results via a shared `_signal_consumer.py` infrastructure. Detailed plan at `.planning/SIGNAL_ARCHITECTURE_MILESTONE.md`. User explicitly frustrated ("rendering a patchwork of shit") — this is the highest priority work.

**Additional tech debt identified:**
- 19 Python files over 500-line limit (company.py at 1,178 is worst)
- 3 v6.0 HTML stub templates never expanded
- `signal_mappers.py` at 999 lines needs split
