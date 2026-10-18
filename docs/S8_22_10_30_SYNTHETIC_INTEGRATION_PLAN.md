# S8.22.10.30 — Synthetic Cross-Module Integration

**Objective:** Verify selected existing modules interoperate under deterministic synthetic inputs. Do not modify or replace the existing production modules.

**Prerequisite:** S8.22.10.29 smoke report showed 39 passing tests across five suites. This does not certify integrated behavior.

**Coverage:**
1. Raw source manifest and SHA-256 verification, canonical player/team resolution, and canonical artifact manifest.
2. Canonical-to-D-1 snapshot adapter, date cutoff, unique player-game keys, team/opponent consistency, metadata, and zero-history labeling.
3. Snapshot-to-opportunity adapter, strictly prior-day form features, and no same-day cross-game contamination.
4. Fail-closed tests: tampered raw source, unknown identity, tampered canonical source, target/future date exclusion, and realized target leakage.

**Explicit gap:** `canonical.game_date` differs from `snapshot.event_date`; `canonical.minutes` differs from `features.min`, and likewise for stats. Adapter exists only in tests. A governed production adapter requires a separately reviewed schema and manifest contract.

**Required validation:** Run `python -m pytest tests/test_s8221030_integration.py -q` in the actual repository. Record actual pass/fail output before updating the development journal and next-agent handoff. The new tests are not proof of real data quality or prediction validity.

**Decision:** Keep `RESEARCH_ONLY / BLOCK_TRAINING / REAL_MONEY_DENIED`. No betting tickets, no model promotion.
