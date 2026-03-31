# Codebase Structure

**Analysis Date:** 2026-02-25

## Directory Layout

```
do-uw/
├── src/do_uw/                      # Main package (installed as "angry-dolphin")
│   ├── cli.py                      # Main CLI entry point (analyze command + sub-apps)
│   ├── cli_brain*.py               # Brain sub-commands (5 files)
│   ├── cli_calibrate.py            # Calibration sub-commands
│   ├── cli_dashboard.py            # Dashboard sub-commands
│   ├── cli_feedback.py             # Feedback sub-commands
│   ├── cli_ingest.py               # Knowledge ingestion sub-commands
│   ├── cli_knowledge*.py           # Knowledge sub-commands (3 files)
│   ├── cli_pricing*.py             # Pricing sub-commands (2 files)
│   ├── cli_validate.py             # Validation sub-commands
│   ├── pipeline.py                 # Pipeline orchestrator (7-stage runner)
│   ├── models/                     # Pydantic v2 domain models
│   ├── stages/                     # 7 pipeline stage implementations
│   ├── brain/                      # DuckDB knowledge store (checks, scoring, patterns)
│   ├── knowledge/                  # SQLite knowledge store + playbooks + pricing
│   ├── cache/                      # SQLite TTL cache for API calls
│   ├── config/                     # JSON config loader
│   ├── calibration/                # Check calibration analysis tools
│   ├── dashboard/                  # FastAPI/Plotly interactive dashboard
│   ├── validation/                 # Post-pipeline QA and batch validation
│   ├── templates/                  # Jinja2 templates (HTML, Markdown, PDF)
│   ├── static/                     # CSS and JS assets for HTML output
│   ├── assets/                     # Static binary assets (fonts, logos)
│   └── scripts/                    # One-off data enrichment scripts
├── tests/                          # Test suite mirroring src/ structure
├── config/                         # Project-level config (quality_checklist.json)
├── output/                         # Pipeline output (gitignored except structure)
│   └── {TICKER}-{DATE}/            # Per-run output directory
│       ├── state.json              # Serialized AnalysisState (resume point)
│       ├── {TICKER}_worksheet.html # Primary output (HTML)
│       ├── {TICKER}_worksheet.docx # Word document
│       ├── {TICKER}_worksheet.pdf  # PDF
│       ├── {TICKER}_worksheet.md   # Markdown
│       ├── charts/                 # Generated chart images
│       └── sources/filings/        # Cached filing text files
├── .cache/                         # Runtime caches (gitignored)
│   ├── analysis.db                 # SQLite API response cache (7-day TTL)
│   └── llm_extractions.db          # LLM extraction cache
├── .planning/                      # Planning documents and phase tracking
│   ├── PROJECT.md                  # Project definition
│   ├── REQUIREMENTS.md             # 111 v1 requirements
│   ├── ROADMAP.md                  # 8-phase roadmap
│   ├── STATE.md                    # Current phase/progress tracker
│   ├── phases/                     # Per-phase plans (44 phases so far)
│   ├── codebase/                   # Codebase analysis documents (this dir)
│   └── research/                   # Research notes
├── knowledge_docs/                 # Raw domain knowledge documents for ingestion
├── Examples/                       # Reference underwriter examples
├── pyproject.toml                  # Project metadata, dependencies, tool config
└── uv.lock                         # Locked dependency versions
```

## Directory Purposes

**`src/do_uw/models/`:**
- Purpose: All Pydantic v2 domain models
- Contains: One file per domain area
- Key files:
  - `state.py` — `AnalysisState` (THE state), `AcquiredData`, `ExtractedData`, `AnalysisResults`, `PIPELINE_STAGES`
  - `common.py` — `SourcedValue[T]`, `Confidence`, `StageStatus`, `StageResult`, `DataFreshness`
  - `company.py` — `CompanyProfile`, `CompanyIdentity`
  - `financials.py` — `ExtractedFinancials`, `FinancialStatements`, distress/liquidity/leverage models
  - `market.py` — `MarketSignals`, stock drop models
  - `governance.py` — `GovernanceData`, board/compensation models
  - `litigation.py` — `LitigationLandscape`, SCA/enforcement models
  - `scoring.py` — `ScoringResult`, `BenchmarkResult`, `FactorScore`, `PatternMatch`, `Tier`
  - `hazard_profile.py` — `HazardProfile` (IES + 7 dimensions)
  - `classification.py` — `ClassificationResult` (Layer 1)

**`src/do_uw/stages/`:**
- Purpose: The 7 pipeline stage implementations
- Contains: One sub-directory per stage, each with `__init__.py` exporting the stage class
- Key directories:
  - `resolve/` — `ResolveStage`, `ticker_resolver.py`, `sec_identity.py`
  - `acquire/` — `AcquireStage`, `orchestrator.py`, `gates.py`, `fallback.py`, `brain_requirements.py`, `rate_limiter.py`
  - `acquire/clients/` — `sec_client.py`, `market_client.py`, `litigation_client.py`, `news_client.py`, `web_search.py`, `serper_client.py`, `filing_fetcher.py`, `filing_text.py`
  - `extract/` — `ExtractStage` plus ~40 extractor modules, `llm/` sub-package
  - `extract/llm/` — LLM extraction engine: `extractor.py`, `prompts.py`, `cache.py`, `cost_tracker.py`, `boilerplate.py`, `prompt_enhancer.py`, `schemas/`
  - `extract/llm/schemas/` — Filing-specific Pydantic output schemas: `ten_k.py`, `ten_q.py`, `def14a.py`, `eight_k.py`, `capital_filing.py`, `ownership_filing.py`
  - `analyze/` — `AnalyzeStage`, `check_engine.py`, `check_evaluators.py`, `check_mappers*.py`, `check_results.py`, analytical engines
  - `analyze/layers/classify/` — Layer 1 classification: `classification_engine.py`, `severity_bands.py`
  - `analyze/layers/hazard/` — Layer 2 hazard profile: `hazard_engine.py`, `dimension_h1_business.py` through `dimension_h7_emerging.py`, `interaction_effects.py`, `data_mapping*.py`
  - `score/` — `ScoreStage`, `factor_scoring.py`, `factor_rules.py`, `factor_data.py`, `pattern_detection.py`, `red_flag_gates*.py`, `allegation_mapping.py`, `peril_mapping.py`, `bear_case_builder.py`, `settlement_prediction.py`, `severity_model.py`, `tier_classification.py`, `frequency_model.py`, `actuarial_model.py`, `actuarial_pricing_builder.py`, `ai_risk_scoring.py`
  - `benchmark/` — `BenchmarkStage`, `peer_metrics.py`, `percentile_engine.py`, `inherent_risk.py`, `summary_builder.py`, `narrative_generator.py`, `benchmark_enrichments.py`
  - `render/` — `RenderStage`, `html_renderer.py`, `word_renderer.py`, `md_renderer.py`, `pdf_renderer.py`, `design_system.py`, formatters, chart generators
  - `render/sections/` — HTML section renderers: `sect1_*.py` (executive), `sect2_*.py` (company), `sect3_*.py` (financial), `sect4_*.py` (market), `sect5_*.py` (governance), `sect6_*.py` (litigation), `sect7_*.py` (scoring), `sect8_ai_risk.py`
  - `render/charts/` — `stock_charts.py`, `radar_chart.py`, `ownership_chart.py`, `timeline_chart.py`

**`src/do_uw/brain/`:**
- Purpose: D&O underwriting knowledge stored in DuckDB (19 tables, 11 views)
- Contains:
  - `brain.duckdb` — Runtime DuckDB database (rebuilt from YAML via `angry-dolphin brain build`)
  - `checks.json` — All 359 checks compiled (engine source)
  - `scoring.json`, `patterns.json`, `red_flags.json`, `sectors.json` — Scoring config
  - `brain_schema.py` — DuckDB DDL schema
  - `brain_loader.py` — `BrainDBLoader` (primary query API)
  - `brain_migrate.py` — Migrates YAML checks → brain.duckdb
  - `brain_migrate_yaml.py`, `brain_migrate_config.py`, `brain_migrate_framework.py`, `brain_migrate_scoring.py` — Migration sub-modules
  - `brain_effectiveness.py` — Check run recording + effectiveness analysis
  - `brain_writer.py`, `brain_writer_export.py` — Write/export brain data
  - `brain_enrich.py`, `enrichment_data.py`, `enrichment_data_ext.py` — Knowledge enrichment
  - `brain_config_loader.py` — Load JSON config files from brain dir
  - `brain_build_checks.py` — Build checks.json from YAML sources
  - `checks/` — YAML check definitions organized by category:
    - `biz/` — Business risk: `competitive.yaml`, `core.yaml`, `dependencies.yaml`, `model.yaml`
    - `exec/` — Executive risk: `activity.yaml`, `profile.yaml`, `insider.yaml`, `ownership.yaml`, `pattern.yaml`
    - `fin/` — Financial: `accounting.yaml`, `balance.yaml`, `forensic.yaml`, `income.yaml`, `temporal.yaml`
    - `fwrd/` — Forward-looking: `guidance.yaml`, `ma.yaml`, `transform.yaml`, `warn_ops.yaml`, `warn_sentiment.yaml`, `warn_tech.yaml`
    - `gov/` — Governance: `activist.yaml`, `board.yaml`, `effect.yaml`, `exec_comp.yaml`, `insider.yaml`, `pay.yaml`, `rights.yaml`
    - `lit/` — Litigation: `defense.yaml`, `other.yaml`, `reg_agency.yaml`, `reg_sec.yaml`, `sca_history.yaml`, `sca.yaml`
    - `nlp/` — NLP signals: `nlp.yaml`
    - `stock/` — Stock/market: `price.yaml`, `short.yaml`

**`src/do_uw/knowledge/`:**
- Purpose: SQLite knowledge store (fallback when brain.duckdb unavailable), playbooks, pricing
- Contains:
  - `knowledge.db` — SQLite database with FTS5
  - `store.py` — `KnowledgeStore` query API
  - `models.py` — SQLAlchemy ORM models
  - `compat_loader.py` — `BackwardCompatLoader` (brain.duckdb primary, KnowledgeStore fallback)
  - `playbooks.py`, `playbook_data*.py` — Industry-specific check overlays
  - `pricing_store.py`, `pricing_models.py` — Insurance pricing data
  - `migrations/` — Alembic migration versions (001-006)
  - `feedback.py`, `learning.py`, `lifecycle.py` — Knowledge feedback loop
  - `ingestion.py`, `ingestion_llm.py` — Document ingestion pipeline

**`src/do_uw/templates/`:**
- Purpose: Jinja2 output templates
- Contains:
  - `html/` — HTML worksheet templates: `worksheet.html.j2`, section partials (`sections/*.html.j2`), `components/`, `appendices/`
  - `markdown/` — Markdown templates: `sections/*.md.j2`
  - `pdf/` — PDF-specific templates
  - `dashboard/` — Dashboard HTML templates with partials

**`src/do_uw/calibration/`:**
- Purpose: Check calibration analysis tools
- Contains: `runner.py`, `analyzer.py`, `impact_ranker.py`, `config.py`

**`src/do_uw/validation/`:**
- Purpose: Post-pipeline output quality assertions and batch testing
- Contains: `qa_report.py`, `runner.py`, `report.py`, `batch.py`, `cost_report.py`, `config.py`

**`tests/`:**
- Purpose: Mirrors `src/` structure
- Contains: `tests/stages/` (acquire, analyze, benchmark, extract, render, score), `tests/brain/`, `tests/knowledge/`, `tests/models/`, `tests/render/`, `tests/config/`, `tests/ground_truth/`

## Key File Locations

**Entry Points:**
- `src/do_uw/cli.py` — Primary CLI entry point, `analyze` command
- `src/do_uw/pipeline.py` — `Pipeline` class, sequential stage runner
- `src/do_uw/dashboard/app.py` — FastAPI dashboard server

**State / Models:**
- `src/do_uw/models/state.py` — `AnalysisState`, `AcquiredData`, `ExtractedData`, `AnalysisResults`, `PIPELINE_STAGES`
- `src/do_uw/models/common.py` — `SourcedValue[T]`, `Confidence`, `StageStatus`

**Stage Orchestrators (entry for each stage):**
- `src/do_uw/stages/resolve/__init__.py` — `ResolveStage`
- `src/do_uw/stages/acquire/__init__.py` — `AcquireStage`
- `src/do_uw/stages/extract/__init__.py` — `ExtractStage`
- `src/do_uw/stages/analyze/__init__.py` — `AnalyzeStage`
- `src/do_uw/stages/score/__init__.py` — `ScoreStage`
- `src/do_uw/stages/benchmark/__init__.py` — `BenchmarkStage`
- `src/do_uw/stages/render/__init__.py` — `RenderStage`

**Brain Knowledge:**
- `src/do_uw/brain/brain.duckdb` — Runtime DuckDB (single source of truth for checks/scoring)
- `src/do_uw/brain/checks.json` — Compiled checks (engine source, ~359 checks)
- `src/do_uw/brain/brain_schema.py` — DuckDB DDL (19 tables, 11 views)
- `src/do_uw/brain/brain_loader.py` — `BrainDBLoader` (primary query API)
- `src/do_uw/knowledge/compat_loader.py` — `BackwardCompatLoader` (unified access)

**Configuration:**
- `src/do_uw/brain/scoring.json` — 10-factor scoring weights and thresholds
- `src/do_uw/brain/patterns.json` — Composite pattern definitions
- `src/do_uw/brain/red_flags.json` — Critical red flag gates (CRF)
- `src/do_uw/brain/sectors.json` — Sector baseline filing rates
- `config/quality_checklist.json` — QA checklist items
- `pyproject.toml` — Package metadata, tool config (pyright, pytest, ruff)

**Render Templates:**
- `src/do_uw/templates/html/worksheet.html.j2` — Main HTML worksheet template
- `src/do_uw/templates/html/base.html.j2` — HTML base template
- `src/do_uw/templates/html/sections/` — Per-section HTML partials

**Cache:**
- `.cache/analysis.db` — SQLite API response cache (gitignored)
- `.cache/llm_extractions.db` — LLM extraction results cache (gitignored)

## Naming Conventions

**Files:**
- Stage orchestrators: `stages/{stage_name}/__init__.py` — the stage class lives here
- Stage helpers: `stages/{stage_name}/{noun}_{verb}.py` (e.g., `extract_governance.py`, `check_engine.py`)
- Brain migration files: `brain_migrate_{area}.py`
- CLI sub-apps: `cli_{feature}.py` (e.g., `cli_brain.py`, `cli_calibrate.py`)
- Render sections: `sect{N}_{area}.py` where N is section number (1-8)
- LLM schemas: filing type snake_case (e.g., `ten_k.py`, `def14a.py`)
- YAML check files: category noun (e.g., `accounting.yaml`, `board.yaml`, `sca.yaml`)
- Test files: `test_{module_name}.py` in mirrored directory structure

**Directories:**
- Snake_case throughout
- Stage names: lowercase single word (`resolve`, `acquire`, `extract`, `analyze`, `score`, `benchmark`, `render`)
- Check categories: 3-4 letter abbreviations (`fin`, `gov`, `lit`, `biz`, `exec`, `fwrd`, `nlp`, `stock`)

**Classes:**
- Stage classes: `{StageName}Stage` (e.g., `ResolveStage`, `AcquireStage`)
- Model classes: PascalCase noun phrases (e.g., `AnalysisState`, `CompanyProfile`, `ExtractedFinancials`)
- CLI apps: `{feature}_app` (e.g., `brain_app`, `knowledge_app`)

## Where to Add New Code

**New pipeline stage:**
- Create `src/do_uw/stages/{stage_name}/` with `__init__.py`
- Implement `{Name}Stage` with `name`, `validate_input()`, `run()` methods
- Add stage name to `PIPELINE_STAGES` in `src/do_uw/models/state.py`
- Add stage output field to `AnalysisState`
- Wire into `_build_default_stages()` in `src/do_uw/pipeline.py`

**New extractor (within EXTRACT stage):**
- Create `src/do_uw/stages/extract/{domain}_{noun}.py`
- Return tuple of `(ExtractedModel, ExtractionReport)`
- Call from `ExtractStage.run()` in `src/do_uw/stages/extract/__init__.py`
- Add result to `state.extracted.{domain}`

**New check:**
- Add YAML entry to appropriate `src/do_uw/brain/checks/{category}/{file}.yaml`
- Run `angry-dolphin brain build` to rebuild `checks.json` and `brain.duckdb`
- Add field mapping in `src/do_uw/stages/analyze/check_mappers.py` if new `field_key`

**New domain model:**
- Create `src/do_uw/models/{domain}.py`
- Use `SourcedValue[T]` for all data fields requiring provenance
- Import and add to `ExtractedData` or `AnalysisState` in `src/do_uw/models/state.py`

**New render section:**
- Create `src/do_uw/stages/render/sections/sect{N}_{area}.py`
- Add corresponding Jinja2 template in `src/do_uw/templates/html/sections/{area}.html.j2`
- Call from `src/do_uw/stages/render/html_renderer.py`

**New CLI sub-command:**
- Create `src/do_uw/cli_{feature}.py` with `{feature}_app = typer.Typer(...)`
- Register in `src/do_uw/cli.py` with `app.add_typer({feature}_app, name="{feature}")`

**Utilities / shared helpers:**
- Cross-stage pure functions: `src/do_uw/stages/{stage_name}/{noun}_helpers.py`
- Shared formatters: `src/do_uw/stages/render/formatters*.py`
- Common math/formulas: `src/do_uw/stages/analyze/financial_formulas.py`

**Tests:**
- Mirror the source path: `src/do_uw/stages/extract/foo.py` → `tests/stages/extract/test_foo.py`

## Special Directories

**`.cache/`:**
- Purpose: Runtime SQLite caches (API responses, LLM extractions)
- Generated: Yes (on first run)
- Committed: No (gitignored)

**`src/do_uw/brain/`:**
- Purpose: DuckDB knowledge store + YAML source check definitions
- Generated: `brain.duckdb` is built from YAML via `angry-dolphin brain build`; `checks.json` is compiled
- Committed: YAML source files are committed; `brain.duckdb` is committed (for convenience); `checks.json` is committed

**`output/`:**
- Purpose: Per-run pipeline output (worksheet files, charts, state.json)
- Generated: Yes (by `RenderStage`)
- Committed: No (gitignored), except directory structure

**`.planning/`:**
- Purpose: Project planning, phase tracking, research
- Generated: No (hand-written planning documents)
- Committed: Yes (except `STATE.md` which is too large for GitHub)

**`src/do_uw/knowledge/migrations/versions/`:**
- Purpose: Alembic schema migration scripts for `knowledge.db`
- Generated: Via `alembic revision`
- Committed: Yes

---

*Structure analysis: 2026-02-25*
