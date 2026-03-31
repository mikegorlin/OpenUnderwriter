# Phase 120: Integration + Visual Verification - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate the complete v8.0 Intelligence Dossier end-to-end on real tickers, verify all existing analytical capabilities are preserved, update visual regression baselines, and add CI gates for do_context coverage. This is a verification phase — no new features.

</domain>

<decisions>
## Implementation Decisions

### Test Ticker Selection
- **HNGE** — Gold standard reference (existing PDF baseline)
- **AAPL** — Clean ticker (mega-cap, excellent data coverage, known good)
- **ANGI** — Complex ticker (WALK-tier, litigation, governance issues, tests "bad company" path)
- All 3 pipeline runs happen **automated within phase execution** (not manual)
- Use `underwrite TICKER --fresh` for all runs to exercise full acquisition/extraction

### Gold Standard Comparison Scope
- The verification bar is **content correctness and completeness**, not pixel-perfect visual matching
- **Information must be correct** — no wrong data, no hallucinated findings
- **Information must be adequate and relevant** — exhaustively informative but concisely presented for underwriter value
- **Sections scale to the company** — same skeleton structure, but section density varies (ANGI has 5 litigations → fat litigation section; AAPL has none → slim section saying "no known SCAs")
- New v8.0 sections (Intelligence Dossier, Forward-Looking Risk, Alt Data, Stock Catalysts) get **full visual review** — verify populated with real company-specific data, correct structure, and underwriter value
- Existing sections get **both automated structural checks AND visual review**

### CI Gate Design
- **Two-layer approach**: pytest assertion for pass/fail gate + standalone script for detailed investigation
- **do_context coverage target: 100%** — every evaluative column must trace to a brain signal do_context block
- Pytest test counts coverage % and fails below 100%
- Standalone script reports detailed breakdown (which columns are covered, which are missing, which signals they trace to)

### Preservation Verification
- **Both automated and visual** for existing analytics
- Automated pytest tests check each existing section has expected HTML elements, data tables, chart containers
- Visual review catches content/quality issues automated tests miss
- **All existing sections equally important** — no prioritization. Every section gets same scrutiny:
  - Executive Brief, Risk Scorecard, 10-Factor Scoring
  - Financial tables (BS, IS, CF), ratios, Beneish/Altman
  - Governance profiles, board forensics, executive compensation
  - Litigation timeline, SCA details, enforcement actions
  - Stock analysis, peer benchmarking, market events
- Performance budget: HTML render <10s, full pipeline <25min

### Claude's Discretion
- Order of pipeline runs (HNGE first as baseline, then AAPL, then ANGI — or parallel)
- Exact HTML structural assertions (which elements, which selectors)
- How to report visual review findings (markdown report, annotated screenshots, or inline)
- Standalone do_context coverage script implementation details

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Gold Standard
- `Feedme/HNGE - D&O Analysis - 2026-03-18.pdf` — Gold standard reference PDF for section-by-section comparison

### Existing Test Infrastructure
- `tests/test_visual_regression.py` — Existing visual regression framework with Playwright screenshots and 10% diff threshold
- `tests/test_performance_budget.py` — Existing performance budget tests (HTML <10s, PDF <30s, pipeline <25min)
- `scripts/qa_compare.py` — Existing cross-ticker QA comparison script

### Brain Architecture
- `src/do_uw/brain/output_manifest.yaml` — Manifest governing all rendered sections (source of truth for section inventory)
- `brain/signals/*.yaml` — Signal definitions with do_context blocks (source of truth for D&O commentary)

### Pipeline Entry Point
- `src/do_uw/cli.py` — CLI entry point (`underwrite TICKER --fresh`)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/test_visual_regression.py` — Playwright screenshot framework, can be extended for new sections
- `tests/test_performance_budget.py` — Performance timing framework, already has HTML/PDF/pipeline budgets
- `scripts/qa_compare.py` — Cross-ticker comparison, validates feature parity across tickers

### Established Patterns
- Visual regression uses golden baselines with configurable diff threshold (10%)
- Performance tests use `PERFORMANCE_TESTS=1` env var gate
- Pipeline runs via `underwrite TICKER --fresh` CLI command

### Integration Points
- `src/do_uw/brain/output_manifest.yaml` — All sections listed here must render
- `src/do_uw/stages/render/html_context_assembly.py` — Where all context builders are wired
- `src/do_uw/stages/render/html_renderer.py` — Final HTML output

</code_context>

<specifics>
## Specific Ideas

- The underwriter's experience is the ultimate test: "Does this tell the right story for this company?"
- ANGI should look markedly different from AAPL — if they look similar, something is wrong (ANGI has governance issues, litigation, low score)
- Section density should vary naturally — don't pad thin sections, don't truncate fat ones

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 120-integration-visual-verification*
*Context gathered: 2026-03-20*
