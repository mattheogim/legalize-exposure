# Legalize: Regulatory Diff × Market Impact Platform

**Project Specification & Strategic Plan**
*Version 1.0 — April 11, 2026*

---

## 1. What We Have Today

### 1.1 Pipeline Infrastructure (legalize-ca-pipeline)

A fully operational, open-source pipeline that converts legislation, case law, and regulations from government XML/API sources into Git-tracked Markdown.

**Completed components:**

- **US Code** — All titles from USLM XML, daily sync via GitHub Actions
- **Canada Federal** — 956 acts + 10,600+ regulations (EN), parsed from Justice Canada XML with full subparagraph/clause/subclause depth
- **Canada BC** — 884 provincial laws from CiviX XML
- **US Case Law** — SCOTUS + all 13 Circuit Courts from CourtListener v4, weekly sync
- **Congress.gov Bill Tracker** — Fetches bill introductions, committee referrals, floor votes across all bill types (HR, S, HJRES, SJRES, etc.)
- **Federal Register Tracker** — Proposed rules, final rules, executive orders, significant regulation filter (>$100M economic impact)

**Data repositories:**

| Repo | Content | Status |
|------|---------|--------|
| legalize-us | US Code (all titles) | ✅ Live, daily sync |
| legalize-ca-federal | Canada Federal acts + regulations | ✅ Live |
| legalize-ca-bc | BC provincial legislation | ✅ Live |
| precedent-us | SCOTUS + Circuit Court opinions | ✅ Live, weekly sync |
| bills-us | Congress.gov bill tracking | ✅ Created |
| regulations-us | Federal Register documents | ✅ Created |

**Technical stack:** Python pipeline, GitHub Actions for automated sync, ThrottledClient for API rate limiting, Markdown output for Git diffability.

### 1.2 What Makes This Unique

Every law change produces a **Git diff**. When Congress amends §230 of the Communications Decency Act, our repo shows exactly which words were added, removed, or changed — the same way developers track code changes. No other public dataset offers this.

---

## 2. Product Vision

### 2.1 The Core Idea

**Show regulatory and legislative text changes (Git diffs) alongside their market impact (S&P 500, sector ETFs, individual stocks) in a unified interface.**

A user opens a regulation change and sees:

1. **Left panel:** The exact text diff — red lines deleted, green lines added (Git-style)
2. **Right panel:** Stock/sector price movement in the window around that change — what happened to XLE (Energy) when EPA published a new emissions rule, what happened to XLF (Financial) when the SEC changed reporting requirements

This is **not a chart with annotations**. It is a Git-commit-style view where each "commit" is a regulatory event, and the "CI/CD dashboard" shows market reaction data.

### 2.2 Why This Doesn't Exist

**We researched the competitive landscape extensively.** The combination of Git-diff regulatory text + quantified market impact has no prior art:

| Platform | What it does | What it lacks |
|----------|-------------|---------------|
| Bloomberg Government (BGOV) | Premium legislative tracking for lobbyists | No text diffs, no market correlation, $$$$ |
| FiscalNote | AI-powered regulatory intelligence | No version control, no market data, $$$$ |
| Quorum | Stakeholder engagement + bill tracking | No text-level changes, no financial signals |
| RegInfo.gov | Unified regulatory agenda | Raw data, no analysis, no market connection |
| Academic papers | Event studies on individual regulations | One-off analyses, not a live platform |

**Why nobody has built this:**

1. **Data integration is hard** — Requires both legal text parsing (XML/HTML from dozens of government sources) AND financial data processing. These are separate domains with separate expertise.
2. **Legal text is messy** — Government XML has nested structures (subparagraph → clause → subclause → continued paragraph), inconsistent formatting, and no standard schema across jurisdictions. We've already solved this.
3. **Causal attribution is genuinely difficult** — Markets react to many things simultaneously. Isolating the effect of one regulation requires rigorous statistical methodology (event studies). Most legal-tech companies don't have quant expertise; most quant firms don't parse legal XML.
4. **No business model pressure** — Bloomberg/FiscalNote sell to compliance teams who don't need market data. Quant funds build proprietary tools internally. Nobody sits at the intersection.

**Our advantage:** We've already built the hard part (the legal text pipeline). Adding market data is comparatively straightforward.

---

## 3. Target Users

### 3.1 Primary: Quantitative Finance

- **Who:** Quant traders, systematic fund managers, risk analysts
- **Need:** Alpha signals from regulatory changes before they're priced in
- **Use case:** Screen regulatory events for sector impact, backtest strategies against historical regulation-market correlations
- **Willingness to pay:** High (information asymmetry = profit)

### 3.2 Primary: Compliance Teams

- **Who:** Regulatory compliance officers at banks, pharma, energy companies
- **Need:** Know exactly what changed in a regulation and whether it affects their business
- **Use case:** Track regulatory diffs by sector, get alerts when comment periods open, compare proposed vs. final rules
- **Willingness to pay:** Medium-high (cost of non-compliance >> subscription cost)

### 3.3 Secondary: Academic Researchers

- **Who:** Law professors, economics researchers, political scientists
- **Need:** Structured, machine-readable dataset of legal changes with financial outcome data
- **Use case:** Large-scale event studies, regulatory impact analysis, policy effectiveness research
- **Willingness to pay:** Low individually, but grants and institutional licenses possible

### 3.4 Secondary: Journalism & Advocacy

- **Who:** Investigative journalists, policy nonprofits, advocacy organizations
- **Need:** Track which regulatory changes had outsized market effects, connect lobbying to outcomes
- **Use case:** Stories about regulatory capture, public comment effectiveness, corporate influence
- **Willingness to pay:** Low (but high social impact, good for open-source credibility)

### 3.5 Tertiary: Macro / Global Investors

- **Who:** Global macro fund managers, emerging market analysts
- **Need:** Cross-jurisdiction regulatory comparison, trade policy tracking
- **Use case:** Compare regulatory approaches across US, EU, Korea, Brazil; track tariff/sanction impacts
- **Willingness to pay:** High for multi-jurisdiction coverage

---

## 4. Mathematical & Research Methodology

### 4.1 Event Study Framework

The standard academic approach for measuring stock market reactions to events. This is our core analytical engine.

**Key paper:** MacKinlay, A. Craig (1997). "Event Studies in Economics and Finance." *Journal of Economic Literature*, 35(1), 13-39.

**The model:**

```
Abnormal Return = Actual Return - Expected Return
AR_it = R_it - E[R_it | X_t]
```

Where:
- `R_it` = actual return of stock/sector i on day t
- `E[R_it | X_t]` = expected return based on market model

**Market Model (estimation):**

```
R_it = α_i + β_i × R_mt + ε_it
```

- Estimate α and β using a **120-day estimation window** (t=-130 to t=-11 before event)
- This gives us "normal" behavior for each stock/sector relative to the market

**Abnormal Return (event window):**

```
AR_it = R_it - (α̂_i + β̂_i × R_mt)
```

**Cumulative Abnormal Return (CAR):**

```
CAR_i(t₁, t₂) = Σ AR_it  for t = t₁ to t₂
```

- Standard event window: **t=-1 to t=+1** (3 days: day before, day of, day after)
- Extended windows: t=-5 to t=+5 for slower-moving effects

**Statistical significance:**

```
t-statistic = CAR / σ(CAR)
```

Test whether CAR is significantly different from zero. A regulation that moves a sector ETF by 2% with a t-stat > 2.0 is a meaningful signal.

### 4.2 Sector Mapping

Each regulatory action maps to affected sectors via:

| Signal | Method | Example |
|--------|--------|---------|
| Agency → Sector | Direct mapping | EPA → XLE (Energy), FDA → XLV (Healthcare), SEC → XLF (Financial) |
| CFR Title → Sector | Title classification | Title 40 → Environment, Title 21 → Food/Drug |
| Policy area keyword | NLP matching | "emissions" → Energy, "drug pricing" → Healthcare |
| Bill committee | Committee mapping | Ways & Means → XLF, Energy & Commerce → XLE/XLV |

**Sector ETFs for measurement:**

| ETF | Sector | Key Agencies |
|-----|--------|-------------|
| XLE | Energy | EPA, DOE, FERC |
| XLF | Financial | SEC, CFTC, CFPB, Treasury |
| XLV | Healthcare | FDA, HHS, CMS |
| XLK | Technology | FCC, FTC, Commerce |
| XLI | Industrial | DOT, DOL, OSHA |
| XLU | Utilities | EPA, FERC, NRC |
| XLP | Consumer Staples | FDA, USDA, FTC |
| XLY | Consumer Discretionary | FTC, CPSC |
| XLRE | Real Estate | HUD, EPA, Treasury |
| XLC | Communication | FCC, FTC |
| XLB | Materials | EPA, MSHA |

### 4.3 Additional Papers to Study

| Paper | Topic | Relevance |
|-------|-------|-----------|
| MacKinlay (1997) | Event study methodology | Core framework |
| Binder (1998) | "The Event Study Methodology Since 1969" | Methodological review and extensions |
| Brav & Heaton (2015) | Testing event study methodology | Statistical robustness considerations |
| Stigler (1971) | "The Theory of Economic Regulation" | Regulatory capture theory — why regulations affect stock prices |
| Peltzman (1976) | Wealth effects of regulation | Empirical evidence on regulation → market value |
| Joskow & Rose (1989) | "The Effects of Economic Regulation" | Handbook chapter on regulation and financial markets |
| Baker, Bloom & Davis (2016) | Economic Policy Uncertainty Index | EPU index methodology, newspaper-based measurement |
| Karpoff, Lott & Wehrly (2005) | Environmental regulation event studies | Sector-specific methodology |
| Ramadorai, Veronesi & Zhu (2020) | Regulation and asset prices | Modern framework for policy-asset links |

### 4.4 Beyond Event Studies: Additional Approaches

| Method | Use Case | Complexity |
|--------|----------|------------|
| Difference-in-Differences (DiD) | Compare regulated vs. unregulated sectors | Medium |
| Regression Discontinuity | Rules with sharp thresholds (e.g., firm size cutoffs) | High |
| Sentiment Analysis | NLP on regulatory language (restrictive vs. permissive) | Medium |
| Granger Causality | Does regulatory activity predict sector returns? | Medium |
| GARCH models | Regulatory events → volatility changes (not just price) | High |

---

## 5. Expansion Strategy

### 5.1 Phase 1: US Deep Coverage (Current → 3 months)

We already have the foundation. Next steps:

- **All 50 US states** — Start with CA, NY, TX (largest economies, most regulation). Each state has unique XML/HTML format requiring a custom parser.
- **Sector tagging** — Automated classification of every bill/regulation by affected industry
- **Comment period tracking** — Days until comment deadline, significant rule flagging
- **Historical backfill** — Congress.gov has data back to the 93rd Congress (1973). Federal Register back to 1994 online.

### 5.2 Phase 2: Multi-Jurisdiction (3–6 months)

**legalize-eu (European Union):**
- EUR-Lex API provides JSON + SPARQL endpoint
- EU regulations are directly applicable across 27 member states
- CELEX document numbering enables precise tracking
- MiFID II, GDPR, AI Act — all high-impact for global markets

**legalize-kr (South Korea):**
- Korea lacks a standardized API for legislation
- National Law Information Center (법제처) provides some structured data
- KOSPI sector ETFs for market measurement
- Relevant for semiconductor, automotive, K-content regulation

**legalize-br (Brazil):**
- Câmara dos Deputados has some API access
- Bovespa sector indices for market measurement
- Relevant for commodities, agriculture, fintech regulation

**legalize-jp (Japan):**
- e-Gov (e-Gov法令検索) has structured legal data
- Nikkei sector indices
- BOJ policy, financial regulation

### 5.3 Phase 3: Macro Cross-Jurisdiction View (6–12 months)

The real power emerges when you can compare:

- How did US tariff changes affect KOSPI semiconductor stocks vs. S&P 500 tech?
- When the EU passes AI regulation, what happens to US tech vs. EU tech vs. emerging market tech?
- Global monetary policy divergence: Fed vs. ECB vs. BOJ regulatory approaches

This requires:
- Normalized regulatory event taxonomy across jurisdictions
- Multi-currency, multi-index financial data
- Cross-correlation analysis framework

---

## 6. Visualization Approach

### 6.1 Git-Diff Regulatory Viewer (Core)

The primary interface is NOT a dashboard with charts. It is a **Git commit log** for law:

```
commit a3f8c2d  [SEC]  2026-03-15
Author: Securities and Exchange Commission
Subject: Amendments to Form 10-K Climate Disclosure Requirements

    17 CFR §229.1500 — Climate-Related Disclosures
    
    - Companies must disclose Scope 1 and Scope 2 emissions
    + Companies must disclose Scope 1, Scope 2, and material Scope 3 emissions
    + Disclosure must include third-party attestation for accelerated filers
    - Phase-in period: 2 fiscal years after effective date
    + Phase-in period: 3 fiscal years after effective date
    
    ──── Market Impact ────────────────────────────
    
    XLE (Energy)     : CAR = -1.82%  (t=-1 to t=+1)  p=0.003 **
    XLF (Financial)  : CAR = -0.47%  (t=-1 to t=+1)  p=0.142
    XLK (Technology) : CAR = +0.31%  (t=-1 to t=+1)  p=0.389
    SPY (S&P 500)    : CAR = -0.28%  (t=-1 to t=+1)  p=0.201
    
    Most affected: $XOM -3.1%, $CVX -2.8%, $COP -2.4%
```

### 6.2 Interface Modes

**Mode 1: Commit Log View**
- Chronological feed of regulatory changes
- Each entry shows: agency, date, summary, text diff snippet, sector CAR scores
- Filter by: sector, agency, significance, date range, CAR threshold

**Mode 2: Diff Detail View**
- Full side-by-side or unified diff of the regulatory text
- Market impact panel with CAR charts for each affected sector
- Related events (prior proposed rule, public comments, similar historical regulations)

**Mode 3: Sector Dashboard**
- Select a sector → see all regulatory events affecting it
- Cumulative regulatory impact over time
- Upcoming events (open comment periods, effective dates, pending rules)

**Mode 4: Macro Comparison** (Phase 3)
- Side-by-side view of how different jurisdictions regulate the same topic
- Cross-market impact comparison

### 6.3 Technology Options

| Approach | Pros | Cons |
|----------|------|------|
| Static site (Next.js + GitHub Pages) | Free hosting, fast, Git-native | Limited interactivity |
| React SPA + API | Full interactivity, real-time | Hosting costs, complexity |
| Jupyter notebooks (research mode) | Immediate for academics | Not a product |
| CLI tool (terminal-native) | Fits Git workflow perfectly | Niche audience |

**Recommendation:** Start with a **React SPA** using a Python/FastAPI backend. The financial computation (event studies) runs server-side. The diff viewer is a modified Monaco editor or custom component. Deploy on Vercel/Railway for low cost.

---

## 7. Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React SPA)                     │
│  Diff Viewer · Sector Dashboard · Commit Log · Macro View   │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST / GraphQL
┌──────────────────────────┴──────────────────────────────────┐
│                    API LAYER (FastAPI)                        │
│  /events · /diffs · /impact · /sectors · /search            │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
┌────────┴───────┐ ┌──────┴──────┐ ┌────────┴───────┐
│ EVENT STUDY    │ │ DIFF ENGINE │ │ DATA STORE     │
│ ENGINE         │ │             │ │                │
│ CAR calc       │ │ Git diff    │ │ PostgreSQL     │
│ Sector mapping │ │ Text diff   │ │ (events,       │
│ Statistical    │ │ Proposed →  │ │  diffs,        │
│ testing        │ │ final match │ │  market data)  │
└────────┬───────┘ └──────┬──────┘ └────────┬───────┘
         │                │                 │
┌────────┴────────────────┴─────────────────┴────────────────┐
│                    DATA COLLECTION LAYER                     │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Congress  │ │Fed Reg   │ │EUR-Lex   │ │State     │       │
│  │.gov API  │ │API       │ │API       │ │Leg APIs  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │yfinance  │ │Alpha     │ │Finnhub   │ │FRED      │       │
│  │(prices)  │ │Vantage   │ │(global)  │ │(econ)    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                 GIT-TRACKED LAW REPOS (Existing)             │
│  legalize-us · legalize-ca-federal · legalize-ca-bc          │
│  precedent-us · bills-us · regulations-us                    │
└─────────────────────────────────────────────────────────────┘
```

### 7.1 Financial Data Sources (Free Tier)

| Source | Data | Limits | Global Support |
|--------|------|--------|----------------|
| yfinance | Historical prices, ETF data | Unofficial, no SLA | US, EU, Asia |
| Alpha Vantage | Prices, fundamentals, forex | 500 req/day (free) | Global |
| Finnhub | Real-time quotes, news | 60 req/min (free) | US, EU |
| EODHD | Historical prices, fundamentals | 20 req/day (free) | 70+ exchanges |
| FRED | Economic indicators | 120 req/min | US macro |

**For MVP:** yfinance (historical sector ETF data) + FRED (economic indicators). No API key needed for yfinance. Alpha Vantage as backup.

### 7.2 Event Study Pipeline

```python
# Pseudocode for the core computation

def compute_impact(regulatory_event, sector_etf):
    event_date = regulatory_event.publication_date
    
    # 1. Estimation window: 120 trading days before event
    estimation_returns = get_returns(sector_etf, event_date - 130, event_date - 11)
    market_returns = get_returns("SPY", event_date - 130, event_date - 11)
    
    # 2. Fit market model: R_i = α + β × R_m
    α, β = ols_regression(estimation_returns, market_returns)
    
    # 3. Event window: t=-1 to t=+1
    actual_returns = get_returns(sector_etf, event_date - 1, event_date + 1)
    expected_returns = α + β * get_returns("SPY", event_date - 1, event_date + 1)
    
    # 4. Abnormal returns
    abnormal_returns = actual_returns - expected_returns
    car = sum(abnormal_returns)
    
    # 5. Statistical test
    σ = std(estimation_abnormal_returns)
    t_stat = car / (σ * sqrt(3))  # 3-day window
    p_value = 2 * (1 - t_cdf(abs(t_stat)))
    
    return {
        "car": car,
        "t_stat": t_stat, 
        "p_value": p_value,
        "significant": p_value < 0.05
    }
```

---

## 8. Phased Roadmap

### Phase 1: Event Study MVP (Weeks 1–4)

**Goal:** Prove the concept works with historical US data.

| Task | Week | Detail |
|------|------|--------|
| Event study engine | 1-2 | Python module: CAR calculation, market model estimation, statistical testing |
| Sector ETF mapping | 1 | Agency → ETF lookup table, CFR title → sector mapping |
| Historical backtest | 2-3 | Run event studies on 100+ known significant regulations (2020–2026) |
| Validation | 3-4 | Compare results against published academic studies for known events |
| Static report generator | 4 | Markdown reports showing diff + impact for each event |

**Success criteria:** Reproduce known results (e.g., Dodd-Frank's impact on XLF, ACA's impact on XLV) within reasonable statistical bounds.

### Phase 2: Live Pipeline + Basic UI (Weeks 5–10)

**Goal:** Real-time tracking of new regulatory events with market impact.

| Task | Week | Detail |
|------|------|--------|
| GitHub Actions: daily event study | 5-6 | Auto-compute CAR for new regulations as they publish |
| Comment period countdown | 5 | Track approaching deadlines for public comment |
| Bill pass probability (v1) | 6-7 | Heuristic scoring based on cosponsors, committee speed, history |
| React frontend (diff viewer) | 7-9 | Git-diff style regulatory text viewer |
| React frontend (impact panel) | 8-10 | CAR display, sector heatmap, significance indicators |
| API layer (FastAPI) | 7-8 | REST endpoints for events, diffs, impacts |
| Proposed ↔ final rule matching | 9-10 | Docket ID / RIN matching to track proposal → final |

### Phase 3: Multi-Jurisdiction + Macro (Weeks 11–20)

**Goal:** Expand beyond US, enable cross-market analysis.

| Task | Week | Detail |
|------|------|--------|
| EUR-Lex integration | 11-13 | EU regulations via CELEX API |
| legalize-kr pipeline | 13-16 | South Korea legislation + KOSPI data |
| legalize-br pipeline | 15-18 | Brazil legislation + Bovespa data |
| Cross-jurisdiction comparison | 17-19 | Normalized taxonomy, multi-market CAR |
| Macro dashboard | 18-20 | Global regulatory heatmap, cross-market impact |

### Phase 4: Intelligence Layer (Weeks 21–30)

**Goal:** Predictive signals and advanced analytics.

| Task | Week | Detail |
|------|------|--------|
| NLP regulatory sentiment | 21-23 | Classify language as restrictive/permissive/neutral |
| Bill pass probability (v2: ML) | 23-26 | Train on historical passage data |
| Lobbying crosswalk (OpenSecrets) | 24-27 | Connect lobbying spend to specific bills and outcomes |
| Regulatory diff scoring | 26-28 | Quantify how much a regulation strengthened/weakened |
| Alert system | 28-30 | Email/webhook notifications for significant events |

---

## 9. Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Confounding events (multiple regulations same day) | High | Use sector-specific ETFs (not broad market), control for earnings season, exclude FOMC days |
| Survivorship bias in historical data | Medium | Use point-in-time ETF compositions, not current |
| Low signal-to-noise (most regulations don't move markets) | High | Focus on "significant" regulations (>$100M impact flag from Federal Register), filter by CAR > 1% |
| API rate limits / data availability | Medium | Multiple free data sources, caching, historical backfill |
| International data quality varies | High | Start with US (best data), add jurisdictions incrementally, validate each before publishing |
| Academic rigor challenges | Medium | Publish methodology openly, invite peer review, compare against established results |

---

## 10. Open-Source Strategy

### 10.1 What's Open

- All legal text data (law is public domain)
- All fetcher/parser code (pipeline)
- Event study methodology and code
- Sector mapping tables
- Historical CAR computations

### 10.2 Potential Premium Layer

- Real-time alerts and notifications
- Custom sector/stock screening
- Multi-jurisdiction macro dashboard
- API access with higher rate limits
- Private deployment for compliance teams

### 10.3 Community Building

- GitHub Issues for all 50 US states + 13 Canadian provinces (already created)
- Contributing guide for new jurisdiction parsers
- Academic collaboration program (provide data access for researchers)
- Regular blog posts explaining methodology and findings

---

## 11. Summary

**What we're building:** The first open-source platform that shows regulatory text changes in Git-diff format alongside their quantified market impact using event study methodology.

**Why it matters:** $400B+ is spent annually on regulatory compliance. Trillions in market value shift based on regulatory changes. Yet no tool connects the actual text of what changed with its financial outcome.

**Why we can build it:** We've already solved the hardest part — parsing messy government XML into clean, diffable text across multiple jurisdictions. The financial analysis is well-established academic methodology (event studies) that we're applying to a novel dataset.

**The moat:** Jurisdiction-by-jurisdiction legal parsing is tedious, unglamorous work. By open-sourcing it, we build a dataset that no single company would invest in creating — and that dataset becomes the foundation for everything else.

---

*This document is designed for cross-validation. Please challenge assumptions, identify gaps, and suggest improvements.*
