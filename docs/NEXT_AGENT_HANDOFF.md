# NBA_MIKE v2 — Next Agent Handoff

## Purpose
Research-first NBA prediction and betting-decision platform. The goal is to prove usefulness, not force daily picks.

## Project root
`C:\Users\micha\Coding\python\nba_mike_v2`

## Environment
Windows / PowerShell / Python / Jupyter / Git / CPU-only.

## Current phase
P0 — Feasibility & Scientific Design.

## Current milestone
P0-S1 — Project Charter & Research Governance.

## Completed
Governance starter files have been prepared:
- README
- Research Governance
- Development Journal
- Discovery Journal
- this handoff
- `.gitignore`

No NBA data has been approved/downloaded and no production model has been created.

## Core decisions
- Data feasibility precedes architecture.
- Baselines precede advanced ML.
- Historical evaluation must respect AS_OF_TIME.
- Research and production are separate.
- Model lifecycle: RESEARCH -> PAPER -> CANDIDATE -> TRUSTED.
- Track all predictions once prediction work begins.
- PASS/NO BET is valid.
- Parlays require correlation/joint-probability research.

## Current risks / unresolved decisions
Data sources, historical depth, prediction timestamps, supported markets, historical injury/lineup reconstruction, odds availability, and final model architecture are intentionally unresolved.

## Exact next task
P0-S2 — Target & Data Feasibility:
1. define candidate target registry;
2. investigate reliable historical/current NBA data categories and timestamps;
3. determine historical reconstructability;
4. classify targets GO / GO_WITH_LIMITATIONS / RESEARCH_ONLY / BLOCKED / REJECTED;
5. do not train production models.

## Continuation commands
```powershell
Set-Location "C:\Users\micha\Coding\python\nba_mike_v2"
git status
git log --oneline --decorate -5
```
