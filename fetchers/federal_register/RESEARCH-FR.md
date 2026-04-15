# RESEARCH: Federal Register API

## Source
- **URL:** https://www.federalregister.gov/api/v1
- **Auth:** None required
- **Rate limit:** No documented hard limit; "reasonable use" policy
- **License:** Public domain (US government publication)
- **Format:** JSON REST API

## Document types
- `PRORULE` — Proposed Rule (open for public comment)
- `RULE` — Final Rule (regulation taking effect)
- `NOTICE` — Agency notice (guidance, meetings)
- `PRESDOC` — Presidential Document (executive orders, proclamations)

## Key endpoints
- `GET /documents.json` — Search with filters (type, date, agency, significance)
- `GET /documents/{number}.json` — Single document by number

## Fields captured
- document_number, type, title, abstract
- agency_names, publication_date, effective_on, comments_close_on
- docket_ids, cfr_references, html_url, pdf_url
- significant (boolean), action

## Usage in exposure engine
The exposure engine maps FR documents to industry/ETF exposure via:
- Agency → industry sector (lookups.py)
- CFR title/part → NAICS codes (lookups.py)
- Document type → obligation type (RESTRICTS, MANDATES, etc.)
