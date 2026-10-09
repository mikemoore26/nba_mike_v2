# S8.8 Offline adversarial leakage tests

Run from project root:

```powershell
python -m pytest -q tests/test_s88_adversarial.py
python research/p0_s8/s8_8/run_s8_8.py --project-root .
```

Outputs in `research/p0_s8/s8_8/results/`: `s8_8_report.json`, `s8_8_cases.csv`.
Exit code 0 = 14 synthetic behavioral cases pass, **NOT** historical as-of certification.
Exit code 2 = a case fails or import is blocked. Do not modify production features or train.

The script imports the existing repository's `nba_mike.features.opportunity.build_opportunity_research_frame` and `nba_mike.features.adaptive_form.make_form_frame`. It does not patch them or access the network. It tests current/future outcome mutation, same-date doubleheader, player isolation, row permutation, target boundary and cold start. A pass cannot prove independent pregame player availability, historical publication times, real-world joins, or downstream target exclusions.
