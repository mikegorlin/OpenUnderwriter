---
phase: 147-golden-manifest-wiring
verified: 2026-03-28T20:30:00Z
status: gaps_found
score: 3/4 must-haves verified
gaps:
  - truth: "Adverse events, tariff risk, and ESG indicators appear as manifest groups with data flowing from pipeline state"
    status: failed
    reason: "ESG and tariff alt-data templates exist (sections/alt_data/esg_risk.html.j2 and tariff_exposure.html.j2) with proper suppression guards and context builders wired, but neither template is registered in output_manifest.yaml. They are orphaned templates — no manifest group references them. Only peer_sca_contagion is in the manifest. WIRE-04 success criterion 2 requires these to appear AS MANIFEST GROUPS."
    artifacts:
      - path: "src/do_uw/templates/html/sections/alt_data/esg_risk.html.j2"
        issue: "Template exists with has_esg_data guard but has no manifest group entry — never rendered"
      - path: "src/do_uw/templates/html/sections/alt_data/tariff_exposure.html.j2"
        issue: "Template exists with has_tariff_data guard but has no manifest group entry — never rendered"
      - path: "src/do_uw/brain/output_manifest.yaml"
        issue: "No esg_risk or tariff_exposure group entries; alt_data section absent entirely"
    missing:
      - "Add esg_risk manifest group to output_manifest.yaml referencing sections/alt_data/esg_risk.html.j2"
      - "Add tariff_exposure manifest group to output_manifest.yaml referencing sections/alt_data/tariff_exposure.html.j2"
      - "test_alt_data_groups_exist currently skips (not fails) because esg/tariff groups absent — once manifest groups added, test will pass"
human_verification:
  - test: "Open AAPL worksheet HTML and inspect for empty cards or tables"
    expected: "No visible empty card containers, no empty table rows, suppressed sections produce zero DOM elements"
    why_human: "Visual inspection of rendered HTML — automated checks verify template logic but not actual render output DOM structure"
---

# Phase 147: Golden Manifest Wiring Verification Report

**Phase Goal:** Every one of the 27 recently-added manifest templates either renders meaningful content from pipeline data or is suppressed -- no empty cards, no placeholder text, no unwired templates
**Verified:** 2026-03-28T20:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Every manifest group is classified as renders, wired, or suppressed | VERIFIED | 163/163 groups classified (45 renders, 6 wired, 112 suppressed), 0 unclassified. `test_audit_classifies_all_groups` passes. |
| 2 | Automated test loads real AAPL state.json and validates classification | VERIFIED | 170 tests pass (169 pass + 1 expected skip for alt-data groups). `test_manifest_completeness` and `test_no_template_crashes` pass. |
| 3 | ESG/tariff/adverse events appear as manifest groups with data flowing | FAILED | ESG and tariff templates exist in `sections/alt_data/` with guards and context builders wired, but output_manifest.yaml has zero group entries for them. They never render. Only peer_sca_contagion is in the manifest. `test_alt_data_groups_exist` skips (not fails) because missing groups cause `pytest.skip`, masking the gap. |
| 4 | No empty cards or tables visible — suppressed templates produce zero DOM | VERIFIED | 3 stub templates confirmed to produce `''` when rendered. 7 additional templates have top-level `{% if %}` guards. `assembly_dossier.py` has individual try/except alt-data wiring with `has_*_data=False` fallbacks. |

**Score:** 3/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/manifest_audit.py` | Classification engine with ManifestClassification, classify_manifest_groups, build_manifest_audit_context | VERIFIED | 197 lines (exceeds 150-line spec, appropriately). All three exports present. Imports load_manifest and collect_signals_by_group from manifest_schema. SilentUndefined approach for crash-free probing. |
| `tests/stages/render/test_manifest_wiring_completeness.py` | 6-test completeness suite, min 80 lines | VERIFIED | 288 lines. All 6 required tests present. Parametrized crash test covers all 163 groups. Uses real AAPL state.json. |
| `src/do_uw/stages/render/context_builders/assembly_dossier.py` | manifest_audit context key + alt-data builders wired | VERIFIED | build_esg_context, build_tariff_context, build_ai_washing_context, build_peer_sca_context all wired individually with try/except. build_manifest_audit_context called as final builder step. |
| `src/do_uw/brain/output_manifest.yaml` | ESG and tariff manifest groups | FAILED | No esg_risk or tariff_exposure entries. Templates exist in alt_data/ but are not in the manifest — never dispatched to a manifest group. peer_sca_contagion IS present. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/stages/render/test_manifest_wiring_completeness.py` | `src/do_uw/stages/render/manifest_audit.py` | `from do_uw.stages.render.manifest_audit import` | WIRED | Import confirmed at line 18-21 of test file |
| `src/do_uw/stages/render/manifest_audit.py` | `src/do_uw/brain/manifest_schema.py` | `from do_uw.brain.manifest_schema import load_manifest` | WIRED | Import confirmed at lines 21-27 of manifest_audit.py |
| `src/do_uw/stages/render/context_builders/assembly_dossier.py` | `src/do_uw/stages/render/manifest_audit.py` | `from do_uw.stages.render.manifest_audit import build_manifest_audit_context` | WIRED | Lines 340-341 of assembly_dossier.py |
| `src/do_uw/stages/render/context_builders/assembly_dossier.py` | `src/do_uw/stages/render/context_builders/alt_data_context.py` | `build_esg_context`, `build_tariff_context`, etc. | WIRED | Lines 202-236 of assembly_dossier.py, individually wrapped |
| `src/do_uw/templates/html/sections/alt_data/esg_risk.html.j2` | render pipeline | manifest group dispatch | NOT_WIRED | Template exists, guard exists, context wired — but no manifest group references this template. Never rendered. |
| `src/do_uw/templates/html/sections/alt_data/tariff_exposure.html.j2` | render pipeline | manifest group dispatch | NOT_WIRED | Same as ESG: template + guard + context exist, but no manifest entry. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `manifest_audit.py` classify_manifest_groups | `ManifestClassification` dict | Jinja2 render probing via SilentUndefined + manifest YAML | Yes — 163 groups with real counts | FLOWING |
| `assembly_dossier.py` manifest_audit context | `context["manifest_audit"]` | build_manifest_audit_context(state, context) | Yes — dict with renders/wired/suppressed counts | FLOWING |
| `alt_data/esg_risk.html.j2` | `esg_risk_level`, `has_esg_data` | build_esg_context() -> state.alt_data.esg | Context keys populated, but template never dispatched from manifest | DISCONNECTED (no manifest group) |
| `alt_data/tariff_exposure.html.j2` | `tariff_risk_level`, `has_tariff_data` | build_tariff_context() -> state.alt_data.tariff | Context keys populated, but template never dispatched from manifest | DISCONNECTED (no manifest group) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 163 manifest groups classified | `uv run python -c "from do_uw.stages.render.manifest_audit import classify_manifest_groups; r = classify_manifest_groups(); print(len(r))"` | 163 | PASS |
| 3 stub templates produce zero output | Jinja2 render of subsidiary_structure, workforce_distribution, operational_resilience | `''` for all three | PASS |
| Manifest wiring completeness test suite | `uv run pytest tests/stages/render/test_manifest_wiring_completeness.py -v` | 170 passed, 1 skipped | PASS |
| ESG manifest group exists | `grep esg output_manifest.yaml` | No output | FAIL |
| Tariff manifest group exists | `grep tariff output_manifest.yaml` | No output | FAIL |
| Pre-existing tests pass (contract enforcement) | `uv run pytest tests/brain/test_contract_enforcement.py tests/brain/test_template_facet_audit.py` | 3 failed — same failures as pre-phase-147 (confirmed by stash check) | PRE-EXISTING |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| WIRE-01 | 147-01 | Audit all manifest templates, categorize as renders/wired/suppressed | SATISFIED | 163/163 groups classified. ManifestClassification engine in manifest_audit.py. |
| WIRE-02 | 147-02 | Wire data-path templates to state/context | PARTIAL | Templates with state paths are wired via assembly_dossier.py. ESG and tariff context keys exist in pipeline context. But ESG/tariff templates are not in manifest, so wiring never reaches a rendered group. |
| WIRE-03 | 147-02 | Suppressed templates produce zero DOM output | SATISFIED | 3 stubs produce `''`. 7 additional templates have top-level if guards. All verified to produce zero DOM when data absent. |
| WIRE-04 | 147-02 | Add manifest groups: adverse_events display, tariff risk, ESG indicators | PARTIAL | adverse_events has representation (eight_k_events, corporate_events groups). peer_sca_contagion is in manifest. ESG group absent from manifest. Tariff group absent from manifest. Templates exist but are orphaned. |
| WIRE-05 | 147-01 | Automated manifest completeness test | SATISFIED | test_manifest_wiring_completeness.py with 6 tests (170 total parametrized). test_manifest_completeness, test_audit_classifies_all_groups both pass. |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `tests/stages/render/test_manifest_wiring_completeness.py` lines 131-145 | `test_suppressed_produce_empty` checks only that `len(suppressed) > 0`, not that suppressed templates actually produce empty HTML. A template classified as suppressed that still renders DOM would pass this test. | Warning | Test weakens verification guarantee for suppression correctness. Does not catch DOM-producing suppressed templates. |
| `test_alt_data_groups_exist` line 252 | Uses `pytest.skip` (not `pytest.fail`) when alt-data manifest groups are absent. This converts a contract violation (WIRE-04 gap) into a silent skip, masking the gap from CI. | Blocker | Hides the ESG/tariff manifest group gap from automated test results. Phase is marked complete but WIRE-04 is only partially satisfied. |

### Human Verification Required

#### 1. Rendered HTML Empty Card Check

**Test:** Open `output/AAPL/` worksheet HTML (after re-render with current code). Inspect visually for empty card containers, empty table bodies, or sections that show a header with no content below it.
**Expected:** No empty visual containers. Suppressed sections are completely invisible — no DOM element, no whitespace, no blank card outline.
**Why human:** Template guard logic is verified programmatically, but actual rendered HTML structure (DOM emptiness vs. CSS-hidden elements) requires visual inspection.

### Gaps Summary

WIRE-04 is the blocking gap. The requirement says "Add missing manifest groups: adverse events display, tariff risk assessment, ESG indicators." The work was performed halfway:

- Context builders for ESG and tariff were wired into the render pipeline (assembly_dossier.py)
- Template files exist with proper suppression guards (sections/alt_data/esg_risk.html.j2, tariff_exposure.html.j2)
- But `output_manifest.yaml` was never updated to add group entries for these templates

The manifest is the dispatch table — if a template has no group entry, it is never rendered regardless of whether context is populated. Both ESG and tariff templates are effectively dead code: present in filesystem, wired in context, but never dispatched.

The fix is small: add two group entries to `output_manifest.yaml` for `esg_risk` (pointing to `sections/alt_data/esg_risk.html.j2`) and `tariff_exposure` (pointing to `sections/alt_data/tariff_exposure.html.j2`). Once added, `test_alt_data_groups_exist` will pass (currently skips), and the manifest completeness count will increase from 163 to 165.

WIRE-01, WIRE-03, and WIRE-05 are fully satisfied. WIRE-02 is partially satisfied (wiring code exists but ESG/tariff templates are never dispatched). WIRE-04 is partially satisfied (peer_sca and adverse_events are wired; ESG and tariff are not in manifest).

---

_Verified: 2026-03-28T20:30:00Z_
_Verifier: Claude (gsd-verifier)_
