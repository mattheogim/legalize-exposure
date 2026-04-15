# Mapping Validation Report

Total: 100 | Mapped: 100 | Failed: 0

## Aggregate Metrics

| Metric | Industry (NAICS 3-digit) | ETF |
|--------|:---:|:---:|
| Precision | 0.690 | 0.813 |
| Recall | 0.845 | 0.851 |
| **F1** | **0.733** | **0.817** |

Industry F1 target (>0.7): **PASS** (0.733)
ETF F1 target (>0.6): **PASS** (0.817)

## Top Industry False Positives (predicted but not in ground truth)

- NAICS 488: 22 times
- NAICS 518: 12 times
- NAICS 113: 11 times
- NAICS 541: 9 times
- NAICS 115: 8 times
- NAICS 331: 8 times
- NAICS 517: 8 times
- NAICS 334: 7 times
- NAICS 332: 4 times
- NAICS 623: 4 times

## Top Industry False Negatives (in ground truth but not predicted)

- NAICS 112: 8 times
- NAICS 311: 4 times
- NAICS 211: 3 times
- NAICS 336: 3 times
- NAICS 523: 3 times
- NAICS 325: 3 times
- NAICS 522: 3 times
- NAICS 481: 3 times
- NAICS 928: 2 times
- NAICS 339: 2 times

## Top ETF False Positives

- XLC: 12 times
- XME: 11 times
- XLB: 11 times
- LIT: 10 times
- ICLN: 10 times
- XLK: 10 times
- HACK: 10 times
- TAN: 10 times
- CIBR: 10 times
- PHO: 9 times

## Top ETF False Negatives

- MOO: 11 times
- JETS: 6 times
- LIT: 4 times
- OIH: 3 times
- XOP: 3 times
- XLB: 3 times
- PHO: 3 times
- XLP: 3 times
- IHI: 3 times
- XLF: 3 times
