# S7.24 — Conservative independent roster evidence staging

This milestone **does not automatically download rosters**. It establishes a reproducible, strict ingestion boundary for independently acquired dated roster evidence. Season roster snapshots and name-only claims are not sufficient to prove day-specific membership. Populate `source_roster_intervals.csv` only with externally supported intervals, source URLs, source-as-of timestamps and stable IDs; mark `interval_basis=DATED_PRIMARY_EVIDENCE`, `identity_basis=STABLE_PLAYER_ID`, and `independent_of_injury_pdf=true` only if supported.

Run `python research/p0_s4/s7_24/run_s7_24.py` to produce qualified and rejected CSVs. **Qualified means schema-screened, not independently authenticated.** Do not automatically append these rows to S7.23's roster evidence or train models. Review source snapshots, identity joins and effective-date provenance first. Keep generated `results/` outside Git.
