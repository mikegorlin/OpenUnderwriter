# Technology Stack

**Analysis Date:** 2026-02-25

## Languages

**Primary:**
- Python 3.12+ — all application code under `src/do_uw/`

**Secondary:**
- HTML/CSS/Jinja2 — worksheet and dashboard templates in `src/do_uw/templates/`
- JSON — configuration and knowledge store files in `src/do_uw/config/` and `src/do_uw/brain/`
- YAML — brain knowledge checks in `src/do_uw/brain/checks/`

## Runtime

**Environment:**
- Python 3.12 (pinned in `.python-version`)
- Runs locally as a CLI tool; no containerization detected

**Package Manager:**
- `uv` (lockfile: `uv.lock` present — committed)
- Never use `pip install` directly

## Frameworks

**Core:**
- Pydantic v2 (`>=2.10`) — all data models; strict validation, `AnalysisState` as the single source of truth
- Typer (`>=0.15`) — CLI entry point at `src/do_uw/cli.py`; sub-apps for brain, calibrate, dashboard, feedback, ingest, knowledge, pricing, validate
- FastAPI (`>=0.128.6`) + Uvicorn (`>=0.40.0`) — interactive dashboard server at `src/do_uw/dashboard/app.py`

**LLM Integration:**
- `anthropic` (`>=0.79.0`) — Anthropic API client for Claude
- `instructor` (`>=1.14.0`) — structured output extraction from Claude with Pydantic schemas
- Default model: `claude-haiku-4-5-20251001` (overridable via `DO_UW_LLM_MODEL` env var)
- Used in: `src/do_uw/stages/extract/llm/extractor.py`, `src/do_uw/stages/benchmark/narrative_generator.py`, `src/do_uw/knowledge/ingestion_llm.py`, `src/do_uw/knowledge/pricing_ingestion.py`, `src/do_uw/validation/batch.py`

**Rendering / Output:**
- `python-docx` (`>=1.1.0`) — Word document generation at `src/do_uw/stages/render/word_renderer.py`
- `jinja2` (`>=3.1.0`) — HTML and PDF templates; template dirs at `src/do_uw/templates/html/`, `src/do_uw/templates/pdf/`, `src/do_uw/templates/dashboard/`
- `weasyprint` (`>=60.0`, optional `pdf` extra) — CSS-based PDF rendering at `src/do_uw/stages/render/pdf_renderer.py`
- `playwright` (`>=1.58.0`) — headless Chromium for HTML-to-PDF; used in `src/do_uw/stages/render/html_renderer.py`
- `matplotlib` (`>=3.9.0`) — chart generation for Word/PDF output in `src/do_uw/stages/render/charts/`
- `plotly` (`>=6.5.2`) — interactive charts for dashboard at `src/do_uw/dashboard/charts.py`, `src/do_uw/dashboard/charts_financial.py`
- `rich` (`>=13.0`) — terminal progress display in `src/do_uw/cli.py`

**Testing:**
- `pytest` (`>=9.0.2`) — test runner; config in `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`)
- `pytest-asyncio` (`>=1.3.0`) — async test support

**Build/Dev:**
- `hatchling` — build backend; package at `src/do_uw/`
- `ruff` (`>=0.15.0`) — linting and formatting; config in `ruff.toml` (target `py312`, line length 99)
- `pyright` (`>=1.1.408`) — strict type checking; config in `pyproject.toml` (`typeCheckingMode = "strict"`)
- `vulture` (`>=2.14`) — dead code detection
- `pytailwindcss` (`>=0.3.0`) — Tailwind CSS compilation for dashboard/static assets

## Key Dependencies

**Critical:**
- `pydantic>=2.10` — validates all data models; every stage input/output is typed
- `httpx[http2]>=0.28` — all direct HTTP calls (SEC EDGAR REST, Serper.dev); NOT `requests`
- `yfinance>=1.1.0` — Yahoo Finance market data (price history, company info, news, insider transactions)
- `edgartools>=5.14.1` — SEC EDGAR filing retrieval library (MCP context); used in ACQUIRE stage
- `anthropic>=0.79.0` + `instructor>=1.14.0` — LLM extraction pipeline in EXTRACT and BENCHMARK stages
- `duckdb>=1.4.4` — brain knowledge store at `src/do_uw/brain/brain.duckdb`

**Infrastructure:**
- `sqlalchemy>=2.0` — ORM for knowledge store SQLite DB at `src/do_uw/knowledge/knowledge.db`
- `alembic>=1.18` — schema migrations for knowledge store; migrations at `src/do_uw/knowledge/migrations/`
- `rapidfuzz>=3.14.3` — fuzzy company name matching in `src/do_uw/stages/resolve/ticker_resolver.py`
- `financedatabase>=2.3.1` — peer group sector/industry data in `src/do_uw/stages/extract/peer_group.py`
- `pysentiment2>=0.1.1` — Loughran-McDonald financial sentiment dictionary in `src/do_uw/stages/analyze/sentiment_analysis.py`
- `textstat>=0.7.12` — readability scoring for narrative analysis
- `aiolimiter>=1.2.1` — async rate limiting (imported but pipeline is primarily synchronous)
- `python-dotenv>=1.2.1` — loads `.env` at CLI startup via `load_dotenv()` in `src/do_uw/cli.py`
- `pyyaml>=6.0` — YAML parsing for brain knowledge checks

## Configuration

**Environment:**
- Variables loaded from `.env` file at startup (no `.env` file committed to repo)
- Required: `ANTHROPIC_API_KEY` — for LLM extraction and narrative generation
- Required: `SERPER_API_KEY` — for web search blind spot detection; pipeline degrades gracefully without it
- Optional: `DO_UW_LLM_MODEL` — override default Claude model (defaults to `claude-haiku-4-5-20251001`)

**Build:**
- `pyproject.toml` — project metadata, dependencies, test config, pyright config
- `ruff.toml` — linting rules (E, F, B, I, UP, S, C4, RUF), isort config, per-file ignores
- `uv.lock` — locked dependency graph

**Runtime Config (JSON):**
- `src/do_uw/config/` — 24 JSON files for scoring weights, thresholds, patterns, hazards, actuarial models
- `src/do_uw/brain/` — knowledge checks (`checks.json`), patterns, red flags, scoring, sectors

## Data Persistence

**Analysis Cache:**
- SQLite at `.cache/analysis.db` via `src/do_uw/cache/sqlite_cache.py`
- TTL-based expiration; keys by `source:ticker:filing_type`
- LLM extraction cache at `.cache/llm_extractions.db`

**Knowledge Store:**
- SQLite at `src/do_uw/knowledge/knowledge.db` via SQLAlchemy ORM
- Schema managed by Alembic; 6 migration versions present

**Brain Store:**
- DuckDB at `src/do_uw/brain/brain.duckdb` via `src/do_uw/brain/brain_schema.py`
- 19 tables, 11 views; rebuilt from YAML/JSON on first CLI invocation

**State Persistence:**
- `AnalysisState` serialized to JSON at `output/{TICKER}-{DATE}/state.json` after each pipeline stage
- Supports resume-from-failure

## Platform Requirements

**Development:**
- Python 3.12 (use `uv` for all package management)
- Playwright Chromium browser (`playwright install chromium` for HTML-to-PDF)

**Production:**
- Local execution only (no deployment infrastructure detected)
- CLI entry points: `angry-dolphin` and `do-uw`

---

*Stack analysis: 2026-02-25*
