# Attack/Defense Report (Contentiousness 8/10)

> **JFE hostile reviewer perspective. Every weakness, honestly assessed.**

---

## Scoreboard

| # | Attack | Rating | Defense Strength |
|---|--------|--------|-----------------|
| 1 | Agency→NAICS = lookup table, no calibration | **DEVASTATING** | "Scaffold for upgrade" — weak |
| 2 | 7-layer ontology mostly hollow | MODERATE | Schema enforces type safety — ok |
| 3 | Event study wrong for regulation (Binder 1998) | **SEVERE** | "We call it observation not causation" — ok |
| 4 | EPA→XLE is trivially obvious | **SEVERE** | Cross-cutting exposure has value — moderate |
| 5 | 35 static ETFs | MODERATE | Live infra exists, not connected — ok |
| 6 | Contamination flags but doesn't correct | MODERATE | find_clean_windows is novel — good |
| 7 | "Exposure not impact" = hedging? | WEAK | **Strongest design choice** — excellent |
| 8 | Yahoo Finance + FR abstracts = thin signal | **SEVERE** | N-PORT parser exists, FR is authoritative — moderate |
| 9 | What does this catch that humans miss? | MODERATE | Cross-cutting + clean windows — good |
| 10 | Just RegData with a dashboard? | **SEVERE** | Real-time pipeline + git diffs = novel — moderate |

---

## DEVASTATING Attacks (Must Fix)

### Attack 1: Agency→NAICS Mapping

**Problem:** `lookups.py` = 31 agencies hardcoded to 55 NAICS. Confidence 0.6/0.7 with zero calibration.
EPA → NAICS 211 (Oil & Gas) treats refinery air quality rule and municipal water test rule identically.
Exclusion rules in mapper.py are an admission the lookup table generates obvious false positives.

**Defense:** These are labeled "LF1/LF2" (Snorkel-style labeling functions). Conservative anchor rules
intended for augmentation by ML/LLM. Every mapping is auditable with provenance.

**Fix needed:** Replace with text-based classification (even TF-IDF > hand-coded lookup).
Or validate empirically: run validation_100.json comparison and report precision/recall.

---

## SEVERE Attacks (Should Fix)

### Attack 3: Event Study Wrong for Regulations

**Problem:** Binder (1998): regulations are anticipated over years. Publication date ≠ information shock.
Market Model is most basic possible. No Fama-French, no robust standard errors (Kolari-Pynnonen 2010).

**Fix needed:** 
- Minimum: FF3 + robust SE
- Better: Synthetic control (Goldsmith-Pinkham 2025)
- Track full event sequence (proposed → comment → final → effective)

### Attack 4: Trivially Obvious

**Problem:** EPA→XLE, SEC→XLF is first-year analyst knowledge.

**Defense:** Value is in automation + cross-cutting (DOL overtime → XHB AND XLI).
Also: 70,000 FR docs/year, no human reads all of them.

### Attack 8: Data Quality

**Problem:** Yahoo Finance (unreliable), FR abstracts (2-3 sentences), NAICS (establishment not firm level).

**Fix needed:** Connect existing N-PORT parser for live holdings. Consider CRSP for research-grade prices.

### Attack 10: Just RegData + Dashboard?

**Problem:** RegData (2017) already does regulation→NAICS with ML. We use hand-coded lookup.

**Defense:** RegData = annual snapshot. We = real-time pipeline + **git diffs** (temporal change measurement).
Real contribution = real-time architecture + version-controlled legislation diffs.

---

## What's Actually Strong

1. **"Exposure not impact" discipline** — methodologically honest (Attack 7: WEAK)
2. **Contamination scoring + find_clean_windows** — novel and useful (Attack 6: MODERATE)  
3. **Architecture separation** (schema, mapper, event_study, replay) — clean and extensible
4. **Language discipline** — "around the time of", never "caused"
5. **Git-as-database for legislation** — nobody else has version-controlled legal diffs

---

## Priority Fix List

| Priority | What | Why | Effort |
|----------|------|-----|--------|
| 1 | **Run validation_100.json precision/recall** | Quantifies Attack 1 damage | 1 day |
| 2 | **Connect N-PORT live holdings** | Fixes Attack 5 + 8 | 2-3 days |
| 3 | **Add FF3 to event study** | Fixes Attack 3 minimum | 1 day |
| 4 | **Text-based NAICS classification** | Fixes Attack 1 + 10 | 1-2 weeks |
| 5 | **Synthetic control implementation** | Fixes Attack 3 fully | 1 week |
