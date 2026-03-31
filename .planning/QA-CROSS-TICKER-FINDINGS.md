# Cross-Ticker QA Findings (2026-03-28)

## Tickers Tested: AAPL, META, JPM, RPM, HNGE (pending)

## Systematic Issues (appear across multiple tickers)

### P0 — CRITICAL (breaks credibility)

| # | Issue | Tickers | Root Cause | Fix |
|---|---|---|---|---|
| 1 | **SourcedValue repr in rendered HTML** — `value='...' source='...' confidence=<Confidence.HIGH>` visible in debt tables, officer profiles, covenants | META, RPM | Context builders pass SourcedValue objects to str() instead of extracting .value | Fixed in financials.py; sanitizer enhanced as safety net |
| 2 | **Industrial metrics applied to banks** — Altman Z "distress zone", DSCR 0.76x "default risk", supply chain complexity for JPM | JPM | No sector-specific metric suppression/caveat. System treats all companies as industrial manufacturers | Need sector-conditional metric display: suppress/caveat inapplicable metrics per SIC code |
| 3 | **IPO boilerplate on mature companies** — "Section 11/12 liability... S-1 Registration" on 46-year-old companies | RPM, JPM | IPO exposure signals fire without checking years_public. Phase 139 contextual validation should annotate but signal still renders in Key Risk Findings | Contextual validator annotations need to suppress the KRF rendering, not just annotate |
| 4 | **Officer names corrupted** — "Time Warner" as CLO, "Netscape Communications" as CTO (META); LAST FIRST inversion (JPM) | META, JPM | Background check prior-company names used as person names; SEC EDGAR raw name format not inverted | Fix officer extraction to use correct name field; add name inverter for SEC EDGAR names |
| 5 | **N/A placeholders mid-sentence** — "disclosure theory (N/A)", "scoring 8.0 under N/A" in executive brief | META, RPM, JPM | Template fields not populated by context builder; narrative generator doesn't check for N/A before insertion | Add N/A guard in narrative generator: skip sentence if key field is N/A |
| 6 | **Meeting prep missing** for JPM — dead anchor link, no questions generated | JPM | Meeting prep generator may have crashed silently for financials sector | Investigate meeting_questions.py for sector-specific failures |

### P1 — MAJOR (reduces usefulness)

| # | Issue | Tickers | Root Cause | Fix |
|---|---|---|---|---|
| 7 | **Raw enum values in prose** — STRONG_BUY, DOJ_FCPA, NET_SELLER, loan_loss_reserves | META, RPM, JPM | Internal enum/taxonomy codes not humanized | Sanitizer enhanced with enum map; also fix upstream sources |
| 8 | **Litigation depth incomplete** — JPM has massive litigation history (London Whale $13B, Madoff, MBS $13B, LIBOR, FX, Epstein) but only 3 SCAs found | JPM | Acquisition limited to SCAC/EFTS + web search; historical settlements not in structured databases | Enhance web search queries for banks; consider manual litigation database for top-100 companies |
| 9 | **JSON/Python list fragments** in company operations divs — raw dict serialization, Python list brackets | RPM | Risk factor objects serialized as str() into template divs | Fix context builder to extract values before passing to template |
| 10 | **Key Positives are template boilerplate** — "Below-average X risk relative to scoring thresholds" repeated 4x | JPM | Positive findings generator uses template language, not company-specific analysis | Rewrite positive findings to reference actual metrics |
| 11 | **Truncated text** — EPA penalty "$6." cut off, "manipulated the precio" Spanish fragment | RPM, JPM | LLM extraction or source text truncated at character limit | Increase extraction context window; add completeness check |
| 12 | **Litigation count inconsistencies** — "0 Active / 0 Historical" badge but "3 Total Cases" in body | RPM | Active/historical count logic doesn't match total case count | Fix count aggregation in litigation context builder |
| 13 | **Geographic Footprint table all N/A** despite prose having the data | JPM | Structured field not populated from LLM extraction; prose generated separately | Wire geographic extraction to structured fields |
| 14 | **EPS actual/estimate swapped** — Q3 2025 shows -84.3% miss (wrong) | META | Data source ordering issue in earnings extraction | Fix earnings data column mapping |

### P2 — MINOR (polish)

| # | Issue | Tickers | Root Cause |
|---|---|---|---|
| 15 | Goodwill missing % sign ("56.06 of stockholders' equity") | RPM | Format string missing % |
| 16 | Stray `",` at end of meeting prep questions | RPM | Python list serialization remnant |
| 17 | "D&D risk protocol" typo (should be D&O) | RPM | LLM generation error |
| 18 | Duplicate business description (synthesized + raw 10-K) | META | Both versions rendered, should be one |
| 19 | Fiat Chrysler data fragment in Meta document | META | Cross-company data contamination |
| 20 | Factor evidence bullets empty (F7: F8: F9: F10:) | JPM | Scoring factors not populated |
| 21 | Board member tenure incorrect (Weinberger shows 1yr, actually 8yr+) | JPM | Tenure calculation from first proxy appearance, not actual start |

## Section Quality Summary

| Section | AAPL | META | JPM | RPM |
|---|---|---|---|---|
| Key Risk Findings | A | B | C+ | C+ |
| Executive Brief | A | B- | B- | B- |
| Business Description | A+ | A- | B | A- |
| Financial Health | A+ | B+ | D+ | B |
| Governance | A | C+ | B+ | B+ |
| Litigation | A+ | B+ | C | C |
| Stock/Market | A+ | B | — | A |
| Meeting Prep | A+ | A- | F | A- |
| Raw Data Leaks | A | D | C- | D |

## Priority Fix Order (for Monday)

1. **Sanitizer enhancement** — already done, re-running all 5 tickers
2. **Sector calibration for financials** — suppress/caveat Altman Z, DSCR, supply chain for banks (SIC 60xx-67xx)
3. **IPO signal suppression** — contextual validator annotations must suppress KRF rendering for mature companies
4. **Officer name fixes** — extract correct name field, add EDGAR name inverter
5. **N/A guard in narrative** — skip sentences with unfilled template fields
6. **Meeting prep crash** — investigate JPM failure, ensure all sectors generate questions
7. **Litigation depth** — enhance web search for banks with known settlement history
