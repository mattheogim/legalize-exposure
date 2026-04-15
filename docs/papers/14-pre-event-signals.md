# Pre-Event Signals: When Does the Market Price In Regulation/Legislation?

> **핵심 발견: 시장은 생각보다 느리다. 대부분의 alpha는 사전이 아니라 사후에 발생.**

---

## 1. 입법 파이프라인 (Bills / Acts)

### Cohen, Diether & Malloy (2013) — THE definitive paper

**"Legislating Stock Prices"** JFE 110(3):574-595

**핵심 발견:**
- 법안 통과 **전** 6-12개월: **거의 반응 없음**
- 법안 통과 **후** 60 trading days: **월 90+ bps 초과수익**
- 복잡한 법안일수록 시장 반응이 더 느림

```
시간축:
  발의 → 위원회 → CBO → 본회의 → 서명
  -------- 거의 반응 없음 --------→ ←-- alpha 여기서 발생 (60일) --→
```

**의미:** 사전 신호(committee, CBO score)는 거래 신호가 아님.
진짜 가치 = **통과 후 빨리 해석하는 것.**

URL: https://www.sciencedirect.com/science/article/abs/pii/S0304405X13002262

### 예외: Tax Cuts and Jobs Act 2017

- 상원 위원회 승인 → 반응 있었음
- 상원 본회의 통과 → 반응 있었음
- 양원 조율 → 반응 있었음
- 최종 서명 → "buy the rumor, sell the fact" (서명일 하락)

**BUT:** 이건 극도로 high-profile 법안. 대부분의 법안에는 해당 안 됨.

### 의원 내부자 거래 증거

- 의회 리더의 거래가 일반 의원보다 월등히 높은 수익
- **사전 정보가 가치 있다는 증거** — 하지만 시장 전체는 이 신호를 추출 못 함
- Source: [CEPR VoxEU](https://cepr.org/voxeu/columns/political-power-and-profitable-trades-us-congress)

### Prediction Markets (Polymarket, PredictIt, Kalshi)

- 플랫폼 간 일일 가격 상관관계 낮음
- Polymarket이 가장 부정확
- 노이즈가 너무 많아서 실시간 입법 확률 추적기로는 부적합
- Source: [DL News](https://www.dlnews.com/articles/markets/polymarket-kalshi-prediction-markets-not-so-reliable-says-study/)

---

## 2. 규제 파이프라인 (Regulations)

### 핵심 발견: 시장은 Final Rule 전에 대부분 반영

| 단계 | 시장 반영 비율 | 핵심 논문 |
|------|:---:|---|
| (a) 미디어/루머 | ~15-25% | Baker-Bloom-Davis 2016; Bauer & Swanson 2018 |
| (b) ANPRM / Unified Agenda | ~10-20% | Ginther & Zavodny 2005 (Beige Book) |
| (c) **Proposed Rule (NPRM)** | **~25-35%** | Greenstone et al.: 75-85% 제안~시행 사이 |
| (d) Comment period close | ~5-10% | 제한적 증거 |
| (e) **Final Rule** | **~10-20%** | 우리가 지금 측정하는 곳 ← 너무 늦음 |
| (f) Effective date | ~0-5% | 거의 다 반영됨 |

**→ Final Rule에서 event study = 전체 효과의 20-40%만 캡처**

### 핵심 논문

**Greenwood et al. (NBER 24586):**
> "60%+ of the direct effect had already been impounded into stock prices
> even six months before the actual event."
URL: https://www.nber.org/system/files/working_papers/w24586/revisions/w24586.rev2.pdf

**Greenstone, Oyer & Vissing-Jorgensen (NBER 16737):**
> 1964 Securities Acts: 제안~시행 사이 11.5-22.1% 초과수익.
> 최종 compliance 발표일에는 3.5%만.
> **75-85%가 사전에 반영됨.**
URL: https://www.nber.org/papers/w16737

**Pastor & Veronesi (2012, JoF):**
> 정책 변경 예상만으로 risk premia 상승, 변동성 증가.
> **공식 발표 전에 불확실성 프리미엄이 이미 주가에 반영.**
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1625845

**Bauer & Swanson (2018, NBER):**
> FOMC "예상치 못한" 결정도 25일 전부터 자산 가격 변화.
> **Pre-announcement drift = 시장이 사전에 감지.**
URL: https://www.nber.org/digest/digestsep18/market-anticipation-fomc-policy-shocks

**Brogaard & Detzel (2015, Management Science):**
> 규제 불확실성 = 체계적 위험 요소. 최고 EPU-beta 포트폴리오가 최저보다 연 5.53% 언더퍼폼.
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2075375

### FDA 사례 (규제 파이프라인 단계별 비교)

**FDA Clinical Trial → Approval (PMC 2022):**
- Phase 2/3 결과 발표 = 가장 큰 시장 반응
- 최종 FDA 승인일 = 잔여 반응만
- **규제의 "중간 단계"가 최종 단계보다 impact 큼**
URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC9439234/

### CMS Medicare Advantage 실제 사례 (2026)
- 1월: Advance Notice (0.09% 인상 제안) → 주가 하락 시작
- 4월: Final Rate (2.48% 인상 확정) → relief rally
- **시장은 Advance Notice(=ANPRM)에서 반응, Final Rule에서 서프라이즈만 추가 반영**

---

## 3. FOMC / Monetary Policy

### Baker-Bloom-Davis (2016)

- 정책 불확실성이 **높은 동안**: 투자 감소, 변동성 증가
- 불확실성 **해소 시**: relief rally (방향 무관)
- 즉, FOMC 결정 자체보다 **불확실성 해소**가 시장을 움직임

### 시사점

```
FOMC 신호 순서:
  Beige Book → Dot Plot → Forward Guidance → 결정 → Minutes
  ←-- 불확실성 증가 기간 --→  ←-- 해소 --→
```

---

## 4. 우리 프로젝트에 대한 시사점

### 기존 가정 (틀렸을 수 있음):
```
❌ "Final Rule 발표일에 event study" → 이미 priced in일 수 있음
❌ "법안 통과일에 event study" → Cohen: 통과 후 60일이 진짜
```

### 수정된 접근:
```
✅ 규제: Proposed Rule 발표일에 event study (정보 최초 공개 시점)
✅ 법안: 통과 후 60일 CAR 측정 (시장이 해석하는 기간)
✅ 전체 시퀀스 추적: ANPRM → NPRM → Final 각 단계별 CAR
✅ 불확실성 해소 이벤트도 추적 (comment period close 등)
```

### 가장 유망한 전략:
> **통과/발표 후 빨리 해석하는 것이 가치.**
> 사전 예측이 아니라, 사후 해석 속도가 경쟁력.
> Cohen et al.: 시장이 60일 걸리는 해석을 우리가 1일 안에 하면 alpha.

---

---

## 5. Priced-In 문제: 공격과 방어

### 공격 (가장 강력한 반증)

**Ellison & Mullin (2001) — THE smoking gun**
"Gradual Incorporation: Pharmaceutical Stocks and Clinton's Health Care Reform"
*Journal of Law and Economics* 44(1):89-129

> 제약주 52.3% 하락이 22개월에 걸쳐 점진적으로 발생.
> 최종 발표일 event study → **0에 가까움** (이미 다 반영).
> Standard event study는 규제가 "효과 없다"고 잘못 결론 내림.

URL: https://doi.org/10.1086/320269

**Reynolds (2006) — 시장이 틀림**
"Anticipated vs. Realized Benefits: Can Event Studies Predict Impact?"
*Eastern Economic Journal*

> Byrd Amendment: 41개 실제 수혜 기업 중 시장이 예측한 건 **5개뿐**.
> 시장은 빠르기만 한 게 아니라 **부정확**함.

URL: https://link.springer.com/article/10.1057/palgrave.eej.9050036

**Malatesta & Thompson (1985) — 수학적 bias 증명**
"Partially Anticipated Events: A Model of Stock Price Reactions"
*JFE* 14(2):237-250

> 이벤트가 발생할 수도/안 할 수도 있는 기간에 market model disturbance ≠ 0.
> → 체계적 bias. 수정: 이벤트 발생 기간 + 비발생 기간 결합.

URL: https://www.sciencedirect.com/science/article/abs/pii/0304405X85900169

### 방어 (해결 방법)

**Prabhala (1997) — 가장 강력한 이론적 방어** ★★★
"Conditional Methods in Event Studies"
*Review of Financial Studies* 10(1):1-38

> **이벤트가 예상되더라도 standard event study는 통계적으로 유효.**
> 이유: 발표는 "불확실성 해소"를 측정. 100% 확실한 규제는 없으므로
> 발표 확정 자체에 정보 가치가 있음. 조건부 방법과 결합 시 검정력 향상.

URL: https://academic.oup.com/rfs/article/10/1/1/1612015

**Schipper & Thompson (1983) — Multi-event solution** ★★★
"Impact of Merger-Related Regulations"

> 단일 날짜 대신 **전체 규제 타임라인** 추적.
> SUR (Seemingly Unrelated Regression): 모든 milestone에 더미 변수.
> 각 단계의 incremental information을 분리 측정.

URL: via Kothari & Warner 2007

**Hiemstra & Lamdin (1998) — 데이터 기반 이벤트 식별**

> 연구자가 날짜를 "추측"하지 말고, 수익률의 **통계적 이상치**로 자동 탐지.
> Binder 비판에 직접 대응.

URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5729

**Eckbo (1983, 1985) — 부호 기반 추론**

> 크기(magnitude)는 anticipation에 의해 왜곡되지만, **방향(sign)**은 여전히 유효.
> 규제 영향 vs 비영향 기업의 수익률 부호 비교 → 인과 추론 가능.

---

## 6. 수정된 설계 (모든 증거 통합)

```
기존 (틀린 접근):
  Final Rule 날짜 → single-window event study → CAR
  = 전체 효과의 20-40%만. null이면 "효과 없음"으로 잘못 결론.

수정 (증거 기반):
  1. MULTI-EVENT WINDOW (Schipper & Thompson)
     ANPRM → NPRM → Comment Close → Final → Effective
     각 단계별 dummy variable → incremental CAR 측정

  2. PRE-EVENT DIAGNOSTIC (Kothari & Warner)
     [-60, -1] pre-event CAR 확인 → 사전 반영 정도 측정
     사전 CAR이 크면 → "이미 priced in" 증거

  3. CROSS-SECTIONAL DOSE-RESPONSE
     노출도 높은 ETF vs 낮은 ETF 비교
     부호(sign)가 예측대로면 → anticipation에도 불구하고 인과 증거 (Eckbo)

  4. CONTINUOUS INDEX (Baker-Bloom-Davis 대안)
     이산 이벤트 대신 연속적 규제 활동 강도 지수
     anticipation 문제를 완전 우회

  5. POST-EVENT INTERPRETATION SPEED (Cohen et al.)
     법안 통과 후 60일 = 시장이 해석하는 기간
     우리가 1일 안에 매핑하면 = 가장 현실적인 가치
```

### 가장 현실적인 가치 제안

> **"규제가 시장에 영향 준다"를 증명하는 것이 아니라,
> "이 규제가 어떤 산업/ETF에 관련되는지"를 시장보다 빨리 해석하는 것.**
>
> Cohen et al.: 시장은 법안 해석에 60일 걸림.
> 우리 시스템: 발표 당일 자동 매핑.
> **이 시간 차이가 가치.**

---

## 추가 논문 (validation framework에 포함)

| Paper | Finding | URL |
|-------|---------|-----|
| Cohen et al. 2013 | 통과 후 60일 alpha, 사전 신호 없음 | [JFE](https://www.sciencedirect.com/science/article/abs/pii/S0304405X13002262) |
| TCJA 2017 studies | 단계별 반응 있었음 (예외적 high-profile) | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0378426620301266) |
| Snowberg-Wolfers-Zitzewitz | Prediction market → asset price 방법론 | [NBER](https://www.nber.org/system/files/working_papers/w18222/w18222.pdf) |
| Congressional insider trading | 사전 정보 가치 있지만 시장이 추출 못 함 | [CEPR](https://cepr.org/voxeu/columns/political-power-and-profitable-trades-us-congress) |
