# NBA_MIKE v2 — Baseline Feature Registry Standard

## Purpose
A feature must earn its way into modeling. Availability alone is not evidence of usefulness.

## Registry statuses
- `APPROVED_BASELINE`: safe enough to enter the governed baseline feature-building stage.
- `RESEARCH_ONLY`: plausible candidate requiring additional coverage/stability/value evidence.
- `BLOCKED`: cannot currently be represented with trustworthy historical pregame semantics.
- `REJECTED`: evaluated and intentionally excluded.

`APPROVED_BASELINE` does not mean a feature is predictive. It means the feature is sufficiently governed to test.

## Required metadata
Every candidate records name, group, description, source domain, pregame availability, historical availability, today availability, missing-value policy, leakage-check status, coverage status, research status, version, and notes.

## Approval requirements
An approved baseline must:
1. be pregame available;
2. be historically reconstructible;
3. have a today-row equivalent;
4. pass leakage review;
5. have PASS coverage status.

## D-1 boundary
Statistical aggregates for target date D use eligible history through D-1.

## Initial baseline families
The registry seeds conservative player-history, recent-form, home/away, and rest candidates.

The last-five-game entries are approved as safe *candidate inputs*, not as proven optimal windows. S5 must compare windows rather than assuming five games is best.

## Research-only features
Advanced usage and tracking data remain research-only where coverage/stability/incremental value still require evidence.

## Blocked domains
Historical injury status, confirmed lineups, and sportsbook prop lines remain blocked until timestamp-safe historical reconstruction is proven.

## Training/prediction parity
A feature cannot be approved for the baseline if historical training rows and live/today rows silently mean different things.

## Feature selection rule
Later predictive value must be measured chronologically and out of sample. In-sample correlation or intuitive basketball logic is not sufficient.
