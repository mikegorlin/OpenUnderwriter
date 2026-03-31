# Phase 47: Check Data Mapping Completeness - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire up ~40 routing-gap checks (bucket-a: field exists in `ExtractedData` but `FIELD_FOR_CHECK` entry is missing) to their corresponding fields. Fill ~28 extraction-gap checks (bucket-b) with new extractor fields. Expand DEF 14A extraction to populate board diversity, director tenure, expertise, and attendance fields. Surface threshold criteria on all triggered findings. Regression on AAPL, RPM, TSLA must hold. No new capabilities — all work is within the SKIPPED check population classified by Phase 46.

</domain>

<decisions>
## Implementation Decisions

### Threshold context display
- QA audit table: full criterion text (e.g., "red: Prior SEC enforcement action within 5 years")
- HTML worksheet: footnote-style — triggered findings get a reference mark; criterion text collected at section end
- Word doc: inline parenthetical (e.g., "CFO departure (red: executive departure within 6 months of inquiry)") — python-docx footnotes are too complex
- Source of truth: brain YAML `threshold.red` / `threshold.yellow` fields, read at evaluation time and stored on `CheckResult.threshold_context`
- Evaluator populates `threshold_context` when a check triggers; downstream render uses it

### DEF 14A missing field handling
- Default behavior: populate field with `None` / Not Available — never skip the field entirely
- Downstream check evaluates to SKIPPED (no data) when field is None — this is honest
- Extraction success = non-null value extracted (any value, not a sanity-checked value)
- 80% success rate target applies per field across AAPL, RPM, TSLA
- Extraction method: LLM-assisted extraction (not regex) — proxy formats vary too much
- DEF 14A acquisition: Phase 47 is self-contained — include an explicit acquisition step to fetch DEF 14A filings for AAPL, RPM, TSLA if not cached

### Bucket-a routing fix approach
- Strategy: audit-first — use Phase 46's bucket classification as the starting task list
- Re-audit required: re-run the Phase 46 gap search tool on the current codebase before beginning routing work; fresh classification supersedes Phase 46's output
- Routing entries live in brain YAML files — each check's YAML gets a `field_for_check` entry, then `brain build` regenerates
- Never add routing entries to `config/` files — brain YAMLs are the canonical check knowledge store

### Regression safety bar
- Zero tolerance: any new TRIGGERED finding on AAPL compared to baseline = phase failure
- Baseline snapshot: run analysis on AAPL, RPM, TSLA before any Phase 47 changes; record TRIGGERED counts per company
- End-of-phase comparison: post-change counts must not exceed baseline on AAPL
- A new routing entry that causes a check to trigger on AAPL means the mapping is wrong or the threshold needs adjustment — must be fixed before the phase closes
- RPM and TSLA may legitimately gain new triggers from newly-routed data (routing gap fixed → data flows → check evaluates correctly)

### Claude's Discretion
- Exact LLM prompt design for DEF 14A extraction
- How to handle split proxy filings (DEF 14A + DEF 14A/A)
- Order of operations within plans (bucket-a first vs interleaved with bucket-b)
- Exact format of footnote reference marks in HTML (numbers, symbols, etc.)

</decisions>

<specifics>
## Specific Ideas

- The re-audit of checks should re-run the same gap search tool built in Phase 46 — not a new analysis from scratch
- Regression baseline should be captured as a QA artifact (e.g., a JSON snapshot of trigger counts) so the comparison is unambiguous, not eyeballed
- DEF 14A fields to extract: board gender diversity %, board racial diversity %, individual director tenure (years), director expertise/skills matrix, board meeting attendance %

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 47-check-data-mapping-completeness*
*Context gathered: 2026-02-25*
