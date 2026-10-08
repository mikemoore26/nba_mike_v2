# S7.0 — Pregame source feasibility and leakage audit

Run from repository root:

```powershell
python .\research\p0_s4\s7_0\run_s7_0_acceptance.py
python .\research\p0_s4\s7_0\run_s7_0.py
```

This is **offline**. Candidate providers are explicitly UNVERIFIED; no scraping, credentials, network access or new data are needed. The runner inventories local research files and SHA-256 hashes (under 20 MB). The report is `results/s7_0_feasibility_report.json`.

Optionally place `candidate_observations.csv` alongside this README with columns `source_id,game_id,player_id,field,value,observed_at_utc,available_at_utc,prediction_cutoff_utc`. Times MUST be ISO-8601 with timezone offsets. For revised records, use `is_revised` and `revision_asof_verified` fields; without verified as-of revision provenance the record is rejected. **Do not treat a provider's present-day corrected archive as an as-of historical feed.**

No live data acquisition, model retraining, or production recommendation occurs in S7.0.
