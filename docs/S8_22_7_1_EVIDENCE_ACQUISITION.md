# S8.22.7.1 — Evidence acquisition and preservation

Problem: S8.22.4 overwrites shared output filenames, and S8.22.7 has four missing date-specific provider snapshots. This patch introduces an opt-in, manually run collector with immutable per-run directories and an optional guarded manifest update. It reuses S8.21 for raw bytes and hashes. It never asserts that a zero-row response means no games; it never manufactures independent references, certifies as-of history, or enables model training. Provider entitlement and reference evidence remain open review gates. Capture directories should be treated as local research artifacts, not automatically committed.

Suggested dates for manually authorized retrieval: 2023-11-15, 2024-01-15, 2024-06-20, 2026-10-10. Existing 2023-10-24 provider data must not be overwritten. Independent reference acquisition is a separate manual workflow. Verify game schedule coverage and official source bytes before filling reference_csv.
