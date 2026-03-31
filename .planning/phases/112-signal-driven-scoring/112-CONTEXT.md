# Phase 112: Signal-Driven Scoring - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Refactor the 10-factor scoring engine to consume signal results instead of reading ExtractedData directly. Signals must influence the composite score, factor breakdowns, and tier classification. Collapse the two parallel evaluation paths (signals + direct data reads) into one signal-driven path with rule-based fallback.

</domain>

<decisions>
## Implementation Decisions

### Signal-to-Factor Mapping
- Signals declare their factor in YAML (`scoring.factor` field, e.g., `F1_prior_litigation`) — brain portability preserved, signals are fully self-describing
- A signal can contribute to multiple factors with per-factor weights (e.g., governance signal → F9 at weight 1.0 + F10 at weight 0.5)
- `factor_data.py` queries signals by factor tag instead of reading ExtractedData directly
- DEFERRED and SKIPPED signals are excluded from factor score calculation but contribute to a per-factor "data completeness" metric — low completeness lowers confidence, not the score itself

### Score Aggregation Formula
- Weighted severity sum, normalized to 0-10 scale: each TRIGGERED signal contributes severity × weight, sum normalized by total possible weight
- YAML declares default signal weight (`scoring.weight: 1.0`), scoring.json can override per-factor for calibration flexibility
- Phased migration: signal-driven aggregation is the primary score; if a factor has <50% signal coverage, fall back to old rule-based score for that factor. Remove fallback once coverage is high.
- Composite score continues to use existing weighted average of factor scores — only factor-level calculation changes, not composite formula

### Calibration & History
- Accept new signal-driven scores as truth — if old scores were wrong due to missing data, the new score IS better
- Full change tracking: every run stores factor-level diff with signal attribution (old score, new score, delta, which signals drove the change, data completeness %)
- Shadow comparison report for 3 test tickers (RPM, HNGE, V) showing old vs new scoring with full signal attribution
- Storage: Claude's discretion (DuckDB, JSON, or both) — must NOT be committed to git (too large)

### Factor Contribution Display
- Top 3 contributing signals shown per factor + expandable full signal list (progressive disclosure, CIQ-style density)
- Augment existing scoring section — add "Signal Attribution" subsection below each factor, don't replace existing layout
- Per-factor confidence bar visible to underwriters (e.g., "15/20 signals evaluated") — transparency on evidence strength
- Factor weights visible in the factor table (e.g., F1 = 15%) — full model transparency for underwriters

### Claude's Discretion
- Exact YAML schema for `scoring.factor` and `scoring.weight` fields
- Normalization formula for weighted severity sum
- Signal coverage threshold for rule-based fallback (suggested 50% but tunable)
- Calibration storage format and location (DuckDB vs JSON, gitignored)
- Layout details for signal attribution in worksheet

</decisions>

<specifics>
## Specific Ideas

- "Actuarially sound models built on all available information" — user wants the long-term direction to be actuarially grounded, not just risk scoring. Phase 112 lays the signal foundation; future milestone redesigns pricing models on top.
- "Ensure we are tracking all changes and have a full history" — calibration is not a one-time report but a permanent record of scoring model evolution
- "Considering Supabase for everything" — centralized data store for run history, calibration, feedback loops (deferred to infrastructure milestone)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `factor_data.py` (442 lines) + `factor_data_market.py`: per-factor data extraction — refactor target, currently reads ExtractedData
- `factor_rules.py`: rule matching per factor — becomes fallback path
- `factor_scoring.py`: orchestrates scoring — entry point for signal integration
- `scoring.json`: factor weights, rules, thresholds — override location for signal weights
- `signal_resolver.py` (Phase 111): YAML-driven field resolution — patterns reusable for signal-to-factor querying
- `_signal_consumer.py` + `_signal_fallback.py` (Phase 104): typed signal result extraction infrastructure

### Established Patterns
- Signal results are `SignalResultView` frozen dataclass (Phase 104) — lightweight typed view
- Mechanism dispatch in `signal_engine.py` — pattern for factor-aware signal querying
- `_calibration_report.py` exists in score/ — extend for shadow comparison storage
- `shadow_calibration.py` already exists — may be extendable for signal-driven comparison

### Integration Points
- `signal_engine.py` produces signal results → `factor_data.py` consumes them (new dependency)
- `factor_scoring.py` → `factor_data.py` → signal results (replaces ExtractedData path)
- Worksheet rendering: scoring section template needs signal attribution subsection
- `output_manifest.yaml`: ten_factor_scoring group already exists (display_only: true from Phase 111)

</code_context>

<deferred>
## Deferred Ideas

- **Rethink what factors feed pricing/actuarial models** — user wants actuarially sound models, potentially redesigning F1-F10 decomposition. Signals should feed actuarial models (frequency, severity, settlement) directly. New milestone scope.
- **Supabase as centralized data store** — for calibration history, run data, feedback loops. Infrastructure milestone.
- **Multiplicative H/A/E scoring model (Phase 106 design)** — replace weighted average with P = H x A x E. Future milestone after signal-driven scoring proves stable.

</deferred>

---

*Phase: 112-signal-driven-scoring*
*Context gathered: 2026-03-16*
