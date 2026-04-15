# Hassan, Hollander, van Lent & Tahoun (2019): Firm-Level Political Risk

> **Quarterly political risk measure from earnings calls — directly aggregable to ETF level**
> QJE 134(4): 2135-2202
> Data: https://www.firmlevelrisk.com/download
> Code: https://github.com/mschwedeler/firmlevelrisk

## Core PRisk Formula

```
PRisk_{i,t} = (1/B_{i,t}) × Σ_{b∈P} [count(b within 10 words of r)_{i,t} × tf_b]
```

Where:
- i = firm, t = quarter
- b = bigram from political bigram set P
- r = risk/uncertainty synonym
- B_{i,t} = total bigrams in transcript (normalization)
- tf_b = term-frequency weight (political association strength)

## Construction Steps

**Step 1:** Build political vs non-political bigram libraries
- Political: poli-sci textbook + political newspaper sections
- Non-political: accounting textbook + non-political sections

**Step 2:** Score each bigram
```
Score_P(b) = tf(b, P_train) / tf(b, NP_train)
```

**Step 3:** In each earnings call transcript, find risk synonyms.
Count political bigrams within 10-word window of each risk word.

**Step 4:** Normalize by transcript length.

## 8 Topic-Specific Sub-Measures
1. Economic Policy & Budget
2. Environment
3. Trade
4. Institutions & Political Process
5. Health
6. Security & Defense
7. Tax Policy
8. Technology & Infrastructure

```
PRisk^k_{i,t} = (1/B_{i,t}) × Σ_{b∈P^k} [count(b within 10 words of r)_{i,t} × tf_b^k]
```

## Key Regressions

**Investment:**
```
CapEx_{i,t+1}/Assets_{i,t} = α + β₁×PRisk_{i,t} + β₂×NPRisk_{i,t} + Controls + FE + ε
```
β₁ negative: higher political risk → less investment

**Volatility:**
```
StockVol_{i,t} = α + β₁×PRisk_{i,t} + Controls + FE + ε
```
β₁ positive: higher political risk → higher stock volatility

## Implications for Us
- Aggregate PRisk to ETF level: Σ(weight_j × PRisk_j) over ETF holdings
- Use 8 topic sub-indices to match regulatory domains
- Quarterly frequency — complements our daily FR tracking
- Data publicly available at firmlevelrisk.com
