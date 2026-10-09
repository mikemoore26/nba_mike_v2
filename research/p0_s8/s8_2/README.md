# S8.2 schema recognition repair and row re-audit

Offline, read-only against the three existing S5.1 player game-log CSV snapshots. Fixes S8.1 false flags for `event_date` and lowercase stat targets; retains duplicate/date/minutes/value checks. Outputs are written only under `research/p0_s8/s8_2/results/`. No model training, historical provenance promotion, or market decisions.

Run: `python research/p0_s8/s8_2/run_s8_2.py --project-root .`
Test: `python -m pytest -q tests/test_s82_recognition.py`
