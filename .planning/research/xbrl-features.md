# Feature Landscape: XBRL-First Data Integrity

**Domain:** XBRL financial extraction and forensic analysis for D&O underwriting
**Researched:** 2026-03-05
**Milestone:** v3.1

## Table Stakes

Features that are essential for the milestone goal of eliminating LLM hallucination from quantitative data. Missing any of these would leave the system with the same data integrity gaps it has today.

| Feature | Why Expected | Complexity | Depends On |
|---------|--------------|------------|------------|
| 8-Quarter XBRL Extraction | QoQ trends essential for earnings manipulation detection; current system uses yfinance fallback (MEDIUM confidence) instead of SEC-sourced data (HIGH confidence) | Med | Existing Company Facts API integration |
| Fiscal Year / Calendar Year Period Alignment | Companies have non-calendar fiscal years (e.g., AAPL ends Sep, SHW ends Dec); fp field disambiguation (Q1/Q2/Q3/Q4/FY) is required to avoid period mismatch | Med | 8-Quarter Extraction |
| Quarterly vs YTD Disambiguation | Company Facts API returns YTD cumulative values for duration concepts in 10-Q filings; must subtract prior quarters to get true quarterly values | High | 8-Quarter Extraction |
| Expanded XBRL Concept Coverage (120+ concepts) | Current 40 concepts miss critical forensic inputs: deferred tax assets/liabilities, pension obligations, operating lease ROU, stock-based compensation, acquisition costs, allowance for doubtful accounts | Med | Existing xbrl_concepts.json |
| Total Liabilities Derivation Hardening | Many filers (SHW, AMZN) lack atomic `Liabilities` tag; current derivation (TA - SE) exists but needs edge case handling for minority interest, preferred stock | Low | Existing financial_models.py |
| XBRL-Fed Distress Models (Altman, Beneish, Ohlson, Piotroski) | Currently partially LLM-fed; all 4 models must consume XBRL-only inputs for HIGH confidence | Med | Expanded XBRL Concepts |
| Form 4 Structured XML Extraction Enhancement | Current parser handles basic non-derivative/derivative transactions; needs: ownership amounts post-transaction, relationship codes, Section 16 reporting person categorization | Med | Existing insider_trading.py |
| Forensic Ratio Calculations from XBRL | Sloan Accruals Ratio, cash flow manipulation detection, revenue recognition red flags -- all derivable from existing XBRL data without LLM | Med | Expanded XBRL Concepts |

## Differentiators

Features that go beyond data integrity into analytical power. Not strictly required to eliminate LLM hallucination but significantly enhance the underwriting product.

| Feature | Value Proposition | Complexity | Depends On |
|---------|-------------------|------------|------------|
| SEC Frames API Peer Benchmarking | True percentile ranking across ALL SEC filers for any XBRL concept, by SIC code -- replaces current ratio-to-baseline proxy | High | New API client |
| Dimensional Revenue by Segment | XBRL segment axis data reveals revenue concentration, segment margin trends, geographic risk -- currently missing entirely | High | edgartools or custom dim parser |
| Dimensional Revenue by Geography | Geographic revenue breakdown via XBRL axis/member taxonomy exposes international exposure for D&O risk | High | Same as segment extraction |
| Beneish M-Score Component Decomposition | Exposing all 8 individual indices (DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI) in the output, not just the composite score | Low | Existing compute_m_score() |
| Multi-Period Forensic Trajectory | Running Beneish/Sloan/accruals ratios across 8 quarters to detect manipulation trend onset -- not just latest-period snapshot | Med | 8-Quarter Extraction + Forensic Ratios |
| Capital Allocation Quality Score | Composite of buyback timing vs stock price, acquisition goodwill impairment rate, capex/D&A ratio, dividend coverage -- pure XBRL derivation | Med | Expanded XBRL Concepts |
| DEF 14A Compensation XBRL Extraction | ECD taxonomy provides structured CEO/NEO pay data (salary, bonus, stock awards, options, NQDC, total) since 2023; reduces LLM extraction for compensation tables | Med | ECD taxonomy mapping |
| Goodwill Impairment Forensics | Track goodwill as % of total assets over time, impairment charges, acquisition history -- high predictive value for D&O claims | Low | Existing goodwill/impairment concepts |
| Pension & Post-Retirement Liability Analysis | XBRL concepts exist for PBO, funded status, service cost -- underfunded pensions are material D&O risk | Med | New XBRL concept mappings |
| Debt Maturity Wall Detection | Near-term debt maturities via XBRL schedule + interest coverage trajectory = refinancing risk signal | Med | New XBRL concept mappings |
| IFRS Foreign Private Issuer Support | companyfacts API returns `ifrs-full` taxonomy alongside `us-gaap`; dual-taxonomy concept mapping enables FPI analysis | High | New IFRS concept mapping table |
| Stock-Based Compensation Forensics | SBC as % of revenue trend, dilution from options/RSUs, non-GAAP vs GAAP earnings gap | Low | Expanded XBRL Concepts |

## Anti-Features

Features to explicitly NOT build in this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Real-time XBRL streaming | SEC API updates in near-real-time but D&O underwriting is quarterly/annual cadence; adds complexity for zero value | Batch extraction at pipeline run time; 14-month cache TTL is fine |
| Custom XBRL extension taxonomy parsing | Companies file custom extension concepts; parsing these requires per-filer logic that doesn't generalize | Use standard US-GAAP/IFRS taxonomy only; custom extensions are <5% of data and not reliable for cross-company comparison |
| XBRL rendering/visualization layer | Building charts/graphs from XBRL data is a rendering concern, not extraction | Existing matplotlib/sparkline infrastructure handles visualization |
| Full XBRL instance document parsing (iXBRL) | Parsing inline XBRL from HTML filings is complex and fragile; Company Facts API already aggregates this data cleanly | Use Company Facts API exclusively; fall back to edgartools for dimensional data |
| SEC EDGAR full-text search for XBRL concepts | EFTS is for filing text search, not structured data lookup | Use Company Facts API (single call returns all facts) and Frames API (cross-filer aggregation) |
| Build own peer group from scratch | Identifying true business peers (Visa vs Mastercard, not Visa vs JPM) requires industry-specific logic | Use SIC-code filtering from Frames API as proxy; defer true peer matching to industry-specific milestone |
| Backward-fill missing XBRL data with LLM | Tempting to use LLM for pre-XBRL periods or missing concepts; defeats the purpose of this milestone | Show "Not Available" for missing XBRL data; track coverage gaps for visibility |

## Feature Details

### 1. 8-Quarter XBRL Financial Extraction

**Current state:** yfinance provides 8 quarters (MEDIUM confidence) via `yfinance_quarterly.py`; Company Facts API used only for annual 10-K data via `xbrl_mapping.py`.

**How it works:** The Company Facts API (`companyfacts/CIK{cik}.json`) returns ALL XBRL facts across ALL filings. Each fact entry contains:
- `val`: The numeric value
- `end`: Period end date (e.g., "2025-09-30")
- `fy`: Fiscal year (e.g., 2025)
- `fp`: Fiscal period -- `Q1`, `Q2`, `Q3`, `Q4`, or `FY`
- `form`: Filing type -- `10-K` or `10-Q`
- `filed`: Filing date
- `frame`: Calendar period label (e.g., `CY2025Q3` for duration, `CY2025Q3I` for instant)
- `accn`: Accession number for provenance

**Critical disambiguation:** Duration concepts (revenue, net income) in 10-Q filings may be reported as **YTD cumulative** values, not standalone quarterly values. The `start` date (implicit from `end` minus duration) determines whether a value is Q-only or YTD:
- Q1 filing: value IS the quarterly value (start = fiscal year start)
- Q2 filing: value is H1 cumulative; true Q2 = H1 - Q1
- Q3 filing: value is 9-month cumulative; true Q3 = 9mo - H1
- Q4 filing: value = FY (from 10-K), or sometimes 10-Q Q4 filing exists

For instant (balance sheet) concepts, no subtraction is needed -- each period's value is standalone.

**Period alignment:** Filter by `form: "10-Q"` and sort by `end` date descending. Take 8 most recent. For companies with non-calendar fiscal years, the `fy`+`fp` fields provide canonical period identification. The `frame` field uses calendar-year convention (`CY2025Q3`) which may not match fiscal quarters -- use `fy`+`fp` for fiscal alignment, `frame` for calendar alignment.

**Implementation approach:** Extend `xbrl_mapping.py` with a `resolve_quarterly_concept()` function that:
1. Calls `extract_concept_value()` with `form_type="10-Q"`
2. Groups entries by `fy`+`fp` (fiscal period identity)
3. For duration concepts: detects YTD via `start` date analysis, subtracts prior quarters
4. For instant concepts: takes values as-is
5. Deduplicates by `end`+`fy`+`fp`, preferring most recently `filed`
6. Returns up to 8 most recent quarters

**Complexity:** MEDIUM. The API call is trivial (already exists). The complexity is in YTD-to-quarterly subtraction and handling edge cases: amended filings (pick latest `filed`), restated quarters, fiscal year changes.

### 2. Dimensional XBRL Data (Segments & Geography)

**Current state:** Zero dimensional data extracted. Revenue segments are LLM-extracted (LOW confidence) or missing entirely.

**How it works:** XBRL dimensional data uses an axis/member system:
- **Axis:** `SegmentReportingInformationBySegmentAxis`, `ProductOrServiceAxis`, `StatementGeographicalAxis`
- **Members:** Company-defined segments (e.g., `iPhoneMember`, `NorthAmericaMember`)
- Facts are tagged with both the concept (e.g., `Revenues`) AND the dimension (axis + member)

**Access methods:**
1. **edgartools** (recommended): `facts.query().by_dimension('Segment').to_dataframe()` -- automatically surfaces dimensional data with standardized mapping across ~2,000 XBRL tags to 95 concepts
2. **Company Facts API** does NOT return dimensional data -- it only has flat (undimensioned) facts
3. **SEC Financial Statement and Notes Data Sets** (bulk download) contain a DIM table with dimensional qualifications
4. **Direct iXBRL parsing** of filing HTML -- most complex, least desirable

**Recommended approach:** Use edgartools for dimensional extraction since the system already has edgartools as an MCP tool. edgartools handles the axis/member resolution and cross-company standardization. This runs in the ACQUIRE stage (MCP boundary).

**Complexity:** HIGH. The axis/member taxonomy is company-specific (custom extension elements for segment names). Cross-company comparison requires normalization. Some companies don't segment-report at all. Geographic axes may use different granularity (Americas vs North America vs US).

### 3. Form 4 Insider Trading Enhancement

**Current state:** Parser (`insider_trading.py`) already handles:
- Non-derivative and derivative transaction parsing from XML
- Transaction codes (P/S/A/M/F/G/D/C/J/K/U/W/I mapped to human-readable types)
- 10b5-1 plan detection via XML element and text search
- Cluster selling detection (sliding window, configurable min insiders)
- yfinance fallback when Form 4 XML unavailable

**What's missing for XBRL-first:**
1. **Post-transaction ownership amounts** (`sharesOwnedFollowingTransaction/value`) -- reveals total insider stake, not just incremental transaction
2. **Derivative security details** (`underlyingSecurityTitle`, `conversionOrExercisePrice`, `exerciseDate`, `expirationDate`) -- option grant/exercise analysis
3. **Reporting person relationship flags** (`isDirector`, `isOfficer`, `isTenPercentOwner`, `isOther`) -- currently partially extracted (officer title only)
4. **SEC Insider Transactions Data Sets** (structured CSV bulk download) -- pre-parsed 6-file dataset: Submissions, Reporting owners, Non-derivative, Derivative, Footnotes, Signatures. Merges on ACCESSION_NUMBER. Could supplement or replace XML parsing for historical data.

**Full transaction code list (verified from SEC):**

| Code | Meaning | Category |
|------|---------|----------|
| P | Open market/private purchase | General |
| S | Open market/private sale | General |
| V | Voluntary early report | General |
| A | Grant/award (Rule 16b-3(d)) | Rule 16b-3 |
| D | Disposition to issuer (Rule 16b-3(e)) | Rule 16b-3 |
| F | Tax withholding on vest/exercise (Rule 16b-3) | Rule 16b-3 |
| I | Discretionary transaction (Rule 16b-3(f)) | Rule 16b-3 |
| M | Exercise/conversion exempt (Rule 16b-3) | Rule 16b-3 |
| C | Conversion of derivative | Derivative |
| E | Expiration of short derivative | Derivative |
| H | Expiration/cancellation of long derivative | Derivative |
| O | Exercise out-of-the-money | Derivative |
| X | Exercise in-the-money/at-the-money | Derivative |
| G | Bona fide gift | Transfer |
| W | Will/estate | Transfer |
| Z | Voting trust deposit/withdrawal | Transfer |
| J | Other (footnoted) | Other |
| K | Equity swap | Other |
| U | Tender in change of control | Other |
| L | Small acquisition (Rule 16a-6) | Other |

**Complexity:** MEDIUM. XML parsing already works. Enhancements are additive fields from the same XML structure.

### 4. Forensic Financial Analysis from XBRL

**Current state:** Beneish M-Score (8 components), Altman Z, Ohlson O, Piotroski F all computed in `financial_models.py` and `financial_formulas.py` / `financial_formulas_distress.py`. BUT some inputs come from LLM extraction when XBRL concepts aren't mapped.

**Beneish M-Score 8 Components (already implemented):**
All 8 indices map to XBRL concepts already in xbrl_concepts.json:

| Index | Formula | XBRL Concepts Needed |
|-------|---------|---------------------|
| DSRI | (AR_t/Rev_t) / (AR_{t-1}/Rev_{t-1}) | AccountsReceivableNetCurrent, Revenues |
| GMI | GM_{t-1} / GM_t | GrossProfit, Revenues |
| AQI | (1-(CA+PPE)/TA)_t / same_{t-1} | AssetsCurrent, PropertyPlantAndEquipmentNet, Assets |
| SGI | Rev_t / Rev_{t-1} | Revenues |
| DEPI | DepRate_{t-1} / DepRate_t | DepreciationDepletionAndAmortization, PropertyPlantAndEquipmentNet |
| SGAI | (SGA/Rev)_t / (SGA/Rev)_{t-1} | SellingGeneralAndAdministrativeExpense, Revenues |
| TATA | (NI - OCF) / TA | NetIncomeLoss, NetCashProvidedByUsedInOperatingActivities, Assets |
| LVGI | (TL/TA)_t / (TL/TA)_{t-1} | Liabilities (or derived TA-SE), Assets |

**Status:** All concepts are mapped. The gap is that `_collect_all_inputs()` in `financial_models.py` extracts from `FinancialStatements` model (which may be LLM-populated) rather than directly from Company Facts XBRL data. Fix: wire XBRL-first extraction so FinancialStatements are XBRL-sourced, making all downstream models automatically XBRL-fed.

**New forensic ratios to add (all XBRL-derivable):**

| Ratio | Formula | D&O Relevance | XBRL Concepts |
|-------|---------|--------------|--------------|
| Sloan Accruals Ratio | (NI - CFO - CFI) / TA | Earnings quality; high accruals predict restatements. Safe zone: -10% to 10%. Warning: 10-25%. Danger: >25%. | NetIncomeLoss, Operating CF, Investing CF, Assets |
| Cash Flow Manipulation Index | OCF/NI trend + OCF/Revenue trend | Divergence flags channel stuffing or expense capitalization | Same as above + Revenues |
| Revenue Recognition Red Flag | DSO change + deferred revenue change + revenue growth vs peer | Accelerated recognition is #1 restatement cause | AccountsReceivableNetCurrent, DeferredRevenueCurrent, Revenues |
| Goodwill Impairment Risk | Goodwill/TA ratio + prior impairments + acquisition pace | D&O claims frequently follow goodwill writedowns | Goodwill, GoodwillImpairmentLoss, Assets |
| SBC Dilution Rate | SBC/Revenue trend + share count growth | Non-GAAP inflation masks true profitability | StockBasedCompensation, WeightedAverageNumberOfDilutedSharesOutstanding |

**Piotroski F-Score 9 Components (already implemented in financial_formulas_distress.py):**

| Signal | Category | XBRL Concepts |
|--------|----------|--------------|
| ROA > 0 | Profitability | NetIncomeLoss, Assets |
| CFO > 0 | Profitability | NetCashProvidedByUsedInOperatingActivities |
| Delta ROA > 0 | Profitability | Same + prior period |
| CFO > NI (accrual quality) | Profitability | Both |
| Delta Leverage < 0 | Leverage | LongTermDebt (or Liabilities), Assets |
| Delta Current Ratio > 0 | Leverage | AssetsCurrent, LiabilitiesCurrent |
| No new equity issued | Leverage | CommonStockSharesOutstanding |
| Delta Gross Margin > 0 | Efficiency | GrossProfit, Revenues |
| Delta Asset Turnover > 0 | Efficiency | Revenues, Assets |

**Complexity:** MEDIUM. Formulas exist. The work is (a) ensuring XBRL-sourced inputs feed FinancialStatements, (b) adding new ratio calculations, (c) wiring to brain signals.

### 5. SEC Frames API for Peer Benchmarking

**Current state:** Peer benchmarking uses ratio-to-baseline proxy (fixed baseline values, not real peer data). Produces approximate percentiles.

**How Frames API works:**
- Endpoint: `https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json`
- Example: `https://data.sec.gov/api/xbrl/frames/us-gaap/Revenues/USD/CY2024.json`
- Returns one fact per reporting entity for the specified concept and period
- Period formats: `CY2024` (annual), `CY2024Q3` (quarterly duration), `CY2024Q3I` (quarterly instant)
- Response fields per entity: `cik`, `entityName`, `val`, `end`, `accn`

**Critical limitation:** The Frames API does NOT support SIC-code filtering natively. To get sector-specific percentiles:
1. Fetch ALL filers for a concept+period (5,000-10,000+ entities per call)
2. Cross-reference with SEC submissions API or bulk CIK-to-SIC mapping to get SIC codes
3. Filter and compute percentiles locally

**Alternative approach:** Build a local cache of SIC-to-CIK mappings from SEC bulk data (`company_tickers.json` + `submissions`). Cache refreshed quarterly. This avoids N submissions API calls per benchmarking run.

**Rate limiting:** 10 req/sec SEC limit. Each concept+period = 1 API call. For 20 concepts across 1 period = 20 calls = 2 seconds. Manageable. Caching Frames responses for 30 days is reasonable since data is backward-looking.

**Complexity:** HIGH. Not because of the API (simple GET), but because of: SIC-to-CIK mapping maintenance, handling missing/zero values, choosing meaningful benchmark concepts, caching strategy for cross-filer data, and ensuring the percentile methodology is statistically sound.

### 6. DEF 14A Compensation XBRL (ECD Taxonomy)

**Current state:** Executive compensation extracted via LLM from DEF 14A narrative text. LOW confidence for numeric values.

**What's available as structured XBRL (mandatory since FY ending Dec 16, 2022):**
The Executive Compensation Disclosure (ECD) taxonomy provides structured tags for:
- **Summary Compensation Table:** Salary, bonus, stock awards, option awards, non-equity incentive plan, change in pension value, all other compensation, total -- for CEO and each NEO
- **Pay vs Performance Table:** Compensation actually paid (CAP), company TSR, peer group TSR, net income, company-selected measure
- **Outstanding Equity Awards:** Options and stock holdings per executive
- **Director Compensation Table:** Per-director fees, stock awards, total

**What still requires LLM extraction:**
- Compensation Discussion & Analysis (CD&A) narrative
- Perquisites detail breakdown
- Clawback policy terms and enforcement history
- Change-in-control/golden parachute provisions
- Performance metric definitions and targets
- Compensation committee analysis

**Access approach:** ECD taxonomy data appears under `ecd:` namespace in companyfacts (alongside `us-gaap:` and `dei:`). Need to extend `resolve_concept()` to check `ecd` namespace. Tags include elements like `ecd:TtlCompAmt` (total compensation), `ecd:SlryAmt` (salary), `ecd:StockAwdAmt` (stock awards), etc.

**Complexity:** MEDIUM. The ECD taxonomy is well-defined and mandatory. Challenge is that tag names are abbreviated (different convention from us-gaap), and the dimensional structure uses executive name as axis member.

### 7. IFRS Foreign Private Issuer Handling

**Current state:** System detects FPI status and fetches 20-F instead of 10-K. But XBRL extraction uses `us-gaap` namespace only -- IFRS filers return data under `ifrs-full` namespace, yielding zero XBRL data.

**How it works:** The companyfacts API returns facts organized by taxonomy namespace:
```
facts.us-gaap.{concept}    -- Domestic filers (US-GAAP)
facts.ifrs-full.{concept}  -- IFRS filers (foreign private issuers)
facts.dei.{concept}         -- Document/Entity Information (all filers)
facts.srt.{concept}         -- SEC Reporting Taxonomy (supplemental)
```

**IFRS concept mapping needed:** A parallel mapping table with canonical-to-IFRS tag mapping:

| Canonical | US-GAAP Tag | IFRS Tag |
|-----------|-------------|----------|
| revenue | Revenues | Revenue |
| net_income | NetIncomeLoss | ProfitLoss |
| total_assets | Assets | Assets |
| stockholders_equity | StockholdersEquity | Equity |
| operating_cash_flow | NetCashProvided...OperatingActivities | CashFlowsFromUsedInOperatingActivities |
| total_liabilities | Liabilities | Liabilities |
| current_assets | AssetsCurrent | CurrentAssets |
| current_liabilities | LiabilitiesCurrent | CurrentLiabilities |

**Scope for this milestone:** Create the IFRS mapping table; modify `resolve_concept()` to check `ifrs-full` when `us-gaap` yields no results (or when company is known FPI). Do NOT attempt to reconcile GAAP vs IFRS measurement differences. Flag IFRS-sourced data with source annotation.

**Complexity:** HIGH. IFRS taxonomy has different concept names, different hierarchy, and some concepts lack 1:1 GAAP equivalents (e.g., IFRS has no EBITDA concept, different cash flow classification rules). The mapping table requires careful validation against real FPI filings.

## Feature Dependencies

```
Expanded XBRL Concepts (120+)
  |
  +-> 8-Quarter XBRL Extraction
  |     |
  |     +-> Fiscal Year / Calendar Year Alignment
  |     |     |
  |     |     +-> Quarterly vs YTD Disambiguation
  |     |
  |     +-> Multi-Period Forensic Trajectory
  |
  +-> XBRL-Fed Distress Models (all 4)
  |
  +-> Forensic Ratio Calculations
  |     |
  |     +-> Sloan Accruals Ratio
  |     +-> Cash Flow Manipulation Index
  |     +-> Revenue Recognition Red Flags
  |     +-> Goodwill Impairment Forensics
  |
  +-> Capital Allocation Quality Score

SEC Frames API Client (new)
  |
  +-> SIC-to-CIK Mapping Cache
  |
  +-> Peer Percentile Calculation

ECD Taxonomy Mapping (new)
  |
  +-> DEF 14A Compensation XBRL

IFRS Concept Mapping (new)
  |
  +-> FPI XBRL Extraction

Form 4 XML Enhancement (existing parser)
  |
  +-> Post-Transaction Ownership
  +-> Derivative Security Details
  +-> Reporting Person Categorization

Dimensional Data Extraction (edgartools)
  |
  +-> Revenue by Segment
  +-> Revenue by Geography
  +-> Operating Expenses by Type
```

## MVP Recommendation

**Phase 1 (Foundation):** Do these first -- everything else depends on them.
1. Expanded XBRL concept coverage (120+ concepts) -- extend xbrl_concepts.json
2. 8-Quarter XBRL extraction with YTD disambiguation -- replace yfinance quarterly as primary source
3. XBRL-fed distress models -- ensure FinancialStatements are XBRL-sourced so all 4 models get HIGH confidence inputs

**Phase 2 (Forensics):** These are the core differentiators for D&O underwriting.
4. Forensic ratio calculations (Sloan Accruals, cash flow manipulation, revenue recognition red flags)
5. Multi-period forensic trajectory across 8 quarters
6. Beneish component decomposition in output (expose individual indices)
7. Goodwill impairment forensics (goodwill/TA ratio + impairment history)

**Phase 3 (Enrichment):** High value but independent of core extraction.
8. SEC Frames API peer benchmarking with SIC filtering
9. Form 4 enhancement (post-transaction ownership, derivative details, relationship flags)
10. DEF 14A compensation XBRL (ECD taxonomy)

**Defer to later milestone:**
- **IFRS foreign private issuer support:** Only ~500 IFRS filers on EDGAR; most D&O underwriting targets domestic filers. HIGH complexity for LOW coverage percentage. Create the mapping table but don't prioritize integration.
- **Dimensional revenue by segment/geography:** HIGH complexity, requires edgartools MCP integration changes in ACQUIRE stage, company-specific axis/member normalization. Extremely valuable but should be its own focused effort after foundation is solid.
- **Capital allocation quality score:** Novel composite metric; needs actuarial validation against actual D&O claim data before relying on it for underwriting decisions.
- **Pension/post-retirement analysis:** Sector-specific concern (manufacturing, utilities, legacy industrials); better fits the deferred industry-specific risk milestone.
- **Debt maturity wall detection:** Valuable but requires XBRL schedule data that is inconsistently tagged across filers; LLM extraction from 10-K footnotes may remain more reliable for this specific use case.

## Signal Integration Notes

Every new XBRL metric should map to a brain signal `field_key`. The signal schema already supports `acquisition.source_type` and `evaluation.data_strategy.field_key`. New forensic signals should declare:
- `schema_version: 2`
- `acquisition.source_type: SEC_XBRL` (new source type to distinguish from LLM-extracted SEC data)
- `evaluation.method: FORMULA` with the computation specified
- `evaluation.data_strategy.field_key` pointing to the extracted XBRL value path in AnalysisState

Estimated new signals: 15-25 covering forensic ratios, quarterly trend anomalies, peer percentile deviations, and compensation analysis red flags.

## Sources

- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) -- Official Company Facts, Company Concept, and Frames API documentation [HIGH confidence]
- [sec-edgar-api Python wrapper](https://sec-edgar-api.readthedocs.io/) -- Confirmed API patterns for companyfacts, frames, company-concept [HIGH confidence]
- [SEC Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets) -- Structured CSV format for Form 4 data [HIGH confidence]
- [SEC Form 4 Transaction Codes](https://www.sec.gov/edgar/searchedgar/ownershipformcodes.html) -- Official transaction code definitions [HIGH confidence]
- [ECD Taxonomy Guide 2025](https://xbrl.sec.gov/ecd/2025/ecdtaxonomyguide-2025-03-17.pdf) -- Executive Compensation Disclosure XBRL tags [HIGH confidence]
- [EdgarTools XBRL Documentation](https://edgartools.readthedocs.io/en/latest/getting-xbrl/) -- Dimensional data access, segment reporting, statement stitching [MEDIUM confidence]
- [EdgarTools Financial Statement Extraction](https://edgartools.readthedocs.io/en/latest/guides/extract-statements/) -- MultiFinancials API, quarterly support, standardized concepts [MEDIUM confidence]
- [Beneish M-Score (Wikipedia)](https://en.wikipedia.org/wiki/Beneish_M-score) -- 8-component formula reference [HIGH confidence]
- [Sloan Accruals Ratio](https://breakingdownfinance.com/finance-topics/equity-valuation/sloan-accruals-ratio/) -- Balance sheet and cash flow approaches, threshold zones [MEDIUM confidence]
- [SEC IFRS Taxonomy](https://www.sec.gov/structureddata/ifrs_taxonomy) -- IFRS namespace support in EDGAR [HIGH confidence]
- [SEC XBRL Guide Feb 2026](https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide.pdf) -- Current XBRL taxonomy specifications [HIGH confidence]
- [2025 SEC XBRL Taxonomy Updates](https://www.workiva.com/blog/2025-sec-xbrl-taxonomy-updates-key-changes-and-implications-filers) -- Taxonomy evolution and new elements [MEDIUM confidence]
