# S7.29 — Player identity resolution

**Scope:** Collect NBA Stats `commonallplayers` directory with stable `PERSON_ID`, `DISPLAY_FIRST_LAST`; match to S7.28 candidates using exact Unicode-normalized names, never fuzzy guesses. Retain raw response, SHA-256, URL, retrieval timestamp, provenance verification of original S7.27 HTML. Duplicate name mapping to different IDs is ambiguous. No match is an unresolved identity, not proof of absence. Exact ID is an **identity candidate**, not an authenticated trade or historical roster assignment.

**Gate:** `RESEARCH_ONLY / BLOCK_TRAINING`; 0 qualified S7.26 events; 0 verified injury assignments. S7.27 source publication and historical as-of availability remain unverified. Network failure fails closed.
