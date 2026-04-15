# Regulatory-to-Exposure Mapping 제품 설계 원칙 v1

*Cross-validated across Claude, GPT, Gemini, Meta AI — April 2026*

---

## 1. 제품의 정체성

이 제품은 시장 예측기가 아니다. 이 제품은 법률/규제 이벤트를 구조화하고, 그것이 어떤 entity / industry / ETF proxy와 관련되는지 정직하게 연결하는 기록·탐색 시스템이다.

핵심:
- 법률 diff를 보여주는 것
- 관련 대상을 매핑하는 것
- 시장 데이터는 나중에 context로 붙이는 것

**쓰면 안 되는 정의:**
- "시장 영향 분석기"
- "이 규제가 ETF를 움직였다"

**써야 하는 정의:**
- Legal event browser
- Regulation-to-exposure mapping
- Market context viewer

---

## 2. 초기 Wedge

초기 wedge는 market reaction panel이 아니라 **exposure mapping**이다.

**초기 제품이 해야 할 일:**
- 어떤 regulation/law event가
- 어떤 regulated entity type / industry와 관련 있는지 보여주기
- 어떤 ETF가 그 산업의 market proxy 역할을 하는지 연결하기
- 중요도와 confidence를 보여주기

**초기 제품이 하지 말아야 할 일:**
- "이 이벤트 때문에 가격이 움직였다"는 식의 인과 암시
- Market panel을 제품 중심으로 내세우기
- Case law까지 한 번에 다 넣기

---

## 3. 기본 계층 구조

초기 기준 체인은 아래로 고정한다.

```
Law → Regulation → Provision → Obligation → Regulated Entity Type → Industry(NAICS) → ETF
```

| 레이어 | 설명 |
|--------|------|
| Law | 상위 법적 권한 |
| Regulation | 구체화된 규정 |
| Provision | 조문/세부 단위 (diff가 여기서 발생) |
| Obligation | 무엇을 하게 하거나 금지하는지 |
| Regulated Entity Type | 누가 그 의무를 지는지 |
| Industry | 산업 분류 (NAICS) |
| ETF | 시장 proxy |

**Phase 2 이후 확장 후보:**
- Activity (NAICS보다 좁은 행위 단위)
- Product (규제가 타깃하는 구체적 자산/제품)
- Company (개별 기업 레벨 매핑)

즉 초기엔 Claude형 7단계 구조를 기본으로, 필요할 때 Meta형으로 확장한다.

---

## 4. 직접 연결 금지 원칙

**Law와 ETF를 직접 연결하지 않는다.**

이유:
- 법은 ETF를 직접 규율하지 않는다
- ETF는 규제 대상이 아니라 시장 관측용 proxy다
- 직접 연결은 의미 없는 거미줄과 인과 착시를 만든다

항상 중간 레이어를 거친다: Entity Type → Obligation → Industry.

---

## 5. Edge 설계 원칙

Edge는 모두 같은 의미가 아니다. **Hard link / soft link를 분리한다.**

### Hard Link — 문서 근거가 명확한 연결

| Edge Type | 뜻 | 근거 |
|-----------|-----|------|
| CITES | 법이 규정을 인용 | US Code → CFR 조문 번호 |
| IMPLEMENTS | 규정이 법을 구체화 | Federal Register preamble "Authority:" |
| IMPOSES | 규정이 의무를 부과 | "shall", "must" 문장 추출 |
| APPLIES_TO | 의무가 적용 대상 정의 | "covered entity means..." |

### Soft Link — 추론 기반 연결

| Edge Type | 뜻 | 근거 |
|-----------|-----|------|
| MENTIONS | 텍스트에 산업 키워드 등장 | TF-IDF, NER |
| EXPOSES | 산업이 ETF에 노출 | 보유비중 × 매출비중 |

**핵심 규칙:** 법률 세계와 시장 세계를 잇는 엣지는 절대 CAUSES를 쓰지 않는다. APPLIES_TO까지만 hard, 그 이후는 EXPOSES로만 표현.

### 규제 성격 — Edge가 아니라 Obligation Property로 저장

| Property | 의미 |
|----------|------|
| RESTRICTS | 제한/규제 강화 |
| MANDATES | 의무 부과 |
| SUBSIDIZES | 보조금/세제 혜택 |
| EXEMPTS | 면제 |

관계 타입은 Meta식, 방향성/성질은 Gemini식 속성으로 분리한다.

---

## 6. Edge 표준 속성

모든 edge에는 아래 4개 필드를 **기본**으로 둔다.

| 필드 | 설명 |
|------|------|
| evidence_type | citation / keyword / metadata / embedding / holdings |
| confidence | 연결 신뢰도 (0.0~1.0) |
| provenance | 근거 스니펫 또는 출처 URL |
| contamination_score | 같은 시기 confounding event 수/정도 |

이 4개는 나중 옵션이 아니라 기본 필드다. 그래야 그래프가 설명 가능해진다.

---

## 7. 초기 분류 방법론

초기 분류는 LLM 중심이 아니라 **ontology + rules + weak supervision + human review** 중심으로 간다.

### Anchor 규칙 (Labeling Functions)

| LF | 방식 | 정밀도 | 재현율 |
|----|------|--------|--------|
| LF1: Agency → Industry 룩업 | EPA→환경/에너지, FDA→헬스케어, SEC→금융 | 중간 | 높음 |
| LF2: CFR Section → Industry | 40 CFR Part 60 → 에너지/제조 | 높음 | 중간 |
| LF3: NAICS/SIC 코드 직접 추출 | 정규식 "NAICS \d{4,6}" | ~100% | 낮음 |
| LF4: RIA 비용 귀속 산업 추출 | "석유 정제 산업에 연간 $2.1B" | 높음 | 낮음 (significant rules만) |
| LF5: 상위 법률 매핑 상속 | Clean Air Act → 이전 매핑 산업 | 중간 | 중간 |
| LF6: LLM zero-shot | "가장 영향받는 NAICS 3개" | 모델 의존 | 보조만 |

이 anchor들이 초기 분류의 뼈대다. Snorkel 스타일로 합산.

---

## 8. LLM 사용 원칙

**LLM은 최종 판정기가 아니다. 약한 신호 하나로만 사용한다.**

초기 정책:
- Output은 yes/no + confidence
- Threshold로 바로 채택하지 않음
- 다른 labeling function과 합산
- Human review 전 단계 보조 신호로 사용

Meta식 보수 접근을 따른다. 초기엔 Gemini식 "0.7 이상 바로 채택"은 쓰지 않는다.

---

## 9. ETF 연결 원칙

**ETF는 이름이 아니라 holdings 기반으로 연결한다.**

초기 방식:
- ETF 구성 종목 목록
- 종목 비중 (weight)
- 종목의 산업/revenue exposure를 기반으로 **exposure score** 계산

```
exposure_score = Σ(weight_i × revenue_share_in_industry_i)
```

Sector label만 보고 붙이지 않는다. Holdings 기반이 설명 가능성 면에서 더 낫다.

**NAICS ≠ GICS 매핑 주의:** 규제 텍스트는 NAICS, ETF 운용사는 GICS 사용. 이 변환 테이블을 직접 구축해야 하며, 완벽한 1:1 대응은 없음을 투명하게 공개.

**Phase 2 실험 후보:**
- ETF prospectus 임베딩
- Text-to-prospectus semantic similarity

---

## 10. 시장 데이터 원칙

시장 데이터는 붙이되, **나중에 context panel로 붙인다.**

### 표준 방법론

| 요소 | 설정 |
|------|------|
| 모델 | Market Model (R_i = α + β × R_m) |
| Estimation Window | 120 trading days (t=-130 to t=-11) |
| Event Window | 기본 [-1, +1], 확장 [-5, +5] |
| 핵심 지표 | AR, CAR, t-statistic |

**핵심 공식:**
```
AR = 실제 수익률 - 기대 수익률
CAR = Σ AR over event window
```

### 주의사항

- 이건 관측 도구이지, 인과 증명 도구가 아니다
- Market panel은 탭 분리 / 접힘 / 별도 패널로 제공
- Benchmark를 반드시 병기: S&P 500, 같은 섹터 다른 ETF, broad market
- Contamination score 표시: 같은 기간 FOMC/실적/지정학 이슈 개수

시장 데이터는 주 제품이 아니라 보조 맥락층이다.

---

## 11. UI/언어 원칙

**제품이 인과처럼 읽히지 않게 설계한다.**

### 금지 표현

| 금지 | 대체 |
|------|------|
| impact | exposure |
| caused | coincided with |
| drove | around the time of |
| led to | co-occurrence |
| market reaction | price movement around event |
| effect | market context |

### UI 원칙

- 기본 화면은 diff + 기록
- 시장 데이터는 사용자가 클릭해야 펼쳐짐 (명시적 선택)
- Hard/soft는 실선/점선으로 구분
- 근거(provenance)는 언제든 열람 가능
- 개별 이벤트: 시장 컨텍스트만 표시
- 집계 뷰에서만 통계적 요약 제공

---

## 12. 초기 범위

### 포함

- Federal Register rules (proposed + final)
- US Code amendments
- Agency → Industry 규칙 기반 매핑
- Sector ETF holdings 기반 exposure

### 제외 (Phase 2+)

- Case law (lifecycle이 다름, 별도 제품 가능성)
- 역방향 시장→법 분석
- Impact score 합성 모델
- Prospectus embedding 기반 자동 연결
- Fama-French multi-factor model (Market Model로 시작)
- GARCH 변동성 보정

---

## 13. Phase 2 확장 후보

### 데이터 소스 확장

**Regulations.gov 코멘트 데이터:**
- Commenter identity / organization type
- Commenter industry mapping (기업명 → NAICS)
- Repeated industry participation 패턴
- **Soft link evidence로만 사용**
- 주의: 코멘트 많다고 경제적 영향이 큰 건 아님. 조직력 좋은 업계가 과대표현될 수 있음

### 국제 확장 순서

| 순위 | 국가 | 데이터 소스 | 이유 |
|------|------|------------|------|
| 1 | EU | EUR-Lex CELLAR/SPARQL | 데이터 성숙도, 시장 규모, AI Act/DMA/CSRD |
| 2 | 한국 | 국가법령정보센터 API | 규제 민감도 높은 시장, 정책 테마주 문화 |
| 3 | 일본 | e-Gov法令API | 공식 인프라 괜찮음, 반도체/자동차/금융 |
| 4 | 브라질 | LexML | 변동성 높아 이벤트 스터디 효과 클 수 있음 |

### 계층 구조 확장

- Activity (NAICS보다 좁은 행위 단위: "lithium mining" vs "battery manufacturing")
- Product (규제가 타깃하는 구체적 자산: "내연기관 엔진")
- Company (개별 기업 레벨)

### 시장 데이터 고도화

- Fama-French 3/5-factor model
- GARCH 변동성 보정
- Abnormal volume / volatility
- Options implied vol change
- Impact score 합성 (Legal Materiality + Market Signal + Confidence)

---

## 14. 백테스트 / Historical Replay

**매핑 정확도를 검증하는 필수 단계.**

### 구성

| 요소 | 설명 |
|------|------|
| 이벤트셋 | 2020~2026 주요 규제 이벤트 200~500건 |
| 시점 제약 | 당시 시점에 알려진 정보만 사용 |
| 검증 대상 | Industry 매핑 정확도, ETF exposure 정확도 |
| 평가 기준 | Precision / recall / false positive rate |
| Human review | 최소 100건은 수동 검증 |

### 목적

- "우리 시스템이 실제로 작동하는 ontology인지" 확인
- "그럴듯한 그래프"와 "검증된 그래프"의 차이를 만드는 단계
- 이 결과가 있어야 제품 신뢰도를 주장할 수 있음

### Phase 2 백테스트 확장

- 시장 데이터 추가 후: CAR 분포 검증 (정규분포 벗어나면 보정 필요)
- Cross-sectional 분석: 유사 규제 유형의 평균 시장 반응 패턴
- Placebo test: 무작위 날짜에서 같은 분석 실행 → 비교 기준

---

## 15. 실행 원칙 (흔들리지 말 것)

| # | 원칙 |
|---|------|
| 1 | Mapping first, market panel later |
| 2 | Hard/soft link 분리 |
| 3 | Law → ETF 직접 연결 금지 |
| 4 | 7단계 계층 구조 (Law → ... → ETF) |
| 5 | Meta edge taxonomy 채택 |
| 6 | Meta식 보수적 LLM 사용 |
| 7 | Holdings 기반 ETF exposure |
| 8 | Market panel은 context layer |
| 9 | Benchmark + contamination score 필수 |
| 10 | Case law는 나중 |
| 11 | Historical replay로 매핑 정확도 검증 |

---

## 16. 필독 논문

### Tier 1 — 필수 (4/4 AI 합의)

- MacKinlay (1997). "Event Studies in Economics and Finance." *JEL*

### Tier 2 — 강력 추천 (3/4 합의)

- Baker, Bloom & Davis (2016). "Measuring Economic Policy Uncertainty." *QJE*
- Kothari & Warner (2007). "Econometrics of Event Studies." *Handbook of Corporate Finance*

### Tier 3 — 추천 (2/4 합의)

- Loughran & McDonald (2011). "When Is a Liability Not a Liability?" — 금융 텍스트 감정 분석
- Stigler (1971). "The Theory of Economic Regulation." — 규제 경제 이론
- Binder (1985). "Measuring the Effects of Regulation with Stock Price Data." — 규제 Event Study

### Tier 4 — 영역별 심화

| 영역 | 논문 |
|------|------|
| Text-as-Data | Gentzkow, Kelly & Taddy (2019) |
| 중앙은행 텍스트→시장 | Hansen & McMahon (2016) |
| 정책 불확실성→주가 | Pastor & Veronesi (2012) |
| 로비스트→수익률 | Cohen, Diether, Malloy (2013) |
| 규제 이벤트 특수성 | Karpoff & Wittry (2018) |
| 텍스트 기반 규제 비용 | Calomiris, Mamaysky, Yang (2020) |
| 구조화 이벤트→주가 | Ding et al. (2014) |
| 법률 NLP | Ash & Chen (2022) |
| 대법원 예측 ML | Katz, Bommarito & Blackman (2017) |

---

## 최종 한 문장

**이 제품의 첫 버전은 regulation-to-exposure mapping 시스템이어야 하며, 법률 이벤트를 entity type과 industry를 거쳐 ETF proxy에 정직하게 연결하고, 시장 데이터는 이후 context layer로 추가하며, historical replay로 매핑 정확도를 검증한다.**
