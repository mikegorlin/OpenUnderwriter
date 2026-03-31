# Phase 98: Sector Risk Classification - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Create 4+ brain signals (SECT.hazard_tier, SECT.claim_patterns, SECT.regulatory_overlay, SECT.peer_comparison) that classify where a company sits in the D&O risk landscape for its sector. All signals use static reference data tables with full provenance, evaluated through the brain signal framework, and rendered through facet dispatch.

Depends on Phase 93 (business model data) and Phase 97 (regulatory data for context).

</domain>

<decisions>
## Implementation Decisions

### Reference Data Approach
- Static YAML/config reference tables in `brain/config/` (alongside `sic_gics_mapping.json`)
- Seeded from SCAC + Cornerstone Research + NERA Economic Consulting D&O studies
- Full provenance on every data point: source publication, year, methodology notes
- No runtime SCAC scraping or external API dependencies for reference data
- Updated manually when new annual D&O studies are published

### Hazard Tier Mapping
- Classification granularity: GICS sub-industry level (~150 sub-industries from 8-digit GICS)
- Fallback chain: GICS sub-industry → SIC 2-digit sector (via existing `sic_to_sector()`) when no GICS match
- 4 tiers: Highest / High / Moderate / Lower — mapped from D&O filing rate data per sub-industry
- Pure lookup from reference table — no company-specific adjustments (those happen in other signals)
- Presentation: Color-coded tier badge + contextual explanation (e.g., "Technology sector has 2.3x average SCA filing rate")

### Peer Comparison Design
- Peers selected by GICS sub-industry match (same classification system as hazard tier)
- Compare across 4 core D&O risk dimensions: overall score, litigation frequency, governance quality, financial health
- Peer median data from static sector benchmarks in `brain/config/` (same reference data approach)
- Outlier threshold: >1 standard deviation from sector median on any dimension
- Provenance on benchmark data same as other reference tables

### SECT-03 vs ENVR-01 Differentiation
- SECT-03 = sector-level regulatory baseline (how regulated is this SECTOR generally?) — reference data
- ENVR-01 = company-specific regulatory intensity (from this company's filings) — extracted data
- SECT-03 includes named regulators per GICS sub-industry (e.g., "FDA, CMS, OIG" for Healthcare)
- Include brief static trend annotations in reference data (e.g., "Increased FTC scrutiny of tech M&A since 2023")
- Rendered in separate section from ENVR-01, with cross-reference link between them

### Claude's Discretion
- Exact YAML structure for reference data tables
- Signal evaluation formula implementation details
- Facet dispatch wiring approach
- How to handle sub-industries with insufficient filing rate data (merge up to industry group?)
- Specific color palette for tier badges (should follow existing signal presentation patterns)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `sic_to_sector()` in `stages/resolve/sec_identity.py`: Maps SIC → ~15 sector codes. Use as fallback when GICS unavailable.
- `sic_gics_mapping.json` in `brain/config/`: SIC → 8-digit GICS mapping. Already used for industry classification fallback.
- ENVR signal pattern in `brain/signals/env/environment.yaml`: Complete v6 signal with acquisition/evaluation/presentation blocks — template for SECT signals.
- Signal schema v3 established across all v6 signals (BMOD, OPS, EVENT, ENVR categories).

### Established Patterns
- Brain signals defined in YAML under `brain/signals/{domain}/` with `schema_version: 3`
- Signal evaluation through check engine and signal mappers
- Reference/lookup data in `brain/config/` (JSON format, e.g., `sic_gics_mapping.json`)
- Output manifest wiring for facet dispatch rendering
- `sector_filter` field exists in signal schema but currently unused — could be leveraged

### Integration Points
- Signals wire into output manifest (`brain/output_manifest.yaml`) for render dispatch
- Sector determination already happens in RESOLVE stage (SIC + GICS available in `state.company.identity`)
- ENVR-01 (regulatory intensity) is the cross-reference target for SECT-03
- Check engine evaluates signals and triggers red flags when thresholds breached

</code_context>

<specifics>
## Specific Ideas

- Reference tables should be structured so the brain portability principle holds — if you took the YAML + reference data, another system could classify sectors
- Hazard tier naming matches D&O insurance industry convention: "Highest Hazard" is familiar to underwriters
- Claim patterns should show top 3 claim theories per sector (e.g., Technology: "Missed earnings guidance", "Product defect/safety", "Trade secret misappropriation")
- Peer comparison should clearly label when data is based on sector benchmarks vs actual peer analysis

</specifics>

<deferred>
## Deferred Ideas

- Custom peer group selection (manually curated) — per REQUIREMENTS.md, deferred
- Live SCAC scraping for real-time filing rate updates — future enhancement
- Building peer statistics from pipeline run history — future enhancement after more companies analyzed
- Market cap banding for peer selection — adds complexity, revisit when peer comparison matures
- External benchmark API integration (AM Best, S&P) — subscription dependency, out of scope

</deferred>

---

*Phase: 98-sector-risk-classification*
*Context gathered: 2026-03-10*
