# S8.22.7.2 — Independent schedule evidence

Two paths: `import` an already saved **official NBA** HTML/JSON page or `fetch` an official page after explicit terms acknowledgement. Both store unmodified source bytes, UTC receipt, SHA-256 and source URL in a unique directory. Neither auto-parses HTML into a schedule.

For each game, manually transcribe the official game ID, home/away team abbreviations and scheduled UTC tipoff into a copy of `reviewed_games_TEMPLATE.csv`, based on the archived source. **One source receipt should substantiate every row**. If a page covers only one game, create a one-game CSV and do not call it a complete date schedule.

Run `normalize` with the matching receipt and manually reviewed CSV. Optionally update the S8.22.7 manifest **once** using `--update-manifest --confirm-full-date-reference` only when the archived page substantiates the full date. It refuses to overwrite existing reference paths.

**No-game dates:** this version deliberately refuses blank reference CSVs. An empty page or missing game listing cannot establish absence of games. Preserve separate authoritative date-level evidence and defer certification.

**Limitations:** Official website material retrieved today does not prove its pregame availability. The current S8.22.7 comparison treats reference rows as a set; it does not independently establish completeness. A 1-game reference CSV is **not** an acceptable complete-date reference for a day with multiple games. Verify date completeness manually before manifest updates. S8.22.7 cannot independently verify the archived evidence hashes: review both receipt and normalized CSV.

## Example (PowerShell)

```powershell
$Runner = ".\research\p0_s8\s8_22_7_2\run_s8_22_7_2.py"
python $Runner --project-root . fetch --date 2023-10-24 --url "https://www.nba.com/game/lal-vs-den-0022300061" --acknowledge-provider-terms
# Review archived page and manually complete a CSV from verified source.
python $Runner --project-root . normalize --date 2023-10-24 --receipt "PATH_TO_RECEIPT_JSON" --reviewed-csv "PATH_TO_REVIEWED_CSV"
# Add --update-manifest only after independently verifying full-day completeness.
```

No `.env` access, no API key needed, no retries, no automated schedule approval.
