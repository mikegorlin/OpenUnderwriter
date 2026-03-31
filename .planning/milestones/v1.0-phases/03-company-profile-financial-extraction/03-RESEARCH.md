# Phase 3: Company Profile & Financial Extraction - Research

**Researched:** 2026-02-07
**Domain:** SEC XBRL financial extraction, company profile parsing, distress scoring, peer group construction
**Confidence:** MEDIUM (edgartools API verified via docs; distress formulas verified via multiple sources; peer group data availability partially verified)

## Summary

Phase 3 transforms raw acquired data (SEC filing metadata, market data from Phase 2) into structured facts for 24 requirements across Company Profile (SECT2) and Financial Health (SECT3). The core technical challenges are: (1) XBRL financial data extraction from SEC filings, (2) text-based extraction from filing HTML/text for non-XBRL data, (3) computing four distress indicator models with sector-appropriate variants, (4) constructing meaningful peer groups from free data sources, and (5) building a validation framework that prevents silent incompleteness and imputation.

The established approach is to use the SEC EDGAR Company Facts REST API (`data.sec.gov/api/xbrl/companyfacts/`) as the primary XBRL data source, supplemented by edgartools for filing-level XBRL statement parsing and DataFrame conversion. For text extraction (Exhibit 21, business descriptions, audit information), direct HTML parsing of SEC filing documents via httpx + a lightweight HTML parser is the standard approach. Distress scores (Z-Score, M-Score, O-Score, F-Score) have well-established formulas that can be implemented directly -- no library needed.

**Primary recommendation:** Use SEC Company Facts API for structured XBRL data (fast, comprehensive, one call per company), edgartools library for filing-level statement parsing and multi-period stitching, and direct SEC filing text parsing for non-XBRL content (Exhibit 21, Item 1 business description, audit report). Build the ~50 concept XBRL mapping table as a JSON config file. Implement all four distress models directly (no external library) for full control over edge cases. Use yfinance `info` dict + FinanceDatabase for peer group construction signals.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| edgartools | latest (PyPI) | Filing-level XBRL parsing, financial statement extraction, DataFrame conversion | Best-in-class SEC EDGAR Python library; handles XBRL statement parsing, multi-period stitching, and pandas integration. MCP server already installed. |
| SEC Company Facts API | REST (no lib) | Bulk XBRL data retrieval per company | Official SEC API at `data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` -- returns ALL XBRL facts for a company in one call. Free, no auth, real-time updates. Already using SEC REST APIs in Phase 2. |
| httpx | >=0.28 (installed) | HTTP client for SEC filing content | Already in dependencies. Rate-limited via `rate_limiter.py`. |
| yfinance | >=1.1.0 (installed) | Market data, company info, sector/industry classification | Already in dependencies. Provides `sectorKey`, `industryKey`, `sectorDisp`, `industryDisp`, `marketCap`, `fullTimeEmployees`, `longBusinessSummary`. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| financedatabase | >=2.2 | Peer group construction: filter equities by sector/industry/country | For finding same-industry peers. 300K+ symbols with sector/industry classification. Free, open-source. |
| lxml or html.parser | stdlib/>=5.0 | Parse SEC filing HTML for text extraction | For Exhibit 21 subsidiaries, Item 1 business description, audit reports -- structured text in HTML filings. Prefer stdlib `html.parser` to avoid new dependency. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SEC Company Facts API | edgartools `company.get_facts()` | edgartools wraps the same API but adds overhead. Direct API call is simpler for bulk concept extraction. Use edgartools for filing-level statement parsing instead. |
| financedatabase | py-gics + manual SIC mapping | py-gics only provides GICS hierarchy, not a ticker database. FinanceDatabase provides the ticker list needed for peer filtering. |
| Hand-rolled distress models | External library (e.g., pyfolio) | No Python library implements all four models (Z, M, O, F) together. Formulas are straightforward (4-9 inputs each). Direct implementation gives control over edge cases. |
| edgartools for all XBRL | sec-edgar-api wrapper | sec-edgar-api wraps the same SEC endpoints but has less functionality than edgartools. edgartools provides statement parsing and DataFrame conversion. |

**Installation:**
```bash
uv add financedatabase
```

Note: edgartools is available as an MCP server but the CLAUDE.md rule says "MCP tools are used ONLY in ACQUIRE stage." For EXTRACT, we should use edgartools as a Python library import (not MCP) to parse locally-acquired filing data. However, the SEC Company Facts API is a data acquisition call -- it must happen in ACQUIRE or be treated as an ACQUIRE expansion within Phase 3 (per CONTEXT.md: "phase boundary is flexible for data acquisition").

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/stages/extract/
    __init__.py              # ExtractStage orchestrator (~150 lines)
    company_profile.py       # SECT2 extraction (~400 lines)
    financial_statements.py  # SECT3-02/03/04: XBRL statement extraction (~450 lines)
    earnings_quality.py      # SECT3-06: forensic analysis ratios (~300 lines)
    distress_models.py       # SECT3-07: Z/M/O/F-Score computations (~400 lines)
    peer_group.py            # SECT2-09 + SECT3-05: peer construction + benchmarking (~350 lines)
    audit_risk.py            # SECT3-12: audit profile extraction (~300 lines)
    debt_analysis.py         # SECT3-08/09/10/11: liquidity, leverage, debt (~350 lines)
    tax_indicators.py        # SECT3-13: tax analysis (~200 lines)
    validation.py            # Extraction validation framework (~250 lines)
    xbrl_mapping.py          # XBRL concept mapping table + helpers (~200 lines)

src/do_uw/config/
    xbrl_concepts.json       # ~50 US GAAP concept mappings (new config file)
    tax_havens.json           # Low-tax jurisdiction list for SECT3-13 (new config file)

src/do_uw/models/
    company.py               # Expanded CompanyProfile model (existing, needs expansion)
    financials.py             # Expanded financial models (existing, needs expansion)
```

### Pattern 1: XBRL Concept Mapping Table (Config-Driven)

**What:** A JSON config file mapping ~50 common US GAAP XBRL taxonomy concepts to canonical field names used in the Pydantic models. Accounts for the fact that companies may use different but equivalent XBRL tags for the same concept (e.g., `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet`).

**When to use:** Every XBRL data extraction operation.

**Example:**
```json
{
  "revenue": {
    "canonical_name": "revenue",
    "xbrl_tags": [
      "Revenues",
      "RevenueFromContractWithCustomerExcludingAssessedTax",
      "SalesRevenueNet",
      "RevenueFromContractWithCustomerIncludingAssessedTax"
    ],
    "unit": "USD",
    "statement": "income",
    "description": "Total revenue / net sales"
  },
  "net_income": {
    "canonical_name": "net_income",
    "xbrl_tags": [
      "NetIncomeLoss",
      "ProfitLoss",
      "NetIncomeLossAvailableToCommonStockholdersBasic"
    ],
    "unit": "USD",
    "statement": "income",
    "description": "Net income / net loss"
  }
}
```

**Why:** Companies are inconsistent in which XBRL tag they use for the same concept. A mapping table with fallback tags ensures extraction works across companies. The table is in a JSON config file (not hardcoded), per CLAUDE.md anti-context-rot rule.

### Pattern 2: Extraction Validation Framework (Anti-Imputation)

**What:** Every extraction function returns both the extracted data AND a validation report documenting what was expected, what was found, and what is missing.

**When to use:** Every extraction operation. This is the PRIMARY trust mechanism.

**Example:**
```python
@dataclass
class ExtractionReport:
    """Validation report for a single extraction operation."""
    extractor_name: str          # e.g., "income_statement"
    expected_fields: list[str]   # What we expected to find
    found_fields: list[str]      # What we actually found
    missing_fields: list[str]    # Expected but not found
    unexpected_fields: list[str] # Found but not expected
    coverage_pct: float          # found / expected
    confidence: Confidence       # Overall extraction confidence
    source_filing: str           # Filing type + date + accession
    fallbacks_used: list[str]    # Any fallback strategies employed
    warnings: list[str]          # Issues detected during extraction
```

**Why:** CONTEXT.md identifies silent incompleteness and silent imputation as the #1 risk. Every extraction MUST produce a validation report comparing what it found against what it expected. The system knows its own completeness.

### Pattern 3: Two-Tier XBRL Extraction (Company Facts + Filing XBRL)

**What:** Use SEC Company Facts API as the primary data source for structured financial data (fast, all concepts in one call), then fall back to edgartools filing-level XBRL parsing for concepts not found or for dimensional data (segments, geographic breakdowns).

**When to use:** All SECT3 financial extractions.

**Tier 1: Company Facts API** (fast, comprehensive for standard line items)
```python
# One API call gets ALL XBRL facts for the company
url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
data = sec_get(url)
# Structure: data["facts"]["us-gaap"]["Revenue"]["units"]["USD"]
# Each entry: {"val": ..., "end": ..., "accn": ..., "fy": ..., "fp": ..., "form": ..., "filed": ...}
```

**Tier 2: edgartools filing-level XBRL** (for statements with line-item detail, segments)
```python
from edgar import Company
from edgar.xbrl import XBRLS

company = Company(ticker)
filings = company.get_filings(form="10-K").head(3)
xbrls = XBRLS.from_filings(filings)
income = xbrls.statements.income_statement()
df = income.to_dataframe()
```

**Why:** Company Facts API returns every concept across all filings in one call but lacks statement structure (you get individual values, not organized statements). edgartools provides organized statements with proper line-item ordering and dimensional data, but requires per-filing parsing. Use both: Company Facts for fast metric extraction and validation, edgartools for structured statement presentation.

### Pattern 4: Distress Model Computation with Sector Guard Rails

**What:** Implement all four distress models directly with explicit handling for: (a) sector-specific model variants, (b) missing inputs, (c) pre-revenue/early-stage companies, (d) financial companies.

**When to use:** SECT3-07 computations.

**Example for Z-Score with sector awareness:**
```python
def compute_z_score(
    financials: dict[str, float | None],
    sector: str,
) -> DistressResult:
    """Compute appropriate Z-Score variant based on sector."""
    if sector in ("FINS", "REIT"):
        return _compute_z_double_prime(financials)  # Non-manufacturing Z''
    elif _is_pre_revenue(financials):
        return _compute_early_stage_metrics(financials)  # Cash runway, burn rate
    else:
        return _compute_z_original(financials)  # Original Z-Score
```

### Pattern 5: Composite Peer Scoring

**What:** Multi-signal approach combining 5 signals into a composite peer relevance score. Each candidate company gets a score 0-100.

**Signals:**
1. SIC code match (2-digit, 3-digit, 4-digit levels) -- 25% weight
2. yfinance industry/sector match -- 20% weight
3. Market cap band (0.5x-2x target) -- 25% weight
4. Revenue magnitude similarity -- 15% weight
5. Business description keyword overlap -- 15% weight

**When to use:** SECT2-09 peer group construction.

### Anti-Patterns to Avoid

- **Relying solely on SIC for peers:** SIC codes are 50+ years old, too broad, and often miscategorize modern companies. Per user decision: "SIC code is notoriously a bad way to determine sector and peer group."
- **Silent imputation of financial fields:** NEVER generate a revenue segment or financial metric that isn't in the source filing. If a company reports 2 segments, output 2 segments -- not 4.
- **Forcing distress models on financial companies:** Standard Altman Z-Score has meaningless results for banks/insurance/REITs because their balance sheet structure is fundamentally different. Must use Z''-Score or bank-specific models.
- **Extracting without validating:** Every extraction MUST compare found vs. expected. An extraction that returns 3 of 12 income statement line items without flagging incompleteness is a system failure.
- **Hardcoding XBRL tag names:** Companies use different tags for the same concept. Always use the mapping table with fallback tags.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XBRL statement parsing and layout | Custom XBRL XML parser | edgartools `filing.xbrl().statements` | XBRL has complex linkbase hierarchies (presentation, calculation, definition). edgartools handles this correctly. |
| Multi-period financial stitching | Manual DataFrame joins | edgartools `XBRLS.from_filings()` | Aligning fiscal periods across filings is tricky (restated numbers, amended filings). edgartools handles this. |
| SEC filing text section extraction | Regex on raw HTML | edgartools `filing.sections()` or filing HTML with `html.parser` | SEC filings have inconsistent HTML structure. edgartools normalizes common sections. |
| XBRL concept lookup by company | Manual per-filing parsing | SEC Company Facts API (`companyfacts/CIK.json`) | One API call returns ALL concepts. Parsing each filing individually is 10-100x slower. |
| Peer universe lookup | Scraping stock screeners | financedatabase filter by sector/industry/country | 300K+ symbols already categorized. No scraping needed. |

**Key insight:** XBRL parsing is deceptively complex. The taxonomy has thousands of concepts, companies choose different tags for the same item, dimensional data (segments, geographies) uses axis/member hierarchies, and multi-period alignment requires understanding fiscal year ends. Using edgartools for statement-level parsing saves weeks of debugging. Use the Company Facts API for fast concept-level queries and validation.

## Common Pitfalls

### Pitfall 1: XBRL Tag Inconsistency Across Companies

**What goes wrong:** Hardcoding `us-gaap:Revenues` works for Apple but fails for Amazon (which uses `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`) and for banks (which may use `InterestAndNoninterestIncome`).
**Why it happens:** US GAAP taxonomy has 17,000+ concepts. Companies choose the most specific applicable tag, which varies by industry and accounting treatment.
**How to avoid:** Build the canonical mapping table with 3-5 alternative tags per concept. Try tags in priority order. Log which tag matched for traceability.
**Warning signs:** Extraction returns `None` for Revenue on a Fortune 500 company -- it's a tag mismatch, not missing data.

### Pitfall 2: Duplicate XBRL Facts (Multiple Filings Report Same Period)

**What goes wrong:** Company Facts API returns the same value multiple times because a 10-K reports current year AND restates prior year, and a 10-Q also reports the same metric. Naive extraction picks wrong value or counts duplicates.
**Why it happens:** Companies file revenue in their 10-K for FY2024, then also report it in their Q1 2025 10-Q comparative column. Both filings produce XBRL facts for the same concept and same end date.
**How to avoid:** Filter by `form` (prefer 10-K for annual, 10-Q for quarterly) and deduplicate by `end` date. For multi-period data, pick the most recent `filed` date per unique `end`+`fy`+`fp` combination.
**Warning signs:** Extraction shows doubled revenue or assets values; 4-quarter trajectory has 8 data points instead of 4.

### Pitfall 3: Confusing Instant vs. Duration Facts

**What goes wrong:** Balance sheet items (instant: point-in-time) and income statement items (duration: period) have different XBRL period representations. Mixing them up produces nonsensical ratios.
**Why it happens:** Balance sheet facts have an `end` date only (instant). Income statement facts have `start` and `end` dates (duration). Company Facts API does not always clearly distinguish these.
**How to avoid:** The mapping table should specify whether each concept is `instant` or `duration`. Use the concept's `form` and `fp` fields to determine the period. For Company Facts API: balance sheet items appear once per period end; income statement items should be filtered to avoid sub-period overlaps.
**Warning signs:** Current ratio calculation using quarterly revenue instead of quarterly balance sheet values.

### Pitfall 4: Exhibit 21 Format Variability

**What goes wrong:** Exhibit 21 (subsidiaries list) has no standardized format. Some companies use HTML tables, others use plain text lists, some use nested structures for subsidiary-of-subsidiary relationships.
**Why it happens:** SEC requires disclosure of subsidiaries but does not mandate a specific format or machine-readable structure.
**How to avoid:** Build a multi-strategy parser: (1) try HTML table extraction, (2) try pattern matching for "subsidiary name | jurisdiction" pairs, (3) fall back to line-by-line parsing. Always count entries and report coverage. Accept that some Exhibit 21s will need manual verification.
**Warning signs:** Parser returns 0 subsidiaries for a large company (parsing failure, not data absence).

### Pitfall 5: Distress Score Inputs Missing or Zero

**What goes wrong:** Altman Z-Score divides by Total Assets. If Total Assets is 0 or None, you get a division error or meaningless score. Similar issues with EBIT, Total Liabilities, etc.
**Why it happens:** Pre-revenue companies may have zero revenue; newly public companies may have incomplete XBRL history; some concepts may not be reported under the expected tag.
**How to avoid:** Per CONTEXT.md decision: compute what's possible, mark as 'partial', list missing inputs. Never output a score without listing which inputs were available and which were missing. Use `DistressResult` model with `is_partial: bool` and `missing_inputs: list[str]`.
**Warning signs:** Z-Score of +50 or -50 (extreme values indicating bad inputs, not genuine distress/safety).

### Pitfall 6: edgartools as MCP vs. Library

**What goes wrong:** Calling edgartools through MCP server in EXTRACT stage violates CLAUDE.md rule "MCP tools are used ONLY in ACQUIRE stage." Also, edgartools MCP calls may not work in subagents.
**Why it happens:** edgartools is installed both as MCP server and as Python library. Developer defaults to MCP usage.
**How to avoid:** Import edgartools directly as a Python library (`from edgar import Company`) in EXTRACT stage code. Only use edgartools MCP in ACQUIRE stage expansion (when acquiring new data not obtained in Phase 2). Any edgartools calls that fetch data from SEC APIs are technically ACQUIRE operations and should be clearly labeled as such.
**Warning signs:** EXTRACT stage code making network calls through MCP.

## Code Examples

### SEC Company Facts API: Extract Revenue History
```python
# Source: SEC EDGAR API documentation (data.sec.gov)
import json
from do_uw.stages.acquire.rate_limiter import sec_get

def get_company_facts(cik_padded: str) -> dict:
    """Fetch all XBRL facts for a company."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
    return sec_get(url)

def extract_concept(
    facts: dict,
    concept: str,
    form_type: str = "10-K",
    unit: str = "USD",
) -> list[dict]:
    """Extract values for a specific XBRL concept.

    Args:
        facts: Full companyfacts API response.
        concept: US GAAP concept name (e.g., 'Revenues').
        form_type: Filter to specific form type.
        unit: Unit of measure (USD, shares, pure).

    Returns:
        List of fact entries sorted by end date, deduplicated.
    """
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    concept_data = us_gaap.get(concept, {})
    units = concept_data.get("units", {})
    entries = units.get(unit, [])

    # Filter by form type and deduplicate by end date
    filtered = [e for e in entries if e.get("form") == form_type]
    seen: set[str] = set()
    deduplicated: list[dict] = []
    for entry in sorted(filtered, key=lambda e: e.get("filed", ""), reverse=True):
        key = f"{entry.get('end')}_{entry.get('fy')}_{entry.get('fp')}"
        if key not in seen:
            seen.add(key)
            deduplicated.append(entry)
    return sorted(deduplicated, key=lambda e: e.get("end", ""))
```

### Canonical XBRL Concept Resolver
```python
# Pattern: Try multiple XBRL tags in priority order
def resolve_concept(
    facts: dict,
    mapping: dict,  # From xbrl_concepts.json
    concept_name: str,
    form_type: str = "10-K",
) -> list[dict] | None:
    """Resolve a canonical concept name to XBRL data.

    Tries each tag in the mapping's priority list until data is found.
    """
    concept_config = mapping.get(concept_name)
    if concept_config is None:
        return None

    unit = concept_config.get("unit", "USD")
    for tag in concept_config["xbrl_tags"]:
        results = extract_concept(facts, tag, form_type, unit)
        if results:
            return results
    return None
```

### Altman Z-Score (Original + Z'' Non-Manufacturing)
```python
# Source: Altman (1968) original, Altman (2002) Z''-Score
# Verified via Wikipedia, WallStreetPrep, CorporateFinanceInstitute

def altman_z_original(
    working_capital: float,
    retained_earnings: float,
    ebit: float,
    market_cap: float,
    total_liabilities: float,
    total_assets: float,
    sales: float,
) -> float:
    """Original Z-Score for public manufacturing companies.

    Z = 1.2*(WC/TA) + 1.4*(RE/TA) + 3.3*(EBIT/TA) + 0.6*(MktCap/TL) + 1.0*(Sales/TA)

    Zones: <1.81 distress, 1.81-2.99 grey, >2.99 safe
    """
    if total_assets == 0:
        raise ValueError("Total assets cannot be zero")
    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_cap / total_liabilities if total_liabilities != 0 else 0.0
    x5 = sales / total_assets
    return 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

def altman_z_double_prime(
    working_capital: float,
    retained_earnings: float,
    ebit: float,
    book_equity: float,
    total_liabilities: float,
    total_assets: float,
) -> float:
    """Z''-Score for non-manufacturing and emerging market companies.

    Z'' = 6.56*(WC/TA) + 3.26*(RE/TA) + 6.72*(EBIT/TA) + 1.05*(BV Equity/TL)

    Removes Sales/TA ratio (inappropriate for non-manufacturing).
    Zones: <1.1 distress, 1.1-2.6 grey, >2.6 safe
    """
    if total_assets == 0:
        raise ValueError("Total assets cannot be zero")
    a = working_capital / total_assets
    b = retained_earnings / total_assets
    c = ebit / total_assets
    d = book_equity / total_liabilities if total_liabilities != 0 else 0.0
    return 6.56 * a + 3.26 * b + 6.72 * c + 1.05 * d
```

### Beneish M-Score
```python
# Source: Beneish (1999), verified via Wikipedia, OldSchoolValue, WallStreetMojo

def beneish_m_score(
    dsri: float,   # Days Sales in Receivables Index
    gmi: float,    # Gross Margin Index
    aqi: float,    # Asset Quality Index
    sgi: float,    # Sales Growth Index
    depi: float,   # Depreciation Index
    sgai: float,   # SGA Expense Index
    tata: float,   # Total Accruals / Total Assets
    lvgi: float,   # Leverage Index
) -> float:
    """Beneish M-Score for earnings manipulation detection.

    M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
        + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI

    Threshold: > -1.78 suggests manipulation
    """
    return (
        -4.84
        + 0.920 * dsri
        + 0.528 * gmi
        + 0.404 * aqi
        + 0.892 * sgi
        + 0.115 * depi
        - 0.172 * sgai
        + 4.679 * tata
        - 0.327 * lvgi
    )
```

### Ohlson O-Score
```python
# Source: Ohlson (1980), verified via Wikipedia, WallStreetMojo

def ohlson_o_score(
    total_assets: float,
    total_liabilities: float,
    working_capital: float,
    current_liabilities: float,
    net_income: float,
    funds_from_ops: float,  # Cash from operations
    gnp_deflator: float,    # Typically use log(CPI-adjusted TA)
    net_income_sign: int,   # 1 if NI<0 in both last 2 years, else 0
    delta_ni: float,        # Change in NI / (|NI_t| + |NI_t-1|)
) -> float:
    """Ohlson O-Score for bankruptcy probability.

    Higher score = greater bankruptcy probability.
    Probability = exp(O) / (1 + exp(O))
    """
    if total_assets == 0:
        raise ValueError("Total assets cannot be zero")
    log_ta = __import__("math").log(total_assets / gnp_deflator) if gnp_deflator > 0 else 0
    tl_ta = total_liabilities / total_assets
    wc_ta = working_capital / total_assets
    cl_ca = current_liabilities / (total_assets - total_liabilities) if (total_assets - total_liabilities) != 0 else 0
    ni_ta = net_income / total_assets
    ffo_tl = funds_from_ops / total_liabilities if total_liabilities != 0 else 0
    tl_gt_ta = 1 if total_liabilities > total_assets else 0

    return (
        -1.32
        - 0.407 * log_ta
        + 6.03 * tl_ta
        - 1.43 * wc_ta
        + 0.076 * cl_ca
        - 1.72 * tl_gt_ta
        - 2.37 * ni_ta
        - 1.83 * ffo_tl
        + 0.285 * net_income_sign
        - 0.521 * delta_ni
    )
```

### Piotroski F-Score
```python
# Source: Piotroski (2000), verified via Wikipedia, StableBread, CorporateFinanceInstitute

def piotroski_f_score(
    # Profitability
    net_income: float,          # Current year
    roa_current: float,         # ROA = NI / TA
    roa_prior: float,           # Prior year ROA
    ocf: float,                 # Operating cash flow
    total_assets: float,        # Current year TA
    # Leverage & Liquidity
    long_term_debt_current: float,
    long_term_debt_prior: float,
    current_ratio_current: float,
    current_ratio_prior: float,
    shares_current: int,
    shares_prior: int,
    # Operating Efficiency
    gross_margin_current: float,
    gross_margin_prior: float,
    asset_turnover_current: float,  # Revenue / TA
    asset_turnover_prior: float,
) -> int:
    """Piotroski F-Score: 0-9 financial strength indicator.

    9 binary criteria across 3 categories. Score of 8-9 = strong, 0-2 = weak.
    """
    score = 0

    # Profitability (4 criteria)
    if net_income > 0:                      # Positive net income
        score += 1
    if roa_current > roa_prior:             # Improving ROA
        score += 1
    if ocf > 0:                             # Positive operating cash flow
        score += 1
    if total_assets > 0 and (ocf / total_assets) > roa_current:  # Accruals
        score += 1

    # Leverage & Liquidity (3 criteria)
    if long_term_debt_current < long_term_debt_prior:    # Decreasing leverage
        score += 1
    if current_ratio_current > current_ratio_prior:      # Improving liquidity
        score += 1
    if shares_current <= shares_prior:                    # No dilution
        score += 1

    # Operating Efficiency (2 criteria)
    if gross_margin_current > gross_margin_prior:         # Improving margins
        score += 1
    if asset_turnover_current > asset_turnover_prior:     # Improving efficiency
        score += 1

    return score
```

### edgartools Financial Statement Extraction
```python
# Source: edgartools docs (edgartools.readthedocs.io)
from edgar import Company
from edgar.xbrl import XBRLS

def extract_multi_period_statements(ticker: str, periods: int = 3):
    """Extract multi-period financial statements using edgartools."""
    company = Company(ticker)
    filings = company.get_filings(form="10-K").head(periods)
    xbrls = XBRLS.from_filings(filings)
    statements = xbrls.statements

    income_df = statements.income_statement().to_dataframe()
    balance_df = statements.balance_sheet().to_dataframe()
    cashflow_df = statements.cashflow_statement().to_dataframe()

    return income_df, balance_df, cashflow_df
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Parse individual XBRL filing XML | SEC Company Facts API (all concepts in one JSON call) | SEC API launched ~2022 | 10-100x faster extraction; no XML parsing needed for structured data |
| SIC-only peer groups | Multi-signal composite (SIC + NAICS + industry + market cap + revenue) | Industry standard shift ~2020s | Much better peer relevance; SIC alone mislassifies modern companies |
| Manual Z-Score only | Multiple distress models (Z + M + O + F) with sector variants | Academic consensus evolved | Z-Score alone misclassifies financials and service companies; M-Score catches manipulation; O-Score adds logistic probability; F-Score measures financial strength |
| edgartools basic parsing | edgartools v3.x with XBRLS multi-period stitching and DataFrame support | edgartools v3+ (2025-2026) | Multi-period analysis, dimensional data, financial metrics extraction |

**Deprecated/outdated:**
- python-xbrl library: Last updated 2020, does not support inline XBRL. Use edgartools instead.
- Direct XBRL XML parsing: SEC Company Facts API eliminates the need for most XML parsing. Use for edge cases only.

## Open Questions

1. **edgartools as Python library dependency vs. MCP-only**
   - What we know: edgartools is installed as MCP server. CLAUDE.md says MCP is ACQUIRE-only. edgartools can also be imported as Python library.
   - What's unclear: Whether to add edgartools as a pyproject.toml dependency for EXTRACT-stage use, or rely solely on the SEC Company Facts REST API + manual HTML parsing.
   - Recommendation: Add edgartools to pyproject.toml dependencies. Use it as a Python library in EXTRACT stage for filing-level statement parsing. Use SEC REST API for Company Facts data (treat as ACQUIRE expansion). This gives us both per-concept data (Company Facts) and structured statement layouts (edgartools). **MEDIUM confidence** -- need to verify edgartools doesn't make unexpected network calls during statement parsing.

2. **GICS codes: accessible for free?**
   - What we know: GICS is proprietary (MSCI/S&P). yfinance provides `sectorKey` and `industryKey` which use Yahoo's classification (loosely based on GICS). FinanceDatabase uses a community-maintained approximation.
   - What's unclear: Whether Yahoo's classification is close enough to GICS for peer grouping purposes.
   - Recommendation: Use yfinance `industryKey` as primary industry signal (it correlates well with GICS sub-industries). Do NOT pay for GICS. The composite peer score approach (SIC + industry + market cap + revenue) compensates for any single signal's imprecision. **HIGH confidence** -- yfinance industry data is well-established.

3. **ETF holdings for peer group: accessible?**
   - What we know: CONTEXT.md wants ETF holdings as a peer signal. Free ETF holdings APIs exist (Finnhub has a free tier) but may have rate limits. SEC 13F filings contain ETF holdings but are quarterly and require parsing.
   - What's unclear: Whether the effort of integrating ETF holdings data justifies the marginal improvement in peer quality.
   - Recommendation: Defer ETF holdings integration. The 4-signal approach (SIC + industry + market cap + revenue) already provides strong peer groups. ETF holdings can be added later if peer quality is insufficient. Use the sector ETF from `sectors.json` (already mapped: XLK, XLF, etc.) for the sector benchmark tier instead. **MEDIUM confidence**.

4. **Exhibit 21 parsing reliability**
   - What we know: Exhibit 21 format varies wildly between companies. Some are HTML tables, some are plain text. No standardized machine-readable format exists.
   - What's unclear: What parsing success rate to expect across different companies.
   - Recommendation: Build a pragmatic parser with 3 strategies (HTML table, delimiter-separated, line-by-line). Accept that some Exhibit 21s will yield partial results. Log extraction coverage. For tax haven analysis (SECT3-13), cross-reference parsed subsidiaries against a known low-tax jurisdiction list. **LOW confidence** on achieving >90% accuracy across all companies.

5. **Company Facts API expansion in ACQUIRE**
   - What we know: Phase 2 ACQUIRE fetches filing METADATA (accession numbers, dates) but not filing CONTENT or XBRL data. Phase 3 EXTRACT needs XBRL data and filing text.
   - What's unclear: Whether to expand ACQUIRE in Phase 3 to fetch Company Facts + filing content, or fetch it in EXTRACT stage and treat it as local data processing.
   - Recommendation: Expand ACQUIRE to include Company Facts API call (one call per company, returns all XBRL data). Filing text content (for Exhibit 21, Item 1, etc.) should be fetched on-demand in EXTRACT via `sec_get_text()` (already exists in rate_limiter.py) -- this is technically data acquisition but is more naturally triggered by extraction needs. Mark these calls clearly as "ACQUIRE expansion" in code comments. **HIGH confidence**.

## Sources

### Primary (HIGH confidence)
- SEC EDGAR API documentation: https://www.sec.gov/search-filings/edgar-application-programming-interfaces -- Company Facts, Company Concept, Frames endpoints
- edgartools documentation: https://edgartools.readthedocs.io/en/latest/ -- XBRL parsing, statement extraction, DataFrame conversion, CompanyFacts
- edgartools extract-statements guide: https://edgartools.readthedocs.io/en/latest/guides/extract-statements/ -- code examples verified
- edgartools company-facts guide: https://edgartools.readthedocs.io/en/latest/guides/company-facts/ -- CompanyFacts class, query API

### Secondary (MEDIUM confidence)
- Altman Z-Score formulas: Wikipedia + WallStreetPrep + CorporateFinanceInstitute -- multiple sources agree on coefficients
- Beneish M-Score formula: Wikipedia + OldSchoolValue + WallStreetMojo -- 8-variable formula with coefficients verified across 3 sources
- Ohlson O-Score formula: Wikipedia + WallStreetMojo + BreakingDownFinance -- 9-variable logistic model verified
- Piotroski F-Score criteria: Wikipedia + StableBread + ChartMill -- 9 binary criteria across 3 categories verified
- yfinance industry fields: yfinance docs + GitHub issues -- `sectorKey`, `industryKey`, `sectorDisp`, `industryDisp` confirmed
- FinanceDatabase: GitHub + PyPI -- 300K+ symbols, sector/industry categorization, free/open-source

### Tertiary (LOW confidence)
- ETF holdings API availability: Web search only -- Finnhub free tier unverified
- Exhibit 21 parsing approaches: Web search + SEC EDGAR examples -- format variability makes any approach uncertain
- edgartools version capabilities: WebFetch from docs -- library evolves rapidly (24 releases in 60 days per PyPI)

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM -- edgartools API verified via docs, but exact behavior under production load unverified
- Architecture: HIGH -- patterns follow established codebase conventions (SourcedValue, config-driven, validation gates)
- Distress formulas: HIGH -- formulas verified across 3+ sources each
- Peer group construction: MEDIUM -- data sources identified but composite scoring algorithm is novel (no established library)
- Pitfalls: HIGH -- derived from real XBRL extraction experience documented in multiple sources

**Research date:** 2026-02-07
**Valid until:** 2026-03-07 (30 days -- edgartools evolves rapidly, but SEC APIs are stable)
