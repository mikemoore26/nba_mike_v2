# NBA_MIKE v2 — P0-S2 Research Pass Findings

## Decision
P0-S2 establishes that the project can proceed with a conservative, leakage-aware historical NBA data foundation. It does **not** authorize model training yet.

## Evidence established
- POC-01: core historical team/player data and identity access passed across 2019-20, 2023-24, and 2025-26.
- POC-02: play-by-play access passed, including substitutions and scoring fields. PBP access alone does not prove lineup reconstruction.
- POC-04: naive rotation reconstruction failed strict truth testing. Failure was driven by starter/period-start inference, so this method is not approved as authoritative.
- POC-05: official game starters were available; constraint-based period-start inference was sometimes unique and sometimes ambiguous. Ambiguous solutions must not be guessed.
- POC-06: GameRotation feasibility was inconclusive because all tested requests timed out. It is not approved as a production dependency.
- POC-07: base, advanced, and selected tracking season-level data were accessible across all three test seasons.
- POC-08: historical DateTo cutoffs behaved as historical season-to-date snapshots across all three eras. This supports day-level leakage-safe research, but not intraday timestamp truth.
- POC-09: the D-1 feature boundary passed across all three test seasons. Every player who played on target date D gained exactly one GP between D-1 and D, with zero wrong target-player deltas and zero non-target-player changes.

## Approved conservative historical rule
For a game on date D:
1. statistical feature snapshots use data through D-1;
2. game-D player logs are outcomes/labels only;
3. game-D results may never enter pregame statistical features;
4. same-day earlier-game information is excluded at this stage;
5. injuries, confirmed lineups, news, and sportsbook markets require separate timestamp-aware research before historical use.

## Data tier decision
CORE RESEARCH CANDIDATES:
- historical player/team box-score data;
- D-1 season-to-date base aggregates;
- game-level player logs as labels/outcomes.

SUPPORTING RESEARCH CANDIDATES:
- D-1 advanced aggregates.

OPTIONAL / ADVANCED RESEARCH CANDIDATES:
- D-1 tracking aggregates, pending stability, historical-depth, missingness, and predictive-value testing.

BLOCKED / NOT AUTHORITATIVE:
- naive PBP-only lineup/rotation reconstruction;
- ambiguous constraint-derived lineups;
- GameRotation as a required dependency until reliability is proven;
- intraday injuries/lineups/news/odds without timestamp evidence.

## Remaining Step-0 questions
Before model training:
- define the canonical raw/intermediate/feature dataset contracts;
- establish acquisition, caching, retries, validation, and provenance;
- validate player/team/game identifiers at scale;
- define chronological splits, walk-forward protocol, baselines, and metrics;
- define target construction for minutes, points, rebounds, assists, 3PM, and combinations;
- research intraday availability/injury/lineup/market data separately;
- define missing-data and role-change policy.

## Status
P0-S2 RESEARCH PASS: PASS WITH EXPLICIT LIMITATIONS.

Next recommended milestone: P0-S3 — Canonical Data Architecture & Dataset Contract.

Do not train predictive models yet.
