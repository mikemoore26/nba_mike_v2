# S8.22.7.11 — Independent full-date schedule evidence (offline)

**Purpose:** Record the independent-evidence gap and assess any subsequently archived authoritative complete-slate source without silently certifying completeness. No HTTP requests, keys, training, or betting.

1. Find the newest `schedule_governance_*.json` in `research/p0_s8/s8_22_7_10/results/2023-11-15`.
2. Run `python research/p0_s8/s8_22_7_11/run_s8_22_7_11.py --project-root . --governance-report PATH`.
3. The resulting unique JSON is written under `research/p0_s8/s8_22_7_11/results/2023-11-15/`.
4. To assess a *separately sourced* archival document, manually capture immutable source bytes with a SHA256 receipt (same `date`, `source_url`, `evidence_path`, `sha256`, `bytes`, `retrieved_utc` fields as S8.22.7.2). Provide a **human-reviewed** JSON manifest containing `date`, `source_url`, `source_sha256`, eight `official_nba_game_ids`, `source_explicitly_states_full_date_slate`, `supporting_quote_or_locator`, and `reviewed_by`. Run with `--independent-manifest PATH --independent-receipt PATH`. This is not automatic source acquisition and the manifest alone is not proof of independence. Candidate results still require human governance review.
5. To append documentation safely (only after reviewing changes), run `python research/p0_s8/s8_22_7_11/append_docs.py --project-root .`. Requires existing `docs/DEVELOPMENT_JOURNAL.md` and `docs/NEXT_AGENT_HANDOFF.md`; creates `.pre_s822711.bak` backups, never replaces prior content, and avoids duplicate appends.

**No new independent source is bundled or claimed.** Matching counts, two URLs, and retrospective data are insufficient to certify a complete historical pregame slate. Status remains `RESEARCH_ONLY / BLOCK_TRAINING`.
