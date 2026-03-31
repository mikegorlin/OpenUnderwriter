# D&O Risk Taxonomy Audit

## Purpose
Complete audit of the D&O liability risk universe against the current brain system (400 signals, 36 YAML files, 8 domains). Identifies gaps, overlaps, and structural issues to inform the v2.0 brain redesign.

---

## Part 1: Complete D&O Risk Taxonomy

### 1.1 Securities Litigation (SCAs)

#### 1.1.1 Section 10(b) / Rule 10b-5 (Exchange Act)
- **Frequency**: HIGH. ~220 core filings/year (2024: 225 total, 220 core per Cornerstone Research). The dominant claim type.
- **Severity**: Average settlement $56M (H1 2025 per Allianz, up 27%); median ~$9-15M. Defense costs ~20-25% of indemnity.
- **Statute**: 2-year SOL (discovery), 5-year repose (violation).
- **Leading indicators**: Stock drop >10% on corrective disclosure, insider selling pre-drop, earnings miss/guidance withdrawal, restatement, SEC investigation, short seller report, analyst downgrade.
- **Correlation**: Co-occurs with derivative suits ~50% of the time. SEC enforcement amplifies. Restatements are strongest predictor.
- **Industry variation**: Tech/biotech highest frequency. Financial services highest severity.

#### 1.1.2 Section 11 (Securities Act)
- **Frequency**: MEDIUM. Tied to IPOs, SPACs, secondary offerings. ~30-50/year.
- **Severity**: Typically lower than 10b-5 (strict liability, no scienter needed, but damages capped at offering price).
- **Statute**: 1-year SOL (discovery), 3-year repose (offering).
- **Leading indicators**: IPO within 3 years, lock-up expiry, S-1 prospectus risk factor inadequacy, post-IPO stock decline below offering price.
- **Industry variation**: SPACs (declining), biotech (clinical trial failures post-IPO), tech IPOs.

#### 1.1.3 Section 12(a)(2) (Securities Act)
- **Frequency**: LOW-MEDIUM. Often piggybacks Section 11 claims.
- **Severity**: Similar to Section 11; rescission remedy.
- **Leading indicators**: Same as Section 11.

#### 1.1.4 Section 14(a) (Exchange Act - Proxy Fraud)
- **Frequency**: MEDIUM. Rising trend with M&A challenges, say-on-pay failures.
- **Severity**: Lower typical settlements; can be very high in M&A context.
- **Statute**: 1-year SOL (discovery), 3-year repose (proxy solicitation).
- **Leading indicators**: Proxy contest, say-on-pay failure (<70% support), M&A deal challenge, inadequate merger disclosure.
- **Industry variation**: Broad; concentrated during M&A waves.

### 1.2 Shareholder Derivative Suits

- **Frequency**: MEDIUM-HIGH. Accompanies ~50% of securities class actions. Standalone frequency increasing.
- **Severity**: Historically modest ($5-50M range), but trending UP. Multi-hundred-million settlements now occurring (e.g., derivative settlements following Caremark duty failures).
- **Leading indicators**: Board independence <67%, CEO/Chair duality, related-party transactions, material weakness in internal controls, board member prior litigation.
- **Correlation**: Strongly correlated with SCA filings, SEC enforcement, and corporate governance failures.
- **Industry variation**: Broad; higher in companies with entrenched boards, dual-class structures.

### 1.3 SEC Enforcement Actions

- **Frequency**: MEDIUM. ~600-800 actions/year across all types. Individual D&O-relevant subset ~100-200/year.
- **Severity**: Fines range $100K-$100M+. Disgorgement often exceeds fines. Officer/director bars. Defense costs ~30% of indemnity.
- **Statute**: 5-year SOL for fraud claims.
- **Leading indicators**: SEC comment letters (accounting-focused), Wells Notice receipt, informal investigation disclosure, whistleblower tip, restatement, material weakness.
- **Correlation**: Frequently precedes follow-on SCA and derivative suits. SEC-parallel litigation is most severe.
- **Industry variation**: Financial services, pharma/biotech, crypto.

### 1.4 DOJ / Criminal Investigations

- **Frequency**: LOW (for D&O-relevant corporate criminal cases). ~20-30 major corporate actions/year.
- **Severity**: EXTREME. Criminal penalties, imprisonment of officers, deferred prosecution agreements. D&O policies typically exclude criminal fines but cover defense costs up to final adjudication.
- **Leading indicators**: FCPA-sensitive geography, healthcare fraud indicators, antitrust cartel behavior, accounting fraud signals.
- **Industry variation**: Healthcare (FCA/kickbacks), defense contractors, financial services, pharma.

### 1.5 State Attorney General Actions

- **Frequency**: MEDIUM. Increasing trend, especially multi-state coordinated actions.
- **Severity**: Variable. Consumer protection fines can be massive ($100M+). Opioid/tobacco-scale actions rare but catastrophic.
- **Leading indicators**: Consumer complaint spikes, state-level regulatory scrutiny, product safety issues, privacy violations.
- **Industry variation**: Consumer-facing companies, pharma, tech (privacy), financial services.

### 1.6 Other Regulatory Actions

#### CFPB (Consumer Financial Protection Bureau)
- **Frequency**: MEDIUM for financial services companies.
- **Severity**: Fines $1M-$100M+. Consent orders common.
- **Industry variation**: Banks, fintech, mortgage, student lending.

#### FTC (Federal Trade Commission)
- **Frequency**: MEDIUM. Antitrust and consumer protection.
- **Severity**: Variable. Consent decrees, fines, behavioral remedies.
- **Industry variation**: Tech (antitrust), consumer products, healthcare.

#### FDA (Food and Drug Administration)
- **Frequency**: MEDIUM for pharma/biotech/medical device.
- **Severity**: Warning letters to product recalls to criminal prosecution. Market impact enormous.
- **Industry variation**: Pharma, biotech, medical devices, food.

#### EPA (Environmental Protection Agency)
- **Frequency**: LOW-MEDIUM.
- **Severity**: Fines + remediation costs. Personal liability for officers under environmental statutes.
- **Industry variation**: Chemicals, mining, energy, manufacturing.

#### OSHA (Occupational Safety and Health)
- **Frequency**: MEDIUM for industrial companies.
- **Severity**: Fines typically modest; headline risk significant.
- **Industry variation**: Construction, manufacturing, energy, logistics.

### 1.7 Employment Practices Liability (EPL)

- **Frequency**: HIGH. Most common claim type by count for private companies. ~20% of private D&O claims.
- **Severity**: Typically $500K-$10M. Class actions can be $50M+. Wage/hour class actions trending severe.
- **Leading indicators**: Employee count >1,000, workforce reductions, labor union activity, Glassdoor complaints, discrimination complaints.
- **Correlation**: Whistleblower complaints often precede both EPL and securities claims.
- **Industry variation**: Retail, hospitality, tech (age/gender discrimination), healthcare.

### 1.8 Fiduciary Duty Breaches (Caremark / State Law)

- **Frequency**: MEDIUM. Increasing trend with Delaware Chancery Court oversight claims.
- **Severity**: Variable. Caremark oversight claims historically dismissed; now succeeding more often. Boeing, McDonald's, Clovis precedents.
- **Leading indicators**: Safety incidents, regulatory violations, compliance failures, lack of board oversight of key risks.
- **Correlation**: Product liability events, environmental disasters, data breaches often trigger Caremark claims.
- **Industry variation**: Broad; recent focus on pharma (opioids), tech (safety), aviation.

### 1.9 M&A Related Claims

- **Frequency**: HIGH during deal activity periods. Merger objection suits were historically 90%+ of deals but have declined post-Trulia (2016).
- **Severity**: Highly variable. Disclosure-only settlements declining. Damages-based claims $10M-$1B+.
- **Leading indicators**: Active M&A (acquirer or target), premium to market >30%, management buyouts, going-private transactions, fairness opinion challenges.
- **Correlation**: Section 14(a) proxy claims, appraisal litigation, activist campaigns.
- **Industry variation**: Concentrated in sectors with high deal activity (tech, pharma, financial services).

### 1.10 Cyber / Data Breach Director Liability

- **Frequency**: MEDIUM and rising sharply. Post-breach derivative suits now standard.
- **Severity**: $10M-$100M+ in combined defense + settlement. Yahoo/Equifax-scale breaches created new precedents.
- **Leading indicators**: Inadequate cybersecurity disclosure (Item 1C), prior breach history, SEC cybersecurity rule non-compliance, volume of PII stored, third-party vendor risk.
- **Correlation**: SEC enforcement for disclosure failures, state AG actions (privacy), FTC enforcement, consumer class actions.
- **Industry variation**: Financial services, healthcare, retail, tech (data-intensive companies).

### 1.11 ESG / Climate Disclosure Liability

- **Frequency**: LOW but rapidly emerging. "Greenwashing" claims increasing. SEC climate rule uncertainty.
- **Severity**: Unknown/developing. Settlement precedents limited. Regulatory fines growing.
- **Leading indicators**: ESG claims in marketing/disclosures, California climate disclosure law compliance, EU CSRD obligations, emissions reduction commitments, ESG-linked executive comp.
- **Correlation**: Activist campaigns, state AG investigations, shareholder proposals.
- **Industry variation**: Energy/oil & gas (highest exposure), manufacturing, financial services (green finance claims).

### 1.12 Antitrust Exposure

- **Frequency**: LOW-MEDIUM. ~15-25 significant D&O-relevant antitrust matters/year.
- **Severity**: HIGH. Treble damages, government fines (EU fines frequently $1B+), follow-on class actions.
- **Statute**: 4-year SOL.
- **Leading indicators**: Market dominance/monopoly position, acquisition patterns, competitor collusion indicators, trade association involvement.
- **Correlation**: DOJ criminal investigations, multi-district litigation.
- **Industry variation**: Tech (platform dominance), pharma (reverse payment), financial services, industrials.

### 1.13 Bankruptcy / Insolvency Director Liability

- **Frequency**: MEDIUM and rising. 22,762 business bankruptcy filings in FY2024 (33% increase YoY per WTW). Zone of insolvency shifts fiduciary duties from shareholders to creditors.
- **Severity**: VERY HIGH. Trustee clawback actions, preference claims, fraudulent transfer suits. D&O policies often exhausted.
- **Leading indicators**: Going concern opinion, Z-Score <1.81, cash burn <12 months, covenant breach, negative working capital, credit downgrade.
- **Correlation**: Zone of insolvency claims, ERISA violations, employment claims, preference actions.
- **Industry variation**: Retail (brick-and-mortar), energy, real estate, tech startups.

### 1.14 FCPA / Anti-Bribery

- **Frequency**: LOW-MEDIUM. ~20-40 FCPA enforcement actions/year.
- **Severity**: VERY HIGH. Corporate fines $10M-$2B+. Individual criminal liability. Disgorgement.
- **Statute**: 5-year SOL.
- **Leading indicators**: Operations in high-corruption countries (CPI <40), government contract reliance, use of third-party agents/distributors, inadequate FCPA compliance program.
- **Correlation**: DOJ + SEC parallel enforcement. Follow-on SCA and derivative claims.
- **Industry variation**: Defense/aerospace, pharma, energy, construction, technology.

### 1.15 Tax Controversy

- **Frequency**: LOW for D&O-relevant claims.
- **Severity**: Variable. Transfer pricing disputes and tax shelter claims can be massive.
- **Leading indicators**: Aggressive tax positions (effective rate <15% for US companies), tax haven subsidiaries, uncertain tax positions (UTPs), IRS audit.
- **Industry variation**: Multinational tech (profit shifting), pharma, financial services.

### 1.16 IP Litigation Exposure

- **Frequency**: MEDIUM-HIGH for IP-dependent companies. Patent trolls create high volume.
- **Severity**: Variable. Royalties/injunctions can be existential. Typically not a D&O claim per se unless directors failed oversight.
- **Leading indicators**: Patent portfolio concentration, freedom-to-operate risks, competitor patent filings.
- **Industry variation**: Tech, pharma (Hatch-Waxman), semiconductors.

### 1.17 Customer / Vendor Disputes Escalating to D&O

- **Frequency**: LOW for direct D&O claims. More commonly a commercial dispute.
- **Severity**: Variable. When a major customer/vendor dispute threatens going concern, it becomes D&O relevant.
- **Leading indicators**: Customer concentration >25%, contract termination, supplier single-source dependency.
- **Industry variation**: Defense contractors (government contracts), retail (key vendor), manufacturing.

### 1.18 Whistleblower-Triggered Claims

- **Frequency**: MEDIUM. SEC whistleblower program has generated >$1B in awards since inception.
- **Severity**: HIGH. Whistleblower tips lead to SEC enforcement which leads to SCA/derivative follow-on.
- **Leading indicators**: SEC whistleblower awards in industry, employee turnover in compliance roles, compliance hiring surge, internal investigation disclosures.
- **Industry variation**: Financial services, pharma, tech, government contractors.

### 1.19 AI-Related D&O Claims (Emerging)

- **Frequency**: LOW but accelerating rapidly. 15 AI-related SCA filings in 2024 (doubled from 7 in 2023). 50+ lawsuits in past 5 years per Allianz.
- **Severity**: Unknown/developing. "AI-washing" claims follow traditional 10b-5 patterns.
- **Leading indicators**: AI revenue claims in disclosures, AI-washing in marketing, regulatory uncertainty for AI products, AI-related capex commitments.
- **Industry variation**: Tech/AI companies (highest), any company making AI capability claims.

---

## Part 2: Current Brain Coverage Map

### 2.1 Domain Summary (400 Signals)

| Domain | Files | Signals | Description |
|--------|-------|---------|-------------|
| biz/ | 4 | 43 | Business profile, competitive, dependencies, model |
| exec/ | 2 | 20 | Executive activity (insider, departure), profile (tenure, board) |
| fin/ | 5 | 58 | Accounting, balance sheet, forensic, income, temporal |
| fwrd/ | 6 | 79 | Disclosure, events, macro, warnings (ops, sentiment, tech) |
| gov/ | 6 | 85 | Activist, board, effectiveness, exec comp, insider, pay, rights |
| lit/ | 5 | 65 | Defense, other litigation, regulatory, SEC, SCA, SCA history |
| nlp/ | 1 | 15 | NLP-based disclosure analysis |
| stock/ | 7 | 35 | Ownership, patterns, price, short, insider, valuation, trading |
| **TOTAL** | **36** | **400** | |

### 2.2 Mapping to Risk Taxonomy

#### WELL-COVERED (Strong signal density):

| Risk Type | Signal Count | Key Signal IDs | Assessment |
|-----------|-------------|----------------|------------|
| **10b-5 Securities Class Actions** | ~50+ | LIT.SCA.*, STOCK.PRICE.*, STOCK.PATTERN.*, FIN.GUIDE.*, EXEC.INSIDER.* | EXCELLENT. Deep coverage of all SCA dimensions: active status, allegations, exposure, class period, settlements, filing patterns. Stock patterns (event collapse, cascade, short attack) directly model SCA triggers. |
| **Financial Fraud / Accounting Manipulation** | ~30+ | FIN.ACCT.*, FIN.FORENSIC.*, FIN.QUALITY.*, FIN.TEMPORAL.* | EXCELLENT. Beneish M-Score, Dechow F-Score, Montier C-Score, Sloan Accrual Ratio, convergence amplifiers, restatement history/magnitude/pattern/auditor-link. Best-in-class forensic coverage. |
| **Corporate Governance** | ~50+ | GOV.BOARD.*, GOV.ACTIVIST.*, GOV.EFFECT.*, GOV.EXEC.*, GOV.PAY.*, GOV.RIGHTS.* | EXCELLENT. Board independence, tenure, attendance, overboarding, departures, CEO/Chair duality, diversity, qualifications, character/conduct, prior litigation. Activist coverage (14 signals) is particularly deep. |
| **Executive Risk / Insider Trading** | ~25+ | EXEC.*, GOV.INSIDER.*, STOCK.INSIDER.* | STRONG. CEO/CFO net selling, cluster selling, 10b5-1 plans, departure timing, c-suite turnover, prior litigation. |
| **SEC Enforcement** | ~15+ | LIT.REG.sec_investigation, LIT.REG.sec_active, LIT.REG.sec_severity, FIN.ACCT.sec_correspondence, LIT.REG.wells_notice, LIT.REG.comment_letters | GOOD. Covers investigation, active enforcement, severity, correspondence, Wells notices, comment letters. |
| **Liquidity / Distress** | ~15+ | FIN.LIQ.*, FIN.DEBT.*, FWRD.WARN.zone_of_insolvency | GOOD. Current ratio, working capital, cash burn, debt structure/coverage/maturity/covenants, credit ratings. |
| **Disclosure Quality** | ~20+ | FWRD.DISC.*, FWRD.NARRATIVE.*, NLP.* | GOOD. MD&A depth, risk factor evolution, non-GAAP reconciliation, NLP tone/readability analysis. |
| **Forward-Looking Events** | ~17 | FWRD.EVENT.* | GOOD. Earnings calendar, M&A closing, synergies, guidance risk, covenant tests, regulatory decisions. |

#### PARTIALLY COVERED (Some signals, but gaps):

| Risk Type | Signal Count | Key Gaps | Assessment |
|-----------|-------------|----------|------------|
| **Derivative Suits** | ~5 | LIT.SCA.derivative, LIT.SCA.demand exist but no dedicated derivative exposure scoring | PARTIAL. Derivative suits lumped with SCA signals. No standalone derivative frequency/severity model, no Caremark oversight duty signals. |
| **Regulatory (Non-SEC)** | ~12 | LIT.REG.doj_investigation, LIT.REG.ftc_investigation, LIT.REG.cfpb_action, LIT.REG.state_ag, LIT.REG.epa_action, LIT.REG.fda_warning, LIT.REG.osha_citation, etc. | PARTIAL. Signals exist but most map to a single generic field. No depth per regulator (CFPB complaint volume, FDA warning letter severity, etc.). Many are "intentionally-unmapped" due to data access. |
| **M&A Risk** | ~5 | FWRD.EVENT.ma_closing, FWRD.EVENT.synergy, FWRD.EVENT.integration | PARTIAL. Post-close integration/synergy covered. MISSING: target/acquirer premium analysis, merger objection lawsuit risk, fairness opinion adequacy, deal financing risk. |
| **Cyber / Data Breach** | ~3 | BIZ.UNI.cyber_posture, BIZ.UNI.cyber_business | PARTIAL. Item 1C disclosure captured. MISSING: prior breach history count, PII volume assessment, third-party vendor risk, SEC cybersecurity rule compliance, post-breach litigation prediction. |
| **Antitrust** | ~2 | LIT.OTHER.antitrust, BIZ.COMP.market_position (chain_role: antitrust_claims) | WEAK. Antitrust signal exists but is a single generic litigation type. No market dominance scoring, no competitor collusion indicators, no merger antitrust risk assessment. |
| **Bankruptcy / Insolvency** | ~5 | FWRD.WARN.zone_of_insolvency, FIN.LIQ.cash_burn, FIN.DEBT.covenants, chain_role: distress_to_bankruptcy | PARTIAL. Financial distress well-covered. MISSING: Preference action risk, fraudulent transfer indicators, trustee clawback exposure, creditor duty shift assessment. |
| **Employment Practices** | ~3 | LIT.OTHER.employment, LIT.OTHER.whistleblower, BIZ.DEPEND.labor | WEAK. Generic employment litigation signal exists. No discrimination claim frequency, no wage/hour class action risk, no workforce reduction litigation triggers. |
| **ESG / Climate** | ~1 | FWRD.MACRO.climate_transition_risk | MINIMAL. One generic climate signal. No ESG disclosure adequacy, no greenwashing risk, no Scope 1/2/3 liability, no California climate law compliance. |
| **AI-Related Claims** | ~5 | BIZ.UNI.ai_claims, FWRD.WARN.ai_revenue_concentration, FWRD.WARN.hyperscaler_dependency, FWRD.WARN.gpu_allocation, FWRD.WARN.data_center_risk | PARTIAL. Good for AI-specific companies. Needs AI-washing assessment for non-AI companies that make AI claims in disclosures. |

#### UNCOVERED or MINIMAL (Major gaps):

| Risk Type | Signal Count | Assessment |
|-----------|-------------|------------|
| **FCPA / Anti-Bribery** | 0 dedicated | CRITICAL GAP. claim_types.json defines FCPA but NO signal evaluates FCPA risk. No corruption jurisdiction analysis, no third-party agent risk, no FCPA compliance program assessment. |
| **Tax Controversy** | 0 | GAP. No effective tax rate analysis vs. peers, no uncertain tax position monitoring, no transfer pricing risk, no tax haven subsidiary assessment (despite tax_havens.json config existing). |
| **IP Litigation Exposure** | 1 generic | WEAK. LIT.OTHER.ip exists as a generic litigation type. No patent portfolio assessment, no freedom-to-operate risk, no competitor patent activity. |
| **Product Liability (as D&O trigger)** | 1 generic | WEAK. LIT.OTHER.product exists. No product recall risk scoring, no FDA/CPSC/NHTSA linkage to D&O claims, no product liability reserve adequacy. |
| **Environmental Liability** | 1 generic | WEAK. LIT.OTHER.environmental exists. No Superfund site exposure, no environmental reserve adequacy, no environmental permit compliance. |
| **Government Contract Risk** | 1 generic | WEAK. LIT.OTHER.gov_contract exists. No False Claims Act risk assessment, no debarment risk, no contract concentration scoring. |
| **ERISA Fiduciary Liability** | 1 | MINIMAL. LIT.SCA.erisa exists as a litigation type. No ERISA-specific risk factors (stock drop plans, company stock concentration in retirement plans, fee reasonableness). |
| **Caremark / Oversight Duty** | 0 | CRITICAL GAP. No signals evaluate whether the board has adequate oversight mechanisms for key business risks (safety, compliance, cybersecurity). This is the fastest-growing derivative claim theory. |
| **Whistleblower Risk (Quantified)** | 1 generic | WEAK. FWRD.WARN.whistleblower_exposure exists. No SEC whistleblower award tracking for the industry, no internal investigation history, no retaliation claim risk. |

---

## Part 3: Gap Analysis

### 3.1 Critical Gaps (Must Add)

1. **FCPA / Anti-Bribery Risk**
   - ZERO signals for a $2B+ penalty risk category
   - Config file `tax_havens.json` exists but is not linked to any signal
   - Need: Corruption jurisdiction analysis (based on revenue_geo), third-party agent risk, FCPA compliance program disclosure, prior FCPA investigation history
   - Suggested signals: LIT.FCPA.jurisdiction_risk, LIT.FCPA.agent_intermediary, LIT.FCPA.compliance_program, LIT.FCPA.prior_actions

2. **Caremark / Board Oversight Duty**
   - ZERO dedicated signals for the fastest-growing derivative claim theory
   - Post-Boeing, post-McDonald's, courts are sustaining Caremark claims at unprecedented rates
   - Need: Board oversight of safety, compliance, cybersecurity. "Red flags" that board should have noticed.
   - Suggested signals: GOV.OVERSIGHT.safety_program, GOV.OVERSIGHT.compliance_program, GOV.OVERSIGHT.cyber_oversight, GOV.OVERSIGHT.risk_committee

3. **Derivative Suit Exposure Scoring**
   - Derivative suits are 50% correlated with SCAs and settlements are escalating
   - Current system treats derivatives as a subset of SCA rather than an independent risk
   - Need: Standalone derivative exposure model with demand futility analysis
   - Suggested signals: LIT.DERIV.demand_futility, LIT.DERIV.caremark_flags, LIT.DERIV.compensation_waste, LIT.DERIV.related_party_self_dealing

4. **ESG / Climate Disclosure Liability**
   - Only 1 generic climate signal in an area with rapidly emerging litigation
   - SEC climate rule, California SB 253/261, EU CSRD all create new disclosure obligations
   - Need: ESG disclosure adequacy, greenwashing risk, emissions commitment tracking
   - Suggested signals: ESG.DISC.climate_claims, ESG.DISC.scope_reporting, ESG.DISC.regulatory_compliance, ESG.DISC.greenwashing_risk

5. **Employment Practices Liability (EPL)**
   - Only 3 generic signals for the highest-frequency D&O claim type
   - Need: Discrimination claim history, wage/hour class action risk, workforce reduction litigation triggers, EEOC complaint tracking
   - Suggested signals: LIT.EPL.discrimination_history, LIT.EPL.wage_hour_risk, LIT.EPL.rif_litigation, LIT.EPL.eeoc_complaints

### 3.2 Important Gaps (Should Add)

6. **Cyber Breach D&O Exposure (Deepened)**
   - Current: 2 signals (posture, business impact)
   - Need: Prior breach count, PII volume assessment, SEC Item 1C compliance adequacy, cybersecurity insurance program, incident response readiness
   - Suggested signals: BIZ.CYBER.breach_history, BIZ.CYBER.pii_volume, BIZ.CYBER.sec_compliance, BIZ.CYBER.insurance_program

7. **Tax Controversy Risk**
   - Need: Effective tax rate vs. peers, uncertain tax positions, transfer pricing risk, tax haven subsidiary analysis
   - Suggested signals: FIN.TAX.effective_rate, FIN.TAX.uncertain_positions, FIN.TAX.transfer_pricing, FIN.TAX.haven_exposure

8. **M&A Litigation Risk (Deepened)**
   - Need: Target premium analysis, merger objection probability, fairness opinion adequacy, deal financing risk, buyer integration history
   - Suggested signals: FWRD.MA.premium_analysis, FWRD.MA.objection_risk, FWRD.MA.fairness_opinion, FWRD.MA.financing_risk

9. **Antitrust Risk (Deepened)**
   - Need: Market dominance assessment, acquisition antitrust risk, competitor collusion indicators, HSR second request probability
   - Suggested signals: LIT.ANTI.market_dominance, LIT.ANTI.acquisition_risk, LIT.ANTI.collusion_indicators

10. **ERISA Fiduciary Liability (Deepened)**
    - Need: Company stock in retirement plan, excessive fee claims, investment monitoring duty
    - Suggested signals: LIT.ERISA.stock_drop, LIT.ERISA.excessive_fees, LIT.ERISA.monitoring_duty

### 3.3 Nice-to-Have Gaps

11. **Product Liability as D&O Trigger** - Recall history, FDA/CPSC action linkage, product reserve adequacy
12. **Environmental Liability** - Superfund exposure, environmental reserve adequacy, permit compliance
13. **Government Contract Risk** - False Claims Act exposure, debarment risk, contract concentration
14. **International / Cross-Border** - Foreign litigation exposure, group action risk in EU/UK/Australia, Bribery Act compliance

---

## Part 4: Overlap Analysis

### 4.1 Redundant Signals (Same dimension measured multiple ways without clear differentiation)

#### HIGH OVERLAP: Board Governance Signals
The following signals measure substantially overlapping concepts across `exec/profile.yaml` and `gov/board.yaml`:

| Signal A | Signal B | Issue |
|----------|----------|-------|
| EXEC.PROFILE.board_size | GOV.BOARD.size | IDENTICAL dimension. Both measure board size from DEF 14A. |
| EXEC.PROFILE.avg_tenure | GOV.BOARD.tenure | IDENTICAL dimension. Both measure board tenure from DEF 14A. |
| EXEC.PROFILE.ceo_chair_duality | GOV.BOARD.ceo_chair | IDENTICAL dimension. Both measure CEO/Chair separation. |
| EXEC.PROFILE.independent_ratio | GOV.BOARD.independence | IDENTICAL dimension. Both measure board independence %. |
| EXEC.PROFILE.overboarded_directors | GOV.BOARD.overboarding | IDENTICAL dimension. Both measure overboarded directors. |

**Recommendation**: Consolidate into `gov/board.yaml` only. Remove duplicates from `exec/profile.yaml`. The exec domain should focus on individual executive risk, not board composition.

#### MEDIUM OVERLAP: Insider Trading Signals
Three separate domains contain insider trading signals:

| Domain | Signals | Focus |
|--------|---------|-------|
| exec/activity.yaml | EXEC.INSIDER.ceo_net_selling, EXEC.INSIDER.cfo_net_selling, EXEC.INSIDER.cluster_selling, EXEC.INSIDER.non_10b51 | CEO/CFO-specific selling patterns |
| gov/insider.yaml | GOV.INSIDER.form4_filings, GOV.INSIDER.executive_sales, GOV.INSIDER.cluster_sales, GOV.INSIDER.net_selling, GOV.INSIDER.ownership_pct, GOV.INSIDER.10b5_plans, GOV.INSIDER.plan_adoption, GOV.INSIDER.unusual_timing | All insider trading from governance perspective |
| stock/insider.yaml | STOCK.INSIDER.summary, STOCK.INSIDER.notable_activity, STOCK.INSIDER.cluster_timing | Insider trading from stock analysis perspective |

**Issue**: EXEC.INSIDER.cluster_selling and GOV.INSIDER.cluster_sales measure the same thing. EXEC.INSIDER.non_10b51 and GOV.INSIDER.10b5_plans cover same ground. STOCK.INSIDER.cluster_timing is a third duplicate.

**Recommendation**: Consolidate all insider trading signals into a single domain (stock/insider.yaml or gov/insider.yaml). Eliminate cross-domain duplication.

#### MEDIUM OVERLAP: Material Weakness
- FIN.ACCT.internal_controls - "Internal Controls" (material weaknesses + significant deficiencies)
- FIN.ACCT.material_weakness - "Material Weakness in Internal Controls"
- GOV.EFFECT.material_weakness - "Material Weakness" (governance effectiveness dimension)

Three signals for one fact (material weakness disclosed: yes/no).

**Recommendation**: Single source signal for the fact, then referenced by scoring chains.

#### MEDIUM OVERLAP: Restatement Signals
Five restatement signals in `fin/accounting.yaml`:
- FIN.ACCT.restatement (history)
- FIN.ACCT.restatement_magnitude (revenue impact)
- FIN.ACCT.restatement_pattern (repeat)
- FIN.ACCT.restatement_auditor_link (auditor change correlation)
- FIN.ACCT.restatement_stock_window (stock drop timing)

**Assessment**: These are different dimensions of a single event. The structure is defensible (each adds unique information) but they should be modeled as a composite signal with sub-dimensions rather than 5 independent signals. The current approach creates 5 separate evaluation passes for what is fundamentally one data acquisition.

#### MEDIUM OVERLAP: Disclosure/Narrative Signals
- FWRD.DISC.* (9 signals) - Disclosure quality dimensions
- FWRD.NARRATIVE.* (6 signals) - Narrative coherence dimensions
- NLP.* (15 signals) - NLP-based disclosure analysis

**Issue**: Significant conceptual overlap. FWRD.DISC.mda_depth and NLP.MDA.readability_change both analyze MD&A. FWRD.NARRATIVE.analyst_skepticism and NLP.MDA.tone_shift both capture narrative sentiment. FWRD.DISC.disclosure_quality_composite should be computed from NLP signals, not independently acquired.

**Recommendation**: NLP signals should be the computation layer; FWRD.DISC/NARRATIVE should be the business interpretation layer. Currently they're parallel and unlinked.

#### LOW OVERLAP: Working Capital / Liquidity
- FIN.LIQ.position, FIN.LIQ.working_capital, FIN.LIQ.efficiency, FIN.LIQ.trend, FIN.LIQ.cash_burn (5 liquidity signals)
- FIN.TEMPORAL.working_capital_deterioration (temporal)
- FWRD.WARN.working_capital_trends (forward warning)
- FWRD.WARN.zone_of_insolvency (distress)

**Assessment**: Defensible — each is a different analytical lens on liquidity. But the data acquisition is nearly identical for all. Should be one data acquisition with multiple evaluations.

### 4.2 Stale / Questionable Signals

#### "Intentionally Unmapped" Signals (18 signals with `gap_bucket: intentionally-unmapped`)
These signals were identified during prior gap analysis as requiring proprietary data sources:

| Signal | Issue |
|--------|-------|
| EXEC.CEO.risk_score | Requires Kroll-style proprietary service |
| EXEC.CFO.risk_score | Requires Kroll-style proprietary service |
| EXEC.PROFILE.board_size | Duplicate of GOV.BOARD.size |
| EXEC.PROFILE.avg_tenure | Duplicate of GOV.BOARD.tenure |
| EXEC.PROFILE.independent_ratio | Duplicate of GOV.BOARD.independence |
| EXEC.PROFILE.overboarded_directors | Duplicate of GOV.BOARD.overboarding |
| GOV.BOARD.* (multiple) | Various with gap_bucket but are extractable from DEF 14A |
| GOV.EFFECT.iss_score | Requires ISS/Glass Lewis API |
| GOV.EFFECT.proxy_advisory | Requires ISS/Glass Lewis API |
| GOV.EFFECT.auditor_change | Marked INACTIVE |
| GOV.EFFECT.sig_deficiency | Marked INACTIVE |
| GOV.EFFECT.late_filing | Marked INACTIVE |
| GOV.EFFECT.nt_filing | Marked INACTIVE |
| GOV.BOARD.expertise | Marked INACTIVE |
| GOV.BOARD.succession | Marked INACTIVE |

**Recommendation**:
- REMOVE proprietary-data signals that will never be populated (ISS score, Kroll scores) — 4 signals
- ACTIVATE or REMOVE INACTIVE signals — 6 signals sitting in limbo
- MERGE duplicates — 5 signals

#### Sentiment/Review Signals (11 signals with deprecation_note)
FWRD.WARN.glassdoor_sentiment, .indeed_reviews, .blind_posts, .linkedin_headcount, .linkedin_departures, .g2_reviews, .trustpilot_trend, .app_ratings, .social_sentiment, .journalism_activity, .cfpb_complaints, .fda_medwatch, .nhtsa_complaints

**Assessment**: These were designed for a more aggressive data acquisition strategy (scraping review sites, monitoring social media). Most have `gap_bucket: intentionally-unmapped`. They represent an aspirational signal set rather than an implementable one.

**Recommendation**: Either (a) downgrade to INACTIVE and exclude from signal count, or (b) reformulate as disclosure-check equivalents (e.g., "Does management discuss employee retention risks in risk factors?") which ARE answerable from filings.

#### Sector-Specific Signals (2 signals)
- FIN.SECTOR.energy
- FIN.SECTOR.retail

**Assessment**: These extract sector-specific financial metrics but are only 2 of the 11 GICS sectors. Either commit to all sectors or remove these.

**Recommendation**: Remove. Sector-specific analysis should be driven by the risk classification (BIZ.CLASS.primary) applying different thresholds, not by separate signals.

### 4.3 Naming / ID Inconsistencies

| Issue | Examples |
|-------|---------|
| ID doesn't match name | BIZ.DEPEND.tech_dep named "Government Contract Percentage"; BIZ.DEPEND.key_person named "Customer Concentration Risk Composite"; BIZ.SIZE.growth_trajectory named "Public Company Tenure" |
| Duplicate field_key mapping | BIZ.DEPEND.customer_conc and BIZ.DEPEND.key_person both map to `customer_concentration` |
| BIZ.DEPEND.supplier_conc maps to `supplier_concentration` but is named "Top 5 Customers Concentration" |
| Multiple signals sharing same field_key | At least 10 instances of multiple signals pointing to same data field |

---

## Part 5: Frequency x Severity Framework

### 5.1 Current State

The brain currently uses a 10-factor scoring model (F1-F10) where:
- F1-F9 map to different risk dimensions
- F10 is a catch-all "other" factor
- Each signal has a `claims_correlation` field (0.0-1.0) indicating correlation with claims
- Thresholds are red/yellow/clear tiered

**Problem**: There is no explicit frequency x severity model. The system evaluates "is this risk present?" but not "how likely is this risk to materialize?" or "if it does, how severe will it be?"

### 5.2 Proposed Frequency x Severity Model

#### Layer 1: Base Rate (Industry Filing Frequency)
Every company has a base rate probability of a D&O claim based on:

| Factor | Data Source | Method |
|--------|-----------|--------|
| **Industry SCA filing rate** | SCAC database | Historical filings/public companies by SIC sector |
| **Market cap tier rate** | Cornerstone Research | Filings per tier (Mega/Large/Mid/Small/Micro) |
| **Years public** | SEC filings | Companies <5 years public have 2-3x filing rate |
| **Geography** | State of incorporation | Delaware companies face more derivative suits |

**Formula**: `base_rate = sector_rate * mcap_modifier * tenure_modifier * jurisdiction_modifier`

Approximate sector filing rates (annual probability of SCA):
- Technology: 4.5%
- Pharmaceuticals/Biotech: 5.0%
- Financial Services: 3.5%
- Healthcare: 3.0%
- Energy: 2.5%
- Consumer: 2.0%
- Industrials: 1.5%
- Utilities: 0.8%
- Real Estate: 1.0%
- Overall Average: 2.5%

#### Layer 2: Company-Specific Modifiers (Signal-Driven)
Each triggered signal adds a multiplier to the base rate:

| Modifier Category | Signal Examples | Multiplier Range |
|-------------------|----------------|------------------|
| **Active SCA** | LIT.SCA.active | 10.0x (litigation already exists) |
| **SEC Investigation** | LIT.REG.sec_investigation | 3.0-5.0x |
| **Restatement** | FIN.ACCT.restatement | 4.0-8.0x |
| **Material Weakness** | FIN.ACCT.material_weakness | 2.0-3.0x |
| **Stock Drop >20%** | STOCK.PRICE.recent_drop_alert (red) | 2.0-4.0x |
| **Insider Selling Cluster** | EXEC.INSIDER.cluster_selling | 1.5-2.5x |
| **CFO Departure** | EXEC.DEPARTURE.cfo_departure_timing | 1.5-3.0x |
| **Guidance Miss** | FIN.GUIDE.track_record (red) | 1.5-2.0x |
| **Short Seller Report** | STOCK.SHORT.report | 2.0-4.0x |
| **Going Concern** | FIN.ACCT.auditor (red) | 3.0-5.0x |
| **Forensic Flags** | FIN.FORENSIC.beneish_dechow_convergence | 2.0-3.0x |
| **Governance Weakness** | GOV.BOARD.independence (red) | 1.2-1.5x |

**Formula**: `adjusted_rate = base_rate * product(applicable_modifiers)`

#### Layer 3: Severity Estimation (Settlement Range)
Once frequency is estimated, severity depends on:

| Factor | Impact on Severity | Source |
|--------|-------------------|--------|
| **Market cap at class period start** | Primary driver (R² ~0.6 with settlement) | Stock data |
| **Market cap decline during class period** | "Damages" proxy | Stock data |
| **Allegation type** | Accounting fraud > Operational miss | SCA data |
| **Institutional ownership %** | Higher institutional = more aggressive prosecution | Ownership data |
| **Lead counsel tier** | Top-10 plaintiff firm = higher settlements | SCAC data |
| **Prior settlement history** | Repeat defendants settle higher | SCA history |
| **SEC parallel investigation** | Doubles severity | Regulatory data |

**Settlement estimation model** (simplified):
```
expected_settlement =
  max_damages * settlement_rate * allegation_multiplier * counsel_multiplier * regulatory_multiplier

where:
  max_damages = market_cap_decline_in_class_period
  settlement_rate = 2-5% of max damages (empirical median ~2.5%)
  allegation_multiplier = {accounting: 1.5, operational: 1.0, regulatory: 1.3}
  counsel_multiplier = {tier1: 1.3, tier2: 1.1, other: 1.0}
  regulatory_multiplier = {sec_parallel: 2.0, none: 1.0}
```

**Defense costs**: Add 15-30% of indemnity depending on claim type:
```
defense_costs = expected_settlement * defense_cost_factor
total_exposure = expected_settlement + defense_costs
```

#### Layer 4: Composite Risk Score
Combine frequency and severity into a single risk metric:

```
expected_loss = adjusted_filing_rate * expected_severity
risk_score = f(expected_loss, market_cap)  # normalized 0-100
```

### 5.3 How This Maps to Current Brain Architecture

The current 10-factor model (F1-F10) can be reframed as:

| Factor | Risk Dimension | Frequency Impact | Severity Impact |
|--------|---------------|-----------------|-----------------|
| F1 | Litigation History | HIGH (repeat filers) | HIGH (establishes pattern) |
| F2 | Stock Performance | HIGH (stock drop = trigger) | HIGH (damages proxy) |
| F3 | Financial Integrity | HIGH (fraud = top trigger) | HIGH (fraud cases settle highest) |
| F4 | (unused/legacy) | - | - |
| F5 | Binary Events | MEDIUM (catalysts) | MEDIUM |
| F6 | Guidance/Earnings | HIGH (miss = trigger) | MEDIUM |
| F7 | Director Character | LOW (indirect) | LOW (reputational) |
| F8 | Cash Flow / M&A | MEDIUM | MEDIUM |
| F9 | Industry/External | MEDIUM (sector rate) | LOW (sector adjustment) |
| F10 | Governance / Other | MEDIUM | LOW |

**Key insight**: Factors F1, F2, F3, and F6 drive 80%+ of SCA claim frequency and severity. The remaining factors are important for derivative/regulatory claims but are secondary for the dominant risk type.

---

## Part 6: Recommendations

### 6.1 Structural Changes

1. **Reorganize around risk types, not data sources**
   - Current organization (biz, fin, gov, lit, etc.) mixes hazards, exposures, and claim types
   - Proposed: Organize signals by the risk taxonomy (SCA, derivative, regulatory, EPL, M&A, cyber, etc.)
   - Each risk type gets its own frequency model, severity model, and leading indicators

2. **Separate "facts" from "evaluations"**
   - A fact: "Board has 9 members, 6 independent" (EXTRACT)
   - An evaluation: "Board independence is inadequate" (EVALUATE)
   - Currently mixed within the same signal set
   - Proposed: Facts are first-class data items; evaluations are scoring rules that consume facts

3. **Introduce composite risk models per claim type**
   - SCA risk model: frequency(base_rate, modifiers) x severity(market_cap, damages, allegation_type)
   - Derivative risk model: governance_weakness x oversight_failure x trigger_event
   - Regulatory risk model: enforcement_activity x compliance_program x sector_rate
   - Each model consumes relevant signals as inputs

### 6.2 Signal Additions (Priority Order)

| Priority | Risk Type | Signals to Add | Est. Count |
|----------|-----------|---------------|------------|
| P0 | FCPA/Anti-Bribery | jurisdiction_risk, agent_intermediary, compliance_program, prior_actions | 4 |
| P0 | Caremark/Oversight | safety_program, compliance_program, cyber_oversight, risk_committee | 4 |
| P0 | ESG/Climate | climate_claims, scope_reporting, regulatory_compliance, greenwashing_risk | 4 |
| P1 | Derivative Exposure | demand_futility, caremark_flags, compensation_waste, self_dealing | 4 |
| P1 | EPL | discrimination_history, wage_hour_risk, rif_litigation, eeoc_complaints | 4 |
| P1 | Cyber (deepened) | breach_history, pii_volume, sec_compliance, insurance_program | 4 |
| P2 | Tax | effective_rate, uncertain_positions, transfer_pricing, haven_exposure | 4 |
| P2 | M&A (deepened) | premium_analysis, objection_risk, fairness_opinion, financing_risk | 4 |
| P2 | Antitrust (deepened) | market_dominance, acquisition_risk, collusion_indicators | 3 |
| P2 | ERISA | stock_drop, excessive_fees, monitoring_duty | 3 |

**Total new signals**: ~38

### 6.3 Signal Removals / Consolidation

| Action | Signals | Est. Count |
|--------|---------|------------|
| REMOVE duplicate board signals from exec/profile | EXEC.PROFILE.board_size, avg_tenure, ceo_chair_duality, independent_ratio, overboarded_directors | 5 |
| REMOVE proprietary-data signals | EXEC.CEO.risk_score, EXEC.CFO.risk_score, GOV.EFFECT.iss_score, GOV.EFFECT.proxy_advisory | 4 |
| DOWNGRADE aspirational sentiment signals to INACTIVE | 11 FWRD.WARN sentiment/review signals with deprecation_notes | 11 |
| REMOVE sector-specific stubs | FIN.SECTOR.energy, FIN.SECTOR.retail | 2 |
| CONSOLIDATE insider trading across domains | Merge ~6 duplicates across exec/gov/stock insider signals | -6 |
| CONSOLIDATE material weakness signals | Merge 3 into 1 fact + scoring reference | -2 |

**Net signal change**: +38 new - 30 removed/consolidated = ~408 signals (net +8)

### 6.4 Frequency x Severity Implementation

1. **Add `frequency_model` field to signal schema**: Each claim-type signal should reference a frequency model that incorporates base rate + modifiers.
2. **Add `severity_model` field to signal schema**: Each claim-type signal should reference a severity estimation model.
3. **Create `brain/models/` directory** for frequency/severity model definitions (YAML):
   - `sca_frequency.yaml` - SCA filing probability model
   - `sca_severity.yaml` - SCA settlement estimation model
   - `derivative_frequency.yaml` - Derivative claim probability model
   - `regulatory_frequency.yaml` - Regulatory action probability model
   - `composite_exposure.yaml` - Total D&O exposure model
4. **Calibrate with empirical data**: Use SCAC database, Cornerstone Research annual reports, and Allianz D&O insights for base rates and modifier calibration.

### 6.5 Data Source Priorities for New Signals

| New Signal Area | Primary Data Source | Secondary | Available? |
|----------------|--------------------|-----------|----|
| FCPA risk | Revenue geographic mix (10-K) + CPI index | News search | YES |
| Caremark oversight | Board committee charters (DEF 14A) + risk disclosures (10-K) | 8-K incident reports | YES |
| ESG disclosure | 10-K Item 1A, sustainability reports | California SOS filings | PARTIAL |
| EPL risk | Employee count + 10-K risk factors + news search | EEOC data (limited) | PARTIAL |
| Tax controversy | 10-K tax footnote (effective rate, UTPs) | News search | YES |
| Cyber (deepened) | 10-K Item 1C + 8-K breach notifications | News search | YES |
| M&A risk | 8-K Item 1.01 + DEFM14A + stock premiums | Deal databases | PARTIAL |
| Antitrust | Market share disclosures + HSR filings | News search | PARTIAL |

---

## Appendix A: Signal Count by Domain and Layer

| Domain | hazard | signal | Total |
|--------|--------|--------|-------|
| biz/ | 33 | 10 | 43 |
| exec/ | 4 | 16 | 20 |
| fin/ | 2 | 56 | 58 |
| fwrd/ | 32 | 47 | 79 |
| gov/ | 42 | 43 | 85 |
| lit/ | 0 | 65 | 65 |
| nlp/ | 0 | 15 | 15 |
| stock/ | 0 | 35 | 35 |
| **Total** | **113** | **287** | **400** |

## Appendix B: Signal Work Type Distribution

| Work Type | Count | Description |
|-----------|-------|-------------|
| extract | ~120 | Data extraction (display only) |
| evaluate | ~250 | Threshold-based evaluation (red/yellow/clear) |
| infer | ~30 | Pattern inference (multi-signal combination) |

## Appendix C: Key Research Sources

- [WTW D&O Liability Look Ahead 2025](https://www.wtwco.com/en-us/insights/2025/01/directors-and-officers-d-and-o-liability-a-look-ahead-to-2025)
- [Cornerstone Research SCA Filings](https://www.cornerstone.com/insights/reports/securities-class-action-filings/)
- [Allianz D&O Insurance Insights 2026](https://commercial.allianz.com/news-and-insights/news/directors-and-officers-insurance-insights-2026.html)
- [Stanford SCAC](https://securities.stanford.edu/)
- [Hogan Lovells Key D&O Risk Trends 2025](https://www.hoganlovells.com/en/publications/key-risk-trends-for-directors-and-officers-in-2025-and-beyond)
- [Woodruff Sawyer Common D&O Lawsuits](https://woodruffsawyer.com/insights/common-do-lawsuits-insurance-response)
- [Washington Service D&O Underwriting Research](https://washingtonservice.com/products/d-o-underwriting-research/)
- [The D&O Diary - What Do Insurers Look For](https://www.dandodiary.com/2008/05/articles/d-o-insurance/what-do-do-insurers-look-for/)
- [Aon Management Liability Insurance Market 2025](https://www.aon.com/en/insights/articles/financial-services-group/management-liability-insurance-market-in-2025-stability-amid-evolving-risks)

---

*Document generated 2026-02-28. This audit covers the complete D&O risk taxonomy and maps all 400 brain signals against it.*
