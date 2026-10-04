# NBA_MIKE v2 — Development Journal

## P0-S1 — Project Charter & Research Governance
**Date:** 2026-10-03  
**Status:** READY FOR USER INSTALLATION / ACCEPTANCE CHECK

### Goal
Create the minimum governance foundation for NBA_MIKE v2 before data collection or model development.

### Problem
Earlier sports projects improved over time, but important safeguards such as strict leakage thinking, research/production separation, model promotion, detailed tracking, and concise AI handoff were often strengthened after development had already begun.

### Options considered
1. Start collecting NBA data immediately.
2. Start building points/rebounds/assists models immediately.
3. Establish research governance first, then prove target/data feasibility.

### Selected solution
Option 3.

### Why
Architecture should follow evidence. Before committing to data sources, features, models, or betting markets, NBA_MIKE v2 needs rules that define what counts as trustworthy evidence.

### Implementation
P0-S1 establishes:
- project charter
- research governance
- separate development and discovery journals
- concise future-AI handoff
- Git milestone discipline
- model lifecycle states
- PASS/no-bet philosophy
- baseline-first and time-aware validation rules

### Files introduced
- `README.md`
- `docs/RESEARCH_GOVERNANCE.md`
- `docs/DEVELOPMENT_JOURNAL.md`
- `docs/DISCOVERY_JOURNAL.md`
- `docs/NEXT_AGENT_HANDOFF.md`
- `.gitignore`

### Testing / acceptance
P0-S1 passes when:
- all required files exist
- Git repository is initialized
- Git can see the intended files
- governance explicitly blocks premature model building
- handoff identifies P0-S2 as the next task

### What could go wrong
Governance can become bureaucracy. Documents must stay useful and should not duplicate each other. The handoff in particular must remain concise.

### What I should learn
A serious modeling project starts by defining how it will decide whether an idea is valid. Writing a model is not evidence that the model works.

### Result
Pending local installation and Git checkpoint.

### Next action
P0-S2 — Target & Data Feasibility. Do not train models yet.


## P0-S2 — Target & Data Feasibility (Research Pass 1)
**Date:** 2026-10-03  
**Status:** RECONNAISSANCE COMPLETE — POC TESTING REQUIRED

### Goal
Determine which targets deserve research and whether the data needed for a time-valid NBA prediction system plausibly exists before selecting model architecture.

### What we did
- created an initial target registry;
- separated foundation targets from betting targets;
- researched candidate sources for box scores, play-by-play, tracking, injuries, lineups, odds and props;
- established that different data families have different historical eras;
- formalized AS_OF_TIME reconstruction requirements.

### Important findings
1. Minutes should be treated as a first-class foundation target.
2. Points/rebounds/assists/3PM earn research priority, but not production approval.
3. PRA/PR/PA/RA should compare direct modeling against derivation from joint component distributions.
4. Historical market data is materially shorter than core basketball-stat history.
5. Pregame mutable information such as injuries, starters and odds requires timestamp-aware snapshots.
6. No single provider currently satisfies every requirement without limitations.
7. NBA_MIKE should begin preserving its own prospective snapshots once live ingestion is approved.

### Architecture impact
The working research architecture remains:
Availability -> Minutes -> Role/Opportunity -> Stat Distributions -> Market Probability -> Edge/EV -> Correlation -> Tickets.

This remains a hypothesis, not a locked production architecture.

### What could go wrong
Source documentation can overstate practical accessibility. Endpoints may be unstable, paid tiers may be expensive, historical fields may be incomplete, and timestamps may not support honest backtesting. Therefore documentation evidence is not enough: controlled POC ingestion tests are required.

### What I should learn
Before training a model, prove that its inputs exist at the time the prediction claims to be made. A powerful feature that cannot be reconstructed historically can create a convincing but invalid backtest.

### Next action
P0-S2 Research Pass 2: controlled source proof-of-concept plan and historical reconstruction tests. Still no model training.


## P0-S2 Closeout — Historical Data Feasibility & Leakage Boundary

### Goal
Determine whether NBA_MIKE v2 can build reproducible historical player-game research data without leaking target-game information.

### Result
PASS WITH EXPLICIT LIMITATIONS.

POC-01 through POC-09 established usable core historical box data, play-by-play access, advanced/tracking research availability, historical DateTo behavior, and a successful D-1 leakage boundary. POC-04 correctly rejected naive rotation reconstruction. POC-05 showed period-start lineups can remain ambiguous. POC-06 GameRotation requests timed out and therefore remain unapproved as a required dependency.

POC-09 was the decisive boundary test: for 2025-26, 2023-24, and 2019-20, every target-date player gained exactly one GP from the D-1 snapshot to D, with zero wrong target deltas and zero non-target changes.

### Architecture decision
For initial historical research, a game on D uses statistical features through D-1. Game-D player logs are labels only. Intraday injuries, confirmed lineups, news, and market data remain separate unresolved timestamp problems.

### Why this matters
The project now has evidence for a conservative historical reconstruction rule rather than assuming that current-looking aggregates are safe. This reduces leakage risk before feature engineering and model comparison.

### Next action
P0-S3 — Canonical Data Architecture & Dataset Contract. No model training yet.

---

# P0-S3 S1 — Canonical Data Architecture & Dataset Contract

## Goal
Translate P0-S2 feasibility evidence into an explicit data architecture before building permanent ingestion or model pipelines.

## Problem
The project now knows that core historical NBA statistics, play-by-play, advanced/tracking data, and D-1 historical statistical reconstruction are feasible, but feasibility alone does not define a safe permanent dataset. Without a contract, later code could mix source schemas, targets, timestamps, identities, and unproven intraday information.

## Options considered
1. Start building collectors immediately.
2. Build one large modeling dataset directly from NBA endpoints.
3. Define canonical layers/contracts first, then implement them incrementally.

## Advantages / disadvantages
Option 1 is fast but risks architecture-by-accident.
Option 2 is simple initially but couples research to source schemas and increases leakage/reproducibility risk.
Option 3 adds design work now but creates enforceable boundaries for raw evidence, validation, canonical facts, historical snapshots, features, and targets.

## Selected solution
Option 3.

## Reason
NBA_MIKE v2 exists to prove model usefulness. That requires proving the historical information set first. The data architecture must therefore preserve source evidence, provenance, identity, time boundaries, and feature/target separation.

## Decisions
- Raw source responses are immutable evidence.
- Validated source-shaped data is separate from canonical data.
- Canonical downstream tables use stable NBA IDs, not names, as primary identities.
- Player-game identity is `game_id + player_id`.
- Initial historical statistical features use the proven conservative D-1 boundary.
- Pregame features and realized targets use separate namespaces/layers.
- Intraday injury/lineup/news/market history remains unresolved and quarantined.
- Ambiguous rotation/lineup reconstruction must not be guessed.
- No predictive model training is authorized in P0-S3 S1.

## Files added
- `docs/P0_S3_CANONICAL_DATA_ARCHITECTURE.md`
- `docs/CANONICAL_DATA_CONTRACT.md`
- `docs/P0_S3_MILESTONE_PLAN.md`
- `research/p0_s3/s1/README.md`

## Tests
Design-content checks for required architecture concepts, D-1 boundary, identity keys, provenance, leakage, and explicit no-model-training rule.

## Result
PENDING USER INSTALLATION / VALIDATION.

## Remaining risks
- Exact physical storage/file-format choices are not yet locked.
- Intraday historical injuries, lineups, news, and market data remain unresolved.
- Canonical builder and automated schema/leakage tests do not exist yet.
- Source reliability/caching policy remains to be implemented.

## Next action
P0-S3 S2 — Storage & Manifest Standard.

