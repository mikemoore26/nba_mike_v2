# NBA_MIKE v2 — Research Governance

## 1. Purpose
These rules prevent NBA_MIKE v2 from confusing model complexity, backtest performance, or short-term betting results with genuine predictive evidence.

## 2. Evidence lifecycle
Every important idea follows:

`QUESTION -> HYPOTHESIS -> SUCCESS CRITERION -> DATA CHECK -> ANALYSIS -> CHRONOLOGICAL VALIDATION -> OUT-OF-SAMPLE CONFIRMATION -> DECISION`

Allowed research statuses:
- DISCOVERED
- PROMISING
- FAILED
- UNSTABLE
- CONFIRMED_OOS
- PRODUCTION_CANDIDATE

Negative results must be recorded.

## 3. Model lifecycle
Models use:
- RESEARCH
- PAPER
- CANDIDATE
- TRUSTED

Promotion requires predefined evidence. A winning streak is not sufficient.

## 4. Baseline rule
Every target must have meaningful simple baselines before advanced models compete. Complexity must demonstrate out-of-sample benefit.

## 5. Time and leakage rule
Historical predictions must be evaluated using only information that would have been available at the prediction `AS_OF_TIME`.

Where relevant, data should distinguish:
- event time
- publication/availability time
- ingestion time
- prediction AS_OF_TIME

Features that cannot be reconstructed safely may be prohibited from historical validation.

## 6. Holdout rule
Exploration, validation, calibration, test, and final lockbox roles must be kept conceptually separate. Repeated inspection of a final holdout is prohibited because it turns the holdout into development data.

## 7. Performance vs market
Player-performance models answer what is likely to happen.
Market/decision logic answers whether an offered line and price justify action.
An OVER prediction alone is not a betting recommendation.

## 8. Uncertainty
Do not collapse all uncertainty into one vague confidence score. Preserve at least:
- model/statistical uncertainty
- information/data quality
- role/minutes uncertainty where relevant
- market attractiveness

## 9. Prediction tracking
When production/paper prediction begins, track all evaluated predictions, including PASS/WATCH outcomes, with enough version and timestamp information to reproduce the decision.

## 10. Ticket and parlay governance
Tickets are downstream outputs of validated models.
Do not force selections.
Do not assume correlated legs are independent.
Parlay/joint-probability logic requires separate validation before promotion.

## 11. Production blocking
Critical failures in required data, schemas, leakage checks, model validity, or stale inputs must prevent questionable recommendations from being silently produced.

## 12. Documentation
Engineering decisions go in `DEVELOPMENT_JOURNAL.md`.
Scientific experiments go in `DISCOVERY_JOURNAL.md`.
Current continuation state goes in `NEXT_AGENT_HANDOFF.md`.

## 13. Git
Stable milestones require:
1. `git status`
2. milestone checks/tests
3. documentation update
4. `git add`
5. focused `git commit`
6. final `git status`

## 14. Change control
These governance rules can be changed, but a material change must document:
- why the old rule was insufficient
- the proposed replacement
- risks introduced
- evidence/reasoning supporting the change
