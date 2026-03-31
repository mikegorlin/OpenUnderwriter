# All Sections: Question Framework

**Status:** Step 1 for all 7 sections — defining questions, question areas, and section boundaries
**Date:** 2026-02-16
**Purpose:** Get agreement on what questions each section answers before mapping data points, checks, and ACQUIRE/ANALYZE/DISPLAY layers.

---

## Section Boundary Rules

| Section | Owns | Does NOT Own |
|---|---|---|
| **COMPANY** | Entity identity, business model, operations, structure, geography, M&A transactions, competitive position | Financial health, people, lawsuits, stock price |
| **FINANCIAL** | Liquidity, leverage, profitability, earnings quality, forensic analysis, distress indicators, guidance credibility, audit/accounting integrity | Business model, people, market price |
| **GOVERNANCE** | Board, executives, compensation, insider trading, shareholder rights, activist pressure, governance effectiveness | Financial statements, stock price, litigation |
| **LITIGATION** | Securities class actions, regulatory enforcement, derivative suits, non-securities litigation, defense posture, litigation reserves | Stock price reaction to lawsuits, governance failures that enable lawsuits |
| **MARKET** | Stock price, volatility, trading patterns, short interest, ownership structure, analyst coverage, valuation | Why price moved (that's COMPANY/FINANCIAL/LITIGATION), insider *motivation* (that's GOVERNANCE) |
| **DISCLOSURE** | Risk factor evolution, MD&A language/tone, filing mechanics, narrative consistency, disclosure quality | Financial *numbers* (that's FINANCIAL), litigation *facts* (that's LITIGATION) |
| **FORWARD** | Upcoming catalysts, employee early warnings, customer signals, macro headwinds, alternative data | Current state of anything (FORWARD = what's coming, not what is) |

---

## Cross-Section Moves (Confirmed)

### Questions Moved TO Other Sections

| Question | From | To | Rationale |
|---|---|---|---|
| Capital markets access | COMPANY | FINANCIAL | Financial condition |
| Revenue growth rate evaluation | COMPANY | FINANCIAL | Financial metric |
| Debt maturity, cash runway, burn rate | COMPANY | FINANCIAL | Financial health |
| Which agencies regulate this entity | COMPANY | LITIGATION | Enforcement jurisdiction |
| Litigation history, recidivist pattern | COMPANY | LITIGATION | Litigation data |
| Zone of insolvency | FORWARD | FINANCIAL | Current distress indicator |
| Goodwill/impairment risk | FORWARD | FINANCIAL | Balance sheet analysis |
| Revenue quality/margin pressure trends | FORWARD | FINANCIAL | Financial trend analysis |
| Working capital trends | FORWARD | FINANCIAL | Financial trend analysis |
| Audit committee effectiveness, SOX 404, material weakness | GOVERNANCE | FINANCIAL | Financial reporting outcomes |
| Risk factor evolution | FORWARD (FWRD.DISC) | DISCLOSURE | Disclosure analysis |
| Narrative coherence | FORWARD (FWRD.NARRATIVE) | DISCLOSURE | Disclosure analysis |

### Questions Moved HERE From Other Sections

| Question | From | To | Rationale |
|---|---|---|---|
| Sector dynamics, consolidation, disruption | FORWARD | COMPANY | Current landscape, not prediction |
| Industry-specific metric applicability | FINANCIAL | COMPANY | Identity question |
| Operating leverage, cost structure | Orphaned checks | COMPANY | Business model fundamentals |

---

# SECTION 1: COMPANY

**Full design:** See COMPANY-SECTION-DESIGN.md (Steps 1-3 complete with ACQUIRE/ANALYZE/DISPLAY)

**Purpose:** Tell the story of the company. When an underwriter finishes this section, they understand the entity completely.

| Area | Questions | Summary |
|---|---|---|
| **AREA 1: IDENTITY** | Q1.1-Q1.4 | Industry, market cap, lifecycle stage, risk archetype |
| **AREA 2: BUSINESS MODEL & REVENUE** | Q2.1-Q2.5 | Revenue model, segments, key products, cost structure, pricing power |
| **AREA 3: OPERATIONS & DEPENDENCIES** | Q3.1-Q3.5 | Customer concentration, supplier dependencies, supply chain, workforce, technology |
| **AREA 4: CORPORATE STRUCTURE & COMPLEXITY** | Q4.1-Q4.4 | Entity structure, VIE/SPE, off-balance sheet, intercompany |
| **AREA 5: GEOGRAPHIC FOOTPRINT** | Q5.1-Q5.3 | Where they operate, jurisdiction risks, sanctions/GDPR/FCPA |
| **AREA 6: M&A & CORPORATE TRANSACTIONS** | Q6.1-Q6.5 | Pending deals, 2-3yr history, goodwill, integration risk, deal litigation |
| **AREA 7: COMPETITIVE POSITION & INDUSTRY** | Q7.1-Q7.5 | Market share, moat, peer comparison, SCA contagion, headwinds/tailwinds |

**Total: 7 areas, 31 questions**
**Existing checks:** 44 (BIZ.* prefix + some FWRD.WARN AI/hyperscaler)

---

# SECTION 2: FINANCIAL

**Purpose:** Assess the company's financial condition, reporting reliability, and distress signals. Answers: "Can this company survive the policy period without triggering financial-related D&O claims?"

## AREA 1: LIQUIDITY & SOLVENCY

*Can the company meet its near-term obligations?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q1.1 | Does the company have adequate liquidity to meet short-term obligations? | Liquidity crisis = bankruptcy risk = D&O claims. Current ratio < 1.0 and declining = RED. | Current ratio, quick ratio, cash ratio with trend (improving/declining) and peer comparison |
| Q1.2 | What is the cash runway — how many months before cash runs out? | Pre-revenue and loss-making companies: if cash < 12 months of burn, existential risk. | Months of cash at current burn rate, with trajectory |
| Q1.3 | Is there a going concern opinion from the auditor? | Going concern = auditor's formal doubt about survival. Strongest single distress indicator. | Clean or going concern qualified; if qualified, management's plan |
| Q1.4 | How has working capital trended over the past 3 years? | Deteriorating working capital precedes liquidity crises. | WC trend (improving/stable/declining), magnitude of change |

## AREA 2: LEVERAGE & DEBT STRUCTURE

*How much debt does the company carry, and can they service it?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q2.1 | How leveraged is the company relative to earnings capacity? | High leverage + earnings decline = covenant breach + bankruptcy. Debt/EBITDA > 4x = concerning. | D/E ratio, Debt/EBITDA, with peer comparison |
| Q2.2 | Can the company service its debt (interest coverage)? | Interest coverage < 2x = struggling to pay interest. <1x = burning cash to pay creditors. | Interest coverage ratio with trend |
| Q2.3 | When does significant debt mature and is refinancing at risk? | Debt maturity walls in rising rate environments = refinancing crisis. | Maturity schedule with near-term concentration callout |
| Q2.4 | Are there covenant compliance risks? | Covenant breach triggers acceleration, default, potentially bankruptcy. | Covenant cushion, approaching thresholds |
| Q2.5 | What is the credit rating and recent trajectory? | Downgrade = market signal of deterioration. Fallen angel (IG to HY) = forced selling. | Rating, outlook, recent actions |

## AREA 3: PROFITABILITY & GROWTH

*Is the business economically viable and growing?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q3.1 | Is revenue growing or decelerating? | Revenue deceleration is the #1 SCA trigger — growth companies that slow down get sued. | Revenue growth rate, YoY and sequential trend, acceleration/deceleration |
| Q3.2 | Are margins expanding, stable, or compressing? | Margin compression = competitive pressure or cost problems. Often precedes guidance misses. | Gross margin, operating margin, EBITDA margin with 3-year trend |
| Q3.3 | Is the company profitable? What's the trajectory? | Persistent losses exhaust cash, approach distress. Trajectory matters more than current level. | Net income trend, path to profitability (if loss-making) |
| Q3.4 | How does cash flow quality compare to reported earnings? | OCF/NI divergence = aggressive accounting. Cash flow declining while earnings grow = fraud signal. | OCF-to-NI ratio, free cash flow, cash conversion |
| Q3.5 | Are there segment-level divergences hiding overall trends? | Aggregate metrics can mask a failing segment subsidized by a healthy one. | Per-segment revenue/margin trend if available |

## AREA 4: EARNINGS QUALITY & FORENSIC ANALYSIS

*Are the financial statements trustworthy, or is there manipulation?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q4.1 | Is there evidence of earnings manipulation? | Beneish M-Score > -1.78 = likely manipulation. Dechow F-Score flags restatement probability. | M-Score, F-Score, with zone classification (safe/grey/danger) |
| Q4.2 | Are accruals abnormally high relative to cash flows? | High accruals = earnings "quality" is low — more paper than cash. Sloan ratio flags this. | Accruals ratio, Sloan ratio, Enhanced Sloan, with peer context |
| Q4.3 | Is revenue quality deteriorating? | DSO expansion, Q4 concentration, deferred revenue decline = revenue recognition aggression. | DSO trend, quarterly revenue distribution, deferred revenue trend |
| Q4.4 | Is there a growing gap between GAAP and non-GAAP earnings? | Widening gap = management obscuring real economics. Common in SCA allegations. | GAAP vs non-GAAP delta, trend, reconciliation items |
| Q4.5 | What does the Financial Integrity Score composite indicate? | Composite forensic score combining multiple indicators for overall manipulation risk. | FIS composite with component breakdown |

## AREA 5: ACCOUNTING INTEGRITY & AUDIT RISK

*Is the financial reporting reliable, and is the auditor raising concerns?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q5.1 | Who is the auditor and what's their tenure and opinion? | Big 4 auditor with long tenure = stability. Non-Big 4 or new auditor = lower deterrent. | Auditor name, Big 4 Y/N, years of tenure, opinion type |
| Q5.2 | Has there been a restatement, material weakness, or significant deficiency? | Restatement = strongest predictor of SCA filing. MW = internal controls failing. Each is a CRF gate. | Restatement Y/N with date/type; MW Y/N; SD Y/N |
| Q5.3 | Has there been an auditor change, and why? | Auditor changes, especially forced/disagreement, signal accounting problems. | Change Y/N, reason (rotation/disagreement/fees), any disagreement letter |
| Q5.4 | Are there SEC comment letters raising accounting questions? | SEC review questions = regulatory concern about specific accounting policies. | Comment letter count, topics, resolution status |
| Q5.5 | What are the critical audit matters (CAMs)? | CAMs = auditor's assessment of most challenging areas. Changes from prior year = evolving risk. | CAM count, topics, new vs prior year |

## AREA 6: FINANCIAL DISTRESS INDICATORS

*Composite models: how close is this company to failure?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q6.1 | What does the Altman Z-Score indicate? | Z < 1.81 = distress zone (40%+ of SCA filers are distressed). Z > 2.99 = safe. | Z-Score, zone (safe/grey/distress), trajectory |
| Q6.2 | What does the Ohlson O-Score show? | Bankruptcy probability model. O > 0.5 = elevated probability. | O-Score, bankruptcy probability estimate |
| Q6.3 | What does the Piotroski F-Score show? | Fundamental quality 0-9. F < 3 = weak fundamentals, likely decline. F > 7 = strong. | F-Score, quality classification |
| Q6.4 | Is the company approaching zone of insolvency? | Zone of insolvency shifts board duties from shareholders to creditors — different litigation landscape. | Solvency assessment (clear/approaching/in zone) |

## AREA 7: GUIDANCE & MARKET EXPECTATIONS

*Is management credible in their forward communications?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q7.1 | Does the company provide earnings guidance and what's the current outlook? | Guidance sets expectations. Aggressive guidance followed by a miss = SCA trigger. | Guidance Y/N, current EPS/revenue guidance range |
| Q7.2 | What's the guidance track record (beat/miss pattern)? | 2+ consecutive misses in 4 quarters = RED. Pattern of narrow beats may be manipulation. | Beat rate %, consecutive misses, last 8 quarters detail |
| Q7.3 | What's the guidance philosophy? | Conservative (low-ball then beat) vs aggressive (promise then miss). Aggressive = higher SCA risk. | Philosophy classification with evidence |
| Q7.4 | How does analyst consensus align with company guidance? | Large gap = either management or analysts are wrong. Divergence = volatility risk. | Company guidance vs consensus estimate, delta |
| Q7.5 | How does the market react to earnings? | Severe market punishment for misses (>10% drops) = heightened SCA trigger risk. | Average earnings reaction, worst recent reaction |

## AREA 8: SECTOR-SPECIFIC FINANCIAL METRICS

*Which industry-specific metrics apply to this company?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q8.1 | What industry-specific KPIs matter for this company? | Biotech = cash runway. SaaS = NRR/Rule of 40. Energy = reserve replacement. Retail = same-store sales. | Applicable KPI list with current values |
| Q8.2 | How do sector KPIs compare to industry benchmarks? | Underperforming on sector-specific metrics = industry-specific claim exposure. | KPI values with peer median comparison |

**Total: 8 areas, 36 questions**
**Existing checks:** 65 (FIN.* prefix) + FWRD.WARN financial-related + GOV.EFFECT audit-related moved here

---

# SECTION 3: GOVERNANCE

**Purpose:** Evaluate the people running the company — their quality, trustworthiness, and alignment with shareholders. Answers: "Are the right people in charge, and are they acting in shareholders' interests?"

## AREA 1: BOARD COMPOSITION & QUALITY

*Is the board structured to provide effective oversight?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q1.1 | How independent is the board? | Independence < 50% fails NYSE requirement. < 67% = below typical large-cap. Low independence = oversight failure risk. | Independence ratio with peer context, compliance status |
| Q1.2 | Is the CEO also the board chair? | Combined CEO/Chair concentrates power, reduces board independence. Common factor in derivative claims. | Duality Y/N, lead independent director existence |
| Q1.3 | What's the board size, tenure distribution, and diversity? | Too small (<5) = limited capacity. Too large (>15) = ineffective. Long avg tenure = entrenchment. | Size, avg tenure, tenure distribution, diversity metrics |
| Q1.4 | Are any directors overboarded? | Directors on 4+ boards can't give adequate attention. ISS threshold = 5 public boards. | Count of overboarded directors, which boards |
| Q1.5 | Is this a classified (staggered) board? | Classified board = harder to replace directors. Revlon duty implications in M&A. Derivative suit factor. | Classified Y/N, declassification timeline if any |
| Q1.6 | How engaged is the board? | Meeting frequency, attendance rates, committee meeting count signal actual oversight vs rubber stamp. | Meeting count, attendance rate, committee structure |

## AREA 2: EXECUTIVE TEAM & STABILITY

*Are the right leaders in place, and is the team stable?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q2.1 | Who is the CEO and what's their tenure and background? | CEO sets culture and risk tolerance. Short tenure (<2yr) = transition risk. Long tenure (>10yr) = entrenchment risk. | CEO name, tenure, background, prior litigation history |
| Q2.2 | Who is the CFO and what's their experience? | CFO controls financial reporting. Big 4 background = quality signal. Prior restatement involvement = RED. | CFO name, tenure, Big 4 Y/N, background |
| Q2.3 | Has there been recent C-suite turnover? | Unplanned CFO departure is the single strongest predictor of future SCA. Multiple departures = crisis. | Departure count (18mo), planned vs unplanned, which roles |
| Q2.4 | Is there a succession plan for key roles? | No succession plan + key-person risk = governance gap. | Succession planning status, interim roles active |
| Q2.5 | Do any executives have prior litigation or enforcement history? | Prior fraud, SEC bars, or litigation at other companies = character risk. | Prior litigation count per executive, nature of issues |
| Q2.6 | Is there founder/key-person concentration risk? | Founder-led companies with key-person dependency = different risk profile. | Founder status, key-person dependency assessment |

## AREA 3: COMPENSATION & ALIGNMENT

*Is management incentivized to act in shareholders' interests?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q3.1 | What's the CEO's total compensation and how does it compare to peers? | Excessive comp = misalignment. >250th percentile vs peers = outlier. | CEO total comp, peer median, multiple |
| Q3.2 | What's the compensation structure (salary vs bonus vs equity)? | High fixed comp = low accountability. All equity = short-term stock price focus. | Comp mix breakdown with industry context |
| Q3.3 | What was the say-on-pay vote result? | <70% approval = significant shareholder dissent. <50% = failed. Both predict derivative suits. | Say-on-pay %, trend, ISS/GL recommendation |
| Q3.4 | Are performance metrics in incentive comp appropriate? | Revenue-only metrics encourage top-line manipulation. Non-GAAP adjustments inflate payouts. | Performance metrics used, GAAP vs non-GAAP basis |
| Q3.5 | Are there clawback policies and what's their scope? | No clawback = no accountability for misstatement. Narrow scope = weak deterrent. | Clawback Y/N, scope (financial/conduct), trigger conditions |
| Q3.6 | Are there related-party transactions or excessive perquisites? | Self-dealing = derivative suit target. Excessive perks = governance failure signal. | Related-party transaction count/value, notable perquisites |
| Q3.7 | What's the golden parachute/change-in-control exposure? | >$50M CIC payout = merger objection litigation catalyst. Excessive = misalignment. | CIC payout estimate, multiple of base salary |

## AREA 4: INSIDER TRADING ACTIVITY

*Are insiders buying or selling, and is the timing suspicious?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q4.1 | What's the net insider trading direction? | Net heavy selling = insiders don't believe in the stock. Net buying = conviction. | Net direction (buying/selling), total values, trend |
| Q4.2 | Are CEO/CFO selling significant holdings? | CEO/CFO selling >50% of holdings = CRITICAL scienter indicator in SCA litigation. | CEO/CFO sell %, timing relative to events |
| Q4.3 | What percentage of transactions use 10b5-1 plans? | <50% via pre-arranged plans = discretionary timing = higher scienter risk. | Plan coverage %, plan adoption timing |
| Q4.4 | Is there cluster selling (multiple insiders simultaneously)? | Multiple insiders selling at the same time = coordinated knowledge. Strongest insider signal. | Cluster event count, participants, values, timing |
| Q4.5 | Is insider trading timing suspicious relative to material events? | Selling before bad news announcement = textbook scienter. | Timing analysis relative to earnings misses, restatements, etc. |

## AREA 5: SHAREHOLDER RIGHTS & PROTECTIONS

*How well are shareholder rights protected?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q5.1 | Does the company have a dual-class voting structure? | Dual-class = founder/insider voting control, limits shareholder recourse. | Dual-class Y/N, voting ratio, sunset provision Y/N |
| Q5.2 | Are there anti-takeover provisions? | Poison pill, supermajority requirements = entrenchment. Relevant to Revlon duty analysis. | Provision inventory, poison pill Y/N, supermajority thresholds |
| Q5.3 | Is there proxy access for shareholder nominations? | No proxy access = limited shareholder ability to nominate director candidates. | Proxy access Y/N, thresholds (3%/3yr typical) |
| Q5.4 | What forum selection and fee-shifting provisions exist? | Federal forum for Section 11; Delaware Chancery for fiduciary. Fee-shifting deters meritless suits. | Forum provision Y/N, federal exclusive Y/N, fee-shifting Y/N |

## AREA 6: ACTIVIST PRESSURE

*Is there activist investor activity creating governance instability?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q6.1 | Are there Schedule 13D filings indicating activist intent? | 13D = 5%+ ownership with activist intent. Proxy fight risk. | 13D filings count, activist names, ownership % |
| Q6.2 | Have there been proxy contests or board seat demands? | Active proxy contest = governance instability + potential D&O claims during fight. | Contest status, board seats sought/gained |
| Q6.3 | Are there shareholder proposals with significant support? | >30% support = growing pressure. >50% = board should act or face derivative claims. | Proposal topics, support levels |
| Q6.4 | Is there a short activism campaign targeting governance? | Short activism + governance failures = amplified D&O exposure on both sides. | Short activism reports Y/N, governance allegations |

**Total: 6 areas, 33 questions**
**Existing checks:** 83 (GOV.* + EXEC.* + STOCK.INSIDER.* moved here)

---

# SECTION 4: LITIGATION

**Purpose:** Map the complete litigation and regulatory exposure landscape. Answers: "Who is suing or investigating this company, and what's the defense posture?"

## AREA 1: SECURITIES CLASS ACTIONS (ACTIVE)

*Are there current SCAs, and how serious are they?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q1.1 | Are there active securities class actions against this company? | Active SCA = known D&O loss. This is the single most important litigation fact. | Active SCA count, case name(s), court, status |
| Q1.2 | What are the class periods, allegations, and case stage? | Class period = exposure window. Allegations = legal theory. Stage = settlement proximity. | Per-case: class period dates, allegation type, motion stage |
| Q1.3 | Who is lead counsel and what tier are they? | Tier 1 plaintiff firms (Robbins Geller, etc.) = higher settlements, more aggressive prosecution. | Lead counsel name, tier classification |
| Q1.4 | What is the estimated exposure (DDL and settlement range)? | Dollar damage line = maximum theoretical exposure. Median settlement ~3% of DDL. | DDL estimate, settlement scenarios (25th/50th/75th/95th) |

## AREA 2: SECURITIES CLASS ACTION HISTORY

*What does the litigation track record tell us?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q2.1 | How many prior SCAs has this company had? | Prior SCA is the single strongest predictor of future SCA. Recidivists get sued repeatedly. | Total SCA count (lifetime), count in last 5 years |
| Q2.2 | What were the outcomes (dismissed, settled, amount)? | Settlement history sets baseline for pricing. Dismissal history suggests defense strength. | Per-SCA: outcome, settlement amount, dismissal basis |
| Q2.3 | Is there a recidivist pattern? | 3+ SCAs = systemic governance/culture problem, not bad luck. Material pricing factor. | Recidivist classification, pattern analysis |
| Q2.4 | Are there pre-filing signals (law firm announcements, investigations)? | Law firm investigation announcements precede SCA filings by weeks/months. Early warning. | Pre-filing announcement count, dates, firms |

## AREA 3: DERIVATIVE & MERGER LITIGATION

*Are there non-SCA shareholder claims?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q3.1 | Are there active derivative suits? | Derivative claims = Caremark oversight failures. Side A coverage trigger (company can't indemnify). | Active derivative count, allegations, court |
| Q3.2 | Are there merger objection lawsuits? | M&A transactions generate litigation in >80% of deals >$100M. | Merger litigation count, deal context |
| Q3.3 | Are there books and records demands (Section 220)? | Section 220 demand = precursor to derivative suit. Early signal of shareholder action. | Demand count, topics, status |

## AREA 4: SEC ENFORCEMENT

*Where is this company in the SEC enforcement pipeline?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q4.1 | What stage is any SEC matter at? | Pipeline: comment letters → informal inquiry → formal investigation → Wells Notice → enforcement action. Each stage = higher severity. | Highest confirmed stage, visual pipeline |
| Q4.2 | Are there SEC comment letters, and what topics? | Comment letters = SEC reviewing specific disclosures. Industry sweep vs targeted matters differently. | Comment letter count, topics, resolution status |
| Q4.3 | Has there been a Wells Notice? | Wells Notice = SEC staff recommending enforcement. CRF gate (binding ceiling on score). | Wells notice Y/N, date, subject matter |
| Q4.4 | What prior SEC enforcement actions exist? | Prior enforcement = regulatory recidivist. Consent decree violations = escalation. | Prior action count, types, penalties, consent decrees |

## AREA 5: OTHER REGULATORY & GOVERNMENT

*What non-SEC enforcement exposure exists?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q5.1 | Which government agencies regulate this company? | Identifies the full regulatory exposure surface. Multi-agency regulation = compounding risk. | Agency inventory with jurisdiction mapping |
| Q5.2 | Are there active DOJ investigations? | Criminal investigations = existential risk. FCPA, antitrust, fraud prosecutions. | DOJ investigation Y/N, nature, stage |
| Q5.3 | Are there state AG investigations or multi-state actions? | Multi-state AG coordinated actions = massive exposure. Often precede federal action. | State AG action count, states involved, allegations |
| Q5.4 | Are there industry-specific enforcement actions? | FDA warnings (pharma), EPA orders (industrial), OSHA citations (workplace), FTC (consumer), CFPB (financial). | Per-agency: action type, severity, status |

## AREA 6: NON-SECURITIES LITIGATION

*What is the aggregate non-SCA litigation landscape?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q6.1 | What is the aggregate active litigation count? | High aggregate litigation = litigious operations. Pattern matters more than individual cases. | Total active matters, breakdown by type |
| Q6.2 | Are there significant product liability, employment, IP, or antitrust matters? | Each type has different D&O implications. Product liability → SEC disclosure risk. Employment → pattern indicator. | Per-type: significant matters, exposure estimate |
| Q6.3 | Are there whistleblower/qui tam actions? | Whistleblower = insider with evidence. Qui tam = False Claims Act (government contract fraud). Precursors to SEC action. | Whistleblower indicator count, type, date |
| Q6.4 | Are there cyber breach or environmental litigation matters? | Post-breach SCA risk = 13.6x normal. Environmental = long-tail liability. | Breach history, environmental matters, remediation status |

## AREA 7: DEFENSE POSTURE & RESERVES

*How well positioned is the company to defend against claims?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q7.1 | What defense provisions exist? | Federal exclusive forum (Section 11), PSLRA safe harbor, Delaware forum selection all affect defense cost and outcomes. | Provision inventory with effectiveness assessment |
| Q7.2 | What are the contingent liabilities and litigation reserves? | ASC 450 reserves = management's own loss estimate. Material probable items = expected payouts. | Reserve total, probable items, range of loss |
| Q7.3 | What is the historical defense success rate? | Companies that get cases dismissed have defensible practices. Companies that always settle have leverage problems. | Dismissal rate, average settlement as % of DDL |

## AREA 8: LITIGATION RISK PATTERNS

*What systemic litigation patterns apply?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q8.1 | What are the open statute of limitations windows? | Open SOL windows = exposure to claims for past conduct. Repose dates = hard cutoffs. | Per-claim-type: SOL expiry, repose expiry, window status |
| Q8.2 | What industry-specific allegation theories apply? | Tech = privacy/IP/antitrust. Pharma = product liability/FDA. Finance = fiduciary/regulatory. | Applicable theories with company exposure assessment |
| Q8.3 | What is the contagion risk from peer lawsuits? | When peers get sued on a theory, the company faces elevated risk for the same theory. | Peer SCA count, shared allegation patterns |

**Total: 8 areas, 31 questions**
**Existing checks:** 56 (LIT.* + STOCK.LIT.* moved here)

---

# SECTION 5: MARKET

**Purpose:** Analyze what the stock market is telling us about this company's risk. Answers: "What do stock price signals, trading patterns, and market behavior indicate about D&O exposure?"

## AREA 1: STOCK PRICE PERFORMANCE

*How has the stock performed, and is there a significant decline?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q1.1 | What's the stock's current position relative to its 52-week range? | >20% below 52-week high = SCA trigger zone. >50% = near-certain SCA if there's any disclosure issue. | Current price, 52-week high/low, decline from high % |
| Q1.2 | What are the multi-horizon returns? | 1mo, 3mo, 6mo, 1yr returns show trajectory. Accelerating decline = increasing risk. | Returns at each horizon with sector comparison |
| Q1.3 | How does performance compare to the sector and peers? | Company-specific underperformance (vs sector) = company-specific problem, not market. Stronger SCA case. | Company return vs sector return, vs peer median |
| Q1.4 | Is there delisting risk? | Stock price < $1 for 30+ consecutive days triggers Nasdaq delisting notice. Delisting = governance failure. | Current price, compliance status, any notice received |

## AREA 2: STOCK DROP EVENTS

*Have there been significant drops that could trigger litigation?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q2.1 | Have there been single-day drops >8% in the past 12 months? | Single-day drops = potential class period end dates. >10% company-specific drop = SCA trigger. | Count of drops, dates, magnitudes |
| Q2.2 | Have there been multi-day decline events >15%? | Multi-day declines may indicate slow information leak or sustained selling pressure. | Decline events with duration, start/end dates |
| Q2.3 | What triggered each significant drop? | Earnings miss, guidance cut, regulatory action, short report — different triggers = different SCA theories. | Per-event: catalyst, company-specific Y/N |
| Q2.4 | What's the recovery pattern? | Quick recovery = market overreaction. No recovery = fundamental problem. | Recovery analysis per event |

## AREA 3: VOLATILITY & TRADING PATTERNS

*What does trading behavior signal?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q3.1 | What's the 90-day volatility and how does it compare to peers? | High volatility amplifies potential SCA damages (larger potential class period losses). | Vol %, peer median vol, ratio |
| Q3.2 | What's the beta? | High beta = market-sensitive. Low beta but high vol = company-specific risk (worse for D&O). | Beta value with interpretation |
| Q3.3 | Is there adequate trading liquidity? | Illiquid stocks = wider spreads, harder to establish class period, but also harder to exit. | Avg daily volume, market cap context |
| Q3.4 | Are there unusual volume or options patterns? | Pre-announcement volume spikes = potential informed trading. Unusual options = sophisticated bet. | Volume anomaly detection, options activity flags |

## AREA 4: SHORT INTEREST & BEARISH SIGNALS

*Are sophisticated investors betting against this company?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q4.1 | What's the short interest as % of float? | >10% = elevated bearish sentiment. >20% = extreme. Short sellers do deep research. | SI %, days to cover, trend |
| Q4.2 | Is short interest trending up or down? | Rising SI = growing skepticism. Falling SI after report = thesis exhausted. | 6-month SI trend |
| Q4.3 | Have there been activist short seller reports? | Hindenburg, Muddy Waters, Citron reports = NUCLEAR D&O risk. SCA filing rate after short report >50%. | Report count, publisher, allegations, stock reaction |

## AREA 5: OWNERSHIP STRUCTURE

*Who owns the stock and are there concentration risks?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q5.1 | What's the institutional vs insider vs retail ownership breakdown? | High institutional = sophisticated, will litigate. High insider = alignment but control issues. High retail = less litigation risk. | Ownership pie with percentages |
| Q5.2 | Who are the largest holders and what's the concentration? | Top 5 holding >50% = concentration risk. Activist in top 5 = governance pressure. | Top holders with % and recent changes |
| Q5.3 | Is institutional ownership declining significantly? | >15% institutional decline QoQ = smart money leaving. Precedes SCA in many cases. | QoQ change in institutional ownership |

## AREA 6: ANALYST COVERAGE & SENTIMENT

*What do professional analysts think?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q6.1 | How many analysts cover this stock? | 0-1 analyst = information asymmetry (bad for underwriting). >15 = well-covered. | Analyst count |
| Q6.2 | What's the consensus rating and recent changes? | 3+ downgrades in 30 days = CRITICAL. Rapid consensus shift = something is wrong. | Consensus rating, recent upgrades/downgrades count |
| Q6.3 | What's the price target relative to current price? | Significant downside to target = bearish. All targets below current = consensus negative. | Mean/high/low target vs current, upside/downside % |

## AREA 7: VALUATION METRICS

*Is the stock priced appropriately relative to fundamentals?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q7.1 | What are the key valuation ratios? | P/E, EV/EBITDA, PEG ratio provide context for whether stock is rich or cheap vs fundamentals. | Ratios with sector median comparison |
| Q7.2 | How does valuation compare to peers? | Premium to peers + disappointing results = larger drop potential = larger SCA damages. | Company vs peer median valuation, premium/discount % |

**Total: 7 areas, 27 questions**
**Existing checks:** 35 (STOCK.* prefix minus STOCK.INSIDER/STOCK.LIT moved to other sections)

---

# SECTION 6: DISCLOSURE

**Purpose:** Detect what management is telling us — or hiding from us — through their disclosure practices and filing behavior. Answers: "Is this company transparent, or are there red flags in how they communicate?"

## AREA 1: RISK FACTOR EVOLUTION

*How are disclosed risk factors changing?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q1.1 | How have risk factors changed year-over-year? | New risk factors = management acknowledging emerging threats. Removed risks = either resolved or buried. | Risk factor count YoY, new additions, removals |
| Q1.2 | Have new litigation-specific or regulatory risk factors appeared? | New litigation/regulatory risk factor = management knows something is coming. Leading indicator. | New litigation/regulatory factors listed with text |
| Q1.3 | Have previously disclosed risks materialized? | If a risk factor from last year actually happened, how well did management prepare? If not disclosed at all, that's worse. | Materialized risks vs prior disclosure assessment |

## AREA 2: MD&A LANGUAGE & TONE

*What does the language reveal about management's confidence?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q2.1 | Has the MD&A readability changed (Fog Index)? | Increasing Fog Index = management making disclosures harder to read. Obfuscation strategy. | Current Fog Index, YoY change, peer comparison |
| Q2.2 | Has the negative tone shifted? | Increasing negative tone = management bracing for bad news. Research shows tone predicts performance. | Negative tone ratio, YoY change |
| Q2.3 | Is there increased hedging/qualifying language? | More "may", "could", "approximately" = less certainty. Management hedging before bad news. | Hedging language frequency, YoY change |
| Q2.4 | Are forward-looking statements decreasing? | Fewer forward-looking statements = management pulling back from commitments. Caution signal. | Forward-looking statement count, YoY change |

## AREA 3: NARRATIVE CONSISTENCY

*Is the story consistent across channels?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q3.1 | Is the 10-K narrative consistent with earnings call messaging? | Divergence between formal SEC filings and investor communications = material misrepresentation risk. | Consistency assessment, specific divergences |
| Q3.2 | Is the investor-facing narrative consistent with SEC filings? | IR website, presentations, and investor days may paint rosier picture than SEC filings. | Divergence detection |
| Q3.3 | Is there analyst skepticism about management's story? | Analyst skepticism in Q&A = market doesn't believe the narrative. Predicts future disappointment. | Skepticism indicators from earnings calls |
| Q3.4 | Are there short thesis narratives contradicting management? | Short sellers publish detailed counter-narratives. When these are credible, they often precede SCAs. | Short thesis summary, specific contradictions |
| Q3.5 | What do auditor CAMs focus on, and has focus changed? | CAM topic changes = auditor shifting attention. New revenue recognition CAM = earnings quality concern. | CAM topics, YoY changes, alignment with risk factors |

## AREA 4: FILING MECHANICS & QUALITY

*Is the company meeting its disclosure obligations?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q4.1 | Has the company filed on time? | NT filing = internal control issues. Late filing = can't close books. CRF gate. | Filing timeliness, any NT notices, date shifts vs prior year |
| Q4.2 | Is non-GAAP reconciliation adequate? | Inadequate reconciliation = SEC comment letter risk. Growing GAAP/non-GAAP gap = red flag. | Reconciliation quality assessment |
| Q4.3 | Is segment reporting consistent? | Segment changes = potentially hiding deteriorating business lines. | Segment count changes, reclassifications |
| Q4.4 | Is related-party disclosure complete? | Undisclosed related-party transactions = derivative suit catalyst. | Related-party disclosure assessment |
| Q4.5 | Is the guidance methodology transparent? | Opaque guidance methodology = easier to blame management when guidance is wrong. | Methodology disclosure assessment |

## AREA 5: WHISTLEBLOWER & INVESTIGATION SIGNALS

*Are there signals of internal problems in the filings?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q5.1 | Is there whistleblower/qui tam language in filings? | Explicit whistleblower disclosure = known internal complaint. Strong leading indicator of enforcement action. | Language detected Y/N, context, severity |
| Q5.2 | Is there internal investigation language? | "Internal investigation" in filings = company knows something is wrong. Often precedes restatement or enforcement. | Language detected Y/N, subject matter, status |

**Total: 5 areas, 19 questions**
**Existing checks:** 30 (NLP.* + FWRD.DISC.* + FWRD.NARRATIVE.* moved here)

---

# SECTION 7: FORWARD

**Purpose:** Look ahead to what could go wrong during the policy period using upcoming events and alternative data. Answers: "What events, signals, or trends suggest claims may emerge in the next 12-24 months?"

## AREA 1: CATALYST EVENTS

*What specific upcoming events could trigger D&O claims?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q1.1 | When is the next earnings report and what's the miss risk? | Earnings miss = stock drop = SCA trigger. Most SCAs are filed within days of earnings miss. | Date, consensus estimate, guidance delta, miss probability assessment |
| Q1.2 | Are there pending regulatory decisions? | FDA approval/rejection (biotech), FCC ruling, antitrust clearance = binary outcome events. | Decision dates, agency, what's at stake |
| Q1.3 | Are there M&A closings or shareholder votes? | M&A closing = merger objection risk. Shareholder vote = proxy contest possibility. | Transaction dates, vote dates, deal value |
| Q1.4 | Are there debt maturities or covenant tests in the next 12 months? | Near-term debt maturity without refinancing plan = distress catalyst. Covenant breach = default trigger. | Maturity dates, amounts, covenant test dates |
| Q1.5 | Are there lockup expirations or warrant expiry? | Post-IPO lockup expiry = selling pressure. Relevant for recent IPOs/SPACs. | Lockup expiry date, shares released |
| Q1.6 | Are there contract renewals or customer retention milestones? | Loss of material contract or customer = revenue impact = stock drop catalyst. | Material contract dates, customer concentration context |
| Q1.7 | Are there litigation milestones (trial dates, settlement deadlines)? | Trial dates create settlement pressure. Class certification = exposure multiplier. | Trial dates, cert hearing dates, settlement conference dates |
| Q1.8 | Are there industry-specific catalysts? | Biotech: PDUFA dates, trial readouts. Pharma: patent cliffs. Sector-specific binary events. | Industry-specific catalyst dates |

## AREA 2: EMPLOYEE & WORKFORCE SIGNALS

*What are employees telling us about the company's health?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q2.1 | What do employee review platforms indicate? | Glassdoor < 3.0 predicts fraud (HBS research). >0.5 rating decline in 12mo = RED. | Glassdoor/Indeed/Blind ratings, trends |
| Q2.2 | Are there unusual hiring patterns? | Compliance/legal hiring surge = company preparing for enforcement. Indicates known internal problems. | Legal/compliance job posting trends |
| Q2.3 | Are there LinkedIn headcount or departure trends? | Department-level departures (accounting, legal) = stronger signal than general attrition. | Headcount trend, departure patterns by department |
| Q2.4 | Are there WARN Act or mass layoff signals? | WARN Act filings = mass layoffs >60 days away. Restructuring risk. | WARN filings, layoff announcements |

## AREA 3: CUSTOMER & PRODUCT SIGNALS

*What are customers and the market experiencing?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q3.1 | Are there customer complaint trends? | CFPB complaint surges (financial services), app rating declines (consumer tech) predict product liability and regulatory action. | Complaint trends by platform, severity |
| Q3.2 | Are there product quality signals? | FDA MedWatch adverse events (pharma/device), NHTSA complaints (auto) = product liability leading indicators. | Adverse event counts, trends, severity |
| Q3.3 | Are there customer churn or partner instability signals? | Customer churn signals = revenue risk. Partner instability = supply chain disruption risk. | Churn indicators, partner stability assessment |

## AREA 4: MACRO & INDUSTRY ENVIRONMENT

*What external forces are creating risk for this company's sector?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q4.1 | How is the sector performing overall? | Sector-wide decline = industry headwind. Company in declining sector faces additional pressure. | Sector performance index, trend |
| Q4.2 | Are peers experiencing similar issues? | Peer SCA contagion = when one company in a sector gets sued, others face elevated risk. | Peer issues count, shared patterns |
| Q4.3 | Is the industry consolidating? | Industry consolidation = M&A wave = transaction litigation wave. | Consolidation assessment, deal activity |
| Q4.4 | Are there disruptive technology threats? | Technology disruption = business model risk. Companies that miss disruption get sued for inadequate disclosure. | Disruption assessment for sector |
| Q4.5 | What macro factors affect this company? | Interest rates, FX, commodities, trade policy, labor markets — each has sector-specific impact. | Applicable macro factors with sensitivity assessment |
| Q4.6 | Are there regulatory or legislative changes in process? | New regulations = compliance transition risk. Non-compliance = enforcement. | Pending regulation inventory for sector |
| Q4.7 | Are there geopolitical or supply chain disruption risks? | Geopolitical exposure (sanctions, trade war) + supply chain vulnerability = operational risk. | Exposure assessment by geography and supply chain |

## AREA 5: MEDIA & EXTERNAL SENTIMENT SIGNALS

*What are external observers seeing and saying?*

| # | Question | Why We Ask | Good Answer Looks Like |
|---|---|---|---|
| Q5.1 | What does social media sentiment indicate? | Social media sentiment shifts precede formal complaints and regulatory attention. | Sentiment trend, volume, specific concerns |
| Q5.2 | Is there investigative journalism activity? | Investigative journalism often uncovers fraud before regulators or the market. | Active investigations, publications, allegations |
| Q5.3 | Are there vendor payment or supply chain stress signals? | Vendor payment delays = cash flow stress signal. Often visible before financial statements reveal it. | Payment delay indicators |

**Total: 5 areas, 25 questions**
**Existing checks:** 59 (FWRD.EVENT.* + FWRD.WARN employee/customer/media + FWRD.MACRO.*)

---

# SUMMARY: ALL SECTIONS

| Section | Areas | Questions | Existing Checks | Key Data Sources |
|---|---|---|---|---|
| **COMPANY** | 7 | 31 | 44 | SEC filings, yfinance, LLM extraction |
| **FINANCIAL** | 8 | 36 | 65 | XBRL, 10-K/10-Q, computed models |
| **GOVERNANCE** | 6 | 33 | 83 | DEF 14A, Form 4, 8-K, ISS/GL |
| **LITIGATION** | 8 | 31 | 56 | Stanford SCAC, CourtListener, SEC, news |
| **MARKET** | 7 | 27 | 35 | yfinance, market data, FINRA |
| **DISCLOSURE** | 5 | 19 | 30 | NLP on filings, year-over-year diffs |
| **FORWARD** | 5 | 25 | 59 | Alternative data, event calendars, web search |
| **TOTAL** | **46** | **202** | **372*** | |

*372 = 388 original - 5 retired - 11 cross-section duplicates resolved in reclassification

---

## Brain Organization Implications

Each **section** maps to a brain knowledge domain. Each **area** maps to a brain topic cluster. Each **question** maps to one or more brain checks.

The brain schema supports:
- `section` → top-level grouping (7 sections)
- `area` → topic cluster within section (46 areas)
- `question_id` → the underwriter question this check answers (202 questions)
- `check_id` → specific evaluation (372+ checks)

This creates a hierarchy: **Section → Area → Question → Check(s)**

A check can answer multiple questions (many-to-many), but each check has a primary question assignment. Questions without any check = gaps. Checks without any question = orphans to retire.

---

## Next Steps

1. **User review** — Confirm questions are right and in right sections
2. **Step 4 per section** — Map existing 372 checks to the 202 questions (identify orphans and gaps)
3. **Steps 2-3 per section** — Full ACQUIRE/ANALYZE/DISPLAY for each question (like COMPANY-SECTION-DESIGN.md)
4. **Step 5** — Consolidation and gap closure across all sections
5. **Step 6** — Implementation plan for the full brain redesign
