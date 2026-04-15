# Legalize Project Roadmap

*Last updated: 2026-04-11*

## Vision

Open-source, Git-tracked pipeline that converts legislation, case law, regulations, and policy signals into structured, diffable data — free for compliance teams, researchers, journalists, quant traders, and advocacy organizations.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SIGNAL / ANALYSIS LAYER                   │
│  Sector tagging · Pass probability · Regulatory diff · NLP  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                      TRACKING LAYER                          │
│  Bill status changes · Comment periods · Committee actions   │
│  Effective date alerts · Amendment detection                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                    DATA COLLECTION LAYER                      │
│  Congress.gov · Federal Register · SEC EDGAR · FRED          │
│  USPTO · USITC · OpenSecrets                                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                    LAW TEXT LAYER (DONE)                      │
│  US Code · CA Federal · BC · SCOTUS · Circuit Courts         │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Foundation (DONE)

Legislation-as-code: raw legal text in Git-tracked Markdown.

| Component | Status | Notes |
|-----------|--------|-------|
| US Code (USLM XML) | ✅ Done | All titles, daily sync via Actions |
| Canada Federal (Justice Canada XML) | ✅ Done | EN acts + regulations, subparagraph/clause/subclause parsing |
| Canada BC (CiviX XML) | ✅ Done | 884 laws, subparagraph/clause/subclause parsing |
| US Case Law — SCOTUS | ✅ Done | CourtListener v4, weekly sync |
| US Case Law — Circuit Courts | ✅ Done | All 13 circuits, weekly sync |
| Canada Case Law (CanLII) | 🔜 Waiting | API key pending |
| GitHub Actions | ✅ Done | Daily legislation + weekly precedent |
| GitHub Issues | ✅ Done | 50 US states + 13 CA provinces/territories |

---

## Phase 1: Legislative Pipeline Tracking (IN PROGRESS)

Track bills and regulations from introduction to enactment.

### 1A — Congress.gov Bill Tracker ✅

Fetcher built and tested. Detects bill introductions, committee referrals, floor votes.

| Feature | Status | Detail |
|---------|--------|--------|
| Fetch recent bills (all types) | ✅ Done | HR, S, HJRES, SJRES, etc. |
| Bill action history | ✅ Done | Full action timeline per bill |
| Committee passage detection | ✅ Done | Detects "reported out" actions |
| Save to Markdown | ✅ Done | `{congress}-{type}-{number}.md` |
| Daily sync via Actions | 🔲 Todo | Add to `update.yml` |
| Incremental fetch (cursor/date) | 🔲 Todo | Only fetch new/updated bills |

### 1B — Federal Register Regulation Tracker ✅

Fetcher built and tested. Detects proposed rules, final rules, executive orders.

| Feature | Status | Detail |
|---------|--------|--------|
| Fetch proposed rules | ✅ Done | Draft regulations open for comment |
| Fetch final rules | ✅ Done | Regulations taking effect |
| Fetch executive orders | ✅ Done | Presidential documents |
| Significant regulation filter | ✅ Done | >$100M economic impact |
| Save to Markdown | ✅ Done | `{type}-{doc_number}.md` |
| Daily sync via Actions | 🔲 Todo | Add to `update.yml` |
| Comment period countdown | 🔲 Todo | Track days until comment deadline |

### 1C — Data Repos

| Repo | Status | Content |
|------|--------|---------|
| `legalize-us` | ✅ Exists | US Code |
| `legalize-ca-federal` | ✅ Exists | Canada Federal legislation |
| `legalize-ca-bc` | ✅ Exists | BC legislation |
| `precedent-us` | ✅ Exists | SCOTUS + Circuit opinions |
| `precedent-ca` | 🔜 Pending | CanLII opinions |
| `bills-us` | 🔲 New | Congress.gov bill tracking |
| `regulations-us` | 🔲 New | Federal Register documents |

---

## Phase 2: Signal Layer

Transform raw data into actionable intelligence.

### 2A — Sector Tagging

Auto-classify bills and regulations by affected industry sector.

| Task | Priority | Approach |
|------|----------|----------|
| Agency → sector mapping | P0 | EPA→Energy, FDA→Healthcare, SEC→Finance, etc. |
| CFR title → sector mapping | P0 | Title 40→Environment, Title 21→Food/Drug, etc. |
| Policy area extraction | P1 | Congress.gov `policyArea` field |
| NLP keyword classification | P2 | Match bill titles/abstracts to GICS sectors |
| Output: `sector_tags.json` | P0 | Machine-readable sector → document mapping |

### 2B — Bill Pass Probability

Score likelihood of a bill becoming law.

| Signal | Weight | Source |
|--------|--------|--------|
| Bipartisan cosponsors | High | Congress.gov cosponsors endpoint |
| Committee passage speed | High | Action timeline analysis |
| Similar bill history | Medium | Historical pass rates by policy area |
| Sponsor seniority/committee chair | Medium | Member data |
| Number of cosponsors | Low-Med | Congress.gov |

### 2C — Regulatory Diff Tracking

Track how regulations change from proposal to final rule.

| Task | Priority | Approach |
|------|----------|----------|
| Match proposed ↔ final rules | P0 | Docket ID / RIN matching |
| Text diff generation | P1 | Git diff between proposal and final |
| Strengthened vs. weakened classification | P2 | NLP comparison of regulatory language |
| Comment influence analysis | P3 | What changed after public comments |

### 2D — Comment Period Timer

| Task | Priority | Detail |
|------|----------|--------|
| Track open comment periods | P0 | `comments_close_on` field from FR API |
| Days remaining calculation | P0 | Simple date math |
| Approaching deadline alerts | P1 | Flag comments closing within 7/14/30 days |
| Significant rule flag | P0 | Highlight >$100M impact rules |

---

## Phase 3: Additional Data Sources

Expand beyond legislation and regulations.

### 3A — SEC EDGAR

Corporate filings, insider trading, enforcement actions.

| Data | API | Use Case |
|------|-----|----------|
| 10-K / 10-Q filings | EDGAR XBRL API | Financial analysis, risk factors |
| 8-K current reports | EDGAR full-text search | Material events, executive changes |
| Insider trading (Form 4) | EDGAR ownership API | Insider sentiment signals |
| Enforcement actions | SEC litigation releases | Compliance risk |
| New rule proposals | SEC regulatory actions | Financial regulation tracking |

### 3B — FRED (Federal Reserve Economic Data)

Economic indicators from the St. Louis Fed.

| Data | Series ID | Use Case |
|------|-----------|----------|
| Federal funds rate | FEDFUNDS | Monetary policy tracking |
| CPI / Inflation | CPIAUCSL | Price level changes |
| GDP growth | GDP | Economic growth |
| Unemployment rate | UNRATE | Labor market |
| Treasury yields | DGS10 | Rate environment |

### 3C — USPTO (Patent Office)

Patent filings and grants for technology trend signals.

| Data | API | Use Case |
|------|-----|----------|
| Patent applications | PatentsView API | Tech sector innovation tracking |
| Patent grants | PatentsView API | IP competitive analysis |
| CPC classification | PatentsView API | Technology area trends |

### 3D — USITC (Trade Commission)

Tariffs, trade investigations, import data.

| Data | Source | Use Case |
|------|--------|----------|
| Tariff schedules (HTS) | USITC HTS API | Tariff change tracking |
| Section 337 investigations | USITC EDIS | Import ban signals |
| Trade remedy cases | USITC case data | Anti-dumping/countervailing duties |

### 3E — OpenSecrets (Lobbying Data)

Lobbying expenditures and political donations.

| Data | Source | Use Case |
|------|--------|----------|
| Lobbying expenditures | OpenSecrets API | Who's lobbying on which bills |
| PAC contributions | OpenSecrets API | Political spending by industry |
| Lobby-bill crosswalk | Custom matching | Connect lobbying to specific legislation |

---

## Phase 4: Target Use Cases

### For Quant / Finance

- Regulation → sector impact signal feed
- Bill pass probability scores
- Comment period → market positioning windows
- EDGAR + FRED + trade data integration
- Executive order tracking (tariffs, sanctions)

### For Compliance Teams

- New regulation alerts by industry
- Comment period deadline tracking
- Regulatory diff: "what changed and does it affect us?"
- Multi-jurisdiction comparison (US federal + states + Canada)

### For Journalism / Research

- Bill sponsor ↔ lobbying crosswalk
- Regulatory language analysis (strengthened vs. weakened)
- Historical trend analysis (regulation density over time)
- Open dataset for academic research

### For Advocacy / Nonprofits

- Bill tracking by policy area
- Alert when bills advance through committee
- Comment period reminders for public participation
- Cross-reference with voting records

---

## Technical Priorities

### Immediate (This Sprint)

1. ~~Fix Federal XML tag handling~~ ✅
2. ~~Build Congress.gov fetcher~~ ✅
3. ~~Build Federal Register fetcher~~ ✅
4. Re-run Federal Canada fetch with tag fixes
5. Update GitHub Actions for bill/regulation sync
6. Create `bills-us` and `regulations-us` data repos

### Short Term (Next 2 Weeks)

7. Incremental fetch with cursor/date filtering
8. Basic sector tagging (agency/CFR → sector mapping)
9. Comment period countdown tracker
10. SEC EDGAR basic fetcher (8-K, enforcement)
11. CanLII integration when API key arrives

### Medium Term (1-2 Months)

12. Bill pass probability scoring (v1: heuristic)
13. Proposed ↔ final rule matching + diff
14. FRED data integration
15. All 50 US state legislation fetchers (start with CA, NY, TX)
16. Patent filing trends (USPTO)

### Long Term (3-6 Months)

17. NLP-based sector classification
18. Lobbying ↔ bill crosswalk (OpenSecrets)
19. Full regulatory diff with strengthened/weakened scoring
20. Trade data integration (USITC)
21. Web dashboard for signal browsing
22. API for programmatic access

---

## Data Repository Structure

```
legalize/
├── legalize-ca-pipeline/          # This repo — all fetcher code
├── legalize-us/                   # US Code (USLM XML → Markdown)
├── legalize-ca-federal/           # Canada Federal acts + regulations
├── legalize-ca-bc/                # BC provincial laws
├── precedent-us/                  # SCOTUS + Circuit Court opinions
├── precedent-ca/                  # Canadian case law (CanLII)
├── bills-us/                      # Congress.gov bill tracking
├── regulations-us/                # Federal Register documents
├── signals/                       # Derived data (sector tags, scores)
│   ├── sector-tags.json
│   ├── bill-scores.json
│   └── comment-deadlines.json
└── data-external/                 # EDGAR, FRED, USPTO, etc.
    ├── edgar/
    ├── fred/
    └── patents/
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Key areas where help is needed:

- US state legislation fetchers (50 states, each with unique XML/HTML format)
- Canadian province/territory fetchers (13 jurisdictions)
- NLP/ML for sector classification and bill scoring
- Frontend dashboard development
- Data validation and quality assurance
