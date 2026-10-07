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

\n## P0-S3 S2 — Storage & Manifest Standard

**Goal:** Turn the S1 layered architecture into an enforceable storage/provenance contract before building historical collectors.

**Problem:** Prior sports workflows could preserve outputs without a sufficiently strict byte-level chain from source request to raw evidence to downstream artifacts. Cache and evidence also need different semantics.

**Options considered:** loose filenames/README-only provenance; database-first metadata; file-backed JSON manifests plus SHA-256. The JSON-manifest approach is selected for the initial local CPU/Windows workflow because it is transparent, testable, portable, and can later feed a registry/database.

**Selected solution:** immutable `data/raw`, explicit layers, JSON artifact manifests, SHA-256 verification, terminal validation states, explicit quarantine reasons, disposable cache, and replay by artifact identity/hash.

**Files:** `docs/STORAGE_MANIFEST_STANDARD.md`, `src/nba_mike/storage/`, `tests/test_storage_manifest.py`, `research/p0_s3/s2/`.

**Tests:** unit acceptance covers directory contract, manifest round-trip, hash verification, tamper detection, quarantine rules, and cache separation.

**Remaining risks:** This does not yet implement source-specific schema validation, canonical identity resolution, large-data archival, or exact intraday historical truth. Those belong to later P0-S3 stages.

**Next action:** P0-S3 S3 — Canonical Identity System after S2 tests and Git checkpoint pass.

## P0-S3 S3 — Canonical Identity System

**Goal:** Establish stable project-owned identities before canonical player-game datasets or joins are built.

**Problem:** Source IDs are provider-specific, names change/collide, players change teams, and schedule representations can change. Using names or one provider's ID as the universal primary key creates silent join errors and identity drift.

**Options considered:** source IDs as primary keys; normalized names; deterministic composite strings; project-owned canonical IDs with explicit source mappings. Project-owned IDs were selected because they separate stable identity from provider representation and make conflicts explicit.

**Selected solution:** immutable player/team/game canonical IDs; exact (`entity_type`, `source_name`, `source_id`) mappings; aliases that can remain ambiguous; fail-closed remap behavior; separate effective-dated player/team membership; game integrity rules; composite player-game keys; JSON registry replay.

**Files:** `docs/CANONICAL_IDENTITY_STANDARD.md`, `src/nba_mike/identity/`, `tests/test_canonical_identity.py`, `research/p0_s3/s3/`.

**Acceptance:** unit tests and S3 acceptance runner cover stable IDs, source resolution, remap conflict rejection, ambiguous names, trades, game integrity, duplicate player-game detection, and serialization round-trip.

**Remaining risks:** This does not yet prove source records are correct, provide source-specific schema validation, solve historical team-membership timing from authoritative transactions, or establish intraday injury/lineup/market truth.

**Next action:** P0-S3 S4 — Schema Validation & Provenance after S3 tests and Git checkpoint pass.


## P0-S3 S4 — Schema Validation & Provenance Enforcement

### Goal
Add a fail-closed validation boundary between retained source evidence and trusted canonical/downstream data.

### Problem
Successful retrieval is not proof that an artifact is safe. APIs can drift, fields can disappear or change type, duplicate keys can enter datasets, values can be impossible, and retained bytes can be modified after a manifest was written.

### Options considered
1. Validate ad hoc inside each future ingestion script.
   - Advantage: quick locally.
   - Disadvantage: duplicated rules and inconsistent failure behavior.
2. Use only permissive dataframe cleanup.
   - Advantage: convenient.
   - Disadvantage: dangerous because unexpected source changes can be silently normalized.
3. Build a reusable explicit contract validator plus provenance gate.
   - Advantage: deterministic, testable, fail-closed, source-independent.
   - Disadvantage: requires contracts to be maintained deliberately.

### Selected option
Option 3.

### Implementation
Added `src/nba_mike/validation/` with explicit column/schema contracts, row validation, primary-key duplicate detection, schema-drift detection, numeric bounds, parent-manifest eligibility checks, and retained-byte SHA-256 verification.

### Safety behavior
A validation issue produces a non-PASS result. A non-PASS parent or hash mismatch raises a provenance error. The validator does not silently fix records to manufacture a PASS.

### Tests / acceptance
`tests/test_schema_validation.py` covers clean records, missing fields, schema drift, type mismatches, impossible values, duplicate keys, blocked non-PASS parents, verified hashes, and tamper rejection.

`research/p0_s3/s4/run_s4_acceptance.py` provides milestone acceptance evidence.

### Modeling status
No predictive models were trained. S4 is infrastructure only.

### Next action
After S4 is independently run and committed on the user's machine, continue according to the living P0-S3 milestone plan. Do not skip the next documented gate.



## P0-S3 S5 — Canonical Dataset Builder & Raw -> Validated -> Canonical Pipeline

### Goal
Turn the S1-S4 governance architecture into an executable, fail-closed canonical build boundary before any predictive modeling begins.

### Design decision
Use a source-independent canonical player-game builder with explicit column mapping and identity resolution. Require a PASS parent manifest and verified SHA-256 before transformation. Publish a new canonical artifact and parent-linked manifest rather than modifying raw evidence.

### Acceptance criteria
- valid canonical build succeeds;
- non-PASS parent is blocked;
- parent tampering is rejected;
- unresolved identity is rejected;
- duplicate canonical player-game keys are rejected;
- impossible values are rejected;
- canonical manifest preserves parent provenance.

### Modeling gate
Remains CLOSED. S5 proves data construction controls, not predictive validity.


## P0-S3 S6 — Reproducible D-1 Point-in-Time Snapshot System

Goal: convert canonical historical data into deterministic pregame statistical snapshots with a conservative D-1 boundary.

Implemented:
- D-1 cutoff enforcement for statistical history.
- same-day and future statistical exclusion.
- PASS-parent and SHA-256 provenance verification.
- duplicate canonical player-game rejection.
- deterministic logical snapshot hashing.
- explicit target date, cutoff date, and as_of_time metadata.
- explicit ZERO_HISTORY handling for players without eligible prior games.
- snapshot artifact + manifest writing.
- tests and acceptance runner.

Important boundary:
S6 does not establish timestamp truth for injuries, confirmed lineups, news, or sportsbook markets. Those remain independently gated. Predictive model training remains closed.


## P0-S3 INFRA-01 — Project Packaging & Execution Standard

Goal: remove reliance on manual `PYTHONPATH` configuration and make the existing `src/` package layout reproducibly installable in the project virtual environment.

Baseline defect confirmed after S6:
- `python -m pip install -e .` failed because the repository had neither `pyproject.toml` nor `setup.py`.
- `import nba_mike` failed in a standalone Python process after removing `PYTHONPATH`.
- Existing tests still passed (38 tests), showing this was an execution/packaging defect rather than evidence that S2-S6 logic was broken.

Implemented:
- minimal setuptools `pyproject.toml` for the `src/` layout;
- explicit naming contract: repository `nba_mike_v2`, distribution `nba-mike-v2`, import package `nba_mike`;
- editable-install development standard;
- packaging/import regression tests;
- acceptance runner that requires manual `PYTHONPATH` to be absent and runs the full regression suite;
- packaging/execution documentation.

Scope boundary:
INFRA-01 does not change statistical logic, D-1 safety, provenance rules, source feasibility conclusions, or the model-training gate. The original P0-S3 S7 remains the Leakage & Invariant Test Suite.


## P0-S3 S7 — Leakage & Invariant Test Suite

### Goal
Convert the canonical data architecture's leakage and integrity rules into executable fail-closed tests before multi-season historical reconstruction.

### Why this milestone exists
A pipeline can be reproducible and still be scientifically invalid if target-day outcomes, future rows, duplicate identities, malformed team/opponent relationships, or target columns leak into predictive inputs. S7 creates a reusable invariant layer and adversarial tests so these states fail explicitly instead of improving backtests silently.

### Implementation
- Added `src/nba_mike/validation/invariants.py` with D-1, key uniqueness, team/opponent, feature-target separation, snapshot metadata, and zero-history checks.
- Exported invariant primitives through `nba_mike.validation`.
- Added targeted adversarial tests in `tests/test_leakage_invariants.py`.
- Added S7 acceptance runner and persisted acceptance outputs.
- Added `docs/LEAKAGE_INVARIANT_STANDARD.md` and S7 research README.
- Preserved S2-S6/INFRA-01 tests as regression gates.

### Scientific/governance boundary
This milestone does not solve intraday historical injuries, confirmed lineups, news, or market-price truth. Same-day statistical information remains excluded under the conservative D-1 contract. Model training remains prohibited until P0-S3 closes.

### Next milestone
P0-S3 S8 — Historical Reconstruction Sample: run governed reconstruction across multiple seasons/dates/games and compare repeated builds for reproducibility.


## P0-S3 S8 — Historical Reconstruction Sample

### Goal
Move from controlled fixtures to a real multi-season reconstruction audit while preserving the conservative D-1 statistical boundary.

### Design
- Reuse the P0-S2 season anchors: 2019-20, 2023-24, 2025-26.
- Retrieve regular-season player-game evidence using the NBA Stats API dependency already used during feasibility work.
- Deterministically select an internal target date for each season.
- Normalize source rows into minimum canonical game/player/team/date identities.
- Rebuild D-1 state.
- Compare D-1 versus D only as an audit of the temporal boundary.
- Require deterministic rebuild hashes.
- Fail closed on source/API failure or any violated invariant.

### Non-claims
S8 does not solve intraday injuries, confirmed lineup publication timing, news timestamps, sportsbook historical odds/line movement, or ambiguous rotation/stint truth.

### Modeling
Predictive model training remains locked.

### Completion gate
S8 is complete only after:
1. targeted reconstruction tests pass;
2. all three real historical season audits pass;
3. S8 acceptance reports OVERALL PASS;
4. the full project regression suite passes;
5. Git checkpoint is clean.

## P0-S3 S9 — Closeout

### Purpose
Close P0-S3 using accumulated acceptance evidence rather than adding another modeling or betting subsystem.

### Decision rule
P0-S3 may PASS only if the required architecture/contracts exist, the S8 multi-season reconstruction evidence remains PASS, unresolved intraday domains remain explicitly quarantined, the D-1 rule remains documented, and the full regression suite passes.

### Scope of PASS
A PASS applies only to the canonical historical statistical-data foundation. It does not assert exact historical intraday truth, model validity, calibration quality, betting edge, or profitability.

### Unresolved domains carried forward
- injuries/availability timing
- confirmed lineup publication timing
- news timestamps
- sportsbook props/odds/line movement
- authoritative complete rotation/stint truth where ambiguous

### Next-phase principle
Future feature/model work must consume governed point-in-time inputs and must not weaken P0-S3 controls for convenience.

## P0-S4 S1 — Feature & Target Research Plan

### Goal
Define the governed research path from canonical D-1 historical data to model-ready targets and features.

### Architecture
availability -> minutes -> role/usage/opportunity -> stat distribution -> market -> decision

### Key decision
Do not jump directly from P0-S3 into model-family competition. First prove target alignment, feature historical availability, training/prediction parity, minutes/role representation, recent-form behavior, context features, and baseline difficulty.

### Planned sequence
S1 plan; S2 targets; S3 baseline feature registry; S4 minutes/role/opportunity; S5 recent form; S6 context; S7 advanced/tracking audit; S8 governed feature dataset; S9 baseline benchmarks; S10 closeout/model-training gate.

