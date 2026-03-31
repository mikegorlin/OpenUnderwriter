# Phase 33: Brain-Driven Worksheet Architecture - Research

**Researched:** 2026-02-20
**Domain:** Internal architecture redesign -- top-down question-to-artifact mapping
**Confidence:** HIGH (all findings based on direct codebase examination)

## Summary

Phase 33 is an internal architecture task, not a library/technology task. It connects the brain's 231 underwriting questions (v6 taxonomy) to the data pipeline and output artifacts. The QUESTION-AUDIT.md from Phase 32 provides the diagnostic: 152 questions ANSWERED, 46 PARTIAL, 14 NO CHECKS, 19 DISPLAY ONLY, and 5 subsections with zero coverage. This phase closes those gaps.

The research reveals six categories of work: (1) adding `v6_subsection` and `v6_question_ids` fields to checks.json so every check traces to the question it answers, (2) designing structured "section artifacts" that intermediate between raw state data and renderers -- currently renderers reach deep into the state model with ad-hoc accessor patterns, (3) closing the 5 zero-coverage subsections by either creating new checks or mapping existing data to those questions, (4) fixing known false triggers where checks evaluate wrong data (employee count as labor flag count, stock price as PE ratio, ceo_chair_duality boolean treated as numeric), (5) verifying every TRIGGERED check makes sense in its question context, and (6) wiring each artifact to its renderer with explicit rendering paths.

**Primary recommendation:** Work top-down from questions. For each of the 45 subsections, define the answer artifact (what data structure the renderer needs), then verify the pipeline produces it. Where it doesn't, add acquisition/extraction/check wiring. Where it does but poorly, fix the data mapping.

## Architecture Patterns

### Current Architecture Flow

```
brain/checks.json (384 checks)
    |
    v
check_mappers.py --> map_check_data(check_id, extracted) --> dict[str, Any]
    |
    v
check_field_routing.py --> narrow_result() --> single field dict
    |
    v
check_evaluators.py --> evaluate_*() --> CheckResult
    |
    v
AnalysisResults.check_results: dict[str, Any]
    |
    v
Renderers: sect1..sect8 each reach into AnalysisState directly
```

### v6 Question Taxonomy Structure

```
5 Sections, 45 Subsections, 231 Questions
    |
    1. COMPANY (11 subsections, 59 questions)
    2. MARKET (8 subsections, 31 questions)
    3. FINANCIAL (8 subsections, 42 questions)
    4. GOVERNANCE & DISCLOSURE (9 subsections, 62 questions)
    5. LITIGATION & REGULATORY (9 subsections, 37 questions)
```

### Existing Mapping Infrastructure

The system already has partial question mapping in `enrichment_data.py`:

- `SUBDOMAIN_TO_RISK_QUESTIONS`: 53 prefix.subdomain -> v6 subsection ID mappings (e.g., `"BIZ.CLASS": ["1.1"]`)
- `CHECK_TO_RISK_QUESTIONS`: 84 explicit check_id -> v6 subsection ID overrides (e.g., `"BIZ.CLASS.litigation_history": ["1.1", "5.2"]`)

But these exist only in the enrichment layer -- they are NOT embedded in checks.json itself (0 checks have `risk_questions`, `v6_question_ids`, or `subsection_id` fields). The brain_checks DuckDB table HAS `risk_questions VARCHAR[]` and `report_section VARCHAR` columns, which suggests Phase 32 designed the schema but did not populate it.

### Section Number Mismatch

**Critical finding:** The check `section` field numbers do NOT match v6 section numbers:

| Check Prefix | Check `section` | v6 Section | Renderer |
|---|---|---|---|
| BIZ | 1 | 1. COMPANY | sect2_company |
| STOCK | 2 | 2. MARKET | sect4_market |
| FIN, NLP | 3 | 3. FINANCIAL | sect3_financial |
| LIT | 4 | 5. LITIGATION | sect6_litigation |
| GOV, EXEC | 5 | 4. GOVERNANCE | sect5_governance |
| FWRD | 6 | 1,3,4 (distributed) | various |

The renderer section numbers (sect1=ExecSummary, sect2=Company, sect3=Financial, sect4=Market, sect5=Governance, sect6=Litigation, sect7=Scoring, sect8=AI) also differ from v6.

**Decision needed:** Whether to renumber checks to match v6 or maintain a mapping layer. Given 384 checks reference these section numbers, a mapping layer (as enrichment_data.py already provides) is lower risk than mass renumbering.

### Recommended Artifact Pattern

Currently renderers reach directly into deeply nested state:
```python
# Current pattern (sect2_company.py)
state.company.section_summary.value
state.company.identity.sic_code.value
state.extracted.governance.board_composition.size
```

The proposed "section artifact" pattern would create intermediate structures:

```python
# Proposed pattern
@dataclass
class SubsectionArtifact:
    subsection_id: str         # "1.2"
    title: str                 # "Business Model & Revenue"
    questions: list[QuestionAnswer]
    checks: list[CheckSummary]
    display_data: dict[str, Any]   # Structured data for rendering
    assessment: str            # "ANSWERED" | "PARTIAL" | "NO DATA" | "DISPLAY ONLY"

@dataclass
class QuestionAnswer:
    question_id: str           # "1.2.1"
    question_text: str
    answer_status: str         # "ANSWERED" | "PARTIAL" | "NOT AVAILABLE"
    answer_data: Any           # The actual answer (varies by question type)
    processing_type: str       # "DISPLAY" | "EVALUATE" | "COMPUTE" | "INFER"
    checks: list[str]          # Check IDs that contribute
    sources: list[str]         # Data sources used
```

**Risk assessment:** This is a significant architectural addition. It should be designed carefully to avoid creating a competing state representation (predecessor failure #3). The artifact should be built from existing state data during RENDER, not stored as additional state.

## Gap Analysis (from QUESTION-AUDIT.md)

### Zero-Coverage Subsections (5 subsections, 14 questions)

| Subsection | Questions | Gap Type | Potential Resolution |
|---|---|---|---|
| **1.4 Corporate Structure** | 3 | NO CHECKS | Data available in 10-K Exhibit 21 (subsidiary list), Item 7 (VIEs). Need new extraction + checks for subsidiary count, VIE presence, related-party complexity |
| **4.9 Media & External Narrative** | 2 | NO CHECKS | Requires web search acquisition (FWRD.WARN.social_sentiment and FWRD.WARN.journalism_activity exist but SKIPPED). Need acquisition to populate |
| **5.7 Defense Posture & Reserves** | 3 | NO CHECKS | Data partially available: forum selection in DEF 14A (GOV.RIGHTS.forum_select), contingent liabilities in 10-K Item 3/Note (extraction exists in contingent_liab.py). Need new checks mapping this data |
| **5.8 Litigation Risk Patterns** | 4 | NO CHECKS | SOL mapper exists (sol_mapper.py), industry theories exist (industry_theories.json), temporal correlation logic exists in stock_drops.py. Need new checks to surface these |
| **5.9 Sector-Specific Litigation** | 2 | NO CHECKS | Industry playbooks exist (Phase 9), industry_theories.json has sector patterns. Need checks that activate per-sector |

### PARTIAL Subsections (key ones)

| Subsection | Questions | Issue | Resolution |
|---|---|---|---|
| **1.9 Employee Signals** | 6 | 5 of 8 checks SKIPPED (Glassdoor, Indeed, Blind, LinkedIn data not acquired) | Acquisition gap -- web scraping needed |
| **1.10 Customer Signals** | 6 | 8 of 11 checks SKIPPED (app ratings, CFPB, Trustpilot, G2 not acquired) | Acquisition gap -- API/web scraping needed |
| **2.3 Volatility & Trading** | 4 | All INFO, no evaluative thresholds | Need to add RED/YELLOW/CLEAR thresholds to STOCK.TRADE checks |
| **3.7 Guidance & Market Expectations** | 5 | All INFO, no evaluative thresholds | Need thresholds for FIN.GUIDE checks |
| **4.7 Narrative Analysis** | 15 | 10 INFO, 2 SKIPPED, no evaluative thresholds | Need thresholds for NLP.MDA/NLP.DISCLOSURE checks |
| **5.4 SEC Enforcement** | 4 | 5 SKIPPED, 4 INFO | Enforcement acquisition incomplete + needs thresholds |

### DISPLAY ONLY Subsections (19 questions across 4 subsections)

| Subsection | Questions | Issue |
|---|---|---|
| **1.2 Business Model & Revenue** | 6 | All 8 checks are MANAGEMENT_DISPLAY -- no evaluative thresholds |
| **1.5 Geographic Footprint** | 2 | Only 1 check, MANAGEMENT_DISPLAY |
| **1.7 Competitive Position** | 4 | All 11 checks are MANAGEMENT_DISPLAY |
| **1.8 Macro & Industry Environment** | 4 | All 18 checks are MANAGEMENT_DISPLAY |

The DISPLAY ONLY status is appropriate for some subsections (business model description should display, not evaluate). But some need evaluative thresholds added (geographic concentration risk, competitive moat assessment).

### Known False Triggers (from AAPL audit)

| Check ID | Check Name | Problem | Root Cause |
|---|---|---|---|
| `BIZ.DEPEND.labor` | Concentration Risk Composite | Triggered RED at 150,000 (AAPL employee count) with threshold `>2 labor risk flags` | `field_key=employee_count` but threshold expects a flag count, not an employee count. Data-to-threshold mismatch |
| `BIZ.DEPEND.key_person` | Customer Concentration Risk | INFO at 150,000 (employee count) | `field_key=employee_count` but name is "Customer Concentration" -- wrong field entirely |
| `GOV.BOARD.ceo_chair` | CEO Chair Separation | Triggered RED at 1.0 with threshold `red < 50.0` | Evaluating boolean (1.0 = True = combined) against a numeric "board independence %" threshold. Threshold type mismatch |
| `GOV.PAY.peer_comparison` | Peer Comparison | Triggered RED at 533.0 (CEO pay in unknown units) with threshold `> 75.0` | Unclear if units match (millions vs percentile vs ratio) |
| `FIN.LIQ.position` | Liquidity Position | Triggered RED at 0.8933 with threshold `red < 6.0` | Current ratio 0.89 flagged against threshold 6.0 -- threshold appears uncalibrated for this metric |

## Processing Type Taxonomy

The user's framework identifies 4 processing types:

| Type | Definition | Example | Pipeline Location |
|---|---|---|---|
| **DISPLAY** | Extract and show it | Employee count, auditor name | EXTRACT -> RENDER (no ANALYZE) |
| **EVALUATE** | Extract, compare to threshold | Current ratio < 1.0 = RED | EXTRACT -> ANALYZE -> SCORE |
| **COMPUTE** | Get inputs, apply formula | Altman Z-Score, Beneish M-Score | EXTRACT -> ANALYZE (computed) |
| **INFER** | Recognize patterns across signals | EVENT_COLLAPSE, INFORMED_TRADING | EXTRACT -> ANALYZE (multi-signal) |

Current checks have `content_type` that partially maps:
- `MANAGEMENT_DISPLAY` (98 checks) -> DISPLAY
- `EVALUATIVE_CHECK` (267 checks) -> EVALUATE or COMPUTE
- `INFERENCE_PATTERN` (19 checks) -> INFER

The enrichment data has `depth` fields hinting at acquisition complexity:
- 20 DISPLAY, 270 COMPUTE, 54 INFER, 44 HUNT (from [31-02] decision)

But checks.json itself has no `processing_type` field. The `check_class` field is present but all 384 are `UNKNOWN` (unpopulated).

## Renderer-to-Data Path Audit

### Current Section Renderers

| Renderer | v6 Section | Data Sources | Artifact Gap |
|---|---|---|---|
| `sect1_executive.py` | Synthesis | Scoring, check_results, classification, hazard_profile | Reads from multiple state paths; no unified artifact |
| `sect2_company.py` | 1. COMPANY | `state.company.*`, `state.extracted.governance.board_composition` | Reaches across domains for board data that belongs in Company |
| `sect3_financial.py` | 3. FINANCIAL | `state.extracted.financials.*`, `state.analysis.check_results` | Directly reads check_results dict, format-dependent |
| `sect4_market.py` | 2. MARKET | `state.extracted.market.*`, check_results | Mixes data domain access with check result access |
| `sect5_governance.py` | 4. GOVERNANCE | `state.extracted.governance.*`, check_results | Most complex -- delegates to board, comp, exposure sub-renderers |
| `sect6_litigation.py` | 5. LITIGATION | `state.extracted.litigation.*`, check_results | Clean domain boundary -- litigation data is well-isolated |
| `sect7_scoring.py` | SCORING | `state.scoring.*`, `state.analysis.*` | Reads scoring/analysis results, well-structured |
| `sect8_ai_risk.py` | AI | `state.extracted.ai_risk.*` | Clean -- dedicated model |

### Key Observations

1. **No subsection-level rendering**: Renderers organize by visual section, not by v6 subsection. A question like "1.4.1 How many subsidiaries?" has no rendering path at all.

2. **Check results accessed ad-hoc**: Renderers dig into `state.analysis.check_results[check_id]` with hardcoded check IDs. There's no "get all checks for subsection 1.3" query.

3. **Narrative generation is separate**: `md_narrative_sections.py` and `md_narrative_helpers.py` generate narratives by reading state data, completely separate from check results. The narrative doesn't reference which checks fired.

4. **No "answer" concept**: Questions are answered implicitly by whatever the renderer shows. There's no data structure that says "Question 1.2.1 is answered by these checks producing this result."

## Data Source Coverage

### Acquisition Sources Currently Active

| Source | Check Prefixes | Status |
|---|---|---|
| SEC 10-K | BIZ.*, FIN.*, NLP.*, FWRD.* | Active, well-covered |
| SEC 10-Q | FIN.LIQ.*, FIN.DEBT.* | Active |
| SEC DEF 14A | GOV.*, EXEC.PROFILE.* | Active but parsing incomplete (board size, independence_ratio, tenure all None for AAPL) |
| SEC Form 4 | GOV.INSIDER.*, EXEC.INSIDER.*, STOCK.INSIDER.* | Active |
| SEC 8-K | FWRD.EVENT.*, EXEC.DEPARTURE.* | Active |
| Market Data (yfinance) | STOCK.* | Active |
| SCAC (Playwright) | LIT.SCA.* | Active |
| Web Search (Brave) | FWRD.WARN.* (blind spot) | Active but many FWRD.WARN checks SKIPPED |
| SEC Enforcement | LIT.REG.* | Partially active (many SKIPPED) |

### Data Gaps (acquisition not implemented)

| Data Need | Questions Affected | Potential Source |
|---|---|---|
| Glassdoor/Indeed reviews | 1.9.1, 1.9.6 | Web scraping (Playwright) |
| LinkedIn headcount/departures | 1.9.3, 1.9.5 | Web scraping (Playwright) |
| CFPB complaints | 1.10.1 | CFPB API |
| App ratings | 1.10.1 | App Store/Google Play APIs |
| Web traffic trends | 1.10.5 | SimilarWeb or alternative |
| Social media sentiment | 4.9.1 | Web search aggregation |
| Investigative journalism | 4.9.2 | News search filtering |
| Subsidiary count (Exhibit 21) | 1.4.1 | SEC EDGAR Exhibit 21 parsing |
| VIE/SPE structures | 1.4.2 | 10-K footnotes (LLM extraction) |
| Related-party transactions | 1.4.3 | DEF 14A parsing |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Question-to-check mapping | Custom mapping code | Extend existing `enrichment_data.py` mappings | Infrastructure already exists with SUBDOMAIN_TO_RISK_QUESTIONS and CHECK_TO_RISK_QUESTIONS |
| Section artifact model | New competing state model | Build artifacts from existing state during RENDER | Avoids predecessor failure #3 (multiple state representations) |
| Check subsection assignment | Manual per-check tagging | Derive from existing prefix-based routing in enrichment_data.py | 53+84 mappings already cover most checks |
| False trigger detection | Manual check-by-check review | Systematic comparison of field_key data type vs threshold type | The problem is structural -- field_key points to wrong field or threshold type doesn't match data type |

## Common Pitfalls

### Pitfall 1: Creating a Competing State Representation
**What goes wrong:** Adding QuestionAnswer/SubsectionArtifact as a new field on AnalysisState, duplicating data that already exists in ExtractedData + AnalysisResults.
**Why it happens:** Natural tendency to create a "clean" view of the data.
**How to avoid:** Artifacts are computed at RENDER time from existing state, not stored. They're a rendering concern, not a pipeline concern.
**Warning signs:** New fields on AnalysisState, new stage between ANALYZE and RENDER.

### Pitfall 2: Renumbering Everything at Once
**What goes wrong:** Trying to renumber check sections, renderer sections, and v6 sections to all match, breaking 384 checks and all tests.
**Why it happens:** The mismatch between section numbers is ugly and feels wrong.
**How to avoid:** Use the mapping layer that already exists (enrichment_data.py). The section number in checks.json is a legacy identifier, not a v6 reference.
**Warning signs:** Mass search-and-replace on section numbers, cascading test failures.

### Pitfall 3: Trying to Fix All 79 Non-ANSWERED Questions at Once
**What goes wrong:** Phase becomes unbounded, quality drops.
**Why it happens:** The audit makes every gap visible and they all feel urgent.
**How to avoid:** Prioritize by impact. Zero-coverage subsections first (14 questions), then false triggers (5 checks), then DISPLAY ONLY where evaluation makes sense. PARTIAL questions where acquisition is missing (Glassdoor, LinkedIn, etc.) are deferred -- they need MCP/scraping work that's a separate phase.
**Warning signs:** Creating new web scraping infrastructure, building new MCP integrations.

### Pitfall 4: Over-Engineering the Artifact Model
**What goes wrong:** Building a complex ORM-like artifact system with many new Pydantic models, adding weeks of work.
**Why it happens:** The concept of "structured output artifact per subsection" is appealing architecturally.
**How to avoid:** Start simple -- a function that, given a subsection ID, returns the relevant check results and display data. The artifact "model" can be a typed dict or simple dataclass, not a full Pydantic hierarchy.
**Warning signs:** More than 2-3 new model classes, artifact model exceeding 200 lines.

### Pitfall 5: Stripping Detail During Refactoring
**What goes wrong:** Simplifying rendering by removing descriptive text, evidence narratives, or check-level detail.
**Why it happens:** Existing renderers are complex with many edge cases.
**How to avoid:** User explicitly objects to removing descriptive information. Every check must still fire, every detail must be preserved.
**Warning signs:** Render output getting shorter, "simplified" rendering paths.

## Scope Boundaries

### In Scope (Phase 33)
1. Add `v6_subsection_ids` to checks.json (all 384 checks mapped)
2. Design subsection artifact structures for all 45 subsections
3. Create checks for 5 zero-coverage subsections using existing data
4. Fix 5 known false triggers (data-to-threshold mismatches)
5. Verify all 22 TRIGGERED checks make sense in their question context
6. Wire artifact-to-renderer for each subsection
7. End-to-end validation: AAPL worksheet with explicit per-question status

### Out of Scope (Future phases)
- New web scraping (Glassdoor, LinkedIn, app stores) -- needs MCP/Playwright work
- CFPB/NHTSA API integration -- acquisition infrastructure
- Renumbering check sections to match v6 -- mapping layer is sufficient
- New data acquisition for currently SKIPPED checks -- acquisition phase
- Renderer visual redesign -- presentation concern

## Existing Code Files Affected

### Must Modify
| File | Lines | Change |
|---|---|---|
| `brain/checks.json` | ~7000 | Add v6_subsection_ids to all 384 checks |
| `brain/enrichment_data.py` | 200 | Verify/complete CHECK_TO_RISK_QUESTIONS for all checks |
| `brain/brain_enrich.py` | ~300 | Populate v6_subsection_ids from enrichment_data |
| `stages/analyze/check_field_routing.py` | 329 | Fix false trigger field_key mappings |
| `stages/render/sections/sect2_company.py` | 355 | Add subsection-level rendering for 1.4, 1.5, etc. |
| `stages/render/sections/sect6_litigation.py` | ~400 | Add rendering for 5.7, 5.8, 5.9 subsections |

### Must Create
| File | Purpose |
|---|---|
| `stages/render/section_artifacts.py` | SubsectionArtifact builder (computed at render time) |
| New checks in checks.json | ~15-20 new checks for zero-coverage subsections |

### Must Not Modify
| File | Reason |
|---|---|
| `models/state.py` | No new state fields -- artifacts are render-time computed |
| `pipeline.py` | No new pipeline stages |
| `stages/acquire/` | No new acquisition -- out of scope |

## State of the Art

### Current System Maturity

| Area | Status | Completeness |
|---|---|---|
| Question framework (v6) | APPROVED, canonical | 231 questions defined |
| Check registry | Active | 384 checks, 377 AUTO |
| Check-to-question mapping | Partial (enrichment_data.py) | 53 subdomain + 84 explicit mappings |
| Check subsection assignment | Missing from checks.json | 0 checks have subsection_id |
| Brain DuckDB schema | Designed | risk_questions column exists but unpopulated |
| False trigger detection | Identified | 5 known, likely more |
| Zero-coverage subsections | Identified | 5 subsections, 14 questions |
| Section artifacts | Not started | No artifact model exists |
| Renderer-to-artifact wiring | Not started | Renderers reach into state ad-hoc |

### What Phase 32 Built (Inputs to Phase 33)

1. **QUESTION-AUDIT.md** (2,323 lines): Complete diagnostic tracing all 231 questions to AAPL pipeline output
2. **QUESTIONS-FINAL.md**: v6 taxonomy -- the canonical 231 questions
3. **brain/checks.json v9.0**: 384 checks with enriched metadata (content_type, data_strategy, field_key)
4. **enrichment_data.py**: SUBDOMAIN_TO_RISK_QUESTIONS and CHECK_TO_RISK_QUESTIONS mappings
5. **brain_schema.py**: DuckDB schema with risk_questions column ready for population
6. **QUESTION-AUDIT methodology**: Can be re-run after Phase 33 to verify improvement

## Open Questions

1. **Artifact granularity:** Should artifacts be per-subsection (45) or per-question (231)? Per-subsection is likely right -- questions within a subsection share data and checks. Per-question would create 231 tiny artifacts with heavy overhead.
   - **Recommendation:** Per-subsection with question-level status tracking inside each artifact.

2. **DISPLAY ONLY subsections:** Should 1.2 (Business Model), 1.7 (Competitive Position), 1.8 (Macro Environment) remain DISPLAY ONLY, or should they get evaluative thresholds?
   - **Recommendation:** Some are genuinely display (1.2.1 business description). Others should evaluate (1.7.3 peer litigation frequency could have a threshold). Decide per-question during planning.

3. **Check section number field:** Should the `section` field in checks.json be updated to match v6, or left as-is with mapping?
   - **Recommendation:** Leave as-is. The enrichment_data.py mapping layer handles the translation. Mass renumbering risks breaking the check engine's section-based routing and all tests.

4. **FWRD prefix distribution:** FWRD checks are currently assigned to section 6 in checks.json but map to v6 sections 1 (risk calendar), 3 (distress), and 4 (disclosure/narrative). How to handle?
   - **Recommendation:** The enrichment_data.py already maps FWRD.EVENT->1.11, FWRD.WARN->3.6, FWRD.DISC->4.6, FWRD.NARRATIVE->4.7, FWRD.MACRO->1.8. Use these existing mappings in the v6_subsection_ids assignment.

5. **Audit re-run timing:** Should the QUESTION-AUDIT be re-run after each plan or only at the end?
   - **Recommendation:** Re-run at the end of Phase 33 as the final validation step (success criterion 7).

## Sources

### Primary (HIGH confidence)
- `QUESTION-AUDIT.md`: 2,323-line diagnostic tracing all 231 questions to AAPL output
- `QUESTIONS-FINAL.md`: v6 canonical taxonomy (231 questions, 45 subsections)
- `brain/checks.json`: 384 checks examined directly
- `brain/enrichment_data.py`: Existing question mapping infrastructure
- `brain/brain_schema.py`: DuckDB schema with risk_questions column
- `stages/analyze/check_engine.py`, `check_mappers.py`, `check_field_routing.py`: Check execution pipeline
- `stages/render/word_renderer.py`, `sections/sect2_company.py`, etc.: Renderer implementations
- `models/state.py`: AnalysisState, ExtractedData, AnalysisResults models

### Secondary (MEDIUM confidence)
- Project MEMORY.md: Known extraction data gaps, false trigger patterns
- STATE.md decisions: Phase 31-32 enrichment decisions

## Metadata

**Confidence breakdown:**
- Architecture: HIGH - based on direct examination of all relevant code
- Gap analysis: HIGH - based on QUESTION-AUDIT.md verified against AAPL run
- False triggers: HIGH - verified by examining check definitions and AAPL output
- Scope estimation: MEDIUM - new check count (15-20) is estimated
- Artifact design: MEDIUM - design not validated against real rendering needs

**Research date:** 2026-02-20
**Valid until:** 2026-03-20 (stable internal architecture)
