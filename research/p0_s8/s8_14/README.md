# S8.14 — Historical Pregame Provenance & Eligibility Feasibility

**RESEARCH_ONLY / BLOCK_TRAINING.** Offline, standard-library-only. No endpoint calls or source certification.

Run: `python research/p0_s8/s8_14/run_s8_14.py --project-root .`

Optional evidence packet: `--evidence-csv research/p0_s8/s8_14/evidence_intake.csv`. Copy `evidence_intake_TEMPLATE.csv` to that filename and fill fields only when you possess an independently preserved artifact. `source_file` must be a project-relative path; `sha256` must match its bytes. `published_at`, `tipoff_at`, and `captured_at` require timezone-aware ISO 8601 strings. Source timestamps supplied by an operator are **not independently verified** by this script.

Outputs in `results/`: `s8_14_report.json`, `s8_14_sample_games.csv`, `s8_14_source_registry.csv`, `s8_14_evidence_review.csv`. A candidate passing internal checks is only `CANDIDATE_MANUAL_REVIEW`, never VERIFIED. Sample uses up to three games per season (early/mid/late) and excludes the 2019–20 July 30–August 14 restart window; all 88 previously flagged games remain blocked separately.

The source registry is a **research plan**, not evidence of availability. Do not use postgame game logs to infer pregame participants. No training is allowed.
