# P0-S3 S5 — Canonical Dataset Builder

This milestone proves a fail-closed Raw -> Validated -> Canonical build path using a small synthetic player-game fixture. It intentionally avoids predictive modeling and live-source expansion.

Run:

`python -m pytest .\tests\test_canonical_builder.py -q`

`python .\research\p0_s3\s5\run_s5_acceptance.py`

Acceptance requires integrity verification, PASS-parent enforcement, schema enforcement, identity resolution, duplicate rejection, impossible-value rejection, canonical publication, and parent-linked provenance.
