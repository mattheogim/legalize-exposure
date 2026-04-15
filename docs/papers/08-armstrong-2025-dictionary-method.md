# Armstrong, Glaeser & Hoopes (2025): Simple Dictionary ≈ GPT for Regulatory Exposure

> **Key finding: Simple methods work as well as LLMs**
> Journal of Accounting and Economics 79(1)
> Data: https://stephenglaeser.web.unc.edu/data/
> SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4428258

## Core Measure

```
AgencyExposure_{f,a,t} = Sentences mentioning agency_a in 10-K_{f,t} / Total sentences in 10-K_{f,t}
```

## Method
- Dictionary of terms per government agency (SEC, IRS, EPA, FDA, DOJ, etc.)
- Count sentences in 10-K that mention any agency term
- Normalize by document length

## Key Result

**Dictionary-based method vs GPT-3.5 Turbo → NO significant difference in predictive power**

Both predict:
- Undisclosed agency investigations
- SEC EDGAR download activity
- Firm profitability (negative relationship)

## Implication for Us

We DON'T need complex ML to measure agency exposure.
Simple keyword/dictionary approach on 10-K text is sufficient.
This validates our lookups.py agency→industry mapping approach.

## Validation
- Predicts undisclosed agency investigations (→ exposure is real)
- Varies with agency-specific events (Sarbanes-Oxley for SEC, budget cuts for IRS)
- Negative relation to profitability (regulatory exposure = cost)
