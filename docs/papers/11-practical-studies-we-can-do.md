# Practical Studies We Can Do With Our Data

> **Our biggest edge: Git History of legislation. Nobody else has version-controlled diffs.**

---

## Tier 1: Highest Impact, Directly Achievable

### Study 1: Regulatory Intensity → ETF Returns (Kalmenovitz 2023 Extension)

**Original:** Kalmenovitz (2023) RFS 36(8):3311 — measured regulatory intensity at industry level
**Our extension:** Push to ETF level + add git-diff dimension (rate of CHANGE in regulation)
**Data needed:** Federal Register API ✅, NAICS→ETF mapping ✅, Yahoo Finance ✅
**Novel contribution:** First study to use legislation version diffs for regulatory intensity measurement
**URL:** https://academic.oup.com/rfs/article-abstract/36/8/3311/6972785

### Study 2: Proposed Rule → Market Reaction (Lee 2019 Empirical Version)

**Original:** Lee (2019) Harvard Law — THEORETICAL proposal that agencies should use event studies
**Our extension:** PRODUCE the empirical evidence his paper calls for
**Data needed:** FR API (proposed+final rules) ✅, event study engine ✅, contamination scoring ✅
**Novel contribution:** First systematic event study across ALL proposed rules (not cherry-picked)
**URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3434194

### Study 3: "RegData with Diffs" Dataset

**Original:** Al-Ubaydli & McLaughlin (2017) — annual snapshots of restriction counts
**Our extension:** Commit-level (daily) granularity from git history
**Data needed:** US Code 59,765 sections as Markdown ✅, git log ✅
**Novel contribution:** Citable dataset — first daily-resolution regulation change database
**URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/rego.12107

---

## Tier 2: Strong Extensions

### Study 4: Legislative Text Diffs → Stock Returns (Cohen 2013 Extension)

**Original:** Cohen, Diether, Malloy (2013) JFE 110(3):574 — used Congressional votes only
**Our extension:** Add WHAT actually changed in the law (US Code diffs)
**Data needed:** Congress.gov API ✅, US Code git history ✅, ETF data ✅
**Novel contribution:** First to combine voting signals with actual legal text changes
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X13002262

### Study 5: Regulatory Activity Index vs EPU (Baker-Bloom-Davis 2016 Alternative)

**Original:** BBD (2016) QJE — newspaper proxy for policy uncertainty
**Our extension:** Direct measurement from Federal Register volume + US Code change rate
**Data needed:** FR API ✅, US Code git ✅, MacroEvent calendar ✅
**Novel contribution:** Source-data index vs newspaper-proxy index — which predicts ETF returns better?
**URL:** https://academic.oup.com/qje/article-abstract/131/4/1593/2468873

### Study 6: Regulatory Fragmentation Changes → ETF (Kalmenovitz et al. 2025)

**Original:** Kalmenovitz, Lowry, Volkova (2025) JoF 80(2) — static fragmentation
**Our extension:** Fragmentation CHANGES over time via git diffs
**Data needed:** Agency→NAICS mapping ✅, FR API ✅, ETF data ✅
**URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13423

### Study 7: Regulatory Comovement (JBF 2023)

**Original:** JBF 2023 — regulation → stock return comovement
**Our extension:** ETF-level + Canada cross-country
**Data needed:** US Code ✅, Canada 956 acts ✅, ETFs ✅
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S0927539823000646

---

## Tier 3: Solid But More Effort

### Study 8: Cumulative Cost of Regulation Update (Coffey et al. 2020)

**Original:** Review of Economic Dynamics — regulation slows GDP by ~0.8%/year
**Our extension:** Extend from 2012 to 2025+ using current US Code data
**URL:** https://www.sciencedirect.com/science/article/abs/pii/S1094202520300223

### Study 9: Restriction Word Momentum Factor (Novel)

**Original concept from:** "Price of Regulations" (2024) RAPS 14(3):381
**Our idea:** Sort industries by RATE OF CHANGE of restriction words → test as a priced factor
**Data needed:** US Code git diffs ✅, ETF returns ✅
**Novel:** Nobody has tested a "regulatory momentum" factor
**URL:** https://academic.oup.com/raps/article/14/3/381/7515258
