# S7.23 independent historical roster evidence gate

Run from repository root: `python research/p0_s4/s7_23/run_s7_23.py`.

The committed `roster_evidence.csv` is **header only**. This milestone establishes a validator, **not** independent roster verification. Do not populate evidence with the injury PDF or its parser outputs. Evidence rows require an independently obtained roster source, player identity, team, valid-from/through dates, source URL, capture/source timestamps, and evidence ID. Date ranges and sources must be checked before use. A missing or incomplete source yields `UNRESOLVED`. Contradictory valid evidence yields `CONFLICT`. Names are provisional join keys; before using `VERIFIED` operationally, resolve independent player IDs and ambiguous names. Outputs are written under `results/` and must not be committed. Historical injury-report availability remains unverified, so training stays blocked.
