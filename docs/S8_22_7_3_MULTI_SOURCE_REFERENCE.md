# S8.22.7.3 — Multi-source official game references

## Problem
S8.22.7.2 could associate one evidence receipt with a reference CSV, which would misattribute a multi-game date. Oct 24, 2023 has two independently archived official game pages with different SHA-256 hashes.

## Implemented
- Read-only inspection of one or more local receipts and archived HTML snapshots.
- Validate official URL, file SHA-256, size, date and timestamp.
- Parse structured `SportsEvent` JSON-LD and verify NBA game ID, home/away team abbreviations and timezone-aware start.
- Write a date-specific reference CSV with **per-row** source URL, SHA-256 and retrieval timestamp.
- Reject duplicates, ambiguous or missing game data, wrong dates, missing files, hash mismatches and off-project receipt paths.
- Optional provisional comparison via S8.22.7 `audit_date` and existing team crosswalk; does not change manifest.
- Explicitly report `date_completeness=NOT_CERTIFIED`, `historical_asof=NOT_CERTIFIED`, `BLOCK_TRAINING`.

## Remaining gates
- Verify date-level completeness from independent official schedule evidence; two game pages alone do not prove a two-game schedule.
- Repeat on Nov 15 2023 and Jan 15 2024.
- Independently investigate zero-game dates Jun 20 2024 and Oct 10 2026.
- Historical as-of evidence and player availability remain separate hard blocks.
