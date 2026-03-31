# Phase 19: LLM Extraction -- Governance & Litigation - Research

**Researched:** 2026-02-10
**Domain:** LLM extraction result consumption, domain model population, regex replacement
**Confidence:** HIGH (all findings from direct codebase analysis)

## Summary

Phase 19 consumes the Phase 18 LLM extraction results (stored in `state.acquired_data.llm_extractions` as `dict[str, Any]`) and uses them to populate the governance (SECT5) and litigation (SECT6) domain models. The core work is building converter modules that deserialize LLM extraction dicts into typed Pydantic models (DEF14AExtraction, TenKExtraction) and then map their fields to the existing domain models (GovernanceData, LitigationLandscape, and their sub-models).

The existing regex extractors for governance and litigation are fragile and produce LOW/MEDIUM confidence data. The LLM extraction schemas from Phase 18 already capture most of the needed fields, but there are specific gaps that need schema expansion. The key architectural decision is integrating LLM results at the sub-orchestrator level (`extract_governance.py`, `extract_litigation.py`) so that each individual extractor can check for LLM data first and fall back to regex only when LLM data is absent.

**Primary recommendation:** Build converter modules that map DEF14AExtraction to GovernanceData sub-models and TenKExtraction to LitigationLandscape sub-models. Modify the sub-orchestrators to pre-deserialize LLM results once, then pass typed extraction objects to individual extractors. Expand schemas for 5-7 missing critical fields.

## Standard Stack

This phase uses exclusively the established project stack. No new dependencies.

### Core
| Library | Version | Purpose | Why Used |
|---------|---------|---------|----------|
| pydantic | v2 | Domain models + LLM extraction schemas | Already established |
| anthropic | existing | LLM API (Phase 18) | Already installed |
| instructor | existing | Structured output (Phase 18) | Already installed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | existing | Unit + integration tests | Validation of converters |
| ruff | existing | Linting | Code quality |
| pyright | strict | Type checking | All new code |

## Architecture Patterns

### Pattern 1: LLM Result Access -- Deserialization from state

**What:** LLM extraction results are stored as `dict[str, Any]` in `state.acquired_data.llm_extractions`, keyed by `'form_type:accession'`. To use them, you must deserialize into the typed schema model.

**Access pattern:**
```python
from do_uw.stages.extract.llm.schemas import DEF14AExtraction, TenKExtraction

def get_llm_def14a(state: AnalysisState) -> DEF14AExtraction | None:
    """Deserialize LLM DEF 14A extraction from state."""
    if state.acquired_data is None:
        return None
    for key, data in state.acquired_data.llm_extractions.items():
        if key.startswith("DEF 14A:"):
            return DEF14AExtraction.model_validate(data)
    return None

def get_llm_ten_k(state: AnalysisState) -> TenKExtraction | None:
    """Deserialize LLM 10-K extraction from state."""
    if state.acquired_data is None:
        return None
    for key, data in state.acquired_data.llm_extractions.items():
        if key.startswith("10-K:"):
            return TenKExtraction.model_validate(data)
    return None
```

**Design decision:** Pre-deserialize once at the sub-orchestrator level. Pass the typed object to individual extractors rather than having each extractor re-deserialize. This avoids repeated `model_validate()` calls and ensures consistency.

### Pattern 2: Converter Module Pattern

**What:** New converter modules that map flat LLM extraction fields to nested domain model fields wrapped in `SourcedValue[T]`.

**Structure:**
```
src/do_uw/stages/extract/
  llm_governance.py     -- DEF14AExtraction -> GovernanceData sub-models
  llm_litigation.py     -- TenKExtraction -> LitigationLandscape sub-models
```

**Example converter function:**
```python
from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance_forensics import BoardForensicProfile
from do_uw.stages.extract.llm.schemas.common import ExtractedDirector
from do_uw.stages.extract.sourced import sourced_str, sourced_float, now

_LLM_SOURCE = "DEF 14A (LLM)"

def convert_director(d: ExtractedDirector) -> BoardForensicProfile:
    """Convert LLM ExtractedDirector to domain BoardForensicProfile."""
    profile = BoardForensicProfile()
    if d.name:
        profile.name = sourced_str(d.name, _LLM_SOURCE, Confidence.HIGH)
    if d.independent is not None:
        profile.is_independent = SourcedValue[bool](
            value=d.independent,
            source=_LLM_SOURCE,
            confidence=Confidence.HIGH,
            as_of=now(),
        )
    if d.tenure_years is not None:
        profile.tenure_years = sourced_float(
            d.tenure_years, _LLM_SOURCE, Confidence.HIGH,
        )
    profile.committees = d.committees
    for board in d.other_boards:
        profile.other_boards.append(
            sourced_str(board, _LLM_SOURCE, Confidence.HIGH)
        )
    profile.is_overboarded = (len(d.other_boards) + 1) >= 4
    return profile
```

**Key principle:** All LLM-extracted data gets `Confidence.HIGH` (same as XBRL) and source `"DEF 14A (LLM)"` or `"10-K (LLM)"`. The `SourcedValue` wrapper must be applied during conversion, not in the LLM schema itself (LLM schemas are intentionally flat).

### Pattern 3: LLM-First with Field-Level Regex Fallback

**What:** At the sub-orchestrator level, check for LLM results first. If LLM produced a result for a filing type, use it as primary. If specific fields are null in the LLM result, run targeted regex extraction for just those fields.

**Example integration in extract_governance.py:**
```python
def run_governance_extractors(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> GovernanceData:
    gov = GovernanceData()

    # Pre-deserialize LLM result (once)
    llm_def14a = get_llm_def14a(state)

    # 1. Board profiles -- LLM first, regex fallback
    if llm_def14a and llm_def14a.directors:
        gov.board_forensics = convert_directors(llm_def14a)
        gov.governance_score = compute_governance_score(
            gov.board_forensics, gov.comp_analysis, weights, thresholds
        )
    else:
        # Full regex fallback
        gov.board_forensics, gov.governance_score = _run_board_governance(state, reports)

    # Field-level fallback example:
    if llm_def14a and llm_def14a.say_on_pay_approval_pct is None:
        # LLM didn't find say-on-pay; try regex on that specific field
        proxy_text = get_filing_document_text(state, "DEF 14A")
        sop = _extract_say_on_pay(proxy_text)
        if sop is not None:
            gov.comp_analysis.say_on_pay_pct = sourced_float(sop, source, Confidence.MEDIUM)
```

### Pattern 4: Source Text Attribution

**What:** LLM extraction schemas already include `source_passage` fields on `ExtractedDirector`, `ExtractedCompensation`, and `ExtractedLegalProceeding`. These should be preserved in the domain models where applicable.

**Where to store:** The domain models don't have explicit `source_passage` fields. Two options:
1. Store in the `source` field of `SourcedValue` (e.g., `source="DEF 14A (LLM): 'Mr. Cook has served as CEO since 2011...'"`). Keeps it compact but limits length.
2. Add `bio_summary`/`source_excerpt` fields to domain models where needed. The `LeadershipForensicProfile` already has `bio_summary: SourcedValue[str]` which can hold the LLM source_passage.

**Recommendation:** Option 1 for most fields (compact, no model changes). Option 2 only for `bio_summary` on `LeadershipForensicProfile` and litigation case descriptions where the passage is genuinely useful for underwriter review.

### Anti-Patterns to Avoid
- **Dual-sourcing a field:** Never store both LLM and regex results for the same field. LLM wins when present; regex fills gaps.
- **Re-deserializing per extractor:** Deserialize `llm_extractions` once in the sub-orchestrator and pass the typed model down.
- **Modifying LLM schemas for domain model compatibility:** Keep LLM schemas flat and simple (Anthropic structured output constraints). Conversion happens in converter modules.
- **Confidence confusion:** LLM extraction reads actual SEC filing text = HIGH confidence. Regex extraction from the same text = MEDIUM/LOW because regex is less reliable.

## Field Mapping Analysis: DEF14AExtraction -> GovernanceData

### Direct Mappings (fields exist in both, straightforward conversion)

| LLM Schema Field | Domain Model Target | Confidence | Notes |
|-------------------|---------------------|------------|-------|
| `directors[].name` | `BoardForensicProfile.name` | HIGH | SourcedValue wrapper |
| `directors[].age` | Not in domain model | -- | Age not in BoardForensicProfile; could add |
| `directors[].independent` | `BoardForensicProfile.is_independent` | HIGH | Direct bool mapping |
| `directors[].tenure_years` | `BoardForensicProfile.tenure_years` | HIGH | Direct float mapping |
| `directors[].committees` | `BoardForensicProfile.committees` | HIGH | Direct list mapping |
| `directors[].other_boards` | `BoardForensicProfile.other_boards` | HIGH | Need SourcedValue wrapping |
| `directors[].source_passage` | `LeadershipForensicProfile.bio_summary` | HIGH | Where applicable |
| `board_size` | `BoardProfile.size` | HIGH | |
| `independent_count` / `board_size` | `BoardProfile.independence_ratio` | HIGH | Computed ratio |
| `classified_board` | `BoardProfile.classified_board` | HIGH | |
| `ceo_chair_combined` | `BoardProfile.ceo_chair_duality` | HIGH | |
| `named_executive_officers[].name` | `LeadershipForensicProfile.name` | HIGH | |
| `named_executive_officers[].title` | `LeadershipForensicProfile.title` | HIGH | |
| `named_executive_officers[].salary` | `CompensationAnalysis.ceo_salary` (for CEO) | HIGH | |
| `named_executive_officers[].bonus` | `CompensationAnalysis.ceo_bonus` (for CEO) | HIGH | |
| `named_executive_officers[].stock_awards` + `option_awards` | `CompensationAnalysis.ceo_equity` (for CEO) | HIGH | Sum of stock + options |
| `named_executive_officers[].other_comp` | `CompensationAnalysis.ceo_other` (for CEO) | HIGH | |
| `named_executive_officers[].total_comp` | `CompensationAnalysis.ceo_total_comp` (for CEO) | HIGH | |
| `ceo_pay_ratio` | `CompensationAnalysis.ceo_pay_ratio` | HIGH | Parse "123:1" to float 123.0 |
| `golden_parachute_total` | `CompensationFlags.golden_parachute_value` | HIGH | |
| `say_on_pay_approval_pct` | `CompensationAnalysis.say_on_pay_pct` / `CompensationFlags.say_on_pay_support_pct` | HIGH | |
| `say_on_pay_frequency` | Not in domain model | -- | Could add to CompensationAnalysis |
| `shareholder_proposals` | Not directly mapped | -- | Could add to GovernanceData |
| `officers_directors_ownership_pct` | `OwnershipAnalysis.insider_pct` | HIGH | |
| `top_5_holders` | `OwnershipAnalysis.top_holders` | HIGH | Parse "Name: X%" format |
| `poison_pill` | Not in domain model | -- | Anti-takeover; could add |
| `supermajority_voting` | Not in domain model | -- | Anti-takeover; could add |
| `blank_check_preferred` | Not in domain model | -- | Anti-takeover; could add |
| `forum_selection_clause` | `DefenseAssessment.forum_provisions.exclusive_forum_details` | HIGH | Cross-domain: DEF 14A data used by litigation |
| `exclusive_forum_provision` | `DefenseAssessment.forum_provisions.has_exclusive_forum` | HIGH | Cross-domain |
| `do_coverage_mentioned` | Not in domain model | -- | D&O-specific, could add to GovernanceData |
| `do_indemnification` | Not in domain model | -- | D&O-specific, could add |
| `indemnification_detail` | Not in domain model | -- | D&O-specific, could add |
| `lead_independent_director` | Not in domain model | -- | Could add to BoardProfile |
| `ceo_name` | Derivable from NEOs | -- | Use NEO with CEO title |
| `chair_name` | Not in domain model | -- | Could add to BoardProfile |
| `audit_committee_members` | Derivable from directors | -- | Match committee membership |
| `compensation_committee_members` | Derivable from directors | -- | Match committee membership |
| `nominating_committee_members` | Derivable from directors | -- | Match committee membership |
| `annual_election` | Related to `classified_board` | -- | Inverse of classified_board |

### Board Aggregate Enrichment

The LLM can populate `BoardProfile` aggregate fields that regex often misses:
- `BoardProfile.size` <- `board_size`
- `BoardProfile.independence_ratio` <- `independent_count / board_size`
- `BoardProfile.ceo_chair_duality` <- `ceo_chair_combined`
- `BoardProfile.classified_board` <- `classified_board`
- `BoardProfile.overboarded_count` <- count of directors with 4+ other_boards
- `BoardProfile.avg_tenure_years` <- mean of `directors[].tenure_years`

## Field Mapping Analysis: TenKExtraction -> LitigationLandscape

### Direct Mappings

| LLM Schema Field | Domain Model Target | Confidence | Notes |
|-------------------|---------------------|------------|-------|
| `legal_proceedings[].case_name` | `CaseDetail.case_name` | HIGH | SourcedValue wrapper |
| `legal_proceedings[].court` | `CaseDetail.court` | HIGH | |
| `legal_proceedings[].filing_date` | `CaseDetail.filing_date` | HIGH | Parse YYYY-MM-DD to date |
| `legal_proceedings[].allegations` | `CaseDetail.allegations` | HIGH | Single string to list |
| `legal_proceedings[].status` | `CaseDetail.status` | HIGH | Map to CaseStatus enum |
| `legal_proceedings[].settlement_amount` | `CaseDetail.settlement_amount` | HIGH | |
| `legal_proceedings[].class_period_start` | `CaseDetail.class_period_start` | HIGH | Parse to date |
| `legal_proceedings[].class_period_end` | `CaseDetail.class_period_end` | HIGH | Parse to date |
| `legal_proceedings[].source_passage` | CaseDetail description context | HIGH | Audit trail |
| `risk_factors[].title` | Custom risk factor model | HIGH | |
| `risk_factors[].category` | Categorized risk | HIGH | Maps to D&O relevance |
| `risk_factors[].severity` | Risk severity | HIGH | |
| `risk_factors[].is_new_this_year` | New risk detection | HIGH | Critical for underwriting |
| `risk_factors[].source_passage` | Audit trail | HIGH | |
| `contingent_liabilities` | `ContingentLiability.description` | HIGH | String list to structured |
| `going_concern` | `AuditRisk.going_concern` | HIGH | Already mapped in financials |
| `material_weaknesses` | `AuditRisk.material_weaknesses` | HIGH | Already mapped in financials |
| `related_party_transactions` | `CompensationAnalysis.related_party_transactions` | HIGH | Cross-domain |

### Legal Proceedings Deep Mapping

The LLM `ExtractedLegalProceeding` maps to the domain `CaseDetail` with these conversions needed:

1. **`allegations` (str) -> `allegations` (list[SourcedValue[str]])**: Split the LLM's single string into individual allegation types. Also infer `legal_theories` from the text ("10b-5" -> `LegalTheory.RULE_10B5`).

2. **`status` (str) -> `status` (SourcedValue[str])**: Map LLM status strings ("ACTIVE", "SETTLED", etc.) to `CaseStatus` enum values.

3. **`filing_date` (str) -> `filing_date` (SourcedValue[date])**: Parse YYYY-MM-DD string to `date` object.

4. **`coverage_type` inference**: Infer from legal theories (same logic as `detect_coverage_type()` in sca_extractor.py).

5. **Merge with external data**: LLM extracts Item 3 cases. Stanford SCAC/EFTS data adds case_number, lead_counsel, lead_counsel_tier, named_defendants. These must merge by case name matching.

### Risk Factor Mapping

The LLM `ExtractedRiskFactor` does NOT map directly to an existing domain model field. Currently risk factors are not stored as structured data in the domain model. They need to go somewhere.

Options:
1. Add `risk_factors: list[RiskFactorProfile]` to `LitigationLandscape` or a new model
2. Use them as inputs to the ANALYZE stage checks
3. Store in `GovernanceData` since risk factors span governance + litigation

**Recommendation:** Add a `risk_factors` field to `ExtractedData` (the top-level extracted container) since risk factors span multiple domains. Or add to the existing state but with a new typed model.

### Contingent Liabilities from LLM

The LLM `contingent_liabilities` field is `list[str]` (free text descriptions like `"$50M-$100M range for patent infringement claim"`). The domain model `ContingentLiability` has structured fields: `asc_450_classification`, `accrued_amount`, `range_low`, `range_high`, `description`, `source_note`.

**Gap:** The LLM schema doesn't extract structured contingency data (classification, amounts, ranges). It only extracts free-text descriptions.

**Recommendation:** Expand the LLM schema to extract structured contingencies:
```python
class ExtractedContingency(BaseModel):
    description: str = ""
    classification: str | None = None  # probable, reasonably_possible, remote
    accrued_amount: float | None = None
    range_low: float | None = None
    range_high: float | None = None
    source_passage: str = ""
```

Replace `contingent_liabilities: list[str]` with `contingent_liabilities: list[ExtractedContingency]` in `TenKExtraction`.

## Schema Expansion Needs

### Critical Expansions (HIGH priority -- fields are critical for underwriting AND reliably extractable)

| Schema | Field to Add | Domain Model Target | Rationale |
|--------|-------------|---------------------|-----------|
| `TenKExtraction` | `contingent_liabilities` -> `list[ExtractedContingency]` | `ContingentLiability` | Current string list loses structure. LLM can extract classification + amounts |
| `ExtractedLegalProceeding` | `legal_theories: list[str]` | `CaseDetail.legal_theories` | LLM can identify 10b-5, Section 11, ERISA from filing text |
| `ExtractedLegalProceeding` | `named_defendants: list[str]` | `CaseDetail.named_defendants` | LLM can extract defendant names from Item 3 |
| `ExtractedLegalProceeding` | `accrued_amount: float | None` | Links to contingent liabilities | LLM can extract "accrued $X million" from legal proceedings |
| `DEF14AExtraction` | `has_clawback: bool | None` | `CompensationAnalysis.has_clawback` | LLM can detect clawback disclosure |
| `DEF14AExtraction` | `clawback_scope: str | None` | `CompensationAnalysis.clawback_scope` | DODD_FRANK_MINIMUM vs BROADER |

### Nice-to-Have Expansions (MEDIUM priority -- useful but not blocking)

| Schema | Field to Add | Domain Model Target | Rationale |
|--------|-------------|---------------------|-----------|
| `DEF14AExtraction` | `anti_takeover_provisions: list[str]` | New field on GovernanceData | Consolidated anti-takeover list |
| `DEF14AExtraction` | `notable_perquisites: list[str]` | `CompensationAnalysis.notable_perquisites` | LLM can identify perks better than regex |
| `DEF14AExtraction` | `performance_metrics: list[str]` | `CompensationAnalysis.performance_metrics` | LLM can extract incentive plan metrics |
| `ExtractedDirector` | `age` already exists | Could add to `BoardForensicProfile` | Useful for board refreshment analysis |
| `ExtractedRiskFactor` | `do_relevance_score: float | None` | New: risk factor D&O scoring | LLM can assess D&O relevance (0-1) |

### Skippable Expansions (LOW priority -- domain models don't use them)

| Schema | Potential Field | Why Skip |
|--------|----------------|----------|
| Director professional background detail | BoardForensicProfile doesn't use it beyond bio_summary |
| Detailed voting results per proposal | Not consumed by scoring |
| Historical compensation YoY changes | Not in current domain model |

## Converter Module Design

### `llm_governance.py` (new file, <500 lines)

Responsibilities:
1. Deserialize DEF14AExtraction from llm_extractions dict
2. Convert `directors[]` -> `BoardForensicProfile[]`
3. Convert `named_executive_officers[]` -> `LeadershipForensicProfile[]` for NEOs
4. Populate `BoardProfile` aggregate fields (size, independence_ratio, etc.)
5. Populate `CompensationAnalysis` from CEO NEO data
6. Populate `CompensationFlags` from say-on-pay, golden parachute
7. Populate `OwnershipAnalysis` insider_pct from officers_directors_ownership_pct
8. Cross-populate `DefenseAssessment.forum_provisions` from DEF 14A forum fields

Key functions:
- `get_llm_def14a(state) -> DEF14AExtraction | None`
- `convert_directors(extraction) -> list[BoardForensicProfile]`
- `convert_neos_to_leaders(extraction) -> list[LeadershipForensicProfile]`
- `convert_compensation(extraction) -> CompensationAnalysis`
- `convert_board_profile(extraction) -> BoardProfile`
- `convert_compensation_flags(extraction) -> CompensationFlags`
- `convert_ownership_from_proxy(extraction) -> partial OwnershipAnalysis`

### `llm_litigation.py` (new file, <500 lines)

Responsibilities:
1. Deserialize TenKExtraction from llm_extractions dict
2. Convert `legal_proceedings[]` -> `CaseDetail[]`
3. Convert `risk_factors[]` -> structured risk factor data
4. Convert `contingent_liabilities` -> `ContingentLiability[]` (after schema expansion)
5. Populate defense-related fields from 10-K (PSLRA, material weaknesses)

Key functions:
- `get_llm_ten_k(state) -> TenKExtraction | None`
- `convert_legal_proceedings(extraction) -> list[CaseDetail]`
- `convert_risk_factors(extraction) -> list[StructuredRiskFactor]`
- `convert_contingencies(extraction) -> list[ContingentLiability]`
- `merge_llm_with_sca(llm_cases, sca_cases) -> list[CaseDetail]`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Case name matching for merge | Custom fuzzy matcher | `word_overlap_pct()` from sca_extractor.py | Already exists, tested, handles edge cases |
| Date parsing | Custom parser | `parse_date_str()` from sca_extractor.py | Already handles multiple formats |
| SourcedValue construction | Inline construction | `sourced_str()`, `sourced_float()`, `sourced_int()` from sourced.py | Consistency with existing extractors |
| Coverage type inference | New logic | `detect_coverage_type()` from sca_extractor.py | Already maps theories to coverage |
| Legal theory detection | New regex | `detect_legal_theories()` from sca_extractor.py | Can apply to LLM text too |
| Governance scoring | Re-implement | `compute_governance_score()` from board_governance.py | Already works, just needs board profiles as input |
| Quality filtering | New logic | `is_case_viable()` from sca_extractor.py | Same viability criteria apply |
| ASC 450 classification | New logic | `classify_asc450()` from contingent_notes.py | Already handles implicit patterns |

## Common Pitfalls

### Pitfall 1: Dual Data Contamination
**What goes wrong:** Both LLM and regex populate the same domain field, leading to duplicate entries or conflicting values.
**Why it happens:** LLM replaces regex at the extractor level, but individual field fallback creates a merge path.
**How to avoid:** Clear ownership rule: for each field, either LLM or regex populates it. Never both. LLM result is authoritative when present. Field-level fallback means "LLM returned null for THIS field, try regex for THIS field only."
**Warning signs:** Domain model lists (e.g., `board_forensics`) have duplicate entries.

### Pitfall 2: Confidence Level Confusion
**What goes wrong:** LLM-extracted data gets MEDIUM confidence because the extractor wrapping uses MEDIUM by default.
**Why it happens:** Copy-pasting from existing regex extractors that default to MEDIUM.
**How to avoid:** All LLM-extracted data is HIGH confidence (it reads actual SEC filing text). Only regex fallback data is MEDIUM/LOW. Source string must include "(LLM)" marker.
**Warning signs:** LLM results showing as MEDIUM in the worksheet.

### Pitfall 3: Broken Governance Scoring
**What goes wrong:** Governance quality score produces different results when fed LLM profiles vs regex profiles because the profiles have different field population patterns.
**Why it happens:** The scoring functions (e.g., `_score_independence()`) check for `is_independent is not None` -- if LLM always populates independence, scores change.
**How to avoid:** This is actually DESIRED behavior -- LLM produces more complete profiles, so scoring should be more accurate. But test that scoring remains correct by validating against known companies.
**Warning signs:** Governance score jumps dramatically between regex-only and LLM+regex runs.

### Pitfall 4: Stale LLM Schema Hash Breaks Cache
**What goes wrong:** Expanding LLM schemas (adding fields) changes the schema hash, invalidating all cached LLM extraction results.
**Why it happens:** `schema_hash()` uses SHA-256 of the JSON schema. Any field addition changes the hash.
**How to avoid:** This is by design -- schema version auto-invalidates cache. But be aware that first runs after schema expansion will re-extract all filings (costs $). Batch schema changes to minimize re-extraction cycles.
**Warning signs:** High LLM API costs after schema changes.

### Pitfall 5: 500-Line Limit on Converter Modules
**What goes wrong:** A single converter module grows beyond 500 lines.
**Why it happens:** Each field mapping involves SourcedValue construction, null checking, and type conversion. With 20+ fields, code grows fast.
**How to avoid:** Plan the split early. `llm_governance.py` handles board + leadership + compensation. If it grows too large, split into `llm_gov_board.py` and `llm_gov_comp.py`.
**Warning signs:** Module approaching 400 lines with more functions to add.

### Pitfall 6: External Source Merge Ordering
**What goes wrong:** LLM legal proceedings from Item 3 conflict with Stanford SCAC cases. A case appears twice because it came from both sources with slightly different names.
**Why it happens:** Different sources use different case name formats.
**How to avoid:** The merge must happen AFTER both LLM and SCAC extraction. Use `word_overlap_pct()` with a threshold (e.g., 0.6) to deduplicate. SCAC data enriches LLM cases (adds case_number, lead_counsel) rather than creating separate records.
**Warning signs:** Duplicate cases in the worksheet's litigation section.

### Pitfall 7: Missing "Not Disclosed" vs "Not Found" Distinction
**What goes wrong:** An LLM field returning `None` could mean either "the filing doesn't disclose this" or "the LLM failed to extract it."
**Why it happens:** LLM schemas use `None` for both missing data and extraction failure.
**How to avoid:** For critical fields, the LLM prompt should instruct "if the filing does not mention X, return null. If it explicitly states no X exists, return the appropriate absence indicator." Some fields like `has_clawback: bool | None` can distinguish: `None` = not mentioned, `False` = explicitly no clawback.
**Warning signs:** Fields that should be populated (e.g., say-on-pay for proxy filers) coming back null.

## Code Examples

### Example 1: Converting ExtractedDirector to BoardForensicProfile

```python
def convert_director(d: ExtractedDirector) -> BoardForensicProfile:
    """Convert LLM-extracted director to domain model."""
    profile = BoardForensicProfile()
    if d.name:
        profile.name = sourced_str(d.name, "DEF 14A (LLM)", Confidence.HIGH)
    if d.independent is not None:
        profile.is_independent = SourcedValue[bool](
            value=d.independent,
            source="DEF 14A (LLM)",
            confidence=Confidence.HIGH,
            as_of=now(),
        )
    if d.tenure_years is not None:
        profile.tenure_years = sourced_float(
            d.tenure_years, "DEF 14A (LLM)", Confidence.HIGH,
        )
    profile.committees = list(d.committees)
    for board_name in d.other_boards:
        profile.other_boards.append(
            sourced_str(board_name, "DEF 14A (LLM)", Confidence.HIGH)
        )
    profile.is_overboarded = (len(d.other_boards) + 1) >= 4
    return profile
```

### Example 2: Converting ExtractedLegalProceeding to CaseDetail

```python
def convert_legal_proceeding(proc: ExtractedLegalProceeding) -> CaseDetail:
    """Convert LLM-extracted legal proceeding to domain CaseDetail."""
    case = CaseDetail()
    source = "10-K (LLM)"

    if proc.case_name:
        case.case_name = sourced_str(proc.case_name, source, Confidence.HIGH)
    if proc.court:
        case.court = sourced_str(proc.court, source, Confidence.HIGH)
    if proc.filing_date:
        parsed = parse_date_str(proc.filing_date)
        if parsed:
            case.filing_date = SourcedValue[date](
                value=parsed, source=source,
                confidence=Confidence.HIGH, as_of=now(),
            )
    if proc.allegations:
        case.allegations.append(
            sourced_str(proc.allegations, source, Confidence.HIGH)
        )
        # Also infer legal theories from allegation text
        theories = detect_legal_theories(proc.allegations, source)
        case.legal_theories = theories
        case.coverage_type = SourcedValue[str](
            value=detect_coverage_type(theories).value,
            source=source, confidence=Confidence.HIGH, as_of=now(),
        )
    if proc.status:
        case.status = sourced_str(proc.status, source, Confidence.HIGH)
    if proc.settlement_amount is not None:
        case.settlement_amount = sourced_float(
            proc.settlement_amount, source, Confidence.HIGH,
        )
    if proc.class_period_start:
        parsed = parse_date_str(proc.class_period_start)
        if parsed:
            case.class_period_start = SourcedValue[date](
                value=parsed, source=source,
                confidence=Confidence.HIGH, as_of=now(),
            )
    if proc.class_period_end:
        parsed = parse_date_str(proc.class_period_end)
        if parsed:
            case.class_period_end = SourcedValue[date](
                value=parsed, source=source,
                confidence=Confidence.HIGH, as_of=now(),
            )
    return case
```

### Example 3: Sub-Orchestrator Integration Pattern

```python
def run_governance_extractors(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> GovernanceData:
    gov = GovernanceData()

    # Step 0: Pre-deserialize LLM result
    llm_def14a = get_llm_def14a(state)

    # Step 1: Board profiles -- LLM or regex
    if llm_def14a and llm_def14a.directors:
        profiles = [convert_director(d) for d in llm_def14a.directors]
        gov.board_forensics = profiles
        # Still compute governance score using existing scoring logic
        weights, thresholds = load_governance_weights()
        gov.governance_score = compute_governance_score(
            profiles, gov.comp_analysis, weights, thresholds,
        )
        reports.append(create_report(
            extractor_name="board_governance",
            expected=EXPECTED_FIELDS,
            found=["board_members", "independence", "committees", ...],
            source_filing="DEF 14A (LLM)",
        ))
    else:
        # Full regex fallback
        profiles, score = _run_board_governance(state, reports)
        gov.board_forensics = profiles
        gov.governance_score = score

    # ... remaining extractors with same pattern
    return gov
```

## Ground Truth Testing Strategy

### Test Company Selection

Choose companies with challenging/interesting governance and litigation disclosures:

| Company | Why Interesting for Governance | Why Interesting for Litigation |
|---------|-------------------------------|-------------------------------|
| TSLA | Dual CEO-Chair, activism risk, unusual board | Multiple active SCAs, SEC enforcement history |
| META | Board changes, proxy contests, high CEO pay | Privacy litigation, antitrust, FTC consent decree |
| AAPL | Strong governance baseline, say-on-pay | Reasonable litigation baseline |
| WFC | Material weakness history, CEO turnover | Extensive enforcement and class action history |
| COIN | Newer public company, crypto-specific risks | SEC enforcement action, novel legal theories |

**Recommendation:** Use TSLA (existing ground truth baseline, 93% extraction coverage) and 1-2 additional companies with different profiles.

### Test Strategy

1. **Unit tests for converter functions:** Test each `convert_*` function with hand-crafted LLM extraction dicts. Verify SourcedValue wrapping, confidence levels, and source strings. These tests are fast and deterministic.

2. **Integration tests with mock LLM results:** Create realistic DEF14AExtraction and TenKExtraction instances (or load from saved JSON), pass through the full converter pipeline, and verify the domain models are correctly populated.

3. **Field-level regression tests:** For each field in the domain model, verify:
   - When LLM provides the field: domain model gets HIGH confidence
   - When LLM returns null: regex fallback runs with MEDIUM/LOW confidence
   - When both are null: field remains None

4. **Ground truth validation (live API):** Run actual LLM extraction against real TSLA/AAPL/etc. filings. Compare every extracted field against hand-verified values from the actual SEC filing. This validates:
   - Extraction accuracy (did the LLM read the filing correctly?)
   - Conversion accuracy (did the converter map correctly?)
   - Completeness (did we get all the fields we expected?)

5. **Coverage regression test:** Run the full pipeline with LLM enabled and verify TSLA governance coverage >= 90% (up from <40%). This is the ultimate success metric.

### Test File Organization

```
tests/
  test_llm_governance_converter.py    -- Unit tests for llm_governance.py
  test_llm_litigation_converter.py    -- Unit tests for llm_litigation.py
  test_llm_governance_integration.py  -- Integration: LLM -> converter -> domain model
  test_llm_litigation_integration.py  -- Integration: LLM -> converter -> domain model
  test_llm_field_fallback.py          -- Field-level LLM/regex fallback behavior
```

### Ground Truth Fixture Pattern

```python
# fixtures/tsla_def14a_llm.json -- saved LLM extraction result
# fixtures/tsla_def14a_truth.json -- hand-verified field values

def test_tsla_governance_accuracy():
    """Verify LLM extraction matches hand-verified TSLA governance data."""
    llm_result = load_fixture("tsla_def14a_llm.json")
    truth = load_fixture("tsla_def14a_truth.json")

    extraction = DEF14AExtraction.model_validate(llm_result)
    profiles = [convert_director(d) for d in extraction.directors]

    assert len(profiles) == truth["board_size"]
    for profile in profiles:
        name = profile.name.value if profile.name else ""
        expected = truth["directors"].get(name, {})
        if "independent" in expected:
            assert profile.is_independent.value == expected["independent"]
```

## Integration Points with Existing Sub-Orchestrators

### extract_governance.py Changes

The `run_governance_extractors()` function (427 lines) is the integration point. Changes needed:

1. Import `get_llm_def14a` and converter functions
2. Pre-deserialize LLM result at top of function
3. For each extractor (_run_leadership, _run_compensation, _run_board_governance):
   - Check if LLM data can provide the result
   - If yes, use LLM converter + report
   - If no, fall back to existing regex extractor
4. For field-level fallback: after LLM conversion, check for null fields and run targeted regex

**Concern:** This file is 427 lines. Adding LLM integration logic could push it over 500. May need to split into `extract_governance.py` (orchestration) and `extract_governance_llm.py` (LLM-specific logic).

### extract_litigation.py Changes

The `run_litigation_extractors()` function (399 lines) is the integration point. Changes needed:

1. Import `get_llm_ten_k` and converter functions
2. Pre-deserialize LLM result at top of function
3. For SCA extraction: merge LLM Item 3 cases with EFTS/SCAC cases
4. For contingent liabilities: use LLM contingencies when available, regex fallback
5. For defense assessment: forum provisions come from LLM DEF14A (cross-domain)

**Concern:** This file is 399 lines. Similar risk of exceeding 500 lines.

### extract __init__.py (ExtractStage) Changes

No changes needed to the main extract stage. LLM extraction already runs as Phase 0 and stores results in `state.acquired_data.llm_extractions`. The sub-orchestrators consume the results.

## Risk Factor Storage Decision

Risk factors from `TenKExtraction.risk_factors` (list of `ExtractedRiskFactor`) need a home in the domain model. Currently there is no structured risk factor storage.

**Options evaluated:**

1. **Add to `LitigationLandscape`** -- Risk factors relate to litigation exposure but also governance and financial risks. Partial fit.

2. **Add to `ExtractedData`** as a new top-level field -- Clean separation but requires state model change. Simple Pydantic model addition.

3. **Add to `GovernanceData`** -- Some risk factors relate to governance but most don't. Poor fit.

4. **New `RiskFactorProfile` model** added to `ExtractedData` -- Best option. Create a simple model:

```python
class RiskFactorProfile(BaseModel):
    title: str
    category: str  # LITIGATION, REGULATORY, FINANCIAL, CYBER, ESG, AI, OTHER
    severity: str  # HIGH, MEDIUM, LOW
    is_new_this_year: bool = False
    do_relevance: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    source_passage: str = ""
    source: str = ""
```

**Recommendation:** Option 4. Add `risk_factors: list[RiskFactorProfile]` to `ExtractedData`. It's the cleanest fit since risk factors are extracted data that span domains.

## Scope Recommendation: Phase 19 vs Phase 20

Based on complexity and dependency analysis:

### Phase 19 (this phase)
1. **Converter infrastructure** -- `llm_governance.py`, `llm_litigation.py`
2. **DEF 14A governance** -- Directors, board profile, CEO/chair, independence
3. **DEF 14A compensation** -- NEO comp, pay ratio, say-on-pay, golden parachute
4. **10-K Item 3 litigation** -- Legal proceedings with full field mapping
5. **10-K contingent liabilities** -- Schema expansion + converter
6. **Sub-orchestrator integration** -- LLM-first with regex fallback
7. **Schema expansions** -- ExtractedContingency, clawback fields, legal_theories

### Phase 20 (next phase)
1. **Risk factors** -- Full Item 1A risk factor extraction and categorization
2. **External source merge** -- Stanford SCAC + LLM case merging
3. **Cross-domain enrichment** -- Forum provisions from DEF 14A to defense assessment
4. **Ground truth validation suite** -- Live API tests against real filings
5. **Coverage regression tests** -- 90%+ target verification

**Rationale:** Phase 19 focuses on the core converter + integration pattern for the two most impactful sections (board governance and Item 3 litigation). Phase 20 extends to risk factors and handles the more complex merge/cross-domain work.

## Open Questions

1. **Board aggregate fields dual-write:** Should LLM data populate BOTH `BoardProfile` (Phase 3 aggregate) AND `BoardForensicProfile` list (Phase 4 forensic)? Currently `BoardProfile` holds aggregate metrics (size, independence_ratio) while `BoardForensicProfile` list holds individual director data. LLM can populate both -- likely yes, populate both for completeness.

2. **NEO-to-Leadership matching:** The LLM extracts named executive officers (NEOs) from the Summary Compensation Table. The regex extractor finds C-suite executives from proxy text. These are partially overlapping sets. Should LLM NEOs replace regex executives entirely, or should they merge? NEOs have compensation data but may not include all C-suite (e.g., General Counsel might not be an NEO). Recommendation: LLM NEOs supplement -- add any NEO not already found by leadership parsing.

3. **Risk factor model location:** The recommendation above puts it on `ExtractedData`. But the planner should confirm this is acceptable given the state model structure. The alternative (putting it on `LitigationLandscape`) avoids adding to the top-level state.

## Sources

### Primary (HIGH confidence)
- All findings from direct codebase analysis of files listed in this document
- Phase 18 schema files: `src/do_uw/stages/extract/llm/schemas/`
- Domain models: `src/do_uw/models/governance.py`, `governance_forensics.py`, `litigation.py`, `litigation_details.py`
- Regex extractors: `board_governance.py`, `compensation_analysis.py`, `leadership_profiles.py`, `leadership_parsing.py`, `sca_extractor.py`, `contingent_liab.py`, `defense_assessment.py`
- Sub-orchestrators: `extract_governance.py`, `extract_litigation.py`
- Pipeline integration: `stages/extract/__init__.py`
- State model: `models/state.py`
- LLM infrastructure: `llm/extractor.py`, `llm/prompts.py`, `llm/schemas/__init__.py`

### Secondary (MEDIUM confidence)
- None needed -- all research based on codebase analysis

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Field mapping analysis: HIGH -- direct comparison of schema and model fields
- Converter patterns: HIGH -- follows established sourced.py patterns
- Schema expansion needs: HIGH -- gap analysis from field comparison
- Integration patterns: HIGH -- based on existing sub-orchestrator structure
- Test strategy: HIGH -- follows existing test patterns in the codebase
- Scope split: MEDIUM -- depends on actual implementation complexity

**Research date:** 2026-02-10
**Valid until:** Indefinite (internal codebase analysis, not dependent on external changes)
