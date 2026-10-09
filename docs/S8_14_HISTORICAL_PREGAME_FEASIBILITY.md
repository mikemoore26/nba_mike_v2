# S8.14 — Historical pregame evidence feasibility

## Research question
Can independently preserved, timestamped sources reconstruct the pre-tipoff player universe, injuries, lineup status, DNPs, and actual tipoff for a small historical game sample?

## Scope
Offline feasibility. Immutable existing game-log snapshots only; 3 sampled non-restart games per available season, deterministically chosen across time. **Sampling games from postgame logs does not establish pregame player eligibility.** The 88 flagged restart games are not resolved by excluding them from this sample.

## Evidence standard
1. Independent source identity, URL, artifact bytes, checksum, archived version.
2. Credible, independently verifiable publication timestamp strictly before actual tipoff; timezone explicit.
3. Game/team/player identity join validated, including ambiguous identities and late updates.
4. Pregame candidate player population reconstructed independently of box-score participation.
5. DNPs, scratches, injury uncertainty, inactive status and late changes reconciled.
6. Actual tipoff and calendar identity validated; restart 88 resolved or permanently excluded under explicit policy.
7. Audit lineage and reviewer signoff. Internal evidence intake checks **do not satisfy** these requirements.

## Candidate sources (not verified)
- NBA injury report archives: may expose pregame updates, but need actual version publication evidence.
- Official NBA schedules: game/tipoff verification candidate, not roster proof.
- NBA gamebooks: often postgame and cannot alone establish pregame eligibility.
- Team announcements and lineup archives: candidate if original timestamp/version preserved.
- Historical rosters/transactions: effective date is not proof of availability at tipoff.

## Next decision
Review `s8_14_report.json`, sample list, and registry. Obtain one authentic preserved artifact with independent timestamp evidence before expanding. If unavailable, record source failure and maintain BLOCK_TRAINING; do not retry previously timed-out endpoint automatically.
