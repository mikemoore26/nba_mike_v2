# S7.22 internal semantic consistency gate

Run from repository root: `python research/p0_s4/s7_22/run_s7_22.py`.

Reads existing S7.14 candidates and section events, never edits them. Outputs `results/s7_22_semantic_checks.csv` and `results/s7_22_report.json`. Requires all five reports and 475 records for the internal gate. This is NOT independent player-to-team roster ground truth: section events originate in the same PDF parser. Publication timing remains unverified; training is blocked. Do not commit result files or original PDFs.
