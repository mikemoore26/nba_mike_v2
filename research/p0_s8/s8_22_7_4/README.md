# S8.22.7.4 — Official date-level evidence comparison

**Offline, fail closed, no training.**

1. Acquire an **independent official NBA date-level schedule page** (not an individual game page) using S8.22.7.2 `import` or `fetch` after terms review. Preserve `source.bin` and `receipt.json`. The source must explicitly cover the requested date.
2. Review the archived page and manually transcribe *every* official game on that date into a copy of `reviewed_date_schedule_TEMPLATE.csv`. Do not copy rows from BALLDONTLIE or the S8.22.7.3 reference: that would defeat independence.
3. Run the S8.22.7.4 validator against the archived date-level receipt and the S8.22.7.3 per-game reference.
4. Review any missing IDs, extra IDs, matchup/tipoff conflicts, and date-level source evidence. An exact match is only `CANDIDATE_DATE_LEVEL_AGREEMENT_REVIEW_REQUIRED` because automated checks cannot establish that the webpage lists **all** games on the date.

The validator requires each transcribed official game ID to occur in the archived raw source bytes, but this is only a sanity check. It cannot verify that the page is truly complete or that its content was available before tipoff.

**No-game dates:** intentionally unsupported; an empty CSV or empty webpage cannot certify no games. Requires separately designed negative-evidence protocol.

**Example**:

```powershell
$Runner = ".\research\p0_s8\s8_22_7_4\run_s8_22_7_4.py"
python $Runner --project-root . --date 2023-10-24 `
  --date-receipt ".\research\p0_s8\s8_22_7_2\evidence\2023-10-24\<date-capture-id>\receipt.json" `
  --reviewed-date-csv ".\research\p0_s8\s8_22_7_4\reviewed_2023-10-24.csv" `
  --game-reference-csv ".\research\p0_s8\s8_22_7_3\results\2023-10-24\official_reference_<id>.csv"
```

No manifest updates, live API calls, or automatic completeness certification.
