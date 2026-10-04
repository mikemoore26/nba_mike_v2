# P0-S2 POC-01 — Core NBA Historical Data & Identity Test

## Goal
Test practical access to representative historical NBA team/player game logs before NBA_MIKE v2 selects a core data source.

## Why three seasons?
The probe deliberately spans recent, medium-recent, and older modern history:
- 2025-26
- 2023-24
- 2019-20

This is not a full historical download.

## What is measured?
- endpoint success/failure
- request duration
- expected schema
- stable game/team/player identifiers
- missingness in key identity/stat columns
- duplicate player-game keys
- whether each game has exactly two team rows
- small samples and schema snapshots for inspection

## Important
This is research-only. It does not approve `nba_api` or NBA.com as a production source.

Endpoint failure is a valid result. Do not add unofficial scraping workarounds just to make the POC pass.

## Outputs
Generated under `research/p0_s2/poc01/results/`:
- `poc01_report.json`
- `poc01_summary.txt`
- season/team/player sample CSV files
- season/team/player schema JSON files

The results directory is intentionally local research evidence and should not be committed until we review what it contains.
