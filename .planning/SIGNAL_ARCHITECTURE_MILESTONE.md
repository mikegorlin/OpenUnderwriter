# v7.0 Signal-Render Integrity -- Milestone Plan

## Problem Statement

The signal engine evaluates 514 signals, but approximately 60% of rendered content bypasses those results. Four major context builders (`market.py`, `financials.py`, `governance.py`, `litigation.py` -- 2,077 lines combined) have **zero** references to `signal_results`. They read raw `state.extracted.*` data directly and compute their own evaluations inline, duplicating logic that the signal engine already performs.

This creates three concrete harms:
1. **Dual maintenance**: Evaluation thresholds exist in both YAML signals and Python context builders. When a threshold changes in YAML, the rendered output does not reflect it.
2. **Broken traceability**: The render audit reports 100% coverage because templates exist, but the data flowing into those templates is not signal-backed. An underwriter cannot trace a rendered judgment back to a specific signal evaluation.
3. **Portability failure**: The architectural promise of v5.0 (signals self-describe data needs, evaluation, AND presentation) is undermined when the renderer ignores signal results and recomputes evaluations from raw data.

## Architectural Principle: Facts vs. Evaluations

**Not everything needs signal backing.** The distinction:

| Category | Example | Source | Signal Needed? |
|----------|---------|--------|----------------|
| **Identity data** | "Apple Inc., SIC 3571, Delaware" | `state.company.identity` | No -- raw fact display |
| **Financial data** | "Revenue: $383.3B, Total Assets: $352.6B" | `state.extracted.financials.statements` | No -- tabular data display |
| **Case listing** | "In re Apple Inc. Sec. Lit., filed 2024-01-15" | `state.extracted.litigation` | No -- structured data display |
| **Board roster** | "Tim Cook, CEO, tenure 13.2 years" | `state.extracted.governance` | No -- factual display |
| **Risk evaluation** | "Altman Z-Score 3.14 -- safe zone" | `state.analysis.signal_results['FIN.ACCT.quality_indicators']` | **YES** -- judgment |
| **Risk evaluation** | "Short interest 2.1% -- below concern" | `state.analysis.signal_results['STOCK.SHORT.position']` | **YES** -- judgment |
| **Risk evaluation** | "Say-on-pay 89% -- below threshold" | `state.analysis.signal_results['GOV.PAY.say_on_pay']` | **YES** -- judgment |
| **Risk evaluation** | "No active securities class actions" | `state.analysis.signal_results['LIT.SCA.active']` | **YES** -- judgment |
| **Aggregate assessment** | "Defense strength: MODERATE" | `state.analysis.signal_results['LIT.DEFENSE.*']` | **YES** -- judgment |
| **Trend evaluation** | "Revenue growth +12% YoY" | `state.extracted.financials` | **Borderline** -- display with computation |

**Rule of thumb**: If the context builder uses an `if/elif/else` to map a value to a risk level label (HIGH/MODERATE/LOW), that is an evaluation and must be backed by a signal result.

## Milestone Structure

**Milestone**: v7.0 Signal-Render Integrity
**Goal**: Every evaluative judgment rendered in the worksheet is backed by a signal evaluation result. Context builders consume `signal_results` for all risk assessments, threshold comparisons, and level classifications. Raw data display remains direct.
**Phase range**: 102-108 (7 phases, estimated 12-16 plans)

## Phase 102: Signal-Render Audit & Classification

**Goal**: Produce a complete inventory of every evaluation bypass in every context builder, classifying each as DATA_DISPLAY (no change needed) or EVALUATION_BYPASS (must be retrofitted).

**Work**:
1. Audit all 12 context builder files. For each `state.extracted.*` access, classify:
   - DATA_DISPLAY: raw value formatting (format_currency, format_percentage, na_if_none)
   - EVALUATION_BYPASS: threshold comparison, level mapping, risk classification, zone determination
2. Cross-reference bypasses against existing signals. For each bypass, determine:
   - Signal already exists and is evaluated but result is ignored by renderer (e.g., `FIN.ACCT.quality_indicators` computes Z-Score zone but `financials.py` also computes it from raw data)
   - Signal exists but does not capture this specific evaluation (e.g., tax haven risk level)
   - No signal exists for this evaluation (new signal needed)
3. Produce the bypass registry as a YAML file at `src/do_uw/brain/config/signal_render_audit.yaml`

**Estimated bypass inventory** (from initial analysis):
- `financials.py`: ~15-20 evaluative bypasses (distress zone classifications, earnings quality assessments, leverage evaluations, tax risk levels, liquidity assessments)
- `market.py`: ~8-12 evaluative bypasses (volatility regime, insider trading assessment, short interest concern level, earnings guidance track record)
- `governance.py`: ~10-15 evaluative bypasses (governance score interpretation, board quality assessment, compensation excess flags, structural governance evaluations)
- `litigation.py`: ~8-12 evaluative bypasses (defense strength assessment, SEC enforcement stage evaluation, SoL window risk, litigation reserve adequacy)
- `company.py` (non-v6.0 sections): ~5-8 evaluative bypasses (exposure factor levels, geographic concentration risk)

**Total estimated**: 46-67 evaluative bypasses across 5 context builders

**Contract test**: `test_signal_render_audit.py` -- validates the audit registry exists and is complete (every context builder file is listed).

**Plans**: 1 plan
**Dependencies**: None

---

## Phase 103: Signal Result Consumer Infrastructure

**Goal**: Build the shared infrastructure that context builders use to consume signal results. This is the "plumbing" phase -- no context builder changes yet.

**Work**:
1. Create `src/do_uw/stages/render/context_builders/_signal_consumer.py` with:
   - `get_signal_result(state, signal_id) -> SignalResultView | None` -- extracts a typed view of a signal result from `state.analysis.signal_results`
   - `get_signal_value(state, signal_id) -> Any` -- shortcut for the evaluated value
   - `get_signal_status(state, signal_id) -> str` -- TRIGGERED/CLEAR/SKIPPED/INFO
   - `get_signal_level(state, signal_id) -> str` -- threshold_level (RED/YELLOW/CLEAR)
   - `get_signals_by_prefix(state, prefix) -> list[SignalResultView]` -- all signals matching a prefix (e.g., "FIN.ACCT.")
   - `signal_to_display_level(status, threshold_level) -> tuple[str, str]` -- maps signal status/threshold to (level_label, css_color) consistently
   - `SignalResultView` -- a typed dataclass exposing: signal_id, signal_name, status, value, threshold_level, confidence, evidence, factors, section, content_type

2. Create `src/do_uw/stages/render/context_builders/_signal_fallback.py` with:
   - Fallback logic: if signal_result is None (signal was SKIPPED or not evaluated), fall back to direct extracted data with a `"signal_unavailable"` marker
   - This ensures rendering never breaks if a signal fails, while making the signal bypass visible in the render audit

3. Unit tests for the consumer infrastructure

**Contract test**: `test_signal_consumer.py` -- validates that `get_signal_result` correctly extracts typed data from signal_results dicts.

**Plans**: 1 plan
**Dependencies**: None (can run in parallel with Phase 102)

---

## Phase 104: Financial Health Signal Wiring

**Goal**: Retrofit `financials.py` (626 lines) to consume signal results for all evaluative content while preserving direct data access for tabular financial display.

**Evaluative bypasses to fix** (estimated 15-20):
- Distress model zone classifications (Z-Score zone, Beneish zone, Piotroski zone, O-Score zone) -- signals: `FIN.ACCT.quality_indicators`, `FIN.ACCT.earnings_manipulation`
- Earnings quality assessment (OCF/NI ratio interpretation, accruals ratio concern level) -- signal: `FIN.ACCT.earnings_quality` (may need new signal or sub-signal)
- Leverage evaluation (D/E ratio concern level, interest coverage adequacy) -- signal: `FIN.DEBT.coverage`
- Liquidity assessment (current ratio adequacy, quick ratio concern) -- signal: `FIN.LIQ.position`
- Tax risk level (haven count risk, transfer pricing flag, ETR trend evaluation) -- signals: may need `FIN.TAX.haven_exposure`, `FIN.TAX.transfer_pricing`
- Audit profile risk (Big 4 status interpretation, material weakness count, going concern flag) -- signals: `FIN.ACCT.material_weakness`, `FIN.ACCT.internal_controls`

**Data display (no change)**: Income statement line items, balance sheet line items, cash flow highlights, statement tables, peer group listing, quarterly updates, sparklines, XBRL quarterly trends, forensic dashboard raw data, peer percentile charts.

**New signals needed** (estimated 3-5):
- `FIN.TAX.haven_exposure` -- evaluates tax haven subsidiary count and concentration
- `FIN.TAX.etr_trend` -- evaluates effective tax rate trajectory
- `FIN.EARN.quality_composite` -- evaluates earnings quality (OCF/NI, accruals, DSO delta) as a composite
- `FIN.LIQ.adequacy` -- evaluates liquidity position (current ratio, quick ratio) with tiered thresholds

**Also wire** `financials_forensic.py` (250 lines) and `financials_quarterly.py` (225 lines) if they contain evaluative bypasses.

**Contract test**: `test_financials_signal_wiring.py` -- for every evaluative field in the financials context dict, asserts that the value traces to a signal_result (not direct extracted data).

**Plans**: 2 plans (one for signal creation + mapper wiring, one for context builder retrofit + tests)
**Dependencies**: Phase 103 (consumer infrastructure)

---

## Phase 105: Market Activity Signal Wiring

**Goal**: Retrofit `market.py` (496 lines) to consume signal results for all evaluative content.

**Evaluative bypasses to fix** (estimated 8-12):
- Volatility regime interpretation (EWMA vol regime: LOW/NORMAL/ELEVATED/CRISIS) -- signal: `STOCK.PRICE.volatility_regime` (may already exist)
- Short interest concern level -- signal: `STOCK.SHORT.position`
- Insider trading assessment (net buying/selling interpretation, cluster event severity, ownership alert severity) -- signals: `STOCK.INSIDER.*`, `GOV.INSIDER.cluster_sales`
- Stock drop significance (D&O claim exposure interpretation per drop) -- signal: `STOCK.PRICE.recent_drop_alert`
- Earnings guidance track record evaluation -- signal: may need `STOCK.GUIDANCE.track_record`
- Analyst consensus divergence -- signal: may need `STOCK.ANALYST.consensus_risk`
- Valuation ratio concern levels (P/E extreme, PEG ratio interpretation) -- may need new signals

**Data display (no change)**: Current price, 52-week range, pct off high, raw short interest numbers, individual transaction detail rows, ownership alert data points, valuation ratio raw values, growth metrics raw values, profitability metrics raw values, stock charts, ownership chart.

**New signals needed** (estimated 2-4):
- `STOCK.GUIDANCE.track_record` -- evaluates earnings guidance hit/miss pattern
- `STOCK.ANALYST.consensus_risk` -- evaluates analyst estimate dispersion
- `STOCK.VALUATION.extreme` -- evaluates whether valuation ratios are outliers (may be captured by peer benchmarking)

**Contract test**: `test_market_signal_wiring.py`

**Plans**: 2 plans
**Dependencies**: Phase 103 (consumer infrastructure)

---

## Phase 106: Governance Signal Wiring

**Goal**: Retrofit `governance.py` (460 lines) and `_governance_helpers.py` (145 lines) to consume signal results for all evaluative content.

**Evaluative bypasses to fix** (estimated 10-15):
- Governance score interpretation (score/100 -> quality level) -- signal: `GOV.BOARD.governance_quality` or composite
- Board independence adequacy (independence ratio vs threshold) -- signal: `GOV.BOARD.independence`
- CEO duality risk assessment -- signal: `GOV.BOARD.ceo_duality`
- Overboarded director count concern -- signal: `GOV.BOARD.overboarded`
- Classified board risk -- signal: `GOV.BOARD.classified`
- ISS risk score interpretation (1-10 scale -> concern level) -- may need new signals
- Compensation analysis risk levels (say-on-pay threshold, CEO pay ratio concern, equity dilution) -- signals: `GOV.PAY.say_on_pay`, `GOV.PAY.ceo_pay_ratio`
- Structural governance evaluation (poison pill, dual class, anti-takeover provisions) -- signals: `GOV.RIGHTS.*`
- Executive forensic flag aggregation (shade factor count -> risk level) -- signal: `EXEC.AGGREGATE.board_risk`
- Board member forensic flag aggregation (interlock count, relationship flags -> concern level) -- may need composite signal

**Data display (no change)**: Board member names/tenures/committees, executive profiles (name, title, tenure, bio), compensation raw numbers, ownership percentages, anti-takeover provision listing, forensic detail items.

**New signals needed** (estimated 2-3):
- `GOV.ISS.overall_risk` -- evaluates ISS governance risk score
- `GOV.BOARD.composition_quality` -- composite evaluating independence + attendance + tenure + overboarding
- `EXEC.FORENSIC.aggregate_flags` -- composite evaluating total forensic flag count across all executives/directors

**Contract test**: `test_governance_signal_wiring.py`

**Plans**: 2 plans
**Dependencies**: Phase 103 (consumer infrastructure)

---

## Phase 107: Litigation Signal Wiring

**Goal**: Retrofit `litigation.py` (495 lines) to consume signal results for all evaluative content.

**Evaluative bypasses to fix** (estimated 8-12):
- Defense strength assessment (overall defense strength -> risk level) -- signal: `LIT.DEFENSE.overall` or existing defense signals
- SEC enforcement stage evaluation (pipeline position -> concern level) -- signal: `LIT.REG.sec_enforcement`
- SoL window risk (open window count -> urgency level) -- signal: `LIT.SCA.sol_status` (may need new)
- Active matter severity (matter count + type -> risk level) -- signal: `LIT.SCA.active`
- Settlement history pattern (total settled + amounts -> risk level) -- signal: `LIT.SCA.settle_amount`
- Derivative suit exposure (count + type -> risk level) -- signal: `LIT.SCA.derivative`
- Contingent liability materiality (ASC 450 reserve amount -> concern level) -- signal: `LIT.DEFENSE.contingent_liabilities`
- Whistleblower indicator risk (indicator count -> concern level) -- may need new signal
- Litigation reserve adequacy (reserve vs active matters) -- may need new signal

**Data display (no change)**: Case names/dates/amounts, settlement case listing, derivative suit details, contingent liability line items, industry claim pattern listing, workforce/product/environmental matter listing, whistleblower indicator listing.

**New signals needed** (estimated 2-3):
- `LIT.SCA.sol_urgency` -- evaluates SoL window openness and urgency
- `LIT.RESERVE.adequacy` -- evaluates litigation reserve relative to active exposure
- `LIT.WHISTLE.indicators` -- evaluates whistleblower risk indicator count

**Contract test**: `test_litigation_signal_wiring.py`

**Plans**: 2 plans
**Dependencies**: Phase 103 (consumer infrastructure)

---

## Phase 108: Contract Enforcement & Regression Prevention

**Goal**: Add CI-level contract tests that prevent future signal bypass regressions. Update the render audit to distinguish signal-backed evaluations from data display.

**Work**:
1. **Signal Render Contract Test** (`tests/brain/test_signal_render_contract.py`):
   - For every context builder function, scan for patterns that indicate evaluative logic:
     - `if score >= N:` followed by level assignment
     - `"HIGH" if X else "MODERATE" if Y else "LOW"`
     - `.zone` access on distress models
     - `"concern"`, `"risk"`, `"adequate"`, `"threshold"` in string literals
   - Assert that each evaluative pattern is accompanied by a `get_signal_result()` call
   - This is an AST-based or regex-based static analysis test

2. **Signal Bypass Counter Test** (`tests/brain/test_no_new_bypasses.py`):
   - Count total `state.extracted.*` accesses in context builder files
   - Count total `get_signal_result()` or `signal_results` accesses
   - Assert ratio: signal accesses / (signal + extracted accesses) >= 0.40 (Phase 104-107 target)
   - This number ratchets up over time as more bypasses are fixed

3. **Render Audit Enhancement**:
   - Update `render_audit.py` to distinguish:
     - SIGNAL_BACKED: context value traces to a signal_result
     - DATA_DISPLAY: context value traces to raw extracted data (acceptable)
     - EVALUATION_BYPASS: context value computes a risk level from raw data without signal backing (violation)
   - Post-pipeline audit reports EVALUATION_BYPASS count (target: 0)

4. **Manifest Enhancement**:
   - Add `data_source: signal | extract | hybrid` field to manifest groups
   - Groups with `data_source: signal` must have all evaluative content backed by signals
   - Groups with `data_source: extract` are pure data display
   - Groups with `data_source: hybrid` (most common) have both

**Contract tests**: 3 new test files as described above

**Plans**: 2 plans (one for contract tests, one for render audit + manifest enhancement)
**Dependencies**: Phases 104-107 (all context builder retrofits)

---

## Signal Count Summary

| Phase | Existing Signals Wired | New Signals Created | Total Change |
|-------|----------------------|-------------------|--------------|
| 102 | 0 | 0 | Audit only |
| 103 | 0 | 0 | Infrastructure only |
| 104 | ~15 (FIN.*) | 3-5 | +3-5 new signals |
| 105 | ~10 (STOCK.*) | 2-4 | +2-4 new signals |
| 106 | ~15 (GOV.*, EXEC.*) | 2-3 | +2-3 new signals |
| 107 | ~10 (LIT.*) | 2-3 | +2-3 new signals |
| 108 | 0 | 0 | Tests only |
| **Total** | **~50 existing wired** | **9-15 new** | **523-529 total signals** |

The key insight: most of the work is **wiring existing signals** into context builders, not creating new ones. The signal engine already evaluates 297 signals that the renderer ignores. Only 9-15 new signals are needed for evaluation dimensions that lack signal coverage entirely.

## Execution Order

```
Phase 102 ──┐
             ├── Phase 104 (financials) ──┐
Phase 103 ──┤                              │
             ├── Phase 105 (market) ───────┤
             │                              ├── Phase 108 (contracts)
             ├── Phase 106 (governance) ───┤
             │                              │
             └── Phase 107 (litigation) ───┘
```

Phases 102 and 103 are independent and can run in parallel.
Phases 104-107 depend on Phase 103 but are independent of each other.
Phase 108 depends on all of Phases 104-107.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Context builder refactor breaks existing output | HIGH | Visual regression tests exist (golden baselines). Run `VISUAL_REGRESSION=1` after each phase. |
| Signal results missing for some companies/tickers | MEDIUM | Fallback infrastructure (Phase 103) ensures rendering never breaks. SKIPPED signals fall back to extracted data with marker. |
| New signals change existing scoring | LOW | New signals are INFO or CONTEXT_DISPLAY category by default. Only promote to DECISION_DRIVING after calibration. |
| Company.py is 1,159 lines -- refactoring risk | MEDIUM | Company.py v6.0 sections already partially use the target pattern. Focus on non-v6.0 sections only. |
| Test count explosion | LOW | Reuse `_signal_consumer.py` helper assertions. One parametrized test per context builder, not per field. |

## Success Criteria

1. Zero evaluative bypasses in context builders (post-Phase 108 contract test passes)
2. All 4 major context builders (`market.py`, `financials.py`, `governance.py`, `litigation.py`) reference `signal_results` or `get_signal_result()` for every risk level/zone/concern determination
3. Render audit reports 0 EVALUATION_BYPASS items
4. No visual regression in HTML output (golden baseline comparison passes)
5. Signal count increases by 9-15 (from 514 to 523-529)
6. CI contract test prevents new bypasses from being introduced

---

### Critical Files for Implementation
- `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/stages/render/context_builders/financials.py` - Largest bypass: 626 lines, zero signal_results references, 15-20 evaluative bypasses including distress models, earnings quality, tax risk
- `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/stages/render/context_builders/market.py` - Second largest bypass: 496 lines, zero signal_results references, all insider trading and volatility evaluations computed inline
- `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/stages/render/context_builders/governance.py` - Zero signal_results references despite 88 GOV/EXEC signals existing, board quality and compensation evaluations computed inline
- `/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/stages/render/context_builders/_bull_bear.py` - TARGET PATTERN: correctly consumes signal_results via `_extract_favorable_signals()` and `_extract_triggered_signals()`, template for all other context builders
- `/Users/gorlin/Projects/do-uw/do-uw/tests/brain/test_contract_enforcement.py` - Existing contract test infrastructure to extend with signal-render integrity checks
