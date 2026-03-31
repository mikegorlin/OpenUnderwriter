# Phase 92: Rendering Completeness - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Guarantee that every piece of extracted data reaches the output, with CI enforcement, post-pipeline audit trails, and cross-ticker validation proving nothing is silently lost. The system already has coverage.py (walk_state_values, check_value_rendered, compute_coverage), contract_validator.py (facet-template-signal), brain_audit.py, and qa_compare.py. This phase wires them into a complete enforcement pipeline.

</domain>

<decisions>
## Implementation Decisions

### CI gate strictness
- Hard fail: adding an extraction field without a render path breaks the build
- Static analysis approach: scan context builders and Jinja2 templates to verify every model field has a code path that references it — no pipeline run needed in CI
- Exclusions declared in a separate config file (render_exclusions.yaml in config/) with a reason string per field — not buried in code
- Developers must explicitly add excluded fields to the config file with justification; any field not rendered and not excluded = build failure

### Audit report format
- Post-pipeline audit appended to the HTML worksheet as a collapsed "Data Audit" appendix section (collapsed by default)
- Two categories displayed: "Excluded by policy (N fields)" and "Unrendered (M fields)" — excluded = expected, unrendered = potential problem
- Audit results also written to state.json under a `render_audit` key for programmatic access by qa_compare.py and other scripts

### Health check heuristics
- All health issues are warnings (never block pipeline) — flagged in the audit appendix
- Raw LLM text detection via known markers: curated pattern list in config (e.g., "Based on the filing...", "According to the...", "I cannot determine...", markdown formatting ##/**bold**, JSON/dict literals in rendered text)
- 0.0 placeholder detection uses a context-aware allowlist of fields where zero is valid (dividends, short_interest, etc.) — any 0.0 NOT on the allowlist gets flagged
- Empty percentage detection also catches 'N/A' and 'Not Available' strings in numeric-typed fields — distinguishes data gaps from intentional omissions via the exclusion config

### Cross-ticker QA scope
- Validation tickers: AAPL + RPM (diverse segment structures, already in qa_compare)
- Extend qa_compare.py (not a separate script) — add business profile validation as new checks alongside existing feature parity checks
- Severity-based reporting: HIGH (field in state.json but not rendered), MEDIUM (field empty in state.json = data gap), LOW (company genuinely doesn't have that data)
- QA also validates that the Data Audit appendix section and render_audit key in state.json are present for each ticker — ensures completeness checks themselves aren't silently missing

### Claude's Discretion
- Exact LLM marker pattern list contents (will be refined through testing)
- Which zero-valid fields go on the allowlist (derive from model inspection)
- render_exclusions.yaml structure and initial exclusion set (migrate from coverage.py EXCLUDED_PATHS)
- Static analysis implementation details (AST parsing vs regex vs template introspection)
- Audit appendix HTML styling and layout within existing design system

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `coverage.py`: `walk_state_values()` extracts all non-null leaf values, `check_value_rendered()` does format-aware matching, `compute_coverage()` returns CoverageReport — core of runtime audit
- `contract_validator.py`: `validate_facet_template_agreement()` checks template existence, `validate_signal_references()` validates signal IDs — CI contract patterns
- `brain_audit.py`: `BrainAuditReport` with severity-based findings — model for health check findings
- `qa_compare.py`: `OutputProfile` dataclass + `compare_profiles()` — extend for business profile validation
- `test_render_coverage.py`: 90+ tests for coverage framework — extend for new CI contract
- `test_contract_enforcement.py`: Existing CI contract test patterns

### Established Patterns
- Coverage exclusions: `EXCLUDED_PATHS` set in coverage.py — migrate to config file
- Contract violations: `ContractViolation` dataclass with severity levels — reuse for health check findings
- QA profiling: `profile_output()` scans HTML + state.json — extend with business profile checks
- Collapsed sections: HTML templates already use `<details>` for collapsible content — use for audit appendix

### Integration Points
- Pipeline post-processing: `post_pipeline.py` runs after pipeline — audit/health check hooks here
- State.json: Written at pipeline end — add `render_audit` key alongside existing metadata
- HTML rendering: Section renderer dispatches facets — add audit appendix as special section
- CI: test_contract_enforcement.py and test_render_coverage.py — add new CI contract test

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. The user consistently chose recommended options, indicating trust in infrastructure-standard patterns with clear separation of concerns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 92-rendering-completeness*
*Context gathered: 2026-03-09*
