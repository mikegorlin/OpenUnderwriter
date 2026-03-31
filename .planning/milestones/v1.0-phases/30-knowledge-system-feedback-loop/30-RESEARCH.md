# Phase 30: Knowledge System & Feedback Loop - Research

**Researched:** 2026-02-15
**Domain:** Internal system architecture (knowledge store wiring, feedback loop, traceability, pricing integration)
**Confidence:** HIGH (all findings from direct codebase investigation)

## Summary

Phase 30 completes the migration from flat JSON config files to the knowledge store as the single source of truth for check definitions, and adds a feedback loop so each pipeline run records per-check results for fire rate analysis and dead check detection.

The codebase is well-positioned for this phase. The knowledge store (`KnowledgeStore` with SQLAlchemy ORM on SQLite) already exists with check tables, full-text search, and lifecycle management. A `BackwardCompatLoader` wrapper already bridges the old `ConfigLoader` interface, but it creates an **in-memory** store each run and re-migrates from `brain/checks.json` every time. The key insight: the persistent `knowledge.db` exists on disk (122KB, tables created) but has **zero checks** in it. Checks only live in the ephemeral in-memory store. Phase 30's Plan 01 must fix this by seeding the persistent store once, then reading from it at runtime.

The learning infrastructure (`learning.py`) already has `record_analysis_run()` and `get_check_effectiveness()` but stores outcomes as JSON-serialized Note objects with the `analysis_run` tag -- a design that works but does not support efficient per-check queries. Phase 30's Plan 02 should add a dedicated `check_runs` table for structured per-check per-run results.

The pricing connection (Plan 04) is largely already built. The BENCHMARK stage already queries `PricingStore` via `MarketPositionEngine`, computes `MarketIntelligence`, and attaches it to `state.executive_summary.deal_context.market_intelligence`. The remaining work is a "Market Context" section in the rendered worksheet.

**Primary recommendation:** Execute plans in dependency order: 30-01 (persistent knowledge store) first since it's foundational, then 30-02 (feedback) and 30-03 (traceability) in parallel since they're independent, then 30-04 (pricing render) last since it depends on nothing but is the most isolated.

## Standard Stack

### Core (already in use -- no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0+ | ORM for knowledge.db | Already used for all knowledge tables |
| SQLite (via Python stdlib) | 3.x | Persistent store | Already the DB backend |
| Alembic | 1.13+ | Schema migrations | Already used (4 migration versions exist) |
| Pydantic v2 | 2.x | Data models | Project-wide standard |
| Typer + Rich | 0.9+/13+ | CLI commands | Already used for `angry-dolphin knowledge` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none new) | - | - | All needed libraries already in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLite check_runs table | JSON Notes (current learning.py) | Notes work but can't efficiently query per-check stats across runs; dedicated table enables SQL aggregation |
| Alembic migration | `Base.metadata.create_all()` auto-create | Auto-create doesn't track schema evolution; Alembic matches existing pattern |

## Architecture Patterns

### Current Data Flow (ANALYZE stage check loading)
```
AnalyzeStage.run()
  -> BackwardCompatLoader(playbook_id=...)
    -> _create_default_store()           # In-memory SQLite
      -> KnowledgeStore(db_path=None)    # Ephemeral
      -> migrate_from_json(brain_dir, store)  # Re-read checks.json every run
    -> load_all() -> BrainConfig
  -> execute_checks(brain.checks["checks"], extracted, company)
```

### Target Data Flow (after Phase 30)
```
AnalyzeStage.run()
  -> KnowledgeStore(db_path=default)     # Persistent SQLite on disk
    -> query_checks(status="ACTIVE")     # Read from DB, not JSON
    -> Convert to check dicts (same format as checks.json "checks" list)
  -> execute_checks(checks, extracted, company)

  After execution:
  -> write_check_run_results(run_id, ticker, results)  # NEW: feedback
```

### Pattern 1: Idempotent Migration Seeding
**What:** One-time seed of persistent knowledge.db from brain/checks.json with idempotent upsert behavior. After seeding, brain/checks.json becomes a migration source only.
**When to use:** First run after Phase 30 deployment, or any `angry-dolphin knowledge migrate` invocation.
**Key constraint:** Must be idempotent -- running migrate twice produces the same result. The current `migrate_from_json()` does INSERT-only (no upsert), so it will fail on duplicate keys if run twice. Need to add upsert-or-skip logic.

### Pattern 2: Backward-Compatible Check Dict Format
**What:** The check engine (`execute_checks`) consumes `list[dict[str, Any]]` where each dict matches the checks.json check structure. The knowledge store's `query_checks()` returns different dict keys. A conversion layer must translate ORM Check objects back to the checks.json dict format.
**When to use:** Runtime check loading from knowledge store.
**Key constraint:** The `metadata_json` field on each Check already stores the original JSON dict. The compat_loader's `_reconstruct_checks()` method already uses this. This is the migration bridge: read `metadata_json`, parse as JSON, feed to check engine. Zero behavior change guaranteed.

### Pattern 3: Check Run Feedback Table
**What:** New `check_runs` table recording per-check per-run results. Schema: `(id, run_id, ticker, run_date, check_id FK, status, value, evidence_quality, data_status, duration_ms)`.
**When to use:** After every ANALYZE stage execution, before marking the stage complete.
**Key insight:** The current `learning.py` stores entire `AnalysisOutcome` objects as JSON-in-Note. A dedicated table enables SQL queries like "fire rate for check X across all runs", "checks that never fire", "checks that always skip".

### Pattern 4: Traceability Chain
**What:** 5-link chain: DATA_SOURCE -> EXTRACTION -> EVALUATION -> OUTPUT -> SCORING. Each link answers: where did the data come from, how was it extracted, how was it evaluated, where does it appear in the output, and how did it affect the score.
**When to use:** Audit and quality assurance.
**Key constraint:** Most links already exist implicitly. CheckResult has `source` (DATA_SOURCE), the check engine evaluation logic is deterministic (EVALUATION), factor mapping exists (SCORING). The gaps are: formalized EXTRACTION link (which EXTRACT module produced the data) and OUTPUT link (which worksheet section renders the result).

### Anti-Patterns to Avoid
- **Dual source of truth:** During migration, do NOT have both brain/checks.json and knowledge.db as active sources. One must be canonical; the other is a migration backup.
- **Breaking the BrainConfig interface:** SCORE and BENCHMARK also use `BackwardCompatLoader`. Changing check loading in ANALYZE without coordinating SCORE/BENCHMARK will break the pipeline.
- **Overengineering the traceability chain:** Don't build a separate graph database. Simple metadata fields on CheckResult (already a Pydantic model) are sufficient for the 5-link chain.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema migrations | Manual ALTER TABLE | Alembic migration (version 005) | Pattern established by 4 existing migrations |
| Check dict reconstruction | New serialization format | `metadata_json` field on Check ORM | Already stores full original JSON per check |
| Fire rate computation | Custom analytics engine | SQL COUNT/GROUP BY queries on check_runs table | Database aggregation is faster and simpler than Python iteration |
| Market Context rendering | New render module | Extend existing SECT1/SECT7 render sections | Market intelligence data already on state |

**Key insight:** The existing `metadata_json` field on each Check ORM object is the golden bridge between the knowledge store and the check engine. It stores the exact JSON dict that `execute_checks()` expects. Reading checks from the knowledge store and feeding `json.loads(check.metadata_json)` to the engine guarantees zero behavior change.

## Common Pitfalls

### Pitfall 1: In-Memory vs Persistent Store Confusion
**What goes wrong:** `BackwardCompatLoader()` with no args creates an in-memory store. `KnowledgeStore()` with no args uses the default `knowledge.db` on disk. Code that instantiates the wrong one will either read empty data (persistent but never seeded) or lose data (in-memory but never persisted).
**Why it happens:** Two constructors, two defaults, easy to mix up.
**How to avoid:** After Plan 30-01, `BackwardCompatLoader` should detect if the persistent store has checks and use it directly, falling back to in-memory migration only if the persistent store is empty. Add a `store.has_checks()` or `store.check_count()` method.
**Warning signs:** Test passes locally (in-memory) but fails in production (persistent store empty).

### Pitfall 2: Migration Idempotency
**What goes wrong:** Running `migrate_from_json()` twice on the persistent store raises duplicate key errors because `bulk_insert_checks()` does `session.add_all()` with existing primary keys.
**Why it happens:** Current migration assumes fresh in-memory store.
**How to avoid:** Use "INSERT OR REPLACE" semantics or check-before-insert. SQLAlchemy's `session.merge()` instead of `session.add()` handles upserts.
**Warning signs:** `IntegrityError: UNIQUE constraint failed: checks.id` on second migration.

### Pitfall 3: Feedback Loop Interfering with Pipeline Performance
**What goes wrong:** Writing 388 check run results after every ANALYZE stage adds latency to the pipeline.
**Why it happens:** SQLite single-writer bottleneck, one INSERT per check.
**How to avoid:** Batch INSERT all results in a single transaction. SQLite can handle 388 inserts in <100ms when batched. Do NOT commit per-check.
**Warning signs:** ANALYZE stage duration increases by >500ms after adding feedback.

### Pitfall 4: Breaking SCORE/BENCHMARK Stages
**What goes wrong:** Changing how `BackwardCompatLoader` works affects SCORE and BENCHMARK stages (both import and use it).
**Why it happens:** Three stages all use `BackwardCompatLoader` -- ANALYZE, SCORE, and BENCHMARK.
**How to avoid:** Keep `BackwardCompatLoader.load_all()` returning identical `BrainConfig` objects regardless of whether data comes from in-memory migration or persistent store. Test by comparing `brain.checks` dict output before and after the change.
**Warning signs:** SCORE stage fails with missing or different check data.

### Pitfall 5: Traceability Over-Design
**What goes wrong:** Building a complex graph traversal system for the 5-link chain when simple metadata fields suffice.
**Why it happens:** The concept of "traceability chain" sounds like it needs a graph.
**How to avoid:** Add 5 string fields to CheckResult (or a single `traceability: dict[str, str]` field). Populate them during check execution. An "incomplete chain" is simply a result where one of the 5 fields is empty. `angry-dolphin knowledge traceability-audit` just queries for these gaps.
**Warning signs:** Creating new ORM tables or relationships for traceability when metadata fields suffice.

## Code Examples

### Example 1: Reading Checks from Persistent Store (Plan 30-01)
```python
# In BackwardCompatLoader.__init__, replace in-memory with persistent:
def __init__(self, store: KnowledgeStore | None = None, ...) -> None:
    if store is not None:
        self._store = store
    else:
        # Try persistent store first
        default_store = KnowledgeStore()  # Uses default knowledge.db
        if self._store_has_checks(default_store):
            self._store = default_store
        else:
            # Fall back to in-memory migration (first run or empty DB)
            self._store = self._create_default_store()

@staticmethod
def _store_has_checks(store: KnowledgeStore) -> bool:
    """Check if the persistent store has been seeded."""
    checks = store.query_checks(limit=1)
    return len(checks) > 0
```

### Example 2: Check Run Feedback Table Schema (Plan 30-02)
```python
# New ORM model in knowledge/models.py
class CheckRun(Base):
    """Per-check per-run result for feedback loop analysis."""
    __tablename__ = "check_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String, nullable=False, index=True)
    run_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    check_id: Mapped[str] = mapped_column(String, ForeignKey("checks.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)  # FIRED/SKIPPED/NO_DATA/ERROR
    value: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence_quality: Mapped[str | None] = mapped_column(String, nullable=True)
    data_status: Mapped[str] = mapped_column(String, nullable=False, default="EVALUATED")
```

### Example 3: Writing Check Results After ANALYZE (Plan 30-02)
```python
# In AnalyzeStage.run(), after execute_checks():
def _record_check_results(state: AnalysisState, results: list[CheckResult]) -> None:
    """Write per-check results to knowledge store for feedback analysis."""
    from do_uw.knowledge.store import KnowledgeStore
    store = KnowledgeStore()
    run_id = f"{state.ticker}_{state.created_at.strftime('%Y%m%d_%H%M%S')}"

    with store.get_session() as session:
        for result in results:
            run = CheckRun(
                run_id=run_id,
                ticker=state.ticker,
                run_date=state.created_at,
                check_id=result.check_id,
                status=_map_status(result.status),
                value=str(result.value) if result.value is not None else None,
                data_status=result.data_status,
            )
            session.add(run)
    # Single transaction commit via context manager
```

### Example 4: Traceability Fields on CheckResult (Plan 30-03)
```python
# Add to CheckResult in check_results.py:
class CheckResult(BaseModel):
    # ... existing fields ...

    # Traceability chain (5 links)
    trace_data_source: str = Field(
        default="",
        description="Link 1: Where data came from (e.g., 'SEC_10K:item_7_mda')",
    )
    trace_extraction: str = Field(
        default="",
        description="Link 2: Which extraction produced the value (e.g., 'xbrl_extractor')",
    )
    trace_evaluation: str = Field(
        default="",
        description="Link 3: Evaluation method (e.g., 'tiered_threshold:red>25%')",
    )
    trace_output: str = Field(
        default="",
        description="Link 4: Where result appears in worksheet (e.g., 'SECT3:financial_health')",
    )
    trace_scoring: str = Field(
        default="",
        description="Link 5: How result affects score (e.g., 'F1:-3.5pts')",
    )
```

### Example 5: CLI Fire Rate Command (Plan 30-02)
```python
@knowledge_app.command("check-stats")
def check_stats(
    check_id: str = typer.Option(None, "--check", "-c", help="Specific check ID"),
    min_runs: int = typer.Option(3, "--min-runs", help="Minimum runs to report"),
) -> None:
    """Show fire rates, skip rates, and anomalies across pipeline runs."""
    store = KnowledgeStore()
    # SQL: SELECT check_id, status, COUNT(*) FROM check_runs GROUP BY check_id, status
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ConfigLoader reads brain/checks.json directly | BackwardCompatLoader wraps KnowledgeStore (in-memory) | Phase 19 | Knowledge store schema exists but checks never persist |
| No check result recording | learning.py records AnalysisOutcome as JSON Notes | Phase 22 | Aggregate fire data exists but not per-check queryable |
| No pricing integration | MarketIntelligence computed in BENCHMARK | Phase 25 | Data exists on state, not yet rendered as "Market Context" |

**Current gap:** The knowledge.db file on disk has 0 checks despite having the schema. All check loading still bottlenecks through brain/checks.json via in-memory migration.

## Open Questions

1. **Should brain/checks.json be deleted after migration?**
   - What we know: Plan says "deprecated, not runtime source." Phase 30 architecture says it becomes "a migration source."
   - What's unclear: Whether to keep it as a human-readable backup or delete it entirely.
   - Recommendation: Keep it as read-only reference. Add a deprecation banner to the file header. Do NOT delete it in this phase.

2. **Should check_runs have a FK constraint to checks table?**
   - What we know: The checks table primary key is check_id (string). CheckRun would reference it.
   - What's unclear: Industry checks from playbooks are dynamically generated -- they may not exist in the checks table at run time.
   - Recommendation: Use check_id as a string column WITHOUT a FK constraint. This allows recording results for dynamically-generated industry checks. Add an index for query performance.

3. **Should the feedback loop record results for ALL checks or only AUTO checks?**
   - What we know: `execute_checks()` filters to `execution_mode == "AUTO"` (about 350 of 388 checks). The remaining 38 are MANUAL checks.
   - What's unclear: Whether MANUAL checks should be tracked for fire rate analysis.
   - Recommendation: Record all checks that pass through `execute_checks()`, which is already only AUTO checks. MANUAL checks are not executed by the engine and have no results to record.

4. **Market Context section location in worksheet**
   - What we know: MarketIntelligence is currently on `executive_summary.deal_context.market_intelligence`. It's computed in BENCHMARK but not rendered as its own section.
   - What's unclear: Whether "Market Context" should be a subsection of Section 1 (Executive Summary) or Section 7 (Scoring).
   - Recommendation: Add to Section 1 (Executive Summary) as SECT1-08, right after Deal Context (SECT1-07). It's executive-level information.

## Detailed Codebase Inventory

### Files That Must Change (Plan 30-01: Knowledge Store as Check Source)

| File | Lines | Current Role | Change Needed |
|------|-------|-------------|---------------|
| `src/do_uw/knowledge/compat_loader.py` | 249 | In-memory migration wrapper | Detect persistent store, use it when available |
| `src/do_uw/knowledge/migrate.py` | 413 | One-shot INSERT migration | Add idempotent upsert (merge) behavior |
| `src/do_uw/knowledge/store.py` | 442 | Query API | Add `check_count()` helper method |
| `src/do_uw/stages/analyze/__init__.py` | 323 | ANALYZE orchestrator | No change needed (uses BackwardCompatLoader) |
| `src/do_uw/stages/score/__init__.py` | 483 | SCORE orchestrator | No change needed (uses BackwardCompatLoader) |
| `src/do_uw/stages/benchmark/__init__.py` | 499 | BENCHMARK orchestrator | No change needed (uses BackwardCompatLoader) |

### Files That Must Change (Plan 30-02: Check Result Feedback)

| File | Lines | Current Role | Change Needed |
|------|-------|-------------|---------------|
| `src/do_uw/knowledge/models.py` | 295 | ORM models | Add CheckRun model |
| `src/do_uw/knowledge/store.py` | 442 | Query API | Add `write_check_runs()` and `get_check_stats()` |
| `src/do_uw/stages/analyze/__init__.py` | 323 | ANALYZE orchestrator | Call feedback recording after check execution |
| `src/do_uw/cli_knowledge.py` | 375 | CLI commands | Add `check-stats` and `anomalies` commands |
| `src/do_uw/knowledge/migrations/versions/005_check_runs.py` | (new) | New migration | Create check_runs table |

### Files That Must Change (Plan 30-03: Check Traceability)

| File | Lines | Current Role | Change Needed |
|------|-------|-------------|---------------|
| `src/do_uw/stages/analyze/check_results.py` | 236 | CheckResult model | Add 5 traceability fields |
| `src/do_uw/stages/analyze/check_engine.py` | 580 | Check execution | Populate trace_evaluation, trace_scoring fields |
| `src/do_uw/stages/analyze/check_mappers.py` | ~varies | Data mapping | Populate trace_data_source, trace_extraction fields |
| `src/do_uw/cli_knowledge.py` | 375 | CLI | Add `traceability-audit` command |

### Files That Must Change (Plan 30-04: Pricing Connection)

| File | Lines | Current Role | Change Needed |
|------|-------|-------------|---------------|
| `src/do_uw/models/scoring.py` | ~350 | BenchmarkResult | Add `market_pricing_context` field |
| `src/do_uw/stages/benchmark/__init__.py` | 499 | BENCHMARK stage | Populate market_pricing_context from PricingStore |
| `src/do_uw/stages/render/sections/` | varies | Render sections | Add Market Context rendering section |

### Key Invariant: BackwardCompatLoader Consumer Chain

Three stages import and use `BackwardCompatLoader`:
1. **ANALYZE** (`stages/analyze/__init__.py:19`): `loader = BackwardCompatLoader(playbook_id=playbook_id)`
2. **SCORE** (`stages/score/__init__.py:21`): `loader = BackwardCompatLoader()`
3. **BENCHMARK** (`stages/benchmark/__init__.py:18`): `loader = BackwardCompatLoader()`

All three call `loader.load_all()` to get `BrainConfig`. Any change to `BackwardCompatLoader` MUST preserve the exact `BrainConfig` output for all three consumers. The regression test is: `before.load_all() == after.load_all()`.

### Key Invariant: Check Dict Format

`execute_checks()` in `check_engine.py` expects `list[dict[str, Any]]` where each dict has at minimum:
- `id` (str): Check identifier
- `name` (str): Human-readable name
- `execution_mode` (str): "AUTO" to be executed
- `threshold` (dict): With `type` key and tier values
- `factors` (list): Scoring factor mappings
- `section` (int): Worksheet section number
- `required_data` (list): Data source requirements
- `data_locations` (dict): Where to find data

These dicts are currently deserialized from `brain.checks["checks"]`. The `metadata_json` field on the Check ORM stores the exact same JSON, so `json.loads(check.metadata_json)` produces an identical dict. This is the zero-regression bridge.

## Sources

### Primary (HIGH confidence)
- Direct codebase investigation: `src/do_uw/knowledge/store.py`, `compat_loader.py`, `models.py`, `migrate.py`, `learning.py`, `lifecycle.py`, `provenance.py`
- Direct codebase investigation: `src/do_uw/stages/analyze/__init__.py`, `check_engine.py`, `check_results.py`
- Direct codebase investigation: `src/do_uw/stages/score/__init__.py`, `src/do_uw/stages/benchmark/__init__.py`
- Direct codebase investigation: `src/do_uw/pipeline.py`, `src/do_uw/cli.py`, `src/do_uw/cli_knowledge.py`
- Direct codebase investigation: `src/do_uw/models/state.py`, `scoring.py`, `executive_summary.py`
- Direct codebase investigation: `src/do_uw/config/loader.py` (BrainConfig)
- SQLite schema inspection: `knowledge.db` (0 checks, full schema present)
- Phase 29 SUMMARY.md: stage boundary enforcement, brain rebalancing

### Secondary (MEDIUM confidence)
- None needed -- all findings from direct codebase investigation

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use, no new dependencies
- Architecture: HIGH - All data flow paths traced through actual code
- Pitfalls: HIGH - Identified from actual code patterns (in-memory vs persistent confusion, migration idempotency) seen in current implementation
- Code examples: HIGH - Modeled on existing patterns in the codebase

**Research date:** 2026-02-15
**Valid until:** 2026-03-15 (stable internal architecture, no external dependencies)
