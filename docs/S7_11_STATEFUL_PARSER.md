# S7.11 — Stateful NBA injury PDF table reconstruction

Visual evidence (pages 3–7 of the 2026-03-27 06:30 AM report) shows player rows continue across pages while team/game labels are not repeated. This experimental parser carries explicit table-section state across compatible pages, changes team on explicit team rows, changes matchup on explicit matchup rows, and clears prior matchup/team when a new explicit date appears. It does **not** infer team from player identity or use nearest-matchup heuristics.

Column lanes are based on the observed landscape report geometry (841.95pt width) and scale with width; this is a research assumption, not a generic NBA PDF parser. Statuses are only read in the player-status column. `NOT YET SUBMITTED` is logged as a team-level section event, not a player record. Original S7.7 output is not modified. Every generated row is REVIEW_REQUIRED and not eligible for historical training.

Review `s7_11_differences.csv`, particularly conflicts where S7.7 already had a nonempty different field, plus the section event stream and records at page boundaries. A passing unit test is not validation of the actual PDF. Independent timestamp provenance is still missing.
