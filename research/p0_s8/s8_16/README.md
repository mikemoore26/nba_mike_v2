# S8.16 — Official evidence acquisition and historical timestamp audit

This milestone **does not certify any source**. Python standard library only. `--project-root` must point at the NBA_MIKE v2 repository.

1. Run `python -m pytest -q tests/test_s816_evidence_acquisition.py`.
2. Run `python research/p0_s8/s8_16/run_s8_16.py --project-root .` for **offline-only** inventory.
3. Opt in to a bounded live official PDF download and Wayback CDX lookup with:
   `python research/p0_s8/s8_16/run_s8_16.py --project-root . --acquire-official --query-wayback`.
4. Re-run without flags to inspect preserved artifacts. Existing artifacts are never overwritten. Network failures are recorded, not treated as historical evidence.
5. Upload the three results: `s8_16_report.json`, `s8_16_artifact_manifest.csv`, `s8_16_archive_candidates.csv`. If practical, also upload the preserved official PDF and CDX JSON for independent review.

Outputs are under `research/p0_s8/s8_16/results/`; source bytes under `research/p0_s8/s8_16/artifacts/`. Do not commit downloaded artifacts by default. Archive CDX results are discovery-only: even a pre-tipoff index timestamp is not proof of the archived bytes' identity, integrity, or independent publication. Current HTTP metadata and embedded PDF timestamps are not historical publication evidence. Full eligible-player population and DNPs remain unresolved. `RESEARCH_ONLY / BLOCK_TRAINING`.
