# Phase 2: Company Resolution & Data Acquisition - Research

**Researched:** 2026-02-07
**Domain:** SEC EDGAR integration, market data APIs, litigation data, rate limiting, caching, web search orchestration
**Confidence:** MEDIUM-HIGH (edgartools/yfinance verified via docs; SEC EDGAR APIs verified via official sources; SCAC/CourtListener partially verified; EFTS API partially documented)

## Summary

Phase 2 implements the RESOLVE and ACQUIRE pipeline stages. RESOLVE maps any US-listed ticker (or company name) to a full company identity via SEC EDGAR, and ACQUIRE gathers raw data from six source categories: SEC filings, market data, litigation, regulatory, news/sentiment, and blind spot discovery. The codebase already has Pydantic models (`CompanyProfile`, `AcquiredData`), pipeline stubs, and an SQLite cache -- Phase 2 replaces the stubs with real implementations.

The standard approach uses **edgartools** as the primary SEC EDGAR interface (MCP server already installed), **yfinance** for market data, **httpx** with rate limiting for direct API calls, and the **Brave Search MCP** for web-based discovery. The SEC's public APIs at `data.sec.gov` provide the company identity resolution backbone (submissions API, company_tickers.json). Rate limiting at 10 req/sec with proper User-Agent is mandatory for all SEC EDGAR requests.

**Primary recommendation:** Build a thin data client layer (`stages/resolve/` and `stages/acquire/clients/`) that wraps edgartools MCP calls for SEC data and httpx for direct API calls, with a central rate limiter (aiolimiter), cache integration (existing SQLite), and fallback chain orchestration. Each data source gets its own client module under 500 lines.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| edgartools (MCP) | Latest | SEC EDGAR filings, company identity, XBRL | Already installed as MCP server; production-ready SEC library with Company class, filing search, XBRL parsing; handles rate limiting internally |
| yfinance | >=0.2.36 | Stock prices, market data, analyst data | De facto standard for Yahoo Finance data in Python; provides Ticker.info, history, insider_transactions, institutional_holders, recommendations |
| httpx | >=0.28 (installed) | HTTP client for direct API calls | Already a dependency; async-capable; project mandates httpx over requests |
| rapidfuzz | >=3.0 | Fuzzy string matching for company name resolution | C++ backend, MIT licensed, faster than thefuzz; needed for company name -> ticker matching |
| aiolimiter | >=1.1 | Rate limiting for SEC EDGAR API calls | Leaky bucket algorithm for asyncio; precise control at 10 req/sec; lightweight, well-maintained |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Brave Search (MCP) | N/A | Web search for blind spot discovery, litigation, news | Already installed; use for broad discovery searches and gap-filling; 2,000 free/month |
| Playwright (MCP) | N/A | Browser automation for JavaScript-heavy sites | Already installed; use for Stanford SCAC (requires login), dynamic court databases |
| Fetch (MCP) | N/A | Simple URL content extraction | Already installed; use for fetching SEC filing documents, company IR pages |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| edgartools | sec-edgar-api (PyPI) | Lighter weight but less feature-rich; edgartools already installed as MCP server, has built-in rate limiting, and is the most comprehensive open-source SEC library |
| yfinance | financetoolkit | More comprehensive financial analysis, but heavier dependency; yfinance is simpler for raw data acquisition |
| rapidfuzz | thefuzz | API-compatible but slower (pure Python); rapidfuzz is the modern successor with C++ performance |
| aiolimiter | asyncio.Semaphore | Semaphore controls concurrency, not rate; aiolimiter provides true time-based rate limiting |

**Installation:**
```bash
uv add yfinance rapidfuzz aiolimiter
```

Note: edgartools is NOT added as a Python dependency -- it is accessed exclusively through the MCP server. httpx is already installed. Brave Search, Playwright, and Fetch are MCP servers, not Python packages.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  stages/
    resolve/
      __init__.py          # ResolveStage class (replace stub)
      sec_identity.py      # SEC EDGAR company resolution logic
      ticker_resolver.py   # Ticker/name -> CIK resolution with fuzzy matching
    acquire/
      __init__.py          # AcquireStage class (replace stub)
      orchestrator.py      # Acquisition orchestration with gates
      clients/
        __init__.py
        sec_client.py      # SEC EDGAR data client (filings via edgartools MCP)
        market_client.py   # yfinance market data client
        litigation_client.py # Litigation data client (web search + SCAC)
        regulatory_client.py # Regulatory data client (openFDA, EPA ECHO, etc.)
        news_client.py     # News/sentiment client (Brave Search)
        web_search.py      # Blind spot discovery web search orchestrator
      gates.py             # Data completeness gate definitions
      rate_limiter.py      # Shared rate limiter for SEC EDGAR
      fallback.py          # Fallback chain execution logic
```

### Pattern 1: Data Client Protocol
**What:** Each data source implements a common DataClient protocol with `acquire()`, `validate()`, and `cache_key()` methods.
**When to use:** Every data source client in the `clients/` directory.
**Example:**
```python
from typing import Protocol, Any
from do_uw.models.state import AnalysisState

class DataClient(Protocol):
    """Protocol for all data acquisition clients."""

    @property
    def name(self) -> str:
        """Human-readable client name for logging."""
        ...

    def acquire(self, state: AnalysisState) -> dict[str, Any]:
        """Acquire raw data and return it for storage in AcquiredData.

        Returns dict of raw data keyed by data type.
        Raises DataAcquisitionError on unrecoverable failure.
        """
        ...

    def cache_key(self, state: AnalysisState) -> str:
        """Generate cache key for this acquisition.

        Format: {client_name}:{ticker}:{date_qualifier}
        """
        ...
```

### Pattern 2: Fallback Chain
**What:** Each data source has a defined fallback chain. The system tries each tier in order, downgrades confidence on fallback, and logs which tier succeeded.
**When to use:** Every data acquisition that has multiple possible sources.
**Example:**
```python
from dataclasses import dataclass
from do_uw.models.common import Confidence

@dataclass
class FallbackTier:
    name: str
    confidence: Confidence
    acquire_fn: Callable[..., dict[str, Any] | None]

class FallbackChain:
    """Execute acquisition through a chain of fallback tiers."""

    def __init__(self, source_name: str, tiers: list[FallbackTier]) -> None:
        self.source_name = source_name
        self.tiers = tiers

    def execute(self, **kwargs: Any) -> tuple[dict[str, Any], Confidence, str]:
        """Try each tier until one succeeds.

        Returns: (data, confidence, tier_name)
        Raises: DataAcquisitionError if all tiers fail.
        """
        errors: list[str] = []
        for tier in self.tiers:
            try:
                result = tier.acquire_fn(**kwargs)
                if result is not None:
                    return result, tier.confidence, tier.name
            except Exception as e:
                errors.append(f"{tier.name}: {e}")

        raise DataAcquisitionError(
            f"All tiers failed for {self.source_name}: {errors}"
        )
```

### Pattern 3: Acquisition Gate
**What:** Hard and soft gates validate data completeness before proceeding to EXTRACT stage.
**When to use:** After all acquisition completes, before marking ACQUIRE stage as complete.
**Example:**
```python
from enum import StrEnum

class GateType(StrEnum):
    HARD = "HARD"  # Must pass to proceed
    SOFT = "SOFT"  # Warn but continue

@dataclass
class AcquisitionGate:
    name: str
    gate_type: GateType
    check_fn: Callable[[AcquiredData], bool]
    description: str

# Gate definitions per user decisions:
ACQUISITION_GATES = [
    AcquisitionGate("10-K/20-F", GateType.HARD,
                    lambda d: bool(d.filings.get("10-K") or d.filings.get("20-F")),
                    "Annual report required"),
    AcquisitionGate("10-Q/6-K", GateType.HARD,
                    lambda d: bool(d.filings.get("10-Q") or d.filings.get("6-K")),
                    "Quarterly report required"),
    AcquisitionGate("DEF14A", GateType.HARD,
                    lambda d: bool(d.filings.get("DEF14A")),
                    "Proxy statement required"),
    AcquisitionGate("Market Data", GateType.HARD,
                    lambda d: bool(d.market_data),
                    "Stock/market data required"),
    AcquisitionGate("Litigation", GateType.SOFT,
                    lambda d: bool(d.litigation_data),
                    "Litigation data recommended"),
    AcquisitionGate("News/Sentiment", GateType.SOFT,
                    lambda d: bool(d.web_search_results),
                    "News/sentiment data recommended"),
]
```

### Pattern 4: Rate Limiter Wrapper
**What:** A shared rate limiter that all SEC EDGAR direct API calls pass through.
**When to use:** Any direct httpx call to data.sec.gov or efts.sec.gov (edgartools MCP handles its own rate limiting).
**Example:**
```python
from aiolimiter import AsyncLimiter

# SEC EDGAR: 10 requests per second
SEC_RATE_LIMITER = AsyncLimiter(10, 1.0)

async def sec_request(client: httpx.AsyncClient, url: str) -> httpx.Response:
    """Make a rate-limited request to SEC EDGAR."""
    async with SEC_RATE_LIMITER:
        response = await client.get(
            url,
            headers={
                "User-Agent": "do-uw/0.1.0 (contact@example.com)",
                "Accept-Encoding": "gzip, deflate",
            },
        )
        response.raise_for_status()
        return response
```

### Pattern 5: Typed AcquiredData Evolution
**What:** The existing `AcquiredData` model (currently `dict[str, Any]` fields) should be extended with more specific typed sub-models for raw filing data, raw market snapshots, etc. while preserving backward compatibility.
**When to use:** Phase 2 implementation of the ACQUIRE stage.
**Key constraint:** The `AcquiredData` model holds RAW data. Parsed/structured data belongs in `ExtractedData` (Phase 3). Keep this boundary clean.

### Anti-Patterns to Avoid
- **Mixing acquisition and extraction:** The ACQUIRE stage stores RAW data. Do not parse XBRL, extract financial statements, or run analysis during acquisition. That is Phase 3 (EXTRACT).
- **Hardcoded filing type lists:** Store expected filing types in config, not code. FPI companies file 20-F instead of 10-K, 6-K instead of 8-K -- the mapping must be configurable.
- **Synchronous-only acquisition:** While Phase 2 may use synchronous calls initially, design the client interfaces to be async-friendly. yfinance is sync-only but SEC EDGAR calls can be async.
- **Silent failure:** Never assume "no data" = "no issue." Every failed acquisition attempt must be logged with the source tried, error encountered, and confidence downgrade.
- **Monolithic acquire function:** Each data source gets its own client module. The orchestrator calls them, it does not contain their logic.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SEC company lookup | Custom SEC EDGAR API wrapper | edgartools `Company(ticker)` via MCP | Handles CIK resolution, ticker mapping, company search, SIC codes, exchange data. Already installed. |
| Stock price history | Custom Yahoo Finance scraper | yfinance `Ticker(ticker).history()` | Handles Yahoo API authentication, rate limiting, data normalization. |
| Fuzzy company name matching | Custom string similarity | rapidfuzz `fuzz.ratio()` / `process.extractOne()` | C++ performance, handles unicode, multiple similarity metrics. |
| Rate limiting | Custom sleep/counter | aiolimiter `AsyncLimiter(10, 1.0)` | Precise leaky bucket algorithm, asyncio-native, handles bursts correctly. |
| SEC filing full text search | Custom EDGAR scraper | EFTS API at `efts.sec.gov/LATEST/search-index` | Free, no authentication, searches all EDGAR filings since 2001. |
| Company ticker/CIK mapping | Custom database | SEC's `company_tickers.json` / `company_tickers_exchange.json` | Official SEC data, updated in real-time, includes exchange info. |

**Key insight:** The SEC provides free, high-quality REST APIs for nearly everything needed. The primary challenge is not data access but orchestrating multiple sources with rate limiting, caching, and fallback chains -- which is the custom logic this phase must build.

## Common Pitfalls

### Pitfall 1: SEC EDGAR Rate Limit Violations
**What goes wrong:** Exceeding 10 req/sec causes temporary IP bans from SEC EDGAR.
**Why it happens:** Multiple clients (edgartools MCP + direct httpx calls) share the same IP but don't coordinate rate limits.
**How to avoid:** Use a single shared rate limiter for all direct SEC EDGAR calls. Edgartools MCP handles its own rate limiting internally -- do NOT double-limit MCP calls. Set User-Agent to `"do-uw/0.1.0 (contact@example.com)"` on all direct requests.
**Warning signs:** HTTP 403 responses from SEC, requests hanging, intermittent failures.

### Pitfall 2: MCP Tool Boundary Confusion
**What goes wrong:** Trying to use MCP tools (edgartools, Brave Search) from subagent stages or non-main context.
**Why it happens:** Per ARCH-08, MCP tools are only available in the main context. The pipeline stages run in the main context, but the architecture constraint is easy to forget when designing async workers or subagent tasks.
**How to avoid:** All MCP tool calls happen within `stages/acquire/` and `stages/resolve/`. No later stage (EXTRACT, ANALYZE, SCORE, etc.) should ever call an MCP tool. The boundary is: ACQUIRE produces raw data in `AcquiredData`, and everything downstream reads from that model.
**Warning signs:** Import of MCP-related code in extract/analyze/score stages.

### Pitfall 3: yfinance Instability
**What goes wrong:** yfinance breaks when Yahoo Finance changes their internal API, which happens regularly.
**Why it happens:** yfinance scrapes Yahoo Finance's internal endpoints, which are not a public API and change without notice.
**How to avoid:** Wrap all yfinance calls in try/except with graceful degradation. Cache successful responses aggressively. Have a fallback plan (web search for basic stock data). Pin yfinance version in uv.lock to avoid surprise breakages on upgrade.
**Warning signs:** `ConnectionError`, `JSONDecodeError`, missing keys in `Ticker.info` dict, empty DataFrames from `.history()`.

### Pitfall 4: Stanford SCAC Access Restrictions
**What goes wrong:** Attempting to scrape SCAC data violates their Terms of Service. The site requires login and prohibits automated access.
**Why it happens:** SCAC is a free academic resource but explicitly prohibits scraping, web crawlers, and automated data collection.
**How to avoid:** Use SCAC as a MANUAL reference, not an automated source. For automated litigation discovery, rely on: (1) broad web search (Brave Search MCP), (2) SEC 10-K Item 3 litigation disclosures, (3) CourtListener API, (4) law firm press releases found via web search. SCAC can be referenced as a validation source for manually confirmed cases.
**Warning signs:** 403/blocking from securities.stanford.edu, ToS violations.

### Pitfall 5: Confusing RAW vs. EXTRACTED Data
**What goes wrong:** Parsing and structuring data during the ACQUIRE stage instead of just storing raw responses.
**Why it happens:** Natural tendency to "do everything at once." The ACQUIRE stage fetches raw data; the EXTRACT stage (Phase 3) parses it into structured models.
**How to avoid:** `AcquiredData` stores raw JSON, raw text, raw API responses. `ExtractedData` stores parsed `SourcedValue[T]` fields. The boundary is: ACQUIRE produces dictionaries and strings; EXTRACT produces typed Pydantic models.
**Warning signs:** Import of Pydantic models from `models/financials.py` or `models/market.py` in acquire stage code; complex parsing logic in client modules.

### Pitfall 6: FPI Filing Type Mismatch
**What goes wrong:** Hard-coding "10-K" and "10-Q" everywhere, then failing for foreign private issuers who file 20-F and 6-K.
**Why it happens:** Most US companies file 10-K/10-Q, so it's easy to forget FPIs.
**How to avoid:** Create a filing type mapping: `{"annual": ["10-K", "20-F"], "quarterly": ["10-Q", "6-K"], "proxy": ["DEF 14A", "DEF14A"], "current": ["8-K", "6-K"]}`. The RESOLVE stage determines if the company is an FPI (from SEC submissions API `entityType` or filing history) and sets a flag. All subsequent filing lookups use the mapping.
**Warning signs:** Missing annual reports for companies like TSM, BABA, SAP; gate failures for known FPI companies.

### Pitfall 7: Brave Search Budget Exhaustion
**What goes wrong:** Running out of the 2,000/month free tier search budget mid-analysis.
**Why it happens:** Blind spot discovery can generate many search queries (company + each risk term, executive names + litigation terms, etc.).
**How to avoid:** Track search count in state or cache. Set a per-analysis budget (user-configurable, default ~50 searches). Prioritize searches by expected value. Batch related queries. Warn user when approaching limit.
**Warning signs:** 429 responses from Brave API, monthly budget depleted after a few analyses.

### Pitfall 8: Cache Key Collisions
**What goes wrong:** Different data for the same company gets overwritten in cache because cache keys aren't specific enough.
**Why it happens:** Using only ticker as cache key without including data source, date, and filing type.
**How to avoid:** Cache key format: `{source}:{ticker}:{data_type}:{date_qualifier}`. Example: `sec:AAPL:10-K:2025`, `yfinance:AAPL:history:2026-02-07`, `brave:AAPL:blind-spot:2026-02-07`.
**Warning signs:** Stale data after re-runs, missing data types in cache, incorrect cache hit rates.

## Code Examples

Verified patterns from official sources:

### edgartools Company Resolution (via MCP)
```python
# The edgartools MCP server provides these capabilities:
# Company lookup by ticker:
#   Company("AAPL") -> returns company with name, CIK, SIC, exchange, etc.
#
# Company properties available:
#   company.name          -> "Apple Inc."
#   company.cik           -> 320193
#   company.sic           -> "3571"
#   company.industry      -> "Electronic Computers"
#   company.exchange      -> "Nasdaq"
#   company.fiscal_year_end -> "0930" (MMDD format)
#   company.tickers       -> ["AAPL"]
#   company.get_exchanges() -> ["Nasdaq"]
#
# Company search by name:
#   find("Apple") -> returns list of matching companies
#
# Filing retrieval:
#   company.get_filings(form="10-K")                    -> all 10-K filings
#   company.get_filings(form="10-K", year=range(2022,2026)) -> 3 years of 10-Ks
#   company.get_filings(form="DEF 14A").latest()         -> latest proxy
#   company.get_filings(form="4")                        -> Form 4 insider trades
#   company.get_filings(form="20-F")                     -> FPI annual reports
#
# Since edgartools is an MCP server, these calls are made through
# the MCP protocol, not through Python imports. The stage code
# will invoke MCP tools and parse the responses.
```

### SEC EDGAR Direct API (via httpx)
```python
# Source: https://www.sec.gov/search-filings/edgar-application-programming-interfaces

# 1. Ticker -> CIK lookup
# GET https://www.sec.gov/files/company_tickers.json
# Returns: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}

# 2. CIK -> Company submissions (identity + filing history)
# GET https://data.sec.gov/submissions/CIK0000320193.json
# Returns: {
#   "cik": "320193",
#   "entityType": "operating",  # or "foreign-private-issuer"
#   "sic": "3571",
#   "sicDescription": "Electronic Computers",
#   "name": "Apple Inc.",
#   "tickers": ["AAPL"],
#   "exchanges": ["Nasdaq"],
#   "stateOfIncorporation": "CA",
#   "fiscalYearEnd": "0930",
#   "filings": { "recent": { ... }, "files": [...] }
# }

# 3. EFTS Full-Text Search (for Wells notices, subpoenas, etc.)
# GET https://efts.sec.gov/LATEST/search-index?q="Wells+notice"&forms=10-K&startdt=2023-01-01&enddt=2026-01-01
# Returns: {"total": {"value": N}, "filings": [...]}

# 4. XBRL Company Facts
# GET https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json
# Returns XBRL fact data for all filings

# All requests require:
# - User-Agent header: "do-uw/0.1.0 (contact@example.com)"
# - Rate limit: max 10 requests/second
# - No authentication required
```

### yfinance Market Data
```python
# Source: https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html

import yfinance as yf

ticker = yf.Ticker("AAPL")

# Company info (dict with 100+ keys)
info = ticker.info
market_cap = info.get("marketCap")          # int
sector = info.get("sector")                 # str
industry = info.get("industry")             # str
exchange = info.get("exchange")             # str ("NMS" for Nasdaq)
short_name = info.get("shortName")          # str
long_name = info.get("longName")            # str
full_time_employees = info.get("fullTimeEmployees")  # int
beta = info.get("beta")                     # float
fifty_two_week_high = info.get("fiftyTwoWeekHigh")   # float
fifty_two_week_low = info.get("fiftyTwoWeekLow")     # float

# Historical prices (DataFrame)
hist = ticker.history(period="1y")           # 1 year daily
hist_5y = ticker.history(period="5y")        # 5 year daily

# Insider transactions (DataFrame)
insider_txns = ticker.insider_transactions   # Recent insider trades
insider_purchases = ticker.insider_purchases # Aggregated purchases

# Institutional holders (DataFrame)
institutions = ticker.institutional_holders  # Top institutional holders
major = ticker.major_holders                 # Insider/institutional breakdown

# Analyst data
recommendations = ticker.recommendations    # Buy/hold/sell history
price_targets = ticker.analyst_price_targets # Target prices
upgrades = ticker.upgrades_downgrades        # Recent changes

# Financial statements (DataFrames)
income = ticker.income_stmt                  # Annual income statement
balance = ticker.balance_sheet               # Annual balance sheet
cashflow = ticker.cashflow                   # Annual cash flow

# Earnings dates
earnings_dates = ticker.earnings_dates       # Upcoming/recent earnings

# News
news = ticker.news                           # Recent news articles
```

### Rate Limiting with aiolimiter
```python
# Source: https://aiolimiter.readthedocs.io/

from aiolimiter import AsyncLimiter
import httpx

# 10 requests per 1 second = SEC EDGAR limit
rate_limiter = AsyncLimiter(10, 1.0)

SEC_USER_AGENT = "do-uw/0.1.0 (contact@example.com)"

async def fetch_sec_data(url: str) -> dict:
    """Fetch data from SEC EDGAR with rate limiting."""
    async with rate_limiter:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"User-Agent": SEC_USER_AGENT},
            )
            response.raise_for_status()
            return response.json()
```

### Fuzzy Company Name Matching with rapidfuzz
```python
# Source: https://rapidfuzz.github.io/RapidFuzz/

from rapidfuzz import fuzz, process

# Load SEC company list (from company_tickers.json)
companies = {
    "Apple Inc.": "AAPL",
    "Alphabet Inc.": "GOOGL",
    "Microsoft Corporation": "MSFT",
    # ... loaded from SEC data
}

def resolve_company_name(query: str, threshold: int = 80) -> list[tuple[str, str, int]]:
    """Resolve a company name to ticker(s) via fuzzy matching.

    Returns list of (company_name, ticker, score) sorted by score.
    """
    results = process.extract(
        query,
        companies.keys(),
        scorer=fuzz.WRatio,  # Weighted ratio handles word order
        limit=5,
        score_cutoff=threshold,
    )
    return [(name, companies[name], score) for name, score, _ in results]

# Example:
# resolve_company_name("apple") -> [("Apple Inc.", "AAPL", 95)]
# resolve_company_name("alphabet") -> [("Alphabet Inc.", "GOOGL", 97)]
```

### Cache Integration with TTL per Data Type
```python
# Extending existing AnalysisCache for data-source-specific TTLs

# Per user decisions:
CACHE_TTLS: dict[str, int] = {
    "10-K":      14 * 30 * 24 * 3600,  # 14 months
    "20-F":      14 * 30 * 24 * 3600,  # 14 months (FPI equivalent)
    "10-Q":       5 * 30 * 24 * 3600,  # 5 months
    "6-K":        5 * 30 * 24 * 3600,  # 5 months (FPI equivalent)
    "stock":      5 * 24 * 3600,       # 5 business days
    "news":      30 * 24 * 3600,       # 30 days
    "company":   30 * 24 * 3600,       # 30 days (identity doesn't change often)
    "litigation": 7 * 24 * 3600,       # 7 days (new filings happen)
}

def cache_key(source: str, ticker: str, data_type: str, qualifier: str = "") -> str:
    """Generate a cache key with source, ticker, data type, and optional qualifier."""
    parts = [source, ticker.upper(), data_type]
    if qualifier:
        parts.append(qualifier)
    return ":".join(parts)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom SEC EDGAR scraping | edgartools library + MCP server | 2024-2025 | Direct Python API or MCP protocol for all SEC data; built-in XBRL parsing |
| SEC CIK manual lookup | data.sec.gov REST APIs | 2022+ | Free JSON APIs, no auth required, real-time updates |
| FuzzyWuzzy for string matching | RapidFuzz | 2021+ | MIT license, C++ speed, same API compatibility |
| requests library | httpx | 2023+ | Async support, HTTP/2, type hints, modern Python |
| EDGAR rate limit was lenient | Strict 10 req/sec enforcement | 2024+ | SEC actively blocks IPs exceeding rate limit |

**Deprecated/outdated:**
- FuzzyWuzzy: Renamed to thefuzz, superseded by rapidfuzz for performance
- requests: Superseded by httpx for new projects (per CLAUDE.md mandate)
- Custom SEC scraping: edgartools handles the complexity of EDGAR navigation

## SEC EDGAR API Reference (Key Endpoints)

These are the SEC's free, official REST APIs that don't require authentication:

| Endpoint | URL Pattern | Purpose | Rate Limit |
|----------|-------------|---------|------------|
| Company Tickers | `https://www.sec.gov/files/company_tickers.json` | Ticker-CIK-name mapping for all filers | 10/sec |
| Company Tickers + Exchange | `https://www.sec.gov/files/company_tickers_exchange.json` | Same + exchange info | 10/sec |
| Submissions | `https://data.sec.gov/submissions/CIK{padded_cik}.json` | Company identity + filing history | 10/sec |
| Company Facts (XBRL) | `https://data.sec.gov/api/xbrl/companyfacts/CIK{padded_cik}.json` | All XBRL facts | 10/sec |
| Full-Text Search (EFTS) | `https://efts.sec.gov/LATEST/search-index?q={query}&forms={form}` | Search filing text | 10/sec |

**CIK formatting:** Submissions and Company Facts APIs require 10-digit zero-padded CIK (e.g., `CIK0000320193`). The company_tickers.json returns unpadded CIKs that must be zero-padded.

**User-Agent requirement:** All requests must include a User-Agent header with contact info. Format: `"CompanyName AdminContact@company.com"`.

**FPI detection:** The submissions API `entityType` field can indicate foreign private issuers. Filing history showing 20-F instead of 10-K is also a reliable FPI indicator.

## Data Source Fallback Chains (Per User Decisions)

### SEC Filings
1. **EdgarTools MCP** (HIGH) - Primary, uses edgartools Company class
2. **SEC EDGAR REST API** (HIGH) - Direct httpx to data.sec.gov
3. **Company IR page** (MEDIUM) - Via Fetch MCP or web search for filing URLs
4. **Web search** (LOW) - Via Brave Search MCP for filing content

### Market/Stock Data
1. **yfinance** (HIGH) - Primary, Ticker.info and Ticker.history
2. **Yahoo Finance web** (MEDIUM) - Via Fetch MCP to finance.yahoo.com
3. **Web search** (LOW) - Via Brave Search for basic market data

### Litigation (leads with web search per user decision)
1. **Web search - broad** (LOW initially) - Brave Search for company + litigation terms
2. **SEC 10-K Item 3** (HIGH) - Legal proceedings disclosure via edgartools
3. **CourtListener API** (MEDIUM) - Free REST API, requires auth token
4. **Law firm press releases** (LOW) - Via web search
5. Cross-reference all findings; upgrade confidence when corroborated

### Regulatory Data
1. **openFDA API** (HIGH) - Free REST API for FDA enforcement, recalls
2. **EPA ECHO** (HIGH) - Free REST API for environmental enforcement
3. **SEC Litigation Releases** (HIGH) - EDGAR search
4. **Web search** (LOW) - For DOJ, state AG, other regulatory actions

### News/Sentiment
1. **Brave Search** (LOW-MEDIUM) - Primary web search for news, sentiment
2. **yfinance news** (MEDIUM) - Ticker.news for recent articles
3. **Fetch MCP** (LOW) - For known URLs (Glassdoor, LinkedIn, etc.)

## FPI (Foreign Private Issuer) Handling

Foreign private issuers (FPIs) file different forms with the SEC:

| Domestic Form | FPI Equivalent | Purpose |
|--------------|----------------|---------|
| 10-K | 20-F | Annual report |
| 10-Q | 6-K | Quarterly/current report (combined) |
| 8-K | 6-K | Current events |
| DEF 14A | DEF 14A or none | Proxy (FPIs may not use US proxy rules) |
| Form 4 | Form 4 (if applicable) | Insider trading (may have exemptions) |

**Detection strategy:**
1. Check `entityType` in SEC submissions API response
2. Look for 20-F in filing history instead of 10-K
3. Set `is_fpi` flag on `CompanyProfile`
4. Use filing type mapping for all subsequent acquisitions

**Key difference:** FPIs may file under IFRS instead of US GAAP. The XBRL taxonomy differs. This affects Phase 3 (EXTRACT) more than Phase 2, but the ACQUIRE stage should tag the reporting framework.

## Brave Search Budget Management

Per user decisions: system tracks Brave Search usage and allows per-analysis budget.

**Implementation approach:**
- Store search count in SQLite cache with monthly key: `brave:count:2026-02`
- Default per-analysis budget: 50 searches (configurable via CLI flag)
- Priority ranking for blind spot searches (do high-value first):
  1. Company + "lawsuit" / "SEC investigation" / "fraud" (highest value)
  2. CEO/CFO name + "lawsuit" / "fired" / "investigation"
  3. Company + "short seller report" / specific short sellers
  4. Industry-specific risk terms
  5. Sentiment sweeps (lowest priority, skip if budget tight)
- Warn user when monthly usage exceeds 80% of 2,000 limit
- Allow `--search-budget N` CLI flag to override default

## Open Questions

Things that couldn't be fully resolved:

1. **EdgarTools MCP exact tool names**
   - What we know: EdgarTools exposes 20+ MCP tools for company lookup, filing retrieval, XBRL data, etc.
   - What's unclear: The exact MCP tool function names, parameters, and response formats are not documented publicly. The MCP server is installed and available, but tool discovery must happen at runtime.
   - Recommendation: During plan 02-01 implementation, run `/mcp` to discover available edgartools tools, then build the resolve stage around the actual tool signatures.

2. **CourtListener API rate limits and authentication**
   - What we know: CourtListener has a REST API v4.3 for searching court opinions and dockets. Free accounts are available. Auth uses API token.
   - What's unclear: Exact rate limits for free tier, whether securities cases are well-indexed, response latency for searches.
   - Recommendation: Create a free account, test search quality for securities litigation before committing to it as a primary source. It's a SECONDARY source in the fallback chain, so lower priority.

3. **EFTS API exact response schema**
   - What we know: `efts.sec.gov/LATEST/search-index` accepts `q`, `forms`, `startdt`, `enddt`, `from`, `size` parameters and returns JSON with `total` and `filings` keys.
   - What's unclear: Complete field list in each filing result, pagination behavior at scale, exact error codes.
   - Recommendation: Test the API directly during implementation with sample queries. The API is public and free.

4. **Sync vs. Async architecture**
   - What we know: yfinance is sync-only. httpx supports async. edgartools MCP is accessed through MCP protocol (sync from Claude's perspective). aiolimiter requires asyncio.
   - What's unclear: Whether to make the entire acquisition pipeline async (with yfinance wrapped in `asyncio.to_thread`) or keep it sync with manual rate limiting.
   - Recommendation: Start synchronous. Use `time.sleep()` for rate limiting direct SEC calls. yfinance is sync anyway. Async can be added later if performance requires it. This avoids complexity in Phase 2.

5. **Company name resolution: SEC list vs. yfinance vs. edgartools**
   - What we know: SEC provides company_tickers.json (~10,000 entries). EdgarTools has `find()` for company search. yfinance doesn't have company name search.
   - What's unclear: Whether to pre-load the SEC company list for fuzzy matching or rely on edgartools `find()`.
   - Recommendation: Use edgartools `Company(ticker)` for ticker resolution (primary path). For company NAME resolution, download `company_tickers.json`, cache it, and use rapidfuzz against the cached list. If ambiguous, present top matches to user.

## Sources

### Primary (HIGH confidence)
- EdgarTools official documentation: https://edgartools.readthedocs.io/en/latest/api/company/
- EdgarTools company search guide: https://edgartools.readthedocs.io/en/latest/guides/finding-companies/
- SEC EDGAR API documentation: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- yfinance API reference: https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html
- yfinance documentation: https://ranaroussi.github.io/yfinance/
- aiolimiter documentation: https://aiolimiter.readthedocs.io/
- openFDA API: https://open.fda.gov/apis/

### Secondary (MEDIUM confidence)
- SEC EDGAR rate limiting announcement: https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits
- SEC EDGAR submissions API field documentation (via multiple blog posts confirming field names)
- Stanford SCAC: https://securities.stanford.edu/ (access restrictions confirmed)
- CourtListener API: https://www.courtlistener.com/help/api/rest/ (v4.3 confirmed)
- RapidFuzz: https://rapidfuzz.github.io/RapidFuzz/

### Tertiary (LOW confidence)
- EFTS API exact parameters (partially documented, reverse-engineered from community usage)
- EdgarTools MCP server exact tool signatures (not publicly documented; must be discovered at runtime)
- yfinance `info` dict complete key list (varies by ticker, Yahoo changes without notice)
- CourtListener rate limits for free tier (not found in documentation)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - edgartools, yfinance, httpx, rapidfuzz, aiolimiter all verified via official docs
- Architecture: HIGH - Patterns based on existing codebase conventions (Protocol pattern, Pydantic models, client modules)
- SEC EDGAR API: HIGH - Official documentation confirms endpoints, rate limits, response structures
- Pitfalls: MEDIUM-HIGH - Based on known issues with yfinance instability, SCAC restrictions, SEC rate limiting
- FPI handling: MEDIUM - Filing type mappings are well-known but exact edgartools FPI support needs runtime verification
- EFTS API details: MEDIUM - Endpoint and basic parameters confirmed; exact response schema needs runtime testing
- MCP tool signatures: LOW - Must be discovered during implementation

**Research date:** 2026-02-07
**Valid until:** 2026-03-07 (30 days -- stable domain, APIs unlikely to change)
