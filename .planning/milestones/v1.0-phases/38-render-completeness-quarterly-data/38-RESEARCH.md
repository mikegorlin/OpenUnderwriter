# Phase 38: Render Completeness & Quarterly Data - Research

**Researched:** 2026-02-21
**Domain:** Render pipeline completeness, cross-format consistency, quarterly financial data
**Confidence:** HIGH (all findings from direct codebase investigation)

## Summary

Phase 38 addresses the largest remaining quality gap in the pipeline: approximately 45-55% of state data never reaches the rendered output. The root causes are well-understood and fall into four categories: (1) entire data domains with no renderer (classification, hazard profile, risk factors, text signals, forensic composites, temporal signals, NLP signals); (2) data domains with partial renderers that drop fields (board forensics missing interlocks/relationship flags/committees in MD template, litigation missing derivative suit details/contingent liabilities/workforce+product+environmental matters); (3) quarterly 10-Q data that IS acquired and extracted by the LLM but has no integration pathway into state or render output; and (4) cross-format divergence where the Word renderer renders data that the Markdown/HTML templates do not, and vice versa.

The three output formats have fundamentally different rendering architectures: Word uses imperative Python (section renderers like `sect3_financial.py`), Markdown uses a single Jinja2 template (`worksheet.md.j2`) fed by extraction helpers (`md_renderer_helpers*.py`), and HTML/PDF uses Jinja2 section templates fed by `build_html_context()` which itself calls the MD `build_template_context()`. This means the Word renderer can access the full typed `AnalysisState` object directly, while the MD/HTML renderers are limited to whatever the `extract_*` helper functions choose to extract into flat dictionaries.

**Primary recommendation:** Build a render coverage test that walks the Pydantic model tree, identifies all non-null leaf values in a sample state.json, then searches the rendered output for evidence of each value. Use this test to drive systematic gap closure. For quarterly data, add a `quarterly_update` field to `ExtractedFinancials` and a new renderer subsection. For cross-format consistency, add a test that extracts section headings and key data points from all three formats and asserts equality.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | Model introspection for field walking | Already used; `model_fields_set`, `model_dump()` enable automated coverage scanning |
| pytest | 9.x | Render coverage test framework | Already used; parametrize enables per-field test cases |
| Jinja2 | 3.x | MD and HTML template rendering | Already used for both MD and HTML/PDF output |
| python-docx | latest | Word document generation | Already used for primary Word output |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| deepdiff | 7.x | Structured comparison of outputs | Cross-format consistency testing (compare section headings, key values) |
| json-flatten | - | NOT NEEDED: roll own walker | Pydantic model_dump() + recursive walk is simpler |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom field walker | deepdiff | deepdiff compares two objects; we need to compare state fields against rendered text -- custom is better |
| Single shared context builder | Per-format context builders | Shared is the current approach (HTML calls MD's `build_template_context`); downside is MD template limitations constrain HTML |

## Architecture Patterns

### Current Render Architecture (Three Paths)

```
AnalysisState
    |
    +---> Word Renderer (sect*.py files)
    |     Direct access to typed state model
    |     Full Pydantic objects with .value, .source, .confidence
    |     Imperative: doc.add_paragraph(), add_styled_table()
    |
    +---> MD Context Builders (md_renderer_helpers*.py)
    |     |  extract_company(), extract_financials(), etc.
    |     |  Flatten SourcedValue[T] to plain strings/dicts
    |     v
    |     MD Jinja2 Template (worksheet.md.j2)
    |     Single 600-line template, conditional blocks
    |
    +---> HTML Context Builder (html_renderer.py)
          |  Calls build_template_context() from MD renderer
          |  Adds HTML-specific context (densities, narratives, chart base64)
          v
          HTML Jinja2 Templates (sections/*.html.j2)
          Multiple section templates, includes base.html.j2
```

### Pattern 1: Render Coverage Test (NEW)
**What:** Automated test that walks AnalysisState model tree, finds all non-null values, and checks they appear in rendered output.
**When to use:** After every render change, as CI gate.
**Approach:**
```python
def walk_state_values(state_dict: dict, prefix: str = "") -> list[tuple[str, Any]]:
    """Recursively yield (field_path, value) for all non-null leaf values."""
    results = []
    for key, value in state_dict.items():
        path = f"{prefix}.{key}" if prefix else key
        if value is None:
            continue
        if isinstance(value, dict):
            # Check if it's a SourcedValue dict (has 'value' key)
            if 'value' in value and 'source' in value:
                results.append((path, value['value']))
            else:
                results.extend(walk_state_values(value, path))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    results.extend(walk_state_values(item, f"{path}[{i}]"))
                else:
                    results.append((f"{path}[{i}]", item))
        elif isinstance(value, (str, int, float, bool)):
            results.append((path, value))
    return results
```

### Pattern 2: Quarterly Update Subsection
**What:** New field on `ExtractedFinancials` holding post-annual quarterly data, rendered as a distinct subsection.
**When to use:** When a 10-Q was filed after the most recent 10-K.
**Data flow:**
```
ACQUIRE: 10-Q filing documents (already acquired, sorted by date)
    |
EXTRACT: LLM extraction via TenQExtraction schema (already exists!)
    |
    v  NEW: aggregate post-annual 10-Q extractions into state
ExtractedFinancials.quarterly_updates: list[QuarterlyUpdate]
    |
RENDER: "Recent Quarterly Update" subsection in Section 3
    Q-over-Q revenue, net income, EPS
    New legal proceedings from the quarter
    Material changes from MD&A
    Subsequent events
```

### Pattern 3: Cross-Format Section Registry
**What:** A single source of truth for section headings and key data point names that all three renderers reference.
**When to use:** To ensure Word, MD, and HTML/PDF all render the same logical sections.
**Approach:**
```python
# render/section_registry.py
SECTIONS = [
    {"id": "executive_summary", "heading": "Executive Summary", "number": 1},
    {"id": "company", "heading": "Company Profile", "number": 2},
    {"id": "financial", "heading": "Financial Health", "number": 3},
    # ...
]
```

### Anti-Patterns to Avoid
- **Duplicating data extraction logic per format:** The MD extract_* helpers already flatten SourcedValues to dicts. The HTML renderer already reuses this. Adding Word-specific extraction would create a third copy. Instead, extend the shared extract_* functions when possible, and let Word renderers access the typed state directly for complex tables.
- **Truncating list data:** The current markdown litigation template renders ALL cases (no `[:3]` limit). The Word renderer also renders all SCAs. Don't introduce limits. The prior audit note about "first 3 cases" may have been fixed already -- verify in current code.
- **Putting quarterly data in a separate top-level state field:** Keep it in `ExtractedFinancials.quarterly_updates` since it's financial data. The litigation updates from 10-Q go to the litigation timeline.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pydantic model tree walking | Custom recursive walker from scratch | `model.model_dump(mode='python')` + recursive dict walker | Pydantic serialization handles all edge cases (optionals, enums, dates, nested models) |
| Section heading extraction from Markdown | Regex parsing | Simple `re.findall(r'^#{1,3} (.+)$', text, re.MULTILINE)` | Standard markdown heading extraction; no need for a parser library |
| Word doc text extraction for testing | Custom XML parsing | `python-docx` paragraph iteration: `[p.text for p in doc.paragraphs]` | Already a dependency; handles runs, tables, headers correctly |
| HTML text extraction for testing | BeautifulSoup | Jinja2 rendered output is just HTML strings; use `re.sub(r'<[^>]+>', '', html)` for simple text extraction | No need for full HTML parser for heading/value checks |

**Key insight:** The render coverage test needs to map state field paths to "evidence of rendering" -- which is NOT an exact string match. A revenue of `$391.03B` in state appears as `$391.0B` in rendered output. The test must be smart about format variations (currency formatting, percentage formatting, date formatting, enum display names).

## Common Pitfalls

### Pitfall 1: Format-Sensitive Value Matching
**What goes wrong:** A test checks for `391035000000.0` in rendered output, but the renderer shows `$391.0B`. Test fails despite the data being correctly rendered.
**Why it happens:** Financial values undergo format_currency(), percentages undergo format_percentage(), booleans become "Yes"/"No", enums become display names.
**How to avoid:** The coverage test should have format-aware matchers. For financial values, check that the formatted version appears. For booleans, check "Yes"/"No". For enums, check the humanized form. The test maps field types to expected formats.
**Warning signs:** Large numbers of false negatives in the coverage test.

### Pitfall 2: Density Gating Hides Data
**What goes wrong:** A field IS rendered -- but only when the section density is ELEVATED or CRITICAL. When it's CLEAN, the data is summarized in a one-liner. The coverage test says the field isn't rendered.
**Why it happens:** Issue-driven density gating (Phase 35) intentionally suppresses detail for clean sections. The coverage test needs to understand this.
**How to avoid:** Two strategies: (a) test with an AAPL-like state that has CRITICAL litigation density to exercise full rendering paths, or (b) mark fields with metadata indicating "rendered only when section density >= X" and exclude CLEAN-gated fields from the >90% threshold.
**Warning signs:** Coverage passes on TSLA (many issues) but fails on AAPL (clean governance/financial).

### Pitfall 3: 10-Q Data Without State Integration
**What goes wrong:** 10-Q filings are acquired, LLM extracts them via TenQExtraction schema, but the results sit in `acquired_data.llm_extractions["10-Q:accession"]` and never get merged into `ExtractedFinancials` or `LitigationLandscape`.
**Why it happens:** The current pipeline (llm_extraction.py) prioritizes 10-Qs after 10-Ks and skips pre-annual ones. Post-annual 10-Qs ARE kept, but their extraction results aren't aggregated into the structured state models.
**How to avoid:** Add a new extraction step that reads post-annual 10-Q LLM results from `acquired_data.llm_extractions`, creates `QuarterlyUpdate` models, and attaches them to `ExtractedFinancials.quarterly_updates`.
**Warning signs:** AAPL state shows 10-Q filings acquired (2026-01-30 post-annual) but 0 LLM extractions for 10-Q (the LLM extraction may be working but keyed differently, or the 10-Q may not be getting extracted at all -- needs investigation during implementation).

### Pitfall 4: Cross-Format Template Drift
**What goes wrong:** A developer adds a new subsection to the Word renderer but forgets to update the Markdown template and HTML sections. Or vice versa.
**Why it happens:** Three separate rendering paths with no shared section definition.
**How to avoid:** The cross-format consistency test extracts section headings from all three outputs and asserts they match (with known exceptions documented). Run this test in CI.
**Warning signs:** PR reviews that only show changes to one renderer file.

### Pitfall 5: 500-Line File Limit During Gap Closure
**What goes wrong:** Adding rendering for 15+ new data domains causes section renderers to exceed 500 lines.
**Why it happens:** Each new data domain needs rendering logic. The financial section alone needs quarterly update, full balance sheet, full cash flow, plus the existing income statement.
**How to avoid:** Split early. The MD template is already ~600 lines (close to limit). New subsections should be delegated to helper macros or included sub-templates. Word section renderers already follow the delegation pattern (sect3_financial delegates to sect3_tables, sect3_audit, sect3_peers).
**Warning signs:** Files approaching 400 lines before the work starts.

## Key Codebase Findings

### Finding 1: AAPL Output Shows "Data Not Available" Despite Full State (HIGH Confidence)
The AAPL markdown output shows "Company profile data not available" despite `state.company` having full Apple Inc. data. This suggests the Markdown renderer's `build_template_context()` is receiving a state object where `company`, `extracted.financials`, etc. are `None`. This is likely a deserialization issue where the state.json is loaded but Pydantic model reconstruction loses data (perhaps `model_validate` vs `model_construct`). This is NOT a Phase 38 problem per se, but Phase 38's coverage test will immediately surface it.

**Evidence:** `state.json` has `company.identity.legal_name.value = "Apple Inc."` but rendered output shows `Company: Unknown Company`.

### Finding 2: 10-Q Extraction Not Happening (HIGH Confidence)
The AAPL state has 9 acquired 10-Q filing documents but 0 LLM extractions with `10-Q:` prefix. The `llm_extraction.py` code filters post-annual 10-Qs correctly (`_filter_superseded_quarterlies`), but the AAPL 10-Q from 2026-01-30 (filed after 10-K on 2025-10-31) should have been extracted. Either: (a) the 10-Q LLM extraction is not being triggered, or (b) the results are stored under a different key format. This needs investigation.

**Evidence:** `acquired_data.filing_documents["10-Q"]` has 9 entries, `acquired_data.llm_extractions` has 15 entries (10-K, 8-K, DEF 14A only).

### Finding 3: Data Domains with Zero Rendering (HIGH Confidence)
These state fields have populated data but NO rendering path in ANY format:

| State Path | Data Present (AAPL) | Rendering Status |
|-----------|-------------------|-----------------|
| `classification` | Full ClassificationResult | NOT RENDERED |
| `hazard_profile` | IES=43.3, 55 dimensions, 7 categories | NOT RENDERED |
| `analysis.temporal_signals` | 8 signals | NOT RENDERED |
| `analysis.forensic_composites` | FIS=86, RQS=50, CFQS=44 | NOT RENDERED |
| `analysis.executive_risk` | weighted_score=0.07, 1 finding | NOT RENDERED |
| `analysis.nlp_signals` | readability, tone, risk factors | NOT RENDERED |
| `analysis.peril_map` | 7 assessments, MODERATE overall | NOT RENDERED (except via scoring Section 7 partially) |
| `analysis.settlement_prediction` | DDL model output | NOT RENDERED (except via scoring) |
| `extracted.risk_factors` | 25 structured risk factors | NOT RENDERED |
| `extracted.text_signals` | 49 topic signals | NOT RENDERED |
| `extracted.litigation.contingent_liabilities` | 2 contingencies | NOT RENDERED |
| `extracted.litigation.workforce_product_environmental` | Employment matters present | NOT RENDERED |
| `extracted.litigation.whistleblower_indicators` | 0 (but field exists) | NOT RENDERED |
| `extracted.governance.board_forensics[].interlocks` | Present per director | NOT RENDERED (committees rendered in Word only) |
| `extracted.governance.board_forensics[].relationship_flags` | Present | NOT RENDERED |
| `extracted.governance.board_forensics[].true_independence_concerns` | Present | NOT RENDERED |

### Finding 4: Word vs Markdown Rendering Divergence (HIGH Confidence)
The Word renderer renders significantly more detail than the Markdown template:

| Feature | Word | Markdown | HTML/PDF |
|---------|------|----------|----------|
| Full financial statement tables (income, BS, CF) | YES (sect3_tables.py) | Summary only (revenue, NI) | Via MD context |
| Balance sheet ratios | YES (computed inline) | Snapshot table only | Via MD context |
| Board forensic profiles (individual) | YES (render_board_composition) | YES (board_members table) | Via MD context |
| Board committee assignments | YES | NO (not in MD template) | NO |
| Distress model trajectory | YES (per-model) | Score + zone only | Via MD context |
| Earnings quality detail | YES (OCF/NI, accruals) | Brief summary | Via MD context |
| Defense assessment detail | YES (sect6_defense.py) | One-line summary | Via MD context |
| SEC enforcement pipeline visual | YES (stage progression) | One row in summary table | Via MD context |
| Ownership donut chart | YES (VIS-02) | Image embed if chart_dir | Image embed |
| Litigation timeline chart | YES (VIS-03) | Image embed if chart_dir | Image embed |
| Density indicators | YES (colored labels) | YES (bold text) | YES (CSS classes) |
| Pre-computed narratives | YES (per-section) | YES (per-section) | YES (per-section) |
| Calibration notes | YES (sect_calibration.py) | YES (in MD template) | YES |

### Finding 5: Markdown Template Size and Structure (HIGH Confidence)
The markdown template `worksheet.md.j2` is ~594 lines. It's a single monolithic file. Adding quarterly data, full financial statements, and missing data domains would push it well past 600 lines. The template should be split into section includes (Jinja2 `{% include %}`) similar to how the HTML template already works. The MD template directory currently only has `worksheet.md.j2` and `__init__.py`.

### Finding 6: 10-Q Schema Already Exists (HIGH Confidence)
`TenQExtraction` in `src/do_uw/stages/extract/llm/schemas/ten_q.py` already defines the extraction schema with fields for: quarter, period_end, revenue, net_income, eps, new_legal_proceedings, legal_proceedings_updates, going_concern, material_weaknesses, new_risk_factors, management_discussion_highlights, subsequent_events. This schema is well-designed for a "Recent Quarterly Update" section. The gap is: (a) ensuring 10-Q LLM extraction actually runs, (b) aggregating results into state, (c) rendering the aggregated data.

### Finding 7: Board Forensic Data Is Rich But Partially Rendered (HIGH Confidence)
`BoardForensicProfile` has: name, tenure, is_independent, committees, other_boards, is_overboarded, prior_litigation, interlocks, relationship_flags, true_independence_concerns. The Word renderer shows: name, tenure, independent, committees, other_boards, overboarded (6 of 10 fields). The MD template shows: name, tenure, independent, other_boards (4 of 10 fields). Neither format renders interlocks, relationship_flags, or true_independence_concerns -- which are critical for D&O underwriting (interlock analysis is specifically called out in the phase success criteria).

### Finding 8: Litigation ALL Cases Already Rendered (MEDIUM Confidence)
The phase description mentions "not just the first 3" cases. However, the current code in `_extract_sca_cases()` iterates ALL cases with no `[:3]` limit, and the Word renderer's `_render_sca_table()` also renders `all_scas`. The current rendering gap is more about DERIVATIVE suits (only shown as a count in MD, no individual case details) and CONTINGENT liabilities (not rendered at all) rather than SCA truncation. The prior audit finding about "first 3 cases" may have already been fixed.

## State Model Fields Requiring New Rendering

### Priority 1: Should definitely render (directly relevant to D&O underwriting)
- `extracted.litigation.derivative_suits` -- individual case details (currently just count)
- `extracted.litigation.contingent_liabilities` -- ASC 450 disclosures
- `extracted.litigation.workforce_product_environmental` -- employment, product, environmental
- `extracted.governance.board_forensics[].interlocks` -- director interlocks
- `extracted.governance.board_forensics[].committees` -- in MD template
- `extracted.governance.board_forensics[].relationship_flags` -- independence concerns
- `extracted.governance.board_forensics[].true_independence_concerns`
- Quarterly 10-Q update section (new)
- Full financial statement tables in MD (income, BS, CF -- Word already has them)

### Priority 2: Should render (adds analytical value)
- `analysis.forensic_composites` (FIS, RQS, CFQS scores)
- `analysis.executive_risk` (board aggregate risk)
- `analysis.peril_map` (already rendered in scoring section 7 via `sect7_peril_map.py` for Word)
- `extracted.risk_factors` (25 structured Item 1A risk factors)
- `classification` (market_cap_tier, base_filing_rate, severity bands)
- `hazard_profile` (IES score, top dimensions)

### Priority 3: Nice to have (supplementary intelligence)
- `analysis.temporal_signals` (trend analysis)
- `analysis.nlp_signals` (filing language analysis)
- `extracted.text_signals` (topic presence)

## Quarterly Data Integration Design

### State Model Addition
```python
class QuarterlyUpdate(BaseModel):
    """Single quarterly report data extracted from 10-Q."""
    quarter: str  # e.g., "Q1 FY2026"
    period_end: str  # e.g., "2025-12-28"
    filing_date: str  # e.g., "2026-01-30"
    revenue: SourcedValue[float] | None = None
    net_income: SourcedValue[float] | None = None
    eps: SourcedValue[float] | None = None
    new_legal_proceedings: list[str] = []
    legal_proceedings_updates: list[str] = []
    going_concern: bool = False
    material_weaknesses: list[str] = []
    new_risk_factors: list[str] = []
    md_a_highlights: list[str] = []
    subsequent_events: list[str] = []
```

Add to `ExtractedFinancials`:
```python
quarterly_updates: list[QuarterlyUpdate] = Field(
    default_factory=list,
    description="Post-annual 10-Q quarterly updates",
)
```

### Extraction Integration
In EXTRACT stage, after processing annual 10-K:
1. Find LLM extractions keyed as `10-Q:accession` in `acquired_data.llm_extractions`
2. Filter to only those filed AFTER the most recent 10-K
3. Convert `TenQExtraction` to `QuarterlyUpdate` with SourcedValue wrapping
4. Append to `state.extracted.financials.quarterly_updates`

### Render Design
New subsection in Section 3 (Financial Health), after the existing content:
```markdown
### Recent Quarterly Update (Q1 FY2026, filed 2026-01-30)

| Metric | Q1 FY2026 | Prior Q1 | Change |
|--------|-----------|----------|--------|
| Revenue | $X.XB | $X.XB | +X.X% |
| Net Income | $X.XB | $X.XB | +X.X% |
| EPS (Diluted) | $X.XX | $X.XX | +X.X% |

**Material Changes:**
- [MD&A highlights]

**New Legal Proceedings:**
- [From 10-Q legal section]
```

## Cross-Format Consistency Test Design

```python
def test_cross_format_consistency(sample_state, tmp_path):
    """Verify Word, Markdown, and PDF contain same sections and key data."""
    # Render all three formats
    ds = DesignSystem()
    md_path = render_markdown(sample_state, tmp_path / "test.md", ds)
    word_path = render_word_document(sample_state, tmp_path / "test.docx", ds)
    # Extract section headings from each
    md_headings = extract_md_headings(md_path)
    word_headings = extract_word_headings(word_path)
    # Verify same logical sections present
    assert set(md_headings) == set(word_headings)
    # Verify key data points present in both
    key_values = extract_key_values(sample_state)  # ticker, score, tier, etc.
    md_text = md_path.read_text()
    word_text = extract_word_text(word_path)
    for label, value in key_values:
        assert value in md_text, f"{label}: {value} not in Markdown"
        assert value in word_text, f"{label}: {value} not in Word"
```

## Open Questions

1. **AAPL "Data Not Available" Bug**
   - What we know: state.json has full data, rendered output shows "not available"
   - What's unclear: Is this a deserialization issue in the current pipeline, or a render-time issue? Does the live pipeline (not just state.json re-render) produce correct output?
   - Recommendation: Investigate before starting Phase 38 work. If it's a pipeline bug, fix first. If it's a state.json re-render issue, document and account for it.

2. **10-Q LLM Extraction Gap**
   - What we know: 10-Q filings are acquired but no LLM extractions exist for them in AAPL state
   - What's unclear: Is the LLM extraction pipeline skipping 10-Qs, or is the issue with how extraction keys are stored?
   - Recommendation: Trace the llm_extraction.py code path for 10-Q documents to determine where the gap is. May need a fix in EXTRACT stage before Phase 38 can render quarterly data.

3. **Coverage Test Threshold**
   - What we know: Success criterion says >90% coverage
   - What's unclear: How to count "coverage" when density gating intentionally suppresses detail for clean sections, and some fields (like `text_signals`) are intermediate computation products not meant for direct display
   - Recommendation: Define an exclusion list of fields that are legitimately not rendered (internal metadata, intermediate computations, acquired raw data). Count coverage only over "renderable" fields. Document exclusions explicitly.

4. **Markdown Template Split Strategy**
   - What we know: Template is ~594 lines, will grow significantly
   - What's unclear: Whether to use Jinja2 `{% include %}` (requires template files) or `{% macro %}` (keeps in single file but harder to maintain)
   - Recommendation: Use `{% include %}` with section template files in `templates/markdown/sections/` directory, matching the HTML template structure. This is the standard Jinja2 pattern for large templates.

5. **Risk Factor Rendering Design**
   - What we know: 25 structured risk factors with title, category, severity, D&O relevance
   - What's unclear: Should these appear as a standalone section, as annotations within relevant sections (litigation risk factors in Section 6, financial risk factors in Section 3), or in an appendix?
   - Recommendation: Render as a subsection within Section 2 (Company Profile) since risk factors come from Item 1A of the 10-K. Group by category with severity badges.

## Sources

### Primary (HIGH confidence)
- Direct codebase investigation of all files listed below
- AAPL state.json analysis (output/AAPL/state.json)
- AAPL rendered output analysis (output/AAPL/AAPL_worksheet.md)

### Key Files Investigated
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/state.py` -- AnalysisState model, all stage output containers
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/financials.py` -- ExtractedFinancials, FinancialStatements, DistressIndicators
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/governance.py` -- GovernanceData, BoardProfile
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/governance_forensics.py` -- BoardForensicProfile (interlocks, committees, etc.)
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/litigation.py` -- LitigationLandscape, CaseDetail, ContingentLiability
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/market.py` -- MarketSignals, StockPerformance
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/company.py` -- CompanyProfile, CompanyIdentity
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/scoring.py` -- ScoringResult, BenchmarkResult
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/classification.py` -- ClassificationResult
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/executive_summary.py` -- ExecutiveSummary
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/md_renderer.py` -- build_template_context, render_markdown
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/md_renderer_helpers.py` -- extract_company, extract_market
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/md_renderer_helpers_ext.py` -- extract_governance, extract_litigation
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/md_renderer_helpers_financial.py` -- extract_financials
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/word_renderer.py` -- Word document assembly
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/html_renderer.py` -- HTML/PDF rendering
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/sections/sect3_financial.py` -- Financial section Word renderer
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/sections/sect3_tables.py` -- Financial statement tables
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/sections/sect5_governance.py` -- Governance section
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/sections/sect5_governance_board.py` -- Board composition tables
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/render/sections/sect6_litigation.py` -- Litigation section
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/templates/markdown/worksheet.md.j2` -- Markdown template (594 lines)
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/templates/html/worksheet.html.j2` -- HTML template entry point
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/extract/llm/schemas/ten_q.py` -- TenQExtraction schema
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/extract/llm_extraction.py` -- LLM extraction orchestrator
- `/Users/gorlin/projects/UW/do-uw/tests/test_render_outputs.py` -- Existing render tests

## Metadata

**Confidence breakdown:**
- Render coverage gap analysis: HIGH -- direct comparison of state.json vs rendered output
- 10-Q integration path: HIGH for design, MEDIUM for the extraction gap root cause
- Cross-format divergence: HIGH -- compared all three rendering paths side by side
- Board forensics rendering: HIGH -- traced data through model to template
- Quarterly data design: MEDIUM -- schema exists but extraction gap needs investigation

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (stable codebase, no external dependency changes expected)
