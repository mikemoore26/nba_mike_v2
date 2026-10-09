# S7.45 — Publication date reconciliation

Reconciles S7.44 metadata **per SHA-256 article object** and produces one review row per article. Publication fields, modification fields, creation fields and unattributed HTML time/date fields remain separate. A single explicit publication date is a *preferred candidate*, not proof. Multiple conflicting publication dates receive priority `HIGH_CONFLICT_REVIEW` and no preferred candidate. Source self-reporting, historical availability, event identity and editorial independence remain distinct gates.

Outputs: `research/p0_s4/s7_45/results/s7_45_review.csv`, `s7_45_report.json`.

S7.46 should retrieve independently timestamped historical snapshots for prioritized articles and evaluate snapshot capture times against actual prediction cutoffs. Do not promote any source or train using these findings alone.
