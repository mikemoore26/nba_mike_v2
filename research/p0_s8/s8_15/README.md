# S8.15 — official NBA injury report pilot

Target: Lakers at Nuggets, game `0022300061`, October 24 2023; scheduled tipoff 7:30 PM ET. Official NBA PDF: https://ak-static.cms.nba.com/referee/injury/Injury-Report_2023-10-24_05PM.pdf (PDF label: 5:30 PM ET).

This is an offline, read-only *historical evidence feasibility* check. The runner never downloads the PDF or validates an external archive. The PDF label is NOT independently verified historical publication time. Do not certify player eligibility, use the report as an exhaustive roster, or train models.

Optional manual intake: obtain the PDF from the official URL; save the original bytes under `artifacts/` (e.g. `artifacts/Injury-Report_2023-10-24_05PM.pdf`). Copy `evidence_intake_TEMPLATE.csv` to `evidence_intake.csv`, enter the artifact's path relative to `artifacts/`, SHA-256 (PowerShell `Get-FileHash ... -Algorithm SHA256`), the document's claimed time with timezone, and an independently archived capture URL/time **only when supported by a verifiable archival record**. Do not invent archive metadata. Even a fully populated intake remains `CANDIDATE_REVIEW_ONLY`, not verified.

Run `python research/p0_s8/s8_15/run_s8_15.py --project-root .`; results in `results/`. Test with `python -m pytest -q tests/test_s815_evidence_pilot.py`.
