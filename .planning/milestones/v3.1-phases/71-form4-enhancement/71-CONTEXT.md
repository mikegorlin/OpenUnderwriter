# Phase 71: Form 4 Insider Trading Enhancement - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Enhance the existing Form 4 XML parser with post-transaction ownership tracking, deduplication, gift/estate filtering, exercise-sell pattern detection, relationship flag parsing, and filing timing analysis. Extend `insider_trading.py` (499 lines) and `InsiderTransaction` model — don't rewrite. New brain signals for ownership concentration and suspicious timing patterns.

</domain>

<decisions>
## Implementation Decisions

### Ownership Concentration Tracking
- Tiered alert system: >25% of holdings sold in 6 months = warning signal, >50% = red flag
- 10b5-1 plan status reduces severity but never suppresses alerts
- Running ownership trajectory per insider (not just snapshot) — build timeline from sharesOwnedFollowingTransaction
- C-suite gets strict tracking (CEO, CFO, COO, CLO, CTO); directors/10% holders get informational transaction list only
- Cluster selling + individual concentration overlap = compound to highest severity
- Lookback extended to 36 months (from current 18) for ownership trajectory
- Track insider PURCHASES as positive signal (open-market buys = skin in the game)
- Report both: percentage of insider's own holdings AND percentage of shares outstanding
- Thresholds stored in brain signal YAML (e.g., GOV.INSIDER.ownership_concentration), consistent with Phase 70 signal architecture

### Transaction Filtering Rules
- Gift transactions (code G) and estate transfers (code W): excluded from ALL aggregates (buy/sell totals, net direction, cluster detection). Still stored for completeness.
- RSU vesting (code A, $0 price) and tax withholding (code F): excluded entirely from output. Compensation noise, not trading decisions.
- Form 4/A amendments: keep both original and amendment. Flag original as "superseded." Audit trail preserved.
- Deduplication key: accession number + transaction date + owner + transaction code. Allows same-person, same-day, different-type transactions.

### Pattern Detection
- Exercise-and-sell (code M + code S, same owner, same day): always amber flag. Combined event reporting.
- Filing timing analysis: 60-day window, both directions (selling before negative 8-K AND buying before positive 8-K)
- 8-K event classification: use item numbers deterministically. 2.02 (earnings), 5.02 (director departure), 4.02 (non-reliance) = negative. 1.01 (material agreement), 2.01 (acquisition) = positive.
- All detected patterns create brain signals (GOV.INSIDER.* namespace). Feeds into scoring system.

### Output Presentation
- Enhanced insider data expands existing Market Events section (Section 4) — new facets within that section
- Ownership trajectory: table format with insider rows, trend arrows, columns for name/role/current shares/6mo change %/18mo change %
- Pattern visualization: timeline with event markers — insider sales as dots, 8-K events as bars, overlaps visible at a glance
- Insider trading subsection: always expanded (not collapsible). Consistent with Red Flags treatment — always relevant to D&O.

### Claude's Discretion
- Meeting prep question generation from ownership changes (user said "you decide" — integrate if natural with existing meeting prep architecture)
- Exact timeline visualization implementation (SVG, CSS, or HTML table with visual markers)
- How to handle edge cases in deduplication (partial matches, different share counts)
- Exercise-sell detection: whether to require exact same-day or allow T+1

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `insider_trading.py` (499 lines): Full Form 4 XML parser, cluster detection, yfinance fallback. Entry point: `extract_insider_trading()`. Extend, don't rewrite.
- `InsiderTransaction` model in `market_events.py`: Has insider_name, title, transaction_date/type/code, shares, price, total_value, is_10b5_1. Needs: shares_owned_following, relationship_flags, accession_number.
- `InsiderClusterEvent` model: Existing cluster selling detection with sliding window. Ownership concentration compounds with this.
- `TX_CODE_MAP`: Already maps all SEC transaction codes including G (GIFT), W (WILL_OR_ESTATE), A (GRANT), M (EXERCISE), F (TAX_WITHHOLD).
- `parse_form4_xml()`: Already extracts isOfficer/isDirector from XML but only uses them for title fallback. FORM4-05 needs full relationship flag extraction.
- `detect_cluster_selling()`: 30-day window, 3+ insiders. Can be extended for compound severity with ownership concentration.
- Brain signal YAML infrastructure (Phase 70): `brain/signals/gov/insider.yaml` exists with insider-related signals.

### Established Patterns
- SourcedValue pattern: Every extracted value gets source + confidence + as_of. New fields follow same pattern.
- ExtractionReport pattern: Every extractor returns tuple[Model, ExtractionReport] with found/warnings/fallbacks.
- Brain signal schema: `data_strategy.field_key` maps to state path. New signals follow existing GOV.INSIDER.* pattern.
- Facet rendering: Phase 62 facet templates access data via signal_results or context builders.
- SVG sparklines (Phase 63): Available if trajectory visualization evolves to sparklines later.

### Integration Points
- `stages/extract/__init__.py`: Calls `extract_insider_trading()` — new fields extracted in same flow
- `stages/acquire/clients/market_client.py`: Acquires Form 4 filings via EdgarTools
- `context_builders/market.py`: Builds insider trading context for HTML templates
- `stages/analyze/signal_field_routing.py`: Routes GOV.INSIDER.* signal field_keys to state data
- `stages/render/sections/sect4_market*.py`: Renders insider trading tables in Market section

</code_context>

<specifics>
## Specific Ideas

- "Broader: 60 days + positive 8-K too" — user explicitly wants bidirectional timing analysis, not just sell-before-bad-news
- "Always expanded" for insider section — user sees this as always-relevant D&O content, not optional detail
- "Yes, compound" — cluster selling + individual concentration should escalate together, reflecting that coordinated insider selling with large position changes is a multiplicative risk
- "Both" for ownership percentage — personal holdings % AND % of outstanding. Different questions answered by each metric.
- The 36-month lookback is specifically for ownership trajectory. Transaction filtering can remain at 18 months.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 71-form4-enhancement*
*Context gathered: 2026-03-06*
