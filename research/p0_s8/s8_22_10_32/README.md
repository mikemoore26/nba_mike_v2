# S8.22.10.32

Install ZIP at project root. Run:

```powershell
python -m pytest tests/test_s8221031_adapter.py tests/test_s8221032_regression.py tests/test_s8221032_journals.py -v
```

If successful, append milestone notes:

```powershell
python research/p0_s8/s8_22_10_32/update_journals.py --project-root .
git diff --check
git diff -- docs/DEVELOPMENT_JOURNAL.md docs/NEXT_AGENT_HANDOFF.md
```

Do not `git add .`. Stage only files listed in installation instructions. Unrelated research evidence and backups are out of scope.
