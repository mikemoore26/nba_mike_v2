# NBA_MIKE v2 — Discovery Journal

This journal records scientific/research findings, including negative results.

## Status vocabulary
- DISCOVERED
- PROMISING
- FAILED
- UNSTABLE
- CONFIRMED_OOS
- PRODUCTION_CANDIDATE

## Experiment template

### Experiment ID
TBD

**Date:**  
**Status:**  
**Question:**  
**Hypothesis:**  
**Predefined success criterion:**  
**Dataset/version:**  
**Sample:**  
**Method:**  
**Visuals:**  
**Potential confounders:**  
**Effect size/result:**  
**Chronological validation:**  
**Out-of-sample result:**  
**Interpretation:**  
**Potential feature/model impact:**  
**Decision:** ACCEPT / REJECT / INCONCLUSIVE / REQUIRES_MORE_DATA  
**Next action:**  

---

## Current state
No NBA research experiment has been run yet.

P0-S1 intentionally creates governance only. The first evidence-gathering work begins with P0-S2 target and data feasibility.

## DISC-P0S2-001 — D-1 historical boundary is reproducible

**Question:** Can season-to-date NBA statistical features be reconstructed before a target game without including that game's result?

**Evidence:** POC-08 and POC-09 across 2019-20, 2023-24, and 2025-26.

**Result:** CONFIRMED FOR DAY-LEVEL RESEARCH. POC-09 showed target-date players increased GP by exactly one from D-1 to D, with zero wrong target-player deltas and zero non-target changes.

**Interpretation:** D-1 is an intentionally conservative feature boundary suitable for the first historical dataset architecture.

**Limit:** This does not prove intraday availability for injuries, lineups, news, or odds.

**Modeling consequence:** Build initial statistical training features from D-1 snapshots; keep target-day game logs strictly on the label side.

**Status:** ACCEPTED FOR DATASET DESIGN.

