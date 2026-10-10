# NBA_MIKE v2 — Next agent handoff

Current phase: P0-S4 S4.1 research hardening; S3 committed at e427c76. S4 original unit and historical research passed (81 tests), but S4 remains uncommitted pending S4.1 validation.

S4.1 replaces opportunity feature builder and research runner. D-1 calendar-date boundary is enforced; duplicate player-dates share historical features. Research outputs are segmented by role change, prior-history depth, and realized minutes (retrospective only). Historical NBA injury/lineup/market evidence remains blocked.

Run S4.1 acceptance, real-data runner, full regression; review JSON and CSV. Commit only after outputs pass and interpretation is documented. Next phase S5 adaptive recent-form windows, not model training.

## S4.1 Research Conclusions — 2026-10-07

- Last-five minutes average led the tested simple baselines in 2019-20, 2023-24, and 2025-26.
- Stable-role last-five MAE: 4.822, 4.908, 4.854.
- Role-change last-five MAE: 5.674, 5.641, 5.721.
- Last-five outperformed last-three in both role groups.
- Role-change flags indicate greater historical prediction uncertainty.
- These are descriptive findings only, not validated betting edges.
- S5 will investigate adaptive windows and chronological robustness.

## Current milestone: P0-S4 S5
S4/S4.1 baseline was last-five minutes MAE ~5; role-change subgroup has higher error. S5 patch adds `features/adaptive_form.py`, tests, research runner and standard. S5 is RESEARCH_ONLY and uncommitted until local tests and historical results reviewed. Next: inspect candidate scores and prequential last-five vs adaptive MAE, plus role subgroup and selected counts. Preserve no-leakage rules and closed model-training gate.


## S5.1 pending validation
Install research/p0_s4/s5_1, docs/S5_1_ROBUSTNESS_STANDARD.md, tests/test_s5_1_robustness.py. Run acceptance, runner, full pytest; inspect report and manifest. EWM-5 was selected after earlier inspection of 2025-26, so the 2025-26 split is a retrospective chronological check, not a truly untouched holdout. S5 remains RESEARCH_ONLY. No commit until review.

## S6 handoff (pending execution)
New `src/nba_mike/features/minutes_uncertainty.py`, S6 runner and tests.
Run acceptance, offline snapshot-backed research and full regression. Review
coverage and width; do not promote predictive intervals without additional validation.


## S6 Research Conclusions — 2026-10-07

- Full regression: 100 tests passed.
- Overall 90% interval coverage: 88.9%-89.3%.
- Stable-role coverage: 89.8%-90.2%.
- Role-change coverage: 84.4%-85.3%.
- Mean interval width: approximately 19.7 minutes.
- Role-change undercoverage is consistent across three seasons.
- Pooled calibration is insufficient for reliable subgroup coverage.
- S6 remains RESEARCH_ONLY; no betting promotion.
- Next: S6.1 role-aware uncertainty calibration.

## S6.1 handoff — pending local evaluation
New `src/nba_mike/features/role_aware_uncertainty.py`, `tests/test_role_aware_uncertainty.py`, `research/p0_s4/s6_1/` runner, and `docs/S6_1_ROLE_AWARE_UNCERTAINTY.md`. Requires S6 prediction CSVs. Compare matched-role coverage and interval width, verify 105 total tests if prior 100 pass, then decide on research-only checkpoint. Do not claim production or betting readiness.


## S6.1 Research Conclusions — 2026-10-07

- Full regression: 105 tests passed.
- Role-specific calibration improved role-change coverage toward 90%.
- Shrinkage achieved near-target coverage with slightly narrower intervals.
- Role-specific calibration increased interval width for changing-role players.
- Methods compared on the same S6.1 evaluation rows.
- S6.1 remains RESEARCH_ONLY.
- Next: S6.2 conditional uncertainty and chronological validation.

## S6.2 pending evaluation
New `conditional_uncertainty.py`, S6.2 runner, tests and documentation. Run acceptance, offline report and full suite. Review common-sample coverage/width for role/history/volatility and existing S6.1 baselines. Preserve RESEARCH_ONLY until independent chronological validation.


## S6.2 Research Conclusions — 2026-10-07

- Acceptance passed.
- Full regression: 110 tests passed.
- Conditional uncertainty evaluated on common S6.1 player-games.
- History and volatility improve risk differentiation.
- Role-change coverage does not consistently improve over role-specific calibration.
- 2025-26 volatility-aware coverage: 89.14%; mean width: 19.64 minutes.
- Role-specific baseline coverage: 89.54%; mean width: 20.15 minutes.
- Retain role-specific as reference baseline.
- S6.2 remains RESEARCH_ONLY.
- Next: S6.3 error attribution and calibration stability.
## S6.3 handoff
- Module: `src/nba_mike/evaluation/s6_3_diagnostics.py`.
- Runner: `research/p0_s4/s6_3/run_s6_3.py` (offline S6.2 outputs).
- Acceptance: `research/p0_s4/s6_3/run_s6_3_acceptance.py`.
- Report: `research/p0_s4/s6_3/results/s6_3_report.json`.
- No production promotion. Await report, regression tests, Git review and commit.


## S7.0 handoff (pending local execution)
- Prior: S6.3 retrospective error attribution, role-specific minutes uncertainty baseline; no production promotion.
- Current: offline S7.0 provenance validator and local research inventory; `research/p0_s4/s7_0/results/s7_0_feasibility_report.json` after runner.
- No historical injury/lineup source verified; no network data acquisition; no betting models authorized.
- Next: source-backed timestamped sample, define prediction cutoff and DNP player-game universe, then S7.1 leakage-safe join POC.


## S7.1 handoff (pending execution)
New `src/nba_mike/data/injury_asof.py`; registry in `research/p0_s4/s7_1/official_report_registry.csv`; audit runner outputs `research/p0_s4/s7_1/results/s7_1_report.json`. Official PDF links are candidate references only. No PDF bytes, independent availability proof, historical coverage, or training permission. Do not assume filename timestamp proves availability. Next: obtain and audit exact archived PDF samples with evidence.

### S7.2 handoff
Files: `src/nba_mike/data/injury_pdf.py`, `research/p0_s4/s7_2/`, `tests/test_injury_pdf.py`, `docs/S7_2_INJURY_ACQUISITION.md`. Requires S7.1 module and PyMuPDF. Explicit `--url` triggers single official PDF download. No automatic bulk scraping. Candidate lines are quarantined; as-of eligibility false. Next S7.3 schema validation + independent publication-time evidence.

## S7.3 handoff
- Code: `src/nba_mike/data/injury_structure.py`; runner `research/p0_s4/s7_3/run_s7_3.py`.
- Requires S7.2 PDF and exact source URL; offline CSV review and validator only.
- Run `python research/p0_s4/s7_3/run_s7_3_acceptance.py`, then full pytest.
- Gate remains RESEARCH_ONLY: verify original publication timestamps and manual schema before any feature training.

## S7.4 handoff
- Run `research/p0_s4/s7_4/run_s7_4.py --pdf <path> --url <official-url>`.
- Inspect CSV and manifest; `AUTO_CANDIDATE` is unverified.
- Training gate remains CLOSED.
- S7.5 should address layout validation and historical as-of evidence.

## S7.5 pending validation
Run S7.5 against 2026-03-27 official PDF; compare counts and inspect suspicious records. No historical publication evidence or model promotion.


### S7.6 handoff
- Replaces `src/nba_mike/data/injury_layout.py` with multi-page column fallback.
- Run `research/p0_s4/s7_6/run_s7_6.py` on the frozen SHA256 PDF.
- Compare per-page diagnostics and spot-check page transitions against original PDF.
- All fallback rows remain `REVIEW_REQUIRED`; historical as-of training is forbidden.
- Preserve uncommitted S7.3–S7.5 changes; commit only after review.


## S7.7 handoff
- Updated `src/nba_mike/data/injury_layout.py` in place.
- Runner: `research/p0_s4/s7_7/run_s7_7.py`.
- Data stays RESEARCH_ONLY; inherited dates are flagged and require verification.
- Next: inspect real-PDF counts, orphan continuation causes, spot-check row assignments and reason completeness; no training authorization.


## S7.8 handoff
Run `python research/p0_s4/s7_8/run_s7_8_acceptance.py`, then full pytest; run S7.8 with CSVs from same PDF SHA. Audit is read-only, BLOCK_TRAINING. Inspect counts, review sample, disagreements and missing dates. S7.7 reports 50 orphan continuations but row CSVs omit raw orphan traces: next step requires parser instrumentation if orphan diagnosis is needed. Do not interpret agreement as ground truth or filename timestamp as historical availability.

## S7.9 handoff
- S7.8 baseline: 108 records, 32 missing dates, 92 review flags, 50 reported orphans; parser agreement is not ground truth.
- S7.9 adds `src/nba_mike/data/injury_context_audit.py`, audit runner, tests, and coordinate traces.
- Run S7.9 on the official PDF with matching S7.7 CSV. Audit does not modify S7.7 output.
- Keep training and betting gates closed. Do not claim historical publication verified.


## S7.10 handoff (pending user run)
S7.9: 205 project tests passed, 108 injury rows, 32 missing context, 0 safe context proposals, 84 reason-line traces (34 NEAR_PLAYER_UNATTACHED, 50 NO_SAFE_PLAYER_ANCHOR). S7.10 diagnostic patch adds `src/nba_mike/data/injury_table_diagnostic.py`, `tests/test_injury_table_s710.py`, `research/p0_s4/s7_10/{run_s7_10.py,run_s7_10_acceptance.py,README.md}`, and docs. Synthetic acceptance 13/13. Run full suite and real PDF; inspect per-page text and PNGs. Do not promote to training or infer publication timestamp from filename. No parser modifications in S7.10.


## S7.11 pending validation
New `src/nba_mike/data/injury_stateful.py` and `research/p0_s4/s7_11/run_s7_11.py`. The parser carries explicitly observed date/matchup/team context across compatible pages and writes separate comparison outputs. Install ZIP, run tests and PDF audit, review difference CSV. Do not claim accuracy or allow training until PDF verification and historical publication evidence are independently established.


## S7.11 pending validation
New `src/nba_mike/data/injury_stateful.py` and `research/p0_s4/s7_11/run_s7_11.py`. The parser carries explicitly observed date/matchup/team context across compatible pages and writes separate comparison outputs. Install ZIP, run tests and PDF audit, review difference CSV. Do not claim accuracy or allow training until PDF verification and historical publication evidence are independently established.


## S7.12 checkpoint (pending local run)
- S7.11 baseline from user: 230 tests, 108 matched records, zero missing context, no nonempty conflicts.
- S7.12 adds read-only structural checks and review sample. Run acceptance, full suite, then real-PDF audit.
- Do not infer independent validation from passing consistency checks. Preserve RESEARCH_ONLY/BLOCK_TRAINING.


## S7.13 handoff
S7.12: 242 tests passing, 108 records, three `TEAM_NOT_IN_MATCHUP` flags, all `LA Clippers` vs `LAC@IND`. S7.13 patches `injury_verify.py` to normalize NBA team labels, adds 30-team/alias tests, and runs the existing verification checks into `s7_13/results`. Await local test and real-PDF outputs. Do not promote data to training.


## S7.14 handoff
Added `src/nba_mike/data/injury_multi_report.py`, `research/p0_s4/s7_14/run_s7_14.py`, and `tests/test_injury_multi_s714.py`. Requires local PDF inputs in `research/p0_s4/s7_14/input_pdfs`. Expected `INSUFFICIENT_DISTINCT_VALID_REPORTS` with only the existing one PDF. Do not promote parser or permit training based on structural consistency. Historical publication verification outstanding.


## S7.15 handoff
New `src/nba_mike/data/injury_acquire.py`, `research/p0_s4/s7_15/` and `tests/test_injury_acquire_s715.py`. Run acceptance, full pytest, then `python research/p0_s4/s7_15/run_s7_15.py`. Inspect acquisition JSON for actual downloaded URLs, 404s, duplicate hashes, and S7.14 distinct count. Manifest candidate URLs not preverified. Continue RESEARCH_ONLY/BLOCK_TRAINING; never equate download time with historical publication time.


### S7.16 handoff
- Module: `src/nba_mike/data/injury_ground_truth.py`; runner `research/p0_s4/s7_16/run_s7_16.py`.
- Inputs: S7.14 `input_pdfs/*.pdf` and `results/<sha>.s7_14_candidates.csv`.
- Outputs: `s7_16_samples.csv`, `s7_16_blind_review.csv`, `GT*.png`, `s7_16_report.json`; grading creates `s7_16_grade.json`.
- Review sheet deliberately blank. No automated ground truth. No historical publication proof. No as-of training.


### S7.17 handoff
S7.16 revealed seven blank reason fields among 20 sampled PDF crops. S7.17 adds `injury_reason_recovery.py` and a read-only batch runner. Inspect `research/p0_s4/s7_17/results/s7_17_reason_proposals.csv`, especially GT004/006/007/012/016/019/020, against the original PDFs. Do not promote proposed strings automatically. Training remains blocked.


### S7.17.2 handoff
Reason-recovery code updated for two-line geometry. Run `research/p0_s4/s7_17_2/run_s7_17_2.py`, inspect review-required proposals, compare against PDF crops. Historical as-of publication remains unverified. Do not train.


### S7.19 handoff
- Run `python research/p0_s4/s7_19/run_s7_19.py` and inspect `research/p0_s4/s7_19/results/`.
- This stage audits the five local source PDFs only; it never promotes records or establishes historical publication time.
- Gate stays `BLOCK_TRAINING` until independently authenticated contemporaneous public-availability evidence predating prediction cutoffs exists, and contextual assignments are validated.

## S7.20 handoff
New: `src/nba_mike/data/injury_capture.py`, `research/p0_s4/s7_20/run_s7_20.py`, `tests/test_injury_capture_s720.py`, `docs/S7_20_SOURCE_FEASIBILITY.md`. Manual capture accepts only exact official NBA static injury-report PDF URLs and writes raw SHA-256 objects plus append-only UTC event lines. Existing five historical PDFs remain `RESEARCH_ONLY / BLOCK_TRAINING`; prospective retrieval proves local first possession only. Next: validate full identity/matchup associations and investigate independently timestamped historical captures. Do not auto-promote data to as-of eligibility.


## S7.21 handoff
Run `python research/p0_s4/s7_21/run_s7_21.py` and `python -m pytest -q`; inspect `research/p0_s4/s7_21/results/`. Independent coordinate check is not human truth or historical availability. Training blocked.


## S7.22 handoff
Run `python research/p0_s4/s7_22/run_s7_22.py` and `python -m pytest -q`. This checks internal semantic consistency, not independent roster ground truth. Keep `RESEARCH_ONLY/BLOCK_TRAINING`; do not promote March PDFs based on creation dates.


## S7.23 handoff
Run `python research/p0_s4/s7_23/run_s7_23.py` and `python -m pytest -q`. Header-only independent roster evidence template is intentionally empty. Never treat existing PDF section events as independent roster proof. Maintain RESEARCH_ONLY/BLOCK_TRAINING; next source feasibility and stable player ID validation.


S7.24: Conservative roster evidence staging adapter, not a historical roster fetcher. Run python research/p0_s4/s7_24/run_s7_24.py; blank source template yields 0 qualified rows. Strict interval/ID/provenance checks; results are provisional and never auto-promoted. S7.23 baseline 475 unresolved. Historical PDF publication unverified. RESEARCH_ONLY / BLOCK_TRAINING. Next: source-specific authenticated acquisition and dated transaction reconstruction.


## S7.25 handoff
Run `python research/p0_s4/s7_25/run_s7_25.py --team NYK --season 2025-26`. Check report and raw snapshot; endpoint may block. Eight targeted tests. Outputs untracked. All evidence remains season-level candidate only; S7.23 475 unresolved must not be auto-promoted. Next: dated transaction provenance and effective interval reconstruction.


## S7.26 handoff
Run `python research/p0_s4/s7_26/run_s7_26.py`; empty template yields 0 events, training remains blocked. Code in `research/p0_s4/s7_26/run_s7_26.py`; outputs in `results/` are untracked. Input requires stable NBA player IDs, event dates, source URLs, original source SHA256 and timezone-aware timestamps. Chronology events are provisional, not roster intervals. Next S7.27: source capture and authentication; do not promote S7.23 rows.

## S7.27 handoff
Run `python research/p0_s4/s7_27/run_s7_27.py` and inspect `research/p0_s4/s7_27/results/s7_27_report.json`. HTML saved by SHA in results/objects; CSV contains provisional candidate text, not S7.26-compatible authenticated transactions. No training promotion. Need stable NBA IDs, source-published timestamps and transaction effective dates; do not infer from webpage headings alone.


## S7.28 handoff
Run `python research/p0_s4/s7_28/run_s7_28.py` after S7.27. Uses S7.27 raw HTML and CSV. Optional independent `--id-map` CSV. Inspect `research/p0_s4/s7_28/results/s7_28_report.json` and review CSV. No automatic S7.26 export; historical injury as-of availability still unverified. Keep RESEARCH_ONLY/BLOCK_TRAINING.

## S7.29 handoff
Run `python -m pytest -q`, then `python research/p0_s4/s7_29/run_s7_29.py`; inspect `research/p0_s4/s7_29/results/s7_29_report.json`. Requires existing S7.27 HTML and S7.28 review CSV. If NBA Stats blocks request, use `--directory-json` with an independently obtained unmodified CommonAllPlayers JSON. Exact matches are provisional IDs only. S7.26/S7.23 unchanged, historical injury publication not verified, training blocked.

## S7.30 handoff
From project root run `python -m pytest -q`, then `python research/p0_s4/s7_30/run_s7_30.py`. Inspect `research/p0_s4/s7_30/results/s7_30_report.json` and `s7_30_review.csv`. Requires S7.27 original HTML, S7.28 review, S7.29 identity candidates. All 80 candidates remain review-only; no S7.26/S7.23 promotion. Next: independent per-event verification and unmatched-name diagnosis. Historical injury publication still unverified; training blocked.

## S7.31 handoff
Run `python -m pytest -q`, then `python research/p0_s4/s7_31/run_s7_31.py`. Requires S7.30 review CSV. Inspect `research/p0_s4/s7_31/results/s7_31_report.json` and review CSV. Optional `independent_evidence.csv` contains only independently sourced, locally saved snapshots with matching SHA-256 and verbatim excerpt; empty by default. No automatic approval of origins, effective dates, historical availability, or training. Next: independently source original team and dated individual transactions.

## S7.32 handoff

Script: `research/p0_s4/s7_32/run_s7_32.py`; default reads S7.30 review, captures up to 12 eligible player searches, up to 2 official NBA news articles per player. Results: `research/p0_s4/s7_32/results/s7_32_report.json`, `s7_32_capture.csv`, `objects/*.html`. NBA search may return zero article links; record this honestly. Run full pytest, inspect counts, commit only code/tests/docs. Next: evidence semantic extraction and human review, not automatic origin assignment. Training blocked.


## S7.33 handoff
Offline article relevance audit added in `research/p0_s4/s7_33/run_s7_33.py`. Requires S7.32 captured HTML and CSV, plus S7.30 review CSV. Report `research/p0_s4/s7_33/results/s7_33_report.json`; per-candidate excerpts in `s7_33_review.csv`. Repeated article URLs, missing-origin eligibility gap, and player/trade-term context are diagnostic only. No origin team verified, no historical publication proven. Maintain RESEARCH_ONLY / BLOCK_TRAINING. Next: fix player-specific source discovery based on measured relevance.


## S7.34 Handoff
S7.33 completed at Git `28285a4`, 457 passing tests. S7.33 found 24/24 article captures lacked target player name; 2 URLs reused 12 times each. S7.34 patch adds targeted Bing RSS discovery, NBA `/news/` URL allowlist, SHA-256 snapshots, full-player-name and trade-language relevance review. Requires S7.30 review CSV. Run `python -m pytest -q`, then `python research/p0_s4/s7_34/run_s7_34.py --limit 12 --max-links 8`; inspect `research/p0_s4/s7_34/results/s7_34_report.json` and `s7_34_review.csv`. Live success not assumed. Preserve `RESEARCH_ONLY / BLOCK_TRAINING`, zero automatic S7.31/S7.26/S7.23 promotions. Git commit source/docs/tests only; leave all historical snapshots/results untracked. Investigate any search engine blocking and check actual article relevance before moving on.


## S7.35 handoff
Run `python research/p0_s4/s7_35/run_s7_35.py` after S7.34. Review `research/p0_s4/s7_35/results/s7_35_report.json` and `s7_35_review.csv` for root cause. No evidence promotion, no training. Next S7.36 must address measured cause rather than replacing discovery blindly.


## S7.36 handoff — pending execution
Run `python -m pytest -q` then `python research/p0_s4/s7_36/run_s7_36.py` from project root. Review `results/s7_36_report.json`, `results/s7_36_domain_counts.csv` and `results/s7_36_url_review.csv`. Source inputs: S7.34 review and preserved SHA-256 XML objects. Fail closed on missing or altered snapshots. Next decision: repair narrowly evidenced official path filtering or investigate external source leads separately. Do not promote any transaction, roster interval or training row.



## S7.37 handoff
- S7.36 demonstrated Bing RSS produced only external links (114/114).
- S7.37 discovers official NBA news and NBA-hosted team news URLs directly from the SHA-verified S7.27 tracker capture and matches player tokens against S7.30 candidates.
- Code: `research/p0_s4/s7_37/run_s7_37.py`; results: `research/p0_s4/s7_37/results/`.
- All findings are URL leads only; no article contents or historical publication proven. `RESEARCH_ONLY / BLOCK_TRAINING` remains mandatory.
- Next: S7.38 selective article fetch and independent provenance/semantic checks, no automatic training promotion.


## S7.38 handoff
Prerequisite: S7.37 `results/s7_37_review.csv`. Run `python research/p0_s4/s7_38/run_s7_38.py --limit 12`. Outputs in `research/p0_s4/s7_38/results/`: `s7_38_report.json`, `s7_38_review.csv`, SHA256-addressed HTML objects. This stage is strictly RESEARCH_ONLY/BLOCK_TRAINING. Relevant leads are not evidence of originating team or historical as-of availability. Review real report before designing S7.39. Never git-add raw downloaded HTML or results by default.


## S7.39 handoff

Run `python research/p0_s4/s7_39/run_s7_39.py` after S7.38. Review `research/p0_s4/s7_39/results/s7_39_review.csv` and report. Statements and team mentions are review-only. Next: independent transaction-direction assessment, evidence conflicts, and historical publication provenance. Never auto-promote.


## S7.40 handoff — evidence quality review
- Previous stable stage S7.39 commit `b325939` (530 tests reported by user).
- New stage: `research/p0_s4/s7_40/run_s7_40.py`; reads `research/p0_s4/s7_39/results/s7_39_review.csv` and writes `research/p0_s4/s7_40/results/s7_40_review.csv` plus report JSON.
- S7.39 status-count inconsistency: 22 emitted rows vs 23 sum in status_counts; S7.40 recomputes counts from rows only.
- New tests: `tests/test_s740_quality.py` (12 focused tests passed in patch build); expected full suite 542 if prior 530 baseline unchanged.
- Do not equate `DIRECTION_PROPOSAL_REVIEW_ONLY` with verified origin. Never enable as-of training. Do not `git add .` or delete untracked historical outputs.
- Next action: review user S7.40 report and statement-level CSV, then decide whether to build independent source corroboration or improve extraction.


## S7.41 handoff
Source code: `research/p0_s4/s7_41/run_s7_41.py`; tests: `tests/test_s741_recovery.py`; docs: `docs/S7_41_ARTICLE_EVIDENCE_RECOVERY.md`. Inputs: S7.38 `results/s7_38_review.csv` and `results/objects/<sha256>.html`. Run `python -m pytest -q` then `python research/p0_s4/s7_41/run_s7_41.py`. Review `results/s7_41_report.json` and `results/s7_41_review.csv`. Offline only; verify hashes, reconcile counts, review headlines vs body, compare S7.40 proposals. No historical as-of publication verification, no roster evidence promotion, no training. Status remains `RESEARCH_ONLY / BLOCK_TRAINING`.


## S7.42 handoff
Run `python research/p0_s4/s7_42/run_s7_42.py` after S7.41; review `research/p0_s4/s7_42/results/`. Do not promote direction candidates, multi-family agreement, or historical as-of training without independent evidence and publication timing proof. Check tracker mismatch and source editorial independence.


## S7.43 handoff
Runner: `python research/p0_s4/s7_43/run_s7_43.py`. Inputs S7.42 review CSV and S7.38 article objects. Tests `tests/test_s743_event_identity.py`. Outputs untracked `research/p0_s4/s7_43/results/`. Review Tyus Jones as unresolved event identity, not a proven conflict. Editorial independence and historical publication remain unverified. **RESEARCH_ONLY / BLOCK_TRAINING**. Next: event-date evidence provenance and independent reporting review, no automatic promotion.

## S7.44 handoff
Run `python research/p0_s4/s7_44/run_s7_44.py` after S7.43. Review the JSON report, CSV evidence, and article inventory. HTML timestamps are only self-reported candidates, not independent publication proof. No roster/transaction event verified, no training. Next evaluate independent historical archive snapshots or official timestamped transaction ledgers with documented provenance; avoid treating article URL date tokens as proof.


## S7.45 handoff

S7.45 source: `research/p0_s4/s7_45/run_s7_45.py`; tests: `tests/test_s745_date_reconciliation.py`. Input: S7.44 local `results/s7_44_review.csv`; output: S7.45 local `results/s7_45_review.csv` and `s7_45_report.json`. Review conflicting publication dates first, then single publication candidates. S7.46 proposed: independent historical archive timestamp verification with exact URL, archived snapshot hash, capture timestamp, and prediction cutoff checks. Status `RESEARCH_ONLY / BLOCK_TRAINING`.


## S7.45 handoff

S7.45 source: `research/p0_s4/s7_45/run_s7_45.py`; tests: `tests/test_s745_date_reconciliation.py`. Input: S7.44 local `results/s7_44_review.csv`; output: S7.45 local `results/s7_45_review.csv` and `s7_45_report.json`. Review conflicting publication dates first, then single publication candidates. S7.46 proposed: independent historical archive timestamp verification with exact URL, archived snapshot hash, capture timestamp, and prediction cutoff checks. Status `RESEARCH_ONLY / BLOCK_TRAINING`.

...

## S7.46 handoff

Input: `research/p0_s4/s7_45/results/s7_45_review.csv`. Runner: `research/p0_s4/s7_46/run_s7_46.py`. Outputs: `research/p0_s4/s7_46/results/s7_46_report.json` and `s7_46_review.csv`, optional `archive_objects/<sha256>.html`. Archive index candidates are not verified historical availability; downloaded captures require original URL, timestamp, and transaction-claim review. All prior evidence gates remain blocked. Next step should depend on the actual CDX results, not assumed archive availability.

## S7.47 — Archived claims handoff

Run `python research/p0_s4/s7_47/run_s7_47.py` after S7.46 capture download; inspect `research/p0_s4/s7_47/results/s7_47_report.json` and review CSV. The source inputs are S7.46 review, saved archive_objects and S7.42 review. Treat all extracted claims as review-only; continue `RESEARCH_ONLY / BLOCK_TRAINING`.

## S7.48 — Archived content recovery handoff

Run `python research/p0_s4/s7_48/run_s7_48.py`; inspect `research/p0_s4/s7_48/results/s7_48_report.json` and `s7_48_review.csv`. Inputs: S7.47 review and S7.46 saved archive_objects. Investigate article-content localization and archive replay contamination before any promotion. Maintain `RESEARCH_ONLY / BLOCK_TRAINING`.


## S7.49 — Next agent handoff

Run `python research/p0_s4/s7_49/run_s7_49.py` and review `research/p0_s4/s7_49/results/s7_49_report.json` plus CSV. Inputs: S7.48 review and S7.46 SHA-addressed archived objects. No network, no training promotion. Next milestone should examine full localized article body and original archive provenance for any grammatical direction candidates, and resolve Anthony Davis mapping independently.


## S7.50 — Full archived text audit
Run `python research/p0_s4/s7_50/run_s7_50.py` after S7.49. Review `research/p0_s4/s7_50/results/s7_50_report.json` and `s7_50_review.csv`. Evidence is offline, SHA-checked, not independent archive publication proof. Anthony Davis mapping gaps remain flagged until independently sourced. Do not train from these records; status RESEARCH_ONLY / BLOCK_TRAINING.


## S7.51 — Handoff
- Read `docs/S7_51_EVIDENCE_BOTTLENECK_DECISION.md` and `research/p0_s4/s7_51/README.md`.
- Runner uses `research/p0_s4/s7_50/results/s7_50_review.csv`, creates `s7_51_report.json`, `s7_51_review.csv`, `s7_51_article_inventory.csv` under S7.51 results.
- Do not confuse per-player review rows with independent reports. No archived article, event date, or roster membership has been promoted to historical as-of proof.
- Research track stop/go: pause same-object extraction; require independently timestamped transaction/roster evidence to reopen. Continue only independently validated non-roster modeling work in parallel.
- Training decision remains `BLOCK_TRAINING` for chronology-dependent features.

## S8.0 — Handoff
Run `python research/p0_s8/s8_0/run_s8_0.py --project-root .`; inspect `research/p0_s8/s8_0/results/s8_0_report.json`, inventory and component review. This is a path/schema-only triage, not a source-quality certification. Never promote roster or transaction chronology from S7.51. Next stage should perform focused row-level as-of audit on discovered minutes/player-stat candidates and baseline code, without training.


## S8.1 — Next-agent handoff
Runner: `research/p0_s8/s8_1/run_s8_1.py`. Test: `tests/test_s81_gamelog_quality.py`. Inputs: `research/p0_s4/s5_1/snapshots/player_gamelogs_{2019-20,2023-24,2025-26}.csv`. Outputs under `research/p0_s8/s8_1/results/`. Review the report and schema CSV before S8.2. Keep `RESEARCH_ONLY / BLOCK_TRAINING`; S7.51 historical roster and transaction data remain blocked. No full-suite run or live dataset execution has been verified by this patch alone.


## S8.2 — Next agent handoff
- Run `python research/p0_s8/s8_2/run_s8_2.py --project-root .`.
- Inspect `research/p0_s8/s8_2/results/s8_2_report.json`, `s8_2_dataset_review.csv`, `s8_2_schema_review.csv`.
- S8.1 false flags: `event_date` and lowercase target columns. S8.2 repairs detection; snapshots remain unchanged.
- Never promote a quality-check pass into pre-tipoff availability certification. Historical roster/transactions remain BLOCKED_S7_51.
- Decide S8.3 based on genuine issues in rerun; otherwise audit lagging/as-of and OOS evaluation protocol.

## S8.3 — Calendar audit handoff

S8.2 found 1,892 2019–20 rows dated July 1 or later, likely related to the pandemic-delayed 2020 season. S8.3 audits three existing snapshots offline and produces `s8_3_report.json`, `s8_3_game_calendar_review.csv`, and `s8_3_dataset_review.csv`. Candidate July 30–August 14 restart dates are **not verified official game schedule evidence**. Preserve original snapshots. No training or promotion; historical roster/transaction features remain `BLOCKED_S7_51`. Inspect observed flag count and date/game conflicts; if suitable, S8.4 should independently verify game IDs and dates against a trusted official schedule.

## S8.4 — Official schedule gate

Run `python research/p0_s8/s8_4/run_s8_4.py --project-root . --fetch-official`. Review `results/s8_4_report.json` and `results/s8_4_game_review.csv`. Official NBA Stats endpoint can fail; do not promote failed, missing, conflicting, or unattested matches. Continue to block model training and all historical roster/transaction features. Next milestone depends on actual report; never assume 88 official matches without evidence.

## S8.5 — Feature-lineage feasibility handoff

Runner: `research/p0_s8/s8_5/run_s8_5.py`. Inputs: three `research/p0_s4/s5_1/snapshots/player_gamelogs_<season>.csv`. Outputs: `research/p0_s8/s8_5/results/s8_5_report.json` and `s8_5_dataset_review.csv`. Tests: `tests/test_s85_lineage.py`. Offline, read-only, no training. S8.4 official NBA schedule fetch timed out: 88 restart candidates unverified. S7 roster/transaction/injury historical as-of blocked. Next: inspect existing feature builders for temporal leakage, historical player-universe selection, and as-of proof. Preserve `RESEARCH_ONLY / BLOCK_TRAINING`.


## S8.6 — Code leakage triage handoff

Run `python research/p0_s8/s8_6/run_s8_6.py --project-root .` after full pytest. Review `research/p0_s8/s8_6/results/s8_6_report.json`, `s8_6_findings.csv`, and `s8_6_file_inventory.csv`. Heuristic patterns are review candidates only. Never assert confirmed leakage from a string match or approve training from absence of matches. Check actual S5/S6 functions and chronological folds; source may be missing from scoped directories. Keep RESEARCH_ONLY / BLOCK_TRAINING; S7.51 and S8.4 blockers persist.


## S8.7 handoff
Run `python research/p0_s8/s8_7/run_s8_7.py --project-root .` after installing patch. Upload `s8_7_report.json` and `s8_7_trace.csv`. Six priority sources traced; hashes compared to S8.6 inventory. Do not interpret static traces as actual mutation-test success. Next: contract-aware adversarial tests; pregame universe remains blocked. `RESEARCH_ONLY / BLOCK_TRAINING`.

## S8.8 handoff (2026-10-09)

S8.7 traced six unchanged source files; five gates remained unverified/blocked. S8.8 provides a read-only, offline behavioral test harness for `build_opportunity_research_frame` and `make_form_frame`, 14 cases on synthetic two-player/same-day data. Run `python -m pytest -q tests/test_s88_adversarial.py` and `python research/p0_s8/s8_8/run_s8_8.py --project-root .`; review JSON/CSV under `research/p0_s8/s8_8/results/`. No claim of historical as-of certification even if all pass. Pending: consumer-level target exclusion, fold-local preprocessing, independent pregame player universe, S8.4 restart calendar 88 games. Maintain `RESEARCH_ONLY / BLOCK_TRAINING`.


## S8.9 handoff
S8.8: 14/14 synthetic behavior checks passed, but pipeline not certified. S8.9 adds read-only downstream source scanning and conservative predictor-list contract tests. Run `python -m pytest -q tests/test_s89_downstream.py` then `python research/p0_s8/s8_9/run_s8_9.py --project-root .`. Review `research/p0_s8/s8_9/results/s8_9_report.json` and `s8_9_findings.csv` with the next agent. Never infer actual model matrix safety from source patterns or tests of an unintegrated helper. Do not train/promote/bet. Governance `RESEARCH_ONLY / BLOCK_TRAINING`.


## S8.10 handoff (2026-10-09)

Standalone fail-closed predictor contract created at `research/p0_s8/s8_10/contract.py`, with `run_s8_10.py`, README and `tests/test_s810_contract.py`. Run offline tests and runner; upload `s8_10_report.json` and `s8_10_cases.csv`. No existing model source changed and contract is not wired into training. Do not interpret passing synthetic contract tests as pipeline certification. Next: inspect actual X construction and fold-local preprocessing; maintain independent as-of, pregame eligibility/DNP, and calendar gates. Governance: RESEARCH_ONLY / BLOCK_TRAINING.

## S8.11 — Handoff

New: `research/p0_s8/s8_11/run_s8_11.py`, README, tests, integration-feasibility documentation. The runner produces `s8_11_report.json`, `s8_11_cases.csv`, `s8_11_entrypoints.csv`. Inspect local reports before selecting actual training integration points. S8.10 contract remains standalone. Do not train or approve any candidate predictors. RESEARCH_ONLY / BLOCK_TRAINING.

## S8.12 handoff — Pipeline boundary mapping

Read-only source map only. Script: `research/p0_s8/s8_12/run_s8_12.py`. Run from repo root. Collect `s8_12_report.json`, `s8_12_priority_paths.csv`, `s8_12_call_sites.csv`, `s8_12_assignment_edges.csv`. Review source locations for real downstream consumers and any actual training matrix construction. AST matches are not proof of model fitting or dataflow. No feature allowlist approved. Do not enable fitting, promotion, or bets. Maintain `RESEARCH_ONLY / BLOCK_TRAINING`; as-of publication, pregame player universe/DNP, fold-local transforms and 88 restart games unresolved.


## S8.13 handoff

S8.13 creates a research-only training-boundary design and tests. `research/p0_s8/s8_13/boundary.py` unconditionally denies training; even complete self-asserted evidence cannot authorize. Runner: `python research/p0_s8/s8_13/run_s8_13.py --project-root .`; outputs `s8_13_report.json` and `s8_13_cases.csv` in `research/p0_s8/s8_13/results/`. Uses existing S8.10 contract for synthetic checks. Do not enable fitting, infer verified as-of lineage, or approve a predictor list. Next: review reports, prioritize independent data-source lineage and player-eligibility evidence, then design future training-service integration with separate approval.

## S8.14 — Next agent handoff

**Current status:** RESEARCH_ONLY / BLOCK_TRAINING. S8.13 standalone boundary exists but is not integrated into training. S8.14 is an offline source-feasibility audit, not as-of certification.

**Files:** `research/p0_s8/s8_14/run_s8_14.py`, `README.md`, `evidence_intake_TEMPLATE.csv`, `tests/test_s814_provenance.py`, `docs/S8_14_HISTORICAL_PREGAME_FEASIBILITY.md`.

**Run:** `python -m pytest -q tests/test_s814_provenance.py` then `python research/p0_s8/s8_14/run_s8_14.py --project-root .`.

**User should upload:** `research/p0_s8/s8_14/results/s8_14_report.json`, `s8_14_sample_games.csv`, `s8_14_source_registry.csv` and `s8_14_evidence_review.csv` if used.

**Constraints:** Never claim verified publication from operator-supplied timestamps; no training; no endpoint retries; postgame participants not pregame universe; 88 restart games unresolved. Source registry candidates are not verified available.

## S8.15 handoff

Runner: `research/p0_s8/s8_15/run_s8_15.py`; test: `tests/test_s815_evidence_pilot.py`. Game `0022300061`, LAL@DEN, 2023-10-24 7:30 PM ET. NBA-hosted 5PM injury PDF identified (PDF header says 5:30 PM ET), but independent proof of pre-tipoff publication absent. Optional manual artifact intake via `evidence_intake_TEMPLATE.csv` copied to `evidence_intake.csv`; original bytes in `artifacts/`. Never mark as certified based on file label, operator CSV or current hosting. Review outputs `s8_15_report.json`, `s8_15_evidence_review.csv`, `s8_15_source_candidates.csv`. Training is blocked; restart 88 unresolved.


## S8.16 — Handoff

New module `research/p0_s8/s8_16/run_s8_16.py`, tests `tests/test_s816_evidence_acquisition.py`, documentation `docs/S8_16_OFFICIAL_EVIDENCE_ACQUISITION.md`. Runner defaults offline; flags `--acquire-official --query-wayback` explicitly permit two network retrievals. Outputs `results/s8_16_report.json`, `results/s8_16_artifact_manifest.csv`, `results/s8_16_archive_candidates.csv`; preserved bytes under `artifacts/`. Review actual reports before proceeding. CDX candidates, PDF metadata, current headers, and claimed publication time are NOT independent pregame proof. Zero certified games; no training, no eligible-player certification; 88 restart games blocked. `RESEARCH_ONLY / BLOCK_TRAINING`.

## S8.17 — archive diagnostics handoff

Source `research/p0_s8/s8_17/run_s8_17.py`, tests `tests/test_s817_archive_diagnostics.py`. S8.16 official NBA PDF checksum `126bd5162d1dc4d568a536029fc4fc4a5557ef23ac25652dd706b3d79c8a0e2f` is historical **artifact identity only**, not historical public availability. Review `results/s8_17_report.json`, `s8_17_request_audit.csv`, `s8_17_capture_candidates.csv` and optionally raw artifacts. Valid empty CDX `[]` means no returned matches, not schema failure. Archive indexes alone never certify pregame availability. Keep `RESEARCH_ONLY / BLOCK_TRAINING`; 88 restart games unresolved.

## S8.18 handoff

Run `python -m pytest -q tests/test_s818_alternative_sources.py`, then `python research/p0_s8/s8_18/run_s8_18.py --project-root . --acquire-sources` (network opt-in). Review `research/p0_s8/s8_18/results/s8_18_report.json` and `s8_18_source_audit.csv`. Current downloads, publisher timestamps, and syndication do not certify pregame publication. Never use postgame inactives as pregame features. Keep `RESEARCH_ONLY / BLOCK_TRAINING`; 88 restart games unresolved.

## S8.19 handoff

Run `python -m pytest -q tests/test_s819_publication_audit.py` then `python research/p0_s8/s8_19/run_s8_19.py --project-root .`. Review `research/p0_s8/s8_19/results/s8_19_report.json`, `s8_19_artifact_review.csv`, `s8_19_publication_claims.csv`, `s8_19_capture_review.csv`. Source metadata and manual capture intake are **not independent proof**. No approved historical pregame sources; `RESEARCH_ONLY / BLOCK_TRAINING`; 88 restart games unresolved.

## S8.20 handoff — hybrid forward-evidence-first design

Run `python -m pytest -q tests/test_s820_strategy.py`, then `python research/p0_s8/s8_20/run_s8_20.py --project-root .`. Upload five result files from `research/p0_s8/s8_20/results/`. Historical snapshots and all pre-2026 capture artifacts remain **exploratory**. No training path is authorized; S8.13 remains fail-closed. Proposed next milestone S8.21: local, offline fixture-based immutable capture-store proof of concept with deterministic IDs, UTC receipt timestamps, hash integrity, duplicate detection, and failure logs; do not claim pregame certification or run production collection without separately authorized source access.


## S8.21 — Handoff

S8.20 adopted hybrid forward-first architecture. S8.21 adds **offline-only** fixture capture: SQLite ledger, SHA256 raw bytes, duplicate/failure tracking, integrity check, health reports. Install patch and run `python -m pytest -q tests/test_s821_capture.py`; run demo with `python research/p0_s8/s8_21/run_s8_21.py --project-root . --demo`. Outputs in `research/p0_s8/s8_21/artifacts/results/`. Exclude artifacts from Git. Next: S8.22 authorized live schedule adapter after source policy and schema review. No source or player certified, no real prospective snapshots, no model fitting; `RESEARCH_ONLY / BLOCK_TRAINING`. 88 restart games separately blocked.


## S8.22 — Current handoff (2026-10-09)
S8.21 fixture capture validated on user's PC (12 events, 2 successes, 7 duplicates, 3 failures, no corruption). S8.22 patch introduces `research/p0_s8/s8_22/run_s8_22.py`, offline fixture, tests, and docs. Tests: 14 passed in patch build. Install into existing repository; do not overwrite S8.21. First run offline fixture; review receipt/CSV. Optional `--live` performs one request to allowlisted `https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json` (endpoint unverified at packaging). Raw bytes are recorded in S8.21 even on parse failure. Live network errors are recorded as failures. Requested checkpoint label is not proof of actual T-minus timing. Do not train, certify as-of, approve eligibility, or remove 88-game block. Next assess real source accessibility/schema; S8.23 injury-report adapter only after review.


## S8.22.1 handoff
- Patch replaces only `research/p0_s8/s8_22/run_s8_22.py` and `tests/test_s822_schedule.py`; S8.21 untouched.
- Run offline pytest before manually attempting one live NBA CDN schedule request.
- New report fields: `http_error_diagnostics`, `source_assessment`; HTTP status retained on HTTPError.
- No alternate endpoint chosen; diagnose status first and assess authorized source separately.
- Do not advance S8.23 until a source is legally accessible, schema-validated, and captured reliably.
- `RESEARCH_ONLY / BLOCK_TRAINING`; 88 restart games remain blocked.


## S8.22.2 handoff
The NBA CDN returned HTTP 403 in S8.22.1. Do not retry or bypass. S8.22.2 compares five candidates offline, with eight unfulfilled acceptance gates. Run `python research/p0_s8/s8_22_2/run_s8_22_2.py --project-root .`; inspect three results in `research/p0_s8/s8_22_2/results/`. No source authorized for collection. Next task: verify written provider permissions, affordable plans and actual schedule coverage before building a live adapter. Preserve S8.21 receipts, explicit source-ID crosswalk, independent eligibility gate and `RESEARCH_ONLY / BLOCK_TRAINING`; 88 restart games remain blocked.


## S8.22.3 — Handoff
Provider comparison is documentation-only. Candidate BALLDONTLIE `/v1/games` (free NBA Games advertised, 5 req/min; key required), fallback API-Sports NBA. Existing NBA CDN yielded 403; do not retry. Runner `research/p0_s8/s8_22_3/run_s8_22_3.py`, tests `tests/test_s8223_provider_review.py`, results in `research/p0_s8/s8_22_3/results/`. Next S8.22.4: after terms and user entitlement confirmation, create explicit manual authorized adapter; store secrets in environment; no secrets in logs, artifacts, Git. Verify real schema, tipoff, provider-to-NBA IDs, and S8.21 provenance. Still RESEARCH_ONLY/BLOCK_TRAINING, 88 restart games separately blocked.


## S8.22.4 — Handoff (2026-10-09)

- Installed new standalone `research/p0_s8/s8_22_4/run_s8_22_4.py` (do not overwrite S8.21/S8.22).
- Local user confirmed `BALLDONTLIE_API_KEY` is readable from `.env` and `git check-ignore -v .env` matches `.gitignore`. Never request the key.
- 15/15 offline tests passed. Execute `python -m pytest -q tests/test_s8224_balldontlie.py` before any live run.
- Fixture run: `python research/p0_s8/s8_22_4/run_s8_22_4.py --project-root . --date 2026-10-10 --fixture research/p0_s8/s8_22_4/fixture_games.json`.
- Explicit live run after user reviews terms: same command with `--live` instead of `--fixture ...`. Do not repeatedly retry HTTP 403/429.
- Review `research/p0_s8/s8_22_4/results/s8_22_4_report.json` and `s8_22_4_games.csv`. Raw evidence remains under S8.21 artifacts; never commit raw artifacts or `.env`.
- Schedule-source acceptance, provider-to-NBA game IDs, tipoff correctness, eligibility, chronological gates and historical as-of evidence remain unverified. `RESEARCH_ONLY / BLOCK_TRAINING`. 88 restart games blocked.


## S8.22.5 handoff — 2026-10-09

- Prior S8.22.4: BALLDONTLIE HTTP 200 and capture SUCCESS for 2026-10-10, zero rows. No coverage certification.
- New offline audit: `research/p0_s8/s8_22_5/run_s8_22_5.py`; 11 passing tests. Reads S8.22.4 CSV, optionally independent official schedule CSV and manually reviewed provider-to-official team crosswalk.
- New output: `research/p0_s8/s8_22_5/results/s8_22_5_report.json` and `s8_22_5_comparison.csv`.
- Explicit states: `EMPTY_SCHEDULE_UNVERIFIED`, `EMPTY_SCHEDULE_CONTRADICTED_BY_REFERENCE`, `PROVIDER_GAMES_PRESENT_UNVERIFIED`, `PARTIAL_OR_UNVERIFIED_COVERAGE`, `CANDIDATE_DATE_COVERAGE_MATCH_REQUIRES_REVIEW`.
- Never infer official NBA game IDs from BALLDONTLIE IDs; matched crosswalk outputs candidate IDs only. No automatic requests, retries, scheduling, training, or betting.
- Next: run with existing zero-game CSV, then authorized manual populated-date test and independently sourced official schedule review. `RESEARCH_ONLY / BLOCK_TRAINING`.


## S8.22.6 handoff
Offline cross-validation patch uses NBA official opening-night publication and game pages for 2023-10-24: LAL@DEN 0022300061 23:30 UTC; PHX@GSW 0022300062 02:00 UTC on 2023-10-25. Provider rows and BALLDONTLIE IDs are **not** official IDs. The user must populate research/p0_s8/s8_22_6/team_crosswalk_review.csv from actual S8.22.4 historical provider records, with independently documented evidence. Run tests and CLI; review report and comparison. Do not promote crosswalk, automate schedules, or train models. Governance RESEARCH_ONLY / BLOCK_TRAINING. Reference source URLs in docs/S8_22_6_OFFICIAL_CROSS_VALIDATION.md.

## S8.22.7 — Handoff

S8.22.6 had 2/2 candidate matches on 2023-10-24; not approved. S8.22.7 introduces `research/p0_s8/s8_22_7/run_s8_22_7.py`, `date_manifest.csv`, and `independent_reference_TEMPLATE.csv`. It reads per-date provider CSVs and independently sourced references only; no live network or model training. Empty or missing evidence is fail-closed. Run `python -m pytest -q tests/test_s8227_multi_date.py`, then `python research/p0_s8/s8_22_7/run_s8_22_7.py --project-root .`. Upload report and date audit. Do not equate retrospective schedule matches with historical as-of availability. Remains RESEARCH_ONLY / BLOCK_TRAINING.


## S8.22.7.1 — Handoff
Installed module: research/p0_s8/s8_22_7_1/run_s8_22_7_1.py. CLI: --date YYYY-MM-DD (--fixture PATH | --live) [--update-manifest]. Reuses S8.22.4 and S8.21; date-specific captures in research/p0_s8/s8_22_7_1/captures/. Optional manifest update only fills blank provider_csv and never modifies reference_csv. Existing 2023-10-24 data preserved. Verify local test results, obtain independent references, run S8.22.7 again. Never commit secrets; no production or training authorization. RESEARCH_ONLY / BLOCK_TRAINING.

## S8.22.7.2 — Handoff

The patch supplies `research/p0_s8/s8_22_7_2/run_s8_22_7_2.py` and tests. Only official NBA HTTPS pages accepted. Source snapshots are immutable unique paths, receipt metadata includes SHA-256 and UTC time. Normalization requires user-reviewed CSV and source receipt; no automatic HTML parsing. Manifest only updated on explicit opt-in, no overwrite.

**Critical:** Never use partial-date reference as complete schedule. Blank reference cannot certify no-game day. Do not infer as-of availability from current page snapshots. Continue source verification and multi-date reliability testing. RESEARCH_ONLY / BLOCK_TRAINING.

## S8.22.7.3 — Handoff

Runner: `research/p0_s8/s8_22_7_3/run_s8_22_7_3.py`; repeat `--receipt` for each independently archived official NBA game. Output includes one reference CSV row per game with individual source URL, SHA-256 and retrieval UTC. Optional `--provider-csv` and `--crosswalk` call the existing S8.22.7 provisional comparator. Does NOT update S8.22.7 manifest or certify full-date completeness. Date-level schedule evidence and historical as-of proof remain outstanding. No automatic training or routine collection approval. RESEARCH_ONLY / BLOCK_TRAINING.

## S8.22.7.4 — Handoff

New module: `research/p0_s8/s8_22_7_4/run_s8_22_7_4.py`. Inputs: date-level S8.22.7.2 official NBA evidence receipt, manually curated date-level CSV, and S8.22.7.3 per-game reference. No network, no manifest modification. Reports missing/extra game IDs, team/tipoff discrepancies, and source-byte ID presence.

All successful comparisons are candidates only. No-game dates cannot be certified by empty CSV. Date completeness and historical pregame as-of remain NOT_CERTIFIED. RESEARCH_ONLY / BLOCK_TRAINING.

## S8.22.7.4.1 — Handoff

Fix to S8.22.7.4 announcement incompatibility: separate `research/p0_s8/s8_22_7_4_1/run_s8_22_7_4_1.py` verifies archived official NBA schedule announcement SHA-256 and visible-text matchup/tipoff/coverage excerpts, then compares against S8.22.7.3 official per-game ID reference. The announcement itself need not contain game IDs. Candidate CSV for Oct 24 requires human verification. No network, no manifest writes, no full-date completeness or historical pregame as-of certification. RESEARCH_ONLY / BLOCK_TRAINING.

## S8.22.7.5 — Handoff

Five-date offline coverage expansion. Manifest at `research/p0_s8/s8_22_7_5/coverage_manifest.csv` intentionally leaves paths blank until user fills verified local paths. Runner `run_s8_22_7_5.py` emits UUID-named JSON/CSV reports and always BLOCK_TRAINING. October 24 candidate announcement may be linked to S8.22.7.4.1; November 15/January 15 need independent date-level official references; June 20 and October 10 zero-provider results cannot certify no games. Never automatically fetch, retry NBA CDN, or claim historical as-of.

## S8.22.7.6 — Handoff

New offline `research/p0_s8/s8_22_7_6/run_s8_22_7_6.py` consumes S8.22.7.5 JSON and creates a five-date evidence queue. Priority P1 Nov 15, P2 Jan 15, P3 June 20 negative evidence, P4 Oct 10 2026 preseason; Oct 24 preserved as control. Optional receipt manifest validates official NBA saved-source SHA256 and size but never certifies coverage. No network, no automatic approval. Outputs in `research/p0_s8/s8_22_7_6/results/`. RESEARCH_ONLY / BLOCK_TRAINING.

## S8.22.7.7 — Handoff

Official NBA date snapshot for 2023-11-15 captured at `research/p0_s8/s8_22_7_2/evidence/2023-11-15/21684d55a7e446e4b8da7288d5750d26/`; SHA-256 `85ea943f3b9cba374728ba6c37f05848bbbe2b34bbd4956ceda367d0c66ae0f4`. `run_s8_22_7_7.py` offline verifies receipt and extracts eight official games `0022300192`–`0022300199` from `__NEXT_DATA__`. Provider count eight known from S8.22.7.5, but per-game matchup/tipoff agreement not yet proven. Need original provider CSV for comparison. No date completeness or historical as-of certification; BLOCK_TRAINING.

## S8.22.7.8 — Handoff

`research/p0_s8/s8_22_7_8/run_s8_22_7_8.py` compares Nov 15 BALLDONTLIE provider CSV to official S8.22.7.7 extracted NBA games; crosswalk is **candidate inferred**, not independently verified. Checks capture hash, unique home/away matchup, UTC tipoff tolerance, missing/extra and duplicate games. Input files are user-local and not bundled. Report is always BLOCK_TRAINING. Next task: verify `/v1/teams` team-ID mappings from independent archived bytes before promoting crosswalk evidence; date completeness/historical as-of remain NOT_CERTIFIED.

## S8.22.7.9 — Handoff

S8.22.7.8 had eight candidate November 15 game matches but 16 game-inferred team mappings. New `research/p0_s8/s8_22_7_9/` contains an offline `/v1/teams` archive verifier and a local receipt creator; no live fetching. Requires authentic directory JSON bytes, SHA-256 receipt, original S8.22.7.8 crosswalk and comparison JSON. Outputs unique JSON review and verified mapping CSV; rejects missing/duplicate/conflicting mappings. Even with verified identities, schedule completeness, historical pregame as-of and training remain blocked. RESEARCH_ONLY / BLOCK_TRAINING.



<!-- S8.22.7.11 documentation checkpoint -->
## S8.22.7.11 handoff

S8.22.7.10 completed on user machine: 4 tests passed, 8/8 games and zero tipoff deltas, all mechanical checks PASS, but `date_completeness=NOT_CERTIFIED`, `historical_asof=NOT_CERTIFIED`, `BLOCK_TRAINING`; commit `9a69e67` pushed to main. S8.22.7.11 is offline independent completeness evidence review at `research/p0_s8/s8_22_7_11/`. Run against latest S8.22.7.10 report; no new source is bundled. Source/receipt/manifest inputs are optional, must be manually acquired and reviewed, and can yield candidate status only. Use `append_docs.py` once to merge append fragments into existing primary docs with backups. Preserve all existing untracked and modified evidence; never `git add .` or `git clean`. Continue RESEARCH_ONLY / BLOCK_TRAINING.

<!-- S8.22.7.12 documentation checkpoint -->
## S8.22.7.12 handoff

Offline source-intake runner: `research/p0_s8/s8_22_7_12/run_s8_22_7_12.py`. Source must be manually acquired, then archived with actual retrieval UTC and SHA256. Review report before making any completeness claim. Even 8/8 matching games means candidate corroboration only; historical as-of and training blocked. Do not make automatic requests or stage evidence indiscriminately.


<!-- S8.22.7.13 documentation checkpoint -->
## S8.22.7.13 — Independent source governance review

**Goal:** Offline audit of S8.22.7.12 third-party source integrity and the limits of eight-game agreement.

**Decision:** Distinct publisher domain is observed, but upstream editorial independence, exhaustive date completeness, and 2023 pregame publication are not established. Keep `RESEARCH_ONLY / BLOCK_TRAINING`.

**Validation:** `python -m pytest tests/test_s822713_source_governance.py -q` and review local source-governance report. Source bytes are not modified or committed automatically.


<!-- S8.22.8 documentation checkpoint -->
## S8.22.8 — Historical pregame feasibility audit

Added offline five-category evidence manifest and fail-closed feasibility report. Categories: player availability, expected minutes, starting lineups, player opportunity, betting markets. Historical as-of, licensing, and pre-tipoff evidence are unverified until independently substantiated. No source requests or model training. Decision: RESEARCH_ONLY / BLOCK_TRAINING. Next: manually review a permitted, historically timestamped source.


<!-- S8.22.9 documentation checkpoint -->
## S8.22.9 — Historical pregame provider shortlist

Reviewed official NBA injury-report archive, SportsDataIO, BALLDONTLIE, and strictly lagged local game-log derivations. Provider descriptions and URLs are in `research/p0_s8/s8_22_9/source_candidates.json`. This is a source-discovery shortlist only; November 2023 as-of timestamps, licensing, and access are NOT_VERIFIED. Priority: manually examine dated official injury reports, ask commercial provider about 2023 replay and timestamps, then design a lag-only minutes/opportunity proof. No credentials, network calls, training, or routine collection. Decision: RESEARCH_ONLY / BLOCK_TRAINING.


<!-- S8.22.10 documentation checkpoint -->
## S8.22.10 — Historical official injury PDF pilot

Implemented manual-only official NBA PDF intake with SHA256 archive, embedded edition-label extraction, eight November 15, 2023 tipoffs, and 60-minute cutoff comparison. The PDF edition label is NOT proof of historical public availability. No network calls, automatic retries, player eligibility claims, training, or production approval. Pilot requires an actual manually obtained original PDF before it can produce evidence. Decision: RESEARCH_ONLY / BLOCK_TRAINING.

## S8.22.10.2 — Coordinate-aware injury candidate attribution
- Implemented offline coordinate-aware candidate extraction from the archived 2023-11-15 NBA injury PDF; player rows and team-level NOT YET SUBMITTED notices are separate.
- SHA256/receipt verification, page and coordinate provenance, conservative game/team matching, ambiguity flags, manual review required.
- Runtime dependency: pypdf; test dependency: pytest. Previous S8.22.10.1 tests additionally require reportlab.
- Outputs remain local; do not stage raw PDFs or generated result files.
- Governance: RESEARCH_ONLY / BLOCK_TRAINING; historical as-of NOT_CERTIFIED.
- Next: inspect actual candidate CSV and ambiguities against original PDF pages before certifying extraction quality.
