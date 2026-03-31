# Phase 20: LLM Extraction -- Full Coverage - Research

**Researched:** 2026-02-10
**Domain:** LLM extraction converter modules, schema consumption, regex-to-LLM migration across all filing sections
**Confidence:** HIGH (all findings from direct codebase analysis of 30+ files)

## Summary

Phase 20 extends the Phase 19 LLM-first/regex-fallback pattern to ALL remaining filing sections: Item 1 (Business), Item 7 (MD&A), Item 8 Footnotes, Item 9A (Controls), 8-K Events, DEF 14A Ownership, and AI Risk. The proven architecture from Phase 19 (llm_helpers.py deserialization, converter modules with SourcedValue wrapping, sub-orchestrator integration) is applied identically -- no new infrastructure is needed.

The TenKExtraction schema (289 lines) already has fields for all seven target areas: `business_description`, `revenue_segments`, `geographic_regions`, `customer_concentration`, `supplier_concentration`, `competitive_position`, `regulatory_environment`, `is_dual_class`, `has_vie` (Item 1); `revenue_trend`, `margin_trend`, `key_financial_concerns`, `critical_accounting_estimates`, `guidance_language`, `non_gaap_measures` (Item 7); `debt_instruments`, `credit_facility_detail`, `covenant_status`, `tax_rate_notes`, `stock_comp_detail` (Item 8 Footnotes); `has_material_weakness`, `material_weakness_detail`, `significant_deficiencies`, `remediation_status`, `auditor_attestation` (Item 9A). The EightKExtraction (153 lines) covers departures, agreements, acquisitions, restatements. DEF14AExtraction (204 lines) has `officers_directors_ownership_pct`, `top_5_holders`, and all ownership fields. These schemas are already being extracted by the LLM in Phase 0 -- the data is sitting in `state.acquired_data.llm_extractions` but is NOT yet consumed by converters for these sections.

The core work is three new converter modules grouped by filing type, plus modifications to four existing sub-orchestrators/extractors. The 500-line limit will require careful file organization. Ground truth expansion adds 20+ new fields verified against actual TSLA/AAPL filings.

**Primary recommendation:** Build `ten_k_converters.py` (Items 1/7/8/9A converters), `eight_k_converter.py` (departure/agreement/acquisition/restatement converters), and `proxy_ownership_converter.py` (ownership table converter). Integrate into `company_profile.py`, `debt_analysis.py`/`debt_text_parsing.py`, `audit_risk.py`, `extract_market.py`/`extract_ai_risk.py`, and `ownership_structure.py`. Expand ground truth fixtures.

## Standard Stack

No new dependencies. Phase 20 uses exclusively the established project stack from Phases 18-19.

### Core
| Library | Version | Purpose | Why Used |
|---------|---------|---------|----------|
| pydantic | v2 | Domain models + LLM schemas | Already established |
| anthropic | existing | LLM API (Phase 18) | Already installed |
| instructor | existing | Structured output (Phase 18) | Already installed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | existing | Unit + integration tests | Converter validation |
| ruff | existing | Linting | Code quality |
| pyright | strict | Type checking | All new code |

## Architecture Patterns

### Pattern 1: Converter Module by Filing Type (CONTEXT.md Decision)

Per the user's locked decision, converters are grouped by filing type, NOT by domain area:

```
src/do_uw/stages/extract/
  ten_k_converters.py         -- Items 1, 7, 8 footnotes, 9A converters
  eight_k_converter.py        -- Executive departures, material agreements, acquisitions, restatements
  proxy_ownership_converter.py -- DEF 14A ownership tables, 5% holders
```

Each follows the established Phase 19 converter pattern:
- Import the LLM schema model (TenKExtraction, EightKExtraction, DEF14AExtraction)
- Map flat LLM fields to domain model fields wrapped in SourcedValue
- Use `Confidence.HIGH` and `"<filing_type> (LLM)"` source strings
- Use `sourced_str()`, `sourced_float()`, `sourced_int()` from `sourced.py`

### Pattern 2: Reuse Existing llm_helpers.py Deserialization

The `get_llm_ten_k(state)`, `get_llm_def14a(state)` helpers from Phase 19 are exactly what Phase 20 needs. A new `get_llm_eight_k(state)` function is needed for 8-K extraction.

```python
# Add to llm_helpers.py
from do_uw.stages.extract.llm.schemas import EightKExtraction

def get_llm_eight_k(state: AnalysisState) -> list[EightKExtraction]:
    """Deserialize ALL LLM 8-K extractions from state.

    Unlike 10-K and DEF 14A (single filing), multiple 8-Ks
    may exist. Returns a list of typed extractions.
    """
    if state.acquired_data is None:
        return []
    results: list[EightKExtraction] = []
    for key, data in state.acquired_data.llm_extractions.items():
        if key.startswith("8-K:") and isinstance(data, dict):
            try:
                results.append(EightKExtraction.model_validate(data))
            except Exception:
                logger.warning("Failed to deserialize 8-K: %s", key, exc_info=True)
    return results
```

**Key difference for 8-K:** Multiple 8-Ks exist (companies file many per year), so the helper returns a `list` not a single result. Each 8-K covers different events.

### Pattern 3: LLM-First with Existing-Data Preservation

The integration pattern differs by section because of how data flows:

**Replace pattern** (LLM replaces regex when present):
- Item 1 business description, revenue segments, geographic footprint, concentration
- Item 7 MD&A fields (revenue_trend, margin_trend, guidance_language, non_gaap_measures)
- Item 9A material weakness details, remediation status
- DEF 14A ownership percentages and top holders

**Supplement pattern** (LLM adds to richer existing data):
- Item 8 debt instruments supplement XBRL-derived debt analysis
- 8-K events supplement the existing 8-K-based business changes detection
- AI risk LLM data supplements keyword-based disclosure analysis

**XBRL-always-wins pattern** (LLM never overrides XBRL):
- Financial ratios (liquidity, leverage) always from XBRL
- Revenue/net income/total assets from XBRL
- LLM provides qualitative context (trends, concerns) but never overrides numbers

### Pattern 4: Sub-Orchestrator Integration Points

Each existing sub-orchestrator needs modification:

| Sub-Orchestrator | Current Lines | LLM Integration Approach |
|------------------|---------------|--------------------------|
| `company_profile.py` | 483 | Add LLM Item 1 fields at top of `extract_company_profile()`. Near 500-line limit -- may need to extract Item 1 helpers. |
| `debt_analysis.py` | 469 | Add LLM Item 8 footnote fields (debt instruments, credit facility, covenants). Near limit. |
| `debt_text_parsing.py` | ~400 | Receives LLM-extracted debt data as supplement to text parsing. |
| `audit_risk.py` | 478 | Add LLM Item 9A fields (material weakness detail, remediation, auditor attestation). Near limit. |
| `extract_market.py` | 254 | Add LLM 8-K event extraction. Room available. |
| `extract_ai_risk.py` | 150 | Add LLM AI disclosure supplement from Item 1A risk factors. Room available. |
| `ownership_structure.py` | 442 | Add LLM DEF 14A top holders and ownership table. Near limit. |
| `extract_governance.py` | 348 | Already done in Phase 19. No changes needed. |
| `extract_litigation.py` | 474 | Already done in Phase 19. No changes needed. |

**Line count concern:** Four files (company_profile, debt_analysis, audit_risk, ownership_structure) are near 450-480 lines. Adding LLM integration code (typically 30-60 lines per section) will push some over 500 lines. Plan splits proactively:
- `company_profile.py`: Extract text-based segment/complexity helpers to `profile_item1_helpers.py` if needed
- `debt_analysis.py`: Debt text parsing is already split out; LLM integration can go in the main file if careful
- `audit_risk.py`: Could extract going concern/MW regex helpers to separate file
- `ownership_structure.py`: Could extract dual-class regex logic to separate file

### Pattern 5: 8-K Multi-Event Aggregation

8-K extraction is unique because:
1. Multiple 8-Ks exist per company per year
2. Each 8-K covers one or a few Items (not comprehensive like 10-K)
3. Events need to be aggregated across 8-Ks into domain model fields

The converter must aggregate across all 8-K extractions:

```python
def aggregate_eight_k_events(
    extractions: list[EightKExtraction],
) -> EightKEventSummary:
    """Aggregate events from multiple 8-K filings."""
    departures: list[ExecutiveDeparture] = []
    agreements: list[MaterialAgreement] = []
    acquisitions: list[CorporateTransaction] = []
    restatements: list[RestatementNotice] = []

    for ext in extractions:
        if ext.departing_officer:
            departures.append(_convert_departure(ext))
        if ext.agreement_type:
            agreements.append(_convert_agreement(ext))
        if ext.transaction_type:
            acquisitions.append(_convert_acquisition(ext))
        if ext.restatement_periods:
            restatements.append(_convert_restatement(ext))

    return EightKEventSummary(
        departures=departures,
        agreements=agreements,
        acquisitions=acquisitions,
        restatements=restatements,
    )
```

**Domain model target:** 8-K events map to multiple domain areas:
- Departures -> `LeadershipForensicProfile` stability indicators (governance)
- Restatements -> `AuditRisk` restatement flags (financials)
- Agreements/Acquisitions -> `CompanyProfile.business_changes` (company profile)
- All events -> `MarketSignals.capital_markets` and event timeline

### Anti-Patterns to Avoid
- **LLM overriding XBRL numbers:** LLM supplements with qualitative context. XBRL revenue, assets, debt values are authoritative.
- **Re-deserializing per extractor:** Reuse `get_llm_ten_k()` from llm_helpers.py. Called once in each sub-orchestrator.
- **Converting 8-K as single filing:** 8-K is multi-instance. Must iterate and aggregate.
- **Duplicating converter logic from Phase 19:** Import and reuse `_sourced_bool`, `_parse_date`, etc. from `llm_governance.py` and `llm_litigation.py` -- or extract shared utilities to `llm_helpers.py`.

## Field Mapping Analysis

### TenKExtraction -> CompanyProfile (Item 1: Business)

| LLM Schema Field | Domain Model Target | Replace/Supplement | Notes |
|-------------------|---------------------|-------------------|-------|
| `business_description` | `CompanyProfile.business_description` | Replace (if richer than regex) | LLM provides 2-3 sentence summary vs raw text truncation |
| `revenue_segments` | `CompanyProfile.revenue_segments` | Supplement (XBRL primary) | Only if XBRL segments not found |
| `geographic_regions` | `CompanyProfile.geographic_footprint` | Replace (regex weak here) | LLM reads actual geo tables |
| `customer_concentration` | `CompanyProfile.customer_concentration` | Replace | LLM extracts "Customer A is 15% of revenue" |
| `supplier_concentration` | `CompanyProfile.supplier_concentration` | Replace | Regex misses most of these |
| `competitive_position` | Not in profile; could add | New field | Useful for underwriter context |
| `regulatory_environment` | Not in profile; could add | New field | Maps to regulatory risk |
| `employee_count` | `CompanyProfile.employee_count` | Supplement (yfinance primary) | Cross-validates yfinance |
| `is_dual_class` | `CompanyProfile.operational_complexity` has_dual_class | Supplement | Cross-validates regex |
| `has_vie` | `CompanyProfile.operational_complexity` has_vie | Supplement | Cross-validates regex |

### TenKExtraction -> ExtractedFinancials (Item 7: MD&A)

| LLM Schema Field | Domain Model Target | Replace/Supplement | Notes |
|-------------------|---------------------|-------------------|-------|
| `revenue_trend` | New: qualitative context for `financial_health_narrative` | Supplement | Enhances narrative, never overrides XBRL |
| `margin_trend` | New: qualitative context | Supplement | LLM reads MD&A margin discussion |
| `key_financial_concerns` | New: risk context | Supplement | Maps to distress/risk factors |
| `critical_accounting_estimates` | New: audit risk context | Supplement | CAEs are a key D&O risk signal |
| `guidance_language` | `MarketSignals.earnings_guidance` | Supplement | LLM captures guidance nuance |
| `non_gaap_measures` | New: disclosure risk | Supplement | Non-GAAP usage is an SCA trigger |

### TenKExtraction -> ExtractedFinancials (Item 8 Footnotes)

| LLM Schema Field | Domain Model Target | Replace/Supplement | Notes |
|-------------------|---------------------|-------------------|-------|
| `debt_instruments` | `debt_structure` dict | Supplement | LLM reads footnote tables; regex parses text |
| `credit_facility_detail` | `debt_structure.credit_facility` | Supplement | LLM captures facility terms |
| `covenant_status` | `debt_structure.covenants` | Replace (regex rarely finds this) | Critical D&O signal |
| `tax_rate_notes` | `tax_indicators` | Supplement | LLM captures effective rate discussion |
| `stock_comp_detail` | New: compensation context | Supplement | Useful for comp analysis enrichment |
| `going_concern` / `going_concern_detail` | `AuditRisk.going_concern` | Supplement | Cross-validates existing regex |
| `material_weaknesses` (Item 8) | `AuditRisk.material_weaknesses` | Supplement | Overlaps with Item 9A extraction |
| `contingent_liabilities` | Already handled in Phase 19 | N/A | Already wired |

### TenKExtraction -> AuditRisk (Item 9A: Controls)

| LLM Schema Field | Domain Model Target | Replace/Supplement | Notes |
|-------------------|---------------------|-------------------|-------|
| `has_material_weakness` | `AuditRisk.has_material_weakness` | Replace | Boolean flag more reliable from LLM |
| `material_weakness_detail` | `AuditRisk.material_weaknesses` list | Replace | LLM captures actual MW descriptions |
| `significant_deficiencies` | New field on AuditRisk | New | Currently not tracked; high D&O relevance |
| `remediation_status` | New field on AuditRisk | New | Critical for underwriter assessment |
| `auditor_attestation` | `AuditRisk.audit_opinion_type` | Supplement | Enriches opinion with attestation detail |
| `auditor_name` | `AuditRisk.auditor_name` | Supplement | Cross-validates existing extraction |
| `auditor_tenure_years` | `AuditRisk.auditor_tenure_years` | Supplement | Cross-validates |

### EightKExtraction -> Multiple Domain Areas

| LLM Schema Field | Domain Model Target | Notes |
|-------------------|---------------------|-------|
| `departing_officer`, `departure_reason`, `successor`, `is_termination` | `LeadershipStability` in governance | Executive departure events |
| `agreement_type`, `counterparty`, `agreement_summary` | `CompanyProfile.business_changes` | Material agreements (M&A, licensing) |
| `transaction_type`, `target_name`, `transaction_value` | `CompanyProfile.business_changes` + `CapitalMarketsActivity` | Acquisitions/dispositions |
| `restatement_periods`, `restatement_reason` | `AuditRisk` restatement flags | Highest-severity D&O event |
| `revenue`, `eps`, `guidance_update` | `EarningsGuidanceAnalysis` | Earnings events |
| `event_description` | Event timeline | Other material events |

### DEF14AExtraction -> OwnershipAnalysis

| LLM Schema Field | Domain Model Target | Replace/Supplement | Notes |
|-------------------|---------------------|-------------------|-------|
| `officers_directors_ownership_pct` | `OwnershipAnalysis.insider_pct` | Already partially wired in Phase 19 | Phase 20 expands |
| `top_5_holders` | `OwnershipAnalysis.top_holders` | Supplement | LLM parses proxy ownership table |

## Schema Analysis: What's Already Extracted vs What's Consumed

**Key insight:** The LLM schemas from Phase 18 were designed comprehensively. The TenKExtraction already has fields for ALL seven target areas. The data is already being extracted in Phase 0 (the `_run_llm_extraction` function in `__init__.py`). Phase 20's job is purely to BUILD CONVERTERS that consume this data.

**Schema gap analysis:**

| Filing Type | Schema Completeness for Phase 20 | Gaps |
|-------------|----------------------------------|------|
| TenKExtraction | 95% complete | May want `segment_performance` structured list for MD&A instead of free-text `revenue_trend` |
| EightKExtraction | 90% complete | Missing `departing_officer_title` (useful for severity assessment) |
| DEF14AExtraction | 100% complete for ownership | No gaps |

**Recommendation:** Add one field to EightKExtraction:
```python
departing_officer_title: str | None = Field(
    default=None,
    description="Title of the departing officer, e.g. 'Chief Financial Officer'",
)
```

This is a minor schema expansion that enables better departure severity classification (CEO/CFO departure vs VP departure).

**Schema hash impact:** Any field addition to schemas invalidates cached LLM extraction results. Per Phase 18 decision, this is by design. Batch all schema changes in one plan to minimize re-extraction cycles. Phase 20 should make all schema changes in the first plan, then build converters in subsequent plans.

## Domain Model Expansion Needs

### AuditRisk Model

Current `AuditRisk` model in `audit_risk.py` needs two new fields:
```python
significant_deficiencies: list[str] = Field(
    default_factory=lambda: [],
    description="Significant deficiencies in internal controls",
)
remediation_status: str | None = Field(
    default=None,
    description="Status of remediation for control deficiencies",
)
```

These are important D&O risk signals currently not tracked.

### CompanyProfile Model

Current `CompanyProfile` may benefit from optional fields:
```python
competitive_position_summary: SourcedValue[str] | None = None
regulatory_environment_summary: SourcedValue[str] | None = None
```

But these could also be stored in the existing `section_summary` or `business_description`. Recommendation: Use existing fields -- `business_description` for Item 1 context, and add to `do_exposure_factors` for regulatory context.

### No New Domain Models Needed

Phase 20 maps LLM data to EXISTING domain model fields. The only model additions are 2 fields on AuditRisk. This is by design -- the domain models from Phases 3-5 were designed to hold this data, they just weren't getting it reliably from regex.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SourcedValue construction | Inline construction | `sourced_str()`, `sourced_float()`, `sourced_int()` from `sourced.py` | Consistency, tested |
| Date parsing | Custom parser | `_parse_date()` from `llm_litigation.py` | Already handles formats |
| LLM deserialization | New accessor | `get_llm_ten_k()`, `get_llm_def14a()` from `llm_helpers.py` | DRY, tested |
| Debt instrument parsing | New parser | Existing `debt_text_parsing.py` for regex fallback | Already handles patterns |
| Dual-class detection | New logic | Existing `extract_dual_class()` in `ownership_structure.py` | LLM supplements, regex fallback |
| Governance scoring recalc | New scorer | `compute_governance_score()` in `board_governance.py` | Already works with profiles |
| ExtractionReport generation | Custom | `_add_llm_report()` from Phase 19's `extract_governance.py` | Reusable pattern |
| Filing section extraction | Custom parser | `extract_section()` from `filing_sections.py` | For regex fallback paths |
| Cost budget management | Custom tracker | `CostTracker` in `llm/cost_tracker.py` | Already enforces budget |

## Common Pitfalls

### Pitfall 1: Near-500-Line Files Getting Pushed Over
**What goes wrong:** Adding LLM integration code to files already at 450-480 lines pushes them over 500.
**Why it happens:** company_profile.py (483), debt_analysis.py (469), audit_risk.py (478), ownership_structure.py (442) are all near the limit.
**How to avoid:** Plan splits BEFORE adding code. Extract regex helper functions to companion files. The narrative helpers pattern from Phase 19 (`governance_narrative.py`) is the template.
**Warning signs:** Any file over 440 lines before LLM code is added.

### Pitfall 2: LLM Overriding XBRL Financial Data
**What goes wrong:** LLM-extracted revenue/debt/asset numbers replace XBRL values, introducing inaccuracy.
**Why it happens:** The TenKExtraction has some numeric fields (employee_count, share_repurchase_amount). Carelessly mapping these could override XBRL.
**How to avoid:** Clear rule: XBRL always wins for financial numbers. LLM fields like `revenue_trend`, `margin_trend` are QUALITATIVE supplements. Never map LLM `revenue` to financial statement line items. Only map LLM numbers that don't have XBRL equivalents (employee_count from Item 1, which supplements yfinance).
**Warning signs:** Financial values changing when LLM is enabled vs disabled.

### Pitfall 3: 8-K Multi-Filing Aggregation Confusion
**What goes wrong:** Converting 8-K data as if there's one 8-K (like 10-K), missing events from other 8-Ks.
**Why it happens:** `get_llm_ten_k()` returns a single result. Developers might expect the same for 8-K.
**How to avoid:** `get_llm_eight_k()` must return `list[EightKExtraction]`. The converter iterates all 8-Ks and aggregates. Each 8-K typically covers a single event type.
**Warning signs:** Only the first 8-K's events appearing in the domain model.

### Pitfall 4: Stale Schema Hash from Minor Field Additions
**What goes wrong:** Adding `departing_officer_title` to EightKExtraction changes the schema hash, forcing all 8-K LLM extractions to re-run and costing money.
**Why it happens:** `schema_hash()` includes every field in the JSON schema.
**How to avoid:** Batch ALL schema changes into one plan (the first plan). After that plan, all subsequent plans only build converters and don't touch schemas.
**Warning signs:** Multiple schema changes across different plans causing multiple cache invalidation cycles.

### Pitfall 5: FPI (Foreign Private Issuer) Edge Cases
**What goes wrong:** 20-F filings lack some 10-K-specific fields (e.g., Item 9A for some FPI companies). The converter assumes all fields exist.
**Why it happens:** `get_llm_ten_k()` already falls back to 20-F key prefix. But the 20-F content may differ.
**How to avoid:** All converter functions already handle `None` fields gracefully (Phase 19 pattern). FPI-specific schema mapping is already handled: 20-F reuses TenKExtraction. Just ensure converters don't fail on missing fields.
**Warning signs:** Crashes when processing FPI companies.

### Pitfall 6: Ground Truth Verification Against Wrong Filing Period
**What goes wrong:** Ground truth values are for FY2025 but LLM extracts FY2024 data because the cached state was from an older run.
**Why it happens:** Ground truth is period-specific. LLM extracts whatever filing is in the filing_documents.
**How to avoid:** Use `fiscal_year_end` and `period_of_report` fields from TenKExtraction to verify the extracted period matches ground truth expectations. Tests should assert the period, not just the values.
**Warning signs:** Financial ground truth values close but not matching -- probably a year off.

### Pitfall 7: Duplicate 8-K Event Data
**What goes wrong:** An executive departure appears twice because it came from both an 8-K and the DEF 14A.
**Why it happens:** 8-K Item 5.02 announces departure; DEF 14A mentions new leadership. Both converters create entries.
**How to avoid:** 8-K departures supplement leadership data. Deduplicate by name when merging with governance leadership profiles. Use the same name-matching pattern from Phase 19 (case-insensitive, existing_names set).
**Warning signs:** Duplicate executive entries in the leadership section.

## Converter Module Design

### `ten_k_converters.py` (new file, target <500 lines)

Responsibilities:
1. Convert `business_description` -> `CompanyProfile.business_description` (SourcedValue[str])
2. Convert `revenue_segments` -> `CompanyProfile.revenue_segments` (list of segment dicts)
3. Convert `geographic_regions` -> `CompanyProfile.geographic_footprint` (list of region entries)
4. Convert `customer_concentration` / `supplier_concentration` -> profile fields
5. Convert `is_dual_class` / `has_vie` -> operational complexity flags
6. Convert `revenue_trend`, `margin_trend`, `key_financial_concerns` -> narrative enrichment data
7. Convert `critical_accounting_estimates`, `non_gaap_measures` -> risk context lists
8. Convert `guidance_language` -> earnings guidance supplement
9. Convert `debt_instruments`, `credit_facility_detail`, `covenant_status` -> debt structure enrichment
10. Convert `tax_rate_notes` -> tax indicator supplement
11. Convert `has_material_weakness`, `material_weakness_detail`, `significant_deficiencies`, `remediation_status`, `auditor_attestation` -> AuditRisk enrichment

Key functions:
```python
def convert_item1_business(extraction: TenKExtraction) -> Item1BusinessData
def convert_item7_mda(extraction: TenKExtraction) -> Item7MDAData
def convert_item8_footnotes(extraction: TenKExtraction) -> Item8FootnoteData
def convert_item9a_controls(extraction: TenKExtraction) -> Item9AControlData
```

Where each returns a lightweight typed data container (namedtuple or dataclass) consumed by the sub-orchestrator. Or, if simpler, returns dicts/SourcedValues directly.

**Line count risk:** 10+ conversion functions with SourcedValue wrapping could exceed 500 lines. Mitigation: split into `ten_k_converters.py` (Items 1 + 7, ~250 lines) and `ten_k_converters_financial.py` (Items 8 + 9A, ~250 lines) if needed.

### `eight_k_converter.py` (new file, target <300 lines)

Responsibilities:
1. Aggregate departures from multiple 8-K extractions
2. Aggregate material agreements
3. Aggregate acquisitions/dispositions
4. Aggregate restatement notices
5. Map earnings events to guidance updates

Key functions:
```python
def get_llm_eight_k(state: AnalysisState) -> list[EightKExtraction]  # in llm_helpers.py
def convert_departures(extractions: list[EightKExtraction]) -> list[DepartureEvent]
def convert_agreements(extractions: list[EightKExtraction]) -> list[MaterialAgreement]
def convert_acquisitions(extractions: list[EightKExtraction]) -> list[CorporateTransaction]
def convert_restatements(extractions: list[EightKExtraction]) -> list[RestatementNotice]
```

**Simpler approach:** Since these map to existing domain model fields scattered across governance, financials, and company profile, the converter could return a single `EightKSummary` dataclass that the various sub-orchestrators consume.

### `proxy_ownership_converter.py` (new file, target <200 lines)

Responsibilities:
1. Parse `top_5_holders` strings (format: "Vanguard Group: 8.2%") into structured holder records
2. Map `officers_directors_ownership_pct` to `OwnershipAnalysis.insider_pct` (already partial in Phase 19)
3. Extract individual officer/director share counts if available from DEF 14A

Key functions:
```python
def convert_top_holders(extraction: DEF14AExtraction) -> list[SourcedValue[dict[str, Any]]]
def convert_proxy_ownership(extraction: DEF14AExtraction) -> OwnershipAnalysis
```

## AI Risk Integration Approach (Claude's Discretion)

**Recommendation: Same LLM pattern, multi-source integration.**

AI risk extraction currently uses three independent sources:
1. `ai_disclosure_extract.py` -- keyword counting in Item 1A text (regex-based)
2. `ai_patent_extract.py` -- USPTO API patent search
3. `ai_competitive_extract.py` -- peer comparison from filing mentions

The LLM TenKExtraction already captures AI-relevant data:
- `risk_factors` with category "AI" (already consumed in Phase 19 for risk factor profiles)
- Business description mentions of AI capabilities
- Item 1A risk factors about AI disruption

**Integration approach:**
1. Use LLM risk factors with `category == "AI"` to supplement `AIDisclosureData.risk_factors` (richer than keyword snippets)
2. Use LLM `mention_count` from risk factors to cross-validate keyword counting
3. Patent data and competitive position remain non-LLM (they use structured APIs)
4. The AI risk sub-orchestrator (`extract_ai_risk.py` at 150 lines) has plenty of room for LLM integration

**No special-case treatment needed.** The LLM pattern applies cleanly. AI risk is just another consumer of TenKExtraction risk_factors.

## LLM + Regex Merging Strategy (Claude's Discretion)

**Recommendation: Per-section authoritative LLM with field-level regex backfill.**

| Section | Strategy | Rationale |
|---------|----------|-----------|
| Item 1 Business | LLM authoritative | LLM produces richer, more coherent business summaries than regex truncation |
| Item 1 Segments | XBRL primary, LLM fallback | XBRL segment data is audited; LLM only fills when XBRL is empty |
| Item 7 MD&A | LLM authoritative for qualitative | No regex equivalent for trends/concerns; LLM is the only source |
| Item 8 Footnotes | Mixed | Debt instruments from LLM; financial ratios from XBRL always |
| Item 9A Controls | LLM authoritative | Material weakness detail/remediation nearly impossible via regex |
| 8-K Events | LLM authoritative | Regex only detects 8-K filing existence, not event content |
| DEF 14A Ownership | LLM authoritative for table data | Regex struggles with proxy ownership tables |
| AI Risk | LLM supplement | Keyword counting remains primary; LLM enriches with categorized factors |

## Large Filing Handling (Claude's Discretion)

**Recommendation: Section-based chunking via filing_sections.py for oversized filings.**

Current behavior: `LLMExtractor.extract()` sends the ENTIRE filing to Claude Haiku 4.5 (200k context). `strip_boilerplate()` removes signatures, XBRL tags, certifications. `MAX_INPUT_TOKEN_ESTIMATE = 190_000` rejects filings exceeding this.

For Phase 20 specifically:
- 10-K filings are sent as complete documents (typically 50k-150k tokens after stripping) -- this works
- 8-K filings are small (1k-5k tokens) -- no issue
- DEF 14A proxy statements can be large (20k-100k tokens) -- usually fits

**Edge case:** Very large 10-K filings (bank 10-Ks can exceed 200k tokens even after stripping) may be rejected by the token limit check. For these:
1. First attempt: send complete filing (current behavior)
2. If too large: use `extract_section()` from `filing_sections.py` to extract only Items 1, 1A, 3, 7, 8, 9A and send those concatenated
3. This section-based chunking is already available in the codebase

**Implementation note:** This is a modification to `_run_llm_extraction()` in `__init__.py`, not to the converters. Can be deferred if it's not hitting real filings.

## Cost Tracking Granularity (Claude's Discretion)

**Recommendation: Per-filing-type cost tracking (current behavior is sufficient).**

Current `CostTracker` tracks total across all filings. The log output already shows per-extraction cost:
```
LLM extraction complete for <accession> (<form_type>): ~<N> input tokens, $<cost>
```

For Phase 20 with $2.00 budget:
- Typical 10-K extraction: ~$0.15-0.30 (50-100k input tokens)
- Typical DEF 14A: ~$0.05-0.15 (20-50k input tokens)
- Typical 8-K: ~$0.01-0.02 (1-5k input tokens)
- Total for ~10 filings: ~$0.50-1.00

The $2.00 budget provides comfortable headroom. Per-section cost tracking within the 10-K is unnecessary -- the LLM makes one call per filing type anyway (Phase 18 design decision: "One model, one API call").

**Update needed:** Change the default `budget_usd` from `1.0` to `2.0` in `LLMExtractor.__init__()` per CONTEXT.md decision.

## --no-llm Degradation Strategy (Claude's Discretion)

**Recommendation: Debugging-only degradation with clear documentation.**

When `--no-llm` is set:
1. `_run_llm_extraction()` returns empty dict
2. All `get_llm_ten_k()` / `get_llm_def14a()` / `get_llm_eight_k()` return None/empty
3. Every sub-orchestrator falls back to regex extractors
4. The worksheet will have coverage gaps (per CONTEXT.md: "debugging use -- worksheet will have gaps")

**No additional work needed.** The LLM-first/regex-fallback pattern inherently handles this. When LLM returns None, every converter check (`if llm_ten_k and llm_ten_k.field:`) fails and regex runs.

**Documentation note:** Add a log warning when `--no-llm` is active:
```
WARNING: LLM extraction disabled. Worksheet will have reduced coverage in Items 1, 7, 8, 9A, 8-K events, and ownership sections.
```

## Ground Truth Expansion Plan

### New Fields to Verify (20+ per CONTEXT.md decision)

| Category | Field | TSLA Expected | AAPL Expected | Source |
|----------|-------|---------------|---------------|--------|
| Item 1 | employee_count | ~140,000 | ~164,000 | 10-K Item 1 |
| Item 1 | is_dual_class | False | False | 10-K / proxy |
| Item 1 | has_vie | False | False | 10-K footnotes |
| Item 1 | customer_concentration_exists | False (no 10%+ customer) | False | 10-K Item 1 |
| Item 7 | non_gaap_count | 3-5 | 2-4 | 10-K Item 7 |
| Item 7 | has_critical_accounting_estimates | True | True | 10-K Item 7 |
| Item 8 | has_going_concern | False | False | 10-K Item 8 |
| Item 8 | debt_instruments_count | 3-5 | 4-6 | 10-K footnotes |
| Item 8 | covenant_status_disclosed | True | True | 10-K footnotes |
| Item 9A | has_material_weakness | False | False | 10-K Item 9A |
| Item 9A | auditor_name | PricewaterhouseCoopers | Ernst & Young | 10-K Part IV |
| Item 9A | auditor_opinion | unqualified | unqualified | 10-K Item 8 |
| 8-K | recent_cfo_departure | False | False | 8-K filings |
| 8-K | has_restatement_24mo | False | False | 8-K filings |
| 8-K | recent_acquisition_disclosed | Verify | Verify | 8-K filings |
| Ownership | insider_ownership_pct | ~21% (Musk) | <1% | DEF 14A |
| Ownership | top_holder_name | Elon Musk / Vanguard | Vanguard | DEF 14A |
| Risk Factors | total_risk_factors | 20-30 | 25-35 | 10-K Item 1A |
| Risk Factors | has_ai_risk_factor | True | True | 10-K Item 1A |
| Risk Factors | has_cyber_risk_factor | True | True | 10-K Item 1A |
| Risk Factors | new_risk_factors_count | 2-8 | 2-5 | 10-K Item 1A |

### Verification Process

1. **Hand-verify each value** against the actual TSLA FY2025 10-K (accession 0001628280-26-003952) and AAPL FY2025 10-K
2. **Add to ground truth modules:** Expand `tests/ground_truth/tsla.py` and `aapl.py` with new sections
3. **Add test functions:** New parametrized tests in `test_ground_truth_validation.py` for each field category
4. **Remove xfail markers:** Phase 19 governance tests marked xfail can now be expected to pass with LLM data

## Integration Points Summary

### Files to Modify (Existing)

| File | Lines Now | Action | Risk |
|------|-----------|--------|------|
| `llm_helpers.py` | 75 | Add `get_llm_eight_k()` | Low (small addition) |
| `company_profile.py` | 483 | Add LLM Item 1 integration | HIGH (near 500) |
| `debt_analysis.py` | 469 | Add LLM Item 8 debt enrichment | HIGH (near 500) |
| `audit_risk.py` | 478 | Add LLM Item 9A enrichment | HIGH (near 500) |
| `extract_market.py` | 254 | Add LLM 8-K event wiring | Low |
| `extract_ai_risk.py` | 150 | Add LLM AI risk supplement | Low |
| `ownership_structure.py` | 442 | Add LLM proxy ownership | Medium |
| `__init__.py` (ExtractStage) | 498 | Update budget to $2.00 | Low (1-line change) |
| `llm/cost_tracker.py` | 100 | Update default budget | Low |
| `llm/schemas/eight_k.py` | 153 | Add `departing_officer_title` | Low |
| `tests/ground_truth/tsla.py` | 73 | Add 20+ fields | Low |
| `tests/ground_truth/aapl.py` | ~73 | Add 20+ fields | Low |
| `test_ground_truth_validation.py` | 532 | Add 10+ new test functions | Medium (near 500) |

### Files to Create (New)

| File | Purpose | Estimated Lines |
|------|---------|-----------------|
| `ten_k_converters.py` | Item 1/7/8/9A LLM -> domain | 300-450 |
| `eight_k_converter.py` | 8-K events LLM -> domain | 200-300 |
| `proxy_ownership_converter.py` | DEF 14A ownership LLM -> domain | 100-200 |
| `tests/test_ten_k_converters.py` | Unit tests for 10-K converters | 200-400 |
| `tests/test_eight_k_converter.py` | Unit tests for 8-K converter | 150-300 |
| `tests/test_proxy_ownership_converter.py` | Unit tests for ownership converter | 100-200 |

### Files NOT Modified (Already Wired in Phase 19)

- `extract_governance.py` (348 lines) -- governance LLM already wired
- `extract_litigation.py` (474 lines) -- litigation LLM already wired
- `llm_governance.py` (339 lines) -- governance converters done
- `llm_litigation.py` (366 lines) -- litigation converters done

## Code Examples

### Example 1: Item 1 Business Converter

```python
# ten_k_converters.py
from do_uw.models.common import Confidence, SourcedValue
from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction
from do_uw.stages.extract.sourced import now, sourced_str, sourced_float

_LLM_SOURCE = "10-K (LLM)"


def convert_business_description(
    extraction: TenKExtraction,
) -> SourcedValue[str] | None:
    """Convert LLM business description to SourcedValue."""
    if not extraction.business_description:
        return None
    return sourced_str(
        extraction.business_description, _LLM_SOURCE, Confidence.HIGH,
    )


def convert_geographic_footprint(
    extraction: TenKExtraction,
) -> list[SourcedValue[dict[str, str]]]:
    """Convert LLM geographic regions to SourcedValue list."""
    results: list[SourcedValue[dict[str, str]]] = []
    for region in extraction.geographic_regions:
        # Parse "United States: 55%" format
        parts = region.rsplit(":", 1)
        entry: dict[str, str] = {"region": parts[0].strip()}
        if len(parts) > 1:
            entry["percentage"] = parts[1].strip()
        results.append(SourcedValue[dict[str, str]](
            value=entry,
            source=_LLM_SOURCE,
            confidence=Confidence.HIGH,
            as_of=now(),
        ))
    return results
```

### Example 2: 8-K Departure Converter

```python
# eight_k_converter.py
from do_uw.stages.extract.llm.schemas.eight_k import EightKExtraction
from do_uw.stages.extract.sourced import sourced_str, now
from do_uw.models.common import Confidence, SourcedValue

_LLM_SOURCE = "8-K (LLM)"


def convert_departures(
    extractions: list[EightKExtraction],
) -> list[dict[str, SourcedValue[str] | None]]:
    """Extract executive departures from 8-K events."""
    departures: list[dict[str, SourcedValue[str] | None]] = []
    for ext in extractions:
        if not ext.departing_officer:
            continue
        departure: dict[str, SourcedValue[str] | None] = {
            "name": sourced_str(ext.departing_officer, _LLM_SOURCE, Confidence.HIGH),
            "reason": (
                sourced_str(ext.departure_reason, _LLM_SOURCE, Confidence.HIGH)
                if ext.departure_reason else None
            ),
            "successor": (
                sourced_str(ext.successor, _LLM_SOURCE, Confidence.HIGH)
                if ext.successor else None
            ),
            "event_date": (
                sourced_str(ext.event_date, _LLM_SOURCE, Confidence.HIGH)
                if ext.event_date else None
            ),
        }
        departures.append(departure)
    return departures
```

### Example 3: Company Profile LLM Integration

```python
# In company_profile.py extract_company_profile():

# After existing _extract_business_description:
llm_ten_k = get_llm_ten_k(state)

if llm_ten_k:
    from do_uw.stages.extract.ten_k_converters import (
        convert_business_description,
        convert_geographic_footprint,
        convert_concentration,
        convert_operational_complexity_flags,
    )

    # Business description: LLM replaces if richer
    llm_desc = convert_business_description(llm_ten_k)
    if llm_desc is not None:
        if profile.business_description is None or (
            len(llm_desc.value) > len(profile.business_description.value)
        ):
            profile.business_description = llm_desc

    # Geographic footprint: LLM replaces if regex found nothing
    if not profile.geographic_footprint:
        profile.geographic_footprint = convert_geographic_footprint(llm_ten_k)

    # Operational complexity: supplement with LLM flags
    llm_flags = convert_operational_complexity_flags(llm_ten_k)
    if profile.operational_complexity is not None and llm_flags:
        # Merge LLM flags into existing complexity dict
        existing = profile.operational_complexity.value
        for key, val in llm_flags.items():
            if val and not existing.get(key):
                existing[key] = val
```

## Open Questions

1. **Should `ten_k_converters.py` be split preemptively?** Items 1/7 are qualitative (strings, lists), while Items 8/9A are more structured (debt instruments, control findings). A natural split would be `ten_k_converters_business.py` (Items 1/7) and `ten_k_converters_financial.py` (Items 8/9A). This depends on actual line counts during implementation. **Recommendation:** Start as one file, split at 400 lines.

2. **Where should 8-K restatement data land?** Restatement notices from 8-K Item 4.02 could go in:
   - `AuditRisk.restatement_history` (new field)
   - `CompanyProfile.business_changes` (existing field, generic)
   - `LitigationLandscape` (restatements trigger SCAs)
   Best fit: `AuditRisk` since restatements are controls/audit findings. But also flag in litigation for SCA correlation.

3. **Test file organization for ground truth expansion.** The existing `test_ground_truth_validation.py` is 532 lines. Adding 10+ test functions will push it over 500. **Recommendation:** Split into `test_ground_truth_validation.py` (identity + financials + distress) and `test_ground_truth_coverage.py` (new sections: Item 1/7/8/9A, 8-K, ownership, risk factors).

## Sources

### Primary (HIGH confidence)
All findings from direct codebase analysis:

- LLM extraction schemas: `src/do_uw/stages/extract/llm/schemas/` (ten_k.py, def14a.py, eight_k.py, common.py, __init__.py)
- Existing converters: `llm_governance.py` (339 lines), `llm_litigation.py` (366 lines)
- LLM helpers: `llm_helpers.py` (75 lines)
- LLM infrastructure: `llm/extractor.py` (242 lines), `llm/prompts.py` (187 lines), `llm/cost_tracker.py` (100 lines), `llm/boilerplate.py` (87 lines)
- Sub-orchestrators: `extract_governance.py` (348), `extract_litigation.py` (474), `extract_market.py` (254), `extract_ai_risk.py` (150)
- Target extractors: `company_profile.py` (483), `debt_analysis.py` (469), `audit_risk.py` (478), `ownership_structure.py` (442)
- Domain models: `models/state.py` (282), `models/ai_risk.py` (200), `models/company.py`, `models/financials.py`
- Pipeline integration: `stages/extract/__init__.py` (498)
- Ground truth: `tests/ground_truth/` (tsla.py, aapl.py, jpm.py), `test_ground_truth_validation.py` (532)
- Phase 19 research & summaries: `19-RESEARCH.md`, `19-04-PLAN.md`, `19-04-SUMMARY.md`

### Secondary (MEDIUM confidence)
- None needed -- all research based on codebase analysis

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Converter module design: HIGH -- follows established Phase 19 patterns identically
- Schema completeness analysis: HIGH -- direct comparison of schema fields vs domain targets
- Field mapping analysis: HIGH -- every field traced from schema to domain model
- 500-line risk assessment: HIGH -- exact line counts measured
- Integration approach: HIGH -- based on working Phase 19 patterns
- Ground truth expansion: MEDIUM -- field values need hand-verification against actual filings
- Cost estimation: MEDIUM -- based on token estimates, not actual usage data

**Research date:** 2026-02-10
**Valid until:** Indefinite (internal codebase analysis, not dependent on external changes)
