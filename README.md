# NBA_MIKE v2

NBA_MIKE v2 is a research-first NBA prediction and betting-decision platform.

## Core objective
Build a system that can prove whether its models are useful. The project does not exist to force daily picks. PASS is a valid and desirable output when evidence is insufficient.

## Current status
- Phase: P0 — Feasibility & Scientific Design
- Milestone: P0-S1 — Project Charter & Research Governance
- Production models: none
- Approved betting markets: none
- NBA data sources: not yet approved
- Status: governance foundation only

## Core principles
1. Data feasibility before model architecture.
2. Baselines before advanced ML.
3. Chronological and information-time validation.
4. Research findings must survive out-of-sample confirmation.
5. Player-performance prediction is separate from betting decisions.
6. Predictive distributions are preferred over point estimates for betting markets.
7. Every production prediction must be reproducible.
8. Track all evaluated predictions, not only recommended bets.
9. Parlays require correlation research; independence cannot be assumed.
10. No model is trusted merely because of a short profitable run.
11. Critical data-quality failures block downstream recommendations.
12. Zero bets is a valid daily result.

## Documentation
- `docs/DEVELOPMENT_JOURNAL.md` — engineering decisions and learning notes.
- `docs/DISCOVERY_JOURNAL.md` — scientific experiments and findings.
- `docs/NEXT_AGENT_HANDOFF.md` — concise current-state file for another AI agent.
- `docs/RESEARCH_GOVERNANCE.md` — rules controlling evidence, validation, promotion, and production.

## Model lifecycle
`RESEARCH -> PAPER -> CANDIDATE -> TRUSTED`

Promotion criteria will be defined before model development. No stage may be skipped merely because recent results look good.

## Immediate next milestone
P0-S2 — Target & Data Feasibility.

No production modeling should begin until Step 0 gates are completed.
