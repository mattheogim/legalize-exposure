# Baker, Bloom & Davis (2016): Measuring Economic Policy Uncertainty

> **MUST READ — Regulation-specific uncertainty sub-index directly applicable**
> QJE 131(4): 1593-1636
> Data: https://www.policyuncertainty.com
> FRED: https://fred.stlouisfed.org/series/USEPUINDXD

## Why This Paper Matters

Constructs a continuous index of policy uncertainty from newspaper text.
We could build a **regulation-specific uncertainty index** for each agency/sector
using the same methodology instead of discrete event studies.

---

## 1. EPU Index Construction

**Composite:**
```
EPU_t = (1/3) × News_t + (1/3) × Tax_t + (1/3) × CPI_Disagreement_t
```

### News Component (most novel)

**Step 1:** Count articles containing ALL THREE categories:
- E: "economic" OR "economy"
- P: "congress" OR "deficit" OR "Federal Reserve" OR "legislation" OR "regulation" OR "White House"
- U: "uncertainty" OR "uncertain"

**Step 2:** Normalize per newspaper:
```
e_{i,t} = X_{i,t} / TotalArticles_{i,t}
```

**Step 3:** Standardize:
```
z_{i,t} = e_{i,t} / σ_i
```

**Step 4:** Average across N newspapers:
```
EPU_news_t = (1/N) × Σ_i z_{i,t}
```

**Step 5:** Rescale to mean 100 over baseline (1985-2009):
```
EPU_news_final_t = k × EPU_news_t
```

### Tax Component
```
Tax_t = Σ_p |DollarImpact_p|  (provisions expiring within window)
```

### Disagreement Component
```
Disagreement_CPI_t = P75(CPI forecast) - P25(CPI forecast)
```
From Survey of Professional Forecasters.

---

## 2. Category-Specific Sub-Indices

**KEY FOR US: Regulation-Specific EPU**

Search terms (E + U + category):
- "regulation" OR "regulatory" OR "deregulation"
- "EPA" OR "SEC" OR "CFTC" OR "FCC" OR "FDIC" OR "FTC"

**Financial Regulation sub-index:**
- "banking supervision" OR "Glass-Steagall" OR "Dodd-Frank" OR "Basel"
- "bank regulation" OR "financial regulation" OR "Volcker rule"
- "stress test" OR "capital requirement"

**We can build agency-specific sub-indices by modifying search terms.**

---

## 3. Validation: 12,000-Article Human Audit

- Hired auditors to read 12,000 articles flagged by the algorithm
- Each classified as truly EPU (1) or false positive (0)
- **Correlation automated vs human: ~0.86 monthly**
- Regression: HumanEPU_t = α + β × AutomatedEPU_t, R² ≈ 0.75

---

## 4. VAR Model

**Specification:**
```
Y_t = [ln(S&P500), EPU, FedFundsRate, ln(Employment), ln(IndustrialProduction)]
Y_t = A_0 + A_1·Y_{t-1} + ... + A_p·Y_{t-p} + e_t
```

**Cholesky ordering:** S&P500 → EPU → FFR → Employment → IP

**Results (1σ EPU shock):**
- Industrial production: -0.5% to -1.0% peak at 4-6 months
- Employment: -0.3% to -0.5%
- S&P 500: decline (partially by construction)

---

## 5. Firm-Level Regressions

```
Investment_{j,t}/Capital_{j,t-1} = α_j + β₁·EPU_t + β₂·EPU_t × PolicyExposure_j + γ·X_{j,t} + δ_t + ε_{j,t}
```

**β₂ negative and significant:** High policy-exposure firms cut investment more when EPU rises.

```
EquityVol_{j,t} = α_j + β₁·EPU_t + β₂·EPU_t × PolicyExposure_j + γ·X_{j,t} + δ_t + ε_{j,t}
```

**β₂ positive and significant:** High policy-exposure firms see larger volatility increase.

---

## 6. Implications for Our Project

1. Build **agency-specific regulatory uncertainty index** from Federal Register text
2. Use as CONTINUOUS measure instead of discrete events
3. Cross-validate with category-specific EPU from policyuncertainty.com
4. Test: does our agency-specific index predict sector ETF volatility?

### CAVEAT (Bae, Jo & Shim 2025 replication)
EPU loses significance for 2008-2019 period. Only works during crises + COVID.
Our agency-specific index may have the same problem.
