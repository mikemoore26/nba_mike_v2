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

