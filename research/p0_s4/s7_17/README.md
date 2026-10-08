# S7.17: Reason geometry recovery

Run `python research/p0_s4/s7_17/run_s7_17.py` after S7.14. The script reads official PDF files and the S7.14 candidate CSVs, and writes a separate `results/s7_17_reason_proposals.csv` and JSON summary. It never overwrites candidates. `PROPOSED_REVIEW_REQUIRED` is not verified ground truth. Run `python research/p0_s4/s7_17/run_s7_17_acceptance.py` and `python -m pytest -q`. No as-of training is permitted.
