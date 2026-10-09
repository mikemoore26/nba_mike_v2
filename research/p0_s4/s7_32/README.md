# S7.32 — Official NBA article discovery and preservation

Run from repository root after S7.30:

`python research/p0_s4/s7_32/run_s7_32.py --limit 12 --per-player 2`

Reads `s7_30_review.csv`; prioritizes uniquely identified players missing origin teams. Requests NBA search pages, extracts official `/news/` article links, downloads matching HTML snapshots with SHA-256 content addressing and logs failures. Search pages may have no server-rendered links; **zero captured articles is a valid research result**. NBA may block requests. Results and raw HTML snapshots stay untracked. Captures are leads requiring manual semantic verification; nothing is auto-exported to S7.31 or roster/training tables. `--search-fixture-dir` supports offline tests with `<candidate_number>.html` search snapshots.
