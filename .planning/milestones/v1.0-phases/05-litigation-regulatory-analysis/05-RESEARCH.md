# Phase 5: Litigation & Regulatory Analysis - Research

**Researched:** 2026-02-08
**Domain:** Securities litigation data extraction, SEC enforcement pipeline mapping, regulatory proceedings parsing, defense posture assessment
**Confidence:** MEDIUM (domain patterns well-understood; some data source access limitations discovered)

## Summary

Phase 5 builds the complete legal landscape for a company by extracting and structuring litigation and regulatory data from sources already acquired in Phase 2 (ACQUIRE stage) and parsing filing text already downloaded. This is EXTRACT stage work -- no new MCP tools, no new pipeline stages, no CLI changes.

The phase requires expanding the existing `LitigationLandscape` Pydantic model (currently a skeleton with 6 fields from Phase 1) into a rich model hierarchy mirroring the `GovernanceData`/`MarketSignals` pattern from Phase 4. It requires a new litigation sub-orchestrator (`extract_litigation.py`) following the established `extract_market.py`/`extract_governance.py` pattern, plus 8-10 individual extractors that parse filing text, web search results, and EFTS search data into structured models.

Key finding: Stanford SCAC has no public API and prohibits web scraping. The primary data sources for this phase are (1) 10-K Item 3 Legal Proceedings text parsing, (2) SEC EFTS full-text search results already captured by LitigationClient, (3) 8-K filing text, (4) DEF 14A charter/bylaw provisions, (5) web search results from blind spot discovery, and (6) config-driven classification lookup tables. This is a text-parsing-heavy phase, not an API-integration phase.

**Primary recommendation:** Follow the Phase 4 model/extractor/sub-orchestrator pattern exactly. Create a 4th sub-orchestrator `run_litigation_extractors()` that sits alongside the existing 3. Expand the litigation model into `litigation.py` + `litigation_details.py` (split for 500-line compliance). Create 8-10 extractors each under 500 lines, and new config files for lead counsel tiers and statute of limitations parameters.

## Standard Stack

### Core

No new external libraries needed. Phase 5 uses the same stack as prior phases:

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.x | Model definitions for litigation data | Already in use; SourcedValue pattern established |
| httpx | 0.x | HTTP client (for any EFTS/SEC calls) | Already in use via rate_limiter |
| re | stdlib | Regex-based filing text parsing | Standard for SEC text extraction per Phase 3/4 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime | stdlib | Statute of limitations date calculations | SOL window computation |
| enum (StrEnum) | stdlib | Case status, claim type, enforcement stage enums | Categorical field typing |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Regex text parsing | spaCy/NLP for legal text | Overkill; Phase 3/4 pattern is regex-based and works well |
| Config JSON for claim types | Hardcoded enums | CLAUDE.md says "no hardcoded thresholds" -- use config |
| Stanford SCAC API | Web scraping | SCAC prohibits scraping; no public API exists |

**Installation:** No new dependencies. `uv sync` is sufficient.

## Architecture Patterns

### Recommended Project Structure

```
src/do_uw/
  models/
    litigation.py           # Expand: LitigationLandscape (top-level), CaseDetail
    litigation_details.py   # NEW: RegulatoryProceeding, DefenseAssessment,
                            #       IndustryClaimPattern, SOLMap, ContingentLiability,
                            #       SECEnforcementPipeline (expanded), ForumProvisions
  stages/
    extract/
      extract_litigation.py # NEW: Sub-orchestrator (like extract_market.py)
      sca_extractor.py      # NEW: Securities class actions (SECT6-03)
      sec_enforcement.py    # NEW: SEC enforcement pipeline (SECT6-04)
      derivative_suits.py   # NEW: Derivative/fiduciary claims (SECT6-05)
      regulatory_extract.py # NEW: Regulatory proceedings (SECT6-06)
      deal_litigation.py    # NEW: M&A and deal litigation (SECT6-07)
      workforce_product.py  # NEW: Workforce/product/environmental (SECT6-08)
      defense_assessment.py # NEW: Defense strength (SECT6-09)
      industry_claims.py    # NEW: Industry claim patterns (SECT6-10)
      sol_mapper.py         # NEW: Statute of limitations map (SECT6-11)
      contingent_liab.py    # NEW: Known matters/contingent liabilities (SECT6-12)
  config/
    lead_counsel_tiers.json # NEW: Top-tier plaintiff law firms
    claim_types.json        # NEW: Claim type taxonomy + SOL parameters
    industry_theories.json  # NEW: Industry -> common claim theory mapping
```

### Pattern 1: Sub-Orchestrator Pattern (Established in Phase 4)

**What:** A module-level function that calls individual extractors in dependency order, wrapping each in try/except, collecting ExtractionReports.
**When to use:** Every SECT6 extractor is called via the litigation sub-orchestrator.
**Example:** (Based on existing `extract_market.py` pattern)

```python
# Source: existing extract_market.py / extract_governance.py pattern
def run_litigation_extractors(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> LitigationLandscape:
    """Run all SECT6 litigation extractors in dependency order."""
    landscape = LitigationLandscape()

    # 1. Securities class actions (SECT6-03) -- foundational
    landscape.securities_class_actions = _run_sca_extractor(state, reports)

    # 2. SEC enforcement pipeline (SECT6-04)
    landscape.sec_enforcement = _run_sec_enforcement(state, reports)

    # 3. Derivative suits (SECT6-05)
    landscape.derivative_suits = _run_derivative_suits(state, reports)

    # ... etc ...

    # N-1. Industry claim patterns (SECT6-10) -- needs peer data
    landscape.industry_patterns = _run_industry_claims(state, reports)

    # N. Litigation summary narrative (SECT6-01) -- must be last
    landscape.litigation_summary = _generate_litigation_summary(landscape)

    return landscape
```

### Pattern 2: Extractor Function Signature (Established in Phase 3/4)

**What:** Every extractor returns a tuple of (model, ExtractionReport).
**When to use:** Every new SECT6 extractor.
**Example:**

```python
# Source: established pattern from audit_risk.py, stock_performance.py, etc.
def extract_securities_class_actions(
    state: AnalysisState,
) -> tuple[list[CaseDetail], ExtractionReport]:
    """Extract SCA data from 10-K Item 3, EFTS results, and web search."""
    cases: list[CaseDetail] = []
    found: list[str] = []
    # ... extraction logic ...
    report = create_report(
        extractor_name="securities_class_actions",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source,
    )
    return cases, report
```

### Pattern 3: Filing Text Section Parsing (Extend filing_sections.py)

**What:** Add Item 3 (Legal Proceedings) to SECTION_DEFS in filing_sections.py.
**When to use:** Item 3 is the primary source for litigation disclosures.
**Example:**

```python
# Add to SECTION_DEFS in filing_sections.py
(
    "item3",
    [
        r"(?i)\bitem\s+3[\.\s:]+legal\s+proceedings\b",
        r"(?i)\bitem\s+3\b(?!\s*[0-9a-z])",
    ],
    [
        r"(?i)\bitem\s+4\b",
        r"(?i)\bitem\s+3a\b",
    ],
),
```

### Pattern 4: Config-Driven Classification

**What:** Claim types, lead counsel tiers, and industry theory mappings stored in JSON config files.
**When to use:** Any classification logic that should be tunable without code changes.
**Example:**

```json
// lead_counsel_tiers.json
{
  "tier_1": [
    "Bernstein Litowitz Berger & Grossmann",
    "Robbins Geller Rudman & Dowd",
    "Kessler Topaz Meltzer & Check",
    "Labaton Sucharow"
  ],
  "tier_2": [
    "Bleichmar Fonti & Auld",
    "Pomerantz",
    "Cohen Milstein",
    "Grant & Eisenhofer",
    "Hagens Berman"
  ],
  "tier_3_default": true
}
```

### Pattern 5: Two-Layer Case Classification

**What:** Every case gets a primary D&O coverage classification and secondary legal theory tags.
**When to use:** All case records in the litigation model.
**Example:**

```python
class CoverageType(StrEnum):
    """Primary D&O coverage relevance classification."""
    SCA_SIDE_A = "SCA_SIDE_A"       # Individual officer/director
    SCA_SIDE_B = "SCA_SIDE_B"       # Company indemnification
    SCA_SIDE_C = "SCA_SIDE_C"       # Entity securities
    DERIVATIVE_SIDE_A = "DERIV_A"   # Individual fiduciary
    DERIVATIVE_SIDE_B = "DERIV_B"   # Company
    SEC_ENFORCEMENT_A = "SEC_A"     # Individual
    SEC_ENFORCEMENT_B = "SEC_B"     # Entity
    REGULATORY_ENTITY = "REG_ENT"   # Entity-level regulatory
    EMPLOYMENT_ENTITY = "EMP_ENT"   # Entity-level employment
    PRODUCT_ENTITY = "PROD_ENT"     # Entity-level product

class LegalTheory(StrEnum):
    """Secondary legal theory tags."""
    RULE_10B5 = "10b-5"
    SECTION_11 = "Section_11"
    SECTION_14A = "Section_14(a)"
    DERIVATIVE_DUTY = "derivative_breach"
    FCPA = "FCPA"
    ANTITRUST = "antitrust"
    # ... etc ...
```

### Anti-Patterns to Avoid

- **Monolithic extractor:** Do NOT put all litigation extraction in one file. Each SECT6 requirement gets its own extractor file, and each stays under 500 lines.
- **Direct SCAC scraping:** Stanford SCAC prohibits web scraping in their Terms of Service. Use web search results, 10-K Item 3 disclosures, and EFTS as primary sources instead.
- **Scoring logic in EXTRACT:** No scoring happens in Phase 5. Extractors populate the model; the scoring engine (Phase 6) uses F.1 factor rules and CRF gates against the extracted data.
- **Hardcoded counsel lists:** Lead counsel tier lists, claim type taxonomies, and SOL parameters go in JSON config, not in Python source per CLAUDE.md.
- **Acquiring new data:** Phase 5 is EXTRACT-only. All data was acquired in Phase 2. If data gaps are found, add graceful "Not Available" handling, do not add new acquisition code.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Date calculations for SOL | Custom date math | `datetime` + `timedelta` | Leap years, edge cases handled |
| HTML stripping | Custom parser | `filing_fetcher.strip_html()` | Already exists and handles SEC HTML |
| Section parsing | Custom parser | `filing_sections.extract_section()` | Already handles TOC skipping, truncation |
| SourcedValue creation | Manual construction | `sourced.py` factories | `sourced_str()`, `sourced_float()`, etc. exist |
| Filing document access | Direct state navigation | `sourced.get_filing_document_text()` | Handles fallbacks, type casting |
| ExtractionReport creation | Manual dataclass | `validation.create_report()` | Computes coverage, confidence automatically |
| Config loading | Custom JSON parsing | `ConfigLoader.load_json()` | Existing pattern from Phase 1 |

**Key insight:** Phase 5 is primarily text parsing and classification. The infrastructure for reading filing text, creating SourcedValue-wrapped results, and reporting extraction coverage already exists. The new work is domain-specific regex patterns and classification logic.

## Common Pitfalls

### Pitfall 1: Item 3 Parsing Complexity

**What goes wrong:** 10-K Item 3 (Legal Proceedings) has wildly inconsistent formatting across companies. Some use tables, some use prose, some cross-reference other sections.
**Why it happens:** There is no standardized format for legal proceedings disclosure.
**How to avoid:** Use multiple parsing strategies (regex patterns for common phrases like "class action", "settlement", "SEC investigation") rather than structural parsing. Extract keywords and classify, don't try to parse complete case records from unstructured text.
**Warning signs:** Extractor returning empty results for companies known to have litigation.

### Pitfall 2: EFTS Rate Limiting / 403 Errors

**What goes wrong:** SEC EFTS (efts.sec.gov) returns 403 errors under certain conditions, especially when making programmatic requests.
**Why it happens:** SEC has rate limiting (10 req/sec) and may block requests that don't have proper User-Agent headers.
**How to avoid:** Use the existing `sec_get()` rate limiter from `rate_limiter.py` for all EFTS calls. The codebase already handles this correctly.
**Warning signs:** All EFTS-sourced data returning empty results.

### Pitfall 3: Confusing ACQUIRE and EXTRACT Boundaries

**What goes wrong:** Wanting to fetch new data (e.g., scrape SCAC, fetch CourtListener API) during extraction.
**Why it happens:** Litigation data feels incomplete without direct court database access.
**How to avoid:** Phase 5 operates ONLY on data already in `state.acquired_data`. Data gaps are flagged in ExtractionReports as missing fields, not fixed by new acquisitions. Future phases can enhance the ACQUIRE stage.
**Warning signs:** Import statements pulling from `stages/acquire/`.

### Pitfall 4: Model Size Explosion

**What goes wrong:** The litigation model grows beyond 500 lines because it has many sub-models (cases, enforcement, regulatory, defense, industry, SOL, contingent).
**Why it happens:** 12 SECT6 requirements each need their own typed model.
**How to avoid:** Split from day 1: `litigation.py` (top-level LitigationLandscape + CaseDetail, ~200 lines) and `litigation_details.py` (all sub-models, ~450 lines). This mirrors the `market.py` / `market_events.py` and `governance.py` / `governance_forensics.py` splits.
**Warning signs:** Model file approaching 400 lines with more fields to add.

### Pitfall 5: Statute of Limitations Date Complexity

**What goes wrong:** SOL calculations produce incorrect windows because they don't account for the difference between statute of limitations (discovery-based) and statute of repose (event-based).
**Why it happens:** 10b-5 has a 2-year SOL + 5-year repose. Section 11 has 1-year SOL + 3-year repose. These are fundamentally different time constraints.
**How to avoid:** Model both windows explicitly. Use config-driven parameters for each claim type's SOL and repose periods. The SOL map should show BOTH the discovery-based window and the absolute repose window.
**Warning signs:** SOL windows that extend beyond the repose period.

### Pitfall 6: Over-Engineering Case Parsing

**What goes wrong:** Building a full case document parser when the actual data available is mostly unstructured text mentions.
**Why it happens:** The requirements describe rich case detail (case name, number, court, judge, class period, etc.) but the available data sources (10-K Item 3, web search snippets) provide fragments, not complete records.
**How to avoid:** Extract what's available and mark missing fields. A case record with only `case_name`, `status`, and `source` is still valuable. Don't attempt to parse full case records from prose text -- extract the facts that are explicitly stated.
**Warning signs:** Large amounts of "Not Available" for fields that no data source can provide.

### Pitfall 7: Existing Pipeline/CLI Test Breakage

**What goes wrong:** Adding the litigation sub-orchestrator to ExtractStage.run() breaks existing tests that mock the extract stage.
**Why it happens:** Phase 4 established sub-orchestrator mocking patterns, but a new sub-orchestrator needs new mock patches.
**How to avoid:** Follow the Phase 4 pattern from 04-11-PLAN: patch at `do_uw.stages.extract.run_litigation_extractors` (module namespace). Add this patch alongside the existing `run_market_extractors` and `run_governance_extractors` mocks in test_extract_stage.py, test_pipeline.py, and test_cli.py.
**Warning signs:** 20+ tests failing after wiring the litigation sub-orchestrator.

## Code Examples

### Item 3 Legal Proceedings Parsing

```python
# Source: domain knowledge, regex patterns for SEC filing text
import re

# Common litigation disclosure patterns in 10-K Item 3
LITIGATION_PATTERNS: list[tuple[str, str]] = [
    (r"class\s+action", "class_action"),
    (r"securities\s+(?:fraud|class\s+action|litigation)", "sca"),
    (r"derivative\s+(?:action|suit|complaint|claim)", "derivative"),
    (r"SEC\s+(?:investigation|inquiry|enforcement|subpoena)", "sec_enforcement"),
    (r"wells\s+notice", "wells_notice"),
    (r"(?:DOJ|Department\s+of\s+Justice)\s+(?:investigation|inquiry)", "doj"),
    (r"(?:FTC|Federal\s+Trade\s+Commission)", "ftc"),
    (r"(?:EPA|Environmental\s+Protection\s+Agency)", "epa"),
    (r"(?:CFPB|Consumer\s+Financial\s+Protection)", "cfpb"),
    (r"(?:state\s+attorney|attorney\s+general)", "state_ag"),
    (r"(?:whistleblower|qui\s+tam|False\s+Claims\s+Act)", "whistleblower"),
    (r"(?:merger|appraisal|Revlon)\s+(?:litigation|suit|action|claim)", "deal_litigation"),
    (r"(?:patent|intellectual\s+property|trade\s+secret)", "ip"),
    (r"(?:employment|discrimination|EEOC|wage\s+and\s+hour)", "employment"),
    (r"(?:product\s+(?:liability|recall)|mass\s+tort)", "product"),
    (r"(?:environmental|Superfund|CERCLA|Clean\s+(?:Air|Water))", "environmental"),
    (r"(?:cybersecurity|data\s+breach|privacy)", "cyber"),
]

def classify_litigation_mentions(text: str) -> dict[str, list[str]]:
    """Extract and classify litigation mentions from filing text."""
    results: dict[str, list[str]] = {}
    sentences = re.split(r'[.!?]+', text)
    for sentence in sentences:
        for pattern, category in LITIGATION_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                if category not in results:
                    results[category] = []
                cleaned = sentence.strip()[:500]
                if cleaned and len(cleaned) > 20:
                    results[category].append(cleaned)
    return results
```

### SEC Enforcement Pipeline Position Detection

```python
# Source: domain knowledge, SEC enforcement process
from enum import StrEnum

class EnforcementStage(StrEnum):
    """SEC enforcement pipeline stages in escalation order."""
    NONE = "NONE"
    COMMENT_LETTER = "COMMENT_LETTER"
    INFORMAL_INQUIRY = "INFORMAL_INQUIRY"
    FORMAL_INVESTIGATION = "FORMAL_INVESTIGATION"
    WELLS_NOTICE = "WELLS_NOTICE"
    ENFORCEMENT_ACTION = "ENFORCEMENT_ACTION"

# Ordered from most severe to least (highest confirmed wins)
ENFORCEMENT_SIGNALS: list[tuple[str, EnforcementStage]] = [
    (r"enforcement\s+action|complaint\s+filed|civil\s+penalty", EnforcementStage.ENFORCEMENT_ACTION),
    (r"wells\s+notice|Wells\s+Notice", EnforcementStage.WELLS_NOTICE),
    (r"formal\s+(?:order\s+of\s+)?investigation|HO-\d+", EnforcementStage.FORMAL_INVESTIGATION),
    (r"informal\s+(?:inquiry|investigation)|information\s+request", EnforcementStage.INFORMAL_INQUIRY),
    (r"comment\s+letter|CORRESP|staff\s+comment", EnforcementStage.COMMENT_LETTER),
]
```

### Statute of Limitations Window Calculation

```python
# Source: securities law -- verified against multiple legal references
from datetime import date, timedelta

# Claim type -> (SOL years, repose years, SOL trigger, repose trigger)
SOL_PARAMETERS: dict[str, tuple[int, int, str, str]] = {
    "10b-5": (2, 5, "discovery", "violation"),
    "Section_11": (1, 3, "discovery", "offering"),
    "Section_14a": (1, 3, "discovery", "proxy_solicitation"),
    "derivative": (3, 6, "demand_refusal", "breach"),
    "FCPA": (5, 5, "violation", "violation"),
    "antitrust": (4, 4, "violation", "violation"),
    "ERISA": (3, 6, "discovery", "violation"),
    "employment_discrimination": (2, 2, "violation", "violation"),
    "environmental": (5, 5, "discovery", "violation"),
}

def compute_sol_window(
    claim_type: str,
    trigger_date: date,
    today: date | None = None,
) -> dict[str, date | bool]:
    """Compute SOL and repose windows for a claim type."""
    today = today or date.today()
    params = SOL_PARAMETERS.get(claim_type)
    if not params:
        return {"status": "unknown_claim_type"}
    sol_years, repose_years, _, _ = params
    sol_expiry = trigger_date + timedelta(days=sol_years * 365)
    repose_expiry = trigger_date + timedelta(days=repose_years * 365)
    return {
        "sol_expiry": sol_expiry,
        "repose_expiry": repose_expiry,
        "sol_open": today < sol_expiry,
        "repose_open": today < repose_expiry,
        "window_open": today < sol_expiry and today < repose_expiry,
    }
```

### Forum Selection Provision Parsing from DEF 14A

```python
# Source: domain knowledge, SEC proxy statement patterns
FORUM_PATTERNS: list[tuple[str, str]] = [
    # Federal forum provision (Securities Act)
    (
        r"(?:federal\s+forum|Securities\s+Act)\s+(?:provision|clause)"
        r".*?(?:United\s+States\s+federal\s+district\s+court|federal\s+court)",
        "federal_forum"
    ),
    # Exclusive forum provision (derivative suits -> Delaware)
    (
        r"(?:exclusive\s+forum|forum\s+selection)\s+(?:provision|clause)"
        r".*?(?:Court\s+of\s+Chancery|Delaware|state\s+court)",
        "exclusive_forum_derivative"
    ),
]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Stanford SCAC web scraping | SCAC prohibits scraping; use EFTS + 10-K + web search | SCAC TOS update | Cannot rely on SCAC as programmatic data source |
| SEC EDGAR EFTS v1 | EFTS `/LATEST/search-index` | Ongoing | Current endpoint used in codebase already |
| CourtListener REST v3 | CourtListener REST v4.3 | 2024-2025 | New party search, enhanced filtering -- but v2 deferred |
| Separate state models | Single LitigationLandscape under ExtractedData | Phase 1 design | All litigation data flows through state.extracted.litigation |

**Deprecated/outdated:**
- **sec-api.io (paid):** Third-party paid SEC API with litigation releases. Out of scope per CORE-07 (100% free data sources in v1).
- **PACER direct access:** $0.10/page cost, explicitly deferred to v2-08.
- **CourtListener deep integration:** Would enhance derivative suit discovery but adds complexity; deferred. Web search covers the gap in v1.

## Data Source Analysis

### What's Already Acquired (Phase 2)

The ACQUIRE stage already collects the following litigation-relevant data:

| Data | Source | Location in State | Confidence |
|------|--------|-------------------|------------|
| Web search: litigation/fraud/investigation | LitigationClient | `acquired_data.litigation_data.web_results` | LOW |
| EFTS: Item 3 legal proceedings filings | LitigationClient | `acquired_data.litigation_data.sec_references` | HIGH |
| Blind spot: lawsuits/SEC/whistleblower | WebSearchClient | `acquired_data.blind_spot_results` | LOW |
| 10-K full text (Item 3 parseable) | SECFilingClient / filing_fetcher | `acquired_data.filing_documents["10-K"]` | HIGH |
| 8-K full text (Item 8.01) | SECFilingClient / filing_fetcher | `acquired_data.filing_documents["8-K"]` | HIGH |
| DEF 14A full text (charter/bylaws) | SECFilingClient / filing_fetcher | `acquired_data.filing_documents["DEF 14A"]` | HIGH |
| Company news (may contain litigation) | NewsClient | `acquired_data.web_search_results` | LOW |
| CORRESP count | audit_risk extractor | already extracted | HIGH |

### What Needs Parsing in EXTRACT (Phase 5)

| Requirement | Data Source | Parsing Strategy |
|-------------|------------|------------------|
| SECT6-03: Securities class actions | 10-K Item 3 + EFTS + web search | Regex pattern matching for SCA keywords; cross-reference web results |
| SECT6-04: SEC enforcement pipeline | 10-K Item 1A/3 + 8-K + EFTS ("Wells notice", "investigation") + CORRESP count | Keyword detection, pipeline stage assignment |
| SECT6-05: Derivative suits | 10-K Item 3 + web search | Regex for "derivative", "Section 220", "demand" |
| SECT6-06: Regulatory proceedings | 10-K Item 3 + 8-K + web search | Agency name pattern matching (DOJ, FTC, EPA, etc.) |
| SECT6-07: M&A/deal litigation | 10-K Item 3 + 8-K + web search | "merger objection", "appraisal", "Revlon" patterns |
| SECT6-08: Workforce/product/env | 10-K Item 3 + 8-K + web search | Category-specific patterns (EEOC, recall, WARN, etc.) |
| SECT6-09: Defense assessment | DEF 14A (forum provisions) + 10-K (PSLRA safe harbor) | Regex for charter provisions, safe harbor language |
| SECT6-10: Industry claim patterns | Peer company SCAs from brain/checks.json + config | Config lookup + sector mapping |
| SECT6-11: SOL map | Computed from filing dates + claim types | Date arithmetic with config-driven parameters |
| SECT6-12: Contingent liabilities | 10-K footnotes (ASC 450) + Item 3 | Regex for "contingent", "accrued", "reasonably possible" |

### What Filing Sections Need Adding to `filing_sections.py`

Currently `filing_sections.py` parses Item 1, Item 7, and Item 9A. Phase 5 needs:

| Section | Purpose | Priority |
|---------|---------|----------|
| Item 3 (Legal Proceedings) | Primary litigation disclosure | CRITICAL |
| Item 1A (Risk Factors) | "under investigation" language, regulatory risk mentions | HIGH |
| Item 8 footnotes | Contingent liability reserves (ASC 450) | HIGH |

Item 3 is the most important addition. Item 1A and Item 8 footnotes can be searched via full-text regex without formal section extraction if the section headers are unreliable.

## Model Expansion Design

### Current LitigationLandscape (Phase 1 Skeleton)

```python
class LitigationLandscape(BaseModel):
    securities_class_actions: list[CaseDetail] = []
    sec_enforcement: SECEnforcement
    derivative_suits: list[CaseDetail] = []
    regulatory_proceedings: list[SourcedValue[dict[str, str]]] = []
    defense_assessment: SourcedValue[str] | None = None
    total_litigation_reserve: SourcedValue[float] | None = None
```

### Required Expansion for Phase 5

**litigation.py** (~250 lines): Top-level container + expanded CaseDetail + SECEnforcementPipeline

Fields to add to CaseDetail:
- `coverage_type: SourcedValue[str]` (CoverageType enum value)
- `legal_theories: list[SourcedValue[str]]` (LegalTheory enum values)
- `lead_plaintiff_type: SourcedValue[str]` (institutional, pension, individual)
- `lead_counsel_tier: SourcedValue[str]` (1, 2, 3 from config)
- `class_period_days: int | None`
- `key_rulings: list[SourcedValue[str]]`

Fields to add to SECEnforcement -> rename to SECEnforcementPipeline:
- `highest_confirmed_stage: SourcedValue[str]` (EnforcementStage)
- `pipeline_signals: list[SourcedValue[str]]` (evidence for each stage)
- `comment_letter_count: SourcedValue[int]`
- `comment_letter_topics: list[SourcedValue[str]]`
- `industry_sweep_detected: SourcedValue[bool]`
- `enforcement_narrative: SourcedValue[str]`

**litigation_details.py** (~450 lines): All new sub-models

- `RegulatoryProceeding` -- agency, type, status, D&O implications
- `DealLitigation` -- merger objection, appraisal, disclosure-only
- `WorkforceProductEnvironmental` -- EEOC, WARN, product recall, EPA, cyber
- `DefenseAssessment` -- forum provisions, PSLRA safe harbor, judge analysis
- `IndustryClaimPattern` -- theory, peer examples, exposure assessment
- `SOLWindow` -- claim type, trigger date, SOL expiry, repose expiry
- `ContingentLiability` -- description, amount range, ASC 450 classification
- `WhistleblowerIndicator` -- source, type, date, significance
- `ForumProvisions` -- federal forum, exclusive forum, details

Fields to add to LitigationLandscape:
- `deal_litigation: list[DealLitigation]`
- `workforce_product_environmental: WorkforceProductEnvironmental`
- `defense: DefenseAssessment`
- `industry_patterns: list[IndustryClaimPattern]`
- `sol_map: list[SOLWindow]`
- `contingent_liabilities: list[ContingentLiability]`
- `whistleblower_indicators: list[WhistleblowerIndicator]`
- `litigation_summary: SourcedValue[str]`
- `litigation_timeline_events: list[SourcedValue[dict[str, str]]]`
- `active_matter_count: SourcedValue[int]`
- `historical_matter_count: SourcedValue[int]`

## Plan Structure Recommendation

Based on the 3-plan structure in the roadmap and the natural grouping:

### Plan 05-01: Foundation + Core Litigation Extractors

**Scope:** Model expansion + Item 3 parsing + SCA extractor + SEC enforcement extractor + derivative suits extractor
**Requirements:** SECT6-01 through SECT6-05
**Estimated size:** ~10-12 files created/modified

Wave 1 (models): Expand litigation.py, create litigation_details.py, add Item 3 to filing_sections.py
Wave 2 (extractors): sca_extractor.py, sec_enforcement.py, derivative_suits.py
Wave 3 (config): lead_counsel_tiers.json, claim_types.json

### Plan 05-02: Regulatory + M&A + Workforce/Product/Environmental

**Scope:** Regulatory proceedings extractor + deal litigation extractor + workforce/product/environmental extractor
**Requirements:** SECT6-06 through SECT6-08
**Estimated size:** ~3-5 files created/modified

Wave 1: regulatory_extract.py, deal_litigation.py, workforce_product.py

### Plan 05-03: Defense + Industry Patterns + SOL + Contingent + Integration

**Scope:** Defense assessment + industry claim patterns + SOL map + contingent liabilities + sub-orchestrator + test updates
**Requirements:** SECT6-09 through SECT6-12
**Estimated size:** ~8-10 files created/modified

Wave 1 (extractors): defense_assessment.py, industry_claims.py, sol_mapper.py, contingent_liab.py
Wave 2 (config): industry_theories.json
Wave 3 (integration): extract_litigation.py sub-orchestrator, wire into ExtractStage.__init__.py, test updates for pipeline/CLI/extract

## Discretion Recommendations

### SEC Enforcement Dig Depth

**Recommendation:** Three-tier search.
1. **Company disclosures** (HIGH confidence): 10-K Item 3, Item 1A risk factors, 8-K for "Wells notice", "subpoena", "investigation" keywords
2. **EDGAR EFTS search** (HIGH confidence): Full-text search for company name + enforcement terms ("Wells notice", "enforcement action", "SEC complaint")
3. **CORRESP/UPLOAD filings** (HIGH confidence): Count from existing audit_risk extractor + categorize topics by keyword matching against full CORRESP text

This avoids needing SEC Litigation Releases (paid API) while still catching most enforcement activity through public filings.

### Contingent Liability Footnote Parsing

**Recommendation:** Medium depth.
- Search 10-K full text for ASC 450 language ("contingent", "accrued", "probable", "reasonably possible", "loss contingency")
- Extract dollar amounts adjacent to litigation/contingent keywords using regex
- Capture "reasonably possible" range disclosures separately from "probable" accruals
- Don't attempt to parse full financial statement footnote tables (too format-variable)

### Lead Counsel Tier List

**Recommendation:** Config-driven 3-tier system:
- **Tier 1** (5-8 firms): Firms consistently in top 10 by settlement value per ISS SCAS reports. Bernstein Litowitz, Robbins Geller, Kessler Topaz, Labaton Sucharow, Grant & Eisenhofer
- **Tier 2** (8-12 firms): Firms consistently in top 50. Bleichmar Fonti & Auld, Pomerantz, Cohen Milstein, Hagens Berman, Kirby McInerney, Glancy Prongay, Scott+Scott
- **Tier 3** (default): All other firms
- Store in `config/lead_counsel_tiers.json`, match by substring (firm names vary in citation)

### Contagion Detection Methodology

**Recommendation:** Config-driven industry theory mapping.
- Create `config/industry_theories.json` mapping SIC ranges to known claim theories (e.g., SIC 2830-2836 pharma -> "clinical trial disclosure", "off-label promotion"; SIC 6020-6029 banks -> "loan loss reserves", "BSA/AML")
- For each mapped theory, check if THIS company has operational exposure (based on business description from Phase 3)
- Flag as "contagion risk" if a peer company in the same SIC range has been sued under a theory that applies to this company
- Confidence: LOW for contagion flags (speculative by nature)

### Time Horizon Exact Cutoffs

**Recommendation:**
- Securities class actions: exactly 10 years (3650 days)
- SEC enforcement / regulatory: exactly 5 years (1825 days)
- Employment / product / environmental: exactly 3 years (1095 days)
- M&A / deal litigation: 5 years (same as regulatory -- deals are regulated transactions)
- Whistleblower: 3 years (leading indicator, recent is most relevant)
- Derivative suits: 5 years (same timeframe as enforcement)

## Open Questions

1. **Stanford SCAC Access in v1**
   - What we know: SCAC prohibits web scraping. Academic data access requires NDA. No public API exists. SCAC is currently "undergoing restructuring."
   - What's unclear: Whether web search results about SCAC entries are sufficient to reconstruct case details, or if this creates gaps.
   - Recommendation: Accept that v1 relies on web search + 10-K + EFTS for SCA data. SCAC integration is a v2 enhancement. Web search captures most high-profile SCAs. 10-K Item 3 captures company's own characterization. Missing: systematic historical search going back 10 years for lesser-known cases.

2. **Judge Track Record Data**
   - What we know: CONTEXT.md says to identify assigned judge and cross-reference reputation via web search. CourtListener has judge data but is v2 deferred.
   - What's unclear: Whether web search alone can reliably identify a judge as plaintiff-friendly or defense-friendly.
   - Recommendation: Extract judge name from case records (if available in 10-K or web search), and run a web search for "[judge name] securities class action dismissal rate". Flag as LOW confidence. Full judge analytics via CourtListener is v2.

3. **Industry Sweep Detection Data Quality**
   - What we know: The requirement is to search for SEC enforcement actions against peer companies.
   - What's unclear: How to reliably detect "industry sweeps" without a structured enforcement database.
   - Recommendation: Use EFTS full-text search for peer company names + enforcement keywords. Cross-reference with web search for "[industry] SEC sweep" or "[industry] SEC enforcement". Flag matches as LOW confidence industry sweep indicators.

4. **CORRESP Filing Content Access**
   - What we know: CORRESP filings are on EDGAR. The codebase counts them but doesn't parse content. CONTEXT.md says to "proactively search EDGAR for SEC comment letter correspondence."
   - What's unclear: Whether CORRESP filing content is already fetched by filing_fetcher.py (it fetches by form type, and CORRESP may not be in the filing type list).
   - Recommendation: Check if CORRESP is in the SECFilingClient's filing type list. If not, the full text won't be available. In that case, use the count from audit_risk extractor + EFTS keyword search as proxy. Adding CORRESP to the filing type list would require ACQUIRE stage changes (out of scope for Phase 5).

## Sources

### Primary (HIGH confidence)
- Existing codebase inspection: `src/do_uw/models/litigation.py`, `src/do_uw/stages/extract/__init__.py`, `src/do_uw/stages/extract/extract_market.py`, `src/do_uw/stages/extract/extract_governance.py`, `src/do_uw/stages/acquire/clients/litigation_client.py`, `src/do_uw/stages/acquire/clients/sec_client.py`
- Project domain knowledge: `src/do_uw/brain/scoring.json` (F.1 Prior Litigation factor), `src/do_uw/brain/red_flags.json` (CRF-01/02/03), `src/do_uw/brain/checks.json` (56 section-4 litigation checks)
- CLAUDE.md, REQUIREMENTS.md, ROADMAP.md, STATE.md

### Secondary (MEDIUM confidence)
- SEC EDGAR EFTS FAQ: https://www.sec.gov/edgar/search/efts-faq.html -- EFTS endpoint and query capabilities
- SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces -- CORRESP search guidance
- ISS SCAS Top Plaintiff Law Firms: https://static.blbglaw.com/docs/ISS%20SCAS%20Top%20Plaintiff%20Law%20Firms%20of%202023.pdf -- firm tier data
- ABA securities SOL article: https://www.americanbar.org/groups/litigation/committees/class-actions/articles/2018/summer2018-timeliness-next-to-godliness-statutes-of-limitations-and-repose-in-securities-class-actions/ -- SOL/repose parameters
- CourtListener REST API v4.3: https://www.courtlistener.com/help/api/rest/ -- v2 enhancement reference

### Tertiary (LOW confidence)
- Stanford SCAC: https://securities.stanford.edu/ -- confirmed no public API, scraping prohibited, restructuring in progress
- Harvard Law forum selection: https://corpgov.law.harvard.edu/2020/04/04/federal-forum-selection-bylaws-for-securities-act-claims/ -- forum provision patterns
- D&O Diary ISS report: https://www.dandodiary.com/2021/03/articles/securities-litigation/iss-scas-report-ranks-top-50-plaintiffs-securities-law-firms-by-2020-settlement-values/ -- firm rankings

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, all patterns established in Phase 3/4
- Architecture: HIGH -- follows exact same sub-orchestrator + extractor + model pattern
- Data sources: MEDIUM -- SCAC limitation confirmed; EFTS + 10-K + web search are solid but won't catch everything
- Pitfalls: MEDIUM -- based on codebase patterns and domain knowledge; text parsing complexity is the main risk
- Model design: HIGH -- directly mirrors governance_forensics.py / market_events.py patterns
- SOL parameters: MEDIUM -- verified against legal references but jurisdiction-specific variations exist

**Research date:** 2026-02-08
**Valid until:** 2026-03-10 (stable domain, no fast-moving dependencies)
