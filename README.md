# Legalize

[![Live docs](https://img.shields.io/badge/docs-legalize--exposure.vercel.app-black?style=flat-square)](https://legalize-exposure.vercel.app)

**Regulation-to-Exposure Mapping Platform**

Law/regulation changes → industry mapping → ETF exposure tracking. Not a market predictor — a regulation-event browser plus a market-context viewer.

---

## Project structure

```
legalize/
├── exposure/              # Core engine (7,580 lines)
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
│   │  ── Core documents (consulted when making decisions) ──
│   ├── DESIGN_PRINCIPLES.md     # 16 design principles — product identity, edge design, LLM usage,
│   │                            #   forbidden phrasing, etc. The "don't waver" list. Immutable. The compass
│   │                            #   for every decision.
│   ├── SPEC.md                  # Full project spec — 5 target user groups, event-study methodology
│   │                            #   (CAR/t-stat), tech architecture (FastAPI+React), 4-phase 30-week roadmap,
│   │                            #   competitive analysis, risks
│   ├── ROADMAP.md               # Execution roadmap — Phase 0 (done) → Phase 4, data-source expansion
│   │                            #   (EDGAR/FRED/USPTO/USITC), technical priorities. Status tracker
│   │                            #   (updated often)
│   │
│   │  ── Validation records (rationale behind decisions) ──
│   ├── CROSS_VALIDATION.md      # 4-AI (Claude/GPT/Gemini/Meta) cross-validation results — 8 unanimous,
│   │                            #   8 strong consensus, 10 partial consensus, 9 unique insights, paper
│   │                            #   recommendations integrated. Source-of-truth for decisions.
│   ├── VALIDATION_ARCHIVE.md    # The 6 prompts used in cross-validation + the original prompts sent to
│   │                            #   each AI. Archived process. Reference when re-running validation.
│   │
│   │  ── Developer guide (consulted when contributing code) ──
│   └── PIPELINE_GUIDE.md        # Unified developer guide — pipeline architecture, data sources &
│                                #   coverage, file formats (YAML frontmatter), contribution flow, how to
│                                #   add a new jurisdiction, code style, commit conventions, PR checklist,
│                                #   model-patch history, license
│
├── templates/             # GitHub issue/PR templates
│   ├── bug-report.md      # Bug-report template (repro, expected behavior, environment)
│   └── new-jurisdiction.md# New-jurisdiction request template (data source, API, priority rationale)
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
| CITES | Hard | Law cites a regulation |
| IMPLEMENTS | Hard | Regulation implements a law |
| IMPOSES | Hard | Regulation imposes an obligation |
| APPLIES_TO | Hard | Obligation defines its target |
| MENTIONS | Soft | Keyword appears in text |
| EXPOSES | Soft | Industry exposed to an ETF |
| NOT_RELATED | Negative | Explicit exclusion |

## Obligation Types

| Type | Color (UI) | Meaning |
|------|-----------|---------|
| RESTRICTS | Red | Restriction / tightening |
| MANDATES | Blue | Imposes an obligation |
| SUBSIDIZES | Green | Subsidy / tax benefit |
| EXEMPTS | Yellow | Exemption |
| PERMITS | Purple | Permission |
| MODIFIES_THRESHOLD | Orange | Threshold change |

## Quick Start

```bash
# Run the pipeline (last 3 days of regulation)
python -m exposure.pipeline --days 3 --significant

# Batch processor (daily)
python -m exposure.batch --date 2026-04-12

# Catch up on missed days
python -m exposure.batch --catch-up

# Collect holdings
python -m exposure.collect_holdings

# Tests
python -m pytest exposure/test_exposure.py -v
```

## Design principles (don't waver)

1. Mapping first, market panel later
2. Hard / soft link separation
3. No direct Law → ETF link
4. 7-layer hierarchy
5. Holdings-based ETF exposure
6. Market panel is a context layer
7. Ban "impact" / "caused" → use "around the time of" / "associated with"
8. Verify mapping accuracy via historical replay

## Data Repos

| Repo | Content | Status |
|------|---------|--------|
| legalize-us | US Code (all titles) | Live, daily sync |
| legalize-ca-federal | Canada Federal acts + regs | Live |
| legalize-ca-bc | BC provincial legislation | Live |
| precedent-us | SCOTUS + Circuit Courts | Live, weekly |
| bills-us | Congress.gov bills | Created |
| regulations-us | Federal Register docs | Created |

## Current status (2026-04-12)

**Done:** 7,580 lines, 17 modules, 35 ETFs, 31 agencies, 55 NAICS, 128 macro events, 11 tests passing.

**Next steps:**
1. Separate ex-ante / ex-post contamination
2. Contamination calibration loop + placebo test
3. ETF exposure intensity (UI)
4. ETF → regulation back-trace (Sector Dashboard)
5. Git-diff regulatory viewer
6. Proposed ↔ Final rule matching
7. 100-case human validation
8. Sentiment / direction indicator

---

*"The first version of this product is a regulation-to-exposure mapping system that honestly connects legal events to ETF proxies through entity types and industries, adds market data only later as a context layer, and verifies mapping accuracy via historical replay."*
