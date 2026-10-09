# S8.19 — Historical publication metadata and capture intake

Offline-only. Requires `research/p0_s8/s8_18/results/s8_18_source_audit.csv` and locally preserved S8.18 artifacts. Run from repo root:

```powershell
python -m pytest -q tests/test_s819_publication_audit.py
python research/p0_s8/s8_19/run_s8_19.py --project-root .
```

Outputs in `research/p0_s8/s8_19/results/`: `s8_19_report.json`, `s8_19_artifact_review.csv`, `s8_19_publication_claims.csv`, `s8_19_capture_review.csv`.

For later manual capture review, copy `capture_intake_TEMPLATE.csv` to `capture_intake.csv`, enter candidate archive URL, timezone-aware UTC capture timestamp, locally saved replay artifact path relative to project root and SHA256. Intake **never** independently certifies a capture: third-party archive identity, capture time and content must be verified separately. Do not insert invented evidence. Never commit source artifacts or sensitive material by default.

If local S8.18 artifacts are unavailable, output reports `ARTIFACT_NOT_PRESENT` and does not claim success. This tool makes **no network requests**, fits no models and always returns `RESEARCH_ONLY / BLOCK_TRAINING`.
