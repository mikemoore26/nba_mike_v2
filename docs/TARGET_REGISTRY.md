# NBA_MIKE v2 — P0-S2 Target Registry

**Status:** FEASIBILITY DECISIONS — NOT PRODUCTION APPROVAL  
**Date:** 2026-10-03

## Decision vocabulary
- GO_RESEARCH — enough evidence exists to justify research.
- GO_WITH_LIMITATIONS — research is justified but important data/time limitations exist.
- SUPPORTING_TARGET — useful intermediate variable rather than primary betting target.
- RESEARCH_ONLY — interesting, but not part of the initial core.
- INVESTIGATE — feasibility remains unresolved.
- BLOCKED — do not build until a named dependency is solved.
- REJECTED — current evidence does not justify development.

| Layer | Target | Decision | Initial role | Main reason |
|---|---|---|---|---|
| Availability | P(player active/plays) | GO_RESEARCH | Foundation | Needed before minutes/stat reasoning |
| Minutes | Minutes distribution | GO_RESEARCH | Highest-priority foundation | Opportunity strongly depends on playing time |
| Opportunity | Usage | SUPPORTING_TARGET | Role | Helps explain possession share |
| Opportunity | FGA | SUPPORTING_TARGET | Scoring opportunity | More interpretable than points alone |
| Opportunity | 3PA | SUPPORTING_TARGET | 3PM opportunity | Separates attempts from conversion |
| Opportunity | FTA | SUPPORTING_TARGET | Scoring opportunity | Captures free-throw volume |
| Opportunity | Potential assists | GO_WITH_LIMITATIONS | Creation opportunity | Valuable but tracking-history/access must be audited |
| Opportunity | Rebound chances | GO_WITH_LIMITATIONS | Rebounding opportunity | Valuable but tracking-history/access must be audited |
| Player stat | Points | GO_RESEARCH | Core | Major market; strong box-score history |
| Player stat | Rebounds | GO_RESEARCH | Core | Major market; strong history |
| Player stat | Assists | GO_RESEARCH | Core | Major market; strong history |
| Player stat | 3PM | GO_RESEARCH | Core | Major market; attempt/conversion decomposition possible |
| Combination | PRA | GO_RESEARCH | Derived/direct experiment | Compare direct model with joint component derivation |
| Combination | PR | GO_RESEARCH | Derived/direct experiment | Same |
| Combination | PA | GO_RESEARCH | Derived/direct experiment | Same |
| Combination | RA | GO_RESEARCH | Derived/direct experiment | Same |
| Player stat | Steals | RESEARCH_ONLY | Later | Higher event variance |
| Player stat | Blocks | RESEARCH_ONLY | Later | Higher event variance |
| Player stat | Turnovers | RESEARCH_ONLY | Later | Not initial core |
| Milestone | Double-double | RESEARCH_ONLY | Derived probability | Prefer joint distribution research first |
| Milestone | Triple-double | RESEARCH_ONLY | Rare event | Requires reliable joint tails |
| Team/game | Moneyline | GO_WITH_LIMITATIONS | Later model family | Historical odds feasible but separate from props |
| Team/game | Spread | GO_WITH_LIMITATIONS | Later model family | Same |
| Team/game | Game total | GO_WITH_LIMITATIONS | Later model family | Same |
| Team/game | Team total | INVESTIGATE | Later | Market/data coverage needs confirmation |
| Parlay | Joint outcome probability | BLOCKED | Late-stage | Requires validated marginals and dependence |
| Parlay | Ticket construction | BLOCKED | Final output | Cannot precede probability/market/correlation validation |

## Initial development priority
1. Availability feasibility.
2. Minutes.
3. Points / rebounds / assists / 3PM.
4. Supporting opportunity variables.
5. Joint component distributions and combination props.
6. Market layer.
7. Correlation and parlay research only after individual probabilities are validated.

## Important
GO_RESEARCH does not mean the target is predictable or profitable. It only means the target has earned a research experiment.
