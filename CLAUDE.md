# D&O Underwriting Worksheet System

## Product Motto (NORTH STAR — filter every decision through this)
**"The single source of truth for underwriters to make the most knowledgeable decisions on a risk."**
1. **Single source of truth** — if it's not in the worksheet, it doesn't exist. Completeness is non-negotiable.
2. **Most knowledgeable** — the system learns from underwriter feedback, surfaces what matters. Human-in-the-middle learning.
3. **Decisions on a risk** — beautiful analytics that tell the risk story at a glance, then let you drill in. CIQ/Bloomberg-quality visualization. Progressive disclosure.
4. **For underwriters** — domain experts are the audience. The system augments their judgment, doesn't replace it.

## Project Overview
Python CLI that takes a stock ticker and produces a comprehensive D&O liability underwriting worksheet. Input: ticker. Output: Word doc (primary), PDF, Markdown.

## Architecture
7-stage pipeline: RESOLVE → ACQUIRE → EXTRACT → ANALYZE → SCORE → BENCHMARK → RENDER
- State: Single Pydantic `AnalysisState` model — the ONLY source of truth
- Cache: DuckDB at `.cache/analysis.duckdb`
- Config: JSON files in `config/` (scoring weights, thresholds, patterns — NOT hardcoded)
- Knowledge: Migrated from predecessor BRAIN/ directory

## Critical Rules

### Brain Source of Truth (NON-NEGOTIABLE)
- **YAML files are the ONLY source of truth for brain signals, sections, and configuration**
- Brain signals live in: `brain/signals/*.yaml` (36 files, 600+ signals)
- Brain sections live in: `brain/sections/*.yaml` (12 files)
- Brain framework lives in: `brain/framework/*.yaml`
- **DuckDB (`brain.duckdb`) is a PROCESSING/CACHE database ONLY** — it stores run history, effectiveness metrics, and feedback logs. It is NEVER the primary source for signal definitions, section specs, or any brain configuration.
- **NEVER query brain.duckdb to read signal definitions** — always read YAML files directly
- **NEVER refer to DuckDB as containing authoritative brain data** — it's a derived/ephemeral cache
- If you need to check what signals exist, read `brain/signals/*.yaml`, NOT the `brain_signals` table
- **Brain portability** — brain YAML + output manifest + signal results JSON must be portable to another system. Everything starts in brain YAML. Manifest IS the contract between brain and rendering. Renderers are dumb consumers — zero business logic, no hardcoded thresholds, no conditional logic based on data content.
- **Brain changes driven by evidence** — signal modifications come from underwriting experience, settlements, studies, regulatory changes. Every change needs: WHY it changed, WHAT evidence drove it, WHAT the expected impact is.

### Narrative Quality (NON-NEGOTIABLE)
- **Every sentence in the worksheet must contain company-specific data** — dollar amounts, percentages, dates, names. If a sentence could apply to any company by changing the name, it FAILS. No boilerplate. No template language. No "has experienced a notable decline" — say "stock declined 27.9% from $167.40 to $120.69 over 326 trading days."
- **Every key negative/positive MUST reference its scoring factor** (e.g., "F.7 = 5/8") and cite specific evidence with numbers
- **Never generate generic D&O commentary** — every "D&O Risk" or "Assessment" column must explain WHY this specific finding matters for THIS company's D&O profile, with the litigation theory it maps to
- **LLM prompts must include full analytical context** — scoring results, signal evaluations, financial data, company specifics. Generic prompts produce generic output. Always pass the actual numbers.
- **D&O commentary originates from brain YAML** (`presentation.do_context`), not Python templates or Jinja2 conditionals. Renderers display, they don't interpret.
- **Human readable** — no factor codes (F1-F10) in prose, no signal counts ("5-of-90"), no system jargon, no "AI Assessment" labels. The worksheet must read like a human underwriter wrote it.
- **Worksheet tells a story** — each section answers the question from the previous section. Opening sentences connect sections. Narrative arc: who is this company → how do they make money → what could go wrong → what has gone wrong → what does this mean for D&O.
- **Investigative depth** — pass the "30-year underwriter" test. Cross-check data between sources. If a signal triggers but doesn't fit context, add annotation. Always include value + meaning + whether concerning + source.

### Data Integrity (NON-NEGOTIABLE)
- Every data point MUST have a `source` and `confidence` field in the Pydantic model
- Source = specific filing type + date + URL/CIK reference
- Confidence = HIGH (audited/official), MEDIUM (unaudited/estimates), LOW (derived/web)
- NEVER generate, guess, or hallucinate financial data — use "Not Available" instead
- Web-sourced data requires cross-validation from 2+ independent sources
- If a data source fails, fall through to next tier — never assume "no data" = "no issue"

### Data Source Priority — XBRL First (NON-NEGOTIABLE)
- **XBRL/SEC filings are ALWAYS the primary data source** for financial metrics (revenue, assets, equity, cash, debt, shares outstanding, income). These are audited, authoritative, and traceable to a specific filing+period.
- **yfinance is a FALLBACK**, not a primary — it's useful for real-time price, market cap, ratios, and data that doesn't exist in XBRL (analyst estimates, short interest, institutional holders). But for any metric that exists in both XBRL and yfinance, XBRL wins.
- **Every displayed value must show its "as of" date** — "Revenue: $3.05B (FY2025)" not just "$3.05B". The underwriter needs to know whether they're looking at trailing-12-month, fiscal year, or quarterly data.
- **Full traceability** — every metric in the worksheet should be traceable: what filing it came from, what period it covers, and what confidence level it has. The render context should carry source metadata, not just the number.

### IPO-Specific Treatment (NON-NEGOTIABLE for companies public < 5 years)
- **Stock chart**: Show IPO date as a vertical bar/annotation. Show IPO/offering price as a dotted horizontal line. These are critical reference points for DDL (Dollar-Day Loss) and Section 11 analysis.
- **Capital filings**: S-1, S-3, 424B MUST be extracted — they contain offering price, lockup terms, use of proceeds, risk factors at time of offering. Prioritize above 8-Ks.
- **Section 11 exposure window**: Each offering (IPO, secondary, shelf) creates a separate liability window. Display all offering dates, prices, and statutes of limitations.
- **Controlled company analysis**: Dual-class structures, majority shareholders, related party transactions with pre-IPO parent must be prominently flagged.
- **Lockup expiration**: Show lockup dates and selling shareholder identity — lockup expiry is a known stock catalyst.

### Root-Cause Problem Solving (NON-NEGOTIABLE)
- **A patch is NEVER a solution.** Before implementing any fix, ask: "Why is this happening?" and solve the root cause so it doesn't happen again for ANY similar case.
- **If you're adding a string to a filter list, you're patching.** Find why that string reaches the output in the first place and fix the pipeline boundary.
- **If the same class of bug appears in multiple places, there is a missing architectural guarantee.** Add the guarantee (typed contract, validation layer, sanitization pass) instead of fixing each instance.
- **Trace every bug to its root cause.** Example: "raw Python list in template" → root cause is "no typed output contract between context builders and templates" → fix is a Pydantic schema that enforces types at the boundary, not adding `| join(', ')` in one template.
- **Five root causes to watch for:** (1) untyped data reaching templates, (2) same metric from multiple sources without reconciliation, (3) signals firing without contextual validation, (4) missing data classification logic, (5) internal debug/processing data leaking to output.

### Anti-Context-Rot
- No source file over 500 lines — split before it gets there
- Single state file (AnalysisState), not multiple competing state representations
- No scoring logic outside `stages/score/` — one definition, one location
- No data acquisition outside `stages/acquire/` — one boundary
- Read state at session start, write state at session end
- Every function does one thing. If you're adding an `elif` branch, consider a new function.

### Visual Quality (NON-NEGOTIABLE)
- **NEVER make things look worse** — when recreating a design from a reference, match it precisely. Do not "interpret" or "approximate." If you have a reference image or HTML, replicate it pixel-for-pixel: same font sizes, same spacing, same alignment, same colors, same visual hierarchy.
- **When given a visual reference**: read the actual CSS values (font-size, padding, margin, gap, letter-spacing, opacity, font-weight) and use them exactly. Do not round, simplify, or substitute.
- **If you can't match it exactly**: say so and explain what's missing. Don't ship a degraded version and call it done.
- **Every visual change must be an improvement** — if the current output looks better than your proposed change, don't make the change. Compare before and after.
- **Always ADD detail, never remove it** — the default direction is MORE visual cues, MORE infographics, MORE data density. If a reference has sparklines + range bars + decile dots, include ALL. Never decide "this is enough." If the user asks to simplify, they'll say so.
- **Maximum data density** — minimal margins, infographic approach (charts/gauges/badges over prose), 2-3 column layouts, CIQ/Bloomberg-quality visual hierarchy through size/weight/color.
- **Modern aesthetic** — borderless tables with subtle row dividers, thin section separators. No heavy borders. Clean, professional look.
- **PDF is the final output** — HTML is intermediate. Every CSS change must work in print. Design for print dimensions. `@media print` styles are primary.

### Card Catalog Design System v4 (ACTIVE — 2026-03-29)

4-layer architecture where each layer is independent:

```
DATA POOL → CARD REGISTRY → DESIGN ELEMENTS → RENDERED WORKSHEET
```

- **Data Pool** — 80+ elements mapped to sources (XBRL, yfinance, LLM, Web, SEC, Supabase, Computed). Cards declare what they need; don't know how data is acquired. Defined in `brain/config/card_registry.yaml`.
- **Card Registry** — 62 lego-brick cards, each `active: true/false`, with `data_keys`, `elements` (sub-components with chart/component refs like `chart_ref: L-07`). Toggle on/off, reorder, compose. Defined in `brain/config/card_registry.yaml`.
- **Design Elements** — 88 chart styles by intent (L-01 through F-08), 56 components (CARD-01 through NARR-06). Each has reference ID. Defined in `brain/config/design_system.yaml`.
- **Rendered Worksheet** — composition of active cards from registry, using design elements. Each card self-contained.

**Operating Dashboard** (7 tabs): `python3 scripts/build_ops_dashboard.py && open output/OPS_DASHBOARD.html`

**Key files:**
- `brain/config/card_registry.yaml` — data pool + 62 card definitions
- `brain/config/design_system.yaml` — colors, typography, 62 cards, 83 elements, chart/component library
- `templates/html/catalog.css` — component CSS (cat- prefixed)
- `.planning/baselines/golden_v4/` — 6 golden baselines
- `output/CARD_CATALOG_FOUNDATION.html` + `scripts/build_card_catalog_foundation.py`

**Card pipeline (per card):** Designed → Data Hooked & Verified → LLM Synthesis → QA Tested

**Section palette:**
| # | Section | Color | Cards |
|---|---------|-------|-------|
| 00 | Overview | #0F172A | 1 |
| 01 | Exec Brief | #6D28D9 | 2 |
| 02 | Company | #0369A1 | 10 |
| 03 | Stock & Market | #EA580C | 6 |
| 04 | Financial | #059669 | 7 |
| 05 | Governance | #D97706 | 6 |
| 06 | Litigation | #DC2626 | 5 |
| 07 | Forward-Looking | #0D9488 | 5 |
| 08 | Industry | #7C3AED | 2 |
| 09 | Scoring | #0891B2 | 13 |
| 10 | UW Framework | #4338CA | 1 |
| 11 | Meeting Prep | #BE185D | 1 |
| 12 | Audit Trail | #64748B | 3 |

**Key principles:**
- Cards are MODULAR — insert/remove without affecting siblings
- Cards are SELF-CONTAINED — own border, header, body, data sources
- Section color is the ONLY visual grouping mechanism
- Inner content FLOWS — card CSS doesn't bleed into content
- Every card shows its data source pills (XBRL, yfinance, LLM, Web, SEC, Supabase, Computed)
- Key Risk Findings sorted by D&O litigation severity (integrity/fraud first → governance → regulatory → operational → market)

**Status:** Architecture defined. Card frames applied to all 12 sections. Old navy headers removed. 3/62 cards designed (internal card redesign in progress). Chart gallery needs expansion. Next: CSS overhaul of internal elements, then section-by-section card breakout.

### Code Quality
- Python 3.12+, managed with `uv` (never `pip install`)
- Type hints on all functions — Pyright strict mode
- Pydantic v2 for all data models
- `httpx` for HTTP (not `requests`)
- `ruff` for formatting and linting
- Tests alongside code, run after every change
- **No bare `float()` in render code** — use `safe_float()` from `stages/render/formatters.py` for any value from state, dicts, or LLM extraction. LLM/API data contains "N/A", "13.2%", concatenated junk that crashes bare `float()`.
- **NEVER truncate analytical content** — no `| truncate()` in templates on evidence, findings, theses, descriptions, or any text an underwriter reads. Only acceptable for tooltip `title` attrs and internal QA audit. If text is long, use CSS `word-wrap` — never cut the text.

### Self-Verification Before Showing Output (NON-NEGOTIABLE)
- **NEVER show the user output without verifying it yourself first** — re-render, then run automated checks on the HTML output BEFORE opening it
- After every template/render change: (1) re-render to a file, (2) run verification checks (count elements, check for duplicates, verify sticky/styles, check data presence), (3) only open if ALL checks pass
- Verification checks MUST include: no duplicate nav bars, sticky elements present, buttons visible (not white-on-white), charts rendering (PNG count), data not empty, no broken template variables
- If any check fails, FIX IT first — do not show broken output to the user
- The user should NEVER be the one discovering rendering problems
- **Visual verification, not just grep** — parsing HTML for section names is insufficient. Check actual values are formatted, N/A counts are reasonable, no raw floats or NaN, no template variables showing through.
- **Self-review loop** — after generating output, review it yourself, critique it, identify improvements, fix, re-render, review again. Like preparing a McKinsey presentation.

### Pipeline Execution Discipline (NON-NEGOTIABLE)
- **Monitor pipeline to completion** — don't just launch and walk away. Watch for stage failures, diagnose immediately, fix, and re-run.
- **After code changes affecting extraction**: run with `--fresh`, verify data year matches most recent filing, compare signal counts before/after.
- **Always use ticker, not company name** for CLI input — fuzzy name resolution can match wrong companies.
- **Incremental by default** — `--fresh` resets stages but does NOT delete caches. LLM extraction cache invalidates only on schema version change. Goal: re-analyze + re-render < 30s for known company.

### Preserve Before Improve (NON-NEGOTIABLE)
- **NEVER remove existing analytical capabilities** — Market Risk Flags, DTL charts, Beneish/Altman, financial forensics, litigation timeline, scoring visualizations are GOLD.
- **All work is ADDITIVE** — new capabilities alongside existing ones, never replacements.
- **Before any refactor**: capture skip rate and field coverage, verify identical or better after.
- **"If not bullshit, is gold"** — verify existing analytics are accurate, then preserve them. Don't casually delete.

### Governance Section Requirements (NON-NEGOTIABLE)
- Governance MUST ALWAYS show: (1) prior lawsuits against board/leadership, (2) personal character issues, (3) experience/qualifications for role — this is what underwriters need to assess individual director risk.
- Board composition table with independence, tenure, committee assignments, other board seats.
- CEO compensation with say-on-pay vote results and pay ratio.

### IPO & Offerings Section (MANDATORY for companies public < 5 years)
- If the company has had an IPO or post-IPO offerings, there MUST be a dedicated section showing: IPO date, IPO price, offering details (S-1/S-3/424B), lockup terms and expiry dates, selling shareholders, use of proceeds, Section 11 exposure timeline.
- This is not optional — it's a core underwriting requirement for recent-IPO companies.

### Blind Spot Detection (NON-NEGOTIABLE)
- Broad web search is a FIRST-CLASS acquisition method, not a fallback
- Every analysis run MUST include proactive discovery searches at START of ACQUIRE
- Structured APIs miss: short seller reports, state AG actions, employee lawsuits, social media, early news
- After structured acquisition, run exploratory searches for company + risk terms, executive names + litigation terms
- Results are LOW confidence unless corroborated — but MISSING them entirely is worse than flagging them

### MCP Boundary
- MCP tools (EdgarTools, Brave Search, Playwright, Fetch) are used ONLY in ACQUIRE stage
- Subagents CANNOT access MCP tools — all data acquisition happens in main context
- EXTRACT and later stages operate on local data only

## File Structure
```
src/do_uw/
  cli.py              — Typer CLI entry point
  models/             — Pydantic state models (AnalysisState, CompanyProfile, etc.)
  stages/
    resolve/          — Ticker → company identity
    acquire/          — Data acquisition (SEC, stock, litigation, sentiment)
    extract/          — Parse filings, extract structured data
    analyze/          — Run checks, detect patterns
    score/            — 10-factor scoring, red flags, allegation mapping
    benchmark/        — Peer-relative comparisons
    render/           — Word/PDF/Markdown generation
  config/             — Scoring weights, thresholds, patterns (JSON)
  brain/              — Migrated knowledge assets from predecessor
  cache/              — DuckDB cache (gitignored)
tests/                — Mirrors src/ structure
```

## Planning & Requirements
- Project definition: `.planning/PROJECT.md`
- Requirements (111 v1): `.planning/REQUIREMENTS.md`
- Roadmap (8 phases): `.planning/ROADMAP.md`
- State tracking: `.planning/STATE.md`
- Research: `.planning/research/`

## MCP Servers Available
- `edgartools` — SEC EDGAR filings, XBRL data
- `brave-search` — Web search with news/domain filtering (2,000 free/month)
- `playwright` — Browser automation for scraping dynamic sites
- `fetch` — Simple URL content extraction
- `context7` — Up-to-date library documentation
- `duckdb` — Analytical data cache
- `github` — Dev workflow

## Session Startup Checklist
1. Read `.planning/STATE.md` for current phase/progress
2. Read `.planning/ROADMAP.md` for phase goals
3. If mid-phase, read the phase's `PLAN.md`
4. Verify MCP servers are connected (`/mcp`)
5. Run `uv sync` if `pyproject.toml` changed

## Data Source Fallback Chains
- **Financial Metrics**: XBRL (audited, HIGH confidence) → 10-K LLM extraction → yfinance (MEDIUM) → web search (LOW)
- **SEC Filings**: EdgarTools MCP → SEC EDGAR REST API → web search
- **Stock Data**: yfinance (real-time price, market data) → FMP (supplemental ownership/estimates) → web search
- **Litigation**: Stanford SCAC (Playwright) → 10-K Item 3 → CourtListener → web search
- **SEC Enforcement**: SEC Litigation Releases → AAER → 10-K disclosure → web search
- **Sentiment/News**: Brave Search → Exa semantic search → built-in WebSearch → WebFetch on known URLs
- **Court Records**: CourtListener API (RECAP dockets) → PACER → web search
- **Semantic Discovery**: Exa neural search (5-query budget, independent of web search budget)
- **Every finding**: Cross-validate against at least 2 sources. Flag single-source as LOW confidence.

## Testing
- **Unit/Integration**: `uv run pytest` — 5,000+ tests, mirrors src/ structure
- **Visual Regression**: `VISUAL_REGRESSION=1 uv run pytest tests/test_visual_regression.py` — per-section Playwright screenshots vs golden baselines (10% diff threshold)
- **Performance Budget**: `PERFORMANCE_TESTS=1 uv run pytest tests/test_performance_budget.py` — HTML <10s, PDF <30s, pipeline <25min
- **Cross-Ticker QA**: `uv run python scripts/qa_compare.py` — validates feature parity across tickers

## Predecessor Failures to Avoid
1. No monolithic files (predecessor: 9,445-line generate_referral.py)
2. No multiple scoring definitions (predecessor: 4 competing versions)
3. No multiple state files (predecessor: 7+ state representations)
4. No deprecated code left importable (predecessor: 14 deprecated files)
5. No mixing data acquisition with analysis (predecessor: 3 generations of data code)
6. No hardcoded thresholds (predecessor: thresholds in code AND config)
7. No building features before state model is solid (predecessor: built on shaky foundations)

<!-- GSD:project-start source:PROJECT.md -->
## Project

**D&O Liability Underwriting System**

A complete Directors & Officers liability underwriting analysis system (Angry Dolphin Underwriting) that ingests a stock ticker and produces an exhaustive risk assessment worksheet. It pulls 100% publicly available data — SEC EDGAR filings (via LLM extraction), court records, governance data, financial metrics, news, and web sources — analyzes the company across every dimension that predicts D&O claims using a 400-check YAML brain framework, benchmarks against industry peers, surfaces red flags with peril-organized scoring, and outputs an HTML/Word/PDF document giving an underwriter the deepest possible insight into the risk. The HTML output matches institutional presentation quality (S&P Capital IQ layout density). Built as a CLI tool (`do-uw analyze <TICKER>`), outputs to `output/<TICKER>/`.

**Core Value:** Surface every red flag and risk signal that exists in public data for any publicly traded company, benchmarked against industry peers, so an underwriter can make the most informed D&O decision possible.

### Constraints

- **Data**: 100% publicly available data only — no proprietary feeds, no paid databases
- **Platform**: Python 3.12+, CLI-first, runs on macOS
- **Architecture**: Modular Python package; no file over 500 lines; single source of truth for every concept
- **MCP limitation**: Background subagents cannot access MCP tools — all data acquisition in main context
- **SEC rate limits**: 10 req/sec max, proper User-Agent required
- **Output**: HTML is primary; Word/PDF/Markdown secondary
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.12+ — all application code under `src/do_uw/`
- HTML/CSS/Jinja2 — worksheet and dashboard templates in `src/do_uw/templates/`
- JSON — configuration and knowledge store files in `src/do_uw/config/` and `src/do_uw/brain/`
- YAML — brain knowledge checks in `src/do_uw/brain/checks/`
## Runtime
- Python 3.12 (pinned in `.python-version`)
- Runs locally as a CLI tool; no containerization detected
- `uv` (lockfile: `uv.lock` present — committed)
- Never use `pip install` directly
## Frameworks
- Pydantic v2 (`>=2.10`) — all data models; strict validation, `AnalysisState` as the single source of truth
- Typer (`>=0.15`) — CLI entry point at `src/do_uw/cli.py`; sub-apps for brain, calibrate, dashboard, feedback, ingest, knowledge, pricing, validate
- FastAPI (`>=0.128.6`) + Uvicorn (`>=0.40.0`) — interactive dashboard server at `src/do_uw/dashboard/app.py`
- `anthropic` (`>=0.79.0`) — Anthropic API client for Claude
- `instructor` (`>=1.14.0`) — structured output extraction from Claude with Pydantic schemas
- Default model: `claude-haiku-4-5-20251001` (overridable via `DO_UW_LLM_MODEL` env var)
- Used in: `src/do_uw/stages/extract/llm/extractor.py`, `src/do_uw/stages/benchmark/narrative_generator.py`, `src/do_uw/knowledge/ingestion_llm.py`, `src/do_uw/knowledge/pricing_ingestion.py`, `src/do_uw/validation/batch.py`
- `python-docx` (`>=1.1.0`) — Word document generation at `src/do_uw/stages/render/word_renderer.py`
- `jinja2` (`>=3.1.0`) — HTML and PDF templates; template dirs at `src/do_uw/templates/html/`, `src/do_uw/templates/pdf/`, `src/do_uw/templates/dashboard/`
- `weasyprint` (`>=60.0`, optional `pdf` extra) — CSS-based PDF rendering at `src/do_uw/stages/render/pdf_renderer.py`
- `playwright` (`>=1.58.0`) — headless Chromium for HTML-to-PDF; used in `src/do_uw/stages/render/html_renderer.py`
- `matplotlib` (`>=3.9.0`) — chart generation for Word/PDF output in `src/do_uw/stages/render/charts/`
- `plotly` (`>=6.5.2`) — interactive charts for dashboard at `src/do_uw/dashboard/charts.py`, `src/do_uw/dashboard/charts_financial.py`
- `rich` (`>=13.0`) — terminal progress display in `src/do_uw/cli.py`
- `pytest` (`>=9.0.2`) — test runner; config in `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`)
- `pytest-asyncio` (`>=1.3.0`) — async test support
- `hatchling` — build backend; package at `src/do_uw/`
- `ruff` (`>=0.15.0`) — linting and formatting; config in `ruff.toml` (target `py312`, line length 99)
- `pyright` (`>=1.1.408`) — strict type checking; config in `pyproject.toml` (`typeCheckingMode = "strict"`)
- `vulture` (`>=2.14`) — dead code detection
- `pytailwindcss` (`>=0.3.0`) — Tailwind CSS compilation for dashboard/static assets
## Key Dependencies
- `pydantic>=2.10` — validates all data models; every stage input/output is typed
- `httpx[http2]>=0.28` — all direct HTTP calls (SEC EDGAR REST, Serper.dev); NOT `requests`
- `yfinance>=1.1.0` — Yahoo Finance market data (price history, company info, news, insider transactions)
- `edgartools>=5.14.1` — SEC EDGAR filing retrieval library (MCP context); used in ACQUIRE stage
- `anthropic>=0.79.0` + `instructor>=1.14.0` — LLM extraction pipeline in EXTRACT and BENCHMARK stages
- `duckdb>=1.4.4` — brain knowledge store at `src/do_uw/brain/brain.duckdb`
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
- Variables loaded from `.env` file at startup (no `.env` file committed to repo)
- Required: `ANTHROPIC_API_KEY` — for LLM extraction and narrative generation
- Required: `SERPER_API_KEY` — for web search blind spot detection; pipeline degrades gracefully without it
- Optional: `DO_UW_LLM_MODEL` — override default Claude model (defaults to `claude-haiku-4-5-20251001`)
- `pyproject.toml` — project metadata, dependencies, test config, pyright config
- `ruff.toml` — linting rules (E, F, B, I, UP, S, C4, RUF), isort config, per-file ignores
- `uv.lock` — locked dependency graph
- `src/do_uw/config/` — 24 JSON files for scoring weights, thresholds, patterns, hazards, actuarial models
- `src/do_uw/brain/` — knowledge checks (`checks.json`), patterns, red flags, scoring, sectors
## Data Persistence
- SQLite at `.cache/analysis.db` via `src/do_uw/cache/sqlite_cache.py`
- TTL-based expiration; keys by `source:ticker:filing_type`
- LLM extraction cache at `.cache/llm_extractions.db`
- SQLite at `src/do_uw/knowledge/knowledge.db` via SQLAlchemy ORM
- Schema managed by Alembic; 6 migration versions present
- DuckDB at `src/do_uw/brain/brain.duckdb` via `src/do_uw/brain/brain_schema.py`
- 19 tables, 11 views; rebuilt from YAML/JSON on first CLI invocation
- `AnalysisState` serialized to JSON at `output/{TICKER}-{DATE}/state.json` after each pipeline stage
- Supports resume-from-failure
## Platform Requirements
- Python 3.12 (use `uv` for all package management)
- Playwright Chromium browser (`playwright install chromium` for HTML-to-PDF)
- Local execution only (no deployment infrastructure detected)
- CLI entry points: `angry-dolphin` and `do-uw`
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- `snake_case.py` throughout — e.g., `factor_scoring.py`, `check_engine.py`, `brain_migrate_yaml.py`
- Stage entry points named `__init__.py` (e.g., `stages/score/__init__.py`)
- CLI files prefixed `cli_` — e.g., `cli_brain.py`, `cli_pricing.py`, `cli_validate.py`
- Brain-subsystem files prefixed `brain_` — e.g., `brain_loader.py`, `brain_schema.py`
- Helper/utility suffix `_helpers.py` — e.g., `check_helpers.py`, `narrative_helpers.py`
- Client files prefixed by domain — e.g., `market_client.py`, `sec_client.py`, `litigation_client.py`
- Renderer section files named `sect{N}_{topic}.py` — e.g., `sect3_financial.py`, `sect7_peril_map.py`
- `snake_case` for all functions
- Private helpers prefixed with `_` — e.g., `_get_sector_code()`, `_make_company()`, `_load_or_create_state()`
- Factory functions named `make_*` or `create_*` — e.g., `create_serper_search_fn()`
- Stage entry functions named `run()` on Stage classes
- Sourced-value constructors: `sourced_str()`, `sourced_int()`, `sourced_float()`, `sourced_dict()`
- `snake_case` throughout
- Config dicts named `*_config` — e.g., `scoring_config`, `rf_config`, `sectors_config`
- Unused parameters explicitly assigned to `_` — `_ = (index, total)` (common in callbacks)
- Error message strings assigned to `msg` before raising
- `PascalCase` for all classes and Pydantic models
- `SCREAMING_SNAKE_CASE` for `StrEnum` members — e.g., `HIGH = "HIGH"`, `COMPLETED = "completed"`
- Type aliases defined as module-level constants — e.g., `JsonDict = dict[str, Any]`
- Stage constant lists in `SCREAMING_SNAKE_CASE` — `PIPELINE_STAGES`, `CHUNK_SIZE`
## Code Style
- Tool: `ruff` (configured in `ruff.toml` at project root)
- Line length: 99 characters
- Target: Python 3.12 (`target-version = "py312"`)
- Rule sets: `E` (pycodestyle), `F` (pyflakes), `B` (bugbear), `I` (isort), `UP` (pyupgrade), `S` (bandit security), `C4` (comprehensions), `RUF` (ruff-specific)
- `S101` (assert) suppressed in `tests/**`
- `B008` (function call in arg defaults) suppressed in all CLI files — required by Typer
- Pyright strict mode (`typeCheckingMode = "strict"` in `pyproject.toml`)
- Pyright venv-aware: `venvPath = "."`, `venv = ".venv"`
## Import Organization
## Error Handling
- `DataAcquisitionError` — raised in `src/do_uw/stages/acquire/fallback.py` when all tiers fail
- `PipelineError` — raised in `src/do_uw/pipeline.py` for pipeline-level failures
## Logging
- `logger.info()` — stage progress, chunk counts, cache hits
- `logger.warning()` — non-fatal fallbacks, missing data, tier failures
- `logger.debug()` — fine-grained navigation (CIK lookups, etc.)
- No `logger.error()` observed — errors either raise or warn
## Comments
## Data Integrity Pattern (Core Convention)
## Function Design
- Type hints required on all parameters (Pyright strict)
- Return type hints required on all functions
- Optional params with `| None` union type, not `Optional[T]`
- Always explicitly typed
- Empty collections (`{}`, `[]`) instead of `None` for missing-data cases in accessors
- `None` for optional stage outputs on `AnalysisState`
## Module Design
- `__init__.py` files expose the public API for each stage (e.g., `stages/score/__init__.py` exports `ScoreStage`)
- Private helpers in same file prefixed with `_`
- Re-exports for backward compatibility annotated with comment: `# Re-export for backward compat (tests import _get_sector_code)`
- All models use `BaseModel` from `pydantic`
- `ConfigDict(frozen=False)` on mutable models
- `Field(description=...)` on every field — description required
- `default_factory=lambda: []` (not mutable defaults)
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- One immutable source of truth: `AnalysisState` Pydantic model passed through all 7 stages
- Stages execute strictly in order; each validates prior stage completed before running
- State serialized to `state.json` after every stage for resume-from-failure support
- Pipeline can be resumed mid-run: completed stages are skipped automatically
- All data carries mandatory provenance via `SourcedValue[T]` wrapper (source + confidence)
## Layers
- Purpose: User entry points, sub-commands, Rich progress display
- Location: `src/do_uw/cli.py`, `src/do_uw/cli_*.py`
- Contains: Typer app with `analyze` command; sub-apps for brain, calibrate, dashboard, feedback, ingest, knowledge, pricing, validate
- Depends on: `Pipeline`, `AnalysisState`
- Used by: End users via `angry-dolphin` / `do-uw` commands
- Purpose: Sequential stage execution with callbacks, state persistence, resume logic
- Location: `src/do_uw/pipeline.py`
- Contains: `Pipeline` class, `StageCallbacks` protocol, `NullCallbacks`, `PipelineError`
- Depends on: All 7 stage classes, `AnalysisState`, `StageStatus`
- Used by: CLI `analyze` command
- Purpose: THE single source of truth for entire analysis
- Location: `src/do_uw/models/state.py`
- Contains: `AnalysisState`, `AcquiredData`, `ExtractedData`, `AnalysisResults`, `RiskFactorProfile`
- Depends on: All domain models in `src/do_uw/models/`
- Used by: Every stage reads and writes to this model
- Purpose: Typed Pydantic v2 models for each data domain
- Location: `src/do_uw/models/`
- Contains: `company.py`, `financials.py`, `market.py`, `governance.py`, `litigation.py`, `scoring.py`, `hazard_profile.py`, `classification.py`, `peril.py`, `ai_risk.py`, `common.py`, `executive_summary.py`, `temporal.py`, `forensic.py`, `density.py`, `market_events.py`, `executive_risk.py`, `scoring_output.py`, `governance_forensics.py`, `litigation_details.py`, `pricing.py`
- Depends on: `common.py` (`SourcedValue[T]`, `Confidence`, `StageResult`)
- Used by: All stages, renderers
- Purpose: The 7 pipeline stages, each with `name`, `validate_input()`, and `run()`
- Location: `src/do_uw/stages/{resolve,acquire,extract,analyze,score,benchmark,render}/`
- Depends on: Domain models, clients, brain config, knowledge store
- Used by: Pipeline orchestrator
- Purpose: Authoritative D&O underwriting knowledge: checks, patterns, scoring, red flags, sector data
- Location: `src/do_uw/brain/` (DuckDB runtime), `src/do_uw/knowledge/` (SQLite store + playbooks)
- Contains: `brain.duckdb` (19 tables, 11 views), `checks.json`, `scoring.json`, `patterns.json`, `red_flags.json`, `sectors.json`, per-category YAML check definitions under `brain/checks/`
- Depends on: Nothing (data layer, consumed by stages)
- Used by: `AnalyzeStage`, `ScoreStage`, `ExtractStage` (via `BackwardCompatLoader`)
- Purpose: SQLite TTL cache for expensive external API calls
- Location: `src/do_uw/cache/sqlite_cache.py`
- Contains: `AnalysisCache` — key/value store with 7-day TTL default
- Path: `.cache/analysis.db` (gitignored)
- Used by: `ResolveStage`, `AcquireStage`
- Purpose: JSON config files for scoring weights, thresholds, calibration — never hardcoded
- Location: `src/do_uw/brain/` JSON files + `config/quality_checklist.json`
- Contains: `scoring.json`, `patterns.json`, `red_flags.json`, `sectors.json`, `actuarial.json`, `settlement_calibration.json`
- Used by: `ScoreStage`, `AnalyzeStage`, `BenchmarkStage`
- Purpose: Post-pipeline output quality checks and batch validation
- Location: `src/do_uw/validation/`
- Contains: `qa_report.py`, `runner.py`, `report.py`, `batch.py`, `cost_report.py`, `config.py`
- Used by: CLI after pipeline completion
- Purpose: Interactive FastAPI/Plotly web dashboard for reviewing analysis output
- Location: `src/do_uw/dashboard/`
- Contains: `app.py`, `state_api.py`, `state_api_ext.py`, `charts.py`, `charts_financial.py`, `design.py`
- Used by: `cli_dashboard.py`
## Data Flow
- Single `AnalysisState` Pydantic model passed by reference through all stages
- Large blobs (company_facts, filing_texts, exhibit_21) stripped before JSON serialization, restored in memory
- Stages write directly to state fields: `state.company`, `state.acquired_data`, `state.extracted`, `state.analysis`, `state.scoring`, `state.benchmark`
## Key Abstractions
- Purpose: Every data point carries provenance — source, confidence, timestamp
- Location: `src/do_uw/models/common.py`
- Pattern: `SourcedValue[str](value="...", source="10-K 2024", confidence=Confidence.HIGH, as_of=datetime)`
- Used on: All data fields in CompanyProfile and domain models
- Purpose: Unified brain data access; routes to `brain.duckdb` (primary) or `KnowledgeStore` (fallback)
- Location: `src/do_uw/knowledge/compat_loader.py`
- Pattern: `loader = BackwardCompatLoader(playbook_id=...); brain = loader.load_all()`
- Used by: `AnalyzeStage`, `ScoreStage`, `BenchmarkStage`
- Purpose: 359 D&O underwriting checks organized by category
- Location: `src/do_uw/brain/checks/{biz,exec,fin,fwrd,gov,lit,nlp,stock}/` (YAML source), compiled to `brain/checks.json` and `brain.duckdb`
- Categories: biz (business), exec (executives), fin (financials), fwrd (forward-looking), gov (governance), lit (litigation), nlp (NLP signals), stock (market)
- Pattern: Each check has `check_id`, `field_key`, `threshold_red/yellow/clear`, `factors`, `hazards`, `execution_mode`
- Purpose: Layer 2 inherent exposure score across 47 dimensions (H1-H7)
- Location: `src/do_uw/stages/analyze/layers/hazard/`
- Pattern: Computed pre-analyze from `ExtractedData`; IES score amplifies behavioral factor scores in SCORE stage
- Files: `dimension_h1_business.py` through `dimension_h7_emerging.py`, `hazard_engine.py`, `interaction_effects.py`
- Purpose: Claude API-powered structured extraction from SEC filing text
- Location: `src/do_uw/stages/extract/llm/`
- Contains: `extractor.py`, `prompts.py`, `cache.py`, `cost_tracker.py`, `schemas/` (Pydantic schemas per filing type)
- Pattern: Parallel extraction with per-schema Pydantic output; cached in `.cache/llm_extractions.db`
- Purpose: Industry-specific check overlays and scoring adjustments
- Location: `src/do_uw/knowledge/playbooks.py`, `playbook_data*.py`
- Pattern: Activated during RESOLVE based on SIC/NAICS → `state.active_playbook_id` set → consumed by `BackwardCompatLoader`
## Entry Points
- Location: `src/do_uw/cli.py`
- Triggers: `angry-dolphin analyze <TICKER>` or `do-uw analyze <TICKER>`
- Responsibilities: Load .env, auto-init brain.duckdb, create/resume state, run pipeline with Rich progress display, print QA report
- Location: `src/do_uw/pipeline.py` → `Pipeline.run(state)`
- Triggers: CLI analyze command
- Responsibilities: Sequential stage execution, validation gates, state persistence, callback notifications
- Location: `src/do_uw/dashboard/app.py`
- Triggers: `angry-dolphin dashboard`
- Responsibilities: FastAPI server for interactive worksheet review
- Location: `src/do_uw/cli_brain.py`
- Triggers: `angry-dolphin brain {status,explore,add,yaml}`
- Responsibilities: Brain DuckDB management, check authoring, effectiveness reporting
## Error Handling
- Each stage wraps `run()` body in try/except: marks stage FAILED, re-raises as `PipelineError`
- Individual analytical engines (classification, hazard, temporal, forensic, NLP) wrapped in their own try/except — failures do NOT block stage completion
- Acquisition clients use fallback chains (SEC primary → REST API fallback → web search)
- Non-critical enrichments (yfinance, industry playbook, brain telemetry) wrapped in try/except with warning logs only
- `PipelineError` propagates from `Pipeline.run()` to CLI; CLI prints error and exits code 1
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
