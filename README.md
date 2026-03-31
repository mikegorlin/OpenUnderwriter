# D&O Liability Underwriting Worksheet System

A comprehensive Directors & Officers liability underwriting analysis system that ingests a stock ticker and produces an institutional-quality risk assessment worksheet. Built for D&O underwriters who need the deepest possible insight into public company risk profiles using 100% publicly available data.

## Features

- **7-Stage Pipeline**: RESOLVE, ACQUIRE, EXTRACT, ANALYZE, SCORE, BENCHMARK, RENDER
- **400 Brain Signals**: YAML-driven risk evaluation framework covering 8 peril categories and 16 causal chains
- **10-Factor Scoring**: Composite risk scoring with 11 CRF gates and tier classification (WIN to NO TOUCH)
- **Multi-Source Data Acquisition**: SEC EDGAR filings (10-K, 10-Q, 8-K, DEF 14A, Form 4), yfinance market data, Stanford SCAC litigation, CourtListener federal dockets, Brave Search + Exa semantic search, Financial Modeling Prep ratios
- **LLM Extraction**: Claude API with instructor for structured data extraction from SEC filings
- **Peer Benchmarking**: 7-metric sector-relative comparison with percentile proxy
- **5-Layer Narrative Architecture**: Verdict, thesis, evidence, implications, context with bull/bear framing
- **Three Output Formats**: HTML (primary, CIQ-level density), Word (.docx), PDF (via Playwright)
- **Meeting Prep**: 231-question framework across 5 sections with bear case generator
- **Visual Regression Testing**: Per-section screenshot comparison with golden baselines
- **Performance Budget**: Enforced render timing (HTML <10s, PDF <30s, pipeline <25min)

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- [Playwright](https://playwright.dev/) browsers (for PDF rendering and visual regression)

### Optional API Keys

Set these environment variables for enhanced data acquisition:

| Variable | Service | Purpose |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Anthropic Claude | LLM extraction from SEC filings (required) |
| `BRAVE_API_KEY` | Brave Search | Blind spot discovery and gap search |
| `EXA_API_KEY` | Exa | Neural semantic search for D&O-relevant content |
| `FMP_API_KEY` | Financial Modeling Prep | Supplemental financial ratios and ownership |
| `COURTLISTENER_API_KEY` | CourtListener | Federal court docket search (RECAP) |

## Setup

```bash
# Clone and install dependencies
git clone <repo-url>
cd do-uw
uv sync

# Install Playwright browsers (for PDF generation)
uv run playwright install chromium

# Set required API key
export ANTHROPIC_API_KEY="your-key-here"
```

## Usage

```bash
# Run full analysis for a ticker
uv run do-uw analyze AAPL

# Output appears in output/AAPL-YYYY-MM-DD/
#   AAPL_worksheet.html  (primary output)
#   AAPL_worksheet.docx  (Word document)
#   AAPL_worksheet.pdf   (PDF via Playwright)
#   AAPL_worksheet.md    (Markdown)
#   state.json           (cached analysis state)
#   charts/              (generated chart images)
#   sources/             (source documentation)
```

### Output Formats

**HTML** (primary): Institutional-quality layout matching S&P Capital IQ density. Two-column design, sticky headers, collapsible sections, interactive charts, tabbed financial statements, risk radar, and full source attribution.

**Word** (.docx): Professional document format consuming the same shared context layer as HTML. Suitable for email distribution and print.

**PDF**: Generated from HTML via Playwright headless Chromium. Includes running headers/footers, table of contents with page numbers, proper page breaks, and expanded detail sections.

## Testing

```bash
# Run all tests (5,000+)
uv run pytest

# Run visual regression tests (requires output/ with HTML files)
VISUAL_REGRESSION=1 uv run pytest tests/test_visual_regression.py -v

# Update golden baselines
VISUAL_REGRESSION=1 uv run pytest tests/test_visual_regression.py --update-golden -v

# Run performance budget tests (requires cached state.json)
PERFORMANCE_TESTS=1 uv run pytest tests/test_performance_budget.py -v

# Cross-ticker QA comparison
uv run python scripts/qa_compare.py
```

## Architecture

```
src/do_uw/
  cli.py              -- Typer CLI entry point
  models/             -- Pydantic state models (AnalysisState, CompanyProfile, etc.)
  stages/
    resolve/          -- Ticker to company identity
    acquire/          -- Data acquisition (SEC, stock, litigation, sentiment)
    extract/          -- Parse filings, extract structured data
    analyze/          -- Run checks, detect patterns
    score/            -- 10-factor scoring, red flags, allegation mapping
    benchmark/        -- Peer-relative comparisons
    render/           -- HTML/Word/PDF generation, context_builders/
  brain/              -- 400 YAML signals, framework, sections, composites
  config/             -- Scoring weights, thresholds, patterns (JSON)
tests/                -- 5,000+ tests mirroring src/ structure
```

## Data Sources

All data is 100% publicly available. No proprietary feeds or paid databases required.

| Source | Data | Method |
|--------|------|--------|
| SEC EDGAR | 10-K, 10-Q, 8-K, DEF 14A, Form 4, CORRESP, S-1, NT filings | EdgarTools MCP + LLM extraction |
| yfinance | Price history, volatility, short interest, analyst consensus, insider trades | Python API |
| Stanford SCAC | Securities class action filings | Playwright scraping |
| CourtListener | Federal court dockets (RECAP) | REST API |
| Brave Search | News, blind spot discovery, gap search | MCP |
| Exa | Neural semantic search for D&O content | REST API |
| FMP | Financial ratios, institutional ownership | REST API |
| USPTO | AI patent data | Web search |

## Brain Framework

The system uses a YAML-driven "brain" with 400 self-describing risk signals across 8 peril categories:

1. Securities Class Action (SCA)
2. Derivative Actions
3. Regulatory/Government
4. M&A Related
5. Cyber/Privacy
6. Employment
7. Bankruptcy/Insolvency
8. ESG/Climate

Each signal declares its own data needs, evaluation logic, and presentation format. The brain drives approximately 80% of the system's behavior.

## Versions

| Version | Date | Highlights |
|---------|------|------------|
| v1.0 | 2026-02-25 | MVP: 7-stage pipeline, 400 brain signals, 119 requirements |
| v1.1 | 2026-02-26 | Brain-driven acquisition, gap search, 14 requirements |
| v1.2 | 2026-02-28 | System intelligence, CI guardrails, feedback loop, 18 requirements |
| v2.0 | 2026-03-02 | Brain-driven architecture, facet rendering, learning loop, 28 requirements |
| v3.0 | 2026-03-06 | Professional-grade output, shared context, narratives, charts, MCP, 58 requirements |
