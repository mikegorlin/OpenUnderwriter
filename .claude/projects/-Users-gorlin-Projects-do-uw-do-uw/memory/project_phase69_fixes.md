---
name: Phase 69 Outstanding Fixes — Research Complete
description: Detailed implementation plan for 4 remaining output quality fixes with exact file/line references
type: project
---

## Phase 69 Outstanding Fixes — Ready to Implement

### Fix 1: Insider Trading Richer Cluster Context
**Status:** Research complete, ready to code
**Problem:** Cluster table shows only aggregate (period, count, names, total). Missing per-insider dates, magnitudes, % holdings, 10b5-1 status.
**Data exists:** All detail is in `InsiderTransaction` objects + `OwnershipConcentrationAlert` — just not extracted by context builder.

**Implementation:**
- **Context builder** `src/do_uw/stages/render/context_builders/market.py:109-149` — For each cluster, map back to `InsiderTransaction` list by matching insider names + date window. Extract per-insider: sale_date, total_value, title, is_10b5_1, personal_pct_sold (from OwnershipConcentrationAlert).
- **Template** `src/do_uw/templates/html/sections/market/insider_trading.html.j2:130-154` — Add expandable sub-rows under each cluster showing per-insider detail with C-suite badge and 10b5-1 badge.
- **No model changes needed** — InsiderTransaction already has all fields.

### Fix 2: Stock Drop Trigger Attribution + News Correlation
**Status:** Research complete, ready to code
**Problem:** All AAPL April 2025 drops show "—" for trigger. Attribution only checks 8-K/earnings within ±3 days. No news correlation.
**Pipeline:** `stock_drops.py:260-362` (initial attr) → `stock_drop_enrichment.py:60-124` (8-K) → `stock_drop_enrichment.py:298-339` (web, passive only)

**Implementation (context builder fix, not pipeline):**
- **Context builder** `market.py:360` — When trigger is empty AND `is_market_driven=True` OR `market_wide_event=True`, infer "Market-wide selloff" as trigger. When sector also dropped >3%, add sector context.
- **Template** `stock_drops.html.j2:77` — Show inferred triggers in italic/gray to distinguish from confirmed triggers.
- **Phase 90 decomposition fields exist:** `market_pct`, `sector_pct`, `company_pct` — use these to auto-label triggers.
- **Longer-term:** Add news search to enrichment pipeline for drops without triggers.

### Fix 3: Forensic Scores Source Attribution
**Status:** Research COMPLETE, ready to code
**Problem:** Context builder (`analysis.py:268-325`) only exposes name + overall score + zone. SubScore.components dict (raw values, normalized scores) and SubScore.evidence string are NOT passed to template.
**Data exists:** Each SubScore already stores `components` dict with raw values (e.g., beneish_raw=-1.95, dechow_raw=1.62) and `evidence` string. Just not extracted.

**Implementation:**
- **Context builder** `analysis.py:268-325` — Extract `sub_scores[*].components` and `sub_scores[*].evidence` from each composite. Add raw value + threshold + normalized score per component.
- **Template** `forensic_composites.html.j2` — Add expandable detail under each sub-score showing: component name, raw value, threshold (from forensic_models.json), normalized score, evidence text.
- **Config** `brain/config/forensic_models.json` — Already has thresholds. Reference for display.
- **Key sub-components:** FIS has 5 dims (manipulation 30%, accrual 20%, revenue 20%, cashflow 15%, audit 15%). Each dim has 2-4 model components with raw+normalized values.

### Fix 4: M&A/Financing Signals as Structured Data
**Status:** Research COMPLETE, requires pipeline work (bigger lift)
**Problem:** 17 FWRD.EVENT signals defined in `brain/signals/fwrd/ma.yaml` but NO data acquisition feeds them. Event catalysts table renders empty.
**What exists:** MAForensics model (serial acquirer flag, goodwill growth). CapitalMarketsActivity (offerings, Section 11). forensic_ma.py computes serial acquirer from XBRL.
**What's missing:** No 8-K Item 1.01 parser, no debt footnote parser, no structured MAEvent/FinancingEvent models.

**Implementation (larger scope — defer to architecture redo):**
- **Models:** Create MAEvent (announcement_date, target, deal_value, closing_date, status) and FinancingEvent (type, amount, coupon, maturity, covenants)
- **Acquire:** Add 8-K Item 1.01/2.05 parsing in SEC client
- **Analyze:** Route events through signal evaluators
- **Render:** Populate event catalysts table + M&A cards
- **Recommendation:** Defer to architecture redo. Current forensic_ma.py serial acquirer detection is adequate interim.

## CSS/Design Upgrade (DONE this session)
- Typography: Calibri → Inter (self-hosted)
- Section headers: gold left-accent + gradient bg + uppercase
- Topbar/cover: gradient + depth shadows
- Sidebar: gold active accent, gradient bg, smooth scrollbar
- Cards/collapsibles: rounded corners, hover shadows, gradient summaries
- Preview: `output/AAPL-2026-03-05/AAPL_worksheet_v2.html`
- Files changed: styles.css, components.css, sidebar.css, input.css, compiled.css

**Why:** User wants continuous output quality improvement before larger architecture redo.
**How to apply:** Start with Fix 1 and Fix 2 (context builder changes only, no pipeline work needed). Then Fix 3 and Fix 4 require deeper changes.
