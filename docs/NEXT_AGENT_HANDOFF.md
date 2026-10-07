# NBA_MIKE v2 — NEXT AGENT HANDOFF

## Current checkpoint
P0-S3 S1-S6 are complete. INFRA-01 packaging/execution is complete at commit `27ceaf9`. P0-S3 S7 — Leakage & Invariant Test Suite has been prepared and must pass targeted tests, full regression, acceptance, and Git review before being called complete.

## S7 package intent
S7 adds fail-closed executable invariants for the conservative D-1 statistical boundary, player-game key uniqueness, feature/target separation, team/opponent consistency, snapshot metadata/provenance integrity, and explicit zero-history semantics. It deliberately injects invalid states and requires rejection.

## Required S7 verification
1. `python -m pytest .\tests\test_leakage_invariants.py -q`
2. `python -m pytest -q`
3. `python .\research\p0_s3\s7\run_s7_acceptance.py`
4. Inspect `git status`; commit only after all checks pass.

## Hard constraints
- No predictive model training yet.
- Statistical pregame boundary remains D-1; same-day earlier-game stats remain excluded.
- Do not claim exact historical intraday injuries, confirmed lineups, news, or sportsbook prices are solved.
- No hidden source fallback, raw mutation, name-based primary identity, target leakage, or missing-as-zero behavior without a field contract.
- Automatic progress-email delivery is still a requirement but is not implemented in this repository; do not claim emails were sent.

## After S7
Proceed to P0-S3 S8 — Historical Reconstruction Sample. Run across multiple seasons/dates/games and compare repeated builds for reproducibility. Then S9 closes P0-S3. Modeling remains locked until closeout explicitly opens the gate.
