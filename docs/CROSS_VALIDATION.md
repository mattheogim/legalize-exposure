# Cross-Validation: Union of Sets Analysis

4개 AI (Claude, GPT, Gemini, Meta) 응답에서 나온 모든 고유 포인트를 추출하고, 누가 뭘 말했는지 분류.

**범례:** ✅ = 언급함, ❌ = 언급 안 함

---

## A. 전원 합의 (4/4) — 반드시 해야 할 것

이건 4개 AI가 전부 지적한 거라 무조건 맞다고 봐야 함.

### A1. Event Study (CAR) 가 핵심 방법론
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
Market Model → AR → CAR → t-test. 모든 AI가 동일한 프레임워크 제시. MacKinlay 1997이 바이블.

### A2. 인과관계 착시가 최대 리스크
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
법 변화와 ETF를 나란히 놓으면 사용자가 자동으로 인과로 해석. 4개 모두 이걸 1순위 리스크로 꼽음.

### A3. Confounding Events 처리 필수
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
같은 날 FOMC, 실적, 지정학 이슈가 겹치면 규제 효과를 분리 불가. 오염도 표시 필요.

### A4. Agency → Sector 규칙 기반 매핑이 출발점
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
EPA→에너지, FDA→헬스케어, SEC→금융. 4개 전부 이걸 1층으로 제시.

### A5. 선반영(Priced-in) 문제
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
최종 규칙 발표 시점엔 이미 시장에 반영됨. Proposed rule, committee markup 등 초기 단계를 추적해야 함.

### A6. 기존 경쟁자는 이 정확한 조합을 안 함
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
FiscalNote, Bloomberg Gov, Quorum, AlphaSense — 전부 "법 추적 OR 시장 분석"이지, "법 diff + 시장 반응"은 없음.

### A7. Entity Mapping이 진짜 어려운 문제
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
규제 텍스트 → 영향받는 산업/ETF 연결이 기술적 핵심. diff UI보다 이게 10배 어려움.

### A8. 초기 타깃은 좁게 시작
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
Federal Register final/proposed rules만 먼저. 모든 국가/판례를 한 번에 하지 말 것.

---

## B. 강한 합의 (3/4) — 거의 확실

### B1. Obligation/Provision 중간 레이어 필요
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ❌ |
Law → Regulation → **Obligation** → Industry → ETF. 직접 연결하면 안 됨. Meta만 간략히 처리.

### B2. 규제를 단일 이벤트가 아니라 이벤트 시퀀스로 처리
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ❌ | ✅ |
Proposed → Comment → Final → Effective → Enforcement. 각 단계별 시장 반응이 다름.

### B3. Hard Link / Soft Link 구분
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ❌ |
텍스트에 명시된 연결(hard) vs 추론에 의한 연결(soft). UI에서 실선/점선으로 구분.

### B4. 설명 가능성(Explainability) 필수
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
"왜 이 ETF를 붙였는가"에 대한 근거를 항상 보여줘야 함. 이게 없으면 전문가 시장에서 신뢰 잃음.

### B5. 백테스트가 제품 신뢰를 만든다
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ❌ | ✅ |
2020-2026 주요 규제 이벤트로 historical replay. 이게 있어야 "우리 시스템이 진짜 작동한다"고 말할 수 있음.

### B6. EU가 국제 확장 1순위
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
EUR-Lex API 성숙도, 시장 규모, AI Act/DMA/CSRD 유스케이스.

### B7. NLP/LLM으로 평문 요약 레이어 필요
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ❌ | ✅ |
법률 diff는 대부분의 사용자에게 읽기 어려움. 자동 요약이 최고 ROI feature.

### B8. 법적 리스크 (투자 조언 오해)
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ❌ | ✅ |
"이 규제로 XLF가 1.2% 하락"은 투자 조언으로 해석될 수 있음. 면책조항 + 언어 통제 필수.

---

## C. 부분 합의 (2/4) — 추가 조사 필요

### C1. Fama-French Multi-Factor Model로 확장
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ❌ | ✅ | ❌ | ✅ |
Market Model만으로 부족, FF3 또는 FF5 factor로 업그레이드.

### C2. GARCH로 변동성 체제 보정
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ❌ | ❌ | ❌ | ✅ |
고변동성 기간에 false positive 증가. Meta만 언급.

### C3. 공개 코멘트(Regulations.gov)를 데이터소스로 활용
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ❌ | ❌ | ❌ |
코멘트 제출자의 산업 분류로 관련 산업 추정. Claude만 상세히 언급.

### C4. Impact Score 합성 점수 (0~100)
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ❌ | ✅ | ❌ | ❌ |
Legal Materiality + Market Signal + Confidence를 합성. GPT만 상세 설계 제시.

### C5. 2차/3차 파급효과 (Value Chain)
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ❌ |
내연기관 규제 → 자동차 하락 + 리튬 상승. 3개가 언급했지만 접근법이 서로 다름.

### C6. 판례는 별도 제품으로 분리
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ❌ | ✅ | ❌ | ❌ |
판례는 lifecycle이 다름. 초기엔 regulation/bill에 집중. GPT만 명확히 분리 제안.

### C7. 역방향: 시장이 먼저 움직이고 법이 따라오는 경우
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ❌ | ❌ | ❌ | ✅ |
GameStop → T+1 결제주기 법안. Meta만 언급. 흥미로운 관점.

### C8. Weak Supervision (Snorkel 스타일)
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ✅ | ✅ | ✅ |
전원 언급했지만 구체성이 다름. Claude/GPT가 LF 단위까지 설계, Gemini는 개념만.

### C9. 한국 정책 테마주 → 리테일 투자자 타깃
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ❌ | ❌ | ✅ | ❌ |
한국 시장의 정책 테마주 특성상 개인 투자자 서비스로 확장 가능. Gemini만 지적.

### C10. ETF Holdings 기반 Exposure Score 계산
| Claude | GPT | Gemini | Meta |
|--------|-----|--------|------|
| ✅ | ❌ | ✅ | ✅ |
ETF 구성종목의 NAICS 가중치 합으로 노출도 계산. 가장 설명 가능한 매핑.

---

## D. 독자적 인사이트 (1/4) — 고유하지만 가치 있는 것

### D1. 텍스트 prior + 시장 posterior 베이지안 업데이트 (GPT)
텍스트 기반으로 먼저 매핑하고, 실제 시장 반응으로 사후 확률 업데이트. 3층 매핑의 3층이 이것.

### D2. "기록형 vs 예측형" 제품 정의의 결정적 중요성 (GPT)
GPT는 대화를 통해 "예측이 아니라 기록이라면?"이라는 전환점을 명확히 정리. 제품 정체성의 핵심.

### D3. 규제 텍스트의 의무 강도 점수화 (Meta)
"shall not" vs "may consider" — 법률 문장의 강제력을 수치화해서 CAR과 회귀.

### D4. Placebo 버튼 (Claude)
UI에 "무작위 날짜 100개 중 이 정도 움직임 비율: 18%" — 사용자가 직접 통계적 의미를 체감.

### D5. 로비스트 연결망 → 수익률 예측 (Meta)
Cohen, Diether, Malloy (2013) 논문. 로비스트 네트워크가 수익률을 예측. 독특한 데이터소스.

### D6. Regulated Entity Type 레이어 (Claude)
Obligation → Industry 사이에 "연간 매출 $10M 이상의 석유 정제 시설" 같은 적용 대상 유형 레이어 추가.

### D7. 산업 분류에 NAICS ≠ GICS 매핑 문제 (Claude)
규제 텍스트는 NAICS, ETF 운용사는 GICS. 이 변환 테이블을 직접 만들어야 함. 1:1 대응 없음.

### D8. 재무제표 시차 (Gemini)
주가는 즉시 반응하지만 실제 펀더멘털 변화는 유예기간 있음. UI에서 어떻게 표현할지.

### D9. Comment Submitter 산업 분류로 관련 산업 추정 (Claude)
Regulations.gov에서 코멘트 제출자 목록 → 기업명 → NAICS 매핑. 에너지 기업이 80% 달면 에너지 관련.

---

## E. 논문 추천 통합 (Union)

### 전원 추천 (필독)
- **MacKinlay (1997)** — Event Study 바이블

### 3/4 추천
- **Baker, Bloom & Davis (2016)** — Economic Policy Uncertainty Index
- **Kothari & Warner (2007)** — Event Study 계량경제학

### 2/4 추천
- **Loughran & McDonald (2011)** — 금융 텍스트 감정 분석 사전
- **Stigler (1971)** — 규제의 경제 이론
- **Binder (1985/1998)** — 규제에 Event Study 적용

### 1/4 추천 (고유)
- **Gentzkow, Kelly & Taddy (2019)** — Text as Data (Claude)
- **Hansen & McMahon (2016)** — 중앙은행 커뮤니케이션과 시장 (Claude)
- **Pastor & Veronesi (2012)** — 정부 정책 불확실성과 주가 (Gemini)
- **Cohen, Diether, Malloy (2013)** — 로비스트 연결망과 수익률 (Meta)
- **Karpoff & Wittry (2018)** — 규제 이벤트 특수성 (Meta)
- **Brown & Warner (1980, 1985)** — 증권 가격 성과 측정 원전 (Meta)
- **Calomiris, Mamaysky, Yang** — 텍스트 기반 규제 비용 측정 (GPT)
- **Ding et al. (2014)** — 구조화 이벤트로 주가 예측 (GPT)
- **Ash & Chen (2022)** — 경제학에서의 텍스트 알고리즘 (Claude)
- **Clapham et al.** — 규제 영향 분석에 NLP 적용 (GPT)
- **Katz, Bommarito & Blackman (2017)** — 대법원 행동 예측 ML (Claude)

---

## F. 핵심 의사결정 요약

### 즉시 결정해야 할 것

| 결정 사항 | 합의 수준 | 추천 방향 |
|-----------|----------|----------|
| 제품 정체성 | 4/4 | "법률 이벤트 브라우저 + 시장 컨텍스트 뷰어" (예측기 아님) |
| 초기 Wedge | 4/4 | Regulation-to-Exposure Mapping 먼저, Market Panel은 나중에 |
| 초기 범위 | 4/4 | US Federal Register (final + proposed rules)만 |
| 매핑 1층 | 4/4 | Agency → Sector 규칙 기반 |
| 인과 언어 금지 | 4/4 | "impact", "caused" 대신 "around", "coincided with" |
| 핵심 방법론 | 4/4 | Event Study (Market Model → AR → CAR) |
| 국제 확장 1순위 | 4/4 | EU (EUR-Lex) |

### 더 조사해야 할 것

| 결정 사항 | 합의 수준 | 의견 갈림 |
|-----------|----------|----------|
| Factor Model 선택 | 2/4 | Market Model만? FF3/FF5? |
| Event Window 길이 | 갈림 | Claude: [-1,+5], GPT: 여러 윈도우 병렬, Meta: [-5,+5] |
| 판례 포함 여부 | 1/4 | GPT만 "별도 분리" 제안, 나머지는 언급 안 함 |
| Impact Score 합성 | 1/4 | GPT만 상세 설계, 나머지는 개념만 |
| GARCH 변동성 보정 | 1/4 | Meta만 언급, 초기엔 불필요할 수도 |
