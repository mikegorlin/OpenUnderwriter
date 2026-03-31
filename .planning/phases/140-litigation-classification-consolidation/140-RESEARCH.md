# Phase 140: Litigation Classification & Consolidation - Research

**Researched:** 2026-03-28
**Domain:** Litigation data pipeline (extraction post-processing, deduplication, classification)
**Confidence:** HIGH

## Summary

Phase 140 creates a unified post-extraction classifier and universal deduplication engine for litigation cases. The existing codebase already has the foundational pieces: `CoverageType` enum (14 values), `LegalTheory` enum (12 values), `detect_coverage_type()`, `detect_legal_theories()`, `deduplicate_cases()` with 80% word overlap, and `_classify_case_destination()` for routing. The problem is that these pieces are scattered across extractors (SCA, derivative, regulatory, deal) with each doing its own classification differently. The unified classifier consolidates this into a single post-extraction pass.

The key architectural insight is that the unified classifier slots into `extract_litigation.py`'s `run_litigation_extractors()` function, running AFTER all individual extractors complete but BEFORE the summary/timeline generation. This is lines 238-247 in the current code. The classifier operates on the fully-populated `LitigationLandscape` and rewrites `coverage_type` and `legal_theories` on every `CaseDetail` uniformly.

**Primary recommendation:** Create a new `litigation_classifier.py` module in `stages/extract/` containing three public functions: `classify_all_cases()` (unified classifier + boilerplate filter), `deduplicate_all_cases()` (universal dedup across all case lists), and `disambiguate_by_year()` (year suffix on all case names). Call all three from `run_litigation_extractors()` after extractors finish.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Unified post-extraction classifier -- a NEW module runs AFTER all extractors complete, reclassifying every case uniformly from legal theories + named defendants. Per-extractor classification becomes initial hints only, overwritten by the unified classifier.
- **D-02:** Classifier overwrites existing `CaseDetail.coverage_type` and `CaseDetail.legal_theories` fields. No new fields -- the unified classifier IS the source of truth. Per-extractor values are treated as initial hints that get replaced.
- **D-03:** Universal dedup engine -- single dedup algorithm handles ALL case types (SCA, derivative, regulatory, deal litigation). Uses case name similarity + filing year + court as matching signals. Consolidates into one entry with all source references listed.
- **D-04:** Consolidated display uses primary (highest-confidence) case name. Below it, list all source references: "Sources: EFTS/SCAC, 10-K Item 3, Supabase SCA DB". Fields merged with highest-confidence source winning per field.
- **D-05:** Always append year to every case name: "In re Fastly (2020)", "SEC v. Ripple Labs (2020)". No conditional logic -- consistent, unambiguous format for all cases.
- **D-06:** Flag missing critical fields (case number, court, class period, named defendants) with data quality annotation. Additionally, trigger targeted web search for the specific case to fill gaps. Recovery results tagged LOW confidence.
- **D-07:** Legal theory match required for classification. A case must match at least one `LegalTheory` enum value. Boilerplate reserves like "routine litigation matters" won't match any theory and get filtered to a separate "unclassified reserves" bucket -- still shown in worksheet but clearly separated from classified cases.

### Claude's Discretion
- Exact similarity thresholds for universal dedup (current SCA dedup uses 80% word overlap -- may need tuning for other case types)
- How to structure the web search queries for missing field recovery
- Internal module organization (single file vs split by concern)
- Whether to extend existing `deduplicate_cases()` or create new dedup module

### Deferred Ideas (OUT OF SCOPE)
- Coverage side financial impact estimation (quantifying A vs B vs C exposure in dollars)
- Automated case status updates from court docket monitoring
- Earnings guidance signal conflation fix (not litigation-related)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LIT-01 | Case type classified from legal theories, not source category | Unified classifier with `THEORY_PATTERNS` regex + `LegalTheory` enum already exists in `sca_extractor.py`; needs generalization to derivative/regulatory/deal cases |
| LIT-02 | Substantially similar cases consolidated into single entry with related case names | Existing `deduplicate_cases()` in `sca_parsing.py` with word overlap + year gap; generalize to universal engine across all case lists |
| LIT-03 | Same-name cases disambiguated by year suffix | `get_case_key()` already includes filing year; add year suffix to `case_name.value` during consolidation pass |
| LIT-04 | Coverage side classification (A/B/C) from case type and named defendants | `detect_coverage_type()` in `sca_extractor.py` handles SCA theories; extend with defendant-based inference (individuals = Side A, entity-only = Side C) |
| LIT-05 | Missing critical fields flagged and acquisition attempted | `count_populated_fields()` already tracks field presence; add annotation + web search trigger for gaps |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | CaseDetail model, SourcedValue | Already used for all models; frozen=False allows field overwrites |
| re (stdlib) | 3.12 | Legal theory pattern matching | Already used extensively in sca_extractor.py |
| difflib (stdlib) | 3.12 | Case name similarity (SequenceMatcher) as alternative to word overlap | More nuanced than word overlap for similar-but-not-identical names |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | existing | Web search for missing field recovery | Only when D-06 recovery triggers |
| logging | stdlib | Classifier audit trail | All classification decisions logged |

No new dependencies needed. All functionality builds on existing stack.

## Architecture Patterns

### Recommended Module Structure
```
src/do_uw/stages/extract/
  litigation_classifier.py     # NEW: unified classifier + dedup + year disambiguation
  sca_extractor.py             # UNCHANGED: per-extractor hints only
  sca_parsing.py               # UNCHANGED: parsing + original dedup (kept for backward compat)
  extract_litigation.py        # MODIFIED: call classifier after all extractors
```

### Pattern 1: Post-Extraction Classifier Pipeline
**What:** Three-pass pipeline running after all extractors complete on the populated `LitigationLandscape`.
**When to use:** Always -- called from `run_litigation_extractors()` before summary/timeline.
**Integration point:** Insert between line 236 (cross_validate_scas) and line 238 (generate_litigation_summary) in `extract_litigation.py`.

```python
# In run_litigation_extractors(), after _cross_validate_scas():
from do_uw.stages.extract.litigation_classifier import (
    classify_all_cases,
    deduplicate_all_cases,
    disambiguate_by_year,
    recover_missing_fields,
)

# Pass 1: Boilerplate filter + unified classification
classify_all_cases(landscape)

# Pass 2: Universal deduplication across all case lists
deduplicate_all_cases(landscape)

# Pass 3: Year disambiguation on all case names
disambiguate_by_year(landscape)

# Pass 4: Missing field recovery (web search)
recover_missing_fields(state, landscape)
```

### Pattern 2: Unified Classification Logic
**What:** Single function that classifies any `CaseDetail` by legal theory + named defendants, regardless of origin.
**Key design:** Overwrites `coverage_type` and `legal_theories` fields (D-02).

```python
def _classify_case(case: CaseDetail) -> None:
    """Reclassify a single case from its text evidence."""
    # Gather all text evidence
    text_evidence = _gather_evidence_text(case)

    # Detect legal theories from evidence
    theories = _detect_theories(text_evidence)
    case.legal_theories = theories

    # Determine coverage type from theories + defendants
    case.coverage_type = _infer_coverage(theories, case.named_defendants)
```

### Pattern 3: Universal Dedup with Source Tracking
**What:** Dedup across all case lists in LitigationLandscape, tracking source references.
**Key insight:** Must handle cross-list dedup (an SCA case and a derivative case that are actually the same case from different extractors).

```python
def deduplicate_all_cases(landscape: LitigationLandscape) -> None:
    """Deduplicate across all case lists, consolidating into primary list."""
    all_cases = _collect_all_cases(landscape)  # Flatten with list-origin tag
    clusters = _cluster_similar_cases(all_cases)
    for cluster in clusters:
        primary = _select_primary(cluster)  # Highest confidence
        _merge_sources(primary, cluster)
    _redistribute_to_lists(landscape, clusters)  # Put back in correct lists
```

### Anti-Patterns to Avoid
- **Per-extractor classification as final:** Each extractor can do initial classification as hints, but the unified classifier MUST overwrite. Don't keep per-extractor values.
- **Dedup only within same list:** Cases from different extractors can be duplicates (e.g., SCA extractor and LLM extractor both find the same case). Must dedup across lists.
- **String matching on case_name.value directly:** Use `word_overlap_pct()` or similar fuzzy matching. Case names vary: "In re Fastly, Inc. Securities Litigation" vs "In re Fastly Securities Lit." are the same case.
- **Modifying CaseDetail schema:** D-02 says no new fields. Use existing fields only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Text similarity | Custom edit distance | Existing `word_overlap_pct()` from `sca_extractor.py` | Already tested, handles case-insensitive word-level overlap |
| Legal theory detection | New regex patterns | Existing `THEORY_PATTERNS` from `sca_extractor.py` | 7 patterns already cover major theories; extend for derivative/regulatory |
| Coverage type inference | New mapping logic | Extend `detect_coverage_type()` from `sca_extractor.py` | Already maps theories to coverage sides; needs defendant-based inference added |
| Case viability check | New filter | Existing `is_case_viable()` from `sca_extractor.py` | Already checks minimum fields |
| Boilerplate detection | New label list | Existing `_GENERIC_LABELS` from `llm_litigation.py` + `_is_boilerplate_litigation` from `signal_mappers_ext.py` | 12 generic labels already defined |

## Common Pitfalls

### Pitfall 1: Cross-List Deduplication Ordering
**What goes wrong:** Dedup within `securities_class_actions` works, but same case appears in both SCA list and `derivative_suits` list (from different extractors).
**Why it happens:** Each extractor populates its own list independently. LLM extraction may classify the same case differently than EFTS.
**How to avoid:** Flatten all case lists, dedup globally, then redistribute based on the unified classifier's type determination.
**Warning signs:** Case count increases after adding new data sources; same case name appears in multiple sections of the worksheet.

### Pitfall 2: Year Disambiguation Breaking Existing Dedup Keys
**What goes wrong:** Adding "(2020)" to case names breaks subsequent dedup comparisons if dedup runs after disambiguation.
**Why it happens:** Word overlap calculation includes the year suffix as a word, diluting similarity scores.
**How to avoid:** Run dedup BEFORE year disambiguation. Order: classify -> dedup -> disambiguate.
**Warning signs:** Previously-merged cases appearing as separate entries after adding year suffix.

### Pitfall 3: Overwriting HIGH Confidence with LOW
**What goes wrong:** Unified classifier replaces MEDIUM/HIGH confidence per-extractor classification with LOW confidence generic detection.
**Why it happens:** The unified classifier uses text-based regex which may produce less confident results than source-specific parsing.
**How to avoid:** When the unified classifier's detection confidence is LOWER than the existing value, keep the higher confidence value. Only overwrite when the unified classifier has equal or higher confidence, or when the existing value is clearly wrong (e.g., regulatory case classified as SCA).
**Warning signs:** Cases losing their specific legal theory classifications after unification.

### Pitfall 4: Missing Field Recovery ACQUIRE Boundary Violation
**What goes wrong:** Recovery web searches need to happen in ACQUIRE stage, but the classifier runs in EXTRACT.
**Why it happens:** D-06 says "trigger targeted web search" but the ACQUIRE boundary rule says data acquisition happens only in ACQUIRE.
**How to avoid:** Flag missing fields with annotations during EXTRACT. Recovery can use already-acquired web search data (blind_spot_results, litigation_data.web_results) but should NOT make new API calls. If truly new web searches are needed, add them to the next ACQUIRE pass or accept that recovery is best-effort from existing data.
**Warning signs:** Import of MCP tools or httpx client in the classifier module.

### Pitfall 5: Boilerplate Filter Removing Real Cases
**What goes wrong:** Legitimate cases with vague names (common in 10-K disclosure) get filtered as boilerplate.
**Why it happens:** Some real cases are described generically in 10-K filings: "certain securities claims" may be a real SCA.
**How to avoid:** Boilerplate filter sends to "unclassified reserves" bucket, NOT deletion. Cases with any detail fields populated (court, date, settlement) should not be filtered even with generic names.
**Warning signs:** Known active cases disappearing from the worksheet after classifier runs.

### Pitfall 6: Regulatory Proceedings Model Mismatch
**What goes wrong:** `regulatory_proceedings` field is typed as `list[SourcedValue[dict[str, str]]]` not `list[CaseDetail]`, so the classifier can't process them uniformly.
**Why it happens:** Phase 3 model design used different types for different litigation categories.
**How to avoid:** The classifier should handle `CaseDetail` lists (SCAs, derivatives, deal litigation) but process regulatory proceedings separately using their dict structure. Don't try to force-cast.
**Warning signs:** TypeError when iterating over regulatory_proceedings expecting CaseDetail attributes.

## Code Examples

### Gathering All CaseDetail Lists from LitigationLandscape
```python
def _collect_case_detail_lists(
    landscape: LitigationLandscape,
) -> list[tuple[str, list[CaseDetail]]]:
    """Collect all CaseDetail lists with their origin tag."""
    return [
        ("sca", landscape.securities_class_actions),
        ("derivative", landscape.derivative_suits),
        # deal_litigation is list[DealLitigation], not CaseDetail
        # regulatory_proceedings is list[SourcedValue[dict]], not CaseDetail
    ]
```

### Extended Theory Detection (Adding Derivative/Regulatory Theories)
```python
# Extend THEORY_PATTERNS for derivative and regulatory theories
EXTENDED_THEORY_PATTERNS: list[tuple[LegalTheory, re.Pattern[str]]] = [
    # Securities theories (from sca_extractor.py)
    (LegalTheory.RULE_10B5, re.compile(r"10b-5|Rule\s+10b-5", re.IGNORECASE)),
    (LegalTheory.SECTION_11, re.compile(r"Section\s+11\b", re.IGNORECASE)),
    (LegalTheory.SECTION_14A, re.compile(r"Section\s+14\(a\)", re.IGNORECASE)),
    # Derivative theories
    (LegalTheory.DERIVATIVE_DUTY, re.compile(
        r"derivative|fiduciary\s+duty|breach\s+of\s+duty|Caremark|oversight",
        re.IGNORECASE,
    )),
    # Regulatory theories
    (LegalTheory.FCPA, re.compile(r"\bFCPA\b|Foreign\s+Corrupt", re.IGNORECASE)),
    (LegalTheory.ANTITRUST, re.compile(r"\bantitrust\b|Sherman\s+Act", re.IGNORECASE)),
    (LegalTheory.ERISA, re.compile(r"\bERISA\b", re.IGNORECASE)),
    (LegalTheory.CYBER_PRIVACY, re.compile(r"data\s+breach|cyber|privacy", re.IGNORECASE)),
    (LegalTheory.ENVIRONMENTAL, re.compile(r"\benvironmental\b|EPA|CERCLA|Superfund", re.IGNORECASE)),
    (LegalTheory.PRODUCT_LIABILITY, re.compile(r"product\s+liability|recall|mass\s+tort", re.IGNORECASE)),
    (LegalTheory.EMPLOYMENT_DISCRIMINATION, re.compile(r"employment|EEOC|Title\s+VII|discrimination", re.IGNORECASE)),
    (LegalTheory.WHISTLEBLOWER, re.compile(r"whistleblower|qui\s+tam|Dodd-Frank\s+retaliation", re.IGNORECASE)),
]
```

### Coverage Type Inference with Defendant Analysis
```python
def _infer_coverage_type(
    theories: list[SourcedValue[str]],
    named_defendants: list[SourcedValue[str]],
) -> CoverageType:
    """Infer D&O coverage side from theories + defendants."""
    theory_values = {t.value for t in theories}
    has_individual_defendants = len(named_defendants) > 0

    # Derivative cases
    if LegalTheory.DERIVATIVE_DUTY.value in theory_values:
        return CoverageType.DERIVATIVE_SIDE_A if has_individual_defendants else CoverageType.DERIVATIVE_SIDE_B

    # SEC enforcement
    if any(t in theory_values for t in ("FCPA",)):
        return CoverageType.SEC_ENFORCEMENT_A if has_individual_defendants else CoverageType.SEC_ENFORCEMENT_B

    # Securities class actions
    if LegalTheory.SECTION_11.value in theory_values:
        return CoverageType.SCA_SIDE_C  # Entity securities coverage
    if LegalTheory.SECTION_14A.value in theory_values:
        return CoverageType.SCA_SIDE_B  # Corporate reimbursement
    if LegalTheory.RULE_10B5.value in theory_values:
        return CoverageType.SCA_SIDE_A if has_individual_defendants else CoverageType.SCA_SIDE_C

    # Regulatory/entity coverage
    if LegalTheory.ENVIRONMENTAL.value in theory_values:
        return CoverageType.REGULATORY_ENTITY
    if LegalTheory.EMPLOYMENT_DISCRIMINATION.value in theory_values:
        return CoverageType.EMPLOYMENT_ENTITY
    if LegalTheory.PRODUCT_LIABILITY.value in theory_values:
        return CoverageType.PRODUCT_ENTITY

    # Default: Side A if individuals named, entity otherwise
    return CoverageType.SCA_SIDE_A if has_individual_defendants else CoverageType.REGULATORY_ENTITY
```

### Year Disambiguation
```python
def _append_year_to_name(case: CaseDetail) -> None:
    """Append filing year to case name per D-05."""
    if not case.case_name or not case.case_name.value:
        return

    name = case.case_name.value
    # Don't double-add year if already present
    if re.search(r"\(\d{4}\)\s*$", name):
        return

    year = _extract_year(case)
    if year:
        case.case_name = SourcedValue[str](
            value=f"{name} ({year})",
            source=case.case_name.source,
            confidence=case.case_name.confidence,
            as_of=case.case_name.as_of,
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-extractor classification | Unified post-extraction classifier (this phase) | Phase 140 | Single source of truth for case type |
| SCA-only dedup (80% word overlap) | Universal dedup across all case types | Phase 140 | Eliminates cross-list duplicates |
| No year suffix on case names | Always append year to every case name | Phase 140 | Unambiguous same-company multi-year cases |
| Missing fields silently ignored | Flagged + recovery attempted | Phase 140 | Better data completeness |
| Boilerplate mixed with real cases | Separate "unclassified reserves" bucket | Phase 140 | Cleaner litigation section |

## Open Questions

1. **ACQUIRE boundary for missing field recovery (D-06)**
   - What we know: CLAUDE.md says "No data acquisition outside stages/acquire/" but D-06 says "trigger targeted web search"
   - What's unclear: Whether recovery web searches should happen in the classifier or be deferred to a re-acquisition pass
   - Recommendation: Use already-acquired data (blind_spot_results, web_results) for recovery. Flag remaining gaps with annotations but don't make new API calls from EXTRACT. This respects the boundary while delivering most of the value. If the user insists on new web searches, route them through the acquisition stage.

2. **Regulatory proceedings type mismatch**
   - What we know: `regulatory_proceedings` is `list[SourcedValue[dict[str, str]]]`, not `list[CaseDetail]`. Cannot be processed uniformly.
   - What's unclear: Whether to convert regulatory proceedings to CaseDetail for unified processing, or handle separately.
   - Recommendation: Handle separately. The classifier processes CaseDetail lists only (SCAs, derivatives). Regulatory proceedings get their own lightweight classification pass using dict field inspection. Don't change the model type -- that's a larger refactor.

3. **DealLitigation type mismatch**
   - What we know: `deal_litigation` is `list[DealLitigation]`, a different model from `CaseDetail`.
   - What's unclear: Whether deal litigation should be included in universal dedup.
   - Recommendation: Skip deal litigation from universal dedup initially. DealLitigation has different fields (acquirer, target, deal_value). Cross-type dedup between DealLitigation and CaseDetail is unlikely to produce meaningful matches.

4. **Universal dedup similarity threshold**
   - What we know: SCA dedup uses 80% word overlap. Court name adds disambiguation power per D-03.
   - What's unclear: Whether 80% is right for derivative cases (often shorter names like "Smith v. Jones").
   - Recommendation: Start with 70% for universal dedup (slightly lower than SCA-specific 80%), combined with filing year + court matching. Tune based on test results with real data.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/test_litigation_classifier.py -x` |
| Full suite command | `uv run pytest tests/ -x --timeout=60` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LIT-01 | Unified classifier sets legal theories from text, not source | unit | `uv run pytest tests/test_litigation_classifier.py::TestUnifiedClassification -x` | Wave 0 |
| LIT-02 | Similar cases from different sources consolidated | unit | `uv run pytest tests/test_litigation_classifier.py::TestUniversalDedup -x` | Wave 0 |
| LIT-03 | Year suffix appended to all case names | unit | `uv run pytest tests/test_litigation_classifier.py::TestYearDisambiguation -x` | Wave 0 |
| LIT-04 | Coverage side derived from theories + defendants | unit | `uv run pytest tests/test_litigation_classifier.py::TestCoverageSideClassification -x` | Wave 0 |
| LIT-05 | Missing fields flagged with annotation | unit | `uv run pytest tests/test_litigation_classifier.py::TestMissingFieldRecovery -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_litigation_classifier.py -x`
- **Per wave merge:** `uv run pytest tests/ -x --timeout=120 -k "litigation or sca or dedup"`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_litigation_classifier.py` -- covers LIT-01 through LIT-05
- [ ] No new framework install needed

## Sources

### Primary (HIGH confidence)
- `src/do_uw/models/litigation.py` -- CoverageType (14 values), LegalTheory (12 values), CaseDetail model
- `src/do_uw/stages/extract/sca_extractor.py` -- detect_coverage_type(), detect_legal_theories(), word_overlap_pct(), is_case_viable()
- `src/do_uw/stages/extract/sca_parsing.py` -- deduplicate_cases(), get_case_key(), _enrich_case()
- `src/do_uw/stages/extract/extract_litigation.py` -- run_litigation_extractors() orchestrator, _classify_case_destination()
- `src/do_uw/stages/extract/llm_litigation.py` -- _GENERIC_LABELS boilerplate detection
- `src/do_uw/stages/score/red_flag_gates.py` -- _is_regulatory_not_sca() classification logic
- `src/do_uw/stages/render/context_builders/_litigation_helpers.py` -- COVERAGE_DISPLAY mapping

### Secondary (MEDIUM confidence)
- `src/do_uw/stages/extract/derivative_suits.py` -- derivative-specific detection patterns (DERIVATIVE_PATTERNS, CAREMARK_RE)
- `src/do_uw/stages/extract/regulatory_extract.py` -- regulatory agency patterns and classification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing code
- Architecture: HIGH -- insertion point is clear, patterns are established
- Pitfalls: HIGH -- identified from reading actual code and understanding data flow

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable domain, no external dependency changes)
