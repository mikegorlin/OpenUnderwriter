---
phase: 118-revenue-model-company-intelligence-dossier
verified: 2026-03-20T15:30:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
human_verification:
  - test: "Run `underwrite AAPL --fresh` and open the HTML output"
    expected: "Section 5 'Company & Business -- Intelligence Dossier' renders with all 8 active subsections populated with company-specific data: business description, revenue flow pre-block, revenue model card table with D&O Risk column, segment breakdown with concentration assessment, unit economics table, revenue waterfall, emerging risk radar, and ASC 606 table"
    why_human: "LLM extraction quality and real-data population cannot be verified programmatically; only a live pipeline run against an actual ticker confirms the extraction prompts produce substantive output rather than empty defaults"
  - test: "In the rendered dossier, open the Revenue Model Card table"
    expected: "Every row has a non-generic D&O Risk column entry containing specific numbers, scoring factor references (e.g., 'F.5'), or company-specific litigation theories -- not boilerplate text"
    why_human: "D&O commentary quality depends on enrichment logic receiving real scoring data; only visual inspection of live output can confirm QUAL-04 compliance"
  - test: "Open the 'How Money Flows' subsection"
    expected: "Pre-formatted monospace revenue flow diagram renders correctly (not raw text) and shows company-specific flow nodes/edges"
    why_human: "Visual rendering of the <pre> block and content quality require human review"
---

# Phase 118: Revenue Model Company Intelligence Dossier Verification Report

**Phase Goal:** The worksheet contains a Company Intelligence Dossier section that tells an underwriter exactly how this company makes money, where concentration risk lives, and what the emerging threats are -- all with D&O risk implications
**Verified:** 2026-03-20T15:30:00Z
**Status:** PASSED
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | DossierData model exists with all 8 sub-models on AnalysisState | VERIFIED | `src/do_uw/models/dossier.py` (215 lines); 8 classes confirmed; `AnalysisState.dossier` field wired via `default_factory=DossierData` |
| 2 | LLM extraction populates DossierData from 10-K (4 focused schemas) | VERIFIED | `src/do_uw/stages/extract/llm/schemas/dossier.py` (197 lines, 4 extraction classes); `src/do_uw/stages/extract/dossier_extraction.py` (641 lines, 4 sub-extractors with QUAL-03 context) |
| 3 | BENCHMARK enrichment generates D&O risk commentary for every dossier table row | VERIFIED | `src/do_uw/stages/benchmark/dossier_enrichment.py` (444 lines) + helpers (178 lines); 7 sub-functions cover all sections including `_enrich_waterfall` and `_enrich_core_do_exposure` |
| 4 | 8 context builders produce template-ready dicts from DossierData (pure formatters) | VERIFIED | 8 `dossier_*.py` files in `src/do_uw/stages/render/context_builders/`; each has `extract_` function returning `_available` flag; zero evaluative conditionals on `tier`/`score`/`HIGH` confirmed |
| 5 | 9 Jinja2 templates render dossier section with D&O Risk columns in every data table | VERIFIED | `dossier.html.j2` (wrapper) + 8 subsection templates; D&O Risk column confirmed in `revenue_model_card.html.j2`, `unit_economics.html.j2`, `asc_606.html.j2`; monospace `<pre>` in `money_flows.html.j2`; no `| truncate` found |
| 6 | Pipeline wired end-to-end: EXTRACT step calls extraction, BENCHMARK calls enrichment, RENDER assembles 8 context keys | VERIFIED | `stages/extract/__init__.py` lines 368-377 call `extract_dossier`; `stages/benchmark/__init__.py` lines 282 + 518-529 call `enrich_dossier`; `html_context_assembly.py` lines 449-534 wire all 8 context keys |
| 7 | output_manifest.yaml has `intelligence_dossier` section with 9 groups (8 active + 1 deferred) | VERIFIED | Manifest confirmed: `intelligence_dossier` with 9 group IDs; `dossier_competitive_landscape` has `render_as: deferred` and placeholder template |
| 8 | 141 dossier-specific tests pass (models, extraction, enrichment, context builders, templates, integration) | VERIFIED | `uv run pytest tests/models/test_dossier.py tests/stages/extract/test_dossier_extraction.py tests/stages/benchmark/test_dossier_enrichment.py tests/stages/render/test_dossier_context_builders.py tests/stages/render/test_dossier_templates.py tests/stages/render/test_dossier_integration.py` → 141 passed in 1.97s |
| 9 | DOSSIER-07 (Competitive Landscape) explicitly deferred to Phase 119 per ROADMAP, not silently missing | VERIFIED | `output_manifest.yaml` has `dossier_competitive_landscape` with `render_as: deferred`; `REQUIREMENTS.md` maps DOSSIER-07 to Phase 119 (Pending); deferred template placeholder exists |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Min Lines | Actual Lines | Status | Key Contents |
|----------|-----------|--------------|--------|--------------|
| `src/do_uw/models/dossier.py` | 120 | 215 | VERIFIED | DossierData + 7 sub-models, all with ConfigDict(frozen=False) |
| `tests/models/test_dossier.py` | 80 | 19 tests | VERIFIED | Instantiation, serialization, parametrized dimensions |
| `src/do_uw/stages/extract/llm/schemas/dossier.py` | 80 | 197 | VERIFIED | RevenueModelExtraction, ASC606Extraction, EmergingRiskExtraction, UnitEconomicsExtraction |
| `src/do_uw/stages/extract/dossier_extraction.py` | 150 | 641 | VERIFIED | extract_dossier + 4 sub-extractors, QUAL-03 analytical context, revenue_segments consumption |
| `tests/stages/extract/test_dossier_extraction.py` | 100 | 17 tests | VERIFIED | Schema validation + orchestration/integration tests |
| `src/do_uw/stages/benchmark/dossier_enrichment.py` | 150 | 444 | VERIFIED | enrich_dossier + 7 sub-functions, waterfall_narrative, core_do_exposure |
| `src/do_uw/stages/benchmark/dossier_enrichment_helpers.py` | -- | 178 | VERIFIED | Card enrichment helpers, text extraction utilities |
| `tests/stages/benchmark/test_dossier_enrichment.py` | 100 | 15 tests | VERIFIED | TDD covering all enrichment functions + edge cases |
| `src/do_uw/stages/render/context_builders/dossier_what_company_does.py` | -- | exists | VERIFIED | extract_what_company_does → dict with what_company_does_available |
| `src/do_uw/stages/render/context_builders/dossier_money_flows.py` | -- | exists | VERIFIED | extract_money_flows |
| `src/do_uw/stages/render/context_builders/dossier_revenue_card.py` | -- | exists | VERIFIED | extract_revenue_model_card |
| `src/do_uw/stages/render/context_builders/dossier_segments.py` | -- | exists | VERIFIED | extract_revenue_segments |
| `src/do_uw/stages/render/context_builders/dossier_unit_economics.py` | -- | exists | VERIFIED | extract_unit_economics |
| `src/do_uw/stages/render/context_builders/dossier_waterfall.py` | -- | exists | VERIFIED | extract_revenue_waterfall |
| `src/do_uw/stages/render/context_builders/dossier_emerging_risks.py` | -- | exists | VERIFIED | extract_emerging_risks |
| `src/do_uw/stages/render/context_builders/dossier_asc606.py` | -- | exists | VERIFIED | extract_asc_606 |
| `tests/stages/render/test_dossier_context_builders.py` | 120 | 33 test cases | VERIFIED | Output shape, CSS class mapping, availability flags |
| `src/do_uw/templates/html/sections/dossier.html.j2` | -- | exists | VERIFIED | 8 {% include %} directives confirmed |
| `src/do_uw/templates/html/sections/dossier/what_company_does.html.j2` | -- | exists | VERIFIED | D&O callout block |
| `src/do_uw/templates/html/sections/dossier/money_flows.html.j2` | -- | exists | VERIFIED | `<pre class="revenue-flow ...">` confirmed |
| `src/do_uw/templates/html/sections/dossier/revenue_model_card.html.j2` | -- | exists | VERIFIED | `D&O Risk` column header + `{{ row.do_risk }}` |
| `src/do_uw/templates/html/sections/dossier/revenue_segments.html.j2` | -- | exists | VERIFIED | Segment table + concentration assessment |
| `src/do_uw/templates/html/sections/dossier/unit_economics.html.j2` | -- | exists | VERIFIED | `D&O Risk` column confirmed |
| `src/do_uw/templates/html/sections/dossier/revenue_waterfall.html.j2` | -- | exists | VERIFIED | Growth decomposition table |
| `src/do_uw/templates/html/sections/dossier/emerging_risk_radar.html.j2` | -- | exists | VERIFIED | `probability_class` + `D&O Factor` column |
| `src/do_uw/templates/html/sections/dossier/asc_606.html.j2` | -- | exists | VERIFIED | `D&O Risk` column + billings narrative |
| `tests/stages/render/test_dossier_templates.py` | 100 | 19 tests | VERIFIED | All 9 templates + available=False handling |
| `src/do_uw/brain/output_manifest.yaml` | -- | 9 groups | VERIFIED | `intelligence_dossier` section with 8 active + 1 deferred group |
| `tests/stages/render/test_dossier_integration.py` | 80 | 38 tests | VERIFIED | End-to-end context assembly + manifest structure |
| `src/do_uw/templates/html/deferred/dossier_competitive_landscape.html.j2` | -- | exists | VERIFIED | Placeholder for DOSSIER-07 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/do_uw/models/state.py` | `src/do_uw/models/dossier.py` | `from do_uw.models.dossier import DossierData` + `dossier: DossierData = Field(default_factory=DossierData)` | WIRED | Lines 22 + 367-372 |
| `src/do_uw/stages/extract/__init__.py` | `src/do_uw/stages/extract/dossier_extraction.py` | `from do_uw.stages.extract.dossier_extraction import extract_dossier` at lines 368-377 | WIRED | Phase 14 step, try/except wrapped |
| `src/do_uw/stages/benchmark/__init__.py` | `src/do_uw/stages/benchmark/dossier_enrichment.py` | `_enrich_dossier()` method calls `enrich_dossier(state)` at lines 518-529; called at line 282 | WIRED | Step 10, after forward-looking intelligence |
| `src/do_uw/stages/render/html_context_assembly.py` | `dossier_*.py` context builders | 8 try/except blocks at lines 449-534, all 8 context keys populated | WIRED | `dossier_what`, `dossier_flows`, `dossier_card`, `dossier_segments`, `dossier_unit`, `dossier_waterfall`, `dossier_risks`, `dossier_asc` |
| `src/do_uw/templates/html/sections/dossier.html.j2` | 8 subsection templates | `{% include "sections/dossier/..." %}` × 8 | WIRED | All 8 includes confirmed |
| `src/do_uw/stages/extract/dossier_extraction.py` | `src/do_uw/models/dossier.py` | Populates `state.dossier` fields from LLM output | WIRED | DossierData imported; `state.company.revenue_segments` consumed at lines 399-400 |
| `src/do_uw/stages/benchmark/dossier_enrichment.py` | `src/do_uw/models/dossier.py` | Reads/mutates `state.dossier` fields in-place | WIRED | `state.dossier.waterfall_narrative`, `state.dossier.core_do_exposure` etc. |

### Requirements Coverage

| Requirement | Phase 118 Plans | Description | Status | Evidence |
|-------------|-----------------|-------------|--------|----------|
| DOSSIER-01 | 01, 02, 03, 04, 05, 06 | "What the Company Does" + core D&O exposure paragraph | SATISFIED | `what_company_does.html.j2`, `_enrich_core_do_exposure`, `dossier_what_company_does.py` |
| DOSSIER-02 | 01, 02, 03, 04, 05, 06 | "How Money Flows" revenue flow diagram | SATISFIED | `money_flows.html.j2` with `<pre class="revenue-flow">`, `extract_money_flows`, revenue_flow nodes/edges in extraction schemas |
| DOSSIER-03 | 01, 02, 03, 04, 05, 06 | "Revenue Model Card" table with D&O Risk column | SATISFIED | `revenue_model_card.html.j2` with `D&O Risk` header + `{{ row.do_risk }}`; `_enrich_revenue_card` generates risk levels |
| DOSSIER-04 | 01, 02, 03, 04, 05, 06 | "Revenue Segment Breakdown" with D&O Exposure + concentration assessment | SATISFIED | `revenue_segments.html.j2` with segment table + concentration dimensions; `_enrich_concentration_dimensions` with 5 risk dimensions |
| DOSSIER-05 | 01, 02, 03, 04, 05, 06 | "Unit Economics" table with single most important metric narrative | SATISFIED | `unit_economics.html.j2`; `_enrich_unit_economics` generates narrative identifying most important metric (NDR priority for SaaS) |
| DOSSIER-06 | 01, 02, 03, 04, 05, 06 | "Revenue Waterfall (Growth Decomposition)" with D&O insight narrative | SATISFIED | `revenue_waterfall.html.j2`; `_enrich_waterfall` analyzes expansion/new-logo/price composition |
| DOSSIER-07 | 06 only (deferred) | "Competitive Landscape & Moat Assessment" | DEFERRED TO PHASE 119 | Manifest has `dossier_competitive_landscape` with `render_as: deferred`; placeholder template exists; REQUIREMENTS.md maps to Phase 119 |
| DOSSIER-08 | 01, 02, 03, 04, 05, 06 | "Emerging Risk Radar" table | SATISFIED | `emerging_risk_radar.html.j2` with probability CSS classes + D&O Factor column; `_enrich_emerging_risks` maps to F.1-F.10 |
| DOSSIER-09 | 01, 02, 03, 04, 05, 06 | "Revenue Recognition (ASC 606)" table | SATISFIED | `asc_606.html.j2` with complexity CSS classes; `_enrich_asc_606` uses SCA settlement statistics |

**Note on DOSSIER-07:** This requirement was explicitly scoped to Phase 119 in both ROADMAP.md and the phase RESEARCH.md before any work began. Plan 06 claims it in its `requirements` array but documents the deferral clearly. The manifest has a proper `render_as: deferred` placeholder. This is a documented, intentional deferral, not a missed requirement.

### Anti-Patterns Found

No anti-patterns found in Phase 118 artifacts:
- No `TODO`/`FIXME`/`PLACEHOLDER` comments in any dossier file
- No `| truncate` in any dossier template
- No `return null` or empty stub implementations
- No evaluative conditionals (`if tier`, `if score`, `if HIGH`) in context builders (pure formatter pattern maintained)

### Pre-Existing Test Failures (Not Phase 118 Regressions)

The following test failures existed before Phase 118 and are unrelated to dossier work:

| Test | Pre-existing Since | Reason |
|------|--------------------|--------|
| `test_brain_contract.py::test_threshold_provenance_categorized` | Before Phase 117 (brain YAML schema) | `ohlson_o_score` uses `'academic'` not `'academic_research'` -- schema validation mismatch |
| `test_contract_enforcement.py::test_real_manifest_template_agreement` | Before Phase 117 | Orphaned templates (`factor_detail.html.j2`, etc.) not in manifest |
| `test_html_signals.py::test_grouped_entry_has_required_keys` | Noted in 118-06 SUMMARY as pre-existing | `do_context` key present but not in `required_keys` set |
| `test_builder_line_limits.py[financials_evaluative.py]` | Phase 113 (file is 347 lines, limit 300) | Pre-dates Phase 118; `financials_evaluative.py` not touched in Phase 118 |
| `test_inference_evaluator.py::TestSingleValueFallback` (2 tests) | Before Phase 118 | Unrelated to dossier |

All 141 Phase 118-specific dossier tests pass. 2,410 non-brain-contract tests pass.

### Human Verification Required

#### 1. Full Pipeline Dossier Content Quality

**Test:** Run `underwrite AAPL --fresh` (or any active ticker) and open the HTML worksheet. Navigate to Section 5 "Company & Business -- Intelligence Dossier."
**Expected:** All 8 active subsections are populated with company-specific content:
- "What the Company Does" shows AAPL's business description and a D&O exposure paragraph with specific risk vectors
- "How Money Flows" shows a readable pre-formatted diagram of Apple's revenue flows
- "Revenue Model Card" has rows with non-boilerplate D&O Risk text referencing scoring factors and dollar amounts
- "Revenue Segment Breakdown" shows Mac/iPhone/iPad/Services/Wearables with D&O Exposure per segment
- "Unit Economics" shows App Store metrics with benchmark comparisons
- "Revenue Waterfall" shows YoY growth decomposition
- "Emerging Risk Radar" shows 3-5 risks with probability/impact/timeframe/D&O factor
- "ASC 606" shows revenue recognition elements with complexity levels
**Why human:** LLM extraction quality and real-data population of `state.dossier` fields can only be confirmed with a live pipeline run against actual 10-K filing text.

#### 2. D&O Risk Commentary Quality (QUAL-04 Compliance)

**Test:** In the rendered worksheet, examine the D&O Risk column in the Revenue Model Card and the Emerging Risk Radar D&O Factor column.
**Expected:** Each D&O Risk entry contains company-specific language: actual dollar amounts, scoring factor references (e.g., "F.5 = 6/8"), litigation theory references, or specific filing citations. No entry should be generic boilerplate applicable to any company.
**Why human:** QUAL-04 (every sentence must contain company-specific data) compliance requires qualitative review of enrichment output with real scoring context.

#### 3. Revenue Flow Diagram Readability

**Test:** View the "How Money Flows" subsection in the rendered HTML.
**Expected:** The pre-formatted diagram renders as a readable, monospace text diagram showing the company's revenue flow topology (sources, processes, outputs) -- not raw JSON or escaped HTML.
**Why human:** Visual rendering quality and content intelligibility require human review.

### Gaps Summary

No gaps. All 8 in-scope requirements (DOSSIER-01 through -06, -08, -09) are fully implemented across the 6 plans. DOSSIER-07 was explicitly deferred to Phase 119 per ROADMAP.md before any work began -- this is a planned deferral, not a gap.

The pipeline is end-to-end wired: EXTRACT (Phase 14) calls `extract_dossier`, BENCHMARK (Step 10) calls `enrich_dossier`, RENDER assembles all 8 context keys into the `html_context_assembly`, and the `dossier.html.j2` section wrapper includes all 8 subsection templates. The manifest registers `intelligence_dossier` as a required section with 9 groups.

---

_Verified: 2026-03-20T15:30:00Z_
_Verifier: Claude (gsd-verifier)_
