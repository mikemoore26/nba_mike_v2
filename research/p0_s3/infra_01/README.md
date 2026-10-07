# P0-S3 INFRA-01 — Project Packaging & Execution

This patch resolves the src-layout import defect discovered after S6.

Baseline evidence before the patch:
- `python -m pip install -e .` failed because no `pyproject.toml` or `setup.py` existed.
- standalone `import nba_mike` failed when `PYTHONPATH` was removed.
- the existing regression suite still reported 38 passing tests.

INFRA-01 adds a minimal setuptools `pyproject.toml`, packaging regression tests, an acceptance runner, and documentation. It deliberately does not consume the planned S7 milestone number; the original P0-S3 S7 remains Leakage & Invariant Test Suite.
