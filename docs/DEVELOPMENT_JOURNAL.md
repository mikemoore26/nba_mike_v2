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

## P0-S4 S2 — Target Contract & Outcome Builder

### Goal
Establish unambiguous player-game outcome semantics before feature experiments.

### Initial targets
minutes, points, rebounds, assists, 3PM, plus an explicit played flag derived only from valid observed outcome rows.

### Key decision
Do not treat missing minutes or absent player-game evidence as a zero-stat DNP. Historically complete availability/DNP truth remains a separate upstream research problem.

### Safety
Targets remain labels and cannot be same-game feature inputs. D-1 remains the statistical feature boundary.

## P0-S4 S3 — Baseline Feature Registry

### Goal
Create the governance registry controlling which candidate inputs may proceed into feature-building research.

### Status model
APPROVED_BASELINE, RESEARCH_ONLY, BLOCKED, REJECTED.

### Key interpretation
APPROVED_BASELINE means historically safe enough to test; it does not mean proven predictive.

### Preserved limitations
Intraday injury/lineup truth and historical sportsbook prop lines remain BLOCKED. Advanced/tracking candidates remain RESEARCH_ONLY pending evidence.

## P0-S4 S4 — Minutes / Role / Opportunity Research

### Goal
Begin empirical research on the upstream opportunity process before modeling counting stats.

### Research signals
Prior minutes; rolling 3/5/10 minutes means and volatility; season-to-date minutes; recent-vs-season role delta; role-change heuristic; prior-only per-minute PTS/REB/AST/3PM rates.

### Leakage control
Every rolling/expanding historical statistic is shifted one player-game. Same-game minutes and production remain outcomes.

### Interpretation
S4 compares simple descriptive minutes signals across 2019-20, 2023-24, and 2025-26. Results do not constitute a production model or betting edge.

## P0-S4 S4.1 — Minutes research hardening
Addressed same-calendar-date leakage in the opportunity feature builder, added research tests and segmented historical evaluation. The original S4 report is preserved. Same-date multi-game histories are aggregated at day level, so window semantics are prior dates rather than exact prior games; this remains a documented research limitation. S4.1 results require real-data execution and interpretation before committing.


## S4.1 Research Conclusions — 2026-10-07

- Last-five minutes average led the tested simple baselines in 2019-20, 2023-24, and 2025-26.
- Stable-role last-five MAE: 4.822, 4.908, 4.854.
- Role-change last-five MAE: 5.674, 5.641, 5.721.
- Last-five outperformed last-three in both role groups.
- Role-change flags indicate greater historical prediction uncertainty.
- These are descriptive findings only, not validated betting edges.
- S5 will investigate adaptive windows and chronological robustness.

## P0-S4 S5 — Adaptive form research (pending validation)
Added candidate minutes windows 2/3/4/5/6/8/10/15, season-to-date, and EWM 3/5/10; strict prior-calendar-date feature construction; global prequential selector compared with last-five. Research runner and offline tests included. Pending local acceptance, historical evaluation, review of sample sizes and subgroup errors. No training or betting gate opened.


## P0-S4 S5.1 — Retrospective EWM robustness (pending local run)
Added fixed two-season training / 2025-26 chronological evaluation, date-block paired-error confidence intervals, immutable local source CSV snapshots with SHA-256 manifests, and tests. This is **not** a blind final holdout: 2025-26 outcomes influenced earlier S5 exploration. Results and promotion decision must be recorded after execution. No betting/model promotion.

## P0-S4 S6 — Minutes uncertainty (pending local acceptance)
Implemented expanding, prior-date-only EWM-5 residual intervals and subgroup error
diagnostics. Uses existing S5.1 snapshots and checksum manifest. Research-only.
Record local acceptance, coverage/width by season and group, and unresolved risks
before checkpointing.


## S6 Research Conclusions — 2026-10-07

- Full regression: 100 tests passed.
- Overall 90% interval coverage: 88.9%-89.3%.
- Stable-role coverage: 89.8%-90.2%.
- Role-change coverage: 84.4%-85.3%.
- Mean interval width: approximately 19.7 minutes.
- Role-change undercoverage is consistent across three seasons.
- Pooled calibration is insufficient for reliable subgroup coverage.
- S6 remains RESEARCH_ONLY; no betting promotion.
- Next: S6.1 role-aware uncertainty calibration.

## P0-S4 S6.1 — Role-aware uncertainty (pending local evaluation)
Goal: correct S6 role-change interval undercoverage without unnecessary interval widening. Implemented sequential pooled, group-specific, and shrinkage calibration on frozen S6 forecasts, with prior-date-only error updates and minimum sample safeguards. Pending local acceptance and full regression; record empirical coverage, widths, tests, Git hash, and decision before promotion. Research-only.


## S6.1 Research Conclusions — 2026-10-07

- Full regression: 105 tests passed.
- Role-specific calibration improved role-change coverage toward 90%.
- Shrinkage achieved near-target coverage with slightly narrower intervals.
- Role-specific calibration increased interval width for changing-role players.
- Methods compared on the same S6.1 evaluation rows.
- S6.1 remains RESEARCH_ONLY.
- Next: S6.2 conditional uncertainty and chronological validation.

## S6.2 — Conditional minutes uncertainty (pending local results)
Implemented sequential role/history/volatility calibration with strictly prior-date residuals, sparse-cell fallback, common-row S6.1 comparison, five tests, and research-only reporting. Await acceptance and retrospective results before determining candidate direction. No production or betting promotion.


## S6.2 Research Conclusions — 2026-10-07

- Acceptance passed.
- Full regression: 110 tests passed.
- Conditional uncertainty evaluated on common S6.1 player-games.
- History and volatility improve risk differentiation.
- Role-change coverage does not consistently improve over role-specific calibration.
- 2025-26 volatility-aware coverage: 89.14%; mean width: 19.64 minutes.
- Role-specific baseline coverage: 89.54%; mean width: 20.15 minutes.
- Retain role-specific as reference baseline.
- S6.2 remains RESEARCH_ONLY.
- Next: S6.3 error attribution and calibration stability.
## P0-S4 S6.3 — Error Attribution and Calibration Stability (research)
- Added offline, paired S6.2 diagnostic analysis across three retrospective seasons.
- Added month/season-phase, role, history, volatility coverage and large-error diagnostics.
- Added calendar-date paired bootstrap uncertainty on coverage/width differences.
- Guardrails and six focused tests; no model promotion. Record observed results after running.


## S7.0 — Pregame availability feasibility (pending local execution)
- Goal: audit historical availability and rotation data for point-in-time feasibility before adding features.
- Decision: fail-closed timestamp provenance, offline inventory, candidate source registry, no external-source claims.
- Files: `src/nba_mike/data/pregame_audit.py`, tests, `research/p0_s4/s7_0/`, `docs/S7_0_PREGAME_FEASIBILITY.md`.
- Gates: provider/terms, historical publication/revision timestamps, DNP universe, prediction cutoff, chronological join tests.
- Status: AUDIT ONLY; append local test and runner results after execution.


## S7.1 — Official injury report source registry (pending execution)
Goal: identify candidate official timestamped injury report versions, introduce URL/byte-hash provenance controls, and fail closed when actual publication/availability evidence is missing. No PDF download or parsing, no verified historical as-of coverage, no training authorization. Run acceptance, registry audit, full tests; record actual results and commit only after review.

## P0-S4 S7.2 — Official injury PDF acquisition
Implemented allowlisted, opt-in single-report acquisition; raw PDF SHA256 archive; UTC download timestamp; page-level text and quarantined status-line candidates. Offline tests and no model promotion. Historical as-of source remains unverified.

## P0-S4 S7.3 — Manual injury-report structural review gate
- Added offline source-hashed, page/line-referenced review worksheets and conservative validation.
- Status-bearing lines remain candidates; manual review against original PDF required.
- No historical as-of verification, player-game join, or training authorization.
- Next: inspect annotated samples, develop layout-aware parser, and benchmark against manually verified rows.

## P0-S4 S7.4 — automatic injury report candidates
- Added heuristic line parser with explicit abstention flags and no training authorization.
- Added CLI runner, isolated acceptance tests, and documentation.
- Research-only; verify sample against PDF and audit historical publication before model use.

## P0-S4 S7.5 — Coordinate-aware injury parsing
Implemented header-based PDF word coordinate extraction, reason continuation handling, fail-closed pages, and S7.4 baseline comparison. Research-only; requires actual PDF evaluation.


## P0-S4 S7.6 — Multi-page coordinate layout recovery
- Problem: S7.5 only processed page 1 because later pages lacked repeated headers.
- Choice: reuse header-derived columns across compatible page widths, reset game/team context per page, and quarantine fallback rows.
- Validation: isolated 8-case tests; run full suite and real-PDF evaluation locally.
- Gate: research-only; no historical public availability evidence, no model or betting use.


## P0-S4 S7.7 — Document date context research
- Added conservative unique-document-date inference for rows with explicit matchups.
- Explicit provenance and review flags; no automatic trust promotion.
- Added regression tests for conflicting dates, missing matchups, no dates, and training exclusion.
- Pending: execute on actual March 27 PDF, evaluate page-wise results, validate independent ground truth and publication time.


## P0-S4 / S7.8 — Cross-parser quality audit (research only)
- Implemented read-only S7.4/S7.6/S7.7 comparison by PDF SHA, source page, and normalized player.
- Inventories missing/inferred dates, matchup/team inconsistencies, duplicates, status disagreements, and page coverage.
- Writes JSON diagnostics and a prioritized, page-diverse 12-record review CSV; does not request review of all 108 rows.
- Orphan continuation raw text is not available in existing CSV; cannot reconstruct 50 orphans without additional instrumentation.
- Gate remains BLOCK_TRAINING pending PDF-level validation and independent publication-time proof.
- Run tests and real-file audit before committing. Record actual outputs in journal after execution.

## P0-S4 S7.9 — Context evidence audit (pending local validation)
- Goal: diagnose missing context and orphan lines from S7.8 without silent inference.
- Implementation: read-only official PDF coordinate audit; page-local evidence proposals; reason line trace.
- Tests: synthetic unit tests included; full project regression and real PDF pending user execution.
- Data governance: research only, BLOCK_TRAINING; historical publication unverified.
- Next: inspect real PDF audit and manually verify a small targeted sample before any promotion.


## P0-S4 S7.10 — PDF Table Structure Investigation (pending real-PDF acceptance)
Goal: diagnose why S7.9 had 32 unresolved contexts and 50 reason traces without safe anchors.
Implementation: evidence-only `injury_table_diagnostic.py`, page-line CSV, row-centered context findings, optional PNG renders, SHA consistency gate, isolated tests.
Tests: 13 isolated synthetic tests passed during patch creation; full project suite and real PDF pending local execution.
Decision: do not modify injury records or infer missing context. RESEARCH_ONLY / BLOCK_TRAINING. Historical publication remains unverified.
Next: inspect real-PDF per-page structure and rendered pages, then design narrowly supported parser correction.


## P0-S4 S7.11 — Stateful table reconstruction (pending local acceptance)
- **Goal:** Recover section context across page boundaries without roster-based inference.
- **Evidence:** Visual pages 3–7 show continued player rows and explicit new game/team section boundaries.
- **Implementation:** Add independent stateful research parser, section event ledger, before/after CSV, and tests. No modification to existing S7.7 rows.
- **Safety:** All candidates REVIEW_REQUIRED; as-of training blocked. Column geometry and context inheritance require PDF-specific verification.
- **Pending:** Run acceptance/full suite and inspect actual PDF output, especially changed nonempty fields.


## P0-S4 S7.11 — Stateful table reconstruction (pending local acceptance)
- **Goal:** Recover section context across page boundaries without roster-based inference.
- **Evidence:** Visual pages 3–7 show continued player rows and explicit new game/team section boundaries.
- **Implementation:** Add independent stateful research parser, section event ledger, before/after CSV, and tests. No modification to existing S7.7 rows.
- **Safety:** All candidates REVIEW_REQUIRED; as-of training blocked. Column geometry and context inheritance require PDF-specific verification.
- **Pending:** Run acceptance/full suite and inspect actual PDF output, especially changed nonempty fields.


## S7.12 — Structural verification (pending local acceptance)
- Goal: check S7.11 reconstructed context and provenance without altering the source records.
- Decision: separate research-only audit, no training eligibility.
- Files: `src/nba_mike/data/injury_verify.py`, `tests/test_injury_verify_s712.py`, `research/p0_s4/s7_12/`, `docs/S7_12_INJURY_VERIFICATION.md`.
- Validation: run acceptance, full pytest suite, and real PDF audit; record observed results here after execution.
- Next: review flagged and cross-page samples visually; test additional distinct injury PDFs and publication timestamps.


## P0-S4 S7.13 — Team-name alias correction
- Goal: distinguish genuine team/matchup conflicts from `LA Clippers` naming mismatch.
- Decision: normalize names to NBA abbreviations; do not modify source injury records.
- Tests: run S7.13 acceptance and full suite locally; results pending.
- Real PDF: rerun corrected validator on 2026-03-27 report; results pending.
- Gate: RESEARCH_ONLY / BLOCK_TRAINING; historical publication time not independently verified.


## S7.14 — Multi-report generalization audit (implementation)
- Goal: test whether S7.11/S7.13 behavior generalizes across distinct official injury PDFs.
- Design: local-only SHA-deduplicated batch runner; per-report parser and validator; risk sample; explicit insufficiency and failure states.
- Tests: 13 isolated unit tests included; full project tests and real report run pending on Windows.
- Guardrails: research only, no training, no inferred historical publication timestamp, no original file modifications.
- Next: run on 3+ distinct official reports, review PDF visual ground truth, quantify field accuracy, and investigate any structural failures.


## S7.15 — Official PDF source acquisition (2026-10-08)
Goal: safely collect distinct official NBA injury report PDFs and rerun S7.14. Implemented allowlisted URL manifest, bounded retrieval, hash deduplication, failure logging, provenance ledger, and batch audit. Manifest URLs are candidates, not verified live links. No inference of historical publication time, no training promotion. Verify local full-suite tests and live acquisition results before concluding source coverage.


## S7.16 — Independent source-image review packet (research-only)
- Purpose: move beyond structural self-consistency by generating a deterministic stratified PDF review sample across S7.14 reports.
- Decision: produce source-PDF crops and a blank, explicit review sheet; never mark unreviewed predictions correct.
- Limitations: crops do not establish inherited context; manual inspection of original pages required. Candidate-only sampling cannot measure missing player rows. Publication time remains unverified. Training blocked.
- Acceptance: isolated tests; full-suite verification on user's machine pending.


### S7.17 — Targeted injury reason recovery
- Motivation: S7.16 visual review found 7 missing reasons in 20 samples.
- Design: separate, source-hash-verified, read-only geometry recovery proposals; no overwrites or as-of training.
- Validation: run S7.17 acceptance, full suite, batch report, compare flagged samples; log actual local results after execution.
- Open: visual confirmation of proposals, full-document context, missed-row recall, publication-time verification.


### S7.17.2 — Geometry correction
- Diagnosis: real NBA PDF reason prefix appears ~7 points above player row, continuation ~7 below.
- Fix: guarded two-line band with adjacent-player midpoints; no source record edits.
- Tests: diagnostic-derived coordinate fixtures and neighbor isolation; run full suite locally.
- Gate: RESEARCH_ONLY / BLOCK_TRAINING.


## S7.19 — Local injury report publication provenance audit (2026-10-08)
- Objective: audit independently verifiable historical source availability before as-of modeling.
- Prior finding: S7.18 matched 475/475 reason strings and 475/475 recognizable status positions, but historical publication time is not established.
- Implementation: added non-promoting SHA256/PDF-metadata evidence audit and four isolated regression tests.
- Decision: `RESEARCH_ONLY / BLOCK_TRAINING`; internal PDF metadata, filename timestamps, and current HTTP headers are not historical publication proof.
- Next: inspect audit outputs, pursue authenticated contemporaneous capture evidence, independently validate team/matchup inherited context.

## S7.20 — Historical source feasibility and prospective capture
Goal: separate historical publication evidence from future local retrieval evidence. Reviewed official PDF, archived capture, licensed-feed, and prospective-source options. Chose a minimal exact-URL allowlisted capture with SHA-256 objects, append-only UTC event log, and explicit `BLOCK_TRAINING`. Alternative automatic historical backfill was rejected because current retrieval does not prove historical public availability. Tests cover URL validation, hash/bytes preservation, repeat events, and invalid inputs. Remaining: independent publication evidence, clock authentication, durable backups, full player/team/matchup audit, capture scheduling, and per-cutoff eligibility.


## S7.21 — Context-coordinate validation
Added independent PDF-coordinate audit of date, matchup and team provenance for all five reports. Structural results must be measured locally. Gate remains RESEARCH_ONLY / BLOCK_TRAINING.


## S7.22 — Internal semantic assignment / leakage audit
Added team-in-matchup checks, section-event state comparison, mutation tests, and fail-closed training eligibility. Source: five S7.14 reports. No source rows changed. Independent roster and historical-publication verification remain unresolved.


## S7.23 — Independent historical roster gate scaffold
Implemented fail-closed external roster evidence schema and date-bounded player/team comparison with contradiction tests. Empty evidence means all candidates UNRESOLVED; no claim of independent verification. No training promotion.


## S7.24 — Historical roster evidence staging
Goal: independent date-specific player/team verification. Decision: reject season-level inference and name-only matching; stage only independently attested, date-bounded, stable-ID evidence. Implemented research/p0_s4/s7_24/run_s7_24.py, empty input template, six regression tests. No automatic network acquisition or S7.23 promotion. Training remains blocked. Next: authenticated raw-source acquisition and event chronology.


## S7.25 — NBA Stats season roster acquisition (research only)
Added bounded NBA Stats CommonTeamRoster collector with content-addressed raw JSON, stable NBA IDs, source metadata, strict season validation, fail-closed errors and offline fixtures. Season-level roster rows are candidates only; no date-specific verification, no injury-row modifications, no training. Source access and historical timestamp provenance remain open.


## S7.26 — Transaction chronology evidence gate
Added schema-validated, offline dated transaction ledger, ordered event output, provenance requirements, same-day contradiction review, and fail-closed gates. No source data fabricated, no live scraping yet, no continuous membership claims, no injury row changes. Tests included. Next: authentic transaction source acquisition and evidence hash validation.

## S7.27 — Official transaction source capture
Added fail-closed one-page official NBA trade tracker acquisition, immutable SHA-256 raw HTML, provisional textual candidates, offline tests. Does not authenticate historical publication or create roster intervals. Await live acquisition results before promoting parsing scope.


## S7.28 — Structured trade tracker review (2026-10-08)
Goal: convert 80 S7.27 raw text candidates to inspectable date/team/player rows while preserving strict provenance. Selected deterministic parsing with source SHA verification, explicit `(via ...)` origins, optional stable-ID mapping, no fuzzy matches. Outputs are review-only. Tests: 10 new targeted tests. Pending: live project test and real snapshot report. No model training authorization.

## S7.29 — Automated stable NBA player-ID candidate matching
Goal: link S7.28 candidate names to NBA Stats CommonAllPlayers stable IDs without fuzzy matching. Implemented live/offline directory acquisition, immutable raw snapshot hash, exact name normalization, ambiguity and provenance checks, test coverage, fail-closed governance. No roster/date promotion; validate full-suite and live response locally before milestone closure.

## S7.30 — Transaction identity and team structure review
Implemented strict S7.28/S7.29 source-provenance join, deterministic flags for missing origin, unresolved player IDs, same-team and same-day multi-destination candidates, and fail-closed review output. No transaction or historical roster membership promoted. Validate complete test suite and actual source results before closeout.

## S7.31 — Independent origin evidence review gate
Added optional SHA-256 checked independent source excerpt staging and per-candidate NBA search discovery links, strict candidate joins, multi-source conflict flags and research-only reports. Missing evidence stays unresolved. No origin or roster promotion. Run full tests and review real output before closing milestone.

## S7.32 — Official article discovery and immutable capture

Goal: move beyond empty evidence templates by attempting official NBA article discovery for S7.30 missing-origin candidates. Introduced rate-limited acquisition, SHA-256 source snapshots, failure reporting, and tests for URL allowlisting, deduplication, missing links, redirect checks, and fail-closed training gate. Captured article is a research lead, not a verified transaction. No promotion to S7.31/S7.26/S7.23. Await local full-suite tests and real acquisition report.


## S7.33 — Offline article relevance audit
Goal: explain repeated S7.32 article captures and acquisition eligibility gap. Implemented SHA-256 snapshot verification, exact player mention detection, nearby trade-term and team-mention review, duplicate URL accounting, and eligibility decomposition. All extracted claims remain research leads. Run `python -m pytest -q` and `python research/p0_s4/s7_33/run_s7_33.py`; record observed counts. No promotion to S7.31/S7.26/S7.23. Status: RESEARCH_ONLY / BLOCK_TRAINING.


## S7.34 — Targeted official article discovery (implementation)

**Starting evidence:** S7.33: 457 tests passed, commit `28285a4`; 24/24 captures PLAYER_NOT_FOUND, only two URLs, 71 missing origins (63 eligible, eight excluded).

**Problem:** NBA site search returned repeated unrelated pages. **Options:** repeat site search; manual collection; targeted external index for discovery with official-source allowlist. **Selected:** RSS search as discovery-only, official NBA article capture, strict full-name + trade-vocabulary relevance gate. This reduces false confidence while preserving reproducible search/article snapshots.

**Files:** `research/p0_s4/s7_34/run_s7_34.py`, README, `tests/test_s734_discovery.py`, `docs/S7_34_DISCOVERY_REPAIR.md`. **Outputs:** `s7_34_review.csv`, `s7_34_report.json`, content-addressed objects. **Testing:** local targeted tests included; run full suite and live research acquisition on user's Windows machine. **Risk:** search engine blocks/irrelevant hits, no historical as-of publication proof. **Decision:** `RESEARCH_ONLY / BLOCK_TRAINING`; do not export evidence automatically. **Next:** use measured relevant leads to prioritize semantic origin review or improve source discovery.


## S7.35 — Offline source discovery diagnosis
Added an offline, hash-checked diagnostic for S7.34 captured search responses. It measures RSS format, item links, and official-source filter exclusions without fetching new material. User must run full suite and review live diagnostic before selecting a repair. RESEARCH_ONLY / BLOCK_TRAINING.


## S7.36 — Offline rejected URL classification (pending local execution)
Goal: explain 114 S7.35 rejected RSS links by source host and URL filter reason. Decision: offline hash-verified audit before changing source policy. Added run_s7_36.py, focused tests, README, and classification design. Local user execution and actual host counts pending. No evidence promotion; RESEARCH_ONLY / BLOCK_TRAINING.



## S7.37 — Controlled official tracker-link discovery
- Motivation: S7.36 found 114 external Bing results and zero NBA-hosted articles; S7.27 official tracker HTML embeds official article links.
- Implementation: SHA-verified offline HTML anchor extraction; NBA host and team/news allowlist; conservative player-token candidate matching; review-only CSV/catalog/report.
- Safety: no network, no origin inference, no historical publication verification, no training promotion.
- Run: `python research/p0_s4/s7_37/run_s7_37.py`; tests: `python -m pytest -q`.
- Next: inspect results, then independently fetch and verify promising articles in S7.38.


## S7.38 — Official NBA announcement capture (research only)
Goal: replace ineffective generic search discovery with direct article leads from the SHA-verified official trade tracker. Added restricted NBA-only fetching, safe redirects, SHA-addressed immutable captures, player-name/transaction relevance review, failure reporting, tests, and documentation. No historical publication verification or origin-team promotion; BLOCK_TRAINING. Run `python research/p0_s4/s7_38/run_s7_38.py --limit 12`. Record actual local results before any further decision.


## S7.39 — Offline transaction statement extraction

Added SHA256-gated extraction of candidate player and transaction verbs in the same visible-text sentence, with team mention annotations and exact statement review rows. Fail closed on missing or modified article objects. No verified origin or historical publication proof; RESEARCH_ONLY / BLOCK_TRAINING.


## S7.40 — Evidence Quality and Direction Review (2026-10-09)
- **Goal:** Improve precision of S7.39 transaction statements before any origin-team verification.
- **Problem:** 22 review rows, 21 same-sentence matches, but S7.39 status counts summed to 23; some sentences contained navigation/long unrelated team lists.
- **Alternatives:** Expand acquisition immediately (rejected: propagates noise); infer direction from team co-mentions (rejected: unsound); conservative offline direction proposals (chosen).
- **Implementation:** `research/p0_s4/s7_40/run_s7_40.py`, review CSV and JSON; strict schema and verification checks, quality flags, deduplication, limited direction regex, tracker destination conflicts, per-candidate conflict checks, reconciled counts.
- **Validation:** 12 focused tests passed in patch build; run complete repository suite locally before commit.
- **Unresolved:** Confirm real captured evidence precision, investigate any zero-proposal outcome, independent transaction corroboration, historical as-of publication proof.
- **Governance:** `RESEARCH_ONLY / BLOCK_TRAINING`; zero automatic promotion.


## S7.41 — Offline article evidence recovery
Goal: recover headline and paragraph-level transaction leads from already captured S7.38 HTML after S7.40 yielded one direction proposal and 9 quality rejections. Decision: prefer source-preserving, SHA256-checked block extraction over flattened sentence scanning; keep all evidence review-only. Added `research/p0_s4/s7_41/run_s7_41.py`, README, tests and documentation. Focused development tests: 14 passed. Full-suite and live-data results must be verified on the user's machine. Risks: page templates, metadata headlines, alias ambiguity, article publication as-of unknown. Next: evaluate recovered rows and compare with S7.40; do not promote or train.


## S7.42 — Transaction direction and source-family review
Added offline multi-player transaction direction parsing, team alias handling, evidence SHA verification, article-object verification, tracker-destination conflict gate, source-family grouping, and explicit report reconciliation. All results are RESEARCH_ONLY / BLOCK_TRAINING.


## S7.43 — Transaction event identity audit
**Goal:** avoid treating same-player, different-event transaction reports as contradictions; audit editorial independence.
**Choice:** fail-closed offline event identity audit with SHA-256 lineage and zero automatic date/source verification.
**Inputs:** S7.42 review; S7.38 objects. **Outputs:** S7.43 report and review CSV.
**Limits:** no historical publication proof; no event dates assigned from tracker; no source independence established.
**Tests:** run `python -m pytest -q`; verify reports before committing.
**Decision:** RESEARCH_ONLY / BLOCK_TRAINING.

## S7.44 — Publication metadata provenance audit
- Goal: audit historical publication claims using saved official NBA HTML without network access.
- Approach: hash-check each captured article; inventory meta, JSON-LD and time-element dates; distinguish publication candidates, event dates, retrieval, and independently verified historical availability.
- Validation: targeted tests and full suite on local machine; no evidence promotion.
- Outputs: research/p0_s4/s7_44/results/ (untracked local evidence).
- Governance: RESEARCH_ONLY / BLOCK_TRAINING. No as-of historical proof.


## S7.45 — Publication date reconciliation

Goal: reconcile 38 S7.44 metadata records from nine SHA-verified NBA article objects and prioritize independent archive verification. Implemented offline grouping by article SHA, distinct publication/modification/creation/unattributed date categories, publication-field conflict detection, date-order anomaly flags, and per-article archive priority. Added 15 targeted tests. No external publication verification, event chronology, roster evidence or training promotion. Run `python -m pytest -q` and `python research/p0_s4/s7_45/run_s7_45.py` on the local evidence before recording observed results.


## S7.45 — Publication date reconciliation

Goal: reconcile 38 S7.44 metadata records from nine SHA-verified NBA article objects and prioritize independent archive verification. Implemented offline grouping by article SHA, distinct publication/modification/creation/unattributed date categories, publication-field conflict detection, date-order anomaly flags, and per-article archive priority. Added 15 targeted tests. No external publication verification, event chronology, roster evidence or training promotion. Run `python -m pytest -q` and `python research/p0_s4/s7_45/run_s7_45.py` on the local evidence before recording observed results.

...
...

## S7.46 — Historical archive discovery

Goal: query historical archive index for nine SHA-addressed NBA article URL candidates from S7.45. Added exact host/path URL checks, archive-index timestamp parsing, explicit network error categories, optional content-addressed archived HTML preservation, offline mode, and 15 targeted tests. Archive timestamps and saved replay content remain review-only, and no historical publication, transaction event, roster, or training evidence is promoted. Commands: `python -m pytest -q`, `python research/p0_s4/s7_46/run_s7_46.py`. Record observed results after local execution.

## S7.47 — Archived transaction claim review

Implemented offline archived-object SHA-256 verification, exact article URL cross-checks, localized direction candidate extraction and optional timezone-aware cutoff comparison. Added 15 targeted tests. No verified historical publication, transaction date, roster promotion or model training.

## S7.48 — Archived content recovery

Added offline extraction of archived HTML title, metadata, JSON-LD, headings and paragraphs with SHA-256 re-verification and URL-only separation. Added 15 targeted tests. Review-only transaction candidates; historical publication and event identity not verified. No training promotion.


## S7.49 — Archived transaction claim audit

Added offline SHA-256 re-verification, strict grammatical transaction direction candidates, transaction stage classification, replay/metadata provenance flags, and missing mapping diagnostics. No historical publication or event dates verified. RESEARCH_ONLY / BLOCK_TRAINING. Generated research results remain untracked.


## S7.50 — Full-article evidence and mapping audit
- Goal: eliminate S7.49's 450-character excerpt limitation and diagnose incomplete player/team mapping.
- Method: offline SHA-256 checks on S7.46 archived objects, full-length article/JSON-LD extraction, grammatical direction proposals, explicit mapping-gap status.
- Constraints: no invented Anthony Davis team mapping, no network, no historical publication or event-date promotion.
- Commands: `python -m pytest -q`; `python research/p0_s4/s7_50/run_s7_50.py`.
- Decision: RESEARCH_ONLY / BLOCK_TRAINING pending user-run results and independent validation.


## S7.51 — Evidence bottleneck decision gate
- Goal: quantify why S7.50 did not yield historically verified transactions; stop repeated archive extraction without a new testable hypothesis.
- Choice: offline read-only S7.50 CSV audit; distinct row/article/object counts and prioritized failure classifications.
- Files: `research/p0_s4/s7_51/run_s7_51.py`, README, tests, `docs/S7_51_EVIDENCE_BOTTLENECK_DECISION.md`.
- Run: `python -m pytest -q`; `python research/p0_s4/s7_51/run_s7_51.py`.
- Decision: `RESEARCH_ONLY / BLOCK_TRAINING`; pause repetitive archive extraction, pursue independent timestamped transaction/roster sources only if available; independently validated non-roster development can continue in parallel.
- Actual user-environment test counts and report results: pending execution.

## S8.0 — Modeling readiness inventory
- Goal: shift from repeated archive extraction to controlled audit of NBA minutes, player stats, baselines, validation, market, and roster components.
- Implementation: read-only artifact inventory, CSV/Parquet schema hints, explicit conservative status classifications, machine-readable reports, tests.
- Decision: `RESEARCH_ONLY / BLOCK_TRAINING`; S7.51 chronology blocked. No training authorization from this step.
- Results: populate after local execution; record pytest count, component statuses, and git commit.


## S8.1 — Game-log quality audit
Implemented a read-only offline audit for 2019-20, 2023-24, and 2025-26 player game-log snapshots. Checks identifiers, duplicate player-game keys, minutes, statistics, dates, schema consistency, file hashes, and incomplete scans. Outputs three review artifacts. Targeted tests included; full-suite results and actual dataset findings must be recorded after user execution. Decision: RESEARCH_ONLY / BLOCK_TRAINING. No historical roster/transaction promotion.


## S8.2 — Schema recognition repair and re-audit
- **Goal:** repair S8.1 false schema flags without altering source game logs.
- **Cause:** `event_date` absent from DATE_KEYS; TARGETS uppercase but snapshot columns lowercase.
- **Decision:** new offline runner in `research/p0_s8/s8_2/` rather than modifying past milestone.
- **Implementation:** case-insensitive target matching, date aliases, finite-number check, targeted regression tests, separate JSON/CSV outputs.
- **Verification:** run full pytest and S8.2 audit locally; inspect findings before further steps.
- **Governance:** RESEARCH_ONLY / BLOCK_TRAINING; historical roster/transaction evidence still blocked S7.51.

## S8.3 — Historical calendar exception audit

**Goal:** Diagnose 1,892 broad-window flags in 2019–20 without changing source data.

**Problem:** S8.2's generic July 1 upper bound marks pandemic-era August games as out of season.

**Options:** (A) discard flagged rows (unsafe); (B) extend window and auto-certify (unjustified); (C) classify game IDs/dates and require independent schedule corroboration (selected).

**Implementation:** `research/p0_s8/s8_3/run_s8_3.py`, targeted tests, per-game calendar review, per-season counts and SHA-256. No source changes, no network, no model training.

**Verification:** Run `python -m pytest -q` and S8.3 runner locally; attach generated reports for analysis. Do not claim full-suite success until user reports it.

**Unresolved:** Official game-ID/date independent validation; pre-tipoff as-of feature provenance; historical roster/transaction evidence (S7.51).

**Next:** S8.4 schedule cross-check, conditional on S8.3 findings.

## S8.4 — Official NBA schedule crosscheck

**Goal:** Verify S8.3 restart game IDs and dates against independently fetched NBA Stats team-game results.
**Design:** Read-only S8.3 review; fetch `leaguegamefinder` over NBA Stats HTTPS; hash raw response; reject missing, mismatched, and conflicting dates. Distinguish offline user-supplied JSON from independently retrieved data. No manual promotion or training.
**Validation:** Targeted unit tests and full suite should be run locally; inspect the JSON report before interpreting evidence.
**Outputs:** `research/p0_s8/s8_4/results/` (untracked).
**Remaining:** Official API may block retrieval; schedule match alone does not certify as-of feature history. `RESEARCH_ONLY / BLOCK_TRAINING`.

## S8.5 — Offline historical feature-lineage feasibility

**Goal:** Stop repeating a failed S8.4 official schedule request and audit strict prior-game feature construction on existing game logs.

**Problem:** S8.4 source timed out; no game was verified. Historical feature as-of eligibility remains unproven.

**Options:** (A) retry identical NBA Stats endpoint; low yield, no new evidence. (B) assume calendar verified; rejected as leakage risk. (C) preserve unresolved gate and audit offline strict prior-date feature feasibility; selected.

**Implementation:** Added read-only S8.5 runner, schema and chronology checks, targeted regression tests and documentation. No original datasets modified, no models trained. Run the full suite locally before committing; record actual counts and test results from your machine.

**Unresolved:** Official schedule verification, pre-tipoff publication, pregame player universe, injury/roster/market provenance, chronological OOS validation.

**Next:** Review S8.5 report and audit S5/S6 feature generation for leakage, especially postgame participation selection and pre-tipoff feature timestamp.


## S8.6 — Read-only feature code leakage triage

**Goal:** inspect the actual S5/S6 feature/evaluation code before any new model training.
**Decision:** conservative static source scan; source hashes and line-level review findings; no automatic leakage certification.
**Implementation:** `research/p0_s8/s8_6/run_s8_6.py`, targeted tests, report/findings/inventory outputs.
**Safety:** RESEARCH_ONLY / BLOCK_TRAINING. Prior S7.51 historical roster/injury gate and S8.4 88-game schedule gate unchanged.
**Next:** review generated findings with source context and establish fold-local, pregame-as-of lineage. Record user's test results and scan counts after run.


## S8.7 — Targeted source tracing
Goal: triage S8.6 medium findings against actual source, without editing production logic.
Decision: use local read-only AST/source excerpts and SHA-256 checks; dynamic mutation tests deferred until source interfaces are inspected.
Artifacts: `research/p0_s8/s8_7/`, `tests/test_s87_trace.py`, `docs/S8_7_TARGETED_SOURCE_TRACE.md`.
Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.

## S8.8 — Offline adversarial leakage testing (2026-10-09)

**Goal:** Move from S8.7 static trace to real behavioral tests of S4/S5 feature builders.
**Decision:** Synthetic mutation, same-day, player-isolation, row-order, cold-start, and target-output checks. No network, production mutation, or training.
**Artifacts:** `research/p0_s8/s8_8/run_s8_8.py`, `README.md`, `tests/test_s88_adversarial.py`, `docs/S8_8_ADVERSARIAL_LEAKAGE_TESTS.md`.
**Commands:** `python -m pytest -q tests/test_s88_adversarial.py`; `python research/p0_s8/s8_8/run_s8_8.py --project-root .`.
**Results:** Pending execution in user's actual checkout. Inspect `s8_8_report.json` and `s8_8_cases.csv`.
**Limitations:** Synthetic only; historical pregame player universe, as-of evidence, target downstream consumers, and fold-local calibration not certified. `RESEARCH_ONLY / BLOCK_TRAINING`.


## S8.9 — Downstream predictor leakage reconnaissance
- Goal: investigate whether realized box-score outcomes or targets can enter model inputs after S8.8 synthetic feature tests passed.
- Decision: read-only source discovery plus unit tests for a conservative predictor-list validation helper; no changes to production feature/model logic.
- Files: `research/p0_s8/s8_9/run_s8_9.py`, `research/p0_s8/s8_9/README.md`, `tests/test_s89_downstream.py`, `docs/S8_9_DOWNSTREAM_PREDICTOR_AUDIT.md`.
- Tests: run local pytest; attach report and findings before assessing real call sites.
- Limitations: no verified end-to-end training matrix, fold-local fit, pregame universe, source timestamps or 88 restart games.
- Status: `RESEARCH_ONLY / BLOCK_TRAINING`.


## S8.10 — Standalone fail-closed predictor contract (2026-10-09)

**Goal:** Establish executable safeguards before any future model-input integration, following S8.9's 45 source-review findings.

**Problem:** S8.9 did not certify a real downstream predictor matrix or chronological preprocessing.

**Options:** Another broad static scan (rejected: little incremental value); integrate directly into unknown training code (rejected: unsafe); standalone tested contract (selected).

**Implementation:** Added `research/p0_s8/s8_10/contract.py`, offline self-check runner, README, tests and research documentation. Explicit numeric predictor allowlist, target/outcome/ID exclusions, finite values, date-separated folds, and permanent BLOCK_TRAINING guard. No existing source modules changed.

**Tests/commands:** `python -m pytest -q tests/test_s810_contract.py`; `python research/p0_s8/s8_10/run_s8_10.py --project-root .`. Record actual local results before milestone closeout.

**Unresolved:** No live matrix inspection, no fold-local preprocessing/calibration verification, no independent pregame roster/DNP or historical as-of timestamps; 88 restart games unverified.

**Decision:** RESEARCH_ONLY / BLOCK_TRAINING. No model training, promotion, or bets.

## S8.11 — Contract integration feasibility

Goal: trace candidate training calls and exercise S8.10 predictor contract on synthetic outputs from actual feature builders.

Design: offline read-only AST inventory plus synthetic candidate matrix construction. Never fit models, enable training, or approve predictors. Tests: `python -m pytest -q tests/test_s811_integration_feasibility.py`. Runner: `python research/p0_s8/s8_11/run_s8_11.py --project-root .`. Record local results before closeout.

Decision: RESEARCH_ONLY / BLOCK_TRAINING. Pending: actual training entrypoint wiring, source timestamps, pregame eligibility, fold-local preprocessing and 88 restart games.

## S8.12 — Read-only pipeline boundary mapping

**Goal:** Map five S8.11 research feature-builder call sites and candidate downstream fitting boundaries without modifying project runtime or training.

**Decision:** AST call/assignment evidence, SHA-256 of priority sources, explicit limitations, offline tests. No automatic training enforcement or predictor certification.

**Files:** `research/p0_s8/s8_12/run_s8_12.py`, `README.md`, `tests/test_s812_pipeline_mapping.py`, `docs/S8_12_PIPELINE_BOUNDARY_MAPPING.md`.

**Commands:** `python -m pytest -q tests/test_s812_pipeline_mapping.py`; `python research/p0_s8/s8_12/run_s8_12.py --project-root .`.

**Governance:** `RESEARCH_ONLY / BLOCK_TRAINING`. Review generated CSVs before deciding integration. Independent as-of and pregame player eligibility remain blocked.


## S8.13 — Training boundary architecture

**Goal:** design a centralized fail-closed research-only boundary following S8.12 source mapping.

**Prior evidence:** S8.12 scanned 131 files and found no identified model-fit, chronological split, or contract call candidates. This is not proof of absence across the full repository or external jobs.

**Implementation:** added `research/p0_s8/s8_13/boundary.py` with ten evidence gates, unconditional training denial, and an optional S8.10 synthetic validation adapter; `run_s8_13.py` writes JSON/CSV reports; added targeted pytest tests and documentation. No existing source feature code or models modified.

**Verification:** run `python -m pytest -q tests/test_s813_boundary.py` and `python research/p0_s8/s8_13/run_s8_13.py --project-root .` in the target checkout. Record local results before marking complete.

**Unresolved:** historical as-of publication, pregame eligibility, DNPs, 88 restart games, independent gate proof, fold-local transformations, runtime training integration.

**Decision:** `RESEARCH_ONLY / BLOCK_TRAINING`.

## S8.14 — Historical Pregame Provenance and Eligibility Feasibility

**Goal:** Move from synthetic boundary tests to a small offline historical-source feasibility sample.

**Problem:** Historical player game logs show postgame participants and do not prove pre-tipoff eligibility, DNP status, or publication timing. Official calendar endpoint previously timed out.

**Options:** (1) bulk fetch history (high failure/ambiguity risk), (2) small offline sample plus evidence intake (chosen), (3) train anyway (rejected).

**Implementation:** Deterministic 3-game-per-season offline sampling, separate restart exclusion, candidate source registry, strict timezone/checksum evidence-intake checks, research-only reports and unit tests. No network calls or training.

**Tests:** `python -m pytest -q tests/test_s814_provenance.py`; `python research/p0_s8/s8_14/run_s8_14.py --project-root .`. Record local results after execution.

**Decision:** RESEARCH_ONLY / BLOCK_TRAINING. All candidate sources and evidence need independent verification. Next: review sample and obtain one source artifact with independently proven pre-tipoff publication.

## S8.15 — Official injury-report evidence pilot

- Objective: move from offline inventory to one genuine NBA-hosted historical source for `0022300061`.
- Identified NBA injury report dated 2023-10-24 5:30 PM ET, ahead of scheduled 7:30 PM ET tipoff. Historical public availability of this exact version remains **unverified**.
- Built offline intake with original-byte SHA-256 checks, timestamp validation and path containment. Tests must pass locally before commit.
- Limits: no independent archive capture, no complete pregame roster, no DNP reconciliation, no training. `RESEARCH_ONLY / BLOCK_TRAINING`.


## S8.16 — Historical artifact acquisition and timestamp audit

Goal: move from source inventory to actual artifact retrieval, while maintaining a fail-closed historical publication standard. Added opt-in official NBA PDF download, optional Wayback CDX query, immutable artifact paths, SHA-256 manifest, PDF metadata claim inspection, and conservative archive-index candidate classification. Local tests validate default offline behavior, candidate-only status, malformed input, unsafe hosts and overwrite protection. No source approved, no model training. Operator must record local command results and any network errors. Next: independent archive replay/capture review and separate pregame population/DNP evidence. Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.

## S8.17 — bounded archive response diagnostic (2026-10-09)

**Goal:** resolve whether the S8.16 three-byte CDX response was a valid empty result and probe limited alternative archive lookup methods. **Method:** preserve immutable response bytes and SHA-256, run four explicitly opted-in archive queries, record candidate-only classifications. **Limits:** no replay verification, independent publication proof, eligible roster or DNP evidence. **Status:** `RESEARCH_ONLY / BLOCK_TRAINING`; review generated local report before determining next action. **Tests:** `python -m pytest -q tests/test_s817_archive_diagnostics.py`. **Runner:** `python research/p0_s8/s8_17/run_s8_17.py --project-root . --query-archives`.

## S8.18 — Alternative historical evidence source investigation

Created bounded offline-first source inventory and optional HTTP artifact acquisition for six Lakers–Nuggets October 24, 2023 candidate sources. Publisher date labels and current downloads are not historical availability certification. S8.17 Wayback attempts produced no verified captures. No training permitted. See `docs/S8_18_ALTERNATIVE_HISTORICAL_SOURCES.md`. Run tests and inspect report locally before marking milestone complete.

## S8.19 — Offline publication evidence audit

Goal: verify S8.18 artifact integrity and extract publisher/file date claims without confusing those with independently established historical publication. Added `research/p0_s8/s8_19/run_s8_19.py`, intake template, seven tests and documentation. No network, model fitting, training authorization or historical source certification. Review generated report before drawing conclusions. Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.

## S8.20 — Historical data strategy redesign (2026-10-09)

**Goal:** Decide a scalable path after S8.19 confirmed source integrity but no independently verified historical publication captures.

**Alternatives:** historical reconstruction (large retrospective coverage but uncertain as-of), forward-only collection (strong prospective retrieval provenance but no immediate history), hybrid (strictly separate exploratory history from prospective evidence). **Decision:** hybrid, forward-evidence-first.

**Implementation:** Added offline read-only strategy runner, strategy comparison, source/checkpoint designs, prior-report integrity inventory, tests, and architecture documentation. **No network calls, captures, fitting, training or betting.** The runner may observe prior report claims but cannot promote them.

**Unresolved:** implement and test a small prospective capture proof of concept with authorized sources, verify independent pregame population/DNP process, fold-local validation and calibration, 88 restart games. Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.


## S8.21 — Offline forward evidence capture prototype

- **Goal:** Implement S8.20 forward evidence storage without implying historical certification.
- **Decision:** Standard-library SQLite append-only application API plus content-addressed raw bytes, SHA-256 integrity, duplicate and failure events, checkpoint health report.
- **Alternatives:** JSONL (simpler but weaker queries) and full production service (premature before adapters); SQLite chosen for simple local testing and audit queries.
- **Files:** `research/p0_s8/s8_21/run_s8_21.py`, README, `tests/test_s821_capture.py`, `docs/S8_21_FORWARD_CAPTURE_INFRASTRUCTURE.md`.
- **Validation:** Run `python -m pytest -q tests/test_s821_capture.py` then `python research/p0_s8/s8_21/run_s8_21.py --project-root . --demo`. Save actual local outcomes in the journal after execution.
- **Unresolved:** No trusted clock, immutable database controls, real acquisition, automatic schedule, source terms assessment, game eligibility or DNP reconciliation. `RESEARCH_ONLY / BLOCK_TRAINING`; 88 restart games remain blocked.


## S8.22 — Manual NBA schedule source adapter (2026-10-09)
- Goal: First bounded source adapter integrated with S8.21 append-only capture API.
- Choice: NBA CDN candidate with explicit --live opt-in; synthetic offline fixture as default testing route.
- Design: raw-first capture, per-event receipt, schema validation, normalized games CSV, failure logging.
- Test: 14/14 offline tests passed in patch build; local installation/live accessibility still to be confirmed.
- Limitations: CDN URL/schema not live-verified during packaging, no checkpoint-time enforcement, no player eligibility, no automatic scheduling, no training.
- Governance: RESEARCH_ONLY / BLOCK_TRAINING. 88 restart games separately blocked.
- Next: User validates fixture/tests, optionally authorizes one live request, uploads reports; then review actual schema and tipoff coverage before S8.23.


## S8.22.1 — HTTP diagnostics correction
- **Problem:** S8.22 live run returned `RETRIEVAL_FAILED_HTTPError` with null status; offline fixture succeeded.
- **Alternatives:** retry/bypass endpoint (rejected); replace source without review (rejected); preserve bounded status/headers/error fingerprint (selected).
- **Implementation:** updated S8.22 runner, allowlisted HTTP headers, bounded error-body SHA-256 diagnostic, regression tests for 403/404/429/500 and network errors.
- **Validation:** run local pytest; one explicit live request optional, no automated retries.
- **Unresolved:** actual live HTTP status and source accessibility; prospective eligibility and all training gates.
- **Governance:** `RESEARCH_ONLY / BLOCK_TRAINING`.


## S8.22.2 — Alternative schedule source evaluation
- Goal: replace the blocked NBA CDN candidate with a sustainable, authorized NBA schedule source.
- Trigger: S8.22.1 confirmed HTTP 403, zero live games.
- Options: undocumented ESPN site API; documented provider plans (balldontlie, API-Sports); licensed Sportradar; blocked NBA CDN.
- Decision: offline comparison only. ESPN's undocumented reachability is not permission; source approval remains pending.
- Implementation: source matrix, eight acceptance gates, read-only prior report inventory, ten regression tests.
- Results: no network calls, no live source approved, BLOCK_TRAINING.
- Next: provider terms, access, costs, coverage, game-ID mapping and UTC tipoff audit. Keep 88 restart games blocked.


## S8.22.3 — Provider selection and authorization review (2026-10-09)
Goal: select a documented NBA schedule candidate without bypassing HTTP 403 or asserting unauthorized live access. Compared official BALLDONTLIE and API-Sports documentation. Selected BALLDONTLIE for *manual terms/account review* based on documented free-tier NBA Games endpoint and date filters; API-Sports is fallback. Implemented offline CSV/JSON report and tests. No live request, account access, secrets, training, or certified game records. Pending: verify terms and user account entitlement, perform permitted manual live test, validate schema and ID crosswalk. Governance RESEARCH_ONLY/BLOCK_TRAINING.


## S8.22.4 — Controlled BALLDONTLIE NBA Games adapter (2026-10-09)

**Goal:** Move from provider documentation review to an explicitly authorized, single-request schedule adapter without weakening S8.21 evidence provenance.

**Context/problem:** NBA CDN returned HTTP 403. S8.22.3 shortlisted BALLDONTLIE, and user locally confirmed `.env` loads the API key and Git ignores `.env`. API authentication/entitlement is not yet proven.

**Options:** Continue blocked CDN (rejected); unofficial ESPN endpoint (permission unverified); documented key-authenticated BALLDONTLIE adapter (selected for controlled testing).

**Implementation:** `research/p0_s8/s8_22_4/run_s8_22_4.py` plus fixture, tests and docs. Explicit `.env` path avoids `python-dotenv` stdin stack issue. One date-scoped GET, no automatic retries, bounded body, SHA-256-backed S8.21 capture, strict schema/pagination/date checks, provider ID namespace, CSV and JSON report. No credential disclosure.

**Validation:** 15/15 offline tests passed, including integration with S8.21 ledger; live account response remains pending. Known risks: plan permissions, licensing, provider schema, time precision, ID mapping, coverage, missing eligible player population. No training.

**Next:** Review real response, resolve any schema mismatch, verify authorization/coverage and game ID crosswalk, then consider limited forward schedule collection. Status `RESEARCH_ONLY / BLOCK_TRAINING`; 88 restart games separately blocked.


## S8.22.5 — Independent schedule audit (2026-10-09)

**Goal:** Detect falsely reassuring empty schedules and compare provider game records to an independently acquired official reference without promoting uncertain IDs or tipoffs.

**Problem/evidence:** S8.22.4 returned HTTP 200, captured SHA256 evidence and parsed zero records for 2026-10-10. That does not establish no games are scheduled.

**Options:** Assume empty is valid (rejected); rely solely on BALLDONTLIE (rejected as circular); offline independent reference plus manually reviewed team crosswalk (selected).

**Implementation:** Added `research/p0_s8/s8_22_5/run_s8_22_5.py`, README, `tests/test_s8225_schedule_validation.py`, and audit design. Produces fail-closed report and candidate-only comparison CSV. No network access or API secrets. No automatic changes to S8.22.4.

**Tests:** 11 offline tests passed: empty, contradicted empty, candidate matchup, mismatched time, missing provenance, partial reference, schema, other date, bad date, duplicate crosswalk and naive timestamp. No live provider validation performed for this milestone.

**Risks:** Official reference and team-ID crosswalk not yet independently acquired; coverage, provider entitlement, prospective timestamps, as-of player eligibility unresolved.

**Next:** Run offline audit on 2026-10-10 CSV; manually collect a known populated date if authorized; acquire official independent schedule and reviewed team crosswalk; audit candidate matches. Remain `RESEARCH_ONLY / BLOCK_TRAINING`.


## S8.22.6 — Curated NBA official opening-night cross-validation
Goal: compare two BALLDONTLIE historical opening-night rows against independently published NBA game schedule and IDs. Issue: S8.22.5 had provider rows but no official reference or team crosswalk. Options: retry restricted NBA CDN (rejected), treat provider IDs as official (rejected), curated official NBA publication and game pages (chosen, with limitations). Implementation: offline deterministic comparator, strict crosswalk inputs, duplicate/date checks, tipoff UTC comparisons, provider SHA256, candidate-only outputs. Validation: dedicated synthetic tests; run locally and record result. Outstanding: fill provider-ID crosswalk from real historical CSV with evidence, inspect actual comparison, preserve official source bytes if possible, validate additional dates and independent historical as-of. No automated approval or training.

