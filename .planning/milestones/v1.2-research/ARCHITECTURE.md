# Architecture Patterns: v1.2 System Intelligence Integration

**Domain:** D&O underwriting pipeline -- system intelligence, diagnostics, feedback loops, signal lifecycle
**Researched:** 2026-02-26
**Confidence:** HIGH (derived from exhaustive source code audit of existing codebase)

---

## Existing Architecture Inventory

Before designing v1.2 integration, here is what exists and where each v1.2 feature connects.

### Current System Map

```
CLI Layer (Typer sub-apps)
  cli.py            -- main: analyze, version
  cli_brain.py      -- brain: status, gaps, effectiveness, build, changelog, backlog, export-docs, backtest
  cli_validate.py   -- validate: run, cost-report
  cli_feedback.py   -- feedback: add, summary, list
  cli_ingest.py     -- ingest: file, url
  cli_knowledge.py  -- knowledge: check-stats, dead-checks, etc.
  cli_calibrate.py  -- calibrate: threshold tuning
  cli_pricing.py    -- pricing: market intelligence
  cli_dashboard.py  -- dashboard: serve (FastAPI)

Pipeline (7 stages, linear, no branching)
  pipeline.py       -- Pipeline orchestrator with StageCallbacks protocol
  stages/resolve/   -- Ticker -> CompanyProfile
  stages/acquire/   -- Data acquisition (SEC, market, lit, web)
  stages/extract/   -- Raw -> structured (LLM + regex)
  stages/analyze/   -- Check engine (400 checks), patterns, forensics
  stages/score/     -- 10-factor scoring, red flags, tier
  stages/benchmark/ -- Peer comparisons, executive summary
  stages/render/    -- HTML/Word/PDF/Markdown generation

Brain Knowledge System (YAML source of truth, DuckDB cache)
  brain/checks/**/*.yaml  -- 400 checks in 36 YAML files across 8 domains
  brain/facets/*.yaml     -- 2 facet specs (governance, red_flags)
  brain/framework/*.yaml  -- Perils (8), causal chains (16)
  brain/brain.duckdb      -- 19 tables, 11 views, rebuilt from YAML via `brain build`
  brain/brain_schema.py   -- DDL for all DuckDB tables
  brain/brain_check_schema.py -- BrainCheckEntry Pydantic model
  brain/brain_loader.py   -- BrainDBLoader reads from DuckDB
  brain/brain_build_checks.py -- YAML -> DuckDB migration
  brain/brain_writer.py   -- Insert/update checks in DuckDB

Knowledge Store (SQLite, separate from brain DuckDB)
  knowledge/knowledge.db     -- SQLite ORM (SQLAlchemy 2.0)
  knowledge/models.py        -- Check, CheckHistory, Pattern, RedFlag, etc.
  knowledge/store.py          -- CRUD operations
  knowledge/lifecycle.py      -- INCUBATING -> DEVELOPING -> ACTIVE -> DEPRECATED
  knowledge/feedback.py       -- Record/query feedback in brain.duckdb
  knowledge/feedback_models.py -- FeedbackEntry, FeedbackSummary, ProposalRecord
  knowledge/gap_detector.py   -- 3-level gap analysis (SOURCE, FIELD, MAPPER)
  knowledge/ingestion_llm.py  -- LLM document intelligence extraction
  knowledge/learning.py       -- Live learning from pipeline runs
  knowledge/calibrate.py      -- Threshold calibration from run data
  knowledge/backtest.py       -- Historical backtesting

State Model (single source of truth)
  models/state.py           -- AnalysisState (root), AcquiredData, ExtractedData, AnalysisResults
  models/common.py          -- StageResult, StageStatus, SourcedValue, Confidence

Validation Infrastructure
  validation/qa_report.py   -- Post-pipeline QA (output files, data completeness, hazard evidence)
  validation/runner.py      -- Multi-ticker ValidationRunner
  validation/config.py      -- Canonical ticker sets
```

### Component File Counts and Budget

The 500-line limit is a hard constraint. Here are files near the limit that cannot absorb new logic:

| File | Lines | Status |
|------|-------|--------|
| `stages/analyze/__init__.py` | 429 | Near limit -- NO new logic here |
| `brain/brain_loader.py` | ~460 | Near limit |
| `brain/brain_build_checks.py` | ~340 | Room for ~160 lines |
| `brain/brain_effectiveness.py` | ~370 | Room for ~130 lines |
| `knowledge/feedback.py` | ~426 | Near limit |
| `validation/qa_report.py` | ~461 | Near limit |
| `pipeline.py` | ~336 | Room for ~160 lines |

**Implication:** All new features MUST be in new files. Existing files should only receive import statements and thin delegation calls.

---

## v1.2 Feature Integration Map

### Feature 1: Pipeline Diagnostics

**What:** Health monitoring dashboard, data routing verification, coverage metrics.

**Existing foundation:**
- `stages/analyze/pipeline_audit.py` -- audit_all_checks() with data_status (HAS_DATA/NO_MAPPER/ALL_NONE)
- `knowledge/gap_detector.py` -- detect_gaps() with 3-level gap analysis
- `brain/brain_effectiveness.py` -- compute_effectiveness() for fire rates
- `cli_brain.py` -- brain status, brain gaps, brain effectiveness commands
- `validation/qa_report.py` -- post-run QA checks

**Integration approach: NEW components, thin wiring to existing**

```
NEW FILES:
  diagnostics/                    -- New top-level package under src/do_uw/
    __init__.py
    health_monitor.py             -- Aggregate health score from multiple probes
    data_route_verifier.py        -- Verify every check's data path end-to-end
    coverage_dashboard.py         -- Rich CLI table or JSON export of coverage metrics
    report.py                     -- DiagnosticsReport Pydantic model

MODIFIED (thin wiring only):
  cli_brain.py                    -- Add `brain diagnostics` command (~15 lines)
  pipeline.py                     -- Optional post-run diagnostics hook (~10 lines)
```

**Data flow:**
```
brain build                              brain diagnostics
    |                                         |
    v                                         v
brain.duckdb  ---reads--->  health_monitor.py
    |                            |
    v                            v
gap_detector.py             DiagnosticsReport
pipeline_audit.py               |
brain_effectiveness.py          v
                          coverage_dashboard.py -> Rich CLI table
```

**Key design decisions:**
1. Diagnostics is a READ-ONLY observer. It queries brain.duckdb and pipeline audit results but never mutates state.
2. No changes to AnalysisState -- diagnostics operates on brain metadata, not pipeline state.
3. Post-run diagnostics hook is OPTIONAL (off by default). Runs after pipeline completes, not during.
4. `brain diagnostics` is the primary entry point. No new CLI sub-app needed.

**What NOT to build:**
- No real-time monitoring during pipeline execution (complexity too high for value)
- No separate diagnostics database (brain.duckdb already has all the data)
- No web UI for diagnostics (Rich CLI tables suffice for v1.2)

---

### Feature 2: Automated QA

**What:** Post-run validation that catches quality regressions + periodic brain health audits.

**Existing foundation:**
- `validation/qa_report.py` -- run_qa_verification() with 5 check categories
- `validation/runner.py` -- Multi-ticker ValidationRunner
- `brain/brain_effectiveness.py` -- Always-fire, never-fire, high-skip detection
- Post-pipeline QA already runs in cli.py analyze command (line 347-351)

**Integration approach: EXTEND existing QA, add brain audit**

```
NEW FILES:
  validation/brain_audit.py       -- Periodic brain consistency checks
  validation/qa_checks_brain.py   -- Brain-specific QA check functions
  validation/regression.py        -- SKIPPED/TRIGGERED count regression baselines

MODIFIED (thin wiring only):
  validation/qa_report.py         -- Add brain_audit check category (~5 lines import + call)
  cli_brain.py                    -- Add `brain audit` command (~15 lines)
```

**Brain audit checks (new):**
1. Every check has required_data populated
2. Every check has data_strategy.field_key or FIELD_FOR_CHECK entry or Phase 26+ mapper
3. Every check's threshold type matches its evaluation path
4. No orphaned checks (check in DuckDB but not in YAML)
5. No orphaned facet signals (signal referenced by facet but check doesn't exist)
6. SKIPPED check count is within threshold of baseline (regression guard)
7. TRIGGERED check count stability across multi-ticker runs

**Data flow:**
```
brain build -> brain.duckdb
                    |
                    v
             brain_audit.py  ---compares--->  regression.py (baseline)
                    |
                    v
              BrainAuditReport (Pydantic)
                    |
                    v
           cli: brain audit -> Rich table
           OR
           qa_report.py -> integrated into post-run QA
```

**Key design decisions:**
1. Brain audit is SEPARATE from post-run QA. Post-run QA validates a single analysis. Brain audit validates the brain corpus itself.
2. Brain audit can run without a pipeline execution (it reads brain.duckdb only).
3. Regression baselines are stored as JSON files in a new `validation/baselines/` directory, committed to git. Updated via explicit command, not automatically.
4. Post-run QA gains ONE new category ("Brain Coverage") by calling into qa_checks_brain.py -- keeps qa_report.py under 500 lines.

---

### Feature 3: Underwriter Feedback CLI

**What:** `do-uw feedback <TICKER>` to capture underwriter reactions and feed back into brain.

**Existing foundation:**
- `cli_feedback.py` -- feedback add/summary/list already exist and work
- `knowledge/feedback.py` -- record_feedback(), get_feedback_summary(), auto-proposal for MISSING_COVERAGE
- `knowledge/feedback_models.py` -- FeedbackEntry, FeedbackSummary, ProposalRecord
- `brain/brain_schema.py` -- brain_feedback and brain_proposals tables exist
- `knowledge/calibrate.py` -- threshold calibration infrastructure

**Integration approach: ENHANCE existing, add processing pipeline**

```
NEW FILES:
  knowledge/feedback_processor.py  -- Batch process pending feedback into brain changes
  knowledge/feedback_report.py     -- Generate feedback impact report

MODIFIED (thin wiring only):
  cli_feedback.py                  -- Add `feedback process` and `feedback report` commands (~30 lines)
```

**What the feedback processor does:**
1. Query brain_feedback WHERE status = 'PENDING'
2. For ACCURACY feedback with direction:
   - FALSE_POSITIVE on a check: propose threshold loosening
   - FALSE_NEGATIVE on a check: propose threshold tightening
   - Record proposed change in brain_proposals
3. For THRESHOLD feedback:
   - TOO_SENSITIVE: calculate suggested threshold from historical fire rate
   - TOO_LOOSE: same calculation, opposite direction
4. For MISSING_COVERAGE: already auto-proposes (existing code)
5. Generate human-reviewable report of all proposals
6. `feedback apply <proposal_id>` applies a proposal and marks feedback as APPLIED

**Data flow:**
```
do-uw feedback add AAPL --check FIN.PROFIT.revenue --type ACCURACY --direction FALSE_POSITIVE --note "..."
    |
    v
brain_feedback table (PENDING)
    |
    v
do-uw feedback process  (new command)
    |
    v
feedback_processor.py
    |
    ├─ Reads brain_check_runs for historical context
    ├─ Reads brain_effectiveness for fire rate
    ├─ Generates proposals in brain_proposals
    └─ Returns FeedbackProcessReport
    |
    v
do-uw feedback report  (new command)
    |
    v
feedback_report.py -> Rich table of proposals with evidence
```

**Key design decisions:**
1. Processing is EXPLICIT (user runs `feedback process`), never automatic. Keeps human in the loop.
2. Proposals require explicit approval (`feedback apply <id>`) before modifying brain YAML.
3. The feedback -> proposal -> apply pipeline reuses existing brain_proposals infrastructure.
4. No modification to AnalysisState -- feedback operates entirely outside the pipeline.

---

### Feature 4: Knowledge Ingestion

**What:** Ingest market events, regulatory changes, case law -- suggest brain changes.

**Existing foundation:**
- `cli_ingest.py` -- ingest file/url commands exist and work
- `knowledge/ingestion_llm.py` -- LLM-powered document analysis, proposal generation
- `knowledge/ingestion_models.py` -- DocumentIngestionResult, IngestionImpactReport, ProposedCheck
- `knowledge/ingestion.py` -- Non-LLM ingestion pipeline

**Integration approach: EXTEND existing ingestion with structured event types**

```
NEW FILES:
  knowledge/event_types.py         -- Structured event type definitions
  knowledge/event_ingestion.py     -- Market event -> brain impact mapping
  knowledge/event_store.py         -- Store ingested events for tracking

MODIFIED (thin wiring only):
  cli_ingest.py                    -- Add `ingest event` command (~20 lines)
  knowledge/ingestion_llm.py       -- NO changes (already works for doc analysis)
```

**Event types to support:**
- SEC_ENFORCEMENT: SEC action against a company or industry
- REGULATORY_CHANGE: New regulation affecting D&O exposure
- CASE_LAW: Court decision creating new precedent
- MARKET_EVENT: Market crash, sector crisis, bubble
- CLAIMS_STUDY: Published claims data from broker/insurer

**Data flow:**
```
do-uw ingest event --type SEC_ENFORCEMENT --source "url" --summary "..."
    |
    v
event_ingestion.py
    |
    ├─ Map event to affected checks (by peril_id, chain_id, factor)
    ├─ Identify threshold impact (does this event change risk levels?)
    ├─ Generate proposals for check modifications or new checks
    └─ Store event record in brain.duckdb (new table: brain_events)
    |
    v
brain_proposals table (proposals for human review)
    |
    v
do-uw feedback report  (shared command shows all proposals)
```

**Key design decisions:**
1. Events are stored permanently as institutional memory (new brain_events table in DuckDB).
2. Event -> check mapping uses existing peril/chain/factor infrastructure in brain YAML.
3. LLM ingestion (existing) handles unstructured documents. Event ingestion handles structured metadata about known event types.
4. Both paths produce brain_proposals entries -- same review/apply workflow.

---

### Feature 5: Signal Lifecycle

**What:** Formal emerging -> established -> deprecated lifecycle driven by data, not just manual state changes.

**Existing foundation:**
- `knowledge/lifecycle.py` -- CheckStatus enum (INCUBATING, DEVELOPING, ACTIVE, DEPRECATED), validate_transition(), transition_check()
- `brain/brain_schema.py` -- brain_checks.lifecycle_state column exists
- `brain/brain_build_checks.py` -- lifecycle_state handled during YAML -> DuckDB build
- `brain/brain_check_schema.py` -- BrainCheckEntry has no lifecycle fields beyond what's in DuckDB
- brain_checks_active view: filters on lifecycle_state NOT IN ('RETIRED', 'INCUBATING', 'INACTIVE')

**Current lifecycle states in brain.duckdb:**
- lifecycle_state column values: ACTIVE, RETIRED, INCUBATING, INACTIVE
- Note: YAML checks currently have NO lifecycle_state field -- it's set during build based on presence/absence

**Gap analysis: What needs to change for signal epistemology**

The current lifecycle.py uses SQLAlchemy ORM against knowledge.db (SQLite). The brain system uses DuckDB. These are two parallel systems that have not converged. v1.2 must resolve this.

**Integration approach: ADD lifecycle to brain YAML, retire SQLite lifecycle**

```
NEW FILES:
  brain/signal_lifecycle.py        -- Signal state machine for brain YAML checks
  brain/signal_lifecycle_rules.py  -- Auto-transition rules (data-driven)

MODIFIED:
  brain/brain_check_schema.py      -- Add lifecycle fields to BrainCheckEntry (~10 lines)
  brain/brain_build_checks.py      -- Read lifecycle fields from YAML during build (~15 lines)
  brain/checks/**/*.yaml           -- Add lifecycle fields to check entries (batch edit)
```

**New lifecycle model for brain YAML:**

```yaml
# In each check YAML entry:
lifecycle:
  state: established       # emerging | established | deprecated
  since: "2026-02-01"      # Date of last state transition
  evidence_count: 47       # Pipeline runs where this check evaluated
  fire_rate_30d: 0.15      # Recent fire rate
  confidence: high         # Based on evidence_count + fire_rate stability
  deprecation_note: ""     # Non-empty = reason for deprecation
```

**State transitions:**
```
emerging -> established:   evidence_count >= 10 AND fire_rate stable (stddev < 0.15)
established -> deprecated: fire_rate == 0.0 for 20+ runs OR underwriter marks as obsolete
deprecated -> emerging:    market event re-activates signal (via event ingestion)
emerging -> deprecated:    evidence_count >= 10 AND fire_rate == 0.0 (never useful)
```

**Data-driven transition rules:**
1. After each pipeline run, update evidence_count and fire_rate for every evaluated check.
2. Check if any auto-transitions are triggered.
3. Auto-transitions generate brain_proposals (not immediate YAML edits).
4. Human reviews and approves lifecycle changes.
5. `brain build` respects lifecycle.state: deprecated checks are excluded from brain_checks_active view.

**Key design decisions:**
1. Lifecycle lives in brain YAML as the source of truth (not in knowledge.db SQLite).
2. The existing SQLite lifecycle (knowledge/lifecycle.py) is NOT modified or deprecated yet -- it can coexist. v1.3 can unify.
3. Auto-transitions always produce PROPOSALS, never direct mutations. Human stays in the loop.
4. The `display.deprecation_note` field already exists in BrainCheckEntry -- reuse it rather than duplicating.
5. fire_rate and evidence_count come from brain_check_runs (DuckDB), computed by brain_effectiveness.py.

---

### Feature 6: CI Guardrails

**What:** Automated tests that catch brain consistency regressions.

**Existing foundation:**
- No .github/workflows/ directory exists yet
- Tests run via `pytest` (3,967+ tests passing)
- `knowledge/gap_detector.py` -- detect_gaps() provides programmatic gap analysis
- `brain/brain_build_checks.py` -- build_checks_from_yaml() validates YAML during build
- `brain/brain_check_schema.py` -- BrainCheckEntry Pydantic validates at load time

**Integration approach: NEW test files, leverage existing validators**

```
NEW FILES:
  tests/brain/test_brain_consistency.py    -- CI-safe brain checks
  tests/brain/test_brain_data_routes.py    -- Every check has a data route
  tests/brain/test_brain_yaml_schema.py    -- YAML validates against Pydantic schema
  tests/brain/test_brain_lifecycle.py      -- Lifecycle state consistency

MODIFIED: None (tests are additive)
```

**CI guardrail checks:**
1. **Schema compliance**: Every YAML check validates against BrainCheckEntry Pydantic model (already happens at build time -- test formalizes it)
2. **Data route completeness**: Every AUTO check has data_strategy.field_key OR FIELD_FOR_CHECK entry OR Phase 26+ mapper
3. **No orphaned checks**: Every check_id in DuckDB has a corresponding YAML source file
4. **Threshold completeness**: Every evaluative check has threshold with at least type + one level (red or triggered)
5. **Factor coverage**: Every scoring factor (F1-F10) has at least 5 checks contributing to it
6. **New check guard**: If a new check_id is added to YAML without data_strategy.field_key, the test fails (prevents adding a check that can never evaluate)
7. **Lifecycle consistency**: No ACTIVE check without required_data. No DEPRECATED check still contributing to scoring factors.

**Key design decisions:**
1. All CI tests are fast (< 10 seconds). They read YAML and brain.duckdb, no network calls.
2. Tests use `brain build` programmatically to ensure YAML -> DuckDB consistency.
3. No GitHub Actions yet (no .github/workflows/ exists). Tests run locally via `pytest`.
4. Future: when GitHub Actions are added, these tests become the brain consistency gate.

---

## Component Boundary Map

### What Gets Modified vs. Created

**MODIFIED files (changes < 30 lines each):**

| File | Change | Lines |
|------|--------|-------|
| `cli_brain.py` | Add `brain diagnostics` and `brain audit` commands | ~30 |
| `cli_feedback.py` | Add `feedback process` and `feedback report` commands | ~30 |
| `cli_ingest.py` | Add `ingest event` command | ~20 |
| `brain/brain_check_schema.py` | Add lifecycle fields to BrainCheckEntry | ~10 |
| `brain/brain_build_checks.py` | Read lifecycle fields from YAML during build | ~15 |
| `brain/brain_schema.py` | Add brain_events table DDL | ~20 |
| `validation/qa_report.py` | Import + call brain QA check category | ~5 |
| `pipeline.py` | Optional post-run diagnostics hook | ~10 |

Total: ~140 lines of modifications across 8 existing files.

**NEW files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `diagnostics/__init__.py` | Package init | ~5 |
| `diagnostics/health_monitor.py` | Aggregate health score | ~200 |
| `diagnostics/data_route_verifier.py` | End-to-end route verification | ~250 |
| `diagnostics/coverage_dashboard.py` | Rich CLI coverage metrics | ~200 |
| `diagnostics/report.py` | DiagnosticsReport Pydantic model | ~80 |
| `validation/brain_audit.py` | Brain consistency audit | ~300 |
| `validation/qa_checks_brain.py` | Brain QA check functions | ~150 |
| `validation/regression.py` | Regression baselines | ~150 |
| `knowledge/feedback_processor.py` | Batch feedback processing | ~300 |
| `knowledge/feedback_report.py` | Feedback impact report | ~200 |
| `knowledge/event_types.py` | Event type definitions | ~100 |
| `knowledge/event_ingestion.py` | Event -> brain impact mapping | ~300 |
| `knowledge/event_store.py` | Event storage in DuckDB | ~150 |
| `brain/signal_lifecycle.py` | Signal state machine | ~250 |
| `brain/signal_lifecycle_rules.py` | Auto-transition rules | ~200 |
| `tests/brain/test_brain_consistency.py` | CI consistency tests | ~250 |
| `tests/brain/test_brain_data_routes.py` | Data route tests | ~200 |
| `tests/brain/test_brain_yaml_schema.py` | YAML schema tests | ~150 |
| `tests/brain/test_brain_lifecycle.py` | Lifecycle state tests | ~150 |

Total: ~3,585 lines of new code across 19 new files.

---

## Architecture Constraints (Enforced)

### Constraint 1: No AnalysisState Changes
v1.2 features are OPERATIONAL INTELLIGENCE, not pipeline data. They read from brain.duckdb and pipeline artifacts but do not modify the AnalysisState model or the 7-stage pipeline data flow.

Exception: The post-run diagnostics hook in pipeline.py runs AFTER all 7 stages complete and state is saved. It does not write to AnalysisState.

### Constraint 2: 500-Line Limit
Every new file stays under 500 lines. Split aggressively:
- `diagnostics/` is a new package (not shoved into existing files)
- `validation/brain_audit.py` and `validation/qa_checks_brain.py` are separate (not merged into qa_report.py)
- `knowledge/feedback_processor.py` is separate from `knowledge/feedback.py` (which is at 426 lines)

### Constraint 3: Brain YAML Remains Source of Truth
- New lifecycle fields go IN the YAML files
- DuckDB is rebuilt from YAML via `brain build`
- No feature writes directly to DuckDB without corresponding YAML update (except brain_events which is operational metadata, not check knowledge)

### Constraint 4: Stage Boundaries
- Diagnostics never runs DURING a pipeline stage
- Feedback processing never modifies in-flight pipeline state
- Knowledge ingestion writes to brain_proposals, never directly to brain YAML (human review required)

### Constraint 5: Human in the Loop
Every auto-generated change goes through brain_proposals:
- Feedback -> proposal -> human approve -> brain YAML edit -> brain build
- Event ingestion -> proposal -> human approve -> brain YAML edit -> brain build
- Lifecycle auto-transition -> proposal -> human approve -> brain YAML edit -> brain build

---

## Data Flow: How Features Interact

```
                    PIPELINE (unchanged)
                    ===================
                    RESOLVE -> ACQUIRE -> EXTRACT -> ANALYZE -> SCORE -> BENCHMARK -> RENDER
                                                      |
                                                      v
                                              brain_check_runs
                                              (per-check results)
                                                      |
                    ┌─────────────────────────────────┤
                    |                                  |
                    v                                  v
            DIAGNOSTICS (read-only)         EFFECTIVENESS (read-only)
            health_monitor.py               brain_effectiveness.py
            data_route_verifier.py                |
            coverage_dashboard.py                 |
                                                  v
                                          SIGNAL LIFECYCLE
                                          signal_lifecycle_rules.py
                                                  |
                                                  v
                                          brain_proposals
                                          (lifecycle transitions)
                                                  |
                    ┌─────────────────────────────────┤
                    |                                  |
                    v                                  v
            FEEDBACK PROCESSOR              KNOWLEDGE INGESTION
            feedback_processor.py           event_ingestion.py
                    |                                  |
                    v                                  v
            brain_proposals                 brain_proposals
            (threshold changes)             (event-driven changes)
                    |                                  |
                    └──────────────┬───────────────────┘
                                   |
                                   v
                           HUMAN REVIEW
                           do-uw feedback report
                           do-uw feedback apply <id>
                                   |
                                   v
                           brain/checks/**/*.yaml
                           (source of truth updated)
                                   |
                                   v
                           brain build
                           (YAML -> DuckDB rebuild)
                                   |
                                   v
                           CI GUARDRAILS
                           pytest tests/brain/
                           (validates consistency)
```

---

## DuckDB Schema Additions

### New Table: brain_events

```sql
CREATE TABLE IF NOT EXISTS brain_events (
    event_id INTEGER PRIMARY KEY DEFAULT nextval('event_seq'),
    event_type VARCHAR NOT NULL,     -- SEC_ENFORCEMENT, REGULATORY_CHANGE, etc.
    event_date DATE,                 -- When the event occurred
    source_url VARCHAR,              -- Where we learned about it
    source_name VARCHAR,             -- Publication/source name
    summary TEXT NOT NULL,           -- Human-readable summary
    affected_tickers VARCHAR[],      -- Specific companies affected
    affected_industries VARCHAR[],   -- Industries affected
    affected_perils VARCHAR[],       -- Peril IDs impacted
    affected_checks VARCHAR[],       -- Specific check IDs impacted
    proposals_generated INTEGER DEFAULT 0,
    ingested_by VARCHAR NOT NULL DEFAULT 'system',
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);
```

### Modified Views: brain_checks_active

The existing view filters lifecycle_state NOT IN ('RETIRED', 'INCUBATING', 'INACTIVE'). When lifecycle fields are added to YAML, the view logic should also respect `lifecycle.state = 'deprecated'` for the new signal lifecycle system.

No DDL change needed initially -- the existing lifecycle_state column already drives visibility. The new YAML lifecycle fields are informational until a later phase migrates all checks to the new system.

---

## Build Order and Dependencies

### Dependency Graph

```
CI Guardrails -------> [no dependencies, can start immediately]
                       (reads YAML + DuckDB, no new tables)

Pipeline Diagnostics -> [no dependencies, can start immediately]
                       (reads brain.duckdb, gap_detector, pipeline_audit)

Automated QA --------> [no dependencies, can start immediately]
                       (reads brain.duckdb, extends qa_report)

Underwriter Feedback -> [depends on: nothing new, existing infrastructure]
                       (adds feedback processing to existing CLI)

Signal Lifecycle -----> [depends on: brain YAML field additions]
                       (needs lifecycle fields in YAML before rules can act)

Knowledge Ingestion --> [depends on: brain_events DuckDB table]
                       (needs event storage before ingestion pipeline)
```

### Recommended Build Order

**Phase 1: Foundation (no dependencies)**
1. CI Guardrails -- tests catch regressions from day one
2. Pipeline Diagnostics -- visibility into current system health
3. Automated QA (brain audit) -- baseline brain consistency checks

**Phase 2: Feedback & Lifecycle (lightweight dependencies)**
4. Underwriter Feedback CLI enhancement -- process + report commands
5. Signal Lifecycle -- YAML field additions + state machine

**Phase 3: Intelligence (depends on Phase 2)**
6. Knowledge Ingestion -- event types + brain_events table + ingestion pipeline

**Rationale for this order:**
- Phase 1 items have zero dependencies and provide immediate value for validating subsequent phases
- CI guardrails catch regressions from Phase 2+ changes
- Diagnostics provides baseline metrics to measure improvement
- Signal lifecycle must exist before knowledge ingestion can drive lifecycle transitions
- Feedback processing must exist before lifecycle rules can consume feedback signal

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Merging Diagnostics into Pipeline
**What:** Adding diagnostic checks inside pipeline stages.
**Why bad:** Diagnostics that fail should not abort the pipeline. Mixing concerns makes the pipeline fragile and harder to maintain.
**Instead:** Diagnostics is a separate read-only observer that runs after pipeline completion or on-demand via CLI.

### Anti-Pattern 2: Direct YAML Mutation from Code
**What:** Having feedback_processor.py or event_ingestion.py directly edit brain YAML files.
**Why bad:** YAML editing is error-prone (formatting, ordering, comment preservation). Multiple writers cause conflicts.
**Instead:** All changes go through brain_proposals -> human review -> explicit apply command that uses brain_writer.py.

### Anti-Pattern 3: Second State Model for Diagnostics
**What:** Creating a DiagnosticsState Pydantic model that parallels AnalysisState.
**Why bad:** Violates "single source of truth" principle. Creates maintenance burden.
**Instead:** Diagnostics produces a DiagnosticsReport (read-only snapshot). It reads from brain.duckdb, never writes to a state model.

### Anti-Pattern 4: Lifecycle in DuckDB Only
**What:** Storing lifecycle state only in brain.duckdb, not in YAML.
**Why bad:** YAML is the source of truth. DuckDB is a cache. If lifecycle lives only in DuckDB, `brain build` would lose lifecycle information.
**Instead:** Lifecycle fields in YAML, rebuilt to DuckDB via `brain build`.

### Anti-Pattern 5: Over-Automating Signal Transitions
**What:** Auto-transitioning lifecycle states without human review.
**Why bad:** A check might appear "always-fire" because the validation set only includes companies where it should fire. Auto-deprecation could remove valuable checks.
**Instead:** Auto-transitions generate proposals. Human reviews with context before approving.

### Anti-Pattern 6: Unifying knowledge.db and brain.duckdb Prematurely
**What:** Migrating all knowledge.db data into brain.duckdb in v1.2.
**Why bad:** The two databases serve different purposes. knowledge.db is the ORM-based knowledge store. brain.duckdb is the YAML-derived query cache. Merging them requires careful migration and testing.
**Instead:** Let them coexist. New features use brain.duckdb. Unification can happen in v1.3 when the full scope is understood.

---

## Scalability Considerations

| Concern | Current (v1.1) | At 50 tickers | At 500 tickers |
|---------|---------------|---------------|----------------|
| brain_check_runs rows | ~1,600 (4 tickers * 400 checks) | ~20,000 | ~200,000 |
| brain_feedback rows | < 10 | ~200 | ~2,000 |
| brain_events rows | 0 | ~50 | ~500 |
| Effectiveness computation | < 1 second | < 5 seconds | < 30 seconds |
| Brain audit | < 2 seconds | < 2 seconds (brain-only) | < 2 seconds |
| CI guardrail tests | < 5 seconds | < 5 seconds (no ticker dependency) | < 5 seconds |

DuckDB handles analytical queries on 200K+ rows effortlessly. No scaling concerns for v1.2.

---

## Sources

- All findings derived from direct source code audit of the following files:
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/pipeline.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/models/state.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/brain/brain_schema.py` (19 tables, 11 views)
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/brain/brain_check_schema.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/brain/brain_effectiveness.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/brain/brain_build_checks.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/brain/brain_loader.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/knowledge/lifecycle.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/knowledge/feedback.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/knowledge/gap_detector.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/knowledge/ingestion_llm.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/stages/analyze/__init__.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/stages/analyze/pipeline_audit.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/stages/analyze/check_engine.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/validation/qa_report.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/cli.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/cli_brain.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/cli_feedback.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/cli_ingest.py`
  - `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/brain/brain_facet_schema.py`
  - 36 brain YAML check files across 8 domains
- Confidence: HIGH -- all claims verified against actual source code
