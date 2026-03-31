# Phase 72: SEC Frames API Peer Benchmarking - Research

**Researched:** 2026-03-06
**Domain:** SEC XBRL Frames API, cross-filer percentile computation, SIC-code sector filtering
**Confidence:** HIGH

## Summary

Phase 72 replaces the current ratio-to-baseline proxy benchmarking with true percentile ranking across all SEC filers using the Frames API. The existing system (in `peer_metrics.py` and `percentile_engine.py`) has 7 metrics, 3 sources (peer_company, sector_baseline, risk_score), and falls back to `ratio_to_baseline()` against fixed sector averages from `sectors.json` when peer data is unavailable. This produces fake percentiles -- a ratio scaled to 0-100 rather than a real population rank.

The SEC Frames API (`data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json`) returns one value per reporting entity for a given XBRL concept and calendar period. A single call for Revenues/USD/CY2024 returns ~5,000-10,000 filer values. This enables true `percentile_rank()` computation against the full SEC filer population. The existing `percentile_rank()` function in `percentile_engine.py` is already correct and reusable -- it just needs real peer data instead of 5-10 yfinance peers.

The main technical challenge is SIC-code filtering: the Frames API response contains `cik`, `entityName`, `loc`, `end`, `val`, `accn` per entity but NOT SIC codes. Sector-relative percentile requires cross-referencing Frames data with a CIK-to-SIC mapping. The SEC submissions API (`data.sec.gov/submissions/CIK{cik}.json`) contains `sic` and `sicDescription` fields, but calling it for each of ~8,000 CIKs is not feasible. The solution is to build a bulk CIK-to-SIC lookup from the SEC submissions bulk download, cached for 30+ days.

**Primary recommendation:** Build a `sec_client_frames.py` acquisition client that fetches Frames data for 10-15 key XBRL concepts, paired with a CIK-to-SIC mapping cache built from SEC bulk data. Feed this into the existing `compute_peer_rankings()` flow in the BENCHMARK stage via a new `frames_benchmarker.py` module.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PEER-01 | Frames API client: `acquire_frames(concepts, periods)` for 10-15 metrics. Cache 180 days/1 day. | SEC Frames API documented below. URL format, response structure, caching strategy all mapped. Use existing `sec_get()` rate limiter. |
| PEER-02 | True percentile against ALL SEC filers. Replace ratio-to-baseline proxy. | Existing `percentile_rank()` in `percentile_engine.py` is reusable. Frames data provides the real `peer_values` list. Current `ratio_to_baseline()` codepath becomes dead code. |
| PEER-03 | SIC-code filtering: cross-reference with company_tickers.json for sector percentile. Cache CIK-to-SIC. | `company_tickers.json` does NOT have SIC codes. Use SEC submissions bulk data or individual submissions API instead. See SIC Mapping section. |
| PEER-04 | Benchmark 10-15 metrics: revenue, net income, total assets, D/E, current ratio, interest coverage, operating margin, net margin, ROE, revenue growth. | Metric-to-XBRL-tag mapping provided in Metric Registry section. Some metrics are derived (ratios) and cannot come directly from Frames -- must compute from multiple Frames calls. |
| PEER-05 | Percentile signals for brain (peer-relative thresholds). | New signal YAML with `field_key` pointing to `benchmarked.frames_percentiles.{metric}`. Pattern follows existing signal schema. |
| PEER-06 | Keep existing yfinance peer group for non-XBRL metrics. | Current `peer_metrics.py` METRIC_REGISTRY kept intact for volatility, short_interest, governance_score. Frames metrics added alongside, not replacing. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | existing | SEC API HTTP calls | Already used via `sec_get()` in rate_limiter.py |
| sqlite3 | stdlib | Cache storage | Already used via `AnalysisCache` |
| Pydantic v2 | existing | Data models | Project standard for all models |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy | existing | Percentile computation (optional) | Only if `percentile_rank()` needs optimization for 8K+ values |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom percentile function | numpy.percentile | Existing `percentile_rank()` is simple and correct; numpy adds dependency for no benefit on ~8K values |
| SEC submissions bulk download | Individual submissions API calls | Bulk is one download vs 8,000 API calls; bulk wins decisively |

**Installation:** No new dependencies needed. Everything is already installed.

## Architecture Patterns

### Recommended Project Structure
```
stages/acquire/clients/
  sec_client_frames.py      # NEW: Frames API acquisition + caching
  sec_client.py             # MODIFIED: call acquire_frames() after company_facts
stages/benchmark/
  frames_benchmarker.py     # NEW: true percentile computation from Frames data
  peer_metrics.py           # MODIFIED: add Frames-sourced metrics to registry
  percentile_engine.py      # UNCHANGED: reuse existing percentile_rank()
models/
  scoring.py                # MODIFIED: add frames_percentiles to BenchmarkResult
brain/signals/fin/
  peer_xbrl.yaml            # NEW: peer-relative threshold signals
```

### Pattern 1: Frames API Acquisition (ACQUIRE stage)
**What:** Fetch cross-filer data for specific XBRL concepts and calendar periods.
**When to use:** Called once per pipeline run, after company_facts acquisition.
**Example:**
```python
# URL pattern (from SEC EDGAR API docs):
# https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json
#
# Period formats:
#   CY2024     -- annual (duration ~365 days +/- 30 days)
#   CY2024Q3   -- quarterly duration (~91 days +/- 30 days)
#   CY2024Q3I  -- instantaneous (balance sheet point-in-time)
#
# Response structure:
# {
#   "taxonomy": "us-gaap",
#   "tag": "Revenues",
#   "ccp": "CY2024",      # calendar period code
#   "uom": "USD",          # unit of measure
#   "label": "Revenues",
#   "description": "...",
#   "pts": 6234,           # point count (number of entities)
#   "data": [
#     {
#       "accn": "0000320193-24-000123",
#       "cik": 320193,
#       "entityName": "Apple Inc",
#       "loc": "CA",
#       "end": "2024-09-28",
#       "val": 391035000000
#     },
#     ...
#   ]
# }

SEC_FRAMES_URL = (
    "https://data.sec.gov/api/xbrl/frames/"
    "{taxonomy}/{tag}/{unit}/{period}.json"
)
```

### Pattern 2: Two-Level Percentile (Overall + Sector)
**What:** Compute percentile against all filers AND against same-SIC filers.
**When to use:** For every Frames-benchmarked metric.
**Example:**
```python
# Overall percentile: rank against ALL filers in Frames response
overall_pct = percentile_rank(company_val, all_values, higher_is_better=True)

# Sector percentile: filter Frames data to same 2-digit SIC, then rank
sector_ciks = sic_mapping.get_ciks_for_sic_prefix(company_sic[:2])
sector_values = [v for cik, v in frames_data if cik in sector_ciks]
sector_pct = percentile_rank(company_val, sector_values, higher_is_better=True)
```

### Pattern 3: Cache Strategy (System-Level, Not Per-Company)
**What:** Frames data is cached at system level since it covers ALL filers.
**When to use:** Every Frames API call.
**Key insight:** Frames data for completed fiscal periods is immutable. CY2023 revenue data will never change.
```python
# Cache key pattern:
# "sec:frames:{taxonomy}:{tag}:{unit}:{period}"
# Example: "sec:frames:us-gaap:Revenues:USD:CY2024"
#
# TTL:
# - Completed periods (CY2023, CY2024Q1, etc.): 180 days
# - Current/recent period (CY2024 if still open): 1 day
```

### Anti-Patterns to Avoid
- **Fetching Frames for ALL 120+ XBRL concepts:** Each call returns 5-20MB. Only fetch for 10-15 key benchmarking metrics. The rest are for single-company analysis only.
- **Calling submissions API per CIK for SIC lookup:** Would require ~8,000 API calls. Use bulk data instead.
- **Storing Frames responses uncompressed:** At 5-20MB each, 15 metrics x 3 periods = 225-900MB. Compress with zlib before caching.
- **Computing derived ratios from Frames data:** Frames returns single concepts, not ratios. D/E ratio requires two separate Frames calls (total_debt and equity) and matching by CIK. This is architecturally different from single-concept percentile.
- **Assuming Frames period alignment matches company fiscal year:** Frames uses calendar alignment (+/- 30 days). Apple's FY2024 (ending Sep 2024) maps to CY2024 in Frames. This is correct for cross-company comparison but may differ from Company Facts fiscal labels.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP rate limiting | Custom rate limiter | Existing `sec_get()` in rate_limiter.py | Already handles 10 req/sec, retries, 403 backoff |
| Percentile computation | New percentile function | Existing `percentile_rank()` in percentile_engine.py | Correct formula with tie handling and higher/lower-is-better support |
| SIC-to-sector mapping | New mapping table | Existing `_SIC_2DIGIT_SECTOR_MAP` and `_SIC_4DIGIT_SECTOR_MAP` in sec_identity.py | Already handles 4-digit disambiguation (pharma vs chemicals, etc.) |
| Cache with TTL | New cache system | Existing `AnalysisCache` (SQLite) | Already has set/get/TTL/source tracking |
| Metric display in BENCHMARK | New rendering | Existing `MetricBenchmark` model + context_builders | Model already has percentile_rank, peer_count, baseline_value fields |

**Key insight:** The existing benchmarking infrastructure is well-designed -- it just lacks real peer data. Phase 72 provides the data; the computation and display layers are largely reusable.

## Common Pitfalls

### Pitfall 1: Frames API Does NOT Include SIC Codes
**What goes wrong:** Assuming Frames response has SIC codes for sector filtering.
**Why it happens:** The PEER-03 requirement says "cross-reference with company_tickers.json for sector percentile" but `company_tickers.json` only has `cik_str`, `ticker`, `title` -- no SIC codes.
**How to avoid:** Build a separate CIK-to-SIC mapping from SEC submissions bulk data. Two options:
  1. **Batch approach (recommended):** Download `data.sec.gov/submissions/CIK{cik}.json` for the ~8,000 CIKs found in Frames responses, extract `sic` field, cache mapping for 90 days. At 10 req/sec this takes ~15 minutes but only needs to run once per 90 days.
  2. **On-demand approach:** For the target company's SIC code (already on `state.company.identity.sic_code`), filter Frames data by 2-digit SIC prefix. Requires knowing which CIKs share the SIC prefix, which still needs the bulk mapping.
**Warning signs:** Sector percentile always returning 50% (no filtering applied).

### Pitfall 2: Derived Metrics Cannot Come Directly from Frames
**What goes wrong:** Trying to get D/E ratio, current ratio, or operating margin from a single Frames call.
**Why it happens:** Frames returns one concept per call. Ratios require two concepts (e.g., debt / equity). You'd need to fetch both concepts, match entities by CIK, then compute the ratio per entity.
**How to avoid:** For each derived metric:
  1. Fetch both component Frames (e.g., `Liabilities` and `StockholdersEquity`)
  2. Inner-join by CIK (only entities reporting both concepts)
  3. Compute ratio per entity
  4. Rank company's ratio against computed peer ratios
This is more complex but the only correct approach. Some metrics (revenue, net_income, total_assets) are direct single-concept lookups.

### Pitfall 3: Frames Response Size and Memory
**What goes wrong:** Loading 15 Frames responses (5-20MB each) into memory simultaneously.
**Why it happens:** Naive implementation fetches all frames before processing.
**How to avoid:** Process one frame at a time. Extract only the `val` list and the company's specific entry. Do not store the full response in state -- store only the computed percentile results.

### Pitfall 4: Missing Company in Frames Data
**What goes wrong:** Company CIK not found in Frames response for a given concept/period.
**Why it happens:** Company may not report that concept, may use a different tag, or may have a non-calendar fiscal year that falls outside the +/- 30 day window.
**How to avoid:** Graceful fallback to existing ratio-to-baseline for that metric. Log which metrics had Frames coverage and which fell back. Do NOT return 50th percentile as default -- return None and let the display layer handle it.

### Pitfall 5: Calendar Period Selection
**What goes wrong:** Fetching the wrong period (e.g., CY2024 when most recent data is CY2023).
**Why it happens:** Frames data for the current year may be sparse (not all companies have filed yet). The most recent COMPLETE period is usually 1-2 quarters behind.
**How to avoid:** Determine the most recent complete annual period based on the target company's most recent 10-K filing date. If the company filed its 10-K for FY2024, use CY2024. Fall back to CY2023 if CY2024 has <50% of CY2023's entity count.

## Code Examples

### Frames API Client
```python
# stages/acquire/clients/sec_client_frames.py

SEC_FRAMES_URL = (
    "https://data.sec.gov/api/xbrl/frames/"
    "{taxonomy}/{tag}/{unit}/{period}.json"
)

# Metrics to benchmark -- each maps to one or more XBRL tags
FRAMES_METRICS: list[FramesMetricDef] = [
    # Direct (single concept = single Frames call)
    FramesMetricDef("revenue", "Revenues", "USD", "duration", True),
    FramesMetricDef("net_income", "NetIncomeLoss", "USD", "duration", True),
    FramesMetricDef("total_assets", "Assets", "USD", "instant", True),
    FramesMetricDef("total_equity", "StockholdersEquity", "USD", "instant", True),
    FramesMetricDef("total_liabilities", "Liabilities", "USD", "instant", False),
    FramesMetricDef("operating_income", "OperatingIncomeLoss", "USD", "duration", True),
    FramesMetricDef("cash_from_operations", "NetCashProvidedByOperatingActivities", "USD", "duration", True),

    # For derived ratios (need two components)
    FramesMetricDef("current_assets", "AssetsCurrent", "USD", "instant", True),
    FramesMetricDef("current_liabilities", "LiabilitiesCurrent", "USD", "instant", False),
    FramesMetricDef("long_term_debt", "LongTermDebt", "USD", "instant", False),
]
```

### Period Format Selection
```python
def _build_period_string(year: int, concept_type: str) -> str:
    """Build Frames API period string.

    Duration concepts (revenue, income): CY2024
    Instant concepts (assets, liabilities): CY2024I
    """
    if concept_type == "instant":
        return f"CY{year}I"
    return f"CY{year}"
```

### CIK-to-SIC Mapping Strategy
```python
# Option A: Build from individual submissions calls (slow but complete)
# Each submissions response has: {"cik": "320193", "sic": "3571", ...}
# Cache the full CIK->SIC map for 90 days

# Option B: Use company's own SIC and 2-digit prefix matching
# state.company.identity.sic_code = "3571" (from RESOLVE stage)
# 2-digit prefix = "35" = "Industrial and Commercial Machinery"
# Filter Frames to CIKs with SIC prefix "35"
# This requires having the mapping either way

# Recommendation: Build mapping incrementally
# 1. First run: fetch SIC for CIKs in Frames response (batch, cached)
# 2. Subsequent runs: use cached mapping, refresh expired entries
```

### Integrating with Existing Benchmark Stage
```python
# In benchmark/__init__.py BenchmarkStage.run():
# After existing compute_peer_rankings():

from do_uw.stages.benchmark.frames_benchmarker import compute_frames_percentiles

frames_percentiles = compute_frames_percentiles(
    frames_data=state.acquired_data.get("filings", {}).get("frames", {}),
    company_cik=state.company.identity.cik.value,
    company_sic=state.company.identity.sic_code.value if state.company.identity.sic_code else None,
    sic_mapping=sic_cache,  # CIK -> SIC dict
)

# Merge into BenchmarkResult
state.benchmark.frames_percentiles = frames_percentiles
# Also feed individual metrics into metric_details for unified display
```

## Metric Registry: XBRL Tags for Benchmarking

### Direct Metrics (single Frames call each)
| Metric | XBRL Tag | Unit | Period Type | Higher is Better |
|--------|----------|------|-------------|-----------------|
| Revenue | `Revenues` | USD | duration (CY2024) | Yes |
| Net Income | `NetIncomeLoss` | USD | duration | Yes |
| Total Assets | `Assets` | USD | instant (CY2024I) | Yes |
| Total Equity | `StockholdersEquity` | USD | instant | Yes |
| Total Liabilities | `Liabilities` | USD | instant | No |
| Operating Income | `OperatingIncomeLoss` | USD | duration | Yes |
| Cash from Operations | `NetCashProvidedByOperatingActivities` | USD | duration | Yes |
| R&D Expense | `ResearchAndDevelopmentExpense` | USD | duration | Context-dependent |

### Derived Metrics (require two Frames calls + CIK join)
| Metric | Components | Formula | Higher is Better |
|--------|-----------|---------|-----------------|
| Current Ratio | AssetsCurrent, LiabilitiesCurrent | CA / CL | Yes |
| D/E Ratio | Liabilities, StockholdersEquity | L / SE | No |
| Operating Margin | OperatingIncomeLoss, Revenues | OI / Rev | Yes |
| Net Margin | NetIncomeLoss, Revenues | NI / Rev | Yes |
| ROE | NetIncomeLoss, StockholdersEquity | NI / SE | Yes |

### Non-Frames Metrics (keep existing yfinance path)
| Metric | Source | Reason Not Frames |
|--------|--------|-------------------|
| Volatility 90d | yfinance | Market data, not XBRL |
| Short Interest % | yfinance | Market data, not XBRL |
| Governance Score | Internal scoring | System-computed, not XBRL |

**Total API calls per run:** 8 direct + 2x5 derived components = 18 Frames calls (at 10 req/sec = ~2 seconds). Cached for 180 days on completed periods.

## SIC Code Mapping Strategy

### The Problem
Frames API response has `cik` but no `sic`. We need CIK-to-SIC mapping for ~8,000 entities.

### Recommended Approach: Incremental Submissions Fetch
1. **On first Frames fetch:** Collect all unique CIKs from the Frames response
2. **For each unique CIK:** Check local SIC cache. If miss, queue for fetch.
3. **Batch fetch:** Call `data.sec.gov/submissions/CIK{cik}.json` for uncached CIKs. Extract `sic` field.
4. **Rate:** 10 req/sec = 800 CIKs/min. Full build of ~8,000 CIKs = ~15 minutes. Run once, cache 90 days.
5. **Cache key:** `sec:sic_mapping:{cik}` with 90-day TTL.
6. **Incremental:** On subsequent runs, only fetch SICs for new CIKs not in cache.

### Why Not company_tickers.json
The SEC's `company_tickers.json` (already used in RESOLVE stage) contains only `cik_str`, `ticker`, `title`. No SIC codes. The SEC's `company_tickers_exchange.json` adds `exchange` but still no SIC.

### Why Not Bulk Submissions Download
SEC provides bulk submissions at `data.sec.gov/submissions/` but there's no single "all CIK-to-SIC" file. Each company's submissions file must be fetched individually.

### SIC Prefix Matching
For sector percentile, use 2-digit SIC prefix (the "division" level):
- SIC 35xx = Industrial Machinery (company's 4-digit SIC code determines exact mapping)
- SIC 73xx = Business Services (includes software companies)
- The existing `_SIC_2DIGIT_SECTOR_MAP` in `sec_identity.py` maps 2-digit ranges to sector codes

This gives ~200-1,000 companies per 2-digit SIC group, which is statistically meaningful for percentile ranking.

## State of the Art

| Old Approach (current) | New Approach (Phase 72) | Impact |
|------------------------|------------------------|--------|
| 5-10 yfinance peers for market_cap/revenue | ~8,000 SEC filers for 10-15 XBRL metrics | True population percentile |
| Fixed sector baselines from sectors.json | SIC-filtered actual filer data | Real sector comparison |
| `ratio_to_baseline()` proxy percentile | `percentile_rank()` on real distribution | Statistically valid |
| 7 metrics (2 peer, 3 sector, 2 risk) | 15+ metrics (8 direct + 5 derived + existing 3) | Comprehensive coverage |
| Zero XBRL in benchmarking | Full XBRL for financial metrics | HIGH confidence data |

**Deprecated after this phase:**
- `ratio_to_baseline()` for financial metrics (keep for non-XBRL metrics only)
- Sector baseline values in `sectors.json` for financial metrics that Frames covers

## Data Flow

```
ACQUIRE Stage:
  sec_client.py
    |
    +-- acquire_company_facts()  [EXISTING]
    +-- acquire_frames()         [NEW - calls sec_client_frames.py]
           |
           +-- For each of 18 concepts: Frames API call
           +-- Cache each response (180-day TTL for completed periods)
           +-- Return dict keyed by metric name
           |
    +-- acquire_sic_mapping()    [NEW - builds CIK->SIC cache]
           |
           +-- Collect unique CIKs from Frames responses
           +-- Batch fetch submissions for uncached CIKs
           +-- Cache SIC per CIK (90-day TTL)

BENCHMARK Stage:
  benchmark/__init__.py
    |
    +-- compute_peer_rankings()  [EXISTING - unchanged for yfinance metrics]
    +-- compute_frames_percentiles()  [NEW]
           |
           +-- For each direct metric: find company in Frames, rank
           +-- For each derived metric: join two Frames by CIK, compute ratio, rank
           +-- For each metric: compute overall + sector percentile
           +-- Return FramesPercentiles model
    +-- Merge into BenchmarkResult
```

## Open Questions

1. **Frames API response size in practice**
   - What we know: Documentation says one fact per entity. ~8,000 filers expected.
   - What's unclear: Actual JSON size. Could be 2MB or 20MB depending on entity count and field sizes.
   - Recommendation: Fetch one sample frame during implementation to measure. Consider zlib compression for cache storage.

2. **SIC mapping build time on first run**
   - What we know: ~8,000 submissions API calls at 10/sec = ~15 minutes.
   - What's unclear: Whether this is acceptable for first-run UX.
   - Recommendation: Build SIC mapping incrementally. First run fetches only the target company's SIC peers (~200-500 calls = 30-60 seconds). Background job builds full mapping.

3. **Revenue tag fragmentation in Frames**
   - What we know: Revenue has multiple valid tags (Revenues, RevenueFromContractWithCustomerExcludingAssessedTax, etc.). Frames returns data for ONE tag per call.
   - What's unclear: Which tag has the broadest coverage in Frames.
   - Recommendation: Start with `Revenues` (most common). If coverage is low, also fetch `RevenueFromContractWithCustomerExcludingAssessedTax` and merge by CIK (take either).

## Sources

### Primary (HIGH confidence)
- [SEC EDGAR API Documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) -- Official Frames API endpoint documentation
- [sec-edgar-api Python wrapper docs](https://sec-edgar-api.readthedocs.io/) -- Confirmed Frames API URL format, response fields (taxonomy, tag, ccp, uom, label, description, pts, data[].accn/cik/entityName/loc/end/val)
- Existing codebase: `peer_metrics.py`, `percentile_engine.py`, `sec_client.py`, `ticker_resolver.py`, `sec_identity.py`, `benchmark/__init__.py`, `scoring.py` (BenchmarkResult model)

### Secondary (MEDIUM confidence)
- [SEC Submissions API](https://data.sec.gov/submissions/) -- CIK-to-SIC mapping source (fields: cik, sic, sicDescription confirmed via multiple sources)
- [SEC company_tickers.json](https://www.sec.gov/files/company_tickers.json) -- Confirmed: NO SIC codes in this file (only cik_str, ticker, title)

### Tertiary (LOW confidence)
- Frames API response size estimates (5-20MB per frame) -- from architecture research, not empirically verified for this project
- SIC mapping build time (~15 minutes for 8K CIKs) -- calculated estimate, not tested

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, all existing libraries
- Architecture: HIGH - existing percentile_engine and benchmark stage are well-understood from code review
- Frames API format: HIGH - confirmed via sec-edgar-api docs and SEC official documentation
- SIC mapping approach: MEDIUM - correct strategy but build time and coverage not empirically validated
- Pitfalls: HIGH - identified from codebase analysis and SEC API documentation

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (SEC APIs are stable; no expected breaking changes)
