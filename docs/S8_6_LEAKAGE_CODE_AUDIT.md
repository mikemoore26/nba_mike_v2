# S8.6 — Feature code leakage triage

**Mode:** research only. **Decision:** block training.

## Scope
Read-only Python source scan of `src/nba_mike` and `research/p0_s4` in the user's actual checkout. Source is not bundled in the patch; local files are inspected when the user runs the tool. Output contains source path, function, line, excerpt, source SHA-256, and severity. Pattern matches are **not confirmed leakage**.

## Investigations
Forward shifts; centered rolling; random cross-validation; fold-global preprocessing; rolling/expanding without proven target exclusion; backfill; postgame columns; participant-universe selection; sorting and date handling. Manual review must inspect split chronology, calibration, feature engineering, joins, and source publication timing.

## Limits
AST-based parsing plus text patterns can miss dynamic pipelines, notebooks, SQL, and indirect leakage. Scanner does not run source code, alter snapshots, train models, or certify availability. A clean scan never authorizes training.

## Next gate
Upload `s8_6_report.json`, `s8_6_findings.csv`, and `s8_6_file_inventory.csv`. Prioritize HIGH review candidates with code context, then audit exact feature/target lineage and chronological OOS folds. The 88 restart games and roster/injury as-of blockers remain open.
