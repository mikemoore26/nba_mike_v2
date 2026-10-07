# NBA_MIKE v2 — Leakage & Invariant Standard

## Purpose
P0-S3 S7 converts the data-governance rules into executable, fail-closed checks. A high backtest score is not evidence if future information, outcomes, broken identities, or invalid provenance can enter predictive inputs.

## Governed invariants
1. **D-1 statistical boundary.** For target game date D, pregame statistical inputs may contain events only through D-1. Same-day earlier games are intentionally excluded under the current conservative contract.
2. **Canonical key uniqueness.** Player-game rows must have non-empty `(game_id, player_id)` keys and those keys must be unique.
3. **Feature/target separation.** Fields explicitly contracted as targets/outcomes are forbidden from feature rows. This is a structural guard; future feature builders must declare their forbidden target field set.
4. **Team/opponent consistency.** Team and opponent IDs must be present and cannot be equal.
5. **Snapshot metadata integrity.** D-1 contract, target date, cutoff date, `as_of_time`, parent artifact identity/hash, logical hash, and snapshot ID must agree with the requested target date.
6. **Zero-history honesty.** An entity with zero eligible prior games must remain `ZERO_HISTORY`; missing history is never silently converted to observed zero performance.
7. **Provenance fail-closed behavior.** Existing S4/S6 controls remain authoritative: non-PASS parents and hash-tampered parents cannot flow downstream.
8. **Determinism and identity controls remain regression gates.** Existing S2-S6 tests stay in the full suite; S7 does not replace them.

## Scope boundary
S7 does not claim that historical intraday injuries, confirmed lineups, news, or sportsbook prices are solved. It does not train predictive models. It does not define final production feature sets. Its job is to make known invalid states fail loudly before S8 historical reconstruction.

## Acceptance
S7 passes only when deliberate leakage/invariant violations are rejected, a governed D-1 snapshot passes the new checks, non-PASS parent evidence remains blocked, and the entire repository regression suite passes.
