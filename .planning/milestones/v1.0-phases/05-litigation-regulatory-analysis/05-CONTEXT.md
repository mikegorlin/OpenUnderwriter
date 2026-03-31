# Phase 5: Litigation & Regulatory Analysis - Context

**Gathered:** 2026-02-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a complete legal landscape for any publicly traded company. Extract and structure securities class actions, SEC enforcement pipeline position, derivative suits, regulatory proceedings, M&A litigation, workforce/product/environmental claims, defense strength assessment, industry claim patterns, statute of limitations mapping, and known contingent liabilities. All data populates the state model for downstream scoring and rendering. No UI or CLI changes.

</domain>

<decisions>
## Implementation Decisions

### Data Source Strategy
- Stanford SCAC as primary source for securities class actions, with 10-K Item 3 as supplement for company's own characterization — cross-reference for completeness
- SEC enforcement depth: Claude's discretion on how deep to dig beyond company disclosures (EDGAR full-text search, Litigation Releases, AAERs at minimum)
- Regulatory proceedings (DOJ, FTC, EPA, state AGs, CFPB): parse 10-K Item 3 and 8-K disclosures, then run targeted web searches for company + regulator names
- Proactively search EDGAR for SEC comment letter correspondence (CORRESP/UPLOAD filings) even when company doesn't mention them
- Whistleblower activity: proactively search for whistleblower complaints, qui tam suits, SEC whistleblower awards as leading indicators

### Time Horizons (Tiered by Case Type)
- Securities class actions: 10 years
- SEC enforcement / regulatory proceedings: 5 years
- Employment, product liability, environmental: 3 years
- Claude's discretion on exact cutoffs within these tiers

### Case Classification & Taxonomy
- Two-layer classification system:
  - Primary: D&O coverage relevance (Securities Class Actions Side A/B/C, Derivative Suits Side A/B, SEC Enforcement Side A/B, Regulatory entity-level, Employment/Product entity-level)
  - Secondary: Legal theory tags (10b-5, Section 11, Section 14(a), derivative breach of duty, FCPA, antitrust, employment discrimination, environmental, etc.)
- Procedural tracking: key milestones only (filing date, current status active/settled/dismissed, settlement amount, key ruling outcomes) — not full procedural timeline
- Settlement data: capture whatever is available and relevant, with amount being the most important field
- Lead counsel: track identity AND tier classification (top-tier firms like Bernstein Litowitz, Robbins Geller signal higher severity/settlement potential)

### SEC Enforcement Pipeline
- Map to discrete stages with signals: comment letters → informal inquiry → formal investigation → Wells notice → enforcement action
- Flag the highest confirmed stage based on available evidence
- Signal sources: "under investigation" language in 10-K, Wells notice disclosure in 8-K, CORRESP filings on EDGAR, SEC Litigation Releases
- Enforcement outcomes: narrative summary (not structured fields)
- Industry sweep detection: search for SEC enforcement actions against peer companies in same SIC/industry; flag active industry sweeps as risk signal

### Defense & Exposure Assessment
- Forum selection provisions: parse charter/bylaws from DEF 14A for federal forum provisions (Securities Act) and exclusive forum provisions (derivative suits)
- Judge analysis: identify assigned judge from case records AND cross-reference for known plaintiff-friendly or defense-friendly reputation via web search
- Statute of limitations: broad claim spectrum — core D&O (10b-5, Section 11, Section 14(a), derivative) plus FCPA, antitrust, ERISA, environmental, employment discrimination
- Contingent liabilities: Claude's discretion on depth of 10-K footnote parsing

### Industry Litigation Signals
- Industry claim patterns: both quantitative (SCA filing rate, settlement frequency, average severity by SIC) and qualitative (specific legal theories used against peer companies, exposure assessment for this company)
- Data sources: Stanford SCAC industry search + config-driven theory mapping + web search for emerging risks
- Contagion risk: flag when a novel legal theory succeeds against a peer company and this company has similar exposure
- Whistleblower tracking: search for signals as leading indicators of enforcement and litigation

### Claude's Discretion
- SEC enforcement dig depth beyond company disclosures
- Contingent liability footnote parsing depth
- Exact time horizon cutoffs within the tiered framework
- Lead counsel tier list composition
- Contagion detection methodology

</decisions>

<specifics>
## Specific Ideas

- Two-layer case classification mirrors how D&O policies actually work — primary grouping by coverage type, secondary by legal theory
- Industry sweep detection is a forward-looking risk signal (SEC targeting an industry means heightened risk for all players)
- Whistleblower activity as a leading indicator is high-value for underwriting — these often precede enforcement actions by 1-2 years
- Comment letters on EDGAR are an underutilized signal — they show what the SEC is asking about before it becomes an investigation

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-litigation-regulatory-analysis*
*Context gathered: 2026-02-08*
