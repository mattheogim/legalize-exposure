"""Exposure engine data source fetchers.

Each source has its own package with client.py (HTTP) and mapper.py (data models).
Use registry.py for dynamic dispatch, config.yaml for source configuration.

Sources:
  federal_register/  — FR API (proposed rules, final rules, exec orders)
  congress/          — Congress.gov API (bills, actions)
  courtlistener/     — CourtListener API (court opinions)
  canlii/            — CanLII API (Canadian case law metadata) [pending API key]

Legacy files (to be removed after migration):
  federal_register.py, congress.py, courtlistener.py, canlii_cases.py
  federal.py, us_federal.py  — replaced by pipeline fork
"""
