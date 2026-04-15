# RESEARCH: Congress.gov API

## Source
- **URL:** https://api.congress.gov/v3
- **Auth:** API key required (free at api.congress.gov, or DEMO_KEY for testing)
- **Rate limit:** 1000 req/hr with key, 100/hr with DEMO_KEY
- **License:** Public domain
- **Format:** JSON REST API

## Key endpoints
- `GET /bill/{congress}/{type}` — List bills by Congress and type
- `GET /bill/{congress}/{type}/{number}` — Single bill detail
- `GET /bill/{congress}/{type}/{number}/actions` — Bill action history

## Bill types
hr, s, hjres, sjres, hconres, sconres, hres, sres

## Fields captured
- congress, bill_type, number, title
- introduced_date, sponsor, committees, policy_area
- latest_action, latest_action_date, url

## Tracked action types
IntroReferral, Committee, Floor, BecameLaw, President, Calendars, ResolvingDifferences
