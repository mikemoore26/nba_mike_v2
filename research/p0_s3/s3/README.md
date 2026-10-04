# P0-S3 S3 — Canonical Identity System

This acceptance package proves the first executable canonical identity contract for NBA_MIKE v2.

It tests project-owned player/team/game IDs, exact source mappings, conflict rejection, ambiguous aliases, trade-safe player identity, game integrity, player-game uniqueness, and JSON replay.

Run from the repository root with the venv active:

```powershell
python -m pytest ".\tests\test_canonical_identity.py" -q
python ".\research\p0_s3\s3\run_s3_acceptance.py"
```

PASS does not prove source truth. It proves the identity layer fails closed instead of silently changing identity.
