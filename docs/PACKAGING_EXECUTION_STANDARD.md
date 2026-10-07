# NBA_MIKE v2 — Packaging & Execution Standard

## Purpose
Make the repository's `src/` layout importable through the active virtual environment without manually setting `PYTHONPATH`.

## Naming contract
- Repository/project directory: `nba_mike_v2`
- Python distribution: `nba-mike-v2`
- Python import package: `nba_mike`

These names intentionally differ. Do not rename `src/nba_mike` to `src/nba_mike_v2` merely to match the repository name.

## Installation contract
From the repository root with `.venv` activated:

    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    python -m pip install -e .

Editable installation is the development standard. Source edits under `src/nba_mike` are then visible to the active environment without reinstalling after each edit.

## Verification contract
A clean shell/environment must be able to run:

    python -c "import nba_mike; print(nba_mike.__file__)"

without manually adding `src` to `PYTHONPATH`.

The complete regression suite must also pass:

    python -m pytest -q

## Scope
This infrastructure patch changes package discovery/execution only. It does not change statistical logic, source truth claims, D-1 rules, schemas, model gates, or intraday-data feasibility conclusions.

## Failure behavior
Do not hide packaging failures by restoring a manual `PYTHONPATH` workaround. Fix the editable installation or environment instead.
