# D&O UNDERWRITING PROJECT — INTERACTION SUMMARY
## All Conversations: December 2025 – February 2026
## Exported February 8, 2026

---

## PROJECT OVERVIEW

Mike is head of underwriting at an MGA with 25+ years of experience. He's built an empirically-calibrated D&O (Directors & Officers) insurance underwriting framework that addresses whether a company is more likely than the baseline 6% chance to face securities class action lawsuits over 18 months, and if so, by how much. The framework works backward from actual securities litigation settlement data (NERA, Cornerstone Research) and uses 10 scoring factors weighted by empirical correlation with litigation outcomes.

The system produces risk scores across five tiers (MINIMAL to EXTREME) that map directly to underwriting decisions including pricing multipliers, retention adjustments, and approval levels.

---

## FRAMEWORK EVOLUTION

| Version | Date | Key Changes |
|---------|------|-------------|
| 4.3 | Dec 2025 | Base framework, 594 checks |
| 4.4 | Dec 2025 | Added NEG-001, VER-001, ZER-001 verification protocols (after MSA miss) |
| 4.5 | Jan 2026 | Added TRI-001 Triage Gate for New vs Renewal routing |
| 4.6 | Jan 2026 | Integrated Streamlined Execution Module, output template v1.1 |
| 4.7 | Jan 2026 | Sector calibration (SEC-001–009), Stock monitoring (STK-001–010), clean rule numbering, v1.2 template |

**Current state**: v4.7 with 287 indexed rules, 661 checks (new business) + 67 (renewal), 10+ industry modules.

**Pending patches** (drafted but never uploaded to project):
- QS-044 to QS-048: Prospective checks (growth catalysts, policy risk, project concentration, competitive position, capital allocation)
- F.5-000: Guidance type prerequisite (company guidance vs analyst consensus distinction)
- OUT-001 to OUT-004: Markdown-first output, mandatory state saves, no TBDs
- FETCH-001/002: SEC EDGAR and Stanford SCAC fallback routing
- v1.3 Markdown output template

---

## COMPLETED ANALYSES (18+)

### 1. MSA Safety (MSA) — INDU | Dec 2025
- **Score**: ~25/100, Below Average
- **Outcome**: Triggered creation of VER-001/ZER-001 protocols
- **Critical lesson**: Missed CFO tenure (<12 months) and a 20% stock drop on first pass. Led to mandatory verification protocols requiring affirmative evidence for every claim and positive evidence for any zero score.
- **Key finding**: New CFO + margin compression + sector headwinds required closer scrutiny than initial pass delivered

### 2. Generac Holdings (GNRC) — INDU | Dec 2025
- **Score**: ~15/100, Low
- **Outcome**: Clean analysis, prospective-only approach for new carriers
- **Key finding**: Clean company, demonstrated framework working properly on straightforward risk

### 3. Design Therapeutics (DSGN) — BIOT | Dec 2025
- **Score**: ~20/100, Below Average
- **Outcome**: Successfully validated biotech industry module
- **Key finding**: Biotech module properly calibrated dismissal rates and binary event risk

### 4. Clear Street Group — FINS (Private) | Jan 2026
- **Score**: N/A (private company)
- **Outcome**: Conditional bind recommendation for pre-IPO company
- **Key finding**: Pre-IPO assessment required different approach — no public stock data, limited financial transparency

### 5. ADT Inc. (ADT) — CDIS | Jan 2026
- **Score**: ~28/100, Below Average
- **Outcome**: Established the formatting template reference (ADT_DO_Analysis_v1_1_Final.docx)
- **Key finding**: Set standards for navy headers, bullet-point format, professional Word doc styling

### 6. CSX Corporation (CSX) — CDIS/Rail | Jan 2026
- **Score**: ~22/100, Below Average
- **Outcome**: Led to creation of Transportation/Freight Rail industry module
- **Key finding**: Rail sector has unique risk factors (derailment liability, regulatory oversight, labor) not covered by existing modules

### 7. Orchid Island Capital (ORC) — REIT | Jan 2026
- **Score**: Initially 9/100, revised to 49/100 after REIT module applied
- **Outcome**: Major lesson — led to complete REIT module rewrite (v2.1)
- **Multiple sessions**: Analysis got stuck on complex docx generation; required REIT module to be rebuilt from educational to action-oriented
- **Key findings**:
  - Initial score of 9 was dangerously low — didn't account for mREIT-specific risks (313% payout ratio, 89% book value erosion, external management)
  - Mike's feedback: module was "too educational" — needs specific thresholds, point adjustments, simple risk tiers that drive pricing
  - Management questions must be ranked by impact with upgrade/downgrade criteria
  - Non-entity coverage gap identified for externally managed REITs

### 8. Edison International (EIX) — UTIL | Jan 2026
- **Score**: 75/100, EXTREME
- **Outcome**: Decline or extreme conditions only
- **Key finding**: Nuclear trigger NT-001 activated (active securities class action re: wildfire liability). DOJ lawsuit, credit downgrade to BBB-, inverse condemnation doctrine exposure. Textbook example of nuclear trigger floor adjustment in practice.

### 9. Discord Inc. — TECH (Private/IPO) | Jan 2026
- **Score**: 58/100, HIGH
- **Outcome**: Support with conditions — prospective-only, $2.5M SIR, child safety exclusions
- **Multiple sessions**: Required 3 chats due to context exhaustion during docx generation
- **Key findings**: IPO Section 11 exposure, 80+ child safety lawsuits pending MDL, NJ AG enforcement, CEO <12 months tenure, down-round valuation ($5-6B vs $15B peak)
- **Used extended search (agent teams)** for comprehensive headwinds and Section 11 liability analysis

### 10. Eikon Therapeutics (EIKN) — BIOT (IPO) | Jan 2026
- **Score**: 28/100, Average (IPO-adjusted)
- **Outcome**: Support with conditions — biotech floor retention + 25% IPO premium
- **Multiple sessions**: Required 3 chats — SEC S-1 fetch timed out repeatedly
- **Key findings**: Elite management team (former Merck executives who developed pembrolizumab), $1.1B+ private funding, Phase 2/3 lead asset with binary event H2 2026
- **Lesson**: When SEC EDGAR fails, fall back to web search for S-1 summary data immediately — don't retry the same failing URL

### 11. Silicon Laboratories (SLAB) — TECH | Jan 2026
- **Score**: ~30/100, Average
- **Outcome**: Quick analysis — material weakness disclosed but no actual suit filed
- **Key finding**: Law firm investigations announced but never converted to filed complaint. Stock recovered. Demonstrates that investigations ≠ litigation.

### 12. TransDigm Group (TDG) — INDU (Aerospace) | Jan 2026
- **Score**: 32/100, Below Average
- **Outcome**: Support renewal at market +20-35%
- **Key findings**: Sole-source aerospace model, 5.8x leverage (normal for sector), DOD price gouging scrutiny from IG reports, CEO succession planned with strong equity alignment
- **Additional deliverable**: Comprehensive management interview guide created from Q4 earnings call transcript, incorporating DOD IG reports and insider trading patterns
- **Meeting notes restructure**: Separate "What Was Said" and "Underwriting Commentary" under each topic

### 13. Primoris Services (PRIM) — INDU | Jan 2026
- **Score**: 5/100, Minimal
- **Outcome**: Support at competitive rates
- **MOST IMPORTANT LESSON**: Lockton underwriter questions exposed that framework was 85% backward-looking. Their questions covered growth catalysts, policy risk, competitive landscape, capital allocation — areas framework didn't address.
- **Mike's correction**: When I proposed 8 new modules and 50+ checks, he said "integrate, don't multiply." Modify existing QS checks instead of creating new categories.
- **F.5 precision error**: Conflated analyst consensus estimates with company-issued guidance. Must first establish whether company provides quarterly guidance at all.
- **Led to**: QS-044 to QS-048 prospective checks, F.5-000 prerequisite (both drafted, never uploaded)

### 14. Kaiser Aluminum (KALU) — INDU | Jan 2026
- **Score**: 19/100, Low (revised from 21 after correcting insider buying classification)
- **Outcome**: Bind at flat to +2% pricing
- **Lesson**: Mike frustrated by TBD placeholders in initial output — "why are they there????" Led to rule: never leave TBDs, mark 🟣 UNKNOWN with search documentation instead.
- **Interest coverage correction**: Initial calculation used outdated 2024 annual data instead of Q3 2025 quarterly. Corrected from 2.0x to 6.7x — significant impact on financial profile assessment.
- **Additional deliverable**: Aluminum industry dynamics section with competitive landscape analysis

### 15. NeuroPace (NPCE) — HLTH (Medical Devices) | Jan 2026
- **Score**: ~55/100, High
- **Outcome**: Immediate escalation to senior management
- **Key findings**: Failed NAUTILUS clinical trial (May 2025) caused 28.4% single-day stock drop, multiple plaintiff firm investigations, CFO departed 24 days after trial failure despite 25-year tenure
- **Sector classification note**: HLTH not BIOT — has FDA-approved products generating ~$80M revenue, but clinical trial exposure similar to biotech

### 16. Paycom Software (PAYC) — TECH | Jan 2026
- **Score**: N/A — focused on meeting notes and management interview
- **Outcome**: Moved from "WALK" to "CAUTION (conditional)" — derivative investigation status must be clarified before binding
- **Key findings**: CFO Bob Foster, CLO Matt, CAO Jason Farmer, and Director of Risk Josh Blair attended. Critical gap: management completely avoided discussing derivative investigation and CIO departure.
- **Formatting lesson**: "What Was Said" and "Underwriting Commentary" must flow together under each topic, not be in separate sections

### 17. Liftoff Mobile — TECH (Private/IPO) | Jan 2026
- **Score**: N/A
- **Outcome**: DECLINE PRIMARY; CONSIDER EXCESS WITH CONDITIONS
- **Key findings**: 7.5x EBITDA debt burden (well above 4.0x tech threshold), Section 11 strict liability for 12 months post-IPO, AppLovin competitive dominance
- **Litigation scenario analysis**: 5 ranked scenarios — post-IPO guidance miss (45-55%), revenue recognition restatement (30-40%), AI washing (25-35%), data privacy (20-30%), debt crisis (15-25%)
- **Used extended search** for comprehensive S-1 and competitive analysis

### 18. Jack in the Box (JACK) — CDIS (Restaurant) | Feb 2026
- **Score**: 45/100, Average
- **Outcome**: Elevated review required
- **Key findings**: 93% franchised (key risk amplifier), AJP/NHG lawsuit, 150-200 closures, active securities investigations
- **Additional deliverable**: Franchise risk supplement created — unique exposure framework for highly-franchised companies

---

## INDUSTRY MODULES CREATED/UPDATED

| Module | Sector Code | Date | Key Event |
|--------|-------------|------|-----------|
| Biotech | BIOT | Dec 2025 | Built from empirical dismissal rate data (72%+ for small biotechs) |
| Technology | TECH | Dec 2025 | Comprehensive — 900+ lines, covers SaaS, hardware, pre-revenue |
| Financials | FINS | Dec 2025 | v3 — covers banks, insurance, asset managers, fintech |
| CPG/Consumer Staples | STPL | Dec 2025 | Product liability, recall risk, supply chain |
| Healthcare Services | HLTH | Jan 2026 | Non-biotech healthcare — hospitals, devices, services |
| Energy/Oil & Gas | ENGY | Jan 2026 | Commodity exposure, environmental liability, transition risk |
| Industrials/Manufacturing | INDU | Jan 2026 | Fixed-price contracts, labor, supply chain, cyclicality |
| REITs/Real Estate | REIT | Jan 2026 | v2 rewrite after ORC lesson — action-oriented, mREIT-specific |
| Media/Entertainment | COMM | Jan 2026 | Content liability, streaming economics, ad market exposure |
| Transportation/Rail | CDIS/Rail | Jan 2026 | Created after CSX analysis — derailment, labor, regulatory |
| IPO Supplement | N/A | Jan 2026 | Path-specific: traditional IPO (13%), de-SPAC (14-20%), direct listings |

---

## FRAMEWORK DEVELOPMENT SESSIONS

### Session: SEC Arbitration Analysis (Jan 2026)
- Analyzed Bloomberg Law article about Sept 2024 SEC ruling allowing mandatory arbitration
- Impact: Could fundamentally change D&O pricing if adopted
- Conflict with Delaware §115(c) creates uncertainty
- Recommended monitoring for adoption patterns

### Session: AI Chatbot / Character.AI Settlement Analysis (Jan 2026)
- Analyzed WSJ article about teen suicide AI chatbot settlements
- Created underwriting note with risk classifications for AI companies
- Mike requested fact-check — caught overstated claims about "first" AI settlement
- Key insight: AI product liability creating new D&O exposure vectors

### Session: D&O Settlement Distribution (Feb 2026)
- Expanded from 10-year to 20-year analysis (2005-2024)
- Mike caught defense cost methodology issues — costs sometimes included, sometimes separate
- Key finding: No comprehensive defense cost database exists (per Stanford)
- Defense costs range: $500K (MTD dismissal) to $20M+ (trial)

### Session: Fiduciary Liability Framework (Jan 2026)
- Mike requested ERISA/fiduciary underwriting framework
- Initial version was over-engineered — mirrored D&O triage gates
- Mike corrected: "This is a single-pass system with limited standard checks. No triage gates needed."
- Tested on Primoris — 27/100 LOW, bind at standard terms

### Session: Framework Audit & Structure (Jan 2026)
- Discovered 07_MARKET_DYNAMICS.md was completely missing despite being referenced everywhere
- Found encoding corruption across 22 files
- Identified inflated header check counts vs actual content
- Created naming convention restructure (later reverted to simpler approach)

### Session: Sector Calibration & Stock Monitoring (Jan 2026)
- Mike identified Quick Screen used absolute thresholds when metrics are sector-relative
- Created SEC-001 to SEC-009 sector calibration rules with 13 sector codes
- Created STK-001 to STK-010 stock performance module replacing 3 legacy checks
- Attribution analysis (company vs sector vs market) and pattern detection (CASCADE, BREAKDOWN)
- Clean sequential numbering eliminated all letter suffixes

### Session: Output Template & Token Efficiency (Jan 2026)
- Diagnosed context window exhaustion as #1 operational problem
- Docx generation costs ~15K tokens per analysis — markdown saves ~12K
- Drafted v1.3 markdown template with full v1.2 parity
- Mike agreed markdown is default output going forward
- State file protocol for conversation continuity

### Session: Comprehensive Memory Setup (Feb 2026)
- Reviewed all 35+ conversations to populate 30/30 memory slots
- Categorized memories: operational rules, lessons, framework state, quality standards, analytical knowledge, case references
- Clarified distinction: memory = operational sticky notes, project files = executable framework
- Committed to showing memory contents at start of relevant conversations

---

## RECURRING ISSUES IDENTIFIED

### Critical
1. **Context window exhaustion**: 6+ analyses required multi-chat continuations. Root cause: docx inline generation (~15K tokens) + full module loads + uncompressed search results
2. **SEC EDGAR / Stanford SCAC failures**: Eikon S-1 timed out 3x. Stanford unreliable. Need fallback routing.

### Important
3. **Orphaned patches**: QS-044–048, F.5-000, output rules drafted but never uploaded to project
4. **Framework 85% backward-looking**: Prospective checks exist as patches only
5. **F.5 guidance vs consensus confusion**: Prerequisite step drafted but not integrated
6. **TBD placeholders in output**: Kaiser analysis delivered incomplete — research gaps must be filled or explicitly documented
7. **Check count inflation**: File headers claim more checks than exist (Litigation: 37→31, Financial: 112→104, Business: 74→64)

### Minor
8. **Inconsistent file naming**: Some modules have version numbers, some don't
9. **Superseded files still in project**: v1.1 template, F.2 patch, renumbering map, issues inventory, corrupted REIT docx
10. **F.2/STK integration incomplete**: Patch file exists separately, not merged into main scoring

---

## KEY PRINCIPLES ESTABLISHED

1. **Red flags escalate, not auto-decline** — Final bind/decline decisions rest with underwriting team
2. **Integration over multiplication** — Modify existing checks rather than adding new modules
3. **Empirical over theoretical** — Work backward from actual settlement data, not assumptions
4. **Thoroughness over speed** — Never take shortcuts, especially with data verification
5. **Action-oriented modules** — Specific thresholds and point adjustments, not educational content
6. **Affirmative verification** — "Didn't find a problem" ≠ "Verified no problem"
7. **Sector-relative thresholds** — 6x Debt/EBITDA is normal for REITs but distressing for tech
8. **Fill gaps, don't punt** — No TBDs; mark 🟣 UNKNOWN with search documentation
9. **Management questions must move the needle** — If the answer can't change the decision, don't ask
10. **Markdown-first output** — Preserve context budget for analysis, not document formatting

---

## FILES IN THIS EXPORT

### Core Framework
- `00_PROJECT_INSTRUCTIONS_V4_7.md` — Master instructions (v4.7 current)
- `01_QUICK_SCREEN_V4_7.md` — 40 QS checks + SEC calibration + STK module
- `02_TRIGGER_MATRIX_V4_7.md` — Maps findings to deep-dive sections
- `10_SCORING.md` — 10-factor scoring methodology
- `10_SCORING_F2_UPDATE.md` — F.2 patch (needs merge into 10_SCORING)
- `11_OUTPUT_TEMPLATE_V1_1.md` — Old template (superseded)
- `11_OUTPUT_TEMPLATE_V1_2.md` — Current template
- `12_OUTPUT_TEMPLATE_V3_0.md` — Comprehensive diagnostic format
- `13_SECTOR_BASELINES.md` — Sector norms reference
- `14_STOCK_MONITORING_REFERENCE.md` — STK calculation methodology
- `RULE_INDEX_V4_7.md` — Master rule index (287 rules)
- `RULE_RENUMBERING_MAP.md` — Legacy conversion map (can delete)
- `PROJECT_ISSUES_INVENTORY.md` — Resolved issues (can delete)

### Deep-Dive Sections
- `03_LITIGATION_REGULATORY.md`
- `04_FINANCIAL_HEALTH.md`
- `05_BUSINESS_MODEL.md`
- `06_GOVERNANCE.md`
- `07_MARKET_DYNAMICS.md`
- `08_ALTERNATIVE_DATA.md`
- `09_PRIOR_ACTS_PROSPECTIVE.md`

### Industry Modules
- `biotech_industry_module_supplement.md`
- `technology_industry_module_supplement.md`
- `financials_industry_module_supplement_v3.md`
- `healthcare_industry_module_supplement.md`
- `energy_oil_gas_industry_module_supplement.md`
- `industrials_manufacturing_industry_module_supplement.md`
- `reits_real_estate_industry_module_supplement_v2.md`
- `cpg_industry_module_supplement.md`
- `media_entertainment_industry_module_supplement.md`
- `transportation_freight_rail_industry_module_supplement.md`

### Renewal & Reference
- `renewal_analysis_module_v1.md`
- `ADT_DO_Analysis_v1_1_Final.docx` — Formatting reference
- `REITs_Industry_Module_v2_1.docx` — Duplicate (can delete)

### Added by This Export
- `MEMORY_EXPORT.md` — All 30 memory slots
- `INTERACTION_SUMMARY.md` — This file
- `FRAMEWORK_AUDIT_v4_7_FEB_2026.md` — Detailed audit with improvement recommendations

---

**END OF INTERACTION SUMMARY**
