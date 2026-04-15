# 5 Critical Questions You Haven't Asked

> **These are the questions that kill projects AFTER the code is written.**

---

## 1. SEC Liability: 이게 투자 조언으로 분류될 수 있나?

**심각도: 치명적**

"Regulation X → XLF 노출도 12%" 보고 누가 거래하면, SEC가 Investment Advisers Act
Section 206 위반으로 볼 수 있음. **고의 없어도 책임 성립.**

- SEC FY2026 검사 우선순위: AI 기반 자동 투자 도구 타겟
- 해결: 공개 전 증권 변호사 법률 의견 필수
- 참고: Publisher's exclusion (Section 202(a)(11)) 가능성 검토
- URL: [Kitces SEC AI Framework](https://www.kitces.com/blog/artificial-intelligence-compliance-considerations-investment-advisers-sec-securities-exchange-commission-legal-regulation-framework/)

## 2. 경쟁 해자(Moat): 누가 90일 안에 복제 못하는 게 뭐야?

**심각도: 높음**

RegTech 시장 ~$2.7B, 18% CAGR. Thomson Reuters, Wolters Kluwer, IBM이 42-48% 점유.
CUBE가 2024년 말 Thomson Reuters 규제 인텔리전스 사업부 인수 → 1000 고객.

**우리의 가능한 해자:**
- (a) 데이터 품질/큐레이션 (20국 법률 git history = 쉽게 복제 안 됨)
- (b) 오픈소스 커뮤니티 네트워크 효과 (legalize-dev)
- (c) 규제→ETF 매핑이라는 특정 니치 (incumbents가 안 함)

**위험:** 니치 = TAM이 작을 수 있음. Incumbent가 한 분기면 추가 가능.

## 3. 실제 고객 검증: 누가 돈 내고 쓸 건데?

**심각도: 높음**

지금까지 모든 질문이 기술적. **한 번도 잠재 고객과 대화한 적 없음.**

| 고객 | 원하는 것 | 지불 의사 | 요구 사항 |
|------|----------|----------|----------|
| 퀀트 헤지펀드 | 데이터 피드 API | $50K-500K/yr | 극도의 정확도 |
| 컴플라이언스 팀 | 대시보드 + 감사 추적 | $5K-50K/yr | UI + 리포트 |
| 리테일 투자자 | 간단한 알림 | ~$0-10/mo | 심플 UX |

**3개 동시에 만들면 실패.** 1개 세그먼트 선택 → 5개 discovery 인터뷰 필요.

## 4. 프로덕션 스케일: 하루 100+ 규제를 처리할 수 있나?

**심각도: 중간-높음**

Federal Register: 일 200-300건 발행. 처리에 24시간 걸리면 이미 alpha 없음.

- Bloomberg 터미널 유저는 헤드라인 즉시 확인
- 매핑이 수동 리뷰 필요하면 스케일 안 됨
- "Morning briefing" vs "trading signal" = 완전히 다른 사업

## 5. 윤리: 규제 front-running 도구가 되나?

**심각도: 중간**

규제 공개 정보로 거래하는 건 합법이지만:
- 느린 기관 포트폴리오를 앞지르는 데 사용 가능
- 규제 발표 주변 변동성 증폭 가능
- 정보 비대칭 → 정교한 플레이어만 혜택

**오픈소스가 부분적 완화** — 정보 비대칭을 민주화.
그러나 내부 버전과 공개 버전이 다르면 문제.

---

## 패턴

> 기술은 탄탄하다. 하지만 **법률, 상업, 윤리, 운영** 기반이 스트레스 테스트 안 됨.
> 이것들이 코드 작성 후에 프로젝트를 죽이는 질문들.
