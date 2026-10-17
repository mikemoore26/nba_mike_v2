# S8.22.10.5 — PDF-anchored manual verification packet

This is a **review preparation** milestone, not an automatic verification or a correction to the S8.22.10.4 parser. Input files and the archived PDF remain untouched.

Run the tests first:

```powershell
python -m pytest .\tests\test_s822105_review.py -q
```

Run the review-packet builder with the S8.22.10.4 results directory:

```powershell
$Receipt = '.\research\p0_s8\s8_22_10\evidence\2023-11-15\0ed781ec55ef4391a7e6dfdb2f6aff14\receipt.json'
$Previous = '.\research\p0_s8\s8_22_10_4\results\2023-11-15\c562cd651f28403f9f0f1b7a9eac76eb'
python .\research\p0_s8\s8_22_10_5\run_s8_22_10_5.py --project-root . --receipt $Receipt --s822104-results $Previous
```

Outputs: `manual_review_ledger.csv`, `schedule_and_artifact_flags.csv`, `review.json` under a unique result directory. The ledger contains source PDF page/y, nearby PDF text, and blank reviewer fields. Every row begins `PENDING` and `training_eligible=NO`.

For human review, open the original PDF beside the ledger. Compare date, matchup, team, player/notice, status and full reason. In a **copy** of the ledger, mark `manual_decision` as `ACCEPT`, `REJECT`, or `UNRESOLVED`; fill `reviewer`, `reviewed_at_utc`, verified fields and review notes. Do not mark records accepted based solely on nearby extracted text. No automatic importer consumes reviewer decisions at this stage.

The `prior_schedule_comparison` column compares against the **previously recorded game-ID slate**, not a newly certified official schedule. Home/away reversals are review flags; neither source is silently selected as authoritative. Rows on November 16 are out of the target date, not necessarily incorrect.

`RESEARCH_ONLY / BLOCK_TRAINING` remains mandatory, even if manual review is complete.
