# P0-S4 S2 — Target Contract & Outcome Builder

S2 creates the first governed target builder for minutes, points, rebounds, assists, and made threes.

Important design choice: missing/DNP evidence is not silently converted into zero. The builder governs observed outcome rows; a historically complete availability universe is a separate problem.

Run:
`python -m pytest tests/test_target_builder.py -q`
then:
`python research/p0_s4/s2/run_s2_acceptance.py`
