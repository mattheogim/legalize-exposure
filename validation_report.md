# Mapping Validation Report

Total: 100 | Mapped: 100 | Failed: 0

## Aggregate Metrics

| Metric | Industry (NAICS 3-digit) | ETF |
|--------|:---:|:---:|
| Precision | 0.640 | 0.756 |
| Recall | 0.821 | 0.798 |
| **F1** | **0.685** | **0.764** |

Industry F1 target (>0.7): **FAIL** (0.685)
ETF F1 target (>0.6): **PASS** (0.764)

## Top Industry False Positives (predicted but not in ground truth)

- NAICS 483: 25 times
- NAICS 484: 22 times
- NAICS 482: 22 times
- NAICS 113: 11 times
- NAICS 518: 10 times
- NAICS 541: 9 times
- NAICS 115: 8 times
- NAICS 517: 8 times
- NAICS 331: 8 times
- NAICS 334: 7 times

## Top Industry False Negatives (in ground truth but not predicted)

- NAICS 114: 8 times
- NAICS 112: 8 times
- NAICS 325: 4 times
- NAICS 311: 4 times
- NAICS 211: 3 times
- NAICS 336: 3 times
- NAICS 523: 3 times
- NAICS 522: 3 times
- NAICS 928: 2 times
- NAICS 339: 2 times

## Top ETF False Positives

- LIT: 30 times
- XLY: 25 times
- XME: 10 times
- XLB: 10 times
- CIBR: 10 times
- ICLN: 10 times
- XLC: 10 times
- XLK: 10 times
- HACK: 10 times
- TAN: 10 times

## Top ETF False Negatives

- ITA: 23 times
- MOO: 11 times
- LIT: 5 times
- XLB: 4 times
- PHO: 4 times
- XLP: 4 times
- OIH: 3 times
- XOP: 3 times
- JETS: 3 times
- IHI: 3 times
