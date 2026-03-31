# External Integrations

**Analysis Date:** 2026-02-25

## APIs & External Services

**SEC EDGAR (Primary Data Source):**
- SEC Submissions API — company filing metadata
  - Endpoint: `https://data.sec.gov/submissions/CIK{cik}.json`
  - Client: `src/do_uw/stages/acquire/clients/sec_client.py` (`SECFilingClient`)
  - Auth: None (public API; SEC User-Agent header required: `do-uw/0.1.0`)
  - Rate limit: 10 req/sec enforced in `src/do_uw/stages/acquire/rate_limiter.py`
- SEC EDGAR Company Facts API — XBRL financial data
  - Endpoint: `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
  - Client: `src/do_uw/stages/acquire/clients/sec_client.py` (`SECFilingClient.acquire_company_facts`)
  - Auth: None (public API)
- SEC EDGAR EFTS Full-Text Search — fallback filing discovery
  - Endpoint: `https://efts.sec.gov/LATEST/search-index`
  - Client: `src/do_uw/stages/acquire/clients/sec_client.py` (`_fetch_from_efts`)
  - Auth: None (public API)
- SEC Company Tickers — ticker-to-CIK resolution
  - Endpoint: `https://www.sec.gov/files/company_tickers.json`
  - Client: `src/do_uw/stages/resolve/ticker_resolver.py`
  - Auth: None

**Anthropic API (LLM Extraction & Narratives):**
- Used for: structured data extraction from SEC filings, analyst narrative generation
  - SDK: `anthropic>=0.79.0` + `instructor>=1.14.0`
  - Auth: `ANTHROPIC_API_KEY` environment variable
  - Default model: `claude-haiku-4-5-20251001` (override via `DO_UW_LLM_MODEL`)
  - Extractor: `src/do_uw/stages/extract/llm/extractor.py` (`LLMExtractor`)
  - Narrative generator: `src/do_uw/stages/benchmark/narrative_generator.py`
  - Knowledge ingestion: `src/do_uw/knowledge/ingestion_llm.py`, `src/do_uw/knowledge/pricing_ingestion.py`
  - Batch validation: `src/do_uw/validation/batch.py`
  - Rate limit: proactive inter-request delays for TPM limits (default 40,000 TPM)
  - Max input token estimate: 190,000 tokens per filing

**Serper.dev Web Search (Blind Spot Detection):**
- Used for: litigation discovery, news, short seller reports, executive risk signals
  - SDK: `httpx` (direct REST calls)
  - Auth: `SERPER_API_KEY` environment variable
  - Endpoints: `https://google.serper.dev/search`, `https://google.serper.dev/news`
  - Client: `src/do_uw/stages/acquire/clients/serper_client.py`
  - Falls back to no-op (`search_fn = None`) if key not set; worksheet shows Data Quality Notice warning
  - Budget: configurable via `--search-budget` CLI flag (default 50 searches per analysis)

**Yahoo Finance via yfinance:**
- Used for: stock price history, company info, insider transactions, institutional holders, analyst recommendations, earnings dates, price targets, news
  - SDK: `yfinance>=1.1.0` (unofficial; unstable API)
  - Auth: None (scraping Yahoo Finance)
  - Client: `src/do_uw/stages/acquire/clients/market_client.py` (`MarketDataClient`)
  - Also retrieves sector ETF (SPDR ETFs mapped via `src/do_uw/brain/sectors.json`) and SPY benchmark data
  - All calls wrapped in try/except; partial data returned on failure

**financedatabase (Peer Group Discovery):**
- Used for: finding peer companies by sector/industry for benchmarking
  - SDK: `financedatabase>=2.3.1`
  - Auth: None (local GICS database)
  - Client: `src/do_uw/stages/extract/peer_group.py` (`_fetch_candidates_financedatabase`)
  - Falls back to hardcoded sector peers if unavailable

## Data Storage

**Databases:**
- Analysis Cache (SQLite)
  - Path: `.cache/analysis.db` (gitignored)
  - Client: `src/do_uw/cache/sqlite_cache.py` (`AnalysisCache`)
  - Purpose: TTL-based caching of SEC filings, market data, litigation results, web search
  - TTLs: 7 days (market), 30 days (news/litigation), 5–14 months (SEC filings)
- LLM Extraction Cache (SQLite)
  - Path: `.cache/llm_extractions.db` (gitignored)
  - Client: `src/do_uw/stages/extract/llm/cache.py` (`ExtractionCache`)
  - Purpose: Cache LLM extraction results by `(accession_number, form_type, schema_hash)`
- Knowledge Store (SQLite via SQLAlchemy)
  - Path: `src/do_uw/knowledge/knowledge.db`
  - ORM: `src/do_uw/knowledge/models.py`
  - Schema: managed by Alembic migrations at `src/do_uw/knowledge/migrations/`
  - Purpose: underwriter knowledge checks, patterns, red flags, pricing rules, playbooks
- Brain Store (DuckDB)
  - Path: `src/do_uw/brain/brain.duckdb`
  - Client: `src/do_uw/brain/brain_schema.py` (`connect_brain_db`)
  - Schema: 19 tables, 11 views; auto-initialized from `checks.json` on first CLI run
  - Purpose: runtime queryable knowledge model for checks, scoring, and pattern matching

**File Storage:**
- Local filesystem only
- Output directory: `output/{TICKER}-{DATE}/` — state.json, Word doc, HTML, Markdown, PDF

**Caching:**
- SQLite-based (see above); no Redis or Memcached

## Authentication & Identity

**Auth Provider:**
- None — no user authentication system
- API keys managed via environment variables loaded from `.env` by `python-dotenv`

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry or equivalent)

**Logs:**
- Python standard `logging` module throughout; logger names follow module path (e.g., `do_uw.stages.acquire.clients.sec_client`)
- Log level: WARNING in production (per `alembic.ini`); no structured logging format configured

**Cost Tracking:**
- LLM API costs tracked in `src/do_uw/stages/extract/llm/cost_tracker.py` (`CostTracker`)
- Reported per analysis run

## CI/CD & Deployment

**Hosting:**
- Local CLI tool only; no cloud hosting or deployment pipeline detected

**CI Pipeline:**
- None detected (no GitHub Actions, CircleCI, etc.)

## MCP Servers (Development Context)

These are Claude MCP tools available during development and agentic analysis sessions — not called from within the Python codebase directly:

- `edgartools` — SEC EDGAR filing retrieval (MCP boundary: ACQUIRE stage only)
- `brave-search` — web search with news/domain filtering (2,000 free/month quota)
- `playwright` — browser automation for dynamic site scraping
- `fetch` — simple URL content extraction
- `context7` — up-to-date library documentation
- `duckdb` — analytical queries against brain.duckdb
- `github` — dev workflow automation

**Critical constraint:** Subagents CANNOT access MCP tools. All MCP-based acquisition must happen in the main context before handing off to EXTRACT and later stages.

## Environment Configuration

**Required env vars:**
- `ANTHROPIC_API_KEY` — Claude LLM API; hard failure in knowledge ingestion, graceful degradation in extraction pipeline (falls back to regex-only mode via `--no-llm` flag)
- `SERPER_API_KEY` — Serper.dev web search; graceful degradation (blind spot detection disabled, Data Quality Notice shown in worksheet)

**Optional env vars:**
- `DO_UW_LLM_MODEL` — override default Claude model (default: `claude-haiku-4-5-20251001`)

**Secrets location:**
- `.env` file at project root (not committed; no `.env.example` detected)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Data Source Fallback Chains

The following fallback hierarchies are implemented in the ACQUIRE stage:

**SEC Filings:**
1. SEC Submissions API (`data.sec.gov/submissions/`)
2. SEC EFTS Full-Text Search (`efts.sec.gov`)
- Implemented via `FallbackChain` / `FallbackTier` in `src/do_uw/stages/acquire/fallback.py`

**Stock/Market Data:**
1. `yfinance` (Yahoo Finance)
2. Partial data returned on individual attribute failures (defensive per-field try/except)

**Litigation Discovery:**
1. Serper.dev web search (fires FIRST per design decision)
2. SEC EFTS search for 10-K Item 3 legal proceedings references

**LLM Extraction:**
1. `anthropic` + `instructor` (structured extraction)
2. Regex-only fallback (when `--no-llm` flag set or `ANTHROPIC_API_KEY` absent)

**Peer Group:**
1. `financedatabase` sector/industry lookup
2. Hardcoded sector fallback peers in `src/do_uw/stages/extract/peer_group.py`

---

*Integration audit: 2026-02-25*
