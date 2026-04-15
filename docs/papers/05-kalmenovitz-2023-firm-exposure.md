# Kalmenovitz (2023): Regulatory Intensity and Firm-Specific Exposure

> **MUST READ — Shows how to map regulations to INDIVIDUAL FIRMS, not just industries**
> RFS 36(8): 3311-3347
> SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3451344

## Why This Paper Matters

Our current approach: Regulation → NAICS industry → ETF (coarse)
This paper's approach: Regulation text ↔ 10-K text → individual firm (granular)

---

## Core Method: RegIn (Regulatory Intensity)

### Step 1: Feature Construction
```
Feature_vector(f, r) = TF-overlap(Text_10K_f, Text_83I_r)
```
Compute vocabulary overlap between firm f's 10-K Item 1 (business description) and regulation r's Form 83-I description.

### Step 2: Supervised ML Classification
```
Relevant(f, r) ∈ {0, 1}
```
Trained on hand-labeled set for each company — small set of regulations split between relevant/irrelevant.

### Step 3: Four RegIn Measures

**Number of active regulations:**
```
RegIn_Reg_{f,t} = Σ_r [Relevant(f,r) × Active(r,t)]
```

**Compliance responses:**
```
RegIn_Resp_{f,t} = Σ_r [Relevant(f,r) × Active(r,t) × Responses(r,t)]
```

**Hours spent:**
```
RegIn_Time_{f,t} = Σ_r [Relevant(f,r) × Active(r,t) × Hours(r,t)]
```

**Dollar cost:**
```
RegIn_Dollar_{f,t} = Σ_r [Relevant(f,r) × Active(r,t) × DollarCost(r,t)]
```

### Regression:
```
Y_{f,t} = α + β × RegIn_{f,t} + γ × X_{f,t} + FE_firm + FE_year + ε_{f,t}
```

## Key Results
- RegIn increases COGS and SG&A (compliance costs)
- Reduces CapEx and employment
- Increases lobbying expenditures
- Effects strongest for financially constrained firms

## Data Sources
- Form 83-I filings from Federal Register (1980-2020)
- 10-K annual filings from SEC EDGAR
- Compustat for financials

## Implications for Us
**Replace NAICS-level mapping with firm-level:**
1. For each regulation, compute text similarity with each firm's 10-K
2. Weight by ETF holdings to get ETF-level exposure
3. Much more accurate than Agency → NAICS → ETF
