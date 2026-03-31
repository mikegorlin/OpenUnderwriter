# Trading Volume and D&O Damages: The Connection

## Key Finding from Brattle Group Research

**Source**: "Securities Class Actions: Trading Models to Estimate Individual Investor Trading Activity and Aggregate Damages"  
**Authors**: Ioannis Gkatzimas, Yingzhen Li, Torben Voetmann (The Brattle Group, Inc.)

### Critical Insight

**Trading volume is used to CALCULATE damages, NOT to PREDICT litigation risk.**

From the Brattle paper (page 1):

> "In securities class action lawsuits, the amount of aggregate damages defendants may face is of interest to all parties involved in litigation. Both plaintiffs and defendants have traditionally relied on **trading models** as a tool to assess defendants' liability."

> "As the overwhelming majority of securities class action cases lack access to individual investor trading data, parties must estimate aggregate damages. Litigants have been using **trading models to estimate damages** in securities litigation for more than two decades. A trading model incorporates assumptions about investors' trading patterns and simulates the trading activity of market participants using a variety of simplifying assumptions. The aggregate damages estimate based on a trading model can oftentimes drive the course of the litigation."

### What This Means

**Trading Volume → Damages Calculation**:
1. Trading volume during the "class period" (when fraud allegedly occurred) determines the SIZE of the plaintiff class
2. More shares traded = more potential damages
3. Damages formula: **Artificial inflation per share × Number of shares traded during class period**

**Therefore**:
- **HIGH trading volume** during a fraud period → **HIGHER potential damages** (if litigation occurs)
- **LOW trading volume** during a fraud period → **LOWER potential damages** (if litigation occurs)

### The Two-Step Relationship

```
Step 1: LITIGATION RISK (probability of being sued)
├── Predicted by: Stock decline, volatility, size, growth, industry
└── Trading volume: NOT a validated predictor

Step 2: DAMAGES SEVERITY (if sued, how much?)
├── Calculated using: Stock price decline × Trading volume during class period
└── Trading volume: DIRECT input to damages calculation
```

### Implication for D&O Underwriting

**High trading volume is a DOUBLE-EDGED SWORD**:

✅ **POSITIVE** (reduces litigation PROBABILITY):
- Better price discovery
- More efficient markets
- Less likely to have illiquid crashes

❌ **NEGATIVE** (increases damages SEVERITY if sued):
- Larger plaintiff class
- More shares damaged
- Higher settlement amounts

### Example Calculation

**Hypothetical Fraud Scenario**:
- Stock price artificially inflated by $10/share
- Class period: 180 days
- Average daily volume: 1,000,000 shares

**Damages Calculation**:
- Total shares traded during class period: 1,000,000 × 180 = 180M shares
- Artificial inflation: $10/share
- **Total damages**: 180M × $10 = **$1.8 billion**

**If volume were 100,000 shares/day instead**:
- Total shares traded: 100,000 × 180 = 18M shares
- **Total damages**: 18M × $10 = **$180 million** (90% lower!)

### Key Distinction

**Trading volume / shares outstanding** affects:
1. **Damages calculation** (if fraud occurs) ✅ VALIDATED
2. **Litigation probability** (whether fraud occurs) ❌ NOT VALIDATED

### Conclusion for Primoris

**Primoris has HIGH trading volume (1.85% of shares outstanding per day)**:

**Implication**:
- IF a securities fraud event occurred, the damages would be HIGHER due to high trading volume
- BUT high liquidity may REDUCE the probability of the triggering event (stock crash)

**Net Effect**: UNCLEAR without empirical data

**Proper Framing**:
- "High trading volume is a positive factor for market efficiency and price discovery"
- "However, in the event of securities litigation, high trading volume would result in larger damages calculations"
- "This is a standard characteristic of liquid stocks and is factored into D&O pricing"

### Recommendation

DO NOT claim that "high trading volume reduces D&O severity" - the opposite is true for damages calculation.

INSTEAD, note that:
1. High liquidity reduces illiquid decline risk (positive)
2. High volume increases potential damages if sued (negative)
3. Net effect depends on which factor dominates (requires actuarial modeling)
