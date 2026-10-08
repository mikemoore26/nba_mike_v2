# S7.1 — Official NBA injury report provenance (research only)

## External source investigation

The NBA maintains an official 2025-26 injury-report archive: https://official.nba.com/nba-injury-report-2025-26-season/. Example PDF versions have timestamp-bearing filenames under `ak-static.cms.nba.com/referee/injury/`. This is evidence that report versions exist, **not** that all historical revisions are complete or that a report's filename is independent proof of when it became accessible. Report formats can vary.

Candidate URLs included in `official_report_registry.csv` are **not downloaded or independently verified** by the patch. The local registry stores source URLs, claimed publication times, independently established availability times, and PDF byte hashes. Empty fields stay unverified. The pipeline fails closed on unverified provenance.

## Cutoff design

Proposed primary research cutoff: 60 minutes before scheduled tipoff (not finalized). Store actual tipoff and scheduled tipoff separately; use a timestamped schedule snapshot known before the cutoff. A report version can be used only if publication and evidenced availability are both <= cutoff. Timezone-aware ET is converted to UTC with DST handling. Do not confuse game date with report date. Do not use future versions, game outcomes, final starters or retrospective DNP labels as pregame inputs.

## Remaining gates

1. Confirm terms, reproducibility, archive completeness and stable retrieval of PDF bytes.
2. Independently evidence availability/revision times, not just PDF title time.
3. Parse PDFs with page provenance and explicit NOT YET SUBMITTED / blank / unknown statuses.
4. Join teams, player IDs and game IDs with a documented mapping and ambiguity quarantine.
5. Define full active-roster player-game universe, including DNP and inactive players, without outcome leakage.
6. Run historical as-of checks and audit coverage across seasons; compare to S6.3 high-risk groups.

No model training, deployment, or betting promotion authorized.
