# Non-Securities-Class-Action D&O Liability Claims Research

**Date:** 2026-02-11
**Purpose:** Identify D&O claim types beyond 10b-5 securities class actions that the current system undermodels, with specific triggers, leading indicators, and detection signals from public data.
**Audience:** Experienced D&O underwriter evaluating system coverage gaps.

---

## Executive Summary

The current knowledge audit (24-KNOWLEDGE-AUDIT.md) maps 8 liability pathways but allocates ~120 of 359 checks to securities class actions, while derivative suits get ~8 checks, regulatory proceedings ~15, and bankruptcy/insolvency D&O claims ~10. This reflects a common industry bias: SCAs are the most visible claim type, but they are not the most frequent. Allianz Commercial's 2026 D&O Insurance Insights report notes that non-accounting and event-driven claims now dominate the D&O landscape, with the frequency of non-accounting securities class actions having more than doubled over the past decade. Derivative settlement values have exploded (Boeing $237.5M, Walmart Opioids $123M), and global business insolvencies are projected to be 24% above pre-pandemic averages by 2026.

This research maps six non-SCA claim categories, identifies specific triggers and leading indicators for each, and recommends checks the system should implement to detect exposure.

---

## 1. Derivative Suits -- Types, Triggers, Trends, Leading Indicators

### 1.1 Caremark Claims (Failure of Board Oversight)

**What They Are:** Shareholder derivative claims alleging the board breached its fiduciary duty of oversight by either (a) utterly failing to implement any reporting or information system, or (b) having implemented such a system, consciously failing to monitor or oversee its operations. Named after *In re Caremark International Inc. Derivative Litigation* (1996, Del. Ch.).

**Current State of the Law:**
- Historically described as "possibly the most difficult theory in corporation law upon which a plaintiff might hope to win judgment," but success rates have increased materially. Approximately 30% of recent Caremark claims survive motions to dismiss, compared to near-zero historically.
- Delaware courts have noted Caremark claims have "bloomed like dandelions after a warm spring rain."
- The standard now applies to corporate officers, not just directors (*Segway Inc. v. Hong Cai*, 2023).

**Specific Triggers That Lead to Caremark Claims:**

| Trigger Category | Specific Trigger | Example Case | Outcome |
|-----------------|-----------------|--------------|---------|
| Regulatory non-compliance causing harm | Opioid distribution law violations | AmerisourceBergen (2023) -- Del. S.Ct. reversed dismissal | Survived: 70+ documented subpoenas/settlements/regulatory warnings put directors on notice |
| Regulatory non-compliance causing harm | Opioid-related oversight failure at retailer | Walmart Opioid Derivative (2024) | Settled: $123M -- largest cash recovery in derivative case involving special litigation committee |
| Safety failure causing death/injury | Aircraft safety oversight failure (737 MAX) | Boeing Air Crash Derivative (2021) | Settled: $237.5M -- largest Caremark settlement in Delaware history, paid entirely by D&O insurance |
| Discriminatory practices | Discriminatory lending and hiring practices | Wells Fargo (2024) | Survived in part: Court held fair lending compliance is "mission critical" for banks |
| Illegal business practices | Overdraft checking practices | Regions Financial (2025) | Survived: Plaintiff seeking return of $191M company paid under CFPB consent settlement |
| Financial compliance failure | Medicaid pharmaceutical benefits cost manipulation | Centene/Bricklayers (2024) | Dismissed: Board had compliance committee receiving quarterly updates; management informed board of corrective measures |
| Billing fraud | Insulin pen overfilling scheme | Walgreens (2024) | Dismissed: Board remedied problem "within months of learning" -- "quibbles with timing fail" |

**Key Principle -- "Mission Critical" Activities:**
Courts increasingly distinguish between "mission critical" compliance risks and ordinary business activities. For a bank, fair lending compliance is mission critical. For an airline, aircraft safety is mission critical. For a pharmaceutical distributor, DEA compliance is mission critical. The "mission critical" determination dramatically affects whether a Caremark claim survives.

**Leading Indicators Detectable from Public Data:**
- Government investigations or enforcement proceedings disclosed in 10-K Item 3 or Item 1A
- Regulatory consent orders or settlement history (multi-year pattern of regulatory problems)
- Lack of board-level compliance committee dedicated to the company's "mission critical" risk
- Whistleblower disclosures in SEC filings
- Repeated regulatory warnings in the same compliance area
- Industry-wide enforcement trend (opioids, lending discrimination, overdraft fees) where the company is a participant

### 1.2 Books and Records Demands (Section 220)

**What They Are:** Shareholder demands under DGCL Section 220 to inspect corporate books and records. These are typically precursors to derivative suits -- shareholders use the inspection to gather evidence before filing.

**Recent Amendment (March 25, 2025):** Delaware significantly narrowed the scope of Section 220. The amended statute defines "books and records" more narrowly, imposes a three-year time limitation on certain categories, and requires stockholders to show "compelling need" for documents beyond the statutory categories. This amendment took effect immediately and applies retroactively.

**What This Means for D&O Risk:**
- A Section 220 demand is itself a leading indicator of a derivative suit
- The narrowed scope may reduce derivative suit filings by limiting pre-suit discovery
- Companies considering reincorporation to Nevada or Texas (a 2025 trend noted by Woodruff Sawyer) may face different inspection right regimes

**Leading Indicators:**
- ISS/Glass Lewis "Against" recommendations on directors (signals activist shareholder interest)
- Low say-on-pay votes (<70% approval)
- Shareholder proposal filings (especially governance-related)
- Public activist shareholder campaigns

### 1.3 Corporate Waste Claims

**What They Are:** Allegations that directors approved transactions so one-sided that no reasonable business person would approve them. The standard is extremely high -- plaintiff must show the consideration was "so inadequate that no person of ordinary, sound business judgment would deem it worth that which the corporation has paid."

**Common Triggers:**
- Excessive executive compensation packages (especially golden parachutes triggered by change-of-control)
- Above-market related party transactions benefiting officers or directors
- Acquisitions at significantly above-market prices where directors had conflicts
- Large charitable donations from corporate funds that benefit director personal interests

**Leading Indicators:**
- CEO compensation in top decile of peer group without corresponding performance
- Related party transactions disclosed in proxy (especially real estate, consulting, procurement with family members)
- "Spring-loaded" stock options (grants timed to precede positive announcements)
- Say-on-pay vote below 50%

### 1.4 Self-Dealing / Related Party Transactions

**What They Are:** Claims that officers or directors used their position for personal gain through transactions between the company and entities they control or in which they have a financial interest.

**Standard of Review:** When a director has a conflict of interest, the business judgment rule does not apply. Instead, the transaction is reviewed under the "entire fairness" standard, which requires both fair dealing (process) and fair price (economic terms). The burden shifts to the defendants to prove fairness.

**Triggers and Red Flags:**
- Related party transactions increasing in number or dollar volume
- New related parties appearing (family members, director-controlled entities)
- Related party receiving above-market terms (rents, consulting fees, supply prices)
- Corporate opportunity diverted to a director's personal entity
- Loans to officers/directors (rare post-SOX but still occurs through indirect structures)

**Leading Indicators from Public Data:**
- Proxy statement related party transaction disclosures (Item 404)
- 10-K footnote related party transaction disclosures
- Board member affiliations with company vendors or customers
- Changes in related party disclosure language year-over-year

### 1.5 Demand Futility Analysis -- When Does the Board Get Sued vs. Protected?

**Current Standard:** The Delaware Supreme Court adopted a universal three-part demand-futility test in *United Food v. Zuckerberg* (2021). For each director, the court asks:
1. Did the director receive a material personal benefit from the alleged misconduct?
2. Does the director face a substantial likelihood of liability?
3. Does the director lack independence from someone who received a material personal benefit or faces a substantial likelihood of liability?

If a majority of the board is compromised under any combination of these factors, demand is excused as futile and the derivative suit proceeds.

**Critical Protection: Exculpation Clauses (Section 102(b)(7))**
Most Delaware companies have charter provisions exculpating directors from monetary liability for duty of care violations. This means that to establish a "substantial likelihood of liability" the plaintiff must allege disloyalty (not just negligence), personal benefit, or lack of independence. The 2024 case law confirms that exculpation remains a powerful defense -- absent loyalty breach, directors are largely protected.

**When Boards Are NOT Protected:**
- Loyalty violations: Self-dealing, corporate opportunity theft, conscious disregard of duties
- Oversight failures where the board had actual knowledge of red flags (Caremark prong two)
- Controlled company transactions where the controlling shareholder benefits at minority expense
- Compensation committee self-dealing (approving own excessive pay)

### 1.6 Recent Derivative Suit Trends (2024-2025)

**Settlement Values Are Increasing Dramatically:**
- Boeing 737 MAX: $237.5M (largest Caremark settlement ever)
- Walmart Opioid: $123M (15th largest derivative settlement ever, approved December 2024)
- Wells Fargo pending (fair lending Caremark claim survived dismissal)
- Regions Financial pending ($191M CFPB consent as the underlying loss)

**Derivative Suits Follow SCAs:** Virtually every securities class action filing triggers a companion derivative suit. The derivative suit often settles for less than the SCA but can result in corporate governance reforms that affect the company for years.

**Plaintiff Firms Are Specializing:** Firms like Bernstein Litowitz and Berman Tabacco are building dedicated derivative litigation practices. The Section 220 demand is now a standard litigation tool -- file the demand, get documents, then file the derivative suit with particularized facts.

**D&O Insurance Interaction:**
- Derivative suits are typically covered under Side A (when company cannot indemnify) and Side B (when company does indemnify)
- Entity coverage (Side C) generally does not apply to derivative suits because the company is the nominal plaintiff
- The Boeing settlement was paid entirely by D&O insurance -- the personal assets of directors were never at risk
- Key underwriting question: Does the company have adequate D&O limits to absorb a derivative settlement in the $100M+ range?

---

## 2. Regulatory/Government D&O Claims -- Enforcement Trends, Individual Liability Patterns

### 2.1 DOJ Individual Accountability Focus

**Policy Framework:**
- **Yates Memo (2015, rescinded 2018):** Required companies to identify all individuals involved in misconduct to receive cooperation credit.
- **Monaco Memo (September 2022):** Reinstated and expanded individual accountability as DOJ's "first priority" in corporate crime. Key requirements: (a) companies must disclose evidence of misconduct quickly, (b) compensation systems must include clawback provisions for criminal misconduct, (c) expedited investigation timelines push resolution of individual cases.
- **2025 Shift:** The Trump administration maintained the individual accountability framework but refocused enforcement on certain priorities (cartels, transnational crime) while reducing resources in areas like FCPA.

**D&O Impact:** DOJ investigations trigger D&O claims in multiple ways:
- Defense costs for individual officers/directors under investigation (Side A coverage)
- Indemnification costs when the company advances defense costs (Side B coverage)
- Follow-on securities class actions after DOJ actions are disclosed
- Follow-on derivative suits alleging board oversight failure

**Leading Indicators:**
- DOJ subpoena disclosure in 10-K/10-Q
- Grand jury subpoena disclosure
- "Cooperating with government investigation" language in filings
- Industry-wide DOJ enforcement sweeps (e.g., healthcare fraud, antitrust price-fixing)
- Whistleblower disclosures referencing potential criminal conduct

### 2.2 State Attorney General Actions

**2024-2025 Trend: State AGs Filling Federal Enforcement Voids**

As federal agencies retreat from or realign enforcement priorities, state attorneys general are increasingly taking the lead. Key areas:

| State AG Focus Area | Individual Liability Risk | Example |
|-------------------|--------------------------|---------|
| Consumer data privacy | Moderate -- CCPA/state laws target "covered persons" and "related persons" | California AG settled with Blackbaud for $6.75M (June 2024); Healthline Media $1.55M CCPA settlement (largest to date) |
| Consumer protection / deceptive practices | Moderate -- some state statutes allow individual officer liability | State AG multistate actions against tech companies for deceptive data practices |
| Environmental enforcement | High -- CERCLA operator liability can reach individual officers | State AG actions against individual operators of polluting facilities |
| Opioid distribution | High -- multiple states have pursued individual pharmacy executives | State AG opioid settlements totaling billions with individual liability components |
| AI-related consumer protection | Emerging -- using existing deceptive practices laws | State AGs pursuing AI-related enforcement under consumer protection statutes |

**Key Risk for D&O:** State AG actions often name the company, not individuals. But the D&O exposure comes from (a) defense costs for the entity and executives, (b) follow-on derivative suits for oversight failure, and (c) the monetary settlements reducing company resources available for indemnification.

### 2.3 CFPB/FTC Enforcement with Individual Liability

**FTC -- Increasing Individual Officer Targeting:**
- Adobe (June 2024): FTC asked DOJ to sue Adobe AND two named executives (SVP of digital go-to-market and president of digital media business) for hiding early termination fees
- Cerebral: FTC named then-CEO Kyle Robertson individually for violations of the Opioid Addiction Recovery Fraud Prevention Act
- Drizly: FTC imposed personal security requirements on the CEO that follow him to future employment

**CFPB Authority to Name Individuals:**
The CFPA authorizes CFPB to bring UDAAP enforcement actions against "covered persons" and "related persons," which includes officers, directors, employees with managerial responsibility, shareholders, consultants, and joint venture partners who "materially participate in the conduct of the affairs" of a covered person.

**2025 Shift:** The CFPB announced a 50% reduction in supervisory exams and a shift toward conciliation. This reduces near-term CFPB enforcement risk but may increase state AG enforcement as states fill the gap.

**Leading Indicators:**
- Company is in a CFPB/FTC-regulated industry (financial services, consumer products, technology)
- Prior consent orders or enforcement actions by CFPB/FTC
- Consumer complaint volume trending upward (CFPB complaint database is public)
- Industry-wide enforcement trend (e.g., overdraft fees, subscription cancellation practices)

### 2.4 FCPA -- When Does This Hit D&O?

**2024 Peak Then 2025 Decline:**
- 2024: 38 FCPA enforcement actions, $1.5B+ in corporate penalties, 24 individual prosecutions (20 DOJ, highest since reversal of prior decline)
- 2025: Dramatic reduction -- only 5 individuals charged. FCPA unit reduced from ~40 prosecutors to ~22. Trump administration paused FCPA enforcement for 180-day review (February 2025), then refocused on cartels and transnational organizations.

**When FCPA Hits D&O:**
- Individual officers who authorized or participated in corrupt payments face criminal prosecution
- Defense costs for FCPA investigations are among the most expensive D&O claims (multi-year, multi-jurisdictional investigations)
- Corporate penalties (even without individual charges) trigger derivative suits for oversight failure
- FCPA investigations are not limited to the specific conduct -- they often uncover other compliance failures

**Leading Indicators:**
- Operations in high-corruption-risk countries (Transparency International CPI score <40)
- Use of third-party sales agents or consultants in government procurement
- Acquisition of companies with foreign government customers without adequate due diligence
- Unusual payments or consultancy fees disclosed in financial statements
- Industry peers facing FCPA enforcement (pharmaceutical, oil & gas, telecom, defense, financial services)

### 2.5 Bank Regulatory Actions (OCC, FDIC)

**Individual Officer/Director Actions in 2024:**
The OCC regularly issues enforcement actions against individual bank officers and directors:
- Personal Cease and Desist Orders for regulatory violations (e.g., Nicholas Jurun, Barrington Bank -- making payments to receive mortgage loan referrals, hiding payments with false documentation)
- Orders of Prohibition permanently barring individuals from banking (e.g., Samantha Cherry, UMB Bank -- embezzlement; Stephen Adams, Sterling Bank -- failure to supervise, $50K civil money penalty)
- Civil Money Penalties against individuals (not just institutions)

**D&O Relevance:**
- Bank director removal proceedings and prohibition orders are among the most severe individual enforcement actions
- Defense costs for bank regulatory proceedings are covered under D&O policies
- Side A coverage becomes critical when the bank is unable or unwilling to indemnify (especially for prohibited or removed officers)
- Bank directors face heightened duty of care standards under federal banking law compared to state corporate law

**Leading Indicators:**
- MRA (Matter Requiring Attention) or MRIA (Matter Requiring Immediate Attention) from regulators
- Consent orders or formal enforcement actions against the institution
- BSA/AML compliance deficiencies
- Community Reinvestment Act (CRA) compliance issues
- Prior regulatory examination findings with unresolved issues

### 2.6 Environmental Liability (CERCLA Individual Liability)

**When Individual Officers/Directors Are Liable:**
Under CERCLA, individual officers and directors can be held personally liable as "operators" if they directed the workings of, managed, or conducted the affairs of the facility as they relate to operations having to do with the leakage or disposal of hazardous substances. The standard weighs:
1. The individual's degree of authority in general
2. Specific responsibility for health and safety practices, including hazardous waste disposal

This is NOT vicarious liability -- it requires active involvement in or authority over the operations that caused contamination.

**D&O Coverage Complications:**
- Many D&O policies have pollution exclusions that may limit coverage for environmental claims
- The "claims made" basis of D&O policies can create gaps because environmental consequences often manifest years after the conduct
- Side A coverage is critical for personal liability under CERCLA

**Leading Indicators:**
- Company operates in environmentally sensitive industry (chemicals, mining, manufacturing, energy)
- EPA enforcement history or Superfund site involvement
- PFAS exposure (emerging litigation wave -- "forever chemicals")
- Environmental liabilities disclosed in 10-K footnotes
- State environmental enforcement actions or consent decrees

---

## 3. Bankruptcy/Insolvency D&O Claims -- Duty Shifting, Claim Types, Side A Triggers

### 3.1 Current Bankruptcy Landscape

Business bankruptcy filings through June 2025 reached 23,043 -- a 4.5% year-over-year increase and higher than pandemic-era 2020 levels. Chapter 11 reorganization filings specifically jumped 11% compared to 2020, driven by elevated interest rates, inflation, credit constraints, and refinancing challenges. Allianz projects global business insolvencies will rise +6% in 2025 and +5% in 2026, reaching 24% above the pre-pandemic average.

### 3.2 Deepening Insolvency Theory

**What It Is:** The theory that directors and officers who expand corporate debt and prolong the life of a corporation beyond the point of insolvency may be liable because continued operations increase losses, deepen insolvency, reduce asset value, and injure creditors.

**Jurisdictional Status:**
- Delaware: Does NOT recognize deepening insolvency as an independent cause of action (*Trenwick America Litigation Trust v. Ernst & Young*, 2006), but the underlying conduct can support breach of fiduciary duty claims
- New Jersey: Recognizes deepening insolvency (*NJ Dep't of Environmental Protection v. Dimant*, 2005)
- Pennsylvania: Recognized then limited (*Official Committee of Unsecured Creditors v. R.F. Lafferty*, 3d Cir. 2001, then narrowed)
- New York: Does NOT recognize as independent tort
- Most jurisdictions: Treat deepening insolvency facts as evidence of breach of fiduciary duty rather than as a standalone claim

**Damages Available:**
- Legal and administrative costs caused by the bankruptcy itself
- Impaired ability to operate profitably
- Lost profit and value due to loss of stakeholder confidence
- Impairment of relationships with employees, customers, and suppliers
- Dissipation of corporate assets during the deepening period

**Leading Indicators:**
- Going concern opinion issued by auditor
- Company continues to take on debt while cash flows decline
- Management narrative remains optimistic while financial metrics deteriorate
- Insider transactions (bonuses, severance agreements) in the zone of insolvency
- New borrowing at significantly above-market rates

### 3.3 Zone of Insolvency Duty Shifting

**What Changes:** When a company enters the "zone of insolvency" (inability to pay debts as they come due or liabilities exceeding assets), the fiduciary duties of directors expand to include creditor interests, not just shareholder interests. Post-*Purdue Pharma* (SCOTUS 2024, restricting nonconsensual third-party releases), directors face heightened personal liability exposure because they can no longer rely on bankruptcy plan releases to shield them.

**Practical Impact:**
- Decisions that favor shareholders over creditors (e.g., dividends, share buybacks, executive bonuses) in the zone of insolvency can become breach of fiduciary duty claims
- Directors must consider creditor interests when making business decisions, creating a dual-duty challenge
- The Purdue Pharma decision means directors cannot count on bankruptcy proceedings to release them from personal liability

**Leading Indicators (from public data):**
- Altman Z-Score entering distress zone (<1.81)
- Going concern opinion or substantial doubt language
- Covenant breaches or waiver negotiations
- Cash runway <12 months based on current burn rate
- Credit rating downgrade to CCC or below
- Missed interest or principal payments
- Delisting warning from exchange
- Auditor change during financial distress

### 3.4 Fraudulent Transfer / Preferential Payment Claims Against Directors

**What They Are:** Bankruptcy trustees can "claw back" transfers made by the company before filing:
- **Preferential Transfers:** Payments to creditors within 90 days before filing (extended to one year for insiders, including officers and directors)
- **Fraudulent Transfers:** Transfers made with actual intent to defraud creditors, or transfers for less than reasonably equivalent value within two years before filing

**How This Hits Directors:**
- Insider bonus payments, severance agreements, or equity vesting within one year of filing are subject to clawback
- Director-approved transactions (acquisitions, dividends, share repurchases) in the zone of insolvency can be challenged
- The entity's fraudulent intent is imputed from the intent of individuals acting on its behalf (e.g., the board of directors)
- Post-confirmation trustees or liquidating trusts routinely pursue these claims against former D&Os

**Case Example:** In *Delaware Bankruptcy Court* (January 2024), the court imputed officers' fraudulent intent to the corporation in avoidance litigation, demonstrating that individual officer knowledge and intent matter for determining whether company transfers can be avoided.

### 3.5 Chapter 7 Trustee Suits Against Former D&Os

In Chapter 7 liquidations, the trustee steps into the shoes of the creditors and can bring any claim the company or its creditors could bring against former directors and officers, including:
- Breach of fiduciary duty
- Waste of corporate assets
- Fraudulent transfers
- Deepening insolvency (in jurisdictions that recognize it)
- Negligence/mismanagement

These claims are often pursued years after the bankruptcy filing, making tail coverage and Side A DIC policies critical.

### 3.6 Side A Tower Importance -- When Is Personal Asset Exposure Real?

**Side A coverage** is the insuring agreement that provides first-dollar coverage for claims against directors and officers when the company cannot or will not indemnify them.

**When Side A Is the Only Protection:**
1. **Bankruptcy:** The company has no funds to indemnify. The bankruptcy estate may claim the D&O policy proceeds as estate assets, leaving directors without coverage UNLESS Side A-only policies are in place (which are NOT estate assets).
2. **Regulatory/criminal proceedings:** Many state corporate laws prohibit indemnification for criminal convictions or regulatory penalties.
3. **Derivative suits:** Company is the nominal plaintiff, so it cannot indemnify the defendants.
4. **Bad faith conduct:** Company charter provisions and bylaws may not permit indemnification for disloyal conduct.

**Recent Case -- *In re First Brands Group* (January 2026, Texas Bankruptcy Court):**
The court granted motions by former executives seeking relief from the automatic stay to access D&O insurance proceeds under Side A policies. The court distinguished between Side A-only policies (not estate assets, accessible) and traditional ABC policies (potentially estate assets, restricted). This case demonstrates why Side A DIC coverage is essential for director protection.

**Key Underwriting Consideration:** When evaluating a company with elevated financial distress signals, the critical question is whether the D&O program includes adequate Side A DIC limits separate from the primary ABC tower. If the primary tower is $10M and the Side A DIC is $5M, that may be insufficient if the company enters bankruptcy and creditors contest access to the primary limits.

---

## 4. Employment/Fiduciary D&O Claims -- ERISA, Whistleblower, Culture Claims

### 4.1 ERISA Fiduciary Breach (Stock Drop Cases -- Dudenhoeffer Standard)

**What They Are:** Lawsuits by participants in employer-sponsored retirement plans (401(k)s) alleging that plan fiduciaries breached their ERISA duties by continuing to offer company stock as an investment option when they knew or should have known the stock price was artificially inflated.

**Current Legal Standard:** *Fifth Third Bancorp v. Dudenhoeffer* (SCOTUS, 2014) abolished the "presumption of prudence" for employer stock investments. Plaintiffs must now plead a specific alternative action the fiduciaries should have taken (e.g., disclosing adverse information, freezing purchases) and that a prudent fiduciary in the same circumstances could not have concluded that the alternative action would do more harm than good (e.g., by causing a stock crash, insider trading liability, or SEC violation).

**Post-Dudenhoeffer Outcomes:**
- Courts have overwhelmingly dismissed ERISA stock drop claims since Dudenhoeffer
- The pleading standard is extremely demanding -- most cases cannot identify a disclosure alternative that wouldn't itself cause harm
- However, the theory survives and cases continue to be filed, particularly when combined with other fraud allegations
- The 2025 Cornell University SCOTUS decision may have implications for ERISA fiduciary liability going forward

**D&O vs. Fiduciary Liability Insurance:**
- ERISA stock drop claims are typically covered under fiduciary liability insurance, not D&O insurance
- However, if the ERISA claim is part of a broader fraud allegation (e.g., company executives knew about fraud and continued to offer company stock in the 401(k)), the D&O policy may be triggered for the underlying fraud claims
- Some D&O policies exclude ERISA claims; others provide sublimited coverage

**Leading Indicators:**
- Company offers own stock as an investment option in the 401(k) plan
- Company is subject to a concurrent SCA or SEC enforcement action (ERISA stock drop claims follow)
- Large percentage of retirement plan assets are in company stock
- Company has had a significant stock price decline (>30%)

### 4.2 Whistleblower Retaliation (Dodd-Frank, SOX)

**Dual Protection Framework:**

| Feature | SOX Whistleblower | Dodd-Frank Whistleblower |
|---------|-------------------|-------------------------|
| Scope | Employees of public companies reporting securities fraud | Anyone reporting securities violations to SEC |
| Reporting | To SEC, to supervisor, or internally | Must report to SEC in writing |
| Causation standard | "Contributing factor" (plaintiff-friendly) | "But for" (higher bar) |
| Damages | Back pay, reinstatement, compensatory damages | Double back pay with interest, reinstatement, attorneys' fees |
| Statute of limitations | 180 days to OSHA | 6-10 years |
| Jury trial | Yes | No (per Edwards v. First Trust, February 2025) |

**D&O Exposure:**
- Retaliation claims name individual officers who made the adverse employment decision
- Defense costs for retaliation claims are covered under most D&O policies (unless employment practices exclusion applies)
- Retaliation claims are often filed alongside or as precursors to broader fraud allegations
- The SEC whistleblower program has awarded over $2B since inception, creating strong financial incentives for reporting

**Leading Indicators:**
- Whistleblower disclosures referenced in SEC filings (Item 3, Item 1A)
- Internal investigation disclosures
- Sudden executive departures (potential constructive discharge)
- SEC whistleblower award announcements referencing the company's industry/geographic area

### 4.3 Workplace Culture / #MeToo-Era D&O Claims

**How Harassment/Culture Reaches D&O:**
The #MeToo movement extended harassment claims beyond employment practices liability (EPL) into D&O liability territory. The D&O pathway is typically through derivative suits alleging board oversight failure:
- *Caremark* claims: Board failed to implement adequate anti-harassment policies and reporting systems
- Corporate waste: Settlement payments for harassment claims waste corporate assets
- Officer liability: Individual officers named as harassers may trigger D&O coverage if the conduct relates to their corporate role

**Legislative Trends (2024-2025):**
- Multiple states now require employers to submit annual reports of harassment/discrimination judgments (Louisiana, Maryland, Illinois)
- NDAs restricting disclosure of harassment are increasingly restricted or banned (Utah, Colorado, Rhode Island, federal Speak Out Act)
- Expanded anti-harassment training requirements (Illinois, Delaware, California, Maine)
- Retaliation remains the most frequently cited EEOC issue (~50% of all filings in 2024)

**Leading Indicators:**
- CEO or senior executive departure for "personal reasons" (potential unreported harassment issue)
- Settlement of harassment claims disclosed in 10-K
- Employee satisfaction surveys or Glassdoor reviews indicating culture problems
- Industry known for culture risk (entertainment, tech, finance, media)
- Company lacks dedicated compliance/ethics reporting hotline

### 4.4 Discrimination Class Actions Reaching Board Oversight Failure

Beyond individual harassment claims, systemic discrimination can create board-level D&O exposure:
- *Wells Fargo* (2024): Discriminatory lending and sham diversity hiring interviews led to Caremark claims; court held fair lending compliance is "mission critical" for a bank
- Employment discrimination class actions can allege board-level oversight failure when the company has a pattern of discriminatory practices
- DEI backlash (2025 trend): Companies that made specific diversity commitments now face claims from both sides -- failure to achieve commitments AND reverse discrimination claims

**Leading Indicators:**
- EEOC complaints or charges filed against the company
- State civil rights commission investigations
- Pattern of discrimination settlements
- Lack of diversity in board composition (potential derivative claim that board cannot oversee diversity because it lacks diversity itself)
- Specific, dated diversity commitments in public filings or ESG reports

### 4.5 Non-Compete / Trade Secret Theft Claims Against Departing Executives

**D&O Exposure:**
- Departing executives who take confidential information, customer lists, or trade secrets to competitors can trigger both company claims (trade secret theft) and D&O claims (breach of duty of loyalty)
- The company may sue its former officer under D&O coverage provisions that cover "wrongful acts" during their tenure
- Antitrust implications: The 2025 DOJ/FTC Antitrust Guidelines for Business Activities Affecting Workers explicitly address non-compete agreements and employee mobility restrictions, with potential criminal liability for no-hire and wage-fixing agreements

**Leading Indicators:**
- Senior executive departures to direct competitors
- Non-compete litigation history
- Company operates in industry with high executive mobility (tech, finance, pharma)
- Trade secret litigation disclosed in 10-K Item 3

---

## 5. Business Complexity as Risk Factor -- How It Correlates with D&O Claims

### 5.1 The Complexity-Claims Correlation

Allianz Commercial reports that the severity of D&O claims has increased as claims have become complex and exposures large, with defense costs having almost doubled for large D&O claims in the past six years. Complex claims can absorb one-quarter to one-third of the insured sum in defense costs alone.

### 5.2 Complex Corporate Structures (VIEs, SPEs, Off-Balance-Sheet)

**Variable Interest Entities (VIEs):**
VIEs allow companies to keep assets, liabilities, and risks off their balance sheets. The D&O risk arises when:
- Improper consolidation obscures true financial position (Enron paradigm)
- VIE relationships create undisclosed contingent liabilities
- Related party VIEs benefit insiders at the company's expense
- Regulatory changes require consolidation of previously off-balance-sheet entities, revealing hidden leverage

**Special Purpose Entities (SPEs):**
SPEs used for securitization, asset-backed lending, or risk isolation can create D&O exposure when:
- The company retains more risk than disclosed
- Transfer pricing between the company and SPE is not at arm's length
- SPE losses flow back to the company through guarantees or recourse provisions

**Detection Signals from Public Data:**
- Number of VIEs disclosed in 10-K footnotes (increasing count = increasing complexity)
- Magnitude of off-balance-sheet commitments (Schedule 13 disclosures)
- Related party VIE relationships
- Consolidation methodology descriptions that are unusually long or hedged
- Auditor CAM related to VIE consolidation or accounting

### 5.3 Multi-Jurisdictional Exposure

**Dual-Listed Companies:**
Companies listed on both US and foreign exchanges face D&O exposure in multiple jurisdictions simultaneously:
- US securities laws (10b-5, Section 11) apply to US-listed shares
- Foreign securities laws may impose additional requirements (e.g., UK FCA, EU Market Abuse Regulation)
- Potential for parallel proceedings in multiple countries
- Differing disclosure requirements can create inconsistencies that plaintiffs exploit

**Foreign Operations Risk:**
- FCPA exposure from operations in high-corruption countries
- Data privacy exposure from EU (GDPR), China, or other jurisdictions
- Sanctions compliance exposure from operations near sanctioned countries
- Transfer pricing disputes with multiple tax authorities

**Leading Indicators:**
- Number of countries with material operations (disclosed in 10-K Item 2 or segment disclosures)
- Revenue concentration in countries with weak rule of law
- Use of foreign subsidiaries with different reporting requirements
- Tax haven subsidiaries (potential tax authority challenge)

### 5.4 Revenue Recognition Complexity

**Why This Matters for D&O:**
Revenue recognition is the single most common area of accounting fraud. The more complex the revenue model, the more opportunity for manipulation and the more likely a restatement. The SEC brought 35 enforcement actions in 2023 involving revenue recognition.

**Complexity Factors:**
- Long-term contracts with variable consideration
- Multiple performance obligations (bundled products/services)
- Right of return provisions or variable pricing
- Channel partner arrangements with return rights
- Bill-and-hold arrangements
- Percentage-of-completion contracts (construction, defense)
- License vs. service revenue recognition decisions

**Leading Indicators from Public Data:**
- Revenue recognition policy description in 10-K Note 2 (complexity and length)
- Changes in revenue recognition methodology
- Deferred revenue trends (accumulating vs. being recognized)
- DSO (Days Sales Outstanding) increasing without business explanation
- Unbilled receivables growing as percentage of revenue
- SEC comment letters on revenue recognition topics
- Auditor CAM related to revenue recognition

### 5.5 Related Party Transaction Webs

Complex webs of related party transactions create D&O exposure through:
- Self-dealing allegations (entire fairness review)
- Disclosure failures (transactions not properly disclosed in proxy)
- Transfer pricing manipulation between related entities
- Conflicts of interest in board decision-making

**Detection Signals:**
- Number and dollar volume of related party transactions (from proxy and 10-K)
- Related party transaction types (real estate leases, consulting fees, product purchases)
- Board members with affiliations to transaction counterparties
- Year-over-year changes in related party disclosure (new entities, increasing amounts)
- Audit committee related party transaction review policies and procedures

### 5.6 Holding Company vs. Operating Company Exposure

**The Distinction Matters for D&O Coverage:**
- Holding company directors may have limited visibility into operating subsidiary risks
- But they can still face Caremark claims for failure to oversee subsidiary operations
- Multi-layered corporate structures can create gaps in D&O coverage (which entity's policy covers which directors?)
- Subsidiary directors may not be covered under the parent's D&O policy

**Leading Indicators:**
- Number of subsidiaries (10-K Exhibit 21)
- Subsidiaries in high-risk jurisdictions
- Subsidiaries with independent directors (not covered by parent policy)
- Complex intercompany transactions

---

## 6. Emerging Trends -- What Is Genuinely New vs. Hype

### 6.1 AI Governance Liability (GENUINE AND ACCELERATING)

**Status: Moving from theoretical to actionable in 2025-2026**

Key developments:
- Weak oversight of AI is now explicitly recognized as a D&O liability risk by major insurers (Allianz, WTW, Woodruff Sawyer)
- 53 AI-related securities class action lawsuits filed since March 2020, with 12 filed in the first half of 2025 alone, mostly alleging management overstated AI benefits or understated risks
- FTC's Rite Aid enforcement action (2023) demonstrated that companies cannot outsource accountability for AI governance -- failures in overseeing third-party AI systems are the company's liability
- Proxy advisors and institutional investors now explicitly ask boards to demonstrate AI oversight (who understands AI, how it is governed, how often it is discussed)

**The Caremark Angle:** Boards that deploy AI without adequate oversight frameworks may face Caremark derivative claims if the AI causes harm (discriminatory lending decisions, biased hiring, incorrect medical diagnoses, privacy violations). The "mission critical" analysis would apply: if AI is central to the company's operations, AI governance becomes a board oversight obligation.

**The Emerging Liability Paradox:** In 2025, the concern was liability from using AI incorrectly. In 2026, the larger question may be liability from NOT using AI -- boards that fail to adopt AI may face claims of wasting corporate resources or missing competitive opportunities.

**Leading Indicators:**
- Company discloses AI as material to operations but lacks AI governance committee or policy
- AI-related risk factors in 10-K that are generic/boilerplate (signals lack of real governance)
- Competitor or peer companies deploying AI that the company has not adopted
- Customer-facing AI applications without disclosed oversight mechanisms
- AI-related regulatory inquiries or enforcement (FTC, state AGs)

### 6.2 Crypto/Digital Asset Regulatory Exposure (SHIFTING, NOT ELIMINATED)

**Status: Enforcement pivot from prosecution to regulation**

The landscape shifted dramatically in 2025:
- SEC dropped nearly all non-fraud enforcement actions against crypto companies commenced under the Biden administration
- DOJ disbanded the National Cryptocurrency Enforcement Team (April 2025), refocusing on underlying crimes (terrorism, narcotics, sanctions evasion)
- Congress moved toward regulatory clarity with the Financial Innovation and Technology for the 21st Century Act (FIT21) and stablecoin legislation
- DeFi governance participants face potential personal liability if DAOs are classified as unincorporated partnerships

**Remaining D&O Risks:**
- Fraud-based claims remain fully enforceable (the enforcement shift only affects regulatory ambiguity cases)
- Companies that custody, transfer, or manage digital assets still face AML/KYC obligations
- State-level enforcement (New York DFS, others) continues regardless of federal shifts
- Protocol operators who manage user interfaces, custody assets, or handle transactions face heightened individual liability

**Leading Indicators:**
- Company holds material digital asset positions on balance sheet
- Company operates exchange, custody, or DeFi protocol
- Company accepts cryptocurrency as payment
- Prior SEC or state enforcement action related to digital assets
- Industry peer under investigation

### 6.3 Supply Chain ESG Liability (GENUINE, GROWING)

**Status: Regulatory requirements crystallizing in EU, enforcement expanding**

Key regulatory developments:
- EU CSDDD (Corporate Sustainability Due Diligence Directive): Requires companies to identify and address adverse human rights and environmental impacts in their supply chains, with personal director liability provisions
- EU Batteries Regulation and Critical Raw Materials Act: Specific supply chain due diligence for conflict minerals
- US Uyghur Forced Labor Prevention Act: Creates rebuttable presumption that goods from Xinjiang are produced with forced labor
- Section 18 of the Securities Exchange Act: Creates liability for materially false or misleading conflict mineral disclosures

**D&O Exposure Pathway:**
- Directors who approve inadequate supply chain due diligence face personal liability under EU CSDDD
- Misleading conflict mineral disclosures create securities fraud exposure
- Supply chain disruptions from forced labor enforcement can cause material financial losses, triggering SCAs
- Reputational damage from supply chain human rights violations can support Caremark claims

**Leading Indicators:**
- Company sources materials from high-risk supply chain countries (Xinjiang, DRC, Myanmar)
- Conflict mineral disclosure filed with SEC (Form SD)
- Supply chain human rights policies that are generic/boilerplate
- Industry peers facing supply chain ESG enforcement
- EU operations that trigger CSDDD compliance

### 6.4 Data Privacy Post-State-AG-Enforcement (GENUINE, ACCELERATING)

**Status: State enforcement exceeding federal**

The shift from federal to state privacy enforcement is creating fragmented but intensifying D&O exposure:
- 20 states now have comprehensive privacy laws (2024-2026 wave)
- State AGs are actively enforcing -- California, Connecticut, Texas, Oregon among the most active
- Enforcement targets not just data breaches but data *practices*: dark patterns, consent mechanisms, data minimization, children's privacy, data broker activities
- CCPA penalties: $2,663 per negligent violation, $7,988 per intentional violation or those involving minors -- these aggregate quickly across millions of consumers

**D&O Relevance:**
- Board oversight of data privacy is emerging as a Caremark obligation, particularly for data-intensive businesses
- Privacy enforcement actions trigger follow-on derivative suits
- Directors who serve on audit or risk committees may face individual exposure for inadequate privacy governance
- Cyber/privacy D&O claims are one of the fastest-growing claim categories

**Leading Indicators:**
- Company processes consumer data at scale (ad tech, social media, health tech, fintech)
- Operations in states with active privacy enforcement (California, Texas, Connecticut)
- Children/minor user base (highest penalty tier)
- Prior data breach or privacy enforcement action
- Inadequate Item 1C (cybersecurity governance) disclosure in 10-K

### 6.5 Antitrust/Market Dominance (GENUINE, BIPARTISAN)

**Status: DOJ/FTC antitrust enforcement remains vigorous despite administration changes**

The January 2025 DOJ/FTC Antitrust Guidelines for Business Activities Affecting Workers expand individual liability exposure:
- Criminal liability for executives involved in no-hire agreements, wage-fixing, and non-solicitation agreements
- Non-compete agreements explicitly flagged as potential antitrust violations
- Information sharing through algorithms or intermediaries can violate antitrust laws
- These guidelines apply to individual decision-makers, not just companies

**Broader Antitrust D&O Risks:**
- Monopoly maintenance allegations (DOJ v. Google, DOJ v. Apple)
- Price-fixing conspiracies with individual criminal exposure (DOJ has historically prosecuted individual executives)
- Merger challenges creating deal uncertainty and shareholder litigation
- Private antitrust class actions with treble damages

**Leading Indicators:**
- Market share exceeding 40% in any product/geographic market
- Industry under active antitrust investigation
- DOJ or FTC Second Request in connection with M&A
- Competitor antitrust complaints or lawsuits
- Employee no-hire or non-solicitation agreements with competitors

### 6.6 Climate Litigation Evolution (GENUINE BUT COMPLEX)

**Status: Approximately 20% of climate change cases filed in 2024 targeted companies or their D&Os**

The climate litigation landscape has evolved beyond greenwashing into several distinct claim types:
- **"Polluter pays" litigation:** Seeking to hold companies accountable for climate-related physical harm (increasingly by state and municipal governments)
- **Corporate framework cases:** Requiring changes in corporate governance to address climate risk
- **Transition risk litigation:** Alleging director/officer mismanagement of climate transition risk
- **Physical risk non-disclosure:** Alleging failure to disclose material physical climate risks to facilities, supply chains, or operations

**SEC Climate Disclosure Rule Status:**
The SEC's final climate risk disclosure rule (March 2024) was suspended during litigation and the SEC voted to end its defense of the rule in 2025. However, California's climate disclosure laws (SB 253, SB 261) remain in effect, creating state-level disclosure requirements.

**D&O Coverage Complications:**
Many D&O policies have pollution exclusions that could limit coverage for climate-related claims. The distinction between a "pollution claim" (excluded) and a "securities/disclosure claim arising from climate issues" (covered) is actively litigated.

**Leading Indicators:**
- Material climate-related risk factors in 10-K (particularly physical risk to operations)
- Specific dated emissions reduction targets without credible reduction plans
- Operations in climate-vulnerable regions (coastal, wildfire-prone, water-stressed)
- Industry with high emissions profile (energy, transportation, manufacturing, agriculture)
- Prior environmental enforcement actions

---

## 7. Gap Assessment -- What Signals Would Detect Each Claim Type from Public Data?

### Signal Detection Matrix

| Claim Type | Currently Detected? | Key Missing Signals | Data Source | Acquisition Difficulty |
|-----------|--------------------|--------------------|-------------|----------------------|
| **Caremark derivative** | WEAK (~8 checks) | Mission-critical compliance area identification; regulatory consent order history; board compliance committee structure; whistleblower disclosures | Proxy, 10-K Items 1A/3, EDGAR enforcement | LOW -- data exists |
| **Section 220 demand** | ABSENT | ISS/GL voting recommendations; say-on-pay results; shareholder proposal history; activist campaigns | Proxy, ISS data, web search | MEDIUM -- ISS data may require subscription |
| **Corporate waste** | ABSENT | CEO pay vs. peer benchmarks; related party transaction volume trends; golden parachute terms | Proxy DEF 14A, 10-K | LOW -- data exists |
| **Self-dealing** | WEAK (1-2 checks) | Related party transaction count, dollar volume, counterparty analysis, year-over-year trends | Proxy Item 404, 10-K footnotes | LOW -- data exists |
| **DOJ investigation** | PARTIAL (~5 checks) | Government subpoena disclosures; industry enforcement sweep identification; cooperating witness language | 10-K/10-Q Items 1A/3, web search | LOW -- public data |
| **State AG enforcement** | WEAK (~2 checks) | Consumer complaint volume; state AG settlement history; industry-wide enforcement trends | CFPB complaint DB, AG press releases, web search | MEDIUM -- requires monitoring |
| **CFPB/FTC individual** | ABSENT | Prior CFPB/FTC enforcement history; consumer complaint volume; subscription/cancellation practice scrutiny | CFPB complaint DB, FTC.gov, 10-K | MEDIUM |
| **FCPA exposure** | WEAK (1 check) | Country risk mapping vs. operations; third-party agent usage; government customer concentration; peer FCPA enforcement | 10-K geographic segments, TI CPI index | LOW -- data exists |
| **Bank regulatory** | WEAK (1-2 checks) | Consent orders; MRA/MRIA history; BSA/AML compliance issues; CRA compliance | OCC/FDIC enforcement databases, 10-K | MEDIUM -- regulatory database access |
| **CERCLA individual** | ABSENT | EPA Superfund site proximity; environmental liabilities in footnotes; prior EPA enforcement; PFAS exposure | 10-K footnotes, EPA databases, web search | MEDIUM |
| **Deepening insolvency** | GOOD (via financial distress) | Debt-funded acquisitions in distress; insider bonuses during distress; new borrowing at above-market rates | 10-K, 8-K, insider trading data | LOW -- mostly exists |
| **Zone of insolvency** | PARTIAL | Altman Z-Score computation; covenant breach disclosures; cash runway calculation; credit agency downgrades | 10-K financial data, credit agency databases | LOW -- mostly computable |
| **Fraudulent transfer** | ABSENT | Insider payments within 1 year of distress; dividend payments during cash flow decline; share buybacks during distress | 10-K, 8-K, insider trading data | LOW -- data exists |
| **Side A trigger risk** | ABSENT | Assessment of whether D&O program has adequate Side A limits; bankruptcy probability; indemnification restrictions | Not available from public data (submission data needed) | HIGH -- requires submission |
| **ERISA stock drop** | ABSENT | 401(k) plan with company stock option; retirement plan assets in company stock percentage; concurrent SCA/fraud allegations | 10-K benefit plan footnotes, Form 11-K | LOW -- data exists |
| **Whistleblower retaliation** | PARTIAL (1-2 checks) | Whistleblower disclosure language in filings; internal investigation disclosures; sudden executive departures | 10-K Items 1A/3, 8-K Item 5.02 | LOW -- public data |
| **Workplace culture** | ABSENT | EEOC complaints; harassment settlement disclosures; CEO/executive departures for "personal reasons"; Glassdoor metrics | 10-K, EEOC data, web search | MEDIUM |
| **Revenue recognition complexity** | WEAK (2-3 checks) | Rev rec policy description complexity; ASC 606 disclosure changes; deferred revenue trends; unbilled receivable growth; DSO trajectory | 10-K Notes 1/2, balance sheet | LOW -- data exists |
| **VIE/SPE complexity** | ABSENT | VIE count; off-balance-sheet commitment magnitude; related party VIEs; auditor CAM on consolidation | 10-K footnotes | LOW -- data exists |
| **Multi-jurisdictional exposure** | WEAK (1-2 checks) | Country count; revenue by geography; operations in high-risk jurisdictions; dual listing status | 10-K geographic segments, SEC filings | LOW -- data exists |
| **AI governance** | ABSENT | AI disclosure in 10-K; AI risk factors; AI governance committee/policy existence; AI-related regulatory inquiries | 10-K Items 1/1A, proxy, web search | LOW -- public data |

---

## 8. Recommendations -- Which Non-SCA Pathways Need Checks in Our System?

### Priority 1: High Impact, Data Available, Low Implementation Effort

**R1. Caremark/Derivative Exposure Assessment (10-15 new checks)**

Rationale: Derivative settlements are now regularly exceeding $100M (Boeing $237.5M, Walmart $123M), and the claim success rate has increased to ~30%. The current system has only ~8 checks covering derivative exposure.

Specific checks to add:
- `DERIV.CAREMARK.mission_critical_compliance`: Does the company have a "mission critical" compliance area (bank lending, pharma safety, food safety, aviation safety, healthcare billing) and does the board have a dedicated committee for it?
- `DERIV.CAREMARK.regulatory_consent_history`: Count and severity of prior regulatory consent orders in the mission-critical area
- `DERIV.CAREMARK.compliance_committee_exists`: Does the proxy disclose a board-level compliance committee separate from audit?
- `DERIV.CAREMARK.whistleblower_disclosure`: Are there whistleblower-related disclosures in 10-K Items 1A, 3, or legal proceedings footnotes?
- `DERIV.CAREMARK.regulatory_pattern`: Pattern of multiple regulatory actions in the same compliance area (indicates systemic failure, not one-off)
- `DERIV.WASTE.ceo_pay_vs_peers`: CEO total compensation vs. peer group median (flag if >2x)
- `DERIV.WASTE.say_on_pay_result`: Say-on-pay vote result (flag if <70% approval)
- `DERIV.SELF_DEAL.related_party_volume`: Dollar volume of related party transactions (absolute and as % of revenue)
- `DERIV.SELF_DEAL.related_party_count`: Number of distinct related party transactions (increasing count = increasing risk)
- `DERIV.SELF_DEAL.related_party_types`: Types of related party transactions (flag: real estate with family, consulting with director-controlled entities)
- `DERIV.DEMAND.shareholder_activism`: Active shareholder proposals or activist campaigns
- `DERIV.DEMAND.iss_against`: ISS/GL "Against" recommendations on directors

Data sources: Proxy DEF 14A, 10-K Items 1A/3/footnotes, ISS data (if available), web search for regulatory history.

**R2. Business Complexity Risk Indicators (8-10 new checks)**

Rationale: Business complexity correlates with both claim frequency and severity. Defense costs have doubled for complex D&O claims. The current system does not systematically assess structural complexity.

Specific checks to add:
- `BIZ.COMPLEX.vie_count`: Number of VIEs disclosed in 10-K footnotes
- `BIZ.COMPLEX.off_balance_sheet`: Magnitude of off-balance-sheet commitments and guarantees
- `BIZ.COMPLEX.subsidiary_count`: Number of subsidiaries (10-K Exhibit 21)
- `BIZ.COMPLEX.jurisdiction_count`: Number of countries with material operations
- `BIZ.COMPLEX.high_risk_jurisdictions`: Operations in countries with TI CPI < 40, sanctions risk, or weak rule of law
- `BIZ.COMPLEX.rev_rec_complexity`: Revenue recognition policy description complexity score (length, number of performance obligations, variable consideration, judgment areas)
- `BIZ.COMPLEX.segment_count`: Number of reporting segments (more segments = more complexity)
- `BIZ.COMPLEX.dual_listing`: Whether company is listed on multiple exchanges in different countries
- `BIZ.COMPLEX.holding_structure`: Whether company operates through a holding company structure with layered subsidiaries

Data sources: 10-K (footnotes, Exhibit 21, Item 2, segment disclosures), proxy.

**R3. Bankruptcy/Insolvency D&O Exposure Enhancement (5-8 new checks)**

Rationale: Business insolvencies are at record levels (+24% above pre-pandemic). The current system detects financial distress well (F8, DEATH_SPIRAL) but does not assess the specific D&O claim triggers that arise in insolvency.

Specific checks to add:
- `INSOL.DUTY_SHIFT.altman_z`: Altman Z-Score computation (flag zones: distress <1.81, gray 1.81-2.99, safe >2.99)
- `INSOL.DUTY_SHIFT.creditor_duty`: Is the company in the "zone of insolvency" where fiduciary duties extend to creditors?
- `INSOL.TRANSFER.insider_payments`: Insider compensation payments (bonuses, severance) during period of financial distress
- `INSOL.TRANSFER.dividends_during_distress`: Dividend payments or share buybacks while cash flow is declining
- `INSOL.TRANSFER.above_market_debt`: New borrowing at rates significantly above market (signals desperation)
- `INSOL.SIDE_A.indemnification_risk`: Assessment of whether the company has resources to indemnify D&Os given current financial position
- `INSOL.DEEPENING.debt_funded_growth`: Acquisition or expansion funded by debt during period of operating cash flow decline

Data sources: 10-K financial statements (already extracted), 8-K filings, insider trading data.

### Priority 2: High Impact, Moderate Implementation Effort

**R4. Regulatory/Government Enforcement Exposure (6-8 new checks)**

Specific checks:
- `REG.DOJ.investigation_disclosure`: DOJ subpoena or investigation disclosure in SEC filings
- `REG.DOJ.cooperation_language`: "Cooperating with government" language in 10-K/10-Q
- `REG.FCPA.geographic_risk`: Revenue or operations concentration in high-corruption-risk countries
- `REG.FCPA.third_party_agents`: Use of third-party sales agents in government procurement (disclosed in 10-K)
- `REG.STATE_AG.consumer_complaints`: Consumer complaint trend (CFPB complaint database is publicly searchable)
- `REG.FTC.prior_enforcement`: Prior FTC/CFPB enforcement action history
- `REG.BANK.consent_orders`: Active regulatory consent orders or formal enforcement actions (bank-specific)
- `REG.ENV.superfund_epa`: EPA Superfund site involvement or environmental enforcement history

**R5. Employment/Fiduciary Exposure (4-6 new checks)**

Specific checks:
- `EMPL.ERISA.company_stock_plan`: Does the 401(k) plan offer company stock as an investment option?
- `EMPL.WHISTLE.internal_investigation`: Internal investigation disclosures in SEC filings
- `EMPL.WHISTLE.executive_departure_sudden`: Sudden executive departures (8-K Item 5.02) without clear succession
- `EMPL.CULTURE.harassment_settlements`: Harassment or discrimination settlement disclosures in 10-K
- `EMPL.CULTURE.eeoc_actions`: Known EEOC complaints or charges against the company
- `EMPL.ANTITRUST.employee_agreements`: Non-compete or non-solicitation agreements with potential antitrust exposure

**R6. Emerging Risk Indicators (4-6 new checks)**

Specific checks:
- `EMERGING.AI.governance_disclosure`: AI governance committee, policy, or oversight framework disclosed in proxy/10-K
- `EMERGING.AI.risk_factor_quality`: Specificity and quality of AI-related risk factor disclosure (generic boilerplate vs. substantive governance)
- `EMERGING.PRIVACY.state_law_exposure`: Number of state privacy laws applicable based on operations and customer base
- `EMERGING.CLIMATE.dated_targets`: Specific dated emissions/climate targets without disclosed reduction progress
- `EMERGING.CRYPTO.balance_sheet_exposure`: Material digital asset holdings on balance sheet
- `EMERGING.ESG.supply_chain_due_diligence`: Conflict mineral filings, forced labor risk in supply chain, supply chain human rights policies

### Priority 3: Important but Requiring New Data Sources

**R7. Side A Adequacy Assessment**
- Cannot be assessed from public data alone (requires submission information about D&O program structure)
- Recommendation: Add to the worksheet as a qualitative question for the underwriter: "Given the company's financial condition, is Side A DIC coverage adequate?"
- If the system detects elevated financial distress signals, flag that Side A adequacy should be specifically evaluated

**R8. Reincorporation Risk Assessment**
- Track whether the company is incorporated in Delaware, Nevada, Texas, or other state
- Different incorporation states have different derivative suit standards, fiduciary duty frameworks, and D&O exposure profiles
- The 2025 reincorporation trend (companies leaving Delaware) may reduce some derivative exposure but create uncertainty about new jurisdiction's standards

### Implementation Sequencing

| Phase | Checks | Effort Estimate | Dependency |
|-------|--------|----------------|------------|
| Phase A | R1 (Caremark/Derivative) | 3-5 days | Proxy data extraction enhancement |
| Phase B | R3 (Bankruptcy/Insolvency) | 2-3 days | No new data needed -- uses existing financial data |
| Phase C | R2 (Business Complexity) | 3-4 days | Footnote extraction enhancement |
| Phase D | R4 (Regulatory Enforcement) | 3-5 days | Web search for regulatory history |
| Phase E | R5 (Employment/Fiduciary) | 2-3 days | 8-K parsing for Item 5.02 |
| Phase F | R6 (Emerging Risks) | 2-3 days | AI/privacy-specific extraction prompts |

Total estimated effort: 15-23 days for 38-53 new checks.

### Scoring Integration

The new checks should integrate into the existing 10-factor scoring model as follows:

| New Check Category | Primary Factor | Secondary Factor | New Weight Consideration |
|-------------------|---------------|-----------------|------------------------|
| Caremark/Derivative | F9 (Governance) | F1 (Prior Litigation) | Consider creating F11 (Derivative Exposure) at 4-6 points |
| Business Complexity | F3 (Restatement/Audit) | F8 (Financial Distress) | Add as complexity multiplier to F3 |
| Bankruptcy/Insolvency | F8 (Financial Distress) | -- | Enhance F8 sub-scoring |
| Regulatory Enforcement | New: F12 (Regulatory Risk) | F1 (Prior Litigation) | Consider creating F12 at 4-6 points, sourced from F1 reweight |
| Employment/Fiduciary | F9 (Governance) | -- | Add as sub-scores under F9 |
| Emerging Risks | Varies | -- | Add as modifiers (not new factors) |

### Critical Red Flag Gates to Add

| CRF ID | Condition | Ceiling | Rationale |
|--------|-----------|---------|-----------|
| CRF-12 | Active DOJ criminal investigation disclosed | REFER | Company with active DOJ criminal investigation requires senior underwriter review |
| CRF-13 | Company in zone of insolvency (Altman Z < 1.81) | DECLINE or REFER | Zone of insolvency fundamentally changes D&O exposure profile |
| CRF-14 | Caremark claim survived dismissal | REFER | Indicates court found colorable evidence of oversight failure |

---

## Sources

### Derivative Suits / Caremark
- [K&L Gates: The Continued Evolution of Caremark Oversight Liability (Oct 2024)](https://www.klgates.com/The-Continued-Evolution-of-Caremark-Oversight-Liability-10-23-2024)
- [Harvard Law School Forum: 2024 Caremark Developments](https://corpgov.law.harvard.edu/2024/05/20/2024-caremark-developments-has-the-courts-approach-shifted/)
- [ABA: Boards' Duty of Oversight -- Caremark to Boeing](https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-may/boards-duty-oversight-caremark-continuing-travails-boeing/)
- [The D&O Diary: Wells Fargo Oversight Claims](https://www.dandodiary.com/2024/09/articles/shareholders-derivative-litigation/breach-of-the-duty-of-oversight-claims-against-wells-fargos-board-sustained-in-part/)
- [The D&O Diary: Walmart Opioid Derivative Settlement ($123M)](https://www.dandodiary.com/2024/10/articles/shareholders-derivative-litigation/walmart-opioid-related-duty-of-oversight-derivative-suit-settled-for-123-million/)
- [The D&O Diary: Boeing Air Crash Derivative Settlement ($237.5M)](https://www.dandodiary.com/2021/11/articles/shareholders-derivative-litigation/boeing-air-crash-derivative-lawsuit-settles-for-237-5-million/)
- [Sidley: Chancery Rejects 'Quibbles' as Basis for Caremark Claims (Jan 2025)](https://ma-litigation.sidley.com/2025/01/chancery-rejects-quibbles-as-the-basis-for-caremark-claims-underscoring-the-wide-gulph-between-imperfect-compliance-and-purposeful-lawbreaking/)

### Section 220 / Demand Futility
- [Mayer Brown: Delaware Section 220 Amendments (May 2025)](https://www.mayerbrown.com/en/insights/publications/2025/05/delaware-law-alert-books-and-records-inspection-under-the-amended-220)
- [Perkins Coie: Delaware Narrows Stockholder Inspection Rights](https://perkinscoie.com/insights/update/delaware-significantly-narrows-scope-stockholder-inspection-corporate-books-and)
- [Harvard Law: Delaware Supreme Court Clarifies Demand Futility Standards](https://corpgov.law.harvard.edu/2021/10/27/delaware-supreme-court-clarifies-the-standards-for-demand-futility/)
- [Harvard Law: Delaware Corporate Law Recent Trends (Feb 2025)](https://corpgov.law.harvard.edu/2025/02/25/delaware-corporate-law-recent-trends-and-developments/)

### Regulatory/Government Enforcement
- [Sidley: Making Sense of DOJ's Monaco Memo](https://www.sidley.com/en/insights/newsupdates/2022/09/making-sense-of-us-dojs-new-monaco-memo-on-corporate-enforcement)
- [Woodruff Sawyer: FTC Holding Corporate Officers Personally Liable](https://woodruffsawyer.com/insights/ftc-enforcement-actions)
- [Venable: Individual Liability in CFPB Enforcement Actions](https://www.venable.com/insights/publications/2021/05/now-its-personal-individual-liability-in-recent)
- [Skadden: State AGs May Fill Enforcement Void (Mar 2025)](https://www.skadden.com/insights/publications/2025/03/state-attorneys-general-may-fill)
- [Husch Blackwell: State AG 2025 Enforcement Landscape](https://www.governmentenforcementreport.com/2025/12/state-attorneys-general-2025-enforcement-landscape-what-companies-need-to-know/)

### FCPA
- [Lexology: FCPA Year-in-Review 2025 Developments](https://www.lexology.com/library/detail.aspx?g=44cf66f6-b0cb-4761-a7d0-b23f8c94a4a9)
- [Steptoe: DOJ's New FCPA Enforcement Guidelines](https://www.steptoe.com/en/news-publications/dojs-new-fcpa-enforcement-guidelines-continuity-with-a-twist.html)
- [V-Comply: FCPA Enforcement Trends in 2025](https://www.v-comply.com/blog/fcpa-enforcement-trends/)

### Bankruptcy/Insolvency
- [ABA: Mitigating D&O Liability Post-Purdue (Mar 2025)](https://www.americanbar.org/groups/business_law/resources/business-law-today/2025-march/best-practices-insolvency-risk-management/)
- [WTW: D&O Insurance and Distressed Risk (Jan 2026)](https://www.wtwco.com/en-us/insights/2026/01/d-and-o-insurance-and-distressed-risk-is-your-program-bankruptcy-ready)
- [National Law Review: Side A D&O Policy Provides Immediate Lifeline During Bankruptcy](https://natlawreview.com/article/side-do-policy-provides-immediate-lifeline-embattled-former-executives-during)
- [K&L Gates: Key Considerations for Officers and Directors of Distressed Companies](https://www.klgates.com/Key-Considerations-for-Officers-and-Directors-of-Distressed-Companies-7-22-2021)

### Employment/Fiduciary
- [Mayer Brown: Key Issues in ERISA Class Action Litigation 2026](https://www.mayerbrown.com/en/insights/publications/2026/01/key-issues-to-watch-in-erisa-defined-contribution-plan-class-action-litigation-in-2026)
- [The D&O Diary: ERISA Claims](https://www.dandodiary.com/articles/erisa/)
- [Zuckerman Law: SEC Whistleblower Protections](https://www.zuckermanlaw.com/sec-whistleblower-protections-dodd-frank-and-sarbanes-oxley-prohibitions-against-retaliation/)
- [Hogan Lovells: #MeToo Wave 2025](https://www.hoganlovells.com/en/publications/the-metoo-wave-will-affect-every-industry-in-2025)

### Business Complexity
- [Allianz Commercial: D&O Notifications and Loss Trends](https://commercial.allianz.com/news-and-insights/expert-risk-articles/d-o-notifications-and-loss-trends.html)
- [Harvard Law: Reporting Obligations of Variable Interest Entities](https://corpgov.law.harvard.edu/2018/09/09/reporting-obligations-of-variable-interest-entities/)

### Emerging Trends
- [Allianz Commercial: D&O Insurance Insights 2026](https://commercial.allianz.com/news-and-insights/news/directors-and-officers-insurance-insights-2026.html)
- [The D&O Diary: Global AI Regulations D&O Liability (Dec 2025)](https://www.dandodiary.com/2025/12/articles/artificial-intelligence/guest-post-global-ai-regulations-do-liability-implications-in-a-changing-legal-landscape/)
- [Insurance Business: AI Governance Failures as D&O Liability Risk](https://www.insurancebusinessmag.com/uk/news/professional-liability/ai-governance-failures-are-becoming-a-dando-liability-risk-564362.aspx)
- [Clearygottlieb: 2026 Digital Assets Regulatory Update](https://www.clearygottlieb.com/news-and-insights/publication-listing/2026-digital-assets-regulatory-update-a-landmark-2025-but-more-developments-on-the-horizon)
- [K&L Gates: Climate Change Litigation Snapshot (Jan 2026)](https://www.klgates.com/Current-Trends-in-Climate-Change-Litigation-A-Snapshot-of-Risk-and-Insurance-Considerations-1-14-2026)
- [WTW: D&O Liability Look Ahead 2025](https://www.wtwco.com/en-us/insights/2025/01/directors-and-officers-d-and-o-liability-a-look-ahead-to-2025)
- [Woodruff Sawyer: 2026 D&O Looking Ahead Guide](https://woodruffsawyer.com/insights/do-looking-ahead-guide)

### Market/Industry Data
- [Woodruff Sawyer: D&O Looking Ahead 2026 Press Release](https://woodruffsawyer.com/press/woodruff-sawyer-releases-13th-annual-do-looking-ahead-guide)
- [Aon: Management Liability Insurance Market 2025](https://www.aon.com/en/insights/articles/financial-services-group/management-liability-insurance-market-in-2025-stability-amid-evolving-risks)
- [WTW: Insurance Marketplace Realities 2026 D&O](https://www.wtwco.com/en-us/insights/2025/10/insurance-marketplace-realities-2026-directors-and-officers-liability)
- [Insurance Business: D&O Claims Rebound -- Allianz](https://www.insurancebusinessmag.com/us/news/professional-liability/dando-claims-rebound-as-boards-face-converging-geopolitical-cyber-and-ai-risks--allianz-558938.aspx)
