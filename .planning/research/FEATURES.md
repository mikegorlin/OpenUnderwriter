# Feature Landscape: v12.0 Output Quality & Architectural Integrity

**Domain:** Data-intensive reporting systems -- typed output contracts, data consistency guarantees, output sanitization, and quality gates applied to a D&O underwriting worksheet pipeline.
**Researched:** 2026-03-27
**Context:** Existing system has 90+ context builders returning `dict[str, Any]`, 100+ Jinja2 templates, 600+ brain signals, 7-stage pipeline. This milestone adds architectural guarantees to eliminate the 5 root causes behind CUO audit failures.

---

## Table Stakes

Features that production data-intensive reporting systems universally implement. Missing any of these means the system ships defects to users.

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| **Typed Output Contracts** (context builder -> template boundary) | Every production financial reporting system (Bloomberg, FactSet, S&P CIQ) enforces typed contracts at rendering boundaries. Untyped `dict[str, Any]` is the #1 source of template runtime errors -- `None` where `str` expected, `list` where `dict` expected, missing keys. Pydantic v2 models at every context builder return eliminate entire error classes. The system already uses Pydantic everywhere else; the context builder boundary is the last untyped gap. | HIGH -- 90+ context builders to retrofit, but incremental per-builder | Existing context builders, Pydantic v2, Jinja2 templates | Start with the 10 highest-traffic builders (company, financials, governance, litigation, scoring, market). Each builder gets a `*Context` Pydantic model; templates consume typed fields. CI gate: Pyright checks template variable access against context model. Use Pydantic (not TypedDict) because project already uses Pydantic and gets validation + serialization for free. |
| **Canonical Metrics Registry** (single computed value per metric) | Bloomberg Terminal never shows two different revenue numbers on the same screen. FactSet reconciles all metrics to a single source. When revenue appears in executive summary, financial tables, peer comparison, and scoring commentary, it must be identical. Currently 90+ context builders independently extract revenue/margins/CEO/exchange from state, producing contradictions across sections. This is the consistency dimension of data quality -- the most critical dimension for financial reporting systems. | MEDIUM -- define 30-50 canonical metrics, replace scattered lookups with registry calls | AnalysisState, XBRL data, all context builders that read financial/company data | Registry is a `CanonicalMetrics` class initialized from AnalysisState with `@cached_property` methods. Metrics: revenue, net_income, total_assets, market_cap, employees, CEO name, exchange, years_public, SCA count, score, tier, etc. Every context builder calls `metrics.revenue` instead of independently navigating `state.extracted.financials.statements[...][...]`. Eliminates the root cause of all cross-section contradictions. |
| **Output Sanitization Layer** (strip artifacts from final HTML) | Every production report system has a post-render sanitization pass. Currently the system has ad-hoc QA grep patterns that catch markdown artifacts (`**bold**`, `###`), debug strings (`[DEBUG]`, `signal_id=`), Python repr leaks (`{'key': 'value'}`), factor codes in prose (`F.7 = 5/8`), and LLM formatting leaks (` ```json`). These grep patterns run after the fact; a deterministic sanitization layer prevents them from reaching the user. The arc42 quality model calls this "output encoding at every rendering boundary." | LOW-MEDIUM -- single-pass regex + BeautifulSoup transform on complete HTML | Final rendered HTML output, BeautifulSoup or lxml | Single function: `sanitize_output(html: str) -> str`. Runs after all Jinja2 rendering completes, before file write. Catches: markdown syntax, raw dicts/lists, debug prefixes, factor codes in prose, raw unformatted floats, NaN/None string literals, template variable leaks (`{{ }}`), LLM code fence artifacts. Log stripped artifacts for debugging (log sanitization events per arc42 guidance). Deterministic, fast (<100ms), auditable. |
| **Cross-Section Consistency Checker** | When revenue is "$3.05B" in the executive summary but "$3.1B" in financial tables and "$3,050M" in peer comparison, underwriters lose trust in the entire document. Power BI and Tableau enforce that the same metric resolves to the same formatted value everywhere. This is the single most common audit failure in the current system. | MEDIUM -- extract rendered instances of key facts, compare | Canonical Metrics Registry (makes this trivial), rendered HTML | Post-render verification pass: parse final HTML, extract all instances of ~15 key metrics (revenue, CEO name, exchange, SCA counts, score, tier), verify they match. Fail the render with explicit error if contradictions found. Implementation: annotate template spans with `data-metric="revenue"` so the checker knows which elements to compare. If canonical registry exists, this becomes a trivial "did formatting diverge?" check rather than "did data diverge?" check. |
| **Section Completeness Gate** | No financial terminal ships a table that is 80% "N/A." Bloomberg suppresses sections with insufficient data rather than displaying broken layouts. BI dashboards use data quality thresholds (typically 70-90% completeness) to determine whether a section is production-ready. The current system renders all sections regardless of data availability, producing walls of "N/A" that underwriters interpret as system failure rather than data absence. | LOW -- count non-null fields per section context, suppress below threshold | Context builders (know what data is available), template rendering logic | Per-section completeness score: `fields_populated / fields_expected`. Threshold: suppress if <50% populated (configurable per section). Replace with a "Data Unavailable" card showing what was attempted and what sources were checked. Some sections (scoring, executive summary) marked `required=True` and never suppressed. Threshold can be section-specific: governance might tolerate 40% (sparse DEF 14A), financials should require 80% (XBRL is reliable). |
| **Real-State Integration Tests** | Bloomberg QA runs against real market data snapshots, not mocks. dbt validates transformations against real data fixtures. The current system has 1,168 MagicMock instances without `spec_set`, meaning tests pass against nonexistent state paths -- they validate nothing. This is the testing equivalent of checking that your calculator's buttons light up without verifying arithmetic. | HIGH -- creating fixtures, migrating 1,168 mocks | Real `state.json` files from pipeline runs (already exist in `output/*/`), pytest fixtures | Strategy: (1) Create 3-5 golden state fixtures from real runs (AAPL, RPM, V -- different sizes/sectors). (2) New tests use `load_real_state("AAPL")` fixture. (3) Migrate highest-value tests first (context builders that build render dicts). (4) CI gate: no new `MagicMock()` without `spec_set=AnalysisState` or the specific Pydantic model. (5) Long-term: deprecate all unspec'd mocks. Not all 1,168 need migration -- triage by value (context builder tests first, client mocks can stay). |

## Differentiators

Features that set the system apart from generic reporting tools. Not universally expected, but high-value for this domain.

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| **Contextual Signal Validation** (post-evaluation cross-check) | Generic BI tools validate data completeness. This system needs to validate *analytical correctness* -- a signal claiming "CEO tenure < 2 years" when the CEO has been there 15 years is worse than no signal at all. Cross-checking signal results against the state that produced them catches false positives from stale data, wrong entity resolution, or evaluator bugs. No off-the-shelf tool does this because it is domain-specific analytical validation. | MEDIUM -- iterate evaluated signals, compare claims against state | Signal evaluation results, AnalysisState, signal YAML definitions | Post-ANALYZE pass: for each triggered signal, verify key assertions. Examples: IPO signals check `years_public > 5` and suppress if true. CEO-change signals verify `current_ceo` matches state. Financial distress signals verify actual ratios. ~20 high-impact cross-checks initially. Each check is a function: `(signal_id, signal_result, state) -> ValidOrSuppressed`. Logged as "contextually suppressed" in audit trail. |
| **Litigation Classification & Consolidation** | Unique to legal/insurance analytics. Same lawsuit appears as "In re Company Securities Litigation" in SCAC, "Smith v. Company" in CourtListener, and "securities class action" in 10-K Item 3. Production legal analytics platforms (Lex Machina, Westlaw) classify by legal theory and deduplicate across sources. The current system shows duplicates and sometimes misclassifies coverage side (D&O vs EPL vs fiduciary). | HIGH -- NLP/rule-based case matching, legal theory taxonomy | Litigation data from multiple sources (SCAC, CourtListener, 10-K, web), case type taxonomy | Components: (1) Case type classifier: SCA, derivative, SEC enforcement, regulatory, breach of fiduciary -- from complaint text + filing metadata. (2) Deduplicator: fuzzy match on case name + parties + court + date range. (3) Coverage side: D&O vs EPL vs fiduciary vs cyber vs crime. (4) Missing field acquisition: if SCAC has case but no resolution, search CourtListener for outcome. Build taxonomy as YAML config, not hardcoded. This is substantial NLP work -- could be its own milestone. |
| **Template Variable Type Validation** (CI gate) | Static analysis of Jinja2 templates against output schemas catches template bugs before runtime. Most Jinja2 projects skip this because templates are "just strings." With 100+ templates and typed context models, a CI gate that parses template variable references and checks against the context Pydantic model prevents `UndefinedError` and silent `None` rendering. No off-the-shelf solution exists for Pydantic + Jinja2 type checking. | MEDIUM -- Jinja2 AST parsing, cross-reference with Pydantic field names | Typed Output Contracts (must exist first), Jinja2 Environment, CI pipeline | Use `jinja2.Environment.parse()` to extract variable references from each template. Cross-reference against the corresponding `*Context` Pydantic model's field names. Flag: undefined variables, wrong nesting depth, filter usage on wrong types. Catches 80% of template bugs with 10% of the effort of a full type checker. Does NOT attempt filter type inference or deep conditional branch analysis (see Anti-Features). |
| **Metric Provenance Trail** | Beyond consistency (same number everywhere), show *where* each number came from. Bloomberg shows "Source: Company Filing, FY2025 10-K" next to every metric. The system already has `source` and `confidence` fields on Pydantic models but they do not propagate to templates. Making provenance visible gives underwriters confidence in the data. | LOW-MEDIUM -- plumb existing source metadata through canonical registry to templates | Canonical Metrics Registry, existing source/confidence fields on models | Each canonical metric carries `(value, source, confidence, as_of_date)`. Templates can optionally render source attribution. Initially show in audit appendix; later as tooltips in HTML. This is additive -- existing rendering unchanged, new `data-source` attributes on metric spans. |
| **Stock Charts: 1-Year and 5-Year Side by Side** | Every institutional equity research report shows price charts vs sector benchmark. The current system has stock data but the chart presentation is not the first thing underwriters see in the Stock & Market section. Placing 1-year and 5-year charts side-by-side vs sector ETF as the section opener matches institutional presentation standards. | MEDIUM -- matplotlib chart generation, dual-panel layout | Existing stock data, sector ETF data, matplotlib infrastructure | Two charts: (1) 1-year daily price vs sector ETF, annotated with significant events (earnings, insider sales, drops >10%). (2) 5-year weekly price vs sector ETF, annotated with SCA filings, restatements, CEO changes. Both use existing `_stock_chart_mpl.py` infrastructure. Layout: side-by-side in the section, full-width in PDF. |

## Anti-Features

Features to explicitly NOT build. These are tempting but wrong for this system at this stage.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Full Jinja2-to-Python type checker** (compile-time type safety across template boundary) | Jinja2 is fundamentally untyped. Building a complete type checker that handles filters, macros, `{% for %}` loops, conditional branches, and template inheritance is a multi-month project. Attempts exist (jinja2-typeguard, jinjalint) but none are production-ready for Pydantic integration. Diminishing returns after basic variable name checking. | Basic CI gate: parse template AST, check top-level variable names exist in context model. Skip filter type inference and deep nesting. Catch 80% of bugs with 10% of the effort. |
| **Runtime schema validation on every template render** | Validating the full context dict through Pydantic on every render adds 200-500ms per section (90+ sections = 20-45s overhead). The pipeline already takes 10-20 minutes; the render stage should be fast. Production systems validate at boundaries, not every function call. | Validate in CI (template type gate) and in integration tests (real-state fixtures). Runtime validation only in `--debug` mode or when `VALIDATE_RENDER=1` env var is set. Production renders trust the pipeline. |
| **Automated metric reconciliation** (auto-fix contradictions) | If revenue differs between executive summary and financial tables, the system should NOT silently pick one. That masks data quality bugs. Auto-reconciliation is what Bloomberg does internally, but Bloomberg has a single authoritative data feed. This system has multiple extraction paths, and contradictions indicate extraction bugs that need fixing. | Fail the render with an explicit error: "Revenue contradiction: exec_summary=$3.05B vs financials=$3.1B. Fix the context builder." Force the developer to resolve at the source. The canonical metrics registry prevents this from happening in the first place. |
| **LLM-based output sanitization** | Using an LLM to "clean up" the final HTML is slow ($0.01-0.05 per call), non-deterministic, and introduces new hallucination risk into the output. The sanitization layer must be rule-based and deterministic. | Regex + BeautifulSoup rules. Deterministic, fast (<100ms), auditable. Log what was stripped so patterns can be added to prevent recurrence at the template level. |
| **Generic data quality framework** (Great Expectations, Soda, dbt-expectations) | These tools validate data warehouse tables -- row counts, column distributions, statistical properties. They do not validate rendered documents. "Does the CEO name in section 3 match section 7?" is not a check Great Expectations can express. Adding a 500MB framework dependency for 15 custom checks is wrong. | Custom quality checks: 15-20 focused assertions in a single Python module (~200 lines). No framework dependency. The checks are domain-specific (D&O worksheet structure), not generic data profiling. |
| **Per-field completeness tracking in templates** | Tempting to add `{% if field.is_available %}` guards around every template element. This makes templates unreadable (100+ conditional blocks per template) and shifts data quality responsibility to the wrong layer. Templates should be dumb renderers per the brain portability principle. | Context builders handle None/missing with `safe_float()`, `na_if_none()`, and format defaults. Templates receive clean, pre-formatted strings. Section completeness gate decides whether to render the section at all. Templates never check data availability. |
| **Migrating all 1,168 MagicMocks at once** | Big-bang mock migration will break hundreds of tests simultaneously, creating a multi-day stabilization effort that blocks all other work. Many of those mocks test low-level client behavior where mocking is appropriate. | Triage by value: migrate context builder tests first (highest ROI -- these test the exact boundary being typed). Keep client/acquisition mocks where mocking is architecturally correct. CI gate prevents NEW unspec'd mocks. Target: migrate 200-300 highest-value mocks, not all 1,168. |

## Feature Dependencies

```
Canonical Metrics Registry (FOUNDATION -- do first)
  |
  +--> Cross-Section Consistency Checker (trivial once registry exists)
  |
  +--> Metric Provenance Trail (extends registry with source metadata)
  |
  +--> Typed Output Contracts (context models consume registry, not raw state)

Typed Output Contracts
  |
  +--> Template Variable Type Validation (CI gate needs types to check against)
  |
  +--> Section Completeness Gate (completeness calculated from typed context fields)

Output Sanitization Layer (INDEPENDENT -- can start immediately)

Contextual Signal Validation (INDEPENDENT -- operates on signal results + state)

Litigation Classification & Consolidation (INDEPENDENT -- operates on litigation data)

Real-State Integration Tests (INDEPENDENT -- can start immediately)

Stock Charts (INDEPENDENT -- rendering feature, no architectural dependency)
```

## MVP Recommendation

### Phase 1 -- Foundation (do first, everything depends on it)
Prioritize:
1. **Canonical Metrics Registry** -- eliminates contradictions immediately, makes consistency checker trivial, simplifies all context builders
2. **Output Sanitization Layer** -- independent, low complexity, immediate quality improvement for every pipeline run
3. **Contextual Signal Validation** -- independent, catches false positives that undermine underwriter trust

Rationale: These three features address 3 of the 5 root causes (metric contradictions, output artifacts, false positive signals) with no inter-dependencies. Can be built in parallel.

### Phase 2 -- Typed Contracts (incremental, highest architectural ROI)
4. **Typed Output Contracts** -- start with top 10 context builders (company, financials, governance, litigation, scoring, market, analysis, calibration, pattern, audit), expand over time
5. **Section Completeness Gate** -- quick win once typed contracts provide field inventory

Rationale: Typed contracts are the architectural centerpiece. They make the template boundary safe and enable the CI gate. But they require incremental migration -- do not attempt all 90+ builders at once.

### Phase 3 -- Verification Infrastructure
6. **Cross-Section Consistency Checker** -- trivial once canonical registry exists; post-render verification pass
7. **Real-State Integration Tests** -- migrate 200-300 highest-value mocks (context builder tests), CI gate on new mocks
8. **Template Variable Type Validation** -- CI gate, requires typed contracts to exist
9. **Stock Charts** -- rendering feature, fits naturally after verification infrastructure ensures rendering quality

**Defer to separate milestone:**
- **Litigation Classification & Consolidation** -- HIGH complexity, substantial NLP work, could be a 2-week effort on its own. The deduplication and legal theory classification requires taxonomy design, fuzzy matching, and coverage-side rules. Worth doing but not a prerequisite for the quality guarantee features.
- **Metric Provenance Trail** -- additive on top of canonical registry, defer until registry is stable and underwriters request it

## Complexity Budget

| Feature | Estimated Effort | Risk | Phase |
|---------|-----------------|------|-------|
| Canonical Metrics Registry | 2-3 days | LOW -- well-understood pattern | 1 |
| Output Sanitization Layer | 1-2 days | LOW -- regex rules, test against known artifacts | 1 |
| Contextual Signal Validation | 2-3 days | LOW -- 20 focused cross-checks | 1 |
| Typed Output Contracts (10 builders) | 3-5 days | MEDIUM -- careful migration, test updates | 2 |
| Section Completeness Gate | 1 day | LOW -- simple counting on typed fields | 2 |
| Cross-Section Consistency Checker | 1-2 days | LOW -- if canonical registry exists | 3 |
| Real-State Integration Tests (200-300 mocks) | 5-7 days | MEDIUM -- fixture creation, triage | 3 |
| Template Variable Type Validation | 2-3 days | MEDIUM -- Jinja2 AST parsing is fiddly | 3 |
| Stock Charts (1yr + 5yr) | 2-3 days | LOW -- extends existing matplotlib infra | 3 |
| **Total** | **~20-30 days** | | |

## Sources

- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/) -- typed validation, runtime contracts (HIGH confidence)
- [TypedTemplate: Pydantic + Template Engine](https://github.com/Shakakai/typedtemplate) -- prior art for typed template contexts (MEDIUM confidence -- small project)
- [arc42 Quality Model: Input Sanitization / Output Encoding](https://quality.arc42.org/approaches/input-sanitization-output-encoding) -- sanitization architecture patterns (HIGH confidence)
- [Data Quality in Power BI: 12 Tests Before Dashboard Launch](https://lets-viz.com/blogs/power-bi-data-quality-tests-dashboard-validation/) -- completeness gates in production BI (MEDIUM confidence)
- [Data Consistency Explained (Atlan)](https://atlan.com/data-consistency-101/) -- cross-section consistency patterns (MEDIUM confidence)
- [Canonical Data Model as Single Source of Truth (CGI)](https://www.cgi.com/sites/default/files/2021-12/canonical-data-model-whitepaper-2021-en.pdf) -- canonical metrics architecture (HIGH confidence)
- [Monte Carlo: The Essential Guide to Data Consistency](https://www.montecarlodata.com/blog-data-consistency/) -- consistency monitoring in data platforms (MEDIUM confidence)
- [dbt: Data Quality Dimensions](https://www.getdbt.com/blog/data-quality-dimensions) -- completeness, accuracy, consistency dimensions (HIGH confidence)
- [Metaplane: Data Consistency Definition and Best Practices](https://www.metaplane.dev/blog/data-consistency-definition-examples) -- format, semantic, transactional consistency types (MEDIUM confidence)
- [Ben Hoyt: Don't Sanitize Input, Escape Output](https://benhoyt.com/writings/dont-sanitize-do-escape/) -- output encoding philosophy (HIGH confidence)
