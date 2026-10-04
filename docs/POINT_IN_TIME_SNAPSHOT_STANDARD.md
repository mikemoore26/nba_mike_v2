# NBA_MIKE v2 — Point-in-Time Snapshot Standard

## Purpose
P0-S3 S6 converts canonical historical rows into deterministic, leakage-resistant D-1 statistical snapshots for a target game date D.

## Statistical cutoff
For the initial historical reconstruction contract, a snapshot for game date D may use statistical events only through D-1.
Rows with event_date >= D are forbidden from the statistical snapshot.

This rule is deliberately conservative. It excludes same-day earlier-game information and does not claim intraday truth.

## Required snapshot metadata
Every snapshot records:
- snapshot_id
- target_game_date
- cutoff_date
- as_of_time
- parent artifact id
- parent SHA-256
- code Git commit when supplied
- row count
- logical SHA-256

`as_of_time` is explicit and must not be earlier than the end of the D-1 statistical cutoff.

## Provenance and trust
A snapshot may be built only from a PASS parent whose bytes match the recorded SHA-256.
Tampered or non-PASS parents fail closed.

## Determinism
Equivalent canonical inputs, cutoff, and snapshot scope must produce the same logical snapshot hash. Runtime metadata such as creation time is not part of the logical hash.

## Identity and duplicates
Canonical player/team/game identifiers are preserved. Duplicate canonical player-game rows are rejected.

## Empty history
A player with no eligible history before D remains a valid zero-history case. S6 does not invent prior statistics. Downstream feature logic must explicitly handle such players.

## Scope boundary
S6 governs statistical history only. Injury reports, confirmed lineups, news, sportsbook markets, and other intraday information are not made safe by this D-1 rule. They require independent timestamp-safe evidence before use.

## Acceptance rule
S6 passes only if tests demonstrate D-1 exclusion, same-day/future blocking, provenance verification, tamper rejection, non-PASS parent blocking, duplicate rejection, deterministic rebuild behavior, explicit as-of metadata, and zero-history handling.

Predictive model training remains closed after S6.
