# S7.41 — Article Evidence Recovery

## Goal
Recover article headlines and article-body paragraphs from hash-verified S7.38 HTML, avoiding S7.39's flattened-page sentence noise. This is a review-only stage, not a transaction truth engine.

## Inputs and safeguards
- S7.38 captured review CSV and SHA256-addressed HTML objects.
- Exact source SHA256 and byte-size validation; reject missing, altered or unexpected verified upstream flags.
- Prefer `og:title`/`twitter:title`, `h1`, and paragraphs inside `article`/`main`. If none exist, use page paragraphs as a lower-confidence fallback.
- Ignore script/style/nav/footer/aside; reject oversized and page-chrome evidence.
- Require full normalized player name and transaction verb in same extracted block. Dedupe per candidate and source.
- Only explicit `acquired PLAYER from TEAM` or `TEAM traded PLAYER to TEAM` syntax produces a review-only direction candidate. Reject mismatch with tracker destination; mark competing proposals for manual review.
- No publication-time proof, independent corroboration, event-date proof, or upstream promotion.

## Outputs
`results/s7_41_review.csv` contains candidate identity, exact article URL/SHA256, evidence type and exact text/SHA256, tentative direction and quality flags. `results/s7_41_report.json` reconciles review-row status counts, reports distinct source hashes checked, and retains `RESEARCH_ONLY / BLOCK_TRAINING`.

## Known limitations
Article HTML templates vary; headlines may be metadata from syndication, and article paragraphs can include related stories. Team aliases can be ambiguous; multi-team transactions are particularly complex. This is a conservative syntactic research aid only. A positive result is not a verified historical roster transaction.
