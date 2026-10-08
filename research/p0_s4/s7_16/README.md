# S7.16 independent source-image review packet

Runs only on local S7.14 PDF and candidate CSV outputs. Samples up to 4 records per PDF, spreads samples across pages, renders source-PDF crops, and writes a BLANK review CSV. The source-image crops are evidence for a human review, NOT automated ground truth. No PDF data is training eligible.

Run: `python research/p0_s4/s7_16/run_s7_16.py`

Review `results/GT*.png` alongside `results/s7_16_samples.csv`. Enter YES, NO, or UNREADABLE in the six `*_correct` columns of `results/s7_16_blind_review.csv`; add notes for mismatches. Leave blank if not reviewed. Run `python research/p0_s4/s7_16/run_s7_16.py --grade` to summarize. The review does not change training eligibility.

**Note:** The crop shows a limited vertical region. For inherited team/date/matchup context, open the original PDF and inspect the preceding section headings and page transitions; a crop alone cannot establish these fields. Reviewer must not infer teams from player rosters. Do not commit the generated images, CSVs, or PDFs.
