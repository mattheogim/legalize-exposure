# Al-Ubaydli & McLaughlin (2017): RegData — Regulation→Industry Mapping

> **Our direct predecessor — regulation text → NAICS classification at scale**
> Regulation & Governance 11(1): 109-123
> Data: https://www.quantgov.org
> User Guide v5.0: https://quantgov-documentation.s3.amazonaws.com/regdata_5_0_user_guide.pdf

## Core Formula

```
IndustryRelevantRestrictions_{i,t} = Σ_j [Restrictions_j × Pr(Industry_i | Document_j)]
```

Where:
- i = NAICS industry (2-6 digit)
- j = regulatory document (CFR part/section)
- t = year

## Restriction Counting
```
Restrictions_j = Count({"shall", "must", "may not", "required", "prohibited"} in doc j)
```

## Industry Relevance (ML Classifier)

**v1.0-2.0 (keyword-based):**
```
Relevance_{i,j} = f(keyword_matches(IndustryName_i, Text_j))
```

**v2.1+ (ML — logistic regression):**
```
Pr(Industry_i | Document_j) = 1 / (1 + exp(-w^T × x_j))
```
Where x_j = bigram count vector of document j

**Training data:** Federal Register publications that explicitly name NAICS codes.

## Evolution
- v1.0-2.0: Human-specified keywords
- v2.1+: Supervised ML (logit + random forests)
- v5.0 (2023): Updated models, extended coverage to 2023+

## Limitations (IMPORTANT)
- "shall" requiring ships to float = "shall" requiring $1M license (both count as 1)
- NAICS may not match how firms experience regulation
- Binary relevant/not — no degree of relevance
- Federal only, misses state/local
- Text ≠ enforcement

## For Us: Baseline + Upgrade Path
1. Use RegData as industry-level baseline
2. Layer Kalmenovitz (firm-specific) on top
3. Layer Armstrong (agency-specific) on top
4. Aggregate to ETF via holdings weights
