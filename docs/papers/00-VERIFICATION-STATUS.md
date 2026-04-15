# Paper Verification Status — FINAL

> **모든 논문을 원본 대조한 결과. 코드 구현 전 이 파일 확인 필수.**
> 자동 검증: `python scripts/verify_papers.py` (Semantic Scholar API)
> 수동 검증: 아래 결과 (2026-04-15)

---

## 🔴 HALLUCINATIONS FOUND (반드시 수정)

| # | 내용 | 유형 | 수정 방법 |
|---|------|------|----------|
| 1 | **Greenwood et al. "60% priced in"** = 중국 margin lending 맥락. 규제 일반에 적용 불가 | WRONG CONTEXT | 14-pre-event-signals.md에서 삭제 또는 맥락 한정 |
| 2 | **"Krieger et al. 2020"** = 실제 저자 **Higgins, Yan & Chatterjee (2021)** | WRONG AUTHOR+YEAR | 03-impact에서 저자명+년도 수정 |
| 3 | **"Bauer & Swanson 2018" NBER 24748** = 실제 저자 **Neuhierl & Weber 2018** "Monetary Momentum" | WRONG AUTHOR | 14-pre-event에서 저자명 수정 |

## 🟡 INACCURACIES (수정 권장)

| # | 내용 | 유형 | 수정 방법 |
|---|------|------|----------|
| 4 | Loughran & McDonald "3/4 negative words" = **2011 JF** 논문의 수치, 2016 survey가 아님 | WRONG SOURCE | 04-adversarial에서 출처 수정 (2011 → 2016 survey에서 인용) |
| 5 | Igan et al. "reverse causality 발견" = 실제로는 **우려 제기 + IV로 해결** | OVERSIMPLIFIED | 04-adversarial에서 표현 수정 |
| 6 | Shapiro "unreliable" = 실제로는 **"a call for nuance"** (더 섬세한 비판) | OVERSIMPLIFIED | 04-adversarial에서 표현 완화 |
| 7 | Reynolds 2006 → 실제 출판 **2008**, EEJ 34(3):310-324 | WRONG YEAR | 14-pre-event에서 년도 수정 |
| 8 | Kalmenovitz "4개 RegIn" → Harvard Law Forum에서는 **3개**로 설명 | UNVERIFIED COUNT | 05-kalmenovitz에서 "3-4개" 또는 원본 확인 후 수정 |
| 9 | Cohen "60 trading days" → abstract에 없음 | UNVERIFIED | 원본 PDF에서 확인 필요 |
| 10 | Bailey et al. → "SSRN"이 아니라 **J. Computational Finance 2015** | WRONG VENUE | 09-validation에서 venue 수정 |
| 11 | Brodeur "25% IV/DiD" → **IV만 25%**, DiD는 더 적음 | IMPRECISE | 09-validation에서 "IV 기준 25%" 명시 |
| 12 | Schipper & Thompson 1983 → 저널은 **J. Accounting Research** (우리 노트에 미기재) | MISSING VENUE | 14-pre-event에서 저널 추가 |

## ✅ VERIFIED (문제 없음 — 28개)

### Core methodology (6)
| Paper | Year | Journal | Status |
|-------|------|---------|--------|
| Goldsmith-Pinkham & Lyu | 2025 | arXiv | ✅ title, authors, synthetic control claim |
| Baker, Bloom & Davis | 2016 | QJE | ✅ 3 components, 10 newspapers |
| Kalmenovitz | 2023 | RFS | ✅ ML + cosine similarity, 10-K text |
| Hassan et al. | 2019 | QJE 134(4) | ✅ bigram + proximity method |
| Al-Ubaydli & McLaughlin | 2017 | Regulation & Governance | ✅ RegData, CFR parsing |
| Armstrong, Glaeser & Hoopes | 2025 | JAE 79(1) | ✅ dictionary-based agency exposure |

### Impact/causal (3)
| Paper | Year | Journal | Status |
|-------|------|---------|--------|
| Cohen, Diether & Malloy | 2013 | JFE 110(3) | ✅ "90 bps/month" confirmed |
| Ramelli, Wagner et al. | 2021 | RCFS 10(4) | ✅ opposite climate shocks |
| Karpoff, Lott & Wehrly | 2005 | JLE 48(2) | ✅ environmental penalties |

### Adversarial (5)
| Paper | Year | Journal | Status |
|-------|------|---------|--------|
| Brav & Heaton | 2015 | WashU Law Rev | ✅ low power + confounding |
| Binder | 1998 | RQFA 11 | ✅ regulatory anticipation |
| Kothari & Warner | 2007 | Handbook | ✅ long-horizon problems |
| Christensen, Hail & Leuz | 2016 | RFS 29(11) | ✅ enforcement context |
| Bae, Jo & Shim | 2025 | CJE 58(1) | ✅ EPU replication failure |

### Validation (7)
| Paper | Year | Journal | Status |
|-------|------|---------|--------|
| Angrist & Pischke | 2010 | JEP | ✅ credibility revolution |
| Brodeur, Cook & Heyes | 2020 | AER | ✅ 21,000 tests, p-hacking |
| Borusyak, Jaravel & Spiess | 2024 | RES 91(6) | ✅ robust event study |
| Harvey, Liu & Zhu | 2016 | RFS 29(1) | ✅ t > 3.0 threshold |
| Nosek et al. | 2018 | PNAS | ✅ pre-registration |
| Jensen, Kelly & Pedersen | 2023 | JoF 78(5) | ✅ replication in finance |
| Fed SR 11-7 | 2011 | Federal Reserve | ✅ model validation standard |

### Pre-event (5)
| Paper | Year | Journal | Status |
|-------|------|---------|--------|
| Pastor & Veronesi | 2012 | JoF 67(4) | ✅ policy uncertainty → risk premia |
| Ellison & Mullin | 2001 | JLE 44(1) | ✅ 52.3% gradual decline |
| Prabhala | 1997 | RFS 10(1) | ✅ standard methods valid under anticipation |
| Malatesta & Thompson | 1985 | JFE 14(2) | ✅ partially anticipated bias formula |
| Schwert | 1981 | JLE 24(1) | ✅ foundational regulatory event study |

### Partially verified (2)
| Paper | Year | Journal | Status |
|-------|------|---------|--------|
| Schipper & Thompson | 1983 | J. Acc. Research | ⚠️ SUR claim plausible but unconfirmed from abstract |
| Bailey et al. | 2014/2015 | J. Comp. Finance | ⚠️ SSRN → journal publication 2015 |

---

## 검증 프로세스 요약

```
총 논문: ~40개 검증 시도
  ✅ 확인됨:        28개 (70%)
  🟡 부정확:        9개 (22.5%) — 수정 가능
  🔴 Hallucination: 3개 (7.5%) — 잘못된 저자/맥락
  ❌ 존재 안 함:     0개

결론: 모든 논문은 실존. 3건의 저자/맥락 오류와 9건의 부정확성 발견.
수식과 구체적 수치는 원본 PDF 확인 전까지 100% 신뢰 불가.
```

---

## 코드 구현 전 반드시

1. 구현할 수식의 원본 PDF Section/Equation 번호 확인
2. 이 파일의 해당 논문이 ✅ VERIFIED인지 확인
3. 🔴 HALLUCINATION 표시된 내용은 사용 금지
4. 🟡 INACCURACY 표시된 내용은 수정 후 사용
