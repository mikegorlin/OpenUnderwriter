# Phase 52: Extraction Data Quality - Research

**Researched:** 2026-02-28
**Domain:** SEC filing extraction, data validation, signal evaluation
**Confidence:** HIGH

## Summary

Phase 52 fixes 4 high-severity data quality issues discovered during the SNA (Snap-on) validation audit. All fixes are in the extraction/analysis layers -- no new pipeline stages, no rendering overhauls. The codebase has strong foundations for all 4 fixes: the LLM extraction pipeline (`instructor` + Anthropic Claude Haiku 4.5) already extracts `ExtractedDirector` records from DEF 14A but the data does not flow correctly into `BoardForensicProfile`; the `guidance_language` field exists in `TenKExtraction` but is never used to determine whether a company provides forward guidance; the litigation converter (`llm_litigation.py`) converts all `ExtractedLegalProceeding` records to `CaseDetail` without validating minimum evidence thresholds; and yfinance `history_1y` already includes daily volume data but no spike detection logic exists.

The primary risk is the LLM prompt changes for DQ-01 and DQ-03. The `ExtractedDirector` schema is already well-structured (name, age, independent, tenure, committees, other_boards, qualifications) and `convert_directors()` in `llm_governance.py` correctly maps these to `BoardForensicProfile`. The issue is likely that the LLM is not extracting directors consistently enough from all proxy statement formats, or the DEF 14A text is missing from acquired data for some tickers. For litigation, the LLM extracts generic labels from boilerplate 10-K language because the prompt does not require specificity.

**Primary recommendation:** Fix extraction-layer data quality through prompt tightening, post-extraction validation filters, model field additions (`provides_forward_guidance`), and new volume spike computation. SNA is the validation target for all 4 fixes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Board Director Extraction**: Extract core governance fields per director: name, independence status, committee memberships, tenure, age, qualifications summary. Qualifications as structured tags (not free text): industry expertise, financial expert, legal/regulatory, technology, public company experience, prior C-suite -- binary flags per director. Populate existing BoardForensicProfile model (add missing fields) rather than creating a separate board_directors array -- one source of truth per director. Accept LLM extraction output, mark all as MEDIUM confidence -- no cross-check against proxy header count. Source: DEF 14A proxy statement parsing.
- **Guidance vs Consensus**: Determine if company provides forward guidance via 10-K/10-Q language check -- search for "forward-looking statements", "guidance range", "we expect revenue of" etc. If no explicit guidance language found: provides_forward_guidance=False. Non-guiding companies: display analyst estimates labeled as "Analyst Consensus (not company guidance)" -- still show data but don't evaluate as company guidance. For companies that DO provide guidance: extract actual guidance ranges from filings. Extraction priority: 8-K earnings releases first, fall back to 10-Q outlook sections. FIN.GUIDE.* checks only evaluate against company-issued numbers, not analyst consensus.
- **Litigation Filtering**: Minimum evidence for a real CaseDetail: named parties (plaintiff name or "class of shareholders") AND court/jurisdiction AND approximate filing date. Boilerplate with zero specifics = rejected (not a CaseDetail). Defense in depth: tighten LLM extraction prompt to require specifics AND add post-extraction validation that drops records missing required fields. Borderline cases (named parties but missing court/docket): keep as LOW confidence rather than dropping -- better to over-flag than miss real litigation. Add SNA regression test: verify 0 boilerplate-derived false SCAs after fix.
- **Volume Spike Detection**: Spike definition: volume > 2x the 20-trading-day moving average. Lookback window: 1 year (252 trading days) -- matches typical D&O policy period. Event correlation: automated inline news search via Brave Search when spike detected -- attach findings to the volume signal. Upgrade STOCK.TRADE.volume_patterns from MANAGEMENT_DISPLAY to EVALUATIVE_CHECK. Scoring thresholds: 0 spikes = clean, 1-2 = watch, 3+ = concern.

### Claude's Discretion
- Exact LLM prompt wording for DEF 14A extraction and litigation filtering
- Internal data model field names and types
- Volume spike scoring weight relative to other STOCK.TRADE.* checks
- Post-extraction validation implementation details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DQ-01 | Board directors array populated from DEF 14A -- individual names, independence, committees, qualifications extracted (not just aggregate stats) | `ExtractedDirector` schema exists with all needed fields; `convert_directors()` in `llm_governance.py` maps to `BoardForensicProfile`; need to add qualification tags field to `BoardForensicProfile`, tighten DEF 14A prompt, and debug why extraction yields empty results for SNA |
| DQ-02 | Guidance vs consensus correctly distinguished -- FIN.GUIDE.* signals check `provides_forward_guidance` before evaluating; non-guiding companies show N/A | `guidance_language` field exists in `TenKExtraction`; `compute_guidance_fields()` in `signal_mappers_ext.py` maps guidance data; need `provides_forward_guidance` field on `EarningsGuidanceAnalysis`, 10-K text pattern matching, and conditional logic in guidance signal mapper |
| DQ-03 | Litigation extraction rejects boilerplate -- LLM requires named parties/court/docket for SCA; post-extraction filter drops hollow CaseDetail records | `convert_legal_proceedings()` in `llm_litigation.py` is the conversion point; `_is_boilerplate_litigation()` exists but catches only case_name patterns; need prompt tightening + post-extraction validation on required fields |
| DQ-04 | Volume spike detection and event correlation -- STOCK.TRADE.volume_patterns upgraded to evaluative with tiered thresholds; spikes trigger targeted news search | `history_1y` dict from yfinance includes Volume column; `StockPerformance.avg_daily_volume` exists; need new extraction function for spike detection, model field for spike events, signal YAML upgrade, and Brave Search correlation in ACQUIRE |
</phase_requirements>

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `instructor` | Latest | Structured LLM extraction with Pydantic schemas | Already used for all filing extraction |
| `anthropic` | Latest | LLM API client (Claude Haiku 4.5) | Already configured with rate limiting and cost tracking |
| `pydantic` v2 | Latest | Data models with validation | Project standard |
| `yfinance` | Latest | Stock data including daily price/volume history | Already acquired in ACQUIRE stage |
| `ruamel.yaml` | Latest | YAML round-trip editing for brain signal changes | Added in Phase 51 for YAML write-back |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `httpx` | Latest | HTTP client for Brave Search API calls | Volume spike event correlation (DQ-04) |
| `re` | stdlib | Pattern matching for guidance language detection | DQ-02 guidance keyword scanning |

### Alternatives Considered
None -- all changes use the existing stack.

## Architecture Patterns

### Current File Layout (relevant to Phase 52)
```
src/do_uw/
  stages/
    extract/
      llm/
        schemas/
          common.py          # ExtractedDirector, ExtractedLegalProceeding
          def14a.py          # DEF14AExtraction schema
          ten_k.py           # TenKExtraction schema (has guidance_language)
        prompts.py           # System prompts per filing type
        extractor.py         # LLMExtractor with caching
      board_parsing.py       # Regex board parsing (fallback)
      llm_governance.py      # convert_directors() -> BoardForensicProfile
      llm_litigation.py      # convert_legal_proceedings() -> CaseDetail
      extract_governance.py  # Governance orchestrator
      extract_litigation.py  # Litigation orchestrator
      earnings_guidance.py   # Earnings guidance extraction
      stock_performance.py   # Stock drop detection
    analyze/
      signal_mappers_ext.py  # compute_guidance_fields(), _is_boilerplate_litigation()
      signal_field_routing.py # FIELD_FOR_SIGNAL dict
  models/
    governance_forensics.py  # BoardForensicProfile model
    litigation.py            # CaseDetail model
    market_events.py         # EarningsGuidanceAnalysis model
    market.py                # StockPerformance model
  brain/
    signals/fin/income.yaml  # FIN.GUIDE.* signal definitions
    signals/stock/insider.yaml # STOCK.TRADE.volume_patterns signal
```

### Pattern 1: Extraction-Layer Data Flow
**What:** LLM extracts flat schema -> converter maps to domain model -> orchestrator wires into state
**When to use:** All 4 DQ fixes follow this pattern
**Key files:**
- Schema: `schemas/common.py` (ExtractedDirector, ExtractedLegalProceeding)
- Converter: `llm_governance.py` (convert_directors), `llm_litigation.py` (convert_legal_proceedings)
- Orchestrator: `extract_governance.py`, `extract_litigation.py`

### Pattern 2: Post-Extraction Validation
**What:** After LLM extraction and conversion, validate domain model records against minimum evidence thresholds; drop or downgrade confidence on records that fail validation.
**When to use:** DQ-03 litigation filtering, DQ-01 director name validation (already exists via `is_valid_person_name()`)
**Example:**
```python
# In llm_litigation.py:
def convert_legal_proceedings(extraction: TenKExtraction) -> list[CaseDetail]:
    results: list[CaseDetail] = []
    for proc in extraction.legal_proceedings:
        if not proc.case_name or not proc.case_name.strip():
            continue
        detail = _convert_one_proceeding(proc)
        if not _meets_minimum_evidence(detail):
            continue  # Drop hollow records
        results.append(detail)
    return results
```

### Pattern 3: Signal-Level Gating
**What:** Before evaluating a signal, check a precondition field; if precondition fails, return a display-only result instead of evaluation.
**When to use:** DQ-02 guidance gating on `provides_forward_guidance`
**Example:**
```python
# In compute_guidance_fields():
def compute_guidance_fields(eg, safe_sourced_fn):
    result = {}
    if not eg.provides_forward_guidance:
        result["guidance_provided"] = "No"
        result["guidance_philosophy"] = "N/A"
        result["beat_rate"] = None  # Still show as analyst data
        return result
    # ... existing guidance evaluation logic
```

### Pattern 4: Time-Series Computation with Threshold Detection
**What:** Compute rolling statistics on acquired time-series data (volume history) and flag threshold breaches.
**When to use:** DQ-04 volume spike detection
**Key data:** `state.acquired_data.market_data["history_1y"]` contains daily OHLCV data as a dict-of-dicts
**Example approach:**
```python
# Volume spike detection (new extraction function)
def detect_volume_spikes(
    history_1y: dict[str, Any],
    lookback: int = 20,
    threshold_multiple: float = 2.0,
) -> list[dict[str, Any]]:
    volumes = extract_volume_series(history_1y)
    spikes = []
    for i in range(lookback, len(volumes)):
        avg = sum(volumes[i-lookback:i]) / lookback
        if avg > 0 and volumes[i] / avg >= threshold_multiple:
            spikes.append({
                "date": dates[i],
                "volume": volumes[i],
                "volume_multiple": round(volumes[i] / avg, 2),
            })
    return spikes
```

### Anti-Patterns to Avoid
- **Modifying LLM schemas without cache invalidation**: The `schema_hash()` in `extractor.py` auto-invalidates cache when Pydantic schemas change. Adding fields to `ExtractedDirector` will automatically invalidate cached extractions, so no manual cache clearing needed.
- **Filtering too aggressively in extraction**: Per user decision, borderline litigation cases (named parties but missing court/docket) should be kept at LOW confidence, not dropped. The post-extraction filter should only drop records with ZERO specifics.
- **Acquisition in EXTRACT/ANALYZE stages**: Volume spike event correlation requires web search (Brave Search). Per CLAUDE.md, MCP tools are ONLY used in ACQUIRE. However, the volume spike detection itself (computation on already-acquired data) belongs in EXTRACT. The news search for event correlation must happen in ACQUIRE or via a late-binding acquisition callback. This is a design tension to resolve.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured LLM extraction | Custom JSON parsing | `instructor` + Pydantic schema | Already working with caching, retry, rate limiting |
| YAML editing | String manipulation | `ruamel.yaml` | Preserves comments, anchors, flow style |
| Volume spike statistics | Custom rolling window | Simple list comprehension | Data is small (252 points), numpy is overkill |
| Guidance keyword matching | NLP/ML classifier | Regex pattern list on 10-K text | Guidance language is formulaic ("we expect revenue", "our outlook") |

**Key insight:** These are data quality fixes, not new feature builds. The infrastructure (LLM extraction pipeline, signal evaluation, YAML brain signals) already exists. The fixes are targeted: tighter prompts, validation filters, new model fields, and new computation on existing data.

## Common Pitfalls

### Pitfall 1: LLM Extraction Cache Stale After Prompt Changes
**What goes wrong:** Changing the DEF 14A or 10-K system prompt does not automatically invalidate cached LLM extractions because the cache key is `(accession, form_type, schema_version)` -- schema_version is from `schema_hash()` which only hashes the Pydantic schema, not the system prompt.
**Why it happens:** The cache is designed for schema changes (field additions/removals), not prompt refinement.
**How to avoid:** When changing prompts (DQ-01, DQ-03), either: (a) clear the extraction cache for the test ticker (SNA), or (b) add a field to the schema to force cache invalidation. Option (a) is simpler for development. For production, consider adding prompt_version to cache key.
**Warning signs:** Test runs show same (bad) results after prompt changes.

### Pitfall 2: Guidance Conflation with Analyst Estimates
**What goes wrong:** `yfinance earnings_dates` "EPS Estimate" field is analyst consensus, not company guidance. The current code stores this as `guidance_eps_low/high` in `EarningsQuarterRecord`, which misleadingly implies company guidance.
**Why it happens:** yfinance field naming ambiguity. The data is useful (analyst consensus beat/miss rate IS relevant for D&O) but the label is wrong.
**How to avoid:** Add `provides_forward_guidance` boolean to `EarningsGuidanceAnalysis`. Determine from 10-K `guidance_language` text. If `provides_forward_guidance=False`, FIN.GUIDE.* signals should either SKIP or return "N/A" display values. The analyst consensus data should still be stored and displayed, just labeled correctly.
**Warning signs:** SNA showing `FIN.GUIDE.current = Yes` when Snap-on doesn't provide guidance.

### Pitfall 3: Boilerplate Litigation Creating Cascading False Signals
**What goes wrong:** A generic 10-K legal reserves paragraph gets extracted as a CaseDetail, which then triggers LIT.SCA.demand, LIT.SCA.derivative, and LIT.PATTERN.sol_windows -- all false positives.
**Why it happens:** The LLM extraction prompt doesn't require specificity, and the existing `_is_boilerplate_litigation()` filter only checks case_name patterns, not structural completeness.
**How to avoid:** Defense in depth: (1) tighten LLM prompt to require named parties, court, filing date; (2) add post-extraction filter in `convert_legal_proceedings()` that validates minimum required fields before creating CaseDetail; (3) borderline cases (some specifics but not all) get LOW confidence per user decision.
**Warning signs:** SNA producing any SCAs or derivative suits.

### Pitfall 4: Volume Spike Event Correlation Violating MCP Boundary
**What goes wrong:** Volume spike detection runs in EXTRACT but event correlation needs web search (ACQUIRE-only per CLAUDE.md).
**Why it happens:** Volume spike detection is a computation on existing data (EXTRACT), but event attribution needs new data (web search = ACQUIRE).
**How to avoid:** Two approaches: (1) Run spike detection in EXTRACT, store spike dates, then run event correlation as a late-binding ACQUIRE step before ANALYZE. (2) Do spike detection AND correlation together in a new ACQUIRE sub-step that runs after initial market data acquisition. Option (2) is simpler but mixes computation with acquisition. Option (1) is architecturally cleaner but requires pipeline plumbing. **Recommendation**: Option (2) -- create a small ACQUIRE helper that takes the already-fetched history_1y, detects spikes, and immediately searches for each spike's catalyst. This keeps it self-contained in ACQUIRE where web search is allowed.
**Warning signs:** Import errors from stages/extract importing MCP tools.

### Pitfall 5: Empty board_forensics Despite LLM Returning Directors
**What goes wrong:** The LLM extracts directors into `DEF14AExtraction.directors`, but `convert_directors()` rejects them all via `is_valid_person_name()` validation.
**Why it happens:** The name validation filter (`leadership_parsing.is_valid_person_name()`) may be too aggressive for director names that include titles, suffixes, or unusual formats.
**How to avoid:** Debug with SNA's actual DEF 14A first. Check: (1) Is `llm_def14a.directors` populated? (2) Does `is_valid_person_name()` reject valid names? (3) Is the DEF 14A text actually present in acquired data? Log rejected names to identify the filter causing the gap.
**Warning signs:** Log message "SECT5: Rejected N director names that failed person-name validation" with N = all directors.

## Code Examples

### DQ-01: Qualification Tags on BoardForensicProfile
```python
# New field on BoardForensicProfile in governance_forensics.py
class BoardForensicProfile(BaseModel):
    # ... existing fields ...
    qualification_tags: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Structured qualification tags: industry_expertise, "
            "financial_expert, legal_regulatory, technology, "
            "public_company_experience, prior_c_suite"
        ),
    )
    age: SourcedValue[int] | None = Field(
        default=None, description="Director age from proxy"
    )
```

### DQ-01: Enhanced ExtractedDirector Schema
```python
# In schemas/common.py - add qualification_tags
class ExtractedDirector(BaseModel):
    # ... existing fields ...
    qualification_tags: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Structured qualification tags from director bio. "
            "Use ONLY these values: 'industry_expertise', 'financial_expert', "
            "'legal_regulatory', 'technology', 'public_company_experience', "
            "'prior_c_suite'. Set each that applies based on bio content."
        ),
    )
```

### DQ-02: Forward Guidance Detection
```python
# Guidance keyword patterns for 10-K/10-Q text
_GUIDANCE_PATTERNS = [
    r"(?i)we\s+expect\s+(?:revenue|earnings|sales)",
    r"(?i)(?:our|the\s+company'?s?)\s+(?:outlook|guidance|forecast)",
    r"(?i)guidance\s+range",
    r"(?i)we\s+(?:anticipate|project|forecast)\s+(?:revenue|net\s+income|EPS)",
    r"(?i)full[- ]year\s+(?:\d{4}\s+)?(?:revenue|earnings)\s+(?:guidance|outlook)",
    r"(?i)(?:raises?|lowers?|maintains?|reaffirms?|withdraws?)\s+(?:its?\s+)?guidance",
]

def detect_forward_guidance(filing_text: str) -> bool:
    """Check if 10-K/10-Q contains explicit forward guidance language."""
    import re
    for pattern in _GUIDANCE_PATTERNS:
        if re.search(pattern, filing_text):
            return True
    return False
```

### DQ-03: Post-Extraction Litigation Validation
```python
# Minimum evidence validation for CaseDetail
def _meets_minimum_evidence(proc: ExtractedLegalProceeding) -> bool:
    """Check if a legal proceeding has enough specifics to be a real case."""
    has_named_parties = bool(
        proc.case_name
        and proc.case_name.strip()
        and not _is_generic_label(proc.case_name)
    )
    has_court = bool(proc.court and proc.court.strip())
    has_filing_date = bool(proc.filing_date and proc.filing_date.strip())
    # Minimum: named parties AND (court OR filing_date)
    return has_named_parties and (has_court or has_filing_date)

_GENERIC_LABELS = {
    "legal settlement", "unspecified legal matter",
    "shareholder derivative action", "general litigation",
    "routine legal proceedings", "various legal proceedings",
}

def _is_generic_label(name: str) -> bool:
    return name.strip().lower() in _GENERIC_LABELS
```

### DQ-04: Volume Spike Detection
```python
# Volume spike detection from yfinance history
def detect_volume_spikes(
    history_1y: dict[str, Any],
    lookback_days: int = 20,
    spike_threshold: float = 2.0,
) -> list[dict[str, Any]]:
    """Detect trading days where volume exceeds Nx the moving average."""
    volumes = _extract_column(history_1y, "Volume")
    dates = _extract_dates(history_1y)
    closes = _extract_column(history_1y, "Close")

    if len(volumes) < lookback_days + 1:
        return []

    spikes: list[dict[str, Any]] = []
    for i in range(lookback_days, len(volumes)):
        window = volumes[i - lookback_days:i]
        avg = sum(window) / len(window)
        if avg > 0 and volumes[i] / avg >= spike_threshold:
            price_change = None
            if i > 0 and closes[i-1] > 0:
                price_change = round((closes[i] - closes[i-1]) / closes[i-1] * 100, 2)
            spikes.append({
                "date": dates[i],
                "volume": int(volumes[i]),
                "volume_multiple": round(volumes[i] / avg, 2),
                "price_change_pct": price_change,
            })
    return spikes
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Regex-only DEF 14A parsing | LLM extraction (instructor + Haiku 4.5) with regex fallback | Phase 32+ | LLM is primary path via `extract_governance.py` lines 143-167 |
| yfinance EPS Estimate = "guidance" | Conflated (BUG) | Phase 45 | This phase fixes it |
| All 10-K legal proceedings = SCAs | Converted without validation (BUG) | Phase 23+ | This phase adds minimum evidence filter |
| Volume as display-only | Display-only (BUG) | Phase 42 | This phase upgrades to evaluative |

**Key insight from codebase analysis:** The `convert_directors()` function in `llm_governance.py` (lines 85-147) is well-written and already handles all the needed mapping. The issue is upstream -- either the LLM is not extracting directors, or the DEF 14A text is not reaching the LLM. The first debugging step is to check whether `llm_def14a.directors` is populated for SNA.

## Open Questions

1. **DEF 14A text availability for SNA**
   - What we know: `get_llm_def14a(state)` deserializes cached LLM results; DEF 14A text is acquired via EdgarTools MCP
   - What's unclear: Is SNA's DEF 14A text actually reaching the LLM, or is it failing silently? Logs from an SNA run would confirm.
   - Recommendation: Debug by running `do-uw analyze SNA` with `DEBUG` logging on `do_uw.stages.extract.llm` and checking whether DEF 14A extraction is attempted and what `DEF14AExtraction.directors` contains.

2. **Volume spike event correlation architecture**
   - What we know: CLAUDE.md says "MCP tools (EdgarTools, Brave Search, Playwright, Fetch) are used ONLY in ACQUIRE stage"
   - What's unclear: Whether computing spikes from already-acquired data (EXTRACT) and then triggering a web search (ACQUIRE) requires a pipeline callback pattern or can be a self-contained ACQUIRE helper.
   - Recommendation: Self-contained ACQUIRE helper that takes `history_1y`, detects spikes, and searches inline. Simpler than a callback. The data is already available in ACQUIRE when market data finishes.

3. **FIN.GUIDE.* signal behavior for non-guiding companies**
   - What we know: 5 FIN.GUIDE signals exist (current, track_record, philosophy, earnings_reaction, analyst_consensus)
   - What's unclear: Should `provides_forward_guidance=False` cause all 5 to SKIP, or should some still evaluate (e.g., analyst_consensus and earnings_reaction are relevant regardless of guidance)?
   - Recommendation: Only FIN.GUIDE.current, FIN.GUIDE.track_record, and FIN.GUIDE.philosophy should be gated on `provides_forward_guidance`. FIN.GUIDE.earnings_reaction and FIN.GUIDE.analyst_consensus remain active because post-earnings stock reactions and analyst consensus divergence are D&O-relevant regardless of whether the company guides.

## Detailed Implementation Analysis

### DQ-01: Board Director Extraction

**Current flow:**
1. `extract_governance.py` line 82: `llm_def14a = get_llm_def14a(state)`
2. Line 143: `if llm_def14a and llm_def14a.directors:`
3. Line 149: `gov.board_forensics = convert_directors(llm_def14a)`
4. Fallback (line 170): regex `_run_board_governance()` -> `board_parsing.py`

**What needs to change:**
- **Schema**: Add `qualification_tags: list[str]` to `ExtractedDirector` in `schemas/common.py` -- binary tags not free text per user decision
- **Model**: Add `qualification_tags: list[str]` and `age: SourcedValue[int] | None` to `BoardForensicProfile` in `governance_forensics.py`
- **Converter**: Update `convert_directors()` in `llm_governance.py` to map qualification_tags and age
- **Prompt**: Enhance `DEF14A_SYSTEM_PROMPT` in `prompts.py` to explicitly request per-director extraction with all fields
- **Debug**: Verify DEF 14A text is reaching LLM for SNA, check if `DEF14AExtraction.directors` returns populated list

**Files touched:** `schemas/common.py`, `governance_forensics.py`, `llm_governance.py`, `prompts.py`
**Lines at risk of 500-line limit:** `llm_governance.py` is currently ~350 lines, safe. `governance_forensics.py` is ~460 lines, near limit -- adding 2 fields is fine.

### DQ-02: Guidance vs Consensus

**Current flow:**
1. `earnings_guidance.py`: `_parse_earnings_dates()` reads yfinance `EPS Estimate` as guidance
2. `compute_guidance_fields()` in `signal_mappers_ext.py`: builds `guidance_provided`, `beat_rate`, etc.
3. FIN.GUIDE.current evaluates `guidance_provided` field (true if quarters exist)

**What needs to change:**
- **Model**: Add `provides_forward_guidance: bool = False` to `EarningsGuidanceAnalysis` in `market_events.py`
- **Extraction**: New function in `earnings_guidance.py` to detect forward guidance from 10-K/10-Q text via regex patterns on `guidance_language` from `TenKExtraction` or raw filing text
- **Mapper**: Update `compute_guidance_fields()` to gate on `provides_forward_guidance`:
  - If False: `guidance_provided = "No"`, `guidance_philosophy = "N/A"`, `beat_rate` still computed but labeled as analyst consensus
  - If True: existing behavior
- **Signal YAML**: No changes needed -- the signal definitions are already correct (tiered thresholds). The gating happens in the mapper, not the signal definition.
- **Rendering**: Worksheet should label data source differently for guiding vs non-guiding companies

**Files touched:** `market_events.py`, `earnings_guidance.py`, `signal_mappers_ext.py`
**Lines at risk:** `earnings_guidance.py` is ~466 lines, safe. `signal_mappers_ext.py` is ~150 lines, very safe.

### DQ-03: Litigation False Positives

**Current flow:**
1. `extract_litigation.py` line 107: `llm_cases = convert_legal_proceedings(llm_ten_k)`
2. Lines 108-116: Dedup by case name, append to SCAs
3. `llm_litigation.py` `convert_legal_proceedings()`: only skips empty case_name

**What needs to change:**
- **Prompt**: Enhance `TEN_K_SYSTEM_PROMPT` in `prompts.py` to explicitly require named parties, court/jurisdiction, and approximate filing date for legal proceedings. Add: "Standard legal reserve disclosures and boilerplate litigation language are NOT legal proceedings. Only extract cases with specific named plaintiffs or class descriptions, identified courts or jurisdictions, and filing dates."
- **Schema**: Optionally add `is_boilerplate: bool = False` to `ExtractedLegalProceeding` to let the LLM self-classify
- **Converter**: Add `_meets_minimum_evidence()` filter to `convert_legal_proceedings()` that requires (named_parties OR case_name with specifics) AND (court OR filing_date)
- **Borderline handling**: Per user decision, cases with named parties but missing court/docket keep as LOW confidence instead of dropping. Add confidence downgrade path.

**Files touched:** `prompts.py`, `schemas/common.py` (optional), `llm_litigation.py`
**Lines at risk:** `llm_litigation.py` is ~372 lines, safe. `prompts.py` is ~187 lines, very safe.

### DQ-04: Volume Spike Detection

**Current flow:**
1. `market_client.py`: acquires `history_1y` with Volume column
2. `stock_performance.py`: extracts stock performance metrics but ignores volume spikes
3. `STOCK.TRADE.volume_patterns` signal: `threshold: type: display`, `data_strategy.field_key: adverse_event_count`

**What needs to change:**
- **New extraction function**: `detect_volume_spikes()` in a new file or in `stock_performance.py` -- computes 20-day moving average, flags days exceeding 2x threshold, records volume_multiple and price_change_pct
- **Model**: Add `volume_spike_events: list[SourcedValue[dict[str, Any]]]` to `StockPerformance` or a new sub-model on `MarketData`
- **Acquisition**: New ACQUIRE helper that takes spike dates and runs Brave Search for each (e.g., "SNA Snap-on 2025-07-15 stock" to find catalyst)
- **Signal YAML**: Update `STOCK.TRADE.volume_patterns` in `brain/signals/stock/insider.yaml`:
  - Change `threshold.type` from `display` to `tiered`
  - Add `red: 3+ volume spikes (>2x avg)`, `yellow: 1-2 volume spikes`, `clear: 0 spikes`
  - Change `data_strategy.field_key` from `adverse_event_count` to `volume_spike_count` (or reuse with new computation)
- **Signal mapper**: Update `_map_market_fields()` to populate `volume_spike_count` from new extraction
- **Field routing**: Update `FIELD_FOR_SIGNAL["STOCK.TRADE.volume_patterns"]` in `signal_field_routing.py`

**Files touched:** `stock_performance.py` (or new `volume_spikes.py`), `market.py` model, `market_client.py` or new acquire helper, `brain/signals/stock/insider.yaml`, `signal_mappers.py`, `signal_field_routing.py`
**Lines at risk:** `stock_performance.py` is ~350 lines, safe for additions. If new file needed for spike detection to avoid exceeding 500 lines, split per CLAUDE.md rules.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `src/do_uw/stages/extract/` -- all extraction modules examined directly
- Codebase analysis: `src/do_uw/models/` -- all relevant data models examined
- Codebase analysis: `src/do_uw/brain/signals/` -- signal YAML definitions examined
- Codebase analysis: `src/do_uw/stages/analyze/` -- signal mappers and field routing examined
- Todo files: `.planning/todos/pending/` -- all 4 high-severity issues documented with root cause analysis

### Secondary (MEDIUM confidence)
- MEMORY.md: Board forensic profiles on `gov.board_forensics` not `gov.board.directors`, boilerplate SCA filter documented
- CONTEXT.md: User decisions on all 4 fixes confirmed with specific thresholds and approaches

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- codebase examined in detail, all touch points identified, existing patterns well-documented
- Pitfalls: HIGH -- root causes identified from codebase analysis and todo files, all 4 issues have clear fix paths

**Research date:** 2026-02-28
**Valid until:** 2026-03-15 (stable -- internal codebase fixes, no external dependency changes)
