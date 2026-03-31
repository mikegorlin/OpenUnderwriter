---
status: testing
phase: 56-facet-driven-rendering
source: 56-01-SUMMARY.md, commits 642edd3..fd0ef1f, uncommitted scoring work
started: 2026-03-01T22:00:00Z
updated: 2026-03-01T22:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 2
name: Financial section renders identically via facet fragments
expected: |
  Open output/SNA-2026-02-27/SNA_worksheet.html. The Financial Health section looks identical to before — annual comparison table, key metrics, quarterly updates, distress indicators, tax risk, earnings quality, audit profile, peer group, financial checks, density alerts all present and properly formatted.
awaiting: user response

## Tests

### 1. Section YAML declarations cover all 8 rendered sections
expected: 12 section YAML files exist in brain/sections/ covering all rendered worksheet sections. Each YAML declares facets with template paths pointing to fragment files.
result: skipped
reason: Infrastructure test — user prefers to verify via rendered output

### 2. Financial section renders identically via facet fragments
expected: Open a real ticker HTML output (e.g. RPM or SNA). The Financial Health section looks identical to before — annual comparison table, key metrics, quarterly updates, distress indicators, tax risk, earnings quality, audit profile, peer group, financial checks, density alerts all present and properly formatted.
result: [pending]

### 3. Governance section renders identically via facet fragments
expected: Governance section in HTML output shows board composition, board forensics, ownership structure, people risk, structural governance, transparency/disclosure, activist risk, governance checks, and density alerts — all present and matching prior layout.
result: [pending]

### 4. Market Activity section renders identically via facet fragments
expected: Market Activity section shows stock performance, capital markets, stock drops, earnings guidance, insider trading, short interest, analyst consensus, stock/ownership charts, market checks, density alerts — all present.
result: [pending]

### 5. Litigation section renders identically via facet fragments
expected: Litigation section shows active matters, settlement history, contingent liabilities, derivative suits, defense strength, SEC enforcement, whistleblower, workforce/product/env, industry patterns, SOL analysis, litigation checks, density alerts — all present.
result: [pending]

### 6. Executive Summary section renders identically via facet fragments
expected: Executive Summary shows company profile, key findings, risk classification, claim probability, tower recommendation, data quality notice, density alerts — all present.
result: [pending]

### 7. AI Risk section renders identically via facet fragments
expected: AI Risk section shows overall score, dimension breakdown, competitive position, forward assessment, density alerts — all present.
result: [pending]

### 8. Scoring section renders identically via facet fragments
expected: Scoring section shows ten-factor scoring, risk classification, tier classification, peril assessment, peril map, hazard profile, severity scenarios, claim probability, tower recommendation, pattern detection, forensic composites, temporal signals, allegation mapping, executive risk profile, NLP analysis, calibration notes, scoring checks, density alerts — all present and properly formatted.
result: [pending]

### 9. Schema renamed correctly (FacetSpec → SectionSpec, SubsectionSpec → FacetSpec)
expected: Code uses SectionSpec for section-level groupings and FacetSpec for atomic display units. brain_section_schema.py is the canonical module. No references to old "SubsectionSpec" remain in active code.
result: [pending]

### 10. Legacy facet YAML files removed (brain/facets/ directory)
expected: The old brain/facets/ directory is cleaned up — facet YAML files have been moved to brain/sections/. No duplicate definitions remain.
result: [pending]

### 11. Section renderer dispatches facets from YAML declarations
expected: section_renderer.py reads section YAML, builds facet list, and dispatches to fragment templates. Adding/removing/reordering facets in YAML changes what renders without code changes.
result: [pending]

### 12. All render tests pass (zero regressions)
expected: Full render test suite passes with zero failures. The 52 section/schema tests pass. No pre-existing test failures introduced.
result: [pending]

## Summary

total: 12
passed: 0
issues: 0
pending: 12
skipped: 0

## Gaps

[none yet]
