# Phase 72: SEC Frames API Peer Benchmarking - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the current ratio-to-baseline proxy benchmarking with true percentile ranking across all SEC filers using the SEC Frames API. SIC-code sector filtering at two levels (2-digit broad industry, 4-digit narrow sub-industry). Existing yfinance peer benchmarking kept for non-XBRL metrics (volatility, short interest, governance score).

</domain>

<decisions>
## Implementation Decisions

### SIC Mapping Build Strategy
- Full batch upfront: fetch CIK-to-SIC mapping for all ~8K unique CIKs on first run (~15 min), then cached 180 days
- Runs during the pipeline (not a separate CLI command). First pipeline run takes longer; subsequent runs are instant.
- SIC-based filtering with modern human-readable sector labels (not NAICS). NAICS taxonomy deferred to Industry-Specific Risk Analysis milestone.
- Two-level sector percentile: 2-digit SIC (broad industry, ~200-1,000 peers) AND 4-digit SIC (narrow sub-industry, ~20-200 peers)
- Minimum 10 peers for sector percentile to be computed. Below 10, fall back to broader SIC group or show N/A.
- Uses existing `_SIC_2DIGIT_SECTOR_MAP` in sec_identity.py for label generation

### Metric Selection
- 9 direct metrics (single Frames call each): Revenue, Net Income, Total Assets, Total Equity, Total Liabilities, Operating Income, Cash from Ops, R&D Expense, Goodwill
- 5 derived metrics (require CIK-joining two Frames responses): Operating Margin, D/E Ratio, Current Ratio, ROE, Net Margin
- Revenue tag fragmentation: primary tag (Revenues) + fallback merge (RevenueFromContractWithCustomerExcludingAssessedTax). Fetch both, merge by CIK, prefer primary.
- Metric registry designed for extensibility: sector-conditional ratios (NIM for banks, loss ratio for insurance, etc.) can be added in future industry-specific phase
- Total: ~20 Frames API calls per run (9 direct + ~11 components for derived), cached for 180 days on completed periods

### Fallback & Transition Behavior
- Frames percentile replaces ratio-to-baseline entirely for all covered financial metrics. Clean cutover, no dual display.
- When company missing from Frames response: use company's own XBRL value (from Phase 67 extraction) and rank against Frames population. HIGH confidence data ranked against real distribution.
- Non-XBRL metrics (volatility, short interest, governance score) keep existing yfinance peer benchmarking unchanged. Clear boundary.
- `ratio_to_baseline()` remains for non-Frames metrics only; dead code for Frames-covered metrics.

### Caching & Staleness Policy
- Frames data: 180-day TTL for completed periods (CY2023 etc.), 7-day TTL for current/recent period
- SIC mapping: 180-day TTL (SIC codes almost never change for a company)
- Cache store: existing SQLite AnalysisCache (consistent with all other caching in the system)
- Compression: zlib before caching (JSON compresses ~80-90%, reducing 90-360MB to 10-40MB)
- Per-concept caching: each Frames response cached independently by taxonomy/tag/unit/period key

### Claude's Discretion
- Exact SIC-to-sector label mapping for display (use existing maps or enhance)
- How to handle CIK-join mismatches for derived metrics (inner join vs left join)
- Frames API period auto-detection (most recent complete annual period)
- Whether to store intermediate joined data or recompute each time
- Progress reporting during SIC mapping build (~15 min first run)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `percentile_engine.py`: `percentile_rank()` with tie handling and higher/lower-is-better support. Core statistical function, fully reusable.
- `peer_metrics.py`: `MetricDef` registry pattern and `compute_peer_rankings()` flow. Extend with Frames-sourced metrics.
- `sec_identity.py`: `_SIC_2DIGIT_SECTOR_MAP` and `_SIC_4DIGIT_SECTOR_MAP` for sector label lookup.
- `rate_limiter.py`: `sec_get()` handles 10 req/sec, retries, 403 backoff. Use for all Frames API calls.
- `AnalysisCache` (SQLite): set/get/TTL/source tracking. Use for both Frames data and SIC mapping cache.
- `BenchmarkResult` model in `scoring.py`: Has `metric_details`, `peer_rankings`. Extend with `frames_percentiles`.
- `MetricBenchmark` model: Already has `percentile_rank`, `peer_count`, `baseline_value` fields.

### Established Patterns
- SourcedValue pattern: Every data point gets source + confidence + as_of
- Tier 1 manifest (Phase 70): Frames data is foundational — always fetched
- Signal field_key convention: `benchmarked.frames_percentiles.{metric}` for new peer signals

### Integration Points
- `stages/acquire/clients/sec_client.py`: Call `acquire_frames()` after `company_facts`
- `stages/benchmark/__init__.py`: Call `compute_frames_percentiles()` after existing `compute_peer_rankings()`
- `models/scoring.py`: Add `frames_percentiles` to `BenchmarkResult`
- `brain/signals/fin/`: New `peer_xbrl.yaml` for peer-relative threshold signals
- `context_builders/`: Frames percentile data flows to rendering via shared context

</code_context>

<specifics>
## Specific Ideas

- "NAICS would be better" — user recognizes SIC limitations but accepts SIC for this phase since SEC data is SIC-native. NAICS taxonomy deferred to Industry-Specific Risk Analysis milestone.
- "You can add more industry specific ones" — metric registry should be extensible for sector-conditional ratios (NIM for banks, R&D/revenue for tech, etc.). Phase 72 builds the infrastructure; industry-specific metrics come later.
- Goodwill explicitly requested as a direct metric — flags M&A-heavy companies, directly relevant to D&O (acquisition-related lawsuits).
- Both 2-digit AND 4-digit SIC percentile — user wants broad industry context AND narrow sub-industry positioning.

</specifics>

<deferred>
## Deferred Ideas

- NAICS-based classification — belongs in Industry-Specific Risk Analysis milestone
- Sector-conditional derived ratios (NIM, loss ratio, etc.) — future phase, but registry should be extensible
- SIC-to-NAICS crosswalk table — deferred with NAICS

</deferred>

---

*Phase: 72-peer-benchmarking*
*Context gathered: 2026-03-06*
