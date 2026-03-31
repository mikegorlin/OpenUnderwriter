# Phase 7: Peer Benchmarking & Executive Summary - Context

**Gathered:** 2026-02-08
**Status:** Ready for planning

<domain>
## Phase Boundary

The BENCHMARK pipeline stage positions every metric peer-relative, and the Executive Summary (Section 1) synthesizes all findings into an at-a-glance risk assessment. This completes the analytical pipeline so that all data needed for document rendering exists in the state file. Requirements: SECT1-01 through SECT1-07 plus CORE-02.

</domain>

<decisions>
## Implementation Decisions

### Peer comparison depth
- Claude's discretion on which metrics get peer-relative ranks — should be driven by what the scoring engine and underwriting decision actually use
- Compute percentile ranks with whatever peers have data (even if only 3/5 peers have a given ratio); note sample size but don't suppress the comparison
- Claude's discretion on data source — determine what peer financial data is already available in state from Phase 3 vs. what needs fetching
- Claude's discretion on format — percentile ranks, ratio to peer median, or both, chosen per metric type for maximum informativeness

### Executive summary curation
- Claude's discretion on top 5 negative/positive selection — design a multi-signal ranking combining scoring impact, recency, trajectory, and claim probability correlation
- Include an underwriting thesis — a 2-3 sentence plain-English narrative connecting the dots ("This is a high-growth tech company facing elevated disclosure risk because...")
- Thesis generated via rich rule-based templates per risk type (GROWTH_DARLING, DISTRESSED, etc.) filled with specific findings — deterministic, no external API call needed
- Key findings (SECT1-03/04) presented as structured entries with labeled fields (Evidence | Section | Impact | Theory) — scannable and consistent
- SECT1-07 deal context: always show empty placeholder fields in ticker-only mode so underwriters know what to fill in

### Inherent risk baseline
- Extend existing sectors.json baselines with filing probability and severity ranges per sector + market cap tier
- Use research-based estimates from published actuarial data (NERA, Cornerstone, Stanford SCAC filing rates) to populate initial values during research phase
- Claude's discretion on how baseline interacts with company-specific score (multiplicative vs additive adjustment) — choose the actuarially sound approach
- Show baseline as standalone comparison in executive summary: "Industry base rate: X% | Company-adjusted: Y%" — the delta tells the underwriter how much worse/better than average

### Narrative tone & density
- Consulting report tone — professional narrative with context, like Marsh or McKinsey: "The company presents elevated disclosure risk driven by..."
- Content structure follows SECT1-01 through SECT1-07 requirements exactly — the worksheet specification defines what goes in, the tone decision defines how it reads

### Claude's Discretion
- Specific metrics selected for peer benchmarking
- Peer data acquisition strategy (reuse vs. fetch)
- Percentile vs. ratio format per metric
- Key findings ranking algorithm design
- Baseline-to-score adjustment methodology (multiplicative vs. additive)
- All template variants for narrative thesis by risk type

</decisions>

<specifics>
## Specific Ideas

- Underwriting thesis should sound like what an underwriter would say in a meeting — connecting risk type, top factors, and allegation theory into a coherent story
- Standalone inherent risk comparison ("Industry base rate: X% vs Company-adjusted: Y%") is high-value — the delta immediately tells the underwriter whether this company is better or worse than the industry
- Deal context placeholders with labeled blank fields signal to the underwriter what additional information would improve the analysis

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-peer-benchmarking-executive-summary*
*Context gathered: 2026-02-08*
