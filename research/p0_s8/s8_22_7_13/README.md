# S8.22.7.13 — Offline source-governance review

No network calls or source recapture. Uses the immutable S8.22.7.12 `review.json` and adjacent `source.bin`, and the **exact** S8.22.7.10 governance JSON referenced by the S8.22.7.12 intake. The script checks the hashes and the eight game pairs. If the prior report differs, it fails closed rather than using a merely similar report.

Run `python -m pytest tests/test_s822713_source_governance.py -q` first. Then run `run_s8_22_7_13.py --project-root . --intake-review <review.json> --governance-report <original S8.22.7.10 JSON>`. Results go to `research/p0_s8/s8_22_7_13/results/2023-11-15/`.

Review the output. The outcome is always `BLOCK_TRAINING` and never certifies date completeness or historical as-of. Run `append_docs.py --project-root .` to safely append notes to the primary docs; inspect the diff before staging. Do not commit archived raw evidence or backups by default.
