# Paper Index — Legalize Exposure Engine

> **RULE: Read the papers marked 🔴 before building any new module.**
> Section-by-section math notes are in `docs/papers/`.
>
> **Additional analysis files:**
> - [09 — Validation framework](papers/09-validation-framework.md) (4-tier pyramid, what top journals require)
> - [10 — Blind spots](papers/10-blind-spots-unasked-questions.md) (SEC liability, moat, customer validation, scale, ethics)
> - [11 — Practical studies](papers/11-practical-studies-we-can-do.md) (9 studies replicable with our data)
> - [12 — ICSE rejection reasons](papers/12-icse-rejection-reasons.md) (evaluation gaps, novelty, scope)
> - [13 — Attack/defense report](papers/13-attack-defense-report.md) (10 attacks at 8/10 contentiousness)

---

## 🔴 MUST READ (blocks implementation)

| # | Paper | Year | Why | Notes | PDF/URL |
|---|-------|------|-----|-------|---------|
| 1 | **Goldsmith-Pinkham & Lyu** — Causal Inference in Financial Event Studies | 2025 | Our event_study.py is biased. Synthetic control is the fix. | [notes](papers/01-goldsmith-pinkham-2025-synthetic-control.md) | [arXiv PDF](https://arxiv.org/pdf/2511.15123) |
| 2 | **Baker, Bloom & Davis** — Measuring Economic Policy Uncertainty | 2016 | Continuous regulation uncertainty index > discrete events | [notes](papers/02-baker-bloom-davis-2016-epu.md) | [QJE](https://academic.oup.com/qje/article/131/4/1593/2468873) · [NBER](https://www.nber.org/papers/w21633) |
| 3 | **Kalmenovitz** — Regulatory Intensity and Firm-Specific Exposure | 2023 | Firm-level mapping via 10-K text similarity > NAICS-level | [notes](papers/05-kalmenovitz-2023-firm-exposure.md) | [RFS](https://academic.oup.com/rfs/article-abstract/36/8/3311/6972785) · [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3451344) |
| 4 | **Brav & Heaton** — Event Studies: Low Power, Confounding, Bias | 2015 | 🔴 ADVERSARIAL: event studies are fundamentally unreliable | [notes](papers/04-adversarial-counter-evidence.md) | [WashU Law](https://openscholarship.wustl.edu/law_lawreview/vol93/iss2/15/) |
| 5 | **Bae, Jo & Shim** — EPU Index Replication Failure | 2025 | 🔴 ADVERSARIAL: EPU loses significance 2008-2019 | [notes](papers/04-adversarial-counter-evidence.md) | [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/caje.12757) |

---

## 📙 SHOULD READ (informs design)

| # | Paper | Year | Why | PDF/URL |
|---|-------|------|-----|---------|
| 6 | **Hassan, Hollander, van Lent & Tahoun** — Firm-Level Political Risk | 2019 | Earnings call text → firm-level political risk | [QJE](https://academic.oup.com/qje/article-abstract/134/4/2135/5531768) · [Data](https://www.firmlevelrisk.com/download) |
| 7 | **Al-Ubaydli & McLaughlin** — RegData | 2017 | Regulation → NAICS ML classifier (our predecessor) | [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/rego.12107) · [Mercatus](https://www.mercatus.org/research/working-papers/regdata) |
| 8 | **Armstrong, Glaeser & Hoopes** — Measuring Firm Exposure to Gov Agencies | 2025 | Simple dictionary ≈ GPT for measuring regulatory exposure | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4428258) |
| 9 | **MacKinlay** — Event Studies in Economics and Finance | 1997 | Event study methodology bible (baseline, know before replacing) | [JEL](https://www.jstor.org/stable/2729691) |
| 10 | **Ramelli, Wagner, Zeckhauser & Ziegler** — Climate Elections | 2021 | Opposite regulatory shocks → opposite returns (strongest causal design) | [RCFS](https://academic.oup.com/rcfs/article-abstract/10/4/748/6303621) |

---

## 📘 REFERENCE (cite when needed)

### Impact / Causal Evidence
| Paper | Year | Method | URL |
|-------|------|--------|-----|
| Krieger et al. — FDA Relabeling Effects | 2020 | DiD | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0048733320302018) |
| Chen & Liu — Environmental Regulation China | 2023 | DiD | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1059056023003015) |
| Gutierrez & Teshima — Carbon Disclosure Impact | 2024 | IV-DiD | [MDPI](https://www.mdpi.com/2227-7072/13/2/98) |
| Chan — UK Mini-Budget Synthetic Control | 2024 | Synth Control | [MDPI](https://www.mdpi.com/2227-7390/12/20/3301) |
| Kordas & Savva — Brexit Synthetic Control | 2020 | Synth Control | [Springer](https://link.springer.com/article/10.1007/s10663-020-09481-7) |
| Dodd-Frank studies (Bongaerts et al.) | 2016 | Multi-event | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0378426616300218) |
| FDA Fast Track Designation | 2023 | Event study | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1359644623002878) |
| Karpoff, Lott & Wehrly — Environmental Penalties | 2005 | Event study | [UChicago](https://www.journals.uchicago.edu/doi/abs/10.1086/430806) |
| Wang, Tang & Li — Registration Reform DML | 2025 | Double ML | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0275531924004616) |
| Abadie, Diamond, Hainmueller — Synthetic Control | 2010 | Method | [JASA](https://www.tandfonline.com/doi/abs/10.1198/jasa.2009.ap08746) |
| Kou et al. — Causal Inference Survey | 2024 | Survey | [ACM](https://dl.acm.org/doi/10.1145/3736752) |

### Adversarial / Counter-Evidence
| Paper | Year | Threat | URL |
|-------|------|--------|-----|
| Binder — Event Study Since 1969 | 1998 | Anticipation problem | [Springer](https://link.springer.com/article/10.1023/A:1008295500105) |
| Kothari & Warner — Econometrics of Event Studies | 2007 | Long-horizon failure | [BU](https://www.bu.edu/econ/files/2011/01/KothariWarner2.pdf) |
| Shapiro — Counting Regulations | 2024 | Text ≠ burden | [Nature](https://www.nature.com/articles/s41599-024-03982-7) |
| Christensen, Hail & Leuz — Securities Regulation | 2016 | Enforcement context | [RFS](https://academic.oup.com/rfs/article-abstract/29/11/2885/2583718) |
| Igan, Mishra & Tressel — Lobbying Reverse Causality | 2012 | Selection bias | [UChicago](https://www.journals.uchicago.edu/doi/full/10.1086/663992) |
| Loughran & McDonald — Text Analysis Survey | 2016 | Text imprecision | [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/1475-679X.12123) |
| Kengmegni — NLP Prediction Fails OOS | 2025 | Overfitting | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5086825) |
| de Chaisemartin — Staggered DiD Bias | 2024 | TWFE estimator | [RES](https://academic.oup.com/restud/article/91/6/3253/7601390) |

### Methodology / Foundation
| Paper | Year | Topic | URL |
|-------|------|-------|-----|
| Pastor & Veronesi — Government Policy Uncertainty | 2012 | Theory model | [JFE](https://doi.org/10.1086/663992) |
| Stigler — Theory of Economic Regulation | 1971 | Foundational | Classic |
| Gentzkow, Kelly & Taddy — Text as Data | 2019 | NLP survey | [JEL](https://doi.org/10.1257/jel.20181020) |
| Cohen, Diether & Malloy — Lobbying → Returns | 2013 | Lobbying alpha | [JFE](https://doi.org/10.1016/j.jfineco.2013.02.002) |

---

## Data Sources (from papers)

| Source | What | URL |
|--------|------|-----|
| EPU Index | Policy uncertainty time series | https://www.policyuncertainty.com |
| EPU on FRED | Daily EPU | https://fred.stlouisfed.org/series/USEPUINDXD |
| Firm-Level Political Risk | Earnings call risk measures | https://www.firmlevelrisk.com/download |
| RegData 5.0 | Regulation → NAICS classifier | [User Guide](https://quantgov-documentation.s3.amazonaws.com/regdata_5_0_user_guide.pdf) |
| BEACON (Census) | NAICS classifier from text | https://github.com/uscensusbureau/BEACON |
