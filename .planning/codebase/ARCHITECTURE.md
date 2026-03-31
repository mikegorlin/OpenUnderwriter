# Architecture

**Analysis Date:** 2026-02-25

## Pattern Overview

**Overall:** Sequential 7-Stage Pipeline with Single State Object

**Key Characteristics:**
- One immutable source of truth: `AnalysisState` Pydantic model passed through all 7 stages
- Stages execute strictly in order; each validates prior stage completed before running
- State serialized to `state.json` after every stage for resume-from-failure support
- Pipeline can be resumed mid-run: completed stages are skipped automatically
- All data carries mandatory provenance via `SourcedValue[T]` wrapper (source + confidence)

## Layers

**CLI Layer:**
- Purpose: User entry points, sub-commands, Rich progress display
- Location: `src/do_uw/cli.py`, `src/do_uw/cli_*.py`
- Contains: Typer app with `analyze` command; sub-apps for brain, calibrate, dashboard, feedback, ingest, knowledge, pricing, validate
- Depends on: `Pipeline`, `AnalysisState`
- Used by: End users via `angry-dolphin` / `do-uw` commands

**Pipeline Orchestrator:**
- Purpose: Sequential stage execution with callbacks, state persistence, resume logic
- Location: `src/do_uw/pipeline.py`
- Contains: `Pipeline` class, `StageCallbacks` protocol, `NullCallbacks`, `PipelineError`
- Depends on: All 7 stage classes, `AnalysisState`, `StageStatus`
- Used by: CLI `analyze` command

**State Model:**
- Purpose: THE single source of truth for entire analysis
- Location: `src/do_uw/models/state.py`
- Contains: `AnalysisState`, `AcquiredData`, `ExtractedData`, `AnalysisResults`, `RiskFactorProfile`
- Depends on: All domain models in `src/do_uw/models/`
- Used by: Every stage reads and writes to this model

**Domain Models:**
- Purpose: Typed Pydantic v2 models for each data domain
- Location: `src/do_uw/models/`
- Contains: `company.py`, `financials.py`, `market.py`, `governance.py`, `litigation.py`, `scoring.py`, `hazard_profile.py`, `classification.py`, `peril.py`, `ai_risk.py`, `common.py`, `executive_summary.py`, `temporal.py`, `forensic.py`, `density.py`, `market_events.py`, `executive_risk.py`, `scoring_output.py`, `governance_forensics.py`, `litigation_details.py`, `pricing.py`
- Depends on: `common.py` (`SourcedValue[T]`, `Confidence`, `StageResult`)
- Used by: All stages, renderers

**Stage Implementations:**
- Purpose: The 7 pipeline stages, each with `name`, `validate_input()`, and `run()`
- Location: `src/do_uw/stages/{resolve,acquire,extract,analyze,score,benchmark,render}/`
- Depends on: Domain models, clients, brain config, knowledge store
- Used by: Pipeline orchestrator

**Brain / Knowledge System:**
- Purpose: Authoritative D&O underwriting knowledge: checks, patterns, scoring, red flags, sector data
- Location: `src/do_uw/brain/` (DuckDB runtime), `src/do_uw/knowledge/` (SQLite store + playbooks)
- Contains: `brain.duckdb` (19 tables, 11 views), `checks.json`, `scoring.json`, `patterns.json`, `red_flags.json`, `sectors.json`, per-category YAML check definitions under `brain/checks/`
- Depends on: Nothing (data layer, consumed by stages)
- Used by: `AnalyzeStage`, `ScoreStage`, `ExtractStage` (via `BackwardCompatLoader`)

**Cache Layer:**
- Purpose: SQLite TTL cache for expensive external API calls
- Location: `src/do_uw/cache/sqlite_cache.py`
- Contains: `AnalysisCache` — key/value store with 7-day TTL default
- Path: `.cache/analysis.db` (gitignored)
- Used by: `ResolveStage`, `AcquireStage`

**Config Layer:**
- Purpose: JSON config files for scoring weights, thresholds, calibration — never hardcoded
- Location: `src/do_uw/brain/` JSON files + `config/quality_checklist.json`
- Contains: `scoring.json`, `patterns.json`, `red_flags.json`, `sectors.json`, `actuarial.json`, `settlement_calibration.json`
- Used by: `ScoreStage`, `AnalyzeStage`, `BenchmarkStage`

**Validation / QA:**
- Purpose: Post-pipeline output quality checks and batch validation
- Location: `src/do_uw/validation/`
- Contains: `qa_report.py`, `runner.py`, `report.py`, `batch.py`, `cost_report.py`, `config.py`
- Used by: CLI after pipeline completion

**Dashboard:**
- Purpose: Interactive FastAPI/Plotly web dashboard for reviewing analysis output
- Location: `src/do_uw/dashboard/`
- Contains: `app.py`, `state_api.py`, `state_api_ext.py`, `charts.py`, `charts_financial.py`, `design.py`
- Used by: `cli_dashboard.py`

## Data Flow

**Primary Analysis Pipeline:**

1. User runs `angry-dolphin analyze AAPL`
2. CLI creates `AnalysisState(ticker="AAPL")` or loads from `state.json` (resume)
3. `Pipeline.run(state)` iterates over 7 stages sequentially
4. **RESOLVE**: `ResolveStage` → SEC EDGAR CIK lookup → yfinance enrichment → `state.company = CompanyProfile`
5. **ACQUIRE**: `AcquireStage` → `AcquisitionOrchestrator`:
   - Phase A: Pre-acquisition blind spot web search (~20% budget)
   - Phase B: Structured SEC, market, litigation, news client calls
   - Phase C: Post-acquisition blind spot sweep
   - Phase D: Gate checking
   - → `state.acquired_data = AcquiredData`
6. **EXTRACT**: `ExtractStage` → 13 extraction phases (company profile, financial statements, distress, earnings quality, debt, audit, tax, peers, quarterly, market, governance, litigation, AI risk) → `state.extracted = ExtractedData`
7. **ANALYZE**: `AnalyzeStage`:
   - Pre-analyze: Layer 1 Classification + Layer 2 Hazard Profile
   - Execute 359 checks from `brain.duckdb`
   - Run 4 analytical engines (temporal, forensic composites, executive forensics, NLP signals)
   - Record check run telemetry to `brain.duckdb` and `knowledge.db`
   - → `state.analysis = AnalysisResults`
8. **SCORE**: `ScoreStage` → 17-step pipeline (CRF gates → factor scoring → pattern detection → pattern modifiers → IES amplification → composite → tier → risk type → allegations → probability → severity → tower → red flags → peril map + bear cases) → `state.scoring = ScoringResult`
9. **BENCHMARK**: `BenchmarkStage` → peer percentile rankings → inherent risk baseline → executive summary → optional market intelligence/actuarial enrichment → `state.benchmark`, `state.executive_summary`
10. **RENDER**: `RenderStage` → Word (.docx), HTML→PDF, Markdown output files in `output/{TICKER}-{DATE}/`
11. State saved to `output/{TICKER}-{DATE}/state.json` after each stage
12. Post-pipeline QA report printed

**State Management:**
- Single `AnalysisState` Pydantic model passed by reference through all stages
- Large blobs (company_facts, filing_texts, exhibit_21) stripped before JSON serialization, restored in memory
- Stages write directly to state fields: `state.company`, `state.acquired_data`, `state.extracted`, `state.analysis`, `state.scoring`, `state.benchmark`

## Key Abstractions

**`SourcedValue[T]`:**
- Purpose: Every data point carries provenance — source, confidence, timestamp
- Location: `src/do_uw/models/common.py`
- Pattern: `SourcedValue[str](value="...", source="10-K 2024", confidence=Confidence.HIGH, as_of=datetime)`
- Used on: All data fields in CompanyProfile and domain models

**`BackwardCompatLoader`:**
- Purpose: Unified brain data access; routes to `brain.duckdb` (primary) or `KnowledgeStore` (fallback)
- Location: `src/do_uw/knowledge/compat_loader.py`
- Pattern: `loader = BackwardCompatLoader(playbook_id=...); brain = loader.load_all()`
- Used by: `AnalyzeStage`, `ScoreStage`, `BenchmarkStage`

**Check System:**
- Purpose: 359 D&O underwriting checks organized by category
- Location: `src/do_uw/brain/checks/{biz,exec,fin,fwrd,gov,lit,nlp,stock}/` (YAML source), compiled to `brain/checks.json` and `brain.duckdb`
- Categories: biz (business), exec (executives), fin (financials), fwrd (forward-looking), gov (governance), lit (litigation), nlp (NLP signals), stock (market)
- Pattern: Each check has `check_id`, `field_key`, `threshold_red/yellow/clear`, `factors`, `hazards`, `execution_mode`

**Hazard Profile (IES):**
- Purpose: Layer 2 inherent exposure score across 47 dimensions (H1-H7)
- Location: `src/do_uw/stages/analyze/layers/hazard/`
- Pattern: Computed pre-analyze from `ExtractedData`; IES score amplifies behavioral factor scores in SCORE stage
- Files: `dimension_h1_business.py` through `dimension_h7_emerging.py`, `hazard_engine.py`, `interaction_effects.py`

**LLM Extraction Subsystem:**
- Purpose: Claude API-powered structured extraction from SEC filing text
- Location: `src/do_uw/stages/extract/llm/`
- Contains: `extractor.py`, `prompts.py`, `cache.py`, `cost_tracker.py`, `schemas/` (Pydantic schemas per filing type)
- Pattern: Parallel extraction with per-schema Pydantic output; cached in `.cache/llm_extractions.db`

**Industry Playbooks:**
- Purpose: Industry-specific check overlays and scoring adjustments
- Location: `src/do_uw/knowledge/playbooks.py`, `playbook_data*.py`
- Pattern: Activated during RESOLVE based on SIC/NAICS → `state.active_playbook_id` set → consumed by `BackwardCompatLoader`

## Entry Points

**Main CLI Command:**
- Location: `src/do_uw/cli.py`
- Triggers: `angry-dolphin analyze <TICKER>` or `do-uw analyze <TICKER>`
- Responsibilities: Load .env, auto-init brain.duckdb, create/resume state, run pipeline with Rich progress display, print QA report

**Pipeline Entry:**
- Location: `src/do_uw/pipeline.py` → `Pipeline.run(state)`
- Triggers: CLI analyze command
- Responsibilities: Sequential stage execution, validation gates, state persistence, callback notifications

**Dashboard Entry:**
- Location: `src/do_uw/dashboard/app.py`
- Triggers: `angry-dolphin dashboard`
- Responsibilities: FastAPI server for interactive worksheet review

**Brain CLI:**
- Location: `src/do_uw/cli_brain.py`
- Triggers: `angry-dolphin brain {status,explore,add,yaml}`
- Responsibilities: Brain DuckDB management, check authoring, effectiveness reporting

## Error Handling

**Strategy:** Graceful degradation at sub-module level; hard failure at stage level

**Patterns:**
- Each stage wraps `run()` body in try/except: marks stage FAILED, re-raises as `PipelineError`
- Individual analytical engines (classification, hazard, temporal, forensic, NLP) wrapped in their own try/except — failures do NOT block stage completion
- Acquisition clients use fallback chains (SEC primary → REST API fallback → web search)
- Non-critical enrichments (yfinance, industry playbook, brain telemetry) wrapped in try/except with warning logs only
- `PipelineError` propagates from `Pipeline.run()` to CLI; CLI prints error and exits code 1

## Cross-Cutting Concerns

**Logging:** Python standard `logging` module; each module creates `logger = logging.getLogger(__name__)`

**Validation:** Pydantic v2 on all models; `validate_input()` method on each stage checks prior stage status

**Authentication:** No auth on CLI tool; API keys read from `.env` file via `python-dotenv` at startup (`SERPER_API_KEY` for web search, `ANTHROPIC_API_KEY` for LLM extraction)

**Data Integrity:** `SourcedValue[T]` wrapper enforced on all data fields; Confidence enum (HIGH/MEDIUM/LOW) required on every data point; no hallucination rule enforced by convention

---

*Architecture analysis: 2026-02-25*
