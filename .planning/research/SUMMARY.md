# Research Summary: v12.0 Output Quality & Architectural Integrity

**Domain:** Typed output contracts, canonical metrics, contextual signal validation, cross-section consistency, and quality gates for existing Pydantic/Jinja2 D&O underwriting pipeline
**Researched:** 2026-03-27
**Overall confidence:** HIGH

## Executive Summary

v12.0 is an architectural integrity milestone, not a feature milestone. The existing 7-stage pipeline (RESOLVE through RENDER), 90+ context builders, 239 Jinja2 templates, and 600+ brain signals produce comprehensive D&O worksheets, but the `dict[str, Any]` boundary between context builders and templates allows raw Python objects, conflicting metric values, and false positive signals to leak into the final output. The 5 root causes behind all CUO audit failures are: (1) untyped context builder returns, (2) same metric computed independently by multiple builders, (3) signals firing without company context validation, (4) unclassified and duplicated litigation entries, and (5) markdown/debug artifacts in rendered HTML.

The recommended approach introduces 6 new architectural components without modifying any of the 239 Jinja2 templates or adding new dependencies. The components are: a CanonicalMetricsRegistry (compute-once with XBRL-first source priority), Typed Context Models (Pydantic BaseModel per section with incremental migration via validation wrappers), a ContextualSignalValidator (YAML-driven rules applied post-ANALYZE), a CrossSectionConsistencyChecker (verify same fact matches everywhere), a SectionCompletenessGate (suppress >50% N/A sections), and an OutputSanitizer (strip leaked artifacts from final HTML).

The critical architectural insight is that all 6 components are additive with fallback paths. Typed context models use try/except validation wrappers that fall back to existing untyped dicts on failure. The consistency checker starts in report-only mode. The signal validator uses YAML rules, not Python if/else chains. No template changes are required because typed models produce the exact dict keys templates already expect via `model_dump(by_alias=True)`. This means the migration can be done one context builder at a time, with zero risk of breaking the existing render pipeline.

The build order is dependency-driven: (1) CanonicalMetricsRegistry first because it enables cross-section consistency by construction, (2) Typed Context Models for the 5 highest-leakage sections, (3) ContextualSignalValidator independently (can parallelize with Phase 2), (4) Quality gates (consistency checker, section gate, sanitizer), (5) CI integration and blocking mode promotion.

## Key Findings

**Stack:** Zero new dependencies. Pydantic v2 (installed), Jinja2 meta introspection (built-in), BeautifulSoup4 (installed), stdlib re -- all sufficient.

**Architecture:** Six new components inserted into existing pipeline at three points: post-ANALYZE (signal validator), pre-render (canonical metrics, typed models, consistency checker, section gate), post-render (output sanitizer). No new pipeline stages. No template changes.

**Critical pitfall:** Pydantic rigidity killing graceful degradation. The existing system handles missing data through 383 `safe_float()` call sites and `format_na` filters. Strict typed models must use `Optional[str] = None` defaults for every field, never required fields for data that can be missing. The validation wrapper with untyped fallback is the essential safety mechanism.

## Implications for Roadmap

Based on research, suggested phase structure:

1. **CanonicalMetricsRegistry** - Foundation for all cross-section consistency
   - Addresses: Metric duplication root cause (revenue computed in 4+ places)
   - Avoids: Big-bang migration (registry exists but nothing reads from it yet)

2. **Typed Context Models (5 priority sections)** - Eliminate untyped leakage at highest-traffic boundaries
   - Addresses: Typed output contracts, template variable type validation
   - Avoids: Big-bang migration (one builder at a time, validation wrappers with fallback)

3. **ContextualSignalValidator** - Eliminate false positive signals systematically
   - Addresses: IPO signals on old companies, insolvency on mega-caps, stale temporal signals
   - Avoids: Python if/else chains (YAML rules, brain portability)
   - Note: Independent of Phases 1-2, can run in parallel

4. **Quality Gates** - Cross-section consistency, section completeness, output sanitization
   - Addresses: Remaining CUO audit failure root causes
   - Avoids: Eager enforcement (report-only first, blocking only at zero inconsistencies)

5. **CI Integration & Blocking Mode** - Lock in guarantees
   - Addresses: Real-state tests replacing 1,168 unspec'd MagicMocks, template type validation gate
   - Avoids: Premature blocking (only after root causes are fixed)

**Phase ordering rationale:**
- Phase 1 first because canonical registry is the foundation for consistency (Phases 2 and 4 reference it)
- Phase 2 before Phase 4 because typed models enable the section completeness gate
- Phase 3 is independent (different pipeline insertion point) and can parallelize with Phase 2
- Phase 4 after 1-2 because consistency checking is most effective against canonical values
- Phase 5 last because blocking mode requires zero existing inconsistencies first

**Research flags for phases:**
- Phase 2: Needs careful field audit per builder -- template variable extraction via `jinja2.meta.find_undeclared_variables()` identifies required keys, but type inference requires manual review
- Phase 3: Safe expression parser for YAML conditions must be designed carefully -- no `eval()`, no arbitrary code execution
- Phase 4: Initial consistency check will find many existing inconsistencies -- expect a "fix the root causes" sub-phase before blocking mode
- Phase 5: MagicMock migration is high effort (1,168 instances) -- triage by value, context builder tests first

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new dependencies. All capabilities exist in installed packages. Verified against `pyproject.toml` and existing usage patterns. |
| Features | HIGH | Root causes identified from direct codebase analysis (90+ context builders inspected, 239 templates counted, `dict[str, Any]` boundary confirmed). CUO audit failures traced to specific code paths. |
| Architecture | HIGH | Component designs based on existing codebase patterns (`state_paths.py` typed accessors, `should_suppress_insolvency()` contextual suppression, `health_check.py` post-render validation, brain YAML-driven rules). All patterns proven in production. |
| Pitfalls | HIGH | Sourced from project experience: Pydantic rigidity risk from `safe_float()` audit (383 call sites), template variable explosion risk from template count (239), MagicMock false-pass risk from spec audit (1,168 unspec'd instances). |

## Gaps to Address

- **Template variable registry:** Need to extract all `{{ var }}` references from 239 templates and cross-reference against context builder output keys. `jinja2.meta.find_undeclared_variables()` handles this but requires parsing all templates. This is a Phase 2 prerequisite.
- **Safe expression parser design:** The contextual validator needs a condition parser that allows comparisons and boolean ops but not arbitrary code. Libraries like `simpleeval` exist but add a dependency. A custom parser for the limited grammar needed (~20 operators) is preferable.
- **Existing inconsistency baseline:** Running the consistency checker against current output will reveal how many cross-section disagreements exist today. This number determines how long the "report-only to blocking" transition takes.
- **MagicMock triage:** Not all 1,168 unspec'd mocks need migration. Need to categorize by test value: context builder tests (highest priority), client mocks (keep), signal evaluator tests (medium priority).

## Sources

### Primary (HIGH confidence)
- Existing codebase: direct analysis of `src/do_uw/` (~420 Python files, 90+ context builders, 239 Jinja2 templates)
- `assembly_registry.py`: confirmed `dict[str, Any]` boundary at `BuilderFn` type definition
- `state_paths.py`: confirmed typed accessor pattern (21 tests passing) as architectural precedent
- `should_suppress_insolvency()` in `red_flag_gates.py`: confirmed contextual suppression as pattern precedent
- `health_check.py` + `semantic_qa.py`: confirmed post-render validation patterns
- `brain/signals/*.yaml`: confirmed YAML-driven rules pattern (600+ signals in production)
- Pydantic v2 semantics: `model_validate()`, `model_dump()`, `ConfigDict(extra="forbid")`, `Field(alias=...)`

---
*Research completed: 2026-03-27*
*Ready for roadmap: yes*
