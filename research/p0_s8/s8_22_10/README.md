# S8.22.10 — Historical official injury report pilot

**Research-only. No automatic HTTP calls, no model training.**

1. Locate a genuine original NBA injury-report PDF edition for November 15, 2023 through the [official 2023–24 injury-report index](https://official.nba.com/nba-injury-report-2023-24-season/). Do not fabricate a guessed PDF URL, bypass access restrictions, or silently substitute a modern summary.
2. Download one PDF manually through your browser, subject to NBA terms. Save it to `research/p0_s8/s8_22_10/manual_input/injury_report.pdf` and record the *actual PDF URL* from the browser address bar.
3. Run the manual intake command shown in `docs/S8_22_10_INJURY_PILOT.md` with a retrieval timestamp captured **when you download**. Do not pass today's time as the 2023 publication time.
4. Review the output receipt under `research/p0_s8/s8_22_10/evidence/2023-11-15/<uuid>/receipt.json`. The edition time comes from the PDF text and is *not independently authenticated*. `edition_before_cutoff` is only a conditional comparison.
5. Do not infer that a player missing from the PDF was healthy or eligible. Do not train models.

Dependency: `pypdf` for local PDF text extraction (`python -m pip install pypdf` if absent).

If no original PDF is obtainable, record `NOT_ESTABLISHED` and stop; do not generate synthetic evidence.
