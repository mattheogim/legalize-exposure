# Paper Verification Status

> **이 파일이 ground truth. 각 논문을 원본과 대조한 결과.**
> VERIFIED = 원본 확인됨, UNVERIFIED = 아직 확인 안 됨, WRONG = 틀린 내용 발견

---

## 핵심 논문 (코드 구현 전 반드시 확인)

### 1. Goldsmith-Pinkham & Lyu 2025
**VERIFIED: PARTIAL**
- ✅ 저자, 제목 확인 (arXiv 2511.15123)
- ✅ Synthetic control 제안 확인 ("construct replicating portfolios from control securities")
- ✅ Factor model misspecification → inconsistent estimates 확인
- ⚠️ Proposition 1 수학: arXiv HTML에서 읽었으나 PDF 원본과 수식 번호 대조 필요
- ⚠️ 시뮬레이션 파라미터 (500 firms, 239 days, 3% effect): 검증 필요
- **ACTION:** 코드 구현 전 PDF 다운로드해서 Section 3-4 수식 직접 확인

### 2. Baker, Bloom & Davis 2016
**VERIFIED: PARTIAL**
- ✅ 3개 컴포넌트 (news, tax, forecaster disagreement) 확인 (policyuncertainty.com)
- ✅ 10개 신문 확인 (이름 목록 일치)
- ⚠️ 검색어 ("economic" AND "policy terms" AND "uncertainty"): 정확한 단어 목록 미확인
- ⚠️ Human audit 상관관계 "~0.86": 내 기억 기반, 원본에서 수치 미확인
- ⚠️ VAR 계수 ("0.5-1.0% IP decline"): 근사치, 정확한 수치 미확인
- **ACTION:** QJE 원본 Table/Figure에서 정확한 수치 확인

### 3. Cohen, Diether & Malloy 2013
**VERIFIED: PARTIAL**
- ✅ 제목 "Legislating Stock Prices" 확인
- ✅ JFE 110(3):574-595, 2013 확인
- ✅ "90 basis points per month" 확인 (NBER abstract에서)
- ✅ Fama-DFA Prize 수상 확인
- ⚠️ "60 trading days" 지속 기간: NBER abstract에 없음, 내 기억 기반 **미검증**
- ⚠️ "사전 반응 없음": 미검증
- 🔴 **이 두 수치는 코드 구현 전 반드시 확인 필요**
- **ACTION:** JFE 원본 PDF에서 Figure/Table 확인 (post-passage drift 기간 + pre-passage 수익)

### 4. Greenwood, Hanson, Shleifer, Sorensen
**VERIFIED: PROBLEMATIC**
- ✅ 논문 존재 확인 (NBER WP 24586)
- 🔴 **"60% of direct effect priced in 6 months before"**: 이 수치가 **중국 margin lending** 맥락이지, 일반적 규제 맥락이 아님!
- 🔴 논문 제목이 "Effects of Credit Expansions on Stock Market Booms and Busts" — 규제가 아니라 **신용 확장**에 관한 논문
- 🔴 **내 노트에서 이 논문을 "규제 일반"으로 확대 해석함 — HALLUCINATION**
- **ACTION:** 이 논문을 규제 priced-in의 증거로 쓰면 안 됨. 삭제 또는 맥락 수정.

### 5. Kalmenovitz 2023
**VERIFIED: PARTIAL**
- ✅ RFS 36(8):3311-3347 확인
- ✅ ML으로 10-K 텍스트 ↔ 규제 텍스트 cosine similarity 확인
- ✅ "supervised machine-learning algorithms" 확인
- ⚠️ "Form 83-I": Harvard Law Forum 요약에서 직접 언급 안 됨, 논문 본문에 있을 수 있음
- ⚠️ "4개 RegIn 측정치": Forum에서는 "3개"로 설명 — **수치 불일치**
- **ACTION:** 원본에서 RegIn 정확히 3개인지 4개인지 확인

### 6. Armstrong, Glaeser & Hoopes 2025
**VERIFIED: PARTIAL**
- ✅ JAE 79(1), 2025 확인
- ✅ 10-K 기반 agency exposure 측정 확인
- ✅ "undisclosed agency investigations" 예측 확인
- ⚠️ "GPT-3.5 ≈ dictionary": 검색 결과에서 직접 나오지 않음, 원본에 있을 수 있지만 **미검증**
- **ACTION:** 원본에서 GPT comparison 섹션 확인

---

## Hallucination 발견 목록

| # | 내용 | 상태 | 심각도 |
|---|------|------|--------|
| 1 | Greenwood et al. "60% priced in" = 규제 일반이 아니라 중국 margin lending | 🔴 **WRONG CONTEXT** | 높음 |
| 2 | Kalmenovitz "4개 RegIn" — Forum에서는 3개로 설명 | ⚠️ 불일치 | 중간 |
| 3 | Cohen "60 trading days" — abstract에 없음, 미검증 | ⚠️ 미확인 | 높음 |
| 4 | BBD human audit "0.86" — methodology page에 수치 없음 | ⚠️ 미확인 | 낮음 |
| 5 | Armstrong "GPT ≈ dictionary" — 검색에서 미확인 | ⚠️ 미확인 | 중간 |

---

## 수정이 필요한 파일

| 파일 | 수정 내용 |
|------|----------|
| `14-pre-event-signals.md` | Greenwood "60%" 인용 수정 — 중국 margin lending 맥락으로 한정, 또는 삭제 |
| `11-practical-studies-we-can-do.md` | Greenwood 참조 수정 |
| `03-impact-causal-evidence.md` | Greenwood 논문 맥락 수정 |

---

## 검증 프로세스

코드 구현 전:
1. 해당 논문 PDF 다운로드
2. 구현하려는 수식의 Section/Equation 번호 확인
3. 변수 정의, 부호, 조건 원본과 대조
4. 이 파일에 VERIFIED 표시 업데이트
5. 수식 노트 파일에 "VERIFIED against PDF Section X.Y" 추가
