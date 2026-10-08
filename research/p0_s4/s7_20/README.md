# S7.20 — Prospective capture, research only

`python research/p0_s4/s7_20/run_s7_20.py` prints readiness without network access.

To capture an exact official NBA injury PDF URL at the time of execution:

`python research/p0_s4/s7_20/run_s7_20.py --url "https://ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_HH_MMAM.pdf"`

Replace the example URL with an actual observed URL. Do not invent URLs. Captures are stored in `captures/objects/<sha256>.pdf` and append-only `captures/capture_events.jsonl`. Do not edit or delete source objects or event lines. Back up the directory securely. Git-ignore generated captures; commit only source and docs.

**Limitations:** This records the time our program finished retrieval, not the first public publication time. No past PDF becomes historical-as-of eligible by fetching it now. Capture event timestamps depend on the local machine clock and are not independently authenticated. Concurrent processes must not write to the same event log without locking; run one capture at a time. Network failures do not produce a capture event. The storage directory is not tamper-proof or remotely backed up. `BLOCK_TRAINING` remains mandatory until a separate provenance and model-cutoff review is approved.
