# Technology Stack

**Project:** D&O Liability Underwriting System -- v1.2 System Intelligence Additions
**Researched:** 2026-02-26
**Confidence:** HIGH -- all features implementable with minimal new dependencies; most require zero new libraries

---

## Scope of This Document

This document covers **only the technology decisions relevant to v1.2 System Intelligence features**. The v1.0/v1.1 baseline stack (Python 3.12, uv, Pydantic v2, httpx, anthropic+instructor, python-docx, Jinja2, matplotlib, yfinance, edgartools, Playwright, SQLAlchemy 2.0, DuckDB, PyYAML, Typer, Rich) is validated and unchanged.

The v1.2 features under scope:

1. **Pipeline integrity diagnostics** -- health monitoring, data flow traceability, coverage metrics
2. **Automated QA validation** -- post-run verification, periodic brain health audits
3. **Underwriter feedback CLI** -- `do-uw feedback <TICKER>` capture and ingestion
4. **Signal lifecycle management** -- formal INCUBATING->DEVELOPING->ACTIVE->DEPRECATED lifecycle
5. **Knowledge ingestion** -- market events, regulatory changes, case law analysis
6. **CI guardrails** -- pre-commit brain consistency checks, automated regression detection

---

## Executive Finding: One New Dev Dependency, Zero New Runtime Dependencies

The v1.2 System Intelligence features are implementable using the existing library stack for all runtime code. The sole new dependency is `pre-commit` (dev-only) for CI guardrails.

**Rationale:** The codebase already has every primitive needed:

| Feature Domain | Required Primitive | Existing Location |
|---|---|---|
| Pipeline diagnostics | DuckDB analytics + Pydantic models | `brain_effectiveness.py`, `pipeline_audit.py`, `brain_schema.py` |
| Automated QA | Post-pipeline check framework | `validation/qa_report.py`, `qa_report_generator.py` |
| Feedback CLI | Typer sub-app + DuckDB storage | `cli_feedback.py`, `knowledge/feedback.py`, `knowledge/feedback_models.py` |
| Signal lifecycle | State machine + history recording | `knowledge/lifecycle.py` (SQLite), `brain_schema.py` (DuckDB `lifecycle_state`) |
| Knowledge ingestion | LLM extraction + proposal pipeline | `cli_ingest.py`, `knowledge/ingestion_llm.py`, `knowledge/ingestion_models.py` |
| CI guardrails | Pydantic YAML validation + pytest | `brain_check_schema.py` (BrainCheckEntry), existing test infra |

---

## Recommended Stack

### Core Technologies (Unchanged from v1.0/v1.1)

| Technology | Version | Purpose | v1.2 Role |
|---|---|---|---|
| Python | 3.12+ | Runtime | Unchanged |
| Pydantic | >=2.10 | State/schema models | Diagnostics models, feedback models, lifecycle models |
| DuckDB | >=1.4.4 | Brain analytics cache | Pipeline run history, effectiveness metrics, feedback storage |
| Typer | >=0.15 | CLI framework | `brain health`, `brain audit`, `feedback` subcommands |
| Rich | >=13.0 | Terminal output | Diagnostic tables, progress bars, health dashboards |
| PyYAML | >=6.0 | YAML brain loading | Brain check validation, CI guardrail checks |
| Jinja2 | >=3.1.0 | Template rendering | Diagnostic report templates |
| anthropic+instructor | >=0.79.0 / >=1.14.0 | LLM structured extraction | Knowledge ingestion intelligence extraction |

### New Dev Dependency

| Technology | Version | Purpose | Why |
|---|---|---|---|
| pre-commit | >=4.0 | Git hook framework | CI guardrails: validate brain YAML on every commit |

**Why pre-commit:** The brain YAML files (400 checks across 36 files) are the single source of truth for the entire scoring pipeline. A malformed YAML check that passes `yaml.safe_load()` but fails `BrainCheckEntry.model_validate()` would silently break the pipeline at runtime. Pre-commit catches this at commit time with zero CI infrastructure needed. The project already uses `ruff` for linting -- pre-commit unifies all pre-commit validation into one framework.

**Why NOT a full CI pipeline (GitHub Actions):** The project runs locally with `uv` and has no remote CI. Pre-commit gives equivalent protection with zero cloud infrastructure. If GitHub Actions is added later, pre-commit hooks translate directly to CI steps.

### No New Runtime Libraries Needed

The following analysis explains why each v1.2 feature requires zero new runtime dependencies.

---

## Feature-by-Feature Stack Analysis

### 1. Pipeline Integrity Diagnostics

**What exists today:**
- `pipeline_audit.py` -- audits check data pipeline status (HAS_DATA / NO_MAPPER / ALL_NONE)
- `brain_effectiveness.py` -- computes fire rates, classifies always-fire/never-fire/high-skip
- `brain_check_runs` DuckDB table -- stores per-check results for every pipeline run
- `brain_effectiveness` DuckDB table -- aggregated effectiveness metrics
- `brain_check_effectiveness` DuckDB view -- live-computed from `brain_check_runs`
- `cli_brain.py` -- `brain status`, `brain gaps`, `brain effectiveness` commands

**What v1.2 adds:**
- Diagnostics dashboard (coverage metrics, data routing health)
- Data flow traceability (source->extract->analyze->score path per check)
- Pipeline run comparison (diff two runs to detect regressions)

**Stack decision: Pure DuckDB analytics + Pydantic models + Rich CLI output**

No new library needed. The diagnostic queries run against the existing `brain_check_runs` and `brain_effectiveness` tables. New DuckDB views can compute run-over-run deltas, data source coverage matrices, and routing completeness metrics. Rich already provides the table rendering.

```python
# Pattern: New DuckDB view for pipeline health metrics
CREATE OR REPLACE VIEW brain_pipeline_health AS
SELECT
    run_id,
    ticker,
    COUNT(*) as total_checks,
    SUM(CASE WHEN status = 'TRIGGERED' THEN 1 ELSE 0 END) as triggered,
    SUM(CASE WHEN status = 'SKIPPED' THEN 1 ELSE 0 END) as skipped,
    ROUND(skipped * 100.0 / total_checks, 1) as skip_rate_pct,
    MIN(run_date) as run_date
FROM brain_check_runs
WHERE is_backtest = FALSE
GROUP BY run_id, ticker;
```

**Confidence:** HIGH -- extending existing DuckDB analytics pattern used throughout the brain module.

### 2. Automated QA Validation

**What exists today:**
- `validation/qa_report.py` -- post-pipeline QA with 5 check categories (Output, Data, Coverage, Evidence, Analysis)
- `validation/runner.py` -- multi-ticker validation batch runner
- `validation/config.py` -- canonical ticker set for validation
- Post-pipeline QA runs automatically in `cli.py` after `pipeline.run()` completes

**What v1.2 adds:**
- Periodic brain health audits (not tied to a pipeline run)
- Brain consistency checks (orphaned references, schema drift)
- Regression detection across runs

**Stack decision: Extend existing QA framework, add `brain audit` CLI command**

The `qa_report.py` pattern (category-based checks returning QACheck objects with PASS/WARN/FAIL) directly extends to brain audits. Add a `brain_audit.py` module that runs checks like:
- Every active check has a data_strategy with a valid field_key
- Every referenced factor_id exists in brain_scoring_factors
- No orphaned peril_id references
- Check version numbers are monotonically increasing
- Threshold types match threshold field population

This is pure Python + DuckDB queries + Pydantic validation. No new library.

**Confidence:** HIGH -- direct extension of existing QACheck/QAReport pattern.

### 3. Underwriter Feedback CLI

**What exists today (already built in v1.0):**
- `cli_feedback.py` -- `feedback add`, `feedback summary`, `feedback list` commands
- `knowledge/feedback.py` -- `record_feedback()`, `get_feedback_summary()`, auto-proposal generation
- `knowledge/feedback_models.py` -- `FeedbackEntry`, `ProposalRecord`, `FeedbackSummary` Pydantic models
- `brain_feedback` DuckDB table -- stores feedback entries
- `brain_proposals` DuckDB table -- stores proposed changes
- Auto-proposal: MISSING_COVERAGE feedback auto-generates INCUBATING checks

**What v1.2 adds:**
- Interactive `do-uw feedback TICKER` mode that loads the most recent run and walks through findings
- Batch feedback from CSV/JSON for bulk import
- Feedback-to-threshold-change pipeline (auto-propose threshold adjustments from FALSE_POSITIVE/FALSE_NEGATIVE patterns)

**Stack decision: Extend existing Typer CLI with Rich prompts**

Typer already supports interactive prompting via `typer.prompt()` and Rich provides styled output. The interactive feedback mode loads state from the output directory (pattern already in `cli_dashboard.py`), presents findings, and collects reactions. No new library.

For bulk import: Python stdlib `csv` module + `json` module handle CSV/JSON input. The feedback recording path (`record_feedback()`) is already batch-capable.

For threshold auto-tuning: DuckDB analytics on `brain_feedback` table (`SELECT check_id, direction, COUNT(*) FROM brain_feedback WHERE feedback_type = 'ACCURACY' GROUP BY check_id, direction HAVING COUNT(*) >= 3`) identifies candidates. Pure SQL + existing proposal pipeline.

**Confidence:** HIGH -- feedback infrastructure is already 80% built; v1.2 is enhancement, not creation.

### 4. Signal Lifecycle Management

**What exists today:**
- `knowledge/lifecycle.py` -- `CheckStatus` enum (INCUBATING/DEVELOPING/ACTIVE/DEPRECATED), `VALID_TRANSITIONS` dict, `transition_check()` with history recording (SQLite via SQLAlchemy)
- `brain_checks.lifecycle_state` DuckDB column -- used by `brain_checks_active` view to filter
- `brain_changelog` DuckDB table -- records all check changes with timestamps
- `brain_checks_current` / `brain_checks_active` DuckDB views -- version-aware active check set

**What v1.2 adds:**
- Automated lifecycle transitions based on run data (high-skip -> deprecation candidate, consistent fire rate -> promotion candidate)
- Market intelligence-driven lifecycle (new regulatory action -> propose new INCUBATING check)
- Convergence of SQLite lifecycle tracking and DuckDB lifecycle_state into single DuckDB system

**Stack decision: Consolidate on DuckDB, retire SQLite lifecycle path**

The project currently has two parallel tracking systems (noted in `brain_effectiveness.py` docstring): SQLAlchemy/SQLite `knowledge.db` and DuckDB `brain.duckdb`. For v1.2, consolidate lifecycle management entirely into DuckDB:

1. `lifecycle.py` transitions rewritten to use DuckDB `brain_checks` + `brain_changelog` directly
2. `VALID_TRANSITIONS` dict remains (pure Python, no library needed)
3. History recording goes to `brain_changelog` (DuckDB) instead of SQLite `check_history`
4. Automated transitions driven by DuckDB analytics on `brain_effectiveness` metrics

This is a net reduction in dependencies (less SQLAlchemy usage for lifecycle, though SQLAlchemy remains for the knowledge store pricing tables).

**Confidence:** HIGH -- the DuckDB schema already supports lifecycle_state and changelog; this is migration from SQLite to DuckDB for one subsystem.

### 5. Knowledge Ingestion

**What exists today (already built in v1.0):**
- `cli_ingest.py` -- `ingest file <path>` and `ingest url <url>` commands
- `knowledge/ingestion_llm.py` -- `extract_document_intelligence()` via Claude Haiku 4.5 + instructor, `fetch_url_content()`, `store_proposals()`
- `knowledge/ingestion_models.py` -- `DocumentIngestionResult`, `IngestionImpactReport`, `ProposedCheck`
- `brain_proposals` DuckDB table -- stores ingestion proposals

**What v1.2 adds:**
- Specialized ingestion paths for case law, regulatory actions, claims studies
- Ingestion history tracking (what was ingested when, what proposals resulted)
- Automated periodic ingestion from known sources (SEC enforcement releases, SCAC database updates)
- Impact assessment that cross-references existing brain checks more deeply

**Stack decision: Extend existing LLM ingestion with specialized prompts and DuckDB tracking**

The ingestion pipeline is already functional. v1.2 enhancements are:

1. **Specialized system prompts** per document type (case law vs. regulatory action vs. claims study) -- pure string constants, no library
2. **Ingestion history table** in DuckDB -- new `brain_ingestion_log` table tracking URL/file, date, proposal count, confidence
3. **Deeper cross-referencing** of affected checks via DuckDB queries on `brain_checks` table -- look up checks by `peril_id`, `risk_questions`, `content_type` to find which existing checks an event might impact
4. **Periodic ingestion** -- for now, a CLI command `do-uw ingest scan-sources` that checks known URLs; no scheduler library needed (user runs manually or via system cron)

No new runtime library. The LLM client (anthropic + instructor) and HTTP client (httpx) already handle the heavy lifting.

**Why NOT add a scheduling library (APScheduler, celery, etc.):** The system is a CLI tool run by an underwriter, not a long-running service. Periodic ingestion is best triggered by system cron or manual invocation. Adding a scheduling library would require a daemon process that contradicts the CLI-first architecture.

**Confidence:** HIGH -- extending existing ingestion pipeline with specialized prompts and DuckDB tracking.

### 6. CI Guardrails

**What exists today:**
- `brain_check_schema.py` -- `BrainCheckEntry` Pydantic model validates all 400 checks at load time
- `brain_build_checks.py` -- `build_checks_from_yaml()` rebuilds DuckDB from YAML
- `cli_brain_yaml.py` -- `brain validate` command (validates YAML check files)
- `ruff` for code formatting/linting (dev dependency)
- `pytest` for testing (dev dependency)
- No pre-commit hooks currently configured

**What v1.2 adds:**
- Pre-commit hooks that validate brain YAML on every commit
- Automated detection of new checks without data routes
- Schema consistency checks (referenced IDs exist, no dangling references)

**Stack decision: Add `pre-commit` framework with custom Pydantic-based YAML validator hook**

The custom hook is a Python script that:
1. Loads all modified `brain/checks/**/*.yaml` files
2. Validates each entry against `BrainCheckEntry.model_validate()`
3. Checks that referenced `peril_id`, `factor_id`, `chain_id` values exist in the brain
4. Fails the commit if any validation error is found

Implementation pattern:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: local
    hooks:
      - id: brain-yaml-validate
        name: Validate brain YAML checks
        entry: python -m do_uw.brain.brain_validate_hook
        language: python
        files: 'src/do_uw/brain/checks/.*\.yaml$'
        types: [yaml]
```

The hook script (`brain_validate_hook.py`) is ~50 lines: load YAML, call `BrainCheckEntry.model_validate()`, report errors. This uses only existing dependencies (PyYAML + Pydantic).

**Why `pre-commit` framework instead of a raw git hook script:** Pre-commit handles hook installation, versioning, environment isolation, and skip patterns. Raw git hooks are fragile (not version-controlled, break across environments). Pre-commit is the standard in the Python ecosystem and integrates cleanly with `ruff` (the project's existing linter).

**Confidence:** HIGH -- pre-commit is a mature, well-documented framework; the custom hook is trivial given existing `BrainCheckEntry` validation.

---

## New DuckDB Tables and Views

v1.2 extends the brain DuckDB schema. No new database technology -- all within existing `brain.duckdb`.

| Table/View | Purpose | Feature |
|---|---|---|
| `brain_pipeline_health` (view) | Per-run health metrics (skip rate, trigger rate, coverage) | Diagnostics |
| `brain_run_comparison` (view) | Delta between two runs for regression detection | Diagnostics |
| `brain_audit_results` (table) | Periodic brain audit check results | Automated QA |
| `brain_ingestion_log` (table) | History of ingested documents with outcomes | Knowledge ingestion |
| `brain_lifecycle_transitions` (view) | Lifecycle state changes over time from changelog | Signal lifecycle |

Schema for new tables:

```sql
CREATE TABLE IF NOT EXISTS brain_audit_results (
    audit_id VARCHAR PRIMARY KEY,
    audit_type VARCHAR NOT NULL,  -- 'SCHEMA', 'CONSISTENCY', 'EFFECTIVENESS', 'COVERAGE'
    check_name VARCHAR NOT NULL,
    status VARCHAR NOT NULL,      -- 'PASS', 'WARN', 'FAIL'
    detail TEXT,
    run_date TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS brain_ingestion_log (
    ingestion_id INTEGER PRIMARY KEY,
    source_type VARCHAR NOT NULL,  -- 'FILE', 'URL', 'SCAN'
    source_ref VARCHAR NOT NULL,
    doc_type VARCHAR NOT NULL,
    ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    confidence VARCHAR NOT NULL,
    proposals_generated INTEGER NOT NULL DEFAULT 0,
    checks_affected INTEGER NOT NULL DEFAULT 0,
    event_type VARCHAR,
    event_summary TEXT
);
```

---

## Alternatives Considered

| Feature | Considered | Rejected | Why |
|---|---|---|---|
| Pipeline diagnostics | Grafana + Prometheus | Rejected | The system is a CLI tool, not a service; terminal-based Rich tables are sufficient |
| Pipeline diagnostics | structlog / loguru | Rejected | Python stdlib `logging` is already used consistently; switching logging frameworks mid-project creates two competing patterns |
| Automated QA | Great Expectations | Rejected | Massive dependency (200+ transitive deps) for data validation; existing QACheck pattern is simpler and sufficient |
| CI guardrails | GitHub Actions | Deferred | No remote CI currently; pre-commit covers the same validation locally |
| CI guardrails | yamllint | Considered but secondary | `yamllint` validates YAML syntax; the real risk is semantic validity (Pydantic schema), which `yamllint` cannot check; use both via pre-commit |
| Knowledge ingestion | LangChain for document processing | Rejected | 50+ transitive deps; httpx + instructor already handles the extraction pattern |
| Signal lifecycle | Apache Airflow for orchestration | Rejected | The system is single-user CLI; no DAG scheduler needed |
| Feedback CLI | questionary / InquirerPy | Rejected | Typer + Rich already provide prompting; adding another CLI library fragments the interaction model |
| Periodic tasks | APScheduler / Celery | Rejected | CLI-first architecture; system cron or manual invocation is appropriate for periodic tasks |
| Logging upgrade | structlog | Rejected | 400+ source files use stdlib logging; migration cost exceeds benefit; Rich already provides formatted console output |

---

## What NOT to Add

| Do Not Add | Why | Use Instead |
|---|---|---|
| `great-expectations` | 200+ transitive deps for data validation | Extend existing `QACheck`/`QAReport` pattern in `validation/` |
| `structlog` or `loguru` | 400+ files already use stdlib `logging`; migration cost outweighs benefit | Continue with `logging` module; Rich handles formatted output |
| `langchain` | Massive dependency for document processing; ingestion already works with instructor | Extend `ingestion_llm.py` with specialized prompts |
| `APScheduler` / `celery` | CLI-first tool, not a service | System cron or manual CLI invocation |
| `questionary` / `InquirerPy` | Interactive CLI prompting | `typer.prompt()` + Rich styled output |
| `grafana` / `prometheus` | Service monitoring for a CLI tool | Rich terminal tables and DuckDB analytics |
| `dbt-duckdb` | SQL transformation framework | Direct DuckDB SQL views (the transform logic is simple aggregations) |
| `alembic` for DuckDB | Migration framework for DuckDB schema | `brain_schema.py` already handles `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN IF NOT EXISTS` idempotently |
| `sqlmodel` | Pydantic-SQLAlchemy hybrid | Already have Pydantic models + raw DuckDB SQL; SQLModel would add confusion without value |

---

## Installation

### New Dev Dependency Only

```bash
# Add pre-commit as dev dependency
uv add --group dev pre-commit

# Install pre-commit hooks (one-time setup per clone)
uv run pre-commit install
```

### No Changes to Runtime Dependencies

The `pyproject.toml` `[project.dependencies]` section is unchanged. All v1.2 features use the existing runtime stack.

### Pre-commit Configuration

Create `.pre-commit-config.yaml` in project root:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-yaml
        exclude: '.venv/|node_modules/'
      - id: end-of-file-fixer
      - id: trailing-whitespace
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: local
    hooks:
      - id: brain-yaml-validate
        name: Validate brain YAML checks
        entry: uv run python -m do_uw.brain.brain_validate_hook
        language: system
        files: 'src/do_uw/brain/checks/.*\.yaml$'
        types: [yaml]
        pass_filenames: true
```

---

## Integration Points Summary

### Diagnostics (extends brain/ and validation/)

```
brain_effectiveness.py  -- existing fire rate / skip rate analytics
brain_schema.py         -- new views (brain_pipeline_health, brain_run_comparison)
pipeline_audit.py       -- existing data pipeline audit (NO_MAPPER / ALL_NONE / HAS_DATA)
cli_brain.py            -- new `brain health` command
validation/qa_report.py -- extend with brain health checks
```

### Automated QA (extends validation/)

```
validation/qa_report.py        -- extend QACheck categories for brain audits
validation/brain_audit.py      -- NEW: brain consistency checks (orphans, schema, references)
cli_brain.py or cli_validate.py -- new `brain audit` command
brain_schema.py                -- new brain_audit_results table
```

### Feedback CLI (extends knowledge/feedback/)

```
cli_feedback.py               -- extend with interactive mode, bulk import
knowledge/feedback.py          -- extend with threshold auto-tuning proposals
knowledge/feedback_models.py   -- extend FeedbackEntry with batch fields
```

### Signal Lifecycle (extends knowledge/lifecycle.py -> brain/)

```
knowledge/lifecycle.py         -- rewrite to use DuckDB instead of SQLAlchemy/SQLite
brain_schema.py                -- lifecycle views (brain_lifecycle_transitions)
brain_effectiveness.py         -- auto-transition logic based on metrics
cli_brain.py                   -- new `brain lifecycle` command
```

### Knowledge Ingestion (extends knowledge/ingestion/)

```
knowledge/ingestion_llm.py     -- specialized prompts per document type
brain_schema.py                -- brain_ingestion_log table
cli_ingest.py                  -- new `ingest scan-sources` command
```

### CI Guardrails (new in brain/)

```
brain/brain_validate_hook.py   -- NEW: pre-commit hook script
.pre-commit-config.yaml        -- NEW: pre-commit configuration
```

---

## Dual-Store Convergence Plan

The codebase currently has two overlapping data stores:

| Store | Technology | Contains | Used By |
|---|---|---|---|
| `brain.duckdb` | DuckDB | Checks, effectiveness, feedback, proposals, changelog | Brain CLI, pipeline, rendering |
| `knowledge.db` | SQLite via SQLAlchemy | Checks, check history, check runs, pricing, playbooks | Knowledge CLI, calibration |

**v1.2 recommendation:** Do NOT attempt full convergence in this milestone. Instead:

1. **Lifecycle management** moves from SQLite to DuckDB (small, well-bounded migration)
2. **Feedback** is already in DuckDB (no change)
3. **Pricing/playbooks** remain in SQLite (out of scope for v1.2; complex domain, deferred)
4. **Check runs** recording continues dual-write (both stores, as currently implemented)

Full convergence is a future milestone after v1.2 validates that DuckDB handles all system intelligence workloads.

---

## Version Compatibility

| Component | Current | Constraint | v1.2 Notes |
|---|---|---|---|
| Pydantic | >=2.10 | pyproject.toml | New diagnostic/audit models follow existing pattern |
| DuckDB | >=1.4.4 | pyproject.toml | New tables/views use standard SQL; no version-specific features |
| Typer | >=0.15 | pyproject.toml | New subcommands follow existing `brain_app.command()` pattern |
| Rich | >=13.0 | pyproject.toml | Table rendering for diagnostics; stable API |
| PyYAML | >=6.0 | pyproject.toml | YAML loading for brain validation; no version risk |
| pre-commit | >=4.0 | NEW dev dep | Framework for git hooks; Python 3.12 compatible |

---

## Sources

**Codebase audit (2026-02-26):**
- `src/do_uw/brain/brain_schema.py` -- 19 tables, 11 views, complete DuckDB schema including lifecycle_state, feedback, proposals, effectiveness, changelog
- `src/do_uw/brain/brain_effectiveness.py` -- fire rate analytics, effectiveness table management, check run recording
- `src/do_uw/brain/brain_check_schema.py` -- BrainCheckEntry Pydantic model (the validation schema for CI guardrails)
- `src/do_uw/stages/analyze/pipeline_audit.py` -- per-check data pipeline audit (HAS_DATA/NO_MAPPER/ALL_NONE)
- `src/do_uw/knowledge/lifecycle.py` -- CheckStatus state machine (INCUBATING->DEVELOPING->ACTIVE->DEPRECATED) with SQLite backend
- `src/do_uw/knowledge/feedback.py` -- feedback recording, auto-proposal, summary queries (DuckDB backend)
- `src/do_uw/knowledge/feedback_models.py` -- FeedbackEntry, ProposalRecord, FeedbackSummary Pydantic models
- `src/do_uw/knowledge/ingestion_llm.py` -- LLM-powered document ingestion with instructor + anthropic
- `src/do_uw/cli_feedback.py` -- feedback add/summary/list CLI commands (already functional)
- `src/do_uw/cli_ingest.py` -- ingest file/url CLI commands (already functional)
- `src/do_uw/cli_brain.py` -- brain status/gaps/effectiveness/build/changelog/backlog CLI
- `src/do_uw/cli_validate.py` -- multi-ticker validation runner
- `src/do_uw/validation/qa_report.py` -- post-pipeline QA verification (5 check categories)
- `pyproject.toml` -- current dependency list (33 runtime, 6 dev dependencies)

**External research:**
- [pre-commit framework](https://pre-commit.com/) -- git hook management framework
- [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) -- check-yaml and other built-in hooks
- [ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit) -- ruff integration with pre-commit
- [Pydantic YAML validation pattern](https://www.sarahglasmacher.com/how-to-validate-config-yaml-pydantic/) -- Pydantic model_validate() on yaml.safe_load() output
- [DuckDB Python analytics](https://deepnote.com/blog/ultimate-guide-to-duckdb-library-in-python) -- DuckDB analytics patterns

---

*Stack research for: D&O Underwriting Worksheet System v1.2 System Intelligence*
*Researched: 2026-02-26*
*Scope: New technology decisions only -- v1.0/v1.1 baseline stack is validated and unchanged*
