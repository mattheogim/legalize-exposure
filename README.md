# Legalize

**Regulation-to-Exposure Mapping Platform**

법률/규제 변경 → 산업 매핑 → ETF 노출도 추적. 시장 예측기가 아닌, 규제 이벤트 브라우저 + 시장 컨텍스트 뷰어.

---

## 프로젝트 구조

```
legalize/
├── exposure/              # 핵심 엔진 (7,580줄)
│   ├── schema.py          # 7-layer ontology, edge types, temporal edges
│   ├── lookups.py         # 31 agencies + 29 CFR titles → 55 NAICS
│   ├── etf_exposure.py    # 35 ETFs, holdings-based exposure score
│   ├── mapper.py          # FR doc → ontology pipeline + negative mapping
│   ├── macro_calendar.py  # FOMC/NFP/CPI/GDP/ISM/earnings (128 events)
│   ├── fr_connector.py    # Federal Register API bridge + contamination
│   ├── pipeline.py        # CLI: fetch → map → report
│   ├── holdings.py        # iShares CSV + SPDR XLSX parser
│   ├── replay.py          # Point-in-time historical replay
│   ├── summarizer.py      # 3-level summaries, forbidden language
│   ├── batch.py           # Daily processor (cron, dedup, catch-up)
│   ├── nport.py           # SEC N-PORT XML parser (17 ETF CIKs)
│   ├── event_study.py     # OLS market model, CAR, t-statistics
│   ├── collect_holdings.py# Daily holdings collection CLI
│   └── test_exposure.py   # 11 tests
│
├── fetchers/              # Data collection pipeline
│   ├── __init__.py
│   ├── federal.py         # Canada Federal legislation
│   ├── us_federal.py      # US Code (USLM XML)
│   ├── congress.py        # Congress.gov bill tracker
│   ├── federal_register.py# Federal Register API
│   ├── courtlistener.py   # SCOTUS + Circuit Courts
│   └── canlii_cases.py    # CanLII case law
│
├── ui/                    # Frontend
│   └── feed.jsx           # React feed (cards, heatmap, filters)
│
├── scripts/               # Utilities
│   ├── __init__.py
│   ├── apply_us_patches.py# US Code XML patches
│   ├── patch_federal_tags.py # Federal tag fixes
│   └── collect_holdings.py# Holdings collector wrapper
│
├── data/                  # Runtime data
│   └── holdings/
│       ├── snapshots/     # Daily ETF holdings snapshots
│       └── naics_cache/   # NAICS lookup cache
│
├── docs/                  # Documentation (6 files)
│   │
│   │  ── 핵심 문서 (의사결정할 때 보는 것) ──
│   ├── DESIGN_PRINCIPLES.md     # 설계 원칙 16조 — 제품 정체성, edge 설계, LLM 사용 원칙, 금지 표현 등
│   │                            #   "흔들리지 말 것" 리스트. 불변. 모든 의사결정의 나침반.
│   ├── SPEC.md                  # 프로젝트 전체 스펙 — 타깃 유저 5그룹, event study 방법론 (CAR/t-stat),
│   │                            #   기술 아키텍처 (FastAPI+React), 4-phase 30주 로드맵, 경쟁 분석, 리스크
│   ├── ROADMAP.md               # 실행 로드맵 — Phase 0(완료)~4, 데이터소스 확장 (EDGAR/FRED/USPTO/USITC),
│   │                            #   기술 우선순위. 진행 상태 추적용 (자주 업데이트됨)
│   │
│   │  ── 검증 기록 (왜 이렇게 결정했는지 근거) ──
│   ├── CROSS_VALIDATION.md      # 4-AI(Claude/GPT/Gemini/Meta) 교차검증 결과 — 전원합의 8개, 강한합의 8개,
│   │                            #   부분합의 10개, 독자적 인사이트 9개, 논문 추천 통합. 의사결정 근거 문서.
│   ├── VALIDATION_ARCHIVE.md    # 교차검증에 사용한 프롬프트 6개 + AI에 보낸 원본 프롬프트 전문.
│   │                            #   프로세스 완료된 아카이브. 같은 방식으로 재검증할 때 참고.
│   │
│   │  ── 개발자 가이드 (코드 기여할 때 보는 것) ──
│   └── PIPELINE_GUIDE.md        # 통합 개발자 가이드 — 파이프라인 아키텍처, 데이터소스 & 커버리지,
│                                #   파일 포맷 (YAML frontmatter), 기여 방법, 새 jurisdiction 추가 절차,
│                                #   코드 스타일, 커밋 컨벤션, PR 체크리스트, 모델 패치 이력, 라이선스
│
├── templates/             # GitHub issue/PR templates
│   ├── bug-report.md      # 버그 리포트 양식 (재현 방법, 예상 동작, 환경)
│   └── new-jurisdiction.md# 새 법역 추가 요청 양식 (데이터소스, API, 우선순위 근거)
│
└── .github/workflows/
    └── update.yml         # GitHub Actions (daily sync)
```

---

## 7-Layer Ontology

```
Law → Regulation → Provision → Obligation → RegulatedEntityType → Industry(NAICS) → ETF
```

## Edge Types

| Type | Category | Description |
|------|----------|-------------|
| CITES | Hard | 법이 규정을 인용 |
| IMPLEMENTS | Hard | 규정이 법을 구체화 |
| IMPOSES | Hard | 규정이 의무를 부과 |
| APPLIES_TO | Hard | 의무가 적용 대상 정의 |
| MENTIONS | Soft | 텍스트에 키워드 등장 |
| EXPOSES | Soft | 산업이 ETF에 노출 |
| NOT_RELATED | Negative | 명시적 제외 |

## Obligation Types

| Type | Color (UI) | Meaning |
|------|-----------|---------|
| RESTRICTS | Red | 제한/규제 강화 |
| MANDATES | Blue | 의무 부과 |
| SUBSIDIZES | Green | 보조금/세제 혜택 |
| EXEMPTS | Yellow | 면제 |
| PERMITS | Purple | 허용 |
| MODIFIES_THRESHOLD | Orange | 기준 변경 |

## Quick Start

```bash
# 파이프라인 실행 (최근 3일 규제)
python -m exposure.pipeline --days 3 --significant

# 배치 프로세서 (일일)
python -m exposure.batch --date 2026-04-12

# 밀린 날짜 따라잡기
python -m exposure.batch --catch-up

# Holdings 수집
python -m exposure.collect_holdings

# 테스트
python -m pytest exposure/test_exposure.py -v
```

## 설계 원칙 (흔들리지 말 것)

1. Mapping first, market panel later
2. Hard/soft link 분리
3. Law → ETF 직접 연결 금지
4. 7단계 계층 구조
5. Holdings 기반 ETF exposure
6. Market panel은 context layer
7. "impact", "caused" 금지 → "around the time of", "associated with"
8. Historical replay로 매핑 정확도 검증

## Data Repos

| Repo | Content | Status |
|------|---------|--------|
| legalize-us | US Code (all titles) | Live, daily sync |
| legalize-ca-federal | Canada Federal acts + regs | Live |
| legalize-ca-bc | BC provincial legislation | Live |
| precedent-us | SCOTUS + Circuit Courts | Live, weekly |
| bills-us | Congress.gov bills | Created |
| regulations-us | Federal Register docs | Created |

## 현재 상태 (2026-04-12)

**완료:** 7,580줄, 17 모듈, 35 ETFs, 31 agencies, 55 NAICS, 128 macro events, 11 tests passing

**다음 단계:**
1. Ex-ante / ex-post contamination 분리
2. Contamination calibration loop + placebo test
3. ETF exposure intensity (UI)
4. ETF → regulation 역추적 (Sector Dashboard)
5. Git-diff regulatory viewer
6. Proposed ↔ Final rule matching
7. 100건 human validation
8. Sentiment / 방향성 표시

---

*"이 제품의 첫 버전은 regulation-to-exposure mapping 시스템이어야 하며, 법률 이벤트를 entity type과 industry를 거쳐 ETF proxy에 정직하게 연결하고, 시장 데이터는 이후 context layer로 추가하며, historical replay로 매핑 정확도를 검증한다."*
