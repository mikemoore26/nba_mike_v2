# S8.22.7.5 — Coverage expansion protocol

**Scope:** 2023-10-24 (2 provider rows), 2023-11-15 (8), 2024-01-15 (11), 2024-06-20 (0), 2026-10-10 (0). Counts are from the preceding S8.22.7 audit, not asserted as exhaustive official counts.

**Evidence hierarchy:** provider snapshot → independent official game references → independent date-level official schedule evidence → human-reviewed date coverage → historical pregame availability. No step implies the next automatically.

**Implementation:** New read-only five-date manifest and offline comparison runner. Detects missing snapshots/references, duplicate IDs, team and tipoff disagreement, insufficient coverage evidence, and zero-provider-row uncertainty. Date-level source receipt integrity can be checked; it is not proof of exhaustive schedule content. Reports are append-only UUID outputs. Existing manifest, source archives and model gates are untouched.

**Decision:** RESEARCH_ONLY / BLOCK_TRAINING. Do not infer no-game days from empty API results or certify historical pregame availability from contemporary captures.
