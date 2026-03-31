# Phase 38: Render Completeness & Quarterly Data - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Every field the brain acquires and populates in state.json appears in the rendered output. No silent data drops. Quarterly results (10-Q) after the most recent annual (10-K) are extracted and shown as a separate "Recent Quarterly Update" section. Word, Markdown, and PDF outputs are consistent in data coverage — same information, format-appropriate presentation.

</domain>

<decisions>
## Implementation Decisions

### Data Density & Prioritization
- **Show everything** — render all items in all data domains at full depth. Completeness wins over brevity. The underwriter can skim what they don't need.
- **Show all fields including empty** — every field appears even if no findings. "None found" confirms the system checked for it. Absence of evidence is documented.
- **No document length limit** — completeness is the priority. The underwriter navigates via table of contents and section headers.
- **Confidence badges on all data** — render every data point with its confidence level (HIGH/MEDIUM/LOW). The underwriter decides what to trust.

### Quarterly Update Presentation
- **Separate "Recent Quarterly Update" section** — standalone section after annual financials. Clear separation: "Here's the annual, here's what changed since."
- **Key metrics + material changes** — revenue, net income, EPS, plus new legal proceedings, going concern flags, material weakness changes, management commentary
- **YTD comparison** — show YTD figures (e.g., 6-month YTD for Q2, 9-month YTD for Q3) compared against the same YTD period from the prior year
- **Omit section if no 10-Q filed** — if no quarterly filing exists after the most recent 10-K, don't show the section at all

### Missing Data Domains
- **Executive summary first** — company snapshot, filing probability, top 5 negatives, top 5 positives, underwriting thesis — all on page 1. The TL;DR an underwriter reads first.
- **Full hazard profile table** — all 55 dimensions rendered with dimension name, exposure level, and evidence
- **Risk factors: D&O-relevant, new, or unique only** — filter SEC 10-K Item 1A to risk factors that are D&O-relevant, new (not in prior filing), or unique to this company (not standard boilerplate). Skip generic business risks.
- **Full forensic profile per board member** — each member gets: name, tenure, committees, independence status, interlocks, relationship flags, prior litigation, other board seats. Full transparency.

### Cross-Format Consistency
- **Three-tier format hierarchy:**
  - **MD**: Full data content, plain text formatting (the information baseline)
  - **Word**: Full data + rich formatting (tables, colors, layout) that MD can't express
  - **PDF**: Consulting-grade presentation — Bloomberg/McKinsey quality. This is the flagship deliverable. Professional style is critically important. (Note: Phase 38 ensures data completeness and consistency in PDF output. Visual polish — typography, colors, table formatting, print layout — is Phase 39 scope.)
- **Full field coverage test** — walk the state model, verify every non-null field appears in all three formats. Strict — catches any data that silently drops.
- **Fix pipeline bug first** — the AAPL "Unknown Company" / "data not available" deserialization/context-building bug must be diagnosed and fixed before adding new render coverage. No point adding sections if existing data isn't flowing.

### Claude's Discretion
- MD template splitting strategy (section-level includes vs other approach to stay under 500 lines)
- Exact table layouts and column ordering for new data domains
- How to handle the shared context builder across formats (enriching extract_* helpers vs building a common context layer)
- Hazard profile table grouping/ordering within the full table

</decisions>

<specifics>
## Specific Ideas

- The PDF is the flagship deliverable — "consulting-level presentation-quality report" that looks like it came from a top-tier firm. This cannot be emphasized enough.
- YTD quarterly comparison matches standard 10-Q format: if Q2 10-Q is the latest, show 6-month YTD vs prior year 6-month YTD
- Risk factor filtering (D&O-relevant, new, unique) is a key innovation — cuts through the boilerplate that makes Item 1A useless in most analyses
- "None found" for empty fields is important for underwriter trust — confirms the system looked rather than leaving ambiguity

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 38-render-completeness-quarterly-data*
*Context gathered: 2026-02-21*
