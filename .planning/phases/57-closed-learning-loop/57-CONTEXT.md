# Phase 57: Closed Learning Loop - Context

**Gathered:** 2026-03-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Every pipeline run makes the brain smarter. Statistical calibration analyzes observed values against thresholds and proposes adjustments. Co-occurrence mining discovers correlated signals. Fire rate alerts flag anomalous signal behavior. Signal lifecycle state machine manages signal maturity. All YAML modifications require human approval — the brain observes automatically but never changes itself.

</domain>

<decisions>
## Implementation Decisions

### Calibration Output (LEARN-01)
- `brain audit --calibrate` generates drift report in terminal AND writes proposal entries to DuckDB
- Proposals include specific suggested threshold values computed from observed distribution (e.g., percentile-based)
- Minimum 5+ runs per signal before proposals are generated — confidence level marked based on N
- Covers both numeric thresholds (statistical distribution analysis) and qualitative signals (fire-rate-based recalibration — if 95% fire, threshold may be too low)
- Each proposal includes: current value, observed mean/σ, fire rate, proposed new value, basis, projected impact

### Correlation Handling (LEARN-02)
- Co-occurrence mining runs as part of `brain audit` — analyzes cross-signal fire patterns from brain_signal_runs
- Both same-prefix and cross-prefix correlations analyzed, labeled differently:
  - Same-prefix: labeled "potential redundancy" (e.g., FIN.LIQ.current ↔ FIN.LIQ.quick)
  - Cross-prefix: labeled "risk correlation" (e.g., GOV.BOARD.independence ↔ FIN.DEBT.leverage)
- Redundancy flagging: explicitly flag when 3+ signals in same prefix co-fire >70% — "consider consolidating"
- Co-fire threshold: configurable in brain config YAML, default 70% per requirements
- Storage: confirmed correlations written to signal YAML (`correlated_signals` field), all discovered correlations (including below-threshold) stored in DuckDB for analysis
- Writing correlated_signals to YAML requires manual approval (consistent with "data collection only" automation boundary)

### Underwriter Workflow (LEARN-03, LEARN-04)
- Extend existing CLI: `brain audit --calibrate` for drift, `brain audit --lifecycle` for state transitions
- Approval via `feedback approve <proposal-id>` — applies change immediately to signal YAML
- Full provenance on every change: who approved, statistical basis (N, mean, σ), before/after values, expected impact, logged to brain_changelog
- Audit is on-demand only — pipeline records to brain_signal_runs, underwriter invokes `brain audit` when they want analysis
- Fire rate alerts (>80% or <2%) surfaced in `brain audit` output alongside calibration proposals

### Signal Lifecycle State Machine (LEARN-04)
- States: INCUBATING → ACTIVE → MONITORING → DEPRECATED → ARCHIVED
- Skip-transitions allowed (defined valid transitions, not strictly linear):
  - INCUBATING → ACTIVE (graduated), INCUBATING → ARCHIVED (never worked)
  - ACTIVE → MONITORING (drifting), ACTIVE → DEPRECATED (clearly broken)
  - MONITORING → ACTIVE (re-calibrated), MONITORING → DEPRECATED (confirmed bad)
  - DEPRECATED → ARCHIVED (final cleanup), DEPRECATED → ACTIVE (un-deprecated)
  - ARCHIVED → nothing (point of no return)
- Transition proposals based on multi-factor evidence: fire rate anomalies + signal age (time in state) + feedback reactions
  - INCUBATING → ACTIVE: 5+ runs, fire rate 5-80%, no feedback issues
  - ACTIVE → MONITORING: fire rate >80% or <2% for 3+ consecutive runs, OR 3+ DISAGREE reactions
  - MONITORING → DEPRECATED: fire rate still anomalous after 10 runs, OR confirmed by feedback
  - DEPRECATED → ARCHIVED: 90+ days in DEPRECATED, no objections
- All lifecycle transitions require manual approval via `feedback approve`

### Automation Boundary
- AUTOMATIC (no approval): record signal runs, compute fire rates/effectiveness, detect threshold drift, mine co-occurrences, flag fire rate anomalies
- MANUAL (requires approval): change any threshold value, change lifecycle state, write correlated_signals to YAML, propose signal consolidation, retire/archive signals
- Pipeline does NOT trigger audit — just records data. Audit is a separate analytical step.

### Claude's Discretion
- Statistical methods for drift detection (percentile-based, z-score, etc.)
- DuckDB table schema for correlation storage
- Exact CLI output formatting and Rich table layouts
- How to handle edge cases (signals with mixed numeric/qualitative thresholds, signals with 0 runs)

</decisions>

<specifics>
## Specific Ideas

- "Brain observes automatically but never changes itself" — the automation boundary principle
- Calibration proposals should feel like the existing feedback process workflow — extend, don't reinvent
- Correlation labels (redundancy vs risk correlation) should help underwriters quickly understand the actionability

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `brain_audit.py` (490 lines): Structural audit — staleness, peril coverage, threshold conflicts, orphans. Extend with `--calibrate` and `--lifecycle` flags
- `brain_effectiveness.py` (425 lines): Fire rate computation, always-fire/never-fire/high-skip classification, `update_effectiveness_table()`. Core data source for calibration
- `brain_writer.py` (496 lines): `retire_check()`, `promote_check()`, changelog logging. Extend for new lifecycle states
- `brain_signal_runs` table (20K+ rows): Per-signal results per pipeline run — the raw data for all learning
- `brain_effectiveness` table: Aggregated fire rates/discrimination — pre-computed metrics
- `brain_changelog` table (1.2K+ entries): Change history — extend for calibration provenance
- `feedback process` CLI: Reactions → proposals pipeline — extend for calibration and lifecycle proposals
- `cli_feedback_process.py`: Existing approval workflow pattern to follow

### Established Patterns
- YAML is source of truth, DuckDB for analytics/history (Phase 53 pattern)
- `BrainLoader` reads YAML at runtime (65ms), no DuckDB intermediary for definitions
- Signal YAML already has `lifecycle_state` field (ACTIVE, INACTIVE, RETIRED used today)
- Pydantic models for all report types (`BrainAuditReport`, `EffectivenessReport`)
- Rich console output for CLI display

### Integration Points
- `brain audit` CLI command (cli_brain_health.py) — add `--calibrate` and `--lifecycle` flags
- `brain_signal_runs` recording in post-ANALYZE pipeline step — already records all check results
- `feedback approve` command — extend to handle calibration and lifecycle proposal types
- Signal YAML files in `brain/signals/*.yaml` — write targets for approved changes
- `brain_changelog` table — write target for provenance logging

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 57-closed-learning-loop*
*Context gathered: 2026-03-02*
