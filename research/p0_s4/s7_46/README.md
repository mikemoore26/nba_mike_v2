# S7.46 — Independent archive discovery (research only)

Run from the project root after S7.45:

```powershell
python research/p0_s4/s7_46/run_s7_46.py --offline
python research/p0_s4/s7_46/run_s7_46.py
# Optional, only if index entries exist and replay content should be preserved:
python research/p0_s4/s7_46/run_s7_46.py --fetch-captures
```

Input: `research/p0_s4/s7_45/results/s7_45_review.csv` (nine article rows).
Outputs: `results/s7_46_report.json`, `results/s7_46_review.csv`; optional content-addressed HTML under `results/archive_objects/`.

CDX lookup is best effort. A 404/429/403/network failure is `CDX_QUERY_FAILED`, not proof no archive exists. `NO_EXACT_ARCHIVE_CAPTURE_FOUND` is likewise not proof an article was unavailable. All findings remain `RESEARCH_ONLY / BLOCK_TRAINING`. Do not commit downloaded HTML or research output.
