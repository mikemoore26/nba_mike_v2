# NBA_MIKE v2 — P0-S4 Feature & Target Research Plan

## Objective
Convert the governed P0-S3 historical statistical foundation into a formally defined feature/target research layer before predictive model selection.

P0-S4 asks:
1. What exactly should each model predict?
2. Which inputs are historically available before game date D?
3. Which feature families are stable enough to test?
4. How should minutes, role, usage, and opportunity be represented?
5. Which simple baselines must later models beat?
6. What evidence is required before model training is authorized?

## Governing architecture
availability -> minutes -> role/usage/opportunity -> stat distribution -> market -> decision

The statistical historical boundary remains D-1 unless stronger timestamp-safe evidence is separately proven.

## Initial target hierarchy
### Upstream targets
- played / did not play, only where historically defensible
- minutes played

### Core player-stat targets
- points
- rebounds
- assists
- made three-pointers
- combinations derived only after component targets are governed

### Later targets
- steals
- blocks
- turnovers
- double-double/triple-double style events
- market-specific threshold probabilities

Targets are outcomes. They must never enter feature rows for the same game.

## Candidate feature families
1. Player historical production
   - season-to-date aggregates
   - rolling game windows
   - per-minute production
   - variance and distribution descriptors
2. Minutes and role
   - prior minutes
   - rolling minutes
   - starts when historically safe
   - role stability/change indicators
3. Usage/opportunity
   - shot/attempt opportunity
   - rebounding opportunity proxies
   - assist/playmaking opportunity proxies
   - D-1 advanced aggregates where coverage passes
4. Team context
   - pace and team statistical context from eligible history
   - teammate/role context only when historically reconstructible
5. Opponent context
   - D-1 opponent/team defensive context
6. Schedule/environment
   - home/away
   - rest days/back-to-back from schedule history
7. Advanced/tracking
   - research-only until historical depth, missingness, stability, and incremental OOS value pass.

## Feature safety contract
Every candidate must be evaluated for:
- pregame availability;
- historical coverage;
- today-row parity;
- missingness;
- duplicate/join risk;
- leakage;
- deterministic reconstruction;
- stability over time;
- incremental out-of-sample value.

## Baseline philosophy
Complex models are not the starting line. Each target must first receive transparent baselines such as:
- season-to-date mean;
- recent rolling mean;
- recent median;
- per-minute rate combined with a simple minutes estimate;
- simple weighted recent/season blend.

## Research rules
- No random split as primary validation.
- No target-day statistical features.
- No full-season aggregates for earlier historical rows.
- No unproven historical injury/lineup/news/market features.
- No feature is retained merely because it is available.
- No advanced model wins unless it beats meaningful simple baselines out of sample.
- Feature experiments must record hypothesis, coverage, missingness, chronology, result, and keep/reject decision.

## P0-S4 milestone sequence
S1 — Feature & Target Research Plan
S2 — Target Contract & Outcome Builder
S3 — Baseline Feature Registry
S4 — Minutes / Role / Opportunity Research
S5 — Recent-Form Window Research
S6 — Team / Opponent / Schedule Context
S7 — Advanced & Tracking Feature Audit
S8 — Feature Dataset Builder & Leakage Acceptance
S9 — Baseline Prediction Benchmarks
S10 — P0-S4 Closeout / Model-Training Gate

## Model-training gate
Serious candidate-model training is not authorized merely because P0-S3 passed. P0-S4 must establish valid targets, feature provenance, training/prediction parity, chronological feature construction, baseline benchmarks, and an accepted modeling dataset.

S9 may use simple benchmark estimators solely to establish baseline difficulty and evaluation plumbing. Candidate model-family competition belongs after the P0-S4 closeout gate.

## Fail conditions
P0-S4 cannot PASS if:
- a target is ambiguous or incorrectly aligned;
- target-day/postgame information leaks into features;
- a feature cannot be reproduced for historical rows;
- train/today feature semantics differ silently;
- identity or join behavior can duplicate player-game rows;
- unresolved intraday information is represented as known;
- feature selection is based only on in-sample fit;
- advanced features are accepted without coverage/stability evidence.
