# S8.22.10.13 — Automated Game-ID Evidence Verification

## Motivation
S8.22.10.12's default crosswalk path wrongly assumed its containing directory used the crosswalk hash prefix. The actual S8.22.10.7 directory is `9194687df27944ca`, while its **file SHA-256** is `ca59d35f24e2ac8c1ba70971b5fec60ec7ce654a938b4d9d1902848f8d115212`. Explicit `--crosswalk` proved that eight of eight evidence checks passed, but a manual worksheet still remained PENDING.

## Decision
Reuse S8.22.10.12 integrity logic without modifying prior milestone files. Discover the crosswalk by its **full expected content hash**; fail on zero/multiple matches. Mark `AUTOMATED_VERIFIED` for records with all local evidence and consistency checks passing, otherwise `MANUAL_EXCEPTION_REQUIRED`. Generate machine-readable verification and exception reports. **Never** fill reviewer identity, timestamps, or approval decisions automatically.

## Scientific boundary
These checks support local archived-evidence consistency, not independent source authentication, historical-as-of proof, human certification, injury/player identity, or model training. Remain `RESEARCH_ONLY / BLOCK_TRAINING` and retain the 54 pending injury-report records.

## Tests and use
See `research/p0_s8/s8_22_10_13/README.md`. Tests include crosswalk-directory regression, SHA mismatch, ambiguous candidates, all-pass, page tampering, and schedule tampering.
