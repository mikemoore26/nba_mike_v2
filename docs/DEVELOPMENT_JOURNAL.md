# NBA_MIKE v2 — Development Journal

## P0-S1 — Project Charter & Research Governance
**Date:** 2026-10-03  
**Status:** READY FOR USER INSTALLATION / ACCEPTANCE CHECK

### Goal
Create the minimum governance foundation for NBA_MIKE v2 before data collection or model development.

### Problem
Earlier sports projects improved over time, but important safeguards such as strict leakage thinking, research/production separation, model promotion, detailed tracking, and concise AI handoff were often strengthened after development had already begun.

### Options considered
1. Start collecting NBA data immediately.
2. Start building points/rebounds/assists models immediately.
3. Establish research governance first, then prove target/data feasibility.

### Selected solution
Option 3.

### Why
Architecture should follow evidence. Before committing to data sources, features, models, or betting markets, NBA_MIKE v2 needs rules that define what counts as trustworthy evidence.

### Implementation
P0-S1 establishes:
- project charter
- research governance
- separate development and discovery journals
- concise future-AI handoff
- Git milestone discipline
- model lifecycle states
- PASS/no-bet philosophy
- baseline-first and time-aware validation rules

### Files introduced
- `README.md`
- `docs/RESEARCH_GOVERNANCE.md`
- `docs/DEVELOPMENT_JOURNAL.md`
- `docs/DISCOVERY_JOURNAL.md`
- `docs/NEXT_AGENT_HANDOFF.md`
- `.gitignore`

### Testing / acceptance
P0-S1 passes when:
- all required files exist
- Git repository is initialized
- Git can see the intended files
- governance explicitly blocks premature model building
- handoff identifies P0-S2 as the next task

### What could go wrong
Governance can become bureaucracy. Documents must stay useful and should not duplicate each other. The handoff in particular must remain concise.

### What I should learn
A serious modeling project starts by defining how it will decide whether an idea is valid. Writing a model is not evidence that the model works.

### Result
Pending local installation and Git checkpoint.

### Next action
P0-S2 — Target & Data Feasibility. Do not train models yet.
