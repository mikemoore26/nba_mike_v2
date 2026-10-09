# S7.38 — Official article capture and relevance audit

## Purpose
S7.37 found direct official NBA article leads in the existing trade-tracker capture. S7.38 fetches only those preapproved links, checks final URL and content type, stores content-addressed raw HTML, and produces conservative player-name and transaction-keyword relevance labels.

## Limitations
This is article discovery/review, **not** independent transaction corroboration, originating-team verification, or historical publication as-of evidence. No training or downstream evidence promotion is permitted. A keyword match can be unrelated to the specific transaction. Retrieval timestamp is not article publication timestamp. Redirects to other hosts fail closed.

## Outputs
`research/p0_s4/s7_38/results/s7_38_report.json`, `s7_38_review.csv`, `objects/<sha256>.html`. Preserve outputs as untracked research artifacts.
