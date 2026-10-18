# S8.22.10.23 — Historical team evidence intake

This milestone **does not automatically verify** historical teams. It creates a dated evidence review for the 44 candidate IDs from S8.22.10.22A. Source evidence must be authenticated separately before certification.

## Run without external evidence

```powershell
python .\research\p0_s8\s8_22_10_23\run_s8_22_10_23.py --project-root .
```

All 44 rows should classify `NO_DATED_EVIDENCE`. This is the correct fail-closed baseline.

## Optional dated evidence intake

Create a CSV using `historical_team_evidence_template.csv` as a header-only template. One row per independently obtained source assertion. Record the **actual source URL**, document SHA-256, publication timestamp, retrieval timestamp, source type, and claimed date range. Never invent dates, URLs, hashes or player-team associations.

```powershell
python .\research\p0_s8\s8_22_10_23\run_s8_22_10_23.py --project-root . --evidence-csv .\path\to\historical_team_evidence.csv
```

An imported row can produce `DATED_TEAM_MATCH_UNCERTIFIED`, `DATED_TEAM_MISMATCH_REVIEW`, or `CONFLICTING_DATED_TEAM_EVIDENCE`; these are **claims, not certifications**. A season-long roster listing does not establish exact November 15 membership. Source document bytes and independently validated historical effective dates are prerequisites to a future certification milestone.

## Docs and Git

```powershell
python .\research\p0_s8\s8_22_10_23\append_docs.py --project-root .
```

Run the docs updater only after a successful single baseline run; it intentionally fails if multiple separate captures exist to avoid picking evidence arbitrarily. The review output is immutable and under `results/2023-11-15/<token>/`. Never commit private/local source evidence without deliberate review. Training remains blocked.
