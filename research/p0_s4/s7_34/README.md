# S7.34 Targeted Official NBA Article Discovery

Research-only repair to S7.32's generic NBA site search. Uses Bing RSS to discover *only* official NBA news URLs. Searches include exact player name, destination team, event-date label and trade terms. Search RSS and NBA article snapshots are SHA-256 content addressed in `results/objects/`. Only articles containing the full player name and transaction vocabulary are labeled `RELEVANT_REVIEW`; they are **not** accepted as transaction proof. Each candidate is assessed independently, even when articles are reused. No evidence export or roster assignment.

From project root:

```powershell
python -m pytest -q
python .\research\p0_s4\s7_34\run_s7_34.py --limit 12 --max-links 8
Get-Content .\research\p0_s4\s7_34\results\s7_34_report.json
Import-Csv .\research\p0_s4\s7_34\results\s7_34_review.csv | Format-Table candidate_number,player_name,capture_status,article_url -AutoSize
```

Network/search services may return no RSS items, block requests, or rate-limit. The report records these outcomes without claiming evidence. Search output is untrusted; the tool only fetches whitelisted official NBA article URLs and verifies redirects. Do not commit generated snapshots or results. No automated promotion to S7.31, S7.26 or S7.23. Historical publication as-of remains unverified.
