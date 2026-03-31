# Phase 4: Market, Trading & Governance Analysis - Research

**Researched:** 2026-02-08
**Domain:** Market signal extraction, insider trading analysis, governance forensics, sentiment analysis
**Confidence:** MEDIUM (yfinance data structures verified against docs; Form 4 XML and DEF 14A parsing based on web research + codebase analysis; Loughran-McDonald verified via official source)

## Summary

Phase 4 extends the EXTRACT stage with 19 new requirements across two sections: Market & Trading Signals (SECT4, 9 requirements) and Governance & Leadership Forensic (SECT5, 10 requirements). The work operates entirely on data already acquired in the ACQUIRE stage -- yfinance market data, SEC filing metadata (Form 4, 8-K, DEF 14A), filing text, news/sentiment, and litigation data.

The primary technical challenges are: (1) parsing yfinance data structures (DataFrames converted to dicts by market_client.py) for stock drops, insider trades, analyst sentiment, and earnings history; (2) extending filing_text.py to fetch DEF 14A text and Form 4 XML content; (3) building a Loughran-McDonald sentiment analyzer for earnings call text; (4) computing governance quality scores from proxy statement data; and (5) extending the existing market.py and governance.py models to hold all the new fields without exceeding the 500-line limit.

**Primary recommendation:** Split into 8-10 extractor modules organized by requirement clusters, following the existing ExtractionReport pattern. Extend ACQUIRE to fetch DEF 14A text, Form 4 XML, and additional filing types (S-3, 13D/13G) before extraction. Use pysentiment2 for Loughran-McDonald sentiment analysis. All rule-based (no LLM) except SECT5-10 which defers LLM to future phase.

## Standard Stack

### Core (already in project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yfinance | latest | Stock data, insider transactions, analyst data | Already in ACQUIRE, well-documented API |
| httpx | latest | HTTP for SEC EDGAR REST API | Already in project, async-capable |
| Pydantic v2 | latest | Data models with SourcedValue[T] | Already project standard |
| Python xml.etree.ElementTree | stdlib | Form 4 XML parsing | No extra dependency needed |
| re (stdlib) | stdlib | Text extraction from filing HTML | Already used in filing_text.py |

### Supporting (new)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pysentiment2 | 0.1.1 | Loughran-McDonald sentiment dictionary | SECT5-04 earnings call sentiment |
| (No new libraries needed) | - | DEF 14A parsing is custom regex | Built on existing filing_text.py pattern |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pysentiment2 | Raw L-M CSV + custom tokenizer | pysentiment2 handles stemming, stopwords, and scoring out of box; CSV gives more control but ~200 lines of boilerplate |
| xml.etree.ElementTree | lxml | lxml is faster but stdlib ET is sufficient for Form 4 (<50KB XML) and avoids new dependency |
| Custom DEF 14A parser | edgartools library | edgartools has proxy support but we deferred MCP integration; custom regex matches our existing filing_text.py pattern |

**Installation:**
```bash
uv add pysentiment2
```

## Architecture Patterns

### Recommended Extractor Structure

New extractors go in `src/do_uw/stages/extract/`:

```
src/do_uw/stages/extract/
  # Existing (Phase 3)
  company_profile.py        # SECT2
  financial_statements.py   # SECT3
  earnings_quality.py       # SECT3-06
  distress_models.py        # SECT3-07
  debt_analysis.py          # SECT3-08/09/10/11
  audit_risk.py             # SECT3-12
  tax_indicators.py         # SECT3-13
  peer_group.py             # SECT2-09/SECT3-05

  # New (Phase 4 - Market)
  stock_performance.py      # SECT4-01/02/03: price charts data, performance table, drop analysis
  insider_trading.py        # SECT4-04: Form 4 parsing, cluster detection, 10b5-1 classification
  short_interest.py         # SECT4-05: short interest vs peers, short seller reports
  earnings_guidance.py      # SECT4-06/07: guidance track record, analyst sentiment
  capital_markets.py        # SECT4-08: S-3/S-1/424B, Section 11 exposure
  adverse_events.py         # SECT4-09: consolidated scoring

  # New (Phase 4 - Governance)
  leadership_profiles.py    # SECT5-01/02/06: exec profiles, forensic, stability
  board_governance.py       # SECT5-03/07: board profiles, governance quality
  compensation_analysis.py  # SECT5-05: exec comp, incentive risk
  sentiment_analysis.py     # SECT5-04/09/10: L-M sentiment, broader signals, coherence
  ownership_structure.py    # SECT5-08: ownership, activist risk, 13D/13G

  # Existing infrastructure (unchanged)
  validation.py
  sourced.py
  xbrl_mapping.py
  profile_helpers.py
```

### Pattern 1: Extractor Function Signature (established pattern)

**What:** Every extractor follows the same function signature and return pattern.
**When to use:** All new extraction modules.
**Example:**
```python
# Source: existing audit_risk.py pattern
def extract_stock_drops(
    state: AnalysisState,
) -> tuple[list[StockDropEvent], ExtractionReport]:
    """Extract significant stock price declines from market data."""
    found_fields: list[str] = []
    warnings: list[str] = []

    market_data = get_market_data(state)
    history = market_data.get("history_1y", {})

    # ... extraction logic ...

    report = create_report(
        extractor_name="stock_drops",
        expected=EXPECTED_FIELDS,
        found=found_fields,
        source_filing="yfinance price history",
        warnings=warnings,
    )
    log_report(report)
    return drops, report
```

### Pattern 2: Model Extension with Sub-Models

**What:** Extend existing MarketSignals and GovernanceData with new typed sub-models.
**When to use:** When existing model fields are too simple for the new requirements.
**Example:**
```python
# In market.py -- extend MarketSignals with new typed sub-models
class StockDropEvent(BaseModel):
    """A single significant stock price decline event."""
    date: SourcedValue[str] | None = None
    drop_pct: SourcedValue[float] | None = None
    drop_type: str = ""  # "SINGLE_DAY" or "MULTI_DAY"
    sector_return: SourcedValue[float] | None = None
    trigger_event: SourcedValue[str] | None = None
    is_company_specific: bool = False

class StockDropAnalysis(BaseModel):
    """SECT4-03 drop analysis results."""
    single_day_events: list[StockDropEvent] = Field(default_factory=lambda: [])
    multi_day_events: list[StockDropEvent] = Field(default_factory=lambda: [])
    analysis_period_months: int = 18
```

### Pattern 3: ACQUIRE Stage Extension

**What:** Some extraction requires data not yet fetched in ACQUIRE stage.
**When to use:** When new filing types (S-3, 13D/13G) or text content (DEF 14A, Form 4 XML) are needed.
**Example:**
```python
# Extend filing_text.py to fetch DEF 14A text
def fetch_proxy_text(
    filings_metadata: dict[str, Any],
    cik: str,
) -> dict[str, str]:
    """Fetch and parse DEF 14A proxy statement text."""
    latest = _get_latest_filing(filings_metadata, "DEF 14A")
    # ... fetch and parse compensation tables, board info ...
```

### Anti-Patterns to Avoid

- **Model file bloat:** market.py (144 lines) and governance.py (127 lines) have room for growth but will exceed 500 lines if all new sub-models go there. Plan to split: market.py -> market.py + market_events.py; governance.py -> governance.py + governance_forensics.py.
- **Extraction in ACQUIRE:** All logic that transforms raw data into typed models belongs in EXTRACT, not ACQUIRE. ACQUIRE fetches raw data; EXTRACT interprets it.
- **Missing ExtractionReport:** Every extractor MUST produce an ExtractionReport. No silent partial extraction.
- **Assuming data availability:** yfinance methods frequently fail or return empty DataFrames. Every yfinance field access needs defensive None/empty checks. The existing `_safe_get_*` pattern in market_client.py handles this at the ACQUIRE level; extractors must handle it again at the EXTRACT level.

## Data Availability Assessment

### What ACQUIRE Already Provides

| Data Source | Available In State | Location in AcquiredData | Confidence |
|-------------|-------------------|--------------------------|------------|
| Stock price history (1y, 5y) | YES | `market_data.history_1y`, `market_data.history_5y` | HIGH |
| yfinance info dict (short interest, beta, etc.) | YES | `market_data.info` | MEDIUM |
| yfinance insider_transactions | YES | `market_data.insider_transactions` | MEDIUM |
| yfinance institutional_holders | YES | `market_data.institutional_holders` | MEDIUM |
| yfinance recommendations | YES | `market_data.recommendations` | MEDIUM |
| yfinance news | YES | `market_data.news` | LOW |
| SEC Form 4 metadata (URLs, dates) | YES | `filings["4"]` | HIGH |
| SEC 8-K metadata (URLs, dates) | YES | `filings["8-K"]` | HIGH |
| SEC DEF 14A metadata (URLs, dates) | YES | `filings["DEF 14A"]` | HIGH |
| 10-K filing text (Item 1, 7, 9A) | YES | `filings.filing_texts` | HIGH |
| Litigation data | YES | `litigation_data` | MEDIUM |
| News/sentiment | YES | `web_search_results` | LOW |

### What ACQUIRE Does NOT Yet Provide (Gaps)

| Data Needed | For Requirement | Gap Description | Resolution |
|-------------|-----------------|-----------------|------------|
| DEF 14A text content | SECT5-02/03/05/06/07 | filing_text.py only fetches 10-K text, not proxy | Extend filing_text.py to fetch DEF 14A |
| Form 4 XML content | SECT4-04 | Only metadata (accession, date) acquired, not XML body | Add Form 4 XML fetch to filing_text.py |
| S-3/S-1/424B metadata | SECT4-08 | Not in DOMESTIC_FILING_TYPES list | Add to sec_client.py filing type list |
| SC 13D/13G metadata | SECT5-08 | Not in DOMESTIC_FILING_TYPES list | Add to sec_client.py filing type list |
| 8-K text content | SECT5-06 | Only metadata, not Item 5.02 text | Extend filing_text.py for 8-K Item 5.02 |
| yfinance get_earnings_dates | SECT4-06 | Not currently fetched by market_client.py | Add to market_client.py |
| yfinance analyst_price_targets | SECT4-07 | Not currently fetched by market_client.py | Add to market_client.py |
| yfinance upgrades_downgrades | SECT4-07 | Not currently fetched by market_client.py | Add to market_client.py |
| Earnings call transcripts | SECT5-04 | Not acquired at all | Need web search or new source |

**Critical ACQUIRE gaps to address BEFORE extraction work begins.** This is the most important planning consideration: Phase 4 requires an ACQUIRE extension sub-phase first.

## yfinance Data Structures (MEDIUM Confidence)

### Price History (history_1y, history_5y)

After market_client.py's `_dataframe_to_dict()` conversion, history data is a dict of lists:

```python
{
    "Date": ["2024-01-02", "2024-01-03", ...],  # ISO date strings
    "Open": [150.0, 151.2, ...],
    "High": [152.0, 153.5, ...],
    "Low": [149.5, 150.0, ...],
    "Close": [151.5, 152.0, ...],
    "Volume": [50000000, 45000000, ...],
    "Dividends": [0.0, 0.0, ...],
    "Stock Splits": [0.0, 0.0, ...]
}
```

**Stock drop analysis approach:** Iterate Close prices, compute daily returns, flag days with returns < -5%. For multi-day analysis, compute rolling N-day returns (N=2,5,20).

### info Dict (Short Interest, Analyst Data)

Key fields available (MEDIUM confidence -- yfinance may change keys):

```python
# Short interest
info["sharesShort"]              # Total shares sold short
info["shortPercentOfFloat"]      # Short % of float (0-1 scale)
info["sharesShortPriorMonth"]    # Prior month comparison
info["shortRatio"]               # Days to cover

# Analyst
info["targetMeanPrice"]          # Mean analyst target
info["targetMedianPrice"]        # Median target
info["targetHighPrice"]          # Highest target
info["targetLowPrice"]           # Lowest target
info["numberOfAnalystOpinions"]  # Coverage count
info["recommendationKey"]        # "buy", "hold", etc.
info["recommendationMean"]       # 1.0 (strong buy) to 5.0 (sell)

# Fundamentals (already used in Phase 3)
info["currentPrice"]
info["fiftyTwoWeekHigh"]
info["fiftyTwoWeekLow"]
info["beta"]
```

### insider_transactions

After `_dataframe_to_dict()`, DataFrame columns (MEDIUM confidence):

```python
{
    "Insider Trading": ["John Smith", ...],  # OR "Insider" depending on version
    "Relation": ["Chief Executive Officer", ...],
    "Date": ["2024-03-15", ...],
    "Transaction": ["Sale", "Purchase", ...],
    "Cost": [150.0, ...],           # Price per share
    "Shares": [10000, ...],         # Number of shares
    "Value": [1500000, ...],        # Total value
    "Shares Total": [500000, ...]   # Remaining holdings
}
```

**Caution:** Column names may vary across yfinance versions. Extractors should use defensive access patterns.

### recommendations

After `_dataframe_to_dict()`, columns include:

```python
{
    "period": ["0m", "-1m", "-2m", "-3m"],
    "strongBuy": [5, 4, 6, 5],
    "buy": [15, 14, 16, 15],
    "hold": [10, 11, 9, 10],
    "sell": [2, 2, 1, 2],
    "strongSell": [0, 0, 0, 1]
}
```

### get_earnings_dates (NOT YET ACQUIRED)

Would provide DataFrame with columns:

```python
{
    "Earnings Date": ["2024-01-25", ...],  # Date indexed
    "EPS Estimate": [1.50, ...],
    "Reported EPS": [1.65, ...],
    "Surprise(%)": [10.0, ...]
}
```

**Known issues:** yfinance has documented bugs with earnings_dates (KeyError, incorrect data). Need defensive handling. Consider fallback to scraping.

## SEC Form 4 XML Parsing (MEDIUM Confidence)

### XML Structure

Form 4 XML follows the EDGAR Ownership XML Technical Specification (v3). Key elements:

```xml
<ownershipDocument>
    <issuer>
        <issuerCik>0001234567</issuerCik>
        <issuerName>Acme Corp</issuerName>
        <issuerTradingSymbol>ACME</issuerTradingSymbol>
    </issuer>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerCik>0009876543</rptOwnerCik>
            <rptOwnerName>John Smith</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
            <isOfficer>1</isOfficer>
            <officerTitle>Chief Executive Officer</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle><value>Common Stock</value></securityTitle>
            <transactionDate><value>2024-03-15</value></transactionDate>
            <transactionCoding>
                <transactionFormType>4</transactionFormType>
                <transactionCode>S</transactionCode>
                <!-- S=Sale, P=Purchase, A=Grant, M=Exercise, G=Gift -->
            </transactionCoding>
            <transactionAmounts>
                <transactionShares><value>10000</value></transactionShares>
                <transactionPricePerShare><value>150.00</value></transactionPricePerShare>
                <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction><value>490000</value></sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership><value>D</value></directOrIndirectOwnership>
            </ownershipNature>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
</ownershipDocument>
```

### 10b5-1 Plan Indicator

As of April 1, 2023, Form 4 includes a checkbox: "Check this box to indicate that a transaction was made pursuant to a contract, instruction or written plan that is intended to satisfy the affirmative defense conditions of Rule 10b5-1(c)."

In the XML, this is represented by the **`AFF10B5ONE`** element (confirmed by SEC's July 2025 update to Insider Transactions Data Sets). Filers must also provide the plan adoption date in the "Explanation of Responses" section (footnotes).

### Transaction Code Reference

| Code | Meaning | D&O Relevance |
|------|---------|---------------|
| P | Open market purchase | Positive signal -- insider buying |
| S | Open market sale | Risk signal if discretionary |
| A | Grant/award | Compensation, less risk-indicative |
| M | Exercise of derivative | Often precedes S (exercise + sell) |
| F | Tax withholding | Routine, not risk-indicative |
| G | Gift | Usually not risk-indicative |
| D | Disposition to issuer | Buyback participation |

### Parsing Approach

Use Python's `xml.etree.ElementTree` to parse Form 4 XML fetched from SEC EDGAR:

```python
import xml.etree.ElementTree as ET

def parse_form4_xml(xml_text: str) -> dict[str, Any]:
    root = ET.fromstring(xml_text)
    owner = root.findtext(".//rptOwnerName", "")
    title = root.findtext(".//officerTitle", "")

    transactions = []
    for txn in root.findall(".//nonDerivativeTransaction"):
        code = txn.findtext(".//transactionCode", "")
        shares = txn.findtext(".//transactionShares/value", "0")
        price = txn.findtext(".//transactionPricePerShare/value", "0")
        date = txn.findtext(".//transactionDate/value", "")
        acq_disp = txn.findtext(
            ".//transactionAcquiredDisposedCode/value", ""
        )
        transactions.append({...})
    return {"owner": owner, "title": title, "transactions": transactions}
```

**ACQUIRE extension needed:** Must fetch actual Form 4 XML content, not just metadata. Extend filing_text.py to download Form 4 primary documents by URL.

## DEF 14A Proxy Statement Parsing (LOW Confidence)

DEF 14A is the most difficult filing to parse programmatically. Unlike 10-K (which has standardized Item headings), proxy statements have varied formatting.

### What We Need to Extract

| Data Point | DEF 14A Section | Parsing Difficulty |
|------------|----------------|-------------------|
| Executive bios/tenure | Directors and Executive Officers | MEDIUM - usually in a named section |
| Board composition | Board of Directors | MEDIUM - table or list format |
| Independence status | Corporate Governance | MEDIUM - usually stated per director |
| Committee membership | Committees | MEDIUM - often in table form |
| Compensation tables (SCT) | Executive Compensation | HIGH - complex HTML tables |
| Say-on-pay results | Proposal results | MEDIUM - specific vote counts |
| CEO pay ratio | CEO Pay Ratio | LOW - single number, standardized |
| Related party transactions | Related Party Transactions | MEDIUM - variable location |
| Overboarding | Director bios | HIGH - must cross-reference other boards |
| Ownership table | Security Ownership | MEDIUM - standardized table |
| Dual-class structure | Voting rights | HIGH - varies significantly |

### Parsing Strategy

1. **Fetch DEF 14A text** via filing_text.py extension (same HTML fetch + strip approach as 10-K).
2. **Section extraction** using regex patterns similar to 10-K Item markers, but for proxy-specific sections: "EXECUTIVE COMPENSATION", "DIRECTOR COMPENSATION", "SECURITY OWNERSHIP", "CORPORATE GOVERNANCE", etc.
3. **Table extraction** for Summary Compensation Table (SCT) -- regex for dollar amounts in proximity to officer names.
4. **Fallback to yfinance info** for basic governance data (board size, institutional ownership percentage).

**Confidence: LOW** -- Proxy statement parsing is the least standardized SEC filing format. Plan for partial extraction with graceful degradation.

## Loughran-McDonald Sentiment Analysis (HIGH Confidence)

### Source

Official: University of Notre Dame Software Repository for Accounting and Finance
- CSV/XLSX dictionary available: `Loughran-McDonald_MasterDictionary_1993-2024.csv`
- Python module available from the same repository
- Seven sentiment categories: Negative, Positive, Uncertainty, Litigious, Strong Modal, Weak Modal, Constraining
- 2024 update added Complexity lexicon

### Python Implementation via pysentiment2

```python
import pysentiment2 as ps

lm = ps.LM()
tokens = lm.tokenize(earnings_call_text)
score = lm.get_score(tokens)
# Returns: {"Positive": int, "Negative": int, "Polarity": float, "Subjectivity": float}
```

**For D&O underwriting, the key signals are:**
- **Negative word count trend** across quarters -- increasing negativity = concern
- **Uncertainty word count** -- hedging language
- **Litigious word count** -- defensive language emergence
- **Polarity trend** -- deteriorating sentiment trajectory

### Limitation: Transcript Availability

Earnings call transcripts are NOT currently acquired. Sources:
1. **Seeking Alpha** -- requires authentication, may need Playwright MCP
2. **Company IR pages** -- variable format, would need web scraping
3. **Financial Modeling Prep API** -- free tier has limits

**Recommendation:** For v1, use 10-K MD&A text (already acquired in filing_texts["item7"]) as a proxy for management sentiment analysis. Defer full earnings call transcript acquisition to a future ACQUIRE enhancement. Flag this as a known limitation in the extraction report.

## Governance Quality Scoring (MEDIUM Confidence)

### Computation Approach

Governance quality score should be rule-based, computed from public data:

| Metric | Weight | Source | Scoring |
|--------|--------|--------|---------|
| Board independence ratio | 20% | DEF 14A / yfinance | >75% = 10, 50-75% = 7, <50% = 3 |
| CEO/Chair separation | 15% | DEF 14A | Separated = 10, Duality = 3 |
| Board refreshment | 10% | DEF 14A (new directors in 3yr) | 2+ new = 10, 1 = 7, 0 = 3 |
| Overboarding | 10% | DEF 14A (4+ boards) | 0 overboarded = 10, 1 = 7, 2+ = 3 |
| Committee structure | 15% | DEF 14A | All key committees = 10, missing any = 5 |
| Say-on-pay support | 15% | DEF 14A / yfinance | >90% = 10, 70-90% = 7, <70% = 3 |
| Average tenure | 15% | DEF 14A | 5-10yr = 10, <5 or >15 = 5 |

Score = weighted sum, normalized to 0-100. Peer-relative percentile rank.

**Store weights in config JSON** (not hardcoded) per project rules.

## Adverse Event Scoring (SECT4-09) (MEDIUM Confidence)

### Design

Aggregate all events from SECT4-03 through SECT4-08 with severity weights:

| Event Type | Severity Weight | Source Requirement |
|------------|----------------|-------------------|
| Single-day drop >5% | 1.0 per event | SECT4-03 |
| Single-day drop >10% | 2.0 per event | SECT4-03 |
| Single-day drop >20% | 4.0 per event | SECT4-03 |
| Multi-day decline >10% | 1.5 per event | SECT4-03 |
| Multi-day decline >25% | 3.0 per event | SECT4-03 |
| Insider cluster selling | 2.0 per cluster | SECT4-04 |
| 10b5-1 modification/termination | 1.5 | SECT4-04 |
| Short interest spike (>2x sector) | 1.5 | SECT4-05 |
| Activist short report | 3.0 per report | SECT4-05 |
| Earnings miss | 1.0 per miss | SECT4-06 |
| Consecutive earnings misses (3+) | 3.0 bonus | SECT4-06 |
| Guidance withdrawal | 2.0 | SECT4-06 |
| Analyst downgrade | 0.5 per downgrade | SECT4-07 |
| Recent offering (Section 11 exposure) | 2.0 per offering | SECT4-08 |

Total score = sum of severity-weighted events. Peer-ranked against primary peer group.

**Store severity weights in config JSON** per project rules.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Financial sentiment dictionary | Custom word lists | pysentiment2 with Loughran-McDonald | 7 sentiment categories, stemming, stopwords, validated in academic literature |
| Stock return computation | Custom price math | numpy/pandas computations on yfinance data | Edge cases: splits, dividends, timezone handling |
| XML parsing | Regex on XML text | xml.etree.ElementTree | Well-structured XML, regex breaks on attribute ordering |
| Date math for lookback periods | Manual timedelta | datetime.timedelta with business day awareness | Holidays, weekends, market closures |
| Cluster detection (insider selling) | Naive date windows | Sliding window algorithm | Need 30-day window with 3+ insider overlap |

**Key insight:** The hardest part of Phase 4 is not the computation -- it's the data parsing. yfinance and SEC filings return data in varied formats. Most engineering effort will go toward defensive parsing with graceful degradation.

## Common Pitfalls

### Pitfall 1: yfinance Data Instability
**What goes wrong:** yfinance columns change names between versions, methods raise KeyError or return empty DataFrames, timestamps shift format.
**Why it happens:** yfinance scrapes Yahoo Finance HTML, which changes without notice.
**How to avoid:** (1) Wrap every yfinance field access in try/except. (2) Use `.get()` for dict access, never direct indexing. (3) Validate column existence before processing. (4) Add yfinance version to ExtractionReport metadata.
**Warning signs:** Passing tests suddenly failing after `uv sync`.

### Pitfall 2: 500-Line Limit on Model Files
**What goes wrong:** Adding all SECT4/SECT5 model fields to market.py (144 lines) and governance.py (127 lines) pushes them over 500 lines.
**Why it happens:** 19 requirements each need multiple model fields with SourcedValue wrappers.
**How to avoid:** Plan model file splits BEFORE coding: market.py + market_events.py (or market_details.py); governance.py + governance_forensics.py. Each sub-model gets its own file if the parent grows past ~350 lines.
**Warning signs:** Model file exceeding 300 lines before all fields are added.

### Pitfall 3: ACQUIRE/EXTRACT Boundary Violation
**What goes wrong:** Extractors try to fetch data (HTTP calls) instead of working on already-acquired data.
**Why it happens:** EXTRACT needs data (DEF 14A text, Form 4 XML) that ACQUIRE doesn't yet provide.
**How to avoid:** Phase 4 MUST begin with ACQUIRE extensions that fetch the missing data. Only then do EXTRACT modules run. Clear separation: ACQUIRE fetches raw bytes/text, EXTRACT parses into typed models.
**Warning signs:** Import of httpx or rate_limiter in any EXTRACT module.

### Pitfall 4: Assuming All Companies Have All Data
**What goes wrong:** Extractor fails because company has no Form 4 filings, no DEF 14A, no earnings guidance, no short interest data.
**Why it happens:** Small companies, recent IPOs, foreign filers, and companies with unusual structures may lack standard disclosures.
**How to avoid:** Every extractor gracefully returns empty/partial results with LOW confidence and appropriate warnings in ExtractionReport. NEVER raise on missing data -- flag it.
**Warning signs:** Exception during extraction instead of degraded result.

### Pitfall 5: DEF 14A Parsing Over-Ambition
**What goes wrong:** Trying to parse every field from the proxy statement results in brittle regex that breaks across companies.
**Why it happens:** DEF 14A has the least standardized format of all SEC filings.
**How to avoid:** Focus on high-value, more standardized sections first (compensation summary table, board independence, say-on-pay results). Accept LOW confidence for text-extracted governance data. Use yfinance info dict as fallback for basic governance metrics.
**Warning signs:** Regex patterns exceeding 200 characters, or more than 10 regex alternatives.

### Pitfall 6: ExtractStage Orchestrator Bloat
**What goes wrong:** Adding 10+ new extractor calls to ExtractStage.__init__.py pushes it past 500 lines.
**Why it happens:** Current ExtractStage.run() is 373 lines with 8 extractors. Adding 10+ more is +150-200 lines.
**How to avoid:** Split orchestration into sub-orchestrators: `_run_financial_extractors()`, `_run_market_extractors()`, `_run_governance_extractors()`. Or create separate `MarketExtractStage` and `GovernanceExtractStage` classes that ExtractStage delegates to.
**Warning signs:** ExtractStage.__init__.py exceeding 400 lines mid-implementation.

## Code Examples

### Stock Drop Analysis

```python
# From yfinance history dict to stock drop events
def _find_single_day_drops(
    history: dict[str, Any],
    threshold_pct: float = -5.0,
) -> list[dict[str, Any]]:
    """Find single-day price drops exceeding threshold."""
    closes = history.get("Close", [])
    dates = history.get("Date", [])

    if len(closes) < 2 or len(dates) != len(closes):
        return []

    drops: list[dict[str, Any]] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        curr = closes[i]
        if prev is None or curr is None or prev == 0:
            continue
        pct_change = ((curr - prev) / prev) * 100.0
        if pct_change <= threshold_pct:
            drops.append({
                "date": dates[i],
                "drop_pct": round(pct_change, 2),
                "close": curr,
                "prev_close": prev,
            })
    return drops
```

### Insider Cluster Detection

```python
# Detect 3+ insiders selling within 30-day window
from datetime import datetime, timedelta

def _detect_cluster_selling(
    transactions: list[dict[str, Any]],
    window_days: int = 30,
    min_insiders: int = 3,
) -> list[dict[str, Any]]:
    """Identify cluster selling events."""
    # Filter to sales only
    sales = [t for t in transactions if t.get("type") in ("S", "Sale")]
    sales.sort(key=lambda t: t.get("date", ""))

    clusters: list[dict[str, Any]] = []
    for i, anchor in enumerate(sales):
        anchor_date = _parse_date(anchor.get("date", ""))
        if anchor_date is None:
            continue
        window_end = anchor_date + timedelta(days=window_days)
        window_insiders: set[str] = {anchor.get("insider", "")}

        for j in range(i + 1, len(sales)):
            other_date = _parse_date(sales[j].get("date", ""))
            if other_date is None:
                continue
            if other_date > window_end:
                break
            window_insiders.add(sales[j].get("insider", ""))

        if len(window_insiders) >= min_insiders:
            clusters.append({
                "start_date": anchor.get("date"),
                "insider_count": len(window_insiders),
                "insiders": sorted(window_insiders),
            })
    return clusters
```

### Governance Quality Score

```python
# Rule-based governance quality scoring
def _compute_governance_score(
    board: BoardProfile,
    compensation: CompensationFlags,
    weights: dict[str, float],
) -> float:
    """Compute normalized governance quality score (0-100)."""
    score = 0.0
    max_score = 0.0

    # Independence ratio
    if board.independence_ratio and board.independence_ratio.value is not None:
        w = weights.get("independence", 0.20)
        ratio = board.independence_ratio.value
        factor = 10 if ratio > 0.75 else (7 if ratio > 0.5 else 3)
        score += factor * w
        max_score += 10 * w

    # CEO/Chair duality
    if board.ceo_chair_duality and board.ceo_chair_duality.value is not None:
        w = weights.get("ceo_chair", 0.15)
        factor = 10 if not board.ceo_chair_duality.value else 3
        score += factor * w
        max_score += 10 * w

    # ... other metrics ...

    return (score / max_score * 100.0) if max_score > 0 else 0.0
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No 10b5-1 disclosure on Form 4 | Checkbox + adoption date required | April 2023 | Can now distinguish planned vs discretionary trades from filing |
| Harvard IV-4 for financial sentiment | Loughran-McDonald (finance-specific) | ~2011, widely adopted | L-M has finance-specific categories (litigious, uncertainty, constraining) |
| SEC filings text via SGML | SEC filings via structured XML/HTML | Ongoing | Form 4 is clean XML; 10-K/DEF 14A still messy HTML |
| Manual proxy statement review | Partial automated extraction possible | Current | Still no standard API for DEF 14A structured data |

**Deprecated/outdated:**
- Harvard IV-4 dictionary for financial text: superseded by Loughran-McDonald for financial domain
- yfinance `earnings_history` attribute: known bugs, prefer `get_earnings_dates()` with error handling

## Open Questions

### 1. Earnings Call Transcript Source
- **What we know:** Seeking Alpha, company IR pages, and Financial Modeling Prep have transcripts. pysentiment2 can analyze them.
- **What's unclear:** None of these are currently in our ACQUIRE pipeline. Seeking Alpha requires authentication.
- **Recommendation:** For v1, use 10-K Item 7 (MD&A) text as proxy for management sentiment. Document this as a known limitation. Defer full transcript acquisition to ACQUIRE enhancement in later phase.

### 2. DEF 14A Parsing Reliability
- **What we know:** Proxy statements have varied formatting. No standard API for structured data extraction.
- **What's unclear:** How reliable regex-based extraction will be across different companies.
- **Recommendation:** Start with high-confidence fields (compensation totals from SCT, say-on-pay votes, board size) and yfinance fallbacks. Mark all DEF 14A-extracted data as MEDIUM confidence at best.

### 3. Short Interest Time Series
- **What we know:** yfinance info dict has current short interest and prior month. No time series API.
- **What's unclear:** How to build 6-month trend without historical snapshots.
- **Recommendation:** Use current vs prior month for direction. For trend, consider storing snapshots in DuckDB cache across runs. For v1, classify trend as RISING/STABLE/DECLINING based on current vs prior month delta.

### 4. Activist Investor Identification
- **What we know:** 13D filings indicate activist intent. Known activists include Icahn, Elliott, ValueAct, Trian, Starboard, etc.
- **What's unclear:** How to maintain an up-to-date activist investor list.
- **Recommendation:** Store known activist funds in config JSON (not hardcoded). Check institutional_holders from yfinance against this list. Also check 13D filing metadata if acquired.

### 5. Scope of ACQUIRE Extension
- **What we know:** Phase 4 requires 7+ new data items from ACQUIRE.
- **What's unclear:** Whether ACQUIRE extensions should be a separate plan or bundled with extraction plans.
- **Recommendation:** Create a dedicated ACQUIRE extension plan (Plan 04-01) before extraction work. This plan extends market_client.py, sec_client.py, and filing_text.py with the missing data sources.

### 6. ExtractStage Orchestrator Growth
- **What we know:** Current __init__.py is 373 lines with 8 extractors. Phase 4 adds 10+ more.
- **What's unclear:** Best splitting strategy for the orchestrator.
- **Recommendation:** Create helper functions `_run_market_extractors()` and `_run_governance_extractors()` in __init__.py. If it still exceeds 500 lines, split into extract_market.py and extract_governance.py sub-orchestrators.

## Planning Considerations

### Recommended Plan Ordering

1. **Plan 04-01: ACQUIRE Extension** -- Add missing data to market_client.py (earnings_dates, analyst_price_targets, upgrades_downgrades), sec_client.py (S-3, 13D/13G filing types), and filing_text.py (DEF 14A text, Form 4 XML, 8-K Item 5.02 text). This MUST come first.

2. **Plan 04-02: Market Model Extension** -- Extend market.py with new sub-models (StockDropEvent, StockDropAnalysis, InsiderTransaction, EarningsGuidanceRecord, AnalystSentimentProfile, CapitalMarketsActivity, AdverseEventScore). Split to market_events.py if needed.

3. **Plan 04-03: Governance Model Extension** -- Extend governance.py with new sub-models (LeadershipProfile, BoardForensicProfile, CompensationAnalysis, OwnershipStructure, SentimentProfile). Split to governance_forensics.py if needed.

4. **Plans 04-04 through 04-08: Extractors** -- One plan per extractor cluster:
   - 04-04: Stock performance + drop analysis (SECT4-01/02/03)
   - 04-05: Insider trading + short interest (SECT4-04/05)
   - 04-06: Earnings guidance + analyst sentiment (SECT4-06/07)
   - 04-07: Capital markets + adverse events (SECT4-08/09)
   - 04-08: Leadership profiles + stability (SECT5-01/02/06)
   - 04-09: Board governance + compensation (SECT5-03/05/07)
   - 04-10: Ownership + sentiment + coherence (SECT5-04/08/09/10)

5. **Plan 04-11: ExtractStage Integration** -- Wire all new extractors into the orchestrator with dependency ordering.

6. **Plan 04-12: Config files** -- Create governance_weights.json (governance quality scoring weights) and adverse_events.json (event severity weights).

### Dependency Chain

```
04-01 (ACQUIRE extension)
  |
  +-- 04-02 (Market models) ----+
  |                              |
  +-- 04-03 (Governance models) -+-- 04-04..04-10 (Extractors) --> 04-11 (Orchestrator)
                                                                      |
                                                               04-12 (Config)
```

## Sources

### Primary (HIGH confidence)
- yfinance official API reference: https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html
- Loughran-McDonald Master Dictionary: https://sraf.nd.edu/loughranmcdonald-master-dictionary/
- SEC Form 4 XML Technical Specification (v3): https://www.sec.gov/info/edgar/ownershipxmltechspec-v3.pdf
- SEC Rule 10b5-1 amendments fact sheet: https://www.sec.gov/files/33-11138-fact-sheet.pdf
- Existing codebase: market_client.py, sec_client.py, filing_text.py, market.py, governance.py

### Secondary (MEDIUM confidence)
- pysentiment2 documentation: https://nickderobertis.github.io/pysentiment/index.html
- Form 4 transaction codes: https://secdatabase.com/Articles/tabid/42/ArticleID/10/Form-4-Transaction-Code-Definitions.aspx
- SEC Form 4/5 10b5-1 disclosure changes: https://www.toppanmerrill.com/blog/rule-10b5-1-insider-trading-form-4-and-5-disclosure-changes-and-form-144-deadline-extended/
- SEC S-3 shelf registration guidance: https://viewpoint.pwc.com/dt/us/en/pwc/pwc_sec_volume/pwc_sec_volume_US/2000_registration_un_US/sec_2120_form_s3_US.html
- yfinance info dict keys: https://zoo.cs.yale.edu/classes/cs458/lectures/yfinance.html

### Tertiary (LOW confidence)
- yfinance earnings_dates issues: https://github.com/ranaroussi/yfinance/issues/1932 -- known bugs, data may be unreliable
- DEF 14A parsing approaches: general web search results -- no authoritative standard parser exists
- Activist investor identification: web search -- requires maintained list

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - using existing project libraries + one new (pysentiment2)
- Architecture: HIGH - follows established extractor pattern from Phase 3
- Data structures: MEDIUM - yfinance may change, SEC XML verified against spec
- DEF 14A parsing: LOW - no standard approach, requires custom regex
- Pitfalls: HIGH - informed by actual codebase constraints and predecessor failures

**Research date:** 2026-02-08
**Valid until:** 2026-03-10 (30 days -- stable domain, yfinance may update)
