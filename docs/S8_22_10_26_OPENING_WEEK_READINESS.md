# S8.22.10.26 — Opening-week readiness

## Scope
Read-only audit of code and documentation to identify candidate implementation paths for current-season data, identity, injuries, minutes, stat models, chronological validation, odds, ticket building and tracking. Does not claim live functionality or historical certification.

## Decision
`RESEARCH_ONLY / BLOCK_TRAINING`. Real-money ticket recommendation approval is `DENIED` until each operational gate has evidence. Paper-ticket workflow may be implemented separately but must not imply betting approval.

## Next acceptance gates
1. Current-season schedule, player, roster, injury and lineup feeds: valid provenance and availability timestamps.
2. Minutes/usage/stat models: versioned artifacts, leakage tests, strict chronological out-of-sample evaluation and calibration.
3. Market odds: timestamped lines, side/price normalization, vig treatment, missing-data handling.
4. Ticket builder: valid probability and EV calculation, correlation controls, no forced bets, stake policy.
5. Forward paper ledger: immutable prediction time, later grading, comparison with market, performance review.

## Limitations
Static string matching produces false positives and misses dynamically named modules. A candidate file is only a lead for inspection. Do not infer model readiness from file counts.
