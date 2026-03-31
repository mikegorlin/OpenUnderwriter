# Phase 23: End-to-End Output Quality - Research

**Researched:** 2026-02-11
**Domain:** Output validation, defect root-cause tracing, cross-pipeline quality assurance
**Confidence:** HIGH (based on direct codebase analysis and actual output inspection)

## Summary

Phase 23 addresses systemic quality failures that span the entire pipeline -- from resolve-stage sector misclassification through extraction-stage employee count errors to render-stage formatting bugs. Research was conducted by directly inspecting the generated output files (XOM, SMCI, NFLX .docx and state.json), tracing defects back to their root cause in the codebase, and evaluating what infrastructure exists for automated output validation.

The findings are severe. The blind spot detection system is **completely non-functional** -- search_fn is no-op for all programmatic pipeline runs because SERPER_API_KEY is not set in the environment, resulting in ZERO web search results for critical D&O signals. SMCI's worksheet says "no active class actions" and "no SEC enforcement" when in reality there are multiple SCAs, a DOJ investigation, EY auditor resignation, and Hindenburg short seller report. XOM's employee count is 62 (should be ~62,000 -- LLM returned thousands without multiplier). NFLX is classified as "Industrials" because SIC 78xx maps to range (74,79) which is labeled "Management, engineering services" in `sec_identity.py`. Shares outstanding are displayed with `$` prefix across all tickers. These are not rendering bugs -- they are data integrity failures at acquisition, extraction, and resolve stages.

**Primary recommendation:** Build a process validation harness using python-docx to read generated .docx files and assert facts against ground truth. Fix defects at their root cause stage. Wire a real web search provider (Serper.dev or Brave Search API) into the pipeline for blind spot detection.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-docx | 1.1+ | Read generated .docx for validation | Already a dependency; supports full text + table extraction |
| pytest | 8.x | Test framework for validation harness | Already in project |
| json (stdlib) | n/a | state.json comparison | Already used everywhere |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| docx2python | 2.x | Alternative .docx reader | Only if python-docx table extraction proves insufficient |
| deepdiff | 7.x | Deep dict comparison with tolerance | For comparing state.json against ground truth with relative tolerance |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-docx for reading | docx2python | docx2python produces nested lists, harder to navigate; python-docx preserves style info |
| Manual .docx inspection | Markdown output comparison | Markdown is easier to parse but doesn't catch formatting issues |
| Per-field ground truth | Full-document snapshot | Snapshots are brittle; per-field is maintainable |

**Installation:**
```bash
# python-docx already installed. deepdiff is optional:
uv add --dev deepdiff
```

## Architecture Patterns

### Recommended Test Structure
```
tests/
├── ground_truth/           # Existing: per-ticker truth files
│   ├── helpers.py          # Existing: state loading, assertions
│   ├── xom.py             # Existing: XOM facts
│   ├── smci.py            # Existing: SMCI facts (NEEDS EXPANSION)
│   └── nflx.py            # NEW: NFLX facts
├── test_output_validation.py  # NEW: Process validation harness
│   ├── TestXOMOutput       # Validates XOM .docx against known facts
│   ├── TestSMCIOutput      # Validates SMCI .docx against known facts
│   └── TestNFLXOutput      # Validates NFLX .docx against known facts
├── test_render_sections_*.py  # Existing: unit tests for renderers
└── test_ground_truth_*.py     # Existing: state.json field validation
```

### Pattern 1: Output Validation Harness
**What:** Read the generated .docx, extract text and table content, assert against ground truth
**When to use:** After every pipeline run for test tickers
**Example:**
```python
from docx import Document  # type: ignore

def extract_table_value(doc, table_index: int, field_label: str) -> str | None:
    """Find a value in a docx table by its label column."""
    if table_index >= len(doc.tables):
        return None
    table = doc.tables[table_index]
    for row in table.rows:
        cells = [c.text.strip() for c in row.cells]
        if len(cells) >= 2 and field_label.lower() in cells[0].lower():
            return cells[1]
    return None

def extract_all_text(doc) -> str:
    """Extract all paragraph text for keyword assertions."""
    return "\n".join(p.text for p in doc.paragraphs)

class TestXOMOutput:
    def test_employee_count_reasonable(self):
        doc = Document("output/XOM/XOM_worksheet.docx")
        emp_text = extract_table_value(doc, 0, "Employees")
        # Should be ~62,000, not 62
        emp_num = int(emp_text.replace(",", "").split()[0])
        assert emp_num > 10000, f"XOM employees {emp_num} seems too low"

    def test_sector_not_industrials(self):
        text = extract_all_text(doc)
        assert "Industrials" not in text or "Energy" in text
```

### Pattern 2: Defect Root-Cause Tracing
**What:** For each output defect, trace backward through pipeline stages to find the root cause
**When to use:** For every bug found by the validation harness
**Example tracing chain:**
```
OUTPUT DEFECT: NFLX sector shows "Industrials"
  ↓ RENDER: sect1_executive.py uses state.company.identity.sector.value
  ↓ SCORE: scoring uses sector for base rate lookup
  ↓ ANALYZE: sector drives check thresholds
  ↓ EXTRACT: no sector logic in extract
  ↓ ACQUIRE: no sector logic in acquire
  ↓ RESOLVE: sec_identity.py sic_to_sector() maps SIC 78 to INDU
  → ROOT CAUSE: _SIC_SECTOR_MAP range (74, 79) = "INDU" is too broad
  → FIX: Add (78, 78): "COMM" for Motion Picture / Entertainment services
```

### Pattern 3: Ground Truth Expansion for Output Validation
**What:** Expand ground truth files beyond state.json field comparisons to include expected output facts
**When to use:** For each test ticker
**Example:**
```python
# tests/ground_truth/xom.py -- expanded for output validation
GROUND_TRUTH = {
    # ... existing state.json validation fields ...
    "output_facts": {
        "employee_count_min": 50000,
        "employee_count_max": 80000,
        "sector_display": "Energy",
        "sector_not": ["Industrials", "Technology"],
        "auditor_name_contains": "PricewaterhouseCoopers",
        "has_active_sca": False,
        "tier_expected_range": ["WANT", "WRITE", "WIN"],
    },
}
```

### Anti-Patterns to Avoid
- **Band-aid in renderer:** Don't fix employee count display in sect2_company.py. Fix it in the LLM extraction prompt or converter.
- **Output snapshot testing:** Don't compare entire .docx byte-for-byte. It's fragile and uninformative on failure.
- **Skipping state.json validation:** The output harness should validate BOTH state.json facts AND .docx presentation.
- **Fixing one ticker, breaking another:** Always run all 3 test tickers (XOM, SMCI, NFLX) after any fix.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| .docx text extraction | Custom XML parser | python-docx Document.paragraphs + .tables | Edge cases with merged cells, nested tables, tracked changes |
| Web search in pipeline | MCP tool calls from Python | Serper.dev API via existing serper_client.py | MCP tools not accessible inside pipeline code; Serper is HTTP API |
| State comparison with tolerance | Manual field-by-field checks | Existing ground_truth/helpers.py assert_financial_close | Already handles relative tolerance, accuracy tracking |
| Sector code mapping | Complex NLP classification | Expand _SIC_SECTOR_MAP with finer granularity | SIC->sector is a lookup table, not a classification problem |

**Key insight:** Most defects in this phase are NOT rendering bugs. They are data bugs in resolve/acquire/extract that happen to manifest in the output. The validation harness catches them; the fix goes upstream.

## Common Pitfalls

### Pitfall 1: Fixing Symptoms Instead of Root Causes
**What goes wrong:** Developer sees "$4.1B" for shares outstanding, adds a special case in the formatter to strip `$` when the label contains "shares"
**Why it happens:** The formatter is the last place touched; it's natural to fix there
**How to avoid:** For every defect, trace the full pipeline path. The formatter should receive correct data; it should not need to interpret field semantics.
**Warning signs:** If you're adding `if "shares" in label` logic to formatters, you're fixing in the wrong place.

### Pitfall 2: LLM Extraction Returns Ambiguous Numbers
**What goes wrong:** LLM returns `62` for employee count (meaning 62,000 from a document that says "approximately 62 thousand employees")
**Why it happens:** The schema says `int` with no unit instruction. The LLM sometimes returns raw text numbers, sometimes converts.
**How to avoid:** Add explicit unit instructions to LLM extraction prompts: "For employee_count, return the total number of individual employees (e.g., 62000, not 62 thousand). If the filing says 'thousands', multiply to get the actual count."
**Warning signs:** Small numbers for large companies in any extracted field.

### Pitfall 3: Blind Spot Detection Appears to Work But Returns Nothing
**What goes wrong:** Pipeline runs without errors, blind_spot_results has the correct structure (pre_structured, post_structured), but all arrays are empty
**Why it happens:** search_fn defaults to no-op when SERPER_API_KEY is not set. The orchestrator logs a warning but continues.
**How to avoid:** Either (a) require SERPER_API_KEY or warn prominently in output, or (b) fall back to an alternative search API (Brave Search), or (c) flag in the worksheet that blind spot detection was not performed.
**Warning signs:** `search_budget_used` is 10 (the base allocation for 5 categories x 2 phases) but all result arrays are empty.

### Pitfall 4: Stock Split Distortion in YoY Calculations
**What goes wrong:** NFLX shows EPS going from $20.28 to $2.58 (-87.3%). This looks like a catastrophic earnings decline but is actually a 10:1 stock split.
**Why it happens:** XBRL data for prior periods is not adjusted for subsequent splits. The system computes raw YoY change.
**How to avoid:** Either (a) use split-adjusted data from yfinance for EPS/shares comparisons, or (b) detect splits via 8-K Item 5.03/yfinance split history and annotate YoY changes, or (c) suppress YoY change display when a split is detected.
**Warning signs:** >50% change in shares outstanding with inverse change in EPS.

### Pitfall 5: Sector Mismatch Between Industry and Scoring Sector
**What goes wrong:** NFLX Table 0 shows "Industry: Entertainment" (from yfinance) but Table 2 shows "Sector: Industrials" (from SIC mapping). Both are displayed, creating an internal contradiction.
**Why it happens:** Two different data sources (yfinance vs. SEC SIC code) are used for industry classification, and they disagree because the SIC mapping table has insufficient granularity.
**How to avoid:** Fix the SIC mapping table to handle entertainment/media SIC codes (78xx, 79xx), or use yfinance industry as a cross-validation to override incorrect SIC mappings.
**Warning signs:** SIC description says something completely different from the sector label.

## Code Examples

### Reading .docx for Validation
```python
# Source: Direct testing against generated output files
from docx import Document  # type: ignore[import-untyped]
from typing import Any

def read_docx_tables(path: str) -> list[list[list[str]]]:
    """Read all tables from a .docx file as nested string lists."""
    doc: Any = Document(path)
    tables: list[list[list[str]]] = []
    for table in doc.tables:
        rows: list[list[str]] = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(cells)
        tables.append(rows)
    return tables

def read_docx_text(path: str) -> str:
    """Read all paragraph text from a .docx file."""
    doc: Any = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def find_in_tables(
    tables: list[list[list[str]]],
    label: str,
) -> list[tuple[int, int, list[str]]]:
    """Find all rows in any table where the first cell matches label."""
    results = []
    for ti, table in enumerate(tables):
        for ri, row in enumerate(table):
            if row and label.lower() in row[0].lower():
                results.append((ti, ri, row))
    return results
```

### SIC-to-Sector Fix Pattern
```python
# In sec_identity.py, the mapping needs finer granularity for SIC 70-89
_SIC_SECTOR_MAP: dict[tuple[int, int], str] = {
    # ... existing entries ...
    # Services: needs per-2-digit breakdown, not ranges
    (70, 72): "CONS",   # Hotels, personal services
    (73, 73): "TECH",   # Computer/data services -> Tech
    (74, 76): "INDU",   # Management, engineering, R&D services
    (78, 79): "COMM",   # Motion picture, amusement/recreation -> Communication Services
    (80, 80): "HLTH",   # Health services -> Healthcare
    (81, 86): "INDU",   # Legal, educational, social services
    (87, 87): "TECH",   # Engineering/R&D/management services -> Tech
    (88, 89): "INDU",   # Misc services
}
# Also need "COMM" sector added to sectors.json config with appropriate base rate
```

### Employee Count Prompt Fix Pattern
```python
# In llm/schemas/ten_k.py, clarify the unit:
employee_count: int | None = Field(
    default=None,
    description=(
        "Total number of individual employees (headcount). "
        "If the filing says 'approximately 62 thousand' or '62,000', "
        "return 62000. Always return the full integer count, "
        "not abbreviated thousands."
    ),
)
```

### Blind Spot Detection Status in Output
```python
# In the executive summary or a dedicated quality section:
def _render_data_quality_notice(doc, state, ds):
    """Flag when blind spot detection was not performed."""
    blind_spots = state.acquired_data.blind_spot_results
    pre = blind_spots.get("pre_structured", {})
    total_results = sum(len(v) for v in pre.values() if isinstance(v, list))
    if total_results == 0:
        para = doc.add_paragraph(style="DOBody")
        run = para.add_run(
            "NOTE: Web-based blind spot detection was not performed "
            "(no search API configured). This worksheet relies solely "
            "on SEC filing data and may miss publicly known events such "
            "as short seller reports, state AG actions, or news coverage."
        )
        # Style as warning
```

## Detailed Defect Inventory

Research identified the following defects across the three test tickers, organized by root cause stage:

### RESOLVE Stage Defects

| Defect | Ticker | Root Cause | Fix Location |
|--------|--------|-----------|--------------|
| NFLX classified as "Industrials" | NFLX | SIC 78xx maps to INDU via range (74,79) | `sec_identity.py` _SIC_SECTOR_MAP |
| DIS classified as "Industrials" | DIS | SIC 7990 maps to INDU via range (74,79) | `sec_identity.py` _SIC_SECTOR_MAP |
| Missing COMM sector | All | No Communication Services sector code exists | `sec_identity.py` + `sectors.json` |

### ACQUIRE Stage Defects

| Defect | Ticker | Root Cause | Fix Location |
|--------|--------|-----------|--------------|
| Blind spot detection returns 0 results | ALL | SERPER_API_KEY not set; search_fn is no-op | `cli.py` / `serper_client.py` / environment config |
| SMCI: No Hindenburg report found | SMCI | No web search executed | Blind spot search dependency |
| SMCI: No EY resignation news | SMCI | No web search executed | Blind spot search dependency |
| SMCI: No DOJ investigation found | SMCI | No web search executed | Blind spot search dependency |
| No Nasdaq delisting warning found | SMCI | No web search executed | Blind spot search dependency |
| web_news always empty | ALL | News client search also no-op | Same search_fn dependency |

### EXTRACT Stage Defects

| Defect | Ticker | Root Cause | Fix Location |
|--------|--------|-----------|--------------|
| Employee count 62 (should be ~62,000) | XOM | LLM returned truncated number | `llm/schemas/ten_k.py` prompt + `ten_k_converters.py` validation |
| SMCI auditor shows N/A | SMCI | LLM extraction did not capture auditor | `llm/schemas/ten_k.py` + auditor extraction logic |
| SMCI material weakness not detected | SMCI | LLM extraction missed MW | `llm/schemas/ten_k.py` prompt + `ten_k_converters.py` |
| SMCI active SCAs not captured | SMCI | SCAs come from SCAC/web, not 10-K | Need web search data flowing to litigation extractor |
| Revenue segments empty for XOM | XOM | Profile shows no segments | `company_profile.py` LLM converter or acquisition gap |

### SCORE Stage Defects

| Defect | Ticker | Root Cause | Fix Location |
|--------|--------|-----------|--------------|
| XOM tier WALK (should be WANT/WRITE) | XOM | Clean mega-cap energy scores poorly | Scoring calibration + missing positive signals |
| Inherent risk base rate unrealistic | XOM | 9.4% for mega-cap energy seems high | `benchmark/` inherent risk calculation |

### RENDER Stage Defects

| Defect | Ticker | Root Cause | Fix Location |
|--------|--------|-----------|--------------|
| Shares outstanding with $ prefix | ALL | `format_currency(compact=True)` used for non-currency values | `sect3_tables.py` or `sect3_financial.py` (incorrect formatter call) |
| EPS YoY change distorted by stock split | NFLX | Raw XBRL data not split-adjusted | YoY computation in `financial_statements.py` or `sect3_tables.py` |
| Piotroski trajectory shows "?:1.0 -> ?:0.0" | SMCI | Period labels missing | `sect3_financial.py` distress rendering |
| Raw enum values in output | Various | StrEnum .value used directly | Various section renderers need `.name` or humanization |
| Sector inconsistency: "Entertainment" vs "Industrials" in same doc | NFLX | Two data sources disagree | Cross-check needed in resolve or render |

## Critical Finding: Blind Spot Detection is Non-Functional

The single most important finding of this research is that **blind spot detection does not work in any pipeline run**. The architecture:

1. `cli.py` calls `create_serper_search_fn()` which checks `SERPER_API_KEY` env var
2. If not set, returns `(None, "SERPER_API_KEY not set -- web search disabled")`
3. `search_fn=None` is passed to `AcquisitionOrchestrator`
4. Orchestrator creates `WebSearchClient(search_fn=None)` which uses `_default_search_fn`
5. `_default_search_fn` logs a warning and returns `[]`
6. All 5 blind spot categories x 2 phases = 10 searches, all return empty

This means the CLAUDE.md NON-NEGOTIABLE requirement "Every analysis run MUST include proactive discovery searches at START of ACQUIRE" has **never been satisfied** in any batch validation run.

**Impact on SMCI specifically:**
- Hindenburg short seller report (Aug 2024): NOT FOUND
- EY auditor resignation (Oct 2024): NOT FOUND
- DOJ investigation: NOT FOUND
- Nasdaq delisting warning: NOT FOUND
- Multiple securities class actions: NOT FOUND
- The worksheet literally states the opposite of reality

**Options to fix:**
1. **Serper.dev API** (existing implementation): Set `SERPER_API_KEY` environment variable. Cost: $50/month for 10,000 searches. Already coded in `serper_client.py`.
2. **Brave Search API** (MCP server exists): Adapt to call Brave Search REST API directly from pipeline code (not via MCP). 2,000 free/month.
3. **Built-in WebSearch tool**: Cannot be used from pipeline Python code -- only available in Claude Code session context.
4. **SerpAPI**: Alternative Google SERP API. Paid.

**Recommendation:** Use Serper.dev (option 1). The code already exists. Just need the API key configured.

## Critical Finding: LLM Employee Count is Unreliable

The LLM extraction for XOM returned `employee_count: 62` when the 10-K says "approximately 62 thousand employees" (or similar phrasing). The schema field says only:
```python
employee_count: int | None = Field(
    default=None, description="Total number of employees"
)
```

This is ambiguous. The LLM may:
- Return 62 (thousands) thinking it's extracting the number from "62 thousand"
- Return 62000 correctly when the filing says "62,000"
- Return 62300 if the filing says "approximately 62,300"

**Fix approach:**
1. Update the field description to explicitly require full integer count
2. Add a post-extraction validation: if employee_count < 100 for a company with revenue > $10B, flag as likely truncated
3. Cross-validate against yfinance `info.get('fullTimeEmployees')` as a sanity check

## Critical Finding: Sector Classification Mapping Gaps

The `_SIC_SECTOR_MAP` in `sec_identity.py` uses coarse 2-digit SIC ranges that conflate very different industries:

| SIC Range | Current Mapping | Includes | Problem |
|-----------|----------------|----------|---------|
| (74, 79) | INDU | 78xx Motion Picture, 79xx Amusement & Recreation | Netflix, Disney classified as "Industrials" |
| (77, 77) | Missing | Missing from map entirely | Would fall through to DEFAULT |

**SIC codes that need dedicated mappings:**
- 78xx: Motion Picture Distribution/Services -> COMM (Communication Services)
- 79xx: Amusement & Recreation Services -> COMM or CONS
- 77xx: (no standard assignment; rare SIC codes)

Additionally, the project needs a "COMM" sector code added to `sectors.json` with appropriate base rates and thresholds. Currently only these sectors exist: TECH, HLTH, FINS, ENGY, INDU, CONS, REIT, UTIL, DEFAULT.

## Section Coherence Analysis

**Current state:** Sections are rendered independently with no cross-referencing mechanism. Each section renderer reads from state but does not produce signals that other sections consume. The executive summary synthesizes key findings from the scoring stage, but does not thread themes through the document.

**Specific coherence failures found:**
1. NFLX: Section 1 says "mega-cap industrials company" while Section 2 says "Entertainment industry"
2. SMCI: Section 1 says "no critical red flags" while an informed reader knows about Hindenburg/EY/DOJ
3. XOM: Section 1 assigns WALK tier while all financial indicators are strong (scoring issue, not coherence)

**What coherence means for this phase:**
- Litigation findings in Section 6 should be cited in severity estimates in Section 7
- Governance red flags in Section 5 should appear in the executive summary key negatives
- If blind spot detection found a short seller report, it should appear in both the litigation section AND the executive summary
- The tier recommendation should be consistent with the findings narrative

**Current architecture limitation:** The render stage runs AFTER all analysis is complete. Cross-section coherence is an analysis/scoring problem (connecting findings), not a rendering problem (displaying connected findings). The scoring stage already produces patterns and key findings that could serve as coherence threads, but the renderers don't fully utilize them.

## python-docx Reading Capabilities

**Confirmed working** (tested against actual generated output):
- `Document(path)` opens .docx files
- `doc.paragraphs` returns all paragraphs with `.text` and `.style.name`
- `doc.tables` returns all tables with row/cell iteration
- Cell text extraction via `cell.text.strip()` works correctly
- Style names (DOHeading1, DOHeading2, DOBody) are preserved and readable
- Table cell text includes all runs within the cell

**Limitations:**
- Merged cells: `cell.text` works but cell boundaries can be confusing with horizontal merges
- Images/charts: Cannot extract embedded chart data via python-docx
- Header/footer text: Requires separate access via `section.header`/`section.footer`
- No native search/regex on document: Must extract text first, then search

**Recommendation:** python-docx is fully sufficient for the output validation harness. Extract all paragraph text and table content, then run assertions against the extracted data.

## Existing Test Infrastructure Assessment

| Component | Exists? | Coverage | Gaps |
|-----------|---------|----------|------|
| Ground truth files (11 companies) | Yes | state.json field validation | No output document validation |
| helpers.py (state navigation) | Yes | Financial comparisons, accuracy tracking | No .docx reading, no table extraction |
| test_render_sections_*.py | Yes | Unit tests with mock state | Tests renderer functions, not output quality |
| test_render_outputs.py | Yes | Markdown and PDF smoke tests | No Word document content validation |
| validation_report.json | Yes | Pipeline pass/fail per ticker | Only tests "did it run", not "is it correct" |

**Key gap:** No test currently validates that the FINAL RENDERED DOCUMENT contains correct, complete, factual information. All existing tests either validate state.json fields or test individual renderer functions with mock data. The gap between "pipeline runs successfully" and "output is usable by an underwriter" is vast.

## Workstream Mapping

Based on research findings, the 7 success criteria map to these workstreams:

### 1. Process Validation Harness
- Read .docx with python-docx
- Assert per-ticker facts (employee count, sector, auditor, tier, litigation)
- Run against XOM, SMCI, NFLX
- Expand ground truth files with output_facts section

### 2. Cross-Cutting Data Bugs
- Shares outstanding `$` prefix (render: wrong formatter)
- Raw enum values (render: various sections)
- Employee count units (extract: LLM prompt)
- Board name concatenation (render: governance section)
- Severity table inconsistency (render: sect1 vs sect7)
- Stock split YoY distortion (extract/render: detection + annotation)
- Piotroski trajectory display (render: sect3_financial)
- Debug text in output (render: various)

### 3. Extraction Quality
- LLM prompt refinement for employee count
- Auditor extraction improvement
- Material weakness detection
- DEF 14A board name parsing
- Revenue segment extraction reliability

### 4. Blind Spot Detection
- Configure Serper.dev API key
- Verify search results populate blind_spot_results
- Ensure blind spot findings flow to litigation/governance extractors
- Add data quality notice when search is unavailable

### 5. Sector Classification
- Expand _SIC_SECTOR_MAP with finer granularity
- Add COMM sector to sectors.json
- Cross-validate with yfinance industry
- Test against known misclassifications (NFLX, DIS)

### 6. Section Coherence
- Executive summary references to downstream findings
- Consistent sector/industry across all sections
- Blind spot findings threaded to litigation + executive summary
- Tier recommendation narrative consistent with findings

### 7. Completeness Check
- Revenue segments populated when public data exists
- Geographic breakdown populated
- Auditor identity always populated
- Full C-suite identified
- Stock charts present (currently referenced but may be missing)
- No empty sections for available data

## Open Questions

Things that couldn't be fully resolved:

1. **Serper.dev API key provisioning**
   - What we know: Code exists in `serper_client.py`, needs `SERPER_API_KEY` env var
   - What's unclear: Whether the user has a Serper.dev account, budget for API calls
   - Recommendation: Phase plan should include setup of search API with fallback options

2. **Stock split detection scope**
   - What we know: NFLX 10:1 split (2022) distorts EPS and shares outstanding YoY comparisons
   - What's unclear: How many other tickers in the validation set had splits; whether yfinance provides reliable split history for all tickers
   - Recommendation: Use yfinance `splits` attribute and suppress YoY change for split periods

3. **XOM WALK tier root cause**
   - What we know: XOM scores 76/100 composite but tier mapping says WALK (score_range 11-30)
   - What's unclear: The tier mapping appears inverted (quality_score 76 should be WANT/WRITE, not WALK). Need to verify if composite_score is risk_points or quality_score.
   - Recommendation: Investigate scoring model and verify tier boundaries match the correct direction

4. **SMCI ground truth accuracy**
   - What we know: Ground truth says `has_active_sca: False` and `has_material_weakness: False`
   - What's unclear: These should be True based on public information. Ground truth file may reflect LLM extraction limitations rather than actual facts
   - Recommendation: Update ground truth to reflect reality, mark current extraction limitations as known failures

5. **Coherence architecture**
   - What we know: Sections render independently; no cross-section theme threading mechanism exists
   - What's unclear: Whether to build a theme threading system (adds complexity) or simply ensure the existing key findings system works correctly
   - Recommendation: Start with ensuring key findings correctly reference all downstream data, defer theme threading architecture to Phase 24

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: `sec_identity.py`, `web_search.py`, `serper_client.py`, `orchestrator.py`, `formatters.py`, `ten_k.py`, `prompts.py`, `pipeline.py`, `cli.py`
- Direct output inspection: `output/XOM/state.json`, `output/SMCI/state.json`, `output/NFLX/state.json`
- Direct .docx reading: `output/XOM/XOM_worksheet.docx`, `output/SMCI/SMCI_worksheet.docx`, `output/NFLX/NFLX_worksheet.docx`
- Existing ground truth: `tests/ground_truth/{xom,smci,nflx}.py`
- Existing test infrastructure: `tests/ground_truth/helpers.py`, `tests/test_render_outputs.py`

### Secondary (MEDIUM confidence)
- python-docx reading capabilities verified by direct testing
- WebSearch results for python-docx table extraction patterns

### Tertiary (LOW confidence)
- XOM WALK tier root cause (needs deeper scoring model investigation)
- Stock split detection completeness across validation set

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - python-docx already in project, tested reading works
- Architecture: HIGH - defect inventory based on direct output inspection, root causes traced to specific files/lines
- Pitfalls: HIGH - every pitfall documented was observed in actual output
- Defect inventory: HIGH - every defect was verified by reading actual .docx and state.json files
- Blind spot finding: HIGH - confirmed by reading actual state.json data (all arrays empty)

**Research date:** 2026-02-11
**Valid until:** 2026-03-11 (stable -- findings are about specific code issues, not evolving libraries)
