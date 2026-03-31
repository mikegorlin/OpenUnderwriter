# Phase 50: Automated QA & Anomaly Detection - Research

**Researched:** 2026-02-26
**Domain:** Pipeline self-validation, brain health metrics, cross-run delta detection, system auditing
**Confidence:** HIGH

## Summary

Phase 50 adds four new capabilities to the brain system: (1) an automated health summary at the end of every `do-uw analyze` run, (2) a unified `brain health` command, (3) a `brain delta <TICKER>` cross-run comparison, and (4) a `brain audit` structural health report. All four build on existing infrastructure -- the `brain_signal_runs` table already records every signal outcome per run, the `brain_effectiveness` table already tracks fire/skip rates, the `brain_feedback` table exists (currently empty), and the QA report system (`validation/qa_report.py`) already runs after every pipeline completion. The existing facet system provides coverage metadata, and the signal YAML provides threshold definitions.

The primary technical challenge is NOT data collection (the pipeline already records everything needed) but rather **aggregation and presentation**. Every data source this phase needs already exists in either brain.duckdb or the output state.json. The work is: (a) computing the right aggregations from existing data, (b) detecting anomalies via simple heuristic rules (not ML), and (c) presenting results through Rich CLI tables.

**Primary recommendation:** Build four self-contained modules -- one per requirement -- each reading from brain.duckdb and/or state.json. Wire them into the existing CLI (brain_app commands) and the post-pipeline QA hook. No new tables needed; no new dependencies.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QA-01 | Every `do-uw analyze` run ends with automated health summary -- evaluated/TRIGGERED/SKIPPED counts, anomaly warnings | Extend existing `validation/qa_report.py` + `qa_report_generator.py` with signal-level health summary. Data comes from `state.analysis.signal_results` (already computed). Anomaly detection is heuristic rules over the result counts. |
| QA-02 | User can view unified system health with `do-uw brain health` -- coverage %, fire rate distribution, top never-fire/always-fire signals, data freshness, feedback queue | New CLI command in `cli_brain.py` (or new file `cli_brain_health.py`). Reads from `brain_signals_active` (coverage), `brain_signal_runs` (fire rates), `brain_effectiveness` (always/never-fire), `brain_feedback` (queue), `brain_meta` (freshness). Most queries exist in `brain_effectiveness.py::compute_effectiveness()` already. |
| QA-04 | User can detect cross-run changes with `do-uw brain delta <TICKER>` -- shows signals that flipped CLEAR<->TRIGGERED since last run | New CLI command. Queries `brain_signal_runs` for the two most recent non-backtest runs for a ticker, then diffs signal statuses. SQL is straightforward: join two run snapshots on signal_id, filter where status changed. |
| QA-05 | User can audit brain health with `do-uw brain audit` -- staleness, coverage imbalance across perils, threshold conflicts, orphaned signals | New CLI command. Reads from `brain_signals_active` (staleness via `last_calibrated`, orphaned = no facet assignment), `brain_coverage_matrix` view (peril imbalance), threshold_full JSON (conflict detection). All data exists in brain.duckdb. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| DuckDB | >=1.4.4 | Brain database queries | Already used; all brain data lives here |
| Rich | >=13.0 | CLI output formatting | Already used in all brain CLI commands |
| Typer | >=0.15 | CLI command registration | Already used; `brain_app` is the parent |
| Pydantic | >=2.10 | Report data models | Already used for all models in the system |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyYAML | >=6.0 | Signal YAML reading | For audit checks that need YAML-level inspection |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Heuristic anomaly rules | ML-based anomaly detection | Explicitly out of scope per REQUIREMENTS.md -- need 50+ companies for ML. Heuristics are correct for N=4 tickers |
| New DuckDB tables for health snapshots | JSON files for health history | DuckDB is the existing pattern; no reason to diverge |

**Installation:**
```bash
# No new dependencies -- all libraries already in pyproject.toml
```

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  validation/
    qa_report.py           # EXISTING: extend with signal health summary (QA-01)
    qa_report_generator.py # EXISTING: extend with signal health rendering (QA-01)
    health_summary.py      # NEW: post-run health summary computation (QA-01)
  brain/
    brain_health.py        # NEW: unified health metrics computation (QA-02)
    brain_delta.py         # NEW: cross-run delta computation (QA-04)
    brain_audit.py         # NEW: structural audit computation (QA-05)
  cli_brain_health.py     # NEW: CLI commands for health, delta, audit (QA-02/04/05)
```

### Pattern 1: Post-Pipeline Health Summary (QA-01)
**What:** After every `do-uw analyze` completes, the existing QA verification hook is extended to include a signal health summary showing evaluated/TRIGGERED/SKIPPED counts and anomaly warnings.
**When to use:** Automatically at the end of every pipeline run.
**Architecture:**
- The hook point already exists in `cli.py` lines 347-353: `run_qa_verification(state, output_dir)` / `print_qa_report(qa_report)`
- New module `validation/health_summary.py` computes:
  - Total signals evaluated, TRIGGERED, CLEAR, SKIPPED, INFO counts (from `state.analysis.signal_results`)
  - Anomaly rules: (a) 0 TRIGGERED when litigation data exists, (b) SKIPPED count above threshold (currently 45), (c) TRIGGERED count above historical average for this ticker
- Returns a `HealthSummary` Pydantic model consumed by `qa_report_generator.py`
- The anomaly warnings are heuristic rules, NOT ML:
  - "0 TRIGGERED but litigation data present" = warning
  - "SKIPPED > MAX_SKIPPED_THRESHOLD (45)" = warning
  - "TRIGGERED count changed by >50% from last run" = info

**Example:**
```python
# validation/health_summary.py
class AnomalyWarning(BaseModel):
    level: str  # "WARNING", "INFO"
    message: str
    detail: str

class HealthSummary(BaseModel):
    total_signals: int
    evaluated: int
    triggered: int
    clear: int
    skipped: int
    info: int
    anomalies: list[AnomalyWarning]
```

### Pattern 2: Unified Brain Health (QA-02)
**What:** A single `do-uw brain health` command that shows the global brain system health.
**When to use:** User wants to understand overall system calibration and coverage.
**Architecture:**
- Reads from existing DuckDB tables/views:
  - `brain_signals_active` -> total signal count, coverage % (signals in facets vs total)
  - `brain_signal_runs` + `brain_effectiveness` -> fire rate distribution, top never-fire, top always-fire
  - `brain_feedback` WHERE status='PENDING' -> feedback queue size
  - `brain_meta` -> data freshness (last build timestamp)
- `brain_effectiveness.py::compute_effectiveness()` already computes fire rates, always-fire, never-fire, high-skip
- The health command adds: coverage %, fire rate histogram, feedback queue status
- Fire rate distribution: bucket into 0-10%, 10-30%, 30-50%, 50-80%, 80-100% bands

**Example:**
```python
# brain/brain_health.py
class BrainHealthReport(BaseModel):
    total_active_signals: int
    coverage_pct: float  # signals in facets / total active
    fire_rate_distribution: dict[str, int]  # band -> count
    top_never_fire: list[dict]  # from effectiveness
    top_always_fire: list[dict]  # from effectiveness
    data_freshness: str  # from brain_meta
    feedback_queue_size: int
    run_count: int
```

### Pattern 3: Cross-Run Delta (QA-04)
**What:** `do-uw brain delta <TICKER>` shows which signals flipped between the two most recent runs.
**When to use:** After re-running analysis on a ticker to understand what changed.
**Architecture:**
- Query `brain_signal_runs` for the two most recent `run_id` values for the given ticker (WHERE is_backtest=FALSE)
- JOIN the two result sets on `signal_id`
- Report: signals where status changed (CLEAR->TRIGGERED, TRIGGERED->CLEAR, SKIPPED->CLEAR, etc.)
- Also support: `--run1 <RUN_ID> --run2 <RUN_ID>` for explicit comparison
- The `brain_signal_runs` table already has: run_id, signal_id, status, value, evidence, ticker, run_date
- This is a pure SQL operation with no new data collection needed

**Example SQL:**
```sql
WITH latest AS (
    SELECT run_id, run_date,
           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY run_date DESC) as rn
    FROM (SELECT DISTINCT run_id, ticker, MIN(run_date) as run_date
          FROM brain_signal_runs WHERE ticker = ? AND is_backtest = FALSE
          GROUP BY run_id, ticker)
)
SELECT r1.signal_id, r1.status AS old_status, r2.status AS new_status
FROM brain_signal_runs r1
JOIN brain_signal_runs r2 ON r1.signal_id = r2.signal_id
WHERE r1.run_id = (SELECT run_id FROM latest WHERE rn = 2)
  AND r2.run_id = (SELECT run_id FROM latest WHERE rn = 1)
  AND r1.status != r2.status
ORDER BY r1.signal_id
```

### Pattern 4: Brain Audit (QA-05)
**What:** `do-uw brain audit` inspects the structural health of the brain signal system.
**When to use:** Periodic maintenance to detect rot, imbalance, and misconfigurations.
**Architecture:**
- **Staleness:** Read `last_calibrated` from `brain_signals_active`; flag signals not calibrated in >180 days
- **Coverage imbalance:** Use `brain_coverage_matrix` view; flag perils with GAP or THIN coverage. NOTE: peril_id column is currently NULL for all active signals (0 with peril_ids). This means coverage-by-peril is currently impossible -- the audit should report this as a known gap rather than computing phantom coverage numbers
- **Threshold conflicts:** Read `threshold_full` JSON from `brain_signals_active`; detect overlapping red/yellow/clear ranges (e.g., red says ">10" but yellow says ">15")
- **Orphaned signals:** Compare `brain_signals_active` IDs against union of all facet signal lists; report signals not in any facet. The CI test `test_every_active_signal_in_exactly_one_facet` already enforces this, but the audit provides runtime visibility

### Anti-Patterns to Avoid
- **Monolithic health file:** Don't put all four features in one file. Each feature gets its own computation module (under brain/ or validation/) and shares CLI registration
- **Real-time computation during pipeline:** The health summary (QA-01) should be lightweight -- read from state that's already computed. Don't re-run signal evaluation
- **Hardcoded thresholds for anomaly detection:** Use config/constants at the top of the module, not buried in logic. Follow the project's "no hardcoded thresholds" rule
- **New DuckDB tables:** All needed data is already in existing tables. Don't create new tables for aggregations that can be computed on-the-fly from `brain_signal_runs`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fire rate computation | Custom SQL aggregation | `brain_effectiveness.py::compute_effectiveness()` | Already computes always-fire, never-fire, high-skip classifications |
| Signal YAML loading | Custom YAML walker | `cli_brain_trace.py::_find_signal_yaml()` or `brain_build_signals.py` | Already loads and parses all signal YAMLs |
| Facet loading | Custom facet reader | `brain_facet_schema.py::load_all_facets()` | Already loads all facets with validation |
| Brain DB connection | Manual duckdb.connect | `brain_schema.py::connect_brain_db()` | Standard connection pattern used everywhere |
| CLI Rich tables | Raw print formatting | `Rich.Table` + `Rich.Panel` patterns from `cli_brain_trace.py` | Already established visual language |

**Key insight:** The brain system has matured to the point where all data this phase needs is already captured and queryable. The work is aggregation and presentation, not data collection.

## Common Pitfalls

### Pitfall 1: Signal Results Key Name Inconsistency
**What goes wrong:** Older state.json files use `check_results` while newer ones use `signal_results` (Phase 49 rename). The delta command reads from `brain_signal_runs` which is consistent, but the health summary reads from state.json.
**Why it happens:** Phase 49 renamed check->signal but backward compat aliases exist.
**How to avoid:** Use the existing `_get_signal_results()` helper from `cli_brain_trace.py` which checks both keys. Apply the same pattern in the health summary module.
**Warning signs:** "0 signals evaluated" when the pipeline clearly ran.

### Pitfall 2: Empty Peril Data in brain_signals_active
**What goes wrong:** The `brain audit` command tries to compute coverage by peril, but `peril_id` is NULL for all 380 active signals. The `brain_coverage_matrix` view depends on peril assignments.
**Why it happens:** Peril IDs were added as columns (Phase 42 framework migration) but signal YAML has not been updated to populate them for most signals.
**How to avoid:** The audit should report "peril coverage: NOT AVAILABLE (0/380 signals have peril assignments)" rather than showing a misleading empty matrix. Flag it as a known data gap.
**Warning signs:** All-zero coverage matrix, or "GAP" across all perils.

### Pitfall 3: brain_signal_runs Deduplication
**What goes wrong:** The delta command finds 110 runs but many are TEST runs or rapid re-runs with nearly identical timestamps (e.g., AAPL has 39 runs, TEST has 55 runs). Multiple runs may have been created during development/testing.
**Why it happens:** Every pipeline execution records a new run, including test runs during development.
**How to avoid:** For delta, use the two most recent DISTINCT run_ids for the given ticker, ordered by run_date DESC. Consider showing run_id and run_date in the output so the user can verify they're comparing the right runs.
**Warning signs:** Delta shows hundreds of changes when the user only changed one signal.

### Pitfall 4: 500-Line File Limit
**What goes wrong:** Combining computation + CLI output + anomaly rules in one file exceeds 500 lines.
**Why it happens:** Each feature has both computation logic and Rich formatting.
**How to avoid:** Split each feature into: (a) computation module (brain/ or validation/), (b) CLI command (cli_brain_health.py). The existing pattern of qa_report.py + qa_report_generator.py demonstrates this split.
**Warning signs:** Any file approaching 400 lines -- split proactively.

### Pitfall 5: Threshold Conflict Detection False Positives
**What goes wrong:** The audit flags threshold "conflicts" that are actually valid configurations. For example, a `boolean_presence` threshold type has only `triggered: true` and no numeric ranges to conflict.
**Why it happens:** Not all threshold types use numeric red/yellow/clear ranges.
**How to avoid:** Group threshold conflict detection by `threshold.type`. Only check for overlapping ranges on `tiered_threshold` and `numeric_threshold` types. Skip `boolean_presence`, `count_threshold`, etc.
**Warning signs:** Hundreds of "conflicts" flagged on boolean signals.

## Code Examples

### Post-Pipeline Health Summary Integration Point
```python
# In cli.py, the existing hook (line 347-353):
qa_report = run_qa_verification(state, output_dir)
print_qa_report(qa_report)

# Extended to include signal health summary:
from do_uw.validation.health_summary import compute_health_summary, print_health_summary
health = compute_health_summary(state)
print_health_summary(health)
```

### Cross-Run Delta Query Pattern
```python
# brain/brain_delta.py
def compute_delta(conn: duckdb.DuckDBPyConnection, ticker: str) -> DeltaReport:
    # Get two most recent run_ids for this ticker
    runs = conn.execute("""
        SELECT run_id, MIN(run_date) as run_date
        FROM brain_signal_runs
        WHERE ticker = ? AND is_backtest = FALSE
        GROUP BY run_id
        ORDER BY MIN(run_date) DESC
        LIMIT 2
    """, [ticker]).fetchall()

    if len(runs) < 2:
        return DeltaReport(error="Need at least 2 runs for delta")

    new_run, old_run = runs[0][0], runs[1][0]

    # Find status changes
    changes = conn.execute("""
        SELECT o.signal_id, o.status AS old_status, n.status AS new_status,
               n.value AS new_value
        FROM brain_signal_runs o
        JOIN brain_signal_runs n ON o.signal_id = n.signal_id
        WHERE o.run_id = ? AND n.run_id = ?
          AND o.status != n.status
        ORDER BY o.signal_id
    """, [old_run, new_run]).fetchall()

    return DeltaReport(
        ticker=ticker,
        old_run_id=old_run,
        new_run_id=new_run,
        changes=[...],
    )
```

### Anomaly Detection Heuristic Rules
```python
# validation/health_summary.py
ANOMALY_RULES = [
    # (name, check_fn, level, message_template)
]

def _check_zero_triggered_with_litigation(state, results) -> AnomalyWarning | None:
    """Flag when 0 signals triggered but litigation data is present."""
    triggered = sum(1 for r in results.values() if r.get("status") == "TRIGGERED")
    has_lit = (state.extracted and state.extracted.litigation
               and state.extracted.litigation.active_cases)
    if triggered == 0 and has_lit:
        return AnomalyWarning(
            level="WARNING",
            message="0 signals TRIGGERED but litigation data is present",
            detail=f"{len(has_lit)} active cases found but no signals fired"
        )
    return None
```

### Brain Health Query Pattern
```python
# brain/brain_health.py
def compute_brain_health(conn: duckdb.DuckDBPyConnection) -> BrainHealthReport:
    # Total active signals
    total = conn.execute("SELECT COUNT(*) FROM brain_signals_active").fetchone()[0]

    # Coverage: signals in at least one facet
    # (load facets from YAML, count unique signal IDs)
    from do_uw.brain.brain_facet_schema import load_all_facets
    facets = load_all_facets(Path(__file__).parent / "facets")
    facet_signal_ids = set()
    for f in facets.values():
        facet_signal_ids.update(f.signals)
    coverage_pct = len(facet_signal_ids) / total * 100 if total > 0 else 0

    # Fire rate distribution
    from do_uw.brain.brain_effectiveness import compute_effectiveness
    eff = compute_effectiveness(conn)

    # Feedback queue
    fb_pending = conn.execute(
        "SELECT COUNT(*) FROM brain_feedback WHERE status = 'PENDING'"
    ).fetchone()[0]

    # Data freshness
    last_build = conn.execute(
        "SELECT meta_value FROM brain_meta WHERE meta_key = 'last_build_at'"
    ).fetchone()

    return BrainHealthReport(...)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No post-run QA | Basic QA report (output files, data completeness) | Phase 45 | QA report exists but lacks signal-level health |
| No cross-run tracking | brain_signal_runs records every result | Phase 30 | All data for delta is already captured |
| check_ terminology | signal_ terminology | Phase 49 | Must handle both key names in state.json |
| No facet system | 9 facets with full signal assignments | Phase 49 | Coverage % is now computable |
| brain_effectiveness compute_effectiveness() | Returns EffectivenessReport with all classifications | Phase 30 | Health command mostly wraps existing computation |

**Deprecated/outdated:**
- `check_results` key in state.json: Still present in older output files. Use `_get_signal_results()` helper that checks both keys.
- `knowledge.db` (SQLite): Dual-write removed in Phase 45. All signal run data is in brain.duckdb only.

## Open Questions

1. **Peril coverage in audit**
   - What we know: 0/380 active signals have peril_ids populated. The `brain_coverage_matrix` view depends on peril assignments.
   - What's unclear: Is peril assignment planned for a future phase, or should Phase 50 skip peril coverage analysis entirely?
   - Recommendation: Report it as "not available" with a clear message. Don't fabricate coverage numbers. The audit should surface the gap, not hide it.

2. **Run deduplication strategy for delta**
   - What we know: Some tickers have dozens of runs from development testing (TEST has 55 runs, AAPL has 39).
   - What's unclear: Should delta only compare "real" runs? Is there a way to distinguish test runs from production runs?
   - Recommendation: Use the two most recent runs by default. Provide `--run1` / `--run2` flags for explicit comparison. The user can see run IDs and dates to verify.

3. **Anomaly threshold configuration**
   - What we know: CLAUDE.md says "no hardcoded thresholds"
   - What's unclear: Should anomaly detection thresholds (e.g., "SKIPPED > 45 is a warning") be in a config file?
   - Recommendation: Define thresholds as module-level constants initially (consistent with MAX_SKIPPED_THRESHOLD in test_brain_contract.py). If they need adjustment, move to a config JSON file later.

## Sources

### Primary (HIGH confidence)
- Codebase analysis of `src/do_uw/brain/brain_effectiveness.py` - fire rate computation, effectiveness report model
- Codebase analysis of `src/do_uw/brain/brain_schema.py` - all 19 tables, 11 views, brain_signal_runs schema
- Codebase analysis of `src/do_uw/validation/qa_report.py` - existing QA verification hook
- Codebase analysis of `src/do_uw/cli.py` lines 347-353 - post-pipeline QA integration point
- Codebase analysis of `src/do_uw/stages/analyze/__init__.py` - _record_signal_results() writes to brain_signal_runs
- Codebase analysis of `src/do_uw/cli_brain_trace.py` - established Rich table patterns, _get_signal_results() helper
- Codebase analysis of `src/do_uw/cli_brain.py` - brain_app command registration pattern
- DuckDB data analysis: 110 runs, 36,946 rows, 4 tickers (AAPL, TEST, MSFT, GOOG)

### Secondary (MEDIUM confidence)
- Codebase analysis of test infrastructure: pytest with tests/brain/ directory, test_brain_contract.py as CI guard

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries needed, all patterns established
- Architecture: HIGH - all data sources exist, patterns well-established in codebase
- Pitfalls: HIGH - derived from direct codebase analysis (NULL peril_ids, key name inconsistency, run deduplication)

**Research date:** 2026-02-26
**Valid until:** 2026-03-26 (stable domain, no external dependencies)
