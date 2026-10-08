# S7.16 Ground-truth audit — research only

Goal: validate S7.11 predictions against the original PDF visually, without treating parser output or its internal consistency as truth. The S7.14 multi-report gate reached 5 distinct reports / 475 extracted records / 0 structural flags; this is not extraction accuracy.

S7.16 prepares up to four deterministic, cross-page-prioritized samples per distinct report and cropped source images. The blind review sheet starts empty and requires explicit YES/NO/UNREADABLE for player, status, team, matchup, game date, reason. Crops are not sufficient to verify inherited context: reviewers must consult the full original PDF and section transitions. Unreviewed is never scored as correct.

Promotion gate stays blocked regardless of manual review completion: separately prove historical publication-time availability and design a representative accuracy threshold and audit of omitted rows. Sampling parser-detected records cannot measure missing player rows (recall).
