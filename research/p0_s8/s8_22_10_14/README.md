# S8.22.10.14 — Injury evidence triage (offline)

This milestone **does not certify injury status, player identity, or historical as-of availability**. It joins the existing 54 S8.22.10.7 candidate rows to S8.22.10.13's automatically verified game IDs and classifies parser/source issues. Team-submission notices are never treated as player injuries. No new scraping or model training.

From project root:

```powershell
python -m pytest .\tests\test_s8221014_injury_triage.py -q
python .\research\p0_s8\s8_22_10_14\run_s8_22_10_14.py --project-root .
python .\research\p0_s8\s8_22_10_14\append_docs.py --project-root .
```

Outputs: `results/2023-11-15/<content-token>/review.json`, `injury_evidence_triage.csv`, `exception_queue.csv`. If multiple candidate inputs exist, use `--ledger <project-local path>` and/or `--game-report <project-local path>`; no arbitrary latest-file fallback. Source inputs are never edited. Original 54-row count and prior game-ID verification are required. Exceptions need evidence-driven resolution, not blanket approvals.

**Governance: RESEARCH_ONLY / BLOCK_TRAINING.**
