# RESEARCH: CourtListener API

## Source
- **URL:** https://www.courtlistener.com/api/rest/v4/
- **Auth:** Free API token (sign up at courtlistener.com)
- **Rate limit:** Not formally documented; API v4 for new accounts only
- **License:** Public domain (US court opinions)
- **Format:** JSON REST API

## Key endpoints
- `GET /api/rest/v4/search/?type=o` — Search opinions
- `GET /api/rest/v4/opinions/{id}/` — Single opinion
- Bulk data available at courtlistener.com/help/api/bulk-data/

## Courts tracked
- SCOTUS (scotus)
- 13 Federal Circuit Courts (ca1-ca11, cadc, cafc)

## Fields captured
- case_name, citation, date_filed, court
- opinion text (HTML), judges, docket_number
- precedential_status, per_curiam, joined_by
