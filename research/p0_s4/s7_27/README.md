# S7.27 — Official transaction source snapshot

Run `python research/p0_s4/s7_27/run_s7_27.py`. The script fetches one official NBA trade tracker page, stores immutable SHA-256 HTML, and emits **unverified textual candidates only**. It does not feed S7.26, prove historical publication, or qualify training. Network failure fails closed.

Offline test: `python research/p0_s4/s7_27/run_s7_27.py --offline-file path/to/saved.html`. Output is in `research/p0_s4/s7_27/results/` (do not commit raw objects by default).
