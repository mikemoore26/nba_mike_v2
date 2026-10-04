# P0-S2 POC-04 hotfix 1

Fixes the JSON serialization crash observed after the POC-04 computation completed.

Cause:
Pandas/Numpy returned one or more `numpy.int64` scalar values inside the nested
research report. Python's standard `json.dumps()` does not serialize NumPy
scalar types automatically.

Change:
- add explicit NumPy/Pandas -> native Python JSON conversion
- no reconstruction logic, thresholds, data source, or acceptance criteria changed

Replace only:
`research/p0_s2/poc04/run_poc04.py`

Then rerun POC-04 from the beginning.
