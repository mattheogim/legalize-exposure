# Adversarial Papers: Counter-Evidence Against Regulation→Market Mapping

> **MUST READ — These papers challenge the foundations of our project.
> Know these arguments before anyone else raises them.**

---

## DEVASTATING (Foundation-Shaking)

### 1. Brav & Heaton (2015) — Event Studies Are Underpowered and Biased
"Event Studies in Securities Litigation: Low Power, Confounding Effects, and Bias"
*Washington University Law Review* 93(2)
URL: https://openscholarship.wustl.edu/law_lawreview/vol93/iss2/15/

**Argument:** Single-firm event studies:
- **Low power** → miss real effects unless enormous
- **Confounding** → inflate detected effects (other news same day)
- **Together** → systematic upward bias in detected impacts

**Our response needed:** Use multi-firm aggregation (sector-level, not single-firm).
Use synthetic control (Goldsmith-Pinkham) instead of standard event study.

---

### 2. Bae, Jo & Shim (2025) — EPU Index Fails Outside Crises
"Does Economic Policy Uncertainty Differ from Other Uncertainty Measures?"
*Canadian Journal of Economics* 58(1): 40-74
URL: https://onlinelibrary.wiley.com/doi/10.1111/caje.12757

**Argument:** EPU index loses significance for 2008-2019 period.
Only works when COVID included. VIX and forecast disagreement
remain significant → EPU captures crises, not normal policy uncertainty.

**Our response needed:** Don't rely solely on EPU-style index.
Combine with direct regulatory text analysis + firm-level measures.
Test our agency-specific index across subperiods.

---

## SEVERE (Methodology-Challenging)

### 3. Binder (1998) — Anticipation Makes Event Windows Unknowable
"The Event Study Methodology Since 1969"
*Review of Quantitative Finance and Accounting* 11: 111-137
URL: https://link.springer.com/article/10.1023/A:1008295500105

**Argument:** Regulatory events are anticipated over prolonged legislative
periods. Market prices regulation in gradually. Clean event windows
don't exist for regulation.

**Our response needed:** Track the FULL event sequence (proposed → comment →
final → effective). Use continuous exposure measure, not single-date events.
This is already in our DESIGN_PRINCIPLES (priced-in problem acknowledged).

---

### 4. Kothari & Warner (2007) — Long-Horizon Event Studies Fail
"Econometrics of Event Studies"
*Handbook of Empirical Corporate Finance*
URL: https://www.bu.edu/econ/files/2011/01/KothariWarner2.pdf

**Argument:** Long-horizon event studies have low power and severe
misspecification. Cross-correlation among event-firm returns causes
false rejections.

**Our response needed:** Short windows [-1, +1] for discrete events.
Synthetic control for longer horizons. Sector-level cross-correlation
must be accounted for in test statistics.

---

### 5. Shapiro (2024) — Text-Based Regulation Measurement Is Unreliable
"Counting Regulations: A Call for Nuance"
*Humanities and Social Sciences Communications* (Nature)
URL: https://www.nature.com/articles/s41599-024-03982-7

**Argument:** Word counts, page counts, "shall/must/prohibited" counts
all fail to capture actual regulatory burden. A "must" requiring ships
to float ≠ a "must" requiring $1M license. Text ≠ enforcement.

**Our response needed:** Our mapping uses AGENCY → INDUSTRY rules
(not word counting). Supplement with firm-level 10-K analysis
(Kalmenovitz approach). Acknowledge enforcement gap in docs.

---

### 6. Christensen, Hail & Leuz (2016) — Effects Depend on Enforcement
"Capital-Market Effects of Securities Regulation"
*Review of Financial Studies* 29(11): 2885-2924
URL: https://academic.oup.com/rfs/article-abstract/29/11/2885/2583718

**Argument:** Regulation effects vary enormously by enforcement quality
and prior institutional conditions. No stable "regulation → outcome"
relationship exists without conditioning on context.

**Our response needed:** Start with US only (single enforcement regime).
When expanding internationally, MUST account for enforcement differences.

---

### 7. Igan, Mishra & Tressel (2012) — Reverse Causality
"A Fistful of Dollars: Lobbying and the Financial Crisis"
*NBER Macroeconomics Annual* 26
URL: https://www.journals.uchicago.edu/doi/full/10.1086/663992

**Argument:** Firms that face regulation are ALREADY different.
They lobby because they're risky, not the other way around.
Regulation exposure correlates with pre-existing characteristics.

**Our response needed:** Use DiD with pre-treatment parallel trends
verification. Control for pre-existing firm characteristics.
This is why we need Kalmenovitz-style firm-level matching.

---

## MODERATE (Important Caveats)

### 8. CEPR/VoxEU — Markets Ignore Policy Uncertainty for Years
"Explaining the Puzzle of High Policy Uncertainty and Low Market Volatility"
URL: https://cepr.org/voxeu/columns/explaining-puzzle-high-policy-uncertainty-and-low-market-volatility

**Argument:** High EPU + low VIX for extended periods (Brexit, Trump era).
Markets rationally ignore regulatory noise when signal-to-noise is low.

---

### 9. Kengmegni (2025) — NLP Return Prediction Fails Out of Sample
"Limitations of News Sentiment Analysis in Short-term Stock Return Prediction"
SSRN Working Paper
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5086825

**Argument:** Sentiment models overfit on price features.
Text signals don't generalize. Supports efficient market hypothesis.

---

### 10. Loughran & McDonald (2016) — Text Analysis Is Imprecise
"Textual Analysis in Accounting and Finance: A Survey"
*Journal of Accounting Research* 54(4)
URL: https://onlinelibrary.wiley.com/doi/abs/10.1111/1475-679X.12123

**Argument:** General sentiment dictionaries massively misclassify
financial text. 3/4 of "negative" words aren't negative in finance.

---

### 11. de Chaisemartin & D'Haultfoeuille (2024) — Staggered DiD Is Biased
"Revisiting Event-Study Designs"
*Review of Economic Studies* 91(6): 3253+
URL: https://academic.oup.com/restud/article/91/6/3253/7601390

**Argument:** Standard TWFE estimators fail with heterogeneous treatment
effects and staggered adoption. Can get the SIGN wrong.

---

### 12. RCFS (2018) — Identification ≠ Causality
"Identification Is Not Causality, and Vice Versa"
*Review of Corporate Finance Studies* 7(1): 1+
URL: https://academic.oup.com/rcfs/article/7/1/1/4590088

**Argument:** Counterfactual "what if this regulation hadn't passed"
can never be validated. Structural models with strong assumptions required.

---

## Summary: The Three Biggest Threats

| Threat | Severity | Our Best Defense |
|--------|----------|-----------------|
| **Anticipation/priced-in** | DEVASTATING | Track full event sequence, continuous measures |
| **Low power + confounding** | DEVASTATING | Synthetic control, multi-firm aggregation |
| **EPU fails outside crises** | DEVASTATING | Combine multiple measures, test across subperiods |

### Honest Assessment

These papers don't say "regulation doesn't affect markets" — they say
"measuring that effect is much harder than event studies suggest."

Our project is defensible IF we:
1. Use synthetic control instead of standard event study
2. Track continuous exposure, not just discrete events
3. Show the mapping WITHOUT causal claims (exposure, not impact)
4. Add causal evidence only where design permits (DiD, opposite shocks)
5. Acknowledge limitations prominently in the product
