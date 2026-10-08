# S7.14 Multi-report generalization audit

Input: **local official NBA injury-report PDFs** under `input_pdfs/` (not committed). Use distinct report versions/dates; do not rename a PDF to make it count twice. A duplicate SHA256 counts once.

Run: `python research/p0_s4/s7_14/run_s7_14.py`.

Outputs: `results/s7_14_report.json`, `s7_14_reports.csv`, `s7_14_review_sample.csv`, per-report candidates/events/checks, and duplicates CSV. All outputs are research-only. No publication timestamp is inferred from filename. This does not constitute independent visual ground truth.

If only one PDF exists, `INSUFFICIENT_DISTINCT_VALID_REPORTS` is the correct result. Acquire two or more additional *actual* official reports before using this as multi-report validation. No guessing of URLs or report publication times.
