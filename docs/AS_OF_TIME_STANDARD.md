# NBA_MIKE v2 — AS_OF_TIME & Historical Reconstruction Standard

## Principle
A historical prediction is valid only if every input could have been known at that prediction's `AS_OF_TIME`.

## Required time concepts
Where applicable, preserve:
- `event_time` — when the basketball/news/market event occurred
- `published_time` — when a source made it available
- `ingested_time` — when NBA_MIKE captured it
- `as_of_time` — cutoff for a prediction
- `effective_time` — when a roster/status/line becomes applicable

## Snapshot rule
Mutable pregame information must not be overwritten as if the latest value always existed.

Examples:
- injury status
- expected starter
- confirmed starter
- sportsbook line
- sportsbook price
- player prop availability

Store snapshots/events so later research can reconstruct the state at a chosen time.

## Historical reconstruction test
Before a mutable data family becomes a production feature:
1. select historical games;
2. choose realistic pregame AS_OF_TIME checkpoints;
3. reconstruct only information available by each checkpoint;
4. compare with the final postgame record;
5. verify no later update leaked backward.

## Feature eligibility
- SAFE: availability time is known and precedes AS_OF_TIME.
- CONDITIONAL: usable only for eras/sources where timing is known.
- HIGH_RISK: timing is ambiguous.
- PROHIBITED: relies on future/postgame information.

## Important examples
A final starting lineup cannot automatically be used in a morning historical prediction.
A closing line cannot be used as an input to a model supposedly making a noon prediction.
A player's final game minutes cannot be used to construct a pregame expected-minutes feature.
A corrected injury status published after the prediction cannot be backfilled into the historical feature row.

## Prospective advantage
Once NBA_MIKE begins operating, it should build its own immutable timestamped snapshot history. This becomes the highest-confidence source for future forward validation.
