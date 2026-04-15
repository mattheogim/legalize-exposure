# Legacy Fetchers (Archived 2026-04-15)

These single-file fetchers have been replaced by the new per-source folder structure.

## Replaced by new structure (`fetchers/{source}/client.py + mapper.py`)
- `federal_register.py` → `fetchers/federal_register/`
- `congress.py` → `fetchers/congress/`
- `courtlistener.py` → `fetchers/courtlistener/`
- `canlii_cases.py` → `fetchers/canlii/` (pending API key)

## Replaced by pipeline fork (`legalize-pipeline/src/legalize/fetcher/`)
- `federal.py` → `legalize-pipeline/src/legalize/fetcher/ca/` (Canada federal)
- `us_federal.py` → `legalize-pipeline/src/legalize/fetcher/us/` (US Code)

## Safe to delete when
- New structure is fully tested and deployed
- No imports reference these files
- Exposure engine regression tests pass without them
