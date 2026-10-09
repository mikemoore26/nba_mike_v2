# S8.22.2 — Alternative schedule source governance

## Trigger
S8.22.1 live NBA CDN schedule attempt returned HTTP 403. Do not retry that restricted endpoint or evade its controls.

## Research candidates
- NBA CDN: failed with 403; no more attempts.
- ESPN site scoreboard: documented by third parties, **unofficial and undocumented**. Public reachability does not imply permission to automate collection; do not activate a collector until terms/permission are established.
- balldontlie / API-Sports: investigate documented plan terms, NBA schedule coverage, date ranges, price and request limits before implementing.
- Sportradar: investigate licensed product scope and cost if affordable.

## Evidence hierarchy
1. Provider's own current written documentation, terms and licensing agreement.
2. Explicit authorization or account entitlement.
3. One permitted, bounded manual retrieval and preserved S8.21 receipt.
4. Real schema, complete game/date coverage, source ID crosswalk and UTC tipoff verification.
5. Separate game-specific pregame eligibility evidence.

## Decision
HYBRID_FORWARD_EVIDENCE_FIRST. No source approved for live ingestion; no training. The preferred next action is a documented provider terms-and-coverage review, not automated endpoint probing. Historical logs remain exploratory; 88 restart games blocked.

## Background references (not proof of license)
- https://github.com/pseudo-r/Public-ESPN-API (third-party, unofficial ESPN endpoints)
- https://publicapis.io/espn-sports-api (third-party description of scoreboard)
