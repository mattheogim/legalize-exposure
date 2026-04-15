# Validation Framework: What Top Journals Require

> **MUST READ — This defines the minimum tests for credibility**

---

## The 4-Tier Pyramid (Academic Consensus)

### Tier 1: Identification (없으면 탈락)

| Test | What | Paper |
|------|------|-------|
| Causal design | DiD, SC, IV, or clean event study. Pure OLS not publishable for causal claims | Angrist & Pischke 2010 |
| Parallel trends | Pre-event coefficient plot + formal test | Borusyak et al. 2024 |
| Multi-window | Test [-1,0], [-1,+1], [-5,+5] at minimum | Kothari & Warner 2007 |

### Tier 2: Robustness (리뷰어가 기대)

| Test | What | Paper |
|------|------|-------|
| Alt models | CAPM + FF3 + FF5 전부에서 결과 유지 | Kothari & Warner 2007 |
| Placebo | 랜덤 날짜에 같은 분석 → 효과 없어야 | Eggers 2024 |
| Alt samples | outlier 제거, 산업별 분리 → 결과 안정 | Lu & White 2014 |
| Non-parametric | sign test, rank test, bootstrap | Bugni et al. 2023 |

### Tier 3: Credibility (Good → Great)

| Test | What | Why Important |
|------|------|---------------|
| **Dose-response** ★★★ | 노출도 높을수록 반응 강해야 | 단일 최강 인과 증거 |
| Out-of-sample | 다른 기간/나라/규제에서도 작동 | 일반화 |
| Confounding check | 이벤트 윈도우에 다른 이벤트 없는지 | ✅ contamination_score |
| Multiple testing | Bonferroni/BH correction 또는 t > 3.0 | Harvey et al. 2016 |

### Tier 4: Replication

| Test | What |
|------|------|
| Open code+data | RFS, JFE 필수 → ✅ 우리는 open source |
| Specification curve | 모든 합리적 선택에서 결과 보여주기 |

---

## Key Papers (Validation-Specific)

| Paper | Year | Journal | Why | URL |
|-------|------|---------|-----|-----|
| Angrist & Pischke — Credibility Revolution | 2010 | JEP | 인과 설계 없으면 불인정 | [AEA](https://www.aeaweb.org/articles?id=10.1257/jep.24.2.3) |
| Brodeur, Cook & Heyes — Methods Matter | 2020 | AER | p-hacking 실태, 25% IV/DiD 결과 의심 | [AER](https://www.aeaweb.org/articles?id=10.1257/aer.20190687) |
| Borusyak, Jaravel & Spiess — Robust Event Study | 2024 | RES | 현재 DiD/event study 표준 | [RES](https://academic.oup.com/restud/article/91/6/3253/7601390) |
| Lu & White — Robustness Tests | 2014 | JoE | Robustness check가 실제로 증명하는 것 | [JoE](https://www.sciencedirect.com/science/article/abs/pii/S0304407613001668) |
| Jensen, Kelly & Pedersen — Replication Crisis | 2023 | JoF | Finance replication 기준 | [JoF](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13249) |
| Fed SR 11-7 — Model Risk Management | 2011 | Fed | 모델 검증 규제 표준 (3 pillars) | [Fed](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm) |
| Harvey, Liu, Zhu — Multiple Testing | 2016 | RFS | t > 3.0 threshold | [RFS](https://academic.oup.com/rfs/article/29/1/5/1843824) |
| Bailey et al. — PBO | 2014 | SSRN | Backtest overfitting 수학적 증명 | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253) |
| Nosek et al. — Pre-registration | 2018 | PNAS | HARKing 방지 | [PNAS](https://www.pnas.org/doi/10.1073/pnas.1708274114) |

---

## Backtesting Bias 완전 목록 (12가지)

| # | Bias | 심각도 | 대응 |
|---|------|--------|------|
| 1 | Look-ahead | 치명 | Point-in-time DB, walk-forward |
| 2 | Selection | 치명 | Pre-registration, 전수 테스트 |
| 3 | Data snooping | 치명 | t > 3.0, specification curve |
| 4 | Overfitting | 치명 | CPCV, PBO metric |
| 5 | HARKing | 치명 | Pre-registration |
| 6 | Survivorship | 심각 | 상폐 종목 포함 (CRSP delisting) |
| 7 | Time-period | 심각 | 다중 기간 테스트 |
| 8 | Model misspec | 심각 | Synthetic control |
| 9 | Non-stationarity | 심각 | Structural break test |
| 10 | Transaction cost | 중간 | N/A (우리는 거래 안 함) |
| 11 | Market impact | 중간 | N/A |
| 12 | Benchmark | 중간 | Multi-benchmark |

## 우리에게 적용되는 것 / 안 되는 것

| Bias | 적용? | 이유 |
|------|-------|------|
| Look-ahead | ✅ 적용 | 과거 규제 결과를 알고 테스트 |
| Selection | ✅ 적용 | "유명 규제" 선정 = 결과 아는 것 |
| Data snooping | ✅ 적용 | 매핑 튜닝하면서 같은 데이터 반복 사용 |
| Overfitting | ⚠️ 부분 | 매핑 테이블이 수동이라 ML overfitting은 아님 |
| Survivorship | ⚠️ 부분 | ETF는 대부분 생존, 개별주는 문제 |
| Transaction cost | ❌ 해당없음 | 거래 전략이 아님 |
| Market impact | ❌ 해당없음 | 거래 안 함 |
