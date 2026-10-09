# S7.32 — Automated NBA article acquisition

Objective: collect independently published NBA news article candidates for the 71 missing-origin transaction rows. Search responses and articles are retained as hashed HTML objects; manifest captures candidate, URL, retrieval time, SHA, outcome. This is *not* independent verification of origin team, player participation, transaction effective date, or historical publication time. No S7.31 evidence rows are populated automatically. Source site may serve client-rendered search pages without links or block scripted access; failures are explicit. The next milestone must evaluate semantic claims with corroboration, rather than infer teams from headlines.

Governance: `RESEARCH_ONLY / BLOCK_TRAINING`.
