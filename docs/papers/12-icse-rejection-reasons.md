# ICSE Reviewer: 3 Rejection Reasons

> **이 피드백을 논문/제품 설계에 반영해야 함**

---

## Rejection 1: 평가가 없다 (DEVASTATING)

**문제:** Gold standard 없음, baseline 비교 없음, user study 없음.

- validation_100.json이 있지만 precision/recall/F1 측정 안 함
- event_study.py가 있지만 시뮬레이션 데이터로만 테스트
- 52개 parser test는 smoke test, 시스템 평가가 아님

**필요한 것:**
- [ ] 500+ regulation-to-industry 매핑 gold standard (복수 annotator, inter-rater agreement)
- [ ] Baseline 비교: keyword matching vs 우리 ontology vs LLM zero-shot
- [ ] 실제 시장 데이터로 event study validation
- [ ] Scalability 벤치마크 (laws/min, 20국 실패율)

---

## Rejection 2: 엔지니어링이지 연구가 아니다 (SEVERE)

**문제:**

| 우리가 주장하는 것 | 리뷰어가 보는 것 |
|-------------------|----------------|
| "Git-as-database 패턴" | git으로 문서 버전 관리 = 기존 도구의 당연한 적용 |
| "7-layer ontology" | 하드코딩된 lookup table (31 agencies → 55 NAICS) |
| "Pipeline architecture" | 표준 ETL 패턴 |

**필요한 것:**
- Git-as-database의 형식적 속성 정의 (idempotency, consistency model)
- Ontology를 자동 구축하거나, 7-layer가 flat보다 우월함을 controlled experiment로 증명
- 20개국 파서 구축 경험에서 일반화 가능한 원칙 추출

---

## Rejection 3: 두 시스템을 합쳤는데 둘 다 얕다 (SEVERE)

**문제:** Pipeline (SE/NLP) + Exposure Engine (Finance) = 두 커뮤니티 어디에도 깊지 않음.

| 커뮤니티 | 기대하는 것 | 우리가 하는 것 |
|----------|-----------|--------------|
| SE/NLP | learned model, cross-lingual transfer | hand-written XML scrapers |
| Finance | FF factors, matched-sample, long-horizon | textbook Market Model |

**해결:**
- **논문을 2개로 분리:**
  - (a) Pipeline → MSR 또는 ICSE SEIP/SEIS
  - (b) Exposure → EMNLP 또는 JFE
- ICSE에는 pipeline만. Exposure 제외.
- Pipeline 고유의 기술적 도전 (temporal versioning, retroactive corrections, cross-jurisdictional schema heterogeneity)에 집중

---

## 가장 현실적인 출판 경로

| 대상 | 학회/저널 | 초점 | 필요한 작업 |
|------|----------|------|-----------|
| Pipeline 시스템 | ICSE SEIP/SEIS, MSR | 20국 법률 추출 + git versioning | Gold standard + scalability eval |
| Exposure 매핑 | EMNLP, ACL (NLP 트랙) | 규제 텍스트 → 산업 분류 | NLP baseline 비교 + F1 |
| Impact 분석 | JFE, RFS | 규제 → ETF returns (causal) | DiD/SC + robustness battery |
| 데이터셋 | NeurIPS Datasets | "RegData with Diffs" | 데이터 문서화 + 재현성 |
