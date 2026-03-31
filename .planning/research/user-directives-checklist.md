# D&O Underwriting Worksheet — Consolidated User Directives Checklist

This checklist consolidates EVERY user requirement, quality standard, and anti-pattern extracted from all memory files. Use it to validate the final worksheet output.

---

## 1. CONTENT REQUIREMENTS — What Must Be in the Worksheet

### 1.1 Company Intelligence Dossier (Biggest Gap vs Gold Standard)
- [ ] Plain English business description + "The core D&O exposure" paragraph identifying the single most important risk vector
- [ ] Revenue flow diagram (ASCII/monospace showing how money flows through the business)
- [ ] Revenue Model Card: table with Attribute / Value / D&O Risk columns (model type, pricing, rev quality, recognition, contract duration, NDR, retention, ARPU, complexity, guidance miss risk, concentration risk, regulatory overlay)
- [ ] Revenue Segment Breakdown with D&O Litigation Exposure column per segment
- [ ] Multi-dimensional concentration assessment (customer, geographic, product, channel, payer mix) with risk levels and D&O implications
- [ ] Unit Economics table (contracted lives, yield, revenue per unit, NDR, retention, ARPU, SBC, gross margin, FCF) with benchmark context and assessment
- [ ] Identification of the SINGLE MOST IMPORTANT METRIC for the business
- [ ] Revenue Waterfall / Growth Decomposition (Starting → +New → +Expansion → -Churn → Ending)
- [ ] Competitive Landscape comparison table (4+ companies: market share, revenue, pricing, technology, SCA history)
- [ ] Moat Assessment table (data advantage, switching costs, scale, brand, network effects, regulatory barrier, distribution lock) with Present/Strength/Durability
- [ ] Emerging Risk Radar: Risk / Probability / Impact / Timeframe / D&O Factor / Status
- [ ] Forward-Looking Statement Risk Map (guided metric → current value → guidance → miss risk → SCA relevance)
- [ ] Revenue Recognition (ASC 606) analysis: Element / Approach / Complexity / D&O Risk
- [ ] Billings vs revenue gap analysis
- [ ] Management Credibility: quarter-by-quarter guidance vs actual table with beat/miss magnitude

### 1.2 Stock & Market Analysis
- [ ] Stock drops: every >5% drop has Date / From / To / Drop / Volume / Catalyst & D&O Assessment (explaining WHY it happened and D&O relevance)
- [ ] DDL (Dollar Damage Line) / MTL (Maximum Tolerable Loss) visualization — if there was a suit, show potential damages
- [ ] Stock chart highlights damage period in a different color
- [ ] Volatility as a prominent D&O metric (stock drop = SCA trigger)
- [ ] Return decomposition: every return broken into market + sector + company-specific components
- [ ] Relative volatility ratios (company vol vs sector/market)
- [ ] Multi-day drop consolidation (consecutive small drops grouped, not separate events)
- [ ] Time-decay on drops (recent drops weighted higher than old ones)
- [ ] Recovery analysis: has it recovered? how quickly? still underwater?
- [ ] Insider sales shown prominently; grants/exercises collapsed under details
- [ ] Market Risk Flags (amber callouts) + Positive Market Indicators (green callouts) with D&O context

### 1.3 Financial Condition
- [ ] Opens with narrative paragraph explaining the financial STORY
- [ ] Key metrics with assessment column (checkmark/warning indicators)
- [ ] Each forensic indicator (Beneish, Altman, Piotroski, Ohlson) has D&O commentary explaining relevance
- [ ] Partial Altman Z guard: show "partial (missing: X)" not fake distress zone
- [ ] Risk factor DELTA analysis: what's NEW, what CHANGED, what was REMOVED vs prior year 10-K

### 1.4 Scoring Detail
- [ ] Each of 10 factors has "What Was Found" + "Underwriting Commentary" (WHY the score matters contextually)
- [ ] Key negatives MUST include: specific finding + dollar/percentage magnitude + scoring factor reference (e.g., "F.7 = 5/8") + D&O litigation theory
- [ ] Key positives MUST include: specific evidence + quantification + WHY it reduces D&O risk

### 1.5 Governance (NON-NEGOTIABLE per user)
- [ ] Prior lawsuits / litigation history for EVERY board member and executive
- [ ] Personal character / conduct issues for EVERY board member and executive
- [ ] Experience / qualifications for role for EVERY board member and executive
- [ ] Board Forensic Profiles with prior litigation detail rows
- [ ] People Risk table with bio sub-rows and litigation flags
- [ ] Board composition: size, independence ratio, avg tenure
- [ ] Executive tenure computed from appointment dates

### 1.6 Litigation
- [ ] SCA (Securities Class Action) data with proper classification (not misclassified commercial/antitrust)
- [ ] Cross-validation of extracted SCAs against web search results
- [ ] Stanford SCAC cross-reference for board member names
- [ ] Web search for "{director name} securities litigation" and "{name} lawsuit/SEC/investigation"

### 1.7 Meeting Prep
- [ ] Questions tiered: Critical / Important / Supporting
- [ ] Each question tied to specific scoring factors (F.1-F.10) with section references
- [ ] Each question has underwriting relevance explanation
- [ ] Answer field for post-meeting input
- [ ] Questions come from actual risk findings, not generic templates

### 1.8 Monitoring Triggers
- [ ] Trigger / Action / Threshold table for ongoing monitoring
- [ ] Triggers include: SCA filing, stock below support, insider selling pace, CEO departure, earnings miss, yield regression

### 1.9 Appendix
- [ ] Shows EVERY signal that ran — triggered, clear, skipped, errored
- [ ] Complete audit trail proving thoroughness ("show your work")
- [ ] Auto-generated from run results, not manifest-driven

### 1.10 Every Data Point Must Have
- [ ] D&O Risk / "So What for D&O?" column or commentary
- [ ] Source citation (filing type + date + URL/CIK reference)
- [ ] Confidence level (HIGH = audited/official, MEDIUM = unaudited/estimates, LOW = derived/web)

---

## 2. PRESENTATION REQUIREMENTS — How It Must Look

### 2.1 Overall Layout Philosophy
- [ ] Bloomberg terminal / professional infographic feel — NOT a Word document
- [ ] S&P Capital IQ density level (user shared CIQ screenshots as target)
- [ ] Minimal margins (0.5rem or less on sides) — every pixel earns its place
- [ ] Maximum data density — charts, gauges, heatmaps, sparklines OVER prose
- [ ] Two-column and three-column layouts where data permits
- [ ] Visual hierarchy through size/weight/color, NOT whitespace
- [ ] Numbers and visualizations FIRST, narrative SECOND
- [ ] Progressive disclosure: summary cards that expand to detail

### 2.2 Structural Layout
- [ ] Sidebar: position:fixed + body padding-left:180px (CIQ pattern, NOT sticky)
- [ ] Topbar: position:fixed, left:180px
- [ ] overflow-x: hidden on html to prevent horizontal scroll
- [ ] No duplicate company info — topbar is the permanent identifier
- [ ] Company ID / key data FIRST — underwriter sees WHO the company is before risk scores

### 2.3 Section Flow (Narrative Arc)
- [ ] Verdict FIRST → Why → Company → Financials → Legal → Governance → Market → Outlook → Recommendation
- [ ] Executive Brief is the "thesis statement" — everything after supports or elaborates
- [ ] Recommendation FIRST in Executive Brief, then evidence
- [ ] Key Negatives / Positives in two-column layout
- [ ] Each section has 1-2 sentence opening connecting to previous section's conclusion
- [ ] If a section doesn't advance the risk story, it belongs in the appendix

### 2.4 Table Design
- [ ] Remove heavy borders — use subtle lines/dividers instead
- [ ] Default to borderless tables with subtle bottom-border rows
- [ ] Thin dividers between sections, whitespace for grouping
- [ ] No full grid borders on data tables
- [ ] Paired-column KV tables (4 cols/row) per CIQ pattern
- [ ] Tabular-nums font feature for numeric columns
- [ ] Collapsible sections with chevrons

### 2.5 Chart Style ("AD Chart Style" — Canonical for All Charts)
- [ ] Wide SVG viewBox matching page proportions (900x200 full-width, ~520x150 half-width)
- [ ] preserveAspectRatio default (xMidYMid meet) — NEVER use "none"
- [ ] CSS: display:block; width:100%; — no fixed height
- [ ] Mountain fill below price line (polygon, navy #0B1D3A, opacity 0.06)
- [ ] Price line: stroke #0B1D3A, width 1.8, stroke-linejoin round
- [ ] Y-axis: price scale with dollar labels, dashed grid lines (stroke-dasharray 2,4)
- [ ] X-axis: quarterly date labels (YYYY-MM format)
- [ ] Damage/highlight periods: light red rect fill (#fef2f2, opacity 0.5)
- [ ] Annotation badges: rounded rect (rx=3), white text, font-weight 700, font-size 9
- [ ] Green (#059669) for peaks/highs, Red (#B91C1C) for current/lows and drop percentage
- [ ] Badges positioned adjacent to marker dots, NOT on axis labels
- [ ] Concise labels — no "peak" or "today" suffix
- [ ] Markers: circle r=4, fill color, stroke #fff width 1.5
- [ ] Dashed reference line from peak across chart (stroke-dasharray 4,3, opacity 0.35)
- [ ] Drop arrow: dashed line with arrowhead marker-end

### 2.6 Badges and Indicators
- [ ] UNCALIBRATED badge on all model-derived panels
- [ ] Red Flags: only CRITICAL/HIGH shown
- [ ] AI Assessment boxes: bordered boxes with bold D&O terms, numbered-list conversion

### 2.7 PDF-First Design
- [ ] ALL design effort focused on PDF output quality — HTML is intermediate only
- [ ] Design for print dimensions (A4/Letter), not browser viewport
- [ ] @media print styles are PRIMARY, screen is secondary
- [ ] Test by opening the PDF, not the HTML
- [ ] Professional typeset quality (Typst target for production)

### 2.8 Output Organization
- [ ] Output folders: `output/TICKER-CompanyName/YYYY-MM-DD/` (company-grouped, date subfolders)
- [ ] Always write to actual output file (e.g., `RPM_worksheet.html`), NOT test files

---

## 3. QUALITY REQUIREMENTS — Quality Bars That Must Be Met

### 3.1 Visual Verification (NON-NEGOTIABLE)
- [ ] After ANY render change, load and visually inspect the actual HTML output — grep-based checks are INSUFFICIENT
- [ ] Parse HTML with BeautifulSoup, check ACTUAL VALUES
- [ ] Check numbers are formatted (not raw floats with 5+ decimals)
- [ ] Check metrics are populated (not N/A for well-known companies)
- [ ] Check labels are readable
- [ ] Check for SCREAMING_SNAKE_CASE leaking (NET_SELLING, A_DISCLOSURE, FALLBACK_ONLY)
- [ ] Check N/A count — if high, investigate why
- [ ] Check company name format ("RPM INTERNATIONAL INC/DE/" should not appear in headers)
- [ ] NEVER say "it's working" based on string-contains checks

### 3.2 Self-Review Loop
- [ ] After generating output, review it like a McKinsey consultant reviewing a presentation deck
- [ ] Critique visual design, data presentation, narrative quality
- [ ] Identify specific improvements (layout, density, boilerplate, missing data)
- [ ] Make targeted fixes, re-render, review again
- [ ] Render -> Look -> Fix -> Repeat (iterate until quality)

### 3.3 Pipeline Monitoring
- [ ] Run pipeline and WAIT for completion
- [ ] If it fails at RENDER: diagnose immediately, fix code, reset render status, re-run (no --fresh)
- [ ] Keep fixing until render succeeds — don't stop at first fix
- [ ] When it succeeds: open and visually verify before telling user it's done
- [ ] Report: company name resolved, score/tier, output file paths, data gaps worth noting
- [ ] Fix ALL float()/similar crashes in one pass, don't play whack-a-mole

### 3.4 Code Quality Checks (Before Presenting as "Done")
- [ ] Read actual changed files (don't trust agent summaries)
- [ ] Verify all import chains are intact
- [ ] Run `uv run pytest` and scan for warnings/errors
- [ ] Run `ruff check src/` for linting issues
- [ ] No file exceeds 500 lines
- [ ] Compare output quality before/after changes
- [ ] Verify no checks accidentally dropped
- [ ] Verify no data sources disconnected
- [ ] Verify all blind spot detection still functions

### 3.5 Data Freshness
- [ ] Most recent filing drives the worksheet (not oldest)
- [ ] Any code iterating `llm_extractions` must pick most recent, not first found
- [ ] After code changes, verify data year matches most recent filing
- [ ] Cached pipeline runs from older code may have stale extractions — re-run with --fresh when needed

### 3.6 Data Integrity
- [ ] Every data point has source + confidence
- [ ] NEVER generate, guess, or hallucinate financial data — use "Not Available" instead
- [ ] Web-sourced data requires cross-validation from 2+ independent sources
- [ ] If a data source fails, fall through to next tier — never assume "no data" = "no issue"
- [ ] Broad web search is FIRST-CLASS acquisition, not fallback
- [ ] Every analysis run includes proactive discovery searches at START of ACQUIRE
- [ ] SCA misclassification routing: only cases with securities theories go to SCA bucket
- [ ] Stock drops validated against reasonable bounds (>25% single-day is extremely rare, flag it)

---

## 4. ANTI-PATTERNS — What NOT to Do (Based on Past Failures)

### 4.1 Never Truncate Analytical Content
- [ ] ZERO `| truncate()` on any content the underwriter reads in Jinja templates
- [ ] ZERO `[:N]` string slicing on evidence, descriptions, or narrative text in Python
- [ ] Only acceptable truncation: HTML tooltip `title` attributes and internal QA audit tables
- [ ] If text is too long, use CSS `word-wrap: break-word` — NEVER cut the text

### 4.2 Never Use Bare float() in Render Code
- [ ] Always use `safe_float()` from `do_uw.stages.render.formatters`
- [ ] LLM/API data contains "N/A", "13.2%", concatenated junk that crashes bare float()
- [ ] Exceptions only: float(0), float(len(...)), float(int(...)) — guaranteed-numeric sources

### 4.3 Never Show Raw System Internals
- [ ] NO "145 (exceeds threshold 100)" — say "operates through 145 subsidiaries"
- [ ] NO "Boolean Check: VIE/SPE structures present" — say "uses VIE/SPE structures, which increase..."
- [ ] NO "Detected keyword: acquisition" — this is extraction metadata, not analysis
- [ ] NO "Source: event_ipo_exposure_score" — internal field names must be human-readable
- [ ] NO internal detection artifacts as bullet points
- [ ] NO raw threshold evidence — translate through humanization layer before rendering
- [ ] NO SourcedValue/dict dumps in output

### 4.4 Never Produce Generic Narrative
- [ ] EVERY sentence must contain company-specific data (dollar amounts, percentages, dates, names)
- [ ] If a sentence could apply to any company by changing the name, it FAILS
- [ ] NO "has experienced a notable decline" — say "stock declined 27.9% from $167.40 to $120.69 over 326 trading days"
- [ ] NO "faces risk from critical red flag" — say what the flag IS with specific numbers
- [ ] D&O commentary comes from brain YAML `do_context`, NOT Python templates or Jinja2 conditionals
- [ ] LLM prompts must include FULL analytical context (scoring results, signal values, financial data)
- [ ] Generic LLM prompts produce generic output — always pass actual numbers

### 4.5 Never Simplify by Stripping Detail
- [ ] User explicitly objects to removing descriptive information (repeated 3x)
- [ ] Never simplify in ways that lose information
- [ ] Never present partial work as complete
- [ ] Don't skip verification because "it's a simple change"

### 4.6 Never Build Architecture Without Data Support
- [ ] Before adding any new signal: verify (1) data is acquired, (2) extraction path exists, (3) field_key resolves
- [ ] Signal count going up while skip count also goes up = REGRESSION, not progress
- [ ] Don't add new architectural layers that ignore the existing data pipeline
- [ ] "You implement new solutions, ignoring the old structure" — each phase must WIRE existing data

### 4.7 Never Present Work as Done Without Genuine Review
- [ ] User has been burned by this multiple times
- [ ] Don't say "tests pass" without reading test output
- [ ] Don't lose analytical power when refactoring
- [ ] Run the actual pipeline after changes and compare output
- [ ] After pipeline run, ALWAYS open and review HTML output section by section
- [ ] Always use --fresh for test runs after code changes (cached runs don't exercise new code)

### 4.8 Never Waste User's Time
- [ ] Be thorough before presenting — don't require user to point out obvious issues
- [ ] Don't say "I can't" when the data exists — actually CHECK state.json first
- [ ] Context comments properly — figure out where feedback fits in scope
- [ ] Don't ship sections autonomously — iterate live with user

### 4.9 Specific Technical Anti-Patterns
- [ ] NO `Jinja2 | default('X')` for Python None — use `v if v else 'X'` or `| format_na`
- [ ] NO concurrent pipeline runs (SQLite cache contention causes disk I/O errors)
- [ ] NO passing company name to resolver when ticker is known (fuzzy matching causes mismatches)
- [ ] NO `preserveAspectRatio="none"` on SVGs (distorts text)
- [ ] NO `LiabilitiesAndStockholdersEquity` in XBRL fallback tags (corrupts balance sheet)

---

## 5. GOVERNANCE-SPECIFIC REQUIREMENTS

### 5.1 Board Members (each must show)
- [ ] Prior lawsuits against this person (SCAC cross-reference + web search)
- [ ] Personal character / conduct issues (shade factors from web search)
- [ ] Experience and qualifications for their specific role (from DEF 14A bio)
- [ ] Bio summary showing actual biographical info, not compensation data

### 5.2 Executives (each must show)
- [ ] Prior litigation history
- [ ] Character/conduct issues
- [ ] Background and qualifications
- [ ] Tenure computed from appointment dates

### 5.3 Extraction Gaps to Fill
- [ ] DEF 14A prompt must extract biographical info SEPARATE from compensation data
- [ ] Web search: "{name} lawsuit", "{name} SEC", "{name} investigation" for shade factors
- [ ] Director qualifications extracted from proxy bio sections
- [ ] Board attendance, expertise, meeting count, CEO succession plan

---

## 6. NARRATIVE REQUIREMENTS

### 6.1 Story Structure
- [ ] Worksheet tells a RISK STORY, not a data dump
- [ ] Each section answers the question the underwriter has after reading the previous one
- [ ] Executive Brief is the thesis statement; everything after supports it
- [ ] Think: "After financial health, underwriter asks 'who's in charge of this mess?' -> governance answers that"

### 6.2 Investigative Intelligence (Senior Underwriter Mindset)
- [ ] Cross-signal pattern detection: combinations that tell a story (insider selling + auditor change + restatement)
- [ ] Conspicuous absence detection: what's NOT there that SHOULD be (no environmental disclosure for chemical company)
- [ ] Temporal narrative: sequence of events tells causal story (CFO departure -> restatement -> SCA)
- [ ] Contrarian challenge: actively argue against the system's own conclusion
- [ ] Peer-relative surprises: "you're the ONLY one in your peer group with this pattern"
- [ ] Every new capability evaluated against: "Would a senior underwriter do this?"

### 6.3 Content Translation
- [ ] All check results in underwriting language, not system internals
- [ ] Every piece of text shown to underwriter in complete English sentences explaining WHY something matters for D&O risk
- [ ] Raw signal/threshold evidence translated through humanization layer
- [ ] 8-K filing dates accompanied by explanation of what the filing contains and why it matters

---

## 7. DATA REQUIREMENTS

### 7.1 Acquisition Completeness
- [ ] Every analysis run includes proactive discovery searches at START of ACQUIRE
- [ ] Broad web search for company + risk terms, executive names + litigation terms
- [ ] Structured APIs miss: short seller reports, state AG actions, employee lawsuits, social media, early news
- [ ] After structured acquisition, run exploratory searches
- [ ] Single-source results flagged as LOW confidence — but MISSING them entirely is worse

### 7.2 Source Traceability
- [ ] Source = specific filing type + date + URL/CIK reference
- [ ] Confidence = HIGH (audited/official), MEDIUM (unaudited/estimates), LOW (derived/web)
- [ ] Every data point traces: data source -> evaluator -> score contribution -> rendering

### 7.3 Cross-Validation
- [ ] Web-sourced data requires 2+ independent sources
- [ ] SCA extraction cross-validated against web search results
- [ ] "Ensure proper validation and verification, dual validation when possible"
- [ ] "Multiple data sources should not be optional"
- [ ] "Sources that are always consistent can always be trusted"

### 7.4 Data Freshness
- [ ] Most recent filing drives the worksheet
- [ ] If business description shows 2023 data when 2025 filing exists, something is wrong
- [ ] After extraction changes, verify data year matches most recent filing

### 7.5 Incremental Acquisition
- [ ] Don't re-run expensive LLM extractions or API calls unnecessarily
- [ ] State.json IS the data inventory
- [ ] Re-analysis of already-analyzed company should take <30 seconds (re-analyze + re-render only)

### 7.6 Section Data Audit Pattern (Apply to Every Section)
- [ ] Look at what data the section currently shows
- [ ] Look at what data is ACTUALLY AVAILABLE in state.json that ISN'T being used
- [ ] See what ADDITIONAL data could be pulled
- [ ] Decide how to best synthesize and present it with graphics
- [ ] The gap between collected and displayed is often a rendering/context-builder issue, not acquisition

---

## 8. PRODUCT NORTH STAR

> **"The single source of truth for underwriters to make the most knowledgeable decisions on a risk."**

Every decision filtered through:
1. **Single source of truth** — if it's not in the worksheet, it doesn't exist. Completeness is non-negotiable.
2. **Most knowledgeable** — system learns from feedback, gets smarter, surfaces what matters.
3. **Decisions on a risk** — beautiful analytics that tell the risk story at a glance, then let you drill in. CIQ/Bloomberg-quality visualization. Progressive disclosure.
4. **For underwriters** — domain experts are the audience. Augment judgment, don't replace it. Must feel like a tool, not homework.

---

## 9. PRESERVATION RULES

- [ ] NEVER remove existing analytical capabilities (Market Risk Flags, DTL charts, Beneish/Altman, financial forensics, litigation timeline, scoring visualizations)
- [ ] All future work is ADDITIVE — new capabilities alongside existing ones, never replacements
- [ ] Before any refactor: capture current output as golden baseline, verify identical output after
- [ ] "If not bullshit, is gold" — verify accuracy, then preserve
- [ ] Brain changes driven by real evidence, not YAML editing — every change needs: WHY it changed, WHAT evidence drove it, WHAT the expected impact is
