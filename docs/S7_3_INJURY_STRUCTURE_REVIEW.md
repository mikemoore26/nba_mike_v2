# S7.3 — Injury report structural review

## Decision
S7.2 extracted 108 status-bearing candidate lines from one eight-page official NBA injury PDF. These are not validated player records. The correct next step is a **manual, page-referenced schema sample**, not automatic interpretation.

## Workflow
1. Freeze SHA256 of the original PDF; preserve the exact source URL.
2. Generate a worksheet with source page, line, raw text, and status token.
3. Manually inspect at least 10 lines spanning multiple pages and statuses; confirm/reject/mark ambiguous. Record game date, team, player, reason only when explicitly supported by PDF.
4. Validate the worksheet, investigate duplicates and continuation lines, and document parsing rules from actual page layout.
5. Only after independently verified manual ground truth should a parser be trained or benchmarked. Historical publication availability is a **separate gate**.

## Constraints
- Filename timestamp is not evidence of historical public availability.
- PDF line extraction can reorder columns and split wrapped rows.
- Passing the worksheet's structural checks does not establish correctness of its annotations.
- No DNP universe or pregame prediction cutoff is established; no training or production promotion.
