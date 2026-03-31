# Phase 2: Company Resolution & Data Acquisition - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Resolve any US-listed stock ticker (or company name) to a full company identity, then acquire all raw data from external sources (SEC filings, market data, litigation, regulatory, news) — completing the RESOLVE and ACQUIRE pipeline stages. Includes rate limiting, caching, fallback chains, data completeness gates, and proactive blind spot discovery. FPIs (foreign private issuers) on US exchanges are in scope.

</domain>

<decisions>
## Implementation Decisions

### Company resolution strategy
- Input can be ticker OR company name — system handles both
- Fuzzy match on company name, auto-proceed with best match when unambiguous
- If ambiguous (multiple strong matches), present options to user with company size and industry context
- Always resolve to the parent entity level (e.g., GOOG and GOOGL both → Alphabet Inc.)
- Foreign private issuers (FPIs) listed on US exchanges are supported (they file 20-F instead of 10-K, 6-K instead of 8-K)
- Recently IPO'd companies: proceed with whatever filings exist, flag gaps prominently — do not hard-fail on missing history

### Data source priority & fallback behavior
- SEC filings fallback chain: EdgarTools MCP → SEC EDGAR REST API → company IR page → web search. Try every fallback before marking unavailable.
- Litigation data: web search fires FIRST for broad discovery, then Stanford SCAC and SEC filings in parallel for structured data. Merge and cross-reference all results.
- Market/stock data: yfinance primary, daily close sufficient (no intraday needed). Fallback to Yahoo Finance web → web search.
- Partial data: actively attempt to fill gaps from secondary sources before accepting. Store what's available, mark missing fields with confidence level and source.

### Acquisition completeness gates
- **Hard gates (must pass to proceed):** SEC filings (10-K or 20-F, 10-Q or 6-K, DEF 14A) and stock/market data. Without these, the worksheet cannot answer core questions.
- **Soft gates (warn but continue):** Litigation sources, regulatory data, news/sentiment. Flag gaps prominently but don't halt the pipeline.
- Hard gate failure behavior: retry each source once after a delay, then halt with clear explanation of what's missing and why.
- Filing lookback: 3 years of filings (3 annual reports, trailing quarterly reports, 3 proxy statements)
- Litigation lookback: 10 years (per roadmap requirement for securities class actions)
- Data freshness/staleness thresholds (filing-type specific):
  - 10-K/20-F: stale after 14 months
  - 10-Q/6-K: stale after 5 months
  - Stock data: stale after 5 business days
  - News/sentiment: stale after 30 days

### Blind spot discovery scope
- Proactive web searches run BOTH before and after structured acquisition
  - Before: broad sweep to cast a wide net, inform what to look for in structured sources
  - After: targeted gap-filling searches for what structured sources missed
- Web-sourced findings are presented inline with confidence tags (HIGH/MEDIUM/LOW) alongside structured data — not in a separate section
- Search budget: system tracks Brave Search usage count, warns when approaching the 2,000/month free tier limit, allows user to set a per-analysis search budget
- Cross-validation requirement per CLAUDE.md: web findings flagged as LOW confidence unless corroborated by 2+ sources

### Claude's Discretion
- Exact number and terms for blind spot discovery searches (broad vs. focused based on initial signals)
- SEC EDGAR rate limiting implementation (must stay under 10/sec with proper User-Agent)
- Cache key design and invalidation strategy
- Specific retry delays and backoff patterns
- How to handle FPI filing type differences (20-F vs 10-K mapping)

</decisions>

<specifics>
## Specific Ideas

- User emphasized "we need to answer the questions" — the system exists to surface every signal an underwriter needs. Completeness matters more than speed.
- Litigation discovery should lead with web search (broad net) then confirm with structured sources (SCAC, SEC) — not the other way around
- Company IR pages are a valid fallback source for SEC filings when EDGAR sources fail

</specifics>

<deferred>
## Deferred Ideas

- **IPO-specific analysis volume** — User wants a separate analysis mode for recently IPO'd companies with deep S-1 analysis. This is a new capability that warrants its own phase.
- **IPO litigation volume** — Separate litigation analysis tailored to IPO-specific risks and Section 11 claims.

</deferred>

---

*Phase: 02-company-resolution-data-acquisition*
*Context gathered: 2026-02-07*
