# Impact Papers: Causal Evidence That Regulations Move Markets

> **READ THESE to build the case that regulation→market impact is real and measurable**

---

## Strongest Causal Evidence (by method)

### 1. Natural Experiment / Opposite Shocks

**Ramelli, Wagner, Zeckhauser & Ziegler (2021)**
"Investor Rewards to Climate Responsibility"
*Review of Corporate Finance Studies* 10(4): 748+
URL: https://academic.oup.com/rcfs/article-abstract/10/4/748/6303621

- Trump 2016 (anti-regulation) → carbon firms UP
- Biden 2020 (pro-regulation) → carbon firms DOWN
- **Opposite shocks → opposite reactions = strongest causal design**
- Effectively a natural experiment with built-in placebo test

### 2. Difference-in-Differences (DiD)

**Krieger et al. (2020)** — "Unpacking Effects of Adverse Regulatory Events"
*Research Policy*
URL: https://www.sciencedirect.com/science/article/abs/pii/S0048733320302018
- FDA safety relabeling → demand drops 16.9% within 2 years
- Market value loss: $569M-$882M per event
- DiD with cross-market controls

**Chen & Liu (2023)** — "Environmental Regulation and Stock Price Synchronicity"
*International Review of Economics & Finance* 88: 1513-1528
URL: https://www.sciencedirect.com/science/article/abs/pii/S1059056023003015
- China's Environmental Protection Law as quasi-natural experiment
- Treatment: high-polluting firms. Control: low-polluting firms
- Reduced stock price synchronicity (more firm-specific info priced in)

**Gutierrez & Teshima (2024)** — "Carbon Information Disclosure on Firm Value"
*International Journal of Financial Studies*
URL: https://www.mdpi.com/2227-7072/13/2/98
- IV-DiD: strongest causal design
- Chinese carbon disclosure mandate → increased firm value

### 3. Synthetic Control

**Chan (2024)** — "UK Mini-Budget Policy on Stock Market"
*Mathematics* 12(20): 3301
URL: https://www.mdpi.com/2227-7390/12/20/3301
- Synthetic FTSE100 from other countries' indices
- Isolates UK policy shock from global movements

**Kordas & Savva (2020)** — "Impact of the Brexit Vote on UK Financial Markets"
*Empirica*
URL: https://link.springer.com/article/10.1007/s10663-020-09481-7
- Synthetic control for Brexit referendum impact

### 4. Multi-Event Event Study

**Dodd-Frank studies (Bongaerts, Cremers, Goetzmann et al. 2016)**
*Journal of Banking & Finance*
URL: https://www.sciencedirect.com/science/article/abs/pii/S0378426616300218
- 18 legislative events tracked
- Cross-sectional regressions on firm size/risk/complexity
- Pattern of reactions across events rules out confounding

**FDA Fast Track Designation (2023)**
*Drug Discovery Today*
URL: https://www.sciencedirect.com/science/article/abs/pii/S1359644623002878
- CAARs: +21.59% (5 days), +38.34% (30 days), +111.37% (3 years)
- Discrete regulatory event, enormous effect size

### 5. Double Machine Learning

**Wang, Tang & Li (2025)** — "Registration Reform and Stock Mispricing"
*Research in International Business and Finance*
URL: https://www.sciencedirect.com/science/article/abs/pii/S0275531924004616
- DML handles high-dimensional confounders
- China's IPO reform → reduced mispricing

### 6. Enforcement / Penalty Events

**Karpoff, Lott & Wehrly (2005)** — "Reputational Penalties for Environmental Violations"
*Journal of Law and Economics* 48(2): 653-675
URL: https://www.journals.uchicago.edu/doi/abs/10.1086/430806
- Environmental enforcement → market value loss ≈ legal penalty
- No reputational penalty beyond direct cost (unlike fraud)

**Anderson & Hager (2024)** — "Regulatory Penalties on Bank Valuation"
*Journal of Financial Regulation and Compliance*
- Counterintuitive: positive returns on penalty day
- Penalty resolves uncertainty (smaller than feared)

---

## Methods That Prove Causation — Summary

| Method | Best For | Key Papers |
|--------|----------|------------|
| Opposite Shocks | Policy regime changes | Ramelli et al. 2021 |
| DiD | Sector-specific regulation | Krieger 2020, Chen 2023 |
| Synthetic Control | Market-level policy shocks | Chan 2024, Kordas 2020 |
| IV-DiD | Endogeneity concerns | Gutierrez 2024 |
| DML | High-dimensional confounders | Wang 2025 |
| Multi-Event | Legislative process | Dodd-Frank studies |

---

## Key Takeaway for Impact Extension

To move from "exposure" to "impact", we need:
1. **Identify regulation as treatment** (which firms/sectors affected)
2. **Construct counterfactual** (what would have happened without regulation)
3. **Method choice depends on setting:**
   - Single big regulation → Synthetic Control
   - Sector regulation with clear treatment/control → DiD
   - Regime change (new administration) → Opposite Shocks
   - Complex multi-factor → DML
