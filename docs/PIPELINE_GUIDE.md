# Pipeline & Data Guide

*legalize-ca-pipeline + data repositories — 개발자/기여자를 위한 통합 가이드*

---

## 1. 프로젝트 소개

> Every law a Markdown file. Every amendment a Git commit. Git becomes a legal research tool.

### Why Git for Law?

Legislation is text that changes constantly. Git is designed to track exactly how text changes over time. Traditional legal databases make it hard to see *what* changed, *when*, and *why*. But Git is the most powerful tool ever built for tracking how text changes over time.

This pipeline converts legislation from official government sources into Markdown files with YAML frontmatter, and commits each law with its actual promulgation date. On top of this data, familiar Git commands become legal research tools:

- **`git log`** — full amendment history of any law
- **`git diff`** — exactly what changed between amendments
- **`grep`** — search the entire body of law instantly
- **`git blame`** — which amendment introduced a specific provision
- Anyone can **fork**, **clone**, and **analyze** as open data

### Case law too

Legislation tells you what the law says. Case law tells you what it *means*. This pipeline also fetches court decisions and manages them the same way — Markdown files with YAML frontmatter, committed with the decision date. Search statutes and case law together with the same Git commands.

---

## 2. 데이터 소스 & 커버리지

All legislation and case law data comes from official government sources. Texts are public domain or freely available under open government licenses.

### Legislation

| Status | Jurisdiction | Laws | Languages | Source | Fetcher |
|---|---|---|---|---|---|
| ✅ | 🇨🇦 Federal (EN) | ~8,800 | English | [justicecanada/laws-lois-xml](https://github.com/justicecanada/laws-lois-xml) | `federal.py` |
| ✅ | 🇨🇦 Federal (FR) | ~6,400 | Français | Same | `federal.py` |
| ✅ | 🏔️ British Columbia | 884 | English | [BC Laws CiviX API](https://www.bclaws.gov.bc.ca/civix/) | `bc.py` |
| ✅ | 🇺🇸 US Code | 58 titles | English | [uscode.house.gov](https://uscode.house.gov/download/download.shtml) | `us_federal.py` |
| 🔜 | 🇺🇸 US CFR | — | English | [govinfo.gov](https://www.govinfo.gov) | planned |
| 🔜 | 🇨🇦 Ontario, Alberta, Quebec | — | English/Français | [CanLII API](https://www.canlii.org) | planned |

### Case Law

| Status | Jurisdiction | Cases | Source | Fetcher |
|---|---|---|---|---|
| 🔜 | 🇨🇦 All courts | — | [CanLII API](https://github.com/canlii/API_documentation) | planned |
| 🔜 | 🇺🇸 All courts | 9M+ | [CourtListener](https://www.courtlistener.com/help/api/bulk-data/) | planned |

---

## 3. Data Repositories

| Repository | Contents |
|---|---|
| [legalize-ca](https://github.com/mattheogim/legalize-ca) | Canadian legislation (federal EN/FR + BC) |
| [legalize-us](https://github.com/mattheogim/legalize-us) | US Code (54 titles + appendices) |

---

## 4. Quick Start

### Pipeline Setup

```bash
git clone https://github.com/mattheogim/legalize-ca-pipeline
cd legalize-ca-pipeline
python -m venv venv && source venv/bin/activate
pip install -e .
```

### Data Repository Access

```bash
# Clone Canadian legislation
git clone https://github.com/mattheogim/legalize-ca
cd legalize-ca

# Clone US Code
git clone https://github.com/mattheogim/legalize-us
cd legalize-us
```

### Running the Pipeline

#### Canada — Federal (English + French)

```bash
# Clone Justice Canada's bulk XML (one-time, ~2 GB)
git clone https://github.com/justicecanada/laws-lois-xml

# Run the pipeline
python -m legalize_ca.cli federal \
  --local-xml ./laws-lois-xml \
  --output-dir ./legalize-ca
```

#### Canada — British Columbia

```bash
python -m legalize_ca.cli bc --output-dir ./legalize-ca
```

#### US — Federal (US Code)

```bash
# Download bulk XML from https://uscode.house.gov/download/download.shtml
python -m legalize_ca.cli us-federal \
  --local-xml ./usc-xml/ \
  --output-dir ./legalize-us
```

### Searching the Law

```bash
# Search all federal laws for a keyword
grep -r "reasonable doubt" federal/eng/

# Same search in French
grep -r "doute raisonnable" federal/fra/

# Search BC laws
grep -r "strata" bc/

# Case-insensitive search across everything
grep -ri "charter" federal/eng/
```

### Tracking Amendments

```bash
# Full amendment history of the Criminal Code
git log -- federal/eng/rsc-1985-c-c-46.md

# What exactly changed in the last amendment
git diff HEAD~1 -- federal/eng/rsc-1985-c-c-46.md

# All laws amended in 2024
git log --since="2024-01-01" --until="2024-12-31" --oneline

# State of a law at a specific date
git log --before="2020-01-01" -1 -- federal/eng/rsc-1985-c-c-46.md

# Compare two points in time
git diff abc1234..def5678 -- federal/eng/rsc-1985-c-c-46.md
```

### Analysis Examples

```bash
# Count all federal acts vs regulations (English)
ls federal/eng/rsc-*.md | wc -l    # Acts (RSC = Revised Statutes)
ls federal/eng/sc-*.md | wc -l     # Acts (SC = Statutes of Canada)
ls federal/eng/sor-*.md | wc -l    # Regulations (SOR)

# Longest laws by file size
ls -lS federal/eng/ | head -20

# Laws mentioning "artificial intelligence"
grep -rl "artificial intelligence" federal/eng/
```

### Searching Case Law (planned)

```bash
# Search Canadian Supreme Court decisions for a legal concept
grep -rl "reasonable expectation of privacy" precedent-ca/supreme-court/

# Find all cases citing a specific statute
grep -rl "Criminal Code" precedent-ca/

# Track when a case was added
git log -- precedent-ca/supreme-court/2016scc27.md
```

### Legislation + Case Law Together

```bash
# Find the statute AND the cases that interpret it
grep -rl "s. 11(b)" federal/eng/ precedent-ca/
```

---

## 5. 파일 포맷

### Legislation File Format

Each law is a Markdown file with YAML frontmatter:

```markdown
---
title: Criminal Code
identifier: RSC-1985-c-C-46
jurisdiction: federal
lang: eng
law_type: act
status: in_force
country: ca
last_amended: 2025-01-15
source: https://laws-lois.justice.gc.ca/eng/acts/C-46/
---

# Criminal Code

## Part I — General

### 1 — Short Title

This Act may be cited as the Criminal Code.
```

#### Frontmatter Fields

| Field | Description | Example |
|---|---|---|
| `title` | Official title of the law | `Criminal Code` |
| `identifier` | Canonical citation | `RSC-1985-c-C-46` |
| `jurisdiction` | Jurisdiction slug | `federal`, `bc`, `us-federal` |
| `lang` | Language code | `eng`, `fra` |
| `law_type` | `act` or `regulation` | `act` |
| `status` | `in_force` or `not_in_force` | `in_force` |
| `country` | Country code | `ca`, `us` |
| `last_amended` | Date of last amendment | `2025-01-15` |
| `source` | Official source URL | `https://laws-lois.justice.gc.ca/...` |

### Case Law File Format (planned)

```markdown
---
case_name: R. v. Jordan
citation: 2016 SCC 27
court: Supreme Court of Canada
court_level: supreme
case_type: criminal
decision_date: 2016-07-08
docket: 36068
source: https://www.canlii.org/en/ca/scc/doc/2016/2016scc27/2016scc27.html
---

# R. v. Jordan

## Headnote

The right to be tried within a reasonable time...

## Judgment

...
```

---

## 6. 디렉토리 구조

### Legislation

```
legalize-ca/
├── federal/
│   ├── eng/
│   │   ├── rsc-1985-c-c-46.md         # Criminal Code
│   │   ├── rsc-1985-c-a-1.md          # Access to Information Act
│   │   ├── sc-2001-c-27.md            # Immigration and Refugee Protection Act
│   │   ├── sor-2022-123.md            # Regulations (SOR = Statutory Orders)
│   │   └── ...
│   └── fra/
│       ├── lrc-1985-ch-c-46.md        # Code criminel
│       ├── lrc-1985-ch-a-1.md         # Loi sur l'accès à l'information
│       └── ...
├── bc/
│   ├── sbc-96001.md
│   ├── sbc-96002.md
│   └── ...
└── README.md

legalize-us/
└── us-federal/
    ├── usc-title-1.md                  # General Provisions
    ├── usc-title-18.md                 # Crimes and Criminal Procedure
    └── ...                              # 58 files total
```

### Case Law (planned)

```
precedent-ca/
├── supreme-court/
│   ├── 2016scc27.md                    # R. v. Jordan
│   └── ...
├── federal-court-appeal/
│   └── ...
├── on-court-appeal/                    # Ontario Court of Appeal
│   └── ...

precedent-us/
├── supreme-court/
│   ├── 410-us-113.md                   # Roe v. Wade
│   └── ...
├── 1st-circuit/
│   └── ...
```

---

## 7. 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                          Sources                                 │
│                                                                  │
│  Justice Canada    BC CiviX    US Code     CanLII    CourtListener│
│  (XML)             (REST)     (USLM XML)  (REST)    (Bulk CSV)   │
└────┬──────────────┬──────────┬───────────┬──────────┬────────────┘
     │              │          │           │          │
     ▼              ▼          ▼           ▼          ▼
┌──────────────────────────────────────────────────────────────────┐
│                        Fetchers                                  │
│                                                                  │
│  federal.py     bc.py    us_federal.py  canlii.py  courtlistener│
│  (legislation)  (legis)  (legislation)  (cases)    (cases)      │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              LawDocument / CaseDocument                           │
│                                                                  │
│  YAML frontmatter + Markdown body + raw source                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Writer / Git                                │
│                                                                  │
│  1. Write Markdown file to output directory                      │
│  2. git add + git commit                                         │
│  3. Commit date = promulgation date (laws) or decision date      │
└──────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
legalize-ca-pipeline/
├── legalize_ca/
│   ├── __init__.py
│   ├── cli.py                    # CLI entry point
│   ├── models.py                 # LawDocument, CaseDocument, enums
│   ├── utils.py                  # ThrottledClient, helpers
│   ├── writer.py                 # Markdown writer + Git committer
│   └── fetchers/
│       ├── __init__.py
│       ├── federal.py            # 🇨🇦 Federal legislation
│       ├── bc.py                 # 🏔️ British Columbia legislation
│       ├── us_federal.py         # 🇺🇸 US Code
│       ├── canlii.py             # 🇨🇦 Canadian case law (planned)
│       └── courtlistener.py      # 🇺🇸 US case law (planned)
├── .github/
│   └── workflows/
│       └── update.yml            # Daily automation
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## 8. 기여 가이드

### Ways to Contribute

#### Add a New Jurisdiction

This is the most impactful contribution. Each jurisdiction needs a **fetcher** — a Python module that downloads legislation from an official source and converts it to Markdown.

**Before you start:**

1. Open an issue with the title `[Jurisdiction] Country/Province name`
2. Include: data source URL, license, estimated number of laws, language(s)
3. Wait for a thumbs-up before writing code

**Steps:**

1. Fork the repo and create a branch: `git checkout -b feat/add-jurisdiction-name`
2. Create `legalize_ca/fetchers/your_jurisdiction.py`
3. Add the jurisdiction to `Jurisdiction` enum in `models.py`
4. Add a CLI command in `cli.py`
5. Test with a small sample (`--limit 10`)
6. Open a PR

**Your fetcher should:**

- Yield `LawDocument` objects (for legislation) or `CaseDocument` objects (for case law)
- Handle errors gracefully (skip bad files, log warnings)
- Respect rate limits on government APIs (use `ThrottledClient`)
- Include docstring with data source URL and usage example

#### Fix Bugs or Improve Existing Fetchers

Check the [Issues](https://github.com/mattheogim/legalize-ca-pipeline/issues) tab for known bugs. Some good first issues:

- BC: complex container laws with nested CiviX directories
- Better HTML → Markdown conversion for case law
- Handling edge cases in XML parsing

#### Improve Documentation

- Fix typos, clarify instructions
- Add examples for using Git as a legal research tool
- Translate README sections

### Development Setup

```bash
git clone https://github.com/mattheogim/legalize-ca-pipeline
cd legalize-ca-pipeline
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
```

### Code Style

- Python 3.11+
- Type hints on function signatures
- Docstrings with data source URLs
- `logger.info` for progress, `logger.error` for failures
- No print statements in library code

### Commit Messages

Infrastructure:

```
feat: add Ontario legislation fetcher
fix: handle empty XML response from CiviX API
docs: add contributing guide
```

Legislation commits:

```
add: Criminal Code (RSC-1985-c-C-46)

Source: https://laws-lois.justice.gc.ca/eng/acts/C-46/
Date: 1985-07-01
```

Case law commits:

```
case: R. v. Jordan (2016 SCC 27)

Source: https://www.canlii.org/en/ca/scc/doc/2016/2016scc27/2016scc27.html
Decision: 2016-07-08
Court: Supreme Court of Canada
```

### Pull Request Checklist

- [ ] Fetcher yields valid `LawDocument` or `CaseDocument` objects
- [ ] Tested with `--limit 10` and output looks correct
- [ ] Added jurisdiction to `Jurisdiction` enum
- [ ] Added CLI command
- [ ] Updated README jurisdiction table
- [ ] No API keys or secrets committed

### Data Source Guidelines

We only include data that is:

- From an **official government source** (not third-party aggregators)
- **Freely available** under an open license or public domain
- **Structured** (XML, JSON, or well-formed HTML)

If your jurisdiction's data requires a paid API or is behind a paywall, open an issue to discuss alternatives.

### Questions?

Open an issue or start a discussion. We're happy to help you get started.

---

## 9. 새 Jurisdiction 추가하기

### Step-by-Step

Want to add your province, state, or country? The pipeline is designed to be extended.

#### 1. Create a Fetcher

Add a new file to `legalize_ca/fetchers/`. Your fetcher should yield `LawDocument` (for legislation) or `CaseDocument` (for case law) objects.

#### 2. Add the Jurisdiction Enum

In `models.py`, add your jurisdiction to the `Jurisdiction` enum:

```python
class Jurisdiction(str, Enum):
    FEDERAL = "federal"       # Canada
    BC = "bc"
    AB = "ab"
    US_FEDERAL = "us-federal" # United States
    # Add your jurisdiction here
```

#### 3. Add Utility Methods

If your fetcher downloads binary files (like ZIP archives), ensure `ThrottledClient` in `utils.py` has a `get_bytes()` method:

```python
def get_bytes(self, url: str) -> bytes:
    """GET request returning raw bytes (for zip downloads)."""
    self._throttle()
    resp = self.session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content
```

#### 4. Register the CLI Command

In `cli.py`, add a subcommand for your jurisdiction.

#### 5. Register the Fetcher

In `fetchers/__init__.py`, import your new fetcher:

```python
from .your_jurisdiction import YourJurisdictionFetcher
```

#### 6. Data Source Checklist

- [ ] Official or authoritative data source
- [ ] Freely available (open government license or equivalent)
- [ ] Structured format (XML, JSON, or scrapeable HTML)
- [ ] Volume is manageable (estimate file count)

#### 7. Open a PR

Include: data source URL, license, expected volume, and any known limitations.

---

## 10. 모델 패치 이력

### Already Applied — models.py Changes

The following changes have already been integrated into the codebase for US Federal support:

#### 1. Add to Jurisdiction enum

```python
class Jurisdiction(str, Enum):
    FEDERAL = "federal"       # Canada
    BC = "bc"
    AB = "ab"
    US_FEDERAL = "us-federal" # United States
```

#### 2. Add `get_bytes` to ThrottledClient (in utils.py)

The US fetcher downloads zip files, so ThrottledClient has a `get_bytes()` method:

```python
def get_bytes(self, url: str) -> bytes:
    """GET request returning raw bytes (for zip downloads)."""
    self._throttle()
    resp = self.session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content
```

#### 3. Register the fetcher in `fetchers/__init__.py`

```python
from .us_federal import USFederalFetcher
```

---

## 11. Known Issues

| Issue | Jurisdiction | Description |
|---|---|---|
| Complex container laws | BC | Some acts have deeply nested CiviX directory structures |
| Historical commits | All | Only current consolidated version; per-amendment commits need amendment-level data |
| Unix epoch limit | All | Git doesn't support dates before 1970-01-01; older laws use 1970-01-01 as commit date |

---

## 12. Roadmap

- [x] Canada Federal (EN + FR) — 15,200 laws
- [x] British Columbia — 884 laws
- [x] US Code — 58 titles
- [ ] Canadian case law via CanLII API
- [ ] US case law via CourtListener bulk data
- [ ] US Code of Federal Regulations (CFR)
- [ ] Ontario, Alberta, Quebec legislation
- [ ] US state laws
- [ ] GitHub Actions daily updates
- [ ] Open-source community for jurisdiction plugins

---

## 13. 참고 & 라이선스

### Inspired By

- [legalize-kr](https://github.com/legalize-kr) — Korean legislation + case law as Git
- [Bundesgit](https://github.com/bundestag/gesetze) — German federal law as Git
- [legalize-dev](https://github.com/legalize-dev) — Spanish legislation as Git

### License

**Pipeline code:** MIT License

**Legislation texts:**
- Canadian federal law: Crown Copyright — [Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada)
- BC law text: Crown Copyright (BC) — [Queen's Printer Licence – BC](https://www.bclaws.gov.bc.ca/standards/qplicence.html)
- US law text: Public domain ([17 U.S.C. § 105](https://www.law.cornell.edu/uscode/text/17/105))

**Case law:**
- US case law: Public domain
- Canadian case law: Freely available via [CanLII](https://www.canlii.org)

**Repository structure:** MIT License
