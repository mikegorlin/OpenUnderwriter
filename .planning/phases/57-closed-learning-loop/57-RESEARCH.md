# Phase 57: Closed Learning Loop - Research

**Researched:** 2026-03-02
**Domain:** Statistical calibration, co-occurrence mining, signal lifecycle management
**Confidence:** HIGH

## Summary

Phase 57 implements the final v2.0 requirement: making the brain self-improving. Every pipeline run already records per-signal results to `brain_signal_runs` (20K+ rows across 400 signals). Phase 57 adds analytical capabilities on top of that data: statistical threshold drift detection, cross-signal correlation mining, fire rate anomaly alerting, and a formal lifecycle state machine.

The implementation is primarily a matter of extending existing well-established patterns rather than introducing new technology. The codebase has a clear audit/feedback/proposal/apply pipeline already in place (Phases 49-52.1). The core work is: (1) new statistical analysis functions that query `brain_signal_runs`, (2) new DuckDB tables/columns for correlation and proposal storage, (3) extending the `brain audit` CLI with `--calibrate` and `--lifecycle` flags, (4) extending `feedback approve` to handle new proposal types, and (5) implementing the 5-state lifecycle machine in YAML.

**Primary recommendation:** Extend existing `brain_audit.py` + `brain_effectiveness.py` + `feedback_process.py` + `yaml_writer.py` modules. No new libraries needed. Python's standard `statistics` module handles all statistical computations. DuckDB's analytical SQL handles all cross-signal queries.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `brain audit --calibrate` generates drift report in terminal AND writes proposal entries to DuckDB
- Proposals include specific suggested threshold values computed from observed distribution (percentile-based)
- Minimum 5+ runs per signal before proposals are generated -- confidence level marked based on N
- Covers both numeric thresholds (statistical distribution analysis) and qualitative signals (fire-rate-based recalibration)
- Each proposal includes: current value, observed mean/sigma, fire rate, proposed new value, basis, projected impact
- Co-occurrence mining runs as part of `brain audit` -- analyzes cross-signal fire patterns from brain_signal_runs
- Same-prefix correlations labeled "potential redundancy"; cross-prefix labeled "risk correlation"
- Redundancy flagging: explicitly flag when 3+ signals in same prefix co-fire >70% -- "consider consolidating"
- Co-fire threshold: configurable in brain config YAML, default 70%
- Confirmed correlations written to signal YAML (`correlated_signals` field); all discovered correlations stored in DuckDB
- Writing correlated_signals to YAML requires manual approval
- Extend existing CLI: `brain audit --calibrate` for drift, `brain audit --lifecycle` for state transitions
- Approval via `feedback approve <proposal-id>` -- applies change immediately to signal YAML
- Full provenance: who approved, statistical basis (N, mean, sigma), before/after values, expected impact, logged to brain_changelog
- Audit is on-demand only -- pipeline records to brain_signal_runs, underwriter invokes `brain audit` when they want analysis
- Fire rate alerts (>80% or <2%) surfaced in `brain audit` output alongside calibration proposals
- Signal lifecycle states: INCUBATING -> ACTIVE -> MONITORING -> DEPRECATED -> ARCHIVED
- Skip-transitions allowed (defined valid transitions, not strictly linear)
- Specific transition criteria defined (5+ runs for graduation, fire rate anomalies for monitoring, 90+ days for archival)
- All lifecycle transitions require manual approval via `feedback approve`
- AUTOMATIC: record signal runs, compute fire rates/effectiveness, detect threshold drift, mine co-occurrences, flag fire rate anomalies
- MANUAL: change any threshold, change lifecycle state, write correlated_signals to YAML, propose signal consolidation, retire/archive signals

### Claude's Discretion
- Statistical methods for drift detection (percentile-based, z-score, etc.)
- DuckDB table schema for correlation storage
- Exact CLI output formatting and Rich table layouts
- How to handle edge cases (signals with mixed numeric/qualitative thresholds, signals with 0 runs)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LEARN-01 | Statistical threshold calibration -- `brain audit` analyzes observed values from `brain_signal_runs` against current thresholds, flags signals where threshold is >2 sigma from observed distribution, proposes adjustments | Existing `brain_signal_runs` stores `value` column (str) per run. Numeric extraction via `_parse_numeric_value()` pattern already in `brain_audit.py`. Python `statistics` module provides mean/stdev. DuckDB aggregation queries provide per-signal distributions. Proposal storage uses existing `brain_proposals` table. |
| LEARN-02 | Co-occurrence mining -- `brain audit` identifies signals that fire together on >70% of analyzed companies, auto-populates `correlated_signals` field on signal YAML | DuckDB cross-join on `brain_signal_runs` grouped by `run_id` yields co-fire matrix. New `brain_correlations` table stores discovered pairs. `correlated_signals` field added to `BrainSignalEntry` Pydantic schema. YAML write-back uses existing `yaml_writer.py` `modify_signal_in_yaml()`. |
| LEARN-03 | Fire rate alerts -- signals firing on >80% or <2% flagged as potential calibration candidates | Existing `brain_effectiveness.py` already classifies `always_fire` (100%) and `never_fire` (0%). Extend thresholds to >80% and <2% as per requirements. Integrate into `--calibrate` output. |
| LEARN-04 | Signal lifecycle state machine -- formal states (INCUBATING -> ACTIVE -> MONITORING -> DEPRECATED -> ARCHIVED) with transitions proposed by `brain audit` and confirmed by underwriter | Existing `lifecycle.py` has 4-state machine (INCUBATING/DEVELOPING/ACTIVE/DEPRECATED) on SQLAlchemy. New implementation: 5-state machine in dedicated module, YAML `lifecycle_state` field (currently only `INACTIVE` and implicit `ACTIVE`), proposal-based transitions, `brain_changelog` provenance. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `statistics` | stdlib | mean, stdev, quantiles | No external deps needed for basic stats on small datasets (<400 signals x <100 runs) |
| DuckDB | 1.1+ (already installed) | Analytical queries on `brain_signal_runs` | Already the project's analytical engine; excellent for cross-signal aggregation |
| ruamel.yaml | 0.18+ (already installed) | Round-trip YAML editing | Already used in `yaml_writer.py` for comment-preserving signal modification |
| Rich | 13+ (already installed) | CLI table/panel output | Already used throughout CLI for all brain commands |
| Pydantic | 2.x (already installed) | Models for proposals, reports, correlations | Already used for all brain data models |
| Typer | 0.x (already installed) | CLI command registration | Already used for all brain/feedback CLI commands |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `itertools.combinations` | stdlib | Generate signal pairs for co-occurrence analysis | Used in correlation mining to avoid self-pairs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python `statistics` | numpy/scipy | Overkill -- 400 signals, <100 data points each; stdlib sufficient and zero deps |
| DuckDB cross-join | Python nested loops | DuckDB is 10-100x faster for cross-signal aggregation with 20K+ rows |
| New correlation table | Flat JSON in brain_proposals | Correlations need indexed querying for redundancy checks; table is cleaner |

**Installation:**
No new packages needed. All dependencies already in project.

## Architecture Patterns

### Recommended Module Structure
```
src/do_uw/brain/
  brain_calibration.py     # NEW: threshold drift analysis, proposal generation (<400 lines)
  brain_correlation.py     # NEW: co-occurrence mining, redundancy detection (<300 lines)
  brain_lifecycle_v2.py    # NEW: 5-state machine, transition logic (<250 lines)
  brain_audit.py           # EXTEND: add --calibrate and --lifecycle dispatch
  brain_effectiveness.py   # REUSE: fire rate data source (no changes)
  brain_schema.py          # EXTEND: new DDL for correlation table, columns

src/do_uw/
  cli_brain_health.py      # EXTEND: add --calibrate and --lifecycle to brain_audit command
  cli_feedback_process.py  # EXTEND: handle CALIBRATION and LIFECYCLE proposal types in approve
```

### Pattern 1: Statistical Threshold Calibration
**What:** Query `brain_signal_runs` for numeric values per signal, compute distribution stats, compare against YAML thresholds.
**When to use:** For signals with `threshold.type` in `{tiered, numeric_threshold, tiered_threshold}` that have numeric values recorded.
**Key details:**
- The `value` column in `brain_signal_runs` is VARCHAR -- must parse to float for numeric signals
- Not all signals have numeric values (boolean, text, display-only)
- Two calibration strategies based on signal type:
  1. **Numeric signals**: Compare threshold value against observed percentiles (e.g., if red threshold is ">5" but 95th percentile of observed values is 12.3, threshold may be too loose)
  2. **Qualitative/boolean signals**: Use fire rate as proxy (if 95% fire, threshold is too sensitive)
- Minimum N=5 runs before generating proposals (per locked decision)

```python
# Pseudocode for threshold drift computation
from statistics import mean, stdev, quantiles

def compute_threshold_drift(signal_id: str, values: list[float], current_threshold: float) -> DriftReport:
    if len(values) < 5:
        return DriftReport(signal_id=signal_id, status="INSUFFICIENT_DATA", n=len(values))

    obs_mean = mean(values)
    obs_stdev = stdev(values) if len(values) > 1 else 0.0
    obs_percentiles = quantiles(values, n=100) if len(values) >= 2 else []

    # Flag if threshold is >2 sigma from observed mean
    if obs_stdev > 0 and abs(current_threshold - obs_mean) > 2 * obs_stdev:
        proposed_value = obs_percentiles[89]  # 90th percentile as new threshold
        return DriftReport(
            signal_id=signal_id,
            status="DRIFT_DETECTED",
            n=len(values),
            current_threshold=current_threshold,
            observed_mean=obs_mean,
            observed_stdev=obs_stdev,
            fire_rate=...,
            proposed_value=proposed_value,
            basis="p90 of observed distribution",
        )
```

### Pattern 2: Co-occurrence Mining via DuckDB
**What:** Cross-join `brain_signal_runs` on `run_id` to find signal pairs that fire together above a configurable threshold.
**When to use:** During `brain audit --calibrate` to discover redundant or correlated signals.
**Key details:**
- DuckDB is ideal for this -- it's an analytical SQL engine with native cross-join performance
- Query returns all pairs with co-fire rate > threshold (default 70%)
- Same-prefix vs cross-prefix classification uses signal ID prefix parsing (e.g., `FIN.LIQ.current` -> prefix `FIN.LIQ`)

```sql
-- Co-occurrence mining query
WITH fired AS (
    SELECT DISTINCT run_id, signal_id
    FROM brain_signal_runs
    WHERE status = 'TRIGGERED' AND is_backtest = FALSE
),
pairs AS (
    SELECT a.signal_id AS sig_a, b.signal_id AS sig_b,
           COUNT(DISTINCT a.run_id) AS co_fire_count,
           (SELECT COUNT(DISTINCT run_id) FROM fired WHERE signal_id = a.signal_id) AS a_total,
           (SELECT COUNT(DISTINCT run_id) FROM fired WHERE signal_id = b.signal_id) AS b_total
    FROM fired a
    JOIN fired b ON a.run_id = b.run_id AND a.signal_id < b.signal_id
    GROUP BY a.signal_id, b.signal_id
)
SELECT sig_a, sig_b, co_fire_count,
       ROUND(co_fire_count * 1.0 / LEAST(a_total, b_total), 3) AS co_fire_rate
FROM pairs
WHERE co_fire_count * 1.0 / LEAST(a_total, b_total) >= 0.70
ORDER BY co_fire_rate DESC;
```

### Pattern 3: Proposal-Based Lifecycle Transitions
**What:** `brain audit --lifecycle` analyzes signals and proposes state transitions based on multi-factor evidence. Proposals stored in `brain_proposals`, applied via `feedback approve`.
**When to use:** For all lifecycle state management.
**Key details:**
- Extends existing proposal workflow (already has `brain_proposals` table, `feedback approve` command)
- New proposal_type values: `LIFECYCLE_TRANSITION`, `THRESHOLD_CALIBRATION`, `CORRELATION_ANNOTATION`
- Each proposal stores statistical evidence in `backtest_results` JSON column

### Pattern 4: Extending brain_proposals for New Types
**What:** The existing `brain_proposals` table and `feedback approve` workflow accommodate new proposal types with zero schema changes.
**When to use:** All learning loop proposals flow through this pattern.
**Key details:**
- `brain_proposals.proposal_type` is VARCHAR -- just add new string values
- `brain_proposals.proposed_changes` is JSON -- flexible enough for any change type
- `brain_proposals.backtest_results` is JSON -- stores statistical evidence
- `brain_proposals.source_type` gains new value: `CALIBRATION` (alongside existing `FEEDBACK`, `INGESTION`, `PATTERN`)

### Anti-Patterns to Avoid
- **Auto-applying changes:** All YAML modifications MUST go through the proposal -> approve workflow. The system proposes, human disposes.
- **Computing stats at pipeline time:** Pipeline ONLY records data. Statistical analysis happens in `brain audit` (on-demand).
- **Replacing the existing feedback workflow:** Extend, don't reinvent. The `feedback process` -> `feedback approve` -> `brain apply-proposal` chain is battle-tested.
- **Monolithic audit function:** Split calibration, correlation, and lifecycle into separate modules (brain_calibration.py, brain_correlation.py, brain_lifecycle_v2.py) -- each <400 lines per CLAUDE.md rules.
- **Using SQLAlchemy lifecycle module:** The existing `knowledge/lifecycle.py` uses SQLAlchemy/SQLite (legacy knowledge.db). Phase 57 should implement the new 5-state machine as a standalone module using DuckDB/YAML, not extend the SQLAlchemy version.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Statistical mean/stdev/percentiles | Custom math functions | `statistics.mean`, `statistics.stdev`, `statistics.quantiles` | Handles edge cases (variance correction for small N) |
| Cross-signal co-occurrence matrix | Python nested loops over run data | DuckDB SQL cross-join query | 20K+ rows x 400 signals = 8M potential comparisons; SQL is orders of magnitude faster |
| YAML round-trip editing | PyYAML dump/load (lossy) | `yaml_writer.py` with ruamel.yaml | Comment preservation is critical (per Phase 51-03 precedent) |
| Proposal storage and approval | New custom storage | Existing `brain_proposals` table + `feedback approve` CLI | Proven pattern with git commit, changelog, revert support |
| Fire rate computation | Custom aggregation | Existing `brain_effectiveness.py` `compute_effectiveness()` | Already computes fire/skip/clear rates per signal with confidence levels |

**Key insight:** This phase is 80% analytical queries + 20% new Pydantic models and CLI plumbing. The data infrastructure (brain_signal_runs), mutation infrastructure (yaml_writer, brain_proposals), and UI infrastructure (Rich CLI) all exist. The new work is computing insights from existing data and routing those insights through existing workflows.

## Common Pitfalls

### Pitfall 1: Insufficient Run Data
**What goes wrong:** With only 3-4 pipeline runs across 2-3 tickers, statistical analysis is meaningless. Mean/stdev of 3 values is noise.
**Why it happens:** The system has 20K+ brain_signal_runs rows, but most signals have been evaluated against only a few distinct tickers/runs.
**How to avoid:** Enforce N>=5 minimum for all proposals (locked decision). Display confidence levels prominently (LOW/MEDIUM/HIGH based on N). Never propose changes at LOW confidence.
**Warning signs:** Most signals showing "INSUFFICIENT_DATA" in calibration output.

### Pitfall 2: VARCHAR Value Parsing Failures
**What goes wrong:** `brain_signal_runs.value` is VARCHAR. Many signals store non-numeric values ("True", "N/A", "3 lawsuits in 2 years", "Profitable"). Naive `float()` conversion crashes.
**Why it happens:** The pipeline stores `str(r.value)` for all signal types, regardless of whether the value is numeric.
**How to avoid:** Use defensive parsing: try `float()`, catch ValueError/TypeError, skip non-numeric. Group signals by `threshold.type` -- only attempt numeric calibration for `tiered`/`numeric_threshold` types. For qualitative signals, use fire rate analysis instead.
**Warning signs:** High skip rate in calibration output.

### Pitfall 3: Lifecycle State Mismatch Between Systems
**What goes wrong:** The YAML signals use `lifecycle_state: INACTIVE` (20 signals) but the new system needs 5 states (INCUBATING/ACTIVE/MONITORING/DEPRECATED/ARCHIVED). The old `lifecycle.py` uses SQLAlchemy with different states (INCUBATING/DEVELOPING/ACTIVE/DEPRECATED). The DuckDB `brain_signals_active` view filters on `NOT IN ('RETIRED', 'INCUBATING', 'INACTIVE')`.
**Why it happens:** Three lifecycle systems evolved independently.
**How to avoid:** Map existing states explicitly: INACTIVE -> DEPRECATED (or MONITORING depending on context). Update `brain_signals_active` view to include MONITORING (signals in MONITORING should still fire in the pipeline -- they're just under observation). Implement the new 5-state machine as a clean module that reads/writes YAML `lifecycle_state` field and logs to `brain_changelog`. Do NOT extend `lifecycle.py` (that's SQLAlchemy legacy).
**Warning signs:** Signals disappearing from pipeline results after lifecycle changes.

### Pitfall 4: Co-occurrence Explosion
**What goes wrong:** With 400 signals, there are 79,800 possible pairs. Many will have spurious correlations, especially signals that fire on almost every company.
**Why it happens:** Signals like "has SEC filings" or "has financial data" fire on 100% of companies, creating 399 false correlations each.
**How to avoid:** Pre-filter: exclude signals with fire rate >80% or <2% from co-occurrence mining (they're calibration candidates, not correlation candidates). Minimum co-fire count (not just rate) to avoid small-sample artifacts. Label same-prefix pairs differently from cross-prefix pairs (per locked decision).
**Warning signs:** Hundreds of "correlated" pairs, most involving the same handful of always-fire signals.

### Pitfall 5: Threshold Direction Ambiguity
**What goes wrong:** For "lower is worse" signals (e.g., current ratio), the threshold is `<1.0`. The "observed mean" might be 2.5. The question "is the threshold >2 sigma from the mean?" requires knowing the direction: the threshold should be BELOW the mean for "lower is worse" signals.
**Why it happens:** Thresholds are stored as English text strings (">5.0", "<1.0 current ratio"), not structured {operator, value} pairs (except for V2 schema signals).
**How to avoid:** For V2 signals: use `evaluation.thresholds[].op` directly. For V1 signals: parse operator from threshold string using `_parse_numeric_value()` pattern already in `brain_audit.py`. For ambiguous cases: fall back to fire rate analysis (always applicable). Flag signals where direction cannot be determined.
**Warning signs:** Proposals suggesting to RAISE a threshold that should be LOWERED, or vice versa.

## Code Examples

Verified patterns from existing codebase:

### DuckDB Query for Per-Signal Value Distribution
```python
# Source: brain_effectiveness.py pattern
def get_signal_value_distribution(conn, signal_id):
    """Get numeric values for a signal from brain_signal_runs."""
    rows = conn.execute(
        """SELECT value FROM brain_signal_runs
           WHERE signal_id = ? AND is_backtest = FALSE
             AND value IS NOT NULL""",
        [signal_id],
    ).fetchall()

    values = []
    for (raw_value,) in rows:
        try:
            values.append(float(raw_value))
        except (ValueError, TypeError):
            continue  # Skip non-numeric values
    return values
```

### Existing Proposal Insertion Pattern
```python
# Source: feedback_process.py lines 358-395
conn.execute(
    """INSERT INTO brain_proposals
       (source_type, source_ref, signal_id, proposal_type,
        proposed_changes, backtest_results, rationale, status)
       VALUES ('CALIBRATION', ?, ?, ?, ?, ?, ?, ?)""",
    [source_ref, signal_id, proposal_type,
     json.dumps(proposed_changes), json.dumps(backtest_results),
     rationale, status],
)
```

### Existing YAML Modification Pattern
```python
# Source: calibrate_apply.py -> yaml_writer.py
from do_uw.knowledge.yaml_writer import (
    build_signal_yaml_index,
    modify_signal_in_yaml,
)

yaml_index = build_signal_yaml_index()
yaml_path = yaml_index[signal_id]
diff_str = modify_signal_in_yaml(yaml_path, signal_id, changes)
```

### Existing Changelog Logging Pattern
```python
# Source: brain_writer_export.py
from do_uw.brain.brain_writer_export import log_change

log_change(
    conn, signal_id, old_version=None, new_version=1,
    change_type="CALIBRATION", description=f"Threshold adjusted: {old} -> {new}",
    changed_by="brain_audit", fields_changed=["threshold.red"],
)
```

### Adding CLI Flags to Existing Command
```python
# Source: cli_brain_health.py pattern
@brain_app.command("audit")
def brain_audit(
    calibrate: bool = typer.Option(False, "--calibrate", help="Run statistical calibration"),
    lifecycle: bool = typer.Option(False, "--lifecycle", help="Analyze lifecycle transitions"),
) -> None:
    # ... existing audit code ...
    if calibrate:
        from do_uw.brain.brain_calibration import compute_calibration_report
        cal_report = compute_calibration_report(conn)
        _display_calibration_report(cal_report)
    if lifecycle:
        from do_uw.brain.brain_lifecycle_v2 import compute_lifecycle_proposals
        lc_report = compute_lifecycle_proposals(conn)
        _display_lifecycle_report(lc_report)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 4-state lifecycle (INCUBATING/DEVELOPING/ACTIVE/DEPRECATED) in SQLAlchemy | 5-state lifecycle in YAML/DuckDB (Phase 57) | Phase 57 | Adds MONITORING and ARCHIVED states; SQLAlchemy module becomes fully legacy |
| Lifecycle managed via `lifecycle.py` (SQLAlchemy) | Lifecycle managed via YAML `lifecycle_state` field + `brain_changelog` (DuckDB) | Phase 53+ | YAML is source of truth since Phase 53; DuckDB for history only |
| Manual threshold tuning via `feedback capture` -> `feedback process` -> `brain apply-proposal` | Statistical threshold proposals via `brain audit --calibrate` -> `feedback approve` | Phase 57 | Automated detection of drift, but human still approves |
| Fire rate classification: always-fire (100%), never-fire (0%) | Extended: >80% and <2% thresholds (per requirements) | Phase 57 | Catches near-extreme signals, not just perfect extremes |

**Deprecated/outdated:**
- `knowledge/lifecycle.py` (SQLAlchemy-based): Still exists but operates on legacy knowledge.db. Phase 57's lifecycle should be built as a new module targeting YAML/DuckDB, not extending this.
- `brain_signals_active` view filter `NOT IN ('RETIRED', 'INCUBATING', 'INACTIVE')`: Must be updated to handle new states (MONITORING should remain visible; ARCHIVED should not).

## Open Questions

1. **MONITORING state pipeline behavior**
   - What we know: MONITORING signals are under observation but should still fire in the pipeline (they're being watched, not disabled).
   - What's unclear: Should the `brain_signals_active` DuckDB view include MONITORING? (Currently it excludes RETIRED, INCUBATING, INACTIVE.)
   - Recommendation: YES -- MONITORING means "still active but under observation." The view filter becomes `NOT IN ('RETIRED', 'INCUBATING', 'INACTIVE', 'DEPRECATED', 'ARCHIVED')`. MONITORING signals stay visible.

2. **INACTIVE -> which new state?**
   - What we know: 20 signals currently have `lifecycle_state: INACTIVE`. The new system uses DEPRECATED for "clearly broken" and ARCHIVED for "final cleanup."
   - What's unclear: Are the 20 INACTIVE signals broken (-> DEPRECATED) or just unneeded (-> ARCHIVED)?
   - Recommendation: Map INACTIVE -> DEPRECATED (preserves current behavior since DEPRECATED is also excluded from active view, and allows re-activation). Add a migration step that updates existing `lifecycle_state: INACTIVE` signals.

3. **Threshold value extraction reliability**
   - What we know: `brain_signal_runs.value` is VARCHAR containing `str(r.value)`. For numeric signals this might be "1.23" or "None" or a dict representation.
   - What's unclear: What percentage of signals have reliably parseable numeric values?
   - Recommendation: Add a diagnostic to `brain audit --calibrate` that reports: "X signals with numeric thresholds, Y with parseable values, Z with N>=5 observations." This surfaces the actual data quality before proposing changes.

4. **Co-fire rate denominator**
   - What we know: Co-fire rate = (runs where both fire) / (runs where at least one fires? OR runs where both are evaluated?).
   - What's unclear: Which denominator best captures "these signals correlate."
   - Recommendation: Use `min(signal_a_fire_count, signal_b_fire_count)` as denominator (Jaccard-inspired). This means "of the times the less-frequently-firing signal fires, how often does the other one also fire?" This avoids dilution from signals with very different base rates.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/brain/test_brain_calibration.py tests/brain/test_brain_correlation.py tests/brain/test_brain_lifecycle_v2.py -x` |
| Full suite command | `pytest tests/ -x --timeout=120` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LEARN-01 | Threshold drift detection: identifies signals >2 sigma from observed distribution | unit | `pytest tests/brain/test_brain_calibration.py::test_drift_detection -x` | Wave 0 |
| LEARN-01 | Calibration proposal generation with statistical basis | unit | `pytest tests/brain/test_brain_calibration.py::test_proposal_generation -x` | Wave 0 |
| LEARN-01 | Minimum N=5 enforcement | unit | `pytest tests/brain/test_brain_calibration.py::test_min_runs_threshold -x` | Wave 0 |
| LEARN-01 | Numeric value parsing from VARCHAR column | unit | `pytest tests/brain/test_brain_calibration.py::test_value_parsing -x` | Wave 0 |
| LEARN-02 | Co-occurrence mining identifies >70% co-fire pairs | unit | `pytest tests/brain/test_brain_correlation.py::test_cooccurrence_mining -x` | Wave 0 |
| LEARN-02 | Same-prefix vs cross-prefix labeling | unit | `pytest tests/brain/test_brain_correlation.py::test_correlation_labeling -x` | Wave 0 |
| LEARN-02 | Redundancy flagging for 3+ same-prefix signals | unit | `pytest tests/brain/test_brain_correlation.py::test_redundancy_flagging -x` | Wave 0 |
| LEARN-02 | correlated_signals field written to YAML via approval | integration | `pytest tests/brain/test_brain_correlation.py::test_yaml_writeback -x` | Wave 0 |
| LEARN-03 | Fire rate >80% flagged | unit | `pytest tests/brain/test_brain_calibration.py::test_high_fire_rate_alert -x` | Wave 0 |
| LEARN-03 | Fire rate <2% flagged | unit | `pytest tests/brain/test_brain_calibration.py::test_low_fire_rate_alert -x` | Wave 0 |
| LEARN-04 | 5-state lifecycle with valid transitions | unit | `pytest tests/brain/test_brain_lifecycle_v2.py::test_valid_transitions -x` | Wave 0 |
| LEARN-04 | Invalid transitions rejected | unit | `pytest tests/brain/test_brain_lifecycle_v2.py::test_invalid_transitions -x` | Wave 0 |
| LEARN-04 | Lifecycle proposals based on fire rate + age + feedback | unit | `pytest tests/brain/test_brain_lifecycle_v2.py::test_proposal_generation -x` | Wave 0 |
| LEARN-04 | ARCHIVED is terminal (no transitions out) | unit | `pytest tests/brain/test_brain_lifecycle_v2.py::test_archived_terminal -x` | Wave 0 |
| LEARN-04 | Approval writes lifecycle_state to YAML | integration | `pytest tests/brain/test_brain_lifecycle_v2.py::test_approval_yaml_write -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/brain/test_brain_calibration.py tests/brain/test_brain_correlation.py tests/brain/test_brain_lifecycle_v2.py -x`
- **Per wave merge:** `pytest tests/ -x --timeout=120`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
- [ ] `tests/brain/test_brain_calibration.py` -- covers LEARN-01, LEARN-03
- [ ] `tests/brain/test_brain_correlation.py` -- covers LEARN-02
- [ ] `tests/brain/test_brain_lifecycle_v2.py` -- covers LEARN-04
- [ ] Shared DuckDB fixture (pattern exists in `tests/knowledge/test_calibrate.py` -- reuse)

## Detailed Existing Code Analysis

### What Already Exists and Can Be Reused

**Data Source -- brain_signal_runs (DuckDB)**
- 20K+ rows, columns: `run_id`, `signal_id`, `signal_version`, `status` (TRIGGERED/CLEAR/SKIPPED/INFO), `value` (VARCHAR), `evidence`, `ticker`, `run_date`, `is_backtest`
- Pipeline records to this table after ANALYZE stage (`stages/analyze/__init__.py` line 326-355)
- Value column: `str(r.value)` -- contains numeric strings for numeric signals, text for qualitative
- Key indexes: `idx_runs_signal(signal_id, status)`, `idx_runs_ticker(ticker, run_date)`

**Effectiveness Engine -- brain_effectiveness.py (425 lines)**
- `compute_effectiveness(conn)` returns `EffectivenessReport` with `always_fire`, `never_fire`, `high_skip`, `consistent` lists
- Already classifies: fire_rate==1.0 (always), fire_rate==0.0 (never), skip_rate>0.5 (high_skip)
- `update_effectiveness_table(conn)` writes aggregated metrics to `brain_effectiveness` table
- `record_signal_runs_batch(conn, rows)` for batch recording (used by pipeline)

**Structural Audit -- brain_audit.py (490 lines)**
- `compute_brain_audit()` returns `BrainAuditReport` with findings list
- Checks: staleness, peril coverage, threshold conflicts, orphaned signals
- CLI: `brain_app.command("audit")` in `cli_brain_health.py` line 441
- Currently takes no flags -- needs `--calibrate` and `--lifecycle` additions

**Proposal Storage -- brain_proposals (DuckDB table)**
- Columns: `proposal_id` (auto-seq), `source_type`, `source_ref`, `signal_id`, `proposal_type`, `proposed_check` (JSON), `proposed_changes` (JSON), `backtest_results` (JSON), `rationale`, `status`, `reviewed_by`, `reviewed_at`
- Existing types: `NEW_CHECK`, `THRESHOLD_CHANGE`, `DEACTIVATION`
- Status values: `PENDING`, `APPLIED`, `CONFLICTED`, `REJECTED`

**Approval Pipeline**
- `feedback approve <proposal-id>` -> `cli_brain_apply.py` -> `calibrate_apply.py::apply_single_proposal()`
- Flow: load proposal -> locate YAML -> compute changes -> ruamel.yaml modify -> brain build -> validate -> git commit -> mark APPLIED
- Change provenance logged to `brain_changelog`

**YAML Writer -- yaml_writer.py (203 lines)**
- `build_signal_yaml_index()`: signal_id -> YAML path mapping
- `modify_signal_in_yaml(path, signal_id, changes)`: ruamel.yaml round-trip edit
- `revert_yaml_change(path)`: git checkout fallback

**Changelog -- brain_changelog (DuckDB table)**
- Columns: `changelog_id`, `signal_id`, `old_version`, `new_version`, `change_type`, `change_description`, `fields_changed`, `changed_by`, `changed_at`, `change_reason`, `triggered_by`
- 1.2K+ entries already

### What Needs to Be Built

1. **brain_calibration.py** (~350 lines)
   - `compute_calibration_report(conn)` -> `CalibrationReport`
   - Per-signal: extract numeric values from `brain_signal_runs.value`, compute stats, compare to YAML thresholds
   - Drift detection: flag when threshold >2 sigma from observed distribution
   - Fire rate alerts: >80% or <2% (extends effectiveness classification)
   - Proposal generation: write `THRESHOLD_CALIBRATION` proposals to `brain_proposals`

2. **brain_correlation.py** (~250 lines)
   - `compute_correlation_report(conn)` -> `CorrelationReport`
   - DuckDB cross-join query for co-fire pairs above threshold
   - Same-prefix vs cross-prefix classification
   - Redundancy flagging (3+ same-prefix signals co-firing >70%)
   - Write discovered correlations to `brain_correlations` DuckDB table
   - Generate `CORRELATION_ANNOTATION` proposals for YAML write-back

3. **brain_lifecycle_v2.py** (~200 lines)
   - `LifecycleState` StrEnum: INCUBATING, ACTIVE, MONITORING, DEPRECATED, ARCHIVED
   - `VALID_TRANSITIONS` dict with all allowed transitions
   - `compute_lifecycle_proposals(conn)` -> `LifecycleReport`
   - Transition criteria: fire rate anomalies + signal age + feedback reactions
   - Write `LIFECYCLE_TRANSITION` proposals to `brain_proposals`

4. **Schema changes**
   - New table: `brain_correlations` (signal_a, signal_b, co_fire_rate, co_fire_count, correlation_type, discovered_at)
   - New column on `BrainSignalEntry`: `correlated_signals: list[str]`
   - New column on signal YAML: `lifecycle_state` (already exists but needs new valid values)
   - Update `brain_signals_active` view to handle MONITORING state

5. **CLI extensions**
   - `brain audit --calibrate`: display calibration report + generate proposals
   - `brain audit --lifecycle`: display lifecycle proposals
   - Extend `feedback approve` to handle new proposal types

6. **ProposalRecord extension**
   - Add `LIFECYCLE_TRANSITION`, `THRESHOLD_CALIBRATION`, `CORRELATION_ANNOTATION` to proposal_type
   - Extend `_compute_yaml_changes()` in `calibrate_apply.py` for new types

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `brain_audit.py` (490 lines), `brain_effectiveness.py` (425 lines), `brain_writer.py` (496 lines), `brain_schema.py` (422 lines)
- Codebase analysis: `cli_brain_health.py` (audit CLI), `cli_feedback_process.py` (feedback process CLI), `cli_brain_apply.py` (apply proposal CLI)
- Codebase analysis: `feedback_process.py` (aggregation + proposal generation), `calibrate_apply.py` (YAML write-back), `yaml_writer.py` (ruamel.yaml round-trip)
- Codebase analysis: `brain_signal_schema.py` (BrainSignalEntry Pydantic model), `brain_signal_runs` table schema, `brain_proposals` table schema
- Python stdlib `statistics` module documentation (mean, stdev, quantiles)

### Secondary (MEDIUM confidence)
- DuckDB analytical SQL capabilities for cross-join queries (verified against existing project DuckDB usage patterns)
- Signal YAML structure verified: 400 signals across 36 files, 20 with explicit `lifecycle_state: INACTIVE`, rest implicit ACTIVE

### Tertiary (LOW confidence)
- None -- all findings verified against existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies, all from existing project stack
- Architecture: HIGH -- extending proven patterns (audit, proposals, YAML write-back)
- Pitfalls: HIGH -- identified from actual codebase analysis (VARCHAR values, lifecycle state fragmentation, co-occurrence explosion)

**Research date:** 2026-03-02
**Valid until:** 2026-04-02 (stable -- no external dependencies changing)
